from collections import defaultdict
from dataclasses import dataclass
from typing import Any
import typing

from pyglet.math import Vec2

from model import Rail, Signal, SignalColor
from observer import CreateEvent, Event
from protocols import RailCollection, SignalCollection, TrainCollection


@dataclass(frozen=True)
class SignalBlock:
    positions: frozenset[Vec2]


class SignalController:
    def __init__(
        self,
        train_collection: TrainCollection,
    ):
        super().__init__()
        self._train_collection = train_collection
        self._signal_blocks: list[SignalBlock] = []
        self._signals: dict[Vec2, Signal] = {}
        self._signal_block_from_position: dict[Vec2, SignalBlock] = {}

    def create_signal_blocks(
        self, rail_collection: RailCollection, signal_collection: SignalCollection
    ):
        self._signals = signal_collection.signals
        rails = set(rail_collection.rails)
        position_sets: list[set[Vec2]] = []
        while rails:
            position_sets.append(set())
            rail = list(rails)[0]
            positions = rail.positions
            while positions:
                position = positions.pop()
                position_sets[-1].add(position)
                if position not in signal_collection.signals:
                    new_rails = rail_collection.rails_at_position(*position)
                    for rail in new_rails:
                        if rail in rails:
                            rails.remove(rail)
                            for position in rail.positions:
                                positions.add(position)
        self._signal_blocks = [
            SignalBlock(frozenset(position_set)) for position_set in position_sets
        ]

        self._signal_block_from_position = {
            position: signal_block
            for signal_block in self._signal_blocks
            for position in signal_block.positions
        }

        self.update_signals()

    def _get_color(self, block: SignalBlock) -> SignalColor:
        return (
            SignalColor.RED
            if self._is_train_in_signal_block(block)
            else SignalColor.GREEN
        )

    def _is_train_in_signal_block(self, block: SignalBlock):
        return any(
            train._current_rail
            and train._current_rail.positions.intersection(block.positions)
            for train in self._train_collection.trains
        )

    def update_signals(self):
        for signal in self._signals.values():
            for connection in signal.connections:
                signal_block = self._signal_block_from_position[
                    connection.towards_position
                ]
                color = self._get_color(signal_block)
                signal.set_signal_color(signal.other_rail(connection.rail), color)
