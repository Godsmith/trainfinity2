from collections import defaultdict
from dataclasses import dataclass, field

from trainfinity2.model import CargoType


@dataclass
class Wagon:
    x: float
    y: float
    cargo_count: dict[CargoType, int] = field(init=False)
    angle: float = 0

    def __post_init__(self):
        self.cargo_count = defaultdict(int)
