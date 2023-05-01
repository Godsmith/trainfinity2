from collections import deque
from dataclasses import dataclass
from itertools import combinations
from typing import Any

import arcade
from pyglet.math import Vec2

from .camera import Camera
from .constants import GRID_HEIGHT, GRID_WIDTH, SECONDS_BETWEEN_IRON_CREATION
from .graphics.drawer import Drawer
from .grid import Grid, RailsBeingBuiltEvent
from .gui import Gui, Mode
from .model import Player, Signal, Station
from .observer import ChangeEvent, CreateEvent, DestroyEvent, Event
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
        self.drawer.highlight([station.position])

    def stop_session(self):
        self._session = None
        self.drawer.highlight([])


class Game:
    def __init__(self):
        self.horizontal_grid_lines = []
        self.vertical_grid_lines = []

        self.is_mouse1_pressed = False
        self.mouse1_pressed_x = 0
        self.mouse1_pressed_y = 0

        self.is_mouse2_pressed = False
        self.mouse2_pressed_x = 0
        self.mouse2_pressed_y = 0

        self.frame_count = 0
        self.score_last_second = 0
        self.score_increase_per_second_last_minute = deque(maxlen=60)
        self.seconds_since_last_gui_figures_update = 0.0

    def setup(self, terrain: Terrain):
        self.camera = Camera()
        self.camera_position_when_mouse2_pressed = self.camera.position

        self.gui = Gui()

        self.trains: list[Train] = []

        self.signal_controller = SignalController()
        self.grid = Grid(terrain, self.signal_controller)
        self.drawer = Drawer()
        self.grid.add_observer(self.drawer, CreateEvent)
        self.grid.add_observer(self.drawer, DestroyEvent)
        self.grid.add_observer(self.drawer, RailsBeingBuiltEvent)
        self.grid.create_buildings()

        self.player = Player(self.gui, self.grid)

        self.iron_counter = 0

        self.drawer.upsert(self.grid)
        self.drawer.create_terrain(
            water=terrain.water, sand=terrain.sand, mountains=terrain.mountains
        )

        self._train_placer = _TrainPlacer(self.drawer)

    def on_update(self, delta_time):
        self.iron_counter += delta_time
        if self.iron_counter > SECONDS_BETWEEN_IRON_CREATION:
            for mine in self.grid.mines.values():
                mine.add_iron()
            self.iron_counter = 0

        self._update_gui_figures(delta_time)

        for train in self.trains:
            train.move(delta_time)

        for train1, train2 in combinations(self.trains, 2):
            if train1.is_colliding_with(train2):
                train1.destroy()
                train2.destroy()
        self.drawer.update()

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
            x, y = self.camera.to_world_coordinates(x, y)
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
        x, y = self.camera.to_world_coordinates(x, y)
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
            self._train_placer.stop_session()
            for train in self.trains:
                train.selected = False
            return
        elif self.gui.mode == Mode.TRAIN:
            if station := self.grid.get_station(x, y):
                if not self._train_placer.session:
                    self._train_placer.start_session(station)
                else:
                    first_station = self._train_placer.session.station
                    # If signal block for first station is reserved, do not create train
                    if self.signal_controller.reserver(first_station.position):
                        return
                    if self.grid.find_route_between_stations(first_station, station):
                        self._create_train(self._train_placer.session.station, station)
                    self._train_placer.stop_session()
        elif self.gui.mode == Mode.SELECT:
            for train in self.trains:
                if train.is_at(x, y):
                    train.selected = True
                    return
                else:
                    train.selected = False
        elif self.gui.mode == Mode.SIGNAL:
            self.create_signals_at_click_position(x, y)

    def create_signals_at_click_position(self, x, y) -> list[Signal]:
        signals = self.grid.create_signals_at_click_position(x, y)
        for signal in signals:
            signal.add_observer(self.drawer, ChangeEvent)
        return signals

    def create_signals_at_grid_position(self, x, y) -> list[Signal]:
        signals = self.grid.create_signals_at_grid_position(x, y)
        for signal in signals:
            signal.add_observer(self.drawer, ChangeEvent)
        return signals

    def _create_train(self, station1: Station, station2: Station):
        train = Train(
            self.player, station1, station2, self.grid, self.signal_controller
        )
        self.trains.append(train)
        train.add_observer(self, DestroyEvent)
        self.drawer.create_train(train)
        self.gui.mode = Mode.SELECT
        train.selected = True
        return train

    def on_notify(self, object: Any, event: Event):
        match object, event:
            case Train(), DestroyEvent():
                self.trains.remove(object)

    def on_right_click(self, x, y):
        pass

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        if self.is_mouse2_pressed:
            self._on_mouse_move_when_mouse_2_pressed(x, y)
        elif self.is_mouse1_pressed:
            x, y = self.camera.to_world_coordinates(x, y)
            self.grid.click_and_drag(
                x, y, self.mouse1_pressed_x, self.mouse1_pressed_y, self.gui.mode
            )

        elif self.gui.mode == Mode.TRAIN and self._train_placer.session:
            x, y = self.camera.to_world_coordinates(x, y)
            if station := self.grid.get_station(x, y):
                if rails := self.grid.find_route_between_stations(
                    self._train_placer.session.station, station
                ):
                    positions = {
                        position for rail in rails for position in rail.positions
                    }
                    self.drawer.highlight(positions)
            else:
                self.drawer.highlight([self._train_placer.session.station.position])

    def _on_mouse_move_when_mouse_2_pressed(self, x, y):
        delta = Vec2(x - self.mouse2_pressed_x, y - self.mouse2_pressed_y)
        delta = delta.scale(self.camera.scale)
        previous_camera_position = self.camera.position
        new_position = self.camera_position_when_mouse2_pressed - delta
        min_x = -self.camera.viewport_width / 2
        max_x = GRID_WIDTH + min_x
        min_y = -self.camera.viewport_height / 2
        max_y = GRID_HEIGHT + min_y
        new_position = Vec2(max(min_x, new_position.x), new_position.y)
        new_position = Vec2(min(max_x, new_position.x), new_position.y)
        new_position = Vec2(new_position.x, max(min_y, new_position.y))
        new_position = Vec2(new_position.x, min(max_y, new_position.y))
        self.camera.move(new_position)
        camera_dx, camera_dy = new_position - previous_camera_position
        self.gui.pan(camera_dx, camera_dy)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        scale_delta = 0.1 if scroll_y < 0 else -0.1
        new_scale = self.camera.scale + scale_delta
        new_scale = min(new_scale, MAX_CAMERA_SCALE)
        new_scale = max(new_scale, MIN_CAMERA_SCALE)

        self.camera.scale = new_scale

        self.gui.refresh()

    def on_resize(self, width, height):
        self.camera = Camera()
        self.gui.refresh()
