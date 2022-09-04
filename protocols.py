from typing import Protocol
import typing

if typing.TYPE_CHECKING:
    from model import Rail


class GridEnlarger(Protocol):
    def enlarge_grid(self):
        raise NotImplementedError


class RailCollection(Protocol):
    rails: list["Rail"]

    def rails_at_position(self, x, y) -> set["Rail"]:
        raise NotImplementedError
