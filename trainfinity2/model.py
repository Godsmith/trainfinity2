from abc import ABC
from collections import defaultdict
from dataclasses import dataclass, field, replace
from enum import Enum, auto
import functools
from typing import Callable, Sequence

from pyglet.math import Vec2

from itertools import pairwise

from .gui import Gui
from .events import CreateEvent, Event


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
class Water:
    position: Vec2


MAX_CARGO_AT_BUILDING = 8


class CargoType(Enum):
    COAL = auto()
    IRON = auto()
    STEEL = auto()
    TOOLS = auto()
    LOGS = auto()
    PLANKS = auto()


@dataclass(frozen=True)
class CargoAddedEvent(Event):
    position: Vec2
    type: CargoType


@dataclass(frozen=True)
class CargoRemovedEvent(Event):
    position: Vec2
    amount: int


@dataclass(frozen=True)
class CargoSoldEvent(Event):
    type: CargoType
    amount: int


@dataclass
class Recipe:
    output: set[CargoType] = field(default_factory=set)
    input: set[CargoType] = field(default_factory=set)


@dataclass
class Building(ABC):
    position: Vec2
    cargo_count: dict[CargoType, int] = field(default_factory=lambda: defaultdict(int))
    recipe: Recipe = field(init=False)

    @property
    def accepts(self) -> set[CargoType]:
        return self.recipe.input

    @property
    def produces(self) -> set[CargoType]:
        return self.recipe.output

    def try_create_cargo(self) -> Sequence[Event]:
        events = []
        if all(
            self.cargo_count[input_cargo] for input_cargo in self.recipe.input
        ) and all(
            self.cargo_count[output_cargo] <= MAX_CARGO_AT_BUILDING
            for output_cargo in self.recipe.output
        ):
            for input_cargo in self.recipe.input:
                self.cargo_count[input_cargo] -= 1
            for output_cargo in self.recipe.output:
                self.cargo_count[output_cargo] += 1
                events.append(CargoAddedEvent(self.position, output_cargo))
        return events

    def remove_cargo(self, type: CargoType, amount: int) -> CargoRemovedEvent:
        assert self.cargo_count[type] >= amount
        self.cargo_count[type] -= amount
        return CargoRemovedEvent(self.position, amount)

    def add_cargo(self, type: CargoType, amount: int) -> list[Event]:
        self.cargo_count[type] += amount
        return [CargoAddedEvent(self.position, type)]


@dataclass
class Market(Building):
    def __post_init__(self):
        self.recipe = Recipe(input={*CargoType})

    def add_cargo(self, type: CargoType, amount: int) -> list[Event]:
        self.cargo_count[type] += amount
        return [CargoSoldEvent(type, amount)]


@dataclass
class SteelWorks(Building):
    def __post_init__(self):
        self.recipe = Recipe(
            input={CargoType.COAL, CargoType.IRON}, output={CargoType.STEEL}
        )


@dataclass
class Workshop(Building):
    def __post_init__(self):
        self.recipe = Recipe(
            input={CargoType.STEEL, CargoType.PLANKS}, output={CargoType.TOOLS}
        )


@dataclass
class CoalMine(Building):
    def __post_init__(self):
        self.recipe = Recipe(output={CargoType.COAL})


@dataclass
class IronMine(Building):
    def __post_init__(self):
        self.recipe = Recipe(output={CargoType.IRON})


@dataclass
class Forest(Building):
    def __post_init__(self):
        self.recipe = Recipe(output={CargoType.LOGS})


@dataclass
class Sawmill(Building):
    def __post_init__(self):
        self.recipe = Recipe(input={CargoType.LOGS}, output={CargoType.PLANKS})


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


def get_level_scores() -> list[int]:
    """
    The number of points required to reach a certain level.
    - Level 1: 0 points
    - Level 2: 10 points
    - Level 3: 30 points
    - ...
    """
    score_increase = 10
    scores = [0, 0]
    for _ in range(1000):
        scores.append(scores[-1] + score_increase)
        score_increase += 10
    return scores


@dataclass
class Player:
    gui: Gui
    level_up_callback: Callable[[int], None]
    _score: int = 0
    _level = 0

    LEVELS = get_level_scores()

    def score_to_grid_increase(self):
        return self.LEVELS[self._level + 1] - self._score

    @property
    def money(self) -> int:
        return self._score

    @money.setter
    def money(self, value):
        self._score = value
        while self._score >= self.LEVELS[self._level + 1]:
            self.level_up()
        self.update_score_in_gui()

    def level_up(self):
        self._level += 1
        self.level_up_callback(self._level)

    def update_score_in_gui(self):
        self.gui.update_score(self._score, self._level, self.score_to_grid_increase())


class SignalColor(Enum):
    RED = auto()
    GREEN = auto()


@dataclass
class SignalConnection:
    rail: Rail
    towards_position: Vec2
    signal_color: SignalColor = SignalColor.GREEN


@dataclass(unsafe_hash=True)
class Signal:
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

    def set_signal_color(self, value: SignalColor) -> CreateEvent:
        self._signal_color = value
        return CreateEvent(self)
