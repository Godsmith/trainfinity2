from typing import Any, Callable
from trainfinity2.grid import Grid
from trainfinity2.constants import GRID_BOX_SIZE
from trainfinity2.model import Rail
from trainfinity2.__main__ import MyGame


def _coordinates(row_number: int, column_number: int):
    assert row_number % 2 == 0
    assert column_number % 2 == 0
    return (int(column_number / 2 * GRID_BOX_SIZE), int(row_number / 2 * GRID_BOX_SIZE))


def _create_buildings(
    lines: list[str],
    building_character: str,
    create_method: Callable[[int, int], Any],
):
    for row_number, row in enumerate(lines):
        for column_number, character in enumerate(row):
            if column_number % 2 == 0 and row_number % 2 == 0:
                x, y = _coordinates(row_number, column_number)
                if character == building_character:
                    create_method(x, y)


def _create_rails(grid: Grid, lines: list[str]):
    for row_number, row in enumerate(lines):
        for column_number, character in enumerate(row):
            if character == "-":
                x1, y1 = _coordinates(row_number, column_number - 1)
                x2, y2 = _coordinates(row_number, column_number + 1)
                grid.create_rail([Rail(x1, y1, x2, y2)])
            elif character == "|":
                x1, y1 = _coordinates(row_number - 1, column_number)
                x2, y2 = _coordinates(row_number + 1, column_number)
                grid.create_rail([Rail(x1, y1, x2, y2)])
            elif character == "/":
                x1, y1 = _coordinates(row_number - 1, column_number - 1)
                x2, y2 = _coordinates(row_number + 1, column_number + 1)
                grid.create_rail([Rail(x1, y1, x2, y2)])
            elif character == "\\":
                x1, y1 = _coordinates(row_number - 1, column_number + 1)
                x2, y2 = _coordinates(row_number + 1, column_number - 1)
                grid.create_rail([Rail(x1, y1, x2, y2)])


def create_objects(game: MyGame, map_: str):
    lines = map_.splitlines()
    lines.reverse()  # Reverse to get row indices to match with coordinates
    _create_buildings(lines, "M", game.grid._create_mine)
    _create_buildings(lines, "F", game.grid._create_factory)
    _create_buildings(lines, "S", game.grid._create_station)
    _create_rails(game.grid, lines)
    _create_buildings(lines, "s", game._create_signal)
