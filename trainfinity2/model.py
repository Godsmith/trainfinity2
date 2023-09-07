from dataclasses import dataclass, replace
from enum import Enum, auto
import functools
from typing import Callable

from pyglet.math import Vec2

from itertools import pairwise

from .gui import Gui
from .observer import ChangeEvent, Event, Subject


@dataclass(frozen=True)
class Rail:
    x1: int
    y1: int
    x2: int
    y2: int
    legal: bool = True  # Whether a rail tile that is currently being built can be built

    def __eq__(self, other: object):
        if isinstance(other, Rail):
            return self.positions == other.positions
        return NotImplemented

    def __hash__(self) -> int:
        return hash(tuple(sorted(((self.x1, self.y1), (self.x2, self.y2)))))

    def is_horizontal(self):
        return self.y1 == self.y2

    def is_vertical(self):
        return self.x1 == self.x2

    def to_illegal(self):
        return replace(self, legal=False)

    def other_end(self, x, y) -> Vec2:
        if self.x1 == x and self.y1 == y:
            return Vec2(self.x2, self.y2)
        if self.x2 == x and self.y2 == y:
            return Vec2(self.x1, self.y1)
        raise ValueError("The provided coordinates was not at either end of the rail.")

    @functools.cached_property
    def positions(self) -> set[Vec2]:
        return {Vec2(self.x1, self.y1), Vec2(self.x2, self.y2)}


@dataclass
class Factory:
    position: Vec2


@dataclass
class Water:
    position: Vec2


MAX_IRON_AT_MINE = 8


@dataclass(frozen=True)
class IronAddedEvent(Event):
    position: Vec2


@dataclass(frozen=True)
class IronRemovedEvent(Event):
    position: Vec2
    amount: int


@dataclass
class Mine(Subject):
    position: Vec2
    iron: int = 0

    def __post_init__(self):
        super().__init__()

    def add_iron(self):
        if self.iron < MAX_IRON_AT_MINE:
            self.iron += 1
            self.notify(IronAddedEvent(self.position))

    def remove_iron(self, amount) -> int:
        amount_taken = amount if amount <= self.iron else self.iron
        self.iron -= amount_taken
        self.notify(IronRemovedEvent(self.position, amount_taken))
        return amount_taken


@dataclass(frozen=True)
class Station:
    positions: tuple[Vec2, ...]
    east_west: bool = True

    @functools.cached_property
    def positions_before_and_after(self) -> tuple[Vec2, Vec2]:
        if self.east_west:
            positions = sorted(self.positions, key=lambda position: position.x)
            return (
                Vec2(positions[0].x - 1, positions[0].y),
                Vec2(positions[-1].x + 1, positions[-1].y),
            )
        else:
            positions = sorted(self.positions, key=lambda position: position.y)
            return (
                Vec2(positions[0].x, positions[0].y - 1),
                Vec2(positions[-1].x, positions[-1].y + 1),
            )

    @functools.cached_property
    def internal_rail(self) -> list[Rail]:
        return [Rail(p1.x, p1.y, p2.x, p2.y) for p1, p2 in pairwise(self.positions)]

    @functools.cached_property
    def internal_and_external_rail(self) -> set[Rail]:
        if self.east_west:
            positions = sorted(self.positions, key=lambda position: position.x)
        else:
            positions = sorted(self.positions, key=lambda position: position.y)
        pos1 = self.positions_before_and_after[0]
        rail1 = Rail(pos1.x, pos1.y, positions[0].x, positions[0].y)
        pos2 = self.positions_before_and_after[1]
        rail2 = Rail(positions[-1].x, positions[-1].y, pos2.x, pos2.y)
        return {rail1, rail2}.union(self.internal_rail)


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
    enlarge_grid: Callable[[], None]
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
            self.enlarge_grid()
        self.gui.update_score(value, self._level, self.score_to_grid_increase())


class SignalColor(Enum):
    RED = auto()
    GREEN = auto()


@dataclass
class SignalConnection:
    rail: Rail
    towards_position: Vec2
    signal_color: SignalColor = SignalColor.GREEN


@dataclass(unsafe_hash=True)
class Signal(Subject):
    from_position: Vec2
    rail: Rail
    _signal_color: SignalColor = SignalColor.GREEN

    def __repr__(self):
        return f"Signal(from position {self.from_position} on {self.rail}: {self.signal_color})"

    def __post_init__(self):
        super().__init__()
        assert self.from_position in self.rail.positions  # For debug
        self._signal_color = SignalColor.GREEN

    @property
    def signal_color(self) -> SignalColor:
        return self._signal_color

    @signal_color.setter
    def signal_color(self, value: SignalColor):
        self._signal_color = value
        self.notify(ChangeEvent())
