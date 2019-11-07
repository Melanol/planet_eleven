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
cursor = pyglet.window.ImageMouseCursor(pyglet.image.load(
    'sprites/cursor.png'), 0, 16)
cursor_fullscreen = pyglet.window.ImageMouseCursor(pyglet.image.load(
    'sprites/cursor_fullscreen.png'), 0, 32)
move_cursor = pyglet.window.ImageMouseCursor(pyglet.image.load(
    'sprites/move_cursor.png'), 0, 16)

terrain_img = pyglet.resource.image("terrain.png")

sel_img = pyglet.resource.image("sel.png")
center_anchor(sel_img)

sel_big_img = pyglet.resource.image("sel_big.png")
center_anchor(sel_big_img)

rp_img = pyglet.resource.image("rp.png")
center_anchor(rp_img)

cp_img = pyglet.resource.image("cp.png")
right_bottom_anchor(cp_img)

cp_buttons_bg_img = pyglet.resource.image(
    "cp_b_bg.png")
center_anchor(cp_buttons_bg_img)

menu_img = pyglet.resource.image("menu.png")
center_anchor(menu_img)

sel_frame_img = pyglet.resource.image("sel_frame.png")
center_anchor(sel_frame_img)

mm_black_bg_img = pyglet.resource.image(
    "mm_black_bg.png")

mm_textured_bg_img = pyglet.resource.image(
    "mm_textured_bg.png")

utility_dot_img = pyglet.resource.image("utility_dot.png")
center_anchor(utility_dot_img)

mm_cam_frame_img = pyglet.resource.image("mm_cam_frame.png")

mm_our_img = pyglet.resource.image("mm_our.png")
center_anchor(mm_our_img)

mm_enemy_img = pyglet.resource.image("mm_enemy.png")
center_anchor(mm_enemy_img)

# Controls
move_img = pyglet.resource.image("move.png")
center_anchor(move_img)

stop_img = pyglet.resource.image("stop.png")
center_anchor(stop_img)

attack_img = pyglet.resource.image("attack.png")
center_anchor(attack_img)

big_base_icon_img = pyglet.resource.image("big_base_icon.png")
center_anchor(big_base_icon_img)

# Resources
mineral = pyglet.resource.image("mineral.png")
center_anchor(mineral)

# Buildings
armory_img = pyglet.resource.image("armory.png")
center_anchor(armory_img)
armory_enemy_img = pyglet.resource.image("armory_enemy.png")
center_anchor(armory_enemy_img)

turret_b_img = pyglet.resource.image("turret_b.png")
center_anchor(turret_b_img)
turret_img = pyglet.resource.image("turret.png")
center_anchor(turret_img)
turret_base_img = pyglet.resource.image("turret_base.png")
center_anchor(turret_base_img)

big_base_img = pyglet.resource.image("big_base.png")
center_anchor(big_base_img)
big_base_enemy_img = pyglet.resource.image("big_base_enemy.png")
center_anchor(big_base_enemy_img)

# Units
defiler_img = pyglet.resource.image("defiler.png")
center_anchor(defiler_img)
defiler_enemy_img = pyglet.resource.image("defiler_enemy.png")
center_anchor(defiler_enemy_img)
defiler_shadow_img = pyglet.resource.image("defiler_shadow.png")
center_anchor(defiler_shadow_img)

centurion_img = pyglet.resource.image("centurion.png")
center_anchor(centurion_img)
centurion_enemy_img = pyglet.resource.image("centurion_enemy.png")
center_anchor(centurion_enemy_img)
centurion_shadow_img = pyglet.resource.image("centurion_shadow.png")
center_anchor(centurion_shadow_img)

vulture_img = pyglet.resource.image("vulture.png")
center_anchor(vulture_img)
vulture_enemy_img = pyglet.resource.image("vulture_enemy.png")
center_anchor(vulture_enemy_img)
vulture_shadow_img = pyglet.resource.image("vulture_shadow.png")
center_anchor(vulture_shadow_img)

pioneer_img = pyglet.resource.image("pioneer.png")
center_anchor(pioneer_img)
pioneer_enemy_img = pyglet.resource.image("pioneer_enemy.png")
center_anchor(pioneer_enemy_img)
pioneer_shadow_img = pyglet.resource.image("pioneer_shadow.png")
center_anchor(pioneer_shadow_img)

apocalypse_img = pyglet.resource.image("apocalypse.png")
center_anchor(apocalypse_img)
apocalypse_enemy_img = pyglet.resource.image("apocalypse_enemy.png")
center_anchor(apocalypse_enemy_img)
apocalypse_shadow_img = pyglet.resource.image("apocalypse_shadow.png")
center_anchor(apocalypse_shadow_img)

# Other
laser_img = pyglet.resource.image("laser.png")
center_anchor(laser_img)

plasma1 = pyglet.image.load('sprites/plasma16_1.png')
plasma1.anchor_x = 8; plasma1.anchor_y = 8
plasma2 = pyglet.image.load('sprites/plasma16_2.png')
plasma2.anchor_x = 8; plasma2.anchor_y = 8
plasma3 = pyglet.image.load('sprites/plasma16_3.png')
plasma3.anchor_x = 8; plasma3.anchor_y = 8
plasma_spts = [plasma1, plasma2, plasma3]
plasma_anim = pyglet.image.Animation.from_image_sequence(plasma_spts, 0.1,
                                                         True)