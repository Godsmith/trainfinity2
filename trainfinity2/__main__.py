import arcade
from pyglet.math import Vec2

from .game import Game
from .terrain import Terrain
from .window import Window

if __name__ == "__main__":
    game = Game()
    window = Window(game)
    game.setup(Terrain(water=[Vec2(0, 0)]))
    arcade.run()
