import pytest
from pyglet.math import Vec2
from trainfinity2.grid import Grid
from trainfinity2.model import Player, Rail, Station
from trainfinity2.signal_controller import SignalController
from trainfinity2.terrain import Terrain
from trainfinity2.train import Train


@pytest.fixture
def mock_gui():
    class MockGui:
        def update_score(self, value, level, score_to_grid_increase):
            pass

    return MockGui


@pytest.fixture
def player(mock_gui):
    return Player(mock_gui(), lambda: None)


@pytest.fixture
def mock_grid():
    return Grid(Terrain(water=[Vec2(0, 0)]), SignalController())


class TestPlayer:
    def test_level_is_increased_when_score_passes_threshold(self, player):
        player.score = 10

        assert player._level == 1


class TestRail:
    def test_other_end_error(self):
        rail = Rail(0, 0, 30, 0)
        with pytest.raises(ValueError):
            rail.other_end(999, 999)


@pytest.fixture
def train(player, mock_grid: Grid):
    station1 = Station(Vec2(0, 0))
    station2 = Station(Vec2(30, 0))
    mock_grid.create_rail([Rail(0, 0, 30, 0)])
    return Train(
        player, station1, station2, mock_grid, SignalController(), wagon_count=3
    )


class TestTrain:
    def test_move_east(self, train):
        train.target_x = 100
        train.x = 0
        train.move(1 / 60)

        assert train.x == pytest.approx(1 / 90)

    def test_move_west(self, train):
        train.target_x = -100
        train.x = 0
        train.move(1 / 60)

        assert train.x == pytest.approx(-1 / 90)

    def test_move_north(self, train):
        train.target_y = 100
        train.y = 0
        train.move(1 / 60)

        assert train.y == pytest.approx(1 / 90)

    def test_move_south(self, train):
        train.target_y = -100
        train.y = 0
        train.move(1 / 60)

        assert train.y == pytest.approx(-1 / 90)


# class TestSignal:
#     def test_calling_other_rail_with_nonadjacent_rail_throws_error(self):
#         rail1 = Rail(0, 0, 30, 0)
#         rail2 = Rail(30, 0, 60, 0)
#         signal_connection1 = SignalConnection(
#             rail1,
#             Vec2(0, 0),
#         )
#         signal_connection2 = SignalConnection(
#             rail2,
#             Vec2(90, 0),
#         )
#         signal = Signal(30, 0, (signal_connection1, signal_connection2))

#         with pytest.raises(ValueError):
#             signal.other_rail(Rail(30, 30, 30, 30))
