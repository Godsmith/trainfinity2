from _typeshed import Incomplete
from collections.abc import Iterable
from perlin_noise.rand_vec import RandVec as RandVec
from perlin_noise.tools import each_with_each as each_with_each, hasher as hasher
from typing import Optional, Union

class PerlinNoise:
    octaves: Incomplete
    seed: Incomplete
    cache: Incomplete
    def __init__(self, octaves: float = ..., seed: Optional[int] = ...) -> None: ...
    def __call__(self, coordinates: Union[int, float, Iterable]) -> float: ...
    def noise(self, coordinates: Union[int, float, Iterable]) -> float: ...
    def get_from_cache_of_create_new(self, coors): ...
