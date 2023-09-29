from arcade import Shape, color
import arcade
from trainfinity2.constants import (
    CARGO_SIZE,
)
from trainfinity2.model import CargoType

FILL_COLOR_FROM_CARGO_TYPE = {
    CargoType.IRON: color.RUST,
    CargoType.COAL: color.SMOKY_BLACK,
    CargoType.STEEL: color.ASH_GREY,
    CargoType.TOOLS: color.ORANGE,
    CargoType.LOGS: color.BROWN,
    CargoType.PLANKS: color.WOOD_BROWN,
}

OUTLINE_COLOR_FROM_CARGO_TYPE = {
    CargoType.IRON: color.BLACK,
    CargoType.COAL: color.DARK_GRAY,
    CargoType.STEEL: color.BLACK,
    CargoType.TOOLS: color.BLACK,
    CargoType.LOGS: color.BLACK,
    CargoType.PLANKS: color.BLACK,
}


def get_cargo_shape(
    x: float, y: float, cargo_type: CargoType, tilt_angle: float = 0
) -> list[Shape]:
    filled_rectangle = arcade.create_rectangle_filled(
        x,
        y,
        CARGO_SIZE,
        CARGO_SIZE,
        color=FILL_COLOR_FROM_CARGO_TYPE[cargo_type],
        tilt_angle=tilt_angle,
    )
    rectangle_outline = arcade.create_rectangle_outline(
        x,
        y,
        CARGO_SIZE,
        CARGO_SIZE,
        color=OUTLINE_COLOR_FROM_CARGO_TYPE[cargo_type],
        tilt_angle=tilt_angle,
    )
    return [filled_rectangle, rectangle_outline]
