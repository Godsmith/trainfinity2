from dataclasses import dataclass
from typing import Any
import typing

from pyglet.math import Vec2

from model import Rail, Signal, SignalColor
from observer import CreateEvent, Event
from protocols import RailCollection, SignalCollection, TrainCollection


@dataclass
class SignalBlock:
    rails: frozenset[Rail]
    signals: list[Signal]


class SignalController:
    def __init__(
        self,
        train_collection: TrainCollection,
    ):
        super().__init__()
        self._train_collection = train_collection
        self._signal_blocks: list[SignalBlock] = []

    def create_signal_blocks(
        self, rail_collection: RailCollection, signal_collection: SignalCollection
    ):
        rails = set(rail_collection.rails)
        rail_sets: list[set[Rail]] = []
        signal_lists: list[list[Signal]] = []
        while rails:
            rail_sets.append(set())
            signal_lists.append([])
            rail = list(rails)[0]
            positions = rail.positions
            while positions:
                position = positions.pop()
                if signal := signal_collection.signals.get(Vec2(*position)):
                    if signal not in signal_lists[-1]:
                        # TODO: make Signal immutable to make signal_lists to signal_sets instead
                        signal_lists[-1].append(signal)
                else:
                    new_rails = rail_collection.rails_at_position(*position)
                    for rail in new_rails:
                        if rail in rails:
                            rail_sets[-1].add(rail)
                            rails.remove(rail)
                            for position in rail.positions:
                                positions.add(position)
        self._signal_blocks = [
            SignalBlock(frozenset(rail_set), list(signal_list))
            for rail_set, signal_list in zip(rail_sets, signal_lists)
        ]

    def _get_color(self, block: SignalBlock) -> SignalColor:
        return (
            SignalColor.RED
            if self._is_train_in_signal_block(block)
            else SignalColor.GREEN
        )

    def _is_train_in_signal_block(self, block: SignalBlock):
        return any(
            train._current_rail in block.rails
            for train in self._train_collection.trains
        )

    def update_signals(self):
        for signal_block in self._signal_blocks:
            for signal in signal_block.signals:
                rail = [
                    connection.rail
                    for connection in signal.connections
                    if connection.rail not in signal_block.rails
                ][0]
                signal.set_signal_color(rail, self._get_color(signal_block))
