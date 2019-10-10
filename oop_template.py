import pyglet


class TestGame(pyglet.window.Window):
    def __init__(self):
        super().__init__()

    def setup(self):
        pass

    def on_draw(self):
        self.clear()

    def update(self, delta_time):
        pass


def main():
    game_window = TestGame()
    game_window.setup()
    pyglet.clock.schedule_interval(game_window.update, 1 / 60)
    pyglet.app.run()


if __name__ == "__main__":
    main()
