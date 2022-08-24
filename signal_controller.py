from dataclasses import dataclass
from typing import Any
import typing

from pyglet.math import Vec2

from model import Rail, Signal, SignalColor
from observer import CreateEvent, Event, Observer, Subject, ChangeEvent
from protocols import RailCollection, SignalCollection, TrainCollection
from train import RailChangedEvent, Train


@dataclass
class SignalBlock:
    rails: frozenset[Rail]
    signals: list[Signal]


class SignalController(Subject, Observer):
    def __init__(
        self,
        train_collection: TrainCollection,
        signal_collection: SignalCollection,
        rail_collection: RailCollection,
    ):
        super().__init__()
        self._train_collection = train_collection
        self._signal_collection = signal_collection
        self._rail_collection = rail_collection
        self._signal_blocks: list[SignalBlock] = []

    def _create_signal_blocks(self):
        rails = set(self._rail_collection.rails)
        rail_sets: list[set[Rail]] = []
        signal_lists: list[list[Signal]] = []
        while rails:
            rail_sets.append(set())
            signal_lists.append([])
            rail = list(rails)[0]
            positions = rail.positions
            while positions:
                position = positions.pop()
                if signal := self._signal_collection.signals.get(Vec2(*position)):
                    if signal not in signal_lists[-1]:
                        # TODO: make Signal immutable to make signal_lists to signal_sets instead
                        signal_lists[-1].append(signal)
                else:
                    new_rails = self._rail_collection.rails_at_position(*position)
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

    def _signal_at_position(self, x, y):
        return next(
            (
                signal
                for signal in self._signal_collection.signals
                if signal.x == x and signal.y == y
            ),
            None,
        )

    def _is_train_in_signal_block(self, block: SignalBlock):
        return any(
            train._current_rail in block.rails
            for train in self._train_collection.trains
        )

    def _get_signal_block_containing(self, rail: Rail) -> SignalBlock:
        for block in self._signal_blocks:
            if rail in block.rails:
                return block
        raise AssertionError(
            "Shouldn't be possible, something must have gone wrong creating signal blocks."
        )

    def on_notify(self, object: Any, event: Event):
        match object, event:
            case Signal(), CreateEvent():
                self._create_signal_blocks()
            case Train(), RailChangedEvent():
                event = typing.cast(RailChangedEvent, event)
                for signal_block in self._signal_blocks:
                    new_color = (
                        SignalColor.RED
                        if self._is_train_in_signal_block(signal_block)
                        else SignalColor.GREEN
                    )
                    for signal in signal_block.signals:
                        for connection in signal.connections:
                            if connection.rail not in signal_block.rails:
                                if new_color != connection.signal_color:
                                    connection.signal_color = new_color
                                    for observer in self._observers[ChangeEvent]:
                                        observer.on_notify(signal, ChangeEvent())
