import pyglet
from pyglet.window import key
from pyglet import gl
import resources


SCREEN_WIDTH = 683
SCREEN_HEIGHT = 384
SCREEN_TITLE = "Planet Eleven"
POS_SPACE = 32
POS_COORDS_N_COLUMNS = 20
POS_COORDS_N_ROWS = 15
POS_COORDS = []
for yi in range(1, POS_COORDS_N_ROWS + 1):
    for xi in range(1, POS_COORDS_N_COLUMNS + 1):
        POS_COORDS.append((xi * POS_SPACE - POS_SPACE / 2, yi * POS_SPACE - POS_SPACE / 2))
print(len(POS_COORDS))
utilities_batch = pyglet.graphics.Batch()

class Planet_Eleven(pyglet.window.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title, fullscreen=False)

    def setup(self):
        self.dots = []
        for x, y in POS_COORDS:
            self.dots.append(pyglet.sprite.Sprite(img=resources.minimap_ally_image, x=x, y=y, batch=utilities_batch))
        print(len(self.dots))

    def on_draw(self):
        self.clear()
        utilities_batch.draw()

    def update(self, delta_time):
        pass

    def on_key_press(self, symbol, modifiers):
        if symbol == key.UP:
            gl.glViewport(reversed_left_view_border, reversed_bottom_view_border, SCREEN_WIDTH, SCREEN_HEIGHT)

def main():
    game_window = Planet_Eleven(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    game_window.setup()
    pyglet.clock.schedule_interval(game_window.update, 1/120)
    pyglet.app.run()


if __name__ == "__main__":
    main()