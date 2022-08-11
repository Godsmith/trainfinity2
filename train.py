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
    rails: list[Rail]
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
        self.current_target_route_index = 1
        route = list(self._route_from_rails())
        self.target_x = route[1].x
        self.target_y = route[1].y
        self._route = route + route[-2:0:-1]
        self.grid.add_observer(self, DestroyEvent)

    def _route_from_rails(self) -> Iterable[Vec2]:
        for rail1, rail2 in pairwise(self.rails):
            yield (rail1.positions - rail2.positions).pop()
        yield self.rails[-1].positions.intersection(self.rails[-2].positions).pop()
        yield (self.rails[-1].positions - self.rails[-2].positions).pop()

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
            self._select_next_position_in_route()

    def is_at(self, x, y):
        return (
            self.x < x < self.x + GRID_BOX_SIZE and self.y < y < self.y + GRID_BOX_SIZE
        )

    def _is_at_station(self) -> Station | None:
        for station in (self.first_station, self.second_station):
            if _is_close(self, station):
                return station

    def _select_next_position_in_route(self):
        self.current_target_route_index += 1
        self.current_target_route_index %= len(self._route)
        self.target_x = self._route[self.current_target_route_index].x
        self.target_y = self._route[self.current_target_route_index].y

        if station := self._is_at_station():
            if isinstance(station.mine_or_factory, Mine):
                self.iron += station.mine_or_factory.remove_iron(1)
            else:
                # Factory
                self.player.score += self.iron
                self.iron = 0

    def destroy(self):
        self.grid.remove_observer(self, DestroyEvent)
        self.notify(DestroyEvent())

    def on_notify(self, object: Any, event: Event):
        match object, event:
            case Rail(), DestroyEvent():
                if object in self.rails:
                    self.destroy()

    def is_colliding_with(self, train):
        return (
            abs(self.x - train.x) < GRID_BOX_SIZE / 2
            and abs(self.y - train.y) < GRID_BOX_SIZE / 2
        )
