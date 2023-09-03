import pytest
import tests.run_debug
import trainfinity2.camera
import trainfinity2.graphics.drawer
import trainfinity2.graphics.rail_shapes
import trainfinity2.graphics.train_drawer
import trainfinity2.gui
from pyglet.math import Vec2
from trainfinity2.__main__ import Game
from trainfinity2.terrain import Terrain


class MockArcade:
    def __init__(self):
        self.viewport = (0, 800, 0, 600)

    class Sprite:
        def __init__(
            self,
            filename: str = "",
            scale: float = 1,
            image_x: float = 0,
            image_y: float = 0,
            image_width: float = 0,
            image_height: float = 0,
            center_x: float = 0,
            center_y: float = 0,
        ):
            pass

    class SpriteList(list):
        def draw(self):
            pass

    class ShapeElementList(list):
        def draw(self):
            pass

    class FadeParticle:
        pass

    class Emitter:
        def __init__(self, center_xy, emit_controller, particle_factory) -> None:
            pass

        def draw(self):
            pass

        def update(self):
            pass

    class EmitterIntervalWithTime:
        def __init__(self, emit_interval: float, lifetime: float) -> None:
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

    def draw_rectangle_filled(self, *args, **kwargs):
        pass

    def draw_rectangle_outline(self, *args, **kwargs):
        pass


@pytest.fixture
def game(monkeypatch: pytest.MonkeyPatch) -> Game:
    monkeypatch.setattr(trainfinity2.camera, "arcade", MockArcade())
    monkeypatch.setattr(trainfinity2.gui, "arcade", MockArcade())
    monkeypatch.setattr(trainfinity2.graphics.drawer, "arcade", MockArcade())
    monkeypatch.setattr(trainfinity2.graphics.rail_shapes, "arcade", MockArcade())
    monkeypatch.setattr(trainfinity2.graphics.train_drawer, "arcade", MockArcade())
    monkeypatch.setattr(tests.run_debug, "arcade", MockArcade())
    # Add a single water tile for code coverage
    game = Game()
    game.setup(terrain=Terrain(water=[Vec2(210, 210)]))
    game.grid.mines = {}
    game.grid.factories = {}
    return game
