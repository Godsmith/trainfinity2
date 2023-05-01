from dataclasses import dataclass, field
from pyglet.math import Vec2


@dataclass
class Wagon:
    x: float
    y: float
    iron: int = 0
    target_x: int = field(init=False)
    target_y: int = field(init=False)

    def __post_init__(self):
        super().__init__()
        self.target_x = int(self.x)
        self.target_y = int(self.y)

    def move(self, delta_time: float, speed: float):
        pixels_moved = delta_time * speed
        if self.x > self.target_x + pixels_moved:
            self.x -= pixels_moved
        elif self.x < self.target_x - pixels_moved:
            self.x += pixels_moved
        if self.y > self.target_y + pixels_moved:
            self.y -= pixels_moved
        elif self.y < self.target_y - pixels_moved:
            self.y += pixels_moved
