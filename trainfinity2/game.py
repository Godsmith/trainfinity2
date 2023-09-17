from collections import deque
from dataclasses import dataclass
from itertools import combinations

import arcade
from pyglet.math import Vec2

from trainfinity2.events import Event

from .camera import Camera
from .constants import (
    GRID_HEIGHT_PIXELS,
    GRID_WIDTH_PIXELS,
    SECONDS_BETWEEN_CARGO_CREATION,
)
from .graphics.drawer import Drawer
from .grid import (
    Grid,
)
from .gui import Gui, Mode
from .model import Player, Station
from .signal_controller import SignalController
from .terrain import Terrain
from .train import Train

MAX_PIXELS_BETWEEN_CLICK_AND_RELEASE_FOR_CLICK = 5
# Min zoom = 1/MAX_CAMERA_SCALE, i.e. 25%
MAX_CAMERA_SCALE = 4
# Max zoom = 1/MIN_CAMERA_SCALE, i.e. 200%
MIN_CAMERA_SCALE = 0.5


@dataclass(frozen=True)
class _TrainPlacerSession:
    station: Station


@dataclass
class _TrainPlacer:
    drawer: Drawer
    _session: _TrainPlacerSession | None = None

    @property
    def session(self):
        return self._session

    def start_session(self, station: Station):
        self._session = _TrainPlacerSession(station)
        self.drawer.highlight(station.positions)

    def stop_session(self):
        self._session = None
        self.drawer.highlight([])


class Game:
    def __init__(self):
        self.is_mouse1_pressed = False
        self.mouse1_pressed_x = 0
        self.mouse1_pressed_y = 0

        self.is_mouse2_pressed = False
        self.mouse2_pressed_x = 0
        self.mouse2_pressed_y = 0

        self.frame_count = 0
        self.score_last_second = 0
        self.score_increase_per_second_last_minute: deque[int] = deque(maxlen=60)
        self.seconds_since_last_gui_figures_update = 0.0

    def setup(self, terrain: Terrain):
        self.camera = Camera()
        self.camera_position_when_mouse2_pressed = self.camera.position

        self.gui_camera = Camera()
        self.gui = Gui(self.gui_camera)

        self.trains: list[Train] = []

        self.signal_controller = SignalController()
        self.grid = Grid(terrain, self.signal_controller)
        self.drawer = Drawer()

        self.player = Player(self.gui, self.level_up)
        self.player.level_up()
        self.player.update_score_in_gui()

        self.cargo_counter = 0.0

        self.drawer.create_grid(self.grid)
        self.drawer.create_terrain(
            water=terrain.water, sand=terrain.sand, mountains=terrain.mountains
        )

        self._train_placer = _TrainPlacer(self.drawer)

    def try_create_cargo_in_all_buildings(self):
        for building in self.grid.buildings.values():
            self.drawer.handle_events([building.try_create_cargo()])

    def on_update(self, delta_time):
        self.cargo_counter += delta_time
        if self.cargo_counter > SECONDS_BETWEEN_CARGO_CREATION:
            self.try_create_cargo_in_all_buildings()
            self.cargo_counter = 0.0
        self._update_gui_figures(delta_time)

        for train in self.trains:
            self.drawer.handle_events(train.move(delta_time))

        for train1, train2 in combinations(self.trains, 2):
            if train1.is_colliding_with(train2):
                self._destroy_train(train1)
                self._destroy_train(train2)
        self.drawer.update()

    def _destroy_train(self, train: Train):
        train.destroy()
        self.drawer.destroy_train(train)
        self.trains.remove(train)

    def _update_gui_figures(self, delta_time):
        self.frame_count += 1
        self.seconds_since_last_gui_figures_update += delta_time
        if self.seconds_since_last_gui_figures_update > 1:
            self.gui.update_fps_number(self.frame_count)
            self.frame_count = 0

            self.score_increase_per_second_last_minute.append(
                self.player.score - self.score_last_second
            )
            self.score_last_second = self.player.score
            self.gui.update_score_per_minute(
                sum(self.score_increase_per_second_last_minute)
            )

            self.seconds_since_last_gui_figures_update -= 1

    def on_draw(self):
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
            self.camera_position_when_mouse2_pressed = self.camera.position
        elif button == arcade.MOUSE_BUTTON_LEFT:
            if self.gui.on_mouse_press(x, y):
                return
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
            self.is_mouse2_pressed = False
        elif button == arcade.MOUSE_BUTTON_LEFT:
            if self.gui.mouse_press_mode:
                self._train_placer.stop_session()
                for train in self.trains:
                    train.selected = False
                return self.gui.on_mouse_release(x, y)
            self.is_mouse1_pressed = False
            if self._is_click(
                self.mouse1_pressed_x,
                self.mouse1_pressed_y,
                x,
                y,
            ):
                self.on_left_click(x, y)
            self.drawer.handle_events(self.grid.release_mouse_button(self.gui.mode))

    def on_left_click(self, x, y):
        world_x, world_y = self.camera.to_world_coordinates(x, y)
        if self.gui.mode == Mode.TRAIN:
            if station := self.grid.get_station(world_x, world_y):
                if not self._train_placer.session:
                    self._train_placer.start_session(station)
                else:
                    first_station = self._train_placer.session.station
                    # If signal block for first station is reserved, do not create train
                    if self.signal_controller.reserver(first_station.positions[0]):
                        return []
                    if self.grid.find_route_between_stations(first_station, station):
                        self._create_train(self._train_placer.session.station, station)
                    self._train_placer.stop_session()
        elif self.gui.mode == Mode.SELECT:
            for train in self.trains:
                if train.is_close_enough_to_click(world_x, world_y):
                    train.selected = True
                    return
                else:
                    train.selected = False
        elif self.gui.mode == Mode.SIGNAL:
            world_x_float, world_y_float = self.camera.to_world_coordinates_no_rounding(
                x, y
            )
            self.drawer.handle_events(
                self.grid.toggle_signals_at_click_position(world_x_float, world_y_float)
            )
        elif self.gui.mode == Mode.DESTROY:
            self.drawer.handle_events(self.grid.remove_rail(Vec2(world_x, world_y)))
            self.drawer.show_rails_to_be_destroyed(set())

    def _create_train(
        self, station1: Station, station2: Station, *, wagon_count: int = 3
    ):
        train = Train(
            self.player,
            station1,
            station2,
            self.grid,
            self.signal_controller,
            wagon_count=wagon_count,
        )
        self.trains.append(train)
        self.drawer.create_train(train)
        self.gui.mode = Mode.SELECT
        train.selected = True
        return train

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        events: list[Event] = []
        world_x, world_y = self.camera.to_world_coordinates(x, y)
        if self.is_mouse2_pressed:
            self._on_mouse_move_when_mouse_2_pressed(x, y)
        elif self.is_mouse1_pressed:
            pressed_world_x, pressed_world_y = self.camera.to_world_coordinates(
                self.mouse1_pressed_x, self.mouse1_pressed_y
            )
            events.extend(
                self.grid.click_and_drag(
                    world_x,
                    world_y,
                    pressed_world_x,
                    pressed_world_y,
                    self.gui.mode,
                )
            )

        elif self.gui.mode == Mode.TRAIN and self._train_placer.session:
            if station := self.grid.get_station(world_x, world_y):
                if rails := self.grid.find_route_between_stations(
                    self._train_placer.session.station, station
                ):
                    positions = {
                        position for rail in rails for position in rail.positions
                    }
                    self.drawer.highlight(positions)
            else:
                self.drawer.highlight(self._train_placer.session.station.positions)

        elif self.gui.mode == Mode.SIGNAL:
            world_x_float, world_y_float = self.camera.to_world_coordinates_no_rounding(
                x, y
            )
            events.append(self.grid.show_signal_outline(world_x_float, world_y_float))

        elif self.gui.mode == Mode.DESTROY:
            self.drawer.show_rails_to_be_destroyed(
                self.grid.rails_at_position(Vec2(world_x, world_y))
            )

        self.drawer.handle_events(events)

    def _on_mouse_move_when_mouse_2_pressed(self, x, y):
        delta = Vec2(x - self.mouse2_pressed_x, y - self.mouse2_pressed_y)
        delta = delta.scale(self.camera.scale)
        new_position = self.camera_position_when_mouse2_pressed - delta
        min_x = -self.camera.viewport_width / 2
        max_x = GRID_WIDTH_PIXELS + min_x
        min_y = -self.camera.viewport_height / 2
        max_y = GRID_HEIGHT_PIXELS + min_y
        new_position = Vec2(max(min_x, new_position.x), new_position.y)
        new_position = Vec2(min(max_x, new_position.x), new_position.y)
        new_position = Vec2(new_position.x, max(min_y, new_position.y))
        new_position = Vec2(new_position.x, min(max_y, new_position.y))
        self.camera.move(new_position)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        scale_delta = 0.1 if scroll_y < 0 else -0.1
        new_scale = self.camera.scale + scale_delta
        new_scale = min(new_scale, MAX_CAMERA_SCALE)
        new_scale = max(new_scale, MIN_CAMERA_SCALE)

        self.camera.scale = new_scale

    def on_resize(self, width, height):
        self.camera.resize(width, height)
        self.gui_camera.resize(width, height)
        self.camera.set_viewport()
        self.gui.refresh_text()

    def level_up(self, level: int):
        self.drawer.handle_events(self.grid.level_up(level))
        self.drawer.create_grid(self.grid)
