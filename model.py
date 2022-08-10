from collections import namedtuple
from dataclasses import dataclass, field, replace
from itertools import pairwise
from typing import TYPE_CHECKING, Iterable

from pyglet.math import Vec2

from constants import GRID_BOX_SIZE
from gui import Gui
from protocols import GridEnlarger, IronDrawer
from destroy_notifier import DestroyNotifier, Destroyable

Factory = namedtuple("Factory", "x y")
Water = namedtuple("Water", "x y")

MAX_IRON_AT_MINE = 8


@dataclass
class Mine:
    x: int
    y: int
    iron_drawer: IronDrawer
    iron: int = 0

    def add_iron(self):
        if self.iron < MAX_IRON_AT_MINE:
            self.iron += 1
            self.iron_drawer.add_iron((self.x, self.y))

    def remove_iron(self, amount) -> int:
        amount_taken = amount if amount <= self.iron else self.iron
        self.iron -= amount_taken
        self.iron_drawer.remove_iron((self.x, self.y), amount_taken)
        return amount_taken


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


Building = Mine | Factory | Station


def get_level_scores() -> list[int]:
    """
    The number of points required to reach a certain level.
    - Level 0: 0 points
    - Level 1: 10 points
    - Level 2: 30 points
    - ...
    """
    score_increase = 10
    scores = [0]
    for _ in range(1000):
        scores.append(scores[-1] + score_increase)
        score_increase += 10
    return scores


@dataclass
class Player:
    gui: Gui
    grid_enlarger: GridEnlarger
    _score: int = 0
    _level = 0

    LEVELS = get_level_scores()

    def score_to_grid_increase(self):
        return self.LEVELS[self._level + 1] - self._score

    @property
    def score(self) -> int:
        return self._score

    @score.setter
    def score(self, value):
        self._score = value
        while self._score >= self.LEVELS[self._level + 1]:
            self._level += 1
            self.grid_enlarger.enlarge_grid()
        self.gui.update_score(value, self._level, self.score_to_grid_increase())


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

    def is_at_station(self, station: Station):
        return self.is_at_position(station.x, station.y)

    def other_end(self, x, y) -> Vec2:
        if self.x1 == x and self.y1 == y:
            return Vec2(self.x2, self.y2)
        if self.x2 == x and self.y2 == y:
            return Vec2(self.x1, self.y1)
        raise ValueError("The provided coordinates was not at either end of the rail.")

    @property
    def positions(self) -> set[Vec2]:
        return {Vec2(self.x1, self.y1), Vec2(self.x2, self.y2)}

    def destroy(self):
        DestroyNotifier.destroyable_is_destroyed(self)


@dataclass
class Train:
    player: Player
    first_station: Station
    second_station: Station
    rails: list[Rail]
    x: float = field(init=False)
    y: float = field(init=False)
    target_x: int = field(init=False)
    target_y: int = field(init=False)
    current_target_route_index: int = field(init=False)
    iron: int = 0
    selected = False

    TRAIN_SPEED_PIXELS_PER_SECOND = 120.0  # 60.0

    def __post_init__(self):
        self.x = self.first_station.x
        self.y = self.first_station.y
        self.current_target_route_index = 1
        route = list(self._route_from_rails())
        self.target_x = route[1].x
        self.target_y = route[1].y
        self._route = route + route[-2:0:-1]
        for rail in self.rails:
            DestroyNotifier.register_observer(self, rail)

    def _route_from_rails(self) -> Iterable[Vec2]:
        for rail1, rail2 in pairwise(self.rails):
            yield (rail1.positions - rail2.positions).pop()
        yield self.rails[-1].positions.intersection(self.rails[-2].positions).pop()
        yield (self.rails[-1].positions - self.rails[-2].positions).pop()

    def move(self, delta_time):
        train_displacement = delta_time * self.TRAIN_SPEED_PIXELS_PER_SECOND

        if self.x > self.target_x + train_displacement:
            self.x -= train_displacement
        elif self.x < self.target_x - train_displacement:
            self.x += train_displacement
        if self.y > self.target_y + train_displacement:
            self.y -= train_displacement
        elif self.y < self.target_y - train_displacement:
            self.y += train_displacement
        if (
            abs(self.x - self.target_x) < train_displacement
            and abs(self.y - self.target_y) < train_displacement
        ):
            self._select_next_position_in_route()

    def is_at(self, x, y):
        return (
            self.x < x < self.x + GRID_BOX_SIZE and self.y < y < self.y + GRID_BOX_SIZE
        )

    def _is_at_station(self) -> Station | None:
        for station in (self.first_station, self.second_station):
            if _is_close(self, station):
                return station

    def _select_next_position_in_route(self):
        self.current_target_route_index += 1
        self.current_target_route_index %= len(self._route)
        self.target_x = self._route[self.current_target_route_index].x
        self.target_y = self._route[self.current_target_route_index].y

        if station := self._is_at_station():
            if isinstance(station.mine_or_factory, Mine):
                self.iron += station.mine_or_factory.remove_iron(1)
            else:
                # Factory
                self.player.score += self.iron
                self.iron = 0

    def destroyable_is_destroyed(self, destroyable: Destroyable):
        # Has to be rail since it is not observing anything else
        self.destroy()

    def destroy(self):
        DestroyNotifier.destroyable_is_destroyed(self)

    def is_colliding_with(self, train):
        return (
            abs(self.x - train.x) < GRID_BOX_SIZE / 2
            and abs(self.y - train.y) < GRID_BOX_SIZE / 2
        )
