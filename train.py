from dataclasses import dataclass, field
from itertools import pairwise
from typing import Any, Iterable

from pyglet.math import Vec2

from constants import GRID_BOX_SIZE
from grid import Grid
from model import Mine, Player, Rail, Station
from observer import DestroyEvent, Event, Observer, Subject


def _is_close(pos1, pos2):
    return (
        abs(pos1.x - pos2.x) < GRID_BOX_SIZE / 2
        and abs(pos1.y - pos2.y) < GRID_BOX_SIZE / 2
    )


@dataclass
class Train(Subject, Observer):
    player: Player
    first_station: Station
    second_station: Station
    grid: Grid
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
        self._rails = []
        self._select_next_target(self.first_station.x, self.first_station.y)

    @property
    def rails(self):
        return self._rails

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

        self._rails = self.grid._explore([], Vec2(x, y), self._target_station)
        if self._rails:
            next_rail = self._rails[0]
            if next_rail.x1 == x and next_rail.y1 == y:
                self.target_x = next_rail.x2
                self.target_y = next_rail.y2
            else:
                self.target_x = next_rail.x1
                self.target_y = next_rail.y1
        else:
            raise NotImplementedError("Need to handle the case where no path is found")

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
