import math
import random
from collections import defaultdict
from dataclasses import dataclass
from itertools import pairwise
from typing import Any, Iterable, Type

from pyglet.math import Vec2

from .constants import GRID_BOX_SIZE, GRID_HEIGHT, GRID_WIDTH
from .gui import Mode
from .model import (
    Factory,
    Mine,
    Rail,
    Signal,
    SignalColor,
    Station,
    Water,
)
from .observer import CreateEvent, DestroyEvent, Event, Subject
from .signal_controller import SignalController
from .terrain import Terrain

from .route_finder import find_route


@dataclass
class RailsBeingBuiltEvent(Event):
    rails: set[Rail]


def positions_between(start: Vec2, end: Vec2):
    positions = [start]
    while positions[-1] != end:
        current = positions[-1]
        abs_dx = abs(current.x - end.x)
        abs_dy = abs(current.y - end.y)
        x_step = (end.x - current.x) // abs_dx if abs_dx else 0
        y_step = (end.y - current.y) // abs_dy if abs_dy else 0
        new_x = current.x + GRID_BOX_SIZE * (abs_dx >= abs_dy) * x_step
        new_y = current.y + GRID_BOX_SIZE * (abs_dy >= abs_dx) * y_step
        positions.append(Vec2(new_x, new_y))
    return positions


def rails_between(start: Vec2, end: Vec2) -> list[Rail]:
    return [
        Rail(x1, y1, x2, y2)
        for (x1, y1), (x2, y2) in pairwise(positions_between(start, end))
    ]


def get_random_position() -> Vec2:
    x = random.randrange(0, GRID_WIDTH // GRID_BOX_SIZE) * GRID_BOX_SIZE
    y = random.randrange(0, GRID_HEIGHT // GRID_BOX_SIZE) * GRID_BOX_SIZE
    return Vec2(x, y)


class Grid(Subject):
    def __init__(self, terrain: Terrain, signal_controller: SignalController) -> None:
        super().__init__()
        self._signal_controller = signal_controller

        self.water: dict[Vec2, Water] = {}
        self.mines: dict[Vec2, Mine] = {}
        self.factories: dict[Vec2, Factory] = {}
        self.stations: dict[Vec2, Station] = {}
        self.signals: dict[tuple[Vec2, Rail], Signal] = {}
        self.rails_being_built: set[Rail] = set()
        self.rails: list[Rail] = []

        self.left = 0
        self.bottom = 0
        self.right = GRID_WIDTH
        self.top = GRID_HEIGHT
        self._create_terrain(terrain)

    def create_buildings(self):
        self._create_mines()
        self._create_factories()

    def _create_terrain(self, terrain: Terrain):
        for position in terrain.water:
            self.water[position] = Water(position)

    @property
    def occupied_positions(self) -> set[Vec2]:
        return (
            self.water.keys()
            | self.mines.keys()
            | self.factories.keys()
            | self.stations.keys()
        )

    def _get_unoccupied_positions(self, count: int) -> set[Vec2]:
        """Gets <count> positions without water, mines, factories or stations. Ignores rails."""
        unoccupied_positions: set[Vec2] = set()
        while len(unoccupied_positions) < count:
            position = get_random_position()
            if position not in self.occupied_positions:
                unoccupied_positions.add(position)
        return unoccupied_positions

    def _get_unoccupied_position(self) -> Vec2:
        return self._get_unoccupied_positions(1).pop()

    def _create_mine(self, position: Vec2):
        mine = Mine(position)
        self.mines[position] = mine
        self._notify_about_other_object(mine, CreateEvent())
        return mine

    def _create_mine_in_random_unoccupied_location(self):
        self._create_mine(self._get_unoccupied_position())

    def _create_mines(self):
        self._create_mine_in_random_unoccupied_location()

    def _create_factory(self, position: Vec2):
        factory = Factory(position)
        self.factories[position] = factory
        self._notify_about_other_object(factory, CreateEvent())
        return factory

    def _create_factory_in_random_unoccupied_location(self):
        self._create_factory(self._get_unoccupied_position())

    def _create_in_random_unoccupied_location(
        self, building: Type[Factory] | Type[Mine]
    ):
        # TODO: pass the type all the way down to drawer
        if building == Factory:
            self._create_factory_in_random_unoccupied_location()
        elif building == Mine:
            self._create_mine_in_random_unoccupied_location()

    def _create_factories(self):
        self._create_factory_in_random_unoccupied_location()

    def snap_to(self, x: float, y: float) -> Vec2:
        return Vec2(self.snap_to_x(x), self.snap_to_y(y))

    def snap_to_x(self, x: float) -> int:
        return math.floor(x / GRID_BOX_SIZE) * GRID_BOX_SIZE

    def snap_to_y(self, y: float) -> int:
        return math.floor(y / GRID_BOX_SIZE) * GRID_BOX_SIZE

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
            self.rails_at_position(station1.position),
            station1.position,
            station2,
        )

    def rails_at_position(self, position: Vec2) -> set[Rail]:
        return {rail for rail in self.rails if rail.is_at_position(position)}

    def possible_next_rails_ignore_red_lights(
        self, position: Vec2, previous_rail: Rail | None
    ):
        return self.rails_at_position(position) - {previous_rail}

    def possible_next_rails(self, position: Vec2, previous_rail: Rail | None):
        """Given a position and where the train came from, return a list of possible rails
        it can continue on.
        Current rules:
        1. The train cannot reverse, i.e. the output cannot contain `previous_rail`.
           (if previous_rail = None, the train is at a standstill, e.g. at a station)
        2. The train cannot go into a red light
        Possible future rules:
        3. The train cannot turn more than X degrees"""
        next_rails = set(self.rails_at_position(position)) - {previous_rail}
        next_rails_with_signals = next_rails.intersection(self.signals)
        for rail in next_rails_with_signals:
            if self.signals[(position, rail)].signal_color == SignalColor.RED:
                next_rails.remove(rail)
        return next_rails

    def _rail_is_in_occupied_position(self, rail: Rail):
        return (
            Vec2(rail.x1, rail.y1) in self.occupied_positions
            or Vec2(rail.x2, rail.y2) in self.occupied_positions
        )

    def _rail_is_inside_grid(self, rail: Rail):
        return all(
            self._is_inside(x, y) for x, y in ((rail.x1, rail.y1), (rail.x2, rail.y2))
        )

    def _mark_illegal_rail(self, rails: Iterable[Rail]) -> set[Rail]:
        return {
            (
                rail.to_illegal()
                if self._rail_is_in_occupied_position(rail)
                or not self._rail_is_inside_grid(rail)
                else rail
            )
            for rail in rails
        }

    def _is_inside(self, x, y):
        return self.left <= x < self.right and self.bottom <= y < self.top

    def click_and_drag(self, x, y, start_x, start_y, mode: Mode):
        x = self.snap_to_x(x)
        y = self.snap_to_y(y)
        start_x = self.snap_to_x(start_x)
        start_y = self.snap_to_y(start_y)

        if mode == Mode.RAIL:
            rails_being_built = rails_between(Vec2(start_x, start_y), Vec2(x, y))
            self.rails_being_built = self._mark_illegal_rail(rails_being_built)
            self.notify(RailsBeingBuiltEvent(self.rails_being_built))
        elif mode == Mode.DESTROY:
            self.remove_rail(Vec2(x, y))

    def remove_rail(self, position: Vec2):
        new_rails = []
        for rail in self.rails:
            if rail.is_at_position(position):
                self._notify_about_other_object(rail, DestroyEvent())
                keys = [
                    key for key, signal in self.signals.items() if signal.rail == rail
                ]
                for key in keys:
                    self._notify_about_other_object(self.signals[key], DestroyEvent())
                    del self.signals[key]
            else:
                new_rails.append(rail)
        self.rails = new_rails

        if position in self.stations:
            station = self.stations[position]
            self._notify_about_other_object(station, DestroyEvent())
            del self.stations[position]

        self._signal_controller.create_signal_blocks(self, list(self.signals.values()))

    def _notify_about_other_object(self, other_object: Any, event: Event):
        for observer in self._observers[type(event)]:
            observer.on_notify(other_object, event)

    def create_rail(self, rails: Iterable[Rail]):
        self.rails.extend(rails)
        for rail in rails:
            self._notify_about_other_object(rail, CreateEvent())
        # TODO: encase in if statement
        # if rails:
        self._signal_controller.create_signal_blocks(self, list(self.signals.values()))

    def release_mouse_button(self):
        if all(rail.legal for rail in self.rails_being_built):
            self.create_rail(self.rails_being_built)
            self._try_create_stations()

        self.rails_being_built.clear()
        self.notify(RailsBeingBuiltEvent(self.rails_being_built))

    def get_station(self, x, y) -> Station | None:
        x, y = self.snap_to(x, y)
        return self.stations.get(Vec2(x, y))

    def _is_adjacent(self, position1: Vec2, position2: Vec2):
        dx = abs(position1.x - position2.x)
        dy = abs(position1.y - position2.y)
        return (
            GRID_BOX_SIZE * 3 / 4 < dx < GRID_BOX_SIZE * 5 / 4
            and dy < GRID_BOX_SIZE / 4
        ) or (
            GRID_BOX_SIZE * 3 / 4 < dy < GRID_BOX_SIZE * 5 / 4
            and dx < GRID_BOX_SIZE / 4
        )

    def adjacent_mines(self, position: Vec2) -> list[Mine]:
        return [
            mine
            for mine in self.mines.values()
            if self._is_adjacent(position, mine.position)
        ]

    def adjacent_factories(self, position: Vec2) -> list[Factory]:
        return [
            factory
            for factory in self.factories.values()
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

    def _create_station(self, position: Vec2, east_west: bool):
        """Creates a station in a location. Must be next to a mine or a factory, or it raises AssertionError.

        East-west if east_west == True, otherwise north-south."""
        mine_or_factory = self._adjacent_mine_or_factory(position)
        assert mine_or_factory
        station = Station(position, east_west)
        self.stations[position] = station
        self._notify_about_other_object(station, CreateEvent())

        return station

    def _try_create_stations(self):
        rails_from_position = defaultdict(list)
        for rail in self.rails:
            for position in rail.positions:
                rails_from_position[position].append(rail)
        for position, rails_at_position in rails_from_position.items():
            if (
                len(rails_at_position) == 2
                and (
                    all(rail.is_horizontal() for rail in rails_at_position)
                    or all(rail.is_vertical() for rail in rails_at_position)
                )
                and self._adjacent_mine_or_factory(position)
                and position not in self.stations
            ):
                self._create_station(
                    position,
                    east_west=all(rail.is_horizontal() for rail in rails_at_position),
                )

    def enlarge_grid(self):
        self.left -= GRID_BOX_SIZE
        self.bottom -= GRID_BOX_SIZE
        self.right += GRID_BOX_SIZE
        self.top += GRID_BOX_SIZE
        # self.drawer.create_grid(self.left, self.bottom, self.right, self.top)
        self._create_in_random_unoccupied_location(Factory)
        self._create_in_random_unoccupied_location(Mine)

    def _two_rails_at_position(self, position: Vec2) -> tuple[Rail, Rail] | None:
        rails = self.rails_at_position(position)
        match rails:
            case (rail1, rail2):
                return (rail1, rail2)
            case _:
                return None

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
        return closest_rail if distance < GRID_BOX_SIZE else None

    def create_signals_at_click_position(self, click_x, click_y):
        # Transpose half a box since rail coordinates are in the bottom left
        # of each grid cell while they are visible in the middle
        x = click_x - GRID_BOX_SIZE / 2
        y = click_y - GRID_BOX_SIZE / 2
        return self.create_signals_at_grid_position(x, y)

    def create_signals_at_grid_position(self, x, y) -> list[Signal]:
        signals = []
        if rail := self._closest_rail(x, y):
            for position in rail.positions:
                signal = Signal(position, rail)
                self.signals[(position, rail)] = signal
                self._notify_about_other_object(signal, CreateEvent())
                signals.append(signal)
        self._signal_controller.create_signal_blocks(self, list(self.signals.values()))
        return signals
