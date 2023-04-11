from pyglet.math import Vec2
from typing import Protocol
import typing

if typing.TYPE_CHECKING:
    from model import Rail  # pragma: no cover


class GridEnlarger(Protocol):
    def enlarge_grid(self):
        raise NotImplementedError


class RailCollection(Protocol):
    rails: list["Rail"]

    def rails_at_position(self, position: Vec2) -> set["Rail"]:
        raise NotImplementedError
