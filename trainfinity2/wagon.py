from dataclasses import dataclass


@dataclass
class Wagon:
    x: float
    y: float
    iron: int = 0
    angle: float = 0
