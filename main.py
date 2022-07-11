import arcade

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

GRID_BOX_SIZE = 30
GRID_LINE_WIDTH = 1
GRID_COLOR = arcade.color.BLACK


class MyGame(arcade.Window):
    def __init__(self):
        super().__init__(width=SCREEN_WIDTH, height=SCREEN_HEIGHT, title="TRAINFINITY")

        self.horizontal_grid_lines = []
        self.vertical_grid_lines = []

        arcade.set_background_color(arcade.color.BUD_GREEN)

    def setup(self):
        pass

    def _draw_grid(self):
        for x in range(0, SCREEN_WIDTH + 1, GRID_BOX_SIZE):
            arcade.draw_line(x, 0, x, SCREEN_HEIGHT, GRID_COLOR, GRID_LINE_WIDTH)

        for y in range(0, SCREEN_HEIGHT + 1, GRID_BOX_SIZE):
            arcade.draw_line(0, y, SCREEN_WIDTH, y, GRID_COLOR, GRID_LINE_WIDTH)

    def on_draw(self):
        self.clear()

        self._draw_grid()


def main():
    window = MyGame()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
