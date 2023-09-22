from pyglet.math import Vec2
from pytest import fixture
from trainfinity2.model import Station
from trainfinity2.station_builder import StationBuilder, _furthest_between


@fixture
def stations():
    return {Station(positions=(Vec2(2, 0), Vec2(3, 0)))}


class TestGetStationBeingBuilt:
    def test_new_station(self):
        actual = StationBuilder().get_station_being_built_and_replaced(
            set(), 1, 0, 0, 0
        )
        assert actual == (Station(positions=(Vec2(0, 0), Vec2(1, 0))), None)

    def test_extend_station_in_one_direction(self, stations: set[Station]):
        actual = StationBuilder().get_station_being_built_and_replaced(
            stations, 4, 0, 4, 0
        )
        assert actual == (
            Station(positions=(Vec2(2, 0), Vec2(3, 0), Vec2(4, 0))),
            stations.pop(),
        )

    def test_extend_station_in_both_directions(self, stations: set[Station]):
        actual = StationBuilder().get_station_being_built_and_replaced(
            stations, 1, 0, 4, 0
        )
        assert actual == (
            Station(positions=(Vec2(1, 0), Vec2(2, 0), Vec2(3, 0), Vec2(4, 0))),
            stations.pop(),
        )

    def test_extend_station_when_ending_drag_on_adjacent_square(
        self, stations: set[Station]
    ):
        actual = StationBuilder().get_station_being_built_and_replaced(
            stations, 5, 0, 4, 0
        )
        assert actual == (
            Station(positions=(Vec2(2, 0), Vec2(3, 0), Vec2(4, 0), Vec2(5, 0))),
            stations.pop(),
        )

    def test_extend_station_when_neither_start_nor_stop_is_adjacent(
        self, stations: set[Station]
    ):
        actual = StationBuilder().get_station_being_built_and_replaced(
            stations, 1, 0, 6, 0
        )
        assert actual == (
            Station(
                positions=(
                    Vec2(1, 0),
                    Vec2(2, 0),
                    Vec2(3, 0),
                    Vec2(4, 0),
                    Vec2(5, 0),
                    Vec2(6, 0),
                )
            ),
            stations.pop(),
        )


def test_furthest_between():
    assert _furthest_between([Vec2(0, 0), Vec2(3, 4), Vec2(0, 2), Vec2(-1, 0)]) == (
        Vec2(3, 4),
        Vec2(-1, 0),
    )
