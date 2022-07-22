import math
import random
from collections import defaultdict
from itertools import pairwise
from typing import Optional
from enum import Enum

import arcade
from arcade import color, Color
from pyglet.math import Vec2


from constants import GRID_HEIGHT, GRID_WIDTH, GRID_BOX_SIZE
from drawer import Drawer
from gui import Gui, Mode
from model import Station, Mine, Factory, Train, Rail

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

MAX_PIXELS_BETWEEN_CLICK_AND_RELEASE_FOR_CLICK = 5

TRAIN_SPEED = 3


# Min zoom = 1/MAX_CAMERA_SCALE, i.e. 25%
MAX_CAMERA_SCALE = 4
# Max zoom = 1/MIN_CAMERA_SCALE, i.e. 200%
MIN_CAMERA_SCALE = 0.5


class TrainPlacementMode(Enum):
    FIRST_STATION = 1
    SECOND_STATION = 2


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
    def __init__(self, drawer: Drawer) -> None:
        self.drawer = drawer
        self.rails_being_built = []
        self.rails = []
        self.stations = []
        self.mines = self._create_mines()
        self.factories = self._create_factories()

    def _create_mines(self):
        x = random.randrange(0, GRID_WIDTH // GRID_BOX_SIZE) * GRID_BOX_SIZE
        y = random.randrange(0, GRID_HEIGHT // GRID_BOX_SIZE) * GRID_BOX_SIZE
        mine = Mine(x, y)
        self.drawer.create_mine(mine)
        return [mine]

    def _create_factories(self):
        x = random.randrange(0, GRID_WIDTH // GRID_BOX_SIZE) * GRID_BOX_SIZE
        y = random.randrange(0, GRID_HEIGHT // GRID_BOX_SIZE) * GRID_BOX_SIZE
        factory = Factory(x, y)
        self.drawer.create_factory(factory)
        return [factory]

    def snap_to(self, x, y) -> tuple[int, int]:
        return self.snap_to_x(x), self.snap_to_y(y)

    def snap_to_x(self, x) -> int:
        return math.floor(x / GRID_BOX_SIZE) * GRID_BOX_SIZE

    def snap_to_y(self, y) -> int:
        return math.floor(y / GRID_BOX_SIZE) * GRID_BOX_SIZE

    def connect_stations(self, station1: Station, station2: Station):
        self.rails_from_vec2 = defaultdict(list)
        for rail in self.rails:
            self.rails_from_vec2[Vec2(rail.x1, rail.y1)].append(rail)
            self.rails_from_vec2[Vec2(rail.x2, rail.y2)].append(rail)
        return self._explore([Vec2(station1.x, station1.y)], station2)

    def _explore(
        self, previous_locations: list[Vec2], target_station: Station
    ) -> Optional[list[Vec2]]:
        if (
            previous_locations[-1].x == target_station.x
            and previous_locations[-1].y == target_station.y
        ):
            return previous_locations
        next_locations = set()
        for rail in self.rails_from_vec2[previous_locations[-1]]:
            next_locations.add(Vec2(rail.x1, rail.y1))
            next_locations.add(Vec2(rail.x2, rail.y2))
        next_locations -= set(previous_locations)
        for next_location in next_locations:
            if route := self._explore(
                previous_locations + [next_location], target_station
            ):
                return route
        return None

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
        self.drawer.set_rails_being_built(self.rails_being_built)

    def release_mouse_button(self):
        self.rails.extend(self.rails_being_built)
        self.drawer.create_rail(self.rails_being_built)
        self.rails_being_built.clear()

        self._add_stations()

    def get_station(self, x, y) -> Optional[Station]:
        x, y = self.snap_to(x, y)
        if Station(x, y) in self.stations:
            return Station(x, y)

    def _is_adjacent(self, position1, position2):
        return (
            abs(position1.x - position2.x) == GRID_BOX_SIZE
            and position1.y == position2.y
        ) or (
            abs(position1.y - position2.y) == GRID_BOX_SIZE
            and position1.x == position2.x
        )

    def _is_adjacent_to_mine_or_factory(self, position):
        return any(
            self._is_adjacent(position, position2)
            for position2 in self.mines + self.factories  # type: ignore
        )

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
                        station = Station(x, y)
                        self.stations.append(station)
                        self.drawer.create_station(station)


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

        arcade.set_background_color(color.BUD_GREEN)

        self.is_mouse1_pressed = False
        self.mouse1_pressed_x = 0
        self.mouse1_pressed_y = 0

        self.is_mouse2_pressed = False
        self.mouse2_pressed_x = 0
        self.mouse2_pressed_y = 0

        # This is repeated in setup() below
        self.camera_sprites = Camera()
        self.camera_position_when_mouse2_pressed = self.camera_sprites.position

        self.drawer = Drawer()
        self.grid = Grid(self.drawer)
        self.gui = Gui()

        self.trains = []
        self.train_placement_mode = TrainPlacementMode.FIRST_STATION
        self.train_placement_station_list = []

    def setup(self):
        arcade.set_viewport(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT)
        self.camera_sprites = Camera()
        self.camera_position_when_mouse2_pressed = self.camera_sprites.position

        self.drawer = Drawer()
        self.grid = Grid(self.drawer)
        self.gui = Gui()

        self.trains = []
        self.train_placement_mode = TrainPlacementMode.FIRST_STATION
        self.train_placement_station_list = []

    def on_update(self, delta_time):
        for train in self.trains:
            if train.x > train.target_x:
                train.x -= TRAIN_SPEED
            else:
                train.x += TRAIN_SPEED
            if train.y > train.target_y:
                train.y -= TRAIN_SPEED
            else:
                train.y += TRAIN_SPEED
            if (
                abs(train.x - train.target_x) < 1
                and abs(train.y - train.target_y) < TRAIN_SPEED
            ):
                train.select_next_position_in_route()

    def on_draw(self):
        self.clear()
        self.drawer.draw()

        # Draw GUI here even though there are many draw calls, since the colors of the boxes
        # are dynamic
        # TODO: move this to drawer class
        self.gui.draw()

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
        x, y = self.camera_sprites.to_world_coordinates(x, y)
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
        if self.gui.on_left_click(x, y):
            return
        # TODO: if train view is selected again, revert to TrainPlacementMode.FIRST_STATION
        # TODO: Abort by pressing Escape
        # TODO: Extract to class with separate state
        elif self.gui.mode == Mode.TRAIN:
            if station := self.grid.get_station(x, y):
                match self.train_placement_mode:
                    case TrainPlacementMode.FIRST_STATION:
                        self.train_placement_station_list.append(station)
                        self.train_placement_mode = TrainPlacementMode.SECOND_STATION
                    case _:  # second station
                        self.train_placement_mode = TrainPlacementMode.FIRST_STATION
                        self.train_placement_station_list.append(station)
                        if route := self.grid.connect_stations(
                            *self.train_placement_station_list
                        ):
                            train = Train(
                                self.train_placement_station_list[0],
                                self.train_placement_station_list[1],
                                route,
                            )
                            self.trains.append(train)
                            self.drawer.create_train(train)
                            self.gui.mode = Mode.SELECT
                            # TODO: Select train here

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


if __name__ == "__main__":
    window = MyGame()
    # Not needed right now
    window.setup()
    arcade.run()
