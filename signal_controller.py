from dataclasses import dataclass
from model import Rail, Signal, SignalColor


@dataclass(frozen=True)
class SignalBlock:
    rails: frozenset[Rail]
    signals: frozenset[Signal]


class SignalController:
    def __init__(self):
        self._signal_blocks: set[SignalBlock] = set()

    def _create_signal_blocks(self):
        pass

    # def _update_signal_colors_because_train_passed_signal(self, signal: Signal, new_rail: Rail):
    #     new_block = self._signal_block_containing(new_rail)
    #     old_block = self._signal_block_containing(signal.other_rail(new_rail))

    #     new_block.signals

    # def _signal_block_contains_trains(self, block: SignalBlock):
    #     for train in self.

    def _signal_block_containing(self, rail: Rail):
        for block in self._signal_blocks:
            if rail in block.rails:
                return block
        raise AssertionError(
            "Shouldn't be possible, something must have gone wrong creating signal blocks."
        )

    def signal_is_stop(self, signal: Signal, towards_rail: Rail):
        other_rail = signal.other_rail(towards_rail)
        block = self._signal_block_containing(other_rail)
        return self._signal_block_contains_trains(block)
