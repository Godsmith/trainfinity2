from collections import deque
from dataclasses import dataclass, field

from math import pi
import math
from typing import Callable, Sequence
from pyglet.math import Vec2

from trainfinity2.events import Event


from .grid import Grid
from .model import Building, Rail, CargoType, Station
from .wagon import Wagon
from .route_finder import find_route, has_reached_end_of_target_station
from .signal_controller import SignalController
from typing import NamedTuple


def approx_equal(a: float, b: float):
    return abs(a - b) < 1.0


class PointAndAngle(NamedTuple):
    point: Vec2
    angle: float


def _find_equidistant_points_and_angles_along_line(
    line_points: Sequence[Vec2], n: int, distance: float
) -> list[PointAndAngle]:
    """Returns n positions with equal distance along the provided line set of positions.

    If the provided line is not long enough for the number of points requested, all
    remaining points returned will be at the end of the line."""

    line_points = deque(line_points)
    current_position = line_points.popleft()
    equidistant_points_and_angles: list[PointAndAngle] = []
    distance_left_to_next_equidistant_point = distance
    while len(equidistant_points_and_angles) < n:
        if not line_points:
            equidistant_points_and_angles.append(PointAndAngle(current_position, 0.0))
        else:
            distance_to_next_line_point = current_position.distance(line_points[0])
            if distance_to_next_line_point > distance_left_to_next_equidistant_point:
                equidistant_point = current_position.lerp(
                    line_points[0],
                    distance_left_to_next_equidistant_point
                    / distance_to_next_line_point,
                )
                angle = -(
                    (equidistant_point - current_position).heading * 360 / 2 / pi - 90
                )
                equidistant_points_and_angles.append(
                    PointAndAngle(equidistant_point, angle)
                )
                current_position = equidistant_point
                distance_left_to_next_equidistant_point = distance
            else:
                current_position = line_points.popleft()
                distance_left_to_next_equidistant_point -= distance_to_next_line_point
    return equidistant_points_and_angles


@dataclass
class Train:
    first_station_position: Vec2
    second_station_position: Vec2
    grid: Grid
    signal_controller: SignalController
    x: float = field(init=False)
    y: float = field(init=False)
    target_x: float = field(init=False)
    target_y: float = field(init=False)
    current_rail: Rail | None = None
    wagons: list[Wagon] = field(init=False)
    selected = False
    wait_timer: float = 0.0
    angle: float = 0
    speed: float = 0.0  # Cells per second

    MAX_SPEED = 4.0  # 60.0  # Cells per second
    ACCELERATION = 1.3  # Cells per second squared

    def __post_init__(self):
        super().__init__()
        self.x = self.first_station_position.x
        self.y = self.first_station_position.y
        self.target_x = self.x
        self.target_y = self.y
        self._target_station = self.grid.station_from_position[
            self.first_station_position
        ]
        self._rails_on_route: list[Rail] | None = []
        self._previous_targets_y = []

        # The position history needs to be approximately as long as the train,
        # since it is used for reserving positions. As long as one wagon is
        # approximately as long as a block, this will do.
        self._position_history: deque[Vec2] = deque(maxlen=1)
        self.wagons = []
        # add_wagon also extends the position history
        self.add_wagon()

        self._run_after_wait: Callable[[], list[Event]] | None = None

    @property
    def rails_on_route(self):
        return self._rails_on_route

    def move(self, delta_time) -> list[Event]:
        if self.wait_timer > 0:
            self.wait_timer -= delta_time
            return []

        if self._run_after_wait:
            events = self._run_after_wait()
            self._run_after_wait = None
            return events

        if self.speed < self.MAX_SPEED:
            self.speed += self.ACCELERATION * delta_time
            self.speed = min(self.speed, self.MAX_SPEED)

        pixels_to_move = delta_time * self.speed
        dx = 0.0
        dy = 0.0
        if self.x > self.target_x + pixels_to_move:
            dx = -pixels_to_move
        elif self.x < self.target_x - pixels_to_move:
            dx = pixels_to_move
        if self.y > self.target_y + pixels_to_move:
            dy = -pixels_to_move
        elif self.y < self.target_y - pixels_to_move:
            dy = pixels_to_move

        if approx_equal(self.angle % 90.0, 45.0):
            dx /= math.sqrt(2)
            dy /= math.sqrt(2)

        self.x += dx
        self.y += dy

        wagon_positions_and_angles = _find_equidistant_points_and_angles_along_line(
            [Vec2(self.x, self.y)] + list(self._position_history),
            len(self.wagons),
            1.0,
        )
        for wagon, (wagon_position, wagon_angle) in zip(
            self.wagons, wagon_positions_and_angles
        ):
            wagon.x, wagon.y = wagon_position
            wagon.angle = wagon_angle

        if (
            abs(self.x - self.target_x) < pixels_to_move
            and abs(self.y - self.target_y) < pixels_to_move
        ):
            return self._on_reached_target()
        return []

    def is_close_enough_to_click(self, x, y):
        return self.x - 1 <= x <= self.x + 1 and self.y - 1 <= y <= self.y + 1

    def destroy(self):
        self.signal_controller.reserve(id(self), set())

    def is_colliding_with(self, train):
        return abs(self.x - train.x) < 0.25 and abs(self.y - train.y) < 0.25

    def _can_reserve_position(self, position: Vec2) -> bool:
        return self.signal_controller.reserver(position) in {id(self), None}

    def _stop_at_station(self, current_station: Station) -> list[Event]:
        # Check factories before mines, or a the iron will
        # instantly be transported to the factory
        self.speed = 0
        # This needs to be updated if we ever get multiple stations in a route
        desired_cargo = self.grid.accepted_cargo(self.next_station(current_station))
        for building in self.grid.adjacent_buildings(current_station.positions):
            for cargo_type in building.accepts:
                if self._has_cargo(cargo_type):
                    self.wait_timer = 1
                    self._run_after_wait = self._create_unload_cargo_method(
                        building, cargo_type
                    )
                    return []
            for cargo_type in building.produces:
                if (
                    cargo_type in desired_cargo
                    and building.cargo_count[cargo_type] > 0
                    and self._has_space(cargo_type)
                ):
                    self.wait_timer = 1
                    self._run_after_wait = self._create_load_cargo_method(cargo_type)
                    return [building.remove_cargo(cargo_type, 1)]
        self._target_station = self.next_station(current_station)
        # This ensures that the train can immediately reverse at the station
        # Otherwise it the train would prefer to continue forward and then reverse
        # self.current_rail = None
        return []

    def _create_unload_cargo_method(
        self, building: Building, cargo_type: CargoType
    ) -> Callable[[], list[Event]]:
        def inner() -> list[Event]:
            events: list[Event] = []
            for wagon in reversed(self.wagons):
                if wagon.cargo_count[cargo_type]:
                    events.extend(
                        building.add_cargo(cargo_type, wagon.cargo_count[cargo_type])
                    )
                    wagon.cargo_count[cargo_type] = 0
                    return events
            return events

        return inner

    def _has_space(self, cargo_type: CargoType):
        return any(not wagon.cargo_count[cargo_type] for wagon in self.wagons)

    def _has_cargo(self, cargo_type: CargoType):
        return any(wagon.cargo_count[cargo_type] for wagon in self.wagons)

    def _create_load_cargo_method(self, cargo_type: CargoType):
        def inner():
            for wagon in self.wagons:
                if not wagon.cargo_count[cargo_type]:
                    wagon.cargo_count[cargo_type] = 1
                    return []
            return []

        return inner

    def next_station(self, current_station: Station) -> Station:
        return (
            self.grid.station_from_position[self.second_station_position]
            if self.first_station_position in current_station.positions
            else self.grid.station_from_position[self.first_station_position]
        )

    def _on_reached_target(self) -> list[Event]:
        current_position = Vec2(self.target_x, self.target_y)

        starting_rails = {
            rail
            for rail in self.grid.possible_next_rails_ignore_red_lights(
                position=current_position, previous_rail=self.current_rail
            )
            if self._can_reserve_position(rail.other_end(*current_position))
        }

        if not starting_rails:
            self.speed = 0
            self.wait_timer = 1
            return []

        if has_reached_end_of_target_station(
            current_position, self.current_rail, self._target_station
        ):
            events = self._stop_at_station(self._target_station)
            events.extend(self._reserve(current_position))
            return events

        self._rails_on_route = find_route(
            self.grid.possible_next_rails_ignore_red_lights,
            starting_rails,
            current_position,
            self._target_station,
            previous_rail=self.current_rail,
        )

        # If there is no path to the target, wait
        if not self._rails_on_route:
            self.speed = 0
            self.wait_timer = 1
            return []

        next_rail = self._rails_on_route[0]
        next_position = next_rail.other_end(*current_position)
        self._position_history.appendleft(Vec2(self.target_x, self.target_y))

        self._update_current_rail_and_target_xy(next_rail, self.target_x, self.target_y)

        # Halve speed, except for trains with no wagons, but that might be unimportant.
        if len(self._position_history) >= 2 and self._is_sharp_corner(
            middle=self._position_history[0],
            point1=self._position_history[1],
            point2=next_position,
        ):
            self.speed /= 2

        return self._reserve(next_position)

    def add_wagon(self):
        self.wagons.append(Wagon(self.x, self.y))
        self._position_history = deque(
            self._position_history, maxlen=len(self.wagons) + 1
        )
        # TODO: wagons are now created on top of train

    def _reserve(self, position: Vec2) -> list[Event]:
        return self.signal_controller.reserve(
            id(self), [*self._position_history, position]
        )

    def _is_sharp_corner(self, middle: Vec2, point1: Vec2, point2: Vec2):
        angle = math.atan2(point2.y - middle.y, point2.x - middle.x) - math.atan2(
            point1.y - middle.y, point1.x - middle.x
        )
        turn_angle = abs(math.pi - abs(angle))
        # pi/4 is 45 degrees, which is ok. pi/2 is 90 degrees, which is not ok.
        return turn_angle > math.pi / 3

    def _update_current_rail_and_target_xy(self, next_rail: Rail, x, y):
        self.current_rail = next_rail
        if self.current_rail.x1 == x and self.current_rail.y1 == y:
            self.target_x = self.current_rail.x2
            self.target_y = self.current_rail.y2
        else:
            self.target_x = self.current_rail.x1
            self.target_y = self.current_rail.y1

        dx = self.target_x - self.x
        dy = self.target_y - self.y
        angle = Vec2(dx, dy).heading * 360 / 2 / pi - 90
        self.angle = -round(angle / 45.0) * 45.0
