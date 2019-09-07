import pyglet
from pyglet.gl import *


def center_image(image):
    """Sets an image's anchor point to its center"""
    image.anchor_x = image.width / 2
    image.anchor_y = image.height / 2


pyglet.resource.path = ['sprites']
pyglet.resource.reindex()

selection_image = pyglet.resource.image("selection.png")
center_image(selection_image)

rally_point_image = pyglet.resource.image("rally_point.png")
center_image(rally_point_image)

minimap_ally_image = pyglet.resource.image("minimap_ally.png")
center_image(minimap_ally_image)

base_image = pyglet.resource.image("base.png")
center_image(base_image)

tank_image = pyglet.resource.image("tank.png")
center_image(tank_image)

vulture_image = pyglet.resource.image("vulture.png")
center_image(vulture_image)
glTexParameteri(vulture_image.target, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
glTexParameteri(vulture_image.target, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)

vulture_shadow_image = pyglet.resource.image("vulture_shadow.png")
center_image(vulture_shadow_image)

defiler_image = pyglet.resource.image("defiler.png")
center_image(defiler_image)