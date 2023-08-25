from dataclasses import dataclass

from pyglet.math import Vec2

from .model import Signal, SignalColor
from .protocols import RailCollection


@dataclass
class SignalBlock:
    """
    A block of rails reserved by a train.

    I have tried a lot of different approaches:

      1. Signals on squares and trains reserve positions
         Did not work because a position needed to belong to multiple signal blocks
         and that made reserving the next position hard
      2. Signals on rails and trains reserve rails
         Did not work because two different trains can reserve the same
         square, leading to collisions

    Current approach: train reserves positions, but signals on rails. That should at
    least solve the previous problems.
    """

    positions: frozenset[Vec2]
    signals: frozenset[Signal]
    reserved_by: int | None = False

    # def __post_init__(self):
    #     count_from_rail_position = Counter(
    #         position for rail in self.rails for position in rail.positions
    #     )
    #     self.edge_positions = {
    #         position
    #         for position, count in count_from_rail_position.items()
    #         if count == 1
    #     }

    @property
    def _color(self):
        return SignalColor.RED if self.reserved_by else SignalColor.GREEN

    def update_signals(self):
        for signal in self.signals:
            signal.signal_color = self._color


class SignalController:
    def __init__(
        self,
    ):
        super().__init__()
        # self._signal_blocks: list[SignalBlock] = []
        self._signal_block_from_position: dict[Vec2, SignalBlock] = {}
        self._signals: list[Signal] = []
        self._reserved_position_from_reserver_id: dict[int, Vec2] = {}

    def __repr__(self) -> str:
        return (
            f"SignalController({', '.join(repr(signal) for signal in self._signals)})"
        )

    def _create_signal_block(
        self,
        available_positions: set[Vec2],
        # TODO: consider just taking a dict here instead of a RailCollection,
        # perhaps less confusing
        rail_collection: RailCollection,
        signals: list[Signal],
    ) -> SignalBlock:
        """
        1. Add a random available position P1 to the signal block
        2. If there is no position in the signal block that has not been handled, finish
        3. Get a random position in the signal block that has not been handled
        4. For each of the neighboring rails
          4.1. Skip if the rail already has been traversed or if it has signal
          3.2. Else, add the position P2 to the signal block
        4. Add P1 to the list of handled positions
        5. Go to 2.
        """
        rails_with_signals = {signal.rail for signal in signals}
        signal_block_positions: set[Vec2] = {list(available_positions)[0]}
        traversed_positions: set[Vec2] = set()
        # Remove this if turns out not needed
        # traversed_rails: set[Rail] = set()
        block_signals = set()
        while signal_block_positions - traversed_positions:
            position = list(signal_block_positions - traversed_positions)[0]
            new_rails = rail_collection.rails_at_position(position)

            block_signals |= {
                signal
                for signal in signals
                if signal.rail in new_rails and signal.from_position != position
            }

            signal_block_positions.update(
                {
                    neighboring_position
                    for new_rail in new_rails
                    for neighboring_position in new_rail.positions
                    if new_rail not in rails_with_signals
                }
            )
            traversed_positions.add(position)
        return SignalBlock(frozenset(signal_block_positions), frozenset(block_signals))

    def create_signal_blocks(
        self,
        rail_collection: RailCollection,
        signals: list[Signal],
    ):
        """Recreate all the signal blocks. Needed if something has been updated that can affect them,
        such as rail having been created or deleted.

        Signal blocks always include the signals bordering the block, so the blocks have an overlap
        of one position to the next block.

        OPTIMIZATION OPPORTUNITY: Currently all signal blocks are recreated each time. It would be
        enough if the signal blocks that are affected are recreated, such as the once in proximity
        to the rail being deleted, for example."""
        # This line is not used in this method, should it be in the constructor instead?
        self._signals = list(signals)

        self._signal_blocks: list[SignalBlock] = []
        available_positions = set().union(
            *[rail.positions for rail in rail_collection.rails]
        )
        while available_positions:
            signal_block = self._create_signal_block(
                available_positions=available_positions,
                rail_collection=rail_collection,
                signals=signals,
            )
            self._signal_blocks.append(signal_block)
            available_positions -= signal_block.positions
        self._signal_block_from_position = {
            position: signal_block
            for signal_block in self._signal_blocks
            for position in signal_block.positions
        }

        self._update_signal_block_reservations()

    def reserver(self, position: Vec2) -> int | None:
        return self._signal_block_from_position[position].reserved_by

    def reserve(self, reserver_id: int, position: Vec2):
        """Called by trains when they enter a new rail. The correct blocks
        are then reserved and unreserved."""
        self._reserved_position_from_reserver_id[reserver_id] = position
        self._update_signal_block_reservations()

    def unreserve(self, reserver_id: int):
        """Called by a train when it is destroyed."""
        if reserver_id in self._reserved_position_from_reserver_id:
            del self._reserved_position_from_reserver_id[reserver_id]
        self._update_signal_block_reservations()

    def _update_signal_block_reservations(self):
        for signal_block in self._signal_blocks:
            signal_block.reserved_by = None
            for id_, position in self._reserved_position_from_reserver_id.items():
                if position in signal_block.positions:
                    signal_block.reserved_by = id_
        self._update_signals()

    def _update_signals(self):
        for signal_block in self._signal_blocks:
            signal_block.update_signals()
