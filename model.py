from collections import namedtuple
from dataclasses import dataclass, field

from pyglet.math import Vec2

Mine = namedtuple("Mine", "x y")
Factory = namedtuple("Factory", "x y")
Station = namedtuple("Station", "x y")


@dataclass
class Train:
    first_station: Station
    second_station: Station
    route: list[Vec2]
    x: float = field(init=False)
    y: float = field(init=False)
    target_x: int = field(init=False)
    target_y: int = field(init=False)
    current_target_route_index: int = field(init=False)

    def __post_init__(self):
        self.x = self.first_station.x
        self.y = self.first_station.y
        self.target_x = self.route[1].x
        self.target_y = self.route[1].y
        self.current_target_route_index = 1
        self.route = self.route + self.route[-2:0:-1]

    def select_next_position_in_route(self):
        self.current_target_route_index += 1
        self.current_target_route_index %= len(self.route)
        self.target_x = self.route[self.current_target_route_index].x
        self.target_y = self.route[self.current_target_route_index].y


@dataclass
class Rail:
    x1: int
    y1: int
    x2: int
    y2: int

    def is_horizontal(self):
        return self.y1 == self.y2

    def is_vertical(self):
        return self.x1 == self.x2
