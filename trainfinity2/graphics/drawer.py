from collections import defaultdict
from typing import Any, Collection, Iterable

import arcade
from arcade import Color, Shape, color
from pyglet.math import Vec2
from trainfinity2.graphics.cargo import get_cargo_shape

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
    PIXEL_OFFSET_PER_CARGO,
    RAIL_TO_BE_DESTROYED_COLOR,
)
from ..grid import (
    Grid,
    RailsBeingBuiltEvent,
    SignalsBeingBuiltEvent,
    StationBeingBuiltEvent,
)
from ..model import (
    Building,
    CargoSoldEvent,
    CargoType,
    CargoAddedEvent,
    CargoRemovedEvent,
    CoalMine,
    Forest,
    IronMine,
    Market,
    Rail,
    Sawmill,
    Signal,
    SignalColor,
    Station,
    SteelWorks,
    Workshop,
)
from ..events import CreateEvent, DestroyEvent, Event
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
        self.cargo_shapes_from_position = defaultdict(list)

        self._sprites_from_object_id = defaultdict(list)
        self._shapes_from_object_id = defaultdict(list)
        self._rail_shapes_from_object_id = defaultdict(list)
        self._signal_shapes_from_object_id = defaultdict(list)

        self._rail_shape_list = _ShapeElementList()
        self._signal_shape_list = _ShapeElementList()

        self._previous_rails_to_be_marked_as_to_be_destroyed: set[Rail] = set()
        self.rail_to_be_destroyed_shape_list = _ShapeElementList()

        self._rails_being_built: set[Rail] = set()
        self.rails_being_built_shape_element_list = _ShapeElementList()

        self._station_being_built: Station | None = None
        self.stations_being_built_shape_element_list = _ShapeElementList()

        self.signals_being_built_shape_element_list = _ShapeElementList()

        self.cargo_shape_element_list = _ShapeElementList()

        self.highlight_shape_element_list = _ShapeElementList()

        self._train_drawer = TrainDrawer()

        self._fps_sprite = arcade.Sprite()
        self._score_sprite = arcade.Sprite()
        self._sprite_list.append(self._fps_sprite)
        self._sprite_list.append(self._score_sprite)

    def handle_events(self, events: Iterable[Event]):
        for event in events:
            match event:
                case CreateEvent(Building() as building):
                    self._create_building(building)
                case CreateEvent(Station() as station):
                    self._create_station(station)
                case CreateEvent(Rail() as rail):
                    self._create_rail(rail)
                case CreateEvent(Signal() as signal):
                    self._update_signal(signal)
                case StationBeingBuiltEvent():
                    self._show_station_being_built(
                        event.station, event.illegal_positions
                    )
                case RailsBeingBuiltEvent():
                    self._show_rails_being_built(event.rails)
                case SignalsBeingBuiltEvent():
                    self._show_signals_being_built(event.signals)
                case CargoAddedEvent():
                    self._add_cargo(event.position, event.type)
                case CargoRemovedEvent():
                    self._remove_cargo(event.position, event.amount)
                case DestroyEvent():
                    self._remove(event.object)
                case CargoSoldEvent():
                    # Do nothing at this point. In the future, perhaps
                    # create some floating text or something
                    pass
                case _:
                    raise ValueError(f"Event not being handled: {event}")

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
        # Just in case it was rails that was destroyed, hide the red outline
        self.show_rails_to_be_destroyed(set())

    def create_grid(self, grid: Grid):
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
        scale = 1.0
        match building:
            case IronMine() | CoalMine():
                scale = 0.75
                filepath = "images/mine.png"
            case Workshop():
                filepath = "images/anvil.png"
            case SteelWorks():
                filepath = "images/steel_mill.png"
            case Forest():
                filepath = "images/forest.png"
            case Sawmill():
                filepath = "images/forest.png"
            case Market():
                filepath = "images/market.png"
            case _:
                filepath = "images/unknown_building.png"

        sprite = arcade.Sprite(
            filepath,
            scale,
            center_x=building.position.x * GRID_BOX_SIZE_PIXELS
            + GRID_BOX_SIZE_PIXELS / 2,
            center_y=building.position.y * GRID_BOX_SIZE_PIXELS
            + GRID_BOX_SIZE_PIXELS / 2,
        )
        self._add_sprite(sprite, building)

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

    def _create_station(self, station: Station):
        for shape in self._get_station_shapes(station):
            self._add_shape(shape, station)

    def _create_signal_shape(self, signal: Signal, is_being_built: bool = False):
        positions = list(signal.rail.positions)
        middle_of_rail = positions[0].lerp(positions[1], 0.5)
        position = middle_of_rail.lerp(signal.from_position, 0.5)
        position = Vec2(
            position.x * GRID_BOX_SIZE_PIXELS + GRID_BOX_SIZE_PIXELS / 2,
            position.y * GRID_BOX_SIZE_PIXELS + GRID_BOX_SIZE_PIXELS / 2,
        )
        alpha = 128 if is_being_built else 255
        color_: Color = (
            color.RED
            if signal.signal_color == SignalColor.RED
            else color.GREEN + (alpha,)
        )
        return arcade.create_ellipse_filled(
            position.x,
            position.y,
            GRID_BOX_SIZE_PIXELS / 6,
            GRID_BOX_SIZE_PIXELS / 6,
            color=color_,
        )

    def _update_signal(self, signal: Signal):
        self._remove(signal)
        self._add_signal_shape(self._create_signal_shape(signal), signal)

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

    def destroy_train(self, train: Train):
        self._train_drawer.remove(train)

    def _add_cargo(self, position: Vec2, cargo_type: CargoType):
        x, y = position.x * GRID_BOX_SIZE_PIXELS, position.y * GRID_BOX_SIZE_PIXELS
        x += len(self.cargo_shapes_from_position[position]) * int(
            PIXEL_OFFSET_PER_CARGO / 2
        )
        for shape in get_cargo_shape(x, y, cargo_type):
            self.cargo_shapes_from_position[position].append(shape)
            self.cargo_shape_element_list.append(shape)

    def _remove_cargo(self, position: Vec2, amount: int):
        for _ in range(amount):
            filled_rectangle = self.cargo_shapes_from_position[position].pop()
            rectangle_outline = self.cargo_shapes_from_position[position].pop()
            self.cargo_shape_element_list.remove(filled_rectangle)
            self.cargo_shape_element_list.remove(rectangle_outline)

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

    def _show_signals_being_built(self, signals: set[Signal]):
        self.signals_being_built_shape_element_list = _ShapeElementList()
        for signal in signals:
            self.signals_being_built_shape_element_list.append(
                self._create_signal_shape(signal, is_being_built=True)
            )

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
            self.rail_to_be_destroyed_shape_list.clear()
            for rail in rails:
                for shape in get_rail_shapes(rail, RAIL_TO_BE_DESTROYED_COLOR):
                    self.rail_to_be_destroyed_shape_list.append(shape)
        self._previous_rails_to_be_marked_as_to_be_destroyed = rails

    def draw(self):
        self._grid_shape_list.draw()
        self._shape_list.draw()
        self._sprite_list.draw()
        self._rail_shape_list.draw()
        self.rail_to_be_destroyed_shape_list.draw()
        self._signal_shape_list.draw()

        self.rails_being_built_shape_element_list.draw()
        self.stations_being_built_shape_element_list.draw()
        self.signals_being_built_shape_element_list.draw()

        self.cargo_shape_element_list.draw()

        self.highlight_shape_element_list.draw()

        self._train_drawer.draw()

    def update(self):
        self._train_drawer.update()
