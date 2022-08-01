from typing import Protocol


class IronDrawer(Protocol):
    def add_iron(self, position: tuple[int, int]):
        pass

    def remove_all_iron(self, position: tuple[int, int]):
        pass