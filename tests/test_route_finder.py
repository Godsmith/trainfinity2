from tests.util import create_objects
from trainfinity2.game import Game
from trainfinity2.model import Rail
from trainfinity2.route_finder import find_route
from pyglet.math import Vec2


class TestFindRoute:
    def test_find_route(self, game: Game):
        create_objects(
            game,
            """
            . M . F .

            .-S-.-S-.
            """,
        )
        station1, station2 = [*game.grid.stations.values()]
        game._create_train(station1, station2)
        assert find_route(
            game.grid.possible_next_rails_ignore_red_lights,
            starting_rails=[Rail(30, 0, 60, 0)],
            initial_position=Vec2(30, 0),
            target_station=station2,
        ) == [Rail(30, 0, 60, 0), Rail(60, 0, 90, 0)]
