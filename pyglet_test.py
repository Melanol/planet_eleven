import pyglet
from pyglet import gl
from pyglet.window import key

window = pyglet.window.Window(800, 600)

test_img = pyglet.resource.image('sprites/tank.png')
gl.glTexParameteri(test_img.target, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
gl.glTexParameteri(test_img.target, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
test_img.anchor_x = test_img.width // 2
test_img.anchor_y = test_img.width // 2

test_sprite = pyglet.sprite.Sprite(img=test_img, x=300, y=400)
left_border = 0
bottom_border = 0

def update_viewport():
    gl.glViewport(left_border, bottom_border, 800, 600)

@window.event
def on_key_press(symbol, modifiers):
    if symbol == key.LEFT:
        test_sprite.rotation -= 33
    elif symbol == key.RIGHT:
        test_sprite.rotation += 33
    elif symbol == key.UP:
        gl.glViewport(0, 100, 800, 600)
    elif symbol == key.DOWN:
        gl.glViewport(0, 0, 800, 600)

@window.event
def on_draw():
    window.clear()
    test_sprite.draw()

pyglet.app.run()
