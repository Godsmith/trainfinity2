from itertools import combinations
from typing import Iterable

from trainfinity2.model import Station
from pyglet.math import Vec2

from trainfinity2.util import positions_between


def _furthest_between(vecs: Iterable[Vec2]) -> tuple[Vec2, Vec2]:
    pair = (Vec2(0, 0), Vec2(0, 0))
    longest_distance = 0
    for vec1, vec2 in combinations(vecs, 2):
        if (distance := vec1.distance(vec2)) > longest_distance:
            longest_distance = distance
            pair = (vec1, vec2)
    return pair


def _station_between(start: Vec2, end: Vec2) -> Station:
    is_east_west = abs(start.x - end.x) >= abs(start.y - end.y)
    new_end = Vec2(end.x, start.y) if is_east_west else Vec2(start.x, end.y)
    return Station(tuple(positions_between(start, new_end)), east_west=is_east_west)


class StationBuilder:
    def get_station_being_built_and_replaced(
        self, stations: set[Station], x: int, y: int, start_x: int, start_y: int
    ) -> tuple[Station, Station | None]:
        if station := self._extends_station(stations, x, y, start_x, start_y):
            return (
                _station_between(
                    *_furthest_between(
                        [
                            *station.positions,
                            Vec2(x, y),
                            Vec2(start_x, start_y),
                        ]
                    )
                ),
                station,
            )
        return _station_between(Vec2(start_x, start_y), Vec2(x, y)), None

    def _extends_station(
        self, stations: set[Station], x: int, y: int, start_x: int, start_y: int
    ) -> Station | None:
        drag_positions = positions_between(Vec2(x, y), Vec2(start_x, start_y))
        for station in stations:
            if (station.east_west and y == start_y) or (
                not station.east_west and x == start_x
            ):
                if any(
                    drag_position in set(station.positions_before_and_after)
                    for drag_position in drag_positions
                ):
                    return station
        return None
