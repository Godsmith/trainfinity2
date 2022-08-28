from dataclasses import dataclass, field
import random

from pyglet.math import Vec2

from constants import GRID_BOX_SIZE
from grid import Grid
from model import Mine, Player, Rail, Station
from observer import DestroyEvent, Subject
from signal_controller import SignalController


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
    current_target_route_index: int = field(init=False)
    iron: int = 0
    selected = False

    TRAIN_SPEED_PIXELS_PER_SECOND = 120.0  # 60.0

    def __post_init__(self):
        super().__init__()
        self.x = self.first_station.x
        self.y = self.first_station.y
        self._target_station = self.first_station
        self._rails_on_route = []
        self._current_rail: Rail | None = None

    @property
    def rails_on_route(self):
        return self._rails_on_route

    def start(self):
        self._select_next_target(self.first_station.x, self.first_station.y)

    def _select_next_target(self, x: int, y: int):
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
            # Ensure that the train can reverse at the station
            self._current_rail = None

        self._rails_on_route = self.grid._find_route(
            Vec2(x, y), self._target_station, previous_rail=self._current_rail
        )

        if next_rail := self._get_next_rail(x, y):
            self._set_current_rail(next_rail, x, y)
            self.signal_controller.update_signals()
        else:
            self.destroy()

    def _set_current_rail(self, next_rail: Rail, x, y):
        self._current_rail = next_rail
        if self._current_rail.x1 == x and self._current_rail.y1 == y:
            self.target_x = self._current_rail.x2
            self.target_y = self._current_rail.y2
        else:
            self.target_x = self._current_rail.x1
            self.target_y = self._current_rail.y1

    def _get_next_rail(self, x, y) -> Rail | None:
        """1. If there is a route to the target, choose the first rail on that route.
        2. If not, choose a random rail.
        3. If there is no rail to choose, reverse, then choose a random rail (possible change: return None?)
        4. If there is still no rail to choose, return None."""
        if self._rails_on_route:
            return self._rails_on_route[0]
        else:
            possible_next_rails = self.grid._possible_next_rails(
                Vec2(x, y), previous_rail=self._current_rail
            )
            if not possible_next_rails:
                # At end of line; reverse
                possible_next_rails = self.grid._possible_next_rails(
                    Vec2(x, y), previous_rail=None
                )
                if not possible_next_rails:
                    return None
            return random.choice(list(possible_next_rails))

    def move(self, delta_time):
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
            self._select_next_target(self.target_x, self.target_y)

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
