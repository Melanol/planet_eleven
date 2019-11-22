import sys
import pyglet
import time
from pyglet.window import key
from pyglet.window import mouse

start_time = time.time()
class TestGame(pyglet.window.Window):
    def __init__(self):
        super().__init__()\

    def setup(self):
        self.frame_count = 0

    def on_draw(self):
        self.clear()

    def update(self, delta_time):
        self.frame_count += 1
        if self.frame_count % 60 == 0:
            print('wakka wakka')
        if self.frame_count == 360:
            print(time.time() - start_time)
            sys.exit()

    def on_key_press(self, symbol, modifiers):
        pass

    def on_mouse_press(self, x, y, button, modifiers):
        pass


def main():
    game_window = TestGame()
    game_window.setup()
    pyglet.clock.schedule_interval(game_window.update, 1 / 60)
    pyglet.app.run()


if __name__ == "__main__":
    main()
