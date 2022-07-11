import pytest
import arcade
from main import MyGame
from pyglet.math import Vec2


@pytest.fixture(autouse=True)
def hide_game_window():
    MyGame.VISIBLE = False


def test_camera_starts_at_origon():
    game = MyGame()

    assert game.camera_sprites.position == Vec2(0, 0)


def test_camera_pans_when_right_clicking_and_dragging():
    game = MyGame()

    game.on_mouse_press(x=100, y=100, button=arcade.MOUSE_BUTTON_RIGHT, modifiers=0)
    game.on_mouse_motion(x=200, y=300, dx=100, dy=200)
    game.on_mouse_release(x=200, y=300, button=arcade.MOUSE_BUTTON_RIGHT, modifiers=0)

    assert game.camera_sprites
