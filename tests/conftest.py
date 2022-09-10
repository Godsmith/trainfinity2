import pytest
import trainfinity2.camera
import trainfinity2.drawer
import trainfinity2.gui
from pyglet.math import Vec2
from trainfinity2.__main__ import MyGame
from trainfinity2.terrain import Terrain


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
    monkeypatch.setattr(trainfinity2.camera, "arcade", MockArcade())
    monkeypatch.setattr(trainfinity2.gui, "arcade", MockArcade())
    monkeypatch.setattr(trainfinity2.drawer, "arcade", MockArcade())
    # Add a single water tile for code coverage
    game = MyGame()
    game.setup(terrain=Terrain(water=[Vec2(210, 210)]))
    game.grid.mines = {}
    game.grid.factories = {}
    return game
