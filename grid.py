import math
import random
from collections import defaultdict
from itertools import pairwise, product
from typing import Iterable, Optional, Type
from perlin_noise import PerlinNoise

from pyglet.math import Vec2

from constants import GRID_BOX_SIZE, GRID_HEIGHT, GRID_WIDTH, WATER_TILES
from drawer import Drawer
from model import Factory, Mine, Rail, Station, Water
from gui import Mode


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
    def __init__(self, drawer: Drawer, terrain: bool) -> None:
        self.drawer = drawer

        self.water: dict[Vec2, Water] = {}
        self.mines: dict[Vec2, Mine] = {}
        self.factories = {}
        self.stations = {}
        self.rails_being_built = []
        self.rails = []

        self.left = 0
        self.bottom = 0
        self.right = GRID_WIDTH
        self.top = GRID_HEIGHT
        self.drawer.create_grid(self.left, self.bottom, self.right, self.top)

        if terrain:
            self._create_terrain()
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

    def _create_terrain(self):
        print("create_terrain in grid")
        sand = []
        mountains = []
        noise1 = PerlinNoise(octaves=3)
        noise2 = PerlinNoise(octaves=6)
        noise3 = PerlinNoise(octaves=12)
        noise4 = PerlinNoise(octaves=24)
        for x, y in product(
            range(-GRID_WIDTH * 2, GRID_WIDTH * 3 + 1, GRID_BOX_SIZE),
            range(-GRID_HEIGHT * 2, GRID_HEIGHT * 3 + 1, GRID_BOX_SIZE),
        ):
            noise_val = noise1([x / GRID_WIDTH, y / GRID_WIDTH])
            noise_val += 0.5 * noise2([x / GRID_WIDTH, y / GRID_WIDTH])
            noise_val += 0.25 * noise3([x / GRID_WIDTH, y / GRID_WIDTH])
            # noise_val += 0.125 * noise4([x / GRID_WIDTH, y / GRID_WIDTH])

            if noise_val < -0.1:
                self.water[Vec2(x, y)] = Water(x, y)
            elif noise_val < 0:
                sand.append(Vec2(x, y))
            elif noise_val > 0.4:
                mountains.append(Vec2(x, y))

        self.drawer.create_terrain(
            water=self.water.keys(), sand=sand, mountains=mountains
        )

    def _create_mine(self, x, y):
        mine = Mine(x, y, self.drawer)
        self.mines[Vec2(x, y)] = mine
        self.drawer.create_building(mine)
        return mine

    def _create_mine_in_random_unoccupied_location(self):
        x, y = self._get_unoccupied_position()
        self._create_mine(x, y)

    def _create_mines(self):
        self._create_mine_in_random_unoccupied_location()

    def _create_factory(self, x, y):
        factory = Factory(x, y)
        self.factories[Vec2(x, y)] = factory
        self.drawer.create_building(factory)
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
            self.drawer.show_rails_being_built(self.rails_being_built)
        elif mode == Mode.DESTROY:
            self.rails = [rail for rail in self.rails if not rail.is_at_position(x, y)]
            if Vec2(x, y) in self.stations:
                self.drawer.remove_building(self.stations[Vec2(x, y)])
                del self.stations[Vec2(x, y)]
            self.drawer.remove_rail((x, y))

    def _create_rail(self, rails: Iterable[Rail]):
        self.rails.extend(rails)
        self.drawer.create_rail(rails)

    def release_mouse_button(self):
        if all(rail.legal for rail in self.rails_being_built):
            self._create_rail(self.rails_being_built)
            self._create_stations()

        self.rails_being_built.clear()
        self.drawer.show_rails_being_built(self.rails_being_built)

    def get_station(self, x, y) -> Optional[Station]:
        print(x, y)
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
        self.drawer.create_building(station)
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
        self.drawer.create_grid(self.left, self.bottom, self.right, self.top)
        self._create_in_random_unoccupied_location(Factory)
        self._create_in_random_unoccupied_location(Mine)
