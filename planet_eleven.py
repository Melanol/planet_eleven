import math
import random
import sys
import numpy as np
import pickle

from pyglet.gl import *
from pyglet.window import key
from pyglet.window import mouse

from movable import Movable
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
    global POS_COORDS, ground_pos_coords_dict, air_pos_coords_dict
    POS_COORDS = []
    for yi in range(1, POS_COORDS_N_ROWS + 1):
        for xi in range(1, POS_COORDS_N_COLUMNS + 1):
            POS_COORDS.append((xi * POS_SPACE - POS_SPACE / 2, yi * POS_SPACE - POS_SPACE / 2))
    ground_pos_coords_dict = {}
    for _x, _y in POS_COORDS:
        ground_pos_coords_dict[(_x, _y)] = None
    air_pos_coords_dict = {}
    for _x, _y in POS_COORDS:
        air_pos_coords_dict[(_x, _y)] = None


gen_pos_coords()


def give_next_target(x, y, angle, flying):
    print('give_next_target input:', x, y, angle)
    if not flying:
        dict_to_check = ground_pos_coords_dict
    else:
        dict_to_check = air_pos_coords_dict
    if angle == 0:
        target = (x + POS_SPACE, y)
        target_id = dict_to_check[target]
    elif angle == 45:
        target = round_coords(x + DISTANCE_PER_JUMP, y + DISTANCE_PER_JUMP)
        target_id = dict_to_check[target]
    elif angle == 90:
        target = (x, y + POS_SPACE)
        target_id = dict_to_check[target]
    elif angle == 135:
        target = round_coords(x - DISTANCE_PER_JUMP, y + DISTANCE_PER_JUMP)
        target_id = dict_to_check[target]
    elif angle in [-180, 180]:
        target = (x - POS_SPACE, y)
        target_id = dict_to_check[target]
    elif angle == -135:
        target = round_coords(x - DISTANCE_PER_JUMP, y - DISTANCE_PER_JUMP)
        target_id = dict_to_check[target]
    elif angle == -90:
        target = (x, y - POS_SPACE)
        target_id = dict_to_check[target]
    elif angle == -45:
        target = round_coords(x + DISTANCE_PER_JUMP, y - DISTANCE_PER_JUMP)
        target_id = dict_to_check[target]
    else:
        raise Exception('bad angle')
    if target_id is None:
        return target
    else:
        return None


def to_minimap(x, y):  # unit.x and unit.y
    x = x / POS_SPACE
    if not x.is_integer():
        x += 1
    x = MINIMAP_ZERO_COORDS[0] + x + left_view_border
    y = y / POS_SPACE
    if not y.is_integer():
        y += 1
    y = MINIMAP_ZERO_COORDS[1] + y + bottom_view_border
    return x, y


# Modify coords for different viewports
def mc(**kwargs):
    if len(kwargs) == 1:
        try:
            return kwargs['x'] + left_view_border
        except KeyError:
            return kwargs['y'] + bottom_view_border
    else:
        return kwargs['x'] + left_view_border, kwargs['y'] + bottom_view_border


class Button(pyglet.sprite.Sprite):
    pass


class Building(pyglet.sprite.Sprite):
    # __init__ == spawn()
    def __init__(self, outer_instance, our_img, enemy_img, x, y, hp, is_enemy):
        self.outer_instance = outer_instance
        self.hp = hp
        ground_pos_coords_dict[(x, y)] = self
        self.is_enemy = is_enemy
        if not self.is_enemy:
            our_buildings_list.append(self)
            img = our_img
            minimap_pixel = res.minimap_our_image
            outer_instance.update_fow(x=x, y=y, radius=3)
        else:
            enemy_buildings_list.append(self)
            img = enemy_img
            minimap_pixel = res.minimap_enemy_image
        super().__init__(img=img, x=x, y=y, batch=buildings_batch)
        pixel_minimap_coords = to_minimap(self.x, self.y)
        self.pixel = pyglet.sprite.Sprite(img=minimap_pixel, x=pixel_minimap_coords[0],
                                          y=pixel_minimap_coords[1],
                                          batch=minimap_pixels_batch)

    def kill(self, delay_del=False):
        global ground_pos_coords_dict, our_buildings_list, enemy_buildings_list
        ground_pos_coords_dict[(self.x, self.y)] = None
        self.pixel.delete()
        if not delay_del:
            if not self.is_enemy:
                del our_buildings_list[our_buildings_list.index(self)]
            else:
                del enemy_buildings_list[enemy_buildings_list.index(self)]
        self.delete()


class ProductionBuilding(Building):
    def __init__(self, outer_instance, our_img, enemy_img, x, y, hp, is_enemy):
        super().__init__(outer_instance, our_img, enemy_img, x, y, hp, is_enemy)
        self.rally_point_x = x
        self.rally_point_y = y
        self.building_queue = []
        self.current_building_time = None
        self.building_complete = True
        self.building_start_time = 0


class Base(ProductionBuilding):
    def __init__(self, outer_instance, x, y, is_enemy=False):
        super().__init__(outer_instance, our_img=res.base_image, enemy_img=res.enemy_base_image, x=x, y=y,
                         hp=100, is_enemy=is_enemy)


class BigBuilding(pyglet.sprite.Sprite):
    # __init__ == spawn()
    def __init__(self, outer_instance, our_img, enemy_img, x, y, hp, is_enemy):
        self.outer_instance = outer_instance
        self.is_big = True
        self.hp = hp
        ground_pos_coords_dict[(x, y)] = self
        ground_pos_coords_dict[(x + POS_SPACE, y)] = self
        ground_pos_coords_dict[(x, y + POS_SPACE)] = self
        ground_pos_coords_dict[(x + POS_SPACE, y + POS_SPACE)] = self
        self.is_enemy = is_enemy
        if not self.is_enemy:
            our_buildings_list.append(self)
            img = our_img
            minimap_pixel = res.minimap_our_image
            outer_instance.update_fow(x=x, y=y, radius=3)
        else:
            enemy_buildings_list.append(self)
            img = enemy_img
            minimap_pixel = res.minimap_enemy_image
        super().__init__(img=img, x=x, y=y, batch=buildings_batch)
        pixel_minimap_coords = to_minimap(self.x, self.y)
        self.pixel = pyglet.sprite.Sprite(img=minimap_pixel, x=pixel_minimap_coords[0],
                                          y=pixel_minimap_coords[1],
                                          batch=minimap_pixels_batch)

    def kill(self, delay_del=False):
        global ground_pos_coords_dict, our_buildings_list, enemy_buildings_list
        ground_pos_coords_dict[(self.x, self.y)] = None
        self.pixel.delete()
        if not delay_del:
            if not self.is_enemy:
                del our_buildings_list[our_buildings_list.index(self)]
            else:
                del enemy_buildings_list[enemy_buildings_list.index(self)]
        self.delete()


class BigProductionBuilding(BigBuilding):
    def __init__(self, outer_instance, our_img, enemy_img, x, y, hp, is_enemy):
        super().__init__(outer_instance, our_img, enemy_img, x, y, hp, is_enemy)
        self.rally_point_x = x
        self.rally_point_y = y
        self.building_queue = []
        self.current_building_time = None
        self.building_complete = True
        self.building_start_time = 0


class BigBase(BigProductionBuilding):
    def __init__(self, outer_instance, x, y, is_enemy=False):
        super().__init__(outer_instance, our_img=res.big_base_image, enemy_img=res.enemy_base_image, x=x, y=y,
                         hp=100, is_enemy=is_enemy)


class AttackingBuilding(Building):
    def __init__(self, outer_instance, our_img, enemy_img, x, y, hp, is_enemy, damage, vision_radius, cooldown):
        super().__init__(outer_instance, our_img, enemy_img, x, y, hp, is_enemy)
        self.rotating_sprite = pyglet.sprite.Sprite(res.turret_image, x, y, batch=turret_batch)
        self.damage = damage
        self.shooting_radius = vision_radius * 32
        self.target_x = None
        self.target_y = None
        self.cooldown = cooldown
        self.on_cooldown = False
        self.cooldown_started = None
        shooting_buildings_list.append(self)
        self.projectile_sprite = res.projectile_image
        self.projectile_speed = 10
        self.projectile_color = (255, 0, 0)

    def shoot(self, frame_count, target_x, target_y, target_obj):
        global projectile_list
        projectile = Projectile(self.x, self.y, target_x, target_y, self.damage, self.projectile_speed, target_obj,
                                color=(200, 200, 255))
        x_diff = target_x - self.x
        y_diff = target_y - self.y
        angle = -math.degrees(math.atan2(y_diff, x_diff)) + 90
        self.rotating_sprite.rotation = angle
        self.on_cooldown = True
        self.cooldown_started = frame_count
        projectile_list.append(projectile)

    def kill(self, delay_del=False):
        global ground_pos_coords_dict, our_buildings_list, enemy_buildings_list
        ground_pos_coords_dict[(self.x, self.y)] = None
        self.pixel.delete()
        if not delay_del:
            if not self.is_enemy:
                del our_buildings_list[our_buildings_list.index(self)]
            else:
                del enemy_buildings_list[enemy_buildings_list.index(self)]
        del shooting_buildings_list[shooting_buildings_list.index(self)]
        self.rotating_sprite.delete()
        self.delete()


class Turret(AttackingBuilding):
    def __init__(self, outer_instance, x, y, is_enemy=False):
        super().__init__(outer_instance, our_img=res.turret_base_image, enemy_img=res.turret_base_image, x=x, y=y,
                         hp=100, is_enemy=is_enemy, damage=10, vision_radius=500, cooldown=60)


class Unit(pyglet.sprite.Sprite):
    def __init__(self, outer_instance, img, hp, vision_radius, damage, cooldown, speed, x, y,
                 projectile_sprite, projectile_speed, has_weapon=True, projectile_color=(255, 255, 255),
                 batch=ground_units_batch):
        super().__init__(img=img, x=x, y=y, batch=batch)
        self.outer_instance = outer_instance
        self.x = x
        self.y = y
        self.hp = hp
        self.vision_radius = vision_radius
        self.has_weapon = has_weapon
        self.damage = damage
        self.shooting_radius = vision_radius * 32
        self.speed = speed
        self.destination_reached = True
        self.movement_interrupted = False
        self.prev_loc_x = x
        self.prev_loc_y = y
        self.target_x = None
        self.target_y = None
        self.destination_x = None
        self.destination_y = None
        self.velocity_x = 0
        self.velocity_y = 0
        self.cooldown = cooldown
        self.on_cooldown = False
        self.cooldown_started = None
        self.projectile_sprite = projectile_sprite
        self.projectile_speed = projectile_speed
        self.projectile_color = projectile_color

    def spawn(self):
        if not self.flying:
            ground_pos_coords_dict[(self.x, self.y)] = self
        else:
            air_pos_coords_dict[(self.x, self.y)] = self
        our_units_list.append(self)

        # Minimap pixel
        pixel_minimap_coords = to_minimap(self.x, self.y)
        self.pixel = pyglet.sprite.Sprite(img=res.minimap_our_image, x=pixel_minimap_coords[0],
                                          y=pixel_minimap_coords[1],
                                          batch=minimap_pixels_batch)

        # Shadow
        if self.flying:
            self.shadow = Movable(img=self.shadow_sprite, x=self.x + 10, y=self.y - 10)
            self.shadow.batch = air_shadows_batch
        else:
            self.shadow = Movable(img=self.shadow_sprite, x=self.x + 3, y=self.y - 3)
            self.shadow.batch = shadows_batch
        self.outer_instance.update_fow(self.x, self.y, self.vision_radius)

    def update(self):
        self.x, self.y = self.x + self.velocity_x, self.y + self.velocity_y

    def move(self, destination):
        # Called once by RMB or when a unit is created
        destination_x, destination_y = destination[0], destination[1]
        print('destination_x =', destination_x, 'destination_y =', destination_y)
        # Not moving: same coords
        if self.x == destination_x and self.y == destination_y:
            if not self.flying:
                ground_pos_coords_dict[(self.x, self.y)] = self
            else:
                air_pos_coords_dict[(self.x, self.y)] = self
            self.destination_reached = True
            return
        self.destination_reached = False
        self.destination_x = destination_x
        self.destination_y = destination_y
        diff_x = self.destination_x - self.x
        diff_y = self.destination_y - self.y
        angle = math.atan2(diff_y, diff_x)  # Rad
        d_angle = math.degrees(angle)
        target = give_next_target(self.x, self.y, round_angle(d_angle), self.flying)
        print('target =', target)
        if target:  # If destination not reached and update_movement will be called (I think)
            self.target_x = target[0]
            self.target_y = target[1]
            self.pixel.x, self.pixel.y = to_minimap(self.target_x, self.target_y)
        else:
            self.destination_reached = True
            if not self.flying:
                ground_pos_coords_dict[(self.prev_loc_x, self.prev_loc_y)] = None
                ground_pos_coords_dict[(self.x, self.y)] = self
            else:
                air_pos_coords_dict[(self.prev_loc_x, self.prev_loc_y)] = None
                air_pos_coords_dict[(self.x, self.y)] = self
            self.prev_loc_x, self.prev_loc_y = self.x, self.y
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

        if not self.flying:
            ground_pos_coords_dict[(self.target_x, self.target_y)] = self
        else:
            air_pos_coords_dict[(self.target_x, self.target_y)] = self

    def distance_to_target(self):
        return ((self.target_x - self.x) ** 2 + (self.target_y - self.y) ** 2) ** 0.5

    def eta(self):
        return self.distance_to_target() / self.speed

    def update_movement(self):
        # Called by update to move to the next point
        print('\nupdate_movement: self.x = {}, self.y = {})'.format(self.x, self.y))
        if not self.flying:
            ground_pos_coords_dict[(self.x, self.y)] = None
        else:
            air_pos_coords_dict[(self.x, self.y)] = None
        diff_x = self.destination_x - self.x
        diff_y = self.destination_y - self.y
        angle = math.atan2(diff_y, diff_x)  # Rad
        d_angle = math.degrees(angle)
        self.rotation = -d_angle + 90
        self.shadow.rotation = -math.degrees(angle) + 90
        next_target = give_next_target(self.x, self.y, round_angle(d_angle), self.flying)
        print('next_target =', next_target)
        if next_target:
            if not self.flying:
                ground_pos_coords_dict[(self.x, self.y)] = None
            else:
                air_pos_coords_dict[(self.x, self.y)] = None
            self.target_x = next_target[0]
            self.target_y = next_target[1]
            self.pixel.x, self.pixel.y = to_minimap(self.target_x, self.target_y)
            if not self.flying:
                ground_pos_coords_dict[(self.target_x, self.target_y)] = self
            else:
                air_pos_coords_dict[(self.target_x, self.target_y)] = self
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
            if not self.flying:
                ground_pos_coords_dict[(self.x, self.y)] = self
            else:
                air_pos_coords_dict[(self.x, self.y)] = self
            self.destination_reached = True
        if self.x == self.destination_x and self.y == self.destination_y:
            print('Destination reached')
            self.destination_reached = True
            print('self.destination_reached =', self.destination_reached)
        print()

    def shoot(self, frame_count, target_x, target_y, target_obj):
        global projectile_list
        projectile = Projectile(x=self.x, y=self.y,
                                target_x=target_x, target_y=target_y,
                                damage=self.damage, speed=self.projectile_speed, target_obj=target_obj)
        x_diff = target_x - self.x
        y_diff = target_y - self.y
        angle = -math.degrees(math.atan2(y_diff, x_diff)) + 90
        self.rotation = angle
        self.shadow.rotation = angle
        self.on_cooldown = True
        self.cooldown_started = frame_count
        projectile_list.append(projectile)

    def kill(self, delay_del=False):
        self.pixel.delete()
        self.shadow.delete()
        if not delay_del:
            del our_units_list[our_units_list.index(self)]
        self.delete()
        try:
            del builders_list[builders_list.index(self)]
        except ValueError:
            pass


class Defiler(Unit):
    building_time = 60

    def __init__(self, outer_instance, x, y):
        super().__init__(img=res.defiler_image, outer_instance=outer_instance, hp=100, vision_radius=6, damage=10,
                         cooldown=60, speed=6, x=x, y=y, projectile_sprite='sprites/laser.png',
                         projectile_speed=5, batch=air_batch)
        self.flying = True
        self.shadow_sprite = res.defiler_shadow_image


class Tank(Unit):
    building_time = 60

    def __init__(self, outer_instance, x, y):
        super().__init__(img=res.tank_image, outer_instance=outer_instance, hp=100, vision_radius=6, damage=10,
                         cooldown=60, speed=0.6, x=x, y=y, projectile_sprite='sprites/laser.png',
                         projectile_speed=5)
        self.flying = False
        self.shadow_sprite = res.tank_shadow_image


class Vulture(Unit):
    building_time = 10

    def __init__(self, outer_instance, x, y):
        super().__init__(img=res.vulture_image, outer_instance=outer_instance, hp=50, vision_radius=3, damage=10,
                         cooldown=60, speed=10, x=x, y=y, projectile_sprite='sprites/laser.png',
                         projectile_speed=5)
        self.flying = False
        self.shadow_sprite = res.vulture_shadow_image


class Builder(Unit):
    building_time = 10

    def __init__(self, outer_instance, x, y):
        super().__init__(img=res.builder_image, outer_instance=outer_instance, hp=50, vision_radius=2, damage=0,
                         cooldown=60, speed=5, x=x, y=y, has_weapon=False, projectile_sprite='sprites/laser.png',
                         projectile_speed=5)
        builders_list.append(self)
        self.flying = False
        self.shadow_sprite = res.builder_shadow_image
        self.to_build = None
        self.building_coord_x = None
        self.building_coord_y = None

    def build(self):
        self.destination_reached = True
        ground_pos_coords_dict[(self.x, self.y)] = self
        if self.to_build == "base":
            Base(self.outer_instance, self.building_coord_x, self.building_coord_y)
        elif self.to_build == "turret":
            Turret(self.outer_instance, self.building_coord_x, self.building_coord_y)
        self.to_build = None


class PlanetEleven(pyglet.window.Window):
    def __init__(self, width, height, title):
        conf = Config(sample_buffers=1,
                      samples=4,
                      depth_size=16,
                      double_buffer=True)
        super().__init__(width, height, title, config=conf, fullscreen=False)
        self.set_mouse_cursor(res.cursor)
        self.fps_display = pyglet.window.FPSDisplay(window=self)

    def clear_level(self):
        global our_units_list, our_buildings_list, enemy_buildings_list, \
            projectile_list, left_view_border, bottom_view_border, minimap_fow_x, minimap_fow_y
        for unit in our_units_list:
            unit.kill(delay_del=True)
        for building in our_buildings_list:
            building.kill(delay_del=True)
        for enemy_building in enemy_buildings_list:
            enemy_building.kill(delay_del=True)
        for projectile in projectile_list:
            projectile.delete()

        our_units_list = []
        our_buildings_list = []
        enemy_buildings_list = []
        projectile_list = []
        left_view_border = 0
        bottom_view_border = 0
        gen_pos_coords()
        minimap_fow_x, minimap_fow_y = MINIMAP_ZERO_COORDS[0] - 1, MINIMAP_ZERO_COORDS[1] - 1

    def reset(self):
        self.clear_level()
        self.setup()
        print('reset')

    def save(self):
        savefile = open("save.p", "wb")
        pickle.dump(left_view_border, savefile)
        pickle.dump(bottom_view_border, savefile)
        pickle.dump(self.frame_count, savefile)
        pickle.dump(self.npa, savefile)

        pickle.dump(self.minimap_textured_background.x, savefile)
        pickle.dump(self.minimap_textured_background.y, savefile)
        pickle.dump(self.control_panel_sprite.x, savefile)
        pickle.dump(self.control_panel_sprite.y, savefile)
        pickle.dump(self.control_panel_buttons_background.x, savefile)
        pickle.dump(self.control_panel_buttons_background.y, savefile)
        pickle.dump(self.move_button.x, savefile)
        pickle.dump(self.move_button.y, savefile)
        pickle.dump(self.stop_button.x, savefile)
        pickle.dump(self.stop_button.y, savefile)
        pickle.dump(self.attack_button.x, savefile)
        pickle.dump(self.attack_button.y, savefile)
        pickle.dump(self.base_button.x, savefile)
        pickle.dump(self.base_button.y, savefile)
        pickle.dump(self.defiler_button.x, savefile)
        pickle.dump(self.defiler_button.y, savefile)
        pickle.dump(self.tank_button.x, savefile)
        pickle.dump(self.tank_button.y, savefile)
        pickle.dump(self.vulture_button.x, savefile)
        pickle.dump(self.vulture_button.y, savefile)
        pickle.dump(self.builder_button.x, savefile)
        pickle.dump(self.builder_button.y, savefile)
        pickle.dump(minimap_fow_x, savefile)
        pickle.dump(minimap_fow_y, savefile)
        pickle.dump(self.minimap_cam_frame_sprite.x, savefile)
        pickle.dump(self.minimap_cam_frame_sprite.y, savefile)

        pickle.dump(len(our_buildings_list), savefile)
        for building in our_buildings_list:
            pickle.dump(str(type(building)), savefile)
            pickle.dump(building.x, savefile)
            pickle.dump(building.y, savefile)
            pickle.dump(building.hp, savefile)
            pickle.dump(building.rally_point_x, savefile)
            pickle.dump(building.rally_point_y, savefile)
            pickle.dump(building.building_queue, savefile)
            pickle.dump(building.current_building_time, savefile)
            pickle.dump(building.building_complete, savefile)
            pickle.dump(building.building_start_time, savefile)

        pickle.dump(len(our_units_list), savefile)
        for unit in our_units_list:
            pickle.dump(str(type(unit)), savefile)
            pickle.dump(unit.x, savefile)
            pickle.dump(unit.y, savefile)
            pickle.dump(unit.rotation, savefile)
            pickle.dump(unit.hp, savefile)
            pickle.dump(unit.destination_reached, savefile)
            pickle.dump(unit.movement_interrupted, savefile)
            pickle.dump(unit.target_x, savefile)
            pickle.dump(unit.target_y, savefile)
            pickle.dump(unit.destination_x, savefile)
            pickle.dump(unit.destination_y, savefile)
            pickle.dump(unit.velocity_x, savefile)
            pickle.dump(unit.velocity_y, savefile)
            pickle.dump(unit.on_cooldown, savefile)
            pickle.dump(unit.cooldown_started, savefile)
            pickle.dump(unit.prev_loc_x, savefile)
            pickle.dump(unit.prev_loc_y, savefile)

        pickle.dump(len(enemy_buildings_list), savefile)
        for building in enemy_buildings_list:
            pickle.dump(str(type(building)), savefile)
            pickle.dump(building.x, savefile)
            pickle.dump(building.y, savefile)
            pickle.dump(building.hp, savefile)
            pickle.dump(building.rally_point_x, savefile)
            pickle.dump(building.rally_point_y, savefile)
            pickle.dump(building.building_queue, savefile)
            pickle.dump(building.current_building_time, savefile)
            pickle.dump(building.building_complete, savefile)
            pickle.dump(building.building_start_time, savefile)

        pickle.dump(len(projectile_list), savefile)
        for projectile in projectile_list:
            pickle.dump(projectile.x, savefile)
            pickle.dump(projectile.y, savefile)
            pickle.dump(projectile.damage, savefile)
            pickle.dump(projectile.speed, savefile)
            pickle.dump(projectile.target_x, savefile)
            pickle.dump(projectile.target_y, savefile)
            pickle.dump(projectile.rotation, savefile)
            pickle.dump(projectile.velocity_x, savefile)
            pickle.dump(projectile.velocity_y, savefile)

        print('saved')

    def load(self):
        global left_view_border, bottom_view_border, minimap_fow_x, minimap_fow_y
        self.clear_level()
        savefile = open("save.p", "rb")
        left_view_border = pickle.load(savefile)
        bottom_view_border = pickle.load(savefile)
        self.frame_count = pickle.load(savefile)
        self.npa = pickle.load(savefile)
        self.minimap_fow_ImageData.set_data('RGBA', self.minimap_fow_ImageData.width * 4,
                                            data=self.npa.tobytes())

        self.minimap_textured_background.x = pickle.load(savefile)
        self.minimap_textured_background.y = pickle.load(savefile)
        self.control_panel_sprite.x = pickle.load(savefile)
        self.control_panel_sprite.y = pickle.load(savefile)
        self.control_panel_buttons_background.x = pickle.load(savefile)
        self.control_panel_buttons_background.y = pickle.load(savefile)
        self.move_button.x = pickle.load(savefile)
        self.move_button.y = pickle.load(savefile)
        self.stop_button.x = pickle.load(savefile)
        self.stop_button.y = pickle.load(savefile)
        self.attack_button.x = pickle.load(savefile)
        self.attack_button.y = pickle.load(savefile)
        self.base_button.x = pickle.load(savefile)
        self.base_button.y = pickle.load(savefile)
        self.defiler_button.x = pickle.load(savefile)
        self.defiler_button.y = pickle.load(savefile)
        self.tank_button.x = pickle.load(savefile)
        self.tank_button.y = pickle.load(savefile)
        self.vulture_button.x = pickle.load(savefile)
        self.vulture_button.y = pickle.load(savefile)
        self.builder_button.x = pickle.load(savefile)
        self.builder_button.y = pickle.load(savefile)
        minimap_fow_x = pickle.load(savefile)
        minimap_fow_y = pickle.load(savefile)
        self.minimap_cam_frame_sprite.x = pickle.load(savefile)
        self.minimap_cam_frame_sprite.y = pickle.load(savefile)

        our_buildings_list_len = pickle.load(savefile)
        for _ in range(our_buildings_list_len):
            building_type = pickle.load(savefile)
            x = pickle.load(savefile)
            y = pickle.load(savefile)
            if building_type == "<class '__main__.Base'>":
                building = Base(self, x=x, y=y)
                building.hp = pickle.load(savefile)
                building.rally_point_x = pickle.load(savefile)
                building.rally_point_y = pickle.load(savefile)
                building.building_queue = pickle.load(savefile)
                building.current_building_time = pickle.load(savefile)
                building.building_complete = pickle.load(savefile)
                building.building_start_time = pickle.load(savefile)

        our_units_list_len = pickle.load(savefile)
        for _ in range(our_units_list_len):
            unit_type = pickle.load(savefile)
            x = pickle.load(savefile)
            y = pickle.load(savefile)
            rotation = pickle.load(savefile)
            if unit_type == "<class '__main__.Defiler'>":
                unit = Defiler(self, x=x, y=y)
            elif unit_type == "<class '__main__.Tank'>":
                unit = Tank(self, x=x, y=y)
            elif unit_type == "<class '__main__.Vulture'>":
                unit = Vulture(self, x=x, y=y)
            elif unit_type == "<class '__main__.Builder'>":
                unit = Builder(self, x=x, y=y)
            unit.spawn()
            unit.rotation = rotation
            unit.hp = pickle.load(savefile)
            unit.destination_reached = pickle.load(savefile)
            unit.movement_interrupted = pickle.load(savefile)
            unit.target_x = pickle.load(savefile)
            unit.target_y = pickle.load(savefile)
            unit.destination_x = pickle.load(savefile)
            unit.destination_y = pickle.load(savefile)
            unit.velocity_x = pickle.load(savefile)
            unit.velocity_y = pickle.load(savefile)
            unit.on_cooldown = pickle.load(savefile)
            unit.cooldown_started = pickle.load(savefile)
            unit.prev_loc_x = pickle.load(savefile)
            unit.prev_loc_y = pickle.load(savefile)
            unit.shadow.rotation = unit.rotation
            unit.shadow.velocity_x = unit.velocity_x
            unit.shadow.velocity_y = unit.velocity_y

        enemy_buildings_list_len = pickle.load(savefile)
        for _ in range(enemy_buildings_list_len):
            building_type = pickle.load(savefile)
            x = pickle.load(savefile)
            y = pickle.load(savefile)
            if building_type == "<class '__main__.Base'>":
                building = Base(self, x=x, y=y, is_enemy=True)
                building.hp = pickle.load(savefile)
                building.rally_point_x = pickle.load(savefile)
                building.rally_point_y = pickle.load(savefile)
                building.building_queue = pickle.load(savefile)
                building.current_building_time = pickle.load(savefile)
                building.building_complete = pickle.load(savefile)
                building.building_start_time = pickle.load(savefile)

        projectile_list_len = pickle.load(savefile)
        for _ in range(projectile_list_len):
            x = pickle.load(savefile)
            y = pickle.load(savefile)
            damage = pickle.load(savefile)
            speed = pickle.load(savefile)
            target_x = pickle.load(savefile)
            target_y = pickle.load(savefile)
            rotation = pickle.load(savefile)
            velocity_x = pickle.load(savefile)
            velocity_y = pickle.load(savefile)
            projectile = Projectile(x, y, target_x, target_y, damage, speed, None)
            projectile_list.append(projectile)
            projectile.rotation = rotation
            projectile.velocity_x = velocity_x
            projectile.velocity_y = velocity_y
            print('target_x =', target_x)
            print('target_y =', target_y)
            for building in enemy_buildings_list:
                print('building.x =', building.x)
                print('building.y =', building.y)
                if building.x == target_x and building.y == target_y:
                    projectile.target_obj = building
                    break
            print(projectile.target_obj)

        print('loaded')

    def setup(self):
        global selected
        self.paused = False
        self.frame_count = 0
        self.dx = 0
        self.dy = 0
        self.minimap_drugging = False
        self.building_location_selection_phase = False

        self.background = pyglet.sprite.Sprite(img=res.background_image, x=0, y=0)
        self.control_panel_sprite = pyglet.sprite.Sprite(img=res.control_panel_image, x=SCREEN_WIDTH, y=0)
        self.menu_button = pyglet.sprite.Sprite(img=res.menu_image, x=center_x, y=SCREEN_HEIGHT - 30)
        self.selected_frame_cp = pyglet.sprite.Sprite(img=res.selected_frame_image, x=center_x, y=SCREEN_HEIGHT - 90)
        self.control_panel_buttons_background = pyglet.sprite.Sprite(img=res.control_panel_buttons_background_image,
                                                                     x=center_x, y=center_y)
        self.minimap_textured_background = pyglet.sprite.Sprite(img=res.minimap_textured_background_image,
                                                                x=MINIMAP_ZERO_COORDS[0], y=MINIMAP_ZERO_COORDS[1])
        self.minimap_cam_frame_sprite = pyglet.sprite.Sprite(img=res.minimap_cam_frame_image,
                                                             x=MINIMAP_ZERO_COORDS[0] - 1,
                                                             y=MINIMAP_ZERO_COORDS[1] - 1)
        self.minimap_fow_image = pyglet.image.load('sprites/minimap_fow.png')
        self.minimap_fow_ImageData = self.minimap_fow_image.get_image_data()
        self.npa = np.fromstring(self.minimap_fow_ImageData.get_data('RGBA', self.minimap_fow_ImageData.width * 4),
                                 dtype=np.uint8)
        self.npa = self.npa.reshape((102, 102, 4))

        # Spawn
        self.our_1st_base = Base(self, POS_SPACE / 2 + POS_SPACE * 6, POS_SPACE / 2 + POS_SPACE * 6)
        selected = self.our_1st_base
        Base(self, POS_SPACE / 2 + POS_SPACE * 6, POS_SPACE / 2 + POS_SPACE * 5, is_enemy=True)
        Base(self, POS_SPACE / 2 + POS_SPACE * 6, POS_SPACE / 2 + POS_SPACE * 4, is_enemy=True)
        Base(self, POS_SPACE / 2 + POS_SPACE * 5, POS_SPACE / 2 + POS_SPACE * 4, is_enemy=True)
        Base(self, POS_SPACE / 2 + POS_SPACE * 4, POS_SPACE / 2 + POS_SPACE * 4, is_enemy=True)
        Base(self, POS_SPACE / 2 + POS_SPACE * 4, POS_SPACE / 2 + POS_SPACE * 5, is_enemy=True)
        BigBase(self, POS_SPACE / 2 + POS_SPACE * 6, POS_SPACE / 2 + POS_SPACE * 7)

        # Buttons
        self.base_button = Button(img=res.base_image, x=CONTROL_BUTTONS_COORDS[3][0],
                                  y=CONTROL_BUTTONS_COORDS[3][1])
        self.turret_button = Button(img=res.turret_button_image, x=CONTROL_BUTTONS_COORDS[4][0],
                                    y=CONTROL_BUTTONS_COORDS[4][1])
        self.big_base_button = Button(img=res.big_base_icon_image, x=CONTROL_BUTTONS_COORDS[5][0],
                                      y=CONTROL_BUTTONS_COORDS[5][1])
        self.move_button = Button(img=res.move_image, x=CONTROL_BUTTONS_COORDS[0][0],
                                  y=CONTROL_BUTTONS_COORDS[0][1])
        self.stop_button = Button(img=res.stop_image, x=CONTROL_BUTTONS_COORDS[1][0],
                                  y=CONTROL_BUTTONS_COORDS[1][1])
        self.attack_button = Button(img=res.attack_image, x=CONTROL_BUTTONS_COORDS[2][0],
                                    y=CONTROL_BUTTONS_COORDS[2][1])
        self.defiler_button = Button(img=res.defiler_image, x=CONTROL_BUTTONS_COORDS[0][0],
                                     y=CONTROL_BUTTONS_COORDS[0][1])
        self.tank_button = Button(img=res.tank_image, x=CONTROL_BUTTONS_COORDS[1][0], y=CONTROL_BUTTONS_COORDS[1][1])
        self.vulture_button = Button(img=res.vulture_image, x=CONTROL_BUTTONS_COORDS[2][0],
                                     y=CONTROL_BUTTONS_COORDS[2][1])
        self.builder_button = Button(img=res.builder_image, x=CONTROL_BUTTONS_COORDS[3][0],
                                     y=CONTROL_BUTTONS_COORDS[3][1])

        self.selection_sprite = pyglet.sprite.Sprite(img=res.selection_image, x=self.our_1st_base.x,
                                                     y=self.our_1st_base.y)
        self.selection_big_sprite = pyglet.sprite.Sprite(img=res.selection_big_image, x=self.our_1st_base.x,
                                                         y=self.our_1st_base.y)
        self.rally_point_sprite = pyglet.sprite.Sprite(img=res.rally_point_image, x=self.our_1st_base.rally_point_x,
                                                       y=self.our_1st_base.rally_point_y)

        # self.dots = []
        # for x, y in POS_COORDS:
        #     dot = pyglet.sprite.Sprite(img=res.utility_dot_image, x=x, y=y, batch=utilities_batch)
        #     self.dots.append(dot)

        self.basic_unit_control_buttons = [self.move_button, self.stop_button, self.attack_button]
        self.controls_dict = {"<class 'NoneType'>": None,
                              "<class '__main__.Base'>": [self.defiler_button, self.tank_button, self.vulture_button,
                                                          self.builder_button],
                              "<class '__main__.Defiler'>": self.basic_unit_control_buttons,
                              "<class '__main__.Tank'>": self.basic_unit_control_buttons,
                              "<class '__main__.Vulture'>": self.basic_unit_control_buttons,
                              "<class '__main__.Builder'>": self.basic_unit_control_buttons + [self.base_button] +
                                                            [self.turret_button] + [self.big_base_button]
                              }
        self.control_buttons_to_render = self.controls_dict["<class '__main__.Base'>"]
        self.base_building_sprite = pyglet.sprite.Sprite(img=res.base_image, x=-100, y=-100)
        self.base_building_sprite.color = (0, 255, 0)
        self.turret_building_sprite = pyglet.sprite.Sprite(img=res.turret_button_image, x=-100, y=-100)
        self.turret_building_sprite.color = (0, 255, 0)

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
        glOrtho(left_view_border, left_view_border + SCREEN_WIDTH, bottom_view_border,
                bottom_view_border + SCREEN_HEIGHT, 1, -1)

        '''for x, y in POS_COORDS:
            draw_dot(x, y, 2)'''

        self.background.draw()
        shadows_batch.draw()
        buildings_batch.draw()
        ground_units_batch.draw()
        turret_batch.draw()
        air_shadows_batch.draw()
        air_batch.draw()
        try:
            if selected.is_big:
                self.selection_big_sprite.draw()
        except AttributeError:
            self.selection_sprite.draw()

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.fow_texture = self.minimap_fow_image.get_texture()
        self.fow_texture.width = 3264
        self.fow_texture.height = 3264
        self.fow_texture.blit(-32, -32)
        utilities_batch.draw()
        if self.building_location_selection_phase:
            if self.to_build == "base":
                self.base_building_sprite.draw()
            elif self.to_build == "turret":
                self.turret_building_sprite.draw()
        self.control_panel_sprite.draw()
        self.menu_button.draw()
        self.selected_frame_cp.draw()
        self.control_panel_buttons_background.draw()
        self.minimap_textured_background.draw()
        minimap_pixels_batch.draw()

        if self.control_buttons_to_render:
            for button in self.control_buttons_to_render:
                button.draw()
            if selected in our_buildings_list and selected not in shooting_buildings_list:
                self.rally_point_sprite.draw()

        self.fow_texture.width = 102
        self.fow_texture.height = 102
        self.fow_texture.blit(minimap_fow_x, minimap_fow_y)

        self.minimap_cam_frame_sprite.draw()

        for projectile in projectile_list:
            projectile.draw()

        self.fps_display.draw()

        # Remove default modelview matrix
        glPopMatrix()

    def update(self, delta_time):
        global selected
        if not self.paused:
            self.frame_count += 1
            # Build units
            for building in our_buildings_list:
                try:
                    if building.building_queue:
                        unit = building.building_queue[0]
                        if unit == 'defiler':
                            building.current_building_time = Defiler.building_time
                        elif unit == 'tank':
                            building.current_building_time = Tank.building_time
                        elif unit == 'vulture':
                            building.current_building_time = Vulture.building_time
                        elif unit == 'builder':
                            building.current_building_time = Builder.building_time
                        if self.frame_count - building.building_start_time == building.current_building_time:
                            if building.building_queue[0] not in LIST_OF_FLYING:
                                dict_to_check = ground_pos_coords_dict
                            else:
                                dict_to_check = air_pos_coords_dict
                            x = building.x - POS_SPACE
                            y = building.y - POS_SPACE
                            place_found = False
                            if dict_to_check[(x, y)] is None:
                                place_found = True
                            else:
                                x += POS_SPACE
                                if dict_to_check[(x, y)] is None:
                                    place_found = True
                                else:
                                    x += POS_SPACE
                                    if dict_to_check[(x, y)] is None:
                                        place_found = True
                                    else:
                                        y += POS_SPACE
                                        if dict_to_check[(x, y)] is None:
                                            place_found = True
                                        else:
                                            y += POS_SPACE
                                            if dict_to_check[(x, y)] is None:
                                                place_found = True
                                            else:
                                                x -= POS_SPACE
                                                if dict_to_check[(x, y)] is None:
                                                    place_found = True
                                                else:
                                                    x -= POS_SPACE
                                                    if dict_to_check[(x, y)] is None:
                                                        place_found = True
                                                    else:
                                                        y -= POS_SPACE
                                                        if dict_to_check[(x, y)] is None:
                                                            place_found = True
                                                        else:
                                                            building.building_start_time += 1
                                                            print('No space')
                            if place_found:
                                unit = building.building_queue.pop(0)
                                if unit == 'defiler':
                                    unit = Defiler(self, x=x, y=y)
                                    unit.spawn()
                                elif unit == 'tank':
                                    unit = Tank(self, x=x, y=y)
                                    unit.spawn()
                                elif unit == 'vulture':
                                    unit = Vulture(self, x=x, y=y)
                                    unit.spawn()
                                elif unit == 'builder':
                                    unit = Builder(self, x=x, y=y)
                                    unit.spawn()
                                building.building_start_time += building.current_building_time
                                unit.move((building.rally_point_x, building.rally_point_y))
                except AttributeError:
                    pass
            # Units
            # Build buildings
            for builder in builders_list:
                if builder.to_build:
                    if abs(builder.x - builder.building_coord_x) == POS_SPACE:
                        if abs(
                                builder.y - builder.building_coord_y) == POS_SPACE or builder.y == builder.building_coord_y:
                            builder.build()
                    elif builder.x == builder.building_coord_x and abs(
                            builder.y - builder.building_coord_y) == POS_SPACE:
                        builder.build()
            # Movement
            for unit in our_units_list:
                # Selection
                if selected == unit:
                    self.selection_sprite.x = unit.x
                    self.selection_sprite.y = unit.y
                # Do not jump
                if not unit.destination_reached:
                    if not unit.eta() <= 1:
                        unit.update()
                        unit.shadow.update()
                    # Jump
                    else:
                        if not unit.movement_interrupted:
                            unit.x = unit.target_x
                            unit.y = unit.target_y
                            if not unit.flying:
                                unit.shadow.x = unit.target_x + 3
                                unit.shadow.y = unit.target_y - 3
                                ground_pos_coords_dict[(unit.prev_loc_x, unit.prev_loc_y)] = None
                                ground_pos_coords_dict[(unit.target_x, unit.target_y)] = unit
                            else:
                                unit.shadow.x = unit.target_x + 10
                                unit.shadow.y = unit.target_y - 10
                                air_pos_coords_dict[(unit.prev_loc_x, unit.prev_loc_y)] = None
                                air_pos_coords_dict[(unit.target_x, unit.target_y)] = unit
                            if unit.x == unit.destination_x and unit.y == unit.destination_y:
                                unit.destination_reached = True
                            else:
                                unit.update_movement()
                            unit.prev_loc_x, unit.prev_loc_y = unit.x, unit.y
                        else:
                            unit.x = unit.target_x
                            unit.y = unit.target_y
                            if not unit.flying:
                                unit.shadow.x = unit.target_x + 3
                                unit.shadow.y = unit.target_y - 3
                                ground_pos_coords_dict[(unit.prev_loc_x, unit.prev_loc_y)] = None
                                ground_pos_coords_dict[(unit.target_x, unit.target_y)] = unit
                            else:
                                unit.shadow.x = unit.target_x + 10
                                unit.shadow.y = unit.target_y - 10
                                air_pos_coords_dict[(unit.prev_loc_x, unit.prev_loc_y)] = None
                                air_pos_coords_dict[(unit.target_x, unit.target_y)] = unit
                            unit.destination_reached = True
                            unit.move((unit.new_dest_x, unit.new_dest_y))
                            unit.movement_interrupted = False
                            unit.prev_loc_x, unit.prev_loc_y = unit.x, unit.y
                        self.update_fow(unit.x, unit.y, unit.vision_radius)
                else:
                    try:
                        unit.to_build = None
                        unit.building_coord_x = None
                        unit.building_coord_y = None
                    except AttributeError:
                        pass
            # Units shooting
            for unit in our_units_list:
                if unit.has_weapon:
                    if unit.destination_reached:
                        if not unit.on_cooldown:
                            closest_enemy = None
                            closest_enemy_dist = None
                            for enemy in enemy_buildings_list:
                                distance_to_enemy = ((enemy.x - unit.x) ** 2 + (enemy.y - unit.y) ** 2) ** 0.5
                                if distance_to_enemy <= unit.shooting_radius:
                                    if not closest_enemy:
                                        closest_enemy = enemy
                                        closest_enemy_dist = distance_to_enemy
                                    else:
                                        if distance_to_enemy < closest_enemy_dist:
                                            closest_enemy = enemy
                                            closest_enemy_dist = distance_to_enemy
                            if closest_enemy:
                                unit.shoot(self.frame_count, closest_enemy.x, closest_enemy.y, closest_enemy)
                        else:
                            if (self.frame_count - unit.cooldown_started) % unit.cooldown == 0:
                                unit.on_cooldown = False
            # Buildings shooting
            for building in shooting_buildings_list:
                if not building.on_cooldown:
                    closest_enemy = None
                    closest_enemy_dist = None
                    for enemy in enemy_buildings_list:
                        distance_to_enemy = ((enemy.x - building.x) ** 2 + (enemy.y - building.y) ** 2) ** 0.5
                        if distance_to_enemy <= building.shooting_radius:
                            if not closest_enemy:
                                closest_enemy = enemy
                                closest_enemy_dist = distance_to_enemy
                            else:
                                if distance_to_enemy < closest_enemy_dist:
                                    closest_enemy = enemy
                                    closest_enemy_dist = distance_to_enemy
                    if closest_enemy:
                        building.shoot(self.frame_count, closest_enemy.x, closest_enemy.y, closest_enemy)
                else:
                    if (self.frame_count - building.cooldown_started) % building.cooldown == 0:
                        building.on_cooldown = False
            # Projectiles
            for i, projectile in enumerate(projectile_list):
                if not projectile.eta() <= 1:
                    projectile.update()
                else:
                    projectile.target_obj.hp -= projectile.damage
                    projectile.delete()
                    del projectile_list[i]

            # Destroying targets
            for enemy in enemy_buildings_list:
                if enemy.hp <= 0:
                    enemy.kill()

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
                if selected in our_units_list:
                    selected.destination_x = selected.target_x
                    selected.destination_y = selected.target_y
            elif symbol == key.F1:
                self.reset()
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
            elif symbol == key.G:
                print(selected)
            elif symbol == key.H:
                for _key, _value in ground_pos_coords_dict.items():
                    if _value:
                        print('key =', _key, 'value =', _value)
            elif symbol == key.J:
                print(selected.is_big)
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
                    for unit in our_units_list:
                        if unit_id == id(unit):
                            unit.kill()
                print(len(our_units_list))
            elif symbol == key.DELETE:
                if selected in our_units_list:
                    selected.kill()
                    if selected.flying:
                        air_pos_coords_dict[(self.selection_sprite.x, self.selection_sprite.y)] = None
                    else:
                        ground_pos_coords_dict[(self.selection_sprite.x, self.selection_sprite.y)] = None
                    selected = None
                elif selected in our_buildings_list:
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
        global selected, our_units_list, left_view_border, bottom_view_border
        if not self.paused:
            if self.fullscreen:
                x /= 2
                y /= 2
            if not self.building_location_selection_phase:
                # Game field
                if x < SCREEN_WIDTH - 139:
                    x, y = round_coords(x, y)
                    x, y = mc(x=x, y=y)
                    print('\nglobal click coords:', x, y)
                    if button == mouse.LEFT:
                        # Selection
                        selected = None
                        air_found = False
                        for _key, value in air_pos_coords_dict.items():
                            if x == _key[0] and y == _key[1]:
                                selected = value
                                if selected:
                                    air_found = True
                                    self.selection_sprite.x = x
                                    self.selection_sprite.y = y
                                break
                        if not air_found:
                            for _key, value in ground_pos_coords_dict.items():
                                if x == _key[0] and y == _key[1]:
                                    selected = value
                                    try:
                                        selected.is_big
                                        self.selection_big_sprite.x = x + POS_SPACE / 2
                                        self.selection_big_sprite.y = y + POS_SPACE / 2
                                    except AttributeError:
                                        self.selection_sprite.x = x
                                        self.selection_sprite.y = y
                                    if selected in our_buildings_list:
                                        self.rally_point_sprite.x = selected.rally_point_x
                                        self.rally_point_sprite.y = selected.rally_point_y
                                    break
                        try:
                            self.control_buttons_to_render = self.controls_dict[str(type(selected))]
                        except KeyError:
                            pass
                        print('SELECTED CLASS =', type(selected))
                    elif button == mouse.RIGHT:
                        # Rally point
                        if selected in our_buildings_list:
                            selected.rally_point_x = x
                            selected.rally_point_y = y
                            self.rally_point_sprite.x = x
                            self.rally_point_sprite.y = y
                            print('Rally set to ({}, {})'.format(x, y))
                        # A unit is selected
                        else:
                            for unit in our_units_list:
                                if unit == selected:
                                    if unit.destination_reached:
                                        unit.move((x, y))
                                    else:  # Movement interruption
                                        unit.destination_x = unit.target_x
                                        unit.destination_y = unit.target_y
                                        unit.movement_interrupted = True
                                        unit.new_dest_x = x
                                        unit.new_dest_y = y
                # Minimap
                elif MINIMAP_ZERO_COORDS[0] <= x <= MINIMAP_ZERO_COORDS[0] + 100 and \
                        MINIMAP_ZERO_COORDS[1] <= y <= MINIMAP_ZERO_COORDS[1] + 100:
                    if button == mouse.LEFT:
                        x -= 19 / 2
                        y -= 14 / 2
                        left_view_border = (x - MINIMAP_ZERO_COORDS[0]) * POS_SPACE
                        bottom_view_border = (y - MINIMAP_ZERO_COORDS[1]) * POS_SPACE
                        self.update_viewport()
                    elif button == mouse.RIGHT:
                        x = (x - MINIMAP_ZERO_COORDS[0]) * POS_SPACE
                        y = (y - MINIMAP_ZERO_COORDS[1]) * POS_SPACE
                        x, y = round_coords(x, y)
                        # A unit is selected
                        unit_found = False
                        for unit in our_units_list:
                            if unit == selected:
                                unit_found = True
                                if unit.destination_reached:
                                    unit.move((x, y))
                                else:  # Movement interruption
                                    unit.destination_x = unit.target_x
                                    unit.destination_y = unit.target_y
                                    unit.movement_interrupted = True
                                    unit.new_dest_x = x
                                    unit.new_dest_y = y
                        if not unit_found:
                            if selected in our_buildings_list:
                                selected.rally_point_x = x
                                selected.rally_point_y = y
                                self.rally_point_sprite.x = x
                                self.rally_point_sprite.y = y
                                print('Rally set to ({}, {})'.format(x, y))

                # Control panel other
                else:
                    x, y = mc(x=x, y=y)
                    print('x =', x, 'y =', y)
                    w = self.menu_button.width
                    h = self.menu_button.height
                    if self.menu_button.x - w // 2 <= x <= self.menu_button.x + w // 2 and \
                            self.menu_button.y - h // 2 <= y <= self.menu_button.y + h // 2:
                        print('SDFSDFSDFSDFSDF')

                    # Build units
                    if selected in our_buildings_list:
                        # Create defiler
                        if self.defiler_button.x - 16 <= x <= self.defiler_button.x + 16 and \
                                self.defiler_button.y - 16 <= y <= self.defiler_button.y + 16:
                            selected.building_queue.append('defiler')
                            if len(selected.building_queue) == 1:
                                selected.building_start_time = self.frame_count
                        # Create tank
                        elif self.tank_button.x - 16 <= x <= self.tank_button.x + 16 and \
                                self.tank_button.y - 16 <= y <= self.tank_button.y + 16:
                            selected.building_queue.append('tank')
                            if len(selected.building_queue) == 1:
                                selected.building_start_time = self.frame_count
                        # Create vulture
                        elif self.vulture_button.x - 16 <= x <= self.vulture_button.x + 16 and \
                                self.vulture_button.y - 16 <= y <= self.vulture_button.y + 16:
                            selected.building_queue.append('vulture')
                            if len(selected.building_queue) == 1:
                                selected.building_start_time = self.frame_count
                        # Create builder
                        elif self.builder_button.x - 16 <= x <= self.builder_button.x + 16 and \
                                self.builder_button.y - 16 <= y <= self.builder_button.y + 16:
                            selected.building_queue.append('builder')
                            if len(selected.building_queue) == 1:
                                selected.building_start_time = self.frame_count
                    elif selected in our_units_list:
                        # Move
                        # Stop
                        if self.stop_button.x - 16 <= x <= self.stop_button.x + 16 and \
                                self.stop_button.y - 16 <= y <= self.stop_button.y + 16:
                            selected.destination_x = selected.target_x
                            selected.destination_y = selected.target_y
                        # Attack
                        # Build
                        if str(type(selected)) == "<class '__main__.Builder'>":
                            if self.base_button.x - 16 <= x <= self.base_button.x + 16 and \
                                    self.base_button.y - 16 <= y <= self.base_button.y + 16:
                                self.base_building_sprite.color = (0, 255, 0)
                                self.building_location_selection_phase = True
                                self.to_build = "base"
                            elif self.turret_button.x - 16 <= x <= self.turret_button.x + 16 and \
                                    self.turret_button.y - 16 <= y <= self.turret_button.y + 16:
                                self.turret_building_sprite.color = (0, 255, 0)
                                self.building_location_selection_phase = True
                                self.to_build = "turret"
            # Building location selection
            else:
                # Game field
                if x < SCREEN_WIDTH - 139:
                    x, y = round_coords(x, y)
                    x, y = mc(x=x, y=y)
                    if button == mouse.LEFT:
                        mx = int((x - 16) / 32) + 1
                        my = int((y - 16) / 32) + 1
                        if not ground_pos_coords_dict[x, y] \
                                and self.npa[my, mx, 3] == 0:
                            selected.to_build = self.to_build
                            selected.building_coord_x = x
                            selected.building_coord_y = y
                            selected.move((x, y))
                            self.building_location_selection_phase = False
                    elif button == mouse.RIGHT:
                        self.building_location_selection_phase = False

    def on_mouse_motion(self, x, y, dx, dy):
        if not self.paused:
            if self.building_location_selection_phase:
                if self.fullscreen:
                    x /= 2
                    y /= 2
                x, y = round_coords(x, y)
                if self.to_build == "base":
                    self.base_building_sprite.x = x + left_view_border
                    self.base_building_sprite.y = y + bottom_view_border
                    x, y = mc(x=x, y=y)
                    x = int((x - 16) / 32) + 1
                    y = int((y - 16) / 32) + 1
                    if ground_pos_coords_dict[self.base_building_sprite.x, self.base_building_sprite.y] or \
                            self.npa[y, x, 3] != 0:
                        self.base_building_sprite.color = (255, 0, 0)
                    else:
                        self.base_building_sprite.color = (0, 255, 0)
                elif self.to_build == "turret":
                    self.turret_building_sprite.x = x + left_view_border
                    self.turret_building_sprite.y = y + bottom_view_border
                    x, y = mc(x=x, y=y)
                    x = int((x - 16) / 32) + 1
                    y = int((y - 16) / 32) + 1
                    if ground_pos_coords_dict[self.turret_building_sprite.x, self.turret_building_sprite.y] or \
                            self.npa[y, x, 3] != 0:
                        self.turret_building_sprite.color = (255, 0, 0)
                    else:
                        self.turret_building_sprite.color = (0, 255, 0)

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
                if x < SCREEN_WIDTH - 139 and buttons == 2:
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
                elif MINIMAP_ZERO_COORDS[0] <= x <= MINIMAP_ZERO_COORDS[0] + 100 and \
                        MINIMAP_ZERO_COORDS[1] <= y <= MINIMAP_ZERO_COORDS[1] + 100 and buttons in [1, 2]:
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
    #         print('sdfsdfs')
    #         bottom_view_border += POS_SPACE
    #         self.update_viewport()

    def update_viewport(self):
        global left_view_border, bottom_view_border, minimap_fow_x, minimap_fow_y

        # Viewport limits
        a = POS_COORDS_N_COLUMNS * POS_SPACE - SCREEN_WIDTH // POS_SPACE * POS_SPACE + POS_SPACE * 4
        if left_view_border < 0:
            left_view_border = 0
        elif left_view_border > a:
            left_view_border = a
        if bottom_view_border < 0:
            bottom_view_border = 0
        elif bottom_view_border > POS_COORDS_N_ROWS * POS_SPACE - SCREEN_HEIGHT:
            bottom_view_border = POS_COORDS_N_ROWS * POS_SPACE - SCREEN_HEIGHT

        self.minimap_textured_background.x = MINIMAP_ZERO_COORDS[0] + left_view_border
        self.minimap_textured_background.y = MINIMAP_ZERO_COORDS[1] + bottom_view_border
        self.control_panel_sprite.x = SCREEN_WIDTH + left_view_border
        self.control_panel_sprite.y = bottom_view_border
        self.menu_button.x = center_x + left_view_border
        self.menu_button.y = SCREEN_HEIGHT - 30 + bottom_view_border
        self.selected_frame_cp.x = center_x + left_view_border
        self.selected_frame_cp.y = SCREEN_HEIGHT - 90 + bottom_view_border
        self.control_panel_buttons_background.x = center_x + left_view_border
        self.control_panel_buttons_background.y = center_y + bottom_view_border
        self.move_button.x = CONTROL_BUTTONS_COORDS[0][0] + left_view_border
        self.move_button.y = CONTROL_BUTTONS_COORDS[0][1] + bottom_view_border
        self.stop_button.x = CONTROL_BUTTONS_COORDS[1][0] + left_view_border
        self.stop_button.y = CONTROL_BUTTONS_COORDS[1][1] + bottom_view_border
        self.attack_button.x = CONTROL_BUTTONS_COORDS[2][0] + left_view_border
        self.attack_button.y = CONTROL_BUTTONS_COORDS[2][1] + bottom_view_border
        self.base_button.x = CONTROL_BUTTONS_COORDS[3][0] + left_view_border
        self.base_button.y = CONTROL_BUTTONS_COORDS[3][1] + bottom_view_border
        self.turret_button.x = CONTROL_BUTTONS_COORDS[4][0] + left_view_border
        self.turret_button.y = CONTROL_BUTTONS_COORDS[4][1] + bottom_view_border
        self.big_base_button.x = CONTROL_BUTTONS_COORDS[5][0] + left_view_border
        self.big_base_button.y = CONTROL_BUTTONS_COORDS[5][1] + bottom_view_border
        self.defiler_button.x = CONTROL_BUTTONS_COORDS[0][0] + left_view_border
        self.defiler_button.y = CONTROL_BUTTONS_COORDS[0][1] + bottom_view_border
        self.tank_button.x = CONTROL_BUTTONS_COORDS[1][0] + left_view_border
        self.tank_button.y = CONTROL_BUTTONS_COORDS[1][1] + bottom_view_border
        self.vulture_button.x = CONTROL_BUTTONS_COORDS[2][0] + left_view_border
        self.vulture_button.y = CONTROL_BUTTONS_COORDS[2][1] + bottom_view_border
        self.builder_button.x = CONTROL_BUTTONS_COORDS[3][0] + left_view_border
        self.builder_button.y = CONTROL_BUTTONS_COORDS[3][1] + bottom_view_border
        for unit in our_units_list:
            unit.pixel.x, unit.pixel.y = to_minimap(unit.x, unit.y)
        for building in our_buildings_list:
            building.pixel.x, building.pixel.y = to_minimap(building.x, building.y)
        for enemy in enemy_buildings_list:
            enemy.pixel.x, enemy.pixel.y = to_minimap(enemy.x, enemy.y)
        self.minimap_cam_frame_sprite.x, self.minimap_cam_frame_sprite.y = to_minimap(left_view_border - 2,
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
        self.minimap_fow_ImageData.set_data('RGBA', self.minimap_fow_ImageData.width * 4,
                                            data=self.npa.tobytes())


def main():
    game_window = PlanetEleven(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    game_window.setup()
    pyglet.clock.schedule_interval(game_window.update, 1 / 60)
    pyglet.app.run()


if __name__ == "__main__":
    main()
