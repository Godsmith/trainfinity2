from dataclasses import dataclass


class Event:
    pass


@dataclass
class DestroyEvent(Event):
    object: object


@dataclass
class CreateEvent(Event):
    object: object
