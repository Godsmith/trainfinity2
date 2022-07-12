import arcade
import pytest
from main import MyGame
from pyglet.math import Vec2
from pytest import approx


@pytest.fixture(autouse=True)
def hide_game_window():
    MyGame.VISIBLE = False


class TestCamera:
    def test_camera_starts_at_origo(self):
        game = MyGame()

        assert game.camera_sprites.position == Vec2(0, 0)

    def test_camera_pans_when_right_clicking_and_dragging(self):
        game = MyGame()

        game.on_mouse_press(x=100, y=100, button=arcade.MOUSE_BUTTON_RIGHT, modifiers=0)
        game.on_mouse_motion(x=200, y=300, dx=100, dy=200)
        game.on_mouse_release(
            x=200, y=300, button=arcade.MOUSE_BUTTON_RIGHT, modifiers=0
        )

        # TODO: forgot assert here
        assert game.camera_sprites

    def test_camera_stops_when_trying_to_move_past_top_left_corner(self):
        game = MyGame()

        game.on_mouse_press(x=100, y=100, button=arcade.MOUSE_BUTTON_RIGHT, modifiers=0)
        game.on_mouse_motion(x=2000, y=3000, dx=1900, dy=2900)
        game.on_mouse_release(
            x=2000, y=3000, button=arcade.MOUSE_BUTTON_RIGHT, modifiers=0
        )

        assert game.camera_sprites.goal_position == Vec2(-400, -300)

    def test_camera_stops_when_trying_to_move_past_bottom_right_corner(self):
        game = MyGame()

        game.on_mouse_press(x=100, y=100, button=arcade.MOUSE_BUTTON_RIGHT, modifiers=0)
        game.on_mouse_motion(x=-2000, y=-3000, dx=-2100, dy=-3100)
        game.on_mouse_release(
            x=-2000, y=-3000, button=arcade.MOUSE_BUTTON_RIGHT, modifiers=0
        )

        assert game.camera_sprites.goal_position == Vec2(200, 300)

    def test_camera_starts_with_scale_1(self):
        game = MyGame()

        assert game.camera_sprites.scale == 1.0

    def test_scrolling_up_zooms_in(self):
        game = MyGame()

        game.on_mouse_scroll(x=100, y=100, scroll_x=0, scroll_y=1)

        assert game.camera_sprites.scale == approx(0.9)

    def test_scrolling_down_zooms_out(self):
        game = MyGame()

        game.on_mouse_scroll(x=100, y=100, scroll_x=0, scroll_y=-1)

        assert game.camera_sprites.scale == approx(1.1)
