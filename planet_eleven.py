import math
import random
import sys
import numpy as np
import pickle

from pyglet.gl import *
from pyglet.window import key
from pyglet.window import mouse

from shadow import Shadow
import resources as res
from projectile import Projectile
from draw_dot import draw_dot
from constants_and_utilities import *

left_view_border = 0
bottom_view_border = 0

POS_COORDS = []
ground_pos_coords_dict = {}
air_pos_coords_dict = {}


def gen_pos_coords():
    """Generates a field of allowed positional coords. Declared as a function
    for resetting these."""
    global POS_COORDS, ground_pos_coords_dict, air_pos_coords_dict
    POS_COORDS = []
    for yi in range(1, POS_COORDS_N_ROWS + 1):
        for xi in range(1, POS_COORDS_N_COLUMNS + 1):
            POS_COORDS.append((xi * POS_SPACE - POS_SPACE / 2,
                               yi * POS_SPACE - POS_SPACE / 2))
    ground_pos_coords_dict = {}
    for _x, _y in POS_COORDS:
        ground_pos_coords_dict[(_x, _y)] = None
    air_pos_coords_dict = {}
    for _x, _y in POS_COORDS:
        air_pos_coords_dict[(_x, _y)] = None


gen_pos_coords()


def to_minimap(x, y):  # unit.x and unit.y
    """Converts global coords into minimap coords. For positioning minimap
    pixels."""
    x = x / POS_SPACE
    if not x.is_integer():
        x += 1
    x = MINIMAP_ZERO_COORDS[0] + x + left_view_border
    y = y / POS_SPACE
    if not y.is_integer():
        y += 1
    y = MINIMAP_ZERO_COORDS[1] + y + bottom_view_border
    return x, y


def mc(**kwargs):
    """Modifies coords for different viewports."""
    if len(kwargs) == 1:
        try:
            return kwargs['x'] + left_view_border
        except KeyError:
            return kwargs['y'] + bottom_view_border
    else:
        return kwargs['x'] + left_view_border, kwargs['y'] + bottom_view_border


def update_shooting(game_instance, our_entities, enemy_entities):
    for entity in our_entities:
        try:  # For shooting buildings
            entity.has_weapon
            entity.dest_reached
        except AttributeError:
            entity.has_weapon = True
            entity.dest_reached = True
        if entity.has_weapon and entity.dest_reached:
            if not entity.on_cooldown:
                if not entity.has_target_p:
                    closest_enemy = None
                    closest_enemy_dist = None
                    for enemy in enemy_entities:
                        try:
                            if not entity.attacks_air and enemy.flying:
                                continue
                            if not entity.attacks_ground and not enemy.flying:
                                continue
                        except AttributeError:
                            pass
                        dist_to_enemy = dist(enemy, entity)
                        if dist_to_enemy <= entity.shooting_radius:
                            if not closest_enemy:
                                closest_enemy = enemy
                                closest_enemy_dist = dist_to_enemy
                            else:
                                if dist_to_enemy < closest_enemy_dist:
                                    closest_enemy = enemy
                                    closest_enemy_dist = dist_to_enemy
                    if closest_enemy:
                        entity.has_target_p = True
                        entity.target_p = closest_enemy
                        entity.target_p_x = closest_enemy.x
                        entity.target_p_y = closest_enemy.y
                        entity.target_p.attackers.append(entity)
                else:
                    entity.shoot(game_instance.frame_count)
            else:
                if (game_instance.frame_count - entity.cooldown_started) % \
                        entity.cooldown == 0:
                    entity.on_cooldown = False


class Player:
    def __init__(self, name):
        self.mineral_count = 50000
        self.name = name


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Explosion(pyglet.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__(res.hit_anim, x, y, batch=explosions_batch)


class UI(pyglet.sprite.Sprite):
    def __init__(self, game_inst, img, x, y):
        super().__init__(img, x, y)
        self.org_x = x
        self.org_y = y
        game_inst.ui.append(self)


class Mineral(pyglet.sprite.Sprite):
    def __init__(self, outer_instance, x, y, amount=5000):
        super().__init__(img=res.mineral, x=x, y=y, batch=buildings_batch)
        self.outer_instance = outer_instance
        self.workers = []
        self.amount = amount
        minerals.append(self)
        ground_pos_coords_dict[(x, y)] = self

    def kill(self):
        for worker in self.workers:
            worker.clear_task()
            worker.stop_move()
        ground_pos_coords_dict[(self.x, self.y)] = None
        self.delete()


def order(game_instance, building, unit):
    """Orders units in buildings. Checks if you have enough minerals."""
    owner = building.owner
    if owner.mineral_count - unit.cost >= 0:
        owner.mineral_count -= unit.cost
        game_instance.min_count_label.text = str(
            int(game_instance.this_player.mineral_count))
        building.building_queue.append(unit)
        building.anim.visible = True
        if len(building.building_queue) == 1:
            building.building_start_time = game_instance.frame_count
    else:
        if owner == game_instance.this_player:
            print("Not enough minerals")


def building_spawn_unit(game_instance, building):
    if building.building_queue:
        unit = building.building_queue[0]
        if str(unit) == "<class '__main__.Defiler'>":
            building.current_building_time = Defiler.building_time
        elif str(unit) == "<class '__main__.Centurion'>":
            building.current_building_time = Centurion.building_time
        elif str(unit) == "<class '__main__.Vulture'>":
            building.current_building_time = Vulture.building_time
        elif str(unit) == "<class '__main__.Apocalypse'>":
            building.current_building_time = Apocalypse.building_time
        elif str(unit) == "<class '__main__.Pioneer'>":
            building.current_building_time = Pioneer.building_time
        if game_instance.frame_count - building.building_start_time == \
                building.current_building_time:
            if str(building.building_queue[0]) not in LIST_OF_FLYING:
                dict_to_check = ground_pos_coords_dict
            else:
                dict_to_check = air_pos_coords_dict
            # Searching for a place to build
            if building.width == POS_SPACE:
                x = building.x - POS_SPACE
                y = building.y - POS_SPACE
            else:
                x = building.x - POS_SPACE * 1.5
                y = building.y - POS_SPACE * 1.5
            org_x = x
            org_y = y
            place_found = False
            n = building.width // POS_SPACE + 2
            for i in range(n):
                x = org_x + POS_SPACE * i
                if dict_to_check[(x, y)] is None:
                    place_found = True
                    break
            for i in range(n):
                y = org_y + POS_SPACE * i
                if dict_to_check[(x, y)] is None:
                    place_found = True
                    break
            org_x = x
            for i in range(n):
                x = org_x - POS_SPACE * i
                if dict_to_check[(x, y)] is None:
                    place_found = True
                    break
            org_y = y
            for i in range(n):
                y = org_y - POS_SPACE * i
                if dict_to_check[(x, y)] is None:
                    place_found = True
                    break
            if place_found:
                unit = building.building_queue.pop(0)
                if str(unit) == "<class '__main__.Defiler'>":
                    unit = Defiler(game_instance, x=x, y=y,
                                   owner=building.owner)
                    unit.spawn()
                elif str(unit) == "<class '__main__.Centurion'>":
                    unit = Centurion(game_instance, x=x, y=y,
                                     owner=building.owner)
                    unit.spawn()
                elif str(unit) == "<class '__main__.Vulture'>":
                    unit = Vulture(game_instance, x=x, y=y,
                                   owner=building.owner)
                    unit.spawn()
                elif str(unit) == "<class '__main__.Apocalypse'>":
                    unit = Apocalypse(game_instance, x=x, y=y,
                                      owner=building.owner)
                    unit.spawn()
                elif str(unit) == "<class '__main__.Pioneer'>":
                    print(building.building_queue)
                    unit = Pioneer(game_instance, x=x, y=y,
                                   owner=building.owner)
                    unit.spawn()
                building.building_start_time += building.current_building_time
                if not building.building_queue:
                    building.anim.visible = False
                if not building.default_rp:
                    unit.move((building.rp_x, building.rp_y))
            else:
                building.building_start_time += 1
                print('No space')


class Building(pyglet.sprite.Sprite):
    """__init__ == spawn()"""
    def __init__(self, game_inst, owner, our_img, enemy_img, vision_radius,
                 hp, x, y):
        self.owner = owner
        if owner == game_inst.this_player:
            our_buildings.append(self)
            img = our_img
            minimap_pixel = res.mm_our_img
            game_inst.update_fow(x=x, y=y, radius=vision_radius)
        else:
            enemy_buildings.append(self)
            img = enemy_img
            minimap_pixel = res.mm_enemy_img
        super().__init__(img=img, x=x, y=y, batch=buildings_batch)
        self.game_inst = game_inst
        self.hp = hp
        if self.width / 32 % 2 == 1:
            d = self.width / POS_SPACE // 2 * POS_SPACE
            n = self.width // POS_SPACE
            width = 1
        else:
            n = int(self.width / POS_SPACE // 2)
            d = self.width / POS_SPACE // 2 * POS_SPACE - POS_SPACE / 2
            width = 2
        print('d =', d, 'n =', n, 'width =', width)
        x -= d
        y -= d
        self.blocks = [(x, y)]
        for _ in range(n):
            for _ in range(width):
                self.blocks.append((x, y))
                ground_pos_coords_dict[(x, y)] = self
                x += POS_SPACE
            x -= POS_SPACE
            for _ in range(width - 1):
                y += POS_SPACE
                self.blocks.append((x, y))
                ground_pos_coords_dict[(x, y)] = self
            for _ in range(width - 1):
                x -= POS_SPACE
                self.blocks.append((x, y))
                ground_pos_coords_dict[(x, y)] = self
            for _ in range(width - 2):
                self.blocks.append((x, y))
                ground_pos_coords_dict[(x, y)] = self
                y -= POS_SPACE
            width += 2
        if self.owner == game_inst.this_player:
            for block in self.blocks:
                game_inst.update_fow(x=block[0], y=block[1],
                                     radius=vision_radius)
        self.default_rp = True
        self.attackers = []

        pixel_minimap_coords = to_minimap(self.x, self.y)
        self.pixel = pyglet.sprite.Sprite(img=minimap_pixel,
                                          x=pixel_minimap_coords[0],
                                          y=pixel_minimap_coords[1],
                                          batch=minimap_pixels_batch)

    def kill(self, delay_del=False):
        global our_buildings, enemy_buildings
        for block in self.blocks:
            ground_pos_coords_dict[(block[0], block[1])] = None
        self.pixel.delete()
        if not delay_del:
            if self.owner.name == 'player1':
                del our_buildings[our_buildings.index(self)]
            else:
                del enemy_buildings[enemy_buildings.index(self)]
        for attacker in self.attackers:
            attacker.has_target_p = False
        try:
            self.anim.delete()
        except AttributeError:
            pass
        self.delete()


class Armory(Building):
    def __init__(self, game_inst, x, y, owner=None):
        if owner is None:
            owner = game_inst.this_player
        super().__init__(game_inst, owner, res.armory_img,
                         res.armory_enemy_img, vision_radius=2, hp=100, x=x,
                         y=y)


class ProductionBuilding(Building):
    def __init__(self, game_inst, owner, our_img, enemy_img, vision_radius, hp,
                 x, y):
        super().__init__(game_inst, owner, our_img, enemy_img, vision_radius,
                         hp, x, y)
        self.rp_x = x
        self.rp_y = y
        self.building_queue = []
        self.current_building_time = None
        self.building_complete = True
        self.building_start_time = 0


class BigBase(ProductionBuilding):
    def __init__(self, game_inst, x, y, owner=None):
        if owner is None:
            owner = game_inst.this_player
        super().__init__(game_inst, our_img=res.big_base_img,
                         enemy_img=res.big_base_enemy_img, x=x, y=y,
                         hp=1500, owner=owner, vision_radius=4)
        self.ctrl_buttons = [game_inst.defiler_b, game_inst.centurion_b,
                             game_inst.vulture_b, game_inst.apocalypse_b,
                             game_inst.pioneer_b]
        self.is_big = True
        if owner.name == 'player1':
            self.anim = pyglet.sprite.Sprite(img=res.anim, x=x, y=y,
                                             batch=ground_units_batch)
        else:
            self.anim = pyglet.sprite.Sprite(img=res.anim_enemy, x=x, y=y,
                                             batch=ground_units_batch)
        self.anim.visible = False


class AttackingBuilding(Building):
    def __init__(self, game_inst, owner, our_img, enemy_img, vision_radius, hp,
                 x, y, damage, cooldown):
        super().__init__(game_inst, owner, our_img, enemy_img, vision_radius,
                         hp, x, y)
        self.plasma_spt = pyglet.sprite.Sprite(res.plasma_anim, x, y,
                                               batch=ground_units_batch)
        self.damage = damage
        self.shooting_radius = vision_radius * 32
        self.target_x = None
        self.target_y = None
        self.cooldown = cooldown
        self.on_cooldown = False
        self.cooldown_started = None
        shooting_buildings.append(self)
        self.projectile_sprite = res.laser_img
        self.projectile_speed = 5
        self.has_target_p = False
        self.target_p = None
        self.target_p_x = None
        self.target_p_y = None

    def shoot(self, frame_count):
        global projectiles
        projectile = Projectile(self.x, self.y, self.target_p.x,
                                self.target_p.y, self.damage,
                                self.projectile_speed, self.target_p,
                                res.plasma_anim)
        x_diff = self.target_p.x - self.x
        y_diff = self.target_p.y - self.y
        self.on_cooldown = True
        self.cooldown_started = frame_count
        projectiles.append(projectile)

    def kill(self, delay_del=False):
        global ground_pos_coords_dict, our_buildings, enemy_buildings
        ground_pos_coords_dict[(self.x, self.y)] = None
        self.pixel.delete()
        if not delay_del:
            if self.owner.name == 'player1':
                del our_buildings[our_buildings.index(self)]
            else:
                del enemy_buildings[enemy_buildings.index(self)]
        del shooting_buildings[shooting_buildings.index(self)]
        self.plasma_spt.delete()
        self.delete()


class Turret(AttackingBuilding):
    def __init__(self, game_inst, x, y, owner=None):
        if owner is None:
            owner = game_inst.this_player
        super().__init__(game_inst, owner=owner, our_img=res.turret_base_img,
                         enemy_img=res.turret_base_img, vision_radius=5,
                         hp=100, x=x, y=y, damage=10, cooldown=60)


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
    print(acc_ends)
    acc_end_nodes = []
    for acc_end in acc_ends:
        print(acc_end)
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
        print("current_node.pos =", current_node.pos)
        for node in acc_end_nodes:
            print("node.pos =", node.pos)
            if node == current_node:
                print(1)
                path = []
                while current_node:
                    path.append(current_node.pos)
                    current_node = current_node.parent
                print(2)
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
    return int((c - POS_SPACE // 2) // POS_SPACE)


def find_path(start, end, is_flying):
    """Main path-finding function. Calls other PF functions."""
    print('start =', start, 'end =', end)
    # Check end neighbors
    if not is_flying:
        selected_dict = ground_pos_coords_dict
    else:
        selected_dict = air_pos_coords_dict
    if selected_dict[(end[0], end[1])] is None:
        acc_ends = [(convert_c_to_simple(end[0]), convert_c_to_simple(end[1]))]
    else:
        width = 3
        while True:
            acc_ends = []
            dx = dy = -POS_SPACE
            for i in range(width):
                coord = (end[0] + dx, end[1] + dy)
                try:
                    if selected_dict[coord] is None:
                        acc_ends.append((convert_c_to_simple(coord[0]),
                                         convert_c_to_simple(coord[1])))
                except KeyError:  # Out of the map borders
                    pass
                dx += POS_SPACE
            dx -= POS_SPACE
            for i in range(width - 1):
                dy += POS_SPACE
                coord = (end[0] + dx, end[1] + dy)
                try:
                    if selected_dict[coord] is None:
                        acc_ends.append((convert_c_to_simple(coord[0]),
                                         convert_c_to_simple(coord[1])))
                except KeyError:  # Out of the map borders
                    pass
            for i in range(width - 1):
                dx -= POS_SPACE
                coord = (end[0] + dx, end[1] + dy)
                try:
                    if selected_dict[coord] is None:
                        acc_ends.append((convert_c_to_simple(coord[0]),
                                         convert_c_to_simple(coord[1])))
                except KeyError:  # Out of the map borders
                    pass
            for i in range(width - 2):
                dy -= POS_SPACE
                coord = (end[0] + dx, end[1] + dy)
                try:
                    if selected_dict[coord] is None:
                        acc_ends.append((convert_c_to_simple(coord[0]),
                                         convert_c_to_simple(coord[1])))
                except KeyError:  # Out of the map borders
                    pass
            if acc_ends:
                break
            width += 1
    print("acc_ends =", acc_ends)
    start = convert_c_to_simple(start[0]), convert_c_to_simple(start[1])
    end = convert_c_to_simple(end[0]), convert_c_to_simple(end[1])
    print('start =', start, 'end =', end)
    map = convert_map(selected_dict)
    print('map converted to simple')
    map[start[1]][start[0]] = 0
    map[end[1]][end[0]] = 0
    path = astar(map, start, end, acc_ends)
    print('path =', path)
    if not path:
        return []
    converted_path = []
    for x, y in path:
        x = x * POS_SPACE + POS_SPACE // 2
        y = y * POS_SPACE + POS_SPACE // 2
        converted_path.append((x, y))
    print('converted_path =', converted_path)
    return converted_path


class Unit(pyglet.sprite.Sprite):
    def __init__(self, game_inst, owner, our_img, enemy_img, flying,
                 vision_radius, hp, x, y, speed, has_weapon, damage, cooldown,
                 attacks_ground, attacks_air, shadow_sprite, ctrl_buttons):
        self.outer_instance = game_inst
        self.owner = owner
        if owner.name == 'player1':
            img = our_img
            our_units.append(self)
        else:
            img = enemy_img
            enemy_units.append(self)
        self.flying = flying
        if not self.flying:
            self.pos_dict = ground_pos_coords_dict
            batch = ground_units_batch
        else:
            self.pos_dict = air_pos_coords_dict
            batch = air_batch
        super().__init__(img=img, x=x, y=y, batch=batch)
        self.vision_radius = vision_radius
        self.attacks_ground = attacks_ground
        self.attacks_air = attacks_air
        self.hp = hp
        self.x = x
        self.y = y
        self.speed = speed
        self.has_weapon = has_weapon
        self.damage = damage
        self.cooldown = cooldown
        self.attacks_ground = attacks_ground
        self.attacks_air = attacks_air
        self.shooting_radius = vision_radius * 32
        self.shadow_sprite = shadow_sprite
        self.ctrl_buttons = ctrl_buttons

        self.dest_reached = True
        self.move_interd = False
        self.target_x = None
        self.target_y = None
        self.dest_x = None
        self.dest_y = None
        self.velocity_x = 0
        self.velocity_y = 0
        self.has_target_p = False
        self.target_p = None
        self.target_p_x = None
        self.target_p_y = None
        self.on_cooldown = False
        self.cooldown_started = None
        self.attackers = []

    def spawn(self):
        """Creates a unit at it's predefined self.x and self.y. Does not move
        it to the rally point."""
        if not self.flying:
            ground_pos_coords_dict[(self.x, self.y)] = self
        else:
            air_pos_coords_dict[(self.x, self.y)] = self

        # Minimap pixel and fow
        pixel_minimap_coords = to_minimap(self.x, self.y)
        if self.owner.name == 'player1':
            pixel = res.mm_our_img
            self.outer_instance.update_fow(self.x, self.y, self.vision_radius)
        else:
            pixel = res.mm_enemy_img
        self.pixel = pyglet.sprite.Sprite(img=pixel, x=pixel_minimap_coords[0],
                                          y=pixel_minimap_coords[1],
                                          batch=minimap_pixels_batch)

        # Shadow
        if self.flying:
            self.shadow = Shadow(img=self.shadow_sprite, x=self.x + 10,
                                 y=self.y - 10)
            self.shadow.batch = air_shadows_batch
        else:
            self.shadow = Shadow(img=self.shadow_sprite, x=self.x + 3,
                                 y=self.y - 3)
            self.shadow.batch = ground_shadows_batch

    def update(self):
        """Updates position."""
        self.x, self.y = self.x + self.velocity_x, self.y + self.velocity_y

    def rotate(self, x, y):
        """Rotates a unit in the direction of his task(mining, building,
        etc.)"""
        diff_x = x - self.x
        diff_y = y - self.y
        angle = math.atan2(diff_y, diff_x)  # Rad
        self.rotation = -math.degrees(angle) + 90
        self.shadow.rotation = -math.degrees(angle) + 90

    def move(self, dest):
        """Called once by RMB or when a unit is created by a building with
        a non-default rally point."""
        # Not moving: same coords
        if self.x == dest[0] and self.y == dest[1]:
            self.dest_reached = True
            return

        if not self.flying:
            selected_dict = ground_pos_coords_dict
        else:
            selected_dict = air_pos_coords_dict
        # Not moving: melee distance and dest occupied
        if is_melee_dist(self, dest[0], dest[1]) and \
                selected_dict[(dest[0], dest[1])]:
            self.dest_reached = True
            return
        # Moving or just rotating
        self.dest_reached = False
        self.dest_x, self.dest_y = dest[0], dest[1]

        self.pfi = 1  # 0 creates a bug of rotating to math degree of 0
        # because the 0 element in path is the starting location
        self.path = find_path((self.x, self.y),
                              (self.dest_x, self.dest_y),
                              self.flying)
        try:
            target = self.path[self.pfi]
        except IndexError:
            self.dest_reached = True
            return
        if target:  # If we can reach there
            print('target =', target)
            self.target_x = target[0]
            self.target_y = target[1]
            self.pixel.x, self.pixel.y = to_minimap(self.target_x,
                                                    self.target_y)
        # Not moving
        else:
            self.dest_reached = True
            selected_dict[(self.x, self.y)] = self
            return
        diff_x = self.target_x - self.x
        diff_y = self.target_y - self.y
        angle = math.atan2(diff_y, diff_x)  # Rad
        self.rotation = -math.degrees(angle) + 90
        self.velocity_x = math.cos(angle) * self.speed
        self.velocity_y = math.sin(angle) * self.speed
        self.shadow.rotation = -math.degrees(angle) + 90
        self.shadow.velocity_x = math.cos(angle) * self.speed
        self.shadow.velocity_y = math.sin(angle) * self.speed
        selected_dict[(self.x, self.y)] = None
        selected_dict[(self.target_x, self.target_y)] = self

    def eta(self):
        """Estimated time of arrival to the target location (not
        dest)."""
        dist_to_target = ((self.target_x - self.x) ** 2 + (
                self.target_y - self.y) ** 2) ** 0.5
        return dist_to_target / self.speed

    def update_move(self):
        """Called by update to move to the next point."""
        self.pfi += 1
        if not self.flying:
            selected_dict = ground_pos_coords_dict
        else:
            selected_dict = air_pos_coords_dict
        diff_x = self.dest_x - self.x
        diff_y = self.dest_y - self.y
        angle = math.atan2(diff_y, diff_x)  # Rad
        d_angle = math.degrees(angle)
        self.rotation = -d_angle + 90
        self.shadow.rotation = -math.degrees(angle) + 90
        try:
            next_target = self.path[self.pfi]
        except IndexError:
            self.dest_reached = True
            return
        if selected_dict[
            (next_target[0], next_target[1])]:  # Obstruction detected
            self.move((self.dest_x, self.dest_y))
            return
        if next_target:  # Moving
            selected_dict[(self.x, self.y)] = None
            self.target_x = next_target[0]
            self.target_y = next_target[1]
            self.pixel.x, self.pixel.y = to_minimap(self.target_x,
                                                    self.target_y)
            selected_dict[(self.target_x, self.target_y)] = self
            diff_x = self.target_x - self.x
            diff_y = self.target_y - self.y
            angle = math.atan2(diff_y, diff_x)  # Rad
            d_angle = math.degrees(angle)
            self.rotation = -d_angle + 90
            self.velocity_x = math.cos(angle) * self.speed
            self.velocity_y = math.sin(angle) * self.speed
            self.shadow.rotation = -math.degrees(angle) + 90
            self.shadow.velocity_x = math.cos(angle) * self.speed
            self.shadow.velocity_y = math.sin(angle) * self.speed
        else:
            selected_dict[(self.x, self.y)] = self
            self.dest_reached = True

    def shoot(self, frame_count):
        global projectiles
        projectile = Projectile(x=self.x, y=self.y,
                                target_x=self.target_p.x,
                                target_y=self.target_p.y,
                                damage=self.damage,
                                speed=5,
                                target_obj=self.target_p)
        x_diff = self.target_p.x - self.x
        y_diff = self.target_p.y - self.y
        angle = -math.degrees(math.atan2(y_diff, x_diff)) + 90
        self.rotation = angle
        self.shadow.rotation = angle
        self.on_cooldown = True
        self.cooldown_started = frame_count
        projectiles.append(projectile)

    def stop_move(self):
        """Stops movement."""
        if not self.dest_reached:
            self.dest_x = self.target_x
            self.dest_y = self.target_y

    def kill(self, delay_del=False):
        self.pixel.delete()
        self.shadow.delete()
        for attacker in self.attackers:
            attacker.has_target_p = False
        if not delay_del:
            if self.owner.name == 'player1':
                del our_units[our_units.index(self)]
            else:
                del enemy_units[enemy_units.index(self)]
        if not self.flying:
            ground_pos_coords_dict[(self.x, self.y)] = None
        else:
            air_pos_coords_dict[(self.x, self.y)] = None
        self.delete()
        try:
            del workers[workers.index(self)]
        except ValueError:
            pass


class Defiler(Unit):
    cost = 250
    building_time = 10

    def __init__(self, game_inst, x, y, owner=None):
        if owner is None:
            owner = game_inst.this_player
        super().__init__(game_inst, owner, res.defiler_img,
                         res.defiler_enemy_img, flying=True, vision_radius=6,
                         hp=70, x=x, y=y, speed=6, has_weapon=True, damage=10,
                         cooldown=60, attacks_ground=True, attacks_air=True,
                         shadow_sprite=res.defiler_shadow_img,
                         ctrl_buttons=game_inst.basic_unit_c_bs)


class Centurion(Unit):
    cost = 400
    building_time = 10

    def __init__(self, game_inst, x, y, owner=None):
        if owner is None:
            owner = game_inst.this_player
        super().__init__(game_inst, owner, res.centurion_img,
                         res.centurion_enemy_img, flying=False,
                         vision_radius=6, hp=100, x=x, y=y, speed=1,
                         has_weapon=True, damage=10, cooldown=120,
                         attacks_ground=True, attacks_air=False,
                         shadow_sprite=res.centurion_shadow_img,
                         ctrl_buttons=game_inst.basic_unit_c_bs)


class Vulture(Unit):
    cost = 150
    building_time = 10

    def __init__(self, game_inst, x, y, owner=None):
        if owner is None:
            owner = game_inst.this_player
        super().__init__(game_inst, owner, res.vulture_img,
                         res.vulture_enemy_img, flying=False,
                         vision_radius=3, hp=25, x=x, y=y, speed=7,
                         has_weapon=True, damage=5, cooldown=60,
                         attacks_ground=True, attacks_air=False,
                         shadow_sprite=res.vulture_shadow_img,
                         ctrl_buttons=game_inst.basic_unit_c_bs)


class Apocalypse(Unit):
    cost = 250
    building_time = 300

    def __init__(self, game_inst, x, y, owner=None):
        if owner is None:
            owner = game_inst.this_player
        super().__init__(game_inst, owner, res.apocalypse_img,
                         res.apocalypse_enemy_img, flying=True,
                         vision_radius=6, hp=100, x=x, y=y, speed=4,
                         has_weapon=True, damage=30, cooldown=120,
                         attacks_ground=True, attacks_air=False,
                         shadow_sprite=res.apocalypse_shadow_img,
                         ctrl_buttons=game_inst.basic_unit_c_bs)


class Pioneer(Unit):
    cost = 50
    building_time = 10

    def __init__(self, game_inst, x, y, owner=None):
        if owner is None:
            owner = game_inst.this_player
        super().__init__(game_inst, owner, res.pioneer_img,
                         res.pioneer_enemy_img, flying=False,
                         vision_radius=2, hp=10, x=x, y=y, speed=4,
                         has_weapon=False, damage=0, cooldown=0,
                         attacks_ground=False, attacks_air=False,
                         shadow_sprite=res.pioneer_shadow_img,
                         ctrl_buttons=game_inst.basic_unit_c_bs +
                                      [game_inst.armory_b] +
                                      [game_inst.turret_b] +
                                      [game_inst.big_base_b])
        workers.append(self)
        self.to_build = None
        self.mineral_to_gather = None
        self.task_x = None
        self.task_y = None
        self.is_gathering = False

        s1 = pyglet.image.load('sprites/zap1.png')
        s1.anchor_y = 8
        s2 = pyglet.image.load('sprites/zap2.png')
        s2.anchor_y = 8
        s3 = pyglet.image.load('sprites/zap3.png')
        s3.anchor_y = 8
        sprites = [s1, s2, s3]
        anim = pyglet.image.Animation.from_image_sequence(sprites, 0.1, True)
        self.zap_sprite = pyglet.sprite.Sprite(anim, self.x, self.y,
                                               batch=zap_batch)

        self.zap_sprite.visible = False

    def build(self):
        self.mineral_to_gather = None
        self.is_gathering = False
        self.zap_sprite.visible = False
        self.dest_reached = True
        ground_pos_coords_dict[(self.x, self.y)] = self
        if self.to_build == "armory":
            Armory(self.outer_instance, self.task_x, self.task_y)
        elif self.to_build == "turret":
            Turret(self.outer_instance, self.task_x, self.task_y)
        self.to_build = None

    def gather(self):
        self.rotate(self.mineral_to_gather.x, self.mineral_to_gather.y)
        self.is_gathering = True
        self.zap_sprite.x = self.x
        self.zap_sprite.y = self.y
        diff_x = self.task_x - self.x
        diff_y = self.task_y - self.y
        dist = (diff_x ** 2 + diff_y ** 2) ** 0.5
        self.zap_sprite.scale_x = dist / POS_SPACE
        angle = math.atan2(diff_y, diff_x)  # Rad
        self.zap_sprite.rotation = -math.degrees(angle)
        self.zap_sprite.visible = True
        self.cycle_started = self.outer_instance.frame_count

    def clear_task(self):
        self.to_build = None
        self.mineral_to_gather = None
        self.task_x = None
        self.task_y = None
        self.is_gathering = False
        self.zap_sprite.visible = False


class PlanetEleven(pyglet.window.Window):
    def __init__(self, width, height, title):
        conf = Config(sample_buffers=1,
                      samples=4,
                      depth_size=16,
                      double_buffer=True)
        super().__init__(width, height, title, config=conf, fullscreen=False)
        self.set_mouse_cursor(res.cursor)
        self.show_fps = True
        self.fps_display = pyglet.window.FPSDisplay(window=self)
        self.ui = []

    def setup(self):
        global selected
        self.paused = False
        self.frame_count = 0
        self.this_player = Player("player1")
        self.computer = Player("computer1")
        self.computer.workers_count = 0
        self.dx = 0
        self.dy = 0
        self.minimap_drugging = False
        self.build_loc_sel_phase = False

        self.terrain = pyglet.sprite.Sprite(img=res.terrain_img, x=0, y=0)
        self.cp_spt = UI(self, res.cp_img, SCREEN_W, 0)
        self.menu_b = UI(self, res.menu_img, cp_c_x, SCREEN_H - 30)
        self.sel_frame_cp = UI(self, res.sel_frame_img, cp_c_x,
                               SCREEN_H - 90)
        self.cp_b_bg = UI(self, res.cp_buttons_bg_img, cp_c_x, cp_c_y)
        self.mm_textured_bg = UI(self, res.mm_textured_bg_img,
                                 MINIMAP_ZERO_COORDS[0],
                                 MINIMAP_ZERO_COORDS[1])
        self.mm_cam_frame_spt = UI(self, res.mm_cam_frame_img,
                                   MINIMAP_ZERO_COORDS[0] - 1,
                                   MINIMAP_ZERO_COORDS[1] - 1)
        self.mm_fow_img = pyglet.image.load('sprites/mm_fow.png')
        self.mm_fow_ImageData = self.mm_fow_img.get_image_data()
        self.npa = np.fromstring(self.mm_fow_ImageData.get_data(
            'RGBA', self.mm_fow_ImageData.width * 4), dtype=np.uint8)
        self.npa = self.npa.reshape((102, 102, 4))
        self.min_count_label = pyglet.text.Label(
            str(self.this_player.mineral_count), x=SCREEN_W - 200,
            y=SCREEN_H - 30)

        # Buttons
        self.armory_b = UI(self, res.armory_img, CTRL_B_COORDS[3][0],
                           CTRL_B_COORDS[3][1])
        self.turret_b = UI(self, res.turret_b_img, CTRL_B_COORDS[4][0],
                           CTRL_B_COORDS[4][1])
        self.big_base_b = UI(self, res.big_base_icon_img,
                             CTRL_B_COORDS[5][0], CTRL_B_COORDS[5][1])
        self.move_b = UI(self, res.move_img, CTRL_B_COORDS[0][0],
                         CTRL_B_COORDS[0][1])
        self.stop_b = UI(self, res.stop_img, CTRL_B_COORDS[1][0],
                         CTRL_B_COORDS[1][1])
        self.attack_b = UI(self, res.attack_img, CTRL_B_COORDS[2][0],
                           CTRL_B_COORDS[2][1])
        self.defiler_b = UI(self, res.defiler_img, CTRL_B_COORDS[0][0],
                            CTRL_B_COORDS[0][1])
        self.centurion_b = UI(self, res.centurion_img,
                              CTRL_B_COORDS[1][0], CTRL_B_COORDS[1][1])
        self.vulture_b = UI(self, res.vulture_img, CTRL_B_COORDS[2][0],
                            CTRL_B_COORDS[2][1])
        self.apocalypse_b = UI(self, res.apocalypse_img,
                               CTRL_B_COORDS[3][0], CTRL_B_COORDS[3][1])
        self.pioneer_b = UI(self, res.pioneer_img, CTRL_B_COORDS[4][0],
                            CTRL_B_COORDS[4][1])

        # Spawn buildings and minerals
        Mineral(self, POS_SPACE / 2 + POS_SPACE * 4,
                POS_SPACE / 2 + POS_SPACE * 7)
        Mineral(self, POS_SPACE / 2 + POS_SPACE * 4,
                POS_SPACE / 2 + POS_SPACE * 8, amount=1)
        self.our_1st_base = BigBase(self, POS_SPACE * 7, POS_SPACE * 8)
        selected = self.our_1st_base
        BigBase(self, POS_SPACE * 5, POS_SPACE * 6, owner=self.computer)
        BigBase(self, POS_SPACE * 13, POS_SPACE * 13, owner=self.computer)

        self.sel_spt = pyglet.sprite.Sprite(img=res.sel_img,
                                            x=self.our_1st_base.x,
                                            y=self.our_1st_base.y)
        self.sel_big_spt = pyglet.sprite.Sprite(img=res.sel_big_img,
                                                x=self.our_1st_base.x,
                                                y=self.our_1st_base.y)
        self.rp_spt = pyglet.sprite.Sprite(img=res.rp_img,
                                           x=self.our_1st_base.rp_x,
                                           y=self.our_1st_base.rp_y)

        self.basic_unit_c_bs = [self.move_b, self.stop_b, self.attack_b]
        self.c_bs_to_render = self.our_1st_base.ctrl_buttons
        self.armory_building_spt = pyglet.sprite.Sprite(img=res.armory_img,
                                                        x=-100, y=-100)
        self.armory_building_spt.color = (0, 255, 0)
        self.turret_building_spt = pyglet.sprite.Sprite(
            img=res.turret_b_img, x=-100, y=-100)
        self.turret_building_spt.color = (0, 255, 0)

        # Spawn units
        Vulture(self, POS_SPACE / 2 + POS_SPACE * 3,
                POS_SPACE / 2 + POS_SPACE * 10, self.computer).spawn()

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
        glOrtho(left_view_border, left_view_border + SCREEN_W,
                bottom_view_border,
                bottom_view_border + SCREEN_H, 1, -1)

        '''for x, y in POS_COORDS:
            draw_dot(x, y, 2)'''

        self.terrain.draw()
        ground_shadows_batch.draw()
        zap_batch.draw()
        buildings_batch.draw()
        ground_units_batch.draw()
        explosions_batch.draw()
        air_shadows_batch.draw()
        air_batch.draw()
        if selected:
            try:
                selected.is_big
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
            if self.to_build == "armory":
                self.armory_building_spt.draw()
            elif self.to_build == "turret":
                self.turret_building_spt.draw()
        self.cp_spt.draw()
        self.menu_b.draw()
        self.sel_frame_cp.draw()
        self.cp_b_bg.draw()
        self.mm_textured_bg.draw()
        minimap_pixels_batch.draw()

        if self.c_bs_to_render:
            for button in self.c_bs_to_render:
                button.draw()
            if selected in our_buildings and selected \
                    not in shooting_buildings:
                self.rp_spt.draw()

        self.fow_texture.width = 102
        self.fow_texture.height = 102
        self.fow_texture.blit(minimap_fow_x, minimap_fow_y)

        self.mm_cam_frame_spt.draw()

        for projectile in projectiles:
            projectile.draw()

        self.min_count_label.draw()
        if self.show_fps:
            self.fps_display.draw()

        # Remove default modelview matrix
        glPopMatrix()

    def update(self, delta_time):
        global selected
        if not self.paused:
            self.frame_count += 1
            # Build units
            for building in our_buildings + enemy_buildings:
                try:
                    building_spawn_unit(self, building)
                except AttributeError:
                    pass
            # AI ordering units
            # if self.frame_count % 60 == 0:
            #     for building in enemy_buildings:
            #         if self.computer.workers_count < 8:
            #             order(self, building, Pioneer)
            #             self.computer.workers_count += 1
            # Units
            # Gathering resources
            for worker in workers:
                if worker.mineral_to_gather and worker.dest_reached:
                    if not worker.is_gathering:
                        if is_melee_dist(worker, worker.task_x,
                                         worker.task_y):
                            print("melee dist")
                            worker.gather()
                    else:
                        worker.mineral_to_gather.amount -= 0.03
                        owner = worker.owner
                        owner.mineral_count += 0.03
                        if owner.name == 'player1':
                            self.min_count_label.text = str(
                                int(owner.mineral_count))
            # AI gathering resources
            # if self.frame_count % 120 == 0:
            #     try:
            #         closest_min = minerals[0]
            #         for worker in workers:
            #             if all((not worker.is_gathering,
            #                     worker.dest_reached,
            #                     worker.owner.name == 'computer1')):
            #                 dist_2_closest_min = dist(closest_min,
            #                                           worker)
            #                 for mineral in minerals[1:]:
            #                     dist_2_min = dist(mineral, worker)
            #                     if dist_2_min < dist_2_closest_min:
            #                         closest_min = mineral
            #                         dist_2_closest_min = dist_2_min
            #                 worker.move((closest_min.x, closest_min.y))
            #                 worker.clear_task()
            #                 print('go gather, lazy worker!')
            #                 worker.mineral_to_gather = closest_min
            #                 worker.task_x = closest_min.x
            #                 worker.task_y = closest_min.y
            #                 closest_min.workers.append(worker)
            #     except IndexError:
            #         pass

            # Build buildings
            for worker in workers:
                if worker.to_build:
                    if is_melee_dist(worker, worker.task_x, worker.task_y):
                        worker.build()
            # Movement
            for unit in our_units + enemy_units:
                # Do not jump
                if not unit.dest_reached:
                    if not unit.eta() <= 1:
                        unit.update()
                        unit.shadow.update()
                        if selected == unit:
                            self.sel_spt.x = unit.x
                            self.sel_spt.y = unit.y
                    # Jump
                    else:
                        if not unit.move_interd:
                            unit.x = unit.target_x
                            unit.y = unit.target_y
                            if selected == unit:
                                self.sel_spt.x = unit.x
                                self.sel_spt.y = unit.y
                            if not unit.flying:
                                unit.shadow.x = unit.target_x + 3
                                unit.shadow.y = unit.target_y - 3
                                ground_pos_coords_dict[
                                    (unit.target_x, unit.target_y)] = unit
                            else:
                                unit.shadow.x = unit.target_x + 10
                                unit.shadow.y = unit.target_y - 10
                                air_pos_coords_dict[
                                    (unit.target_x, unit.target_y)] = unit
                            if unit.x == unit.dest_x and unit.y == \
                                    unit.dest_y:
                                unit.dest_reached = True
                            else:
                                unit.update_move()
                        # Movement interrupted
                        else:
                            unit.x = unit.target_x
                            unit.y = unit.target_y
                            if not unit.flying:
                                unit.shadow.x = unit.target_x + 3
                                unit.shadow.y = unit.target_y - 3
                                ground_pos_coords_dict[
                                    (unit.target_x, unit.target_y)] = unit
                            else:
                                unit.shadow.x = unit.target_x + 10
                                unit.shadow.y = unit.target_y - 10
                                air_pos_coords_dict[
                                    (unit.target_x, unit.target_y)] = unit
                            unit.dest_reached = True
                            unit.move((unit.new_dest_x, unit.new_dest_y))
                            unit.move_interd = False
                        self.update_fow(unit.x, unit.y, unit.vision_radius)
                else:
                    try:
                        unit.to_build = None
                        unit.task_x = None
                        unit.task_y = None
                    except AttributeError:
                        pass
            # Shooting
            update_shooting(self, shooting_buildings + our_units,
                            enemy_buildings + enemy_units)
            update_shooting(self, enemy_units,
                            our_buildings + our_units)
            # Projectiles
            for i, projectile in enumerate(projectiles):
                if not projectile.eta() <= 1:
                    projectile.update()
                else:  # Hit!
                    projectile.target_obj.hp -= projectile.damage
                    Explosion(projectile.x, projectile.y)
                    projectile.delete()
                    del projectiles[i]
            # Destroying minerals
            minerals_to_del = []
            for mineral in minerals:
                if mineral.amount <= 0:
                    mineral.kill()
                    minerals_to_del.append(mineral)
            for mineral in minerals_to_del:
                minerals.remove(mineral)
            # Destroying targets
            for entity in our_buildings + our_units + \
                          enemy_buildings + enemy_units:
                if entity.hp <= 0:
                    if entity.owner.name == 'computer1' and \
                            isinstance(entity, Pioneer):
                        self.computer.workers_count -= 1
                    entity.kill()
                    if entity == selected:
                        selected = None

    def on_key_press(self, symbol, modifiers):
        """Called whenever a key is pressed. """
        global selected, left_view_border, bottom_view_border
        if symbol == key.F:
            if self.fullscreen:
                self.set_mouse_cursor(res.cursor)
                self.set_fullscreen(False)
            else:
                self.set_mouse_cursor(res.cursor_fullscreen)
                self.set_fullscreen(True)
        if not self.paused:
            if symbol == key.S:
                try:
                    selected.stop_move()
                except AttributeError:
                    pass
            elif symbol == key.F1:
                if self.show_fps == False:
                    self.show_fps = True
                else:
                    self.show_fps = False
            elif symbol == key.F2:
                self.save()
            elif symbol == key.F3:
                self.load()
            elif symbol == key.LEFT:
                left_view_border -= POS_SPACE
                self.update_viewport()
            elif symbol == key.RIGHT:
                left_view_border += POS_SPACE
                self.update_viewport()
            elif symbol == key.DOWN:
                bottom_view_border -= POS_SPACE
                self.update_viewport()
            elif symbol == key.UP:
                bottom_view_border += POS_SPACE
                self.update_viewport()
            elif symbol == key.Q:
                print('POS_COORDS =', POS_COORDS)
            elif symbol == key.W:
                print('convert_map() =', convert_map())
            elif symbol == key.E:
                print('find_path()')
                find_path()
            elif symbol == key.R:
                for y in convert_map():
                    for x in y:
                        if x == 1:
                            print(1)
            elif symbol == key.G:
                print(selected)
            elif symbol == key.H:
                for _key, _value in ground_pos_coords_dict.items():
                    if _value:
                        print('key =', _key, 'value =', _value)
            elif symbol == key.J:
                print(workers)
            elif symbol == key.K:
                print(our_units)
            # elif symbol == key.Z:
            #     i = 0
            #     for _key, value in ground_pos_coords_dict.items():
            #         if i % 1 == 0:
            #             if value is None:
            #                 unit = Vulture(self, _key[0], _key[1])
            #                 unit.spawn()
            #         i += 1
            elif symbol == key.X:
                coords_to_delete = []
                yi = bottom_view_border + POS_SPACE // 2
                for y in range(yi, yi + 12 * POS_SPACE, POS_SPACE):
                    xi = left_view_border + POS_SPACE // 2
                    for x in range(xi, xi + 17 * POS_SPACE, POS_SPACE):
                        coords_to_delete.append((x, y))
                for coord in coords_to_delete:
                    unit_id = ground_pos_coords_dict[coord]
                    ground_pos_coords_dict[coord] = None
                    for unit in our_units:
                        if unit_id == id(unit):
                            unit.kill()
            elif symbol == key.DELETE:
                if selected in our_units:
                    selected.kill()
                    if selected.flying:
                        air_pos_coords_dict[(self.sel_spt.x,
                                             self.sel_spt.y)] = None
                    else:
                        ground_pos_coords_dict[(self.sel_spt.x,
                            self.sel_spt.y)] = None
                    selected = None
                elif selected in our_buildings:
                    selected.kill()
                    selected = None
            elif symbol == key.SPACE:
                self.paused = True
            elif symbol == key.ESCAPE:
                sys.exit()
        # Paused
        else:
            if symbol == key.SPACE:
                self.paused = False

    def on_mouse_press(self, x, y, button, modifiers):
        global selected, our_units, left_view_border, bottom_view_border
        if not self.paused:
            if self.fullscreen:
                x /= 2
                y /= 2
            if not self.build_loc_sel_phase:
                # Game field
                if x < SCREEN_W - 139:
                    x, y = round_coords(x, y)
                    x, y = mc(x=x, y=y)
                    print('\nglobal click coords:', x, y)
                    if button == mouse.LEFT:
                        # Selection
                        to_be_selected = air_pos_coords_dict[(x, y)]
                        if to_be_selected:
                            selected = to_be_selected
                            self.sel_spt.x = x
                            self.sel_spt.y = y
                        else:
                            to_be_selected = ground_pos_coords_dict[(x, y)]
                            if to_be_selected:
                                try:
                                    to_be_selected.is_big
                                    self.sel_big_spt.x = \
                                        to_be_selected.x
                                    self.sel_big_spt.y = \
                                        to_be_selected.y
                                except AttributeError:
                                    self.sel_spt.x = x
                                    self.sel_spt.y = y
                                selected = to_be_selected
                        if isinstance(selected, Mineral):
                            self.c_bs_to_render = None
                        else:
                            if selected.owner.name == 'player1':
                                try:
                                    self.c_bs_to_render = \
                                        selected.ctrl_buttons
                                except AttributeError:
                                    self.c_bs_to_render = None
                            else:
                                self.c_bs_to_render = None
                            print('SELECTED CLASS =', type(selected))
                    elif button == mouse.RIGHT:
                        # Rally point
                        if selected in our_buildings:
                            if ground_pos_coords_dict[x, y] != selected:
                                selected.rp_x = x
                                selected.rp_y = y
                                selected.default_rp = False
                                self.rp_spt.x = x
                                self.rp_spt.y = y
                            else:
                                selected.default_rp = True
                                self.rp_spt.x = selected.x
                                self.rp_spt.y = selected.y
                            print('Rally set to ({}, {})'.format(x, y))
                        # A unit is selected
                        else:
                            if selected in our_units:
                                if selected.dest_reached:
                                    selected.move((x, y))
                                # Movement interruption
                                else:
                                    selected.move_interd = True
                                    selected.new_dest_x = x
                                    selected.new_dest_y = y
                                selected.has_target_p = False
                                if str(type(selected)) == \
                                        "<class '__main__.Pioneer'>":
                                    selected.clear_task()
                                    obj = ground_pos_coords_dict[(x, y)]
                                    if str(type(obj)) == \
                                            "<class '__main__.Mineral'>":
                                        print('go gather, lazy worker!')
                                        selected.mineral_to_gather = obj
                                        selected.task_x = obj.x
                                        selected.task_y = obj.y
                                        obj.workers.append(selected)
                # Minimap
                elif MINIMAP_ZERO_COORDS[0] <= x <= MINIMAP_ZERO_COORDS[
                    0] + 100 and \
                        MINIMAP_ZERO_COORDS[1] <= y <= MINIMAP_ZERO_COORDS[
                    1] + 100:
                    if button == mouse.LEFT:
                        x -= 19 / 2
                        y -= 14 / 2
                        left_view_border = (x - MINIMAP_ZERO_COORDS[
                            0]) * POS_SPACE
                        bottom_view_border = (y - MINIMAP_ZERO_COORDS[
                            1]) * POS_SPACE
                        self.update_viewport()
                    elif button == mouse.RIGHT:
                        x = (x - MINIMAP_ZERO_COORDS[0]) * POS_SPACE
                        y = (y - MINIMAP_ZERO_COORDS[1]) * POS_SPACE
                        x, y = round_coords(x, y)
                        # A unit is selected
                        unit_found = False
                        for unit in our_units:
                            if unit == selected:
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
                            if selected in our_buildings:
                                selected.rp_x = x
                                selected.rp_y = y
                                self.rp_spt.x = x
                                self.rp_spt.y = y
                                # print('Rally set to ({}, {})'.format(x, y))
                # Control panel other
                else:
                    x, y = mc(x=x, y=y)
                    # print('x =', x, 'y =', y)
                    w = self.menu_b.width
                    h = self.menu_b.height
                    if self.menu_b.x - w // 2 <= x <= \
                            self.menu_b.x + w // 2 and \
                            self.menu_b.y - h // 2 <= y <= \
                            self.menu_b.y + h // 2:
                        pass
                    # Build units
                    if selected in our_buildings:
                        # Create defiler
                        if self.defiler_b.x - 16 <= x <= \
                                self.defiler_b.x + 16 and \
                                self.defiler_b.y - 16 <= y <= \
                                self.defiler_b.y + 16:
                            order(self, selected, Defiler)
                        # Create centurion
                        elif self.centurion_b.x - 16 <= x <= \
                                self.centurion_b.x + 16 and \
                                self.centurion_b.y - 16 <= y <= \
                                self.centurion_b.y + 16:
                            order(self, selected, Centurion)
                        # Create vulture
                        elif self.vulture_b.x - 16 <= x <= \
                                self.vulture_b.x + 16 and \
                                self.vulture_b.y - 16 <= y <= \
                                self.vulture_b.y + 16:
                            order(self, selected, Vulture)
                        # Create apocalypse
                        elif self.apocalypse_b.x - 16 <= x <= \
                                self.apocalypse_b.x + 16 and \
                                self.apocalypse_b.y - 16 <= y <= \
                                self.apocalypse_b.y + 16:
                            order(self, selected, Apocalypse)
                        # Create pioneer
                        elif self.pioneer_b.x - 16 <= x <= \
                                self.pioneer_b.x + 16 and \
                                self.pioneer_b.y - 16 <= y <= \
                                self.pioneer_b.y + 16:
                            order(self, selected, Pioneer)
                    elif selected in our_units:
                        # Move
                        # Stop
                        if self.stop_b.x - 16 <= x <= \
                                self.stop_b.x + 16 and \
                                self.stop_b.y - 16 <= y <= \
                                self.stop_b.y + 16:
                            selected.stop_move()
                        # Attack
                        # Build
                        if str(type(selected)) == "<class '__main__.Pioneer'>":
                            if self.armory_b.x - 16 <= x <= \
                                    self.armory_b.x + 16 and \
                                    self.armory_b.y - 16 <= y <= \
                                    self.armory_b.y + 16:
                                self.armory_building_spt.color = (0, 255, 0)
                                self.build_loc_sel_phase = True
                                self.to_build = "armory"
                            elif self.turret_b.x - 16 <= x <= \
                                    self.turret_b.x + 16 and \
                                    self.turret_b.y - 16 <= y <= \
                                    self.turret_b.y + 16:
                                self.turret_building_spt.color = (0, 255, 0)
                                self.build_loc_sel_phase = True
                                self.to_build = "turret"
            # Building location selection
            else:
                # Game field
                if x < SCREEN_W - 139:
                    x, y = round_coords(x, y)
                    x, y = mc(x=x, y=y)
                    if button == mouse.LEFT:
                        mx = int((x - 16) / 32) + 1
                        my = int((y - 16) / 32) + 1
                        if not ground_pos_coords_dict[x, y] \
                                and self.npa[my, mx, 3] == 0:
                            selected.to_build = self.to_build
                            selected.task_x = x
                            selected.task_y = y
                            selected.move((x, y))
                            self.build_loc_sel_phase = False
                    elif button == mouse.RIGHT:
                        self.build_loc_sel_phase = False

    def on_mouse_motion(self, x, y, dx, dy):
        if not self.paused:
            if self.build_loc_sel_phase:
                if self.fullscreen:
                    x /= 2
                    y /= 2
                x, y = round_coords(x, y)
                if self.to_build == "armory":
                    self.armory_building_spt.x = x + left_view_border
                    self.armory_building_spt.y = y + bottom_view_border
                    x, y = mc(x=x, y=y)
                    x = int((x - 16) / 32) + 1
                    y = int((y - 16) / 32) + 1
                    if ground_pos_coords_dict[self.armory_building_spt.x,
                                              self.armory_building_spt.y] or \
                            self.npa[y, x, 3] != 0:
                        self.armory_building_spt.color = (255, 0, 0)
                    else:
                        self.armory_building_spt.color = (0, 255, 0)
                elif self.to_build == "turret":
                    self.turret_building_spt.x = x + left_view_border
                    self.turret_building_spt.y = y + bottom_view_border
                    x, y = mc(x=x, y=y)
                    x = int((x - 16) / 32) + 1
                    y = int((y - 16) / 32) + 1
                    if ground_pos_coords_dict[self.turret_building_spt.x,
                                              self.turret_building_spt.y] \
                            or self.npa[y, x, 3] != 0:
                        self.turret_building_spt.color = (255, 0, 0)
                    else:
                        self.turret_building_spt.color = (0, 255, 0)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        global left_view_border, bottom_view_border
        if not self.paused:
            if self.fullscreen:
                x /= 2
                y /= 2
                dx /= 2
                dy /= 2
            if not self.minimap_drugging:
                # Game field
                if x < SCREEN_W - 139 and buttons == 2:
                    self.dx += dx * MMB_PAN_SPEED
                    self.dy += dy * MMB_PAN_SPEED
                    if abs(self.dx) >= POS_SPACE:
                        if self.dx < 0:
                            left_view_border += POS_SPACE
                            self.update_viewport()
                            self.dx -= self.dx
                        else:
                            left_view_border -= POS_SPACE
                            self.update_viewport()
                            self.dx -= self.dx
                    if abs(self.dy) >= POS_SPACE:
                        if self.dy < 0:
                            bottom_view_border += POS_SPACE
                            self.update_viewport()
                            self.dy -= self.dy
                        else:
                            bottom_view_border -= POS_SPACE
                            self.update_viewport()
                            self.dy -= self.dy
                # Minimap
                elif MINIMAP_ZERO_COORDS[0] <= x <= MINIMAP_ZERO_COORDS[
                    0] + 100 and \
                        MINIMAP_ZERO_COORDS[1] <= y <= MINIMAP_ZERO_COORDS[
                    1] + 100 and buttons in [1, 2]:
                    self.minimap_drugging = True
                    left_view_border += dx * POS_SPACE
                    bottom_view_border += dy * POS_SPACE
                    self.update_viewport()
            # Minimap dragging
            else:
                # if x < MINIMAP_ZERO_COORDS[0]:
                #     x = MINIMAP_ZERO_COORDS[0]
                # elif x > MINIMAP_ZERO_COORDS[0] + 100:
                #     x = MINIMAP_ZERO_COORDS[0] + 100
                # if y < MINIMAP_ZERO_COORDS[1]:
                #     y = MINIMAP_ZERO_COORDS[1]
                # elif y > MINIMAP_ZERO_COORDS[1] + 100:
                #     y = MINIMAP_ZERO_COORDS[1] + 100
                left_view_border += dx * POS_SPACE
                bottom_view_border += dy * POS_SPACE
                self.update_viewport()

    def on_mouse_release(self, x, y, button, modifiers):
        self.minimap_drugging = False

    # def on_mouse_motion(self, x, y, dx, dy):
    #     global left_view_border, bottom_view_border
    #     if TOP_SCREEN_SCROLL_ZONE[0] <= y <= TOP_SCREEN_SCROLL_ZONE[1]:
    #         # print('sdfsdfs')
    #         bottom_view_border += POS_SPACE
    #         self.update_viewport()

    def update_viewport(self):
        global left_view_border, bottom_view_border, minimap_fow_x, \
            minimap_fow_y

        # Viewport limits
        a = POS_COORDS_N_COLUMNS * POS_SPACE - SCREEN_W // POS_SPACE \
            * POS_SPACE + POS_SPACE * 4
        if left_view_border < 0:
            left_view_border = 0
        elif left_view_border > a:
            left_view_border = a
        if bottom_view_border < 0:
            bottom_view_border = 0
        elif bottom_view_border > POS_COORDS_N_ROWS * POS_SPACE \
                - SCREEN_H:
            bottom_view_border = POS_COORDS_N_ROWS * POS_SPACE - SCREEN_H

        self.mm_textured_bg.x = MINIMAP_ZERO_COORDS[0] + left_view_border
        self.mm_textured_bg.y = MINIMAP_ZERO_COORDS[1] + bottom_view_border
        for el in self.ui:
            el.x = el.org_x + left_view_border
            el.y = el.org_y + bottom_view_border
        self.min_count_label.x = SCREEN_W - 200 + left_view_border
        self.min_count_label.y = SCREEN_H - 30 + bottom_view_border
        for entity in our_buildings + our_units \
                      + enemy_buildings + enemy_units:
            entity.pixel.x, entity.pixel.y = to_minimap(entity.x, entity.y)
        self.mm_cam_frame_spt.x, self.mm_cam_frame_spt.y = \
            to_minimap(
                left_view_border - 2,
                bottom_view_border - 2)
        minimap_fow_x = MINIMAP_ZERO_COORDS[0] - 1 + left_view_border
        minimap_fow_y = MINIMAP_ZERO_COORDS[1] - 1 + bottom_view_border

    def update_fow(self, x, y, radius):
        x = int((x - 16) / 32) + 1
        y = int((y - 16) / 32) + 1
        for yi in range(-radius + y, radius + 1 + y):
            if 0 <= yi <= 101:
                for xi in range(-radius + x, radius + 1 + x):
                    if 0 <= xi <= 101:
                        if ((xi - x) ** 2 + (yi - y) ** 2) ** 0.5 <= radius:
                            self.npa[yi, xi, 3] = 0
        self.mm_fow_ImageData.set_data('RGBA',
                                       self.mm_fow_ImageData.width
                                       * 4, data=self.npa.tobytes())


def main():
    game_window = PlanetEleven(SCREEN_W, SCREEN_H, SCREEN_TITLE)
    game_window.setup()
    pyglet.clock.schedule_interval(game_window.update, 1 / 60)
    pyglet.app.run()


if __name__ == "__main__":
    main()
