from collections import namedtuple
from enum import Enum, auto

import arcade
from arcade import color

from trainfinity2.camera import Camera

SELECTED_BOX_BACKGROUND_COLOR = color.WHITE
DESELECTED_BOX_BACKGROUND_COLOR = color.GRAY
BOX_TEXT_COLOR = color.BLACK
BOX_OUTLINE_COLOR = color.BLACK
BOX_SIZE_PIXELS = 60


Box = namedtuple("Box", "text mode")


class Mode(Enum):
    SELECT = auto()
    RAIL = auto()
    STATION = auto()
    TRAIN = auto()
    SIGNAL = auto()
    DESTROY = auto()


class Gui:
    def __init__(self, camera: Camera) -> None:
        self.camera = camera
        self.boxes = [
            Box("SELECT", Mode.SELECT),
            Box("RAIL", Mode.RAIL),
            Box("STATION", Mode.STATION),
            Box("TRAIN", Mode.TRAIN),
            Box("SIGNAL", Mode.SIGNAL),
            Box("DESTROY", Mode.DESTROY),
        ]
        self._mode = Mode.RAIL
        self._enabled = True
        self._shape_element_list: arcade.ShapeElementList = arcade.ShapeElementList()
        self._sprite_list = arcade.SpriteList()
        self._text_sprite_list = arcade.SpriteList()
        self._fps_sprite = arcade.Sprite()
        self._score_sprite = arcade.Sprite()
        self._score_per_minute_sprite = arcade.Sprite()
        self._text_sprite_list = arcade.SpriteList()
        self._text_sprite_list.append(self._fps_sprite)
        self._text_sprite_list.append(self._score_sprite)
        self._text_sprite_list.append(self._score_per_minute_sprite)
        self._fps = 0
        self._score = 0
        self._level = 0
        self._score_to_next_level = 10  # TODO: should not be hardcoded here
        self.refresh()

    def disable(self):
        """Stop the GUI from taking clicks. Currently mostly useful for unit testing."""
        self._enabled = False

    def enable(self):
        self._enabled = True

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value: Mode):
        self._mode = value
        self.refresh()

    def draw(self):
        with self.camera:
            self._shape_element_list.draw()
            self._sprite_list.draw()
            self._text_sprite_list.draw()

    def pan(self, dx, dy):
        self._sprite_list.move(dx, dy)
        self._text_sprite_list.move(dx, dy)
        self._shape_element_list.move(dx, dy)

    def refresh(self):
        with self.camera:
            """Recreates the boxes. Necessary for example after zooming and after
            changing color of the boxes when switching active mode."""
            self._shape_element_list = arcade.ShapeElementList()
            self._sprite_list = arcade.SpriteList()
            for i, box in enumerate(self.boxes):
                self._create_box(box, i)

            self._refresh_fps_sprite()
            self._refresh_score_sprite()

    def _is_inside(self, x, y, index):
        left, _, bottom, _ = arcade.get_viewport()
        left += index * BOX_SIZE_PIXELS
        return (
            left < x < left + BOX_SIZE_PIXELS and bottom < y < bottom + BOX_SIZE_PIXELS
        )

    def on_left_click(self, x, y):
        """Returns True if the event was handled, False otherwise."""
        with self.camera:
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

    def update_fps_number(self, fps: int):
        with self.camera:
            self._fps = fps
            self._refresh_fps_sprite()

    def update_score_per_minute(self, value: int):
        with self.camera:
            self._score_per_minute = value
            self._refresh_score_per_minute_sprite()

    def _refresh_fps_sprite(self):
        _, right, _, top = arcade.get_viewport()
        x = right - 20
        y = top - 20
        sprite = arcade.create_text_sprite(
            f"FPS: {self._fps}", x, y, color=color.BLACK, anchor_x="right"
        )
        self._text_sprite_list.remove(self._fps_sprite)
        self._fps_sprite = sprite
        self._text_sprite_list.append(sprite)

    def _refresh_score_per_minute_sprite(self):
        _, right, _, top = arcade.get_viewport()
        x = right - 20
        y = top - 60
        sprite = arcade.create_text_sprite(
            f"Score per minute: {self._score_per_minute}",
            x,
            y,
            color=color.BLACK,
            anchor_x="right",
        )
        self._text_sprite_list.remove(self._score_per_minute_sprite)
        self._score_per_minute_sprite = sprite
        self._text_sprite_list.append(sprite)

    def update_score(self, score: int, level: int, score_to_next_level: int):
        with self.camera:
            self._score = score
            self._level = level
            self._score_to_next_level = score_to_next_level
            self._refresh_score_sprite()

    def _refresh_score_sprite(self):
        _, right, _, top = arcade.get_viewport()
        x = right - 20
        y = top - 40
        sprite = arcade.create_text_sprite(
            f"Score: {self._score}. Level: {self._level}. To next level: {self._score_to_next_level}",
            x,
            y,
            color=color.BLACK,
            anchor_x="right",
        )
        self._text_sprite_list.remove(self._score_sprite)
        self._score_sprite = sprite
        self._text_sprite_list.append(sprite)
