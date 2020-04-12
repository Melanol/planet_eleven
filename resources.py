import os

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


subds = next(os.walk('./sprites'))[1]
allsubds = ['./sprites']
for subd in subds:
    next_subd = next(os.walk('./sprites/' + subd))[1]
    if next_subd:
        arr = []
        for d in next_subd:
            arr.append('sprites/' + subd + '/' + d)
        allsubds += arr
    else:
        allsubds += ['sprites/' + subd]
print("allsubds =", allsubds)
pyglet.resource.path = allsubds
pyglet.resource.reindex()

# Utilities
cursor = pyglet.window.ImageMouseCursor(pyglet.image.load(
    'sprites/cursor.png'), 0, 32)
cursor_target = pyglet.window.ImageMouseCursor(pyglet.image.load(
    'sprites/cursor_target.png'), 32, 32)

terrain_img = pyglet.resource.image("terrain.png")

none_img = center_load("none.png")

# Menu
menu_img = center_load("menu.png")
menu_bg = pyglet.resource.image("menu_bg.png")
resume_img = center_load("resume.png")
save_img = center_load("save.png")
load_img = center_load("load.png")
restart_img = center_load("restart.png")
options_img = center_load("options.png")
exit_img = center_load("exit.png")
fullscreen_img = center_load("fullscreen_img.png")
check_b = center_load("check_b.png")
check = center_load("check.png")
back_img = center_load("back.png")

sel_img = center_load("sel.png")
sel_big_img = center_load("sel_big.png")
rp_img = center_load("rp.png")
cp_img = right_bottom_load("cp.png")
cp_buttons_bg_img = center_load("cp_b_bg.png")
sel_frame_img = center_load("sel_frame.png")
mm_black_bg_img = pyglet.resource.image("mm_black_bg.png")
mm_textured_bg_img = pyglet.resource.image("mm_textured_bg.png")
utility_dot_img = center_load("utility_dot.png")
mm_cam_frame_img = pyglet.resource.image("mm_cam_frame.png")
mm_our_img = center_load("mm_our.png")
mm_enemy_img = center_load("mm_enemy.png")
mineral_small = center_load("mineral_small.png")

# Hints
hint_armory = right_bottom_load("hint_armory.png")
hint_turret = right_bottom_load("hint_turret.png")
hint_mech_center = right_bottom_load("hint_mech_center.png")

hint_defiler = right_bottom_load("hint_defiler.png")
hint_centurion = right_bottom_load("hint_centurion.png")
hint_wyrm = right_bottom_load("hint_wyrm.png")
hint_apocalypse = right_bottom_load("hint_apocalypse.png")
hint_pioneer = right_bottom_load("hint_pioneer.png")

# Controls
move_img = center_load("move.png")
stop_img = center_load("stop.png")
attack_img = center_load("attack.png")
mech_center_icon_img = center_load("mech_center_icon.png")

# Resources
mineral = center_load("mineral.png")

# Buildings
constr_dummy1 = center_load('constr_dummy32_1.png')
constr_dummy2 = center_load('constr_dummy32_2.png')
constr_dummy3 = center_load('constr_dummy32_3.png')
constr_dummy_anim = pyglet.image.Animation.from_image_sequence([constr_dummy1,
        constr_dummy2, constr_dummy3], 0.1, True)

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

mech_center_img = center_load("mech_center.png")
mech_center_enemy_img = center_load("mech_center_enemy.png")
anim_img1 = center_load('mech_center_anim1.png')
anim_img2 = center_load('mech_center_anim2.png')
anim_img3 = center_load('mech_center_anim3.png')
anim = pyglet.image.Animation.from_image_sequence([anim_img1, anim_img2,
                                                   anim_img3], 0.7, True)
anim_enemy_img1 = center_load('mech_center_anim_enemy1.png')
anim_enemy_img2 = center_load('mech_center_anim_enemy2.png')
anim_enemy_img3 = center_load('mech_center_anim_enemy3.png')
anim_enemy = pyglet.image.Animation.from_image_sequence([anim_enemy_img1,
    anim_enemy_img2, anim_enemy_img3], 0.7, True)

# Units
defiler_img = center_load("defiler.png")
defiler_team_color = center_load("defiler_team_color.png")
defiler_shadow_img = center_load("defiler_shadow.png")

centurion_img = center_load("centurion.png")
centurion_team_color = center_load("centurion_team_color.png")
centurion_shadow_img = center_load("centurion_shadow.png")

wyrm_img = center_load("wyrm.png")
wyrm_team_color = center_load("wyrm_team_color.png")
wyrm_shadow_img = center_load("wyrm_shadow.png")

pioneer_img = center_load("pioneer.png")
pioneer_team_color = center_load("pioneer_team_color.png")
pioneer_shadow_img = center_load("pioneer_shadow.png")

apocalypse_img = center_load("apocalypse.png")
apocalypse_team_color = center_load("apocalypse_team_color.png")
apocalypse_shadow_img = center_load("apocalypse_shadow.png")

# Other
laser_img = center_load("laser.png")

plasma1 = center_load('plasma16_1.png')
plasma2 = center_load('plasma16_2.png')
plasma3 = center_load('plasma16_3.png')
plasma_anim = pyglet.image.Animation.from_image_sequence([plasma1, plasma2,
                                                          plasma3], 0.1, True)

explosion1 = center_load('explosion1.png')
explosion2 = center_load('explosion2.png')
explosion3 = center_load('explosion3.png')
explosion4 = center_load('explosion4.png')
explosion5 = center_load('explosion5.png')
explosion_anim = pyglet.image.Animation.from_image_sequence([explosion1,
    explosion2, explosion3, explosion4, explosion5], 0.07, False)