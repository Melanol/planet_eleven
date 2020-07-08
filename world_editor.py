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


class WorldEditor(pyglet.window.Window):
    def __init__(self, width, height, title):
        global sel
        sel = None
        conf = Config(sample_buffers=1, samples=4, depth_size=16,
                      double_buffer=True)
        super().__init__(width, height, title, config=conf)
        self.set_mouse_cursor(res.cursor)
        self.ui = []
        self.mouse_x = 0
        self.mouse_y = 0
        self.show_hint = False
        self.menu_bg = UI(self, res.menu_bg, 0, 0)
        self.options = False
        self.cbs_2_render = None
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
        if not self.paused:
            if symbol is key.F1:
                if not self.show_fps:
                    self.show_fps = True
                else:
                    self.show_fps = False
            elif symbol is key.F2:
                self.save()
            elif symbol is key.F3:
                self.load()
            elif symbol is key.F4:
                # Removes FOW
                self.npa[:, :, 3] = 0
                self.mm_fow_ImageData.set_data('RGBA',
                    self.mm_fow_ImageData.width * 4, data=self.npa.tobytes())
            elif symbol is key.F5:
                self.this_player.min_c = 99999
                self.update_min_c_label()
            elif symbol is key.F6:
                self.this_player.min_c = 0
                self.update_min_c_label()
            elif symbol is key.F7:
                print('type(sel) =', type(sel))
            elif symbol is key.DELETE:
                # Kill entity
                if sel in our_units:
                    sel.kill()
                    if sel.flying:
                        a_pos_coord_d[(self.sel_spt.x, self.sel_spt.y)] = None
                    else:
                        g_pos_coord_d[(self.sel_spt.x, self.sel_spt.y)] = None
                    sel = None
                elif sel in our_structs:
                    sel.kill()
                    sel = None
            elif symbol is key.ESCAPE:
                # Cancel command
                self.build_loc_sel_phase = False
                self.targeting_phase = False
                self.m_targeting_phase = False
                self.set_mouse_cursor(res.cursor)
            elif symbol is key.LEFT:
                lvb -= PS
                self.update_viewport()
            elif symbol is key.RIGHT:
                lvb += PS
                self.update_viewport()
            elif symbol is key.DOWN:
                bvb -= PS
                self.update_viewport()
            elif symbol is key.UP:
                bvb += PS
                self.update_viewport()
            elif symbol is key.Q:
                # Move
                if sel in our_units and sel.owner.name == "p1":
                    self.set_mouse_cursor(res.cursor_target)
                    self.m_targeting_phase = True
                    return
                # Build defiler
                elif isinstance(sel, MechCenter):
                    order_unit(self, sel, Defiler)
            elif symbol is key.W:
                # Stop
                if sel in our_units:
                    sel.stop()
                # Build centurion
                elif isinstance(sel, MechCenter):
                    order_unit(self, sel, Centurion)
            elif symbol is key.E:
                # Attack move
                if sel in our_units:
                    try:
                        if sel.weapon_type != 'none':
                            if sel.owner.name == 'p1':
                                self.set_mouse_cursor(res.cursor_target)
                            self.targeting_phase = True
                    except AttributeError:
                        pass
                # Build wyrm
                elif isinstance(sel, MechCenter):
                    order_unit(self, sel, Wyrm)
            elif symbol is key.A:
                # Build armory
                if isinstance(sel, Pioneer):
                    self.to_build_spt.image = res.armory_img
                    self.to_build = Armory
                    self.hotkey_constr_cur_1b()
                # Build apocalypse
                elif isinstance(sel, MechCenter):
                    order_unit(self, sel, Apocalypse)
            elif symbol is key.S:
                # Build turret
                if isinstance(sel, Pioneer):
                    self.to_build_spt.image = res.turret_icon_img
                    self.to_build = Turret
                    self.hotkey_constr_cur_1b()
                # Build pioneer
                elif isinstance(sel, MechCenter):
                    order_unit(self, sel, Pioneer)
            elif symbol is key.D:
                # Build mech center
                if isinstance(sel, Pioneer):
                    self.to_build_spt.image = res.mech_center_img
                    self.build_loc_sel_phase = True
                    self.to_build = MechCenter
                    x, y = win32api.GetCursorPos()
                    x, y = x / 2, y / 2
                    y = SCREEN_H - y
                    x, y = mc(x=x, y=y)
                    x, y = round_coords(x, y)
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
                    x += PS / 2
                    y += PS / 2
                    self.to_build_spt.x, self.to_build_spt.y = x, y
            elif symbol is key.C:
                self.cancel_prod()
            elif symbol is key.X:
                # Deletes all our units on the screen
                coords_to_delete = []
                yi = bvb + PS // 2
                for y in range(yi, yi + 12 * PS, PS):
                    xi = lvb + PS // 2
                    for x in range(xi, xi + 17 * PS, PS):
                        coords_to_delete.append((x, y))
                for coord in coords_to_delete:
                    for unit in our_units:
                        if g_pos_coord_d[coord[0], coord[1]] is unit:
                            unit.kill()
            elif symbol is key.Z:
                # Fills the entire map with wyrms
                i = 0
                for _key, value in g_pos_coord_d.items():
                    if i % 1 == 0:
                        if value is None:
                            unit = Wyrm(self, _key[0], _key[1])
                            unit.spawn()
                    i += 1
            elif symbol is key.V:
                pass
                # print(lvb, bvb)
                # print(lvb % 32 == 0, bvb % 32 == 0)
        # Menu
        else:
            if symbol is key.ESCAPE:
                self.paused = False

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
                        order_structure(self, sel, self.to_build, x, y)
                        self.build_loc_sel_phase = False
                elif button == mouse.RIGHT:
                    self.build_loc_sel_phase = False
        # Movement target selection phase
        elif self.m_targeting_phase:
            if button == mouse.LEFT:
                x, y = mc(x=x, y=y)
                # Game field
                if x < mc(x=SCREEN_W) - 139:
                    pass
                # Minimap
                elif MM0X <= x <= MM0X + 100 and MM0Y <= y <= MM0Y + 100:
                    x = (x - MM0X) * PS
                    y = (y - MM0Y) * PS
                else:
                    return
                x, y = round_coords(x, y)
                if sel.dest_reached:
                    sel.move((x, y))
                # Movement interruption
                else:
                    sel.move_interd = True
                    sel.new_dest_x = x
                    sel.new_dest_y = y
                sel.has_target_p = False
                self.m_targeting_phase = False
                self.set_mouse_cursor(res.cursor)
            else:
                self.m_targeting_phase = False
                self.set_mouse_cursor(res.cursor)
        # Targeting phase
        elif self.targeting_phase:
            if button == mouse.LEFT:
                x, y = mc(x=x, y=y)
                # Game field
                if x < mc(x=SCREEN_W) - 139:
                    x, y = round_coords(x, y)
                    # On-entity attack command
                    target_p_found = False
                    if sel.attacks_air:
                        target_p = a_pos_coord_d[(x, y)]
                        if target_p and target_p != sel:
                            target_p_found = True
                            sel.has_target_p = True
                            sel.target_p = target_p
                            sel.target_p_x = x
                            sel.target_p_y = y
                            target_p.attackers.append(sel)
                            # Too far
                            closest_coord = None
                            closest_d = 10000
                            for coord in target_p.coords:
                                d = ((sel.x-target_p.x) ** 2
                                + (sel.y-target_p.y) ** 2) ** 0.5
                                if d < closest_d:
                                    closest_coord = coord
                                    closest_d = d
                            if sel.attack_rad * PS < closest_d:
                                closest_d = 10000
                                for coords in rad_clipped[sel.attack_rad]:
                                    _x = coords[0]*32 + closest_coord[0]
                                    _y = coords[1]*32 + closest_coord[1]
                                    d = ((sel.x-_x) ** 2
                                        + (sel.y-_y) ** 2) ** 0.5
                                    if d < closest_d:
                                        closest_d = d
                                        x, y = _x, _y
                                sel.move((x, y))
                                self.targeting_phase = False
                                self.set_mouse_cursor(res.cursor)
                                return
                    if not target_p_found and sel.attacks_ground:
                        target_p = g_pos_coord_d[(x, y)]
                        if target_p and target_p != sel:
                            sel.has_target_p = True
                            sel.target_p = target_p
                            sel.target_p_x = x
                            sel.target_p_y = y
                            target_p.attackers.append(sel)
                            # Too far
                            closest_coord = None
                            closest_d = 10000
                            for coord in target_p.coords:
                                d = ((sel.x-target_p.x) ** 2
                                + (sel.y-target_p.y) ** 2) ** 0.5
                                if d < closest_d:
                                    closest_coord = coord
                                    closest_d = d
                            if sel.attack_rad * PS < closest_d:
                                closest_d = 10000
                                for coords in rad_clipped[sel.attack_rad]:
                                    _x = coords[0]*32 + closest_coord[0]
                                    _y = coords[1]*32 + closest_coord[1]
                                    d = ((sel.x-_x) ** 2
                                        + (sel.y-_y) ** 2) ** 0.5
                                    if d < closest_d:
                                        closest_d = d
                                        x, y = _x, _y
                                sel.move((x, y))
                                self.targeting_phase = False
                                self.set_mouse_cursor(res.cursor)
                                return

                    sel.attack_moving = True
                    if sel.dest_reached:
                        sel.move((x, y))
                    # Movement interruption
                    else:
                        sel.move_interd = True
                        sel.new_dest_x = x
                        sel.new_dest_y = y
                    self.targeting_phase = False
                    self.set_mouse_cursor(res.cursor)
                # Minimap
                elif MM0X <= x <= MM0X + 100 and MM0Y <= y <= MM0Y + 100:
                    x = (x - MM0X) * PS
                    y = (y - MM0Y) * PS
                    x, y = round_coords(x, y)
                    sel.attack_moving = True
                    if sel.dest_reached:
                        sel.move((x, y))
                    # Movement interruption
                    else:
                        sel.move_interd = True
                        sel.new_dest_x = x
                        sel.new_dest_y = y
                    self.targeting_phase = False
                    self.set_mouse_cursor(res.cursor)
                else:
                    return
            else:
                self.targeting_phase = False
                self.set_mouse_cursor(res.cursor)
        # Normal phase
        else:
            self.show_hint = False  # Fixes a bug with hints
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
                    # Rally point
                    if sel in our_structs:
                        if g_pos_coord_d[x, y] != sel:
                            sel.rp_x = x
                            sel.rp_y = y
                            sel.default_rp = False
                            self.rp_spt.x = x
                            self.rp_spt.y = y
                        else:
                            sel.default_rp = True
                            self.rp_spt.x = sel.x
                            self.rp_spt.y = sel.y
                        # print('Rally set to ({}, {})'.format(x, y))
                    # A unit is selected
                    else:
                        if sel in our_units:
                            if sel.dest_reached:
                                sel.move((x, y))
                            # Movement interruption
                            else:
                                sel.move_interd = True
                                sel.new_dest_x = x
                                sel.new_dest_y = y
                                # Refunding structures
                                try:
                                    if sel.to_build:
                                        sel.owner.min_c += sel.to_build.cost
                                        self.update_min_c_label()
                                except AttributeError:
                                    pass
                            sel.has_target_p = False
                            # Gathering
                            if isinstance(sel, Pioneer):
                                if sel.path or is_melee_dist(sel, x, y):
                                    sel.clear_task()
                                    obj = g_pos_coord_d[(x, y)]
                                    if isinstance(obj, Mineral):
                                        sel.mineral_to_gather = obj
                                        sel.task_x = obj.x
                                        sel.task_y = obj.y
                                        obj.workers.append(sel)
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
                    x = (x - MM0X) * PS
                    y = (y - MM0Y) * PS
                    x, y = round_coords(x, y)
                    # A unit is sel
                    unit_found = False
                    for unit in our_units:
                        if unit is sel:
                            unit_found = True
                            if unit.dest_reached:
                                unit.move((x, y))
                            else:  # Movement interruption
                                unit.dest_x = unit.target_x
                                unit.dest_y = unit.target_y
                                unit.move_interd = True
                                unit.new_dest_x = x
                                unit.new_dest_y = y
                    if not unit_found:
                        if sel in our_structs:
                            sel.rp_x = x
                            sel.rp_y = y
                            self.rp_spt.x = x
                            self.rp_spt.y = y
                            # print('Rally set to ({}, {})'.format(x, y))
            # Control panel other
            else:
                x, y = mc(x=x, y=y)
                w = self.menu_b.width
                h = self.menu_b.height
                if self.menu_b.x - w // 2 <= x <= \
                        self.menu_b.x + w // 2 and \
                        self.menu_b.y - h // 2 <= y <= \
                        self.menu_b.y + h // 2:
                    self.paused = True
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
                elif sel in our_units:
                    # Move
                    if self.move_b.x - 16 <= x <= self.move_b.x + 16 and \
                            self.move_b.y - 16 <= y <= self.move_b.y + 16:
                        self.set_mouse_cursor(res.cursor_target)
                        self.m_targeting_phase = True
                        return
                    # Stop
                    if self.stop_b.x - 16 <= x <= self.stop_b.x + 16 and \
                            self.stop_b.y - 16 <= y <= self.stop_b.y + 16:
                        sel.stop()
                        return
                    # Attack
                    if self.attack_b.x - 16 <= x <= self.attack_b.x + 16 \
                            and self.attack_b.y - 16 <= y <= \
                            self.attack_b.y + 16:
                        try:
                            if sel.weapon_type != 'none':
                                if sel.owner.name == 'p1':
                                    self.set_mouse_cursor(
                                        res.cursor_target)
                                self.targeting_phase = True
                        except AttributeError:
                            pass
                        return
                    # Construct structures
                    if isinstance(sel, Pioneer):
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
            if self.to_build is MechCenter:
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
                if g_pos_coord_d[self.to_build_spt.x, self.to_build_spt.y] or \
                        self.npa[y, x, 3] != 0:
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
