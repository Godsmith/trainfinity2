from dataclasses import dataclass, field
from typing import Any, Callable, Iterable
from trainfinity2.grid import Grid
from trainfinity2.model import CargoType, Rail, Station
from pyglet.math import Vec2


def _create_buildings(
    lines: list[str],
    building_character: str,
    create_method: Callable[..., Any],
    extra_args: list[Any] | None = None,
):
    extra_args = extra_args or []
    for row_number, row in list(enumerate(lines))[::2]:
        for column_number, character in list(enumerate(row))[::2]:
            if character == building_character:
                args = [Vec2(column_number / 2, row_number / 2), *extra_args]
                create_method(*args)


def _create_rails(grid: Grid, lines: list[str]):
    for row_number, row in enumerate(lines):
        for column_number, character in enumerate(row):
            x1_diff = y1_diff = x2_diff = y2_diff = 0
            if character in "-h":
                x1_diff = -1
                x2_diff = 1
            elif character in "|v":
                y1_diff = -1
                y2_diff = 1
            elif character == "/":
                x1_diff = -1
                y1_diff = -1
                x2_diff = 1
                y2_diff = 1
            elif character == "\\":
                x1_diff = 1
                y1_diff = -1
                x2_diff = -1
                y2_diff = 1
            x1 = (column_number + x1_diff) // 2
            y1 = (row_number + y1_diff) // 2
            x2 = (column_number + x2_diff) // 2
            y2 = (row_number + y2_diff) // 2

            if character in "-h|v/\\":
                grid.create_rail({Rail(x1, y1, x2, y2)})
            if character in "hv":
                grid.toggle_signals_at_grid_position(abs(x1 + x2) / 2, abs(y1 + y2) / 2)


def _remove_offset(lines: Iterable[str]):
    non_empty_lines = [line for line in lines if line.strip()]
    number_of_beginning_spaces = min(
        len(line) - len(line.lstrip()) for line in non_empty_lines
    )
    return [line[number_of_beginning_spaces:] for line in lines]


@dataclass
class StationCreator:
    """Creates stations from sets of positions. Adjacent positions are clumped into
    one large station."""

    grid: Grid
    east_west: bool
    _positions: set[Vec2] = field(default_factory=set)
    _sets_of_positions: list[set[Vec2]] = field(default_factory=list)

    def add(self, position: Vec2):
        self._positions.add(position)

    def create_stations(self):
        self._sets_of_positions = []
        for position in self._positions:
            self._add_to_set_of_positions(position)
        for set_of_positions in self._sets_of_positions:
            self.grid._create_station(
                Station(
                    positions=tuple(sorted(set_of_positions)), east_west=self.east_west
                )
            )

    def _add_to_set_of_positions(self, position: Vec2):
        for set_of_positions in self._sets_of_positions:
            for other_position in set_of_positions:
                if self._is_adjacent(other_position, position):
                    set_of_positions.add(position)
                    return
        self._sets_of_positions.append({position})

    @staticmethod
    def _is_adjacent(pos1: Vec2, pos2: Vec2) -> bool:
        return (pos1.x == pos2.x and abs(pos1.y - pos2.y) == 1) or (
            pos1.y == pos2.y and abs(pos1.x - pos2.x) == 1
        )


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

    _create_buildings(lines, "M", grid.create_mine, [CargoType.IRON])
    _create_buildings(lines, "C", grid.create_mine, [CargoType.COAL])
    _create_buildings(lines, "F", grid._create_factory)

    east_west_station_creator = StationCreator(grid, east_west=True)
    north_south_station_creator = StationCreator(grid, east_west=False)
    _create_buildings(lines, "S", east_west_station_creator.add)
    _create_buildings(lines, "s", north_south_station_creator.add)
    east_west_station_creator.create_stations()
    north_south_station_creator.create_stations()

    _create_rails(grid, lines)
