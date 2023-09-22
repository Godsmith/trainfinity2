from pyglet.math import Vec2


def positions_between(start: Vec2, end: Vec2) -> list[Vec2]:
    positions = [start]
    while positions[-1] != end:
        current = positions[-1]
        abs_dx = abs(current.x - end.x)
        abs_dy = abs(current.y - end.y)
        x_step = (end.x - current.x) // abs_dx if abs_dx else 0
        y_step = (end.y - current.y) // abs_dy if abs_dy else 0
        new_x = current.x + (abs_dx >= abs_dy) * x_step
        new_y = current.y + (abs_dy >= abs_dx) * y_step
        positions.append(Vec2(new_x, new_y))
    return positions
