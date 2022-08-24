from typing import Protocol
import typing
from pyglet.math import Vec2

if typing.TYPE_CHECKING:
    from train import Train
    from model import Rail, Signal


class GridEnlarger(Protocol):
    def enlarge_grid(self):
        raise NotImplementedError


class TrainCollection(Protocol):
    trains: list["Train"]


class SignalCollection(Protocol):
    signals: dict[Vec2, "Signal"]


class RailCollection(Protocol):
    rails: list["Rail"]

    def rails_at_position(self, x, y) -> set["Rail"]:
        raise NotImplementedError
