from collections import defaultdict
from typing import Any, Protocol, Type


class Event:
    pass


class DestroyEvent(Event):
    pass


class CreateEvent(Event):
    pass


class ChangeEvent(Event):
    pass


class Observer(Protocol):
    def on_notify(self, object: Any, event: Event):
        raise NotImplementedError


class Subject:
    def __init__(self):
        self._observers: dict[Type[Event], list[Observer]] = defaultdict(list)
        super().__init__()

    def add_observer(self, observer: Observer, event_type: Type[Event]):
        self._observers[event_type].append(observer)

    # def remove_observer(self, observer: Observer, event_type: Type[Event]):
    #     self._observers[event_type].remove(observer)

    def notify(self, event: Event):
        for observer in self._observers[type(event)]:
            observer.on_notify(self, event)
