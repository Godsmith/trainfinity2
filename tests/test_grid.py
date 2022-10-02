from pyglet.math import Vec2
from trainfinity2.constants import GRID_BOX_SIZE
from trainfinity2.grid import positions_between

i = GRID_BOX_SIZE


class TestPositionsBetween:
    def test_positions_between(self):
        assert positions_between(Vec2(0, 0), Vec2(1 * i, 2 * i)) == [
            Vec2(0, 0),
            Vec2(0, 1 * i),
            Vec2(1 * i, 2 * i),
        ]
