from collections import namedtuple, defaultdict
from dataclasses import dataclass
import random
from typing import Iterable
from pyglet.math import Vec2
import arcade
import arcade.color
from arcade import Color
import math
from itertools import pairwise

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

GRID_WIDTH = 600
GRID_HEIGHT = 600
GRID_BOX_SIZE = 30
GRID_LINE_WIDTH = 1
GRID_COLOR = arcade.color.BLACK
FINISHED_RAIL_COLOR = arcade.color.RED
BUILDING_RAIL_COLOR = arcade.color.RED_BROWN
RAIL_LINE_WIDTH = 5

MAX_PIXELS_BETWEEN_CLICK_AND_RELEASE_FOR_CLICK = 5


# Min zoom = 1/MAX_CAMERA_SCALE, i.e. 25%
MAX_CAMERA_SCALE = 4
# Max zoom = 1/MIN_CAMERA_SCALE, i.e. 200%
MIN_CAMERA_SCALE = 0.5


Mine = namedtuple("Mine", "x y")
Factory = namedtuple("Factory", "x y")
Station = namedtuple("Station", "x y")


@dataclass
class Rail:
    x1: int
    y1: int
    x2: int
    y2: int

    def is_horizontal(self):
        return self.y1 == self.y2

    def is_vertical(self):
        return self.x1 == self.x2


class Camera:
    def __init__(self):
        (
            self.original_left,
            self.original_right,
            self.original_bottom,
            self.original_top,
        ) = arcade.get_viewport()

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

    def to_world_coordinates(self, x, y):
        """Convert a position x, y in the current window to world coordinates."""
        relative_x = (x - self.original_left) / (
            self.original_right - self.original_left
        )
        relative_y = (y - self.original_bottom) / (
            self.original_top - self.original_bottom
        )
        left, right, bottom, top = arcade.get_viewport()
        return int(left + (right - left) * relative_x), int(
            bottom + (top - bottom) * relative_y
        )


class Grid:
    def __init__(self) -> None:
        self.rails_being_built = []
        self.rails = []
        self.stations = []
        self.mines = self._create_mines()
        self.factories = self._create_factories()

    def _create_mines(self):
        x = random.randrange(0, GRID_WIDTH // GRID_BOX_SIZE) * GRID_BOX_SIZE
        y = random.randrange(0, GRID_HEIGHT // GRID_BOX_SIZE) * GRID_BOX_SIZE
        return [Mine(x, y)]

    def _create_factories(self):
        x = random.randrange(0, GRID_WIDTH // GRID_BOX_SIZE) * GRID_BOX_SIZE
        y = random.randrange(0, GRID_HEIGHT // GRID_BOX_SIZE) * GRID_BOX_SIZE
        return [Factory(x, y)]

    def snap_to_x(self, x) -> int:
        return math.floor(x / GRID_BOX_SIZE) * GRID_BOX_SIZE

    def snap_to_y(self, y) -> int:
        return math.floor(y / GRID_BOX_SIZE) * GRID_BOX_SIZE

    def _is_not_straight_horizontal_or_diagonal(self, xs, ys):
        return len(xs) != len(ys) and (
            (len(xs) > 1 and len(ys) != 1) or (len(ys) > 1 and len(xs) != 1)
        )

    def click_and_drag(self, x, y, start_x, start_y):
        x = self.snap_to_x(x)
        y = self.snap_to_y(y)
        start_x = self.snap_to_x(start_x)
        start_y = self.snap_to_y(start_y)

        dx = GRID_BOX_SIZE if x < start_x else -GRID_BOX_SIZE
        dy = GRID_BOX_SIZE if y < start_y else -GRID_BOX_SIZE

        xs = list(range(x, start_x + int(dx / abs(dx)), dx))
        ys = list(range(y, start_y + int(dy / abs(dy)), dy))

        if self._is_not_straight_horizontal_or_diagonal(xs, ys):
            return

        if len(xs) > len(ys):
            ys = ys * len(xs)
        elif len(ys) > len(xs):
            xs = xs * len(ys)

        self.rails_being_built = [
            Rail(x1, y1, x2, y2) for (x1, y1), (x2, y2) in pairwise(zip(xs, ys))
        ]

    def release_mouse_button(self):
        self.rails.extend(self.rails_being_built)
        self.rails_being_built.clear()

        self._add_stations()

    def _is_adjacent(self, position1, position2):
        return (
            abs(position1.x - position2.x) == GRID_BOX_SIZE
            and position1.y == position2.y
        ) or (
            abs(position1.y - position2.y) == GRID_BOX_SIZE
            and position1.x == position2.x
        )

    def _is_adjacent_to_mine_or_factory(self, position):
        for mine in self.mines:
            if self._is_adjacent(position, mine):
                return True
        for factory in self.factories:
            if self._is_adjacent(position, factory):
                return True
        return False

    def _add_stations(self):
        rails_from_position = defaultdict(list)
        for rail in self.rails:
            rails_from_position[(rail.x1, rail.y1)].append(rail)
            rails_from_position[(rail.x2, rail.y2)].append(rail)

        for (x, y), rails in rails_from_position.items():
            if len(rails) == 2:
                if all(rail.is_horizontal() for rail in rails) or all(
                    rail.is_vertical() for rail in rails
                ):
                    # Checking for existing stations might not be needed later if
                    # building rail on top of rail will be prohibited.
                    if (
                        self._is_adjacent_to_mine_or_factory(Vec2(x, y))
                        and Station(x, y) not in self.stations
                    ):
                        self.stations.append(Station(x, y))


class MyGame(arcade.Window):
    def __init__(self, visible=True):
        super().__init__(
            width=SCREEN_WIDTH,
            height=SCREEN_HEIGHT,
            title="TRAINFINITY",
            visible=visible,
        )  # type: ignore

        self.horizontal_grid_lines = []
        self.vertical_grid_lines = []

        arcade.set_background_color(arcade.color.BUD_GREEN)

        self.camera_sprites = Camera()
        self.camera_gui = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

        self.is_mouse1_pressed = False
        self.mouse1_pressed_x = 0
        self.mouse1_pressed_y = 0

        self.is_mouse2_pressed = False
        self.mouse2_pressed_x = 0
        self.mouse2_pressed_y = 0

        self.camera_position_when_mouse2_pressed = self.camera_sprites.position

        self.grid = Grid()

    def setup(self):
        pass

    def _draw_grid(self):
        for x in range(0, GRID_WIDTH + 1, GRID_BOX_SIZE):
            arcade.draw_line(x, 0, x, GRID_HEIGHT, GRID_COLOR, GRID_LINE_WIDTH)

        for y in range(0, GRID_HEIGHT + 1, GRID_BOX_SIZE):
            arcade.draw_line(0, y, GRID_WIDTH, y, GRID_COLOR, GRID_LINE_WIDTH)

    def _draw_rails(self, rails: Iterable[Rail], color: Color):
        for rail in rails:
            x1, y1, x2, y2 = [
                coordinate + GRID_BOX_SIZE / 2
                for coordinate in (rail.x1, rail.y1, rail.x2, rail.y2)
            ]
            arcade.draw_line(x1, y1, x2, y2, color, RAIL_LINE_WIDTH)

    def _draw_all_rails(self):
        self._draw_rails(self.grid.rails_being_built, BUILDING_RAIL_COLOR)
        self._draw_rails(self.grid.rails, FINISHED_RAIL_COLOR)

    def _draw_mines(self):
        for mine in self.grid.mines:
            arcade.draw_text("M", mine.x, mine.y, bold=True, font_size=24)

    def _draw_factories(self):
        for factory in self.grid.factories:
            arcade.draw_text("F", factory.x, factory.y, bold=True, font_size=24)

    def _draw_stations(self):
        for station in self.grid.stations:
            arcade.draw_text("S", station.x, station.y, bold=True, font_size=24)

    def on_draw(self):
        self.clear()

        self._draw_grid()
        self._draw_all_rails()
        self._draw_stations()
        self._draw_mines()
        self._draw_factories()

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        if button == arcade.MOUSE_BUTTON_RIGHT:
            self.mouse2_pressed_x = x
            self.mouse2_pressed_y = y
            self.is_mouse2_pressed = True
            self.camera_position_when_mouse2_pressed = self.camera_sprites.position
        elif button == arcade.MOUSE_BUTTON_LEFT:
            x, y = self.camera_sprites.to_world_coordinates(x, y)
            self.mouse1_pressed_x = x
            self.mouse1_pressed_y = y
            self.is_mouse1_pressed = True

    def _is_click(self, mouse_down_x, mouse_down_y, mouse_up_x, mouse_up_y):
        return (
            abs(mouse_down_x - mouse_up_x)
            < MAX_PIXELS_BETWEEN_CLICK_AND_RELEASE_FOR_CLICK
            and abs(mouse_down_y - mouse_up_y)
            < MAX_PIXELS_BETWEEN_CLICK_AND_RELEASE_FOR_CLICK
        )

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        if button == arcade.MOUSE_BUTTON_RIGHT:
            if self._is_click(self.mouse2_pressed_x, self.mouse2_pressed_y, x, y):
                self.on_right_click(x, y)
            self.is_mouse2_pressed = False
        elif button == arcade.MOUSE_BUTTON_LEFT:
            if self._is_click(self.mouse1_pressed_x, self.mouse1_pressed_y, x, y):
                self.on_left_click(x, y)
            self.is_mouse1_pressed = False
            self.grid.release_mouse_button()

    def on_left_click(self, x, y):
        pass

    def on_right_click(self, x, y):
        pass

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        if self.is_mouse2_pressed:
            delta = Vec2(x - self.mouse2_pressed_x, y - self.mouse2_pressed_y)

            # Required for panning to work correctly when zoomed in or out
            delta = delta.scale(self.camera_sprites.scale)

            new_position = self.camera_position_when_mouse2_pressed - delta

            min_x = -self.camera_sprites.viewport_width / 2
            max_x = GRID_WIDTH + min_x
            min_y = -self.camera_sprites.viewport_height / 2
            max_y = GRID_HEIGHT + min_y

            new_position = Vec2(max(min_x, new_position.x), new_position.y)
            new_position = Vec2(min(max_x, new_position.x), new_position.y)
            new_position = Vec2(new_position.x, max(min_y, new_position.y))
            new_position = Vec2(new_position.x, min(max_y, new_position.y))

            self.camera_sprites.move(new_position)
        elif self.is_mouse1_pressed:
            x, y = self.camera_sprites.to_world_coordinates(x, y)
            self.grid.click_and_drag(x, y, self.mouse1_pressed_x, self.mouse1_pressed_y)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        if scroll_y < 0:
            scale_delta = 0.1
        else:
            scale_delta = -0.1

        new_scale = self.camera_sprites.scale + scale_delta
        new_scale = min(new_scale, MAX_CAMERA_SCALE)
        new_scale = max(new_scale, MIN_CAMERA_SCALE)

        self.camera_sprites.scale = new_scale


def main():
    window = MyGame()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
