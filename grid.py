from dataclasses import dataclass
import math
import random
from collections import defaultdict
from itertools import pairwise
from typing import Any, Iterable, Type
from route_finder import find_route


from pyglet.math import Vec2

from constants import GRID_BOX_SIZE, GRID_HEIGHT, GRID_WIDTH, WATER_TILES
from model import (
    Factory,
    Mine,
    Rail,
    Signal,
    SignalConnection,
    Station,
    Water,
    SignalColor,
)
from gui import Mode
from observer import CreateEvent, DestroyEvent, Event, Subject
from terrain import Terrain
from signal_controller import SignalController


@dataclass
class RailsBeingBuiltEvent(Event):
    rails: Iterable[Rail]


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
        self.signals: dict[Vec2, Signal] = {}
        self.rails_being_built = []
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
            self.water[position] = Water(*position)

    @property
    def occupied_positions(self) -> set[Vec2]:
        return (
            self.water.keys()
            | self.mines.keys()
            | self.factories.keys()
            | self.stations.keys()
            | self.signals.keys()
        )

    def _get_unoccupied_positions(self, count: int) -> set[Vec2]:
        """Gets <count> positions without water, mines, factories or stations. Ignores rails."""
        unoccupied_positions = set()
        while len(unoccupied_positions) < count:
            position = get_random_position()
            if position not in self.occupied_positions:
                unoccupied_positions.add(position)
        return unoccupied_positions

    def _get_unoccupied_position(self) -> Vec2:
        return self._get_unoccupied_positions(1).pop()

    def _create_mine(self, x, y):
        mine = Mine(x, y)
        self.mines[Vec2(x, y)] = mine
        self._notify_about_other_object(mine, CreateEvent())
        return mine

    def _create_mine_in_random_unoccupied_location(self):
        x, y = self._get_unoccupied_position()
        self._create_mine(x, y)

    def _create_mines(self):
        self._create_mine_in_random_unoccupied_location()

    def _create_factory(self, x, y):
        factory = Factory(x, y)
        self.factories[Vec2(x, y)] = factory
        self._notify_about_other_object(factory, CreateEvent())
        return factory

    def _create_factory_in_random_unoccupied_location(self):
        x, y = self._get_unoccupied_position()
        self._create_factory(x, y)

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

    def snap_to(self, x, y) -> tuple[int, int]:
        return self.snap_to_x(x), self.snap_to_y(y)

    def snap_to_x(self, x) -> int:
        return math.floor(x / GRID_BOX_SIZE) * GRID_BOX_SIZE

    def snap_to_y(self, y) -> int:
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
            Vec2(station1.x, station1.y),
            station2,
        )

    def rails_at_position(self, x, y):
        return {rail for rail in self.rails if rail.is_at_position(x, y)}

    def _is_red_signal(self, signal_position: Vec2, coming_from_rail: Rail):
        if signal := self.signals.get(signal_position):
            return signal.signal_color_coming_from(coming_from_rail) == SignalColor.RED
        return False

    def possible_next_rails_ignore_red_lights(
        self, position: Vec2, previous_rail: Rail | None
    ):
        return self.rails_at_position(*position) - {previous_rail}

    def possible_next_rails(self, position: Vec2, previous_rail: Rail | None):
        """Given a position and where the train came from, return a list of possible rails
        it can continue on.
        Current rules:
        1. The train cannot reverse, i.e. the output cannot contain `previous_rail`.
           (if previous_rail = None, the train is at a standstill, e.g. at a station)
        2. The train cannot go into a red light
        Possible future rules:
        3. The train cannot turn more than X degrees"""
        return {
            rail
            for rail in self.rails_at_position(*position)
            if not self._is_red_signal(rail.other_end(*position), rail)
        } - {previous_rail}

    def _rail_is_in_occupied_position(self, rail: Rail):
        return (
            Vec2(rail.x1, rail.y1) in self.occupied_positions
            or Vec2(rail.x2, rail.y2) in self.occupied_positions
        )

    def _rail_is_inside_grid(self, rail: Rail):
        return all(
            self._is_inside(x, y) for x, y in ((rail.x1, rail.y1), (rail.x2, rail.y2))
        )

    def _mark_illegal_rail(self, rails: Iterable[Rail]) -> list[Rail]:
        return [
            (
                rail.to_illegal()
                if self._rail_is_in_occupied_position(rail)
                or not self._rail_is_inside_grid(rail)
                else rail
            )
            for rail in rails
        ]

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
            self.remove_rail(x, y)

    def remove_rail(self, x, y):
        new_rails = []
        for rail in self.rails:
            if rail.is_at_position(x, y):
                self._notify_about_other_object(rail, DestroyEvent())
            else:
                new_rails.append(rail)
        self.rails = new_rails

        if Vec2(x, y) in self.stations:
            station = self.stations[Vec2(x, y)]
            self._notify_about_other_object(station, DestroyEvent())
            del self.stations[Vec2(x, y)]

        if Vec2(x, y) in self.signals:
            signal = self.signals[Vec2(x, y)]
            self._notify_about_other_object(signal, DestroyEvent())
            del self.signals[Vec2(x, y)]

        self._signal_controller.create_signal_blocks(self, self.signals)

    def _notify_about_other_object(self, other_object: Any, event: Event):
        for observer in self._observers[type(event)]:
            observer.on_notify(other_object, event)

    def _create_rail(self, rails: Iterable[Rail]):
        self.rails.extend(rails)
        for rail in rails:
            self._notify_about_other_object(rail, CreateEvent())
        self._signal_controller.create_signal_blocks(self, self.signals)

    def release_mouse_button(self):
        if all(rail.legal for rail in self.rails_being_built):
            self._create_rail(self.rails_being_built)
            self._create_stations()

        self.rails_being_built.clear()
        self.notify(RailsBeingBuiltEvent(self.rails_being_built))

    def get_station(self, x, y) -> Station | None:
        x, y = self.snap_to(x, y)
        return self.stations.get(Vec2(x, y))

    def _is_adjacent(self, position1, position2):
        return (
            abs(position1.x - position2.x) == GRID_BOX_SIZE
            and position1.y == position2.y
        ) or (
            abs(position1.y - position2.y) == GRID_BOX_SIZE
            and position1.x == position2.x
        )

    def _adjacent_mine_or_factory(self, position: Vec2) -> Mine | Factory | None:
        for mine in self.mines.values():
            if self._is_adjacent(position, Vec2(mine.x, mine.y)):
                return mine
        for factory in self.factories.values():
            if self._is_adjacent(position, Vec2(factory.x, factory.y)):
                return factory

    def _create_station(self, x, y):
        """Creates a station in a location. Must be next to a mine or a factory, or it raises AssertionError."""
        mine_or_factory = self._adjacent_mine_or_factory(Vec2(x, y))
        assert mine_or_factory
        station = Station(x, y, mine_or_factory)
        self.stations[Vec2(x, y)] = station
        self._notify_about_other_object(station, CreateEvent())

        return station

    def _create_stations(self):
        rails_from_position = defaultdict(list)
        for rail in self.rails:
            rails_from_position[rail.x1, rail.y1].append(rail)
            rails_from_position[rail.x2, rail.y2].append(rail)
        for (x, y), rails in rails_from_position.items():
            if (
                len(rails) == 2
                and (
                    all(rail.is_horizontal() for rail in rails)
                    or all(rail.is_vertical() for rail in rails)
                )
                and self._adjacent_mine_or_factory(Vec2(x, y))
                and Vec2(x, y) not in self.stations
            ):
                self._create_station(x, y)

    def enlarge_grid(self):
        self.left -= GRID_BOX_SIZE
        self.bottom -= GRID_BOX_SIZE
        self.right += GRID_BOX_SIZE
        self.top += GRID_BOX_SIZE
        # self.drawer.create_grid(self.left, self.bottom, self.right, self.top)
        self._create_in_random_unoccupied_location(Factory)
        self._create_in_random_unoccupied_location(Mine)

    def _two_rails_at_position(self, x, y) -> tuple[Rail, Rail] | None:
        rails = self.rails_at_position(x, y)
        return tuple(rails) if len(rails) == 2 else None

    def create_signal(self, x, y):
        x, y = self.snap_to(x, y)
        if rails := self._two_rails_at_position(x, y):
            signal = Signal(
                x,
                y,
                (
                    SignalConnection(
                        rails[0], rails[0].other_end(x, y), SignalColor.GREEN
                    ),
                    SignalConnection(
                        rails[1], rails[1].other_end(x, y), SignalColor.GREEN
                    ),
                ),
            )
            self.signals[Vec2(x, y)] = signal
            self._notify_about_other_object(signal, CreateEvent())
            self._signal_controller.create_signal_blocks(self, self.signals)
            return signal
