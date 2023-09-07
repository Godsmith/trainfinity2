from pyglet.math import Vec2
from pytest import fixture
from tests.util import create_objects
from trainfinity2.grid import Grid, positions_between
from trainfinity2.model import Rail, Station
from trainfinity2.signal_controller import SignalController
from trainfinity2.terrain import Terrain


@fixture
def grid():
    # Add a single water tile, or real terrain will be generated
    return Grid(
        terrain=Terrain(water=[Vec2(210, 210)]), signal_controller=SignalController()
    )


class TestPositionsBetween:
    def test_positions_between(self):
        assert positions_between(Vec2(0, 0), Vec2(1, 2)) == [
            Vec2(0, 0),
            Vec2(0, 1),
            Vec2(1, 2),
        ]


class TestBuildStation:
    def test_cannot_build_station_away_from_mine_or_factory(self, grid: Grid):
        create_objects(
            grid,
            """
            M . .

            . . .

            . . .
            """,
        )
        assert grid._illegal_station_positions(Station((Vec2(1, 0), Vec2(2, 0)))) == {
            Vec2(1, 0),
            Vec2(2, 0),
        }

    def test_cannot_build_station_if_rail_in_wrong_direction(self, grid: Grid):
        create_objects(
            grid,
            """
            . . M
              |
            . . .

            . . .
            """,
        )
        assert grid._illegal_station_positions(Station((Vec2(1, 1), Vec2(2, 1)))) == {
            Vec2(1, 1)
        }

    def test_can_build_station_if_rail_in_right_direction_vertical(self, grid: Grid):
        create_objects(
            grid,
            """
            . . M
              |
            . . .

            . . .
            """,
        )
        assert (
            grid._illegal_station_positions(Station((Vec2(1, 1), Vec2(1, 2)))) == set()
        )

    def test_can_build_station_right_to_left_if_rail_in_right_direction(
        self, grid: Grid
    ):
        create_objects(
            grid,
            """
            . M .

            . .-. .
            """,
        )
        assert (
            grid._illegal_station_positions(Station((Vec2(2, 0), Vec2(1, 0)))) == set()
        )

    def test_can_build_station_partly_overlapping_rail(self, grid: Grid):
        create_objects(
            grid,
            """
            . M .

            .-.-.
            """,
        )
        assert (
            grid._illegal_station_positions(Station((Vec2(2, 0), Vec2(1, 0)))) == set()
        )


class TestBuildRail:
    def test_cannot_build_rail_on_station_if_wrong_direction(self, grid: Grid):
        create_objects(
            grid,
            """
            . .

            S .
            """,
        )
        rail = grid._mark_illegal_rail([Rail(0, 0, 0, 1)]).pop()
        assert not rail.legal

    def test_can_build_rail_on_station_if_right_direction(self, grid: Grid):
        create_objects(
            grid,
            """
            . .

            S .
            """,
        )
        rail = grid._mark_illegal_rail([Rail(0, 0, 1, 0)]).pop()
        assert rail.legal
