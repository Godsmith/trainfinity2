from collections import defaultdict
from heapq import heappop, heappush
from typing import Callable, Iterable

from pyglet.math import Vec2

from .model import Rail, Station


def find_route(
    possible_next_rails_method: Callable[[Vec2, Rail | None], Iterable[Rail]],
    starting_rails: Iterable[Rail],
    initial_position: Vec2,
    target_station: Station,
    previous_rail: Rail | None = None,  # Assures the train can not just reverse
) -> list[Rail] | None:
    """Finds the shortest route (list of Rail) to a station from a specific station.

    Returns None if no route can be found."""

    if initial_position in {
        target_station.positions[0],
        target_station.positions[-1],
    } and (
        previous_rail in target_station.internal_rail
        or len(target_station.positions) == 1
    ):
        return []
    distance_at_position = defaultdict(lambda: 999999999)
    distance_at_position[initial_position] = 0
    rail_in_shortest_route_from_position: dict[Vec2, Rail] = {}
    visited_positions = set()
    unvisited_position_distances_and_positions = [(0, initial_position)]
    first_iteration = True

    while unvisited_position_distances_and_positions:
        _, current_position = heappop(unvisited_position_distances_and_positions)
        visited_positions.add(current_position)
        if current_position == target_station.positions[0]:
            route: list[Rail] = []
            while current_position != initial_position:
                rail = rail_in_shortest_route_from_position[current_position]
                route.append(rail)
                current_position = rail.other_end(*current_position)
            # Make sure that the train always goes to the furthest end of the station
            if not (set(route) & set(target_station.internal_rail)):
                route = list(reversed(target_station.internal_rail)) + route
            return route[::-1]

        if first_iteration:
            possible_next_rails = starting_rails
            first_iteration = False
        else:
            possible_next_rails = possible_next_rails_method(
                current_position, previous_rail
            )
        for rail in possible_next_rails:
            adjacent_position = rail.other_end(*current_position)
            if adjacent_position not in visited_positions:
                adjacent_distance = distance_at_position[current_position] + 1
                if distance_at_position[adjacent_position] > adjacent_distance:
                    distance_at_position[adjacent_position] = adjacent_distance
                    heappush(
                        unvisited_position_distances_and_positions,
                        (adjacent_distance, adjacent_position),
                    )
                    rail_in_shortest_route_from_position[adjacent_position] = rail
    return None
