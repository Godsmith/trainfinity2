import arcade
from pyglet.math import Vec2


class Camera:
    def __init__(self):
        (
            self.original_left,
            self.original_right,
            self.original_bottom,
            self.original_top,
        ) = arcade.get_viewport()
        print(arcade.get_viewport())

    @property
    def position(self):
        x, _, y, _ = arcade.get_viewport()
        return Vec2(x, y)

    @property
    def scale(self):
        left, right, _, _ = arcade.get_viewport()

        return (right - left) / (self.original_right - self.original_left)

    @scale.setter
    def scale(self, number):
        original_width = self.original_right - self.original_left
        new_width = original_width * number
        original_height = self.original_top - self.original_bottom
        new_height = original_height * number
        left, right, bottom, top = arcade.get_viewport()
        width_difference = (right - left) - new_width
        height_difference = (top - bottom) - new_height

        # arcade.set_viewport(left, left + new_width, bottom, bottom + new_height)
        arcade.set_viewport(
            left + width_difference / 2,
            right - width_difference / 2,
            bottom + height_difference / 2,
            top - height_difference / 2,
        )

    @property
    def viewport_width(self):
        left, right, _, _ = arcade.get_viewport()
        return right - left

    @property
    def viewport_height(self):
        _, _, bottom, top = arcade.get_viewport()
        return top - bottom

    def move(self, position: Vec2):
        left, right, bottom, top = arcade.get_viewport()
        dx, dy = position - Vec2(left, bottom)
        arcade.set_viewport(left + dx, right + dx, bottom + dy, top + dy)

    def to_world_coordinates(self, x, y) -> tuple[int, int]:
        """Convert a position x, y in the current window to world coordinates."""
        relative_x = x / (self.original_right - self.original_left)
        relative_y = y / (self.original_top - self.original_bottom)
        left, right, bottom, top = arcade.get_viewport()
        return int(left + (right - left) * relative_x), int(
            bottom + (top - bottom) * relative_y
        )
