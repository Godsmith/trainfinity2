import itertools
from collections import defaultdict
from typing import Any, Collection, Iterable, TYPE_CHECKING
import typing
import arcade
from arcade import color
from pyglet.math import Vec2

from constants import (
    BUILDING_RAIL_COLOR,
    BUILDING_ILLEGAL_RAIL_COLOR,
    FINISHED_RAIL_COLOR,
    GRID_BOX_SIZE,
    GRID_COLOR,
    GRID_HEIGHT,
    GRID_LINE_WIDTH,
    GRID_WIDTH,
    IRON_SIZE,
    PIXEL_OFFSET_PER_IRON,
    RAIL_LINE_WIDTH,
    HIGHLIGHT_COLOR,
)
from grid import Grid, RailsBeingBuiltEvent

from model import (
    Factory,
    Mine,
    Rail,
    Station,
    Building,
    IronAddedEvent,
    IronRemovedEvent,
)
from train import Train
from observer import CreateEvent, DestroyEvent, Event


class Drawer:
    _instance = None

    def __init__(self):

        self._grid_shape_list = arcade.ShapeElementList()
        self._shape_list = arcade.ShapeElementList()
        self._sprite_list = arcade.SpriteList()

        # Needed to easily remove sprites and shapes
        self.rail_shapes_from_rail = defaultdict(set)
        self.iron_shapes_from_position = defaultdict(list)

        self._sprites_from_object_id = defaultdict(list)
        self._shapes_from_object_id = defaultdict(list)

        self.rails_being_built_shape_element_list = arcade.ShapeElementList()
        self.rails_shape_element_list = arcade.ShapeElementList()
        self.iron_shape_element_list = arcade.ShapeElementList()

        self.highlight_shape_element_list = arcade.ShapeElementList()

        self._trains = []

        self._fps_sprite = arcade.Sprite()
        self._score_sprite = arcade.Sprite()
        self._sprite_list.append(self._fps_sprite)
        self._sprite_list.append(self._score_sprite)

    @classmethod
    def create_instance(cls):
        cls._instance = Drawer()
        return cls._instance

    @classmethod
    @property
    def instance(cls) -> "Drawer":
        cls._instance = typing.cast(Drawer, cls._instance)
        return cls._instance

    @classmethod
    def upsert(cls, object: Any):
        self = cls.instance
        match object:
            case Grid():
                self._create_grid(object)
                print("create_grid")
            case Factory() | Mine() | Station():
                self._create_building(object)

    @classmethod
    def remove(cls, object: Any):
        self = cls.instance
        for sprite in self._sprites_from_object_id[id(object)]:
            self._sprite_list.remove(sprite)
            del self._sprites_from_object_id[id(object)]
        for shape in self._shapes_from_object_id[id(object)]:
            self._shape_list.remove(shape)
            del self._shapes_from_object_id[object]

    def _create_grid(self, grid: Grid):
        self._grid_shape_list = arcade.ShapeElementList()
        for x in range(grid.left, grid.right + 1, GRID_BOX_SIZE):
            self._grid_shape_list.append(
                arcade.create_line(
                    x,
                    grid.bottom,
                    x,
                    grid.top,
                    GRID_COLOR,
                    GRID_LINE_WIDTH,
                )
            )

        for y in range(grid.bottom, grid.top + 1, GRID_BOX_SIZE):
            self._grid_shape_list.append(
                arcade.create_line(
                    grid.left, y, grid.right, y, GRID_COLOR, GRID_LINE_WIDTH
                )
            )

    def _create_building(self, building: Building):
        match building:
            case Factory():
                character = "F"
            case Mine():
                character = "M"
            case Station():
                character = "S"
        sprite = arcade.create_text_sprite(
            character, building.x, building.y, color=color.WHITE, font_size=24
        )
        self._add_sprite(sprite, building)

    def _add_sprite(self, sprite: arcade.Sprite, object: Any):
        self._sprite_list.append(sprite)
        self._sprites_from_object_id[id(object)].append(sprite)

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
        center_x = position.x + GRID_BOX_SIZE / 2
        center_y = position.y + GRID_BOX_SIZE / 2
        shape = arcade.create_rectangle_filled(
            center_x, center_y, GRID_BOX_SIZE, GRID_BOX_SIZE, color=color
        )
        self._shape_list.append(shape)

    def create_train(self, train: Train):
        self._trains.append(train)
        train.add_observer(self, DestroyEvent)

    def on_notify(self, object: Any, event: Event):
        match (object, event):
            case Mine(), IronAddedEvent():
                event = typing.cast(IronAddedEvent, event)
                self.add_iron((event.x, event.y))
            case Mine(), IronRemovedEvent():
                event = typing.cast(IronRemovedEvent, event)
                self.remove_iron((event.x, event.y), event.amount)
            case Mine(), CreateEvent():
                self.upsert(object)
                object.add_observer(self, IronAddedEvent)
                object.add_observer(self, IronRemovedEvent)
            case Train(), DestroyEvent():
                self._trains.remove(object)
            case Rail(), DestroyEvent():
                # TODO: change remove_rail to take rail object instead
                self.remove_rail(object)
            case Mine() | Station() | Factory(), DestroyEvent():
                self.remove(object)
            case Rail(), CreateEvent():
                self.create_rail(object)
            case Grid(), RailsBeingBuiltEvent():
                event = typing.cast(RailsBeingBuiltEvent, event)
                self.show_rails_being_built(event.rails)
            case Factory() | Station(), CreateEvent():
                self.upsert(object)

    def create_rail(self, rail: Rail):
        x1, y1, x2, y2 = [
            coordinate + GRID_BOX_SIZE / 2
            for coordinate in (rail.x1, rail.y1, rail.x2, rail.y2)
        ]
        shape = arcade.create_line(x1, y1, x2, y2, FINISHED_RAIL_COLOR, RAIL_LINE_WIDTH)
        self.rails_shape_element_list.append(shape)
        self.rail_shapes_from_rail[rail].add(shape)

    def add_iron(self, position: tuple[int, int]):
        x, y = position
        x += len(self.iron_shapes_from_position[position]) * PIXEL_OFFSET_PER_IRON / 2
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

    def remove_iron(self, position: tuple[int, int], amount: int):
        for _ in range(amount):
            filled_rectangle = self.iron_shapes_from_position[position].pop()
            rectangle_outline = self.iron_shapes_from_position[position].pop()
            self.iron_shape_element_list.remove(filled_rectangle)
            self.iron_shape_element_list.remove(rectangle_outline)
        # Workaround for Arcade.py bug: If the last element in a ShapeElementList is removed,
        # the draw() method crashes, so we have to recreate the list if it becomes empty.
        if not self.iron_shape_element_list:
            self.iron_shape_element_list = arcade.ShapeElementList()

    def remove_rail(self, rail: Rail):
        removed_shapes = []
        for shape in self.rail_shapes_from_rail[rail]:
            self.rails_shape_element_list.remove(shape)
            removed_shapes.append(shape)
        for rail, shape in itertools.product(
            self.rail_shapes_from_rail, removed_shapes
        ):
            self.rail_shapes_from_rail[rail].discard(shape)
        # Workaround for Arcade.py bug: If the last element in a ShapeElementList is removed,
        # the draw() method crashes, so we have to recreate the list if it becomes empty.
        if not self.rails_shape_element_list:
            self.rails_shape_element_list = arcade.ShapeElementList()

    def show_rails_being_built(self, rails: Iterable[Rail]):
        self.rails_being_built_shape_element_list = arcade.ShapeElementList()
        for rail in rails:
            color = BUILDING_RAIL_COLOR if rail.legal else BUILDING_ILLEGAL_RAIL_COLOR
            x1, y1, x2, y2 = [
                coordinate + GRID_BOX_SIZE / 2
                for coordinate in (rail.x1, rail.y1, rail.x2, rail.y2)
            ]
            self.rails_being_built_shape_element_list.append(
                arcade.create_line(x1, y1, x2, y2, color, RAIL_LINE_WIDTH)
            )

    def _draw_trains(self):
        # TODO: Create a shapelist per train that we can move instead
        for train in self._trains:
            x = train.x + GRID_BOX_SIZE / 2
            y = train.y + GRID_BOX_SIZE / 2
            arcade.draw_circle_filled(
                x,
                y,
                GRID_BOX_SIZE / 2,
                color=color.RED,
            )
            if train.iron:
                arcade.draw_rectangle_filled(
                    x,
                    y,
                    IRON_SIZE,
                    IRON_SIZE,
                    color=color.TROLLEY_GREY,
                )
                arcade.draw_rectangle_outline(
                    x,
                    y,
                    IRON_SIZE,
                    IRON_SIZE,
                    color=color.BLACK,
                )
            if train.selected:
                arcade.draw_circle_outline(
                    x, y, GRID_BOX_SIZE / 2, color=HIGHLIGHT_COLOR, border_width=5
                )
                positions = {
                    position for rail in train.rails for position in rail.positions
                }
                for position in positions:
                    arcade.draw_rectangle_filled(
                        position.x + GRID_BOX_SIZE / 2,
                        position.y + GRID_BOX_SIZE / 2,
                        GRID_BOX_SIZE,
                        GRID_BOX_SIZE,
                        color=HIGHLIGHT_COLOR,
                    )

    def highlight(self, positions: Iterable[Vec2]):
        self.highlight_shape_element_list = arcade.ShapeElementList()
        for position in positions:
            shape = arcade.create_rectangle_filled(
                position.x + GRID_BOX_SIZE / 2,
                position.y + GRID_BOX_SIZE / 2,
                GRID_BOX_SIZE,
                GRID_BOX_SIZE,
                color=HIGHLIGHT_COLOR,
            )
            self.highlight_shape_element_list.append(shape)

    def draw(self):
        self._grid_shape_list.draw()
        self._shape_list.draw()
        self._sprite_list.draw()

        self.rails_shape_element_list.draw()
        self.rails_being_built_shape_element_list.draw()
        self.iron_shape_element_list.draw()

        self.highlight_shape_element_list.draw()

        self._draw_trains()
