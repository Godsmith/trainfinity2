from dataclasses import dataclass, field
import math
from pyglet.math import Vec2
from math import pi

def approx_equal(a: float, b: float):
    return abs(a - b) < 1.0


@dataclass
class Wagon:
    x: float
    y: float
    iron: int = 0
    angle: float = 0
    target_x: int = field(init=False)
    target_y: int = field(init=False)

    def __post_init__(self):
        super().__init__()
        self.target_x = int(self.x)
        self.target_y = int(self.y)

    def move(self, delta_time: float, speed: float):
        pixels_moved = delta_time * speed
        dx = 0
        dy = 0
        if self.x > self.target_x + pixels_moved:
            dx = -pixels_moved
        elif self.x < self.target_x - pixels_moved:
            dx = pixels_moved
        if self.y > self.target_y + pixels_moved:
            dy = -pixels_moved
        elif self.y < self.target_y - pixels_moved:
            dy = pixels_moved

        if approx_equal(self.angle % 90.0, 45.0):
            dx /= math.sqrt(2)
            dy /= math.sqrt(2)

        self.x += dx
        self.y += dy
        self.angle = -(Vec2(dx, dy).heading * 360 / 2 / pi - 90)
