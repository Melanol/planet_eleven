import pyglet
from pyglet.gl import *


class App(pyglet.window.Window):

    def __init__(self, width, height, *args, **kwargs):
        conf = Config(sample_buffers=1,
                      samples=4,
                      depth_size=16,
                      double_buffer=True)
        super().__init__(width, height, config=conf, *args, **kwargs)

        # Initialize camera values
        self.left = 0
        self.right = width
        self.bottom = 0
        self.top = height

        pyglet.resource.path = ['sprites']
        pyglet.resource.reindex()
        tank_image = pyglet.resource.image("tank.png")
        self.tank_sprite = pyglet.sprite.Sprite(img=tank_image, x=300, y=300)

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.H:
            print(self.tank_sprite.y)
        elif symbol == pyglet.window.key.UP:
            self.tank_sprite.y += 10
        elif symbol == pyglet.window.key.DOWN:
            self.tank_sprite.y -= 10

    def on_mouse_press(self, x, y, button, modifiers):
        print(x, y)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        # Move camera
        self.left -= dx
        self.right -= dx
        self.bottom -= dy
        self.top -= dy

    def on_draw(self):
        # Initialize Projection matrix
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        # Initialize Modelview matrix
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        # Save the default modelview matrix
        glPushMatrix()

        # Clear window with ClearColor
        glClear(GL_COLOR_BUFFER_BIT)

        # Set orthographic projection matrix
        glOrtho(self.left, self.right, self.bottom, self.top, 1, -1)

        self.tank_sprite.draw()
        # Remove default modelview matrix
        glPopMatrix()

    def run(self):
        pyglet.app.run()


App(500, 500).run()
