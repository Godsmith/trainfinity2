"""Can be run with

  hatch run python -m tests.run_debug

to start a game with some objects already created for easier testing."""
import arcade
from trainfinity2.__main__ import Game, Window
from pyglet.math import Vec2
from trainfinity2.model import Rail
from trainfinity2.terrain import Terrain

game = Game()
window = Window(game)
game.setup(Terrain(water=[Vec2(0, 0)]))
game.grid._create_mine(Vec2(30, 30))
game.grid._create_factory(Vec2(180, 30))
game.grid.create_rail(
    [
        Rail(0, 60, 30, 60),
        Rail(30, 60, 60, 60),
        Rail(60, 60, 90, 60),
        Rail(90, 60, 120, 60),
        Rail(120, 60, 150, 60),
        Rail(150, 60, 180, 60),
        Rail(60, 60, 90, 90),
        Rail(90, 90, 120, 90),
        Rail(120, 90, 150, 60),
    ]
)
station1 = game.grid._create_station(Vec2(30, 60), True)
station2 = game.grid._create_station(Vec2(180, 60), True)
# game._create_signal(90, 60)
# game._create_signal(90, 90)
# game._create_signal(120, 60)
# game._create_signal(120, 90)
# game._create_train(station1, station2)
# game._create_train(station2, station1)

arcade.run()
