from pyglet.gl import *


def center_anchor(image):
    image.anchor_x = image.width / 2
    image.anchor_y = image.height / 2


def right_bottom_anchor(image):
    image.anchor_x = image.width


pyglet.resource.path = ['sprites']
pyglet.resource.reindex()

selection_image = pyglet.resource.image("selection.png")
center_anchor(selection_image)

rally_point_image = pyglet.resource.image("rally_point.png")
center_anchor(rally_point_image)

control_panel_image = pyglet.resource.image("control_panel.png")
right_bottom_anchor(control_panel_image)
glTexParameteri(control_panel_image.target, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
glTexParameteri(control_panel_image.target, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)

utility_dot_image = pyglet.resource.image("utility_dot.png")
center_anchor(utility_dot_image)

minimap_ally_image = pyglet.resource.image("minimap_ally.png")
center_anchor(minimap_ally_image)
glTexParameteri(minimap_ally_image.target, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
glTexParameteri(minimap_ally_image.target, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)

base_image = pyglet.resource.image("base.png")
center_anchor(base_image)

tank_image = pyglet.resource.image("tank.png")
center_anchor(tank_image)

vulture_image = pyglet.resource.image("vulture.png")
center_anchor(vulture_image)
glTexParameteri(vulture_image.target, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
glTexParameteri(vulture_image.target, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)

vulture_shadow_image = pyglet.resource.image("vulture_shadow.png")
center_anchor(vulture_shadow_image)

defiler_image = pyglet.resource.image("defiler.png")
center_anchor(defiler_image)
