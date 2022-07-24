from collections import defaultdict
from itertools import pairwise
from typing import Optional
from pyglet.math import Vec2
from constants import GRID_BOX_SIZE, GRID_WIDTH, GRID_HEIGHT, WATER_TILES
from drawer import Drawer
from model import Mine, Factory, Rail, Station, Water
import math
import random


def positions_between(start: Vec2, end: Vec2):
    positions = [start]
    while positions[-1] != end:
        current = positions[-1]
        abs_dx = abs(current.x - end.x)
        abs_dy = abs(current.y - end.y)
        x_step = (end.x - current.x) / abs_dx if abs_dx else 0
        y_step = (end.y - current.y) / abs_dy if abs_dy else 0
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


class Grid:
    def __init__(self, drawer: Drawer) -> None:
        self.drawer = drawer

        self.water = {}
        self.mines = {}
        self.factories = {}
        self.stations = {}
        self.rails_being_built = []
        self.rails = []

        self._create_water()
        self._create_mines()
        self._create_factories()

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
        unoccupied_positions = set()
        while len(unoccupied_positions) < count:
            position = get_random_position()
            if position not in self.occupied_positions:
                unoccupied_positions.add(position)
        return unoccupied_positions

    def _get_unoccupied_position(self) -> Vec2:
        return self._get_unoccupied_positions(1).pop()

    def _create_water(self):
        water_tiles = {
            position: Water(*position)
            for position in self._get_unoccupied_positions(WATER_TILES)
        }
        for water in water_tiles.values():
            self.drawer.create_water(water)
        return water_tiles

    def _create_mines(self):
        position = self._get_unoccupied_position()
        mine = Mine(*position)
        self.drawer.create_mine(mine)
        return {position: mine}

    def _create_factories(self):
        position = self._get_unoccupied_position()
        factory = Factory(*get_random_position())
        self.drawer.create_factory(factory)
        return {position: factory}

    def snap_to(self, x, y) -> tuple[int, int]:
        return self.snap_to_x(x), self.snap_to_y(y)

    def snap_to_x(self, x) -> int:
        return math.floor(x / GRID_BOX_SIZE) * GRID_BOX_SIZE

    def snap_to_y(self, y) -> int:
        return math.floor(y / GRID_BOX_SIZE) * GRID_BOX_SIZE

    def connect_stations(self, station1: Station, station2: Station):
        self.rails_from_vec2 = defaultdict(list)
        for rail in self.rails:
            self.rails_from_vec2[Vec2(rail.x1, rail.y1)].append(rail)
            self.rails_from_vec2[Vec2(rail.x2, rail.y2)].append(rail)
        return self._explore([Vec2(station1.x, station1.y)], station2)

    def _explore(
        self, previous_locations: list[Vec2], target_station: Station
    ) -> Optional[list[Vec2]]:
        if (
            previous_locations[-1].x == target_station.x
            and previous_locations[-1].y == target_station.y
        ):
            return previous_locations
        next_locations = set()
        for rail in self.rails_from_vec2[previous_locations[-1]]:
            next_locations.add(Vec2(rail.x1, rail.y1))
            next_locations.add(Vec2(rail.x2, rail.y2))
        next_locations -= set(previous_locations)
        for next_location in next_locations:
            if route := self._explore(
                previous_locations + [next_location], target_station
            ):
                return route
        return None

    def _is_not_straight_horizontal_or_diagonal(self, xs, ys):
        return len(xs) != len(ys) and (
            (len(xs) > 1 and len(ys) != 1) or (len(ys) > 1 and len(xs) != 1)
        )

    def click_and_drag(self, x, y, start_x, start_y):
        x = self.snap_to_x(x)
        y = self.snap_to_y(y)
        start_x = self.snap_to_x(start_x)
        start_y = self.snap_to_y(start_y)

        self.rails_being_built = rails_between(Vec2(start_x, start_y), Vec2(x, y))
        self.drawer.set_rails_being_built(self.rails_being_built)

    def release_mouse_button(self):
        self.rails.extend(self.rails_being_built)
        self.drawer.create_rail(self.rails_being_built)
        self.rails_being_built.clear()

        self._add_stations()

    def get_station(self, x, y) -> Optional[Station]:
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

    def _is_adjacent_to_mine_or_factory(self, position):
        return any(
            self._is_adjacent(position, position2)
            for position2 in self.mines.keys() | self.factories.keys()
        )

    def _add_stations(self):
        rails_from_position = defaultdict(list)
        for rail in self.rails:
            rails_from_position[(rail.x1, rail.y1)].append(rail)
            rails_from_position[(rail.x2, rail.y2)].append(rail)

        for (x, y), rails in rails_from_position.items():
            if len(rails) == 2:
                if all(rail.is_horizontal() for rail in rails) or all(
                    rail.is_vertical() for rail in rails
                ):
                    # Checking for existing stations might not be needed later if
                    # building rail on top of rail will be prohibited.
                    if (
                        self._is_adjacent_to_mine_or_factory(Vec2(x, y))
                        and Vec2(x, y) not in self.stations
                    ):
                        station = Station(x, y)
                        self.stations[Vec2(x, y)] = station
                        self.drawer.create_station(station)
