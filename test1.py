import pickle
import pyglet
from pyglet.window import key


arr = [1, 2, 3]


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
        global arr
        if symbol == key.F1:
            pickle.dump(arr, open("save.p", "wb"))
        elif symbol == key.F2:
            arr = pickle.load(open("save.p", "rb"))
        elif symbol == key._1:
            arr = [1, 2, 3]
        elif symbol == key._2:
            arr = [4, 5, 6]
        elif symbol == key.H:
            print(arr)


def main():
    game_window = TestGame()
    game_window.setup()
    pyglet.clock.schedule_interval(game_window.update, 1 / 60)
    pyglet.app.run()


if __name__ == "__main__":
    main()
