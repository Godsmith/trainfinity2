import pytest
from grid import Grid
from model import Mine, Player, Rail, Station
from signal_controller import SignalController
from train import Train
from pyglet.math import Vec2
from terrain import Terrain


@pytest.fixture
def mock_gui():
    class MockGui:
        def update_score(self, value, level, score_to_grid_increase):
            pass

    return MockGui


@pytest.fixture
def mock_drawer():
    class MockDrawer:
        def __init__(self, width, height) -> None:
            pass

        def enlarge_grid(self):
            pass

    return MockDrawer


class MockTrainCollection:
    trains: list[Train] = []


@pytest.fixture
def player(mock_gui, mock_drawer):
    return Player(mock_gui(), mock_drawer(800, 600))


@pytest.fixture
def mock_grid():
    return Grid(Terrain(water=[Vec2(0, 0)]))


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
    station1 = Station(0, 0, Mine(0, 0))
    station2 = Station(30, 0, Mine(0, 0))
    mock_grid._create_rail([Rail(0, 0, 30, 0)])
    return Train(
        player, station1, station2, mock_grid, SignalController(MockTrainCollection())
    )


class TestTrain:
    def test_move_east(self, train):
        train.target_x = 100
        train.x = 0
        train.move(1 / 60)

        assert train.x == pytest.approx(2)

    def test_move_west(self, train):
        train.target_x = -100
        train.x = 0
        train.move(1 / 60)

        assert train.x == pytest.approx(-2)

    def test_move_north(self, train):
        train.target_y = 100
        train.y = 0
        train.move(1 / 60)

        assert train.y == pytest.approx(2)

    def test_move_south(self, train):
        train.target_y = -100
        train.y = 0
        train.move(1 / 60)

        assert train.y == pytest.approx(-2)
