from collections import defaultdict
from dataclasses import dataclass
from heapq import heappop, heappush
from typing import Callable, Iterable

from pyglet.math import Vec2

from .model import Rail, Station


@dataclass(frozen=True)
class _RailVector:
    """Models a single rail and a direction of movement: the position to where the
    train is going. Alternatively a position and the rail it used to go there."""

    position: Vec2
    rail: Rail | None

    def __lt__(self, other):
        return self.position < other.position


def find_route(
    possible_next_rails_method: Callable[[Vec2, Rail | None], Iterable[Rail]],
    starting_rails: set[Rail],
    initial_position: Vec2,
    target_station: Station,
    previous_rail: Rail | None = None,  # Assures the train can not just reverse
) -> list[Rail] | None:
    """Finds the shortest route (list of Rail) to the furthest end of a station.

    Returns an empty list if the train is already at the station.
    Returns None if no route can be found."""

    distance_from_railvector: dict[_RailVector, int] = defaultdict(lambda: 999999999)
    distance_from_railvector[_RailVector(initial_position, previous_rail)] = 0
    railvectors_in_shortest_route: list[_RailVector] = []
    visited_railvectors: set[_RailVector] = set()
    unvisited_railvectors: list[_RailVector] = [
        _RailVector(initial_position, previous_rail)
    ]
    first_iteration = True

    while unvisited_railvectors:
        current_railvector = heappop(unvisited_railvectors)
        visited_railvectors.add(current_railvector)

        if has_reached_end_of_target_station(
            current_railvector.position, current_railvector.rail, target_station
        ):
            return _route(
                current_railvector,
                railvectors_in_shortest_route,
                initial_position,
                starting_rails,
                target_station,
            )

        if first_iteration:
            possible_next_rails = starting_rails
            first_iteration = False
        else:
            previous_rail = current_railvector.rail
            possible_next_rails = possible_next_rails_method(
                current_railvector.position, previous_rail
            )
        for rail in possible_next_rails:
            adjacent_railvector = _RailVector(
                rail.other_end(*current_railvector.position), rail
            )
            if adjacent_railvector not in visited_railvectors:
                adjacent_distance = distance_from_railvector[current_railvector] + 1
                if distance_from_railvector[adjacent_railvector] > adjacent_distance:
                    distance_from_railvector[adjacent_railvector] = adjacent_distance
                    heappush(
                        unvisited_railvectors,
                        adjacent_railvector,
                    )
                    railvectors_in_shortest_route.append(adjacent_railvector)
    return None


def has_reached_end_of_target_station(
    position: Vec2, previous_rail: Rail | None, target_station: Station
):
    return position in {
        target_station.positions[0],
        target_station.positions[-1],
    } and (
        len(target_station.positions) == 1
        or previous_rail in target_station.internal_rail
    )


def _route(
    current_railvector: _RailVector,
    railvectors_in_shortest_route: list[_RailVector],
    initial_position: Vec2,
    starting_rails: set[Rail],
    target_station: Station,
):
    route: list[Rail] = []
    while True:
        rail = current_railvector.rail
        assert rail
        route.append(rail)
        next_position = rail.other_end(*current_railvector.position)

        if (
            next_position == initial_position
            and current_railvector.rail in starting_rails
        ):
            break

        current_railvector = [
            railvector
            for railvector in railvectors_in_shortest_route
            if railvector.position == next_position and railvector.rail != rail
        ][0]

    # Make sure that the train always goes to the furthest end of the station
    if not (set(route) & set(target_station.internal_rail)):
        route = list(reversed(target_station.internal_rail)) + route
    return route[::-1]
