from collections import namedtuple
from dataclasses import dataclass, replace
from enum import Enum, auto

from pyglet.math import Vec2

from .gui import Gui
from .observer import ChangeEvent, Event, Subject
from .protocols import GridEnlarger

Factory = namedtuple("Factory", "x y")
Water = namedtuple("Water", "x y")

MAX_IRON_AT_MINE = 8


@dataclass(frozen=True)
class IronAddedEvent(Event):
    x: int
    y: int


@dataclass(frozen=True)
class IronRemovedEvent(Event):
    x: int
    y: int
    amount: int


@dataclass
class Mine(Subject):
    x: int
    y: int
    iron: int = 0

    def __post_init__(self):
        super().__init__()

    def add_iron(self):
        if self.iron < MAX_IRON_AT_MINE:
            self.iron += 1
            self.notify(IronAddedEvent(self.x, self.y))

    def remove_iron(self, amount) -> int:
        amount_taken = amount if amount <= self.iron else self.iron
        self.iron -= amount_taken
        self.notify(IronRemovedEvent(self.x, self.y, amount_taken))
        return amount_taken


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
    x: int
    y: int
    connections: tuple[SignalConnection, SignalConnection]

    def __post_init__(self):
        super().__init__()

    # @property
    # def position(self):
    #     return Vec2(self.x, self.y)

    # @property
    # def rails(self):
    #     return {connection.rail for connection in self.connections}

    def _connection_from_rail(self, rail: Rail):
        return [
            connection for connection in self.connections if connection.rail == rail
        ][0]

    def set_signal_color(self, rail: Rail, color: SignalColor):
        # if connection.signal_color != color:
        self._connection_from_rail(rail).signal_color = color
        self.notify(ChangeEvent())

    def other_rail(self, rail: Rail):
        if rail == self.connections[0].rail:
            return self.connections[1].rail
        elif rail == self.connections[1].rail:
            return self.connections[0].rail
        else:
            raise ValueError(f"Signal {self} is not next to rail {rail}")

    def signal_color_coming_from(self, rail: Rail):
        return self._connection_from_rail(rail).signal_color
