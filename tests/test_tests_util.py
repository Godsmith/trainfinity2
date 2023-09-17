from pyglet.math import Vec2
from trainfinity2.model import (
    IronMine,
    Rail,
    SignalColor,
    Station,
    Building,
    SteelWorks,
)
from trainfinity2.__main__ import Game

from tests.util import create_objects


def test_create_horizontal_rail(game: Game):
    create_objects(
        game.grid,
        """
        .-.""",
    )

    assert set(game.grid.rails) == {Rail(0, 0, 1, 0)}


def test_create_vertical_rail(game: Game):
    create_objects(
        game.grid,
        r"""
         .
         |
         .""",
    )

    assert set(game.grid.rails) == {Rail(0, 0, 0, 1)}


def test_create_diagonal_rail_1(game: Game):
    create_objects(
        game.grid,
        r"""
         . .
         ./.
         . . """,
    )

    assert set(game.grid.rails) == {Rail(0, 0, 1, 1)}


def test_create_diagonal_rail_2(game: Game):
    create_objects(
        game.grid,
        r"""
         . .
          \
         . . """,
    )

    assert set(game.grid.rails) == {Rail(1, 0, 0, 1)}


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
        Rail(x1=1, y1=0, x2=0, y2=1),
        Rail(x1=1, y1=0, x2=2, y2=0),
        Rail(x1=2, y1=0, x2=3, y2=1),
        Rail(x1=0, y1=2, x2=1, y2=3),
        Rail(x1=3, y1=2, x2=2, y2=3),
        Rail(x1=0, y1=1, x2=0, y2=2),
        Rail(x1=1, y1=3, x2=2, y2=3),
        Rail(x1=3, y1=1, x2=3, y2=2),
    }


def test_create_objects(game: Game):
    create_objects(
        game.grid,
        """
    . M . F .

    .-S-.hS-.""",
    )

    assert game.grid.buildings == {
        Vec2(1, 1): IronMine(Vec2(1, 1)),
        Vec2(3, 1): SteelWorks(Vec2(3, 1)),
    }
    assert game.grid.station_from_position == {
        Vec2(3, 0): Station((Vec2(3, 0),)),
        Vec2(1, 0): Station((Vec2(1, 0),)),
    }
    signal_facing_west = game.grid.signals[(Vec2(2, 0), Rail(2, 0, 3, 0))]
    signal_facing_east = game.grid.signals[(Vec2(3, 0), Rail(2, 0, 3, 0))]
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
    assert game.grid.buildings == {Vec2(1, 1): IronMine(Vec2(1, 1))}


def test_create_with_offset_and_last_line(game: Game):
    create_objects(
        game.grid,
        """
        . M

        . .
        """,
    )
    assert game.grid.buildings == {Vec2(1, 1): IronMine(Vec2(1, 1))}
