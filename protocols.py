from typing import Protocol


class IronDrawer(Protocol):
    def add_iron(self, position: tuple[int, int]):
        raise NotImplementedError

    def remove_all_iron(self, position: tuple[int, int]):
        raise NotImplementedError

class GridEnlarger(Protocol):
    def enlarge_grid(self):
        raise NotImplementedError