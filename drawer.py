from collections import defaultdict
from typing import Iterable
import arcade
from arcade import color

from constants import (
    BUILDING_RAIL_COLOR,
    BUILDING_ILLEGAL_RAIL_COLOR,
    FINISHED_RAIL_COLOR,
    GRID_BOX_SIZE,
    GRID_COLOR,
    GRID_HEIGHT,
    GRID_LINE_WIDTH,
    GRID_WIDTH,
    RAIL_LINE_WIDTH,
)
from model import Factory, Mine, Rail, Station, Train, Water


class Drawer:
    def __init__(self):
        self.shape_list = arcade.ShapeElementList()
        self.sprite_list = arcade.SpriteList()

        self.station_sprite_list = arcade.SpriteList()
        self.mine_sprite_list = arcade.SpriteList()
        self.factory_sprite_list = arcade.SpriteList()

        # Needed to easily remove sprites and shapes
        self.station_sprite_from_position = {}
        self.rail_shapes_from_position = defaultdict(set)

        self.rails_being_built_shape_element_list = arcade.ShapeElementList()
        self.rails_shape_element_list = arcade.ShapeElementList()

        self._trains = []
        self._create_grid()

    def _create_grid(self):
        for x in range(0, GRID_WIDTH + 1, GRID_BOX_SIZE):
            self.shape_list.append(
                arcade.create_line(x, 0, x, GRID_HEIGHT, GRID_COLOR, GRID_LINE_WIDTH)
            )

        for y in range(0, GRID_HEIGHT + 1, GRID_BOX_SIZE):
            self.shape_list.append(
                arcade.create_line(0, y, GRID_WIDTH, y, GRID_COLOR, GRID_LINE_WIDTH)
            )

    def create_mine(self, mine: Mine):
        sprite = arcade.create_text_sprite(
            "M", mine.x, mine.y, color=color.WHITE, font_size=24
        )
        self.mine_sprite_list.append(sprite)

    def create_factory(self, factory: Factory):
        sprite = arcade.create_text_sprite(
            "F", factory.x, factory.y, color=color.WHITE, font_size=24
        )
        self.factory_sprite_list.append(sprite)

    def create_station(self, station: Station):
        sprite = arcade.create_text_sprite(
            "S", station.x, station.y, color=color.WHITE, font_size=24
        )
        self.station_sprite_from_position[(station.x, station.y)] = sprite
        self.station_sprite_list.append(sprite)

    def remove_station(self, position: tuple[int, int]):
        """Does nothing if there is no station at position."""
        if position in self.station_sprite_from_position:
            self.station_sprite_list.remove(self.station_sprite_from_position[position])
            del self.station_sprite_from_position[position]

    def create_water(self, water: Water):
        center_x = water.x + GRID_BOX_SIZE / 2
        center_y = water.y + GRID_BOX_SIZE / 2
        shape = arcade.create_rectangle_filled(
            center_x, center_y, GRID_BOX_SIZE, GRID_BOX_SIZE, color=color.SEA_BLUE
        )
        self.shape_list.append(shape)

    def create_train(self, train: Train):
        self._trains.append(train)

    def create_rail(self, rails: Iterable[Rail]):
        for rail in rails:
            x1, y1, x2, y2 = [
                coordinate + GRID_BOX_SIZE / 2
                for coordinate in (rail.x1, rail.y1, rail.x2, rail.y2)
            ]
            shape = arcade.create_line(
                x1, y1, x2, y2, FINISHED_RAIL_COLOR, RAIL_LINE_WIDTH
            )
            self.rails_shape_element_list.append(shape)
            self.rail_shapes_from_position[(rail.x1, rail.y1)].add(shape)
            self.rail_shapes_from_position[(rail.x2, rail.y2)].add(shape)

    def remove_rail(self, position: tuple[int, int]):
        """Does nothing if there is no rail at position."""
        removed_shapes = []
        for shape in self.rail_shapes_from_position[position]:
            self.rails_shape_element_list.remove(shape)
            removed_shapes.append(shape)
        for position in self.rail_shapes_from_position:
            for shape in removed_shapes:
                self.rail_shapes_from_position[position].discard(shape)
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
        for train in self._trains:
            arcade.draw_circle_filled(
                train.x + GRID_BOX_SIZE / 2,
                train.y + GRID_BOX_SIZE / 2,
                GRID_BOX_SIZE / 2,
                color=color.RED,
            )

    def draw(self):
        self.shape_list.draw()

        self.rails_shape_element_list.draw()
        self.rails_being_built_shape_element_list.draw()
        self.station_sprite_list.draw()
        self.mine_sprite_list.draw()
        self.factory_sprite_list.draw()

        # Draw trains here since it is only a single draw call per train
        self._draw_trains()
