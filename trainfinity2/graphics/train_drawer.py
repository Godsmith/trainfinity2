from arcade import color
import arcade
from trainfinity2.constants import (
    GRID_BOX_SIZE,
    HIGHLIGHT_COLOR,
    IRON_SIZE,
    TRAIN_RADIUS,
)

from trainfinity2.train import Train


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
            x = train.x + GRID_BOX_SIZE / 2
            y = train.y + GRID_BOX_SIZE / 2
            arcade.draw_circle_filled(
                x,
                y,
                TRAIN_RADIUS,
                color=color.BLACK,
            )
            if train.iron:
                arcade.draw_rectangle_filled(
                    x,
                    y,
                    IRON_SIZE,
                    IRON_SIZE,
                    color=color.TROLLEY_GREY,
                )
                arcade.draw_rectangle_outline(
                    x,
                    y,
                    IRON_SIZE,
                    IRON_SIZE,
                    color=color.BLACK,
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
