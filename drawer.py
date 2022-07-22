import arcade
from arcade import color

from constants import (
    BUILDING_RAIL_COLOR,
    FINISHED_RAIL_COLOR,
    GRID_BOX_SIZE,
    GRID_COLOR,
    GRID_HEIGHT,
    GRID_LINE_WIDTH,
    GRID_WIDTH,
    RAIL_LINE_WIDTH,
)
from model import Factory, Mine, Rail, Station, Train


class Drawer:
    def __init__(self):
        self.shape_list = arcade.ShapeElementList()
        self.sprite_list = arcade.SpriteList()

        self.station_sprite_list = arcade.SpriteList()
        self.mine_sprite_list = arcade.SpriteList()
        self.factory_sprite_list = arcade.SpriteList()

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
        self.station_sprite_list.append(sprite)

    def create_train(self, train: Train):
        self._trains.append(train)

    def create_rail(self, rails: list[Rail]):
        for rail in rails:
            x1, y1, x2, y2 = [
                coordinate + GRID_BOX_SIZE / 2
                for coordinate in (rail.x1, rail.y1, rail.x2, rail.y2)
            ]
            self.rails_shape_element_list.append(
                arcade.create_line(x1, y1, x2, y2, FINISHED_RAIL_COLOR, RAIL_LINE_WIDTH)
            )

    def set_rails_being_built(self, rails: list[Rail]):
        self.rails_being_built_shape_element_list = arcade.ShapeElementList()
        for rail in rails:
            x1, y1, x2, y2 = [
                coordinate + GRID_BOX_SIZE / 2
                for coordinate in (rail.x1, rail.y1, rail.x2, rail.y2)
            ]
            self.rails_being_built_shape_element_list.append(
                arcade.create_line(x1, y1, x2, y2, BUILDING_RAIL_COLOR, RAIL_LINE_WIDTH)
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
