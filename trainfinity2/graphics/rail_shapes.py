import math
import arcade
from more_itertools import numeric_range
from trainfinity2.constants import (
    GRID_BOX_SIZE_PIXELS,
    RAIL_LINE_WIDTH,
)
from trainfinity2.model import Rail
from pyglet.math import Vec2


def get_rail_shapes(rail: Rail, color: list[int]) -> list[arcade.Shape]:
    return _get_sleepers(rail, color) + _get_metal_rail_shapes(rail, color)


def _get_sleepers(rail: Rail, color: list[int]) -> list[arcade.Shape]:
    x1, y1, x2, y2 = [
        coordinate * GRID_BOX_SIZE_PIXELS + GRID_BOX_SIZE_PIXELS / 2
        for coordinate in (rail.x1, rail.y1, rail.x2, rail.y2)
    ]

    x = x1
    y = y1
    sleeper_count = 10
    sleeper_width = GRID_BOX_SIZE_PIXELS / 3
    sleeper_shapes = []
    if x2 == x1:
        xs = [x1] * sleeper_count
    else:
        xs = list(numeric_range(x1, x2, (x2 - x1) / sleeper_count))
    if y2 == y1:
        ys = [y1] * sleeper_count
    else:
        ys = list(numeric_range(y1, y2, (y2 - y1) / sleeper_count))
    for x, y in zip(xs, ys):
        x += (x2 - x1) / sleeper_count
        y += (y2 - y1) / sleeper_count
        offset = _offset_multiplier(x1, x2, y1, y2).scale(sleeper_width / 2)
        sleeper_x1, sleeper_y1 = Vec2(x, y) - offset
        sleeper_x2, sleeper_y2 = Vec2(x, y) + offset
        shape = arcade.create_line(
            sleeper_x1,
            sleeper_y1,
            sleeper_x2,
            sleeper_y2,
            color,
            RAIL_LINE_WIDTH,
        )

        sleeper_shapes.append(shape)
    return sleeper_shapes


def _get_metal_rail_shapes(rail: Rail, color: list[int]) -> list[arcade.Shape]:
    x1, y1, x2, y2 = [
        coordinate * GRID_BOX_SIZE_PIXELS + GRID_BOX_SIZE_PIXELS / 2
        for coordinate in (rail.x1, rail.y1, rail.x2, rail.y2)
    ]
    train_track_width = GRID_BOX_SIZE_PIXELS / 6
    offset = _offset_multiplier(x1, x2, y1, y2).scale(train_track_width / 2)
    return [
        arcade.create_line(
            x1 - offset.x,
            y1 - offset.y,
            x2 - offset.x,
            y2 - offset.y,
            color,
            RAIL_LINE_WIDTH,
        ),
        arcade.create_line(
            x1 + offset.x,
            y1 + offset.y,
            x2 + offset.x,
            y2 + offset.y,
            color,
            RAIL_LINE_WIDTH,
        ),
    ]


def _offset_multiplier(x1: float, x2: float, y1: float, y2: float) -> Vec2:
    if x1 == x2:  # vertical
        x_offset = 1.0
        y_offset = 0.0
    elif y1 == y2:  # horizontal
        x_offset = 0.0
        y_offset = 1.0
    elif (x2 > x1 and y2 > y1) or (x2 < x1 and y2 < y1):  # NE or SW
        x_offset = 1 / math.sqrt(2)
        y_offset = -1 / math.sqrt(2)
    else:  # NW or SE
        x_offset = y_offset = 1 / math.sqrt(2)
    return Vec2(x_offset, y_offset)
