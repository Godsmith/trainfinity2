import arcade
import pytest
from main import MyGame, Rail, Station, Mine, Factory
from pyglet.math import Vec2
from pytest import approx


@pytest.fixture(autouse=True)
def game() -> MyGame:
    game = MyGame(visible=False)
    return game


class TestCamera:
    def test_camera_starts_at_origo(self, game):
        assert game.camera_sprites.position == Vec2(0, 0)

    def test_camera_pans_when_right_clicking_and_dragging(self, game):
        game.on_mouse_press(x=100, y=100, button=arcade.MOUSE_BUTTON_RIGHT, modifiers=0)
        game.on_mouse_motion(x=200, y=300, dx=100, dy=200)
        game.on_mouse_release(
            x=200, y=300, button=arcade.MOUSE_BUTTON_RIGHT, modifiers=0
        )

        # TODO: forgot assert here
        assert game.camera_sprites

    def test_camera_stops_when_trying_to_move_past_top_left_corner(self, game):
        game.on_mouse_press(x=100, y=100, button=arcade.MOUSE_BUTTON_RIGHT, modifiers=0)
        game.on_mouse_motion(x=2000, y=3000, dx=1900, dy=2900)
        game.on_mouse_release(
            x=2000, y=3000, button=arcade.MOUSE_BUTTON_RIGHT, modifiers=0
        )

        assert game.camera_sprites.position == Vec2(-400, -300)

    def test_camera_stops_when_trying_to_move_past_bottom_right_corner(self, game):
        game.on_mouse_press(x=100, y=100, button=arcade.MOUSE_BUTTON_RIGHT, modifiers=0)
        game.on_mouse_motion(x=-2000, y=-3000, dx=-2100, dy=-3100)
        game.on_mouse_release(
            x=-2000, y=-3000, button=arcade.MOUSE_BUTTON_RIGHT, modifiers=0
        )

        assert game.camera_sprites.position == Vec2(200, 300)

    def test_camera_starts_with_scale_1(self, game):
        assert game.camera_sprites.scale == 1.0

    def test_scrolling_up_zooms_in(self, game):
        game.on_mouse_scroll(x=100, y=100, scroll_x=0, scroll_y=1)

        assert game.camera_sprites.scale == approx(0.9)

    def test_scrolling_down_zooms_out(self, game):
        game.on_mouse_scroll(x=100, y=100, scroll_x=0, scroll_y=-1)

        assert game.camera_sprites.scale == approx(1.1)


class TestGrid:
    def test_horizontal_rail_being_built(self, game: MyGame):
        game.on_mouse_press(x=90, y=90, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_motion(x=120, y=90, dx=30, dy=0)

        assert game.grid.rails_being_built == [Rail(120, 90, 90, 90)]

    def test_vertical_rail_being_built(self, game: MyGame):
        game.on_mouse_press(x=90, y=90, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_motion(x=90, y=120, dx=0, dy=30)

        assert game.grid.rails_being_built == [Rail(90, 120, 90, 90)]

    def test_diagonal_rail_being_built(self, game: MyGame):
        game.on_mouse_press(x=90, y=90, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_motion(x=120, y=120, dx=30, dy=30)

        assert game.grid.rails_being_built == [Rail(120, 120, 90, 90)]

    def test_trying_to_build_non_straight_does_nothing(self, game: MyGame):
        game.on_mouse_press(x=100, y=100, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_motion(x=160, y=130, dx=60, dy=30)

        assert len(game.grid.rails_being_built) == 0

    def test_built_rail(self, game: MyGame):
        game.on_mouse_press(x=100, y=100, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_motion(x=130, y=100, dx=30, dy=0)
        game.on_mouse_release(
            x=130, y=100, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0
        )

        assert len(game.grid.rails_being_built) == 0
        assert len(game.grid.rails) == 1

    def test_building_horizontal_station(self, game: MyGame):
        game.grid.mines = [Mine(0, 30)]
        game.on_mouse_press(x=-30, y=0, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_motion(x=30, y=0, dx=30, dy=0)
        game.on_mouse_release(x=30, y=0, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)

        assert game.grid.stations == [Station(0, 0)]

    def test_building_vertical_station(self, game: MyGame):
        game.grid.factories = [Factory(30, 0)]
        game.on_mouse_press(x=0, y=-30, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)
        game.on_mouse_motion(x=0, y=30, dx=0, dy=30)
        game.on_mouse_release(x=0, y=30, button=arcade.MOUSE_BUTTON_LEFT, modifiers=0)

        assert game.grid.stations == [Station(0, 0)]
