import math
import random
import sys
import numpy as np

import pyglet
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
    def __init__(self, img, x, y):
        super().__init__(img=img, x=x, y=y)


class Building(pyglet.sprite.Sprite):
    def __init__(self, our_img, enemy_img, x, y, hp, is_enemy):
        self.hp = hp
        ground_pos_coords_dict[(x, y)] = self
        self.rally_point_x = x
        self.rally_point_y = y
        self.building_queue = []
        self.current_building_time = None
        self.building_complete = True
        self.building_start_time = 0
        self.is_enemy = is_enemy
        if not self.is_enemy:
            our_buildings_list.append(self)
            img = our_img
            minimap_pixel = res.minimap_our_image
        else:
            enemies_list.append(self)
            img = enemy_img
            minimap_pixel = res.minimap_enemy_image
        super().__init__(img=img, x=x, y=y, batch=ground_batch)
        pixel_minimap_coords = to_minimap(self.x, self.y)
        pixel = pyglet.sprite.Sprite(img=minimap_pixel, x=pixel_minimap_coords[0],
                                     y=pixel_minimap_coords[1],
                                     batch=minimap_pixels_batch)
        minimap_pixels_dict[id(self)] = pixel

    def kill(self):
        ground_pos_coords_dict[(self.x, self.y)] = None
        minimap_pixels_dict[id(self)].delete()
        if not self.is_enemy:
            del our_buildings_list[our_buildings_list.index(self)]
        else:
            del enemies_list[enemies_list.index(self)]
        self.delete()


class Base(Building):
    def __init__(self, x, y, is_enemy=False):
        super().__init__(our_img=res.base_image, enemy_img=res.enemy_base_image, x=x, y=y, hp=100, is_enemy=is_enemy)


class Unit(pyglet.sprite.Sprite):
    def __init__(self, img, hp, vision_radius, damage, cooldown, speed, x, y,
                 projectile_sprite, projectile_speed, has_weapon=True, projectile_color=(255, 255, 255),
                 batch=ground_batch):
        super().__init__(img=img, x=x, y=y, batch=batch)
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
        pixel = pyglet.sprite.Sprite(img=res.minimap_our_image, x=pixel_minimap_coords[0],
                                     y=pixel_minimap_coords[1],
                                     batch=minimap_pixels_batch)
        minimap_pixels_dict[id(self)] = pixel

        # Shadow
        if self.flying:
            shadow = Movable(img=self.shadow_sprite, x=self.x + 10, y=self.y - 10)
            shadow.batch = air_shadows_batch
        else:
            shadow = Movable(img=self.shadow_sprite, x=self.x + 3, y=self.y - 3)
            shadow.batch = shadows_batch
        shadows_dict[id(self)] = shadow

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

        if not self.flying:
            ground_pos_coords_dict[(self.x, self.y)] = None
        else:
            air_pos_coords_dict[(self.x, self.y)] = None
        self.destination_reached = False
        self.destination_x = destination_x
        self.destination_y = destination_y
        diff_x = self.destination_x - self.x
        diff_y = self.destination_y - self.y
        angle = math.atan2(diff_y, diff_x)  # Rad
        d_angle = math.degrees(angle)
        target = give_next_target(self.x, self.y, round_angle(d_angle), self.flying)
        print('target =', target)
        if target:
            self.target_x = target[0]
            self.target_y = target[1]
            pixel = minimap_pixels_dict[id(self)]
            pixel.x, pixel.y = to_minimap(self.target_x, self.target_y)
        else:
            self.destination_reached = True
            if not self.flying:
                ground_pos_coords_dict[(self.x, self.y)] = self
            else:
                air_pos_coords_dict[(self.x, self.y)] = self
            return
        diff_x = self.target_x - self.x
        diff_y = self.target_y - self.y
        angle = math.atan2(diff_y, diff_x)  # Rad
        self.rotation = -math.degrees(angle) + 90
        self.velocity_x = math.cos(angle) * self.speed
        self.velocity_y = math.sin(angle) * self.speed
        shadow = shadows_dict[id(self)]
        shadow.rotation = -math.degrees(angle) + 90
        shadow.velocity_x = math.cos(angle) * self.speed
        shadow.velocity_y = math.sin(angle) * self.speed

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
        shadow = shadows_dict[id(self)]
        diff_x = self.destination_x - self.x
        diff_y = self.destination_y - self.y
        angle = math.atan2(diff_y, diff_x)  # Rad
        d_angle = math.degrees(angle)
        self.rotation = -d_angle + 90
        shadow.rotation = -math.degrees(angle) + 90
        next_target = give_next_target(self.x, self.y, round_angle(d_angle), self.flying)
        print('next_target =', next_target)
        if next_target:
            if not self.flying:
                ground_pos_coords_dict[(self.x, self.y)] = None
            else:
                air_pos_coords_dict[(self.x, self.y)] = None
            self.target_x = next_target[0]
            self.target_y = next_target[1]
            pixel = minimap_pixels_dict[id(self)]
            pixel.x, pixel.y = to_minimap(self.target_x, self.target_y)
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
            shadow.rotation = -math.degrees(angle) + 90
            shadow.velocity_x = math.cos(angle) * self.speed
            shadow.velocity_y = math.sin(angle) * self.speed
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

    def shoot(self, frame_count, target_x, target_y, target_id):
        global projectile_list
        projectile = Projectile(x=self.x, y=self.y,
                                target_x=target_x, target_y=target_y,
                                damage=self.damage, speed=self.projectile_speed, target_id=target_id)
        x_diff = target_x - self.x
        y_diff = target_y - self.y
        angle = -math.degrees(math.atan2(y_diff, x_diff)) + 90
        self.rotation = angle
        shadow = shadows_dict[id(self)]
        shadow.rotation = angle
        self.on_cooldown = True
        self.cooldown_started = frame_count
        projectile_list.append(projectile)

    def kill(self):
        shadows_dict[id(self)].delete()
        minimap_pixels_dict[id(self)].delete()
        del our_units_list[our_units_list.index(self)]
        self.delete()


class Defiler(Unit):
    building_time = 60

    def __init__(self, x, y):
        super().__init__(img=res.defiler_image, hp=100, vision_radius=6, damage=10, cooldown=60, speed=6, x=x,
                         y=y, projectile_sprite='sprites/blue_laser.png',
                         projectile_speed=5, batch=air_batch)
        self.flying = True
        self.shadow_sprite = res.defiler_shadow_image


class Tank(Unit):
    building_time = 60

    def __init__(self, x, y):
        super().__init__(img=res.tank_image, hp=100, vision_radius=6, damage=10, cooldown=60, speed=0.6, x=x,
                         y=y, projectile_sprite='sprites/blue_laser.png',
                         projectile_speed=5)
        self.flying = False
        self.shadow_sprite = res.tank_shadow_image


class Vulture(Unit):
    building_time = 10

    def __init__(self, x, y):
        super().__init__(img=res.vulture_image, hp=50, vision_radius=3, damage=10, cooldown=60, speed=10,
                         x=x, y=y, projectile_sprite='sprites/blue_laser.png',
                         projectile_speed=5)
        self.flying = False
        self.shadow_sprite = res.vulture_shadow_image


class Builder(Unit):
    building_time = 10

    def __init__(self, x, y):
        super().__init__(img=res.builder_image, hp=50, vision_radius=2, damage=0, cooldown=60, speed=2,
                         x=x, y=y, has_weapon=False, projectile_sprite='sprites/blue_laser.png',
                         projectile_speed=5)
        self.flying = False
        self.shadow_sprite = res.builder_shadow_image


class PlanetEleven(pyglet.window.Window):
    def __init__(self, width, height, title):
        conf = Config(sample_buffers=1,
                      samples=4,
                      depth_size=16,
                      double_buffer=True)
        super().__init__(width, height, title, config=conf, fullscreen=False)
        self.set_mouse_cursor(cursor)
        self.paused = False
        self.frame_count = 0
        self.dx = 0
        self.dy = 0
        self.minimap_drugging = False
        self.building_location_selection_phase = False
        self.fps_display = pyglet.window.FPSDisplay(window=self)

    def setup(self):
        global selected
        self.background = pyglet.sprite.Sprite(img=res.background_image, x=0, y=0)
        self.control_panel_sprite = pyglet.sprite.Sprite(img=res.control_panel_image, x=SCREEN_WIDTH, y=0)
        self.control_panel_buttons_background = pyglet.sprite.Sprite(img=res.control_panel_buttons_background_image,
                                                                     x=center_x, y=center_y)
        self.minimap_black_background = pyglet.sprite.Sprite(img=res.minimap_black_background_image,
                                                             x=MINIMAP_ZERO_COORDS[0], y=MINIMAP_ZERO_COORDS[1])
        self.minimap_textured_background = pyglet.sprite.Sprite(img=res.minimap_textured_background_image,
                                                             x=MINIMAP_ZERO_COORDS[0], y=MINIMAP_ZERO_COORDS[1])
        self.minimap_cam_frame_sprite = pyglet.sprite.Sprite(img=res.minimap_cam_frame_image, x=MINIMAP_ZERO_COORDS[0]-1,
                                                             y=MINIMAP_ZERO_COORDS[1]-1)
        self.minimap_fow_image = pyglet.image.load('sprites/minimap_fow.png')
        self.minimap_fow_ImageData = self.minimap_fow_image.get_image_data()
        self.npa = np.fromstring(self.minimap_fow_ImageData.get_data('RGBA', self.minimap_fow_ImageData.width * 4), dtype=np.uint8)
        self.npa = self.npa.reshape((102, 102, 4))

        # Spawn
        self.our_1st_base = Base(POS_SPACE / 2 + POS_SPACE, POS_SPACE / 2 + POS_SPACE)
        selected = self.our_1st_base
        Base(POS_SPACE / 2 + POS_SPACE * 3, POS_SPACE / 2 + POS_SPACE)
        Base(POS_SPACE / 2 + POS_SPACE * 4, POS_SPACE / 2 + POS_SPACE * 6, is_enemy=True)
        Base(POS_SPACE / 2 + POS_SPACE * 10, POS_SPACE / 2 + POS_SPACE * 8, is_enemy=True)
        Base(POS_SPACE / 2 + POS_SPACE * 12, POS_SPACE / 2 + POS_SPACE * 8, is_enemy=True)
        Base(POS_SPACE / 2 + POS_SPACE * 8, POS_SPACE / 2 + POS_SPACE * 6, is_enemy=True)

        # Buttons
        self.base_button = Button(img=res.base_image, x=CONTROL_BUTTONS_COORDS[3][0],
                                  y=CONTROL_BUTTONS_COORDS[3][1])
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
                                                     y=self.our_1st_base.y, batch=utilities_batch)
        self.rally_point_sprite = pyglet.sprite.Sprite(img=res.rally_point_image, x=self.our_1st_base.rally_point_x,
                                                       y=self.our_1st_base.rally_point_y)


        # self.dots = []
        # for x, y in POS_COORDS:
        #     dot = pyglet.sprite.Sprite(img=res.utility_dot_image, x=x, y=y, batch=utilities_batch)
        #     self.dots.append(dot)

        self.basic_unit_control_buttons = [self.move_button, self.stop_button, self.attack_button]
        self.controls_dict = {"<class '__main__.Base'>": [self.defiler_button, self.tank_button, self.vulture_button,
                                                          self.builder_button],
                        "<class '__main__.Defiler'>": self.basic_unit_control_buttons,
                        "<class '__main__.Tank'>": self.basic_unit_control_buttons,
                        "<class '__main__.Vulture'>": self.basic_unit_control_buttons,
                        "<class '__main__.Builder'>": self.basic_unit_control_buttons + [self.base_button]}
        self.control_buttons_to_render = self.controls_dict["<class '__main__.Base'>"]
        self.base_building_sprite = pyglet.sprite.Sprite(img=res.base_image, x=-100, y=-100)
        self.base_building_sprite.color = (0, 255, 0)


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
        ground_batch.draw()
        air_shadows_batch.draw()
        air_batch.draw()
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.texture = self.minimap_fow_image.get_texture()
        self.texture.width = 3264
        self.texture.height = 3264
        self.texture.blit(-32, -32)
        utilities_batch.draw()
        if self.building_location_selection_phase:
            self.base_building_sprite.draw()
        self.control_panel_sprite.draw()
        self.control_panel_buttons_background.draw()
        self.minimap_black_background.draw()
        self.minimap_textured_background.draw()
        minimap_pixels_batch.draw()

        for button in self.control_buttons_to_render:
            button.draw()
        if selected in our_buildings_list:
            self.rally_point_sprite.draw()

        self.texture.width = 102
        self.texture.height = 102
        self.texture.blit(minimap_fow_x, minimap_fow_y)

        self.minimap_cam_frame_sprite.draw()

        for projectile in projectile_list:
            projectile.draw()

        self.fps_display.draw()

        # Remove default modelview matrix
        glPopMatrix()

    def update(self, delta_time):
        if not self.paused:
            global minimap_pixels_dict
            self.frame_count += 1
            # Units
            # Building units
            for building in our_buildings_list:
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
                        if dict_to_check[(building.x + POS_SPACE, building.y + POS_SPACE)] is None:
                            unit = building.building_queue.pop(0)
                            if unit == 'defiler':
                                unit = Defiler(x=building.x + POS_SPACE, y=building.y + POS_SPACE)
                                unit.spawn()
                            elif unit == 'tank':
                                unit = Tank(x=building.x + POS_SPACE, y=building.y + POS_SPACE)
                                unit.spawn()
                            elif unit == 'vulture':
                                unit = Vulture(x=building.x + POS_SPACE, y=building.y + POS_SPACE)
                                unit.spawn()
                            elif unit == 'builder':
                                unit = Builder(x=building.x + POS_SPACE, y=building.y + POS_SPACE)
                                unit.spawn()
                            building.building_start_time += building.current_building_time
                            unit.move((building.rally_point_x, building.rally_point_y))
                        else:
                            building.building_start_time += 1
                            print('No space')

            # Movement
            for unit in our_units_list:
                shadow = shadows_dict[id(unit)]
                # Selection
                if selected == unit:
                    self.selection_sprite.x = unit.x
                    self.selection_sprite.y = unit.y
                # Do not jump
                if not unit.destination_reached:
                    if not unit.eta() <= 1:
                        unit.update()
                        shadow.update()
                    # Jump
                    else:
                        if not unit.movement_interrupted:
                            unit.x = unit.target_x
                            unit.y = unit.target_y
                            if unit.flying:
                                shadow.x = unit.target_x + 10
                                shadow.y = unit.target_y - 10
                            else:
                                shadow.x = unit.target_x + 3
                                shadow.y = unit.target_y - 3
                            if not unit.flying:
                                ground_pos_coords_dict[(unit.target_x, unit.target_y)] = unit
                            else:
                                air_pos_coords_dict[(unit.target_x, unit.target_y)] = unit
                            if unit.x == unit.destination_x and unit.y == unit.destination_y:
                                unit.destination_reached = True
                            else:
                                unit.update_movement()
                        else:
                            unit.x = unit.target_x
                            unit.y = unit.target_y
                            if unit.flying:
                                shadow.x = unit.target_x + 10
                                shadow.y = unit.target_y - 10
                            else:
                                shadow.x = unit.target_x + 3
                                shadow.y = unit.target_y - 3
                            if not unit.flying:
                                ground_pos_coords_dict[(unit.target_x, unit.target_y)] = unit
                            else:
                                air_pos_coords_dict[(unit.target_x, unit.target_y)] = unit
                            unit.destination_reached = True
                            unit.move((unit.new_dest_x, unit.new_dest_y))
                            unit.movement_interrupted = False
                        self.update_fow(unit.x, unit.y, unit.vision_radius)
            # Shooting
            for unit in our_units_list:
                if unit.has_weapon:
                    if unit.destination_reached:
                        if not unit.on_cooldown:
                            for enemy in enemies_list:
                                if ((enemy.x - unit.x) ** 2 + (enemy.y - unit.y) ** 2) ** 0.5 <= unit.shooting_radius:
                                    unit.shoot(self.frame_count, enemy.x, enemy.y, enemy)
                                    break
                        else:
                            if (self.frame_count - unit.cooldown_started) % unit.cooldown == 0:
                                unit.on_cooldown = False

            # Projectiles
            for i, projectile in enumerate(projectile_list):
                if not projectile.eta() <= 1:
                    projectile.update()
                else:
                    projectile.target_id.hp -= projectile.damage
                    projectile.delete()
                    del projectile_list[i]

            # Destroying
            for enemy in enemies_list:
                if enemy.hp <= 0:
                    enemy.kill()

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

    def on_key_press(self, symbol, modifiers):
        """Called whenever a key is pressed. """
        global selected, left_view_border, bottom_view_border
        if symbol == key.F:
            if self.fullscreen:
                self.set_mouse_cursor(cursor)
                self.set_fullscreen(False)
            else:
                self.set_mouse_cursor(cursor_fullscreen)
                self.set_fullscreen(True)
        elif symbol in [key.LEFT, key.A]:
            left_view_border -= POS_SPACE
            self.update_viewport()
        elif symbol in [key.RIGHT, key.D]:
            left_view_border += POS_SPACE
            self.update_viewport()
        elif symbol in [key.DOWN, key.S]:
            bottom_view_border -= POS_SPACE
            self.update_viewport()
        elif symbol in [key.UP, key.W]:
            bottom_view_border += POS_SPACE
            self.update_viewport()
        elif symbol == key.H:
            self.minimap_fow_bytearray[7] = 0
            self.minimap_fow_ImageData.set_data('RGBA', self.minimap_fow_ImageData.width * 4,
                                                data=bytes(self.minimap_fow_bytearray))
        elif symbol == key.Z:
            i = 0
            for _key, value in ground_pos_coords_dict.items():
                if i % 1 == 0:
                    if value is None:
                        unit = Vulture(_key[0], _key[1])
                        unit.spawn()
                i += 1
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
            if not self.paused:
                self.paused = True
            else:
                self.paused = False
        elif symbol == key.ESCAPE:
            sys.exit()

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

        self.minimap_black_background.x = MINIMAP_ZERO_COORDS[0] + left_view_border
        self.minimap_black_background.y = MINIMAP_ZERO_COORDS[1] + bottom_view_border
        self.minimap_textured_background.x = MINIMAP_ZERO_COORDS[0] + left_view_border
        self.minimap_textured_background.y = MINIMAP_ZERO_COORDS[1] + bottom_view_border
        self.control_panel_sprite.x = SCREEN_WIDTH + left_view_border
        self.control_panel_sprite.y = bottom_view_border
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
        self.defiler_button.x = CONTROL_BUTTONS_COORDS[0][0] + left_view_border
        self.defiler_button.y = CONTROL_BUTTONS_COORDS[0][1] + bottom_view_border
        self.tank_button.x = CONTROL_BUTTONS_COORDS[1][0] + left_view_border
        self.tank_button.y = CONTROL_BUTTONS_COORDS[1][1] + bottom_view_border
        self.vulture_button.x = CONTROL_BUTTONS_COORDS[2][0] + left_view_border
        self.vulture_button.y = CONTROL_BUTTONS_COORDS[2][1] + bottom_view_border
        self.builder_button.x = CONTROL_BUTTONS_COORDS[3][0] + left_view_border
        self.builder_button.y = CONTROL_BUTTONS_COORDS[3][1] + bottom_view_border
        for unit in our_units_list:
            pixel = minimap_pixels_dict[id(unit)]
            pixel.x, pixel.y = to_minimap(unit.x, unit.y)
        for building in our_buildings_list:
            pixel = minimap_pixels_dict[id(building)]
            pixel.x, pixel.y = to_minimap(building.x, building.y)
        for enemy in enemies_list:
            pixel = minimap_pixels_dict[id(enemy)]
            pixel.x, pixel.y = to_minimap(enemy.x, enemy.y)
        self.minimap_cam_frame_sprite.x, self.minimap_cam_frame_sprite.y = to_minimap(left_view_border-2,
                                                                                      bottom_view_border-2)
        minimap_fow_x = MINIMAP_ZERO_COORDS[0] - 1 + left_view_border
        minimap_fow_y = MINIMAP_ZERO_COORDS[1] - 1 + bottom_view_border

    def on_mouse_press(self, x, y, button, modifiers):
        global selected, minimap_pixels_dict, our_units_list, left_view_border, bottom_view_border
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
            # Control panel other
            else:
                x, y = mc(x=x, y=y)
                print('x =', x, 'y =', y)
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
                    # Attack
                    if str(type(selected)) == "<class '__main__.Builder'>":
                        if self.base_button.x - 16 <= x <= self.base_button.x + 16 and \
                                self.base_button.y - 16 <= y <= self.base_button.y + 16:
                            self.base_building_sprite.color = (0, 255, 0)
                            self.building_location_selection_phase = True
        # Building location selection
        else:
            # Game field
            if x < SCREEN_WIDTH - 139:
                x, y = round_coords(x, y)
                x, y = mc(x=x, y=y)
                if button == mouse.LEFT:
                    if not ground_pos_coords_dict[self.base_building_sprite.x, self.base_building_sprite.y]:
                        Base(self.base_building_sprite.x, self.base_building_sprite.y)
                elif button == mouse.RIGHT:
                    self.building_location_selection_phase = False

    def on_mouse_motion(self, x, y, dx, dy):
        if self.building_location_selection_phase:
            x, y = round_coords(x, y)
            if self.fullscreen:
                x /= 2
                y /= 2
            self.base_building_sprite.x, self.base_building_sprite.y = x, y
            if ground_pos_coords_dict[self.base_building_sprite.x, self.base_building_sprite.y]:
                self.base_building_sprite.color = (255, 0, 0)
            else:
                self.base_building_sprite.color = (0, 255, 0)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        global left_view_border, bottom_view_border
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


def main():
    game_window = PlanetEleven(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    game_window.setup()
    pyglet.clock.schedule_interval(game_window.update, 1 / 60)
    pyglet.app.run()


if __name__ == "__main__":
    main()
