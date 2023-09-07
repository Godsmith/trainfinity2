from dataclasses import dataclass

import arcade
from arcade import Emitter, color

from trainfinity2.constants import (
    GRID_BOX_SIZE_PIXELS,
    HIGHLIGHT_COLOR,
    IRON_SIZE,
)
from trainfinity2.train import Train
from trainfinity2.wagon import Wagon

ROCKET_SMOKE_TEXTURE = arcade.make_soft_circle_texture(
    GRID_BOX_SIZE_PIXELS * 3 // 4, color.WHITE
)


def _make_smoke_emitter():
    """Returns an emitter that emits its particles at a constant rate for a given amount of time"""
    particle_factory = arcade.FadeParticle
    return arcade.Emitter(
        center_xy=(0.0, 0.0),
        emit_controller=arcade.EmitterIntervalWithTime(
            emit_interval=0.2, lifetime=1000000.0
        ),
        particle_factory=lambda emitter: particle_factory(
            filename_or_texture=ROCKET_SMOKE_TEXTURE,
            change_xy=(0.1, 0.2),
            lifetime=1.5,
            scale=1.0,
        ),
    )


@dataclass
class SmokingTrain:
    train: Train
    smoke_emitter: Emitter


class TrainDrawer:
    def __init__(self) -> None:
        self._smoking_trains: list[SmokingTrain] = []
        self._smoke_emitters_from_train: list[Emitter] = []

    def add(self, train: Train):
        emitter = _make_smoke_emitter()
        self._smoking_trains.append(SmokingTrain(train, emitter))

    def remove(self, train: Train):
        self._smoking_trains = [
            smoking_train
            for smoking_train in self._smoking_trains
            if smoking_train.train != train
        ]

    def draw(self):
        # TODO: Create a shapelist per train that we can move instead
        for train in self._smoking_trains:
            self._draw_train(train.train)
            for wagon in train.train.wagons:
                self._draw_wagon(wagon)
            train.smoke_emitter.draw()

    def update(self):
        for train in self._smoking_trains:
            x = train.train.x * GRID_BOX_SIZE_PIXELS + GRID_BOX_SIZE_PIXELS / 2
            y = train.train.y * GRID_BOX_SIZE_PIXELS + GRID_BOX_SIZE_PIXELS / 2
            train.smoke_emitter.center_x = x
            train.smoke_emitter.center_y = y
            train.smoke_emitter.update()

    def _draw_train(self, train: Train):
        x = train.x * GRID_BOX_SIZE_PIXELS + GRID_BOX_SIZE_PIXELS / 2
        y = train.y * GRID_BOX_SIZE_PIXELS + GRID_BOX_SIZE_PIXELS / 2
        arcade.draw_rectangle_filled(
            x,
            y,
            GRID_BOX_SIZE_PIXELS * 0.5,
            GRID_BOX_SIZE_PIXELS * 0.8,
            color=color.BLACK,
            tilt_angle=train.angle,
        )
        if train.selected:
            arcade.draw_rectangle_outline(
                x,
                y,
                GRID_BOX_SIZE_PIXELS * 0.5,
                GRID_BOX_SIZE_PIXELS * 0.8,
                color=HIGHLIGHT_COLOR,
                tilt_angle=-train.angle,  # Not sure why minus sign needed here
                border_width=5,
            )
            if train.rails_on_route:
                positions = [
                    # (train.x + GRID_BOX_SIZE / 2, train.y + GRID_BOX_SIZE / 2)
                    (
                        position.x * GRID_BOX_SIZE_PIXELS + GRID_BOX_SIZE_PIXELS / 2,
                        position.y * GRID_BOX_SIZE_PIXELS + GRID_BOX_SIZE_PIXELS / 2,
                    )
                    for rail in train.rails_on_route[1:]
                    for position in rail.positions
                ]
                arcade.draw_lines(positions, color=HIGHLIGHT_COLOR, line_width=4)

    def _draw_wagon(self, wagon: Wagon):
        x = (wagon.x + 1 / 2) * GRID_BOX_SIZE_PIXELS
        y = (wagon.y + 1 / 2) * GRID_BOX_SIZE_PIXELS
        arcade.draw_rectangle_filled(
            x,
            y,
            GRID_BOX_SIZE_PIXELS * 0.5,
            GRID_BOX_SIZE_PIXELS * 0.8,
            color=color.REDWOOD,
            tilt_angle=wagon.angle,
        )
        if wagon.iron:
            arcade.draw_rectangle_filled(
                x,
                y,
                IRON_SIZE,
                IRON_SIZE,
                color=color.TROLLEY_GREY,
                tilt_angle=wagon.angle,
            )
            arcade.draw_rectangle_outline(
                x,
                y,
                IRON_SIZE,
                IRON_SIZE,
                color=color.BLACK,
                tilt_angle=wagon.angle,
            )
