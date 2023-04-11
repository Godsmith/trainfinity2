from pyglet.math import Vec2
from trainfinity2.model import Rail, Signal
from trainfinity2.signal_controller import SignalController


class Rails:
    def __init__(self, rails: list[Rail]) -> None:
        self.rails = rails

    def rails_at_position(self, x, y) -> set[Rail]:
        return {rail for rail in self.rails if rail.is_at_position(x, y)}


class TestCreateSignalBlocks:
    def test_three_rails_and_one_signal_creates_two_signal_blocks(self):
        controller = SignalController()
        rail1 = Rail(0, 0, 30, 0)
        rail2 = Rail(30, 0, 60, 0)
        rail3 = Rail(60, 0, 90, 0)
        rails = Rails([rail1, rail2, rail3])

        signal1 = Signal(Vec2(30, 0), rail2)
        signal2 = Signal(Vec2(60, 0), rail2)
        signals = [signal1, signal2]

        controller.create_signal_blocks(rail_collection=rails, signals=signals)
        signal_block_1, signal_block_2 = controller._signal_blocks
        assert signal_block_1.positions == {Vec2(60, 0), Vec2(90, 0)}
        assert signal_block_2.positions == {Vec2(0, 0), Vec2(30, 0)}
        assert signal_block_1.signals == frozenset({signal1})
        assert signal_block_2.signals == frozenset({signal2})
