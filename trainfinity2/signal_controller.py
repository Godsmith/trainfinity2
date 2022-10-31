from collections import defaultdict
from dataclasses import dataclass

from pyglet.math import Vec2

from .model import Signal, SignalColor, Rail
from .protocols import RailCollection


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
        self._reserved_position_from_reserver_id: dict[int, Vec2] = {}

    def __repr__(self) -> str:
        s = "SignalController("
        for signal in self._signals:
            for connection in signal.connections:
                s += f"({signal.x},{signal.y})->({connection.towards_position.x, connection.towards_position.y}): {connection.signal_color.name}, "
        return s

    def _create_signal_block(
        self,
        original_available_rails: set[Rail],
        rail_collection: RailCollection,
        signal_from_position: dict[Vec2, Signal],
    ) -> tuple[SignalBlock, set[Rail]]:
        available_rails = set(original_available_rails)
        signal_block_positions = set()
        rail = available_rails.pop()
        edge_positions = set(rail.positions)
        while edge_positions:
            position = edge_positions.pop()
            signal_block_positions.add(position)
            if position in signal_from_position:
                continue
            available_rails_at_position = rail_collection.rails_at_position(
                *position
            ).intersection(available_rails)
            for new_rail in available_rails_at_position:
                available_rails.discard(new_rail)
                edge_positions.update(
                    new_position
                    for new_position in new_rail.positions
                    if new_position not in signal_block_positions
                )
        return SignalBlock(
            frozenset(signal_block_positions)
        ), original_available_rails.difference(available_rails)

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
        self._signals = list(signal_from_position.values())
        # TODO: did the following line make all blocks unreserved when recreating
        # signal blocks? Try to comment it out, it might improve stability.
        # self._reserved_position_from_reserver_id: dict[int, Vec2] = {}
        rails = set(rail_collection.rails)
        self._signal_blocks = []
        while rails:
            signal_block, used_rails = self._create_signal_block(
                rails, rail_collection, signal_from_position
            )
            self._signal_blocks.append(signal_block)
            rails.difference_update(used_rails)
        # TODO: create a new class SignalBlockCollection or similar to avoid two vars
        self._signal_blocks_from_position = defaultdict(list)
        for signal_block in self._signal_blocks:
            for position in signal_block.positions:
                self._signal_blocks_from_position[position].append(signal_block)

        self._update_signal_block_reservations()

    def is_unreserved(self, position: Vec2) -> bool:
        signal_blocks_at_position = self._signal_blocks_from_position[position]
        if len(signal_blocks_at_position) == 1:
            return True
        return not all(
            signal_block.reserved for signal_block in signal_blocks_at_position
        )

    def reserve(self, reserver_id: int, new_position: Vec2):
        """Called by trains when they enter a new position. The correct blocks
        are then reserved and unreserved."""
        self._reserved_position_from_reserver_id[reserver_id] = new_position
        self._update_signal_block_reservations()

    def _update_signal_block_reservations(self):
        for signal_block in self._signal_blocks:
            signal_block.reserved = bool(
                signal_block.positions.intersection(
                    self._reserved_position_from_reserver_id.values()
                )
            )
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
