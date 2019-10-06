import pyglet


class TestGame(pyglet.window.Window):
    def __init__(self):
        super().__init__()
        self.image = pyglet.image.load('sprites/test_image.png')

        x = self.image.get_image_data()
        data = x.get_data('RGBA', x.width * 4)
        print(len(data))
        print(data[0])
        print(type(data))
        print(type(data[0]))
        print(data)
        print(data[0])
        data = b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\xff\xff\xff\x00'
        ba = bytearray(data)
        print(ba)
        ba[0] = 0
        ba[1] = 0
        ba[2] = 0
        x.set_data('RGBA', x.width * 4, data=bytes(ba))
        print(self.image)
        self.image.save('sprites/test_image1.png')
        self.test_sprite = pyglet.sprite.Sprite(self.image, x=100, y=100)

    def setup(self):
        pass

    def on_draw(self):
        self.clear()
        self.test_sprite.draw()

    def update(self, delta_time):
        pass


def main():
    game_window = TestGame()
    game_window.setup()
    pyglet.clock.schedule_interval(game_window.update, 1 / 60)
    pyglet.app.run()


if __name__ == "__main__":
    main()
