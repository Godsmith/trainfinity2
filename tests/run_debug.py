"""Can be run with

  hatch run python -m tests.run_debug

to start a game with some objects already created for easier testing."""
import arcade
from trainfinity2.__main__ import Game, Window
from pyglet.math import Vec2
from trainfinity2.model import CoalMine, IronMine, Rail, Station, SteelWorks
from trainfinity2.events import Event
from trainfinity2.terrain import Terrain


def init(game: Game):
    events: list[Event] = []
    game.setup(Terrain(water=[Vec2(0, 0)]))
    events.extend(
        (
            game.grid.create_building(IronMine(Vec2(2, 2))),
            game.grid.create_building(CoalMine(Vec2(7, 7))),
            game.grid.create_building(SteelWorks(Vec2(7, 2))),
        )
    )
    events.extend(
        game.grid.create_rail(
            {
                Rail(1, 3, 2, 3),
                Rail(2, 3, 3, 3),
                Rail(3, 3, 4, 3),
                Rail(4, 3, 5, 3),
                Rail(5, 3, 6, 3),
                Rail(6, 3, 7, 3),
                Rail(3, 3, 4, 4),
                Rail(4, 4, 5, 4),
                Rail(5, 4, 6, 3),
                Rail(8, 7, 8, 6),
                Rail(8, 6, 8, 5),
                Rail(8, 5, 8, 4),
                Rail(8, 4, 8, 3),
                Rail(8, 3, 8, 2),
            }
        )
    )
    events.extend(
        (
            game.grid.create_station(Station((Vec2(8, 7),), east_west=False)),
            game.grid.create_station(Station((Vec2(8, 2),), east_west=False)),
            game.grid.create_station(Station((Vec2(2, 3),))),
            game.grid.create_station(Station((Vec2(7, 3),))),
        )
    )
    game.drawer.handle_events(events)
    # game._create_signal(3, 2)
    # game._create_signal(3, 3)
    # game._create_signal(4, 2)
    # game._create_signal(4, 3)
    # game._create_train(station1, station2)
    # game._create_train(station2, station1)


if __name__ == "__main__":
    game = Game()
    window = Window(game)
    init(game)
    arcade.run()
