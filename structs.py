from classes import *


def order_unit(game_inst, struct, unit):
    """Orders units in structures. Checks if you have enough minerals."""
    owner = struct.owner
    # Queue is full
    if len(struct.prod_q) == 3:
        if owner == game_inst.this_player:
            game_inst.txt_out.text = "Queue is full"
            game_inst.txt_out_upd_f = game_inst.f
        return
    # Enough minerals
    if owner.min_c - unit.cost >= 0:
        owner.min_c -= unit.cost
        game_inst.update_min_c_label()
        struct.prod_q.append(unit)
        struct.anim.visible = True
        struct.prod_complete = False
        if selected == struct:
            game_inst.prod_bar_bg.visible = True
            game_inst.prod_bar.visible = True
            game_inst.prod_icon1.visible = True
            game_inst.prod_icon2.visible = True
            game_inst.prod_icon3.visible = True
            if len(struct.prod_q) == 1:
                struct.prod_start_f = game_inst.f
                game_inst.prod_icon1.image = unit.icon
            elif len(struct.prod_q) == 2:
                game_inst.prod_icon2.image = unit.icon
            else:
                game_inst.prod_icon3.image = unit.icon
    # Not enough minerals
    else:
        if owner == game_inst.this_player:
            game_inst.txt_out.text = "Not enough minerals"
            game_inst.txt_out_upd_f = game_inst.f


def building_spawn_unit(game_inst, struct):
    if struct.prod_q:
        unit = struct.prod_q[0]
        struct.cur_max_prod_time = unit.build_time
        # Is it time to spawn?
        if game_inst.f - struct.prod_start_f >= struct.cur_max_prod_time:
            if str(struct.prod_q[0]) not in LIST_OF_FLYING:
                dict_to_check = g_pos_coord_d
            else:
                dict_to_check = a_pos_coord_d
            # Searching for a place to build
            if struct.width == PS:
                x = struct.x - PS
                y = struct.y - PS
            else:
                x = struct.x - PS * 1.5
                y = struct.y - PS * 1.5
            org_x = x
            org_y = y
            place_found = False
            n = struct.width // PS + 2
            for i in range(n):
                x = org_x + PS * i
                if dict_to_check[(x, y)] is None:
                    place_found = True
                    break
            for i in range(n):
                y = org_y + PS * i
                if dict_to_check[(x, y)] is None:
                    place_found = True
                    break
            org_x = x
            for i in range(n):
                x = org_x - PS * i
                if dict_to_check[(x, y)] is None:
                    place_found = True
                    break
            org_y = y
            for i in range(n):
                y = org_y - PS * i
                if dict_to_check[(x, y)] is None:
                    place_found = True
                    break
            if place_found:
                unit = struct.prod_q.pop(0)
                unit = unit(game_inst, x=x, y=y, owner=struct.owner)
                unit.spawn()
                struct.prod_start_f += struct.cur_max_prod_time
                if not struct.prod_q:
                    struct.anim.visible = False
                if not struct.default_rp:
                    unit.move((struct.rp_x, struct.rp_y))
                if struct.owner == game_inst.this_player:
                    game_inst.prod_icon1.image = game_inst.prod_icon2.image
                    game_inst.prod_icon2.image = game_inst.prod_icon3.image
                    game_inst.prod_icon3.image = res.none_img
            else:
                struct.prod_start_f += 1
                if struct.owner == game_inst.this_player:
                    game_inst.txt_out.text = "No place"
                    game_inst.txt_out_upd_f = game_inst.f


def order_structure(game_inst, unit, struct, x, y):
    owner = unit.owner
    if owner.min_c - struct.cost >= 0:
        owner.min_c -= struct.cost
        game_inst.update_min_c_label()
        unit.to_build = game_inst.to_build
        unit.task_x = game_inst.to_build_spt.x
        unit.task_y = game_inst.to_build_spt.y
        # unit.move((x, y))
        if unit.dest_reached:
            unit.move((x, y))
            # Movement interruption
        else:
            unit.move_interd = True
            unit.new_dest_x = x
            unit.new_dest_y = y
    else:
        if owner == game_inst.this_player:
            game_inst.txt_out.text = "Not enough minerals"
            game_inst.txt_out_upd_f = game_inst.f


class Struct(Sprite):
    """This is what I call buildings. __init__ == spawn()"""

    def __init__(self, game_inst, owner, img, team_color_img, icon, vision_radius,
                 hp, x, y):
        self.owner = owner
        self.team_color = Sprite(team_color_img, x, y,
                                 batch=ground_team_color_batch)
        self.team_color.visible = False
        self.icon = icon
        if owner == game_inst.this_player:
            self.team_color.color = OUR_TEAM_COLOR
            our_structs.append(self)
            minimap_pixel = res.mm_our_img
            game_inst.update_fow(x=x, y=y, radius=vision_radius)
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
        if self.owner == game_inst.this_player:
            for block in self.blocks:
                game_inst.update_fow(x=block[0], y=block[1],
                                     radius=vision_radius)
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
            self.const_f = self.game_inst.f
            self.under_constr = True
        else:
            self.constr_complete()


class Armory(Struct, GuardianStructure):
    cost = 200
    build_time = 60

    def __init__(self, game_inst, x, y, owner=None, skip_constr=False):
        if owner is None:
            owner = game_inst.this_player
        super().__init__(game_inst, owner, res.armory_img,
                         res.armory_team_color, res.armory_icon_img,
                         vision_radius=2,  hp=100, x=x, y=y)
        super().gs_init(skip_constr)


class MechCenter(Struct, ProductionStruct, GuardianStructure):
    cost = 500
    build_time = 100

    def __init__(self, game_inst, x, y, owner=None, skip_constr=False):
        if owner is None:
            owner = game_inst.this_player
        super().__init__(game_inst, owner, res.mech_center_img,
                         res.mech_center_team_color, res.mech_center_icon_img,
                         x=x, y=y, hp=1500, vision_radius=4)
        super().ps_init()
        super().gs_init(skip_constr)
        self.cbs = [game_inst.defiler_b, game_inst.centurion_b,
                    game_inst.wyrm_b, game_inst.apocalypse_b,
                    game_inst.pioneer_b, game_inst.cancel_b]
        self.is_big = True
        if owner.name == 'player1':
            self.anim = Sprite(img=res.anim, x=x, y=y, batch=ground_units_batch)
        else:
            self.anim = Sprite(img=res.anim_enemy, x=x, y=y,
                               batch=ground_units_batch)
        self.anim.visible = False


class OffensiveStruct(Struct):
    def __init__(self, game_inst, owner, img, team_color, icon, vision_radius, hp,
                 x, y, damage, cooldown):
        super().__init__(game_inst, owner, img, team_color, icon, vision_radius,
                         hp, x, y)
        self.damage = damage
        self.shooting_radius = vision_radius * 32
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
            if self.owner.name == 'player1':
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
    build_time = 40

    def __init__(self, game_inst, x, y, owner=None, skip_constr=False):
        if owner is None:
            owner = game_inst.this_player
        super().__init__(game_inst, owner, res.turret_img,
                         res.turret_team_color, res.turret_icon_img,
                         vision_radius=5,
                         hp=100, x=x, y=y, damage=20, cooldown=60)
        super().gs_init(skip_constr)

    def constr_complete(self):
        self.under_constr = False
        self.image = self.completed_image
        self.team_color.visible = True

        self.plasma_spt = Sprite(res.plasma_anim, self.x, self.y,
                                 batch=ground_units_batch)

