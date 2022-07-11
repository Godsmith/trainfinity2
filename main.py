from re import S
from pyglet.math import Vec2
import arcade

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

GRID_BOX_SIZE = 30
GRID_LINE_WIDTH = 1
GRID_COLOR = arcade.color.BLACK

# Min zoom = 1/MAX_CAMERA_SCALE, i.e. 25%
MAX_CAMERA_SCALE = 4
# Max zoom = 1/MIN_CAMERA_SCALE, i.e. 200%
MIN_CAMERA_SCALE = 0.5


class MyGame(arcade.Window):

    VISIBLE = True  # Overridden for unit testing

    def __init__(self):
        super().__init__(
            width=SCREEN_WIDTH,
            height=SCREEN_HEIGHT,
            title="TRAINFINITY",
            visible=self.VISIBLE,
        )

        self.horizontal_grid_lines = []
        self.vertical_grid_lines = []

        arcade.set_background_color(arcade.color.BUD_GREEN)

        self.camera_sprites = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.camera_gui = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

        self.is_mouse2_pressed = False
        self.mouse2_pressed_x = 0
        self.mouse2_pressed_y = 0
        self.camera_position_when_mouse2_pressed = self.camera_sprites.position

    def setup(self):
        pass

    def _draw_grid(self):
        for x in range(0, SCREEN_WIDTH + 1, GRID_BOX_SIZE):
            arcade.draw_line(x, 0, x, SCREEN_HEIGHT, GRID_COLOR, GRID_LINE_WIDTH)

        for y in range(0, SCREEN_HEIGHT + 1, GRID_BOX_SIZE):
            arcade.draw_line(0, y, SCREEN_WIDTH, y, GRID_COLOR, GRID_LINE_WIDTH)

    def on_draw(self):
        self.clear()

        self.camera_sprites.use()

        self._draw_grid()

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        if button == arcade.MOUSE_BUTTON_RIGHT:
            self.mouse2_pressed_x = x
            self.mouse2_pressed_y = y
            self.is_mouse2_pressed = True
            self.camera_position_when_mouse2_pressed = self.camera_sprites.position

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        self.is_mouse2_pressed = False

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        if self.is_mouse2_pressed:
            delta = Vec2(x - self.mouse2_pressed_x, y - self.mouse2_pressed_y)

            # Required for panning to work correctly when zoomed in or out
            delta = delta.scale(self.camera_sprites.scale)

            new_position = self.camera_position_when_mouse2_pressed - delta

            self.camera_sprites.move(new_position)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        if scroll_y < 0:
            scale_delta = 0.1
        else:
            scale_delta = -0.1

        new_scale = self.camera_sprites.scale + scale_delta
        new_scale = min(new_scale, MAX_CAMERA_SCALE)
        new_scale = max(new_scale, MIN_CAMERA_SCALE)

        self.camera_sprites.scale = new_scale


def main():
    window = MyGame()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
