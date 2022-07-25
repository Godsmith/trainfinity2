from enum import Enum

import arcade
from arcade import color
from pyglet.math import Vec2


from constants import GRID_HEIGHT, GRID_WIDTH
from drawer import Drawer
from gui import Gui, Mode
from model import Train
from grid import Grid
from camera import Camera

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

MAX_PIXELS_BETWEEN_CLICK_AND_RELEASE_FOR_CLICK = 5

TRAIN_SPEED_PIXELS_PER_SECOND = 60.0


# Min zoom = 1/MAX_CAMERA_SCALE, i.e. 25%
MAX_CAMERA_SCALE = 4
# Max zoom = 1/MIN_CAMERA_SCALE, i.e. 200%
MIN_CAMERA_SCALE = 0.5


class TrainPlacementMode(Enum):
    FIRST_STATION = 1
    SECOND_STATION = 2


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

        self.fps = 0.0

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
        self.fps = 1 / delta_time
        train_displacement = delta_time * TRAIN_SPEED_PIXELS_PER_SECOND

        for train in self.trains:
            if train.x > train.target_x:
                train.x -= train_displacement
            else:
                train.x += train_displacement
            if train.y > train.target_y:
                train.y -= train_displacement
            else:
                train.y += train_displacement
            if (
                abs(train.x - train.target_x) < 1
                and abs(train.y - train.target_y) < train_displacement
            ):
                train.select_next_position_in_route()

    def on_draw(self):
        self.clear()
        self.drawer.draw()

        # Draw GUI here even though there are many draw calls, since the colors of the boxes
        # are dynamic
        # TODO: move this to drawer class
        self.gui.draw()

        self._draw_fps()

    def _draw_fps(self):
        x, y = self.camera_sprites.to_world_coordinates(
            SCREEN_WIDTH - 100, SCREEN_HEIGHT - 20
        )
        arcade.draw_text(self.fps, x, y, color=color.BLACK)

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
        # TODO: Indicate TrainPlacementMode visually
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
                            self.train_placement_station_list.clear()
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

            change_x = dx * self.camera_sprites.scale
            change_y = dy * self.camera_sprites.scale
            self.gui.pan(-change_x, -change_y)
        elif self.is_mouse1_pressed:
            x, y = self.camera_sprites.to_world_coordinates(x, y)
            self.grid.click_and_drag(
                x, y, self.mouse1_pressed_x, self.mouse1_pressed_y, self.gui.mode
            )

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        if scroll_y < 0:
            scale_delta = 0.1
        else:
            scale_delta = -0.1

        new_scale = self.camera_sprites.scale + scale_delta
        new_scale = min(new_scale, MAX_CAMERA_SCALE)
        new_scale = max(new_scale, MIN_CAMERA_SCALE)

        self.camera_sprites.scale = new_scale

        self.gui.create_boxes()


if __name__ == "__main__":
    window = MyGame()
    window.setup()
    arcade.run()
