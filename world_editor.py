import sys
import numpy as np
import win32api

from pyglet.gl import *
from pyglet.window import key
from pyglet.window import mouse
from pyglet.sprite import Sprite
from weapons import *
from constants_and_utilities import *
from shadowandunittc import ShadowAndUnitTC
from bb_enemy_detection import rad_clipped

lvb = 0
bvb = 0

POS_COORDS = []
g_pos_coord_d = {}
a_pos_coord_d = {}
def gen_pos_coords():
    """Generates a field of allowed positional coords. Declared as a function
    for resetting these."""
    global POS_COORDS, g_pos_coord_d, a_pos_coord_d
    POS_COORDS = []
    for yi in range(1, POS_COORDS_N_ROWS + 1):
        for xi in range(1, POS_COORDS_N_COLUMNS + 1):
            POS_COORDS.append((xi * PS - PS / 2,
                               yi * PS - PS / 2))
    g_pos_coord_d = {}
    for x, y in POS_COORDS:
        g_pos_coord_d[(x, y)] = None
    a_pos_coord_d = {}
    for x, y in POS_COORDS:
        a_pos_coord_d[(x, y)] = None
gen_pos_coords()

def to_minimap(x, y):  # unit.x and unit.y
    """Converts global coords into minimap coords. For positioning minimap
    pixels and camera."""
    x = x / PS
    if not x.is_integer():
        x += 1
    x = MM0X + x + lvb
    y = y / PS
    if not y.is_integer():
        y += 1
    y = MM0Y + y + bvb
    return x, y

def mc(**kwargs):
    """Modifies coords for different viewports. All clicks need this. Required for
    game field, minimap, control panel."""
    if len(kwargs) == 1:
        try:
            return kwargs['x'] + lvb
        except KeyError:
            return kwargs['y'] + bvb
    else:
        return kwargs['x'] + lvb, kwargs['y'] + bvb

class UI(Sprite):
    """This class is used for UI elements that need to be relocated when
    a player moves the viewport."""
    def __init__(self, game_inst, img, x, y, batch=None):
        super().__init__(img, x, y, batch=batch)
        self.org_x = x
        self.org_y = y
        game_inst.ui.append(self)

class CheckB(Sprite):
    """Check buttons."""
    def __init__(self, game_inst, x, y, checked=True):
        super().__init__(res.check_b, x, y, batch=options_batch)
        self.org_x = x
        self.org_y = y
        game_inst.ui.append(self)
        self.check = UI(game_inst, res.check, x, y, batch=check_batch)
        if not checked:
            self.check.visible = False

class Player:
    def __init__(self, name):
        self.min_c = 5000
        self.name = name

entities = []
class Entity(Sprite):
    def __init__(self, name, x, y, batch):
        entities.append(self)
        self.name = name
        super().__init__(res.mineral, x, y, batch=batch)

def build_structure(game_inst, struct, x, y):
    struct(game_inst, x, y, skip_constr=True)

class Struct(Sprite):
    """This is what I call buildings. __init__ == spawn()"""

    def __init__(self, game_inst, owner, img, team_color_img, icon, vision_rad,
                 hp, x, y, width):
        self.owner = owner
        self.team_color = Sprite(team_color_img, x, y,
                                 batch=ground_team_color_batch)
        self.team_color.visible = False
        self.icon = icon
        if width == 1:
            self.coords = ((x, y),)
        else:
            self.coords = ((x - PS/2, y + PS/2), (x + PS/2, y + PS/2),
                           (x - PS/2, y - PS/2), (x + PS/2, y - PS/2))
        if owner.name == "p1":
            self.team_color.color = OUR_TEAM_COLOR
            our_structs.append(self)
            minimap_pixel = res.mm_our_img
        else:
            self.team_color.color = ENEMY_TEAM_COLOR
            enemy_structs.append(self)
            minimap_pixel = res.mm_enemy_img
        super().__init__(img, x, y, batch=structures_batch)
        self.completed_image = img
        self.game_inst = game_inst
        self.max_hp = hp
        self.hp = hp
        if self.width / 32 % 2 == 1:
            d = self.width / PS // 2 * PS
            n = self.width // PS
            width = 1
        else:
            n = int(self.width / PS // 2)
            d = self.width / PS // 2 * PS - PS / 2
            width = 2
        # print('d =', d, 'n =', n, 'width =', width)
        x -= d
        y -= d
        self.blocks = [(x, y)]
        for _ in range(n):
            for _ in range(width):
                self.blocks.append((x, y))
                g_pos_coord_d[(x, y)] = self
                x += PS
            x -= PS
            for _ in range(width - 1):
                y += PS
                self.blocks.append((x, y))
                g_pos_coord_d[(x, y)] = self
            for _ in range(width - 1):
                x -= PS
                self.blocks.append((x, y))
                g_pos_coord_d[(x, y)] = self
            for _ in range(width - 2):
                self.blocks.append((x, y))
                g_pos_coord_d[(x, y)] = self
                y -= PS
            width += 2
        self.default_rp = True
        self.attackers = []

        pixel_minimap_coords = to_minimap(self.x, self.y)
        self.pixel = Sprite(img=minimap_pixel,
                            x=pixel_minimap_coords[0],
                            y=pixel_minimap_coords[1],
                            batch=minimap_pixels_batch)

    def kill(self, delay_del=False):
        global our_structs, enemy_structs
        for block in self.blocks:
            g_pos_coord_d[(block[0], block[1])] = None
        self.team_color.delete()
        self.pixel.delete()
        if not delay_del:
            for arr in (our_structs, enemy_structs, prod_structs):
                try:
                    arr.remove(self)
                except ValueError:
                    pass
        for attacker in self.attackers:
            attacker.has_target_p = False
        try:
            self.anim.delete()
        except AttributeError:
            pass
        Explosion(self.x, self.y, self.width / PS / 2)
        self.delete()

    def constr_complete(self):
        self.under_constr = False
        self.image = self.completed_image
        self.team_color.visible = True


class ProductionStruct:
    def ps_init(self):
        prod_structs.append(self)
        self.rp_x = self.x
        self.rp_y = self.y
        self.prod_q = []
        self.cur_max_prod_time = None
        self.prod_complete = True
        self.prod_start_f = 0


class GuardianStructure:
    def gs_init(self, skip_constr):
        if not skip_constr:
            guardian_dummies.append(self)
            self.image = res.constr_dummy_anim
            self.constr_f = self.game_inst.f
            self.under_constr = True
        else:
            self.constr_complete()


class Armory(Struct, GuardianStructure):
    cost = 200
    build_time = 600

    def __init__(self, game_inst, x, y, owner=None, skip_constr=False):
        if owner is None:
            owner = game_inst.this_player
        super().__init__(game_inst, owner, res.armory_img,
                         res.armory_team_color, res.armory_icon_img,
                         vision_rad=2,  hp=100, x=x, y=y, width=1)
        super().gs_init(skip_constr)
        self.cbs = None


class MechCenter(Struct, ProductionStruct, GuardianStructure):
    cost = 500
    build_time = 1000

    def __init__(self, game_inst, x, y, owner=None, skip_constr=False):
        if owner is None:
            owner = game_inst.this_player
        super().__init__(game_inst, owner, res.mech_center_img,
                         res.mech_center_team_color, res.mech_center_icon_img,
                         x=x, y=y, hp=1500, vision_rad=4, width=2)
        super().ps_init()
        super().gs_init(skip_constr)
        self.cbs = [game_inst.defiler_b, game_inst.centurion_b,
                    game_inst.wyrm_b, game_inst.apocalypse_b,
                    game_inst.pioneer_b, game_inst.cancel_b]
        self.is_big = True
        if owner.name == 'p1':
            self.anim = Sprite(img=res.anim, x=x, y=y, batch=ground_units_batch)
        else:
            self.anim = Sprite(img=res.anim_enemy, x=x, y=y,
                               batch=ground_units_batch)
        self.anim.visible = False


class OffensiveStruct(Struct):
    def __init__(self, game_inst, owner, img, team_color, icon, vision_rad, hp,
                 x, y, damage, cooldown, width):
        super().__init__(game_inst, owner, img, team_color, icon, vision_rad,
                         hp, x, y, width)
        self.damage = damage
        self.attack_rad = vision_rad
        self.target_x = None
        self.target_y = None
        self.cooldown = cooldown
        self.on_cooldown = False
        self.cooldown_started = None
        offensive_structs.append(self)
        self.projectile_sprite = res.laser_img
        self.projectile_speed = 5
        self.has_target_p = False
        self.target_p = None
        self.target_p_x = None
        self.target_p_y = None
        self.attacks_ground = True
        self.attacks_air = True

    def shoot(self, f):
        global projectiles
        projectile = Projectile(self.x, self.y, self.target_p.x,
                                self.target_p.y, self.damage,
                                self.projectile_speed, self.target_p,
                                res.plasma_anim)
        x_diff = self.target_p.x - self.x
        y_diff = self.target_p.y - self.y
        self.on_cooldown = True
        self.cooldown_started = f
        projectiles.append(projectile)

    def kill(self, delay_del=False):
        global g_pos_coord_d, our_structs, enemy_structs
        g_pos_coord_d[(self.x, self.y)] = None
        self.pixel.delete()
        for attacker in self.attackers:
            attacker.has_target_p = False
        if not delay_del:
            if self.owner.name == 'p1':
                del our_structs[our_structs.index(self)]
            else:
                del enemy_structs[enemy_structs.index(self)]
        del offensive_structs[offensive_structs.index(self)]
        self.plasma_spt.delete()
        self.team_color.delete()
        Explosion(self.x, self.y, self.width / PS / 2)
        self.delete()


class Turret(OffensiveStruct, GuardianStructure):
    cost = 150
    build_time = 1200

    def __init__(self, game_inst, x, y, owner=None, skip_constr=False):
        if owner is None:
            owner = game_inst.this_player
        super().__init__(game_inst, owner, res.turret_img,
                         res.turret_team_color, res.turret_icon_img,
                         vision_rad=5,
                         hp=100, x=x, y=y, damage=20, cooldown=60, width=1)
        super().gs_init(skip_constr)
        self.cbs = None

    def constr_complete(self):
        self.under_constr = False
        self.image = self.completed_image
        self.team_color.visible = True

        self.plasma_spt = Sprite(res.plasma_anim, self.x, self.y,
                                 batch=ground_units_batch)


class WorldEditor(pyglet.window.Window):
    def __init__(self, width, height, title):
        global sel
        sel = None
        conf = Config(sample_buffers=1, samples=4, depth_size=16,
                      double_buffer=True)
        super().__init__(width, height, title, config=conf)
        self.set_mouse_cursor(res.cursor)
        self.ui = []
        self.this_player = Player("p1")
        self.computer = Player("c1")
        self.mouse_x = 0
        self.mouse_y = 0
        self.show_hint = False
        self.menu_bg = UI(self, res.menu_bg, 0, 0)
        self.options = False
        self.f = 0
        self.dx = 0
        self.dy = 0
        self.minimap_drugging = False
        self.build_loc_sel_phase = False
        self.m_targeting_phase = False
        self.targeting_phase = False

        self.terrain = Sprite(img=res.terrain_img, x=0, y=0)
        self.cp_spt = UI(self, res.cp_img, SCREEN_W, 0)
        self.menu_b = UI(self, res.menu_img, cp_c_x, SCREEN_H - 30)
        self.sel_frame_cp = UI(self, res.sel_frame_img, cp_c_x, SCREEN_H - 90)
        self.cp_b_bg = UI(self, res.cp_buttons_bg_img, cp_c_x, cp_c_y)
        self.mm_textured_bg = UI(self, res.mm_textured_bg_img, MM0X, MM0Y)
        self.mm_cam_frame_spt = Sprite(res.mm_cam_frame_img, MM0X - 1,
                                       MM0Y - 1)
        self.sel_icon = UI(self, res.none_img, CB_COORDS[0][0],
                                SCREEN_H - 72)
        self.sel_hp = pyglet.text.Label('', x=CB_COORDS[1][0] - 15,
                                             y=SCREEN_H - 72, anchor_y='center',
                                             font_size=8,
                                             color=(0, 0, 0,255))
        self.txt_out = pyglet.text.Label('', x=SCREEN_W / 2 - 50, y=100,
                anchor_x='center', anchor_y='center', font_size=8)
        self.txt_out_upd_f = None

        # Hints
        self.hint = UI(self, res.hint_defiler, 100, 100)

        # Menu
        self.options_b = UI(self, res.options_img, SCREEN_W / 2, 220,
                            batch=menu_b_batch)
        self.exit_b = UI(self, res.exit_img, SCREEN_W / 2, 200,
                         batch=menu_b_batch)
        self.fullscreen_img = UI(self, res.fullscreen_img, SCREEN_W / 2, 200,
                         batch=options_batch)
        self.fullscreen_c = CheckB(self, SCREEN_W / 2 + 70, 200, False)
        self.back_b = UI(self, res.back_img, SCREEN_W / 2, 180,
                         batch=options_batch)

        # Control panel buttons
        self.armory_icon = UI(self, res.armory_icon_img, CB_COORDS[3][0],
                              CB_COORDS[3][1])
        self.turret_icon = UI(self, res.turret_icon_img, CB_COORDS[4][0],
                              CB_COORDS[4][1])
        self.mech_center_icon = UI(self, res.mech_center_icon_img,
                                   CB_COORDS[5][0], CB_COORDS[5][1])
        self.defiler_b = UI(self, res.defiler_img, CB_COORDS[0][0],
                            CB_COORDS[0][1])
        self.centurion_b = UI(self, res.centurion_img,
                              CB_COORDS[1][0], CB_COORDS[1][1])
        self.wyrm_b = UI(self, res.wyrm_img, CB_COORDS[2][0],
                         CB_COORDS[2][1])
        self.apocalypse_b = UI(self, res.apocalypse_img,
                               CB_COORDS[3][0], CB_COORDS[3][1])
        self.pioneer_b = UI(self, res.pioneer_img, CB_COORDS[4][0],
                            CB_COORDS[4][1])
        self.cbs_2_render = [self.armory_icon, self.turret_icon]
        self.to_build_spt = Sprite(img=res.armory_img, x=-100, y=-100)
        self.to_build_spt.color = (0, 255, 0)

    def on_draw(self):
        """
        Render the screen.
        """
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
        glOrtho(lvb, lvb + SCREEN_W, bvb, bvb + SCREEN_H, 1, -1)

        self.terrain.draw()
        ground_shadows_batch.draw()
        structures_batch.draw()
        ground_units_batch.draw()
        ground_team_color_batch.draw()
        weapons_batch.draw()
        air_shadows_batch.draw()
        air_batch.draw()
        air_team_color_batch.draw()
        if sel:
            try:
                sel.is_big
                self.sel_big_spt.draw()
            except AttributeError:
                self.sel_spt.draw()

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        utilities_batch.draw()
        if self.build_loc_sel_phase:
            self.to_build_spt.draw()
        self.cp_spt.draw()
        self.menu_b.draw()
        self.sel_frame_cp.draw()
        self.sel_icon.draw()
        self.sel_hp.draw()
        self.cp_b_bg.draw()
        self.mm_textured_bg.draw()
        minimap_pixels_batch.draw()

        if self.cbs_2_render:
            for button in self.cbs_2_render:
                button.draw()
            if sel in our_structs and sel \
                    not in offensive_structs:
                self.rp_spt.draw()

        self.mm_cam_frame_spt.draw()
        if self.show_hint:
            self.hint.draw()
        self.txt_out.draw()

        # Remove default modelview matrix
        glPopMatrix()

    def update(self, delta_time):
        pass

    def on_key_press(self, symbol, modifiers):
        """Called whenever a key is pressed."""
        global sel, lvb, bvb
        if symbol is key.F:
            if self.fullscreen:
                self.set_fullscreen(False)
            else:
                self.set_fullscreen(True)
        elif symbol is key.H:
            print(structures_batch._draw_list)

    def on_mouse_press(self, x, y, button, modifiers):
        """Don't play with mc(), globals"""
        global sel, lvb, bvb
        if self.fullscreen:
            x //= 2
            y //= 2
        # Building location selection
        if self.build_loc_sel_phase:
            # Game field
            x, y = mc(x=x, y=y)
            if x < mc(x=SCREEN_W) - 139:
                x, y = round_coords(x, y)
                if button == mouse.LEFT:
                    if self.loc_clear:
                        build_structure(self, self.to_build, x, y)
                        self.build_loc_sel_phase = False
                elif button == mouse.RIGHT:
                    self.build_loc_sel_phase = False
        # Normal phase
        else:
            # Game field
            if x < SCREEN_W - 139:
                x, y = round_coords(x, y)
                x, y = mc(x=x, y=y)
                if button == mouse.LEFT:
                    # Selection
                    if not bin(modifiers)[-1] == '1':  # Shift is pressed
                        to_be_sel = a_pos_coord_d[(x, y)]
                        if to_be_sel:  # Air unit found
                            sel = to_be_sel
                            self.sel_spt.x = x
                            self.sel_spt.y = y
                        else:
                            to_be_sel = g_pos_coord_d[(x, y)]
                            if to_be_sel:
                                try:
                                    to_be_sel.is_big
                                    self.sel_big_spt.x = to_be_sel.x
                                    self.sel_big_spt.y = to_be_sel.y
                                except AttributeError:
                                    self.sel_spt.x = x
                                    self.sel_spt.y = y
                                sel = to_be_sel
                    else:
                        to_be_sel = g_pos_coord_d[(x, y)]
                        if to_be_sel:
                            try:
                                to_be_sel.is_big
                                self.sel_big_spt.x = to_be_sel.x
                                self.sel_big_spt.y = to_be_sel.y
                            except AttributeError:
                                self.sel_spt.x = x
                                self.sel_spt.y = y
                            sel = to_be_sel
                    if sel:
                        self.sel_icon.image = sel.icon
                        try:
                            self.sel_hp.text = str(int(sel.hp)) \
                                + '/' + str(sel.max_hp)
                        except AttributeError:
                            self.sel_hp.text = str(int(sel.hp))
                    # Control buttons
                    try:
                        if sel.owner.name == 'p1':
                            try:
                                if not sel.under_constr:
                                    self.cbs_2_render = sel.cbs
                                else:
                                    self.cbs_2_render = None
                            except AttributeError:
                                self.cbs_2_render = sel.cbs
                        else:
                            self.cbs_2_render = None
                    except AttributeError:  # For minerals
                        self.cbs_2_render = None
                    try:
                        self.rp_spt.x = sel.rp_x
                        self.rp_spt.y = sel.rp_y
                    except AttributeError:
                        pass
                elif button == mouse.RIGHT:
                    pass
            # Minimap
            elif MM0X <= x <= MM0X + 100 and MM0Y <= y <= MM0Y + 100:
                if button == mouse.LEFT:
                    # The viewport is 17x12 blocks. This +2 is
                    # about 2 border pixels of the frame
                    x -= 19 // 2
                    y -= 14 // 2
                    # print('x =', x, 'y =', y)
                    lvb = (x - MM0X) * PS
                    bvb = (y - MM0Y) * PS
                    self.update_viewport()
                elif button == mouse.RIGHT:
                    pass
            # Control panel other
            else:
                x, y = mc(x=x, y=y)
                w = self.menu_b.width
                h = self.menu_b.height
                if self.menu_b.x - w // 2 <= x <= \
                        self.menu_b.x + w // 2 and \
                        self.menu_b.y - h // 2 <= y <= \
                        self.menu_b.y + h // 2:
                    return
                # Build units
                if sel in our_structs and not sel.under_constr:
                    # Create defiler
                    if self.defiler_b.x - 16 <= x <= \
                            self.defiler_b.x + 16 and \
                            self.defiler_b.y - 16 <= y <= \
                            self.defiler_b.y + 16:
                        order_unit(self, sel, Defiler)
                    # Create centurion
                    elif self.centurion_b.x - 16 <= x <= \
                            self.centurion_b.x + 16 and \
                            self.centurion_b.y - 16 <= y <= \
                            self.centurion_b.y + 16:
                        order_unit(self, sel, Centurion)
                    # Create wyrm
                    elif self.wyrm_b.x - 16 <= x <= \
                            self.wyrm_b.x + 16 and \
                            self.wyrm_b.y - 16 <= y <= \
                            self.wyrm_b.y + 16:
                        order_unit(self, sel, Wyrm)
                    # Create apocalypse
                    elif self.apocalypse_b.x - 16 <= x <= \
                            self.apocalypse_b.x + 16 and \
                            self.apocalypse_b.y - 16 <= y <= \
                            self.apocalypse_b.y + 16:
                        order_unit(self, sel, Apocalypse)
                    # Create pioneer
                    elif self.pioneer_b.x - 16 <= x <= \
                            self.pioneer_b.x + 16 and \
                            self.pioneer_b.y - 16 <= y <= \
                            self.pioneer_b.y + 16:
                        order_unit(self, sel, Pioneer)
                    # Cancel last order
                    elif self.cancel_b.x - 16 <= x <= \
                            self.cancel_b.x + 16 and \
                            self.cancel_b.y - 16 <= y <= \
                            self.cancel_b.y + 16:
                        self.cancel_prod()
                else:
                    # Construct structures
                    if self.armory_icon.x - 16 <= x <= \
                            self.armory_icon.x + 16 and \
                            self.armory_icon.y - 16 <= y <= \
                            self.armory_icon.y + 16:
                        self.to_build_spt.image = res.armory_img
                        self.to_build_spt.color = (0, 255, 0)
                        self.build_loc_sel_phase = True
                        self.to_build = Armory
                        self.to_build_spt.x, self.to_build_spt.y = x, y
                    elif self.turret_icon.x - 16 <= x <= \
                            self.turret_icon.x + 16 and \
                            self.turret_icon.y - 16 <= y <= \
                            self.turret_icon.y + 16:
                        self.to_build_spt.image = res.turret_icon_img
                        self.to_build_spt.color = (0, 255, 0)
                        self.build_loc_sel_phase = True
                        self.to_build = Turret
                        self.to_build_spt.x, self.to_build_spt.y = x, y
                    elif self.mech_center_icon.x - 16 <= x <= \
                            self.mech_center_icon.x + 16 and \
                            self.mech_center_icon.y - 16 <= y <= \
                            self.mech_center_icon.y + 16:
                        self.to_build_spt.image = res.mech_center_img
                        self.to_build_spt.color = (0, 255, 0)
                        self.build_loc_sel_phase = True
                        self.to_build = MechCenter
                        self.to_build_spt.x, self.to_build_spt.y = x, y

    def on_mouse_motion(self, x, y, dx, dy):
        if self.fullscreen:
            x /= 2
            y /= 2
        if self.build_loc_sel_phase:
            self.mouse_x = x
            self.mouse_y = y
            if self.to_build == "MechCenter":
                x, y = round_coords(x, y)
                self.to_build_spt.x = x + lvb + PS / 2
                self.to_build_spt.y = y + bvb + PS / 2
                x, y = mc(x=x, y=y)
                s_x = int((x - 16) / 32) + 1
                s_y = int((y - 16) / 32) + 1
                s_coords_to_check = [(s_x, s_y), (s_x + 1, s_y),
                                     (s_x + 1, s_y + 1), (s_x, s_y + 1)]
                no_place = False
                for c in s_coords_to_check:
                    if self.npa[c[1], c[0], 3] != 0:
                        no_place = True
                        break
                if no_place is False:
                    coords_to_check = [(x, y), (x + PS, y),
                                       (x + PS, y + PS), (x, y + PS)]
                    for c in coords_to_check:
                        if g_pos_coord_d[c[0], c[1]]:
                            no_place = True
                            break
                if no_place:
                    self.to_build_spt.color = (255, 0, 0)
                    self.loc_clear = False
                else:
                    self.loc_clear = True
                    self.to_build_spt.color = (0, 255, 0)
            # Other buildings
            else:
                x, y = round_coords(x, y)
                self.to_build_spt.x = x + lvb
                self.to_build_spt.y = y + bvb
                x, y = mc(x=x, y=y)
                x = int((x - 16) / 32) + 1
                y = int((y - 16) / 32) + 1
                if g_pos_coord_d[self.to_build_spt.x, self.to_build_spt.y]:
                    self.to_build_spt.color = (255, 0, 0)
                    self.loc_clear = False
                else:
                    self.to_build_spt.color = (0, 255, 0)
                    self.loc_clear = True

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        global lvb, bvb
        if self.fullscreen:
            x /= 2
            y /= 2
            # dx /= 2
            # dy /= 2
        if not self.minimap_drugging:
            # Game field + MMB
            if x < SCREEN_W - 139 and buttons == 2:
                self.dx += dx * MMB_PAN_SPEED
                self.dy += dy * MMB_PAN_SPEED
                if abs(self.dx) >= PS:
                    if self.dx < 0:
                        lvb += PS
                        self.update_viewport()
                        self.dx -= self.dx
                    else:
                        lvb -= PS
                        self.update_viewport()
                        self.dx -= self.dx
                if abs(self.dy) >= PS:
                    if self.dy < 0:
                        bvb += PS
                        self.update_viewport()
                        self.dy -= self.dy
                    else:
                        bvb -= PS
                        self.update_viewport()
                        self.dy -= self.dy
            # Minimap + LMB or RMB
            elif MM0X <= x <= MM0X + 100 and MM0Y <= y <= MM0Y + 100 \
                    and buttons == 1:
                self.minimap_drugging = True
        # Minimap dragging
        else:
            # dx /= 2
            # dy /= 2
            lvb += dx * PS
            bvb += dy * PS
            self.update_viewport()

    def on_mouse_release(self, x, y, button, modifiers):
        self.minimap_drugging = False

    def update_viewport(self):
        global lvb, bvb, minimap_fow_x, minimap_fow_y
        # Viewport limits
        cp_limit = POS_COORDS_N_COLUMNS * PS - SCREEN_W // PS * PS + PS * 4
        if lvb % PS != 0:
            lvb += PS // 2
        if bvb % PS != 0:
            bvb += PS // 2
        if lvb < 0:
            lvb = 0
        elif lvb > cp_limit:
            lvb = cp_limit
        if bvb < 0:
            bvb = 0
        elif bvb > POS_COORDS_N_ROWS * PS - SCREEN_H:
            bvb = POS_COORDS_N_ROWS * PS - SCREEN_H

        self.mm_textured_bg.x = MM0X + lvb
        self.mm_textured_bg.y = MM0Y + bvb
        for el in self.ui:
            el.x = el.org_x + lvb
            el.y = el.org_y + bvb
        self.sel_hp.x = CB_COORDS[1][0] - 15 + lvb
        self.sel_hp.y = SCREEN_H - 72 + bvb
        self.txt_out.x = SCREEN_W / 2 - 50 + lvb
        self.txt_out.y = 100 + bvb
        for entity in our_structs + our_units \
                      + enemy_structs + enemy_units:
            entity.pixel.x, entity.pixel.y = to_minimap(entity.x, entity.y)
        self.mm_cam_frame_spt.x, self.mm_cam_frame_spt.y = to_minimap(lvb, bvb)
        self.mm_cam_frame_spt.x -= 1
        self.mm_cam_frame_spt.y -= 1
        minimap_fow_x = MM0X - 1 + lvb
        minimap_fow_y = MM0Y - 1 + bvb


    def hotkey_constr_cur_1b(self):
        self.build_loc_sel_phase = True
        x, y = win32api.GetCursorPos()
        x, y = x / 2, y / 2
        y = SCREEN_H - y
        x, y = mc(x=x, y=y)
        x, y = round_coords(x, y)
        self.to_build_spt.x, self.to_build_spt.y = x, y
        s_x = int((x - 16) / 32) + 1
        s_y = int((y - 16) / 32) + 1
        if g_pos_coord_d[self.to_build_spt.x, self.to_build_spt.y] \
                or self.npa[s_y, s_x, 3] != 0:
            self.to_build_spt.color = (255, 0, 0)
            self.loc_clear = False
        else:
            self.to_build_spt.color = (0, 255, 0)
            self.loc_clear = True


def main():
    game_window = WorldEditor(SCREEN_W, SCREEN_H, SCREEN_TITLE)
    pyglet.clock.schedule_interval(game_window.update, 1 / 60)
    pyglet.app.run()


if __name__ == "__main__":
    main()
