import typing
from collections import defaultdict
from typing import Any, Collection, Iterable

import arcade
from arcade import Shape, color
from pyglet.math import Vec2

from trainfinity2.graphics.rail_shapes import get_rail_shapes
from trainfinity2.graphics.train_drawer import TrainDrawer

from ..constants import (
    BUILDING_RAIL_COLOR,
    FINISHED_RAIL_COLOR,
    BUILDING_ILLEGAL_RAIL_COLOR,
    GRID_BOX_SIZE_PIXELS,
    GRID_COLOR,
    GRID_LINE_WIDTH,
    HIGHLIGHT_COLOR,
    IRON_SIZE,
    PIXEL_OFFSET_PER_IRON,
    RAIL_TO_BE_DESTROYED_COLOR,
)
from ..grid import Grid, RailsBeingBuiltEvent, StationBeingBuiltEvent
from ..model import (
    Building,
    Factory,
    IronAddedEvent,
    IronRemovedEvent,
    Mine,
    Rail,
    Signal,
    SignalColor,
    Station,
)
from ..observer import ChangeEvent, CreateEvent, DestroyEvent, Event
from ..train import Train


class _ShapeElementList:
    """Wrapper class for arcade.ShapeElementList that recreates the list
    if the last element is removed, because the draw() method crashes
    if trying to draw an empty list."""

    def __init__(self) -> None:
        self._list = arcade.ShapeElementList[Shape]()

    def __len__(self) -> int:
        return len(self._list)

    def append(self, obj: Any):
        self._list.append(obj)

    def remove(self, obj: Any):
        self._list.remove(obj)
        if not self._list:
            self._list = arcade.ShapeElementList()

    def draw(self):
        self._list.draw()

    def clear(self):
        self._list = arcade.ShapeElementList()


class Drawer:
    def __init__(self):

        self._grid_shape_list = _ShapeElementList()
        self._shape_list = _ShapeElementList()
        self._sprite_list = arcade.SpriteList()

        # Needed to easily remove sprites and shapes
        self.iron_shapes_from_position = defaultdict(list)

        self._sprites_from_object_id = defaultdict(list)
        self._shapes_from_object_id = defaultdict(list)
        self._rail_shapes_from_object_id = defaultdict(list)
        self._signal_shapes_from_object_id = defaultdict(list)

        self._rail_shape_list = _ShapeElementList()
        self._signal_shape_list = _ShapeElementList()

        self._previous_rails_to_be_marked_as_to_be_destroyed: set[Rail] = set()
        self._rail_to_be_destroyed_shape_list = _ShapeElementList()

        self._rails_being_built: set[Rail] = set()
        self.rails_being_built_shape_element_list = _ShapeElementList()

        self._station_being_built: Station | None = None
        self.stations_being_built_shape_element_list = _ShapeElementList()

        self.iron_shape_element_list = _ShapeElementList()

        self.highlight_shape_element_list = _ShapeElementList()

        self._train_drawer = TrainDrawer()

        self._fps_sprite = arcade.Sprite()
        self._score_sprite = arcade.Sprite()
        self._sprite_list.append(self._fps_sprite)
        self._sprite_list.append(self._score_sprite)

    def upsert(self, object: Any):
        match object:
            case Grid():
                self._create_grid(object)
            case Mine() | Factory() | Station():
                self._create_building(object)
            case Rail():
                self._create_rail(object)
            case Signal():
                self._update_signal(object)
            case _:
                raise ValueError(f"Received unknown object {object}")

    def _remove(self, object: Any):
        for sprite in self._sprites_from_object_id[id(object)]:
            self._sprite_list.remove(sprite)
        del self._sprites_from_object_id[id(object)]
        for shape in self._shapes_from_object_id[id(object)]:
            self._shape_list.remove(shape)
        del self._shapes_from_object_id[id(object)]
        for rail_shape in self._rail_shapes_from_object_id[id(object)]:
            self._rail_shape_list.remove(rail_shape)
        del self._rail_shapes_from_object_id[id(object)]
        for signal_shape in self._signal_shapes_from_object_id[id(object)]:
            self._signal_shape_list.remove(signal_shape)
        del self._signal_shapes_from_object_id[id(object)]

    def _create_grid(self, grid: Grid):
        self._grid_shape_list = _ShapeElementList()
        for x in range(
            grid.left * GRID_BOX_SIZE_PIXELS,
            grid.right * GRID_BOX_SIZE_PIXELS + 1,
            GRID_BOX_SIZE_PIXELS,
        ):
            self._grid_shape_list.append(
                arcade.create_line(
                    x,
                    grid.bottom * GRID_BOX_SIZE_PIXELS,
                    x,
                    grid.top * GRID_BOX_SIZE_PIXELS,
                    GRID_COLOR,
                    GRID_LINE_WIDTH,
                )
            )

        for y in range(
            grid.bottom * GRID_BOX_SIZE_PIXELS,
            grid.top * GRID_BOX_SIZE_PIXELS + 1,
            GRID_BOX_SIZE_PIXELS,
        ):
            self._grid_shape_list.append(
                arcade.create_line(
                    grid.left * GRID_BOX_SIZE_PIXELS,
                    y,
                    grid.right * GRID_BOX_SIZE_PIXELS,
                    y,
                    GRID_COLOR,
                    GRID_LINE_WIDTH,
                )
            )

    def _create_building(self, building: Building):
        match building:
            case Factory():
                sprite = arcade.Sprite(
                    "images/factory.png",
                    0.75,
                    center_x=building.position.x * GRID_BOX_SIZE_PIXELS
                    + GRID_BOX_SIZE_PIXELS / 2,
                    center_y=building.position.y * GRID_BOX_SIZE_PIXELS
                    + GRID_BOX_SIZE_PIXELS / 2,
                )
                self._add_sprite(sprite, building)
            case Mine():
                sprite = arcade.Sprite(
                    "images/mine.png",
                    0.75,
                    center_x=building.position.x * GRID_BOX_SIZE_PIXELS
                    + GRID_BOX_SIZE_PIXELS / 2,
                    center_y=building.position.y * GRID_BOX_SIZE_PIXELS
                    + GRID_BOX_SIZE_PIXELS / 2,
                )
                self._add_sprite(sprite, building)
            case Station():
                self._add_station(building)

    def _get_station_shapes(self, station: Station, is_building: bool = False):
        def set_alpha(color_: tuple[int, int, int]) -> tuple[int, int, int, int]:
            alpha = 128 if is_building else 255
            return (*color_, alpha)

        shapes = []
        for position in station.positions:
            ground_shape = arcade.create_rectangle_filled(
                position.x * GRID_BOX_SIZE_PIXELS + GRID_BOX_SIZE_PIXELS / 2,
                position.y * GRID_BOX_SIZE_PIXELS + GRID_BOX_SIZE_PIXELS / 2,
                GRID_BOX_SIZE_PIXELS,
                GRID_BOX_SIZE_PIXELS,
                set_alpha(color.ASH_GREY),
            )
            shapes.append(ground_shape)

        house_position = Vec2(
            (
                station.positions[0].x * GRID_BOX_SIZE_PIXELS
                + station.positions[-1].x * GRID_BOX_SIZE_PIXELS
            )
            / 2,
            (
                station.positions[0].y * GRID_BOX_SIZE_PIXELS
                + station.positions[-1].y * GRID_BOX_SIZE_PIXELS
            )
            / 2,
        )
        x = house_position.x + GRID_BOX_SIZE_PIXELS / 2
        y = house_position.y + GRID_BOX_SIZE_PIXELS / 7
        width = GRID_BOX_SIZE_PIXELS * 3 / 4
        height = GRID_BOX_SIZE_PIXELS / 4
        if not station.east_west:
            x = house_position.x + GRID_BOX_SIZE_PIXELS / 7
            y = house_position.y + GRID_BOX_SIZE_PIXELS / 2
            width, height = height, width
        house_shape = arcade.create_rectangle_filled(
            x,
            y,
            width,
            height,
            set_alpha(color.DARK_BROWN),
        )
        shapes.append(house_shape)
        return shapes

    def _add_station(self, station: Station):
        for shape in self._get_station_shapes(station):
            self._add_shape(shape, station)

    def _update_signal(self, signal: Signal):
        self._remove(signal)
        positions = list(signal.rail.positions)
        middle_of_rail = positions[0].lerp(positions[1], 0.5)
        position = middle_of_rail.lerp(signal.from_position, 0.5)
        position = Vec2(
            position.x * GRID_BOX_SIZE_PIXELS + GRID_BOX_SIZE_PIXELS / 2,
            position.y * GRID_BOX_SIZE_PIXELS + GRID_BOX_SIZE_PIXELS / 2,
        )
        shape = arcade.create_ellipse_filled(
            position.x,
            position.y,
            GRID_BOX_SIZE_PIXELS / 6,
            GRID_BOX_SIZE_PIXELS / 6,
            color.RED if signal.signal_color == SignalColor.RED else color.GREEN,
        )
        self._add_signal_shape(shape, signal)

    def _add_sprite(self, sprite: arcade.Sprite, object: Any):
        self._sprite_list.append(sprite)
        self._sprites_from_object_id[id(object)].append(sprite)

    def _add_shape(self, shape: arcade.Shape, object: Any):
        self._shape_list.append(shape)
        self._shapes_from_object_id[id(object)].append(shape)

    def _add_rail_shape(self, shape: arcade.Shape, object: Any):
        self._rail_shape_list.append(shape)
        self._rail_shapes_from_object_id[id(object)].append(shape)

    def _add_signal_shape(self, shape: arcade.Shape, object: Any):
        self._signal_shape_list.append(shape)
        self._signal_shapes_from_object_id[id(object)].append(shape)

    def create_terrain(
        self,
        water: Collection[Vec2],
        sand: Collection[Vec2],
        mountains: Collection[Vec2],
    ):
        print(f"{len(water)=}, {len(sand)=}, {len(mountains)=}")
        for positions, terrain_color in [
            (water, color.SEA_BLUE),
            (sand, color.SAND),
            (mountains, color.DIM_GRAY),
        ]:
            for position in positions:
                self._create_terrain(position, terrain_color)

    def _create_terrain(self, position: Vec2, color):
        center_x = position.x * GRID_BOX_SIZE_PIXELS + GRID_BOX_SIZE_PIXELS / 2
        center_y = position.y * GRID_BOX_SIZE_PIXELS + GRID_BOX_SIZE_PIXELS / 2
        shape = arcade.create_rectangle_filled(
            center_x, center_y, GRID_BOX_SIZE_PIXELS, GRID_BOX_SIZE_PIXELS, color=color
        )
        self._shape_list.append(shape)

    def create_train(self, train: Train):
        self._train_drawer.add(train)
        train.add_observer(self, DestroyEvent)

    def on_notify(self, object: Any, event: Event):
        match (object, event):
            case Mine(), IronAddedEvent():
                event = typing.cast(IronAddedEvent, event)
                self._add_iron(event.position)
            case Mine(), IronRemovedEvent():
                event = typing.cast(IronRemovedEvent, event)
                self._remove_iron(event.position, event.amount)
            case Mine(), CreateEvent():
                self.upsert(object)
                object.add_observer(self, IronAddedEvent)
                object.add_observer(self, IronRemovedEvent)
            case Train(), DestroyEvent():
                self._train_drawer.remove(object)
            case Rail(), DestroyEvent():
                self._remove(object)
            case Mine() | Station() | Factory() | Signal(), DestroyEvent():
                self._remove(object)
            case Rail(), CreateEvent():
                self.upsert(object)
            case Grid(), RailsBeingBuiltEvent():
                event = typing.cast(RailsBeingBuiltEvent, event)
                self._show_rails_being_built(event.rails)
            case Grid(), StationBeingBuiltEvent():
                event = typing.cast(StationBeingBuiltEvent, event)
                self._show_station_being_built(event.station, event.illegal_positions)
            case Factory() | Station(), CreateEvent():
                self.upsert(object)
            case Signal(), CreateEvent() | ChangeEvent():
                self.upsert(object)
            case _:
                raise ValueError(
                    f"Received unexpected combination {object} and {event}"
                )

    def _add_iron(self, position: Vec2):
        x, y = position.x * GRID_BOX_SIZE_PIXELS, position.y * GRID_BOX_SIZE_PIXELS
        x += len(self.iron_shapes_from_position[position]) * int(
            PIXEL_OFFSET_PER_IRON / 2
        )
        filled_rectangle = arcade.create_rectangle_filled(
            x,
            y,
            IRON_SIZE,
            IRON_SIZE,
            color=color.TROLLEY_GREY,
        )
        rectangle_outline = arcade.create_rectangle_outline(
            x,
            y,
            IRON_SIZE,
            IRON_SIZE,
            color=color.BLACK,
        )
        self.iron_shapes_from_position[position].append(filled_rectangle)
        self.iron_shapes_from_position[position].append(rectangle_outline)
        self.iron_shape_element_list.append(filled_rectangle)
        self.iron_shape_element_list.append(rectangle_outline)

    def _remove_iron(self, position: Vec2, amount: int):
        for _ in range(amount):
            filled_rectangle = self.iron_shapes_from_position[position].pop()
            rectangle_outline = self.iron_shapes_from_position[position].pop()
            self.iron_shape_element_list.remove(filled_rectangle)
            self.iron_shape_element_list.remove(rectangle_outline)

    def _show_rails_being_built(self, rails: set[Rail]):
        if rails != self._rails_being_built:
            self.rails_being_built_shape_element_list = _ShapeElementList()
            for rail in rails:
                color = (
                    BUILDING_RAIL_COLOR if rail.legal else BUILDING_ILLEGAL_RAIL_COLOR
                )
                rail_shapes = get_rail_shapes(rail, color)
                for rail_shape in rail_shapes:
                    self.rails_being_built_shape_element_list.append(rail_shape)
            self._rails_being_built = rails

    def _show_station_being_built(
        self, station: Station | None, illegal_positions: set[Vec2]
    ):
        if station != self._station_being_built:
            self.stations_being_built_shape_element_list = _ShapeElementList()
            if station:
                station_shapes = self._get_station_shapes(station, True)
                for station_shape in station_shapes:
                    self.stations_being_built_shape_element_list.append(station_shape)
                self._station_being_built = station
            for position in illegal_positions:
                red_box_shape = arcade.create_rectangle_filled(
                    position.x * GRID_BOX_SIZE_PIXELS + GRID_BOX_SIZE_PIXELS / 2,
                    position.y * GRID_BOX_SIZE_PIXELS + GRID_BOX_SIZE_PIXELS / 2,
                    GRID_BOX_SIZE_PIXELS,
                    GRID_BOX_SIZE_PIXELS,
                    color=HIGHLIGHT_COLOR,
                )
                self.stations_being_built_shape_element_list.append(red_box_shape)
            self._station_being_built = station

    def _create_rail(self, rail: Rail):
        for rail_shape in get_rail_shapes(rail, FINISHED_RAIL_COLOR):
            self._add_rail_shape(rail_shape, rail)

    def highlight(self, positions: Iterable[Vec2]):
        self.highlight_shape_element_list = _ShapeElementList()
        for position in positions:
            shape = arcade.create_rectangle_filled(
                position.x * GRID_BOX_SIZE_PIXELS + GRID_BOX_SIZE_PIXELS / 2,
                position.y * GRID_BOX_SIZE_PIXELS + GRID_BOX_SIZE_PIXELS / 2,
                GRID_BOX_SIZE_PIXELS,
                GRID_BOX_SIZE_PIXELS,
                color=HIGHLIGHT_COLOR,
            )
            self.highlight_shape_element_list.append(shape)

    def show_rails_to_be_destroyed(self, rails: set[Rail]):
        if rails != self._previous_rails_to_be_marked_as_to_be_destroyed:
            self._rail_to_be_destroyed_shape_list.clear()
            for rail in rails:
                for shape in get_rail_shapes(rail, RAIL_TO_BE_DESTROYED_COLOR):
                    self._rail_to_be_destroyed_shape_list.append(shape)
        self._previous_rails_to_be_marked_as_to_be_destroyed = rails

    def draw(self):
        self._grid_shape_list.draw()
        self._shape_list.draw()
        self._sprite_list.draw()
        self._rail_shape_list.draw()
        self._rail_to_be_destroyed_shape_list.draw()
        self._signal_shape_list.draw()

        self.rails_being_built_shape_element_list.draw()
        self.stations_being_built_shape_element_list.draw()
        self.iron_shape_element_list.draw()

        self.highlight_shape_element_list.draw()

        self._train_drawer.draw()

    def update(self):
        self._train_drawer.update()
