import sys
import socket
import threading
import numpy as np
import win32api

from pyglet.gl import *
from pyglet.window import key
from pyglet.window import mouse
from pyglet.sprite import Sprite
from constants_and_utilities import *
from shadowandunittc import ShadowAndUnitTC
import resources as res

lvb = 0
bvb = 0

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
    game field, minimap, and control panel."""
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

class HitAnim(Sprite):
    def __init__(self, x, y):
        super().__init__(res.hit_anim, x, y, batch=explosions_batch)

class Explosion(Sprite):
    def __init__(self, x, y, scale=1):
        super().__init__(res.explosion_anim, x, y, batch=explosions_batch)
        self.scale = scale

class PlanetEleven(pyglet.window.Window):
    def __init__(self, width, height, title):
        global sel
        conf = Config(sample_buffers=1, samples=4, depth_size=16,
                      double_buffer=True)
        super().__init__(width, height, title, config=conf)
        self.set_mouse_cursor(res.cursor)
        self.show_fps = True
        self.fps_display = pyglet.window.FPSDisplay(window=self)
        self.ui = []
        self.mouse_x = 0
        self.mouse_y = 0
        self.show_hint = False
        self.menu_bg = UI(self, res.menu_bg, 0, 0)
        self.paused = False
        self.options = False
        self.f = 0
        host = "127.0.0.1"
        port = 12345
        self.conn = socket.socket()
        self.conn.connect((host, port))
        self.user_input = False
        self.msg_2_send = "Empty message"
        counter = self.conn.recv(1024).decode()
        if counter == "1":
            self.this_player = Player("p1")
            self.other_player = Player("p2")
        elif counter == "2":
            self.this_player = Player("p2")
            self.other_player = Player("p1")
        # self.other_player.min_c = 50000
        # self.other_player.workers_count = 0
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
        self.mm_fow_img = pyglet.image.load('sprites/mm/mm_fow.png')
        self.mm_fow_ImageData = self.mm_fow_img.get_image_data()
        self.npa = np.fromstring(self.mm_fow_ImageData.get_data(
            'RGBA', self.mm_fow_ImageData.width * 4), dtype=np.uint8)
        self.npa = self.npa.reshape((102, 102, 4))
        self.min_c_label = pyglet.text.Label(
            str(self.this_player.min_c), x=SCREEN_W - 180,
            y=SCREEN_H - 20, anchor_x='center', anchor_y='center')
        self.mineral_small = UI(self, res.mineral_small, x=SCREEN_W - 210,
            y=SCREEN_H - 20)
        self.sel_icon = UI(self, res.none_img, CB_COORDS[0][0],
                                SCREEN_H - 72)
        self.sel_hp = pyglet.text.Label('', x=CB_COORDS[1][0] - 15,
                                             y=SCREEN_H - 72, anchor_y='center',
                                             font_size=8,
                                             color=(0, 0, 0,255))
        self.txt_out = pyglet.text.Label('', x=SCREEN_W / 2 - 50, y=100,
                anchor_x='center', anchor_y='center', font_size=8)
        self.txt_out_upd_f = None
        self.prod_bar_bg = UI(self, res.prod_bar_bg_img, CP_CENTER_X,
                              SCREEN_H - 93)
        self.prod_bar_bg.visible = False
        self.prod_bar = UI(self, res.prod_bar_img, SCREEN_W - 120, SCREEN_H - 94)
        self.prod_bar.visible = False
        self.prod_icon1 = UI(self, res.none_img, CB_COORDS[0][0], SCREEN_H - 110)
        self.prod_icon2 = UI(self, res.none_img, CB_COORDS[1][0], SCREEN_H - 110)
        self.prod_icon3 = UI(self, res.none_img, CB_COORDS[2][0], SCREEN_H - 110)

        # Hints
        self.hint = UI(self, res.hint_defiler, 100, 100)

        # Menu
        self.resume_b = UI(self, res.resume_img, SCREEN_W / 2, 300,
                           batch=menu_b_batch)
        self.save_b = UI(self, res.save_img, SCREEN_W / 2, 280,
                         batch=menu_b_batch)
        self.load_b = UI(self, res.load_img, SCREEN_W / 2, 260,
                         batch=menu_b_batch)
        self.restart_b = UI(self, res.restart_img, SCREEN_W / 2, 240,
                            batch=menu_b_batch)
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
        self.move_b = UI(self, res.move_img, CB_COORDS[0][0],
                         CB_COORDS[0][1])
        self.stop_b = UI(self, res.stop_img, CB_COORDS[1][0],
                         CB_COORDS[1][1])
        self.attack_b = UI(self, res.attack_img, CB_COORDS[2][0],
                           CB_COORDS[2][1])
        self.cancel_b = UI(self, res.cancel_img, CB_COORDS[8][0],
                           CB_COORDS[8][1])
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
        # Spawn minerals
        Mineral(self, PS / 2 + PS * 4, PS / 2 + PS * 7)
        Mineral(self, PS / 2 + PS * 4,  PS / 2 + PS * 8)
        Mineral(self, PS / 2 + PS * 6, PS / 2 + PS * 4)
        Mineral(self, PS / 2 + PS * 7, PS / 2 + PS * 3)
        Mineral(self, PS / 2 + PS * 10, PS / 2 + PS * 4)
        Mineral(self, PS / 2 + PS * 11, PS / 2 + PS * 4)

        Mineral(self, PS / 2 + PS * 52, PS / 2 + PS * 47)
        Mineral(self, PS / 2 + PS * 52, PS / 2 + PS * 46)
        Mineral(self, PS / 2 + PS * 46, PS / 2 + PS * 46)
        Mineral(self, PS / 2 + PS * 46, PS / 2 + PS * 48)
        # Spawn structures
        if self.this_player.name == "p1":
            x1, y1 = PS * 7, PS * 8
            x2, y2 = PS * 9, PS * 10
        elif self.this_player.name == "p2":
            x1, y1 = PS * 9, PS * 10
            x2, y2 = PS * 7, PS * 8
        self.our_1st_base = MechCenter(self, x1, y1, skip_constr=True)
        MechCenter(self, x2, y2, skip_constr=True, owner=self.other_player)
        sel = self.our_1st_base
        self.sel_icon.image = sel.icon

        self.sel_spt = Sprite(img=res.sel_img, x=self.our_1st_base.x,
                              y=self.our_1st_base.y)
        self.sel_big_spt = Sprite(img=res.sel_big_img, x=self.our_1st_base.x,
                                  y=self.our_1st_base.y)
        self.rp_spt = Sprite(img=res.rp_img, x=self.our_1st_base.rp_x,
                             y=self.our_1st_base.rp_y)

        self.basic_unit_c_bs = [self.move_b, self.stop_b, self.attack_b]
        self.cbs_2_render = self.our_1st_base.cbs
        self.to_build_spt = Sprite(img=res.armory_img, x=-100, y=-100)
        self.to_build_spt.color = (0, 255, 0)

        # Spawn units. Have to spawn them right here. I don't remember why.
        if self.this_player.name == "p1":
            x1, y1 = PS / 2 + PS * 8, PS / 2 + PS * 6
            x2, y2 = PS / 2 + PS * 10, PS / 2 + PS * 6
        elif self.this_player.name == "p2":
            x1, y1 = PS / 2 + PS * 10, PS / 2 + PS * 6
            x2, y2 = PS / 2 + PS * 8, PS / 2 + PS * 6
        Pioneer(self, x1, y1).spawn()
        Pioneer(self, x2, y2, owner=self.other_player).spawn()

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

        # Me playing with OpenGL
        # glViewport(0, 0, SCREEN_WIDTH - 179, SCREEN_HEIGHT)

        # Set orthographic projection matrix
        glOrtho(lvb, lvb + SCREEN_W, bvb, bvb + SCREEN_H, 1, -1)

        if not self.paused:
            self.terrain.draw()
            ground_shadows_batch.draw()
            structures_batch.draw()
            ground_units_batch.draw()
            ground_team_color_batch.draw()
            weapons_batch.draw()
            explosions_batch.draw()
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
            self.fow_texture = self.mm_fow_img.get_texture()
            self.fow_texture.width = 3264
            self.fow_texture.height = 3264
            self.fow_texture.blit(-32, -32)
            utilities_batch.draw()
            if self.build_loc_sel_phase:
                self.to_build_spt.draw()
            self.cp_spt.draw()
            self.menu_b.draw()
            self.sel_frame_cp.draw()
            self.sel_icon.draw()
            self.prod_bar_bg.draw()
            self.prod_bar.draw()
            self.prod_icon1.draw()
            self.prod_icon2.draw()
            self.prod_icon3.draw()
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

            self.fow_texture.width = 102
            self.fow_texture.height = 102
            self.fow_texture.blit(minimap_fow_x, minimap_fow_y)

            self.mm_cam_frame_spt.draw()
            self.min_c_label.draw()
            self.mineral_small.draw()
            if self.show_fps:
                self.fps_display.draw()

            if self.show_hint:
                self.hint.draw()
            self.txt_out.draw()
        else:
            self.menu_bg.draw()
            if self.options:
                options_batch.draw()
                check_batch.draw()
            else:
                menu_b_batch.draw()

        # Remove default modelview matrix
        glPopMatrix()

    def update(self, delta_time):
        """Updates client game state after receiving changes from the server."""
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
                if sel in our_units and sel.owner is self.this_player:
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
                            if sel.owner is self.this_player:
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
        if not self.paused:
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
                        self.sel_icon.image = sel.icon
                        try:
                            self.sel_hp.text = str(int(sel.hp)) \
                                + '/' + str(sel.max_hp)
                        except AttributeError:
                            self.sel_hp.text = str(int(sel.hp))
                        # Production
                        if sel.owner is self.this_player:
                            try:
                                sel.prod_q[0]
                                self.prod_bar_bg.visible = True
                                self.prod_bar.visible = True
                                self.prod_icon1.visible = True
                                self.prod_icon2.visible = True
                                self.prod_icon3.visible = True
                            # Not a structure or nothing in production
                            except (AttributeError, IndexError):
                                self.prod_bar_bg.visible = False
                                self.prod_bar.visible = False
                                self.prod_icon1.visible = False
                                self.prod_icon2.visible = False
                                self.prod_icon3.visible = False
                        else:
                            self.prod_bar_bg.visible = False
                            self.prod_bar.visible = False
                            self.prod_icon1.visible = False
                            self.prod_icon2.visible = False
                            self.prod_icon3.visible = False
                        # Control buttons
                        try:
                            if sel.owner is self.this_player:
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
                                    if sel.owner is self.this_player:
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
        # Paused
        else:
            x, y = mc(x=x, y=y)
            if self.options:
                if self.fullscreen_c.x - 8 <= x <= self.fullscreen_c.x + 8 \
                    and \
                   self.fullscreen_c.y - 8 <= y <= self.fullscreen_c.y + 8:
                    if self.fullscreen:
                        self.set_fullscreen(False)
                        self.fullscreen_c.check.visible = False
                    else:
                        self.set_fullscreen(True)
                        self.fullscreen_c.check.visible = True
                elif self.back_b.x - 25.5 <= x <= self.back_b.x + 25.5 and \
                        self.back_b.y - 8 <= y <= self.back_b.y + 8:
                    self.options = False
            else:
                if self.resume_b.x - 48 <= x <= self.resume_b.x + 48 and \
                   self.resume_b.y - 8 <= y <= self.resume_b.y + 8:
                    self.paused = False
                elif self.options_b.x - 48 <= x <= self.options_b.x + 48 and \
                     self.options_b.y - 8 <= y <= self.options_b.y + 8:
                    self.options = True
                elif self.exit_b.x - 48 <= x <= self.exit_b.x + 48 and \
                     self.exit_b.y - 8 <= y <= self.exit_b.y + 8:
                    sys.exit()

    def on_mouse_motion(self, x, y, dx, dy):
        if self.fullscreen:
            x /= 2
            y /= 2
        if not self.paused and self.build_loc_sel_phase:
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
        elif not self.paused:
            # Hits
            if isinstance(sel, MechCenter) and not sel.under_constr:
                # Defiler
                if CB_COORDS[0][0] - 16 <= x <= CB_COORDS[0][0] + \
                    16 and CB_COORDS[0][1] - 16 <= y <= CB_COORDS[0][1] + 16:
                    self.hint.image = res.hint_defiler
                    self.hint.x = x + lvb
                    self.hint.y = y + bvb
                    self.show_hint = True
                # Centurion
                elif CB_COORDS[1][0] - 16 <= x <= CB_COORDS[1][0] + \
                16 and CB_COORDS[1][1] - 16 <= y <= CB_COORDS[1][1] + 16:
                    self.hint.image = res.hint_centurion
                    self.hint.x = x + lvb
                    self.hint.y = y + bvb
                    self.show_hint = True
                # Wyrm
                elif CB_COORDS[2][0] - 16 <= x <= CB_COORDS[2][0] + \
                16 and CB_COORDS[2][1] - 16 <= y <= CB_COORDS[2][1] + 16:
                    self.hint.image = res.hint_wyrm
                    self.hint.x = x + lvb
                    self.hint.y = y + bvb
                    self.show_hint = True
                # Apocalypse
                elif CB_COORDS[3][0] - 16 <= x <= CB_COORDS[3][0] + \
                16 and CB_COORDS[3][1] - 16 <= y <= CB_COORDS[3][1] + 16:
                    self.hint.image = res.hint_apocalypse
                    self.hint.x = x + lvb
                    self.hint.y = y + bvb
                    self.show_hint = True
                # Pioneer
                elif CB_COORDS[4][0] - 16 <= x <= CB_COORDS[4][0] + \
                16 and CB_COORDS[4][1] - 16 <= y <= CB_COORDS[4][1] + 16:
                    self.hint.image = res.hint_pioneer
                    self.hint.x = x + lvb
                    self.hint.y = y + bvb
                    self.show_hint = True
                else:
                    self.show_hint = False
            elif isinstance(sel, Pioneer):
                # Armory
                if CB_COORDS[3][0] - 16 <= x <= CB_COORDS[3][0] + \
                16 and CB_COORDS[3][1] - 16 <= y <= CB_COORDS[3][1] + 16:
                    self.hint.image = res.hint_armory
                    self.hint.x = x + lvb
                    self.hint.y = y + bvb
                    self.show_hint = True
                    # Armory
                elif CB_COORDS[4][0] - 16 <= x <= CB_COORDS[4][0] + \
                16 and CB_COORDS[4][1] - 16 <= y <= CB_COORDS[4][1] + 16:
                    self.hint.image = res.hint_turret
                    self.hint.x = x + lvb
                    self.hint.y = y + bvb
                    self.show_hint = True
                elif CB_COORDS[5][0] - 16 <= x <= CB_COORDS[5][0] + \
                16 and CB_COORDS[5][1] - 16 <= y <= CB_COORDS[5][1] + 16:
                    self.hint.image = res.hint_mech_center
                    self.hint.x = x + lvb
                    self.hint.y = y + bvb
                    self.show_hint = True
                else:
                    self.show_hint = False

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        global lvb, bvb
        if not self.paused:
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
        self.min_c_label.x = SCREEN_W - 180 + lvb
        self.min_c_label.y = SCREEN_H - 20 + bvb
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

    def update_fow(self, x, y, radius):
        x = int((x - 16) / 32) + 1
        y = int((y - 16) / 32) + 1
        for yi in range(-radius + y, radius + 1 + y):
            if 0 <= yi <= 101:
                for xi in range(-radius + x, radius + 1 + x):
                    if 0 <= xi <= 101:
                        if ((xi - x) ** 2 + (yi - y) ** 2) ** 0.5 <= radius:
                            self.npa[yi, xi, 3] = 0
        self.mm_fow_ImageData.set_data('RGBA', self.mm_fow_ImageData.width
                                       * 4, data=self.npa.tobytes())

    def update_min_c_label(self):
        self.min_c_label.text = str(int(self.this_player.min_c))

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

    def cancel_prod(self):
        try:
            self.this_player.min_c += sel.prod_q[-1].cost
            self.update_min_c_label()
            del sel.prod_q[-1]
            if not sel.prod_q:
                sel.anim.visible = False
                sel.prod_complete = True
                self.prod_bar.scale_x = 1
            exec("self.prod_icon{}.image = res.none_img".format(
                len(sel.prod_q) + 1))
        except (AttributeError, IndexError):
            return

    def ai(self):
        # AI ordering units
        for struct in enemy_structs:
            if isinstance(struct, MechCenter):
                if self.other_player.workers_count < 6:
                    order_unit(self, struct, Pioneer)
                    self.other_player.workers_count += 1
                else:
                    order_unit(self, struct, random.choice((Wyrm, Centurion,
                                                            Defiler, Apocalypse)))
        # AI gathering resources
        try:
            closest_min = minerals[0]
            for worker in workers:
                if all((not worker.is_gathering,
                        worker.dest_reached,
                        worker.owner.name == 'p2')):
                    dist_2_closest_min = dist(closest_min, worker)
                    for mineral in minerals[1:]:
                        dist_2_min = dist(mineral, worker)
                        if dist_2_min < dist_2_closest_min:
                            closest_min = mineral
                            dist_2_closest_min = dist_2_min
                    worker.move((closest_min.x, closest_min.y))
                    worker.clear_task()
                    # print('go gather, lazy worker!')
                    worker.mineral_to_gather = closest_min
                    worker.task_x = closest_min.x
                    worker.task_y = closest_min.y
                    closest_min.workers.append(worker)
        except IndexError:
            pass
        # AI sending units to attack:
        for unit in enemy_units:
            if unit.weapon_type != 'none' and not unit.has_target_p:
                closest_enemy = None
                closest_enemy_dist = None
                for entity in our_units + our_structs:
                    try:
                        if not unit.attacks_air and entity.flying:
                            continue
                        if not unit.attacks_ground \
                                and not entity.flying:
                            continue
                    except AttributeError:
                        pass
                    dist_to_enemy = dist(unit, entity)
                    if not closest_enemy:
                        closest_enemy = entity
                        closest_enemy_dist = dist_to_enemy
                    else:
                        if dist_to_enemy < closest_enemy_dist:
                            closest_enemy = entity
                            closest_enemy_dist = dist_to_enemy
                try:
                    unit.move(round_coords(closest_enemy.x,
                                           closest_enemy.y))
                    unit.attack_moving = True
                except AttributeError:
                    pass

    def incoming_msg(self):
        while True:
            print("Waiting for message")
            msg = [int(float(x)) for x in self.conn.recv(1024).decode().split()]
            print("received_msg =", msg)
            unit = g_pos_coord_d[(msg[0], msg[1])]
            unit.move((msg[2], msg[3]))


def main():
    game_window = PlanetEleven(SCREEN_W, SCREEN_H, SCREEN_TITLE)
    inc_msg_thread = threading.Thread(target=game_window.incoming_msg)
    inc_msg_thread.start()
    pyglet.clock.schedule_interval(game_window.update, 1 / 60)
    pyglet.app.run()


if __name__ == "__main__":
    main()
