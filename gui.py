from collections import namedtuple
import arcade

SELECTED_BOX_BACKGROUND_COLOR = arcade.color.WHITE
DESELECTED_BOX_BACKGROUND_COLOR = arcade.color.GRAY
BOX_TEXT_COLOR = arcade.color.BLACK
BOX_OUTLINE_COLOR = arcade.color.BLACK


Box = namedtuple("Box", "text")


class Gui:
    def __init__(self) -> None:
        self.boxes = [Box("RAIL"), Box("TRAIN")]
        self.selection = 0

    def draw(self):
        for i, box in enumerate(self.boxes):
            self._draw_box(box, i)

    def _is_inside(self, x, y, index):
        left, _, bottom, top = arcade.get_viewport()
        box_size = (top - bottom) / 10
        left += index * box_size
        return left < x < left + box_size and bottom < y < bottom + box_size

    def on_left_click(self, x, y):
        for i, _ in enumerate(self.boxes):
            if self._is_inside(x, y, i):
                self.selection = i

    def _draw_box(self, box: Box, index: int):
        left, _, bottom, top = arcade.get_viewport()
        box_size = (top - bottom) / 10
        left += index * box_size
        background_color = (
            SELECTED_BOX_BACKGROUND_COLOR
            if self.selection == index
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
