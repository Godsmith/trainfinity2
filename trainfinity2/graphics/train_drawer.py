from arcade import color
import arcade
from trainfinity2.constants import (
    GRID_BOX_SIZE,
    HIGHLIGHT_COLOR,
    IRON_SIZE,
    TRAIN_RADIUS,
)

from trainfinity2.train import Train
from trainfinity2.wagon import Wagon


class TrainDrawer:
    def __init__(self) -> None:
        self._trains: list[Train] = []

    def add(self, train: Train):
        self._trains.append(train)

    def remove(self, train: Train):
        self._trains.remove(train)

    def draw(self):
        # TODO: Create a shapelist per train that we can move instead
        for train in self._trains:
            self._draw_train(train)
            for wagon in train.wagons:
                self._draw_wagon(wagon)

    def _draw_train(self, train: Train):
        x = train.x + GRID_BOX_SIZE / 2
        y = train.y + GRID_BOX_SIZE / 2
        arcade.draw_rectangle_filled(
            x,
            y,
            GRID_BOX_SIZE * 0.5,
            GRID_BOX_SIZE * 0.8,
            color=color.BLACK,
            tilt_angle=train.angle,
        )
        if train.selected:
            arcade.draw_circle_outline(
                x, y, TRAIN_RADIUS, color=HIGHLIGHT_COLOR, border_width=5
            )
            if train.rails_on_route:
                positions = {
                    position
                    for rail in train.rails_on_route[1:]
                    for position in rail.positions
                }
                for position in positions:
                    arcade.draw_rectangle_filled(
                        position.x + GRID_BOX_SIZE / 2,
                        position.y + GRID_BOX_SIZE / 2,
                        GRID_BOX_SIZE,
                        GRID_BOX_SIZE,
                        color=HIGHLIGHT_COLOR,
                    )

    def _draw_wagon(self, wagon: Wagon):
        x = wagon.x + GRID_BOX_SIZE / 2
        y = wagon.y + GRID_BOX_SIZE / 2
        arcade.draw_rectangle_filled(
            x,
            y,
            GRID_BOX_SIZE * 0.5,
            GRID_BOX_SIZE * 0.8,
            color=color.EGGSHELL,
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
