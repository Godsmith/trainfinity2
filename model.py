import arcade
from collections import namedtuple
from dataclasses import dataclass, field, replace

from pyglet.math import Vec2

from constants import GRID_BOX_SIZE
from gui import Gui

Factory = namedtuple("Factory", "x y")
Water = namedtuple("Water", "x y")


@dataclass
class Mine:
    x: int
    y: int
    drawer: "Drawer"
    _iron: int = 0

    def add_iron(self):
        self._iron += 1
        self.drawer.add_iron((self.x, self.y))

    def remove_all_iron(self) -> int:
        iron = self._iron
        self._iron = 0
        self.drawer.remove_all_iron((self.x, self.y))
        return iron


def _is_close(pos1, pos2):
    return (
        abs(pos1.x - pos2.x) < GRID_BOX_SIZE / 2
        and abs(pos1.y - pos2.y) < GRID_BOX_SIZE / 2
    )


@dataclass
class Station:
    x: int
    y: int
    mine_or_factory: Mine | Factory


@dataclass
class Player:
    gui: Gui
    _score: int = 0

    @property
    def score(self) -> int:
        return self._score

    @score.setter
    def score(self, value):
        self._score = value
        self.gui.update_score(value)


@dataclass
class Train:
    player: Player
    first_station: Station
    second_station: Station
    route: list[Vec2]
    drawer: "Drawer"
    x: float = field(init=False)
    y: float = field(init=False)
    target_x: int = field(init=False)
    target_y: int = field(init=False)
    current_target_route_index: int = field(init=False)
    iron: int = 0

    def __post_init__(self):
        self.x = self.first_station.x
        self.y = self.first_station.y
        self.target_x = self.route[1].x
        self.target_y = self.route[1].y
        self.current_target_route_index = 1
        self.route = self.route + self.route[-2:0:-1]

    def _is_at_station(self) -> Station | None:
        for station in (self.first_station, self.second_station):
            if _is_close(self, station):
                return station

    def select_next_position_in_route(self):
        self.current_target_route_index += 1
        self.current_target_route_index %= len(self.route)
        self.target_x = self.route[self.current_target_route_index].x
        self.target_y = self.route[self.current_target_route_index].y

        if station := self._is_at_station():
            if isinstance(station.mine_or_factory, Mine):
                self.iron += station.mine_or_factory.remove_all_iron()
            else:
                # Factory
                self.player.score += self.iron
                self.iron = 0


@dataclass(frozen=True)
class Rail:
    x1: int
    y1: int
    x2: int
    y2: int
    legal: bool = True  # Whether a rail tile that is currently being built can be built

    def is_horizontal(self):
        return self.y1 == self.y2

    def is_vertical(self):
        return self.x1 == self.x2

    def to_illegal(self):
        return replace(self, legal=False)

    def is_at_position(self, x, y):
        return (self.x1 == x and self.y1 == y) or (self.x2 == x and self.y2 == y)
