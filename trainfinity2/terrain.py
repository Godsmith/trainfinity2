from itertools import product

from perlin_noise import PerlinNoise
from pyglet.math import Vec2

from .constants import GRID_BOX_SIZE, GRID_HEIGHT, GRID_WIDTH, WATER_TILES


class Terrain:
    def __init__(
        self,
        water: list[Vec2] | None = None,
        sand: list[Vec2] | None = None,
        mountains: list[Vec2] | None = None,
    ):
        self.water = water or []
        self.sand = sand or []
        self.mountains = mountains or []
        if not water and not sand and not mountains:
            noise1 = PerlinNoise(octaves=3)
            noise2 = PerlinNoise(octaves=6)
            noise3 = PerlinNoise(octaves=12)
            noise4 = PerlinNoise(octaves=24)
            for x, y in product(
                range(-GRID_WIDTH * 2, GRID_WIDTH * 3 + 1, GRID_BOX_SIZE),
                range(-GRID_HEIGHT * 2, GRID_HEIGHT * 3 + 1, GRID_BOX_SIZE),
            ):
                noise_val = noise1([x / GRID_WIDTH, y / GRID_WIDTH])
                noise_val += 0.5 * noise2([x / GRID_WIDTH, y / GRID_WIDTH])
                noise_val += 0.25 * noise3([x / GRID_WIDTH, y / GRID_WIDTH])
                # noise_val += 0.125 * noise4([x / GRID_WIDTH, y / GRID_WIDTH])

                if noise_val < -0.1:
                    self.water.append(Vec2(x, y))
                elif noise_val < 0:
                    self.sand.append(Vec2(x, y))
                elif noise_val > 0.4:
                    self.mountains.append(Vec2(x, y))
