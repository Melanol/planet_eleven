import time
import socket
import threading

from weapons import *
from bb_enemy_detection import rad_clipped

LIST_OF_FLYING = ["<class '__main__.Defiler'>",
                  "<class '__main__.Apocalypse'>"]
minerals = []
our_units = []
workers = []
our_structs = []
enemy_structs = []
prod_structs = []
offensive_structs = []
enemy_units = []

def dist(obj1, obj2):
    return ((obj1.x - obj2.x) ** 2 + (obj1.y - obj2.y) ** 2) ** 0.5

def is_melee_dist(unit, target_x, target_y):
    """Checks if a unit is in the 8 neighboring blocks of the target object.
    Used for melee interaction."""
    if abs(unit.x - target_x) == PS:
        if abs(unit.y - target_y) == PS or unit.y == target_y:
            return True
    elif unit.x == target_x and abs(unit.y - target_y) == PS:
        return True
    return False

def is_2_melee_dist(unit, target_x, target_y):
    """Similar to is_melee_dist(), but for buildings 2 blocks wide."""
    if abs(unit.x - target_x) <= PS * 1.5:
        if abs(unit.y - target_y) <= PS * 1.5:
            return True
    return False

POS_COORDS_N_ROWS = 100  # Should be 100 for the minimap to work
POS_COORDS_N_COLUMNS = 100  # Should be 100 for the minimap to work
PS = 32
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

def closest_enemy_2_att(entity, enemy_entities):
    x = entity.x
    y = entity.y
    for rad in rad_clipped[:entity.attack_rad + 1]:
        for coord in rad:
            if entity.attacks_air:
                entity1 = a_pos_coord_d.get((x + coord[0] * 32,
                                             y + coord[1] * 32))
                if entity1 in enemy_entities:
                    return entity1
            if entity.attacks_ground:
                entity1 = g_pos_coord_d.get((x + coord[0] * 32,
                                             y + coord[1] * 32))
                if entity1 in enemy_entities:
                    return entity1

def update_shooting(game_inst, our_entities, enemy_entities):
    for entity in our_entities:
        try:  # For shooting structures
            entity.weapon_type
            entity.dest_reached
        except AttributeError:
            if entity.under_constr:
                return
            entity.weapon_type = 'projectile'
            entity.dest_reached = True
        if entity.weapon_type != 'none' and entity.dest_reached:
            if not entity.on_cooldown:
                if not entity.has_target_p:
                    closest_enemy = closest_enemy_2_att(entity, enemy_entities)
                    if closest_enemy:
                        entity.has_target_p = True
                        entity.target_p = closest_enemy
                        entity.target_p_x = closest_enemy.x
                        entity.target_p_y = closest_enemy.y
                        entity.target_p.attackers.append(entity)
                # Has target_p
                elif dist(entity, entity.target_p) <= entity.attack_rad * 32:
                    entity.shoot(game_inst.f)
                else:
                    entity.has_target_p = False
                    entity.target_p.attackers.remove(entity)
                    entity.target_p = None
                    entity.target_p_x = None
                    entity.target_p_y = None
            else:
                if (game_inst.f - entity.cooldown_started) % \
                        entity.cooldown == 0:
                    entity.on_cooldown = False

class Player:
    def __init__(self, name):
        self.min_c = 5000
        self.name = name

class Mineral:
    def __init__(self, outer_instance, x, y, hp=5000):
        self.outer_instance = outer_instance
        self.workers = []
        self.hp = hp
        self.cbs = None
        self.icon = res.mineral
        minerals.append(self)
        g_pos_coord_d[(x, y)] = self

    def kill(self):
        for worker in self.workers:
            worker.clear_task()
            worker.stop()
        g_pos_coord_d[(self.x, self.y)] = None
        self.delete()


def order_unit(game_inst, struct, unit):
    """Orders units in structures. Checks if you have enough minerals."""
    owner = struct.owner
    # Queue is full
    if len(struct.prod_q) == 3:
        if owner is game_inst.this_player:
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
        if sel is struct and owner is game_inst.this_player:
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
        if owner is game_inst.this_player:
            game_inst.txt_out.text = "Not enough minerals"
            game_inst.txt_out_upd_f = game_inst.f


def struct_spawn_unit(game_inst, struct):
    if struct.prod_q:
        unit = struct.prod_q[0]
        struct.cur_max_prod_time = unit.build_time
        # Time to spawn?
        if game_inst.f - struct.prod_start_f >= struct.cur_max_prod_time:
            if str(struct.prod_q[0]) not in LIST_OF_FLYING:
                dict_to_check = g_pos_coord_d
            else:
                dict_to_check = a_pos_coord_d
            # Searching for a place to spawn
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
                try:
                    if dict_to_check[(x, y)] is None:
                        place_found = True
                        break
                except KeyError:
                    pass
            for i in range(n):
                y = org_y + PS * i
                try:
                    if dict_to_check[(x, y)] is None:
                        place_found = True
                        break
                except KeyError:
                    pass
            org_x = x
            for i in range(n):
                x = org_x - PS * i
                try:
                    if dict_to_check[(x, y)] is None:
                        place_found = True
                        break
                except KeyError:
                    pass
            org_y = y
            for i in range(n):
                y = org_y - PS * i
                try:
                    if dict_to_check[(x, y)] is None:
                        place_found = True
                        break
                except KeyError:
                    pass
            if place_found:
                unit = struct.prod_q.pop(0)
                unit = unit(game_inst, x, y, struct.owner)
                unit.spawn()
                struct.prod_start_f += struct.cur_max_prod_time
                if not struct.prod_q:
                    struct.anim.visible = False
                if not struct.default_rp:
                    unit.move((struct.rp_x, struct.rp_y))
                if struct.owner is game_inst.this_player:
                    game_inst.prod_icon1.image = game_inst.prod_icon2.image
                    game_inst.prod_icon2.image = game_inst.prod_icon3.image
                    game_inst.prod_icon3.image = res.none_img
            else:
                struct.prod_start_f += 1
                if struct.owner is game_inst.this_player:
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
        if owner is game_inst.this_player:
            game_inst.txt_out.text = "Not enough minerals"
            game_inst.txt_out_upd_f = game_inst.f


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
        if owner is game_inst.this_player:
            self.team_color.color = OUR_TEAM_COLOR
            our_structs.append(self)
            minimap_pixel = res.mm_our_img
            game_inst.update_fow(x=x, y=y, radius=vision_rad)
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
        if self.owner is game_inst.this_player:
            for block in self.blocks:
                game_inst.update_fow(x=block[0], y=block[1],
                                     radius=vision_rad)
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
    build_time = 60

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
    build_time = 100

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
        if owner is self.game_inst.this_player:
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
            if self.owner is self.game_inst.this_player:
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


node_count = 0
def astar(map, start, end, acc_ends):
    """A* pathfinding. acc_ends are other acceptable end coords that are used
    when we cannot reach the exact end."""
    global node_count

    class Node:
        def __init__(self, parent=None, pos=None):
            global node_count
            node_count += 1
            self.parent = parent
            self.pos = pos
            self.g = 0
            self.f = 0

        def __eq__(self, other):
            return self.pos == other.pos

    # Create start, end, and acc_ends nodes
    start_node = Node(None, start)
    start_node.g = start_node.f = 0
    end_node = Node(None, end)
    end_node.g = end_node.f = 0
    # print(acc_ends)
    acc_end_nodes = []
    for acc_end in acc_ends:
        # print(acc_end)
        acc_end_nodes.append(Node(None, acc_end))
    # open_list is where you can go now
    open_list = [start_node]
    # closed_list is where we already were
    closed_list = []

    max_nodes = ((start[0] + end[0]) ** 2 + (
            start[1] + end[1]) ** 2) ** 0.5 * 7

    # Loop until you find the end
    while len(open_list) > 0:
        # Get the current node. Which is the node with lowest f of the entire
        # open_list
        current_node = open_list[0]
        current_index = 0
        for index, item in enumerate(open_list):
            if item.f < current_node.f:
                current_node = item
                current_index = index

        # Pop current off open_list, add to closed list
        closed_list.append(open_list.pop(current_index))

        if node_count > max_nodes:
            node_count = 0
            return []

        # Return path
        # print("current_node.pos =", current_node.pos)
        for node in acc_end_nodes:
            # print("node.pos =", node.pos)
            if node == current_node:
                # print(1)
                path = []
                while current_node:
                    path.append(current_node.pos)
                    current_node = current_node.parent
                # print(2)
                node_count = 0
                return path[::-1]  # Return reversed path

        # Generate children
        children = []
        for new_pos in [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1),
                        (1, -1), (1, 1)]:  # Adjacent squares

            # Get node position
            node_pos = (
                current_node.pos[0] + new_pos[0],
                current_node.pos[1] + new_pos[1])

            # Make sure within range
            if node_pos[0] > len(map[0]) - 1 or node_pos[0] < 0 \
                    or node_pos[1] > len(map) - 1 or node_pos[1] < 0:
                continue

            # Make sure walkable terrain
            if map[node_pos[1]][node_pos[0]] != 0:
                continue

            # Create new node
            new_node = Node(current_node, node_pos)

            # Append
            children.append(new_node)

        # Loop through children
        for child in children:

            # Child is already in the open list
            if child in open_list:
                continue

            # Child is on the closed list
            if child in closed_list:
                continue

            # Create the f, g, and h values
            child.g = current_node.g + 1
            child.f = child.g + (child.pos[0] - end_node.pos[0]) ** 2 + (
                    child.pos[1] - end_node.pos[1]) ** 2

            # Add the child to the open list
            open_list.append(child)


def convert_map(pos_coords_dict):
    """Converts the map for path-finding."""
    new_map = []
    i = 1
    row = []
    for x, y in POS_COORDS:
        if pos_coords_dict[(x, y)]:
            row.append(1)
        else:
            row.append(0)
        if i % 100 == 0:
            new_map.append(row)
            row = []
        i += 1
    return new_map


def convert_c_to_simple(c):
    """Called by find_path() only."""
    return int((c - PS // 2) // PS)


def find_path(start, end, is_flying):
    """Main path-finding function. Calls other PF functions."""
    # print('start =', start, 'end =', end)
    # Check end neighbors
    if not is_flying:
        sel_dict = g_pos_coord_d
    else:
        sel_dict = a_pos_coord_d
    if sel_dict[(end[0], end[1])] is None:
        acc_ends = [(convert_c_to_simple(end[0]), convert_c_to_simple(end[1]))]
    else:
        width = 3
        while True:
            acc_ends = []
            dx = dy = -PS
            for i in range(width):
                coord = (end[0] + dx, end[1] + dy)
                try:
                    if sel_dict[coord] is None:
                        acc_ends.append((convert_c_to_simple(coord[0]),
                                         convert_c_to_simple(coord[1])))
                except KeyError:  # Out of the map borders
                    pass
                dx += PS
            dx -= PS
            for i in range(width - 1):
                dy += PS
                coord = (end[0] + dx, end[1] + dy)
                try:
                    if sel_dict[coord] is None:
                        acc_ends.append((convert_c_to_simple(coord[0]),
                                         convert_c_to_simple(coord[1])))
                except KeyError:  # Out of the map borders
                    pass
            for i in range(width - 1):
                dx -= PS
                coord = (end[0] + dx, end[1] + dy)
                try:
                    if sel_dict[coord] is None:
                        acc_ends.append((convert_c_to_simple(coord[0]),
                                         convert_c_to_simple(coord[1])))
                except KeyError:  # Out of the map borders
                    pass
            for i in range(width - 2):
                dy -= PS
                coord = (end[0] + dx, end[1] + dy)
                try:
                    if sel_dict[coord] is None:
                        acc_ends.append((convert_c_to_simple(coord[0]),
                                         convert_c_to_simple(coord[1])))
                except KeyError:  # Out of the map borders
                    pass
            if acc_ends:
                break
            width += 1
    # print("acc_ends =", acc_ends)
    start = convert_c_to_simple(start[0]), convert_c_to_simple(start[1])
    end = convert_c_to_simple(end[0]), convert_c_to_simple(end[1])
    # print('start =', start, 'end =', end)
    map = convert_map(sel_dict)
    # print('map converted to simple')
    map[start[1]][start[0]] = 0
    map[end[1]][end[0]] = 0
    path = astar(map, start, end, acc_ends)
    # print('path =', path)
    if not path:
        return []
    converted_path = []
    for x, y in path:
        x = x * PS + PS // 2
        y = y * PS + PS // 2
        converted_path.append((x, y))
    # print('converted_path =', converted_path)
    return converted_path


class Unit(Sprite):
    def __init__(self, game_inst, owner, img, team_color_img, icon, flying,
                 vision_rad, hp, x, y, speed, weapon_type, w_img, damage,
                 cooldown,
                 attacks_ground, attacks_air, shadow_sprite, cbs):
        self.game_inst = game_inst
        self.owner = owner
        self.team_color = ShadowAndUnitTC(team_color_img, x, y,
                                          ground_team_color_batch)
        self.icon = icon
        self.coords = ((x, y),)
        if owner is game_inst.this_player:
            self.team_color.color = OUR_TEAM_COLOR
            our_units.append(self)
        else:
            self.team_color.color = ENEMY_TEAM_COLOR
            enemy_units.append(self)
        self.flying = flying
        if not self.flying:
            self.pos_dict = g_pos_coord_d
            batch = ground_units_batch
        else:
            self.pos_dict = a_pos_coord_d
            batch = air_batch
            self.team_color.batch = air_team_color_batch
        super().__init__(img, x, y, batch=batch)
        self.vision_rad = vision_rad
        self.attack_rad = vision_rad
        self.attacks_ground = attacks_ground
        self.attacks_air = attacks_air
        self.max_hp = hp
        self.hp = hp
        self.x = x
        self.y = y
        self.speed = speed
        self.weapon_type = weapon_type
        self.w_img = w_img
        self.damage = damage
        self.cooldown = cooldown
        self.shadow_sprite = shadow_sprite
        self.cbs = cbs

        self.dest_reached = True
        self.move_interd = False
        self.target_x = x
        self.target_y = y
        self.dest_x = None
        self.dest_y = None
        self.velocity_x = 0
        self.velocity_y = 0
        self.path = []

        self.has_target_p = False
        self.target_p = None
        self.target_p_x = None
        self.target_p_y = None
        self.on_cooldown = False
        self.cooldown_started = None
        self.attackers = []
        self.attack_moving = False

    def spawn(self):
        """Creates a unit at it's predefined self.x and self.y. Does not move
        it to the rally point."""
        self.pos_dict[(self.x, self.y)] = self

        # Minimap pixel and fow
        pixel_minimap_coords = to_minimap(self.x, self.y)
        if self.owner is self.game_inst.this_player:
            pixel = res.mm_our_img
            self.game_inst.update_fow(self.x, self.y, self.vision_rad)
        else:
            pixel = res.mm_enemy_img
        self.pixel = Sprite(img=pixel, x=pixel_minimap_coords[0],
                            y=pixel_minimap_coords[1],
                            batch=minimap_pixels_batch)

        # Shadow
        if self.flying:
            self.shadow = ShadowAndUnitTC(img=self.shadow_sprite, x=self.x + 10,
                                          y=self.y - 10)
            self.shadow.batch = air_shadows_batch
        else:
            self.shadow = ShadowAndUnitTC(img=self.shadow_sprite, x=self.x + 3,
                                          y=self.y - 3)
            self.shadow.batch = ground_shadows_batch

    def update(self):
        """Updates position and shadow."""
        self.x, self.y = self.x + self.velocity_x, self.y + self.velocity_y
        self.team_color.update()
        self.shadow.update()

    def rotate(self, x, y):
        """Rotates a unit in the direction of his task(mining, building,
        etc.)"""
        diff_x = x - self.x
        diff_y = y - self.y
        angle = math.atan2(diff_y, diff_x)  # Rad
        self.rotation = -math.degrees(angle) + 90
        self.team_color.rotation = -math.degrees(angle) + 90
        self.shadow.rotation = -math.degrees(angle) + 90

    def move(self, dest):
        """Called once by RMB or when a unit is created by a building with
        a non-default rally point."""
        # Attack move
        if self.attack_moving and (self.x, self.y) in POS_COORDS:
            if self.owner is self.game_inst.this_player:
                if closest_enemy_2_att(self, enemy_units + enemy_structs):
                    self.attack_moving = False
                    self.dest_reached = True
                    return
            else:
                if closest_enemy_2_att(self, our_units + our_structs):
                    self.attack_moving = False
                    self.dest_reached = True
                    return
        # Not moving: same coords
        if self.x == dest[0] and self.y == dest[1]:
            self.dest_reached = True
            return

        # Not moving: melee distance and dest occupied
        if is_melee_dist(self, dest[0], dest[1]) and \
                self.pos_dict[(dest[0], dest[1])]:
            self.dest_reached = True
            return
        # Moving or just rotating
        self.dest_reached = False
        self.dest_x, self.dest_y = dest[0], dest[1]

        self.pfi = 1  # 0 creates a bug of rotating to math degree of 0
        # because the 0 element in path is the starting location
        self.path = find_path((self.x, self.y), (self.dest_x, self.dest_y),
                              self.flying)
        try:
            target = self.path[self.pfi]
        except IndexError:
            self.dest_reached = True
            return
        if target:  # If we can reach there
            # print('target =', target)
            self.target_x = target[0]
            self.target_y = target[1]
            self.pixel.x, self.pixel.y = to_minimap(self.target_x,
                                                    self.target_y)
        # Not moving
        else:
            self.dest_reached = True
            self.pos_dict[(self.x, self.y)] = self
            return
        diff_x = self.target_x - self.x
        diff_y = self.target_y - self.y
        angle = math.atan2(diff_y, diff_x)  # Rad
        self.rotation = -math.degrees(angle) + 90
        self.velocity_x = math.cos(angle) * self.speed
        self.velocity_y = math.sin(angle) * self.speed
        self.pos_dict[(self.x, self.y)] = None
        self.pos_dict[(self.target_x, self.target_y)] = self
        msg_2_send = f"{self.x} {self.y} {self.target_x} {self.target_y}"
        self.game_inst.conn.sendall(msg_2_send.encode())

        self.team_color.rotation = -math.degrees(angle) + 90
        self.team_color.velocity_x = math.cos(angle) * self.speed
        self.team_color.velocity_y = math.sin(angle) * self.speed
        self.shadow.rotation = -math.degrees(angle) + 90
        self.shadow.velocity_x = math.cos(angle) * self.speed
        self.shadow.velocity_y = math.sin(angle) * self.speed

    def eta(self):
        """Estimated time of arrival to the target location (not dest)."""
        dist_to_target = ((self.target_x - self.x) ** 2 + (
                self.target_y - self.y) ** 2) ** 0.5
        return dist_to_target / self.speed

    def update_move(self):
        """Called by update to move to the next point."""
        self.pfi += 1
        diff_x = self.dest_x - self.x
        diff_y = self.dest_y - self.y
        angle = math.atan2(diff_y, diff_x)  # Rad
        d_angle = math.degrees(angle)
        self.rotation = -d_angle + 90
        self.team_color.rotation = -math.degrees(angle) + 90
        self.shadow.rotation = -math.degrees(angle) + 90
        try:
            next_target = self.path[self.pfi]
        except IndexError:
            self.dest_reached = True
            return
        if self.pos_dict[
            (next_target[0], next_target[1])]:  # Obstruction detected
            self.move((self.dest_x, self.dest_y))
            return
        if next_target:  # Moving
            self.pos_dict[(self.x, self.y)] = None
            self.target_x = next_target[0]
            self.target_y = next_target[1]
            self.pixel.x, self.pixel.y = to_minimap(self.target_x,
                                                    self.target_y)
            self.pos_dict[(self.target_x, self.target_y)] = self
            diff_x = self.target_x - self.x
            diff_y = self.target_y - self.y
            angle = math.atan2(diff_y, diff_x)  # Rad
            d_angle = math.degrees(angle)
            self.rotation = -d_angle + 90
            self.velocity_x = math.cos(angle) * self.speed
            self.velocity_y = math.sin(angle) * self.speed
            self.team_color.rotation = -math.degrees(angle) + 90
            self.team_color.velocity_x = math.cos(angle) * self.speed
            self.team_color.velocity_y = math.sin(angle) * self.speed
            self.shadow.rotation = -math.degrees(angle) + 90
            self.shadow.velocity_x = math.cos(angle) * self.speed
            self.shadow.velocity_y = math.sin(angle) * self.speed
        else:
            self.pos_dict[(self.x, self.y)] = self
            self.dest_reached = True

    def shoot(self, f):
        if self.weapon_type == 'projectile':
            projectile = Projectile(x=self.x, y=self.y, target_px=self.target_p.x,
                target_py=self.target_p.y, damage=self.damage,
                speed=10, target_obj=self.target_p, img=self.w_img)
            projectiles.append(projectile)
        elif self.weapon_type == 'bomb':
            bomb = Bomb(x=self.x, y=self.y, target_px=self.target_p.x,
                        target_py=self.target_p.y, damage=self.damage,
                        speed=2)
            bombs.append(bomb)
        else:  # Zap
            self.target_p.hp -= self.damage
            Zap(self.x, self.y, self.target_p.x, self.target_p.y,
                self.game_inst.f)
            HitAnim(self.target_p.x, self.target_p.y)
        x_diff = self.target_p.x - self.x
        y_diff = self.target_p.y - self.y
        angle = -math.degrees(math.atan2(y_diff, x_diff)) + 90
        self.rotation = angle
        self.team_color.rotation = angle
        self.shadow.rotation = angle
        self.on_cooldown = True
        self.cooldown_started = f

    def stop(self):
        if not self.dest_reached:
            self.dest_x = self.target_x
            self.dest_y = self.target_y
        # Worker
        try:
            self.clear_task()
        except AttributeError:
            pass

    def kill(self, delay_del=False):
        self.pixel.delete()
        self.team_color.delete()
        self.shadow.delete()
        for attacker in self.attackers:
            attacker.has_target_p = False
        if not delay_del:
            if self.owner is self.game_inst.this_player:
                del our_units[our_units.index(self)]
            else:
                del enemy_units[enemy_units.index(self)]
        self.pos_dict[(self.target_x, self.target_y)] = None
        Explosion(self.x, self.y, 0.25)
        # Worker
        try:
            if self.to_build:
                self.owner.min_c += self.to_build.cost
                self.game_inst.update_min_c_label()
            del workers[workers.index(self)]
            self.zap_sprite.delete()
        except (AttributeError, ValueError):
            pass
        if self is sel:
            self.game_inst.build_loc_sel_phase = False
            self.game_inst.m_targeting_phase = False
            self.game_inst.targeting_phase = False
            self.game_inst.set_mouse_cursor(res.cursor)
        self.delete()


class Apocalypse(Unit):
    cost = 600
    build_time = 1
    icon = res.apocalypse_icon_img

    def __init__(self, game_inst, x, y, owner=None):
        if owner is None:
            owner = game_inst.this_player
        super().__init__(game_inst, owner, res.apocalypse_img,
                         res.apocalypse_team_color, res.apocalypse_icon_img,
                         flying=True,
                         vision_rad=6, hp=100, x=x, y=y, speed=1,
                         weapon_type='projectile', w_img=res.bomb_anim,
                         damage=100, cooldown=200,
                         attacks_ground=True, attacks_air=False,
                         shadow_sprite=res.apocalypse_shadow_img,
                         cbs=game_inst.basic_unit_c_bs)


class Centurion(Unit):
    cost = 400
    build_time = 1
    icon = res.centurion_icon_img

    def __init__(self, game_inst, x, y, owner=None):
        if owner is None:
            owner = game_inst.this_player
        super().__init__(game_inst, owner, res.centurion_img,
                         res.centurion_team_color, res.centurion_icon_img,
                         flying=False,
                         vision_rad=6, hp=100, x=x, y=y, speed=1,
                         weapon_type='projectile', w_img=res.laser_img,
                         damage=30, cooldown=120,
                         attacks_ground=True, attacks_air=False,
                         shadow_sprite=res.centurion_shadow_img,
                         cbs=game_inst.basic_unit_c_bs)


class Defiler(Unit):
    cost = 300
    build_time = 1
    icon = res.defiler_icon_img

    def __init__(self, game_inst, x, y, owner=None):
        if owner is None:
            owner = game_inst.this_player
        super().__init__(game_inst, owner, res.defiler_img,
                         res.defiler_team_color, res.defiler_icon_img,
                         flying=True,
                         vision_rad=6, hp=70, x=x, y=y, speed=3,
                         weapon_type='instant', w_img=res.laser_img, damage=1,
                         cooldown=10,
                         attacks_ground=True, attacks_air=True,
                         shadow_sprite=res.defiler_shadow_img,
                         cbs=game_inst.basic_unit_c_bs)


class Pioneer(Unit):
    cost = 50
    build_time = 1
    icon = res.pioneer_icon_img

    def __init__(self, game_inst, x, y, owner=None):
        if owner is None:
            owner = game_inst.this_player
        super().__init__(game_inst, owner, res.pioneer_img,
                         res.pioneer_team_color, res.pioneer_icon_img,
                         flying=False,
                         vision_rad=4, hp=10, x=x, y=y, speed=2,
                         weapon_type='none', w_img=res.zap_anim, damage=0,
                         cooldown=0,
                         attacks_ground=False, attacks_air=False,
                         shadow_sprite=res.pioneer_shadow_img,
                         cbs=game_inst.basic_unit_c_bs +
                                      [game_inst.armory_icon] +
                                      [game_inst.turret_icon] +
                                      [game_inst.mech_center_icon])
        workers.append(self)
        self.to_build = None
        self.mineral_to_gather = None
        self.task_x = None
        self.task_y = None
        self.is_gathering = False
        self.zap_sprite = Sprite(res.zap_anim, self.x, self.y,
                                 batch=weapons_batch)
        self.zap_sprite.visible = False

    def build(self):
        self.mineral_to_gather = None
        self.is_gathering = False
        self.zap_sprite.visible = False
        self.dest_reached = True
        g_pos_coord_d[(self.target_x, self.target_y)] = None
        g_pos_coord_d[(self.x, self.y)] = self
        if self.to_build is Armory:
            if not g_pos_coord_d[(self.task_x, self.task_y)]:
                Armory(self.game_inst, self.task_x, self.task_y)
            else:
                self.owner.min_c += Armory.cost
        elif self.to_build is Turret:
            if not g_pos_coord_d[(self.task_x, self.task_y)]:
                Turret(self.game_inst, self.task_x, self.task_y)
            else:
                self.owner.min_c += Turret.cost
        elif self.to_build is MechCenter:
            x = self.task_x - PS / 2
            y = self.task_y - PS / 2
            coords_to_check = [(x, y), (x + PS, y), (x + PS, y + PS),
                               (x, y + PS)]
            no_place = False
            for c in coords_to_check:
                if g_pos_coord_d[(c[0], c[1])]:
                    no_place = True
                    break
            if no_place is False:
                MechCenter(self.game_inst, self.task_x, self.task_y)
            else:
                self.owner.min_c += MechCenter.cost
        self.to_build = None

    def gather(self):
        self.rotate(self.mineral_to_gather.x, self.mineral_to_gather.y)
        self.is_gathering = True
        self.zap_sprite.x = self.x
        self.zap_sprite.y = self.y
        diff_x = self.task_x - self.x
        diff_y = self.task_y - self.y
        _dist = (diff_x ** 2 + diff_y ** 2) ** 0.5
        self.zap_sprite.scale_x = _dist / PS
        angle = math.atan2(diff_y, diff_x)  # Rad
        self.zap_sprite.rotation = -math.degrees(angle)
        self.zap_sprite.visible = True
        self.cycle_started = self.game_inst.f

    def clear_task(self):
        self.to_build = None
        self.mineral_to_gather = None
        self.task_x = None
        self.task_y = None
        self.is_gathering = False
        self.zap_sprite.visible = False


class Wyrm(Unit):
    cost = 150
    build_time = 1
    icon = res.wyrm_icon_img

    def __init__(self, game_inst, x, y, owner=None):
        if owner is None:
            owner = game_inst.this_player
        super().__init__(game_inst, owner, res.wyrm_img,
                         res.wyrm_team_color, res.wyrm_icon_img, flying=False,
                         vision_rad=3, hp=25, x=x, y=y, speed=3,
                         weapon_type='projectile', w_img=res.laser_img,
                         damage=5, cooldown=60,
                         attacks_ground=True, attacks_air=False,
                         shadow_sprite=res.wyrm_shadow_img,
                         cbs=game_inst.basic_unit_c_bs)



host_ip = "127.0.0.1"
port = 12345
s = socket.socket()
s.bind((host_ip, port))
s.listen()
cons_list = []
def new_con():
    """Accepts new connections"""
    counter = 1
    while True:
        exec(f"con{counter}, addr = s.accept()")
        exec(f"con{counter}.sendall(str(counter).encode())")
        exec(f"cons_list.append(con{counter}")
        counter += 1
new_con_thread = threading.Thread(target=new_con)
new_con_thread.start()

# Init


# Update
f = 0
if not paused:
    f += 1
    # Build units
    for struct in prod_structs:
        try:
            struct_spawn_unit(self, struct)
            if not struct.prod_q:
                struct.prod_complete = True
        except AttributeError:
            pass
    # AI
    # if self.f % 50 == 0:
    #     self.ai()
    # Units
    # Gathering resources
    for worker in workers:
        if worker.mineral_to_gather and worker.dest_reached:
            if not worker.is_gathering:
                try:
                    if is_melee_dist(worker, worker.task_x,
                                     worker.task_y):
                        # print("melee dist")
                        worker.gather()
                except TypeError:
                    worker.clear_task()
            else:
                worker.mineral_to_gather.hp -= 0.03
                owner = worker.owner
                owner.min_c += 0.03
                if owner is self.game_inst.this_player:
                    self.update_min_c_label()
    # Summon structures
    for worker in workers:
        if worker.to_build:
            if worker.to_build is MechCenter:
                if is_2_melee_dist(worker, worker.task_x,
                                   worker.task_y):
                    worker.build()
            else:
                if is_melee_dist(worker, worker.task_x, worker.task_y):
                    worker.build()
    # Finish summoning Guardian structures
    if self.f % 10 == 0:
        for struct in guardian_dummies:
            if struct.constr_f + struct.build_time <= self.f:
                struct.constr_complete()
                if sel is struct:
                    self.cbs_2_render = struct.cbs
                delayed_del = (struct, guardian_dummies)
        # Delayed del
        try:
            del delayed_del[1][delayed_del[1].index(
                delayed_del[0])]
        except:
            pass
    # Movement
    for unit in our_units + enemy_units:
        if not unit.dest_reached:
            # Do not jump
            if not unit.eta() <= 1:
                unit.update()
                if sel is unit:
                    self.sel_spt.x = unit.x
                    self.sel_spt.y = unit.y
            # Jump
            else:
                unit.x = unit.target_x
                unit.y = unit.target_y
                unit.coords = ((unit.x, unit.y),)
                unit.team_color.x = unit.target_x
                unit.team_color.y = unit.target_y
                if not unit.move_interd:
                    if sel is unit:
                        self.sel_spt.x = unit.x
                        self.sel_spt.y = unit.y
                    if not unit.flying:
                        unit.shadow.x = unit.target_x + 3
                        unit.shadow.y = unit.target_y - 3
                    else:
                        unit.shadow.x = unit.target_x + 10
                        unit.shadow.y = unit.target_y - 10
                    unit.pos_dict[
                        (unit.target_x, unit.target_y)] = unit
                    if unit.x == unit.dest_x and unit.y == \
                            unit.dest_y:
                        unit.dest_reached = True
                    else:
                        if unit.attack_moving:
                            if unit.owner is self.this_player:
                                if closest_enemy_2_att(unit,
                                                       enemy_units + enemy_structs):
                                    unit.dest_reached = True
                                    unit.attack_moving = False
                                else:
                                    unit.update_move()
                            else:
                                if closest_enemy_2_att(unit,
                                                       our_units + our_structs):
                                    unit.dest_reached = True
                                    unit.attack_moving = False
                                else:
                                    unit.update_move()
                        else:
                            unit.update_move()
                # Movement interrupted
                else:
                    if not unit.flying:
                        unit.shadow.x = unit.target_x + 3
                        unit.shadow.y = unit.target_y - 3
                        g_pos_coord_d[(unit.target_x, unit.target_y)] \
                            = unit
                    else:
                        unit.shadow.x = unit.target_x + 10
                        unit.shadow.y = unit.target_y - 10
                        a_pos_coord_d[(unit.target_x, unit.target_y)] \
                            = unit
                    unit.dest_reached = True
                    unit.move((unit.new_dest_x, unit.new_dest_y))
                    unit.move_interd = False
                if unit in our_units:
                    self.update_fow(unit.x, unit.y, unit.vision_rad)
        else:
            try:
                unit.to_build = None
                unit.task_x = None
                unit.task_y = None
            except AttributeError:
                pass
    # Shooting
    update_shooting(self, offensive_structs + our_units,
                    enemy_structs + enemy_units)
    update_shooting(self, enemy_units, our_structs + our_units)
    # Projectiles
    delayed_del = []
    for i, projectile in enumerate(projectiles):
        if not projectile.eta() <= 1:
            projectile.update()
        else:  # Hit!
            projectile.target_obj.hp -= projectile.damage
            HitAnim(projectile.x, projectile.y)
            delayed_del.append(projectile)
    for projectile in delayed_del:
        projectiles.remove(projectile)
        projectile.delete()
    # Zaps
    delayed_del = []
    for zap in zaps:
        if zap.f_started + ZAPS_LAST_F <= self.f:
            delayed_del.append(zap)
    for zap in delayed_del:
        zaps.remove(zap)
        zap.delete()
    # Bombs
    delayed_del = []
    for i, bomb in enumerate(bombs):
        if not bomb.eta() <= 1:
            bomb.update()
        else:  # Hit!
            try:
                g_pos_coord_d[(bomb.target_x, bomb.target_y)].hp -= \
                    bomb.damage
            # This is because of 2-block-wide
            # structures and the way enemy-finding workds
            except KeyError:
                try:
                    g_pos_coord_d[(bomb.target_x - 16,
                                   bomb.target_y - 16)].hp -= bomb.damage
                except AttributeError:
                    pass
            except AttributeError:  # For already dead? Errr
                pass
            hit_anim = HitAnim(bomb.x, bomb.y)
            hit_anim.color = (255, 200, 200)
            delayed_del.append(bomb)
    for bomb in delayed_del:
        bombs.remove(bomb)
        bomb.delete()
    # Destroying minerals
    minerals_to_del = []
    for mineral in minerals:
        if mineral.hp <= 0:
            mineral.kill()
            minerals_to_del.append(mineral)
    for mineral in minerals_to_del:
        minerals.remove(mineral)
    # Destroying targets
    for entity in our_structs + our_units + \
                  enemy_structs + enemy_units:
        if entity.hp <= 0:
            # if entity.owner.name == 'p2' and isinstance(entity, Pioneer):
            #     self.other_player.workers_count -= 1
            entity.kill()
            if entity is sel:
                sel = None

    if self.f % 10 == 0:
        # Update hp label
        try:
            sel.max_hp
            self.sel_hp.text = str(int(sel.hp)) + '/' + \
                               str(sel.max_hp)
        except AttributeError:
            try:
                self.sel_hp.text = str(int(sel.hp))
            except AttributeError:  # The entity is no more
                self.sel_icon.image = res.none_img
                self.sel_hp.text = ''
        # Reset txt_out
        if self.txt_out_upd_f:
            if self.f >= self.txt_out_upd_f + TXT_OUT_DECAY:
                self.txt_out.text = ''
                self.txt_out_upd_f = None
        # Production bar
        try:
            if not sel.prod_complete:
                self.prod_bar.scale_x = (self.f - sel.prod_start_f) \
                                        * 100 / sel.cur_max_prod_time + 1
            else:
                self.prod_bar_bg.visible = False
                self.prod_bar.visible = False
        except (AttributeError, TypeError):
            pass
if self.f % 50 == 0:
    if not enemy_structs:
        self.txt_out.text = "Victory"
        self.txt_out_upd_f = self.f
    elif not our_structs:
        self.txt_out.text = "Defeat"
        self.txt_out_upd_f = self.f
# Sending data to clients
data = ""
while True:
    start = time.time()
    for con in cons_list:
        con.sendall(data.encode())
    diff = time.time() - start
    if diff < 0.01:
        time.sleep(0.01 - diff)
