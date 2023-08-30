from dataclasses import dataclass, replace
from enum import Enum, auto
from typing import Callable

from pyglet.math import Vec2

from .gui import Gui
from .observer import ChangeEvent, Event, Subject


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


@dataclass
class Station:
    position: Vec2
    east_west: bool = True


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

    def is_at_position(self, position: Vec2):
        x, y = position
        return (self.x1 == x and self.y1 == y) or (self.x2 == x and self.y2 == y)

    def other_end(self, x, y) -> Vec2:
        if self.x1 == x and self.y1 == y:
            return Vec2(self.x2, self.y2)
        if self.x2 == x and self.y2 == y:
            return Vec2(self.x1, self.y1)
        raise ValueError("The provided coordinates was not at either end of the rail.")

    @property
    def positions(self) -> set[Vec2]:
        return {Vec2(self.x1, self.y1), Vec2(self.x2, self.y2)}


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
