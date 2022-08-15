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
    GRID_LINE_WIDTH,
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
    def __init__(self, left, bottom, right, top):

        self._grid_shape_list = arcade.ShapeElementList()
        self.shape_list = arcade.ShapeElementList()
        self.sprite_list = arcade.SpriteList()

        self.station_sprite_list = arcade.SpriteList()
        self.mine_sprite_list = arcade.SpriteList()
        self.factory_sprite_list = arcade.SpriteList()

        # Needed to easily remove sprites and shapes
        self._building_sprite_from_position = {}
        self.rail_shapes_from_rail = defaultdict(set)
        self.iron_shapes_from_position = defaultdict(list)

        self.rails_being_built_shape_element_list = arcade.ShapeElementList()
        self.rails_shape_element_list = arcade.ShapeElementList()
        self.iron_shape_element_list = arcade.ShapeElementList()

        self.highlight_shape_element_list = arcade.ShapeElementList()

        self._trains = []
        self.create_grid(left, bottom, right, top)

        self._fps_sprite = arcade.Sprite()
        self._score_sprite = arcade.Sprite()
        self.sprite_list.append(self._fps_sprite)
        self.sprite_list.append(self._score_sprite)

    def create_grid(self, left, bottom, right, top):
        self._grid_shape_list = arcade.ShapeElementList()
        for x in range(left, right + 1, GRID_BOX_SIZE):
            self._grid_shape_list.append(
                arcade.create_line(
                    x,
                    bottom,
                    x,
                    top,
                    GRID_COLOR,
                    GRID_LINE_WIDTH,
                )
            )

        for y in range(bottom, top + 1, GRID_BOX_SIZE):
            self._grid_shape_list.append(
                arcade.create_line(left, y, right, y, GRID_COLOR, GRID_LINE_WIDTH)
            )

    def _create_building_sprite(self, building: Building):
        if isinstance(building, Factory):
            character = "F"
        elif isinstance(building, Mine):
            character = "M"
        elif isinstance(building, Station):
            character = "S"
        return arcade.create_text_sprite(
            character, building.x, building.y, color=color.WHITE, font_size=24
        )

    def create_building(self, building: Building):
        sprite = self._create_building_sprite(building)
        self.sprite_list.append(sprite)
        self._building_sprite_from_position[(building.x, building.y)] = sprite

    def remove_building(self, building: Building):
        sprite = self._building_sprite_from_position[(building.x, building.y)]
        del self._building_sprite_from_position[(building.x, building.y)]
        self.sprite_list.remove(sprite)

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
        self.shape_list.append(shape)

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
                self.create_building(object)
                object.add_observer(self, IronAddedEvent)
                object.add_observer(self, IronRemovedEvent)
            case Train(), DestroyEvent():
                self._trains.remove(object)
            case Rail(), DestroyEvent():
                # TODO: change remove_rail to take rail object instead
                self.remove_rail(object)
            case Mine() | Station() | Factory(), DestroyEvent():
                self.remove_building(object)
            case Rail(), CreateEvent():
                self.create_rail(object)
            case Grid(), RailsBeingBuiltEvent():
                event = typing.cast(RailsBeingBuiltEvent, event)
                self.show_rails_being_built(event.rails)
            case Factory() | Station(), CreateEvent():
                self.create_building(object)

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
        self.shape_list.draw()
        self.sprite_list.draw()

        self.rails_shape_element_list.draw()
        self.rails_being_built_shape_element_list.draw()
        self.station_sprite_list.draw()
        self.mine_sprite_list.draw()
        self.factory_sprite_list.draw()
        self.iron_shape_element_list.draw()

        self.highlight_shape_element_list.draw()

        self._draw_trains()
