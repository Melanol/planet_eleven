from pyglet.gl import *
from pyglet.image.atlas import TextureAtlas


class BorderedTextureAtlas(TextureAtlas):
    def add(self, img):
        x, y = self.allocator.alloc(img.width+2, img.height+2)
        self.texture.blit_into(img, x+1, y+1, 0)
        return self.texture.get_region(x+1, y+1, img.width, img.height)


pyglet.image.atlas.TextureAtlas = BorderedTextureAtlas


def center_load(_str):
    img = pyglet.resource.image(_str)
    img.anchor_x = img.width / 2
    img.anchor_y = img.height / 2
    glTexParameteri(img.target, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
    glTexParameteri(img.target, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
    return img


def right_bottom_load(_str):
    img = pyglet.resource.image(_str)
    img.anchor_x = img.width
    glTexParameteri(img.target, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
    glTexParameteri(img.target, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
    return img


def center_load_anim(_str):
    anim = pyglet.image.load_animation(_str)
    bin = pyglet.image.atlas.TextureBin()
    anim.add_to_texture_bin(bin)
    return anim


pyglet.resource.path = ['sprites', 'sprites/big_base', 'sprites/plasma_hit']
pyglet.resource.reindex()

# Utilities
cursor = pyglet.window.ImageMouseCursor(pyglet.image.load(
    'sprites/cursor.png'), 0, 16)
cursor_fullscreen = pyglet.window.ImageMouseCursor(pyglet.image.load(
    'sprites/cursor_fullscreen.png'), 0, 32)
move_cursor = pyglet.window.ImageMouseCursor(pyglet.image.load(
    'sprites/move_cursor.png'), 0, 16)

terrain_img = pyglet.resource.image("terrain.png")

sel_img = center_load("sel.png")
sel_big_img = center_load("sel_big.png")
rp_img = center_load("rp.png")
cp_img = right_bottom_load("cp.png")
cp_buttons_bg_img = center_load("cp_b_bg.png")
menu_img = center_load("menu.png")
sel_frame_img = center_load("sel_frame.png")
mm_black_bg_img = pyglet.resource.image("mm_black_bg.png")
mm_textured_bg_img = pyglet.resource.image("mm_textured_bg.png")
utility_dot_img = center_load("utility_dot.png")
mm_cam_frame_img = pyglet.resource.image("mm_cam_frame.png")
mm_our_img = center_load("mm_our.png")
mm_enemy_img = center_load("mm_enemy.png")

# Controls
move_img = center_load("move.png")
stop_img = center_load("stop.png")
attack_img = center_load("attack.png")
big_base_icon_img = center_load("big_base_icon.png")

# Resources
mineral = center_load("mineral.png")

# Buildings
armory_img = center_load("armory.png")
armory_enemy_img = center_load("armory_enemy.png")

turret_b_img = center_load("turret_b.png")
turret_img = center_load("turret.png")
turret_base_img = center_load("turret_base.png")
hit1 = center_load("plasma16_hit1.png")
hit2 = center_load("plasma16_hit2.png")
hit3 = center_load("plasma16_hit3.png")
hit_anim = pyglet.image.Animation.from_image_sequence([hit1, hit2, hit3], 0.1,
                                                      False)

big_base_img = center_load("big_base.png")
big_base_enemy_img = center_load("big_base_enemy.png")
anim_img1 = center_load('big_base_anim1.png')
anim_img2 = center_load('big_base_anim2.png')
anim_img3 = center_load('big_base_anim3.png')
anim = pyglet.image.Animation.from_image_sequence([anim_img1, anim_img2,
                                                   anim_img3], 0.7, True)
anim_enemy_img1 = center_load('big_base_anim_enemy1.png')
anim_enemy_img2 = center_load('big_base_anim_enemy2.png')
anim_enemy_img3 = center_load('big_base_anim_enemy3.png')
anim_enemy = pyglet.image.Animation.from_image_sequence([anim_enemy_img1,
                                                         anim_enemy_img2,
                                                         anim_enemy_img3], 0.7,
                                                        True)


# Units
defiler_img = center_load("defiler.png")
defiler_enemy_img = center_load("defiler_enemy.png")
defiler_shadow_img = center_load("defiler_shadow.png")

centurion_img = center_load("centurion.png")
centurion_enemy_img = center_load("centurion_enemy.png")
centurion_shadow_img = center_load("centurion_shadow.png")

vulture_img = center_load("vulture.png")
vulture_enemy_img = center_load("vulture_enemy.png")
vulture_shadow_img = center_load("vulture_shadow.png")

pioneer_img = center_load("pioneer.png")
pioneer_enemy_img = center_load("pioneer_enemy.png")
pioneer_shadow_img = center_load("pioneer_shadow.png")

apocalypse_img = center_load("apocalypse.png")
apocalypse_enemy_img = center_load("apocalypse_enemy.png")
apocalypse_shadow_img = center_load("apocalypse_shadow.png")

# Other
laser_img = center_load("laser.png")

plasma1 = center_load('plasma16_1.png')
plasma2 = center_load('plasma16_2.png')
plasma3 = center_load('plasma16_3.png')
plasma_anim = pyglet.image.Animation.from_image_sequence([plasma1, plasma2,
                                                          plasma3], 0.1, True)