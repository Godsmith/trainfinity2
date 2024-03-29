from _typeshed import Incomplete
from perlin_noise.tools import (
    dot as dot,
    fade as fade,
    product as product,
    sample_vector as sample_vector,
)
from typing import List, Tuple

class RandVec:
    coordinates: Incomplete
    vec: Incomplete
    def __init__(self, coordinates: Tuple[int], seed: int) -> None: ...
    def dists_to(self, coordinates: List[float]) -> Tuple[float, ...]: ...
    def weight_to(self, coordinates: List[float]) -> float: ...
    def get_weighted_val(self, coordinates: List[float]) -> float: ...
