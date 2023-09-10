import arcade

from .game import Game
from .terrain import Terrain
from .window import Window

if __name__ == "__main__":
    game = Game()
    window = Window(game)
    game.setup(Terrain())
    arcade.run()
