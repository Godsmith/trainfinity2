from pyglet.math import Vec2
from typing import Protocol
import typing

if typing.TYPE_CHECKING:
    from trainfinity2.model import Rail  # pragma: no cover


class RailCollection(Protocol):
    rails: set["Rail"]

    def rails_at_position(self, position: Vec2) -> set["Rail"]:
        raise NotImplementedError
