from grid import Grid
from constants import GRID_BOX_SIZE
from model import Rail


def _coordinates(row_number: int, column_number: int):
    assert row_number % 2 == 0
    assert column_number % 2 == 0
    return (int(row_number / 2 * GRID_BOX_SIZE), int(column_number / 2 * GRID_BOX_SIZE))


def create_grid_objects(grid: Grid, map_: str):
    lines = map_.splitlines()
    non_empty_lines = [line for line in lines if line]
    non_empty_lines.reverse()  # Reverse to get columns match up
    for row_number, row in enumerate(non_empty_lines):
        for column_number, character in enumerate(row):
            if column_number % 2 == 0 and row_number % 2 == 0:
                pass
                # Handle non rail objects
            else:
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
