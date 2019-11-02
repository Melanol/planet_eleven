from pyglet.gl import *
from pyglet.image.atlas import TextureAtlas


class BorderedTextureAtlas(TextureAtlas):
    def add(self, img):
        x, y = self.allocator.alloc(img.width+2, img.height+2)
        self.texture.blit_into(img, x+1, y+1, 0)
        return self.texture.get_region(x+1, y+1, img.width, img.height)


pyglet.image.atlas.TextureAtlas = BorderedTextureAtlas


def center_anchor(image):
    image.anchor_x = image.width / 2
    image.anchor_y = image.height / 2
    glTexParameteri(image.target, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
    glTexParameteri(image.target, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)


def right_bottom_anchor(image):
    image.anchor_x = image.width
    glTexParameteri(image.target, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
    glTexParameteri(image.target, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)


def big_building_anchor(image):
    image.anchor_x = 16
    image.anchor_y = 16
    glTexParameteri(image.target, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
    glTexParameteri(image.target, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)


pyglet.resource.path = ['sprites']
pyglet.resource.reindex()

# Utilities
cursor = pyglet.window.ImageMouseCursor(pyglet.image.load('sprites/cursor.png'), 0, 16)
cursor_fullscreen = pyglet.window.ImageMouseCursor(pyglet.image.load('sprites/cursor_fullscreen.png'), 0, 32)
move_cursor = pyglet.window.ImageMouseCursor(pyglet.image.load('sprites/move_cursor.png'), 0, 16)

background_image = pyglet.resource.image("background.png")

selection_image = pyglet.resource.image("selection.png")
center_anchor(selection_image)

selection_big_image = pyglet.resource.image("selection_big.png")
center_anchor(selection_big_image)

rally_point_image = pyglet.resource.image("rally_point.png")
center_anchor(rally_point_image)

control_panel_image = pyglet.resource.image("control_panel.png")
right_bottom_anchor(control_panel_image)

control_panel_buttons_background_image = pyglet.resource.image("control_panel_buttons_background.png")
center_anchor(control_panel_buttons_background_image)

menu_image = pyglet.resource.image("menu.png")
center_anchor(menu_image)

selected_frame_image = pyglet.resource.image("selected_frame.png")
center_anchor(selected_frame_image)

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

big_base_icon_image = pyglet.resource.image("big_base_icon.png")
center_anchor(big_base_icon_image)

# Resources
mineral = pyglet.resource.image("mineral.png")
center_anchor(mineral)
mineral_shadow = pyglet.resource.image("mineral_shadow.png")
center_anchor(mineral_shadow)

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

big_base_image = pyglet.resource.image("big_base.png")
center_anchor(big_base_image)

# Units
centurion_image = pyglet.resource.image("centurion.png")
center_anchor(centurion_image)
centurion_shadow_image = pyglet.resource.image("centurion_shadow.png")
center_anchor(centurion_shadow_image)

vulture_image = pyglet.resource.image("vulture.png")
center_anchor(vulture_image)
vulture_shadow_image = pyglet.resource.image("vulture_shadow.png")
center_anchor(vulture_shadow_image)

defiler_image = pyglet.resource.image("defiler.png")
center_anchor(defiler_image)
defiler_shadow_image = pyglet.resource.image("defiler_shadow.png")
center_anchor(defiler_shadow_image)

pioneer_image = pyglet.resource.image("pioneer.png")
center_anchor(pioneer_image)
pioneer_shadow_image = pyglet.resource.image("pioneer_shadow.png")
center_anchor(pioneer_shadow_image)

apocalypse_image = pyglet.resource.image("apocalypse.png")
center_anchor(apocalypse_image)
apocalypse_shadow_image = pyglet.resource.image("apocalypse_shadow.png")
center_anchor(apocalypse_shadow_image)

# Other
projectile_image = pyglet.resource.image("laser.png")
center_anchor(projectile_image)
