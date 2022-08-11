from typing import Protocol


class GridEnlarger(Protocol):
    def enlarge_grid(self):
        raise NotImplementedError
