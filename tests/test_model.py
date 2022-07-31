import arcade

from pytest import MonkeyPatch
import pytest
from drawer import Drawer
from gui import Gui
from model import Player


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


class TestPlayer:
    def test_level_is_increased_when_score_passes_threshold(
        self, mock_gui, mock_drawer
    ):
        player = Player(mock_gui(), mock_drawer(800, 600))

        player.score = 10

        assert player._level == 1
