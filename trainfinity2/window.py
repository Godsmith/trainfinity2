import arcade
from arcade import color

from .drawer import Drawer
from .game import Game
from .model import Station

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600


class Window(arcade.Window):
    def __init__(self, game: Game):
        super().__init__(
            width=SCREEN_WIDTH,
            height=SCREEN_HEIGHT,
            title="TRAINFINITY",
            resizable=True,
        )  # type: ignore
        self._game = game
        arcade.set_background_color(color.BUD_GREEN)

    def on_update(self, delta_time: float):
        super().on_update(delta_time)
        self._game.on_update(delta_time)

    def on_draw(self):
        super().on_draw()
        self.clear()
        self._game.on_draw()

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self._game.on_resize(width, height)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        super().on_mouse_motion(x, y, dx, dy)
        self._game.on_mouse_motion(x, y, dx, dy)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        super().on_mouse_press(x, y, button, modifiers)
        self._game.on_mouse_press(x, y, button, modifiers)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        super().on_mouse_release(x, y, button, modifiers)
        self._game.on_mouse_release(x, y, button, modifiers)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        super().on_mouse_scroll(x, y, scroll_x, scroll_y)
        self._game.on_mouse_scroll(x, y, scroll_x, scroll_y)
