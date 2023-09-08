from dataclasses import dataclass

from trainfinity2.model import CargoType


@dataclass
class Wagon:
    x: float
    y: float
    cargo_type: CargoType = CargoType.IRON
    cargo_count: int = 0
    angle: float = 0
