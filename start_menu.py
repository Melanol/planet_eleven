import pyglet
from pyglet.window import key
from pyglet.window import mouse
import os



class TestGame(pyglet.window.Window):
    def __init__(self):
        super().__init__()

    def setup(self):
        pass

    def on_draw(self):
        self.clear()

    def update(self, delta_time):
        pass

    def on_key_press(self, symbol, modifiers):
        if symbol == key.F1:
            os.system('python planet_eleven.py')


def main():
    game_window = TestGame()
    game_window.setup()
    pyglet.clock.schedule_interval(game_window.update, 1 / 60)
    pyglet.app.run()


if __name__ == "__main__":
    main()
