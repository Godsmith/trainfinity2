from collections import deque
from dataclasses import dataclass, field

from math import pi
import math
from typing import Iterator, Sequence
from pyglet.math import Vec2

from .constants import GRID_BOX_SIZE
from .grid import Grid
from .model import Player, Rail, Station
from .wagon import Wagon
from .observer import DestroyEvent, Subject
from .route_finder import find_route
from .signal_controller import SignalController
from typing import NamedTuple


def approx_equal(a: float, b: float):
    return abs(a - b) < 1.0


def _is_close(pos1: Vec2, pos2: Vec2):
    return (
        abs(pos1.x - pos2.x) < GRID_BOX_SIZE / 2
        and abs(pos1.y - pos2.y) < GRID_BOX_SIZE / 2
    )


class PointAndAngle(NamedTuple):
    point: Vec2
    angle: float


def _find_equidistant_points_and_angles_along_line(
    line_points: Sequence[Vec2], n: int, distance: float
) -> list[Vec2]:
    """Returns n positions with equal distance along the provided line set of positions.

    If the provided line is not long enough for the number of points requested, all
    remaining points returned will be at the end of the line."""

    line_points = deque(line_points)
    current_position = line_points.popleft()
    equidistant_points_and_angles = []
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
class Train(Subject):
    player: Player
    first_station: Station
    second_station: Station
    grid: Grid
    signal_controller: SignalController
    x: float = field(init=False)
    y: float = field(init=False)
    target_x: int = field(init=False)
    target_y: int = field(init=False)
    current_rail: Rail | None = None
    wagons: list[Wagon] = field(init=False)
    selected = False
    wait_timer: float = 0.0
    angle: float = 0
    speed = 0.0  # Pixels per second

    MAX_SPEED = 120.0  # 60.0  # Pixels per second
    ACCELERATION = 40.0  # Pixels per second squared

    def __post_init__(self):
        super().__init__()
        self.x = self.first_station.position.x
        self.y = self.first_station.position.y
        self.target_x = self.x
        self.target_y = self.y
        self._target_station = self.first_station
        self._rails_on_route = []
        self._position_history = deque(
            maxlen=4
        )  # TODO: needs to be more than number of wagons
        self._previous_targets_y = []
        # TODO: wagons are now created on top of train
        self.wagons = []
        self.wagons.append(Wagon(self.x, self.y))
        self.wagons.append(Wagon(self.x, self.y))
        self.wagons.append(Wagon(self.x, self.y))

    @property
    def rails_on_route(self):
        return self._rails_on_route

    def move(self, delta_time):
        if self.wait_timer > 0:
            self.wait_timer -= delta_time
            return

        if self.speed < self.MAX_SPEED:
            self.speed += self.ACCELERATION * delta_time
            self.speed = min(self.speed, self.MAX_SPEED)

        pixels_to_move = delta_time * self.speed
        dx = 0
        dy = 0
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
            GRID_BOX_SIZE,
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
            self._on_reached_target()

    def is_at(self, x, y):
        return (
            self.x < x < self.x + GRID_BOX_SIZE and self.y < y < self.y + GRID_BOX_SIZE
        )

    def destroy(self):
        train_and_wagon_ids = {id(obj) for obj in [self] + self.wagons}
        for id_ in train_and_wagon_ids:
            self.signal_controller.unreserve(id_)
        self.notify(DestroyEvent())

    def is_colliding_with(self, train):
        return (
            abs(self.x - train.x) < GRID_BOX_SIZE / 4
            and abs(self.y - train.y) < GRID_BOX_SIZE / 4
        )

    def _can_reserve_position(self, position: Vec2) -> bool:
        train_and_wagon_ids = {id(obj) for obj in [self] + self.wagons}
        return (
            not self.signal_controller.reserver(position)
            or self.signal_controller.reserver(position) in train_and_wagon_ids
        )

    def _stop_at_target_station(self):
        # Check factories before mines, or a the iron will
        # instantly be transported to the factory
        if self.grid.adjacent_factories(Vec2(self.x, self.y)):
            for wagon in self.wagons:
                if wagon.iron:
                    self.player.score += wagon.iron
                    wagon.iron = 0
        for mine in self.grid.adjacent_mines(Vec2(self.x, self.y)):
            for wagon in self.wagons:
                if mine.iron > 0 and wagon.iron == 0:
                    wagon.iron += mine.remove_iron(1)
        self._target_station = (
            self.second_station
            if self._target_station == self.first_station
            else self.first_station
        )
        # This ensures that the train can immediately reverse at the station
        # Otherwise it the train would prefer to continue forward and then reverse
        self.current_rail = None

        self.speed = 0

    def _on_reached_target(self):
        if _is_close(Vec2(self.x, self.y), self._target_station.position):
            self._stop_at_target_station()

        current_position = Vec2(self.target_x, self.target_y)

        starting_rails = []
        adjacent_reserved_positions = []
        for rail in self.grid.possible_next_rails_ignore_red_lights(
            position=current_position, previous_rail=self.current_rail
        ):
            position = rail.other_end(*current_position)
            if self._can_reserve_position(position):
                starting_rails.append(rail)
            else:
                adjacent_reserved_positions.append(position)

        if not starting_rails:
            # If the train has nowhere to go from the current position,
            # destroy the train. TODO: is this needed?
            if not adjacent_reserved_positions:
                self.destroy()
                return
            # Stop the train and wait
            self.speed = 0
            self.wait_timer = 1
            return

        self._rails_on_route = find_route(
            self.grid.possible_next_rails_ignore_red_lights,
            starting_rails,
            current_position,
            self._target_station,
            previous_rail=self.current_rail,
        )

        # If there is no path to the target, destroy the train
        if not self._rails_on_route:
            self.destroy()
            return
        next_rail = self._rails_on_route[0]
        next_position = next_rail.other_end(*current_position)
        self._position_history.appendleft(Vec2(self.target_x, self.target_y))
        self._update_current_rail_and_target_xy(next_rail, self.target_x, self.target_y)

        self.signal_controller.reserve(id(self), next_position)
        for wagon in self.wagons:
            # Kind of dangerous, an implementation change could
            # mean that another train gets the chance to
            # reserve the block before the wagon gets the chance
            # to reserve it again
            self.signal_controller.unreserve(id(wagon))
            self.signal_controller.reserve(
                id(wagon), self.grid.snap_to(wagon.x, wagon.y)
            )

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
