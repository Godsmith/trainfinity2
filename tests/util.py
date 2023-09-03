from typing import Any, Callable, Iterable
from trainfinity2.constants import GRID_BOX_SIZE
from trainfinity2.grid import Grid
from trainfinity2.model import Rail, Station
from pyglet.math import Vec2


def _coordinates(row_number: int, column_number: int):
    # assert row_number % 2 == 0
    # assert column_number % 2 == 0
    return (int(column_number / 2 * GRID_BOX_SIZE), int(row_number / 2 * GRID_BOX_SIZE))


def _create_buildings(
    lines: list[str],
    building_character: str,
    create_method: Callable[[Vec2], Any],
):
    for row_number, row in enumerate(lines):
        for column_number, character in enumerate(row):
            if column_number % 2 == 0 and row_number % 2 == 0:
                x, y = _coordinates(row_number, column_number)
                if character == building_character:
                    create_method(Vec2(x, y))


def _create_rails(grid: Grid, lines: list[str]):
    for row_number, row in enumerate(lines):
        for column_number, character in enumerate(row):
            x1 = y1 = x2 = y2 = 0  # To avoid unbound warning
            if character in "-h":
                x1, y1 = _coordinates(row_number, column_number - 1)
                x2, y2 = _coordinates(row_number, column_number + 1)
                grid.create_rail({Rail(x1, y1, x2, y2)})
            elif character in "|v":
                x1, y1 = _coordinates(row_number - 1, column_number)
                x2, y2 = _coordinates(row_number + 1, column_number)
                grid.create_rail({Rail(x1, y1, x2, y2)})
            elif character == "/":
                x1, y1 = _coordinates(row_number - 1, column_number - 1)
                x2, y2 = _coordinates(row_number + 1, column_number + 1)
                grid.create_rail({Rail(x1, y1, x2, y2)})
            elif character == "\\":
                x1, y1 = _coordinates(row_number - 1, column_number + 1)
                x2, y2 = _coordinates(row_number + 1, column_number - 1)
                grid.create_rail({Rail(x1, y1, x2, y2)})
            if character in "hv":
                grid.create_signals_at_grid_position(abs(x1 + x2) / 2, abs(y1 + y2) / 2)


def _remove_offset(lines: Iterable[str]):
    non_empty_lines = [line for line in lines if line.strip()]
    number_of_beginning_spaces = min(
        len(line) - len(line.lstrip()) for line in non_empty_lines
    )
    return [line[number_of_beginning_spaces:] for line in lines]


def create_station_method(grid: Grid, east_west: bool) -> Callable[[Vec2], None]:
    def inner(position: Vec2):
        grid._create_station(Station(positions=(position,), east_west=east_west))

    return inner


def create_objects(grid: Grid, map_: str):
    """Create objects in game from a map string

    Objects this does not support, since there are currently no way to express them,
    and therefore has to be created separately if needed:
      - Trains
      - Signals on diagonal rail

    Objects that could be supported, but currently are not:
      - Rails formed as an X
    """
    map_without_empty_lines_at_the_end = map_.rstrip(" \n")
    lines = map_without_empty_lines_at_the_end.splitlines()
    lines.reverse()  # Reverse to get row indices to match with coordinates
    lines = _remove_offset(lines)
    _create_buildings(lines, "M", grid._create_mine)
    _create_buildings(lines, "F", grid._create_factory)
    _create_buildings(lines, "S", create_station_method(grid, east_west=True))
    _create_buildings(lines, "s", create_station_method(grid, east_west=False))
    _create_rails(grid, lines)
