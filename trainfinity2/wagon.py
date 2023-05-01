from dataclasses import dataclass, field
from pyglet.math import Vec2
from math import pi


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
        self.x += dx
        self.y += dy
        self.angle = -(Vec2(dx, dy).heading * 360 / 2 / pi - 90)
