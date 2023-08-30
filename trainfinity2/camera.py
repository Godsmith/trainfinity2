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
        self.left = self.original_left
        self.right = self.original_right
        self.bottom = self.original_bottom
        self.top = self.original_top
        self._old_viewport = (0, 0, 0, 0)
        self._is_active = False

    def __enter__(self):
        if not self._is_active:
            self._old_viewport = arcade.get_viewport()
            self._is_active = True
            self.set_viewport()

    def __exit__(self, exc_type, exc_value, traceback):
        arcade.set_viewport(*self._old_viewport)
        self._is_active = False

    @property
    def position(self):
        return Vec2(self.left, self.bottom)

    @property
    def scale(self):
        return (self.right - self.left) / (self.original_right - self.original_left)

    @scale.setter
    def scale(self, number):
        original_width = self.original_right - self.original_left
        new_width = original_width * number
        original_height = self.original_top - self.original_bottom
        new_height = original_height * number
        width_difference = (self.right - self.left) - new_width
        height_difference = (self.top - self.bottom) - new_height

        self.left += width_difference / 2
        self.right -= width_difference / 2
        self.bottom += height_difference / 2
        self.top -= height_difference / 2

        self.set_viewport()

    @property
    def viewport_width(self):
        left, right, _, _ = arcade.get_viewport()
        return right - left

    @property
    def viewport_height(self):
        _, _, bottom, top = arcade.get_viewport()
        return top - bottom

    def move(self, position: Vec2):
        dx, dy = position - Vec2(self.left, self.bottom)
        self.left = self.left + dx
        self.right = self.right + dx
        self.bottom = self.bottom + dy
        self.top = self.top + dy
        self.set_viewport()

    def to_world_coordinates(self, x, y) -> tuple[int, int]:
        """Convert a position x, y in the current window to world coordinates."""
        relative_x = x / (self.original_right - self.original_left)
        relative_y = y / (self.original_top - self.original_bottom)
        left, right, bottom, top = arcade.get_viewport()
        return int(left + (right - left) * relative_x), int(
            bottom + (top - bottom) * relative_y
        )

    def set_viewport(self):
        arcade.set_viewport(self.left, self.right, self.bottom, self.top)

    def resize(self, width, height):
        # Currently, the zoom always resets when resizing
        self.right = self.left + width
        self.top = self.bottom + height
        self.original_right = width
        self.original_top = height
        self.set_viewport()
