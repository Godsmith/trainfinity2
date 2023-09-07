from tests.util import create_objects
from trainfinity2.game import Game
from trainfinity2.model import Rail
from trainfinity2.route_finder import find_route
from pyglet.math import Vec2


class TestFindRoute:
    def test_find_route(self, game: Game):
        create_objects(
            game.grid,
            """
            . M . F .

            .-S-.-S-.
            """,
        )
        station1, station2 = [*game.grid.station_from_position.values()]
        game._create_train(station1, station2)
        assert find_route(
            game.grid.possible_next_rails_ignore_red_lights,
            starting_rails={Rail(1, 0, 2, 0)},
            initial_position=Vec2(1, 0),
            target_station=station2,
        ) == [Rail(1, 0, 2, 0), Rail(2, 0, 3, 0)]

    def test_find_route_visit_some_rails_twice_in_different_directions(
        self, game: Game
    ):
        create_objects(
            game.grid,
            r"""
            . M . F . . .-. .
                       /   \
            .-S-.-S-.-. . . .
                     \      |
            . . . . . . . . .
                       \   /
            . . . . . . .-. .
            """,
        )
        station1, station2 = sorted(
            game.grid.station_from_position.values(),
            key=lambda station: station.positions[0],
        )
        game._create_train(station1, station2)
        result = find_route(
            game.grid.possible_next_rails_ignore_red_lights,
            starting_rails={Rail(3, 2, 4, 2)},
            initial_position=Vec2(3, 2),
            target_station=station1,
        )
        assert result
        assert len(result) == 13

    def test_cannot_find_route_if_heading_in_wrong_direction(self, game: Game):
        create_objects(
            game.grid,
            r"""
            . M . F .

            .-S-.-S-.

            . . . . .

            . . . . .
            """,
        )
        station1, station2 = sorted(
            game.grid.station_from_position.values(),
            key=lambda station: station.positions[0],
        )
        game._create_train(station1, station2)
        result = find_route(
            game.grid.possible_next_rails_ignore_red_lights,
            starting_rails={Rail(3, 2, 4, 2)},
            initial_position=Vec2(3, 2),
            target_station=station1,
        )
        assert result is None
