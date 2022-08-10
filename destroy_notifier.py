from collections import defaultdict
from typing import Protocol


class Destroyable(Protocol):
    def destroy(self):
        raise NotImplementedError


class DestroyableObserver(Protocol):
    def destroyable_is_destroyed(self, destroyable: Destroyable):
        raise NotImplementedError


class DestroyNotifier:
    _observers: dict[int, list[DestroyableObserver]] = defaultdict(list)

    @classmethod
    def register_observer(cls, observer: DestroyableObserver, destroyable):
        cls._observers[id(destroyable)].append(observer)

    @classmethod
    def destroyable_is_destroyed(cls, destroyable: Destroyable):
        for observer in cls._observers[id(destroyable)]:
            observer.destroyable_is_destroyed(destroyable)
        del cls._observers[id(destroyable)]
