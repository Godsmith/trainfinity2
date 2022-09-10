import camera
import drawer
import gui
import pytest
from main import MyGame
from pyglet.math import Vec2
from terrain import Terrain


class MockArcade:
    def __init__(self):
        self.viewport = (0, 800, 0, 600)

    class Sprite:
        pass

    class SpriteList(list):
        def draw(self):
            pass

        def move(self, dx, dy):
            pass

    class ShapeElementList(list):
        def draw(self):
            pass

        def move(self, dx, dy):
            pass

    def get_viewport(self):
        return self.viewport

    def set_viewport(self, left, right, bottom, top):
        self.viewport = (left, right, bottom, top)

    def create_text_sprite(self, *args, **kwargs):
        pass

    def create_rectangle_filled(self, *args, **kwargs):
        pass

    def create_rectangle_outline(self, *args, **kwargs):
        pass

    def create_ellipse_filled(self, *args, **kwargs):
        pass

    def create_line(self, *args, **kwargs):
        pass

    def draw_circle_filled(self, *args, **kwargs):
        pass

    def draw_rectangle_filled(self, *args, **kwargs):
        pass

    def draw_rectangle_outline(self, *args, **kwargs):
        pass

    def draw_circle_outline(self, *args, **kwargs):
        pass


@pytest.fixture
def game(monkeypatch: pytest.MonkeyPatch) -> MyGame:
    monkeypatch.setattr(camera, "arcade", MockArcade())
    monkeypatch.setattr(gui, "arcade", MockArcade())
    monkeypatch.setattr(drawer, "arcade", MockArcade())
    # Add a single water tile for code coverage
    game = MyGame()
    game.setup(terrain=Terrain(water=[Vec2(210, 210)]))
    game.grid.mines = {}
    game.grid.factories = {}
    return game
