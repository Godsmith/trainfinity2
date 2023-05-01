from trainfinity2.train import (
    _find_equidistant_points_and_angles_along_line,
    PointAndAngle,
)
from pyglet.math import Vec2


class TestFindEquidistantPointsAndAnglesAlongLine:
    def test_two_point_line(self):
        line_points = [Vec2(0.0, 0.0), Vec2(1.0, 0.0)]
        n = 1
        distance = 0.5
        points = list(
            _find_equidistant_points_and_angles_along_line(line_points, n, distance)
        )
        assert points == [PointAndAngle(Vec2(0.5, 0.0), 90.0)]

    def test_three_point_line(self):
        line_points = [Vec2(0.0, 0.0), Vec2(3.0, 0.0), Vec2(6.0, 0.0)]
        n = 2
        distance = 2.0
        points = list(
            _find_equidistant_points_and_angles_along_line(line_points, n, distance)
        )
        assert points == [
            PointAndAngle(Vec2(2.0, 0.0), 90.0),
            PointAndAngle(Vec2(4.0, 0.0), 90.0),
        ]

    def test_three_point_line_with_angle(self):
        line_points = [Vec2(0.0, 0.0), Vec2(3.0, 0.0), Vec2(3.0, 3.0)]
        n = 2
        distance = 2.0
        points = list(
            _find_equidistant_points_and_angles_along_line(line_points, n, distance)
        )
        assert points == [
            PointAndAngle(Vec2(2.0, 0.0), 90.0),
            PointAndAngle(Vec2(3.0, 1.0), 0.0),
        ]

    def test_repeatedly_return_last_point_of_line_if_line_runs_out(self):
        line_points = [Vec2(0.0, 0.0), Vec2(1.0, 0.0)]
        n = 2
        distance = 2.0
        points = list(
            _find_equidistant_points_and_angles_along_line(line_points, n, distance)
        )
        assert points == [
            PointAndAngle(Vec2(1.0, 0.0), 0.0),
            PointAndAngle(Vec2(1.0, 0.0), 0.0),
        ]
