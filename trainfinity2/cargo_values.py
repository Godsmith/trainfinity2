from .model import CargoType

CARGO_VALUES: dict[CargoType, int] = {
    CargoType.COAL: 1,
    CargoType.IRON: 1,
    CargoType.LOGS: 1,
    CargoType.PLANKS: 3,
    CargoType.STEEL: 3,
    CargoType.TOOLS: 10,
}
