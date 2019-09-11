import pyglet
from pyglet.window import key

pyglet.resource.path = ['sprites']
pyglet.resource.reindex()

def center_anchor(image):
    image.anchor_x = image.width / 2
    image.anchor_y = image.height / 2

test_image = pyglet.resource.image("test.png")
center_anchor(test_image)

class MyGame(pyglet.window.Window):
    def __init__(self):
        super().__init__()
        self.test_sprite = pyglet.sprite.Sprite(img=test_image, x=100, y=100)

    def on_draw(self):
        self.clear()
        self.test_sprite.draw()

    def update(self, delta_time):
        pass

    def on_key_press(self, symbol, modifiers):
        if symbol == key.UP:
            self.test_sprite.rotation = 90
        elif symbol == key.DOWN:
            self.test_sprite.rotation = -90
        elif symbol == key.RIGHT:
            self.test_sprite.rotation = 0
        elif symbol == key.LEFT:
            self.test_sprite.rotation = 180

def main():
    game_window = MyGame()
    pyglet.clock.schedule_interval(game_window.update, 1/120)
    pyglet.app.run()


if __name__ == "__main__":
    main()
