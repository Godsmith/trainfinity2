from arcade import Shape, color
import arcade
from trainfinity2.constants import (
    CARGO_SIZE,
)
from trainfinity2.model import CargoType


def get_cargo_shape(
    x: float, y: float, cargo_type: CargoType, tilt_angle: float = 0
) -> list[Shape]:
    fill_color = color.TROLLEY_GREY if cargo_type == CargoType.IRON else color.BLACK
    filled_rectangle = arcade.create_rectangle_filled(
        x, y, CARGO_SIZE, CARGO_SIZE, color=fill_color, tilt_angle=tilt_angle
    )
    rectangle_outline = arcade.create_rectangle_outline(
        x, y, CARGO_SIZE, CARGO_SIZE, color=color.BLACK, tilt_angle=tilt_angle
    )
    return [filled_rectangle, rectangle_outline]
