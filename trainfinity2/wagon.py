from collections import defaultdict
from dataclasses import dataclass, field

from trainfinity2.model import CargoType


@dataclass
class Wagon:
    x: float
    y: float
    cargo_types: set[CargoType] = field(init=False)
    cargo_count: dict[CargoType, int] = field(init=False)
    angle: float = 0

    def __post_init__(self):
        self.cargo_types = {CargoType.IRON, CargoType.COAL}
        self.cargo_count = defaultdict(int)
