from collections import defaultdict
from typing import Iterable
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
)
from model import Factory, Mine, Player, Rail, Station, Train, Water


class Drawer:
    def __init__(self, grid_width, grid_height):
        self._grid_width = grid_width
        self._grid_height = grid_height
        self._grid_left = 0
        self._grid_bottom = 0

        self._grid_shape_list = arcade.ShapeElementList()
        self.shape_list = arcade.ShapeElementList()
        self.sprite_list = arcade.SpriteList()

        self.station_sprite_list = arcade.SpriteList()
        self.mine_sprite_list = arcade.SpriteList()
        self.factory_sprite_list = arcade.SpriteList()

        # Needed to easily remove sprites and shapes
        self.station_sprite_from_position = {}
        self.rail_shapes_from_position = defaultdict(set)
        self.iron_shapes_from_position = defaultdict(set)

        self.rails_being_built_shape_element_list = arcade.ShapeElementList()
        self.rails_shape_element_list = arcade.ShapeElementList()
        self.iron_shape_element_list = arcade.ShapeElementList()

        self._trains = []
        self._create_grid()

        self._fps_sprite = arcade.Sprite()
        self._score_sprite = arcade.Sprite()
        self.sprite_list.append(self._fps_sprite)
        self.sprite_list.append(self._score_sprite)

    def _create_grid(self):
        self._grid_shape_list = arcade.ShapeElementList()
        for x in range(self._grid_left, self._grid_width + 1, GRID_BOX_SIZE):
            self._grid_shape_list.append(
                arcade.create_line(
                    x,
                    self._grid_bottom,
                    x,
                    self._grid_height,
                    GRID_COLOR,
                    GRID_LINE_WIDTH,
                )
            )

        for y in range(self._grid_bottom, self._grid_height + 1, GRID_BOX_SIZE):
            self._grid_shape_list.append(
                arcade.create_line(
                    self._grid_left, y, self._grid_width, y, GRID_COLOR, GRID_LINE_WIDTH
                )
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

    def create_terrain(
        self, water: list[Vec2], sand: list[Vec2], mountains: list[Vec2]
    ):
        print(f"{len(water)=}, {len(sand)=}, {len(mountains)=}")
        for positions, terrain_color in [
            (water, color.SEA_BLUE),
            (sand, color.SAND),
            # (mountains, color.ROAST_COFFEE),
            # (mountains, color.LIGHT_SLATE_GRAY),
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
        self.iron_shapes_from_position[position].add(filled_rectangle)
        self.iron_shapes_from_position[position].add(rectangle_outline)
        self.iron_shape_element_list.append(filled_rectangle)
        self.iron_shape_element_list.append(rectangle_outline)

    def remove_all_iron(self, position: tuple[int, int]):
        for shape in self.iron_shapes_from_position[position]:
            self.iron_shape_element_list.remove(shape)
        self.iron_shapes_from_position[position].clear()
        # Workaround for Arcade.py bug: If the last element in a ShapeElementList is removed,
        # the draw() method crashes, so we have to recreate the list if it becomes empty.
        if not self.iron_shape_element_list:
            self.iron_shape_element_list = arcade.ShapeElementList()

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

        self._draw_trains()

    def enlarge_grid(self):
        self._grid_left -= GRID_BOX_SIZE
        self._grid_bottom -= GRID_BOX_SIZE
        self._grid_width += 2 * GRID_BOX_SIZE
        self._grid_height += 2 * GRID_BOX_SIZE
        self._create_grid()
