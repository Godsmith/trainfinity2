from dataclasses import dataclass, field

from pyglet.math import Vec2

from .constants import GRID_BOX_SIZE
from .grid import Grid
from .model import Mine, Player, Rail, Station
from .observer import DestroyEvent, Subject
from .route_finder import find_route
from .signal_controller import SignalController


def _is_close(pos1, pos2):
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
    iron: int = 0
    selected = False
    wait_timer: float = 0.0

    TRAIN_SPEED_PIXELS_PER_SECOND = 120.0  # 60.0

    def __post_init__(self):
        super().__init__()
        self.x = self.first_station.x
        self.y = self.first_station.y
        self.target_x = self.x
        self.target_y = self.y
        self._target_station = self.first_station
        self._rails_on_route = []

    @property
    def rails_on_route(self):
        return self._rails_on_route

    def move(self, delta_time):
        if self.wait_timer > 0:
            self.wait_timer -= delta_time
            return

        train_displacement = delta_time * self.TRAIN_SPEED_PIXELS_PER_SECOND
        if self.x > self.target_x + train_displacement:
            self.x -= train_displacement
        elif self.x < self.target_x - train_displacement:
            self.x += train_displacement
        if self.y > self.target_y + train_displacement:
            self.y -= train_displacement
        elif self.y < self.target_y - train_displacement:
            self.y += train_displacement
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
        self.notify(DestroyEvent())

    def is_colliding_with(self, train):
        return (
            abs(self.x - train.x) < GRID_BOX_SIZE / 2
            and abs(self.y - train.y) < GRID_BOX_SIZE / 2
        )

    def _on_reached_target(self):
        if _is_close(self, self._target_station):
            if isinstance(self._target_station.mine_or_factory, Mine):
                self.iron += self._target_station.mine_or_factory.remove_iron(1)
            else:
                # Factory
                self.player.score += self.iron
                self.iron = 0
            self._target_station = (
                self.second_station
                if self._target_station == self.first_station
                else self.first_station
            )
            # This ensures that the train can immediately reverse at the station
            # Otherwise it the train would prefer to continue forward and then reverse
            self.current_rail = None

        current_position = Vec2(self.target_x, self.target_y)

        self._rails_on_route = find_route(
            self.grid.possible_next_rails,
            current_position,
            self._target_station,
            previous_rail=self.current_rail,
        )

        if not self._rails_on_route:
            self._rails_on_route = find_route(
                self.grid.possible_next_rails_ignore_red_lights,
                current_position,
                self._target_station,
                previous_rail=self.current_rail,
            )

        if not self._rails_on_route:
            self.destroy()
            return

        next_rail = self._rails_on_route[0]
        next_position = next_rail.other_end(self.target_x, self.target_y)
        if self.signal_controller.is_unreserved(next_position):
            self._set_current_rail(next_rail, self.target_x, self.target_y)
            self.signal_controller.change_block_reservation(
                Vec2(self.target_x, self.target_y), current_position
            )
        else:
            self.wait_timer = 1

    def _set_current_rail(self, next_rail: Rail, x, y):
        self.current_rail = next_rail
        if self.current_rail.x1 == x and self.current_rail.y1 == y:
            self.target_x = self.current_rail.x2
            self.target_y = self.current_rail.y2
        else:
            self.target_x = self.current_rail.x1
            self.target_y = self.current_rail.y1