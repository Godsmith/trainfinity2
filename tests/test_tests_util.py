from pyglet.math import Vec2
from trainfinity2.model import Factory, Mine, Rail, SignalColor, Station
from trainfinity2.__main__ import Game

from tests.util import create_objects


def test_create_horizontal_rail(game: Game):
    create_objects(
        game.grid,
        """
        .-.""",
    )

    assert set(game.grid.rails) == {Rail(0, 0, 30, 0)}


def test_create_vertical_rail(game: Game):
    create_objects(
        game.grid,
        r"""
         .
         |
         .""",
    )

    assert set(game.grid.rails) == {Rail(0, 0, 0, 30)}


def test_create_diagonal_rail_1(game: Game):
    create_objects(
        game.grid,
        r"""
         . .
         ./.
         . . """,
    )

    assert set(game.grid.rails) == {Rail(0, 0, 30, 30)}


def test_create_diagonal_rail_2(game: Game):
    create_objects(
        game.grid,
        r"""
         . .
          \
         . . """,
    )

    assert set(game.grid.rails) == {Rail(30, 0, 0, 30)}


def test_create_multiple_rail(game: Game):
    map_ = r"""
. .-. .
 /   \
. . . .
|     |
. . . .
 \   /
. .-. .
"""
    create_objects(game.grid, map_)

    assert set(game.grid.rails) == {
        Rail(x1=30, y1=0, x2=0, y2=30),
        Rail(x1=30, y1=0, x2=60, y2=0),
        Rail(x1=60, y1=0, x2=90, y2=30),
        Rail(x1=0, y1=60, x2=30, y2=90),
        Rail(x1=90, y1=60, x2=60, y2=90),
        Rail(x1=0, y1=30, x2=0, y2=60),
        Rail(x1=30, y1=90, x2=60, y2=90),
        Rail(x1=90, y1=30, x2=90, y2=60),
    }


def test_create_objects(game: Game):
    create_objects(
        game.grid,
        """
    . M . F .

    .-S-.hS-.""",
    )

    assert game.grid.mines == {Vec2(30, 30): Mine(Vec2(30, 30))}
    assert game.grid.factories == {Vec2(90, 30): Factory(Vec2(90, 30))}
    assert game.grid.station_from_position == {
        Vec2(90, 0): Station((Vec2(90, 0),)),
        Vec2(30, 0): Station((Vec2(30, 0),)),
    }
    signal_facing_west = game.grid.signals[(Vec2(60, 0), Rail(60, 0, 90, 0))]
    signal_facing_east = game.grid.signals[(Vec2(90, 0), Rail(60, 0, 90, 0))]
    assert signal_facing_west.signal_color == SignalColor.GREEN
    assert signal_facing_east.signal_color == SignalColor.GREEN
    assert len(game.grid.signals) == 2


def test_create_with_offset(game: Game):
    create_objects(
        game.grid,
        """
        . M

        . .""",
    )
    assert game.grid.mines == {Vec2(30, 30): Mine(Vec2(30, 30))}


def test_create_with_offset_and_last_line(game: Game):
    create_objects(
        game.grid,
        """
        . M

        . .
        """,
    )
    assert game.grid.mines == {Vec2(30, 30): Mine(Vec2(30, 30))}
