import pytest
from grid import Grid
from model import Rail, Station
from pyglet.math import Vec2

from tests.util import create_grid_objects


@pytest.fixture
def grid(game):
    return game.grid


def test_create_horizontal_rail(grid: Grid):
    map_ = """
 -
"""
    create_grid_objects(grid, map_)

    assert set(grid.rails) == {Rail(0, 0, 0, 30)}


def test_create_vertical_rail(grid: Grid):
    map_ = r"""

|
 
"""
    create_grid_objects(grid, map_)

    assert set(grid.rails) == {Rail(0, 0, 30, 0)}


def test_create_diagonal_rail_1(grid: Grid):
    map_ = r"""

 /
 
"""
    create_grid_objects(grid, map_)

    assert set(grid.rails) == {Rail(0, 0, 30, 30)}


def test_create_diagonal_rail_2(grid: Grid):
    map_ = r"""

 \
 
"""
    create_grid_objects(grid, map_)

    assert set(grid.rails) == {Rail(0, 30, 30, 0)}


def test_create_multiple_rail(grid: Grid):
    map_ = r"""
   - 
 /   \
       
|     |
       
 \   /
   - 
"""
    create_grid_objects(grid, map_)

    assert set(grid.rails) == {
        Rail(x1=0, y1=30, x2=30, y2=0),
        Rail(x1=30, y1=0, x2=60, y2=0),
        Rail(x1=60, y1=0, x2=90, y2=30),
        Rail(x1=0, y1=60, x2=30, y2=90),
        Rail(x1=60, y1=90, x2=90, y2=60),
        Rail(x1=0, y1=30, x2=0, y2=60),
        Rail(x1=30, y1=90, x2=60, y2=90),
        Rail(x1=90, y1=30, x2=90, y2=60),
    }


def test_create_stations_mine_and_factory(grid: Grid):
    map_ = r"""
  M   F  

 -S- -S-
"""
    create_grid_objects(grid, map_)

    assert grid.mines == {}
    assert grid.stations == {Vec2(0, 30): Station(0, 30)}
