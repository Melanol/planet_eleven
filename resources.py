from pyglet.gl import *


def center_anchor(image):
    image.anchor_x = image.width / 2
    image.anchor_y = image.height / 2
    glTexParameteri(image.target, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
    glTexParameteri(image.target, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)


def right_bottom_anchor(image):
    image.anchor_x = image.width
    glTexParameteri(image.target, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
    glTexParameteri(image.target, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)


pyglet.resource.path = ['sprites']
pyglet.resource.reindex()

# Utilities
background_image = pyglet.resource.image("background.png")

selection_image = pyglet.resource.image("selection.png")
center_anchor(selection_image)

rally_point_image = pyglet.resource.image("rally_point.png")
center_anchor(rally_point_image)

control_panel_image = pyglet.resource.image("control_panel.png")
right_bottom_anchor(control_panel_image)

control_panel_buttons_background_image = pyglet.resource.image("control_panel_buttons_background.png")
center_anchor(control_panel_buttons_background_image)

minimap_black_background_image = pyglet.resource.image("minimap_black_background.png")

minimap_textured_background_image = pyglet.resource.image("minimap_textured_background.png")

utility_dot_image = pyglet.resource.image("utility_dot.png")
center_anchor(utility_dot_image)

minimap_cam_frame_image = pyglet.resource.image("minimap_cam_frame.png")

minimap_our_image = pyglet.resource.image("minimap_our.png")
center_anchor(minimap_our_image)

minimap_enemy_image = pyglet.resource.image("minimap_enemy.png")
center_anchor(minimap_enemy_image)

# Controls
move_image = pyglet.resource.image("move.png")
center_anchor(move_image)

stop_image = pyglet.resource.image("stop.png")
center_anchor(stop_image)

attack_image = pyglet.resource.image("attack.png")
center_anchor(attack_image)

# Buildings
base_image = pyglet.resource.image("base.png")
center_anchor(base_image)

enemy_base_image = pyglet.resource.image("enemy_base.png")
center_anchor(enemy_base_image)

turret_button_image = pyglet.resource.image("turret_button.png")
center_anchor(turret_button_image)
turret_image = pyglet.resource.image("turret.png")
center_anchor(turret_image)
turret_base_image = pyglet.resource.image("turret_base.png")
center_anchor(turret_base_image)

# Units
tank_image = pyglet.resource.image("tank.png")
center_anchor(tank_image)
tank_shadow_image = pyglet.resource.image("tank_shadow.png")
center_anchor(tank_shadow_image)

vulture_image = pyglet.resource.image("vulture.png")
center_anchor(vulture_image)
vulture_shadow_image = pyglet.resource.image("vulture_shadow.png")
center_anchor(vulture_shadow_image)

defiler_image = pyglet.resource.image("defiler.png")
center_anchor(defiler_image)
defiler_shadow_image = pyglet.resource.image("defiler_shadow.png")
center_anchor(defiler_shadow_image)

builder_image = pyglet.resource.image("builder.png")
center_anchor(builder_image)
builder_shadow_image = pyglet.resource.image("builder_shadow.png")
center_anchor(builder_shadow_image)

# Other
projectile_image = pyglet.resource.image("laser.png")
center_anchor(projectile_image)
