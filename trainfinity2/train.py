from collections import deque
from dataclasses import dataclass, field

from math import pi
import math
from pyglet.math import Vec2

from .constants import GRID_BOX_SIZE
from .grid import Grid
from .model import Player, Rail, Station
from .wagon import Wagon, approx_equal
from .observer import DestroyEvent, Subject
from .route_finder import find_route
from .signal_controller import SignalController


def _is_close(pos1: Vec2, pos2: Vec2):
    return (
        abs(pos1.x - pos2.x) < GRID_BOX_SIZE / 2
        and abs(pos1.y - pos2.y) < GRID_BOX_SIZE / 2
    )


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
        self._target_x_history = deque(maxlen=3)
        self._target_y_history = deque(maxlen=3)
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

        train_displacement = delta_time * self.speed
        dx = 0
        dy = 0
        if self.x > self.target_x + train_displacement:
            dx = -train_displacement
        elif self.x < self.target_x - train_displacement:
            dx = train_displacement
        if self.y > self.target_y + train_displacement:
            dy = -train_displacement
        elif self.y < self.target_y - train_displacement:
            dy = train_displacement

        if approx_equal(self.angle % 90.0, 45.0):
            dx /= math.sqrt(2)
            dy /= math.sqrt(2)

        self.x += dx
        self.y += dy
        self.angle = -(Vec2(dx, dy).heading * 360 / 2 / pi - 90)

        for wagon in self.wagons:
            wagon.move(delta_time, self.speed)

        if (
            abs(self.x - self.target_x) < train_displacement
            and abs(self.y - self.target_y) < train_displacement
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
        self._target_x_history.append(self.target_x)
        self._target_y_history.append(self.target_y)
        for target_x, target_y, wagon in zip(
            self._target_x_history, self._target_y_history, self.wagons
        ):
            wagon.target_x = target_x
            wagon.target_y = target_y
            self.signal_controller.reserve(id(wagon), Vec2(target_x, target_y))
        self._update_current_rail_and_target_xy(next_rail, self.target_x, self.target_y)
        self.signal_controller.reserve(id(self), next_position)

    def _update_current_rail_and_target_xy(self, next_rail: Rail, x, y):
        self.current_rail = next_rail
        if self.current_rail.x1 == x and self.current_rail.y1 == y:
            self.target_x = self.current_rail.x2
            self.target_y = self.current_rail.y2
        else:
            self.target_x = self.current_rail.x1
            self.target_y = self.current_rail.y1
