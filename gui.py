from collections import namedtuple
from enum import Enum
import arcade

SELECTED_BOX_BACKGROUND_COLOR = arcade.color.WHITE
DESELECTED_BOX_BACKGROUND_COLOR = arcade.color.GRAY
BOX_TEXT_COLOR = arcade.color.BLACK
BOX_OUTLINE_COLOR = arcade.color.BLACK


Box = namedtuple("Box", "text mode")


class Mode(Enum):
    SELECT = 1
    RAIL = 2
    TRAIN = 3


class Gui:
    def __init__(self) -> None:
        self.boxes = [
            Box("SELECT", Mode.SELECT),
            Box("RAIL", Mode.RAIL),
            Box("TRAIN", Mode.TRAIN),
        ]
        self.mode = Mode.RAIL
        self._enabled = True

    def disable(self):
        """Stop the GUI from taking clicks. Currently mostly useful for unit testing."""
        self._enabled = False

    def draw(self):
        for i, box in enumerate(self.boxes):
            self._draw_box(box, i)

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
                    return True
        return False

    def _draw_box(self, box: Box, index: int):
        left, _, bottom, top = arcade.get_viewport()
        box_size = (top - bottom) / 10
        left += index * box_size
        background_color = (
            SELECTED_BOX_BACKGROUND_COLOR
            if self.mode == box.mode
            else DESELECTED_BOX_BACKGROUND_COLOR
        )
        arcade.draw_lrtb_rectangle_filled(
            left, left + box_size, bottom + box_size, bottom, background_color
        )
        arcade.draw_lrtb_rectangle_outline(
            left, left + box_size, bottom + box_size, bottom, BOX_OUTLINE_COLOR
        )
        arcade.draw_text(
            box.text,
            start_x=left,
            start_y=bottom + box_size / 2,
            color=BOX_TEXT_COLOR,
            width=int(box_size),
            align="center",
        )
