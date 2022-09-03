from collections import defaultdict
from dataclasses import dataclass

from pyglet.math import Vec2

from model import Signal, SignalColor
from protocols import RailCollection


@dataclass
class SignalBlock:
    positions: frozenset[Vec2]
    reserved: bool = False

    @property
    def color(self):
        return SignalColor.RED if self.reserved else SignalColor.GREEN


class SignalController:
    def __init__(
        self,
    ):
        super().__init__()
        self._signal_blocks: list[SignalBlock] = []
        self._signal_blocks_from_position: dict[Vec2, list[SignalBlock]] = defaultdict(
            list
        )
        self._signals: list[Signal] = []

    def create_signal_blocks(
        self, rail_collection: RailCollection, signal_from_position: dict[Vec2, Signal]
    ):
        """Recreate all the signal blocks. Needed if something has been updated that can affect them,
        such as rail having been created or deleted.

        Signal blocks always include the signals bordering the block, so the blocks have an overlap
        of one position to the next block.

        OPTIMIZATION OPPORTUNITY: Currently all signal blocks are recreated each time. It would be
        enough if the signal blocks that are affected are recreated, such as the once in proximity
        to the rail being deleted, for example."""
        rails = set(rail_collection.rails)
        self._signals = list(signal_from_position.values())
        position_sets: list[set[Vec2]] = []
        self._signal_blocks_from_position = defaultdict(list)
        while rails:
            position_sets.append(set())
            rail = list(rails)[0]
            positions = rail.positions
            while positions:
                position = positions.pop()
                position_sets[-1].add(position)
                if position not in signal_from_position:
                    new_rails = rail_collection.rails_at_position(*position)
                    for rail in new_rails:
                        if rail in rails:
                            rails.remove(rail)
                            for position in rail.positions:
                                positions.add(position)
        self._signal_blocks = [
            SignalBlock(frozenset(position_set)) for position_set in position_sets
        ]
        for signal_block in self._signal_blocks:
            for position in signal_block.positions:
                self._signal_blocks_from_position[position].append(signal_block)

        self._update_signals()

    def change_block_reservation(self, new_position: Vec2, left_position: Vec2):
        """Called by trains when they enter a new position. The correct blocks
        are then reserved and unreserved."""
        signal_update_needed = False
        for signal_block in self._signal_blocks_from_position[left_position]:
            signal_block.reserved = False
            signal_update_needed = True
        for signal_block in self._signal_blocks_from_position[new_position]:
            signal_block.reserved = True
            signal_update_needed = True
        if signal_update_needed:
            self._update_signals()

    def _update_signals(self):
        for signal in self._signals:
            for connection in signal.connections:
                signal_block = self._signal_blocks_from_position[
                    connection.towards_position
                ][
                    0
                ]  # Should always just be one signal block here
                signal.set_signal_color(
                    signal.other_rail(connection.rail), signal_block.color
                )
