import random
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import pairwise
from typing import Iterable, Sequence

from pyglet.math import Vec2

from trainfinity2.constants import GRID_HEIGHT_CELLS, GRID_WIDTH_CELLS

from .gui import Mode
from .model import (
    Factory,
    Mine,
    Rail,
    CargoType,
    Signal,
    Station,
    Water,
)
from .events import CreateEvent, DestroyEvent, Event
from .signal_controller import SignalController
from .terrain import Terrain

from .route_finder import find_route


@dataclass
class SignalsBeingBuiltEvent(Event):
    signals: set[Signal]


@dataclass
class RailsBeingBuiltEvent(Event):
    rails: set[Rail]


@dataclass
class StationBeingBuiltEvent(Event):
    station: Station | None
    illegal_positions: set[Vec2] = field(default_factory=set)


def positions_between(start: Vec2, end: Vec2) -> list[Vec2]:
    positions = [start]
    while positions[-1] != end:
        current = positions[-1]
        abs_dx = abs(current.x - end.x)
        abs_dy = abs(current.y - end.y)
        x_step = (end.x - current.x) // abs_dx if abs_dx else 0
        y_step = (end.y - current.y) // abs_dy if abs_dy else 0
        new_x = current.x + (abs_dx >= abs_dy) * x_step
        new_y = current.y + (abs_dy >= abs_dx) * y_step
        positions.append(Vec2(new_x, new_y))
    return positions


def rails_between(start: Vec2, end: Vec2) -> list[Rail]:
    return [
        Rail(x1, y1, x2, y2)
        for (x1, y1), (x2, y2) in pairwise(positions_between(start, end))
    ]


def station_between(start: Vec2, end: Vec2) -> Station:
    is_east_west = abs(start.x - end.x) >= abs(start.y - end.y)
    new_end = Vec2(end.x, start.y) if is_east_west else Vec2(start.x, end.y)
    return Station(tuple(positions_between(start, new_end)), east_west=is_east_west)


def get_random_position() -> Vec2:
    x = random.randrange(0, GRID_WIDTH_CELLS)
    y = random.randrange(0, GRID_HEIGHT_CELLS)
    return Vec2(x, y)


class Grid:
    def __init__(self, terrain: Terrain, signal_controller: SignalController) -> None:
        super().__init__()
        self._signal_controller = signal_controller

        self.water: dict[Vec2, Water] = {}
        self.mines: dict[Vec2, Mine] = {}
        self.factories: dict[Vec2, Factory] = {}
        self.station_from_position: dict[Vec2, Station] = {}
        self.signals: dict[tuple[Vec2, Rail], Signal] = {}
        self.rails_being_built: set[Rail] = set()
        self.station_being_built: Station | None = None
        self.rails: set[Rail] = set()

        self.left = 0
        self.bottom = 0
        self.right = GRID_WIDTH_CELLS
        self.top = GRID_HEIGHT_CELLS
        self._create_terrain(terrain)

    def _create_terrain(self, terrain: Terrain):
        for position in terrain.water:
            self.water[position] = Water(position)

    def _get_random_position_to_build_mine_or_factory(self) -> Vec2:
        illegal_positions = (
            self.water.keys()
            | self.mines.keys()
            | self.factories.keys()
            | self.station_from_position.keys()
            | {position for rail in self.rails for position in rail.positions}
        )
        while True:
            position = get_random_position()
            if position not in illegal_positions:
                return position

    def create_mine(self, position: Vec2, cargo: CargoType) -> CreateEvent:
        mine = Mine(position, cargo_type=cargo)
        self.mines[position] = mine
        return CreateEvent(mine)

    def _create_mine_in_random_unoccupied_location(
        self, cargo: CargoType
    ) -> CreateEvent:
        return self.create_mine(
            self._get_random_position_to_build_mine_or_factory(), cargo
        )

    def _create_factory(self, position: Vec2) -> CreateEvent:
        factory = Factory(position)
        self.factories[position] = factory
        return CreateEvent(factory)

    def _create_factory_in_random_unoccupied_location(self) -> CreateEvent:
        return self._create_factory(
            self._get_random_position_to_build_mine_or_factory()
        )

    def find_route_between_stations(
        self, station1: Station, station2: Station
    ) -> list[Rail] | None:
        """Finds the shortest route between two stations.

        Returns None if there is no route or if `station1 == station2`."""
        if station1 == station2:
            return None
        self.rails_from_vec2 = defaultdict(list)
        for rail in self.rails:
            self.rails_from_vec2[Vec2(rail.x1, rail.y1)].append(rail)
            self.rails_from_vec2[Vec2(rail.x2, rail.y2)].append(rail)
        return find_route(
            self.possible_next_rails_ignore_red_lights,
            self.rails_at_position(station1.positions[0]),
            station1.positions[0],
            station2,
        )

    def rails_at_position(self, position: Vec2) -> set[Rail]:
        return {rail for rail in self.rails if position in rail.positions}

    def possible_next_rails_ignore_red_lights(
        self, position: Vec2, previous_rail: Rail | None
    ):
        return self.rails_at_position(position) - {previous_rail}

    def _rail_is_inside_grid(self, rail: Rail):
        return all(
            self._is_inside(x, y) for x, y in ((rail.x1, rail.y1), (rail.x2, rail.y2))
        )

    def _is_inside_station_in_wrong_direction(self, rail: Rail):
        for station in self.station_from_position.values():
            if rail.positions & set(station.positions):
                if (rail.y1 == rail.y2 and station.east_west) or (
                    rail.x1 == rail.x2 and not station.east_west
                ):
                    return False
                return True
        return False

    def _mark_illegal_rail(self, rails: Iterable[Rail]) -> set[Rail]:
        illegal_positions = (
            self.water.keys() | self.mines.keys() | self.factories.keys()
        )
        return {
            (
                rail.to_illegal()
                if (rail.positions & illegal_positions)
                or not self._rail_is_inside_grid(rail)
                or self._is_inside_station_in_wrong_direction(rail)
                else rail
            )
            for rail in rails
        }

    def _illegal_station_positions(self, station: Station) -> set[Vec2]:
        if not any(
            self._adjacent_mine_or_factory(position) for position in station.positions
        ):
            return set(station.positions)

        overlapping_positions_with_rail_in_wrong_direction = {
            position
            for rail in self.rails - station.internal_and_external_rail
            for position in rail.positions
            if position in station.positions
        }
        positions_outside = {
            position for position in station.positions if not self._is_inside(*position)
        }
        illegal_positions = (
            self.water.keys()
            | self.mines.keys()
            | self.factories.keys()
            | self.station_from_position.keys()
        )
        return (
            overlapping_positions_with_rail_in_wrong_direction
            | positions_outside
            | (illegal_positions & set(station.positions))
        )

    def _is_inside(self, x, y):
        return self.left <= x < self.right and self.bottom <= y < self.top

    def click_and_drag(
        self, x: int, y: int, start_x: int, start_y: int, mode: Mode
    ) -> Sequence[Event]:
        if mode == Mode.RAIL:
            return [self._show_rails_being_built(Vec2(start_x, start_y), Vec2(x, y))]
        elif mode == Mode.STATION:
            self.station_being_built = station_between(
                Vec2(start_x, start_y), Vec2(x, y)
            )
            return [
                StationBeingBuiltEvent(
                    self.station_being_built,
                    self._illegal_station_positions(self.station_being_built),
                ),
                self._show_rails_being_built(
                    *self.station_being_built.positions_before_and_after
                ),
            ]

        elif mode == Mode.DESTROY:
            return self.remove_rail(Vec2(x, y))

        return []

    def _show_rails_being_built(self, start: Vec2, stop: Vec2) -> RailsBeingBuiltEvent:
        rails_being_built = rails_between(start, stop)
        self.rails_being_built = self._mark_illegal_rail(rails_being_built)
        return RailsBeingBuiltEvent(self.rails_being_built)

    def remove_rail(self, position: Vec2) -> list[Event]:
        events: list[Event] = []
        for rail in self.rails_at_position(position):
            events.append(DestroyEvent(rail))
            keys = [key for key, signal in self.signals.items() if signal.rail == rail]
            for key in keys:
                events.append(DestroyEvent(self.signals[key]))
                del self.signals[key]
            self.rails.remove(rail)
            for station in set(self.station_from_position.values()):
                if rail in station.internal_and_external_rail:
                    events.append(DestroyEvent(station))
                    for position in station.positions:
                        del self.station_from_position[position]

        events.extend(
            self._signal_controller.create_signal_blocks(
                self, list(self.signals.values())
            )
        )
        return events

    def create_rail(self, rails: set[Rail]) -> list[Event]:
        self.rails.update(rails)
        events = self._signal_controller.create_signal_blocks(
            self, list(self.signals.values())
        )
        # Objects might change id when they are put into a set. Since Drawer uses
        # the object id as key, we need to first put the object in the set and then
        # use the object from the set.
        events.extend(CreateEvent(rail) for rail in self.rails if rail in rails)
        return events

    def release_mouse_button(self, mode: Mode) -> list[Event]:
        events: list[Event] = []
        if all(rail.legal for rail in self.rails_being_built):
            if mode == mode.RAIL:
                events.extend(self.create_rail(self.rails_being_built))
            elif (
                mode == mode.STATION
                and self.station_being_built
                and not (self._illegal_station_positions(self.station_being_built))
            ):
                events.extend(self.create_rail(self.rails_being_built))
                events.append(self._create_station(self.station_being_built))

        self.rails_being_built.clear()
        events.append(RailsBeingBuiltEvent(self.rails_being_built))
        self.station_being_built = None
        events.append(StationBeingBuiltEvent(self.station_being_built))

        return events

    def get_station(self, x, y) -> Station | None:
        return self.station_from_position.get(Vec2(x, y))

    def _is_adjacent(self, position1: Vec2, position2: Vec2):
        dx = abs(position1.x - position2.x)
        dy = abs(position1.y - position2.y)
        return (3 / 4 < dx < 5 / 4 and dy < 1 / 4) or (
            3 / 4 < dy < 5 / 4 and dx < 1 / 4
        )

    def adjacent_mines(self, positions: Iterable[Vec2]) -> list[Mine]:
        return [
            mine
            for mine in self.mines.values()
            for position in positions
            if self._is_adjacent(position, mine.position)
        ]

    def adjacent_factories(self, positions: Iterable[Vec2]) -> list[Factory]:
        return [
            factory
            for factory in self.factories.values()
            for position in positions
            if self._is_adjacent(position, factory.position)
        ]

    def _adjacent_mine_or_factory(self, position: Vec2) -> Mine | Factory | None:
        for mine in self.mines.values():
            if self._is_adjacent(position, mine.position):
                return mine
        for factory in self.factories.values():
            if self._is_adjacent(position, factory.position):
                return factory
        return None

    def _create_station(self, station: Station) -> CreateEvent:
        """Creates a station in a location. Must be next to a mine or a factory, or it raises AssertionError.

        East-west if east_west == True, otherwise north-south."""
        # mine_or_factory = self._adjacent_mine_or_factory(station.position)
        # assert mine_or_factory
        for position in station.positions:
            self.station_from_position[position] = station
        return CreateEvent(station)

    def level_up(self, new_level: int) -> Sequence[Event]:
        events = []
        self.left -= 1
        self.bottom -= 1
        self.right += 1
        self.top += 1

        if new_level == 1:
            events.append(
                self._create_mine_in_random_unoccupied_location(CargoType.IRON)
            )
            events.append(self._create_factory_in_random_unoccupied_location())
        elif new_level % 3 == 2:
            events.append(
                self._create_mine_in_random_unoccupied_location(CargoType.COAL)
            )
        elif new_level % 3 == 0:
            events.append(self._create_factory_in_random_unoccupied_location())
        else:
            events.append(
                self._create_mine_in_random_unoccupied_location(CargoType.IRON)
            )

        return events

    def _closest_rail(self, x, y) -> Rail | None:
        """Return None if
        1. manhattan distance larger than a grid box size
        2. there is no rail"""
        if not self.rails:
            return None

        def distance_to_rail(rail: Rail, x: float, y: float):
            return abs((rail.x1 + rail.x2) / 2 - x) + abs((rail.y1 + rail.y2) / 2 - y)

        rails_and_distances = [
            (rail, distance_to_rail(rail, x, y)) for rail in self.rails
        ]
        closest_rail, distance = sorted(rails_and_distances, key=lambda x: x[1])[0]
        return closest_rail if distance < 1 else None

    def create_signals_at_click_position(
        self, world_x: float, world_y: float
    ) -> Sequence[Event]:
        # Transpose half a box since rail coordinates are in the bottom left
        # of each grid cell while they are visible in the middle
        x = world_x - 0.5
        y = world_y - 0.5
        return self.create_signals_at_grid_position(x, y)

    def create_signals_at_grid_position(self, x: float, y: float) -> Sequence[Event]:
        events = []
        if rail := self._closest_rail(x, y):
            for position in rail.positions:
                signal = Signal(position, rail)
                self.signals[(position, rail)] = signal
                events.append(CreateEvent(signal))
        self._signal_controller.create_signal_blocks(self, list(self.signals.values()))
        return events

    def show_signal_outline(
        self, world_x: float, world_y: float
    ) -> SignalsBeingBuiltEvent:
        x = world_x - 0.5
        y = world_y - 0.5
        if rail := self._closest_rail(x, y):
            signals = {Signal(position, rail) for position in rail.positions}
        else:
            signals = set()
        return SignalsBeingBuiltEvent(signals)
