from collections import namedtuple
from enum import Enum

import arcade
from arcade import color

SELECTED_BOX_BACKGROUND_COLOR = color.WHITE
DESELECTED_BOX_BACKGROUND_COLOR = color.GRAY
BOX_TEXT_COLOR = color.BLACK
BOX_OUTLINE_COLOR = color.BLACK
BOX_SIZE_PIXELS = 60


Box = namedtuple("Box", "text mode")


class Mode(Enum):
    SELECT = 1
    RAIL = 2
    TRAIN = 3
    DESTROY = 4


class Gui:
    def __init__(self) -> None:
        self.boxes = [
            Box("SELECT", Mode.SELECT),
            Box("RAIL", Mode.RAIL),
            Box("TRAIN", Mode.TRAIN),
            Box("DESTROY", Mode.DESTROY),
        ]
        self._mode = Mode.RAIL
        self._enabled = True
        self._shape_element_list = arcade.ShapeElementList()
        self._sprite_list = arcade.SpriteList()
        self.create_boxes()

    def disable(self):
        """Stop the GUI from taking clicks. Currently mostly useful for unit testing."""
        self._enabled = False

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value: Mode):
        self._mode = value
        self.create_boxes()

    def draw(self):
        self._shape_element_list.draw()
        self._sprite_list.draw()

    def pan(self, dx, dy):
        self._sprite_list.move(dx, dy)
        self._shape_element_list.move(dx, dy)

    def create_boxes(self):
        """Recreates the boxes. Necessary for example after zooming and after
        changing color of the boxes when switching active mode."""
        self._shape_element_list = arcade.ShapeElementList()
        self._sprite_list = arcade.SpriteList()
        for i, box in enumerate(self.boxes):
            self._create_box(box, i)

    def _is_inside(self, x, y, index):
        left, _, bottom, _ = arcade.get_viewport()
        left += index * BOX_SIZE_PIXELS
        return (
            left < x < left + BOX_SIZE_PIXELS and bottom < y < bottom + BOX_SIZE_PIXELS
        )

    def on_left_click(self, x, y):
        """Returns True if the event was handled, False otherwise."""
        if self._enabled:
            for i, box in enumerate(self.boxes):
                if self._is_inside(x, y, i):
                    self.mode = box.mode
                    return True
        return False

    def _create_box(self, box: Box, index: int):
        left, _, bottom, _ = arcade.get_viewport()
        left += index * BOX_SIZE_PIXELS
        background_color = (
            SELECTED_BOX_BACKGROUND_COLOR
            if self.mode == box.mode
            else DESELECTED_BOX_BACKGROUND_COLOR
        )
        center_x = left + BOX_SIZE_PIXELS / 2
        center_y = bottom + BOX_SIZE_PIXELS / 2
        self._shape_element_list.append(
            arcade.create_rectangle_filled(
                center_x, center_y, BOX_SIZE_PIXELS, BOX_SIZE_PIXELS, background_color
            )
        )
        self._shape_element_list.append(
            arcade.create_rectangle_outline(
                center_x, center_y, BOX_SIZE_PIXELS, BOX_SIZE_PIXELS, BOX_OUTLINE_COLOR
            )
        )
        self._sprite_list.append(
            arcade.create_text_sprite(
                box.text,
                start_x=left,
                start_y=bottom + BOX_SIZE_PIXELS / 2,
                color=BOX_TEXT_COLOR,
                width=int(BOX_SIZE_PIXELS),
                align="center",
            )
        )
