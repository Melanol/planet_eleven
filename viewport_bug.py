import pyglet
from pyglet import gl
from pyglet.window import key

window = pyglet.window.Window(640, 480)

left_border = 0
bottom_border = 0


def update_viewport():
    gl.glViewport(left_border, bottom_border, 640, 480)

@window.event
def on_draw():
    window.clear()
    pyglet.graphics.draw(1, pyglet.gl.GL_POINTS, ('v2i', (100, 100)))

@window.event
def on_key_press(symbol, modifiers):
    global left_border, bottom_border
    if symbol == key.LEFT:
        left_border -= 100
        update_viewport()
    elif symbol == key.RIGHT:
        left_border += 100
        update_viewport()
    elif symbol == key.UP:
        bottom_border += 100
        update_viewport()
    elif symbol == key.DOWN:
        bottom_border -= 100
        update_viewport()

@window.event
def on_mouse_press(x, y, button, modifiers):
    print(x, y)


pyglet.app.run()
