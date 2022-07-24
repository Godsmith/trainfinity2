from collections import namedtuple
from enum import Enum

import arcade
from arcade import color

SELECTED_BOX_BACKGROUND_COLOR = color.WHITE
DESELECTED_BOX_BACKGROUND_COLOR = color.GRAY
BOX_TEXT_COLOR = color.BLACK
BOX_OUTLINE_COLOR = color.BLACK


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
        self.mode = Mode.RAIL
        self._enabled = True
        self._shape_element_list = arcade.ShapeElementList()
        self._sprite_list = arcade.SpriteList()
        self.create_boxes()

    def disable(self):
        """Stop the GUI from taking clicks. Currently mostly useful for unit testing."""
        self._enabled = False

    def draw(self):
        self._shape_element_list.draw()
        self._sprite_list.draw()

    def pan(self, dx, dy):
        self._sprite_list.move(dx, dy)
        self._shape_element_list.move(dx, dy)

    def create_boxes(self):
        self._shape_element_list = arcade.ShapeElementList()
        self._sprite_list = arcade.SpriteList()
        for i, box in enumerate(self.boxes):
            self._create_box(box, i)

    def _is_inside(self, x, y, index):
        left, _, bottom, top = arcade.get_viewport()
        box_size = (top - bottom) / 10
        left += index * box_size
        return left < x < left + box_size and bottom < y < bottom + box_size

    def on_left_click(self, x, y):
        """Returns True if the event was handled, False otherwise."""
        if self._enabled:
            for i, box in enumerate(self.boxes):
                if self._is_inside(x, y, i):
                    self.mode = box.mode
                    self.create_boxes()
                    return True
        return False

    def _create_box(self, box: Box, index: int):
        left, _, bottom, top = arcade.get_viewport()
        box_size = (top - bottom) / 10
        left += index * box_size
        background_color = (
            SELECTED_BOX_BACKGROUND_COLOR
            if self.mode == box.mode
            else DESELECTED_BOX_BACKGROUND_COLOR
        )
        center_x = left + box_size / 2
        center_y = bottom + box_size / 2
        self._shape_element_list.append(
            arcade.create_rectangle_filled(
                center_x, center_y, box_size, box_size, background_color
            )
        )
        self._shape_element_list.append(
            arcade.create_rectangle_outline(
                center_x, center_y, box_size, box_size, BOX_OUTLINE_COLOR
            )
        )
        self._sprite_list.append(
            arcade.create_text_sprite(
                box.text,
                start_x=left,
                start_y=bottom + box_size / 2,
                color=BOX_TEXT_COLOR,
                width=int(box_size),
                align="center",
            )
        )
