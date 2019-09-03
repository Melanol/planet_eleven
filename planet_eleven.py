import math
import random
import sys

import pyglet
from pyglet import gl
from pyglet.window import key
from pyglet.window import mouse

import resources
from draw_dot import draw_dot

# TODO: Proper pathfinding
# TODO: Diagonal movement interception
# TODO: Waypoint shooting
# TODO: Unit following unit movement
# TODO: Fix coordinates and UI
# TODO: No-space spawning
# TODO: Finalize minimap
# TODO: On-sprite shadows
SCREEN_WIDTH = 683
SCREEN_HEIGHT = 384
SCREEN_TITLE = "Planet Eleven"
reversed_left_view_border = 0
reversed_bottom_view_border = 0
POS_SPACE = 32
SELECTION_RADIUS = 20
selected = None



MINIMAP_ZERO_COORDS = (SCREEN_WIDTH - 120, SCREEN_HEIGHT - 230)

# Generate positional coordinates:
POS_COORDS_N_COLUMNS = 13
POS_COORDS_N_ROWS = 20
POS_COORDS = []
for yi in range(1, POS_COORDS_N_ROWS + 1):
    for xi in range(1, POS_COORDS_N_COLUMNS + 1):
        POS_COORDS.append((xi * POS_SPACE - POS_SPACE / 2, yi * POS_SPACE - POS_SPACE / 2))
pos_coords_dict = {}
for x, y in POS_COORDS:
    pos_coords_dict[(x, y)] = None

DISTANCE_PER_JUMP = (2 * POS_SPACE ** 2) ** 0.5
minimap_pixels_dict = {}
shadows_dict = {}

ground_batch = pyglet.graphics.Batch()
buttons_batch = pyglet.graphics.Batch()
utilities_batch = pyglet.graphics.Batch()
minimap_pixels_batch = pyglet.graphics.Batch()
shadows_batch = pyglet.graphics.Batch()

unit_list = []
projectile_list = []


def round_coords(x, y):
    global reversed_left_view_border, reversed_bottom_view_border
    print('left_view_border =', reversed_left_view_border, 'bottom_view_border =', reversed_bottom_view_border)
    sel_x = POS_SPACE / 2 * round(x / (POS_SPACE / 2))
    sel_y = POS_SPACE / 2 * round(y / (POS_SPACE / 2))
    print('sel_x =', sel_x, 'sel_y =', sel_y)
    if sel_x % POS_SPACE == 0:
        if x > sel_x:
            sel_x += POS_SPACE / 2
        else:
            sel_x -= POS_SPACE / 2
    if sel_y % POS_SPACE == 0:
        if y > sel_y:
            sel_y += POS_SPACE / 2
        else:
            sel_y -= POS_SPACE / 2
    sel_x -= reversed_left_view_border
    sel_y -= reversed_bottom_view_border
    print('sel_x =', sel_x, 'sel_y =', sel_y)
    return sel_x, sel_y


def round_angle(angle):
    return 45 * round(angle / 45)


def give_next_target(x, y, angle):
    print('give_next_target:', x, y, angle)
    if angle == 0:
        target = (x + POS_SPACE, y)
        target_id = pos_coords_dict[target]
    elif angle == 45:
        target = round_coords(x + DISTANCE_PER_JUMP, y + DISTANCE_PER_JUMP)
        target_id = pos_coords_dict[target]
    elif angle == 90:
        target = (x, y + POS_SPACE)
        target_id = pos_coords_dict[target]
    elif angle == 135:
        target = round_coords(x - DISTANCE_PER_JUMP, y + DISTANCE_PER_JUMP)
        target_id = pos_coords_dict[target]
    elif angle in [-180, 180]:
        target = (x - POS_SPACE, y)
        target_id = pos_coords_dict[target]
    elif angle == -135:
        target = round_coords(x - DISTANCE_PER_JUMP, y - DISTANCE_PER_JUMP)
        target_id = pos_coords_dict[target]
    elif angle == -90:
        target = (x, y - POS_SPACE)
        target_id = pos_coords_dict[target]
    elif angle == -45:
        target = round_coords(x + DISTANCE_PER_JUMP, y - DISTANCE_PER_JUMP)
        target_id = pos_coords_dict[target]
    else:
        raise Exception('bad angle')
    print('target_id =', target_id)
    if target_id is None:
        print('target =', target)
        return target
    else:
        print('target =', None)
        return None


def convert_to_minimap(x, y):
    x = x / POS_SPACE
    if not x.is_integer():
        x += 1
    x = MINIMAP_ZERO_COORDS[0] + x
    y = y / POS_SPACE
    if not y.is_integer():
        y += 1
    y = MINIMAP_ZERO_COORDS[1] + y
    return x, y


class Button(pyglet.sprite.Sprite):
    def __init__(self, img, x, y):
        super().__init__(img=img, x=x, y=y, batch=buttons_batch)


class Base(pyglet.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__(img=resources.base_image, x=x, y=x, batch=ground_batch)
        self.center_x = x
        self.center_y = x
        self.hp = 100
        pos_coords_dict[(x, y)] = id(self)
        self.rally_point_x = POS_SPACE * 2 - POS_SPACE / 2
        self.rally_point_y = POS_SPACE * 2 - POS_SPACE / 2
        self.building_queue = []
        self.current_building_time = None
        self.building_complete = True
        self.building_start_time = 0


class Unit(pyglet.sprite.Sprite):
    def __init__(self, img, hp, damage, cooldown, speed, x, y,
                 projectile_sprite, projectile_speed, batch, projectile_color=(255, 255, 255)):
        super().__init__(img=img, x=x, y=y, batch=batch)
        self.x = x
        self.y = y
        self.hp = hp
        self.damage = damage
        self.speed = speed
        self.destination_reached = True
        self.movement_interrupted = False
        self.cooldown = cooldown
        self.on_cooldown = False
        self.cooldown_started = None
        self.projectile_sprite = projectile_sprite
        self.projectile_speed = projectile_speed
        self.projectile_color = projectile_color

    def move(self, destination_x, destination_y):
        # Called once by RMB or when a unit is created

        # Not moving: same coords
        if self.x == destination_x and self.y == destination_y:
            pos_coords_dict[(self.x, self.y)] = id(self)
            self.destination_reached = True
            return

        pos_coords_dict[(self.x, self.y)] = None
        self.destination_reached = False
        self.destination_x = destination_x
        self.destination_y = destination_y
        diff_x = self.destination_x - self.x
        diff_y = self.destination_y - self.y
        angle = math.atan2(diff_y, diff_x)  # Rad
        d_angle = math.degrees(angle)
        target = give_next_target(self.x, self.y, round_angle(d_angle))
        if target:
            self.target_x = target[0]
            self.target_y = target[1]
        else:
            self.destination_reached = True
            pos_coords_dict[(self.x, self.y)] = id(self)
            return
        diff_x = self.target_x - self.x
        diff_y = self.target_y - self.y
        angle = math.atan2(diff_y, diff_x)  # Rad
        self.rotate = math.degrees(angle) - 90
        self.velocity_x = math.cos(angle) * self.speed
        self.velocity_y = math.sin(angle) * self.speed
        shadow = shadows_dict[id(self)]
        shadow.angle = math.degrees(angle) - 90
        shadow.velocity_x = math.cos(angle) * self.speed
        shadow.velocity_y = math.sin(angle) * self.speed

        pos_coords_dict[(self.target_x, self.target_y)] = id(self)

    def distance_to_target(self):
        return ((self.target_x - self.x) ** 2 + (self.target_y - self.y) ** 2) ** 0.5

    def eta(self):
        return self.distance_to_target() / self.speed

    def update_movement(self):
        # Called by update to move to the next point
        print('\nupdate_movement({}, {})'.format(self.x, self.y))
        pos_coords_dict[(self.x, self.y)] = None
        shadow = shadows_dict[id(self)]
        diff_x = self.destination_x - self.x
        diff_y = self.destination_y - self.y
        angle = math.atan2(diff_y, diff_x)  # Rad
        d_angle = math.degrees(angle)
        self.rotate = d_angle - 90
        shadow.angle = math.degrees(angle) - 90
        next_target = give_next_target(self.x, self.y, round_angle(d_angle))
        print('next_target =', next_target)
        if next_target:
            pos_coords_dict[(self.x, self.y)] = None
            self.target_x = next_target[0]
            self.target_y = next_target[1]
            pixel = minimap_pixels_dict[id(self)]
            pixel.x, pixel.x = convert_to_minimap(self.target_x, self.target_y)
            pos_coords_dict[(self.target_x, self.target_y)] = id(self)
            diff_x = self.target_x - self.x
            diff_y = self.target_y - self.y
            angle = math.atan2(diff_y, diff_x)  # Rad
            d_angle = math.degrees(angle)
            self.rotate = d_angle - 90
            self.velocity_x = math.cos(angle) * self.speed
            self.velocity_y = math.sin(angle) * self.speed
            shadow.angle = math.degrees(angle) - 90
            shadow.change_x = math.cos(angle) * self.speed
            shadow.change_y = math.sin(angle) * self.speed
        else:
            pos_coords_dict[(self.x, self.y)] = id(self)
            self.destination_reached = True
        if self.x == self.destination_x and self.y == self.destination_y:
            print('Destination reached')
            self.destination_reached = True
            print('self.destination_reached =', self.destination_reached)
        print()

    def shoot(self, frame_count, enemy_base_x, enemy_base_y):
        projectile = Projectile(img=self.projectile_sprite, x=self.x, y=self.y,
                                target_x=enemy_base_x, target_y=enemy_base_y,
                                damage=self.damage, speed=self.projectile_speed, projectile_color=self.projectile_color)
        x_diff = enemy_base_x - self.x
        y_diff = enemy_base_y - self.y
        self.rotate = math.degrees(math.atan2(y_diff, x_diff)) - 90
        self.on_cooldown = True
        self.cooldown_started = frame_count


class Defiler(Unit):
    building_time = 60

    def __init__(self, x, y):
        super().__init__(img=resources.defiler_image, hp=100, damage=10, cooldown=60, speed=3, x=x,
                         y=y, projectile_sprite='sprites/laserBlue01.png',
                         projectile_speed=10)


class Tank(Unit):
    building_time = 60

    def __init__(self, x, y):
        super().__init__(img=resources.tank_image, hp=100, damage=10, cooldown=60, speed=0.6, x=x,
                         y=y, projectile_sprite='sprites/laserBlue01.png',
                         projectile_speed=10)


class Vulture(Unit):
    building_time = 100

    def __init__(self, x, y):
        super().__init__(img=resources.vulture_image, hp=50, damage=10, cooldown=60, speed=10,
                         x=x, y=y, projectile_sprite='sprites/laserBlue01.png',
                         projectile_speed=10, batch=ground_batch)


class Projectile(pyglet.sprite.Sprite):
    def __init__(self, img, x, y, target_x, target_y, damage, speed, projectile_color):
        super().__init__(img=img, x=x, y=y)
        self._set_color(projectile_color)
        self.damage = damage
        self.speed = speed

        x_diff = target_x - x
        y_diff = target_y - y
        angle = math.atan2(y_diff, x_diff)
        self.angle = math.degrees(angle)

        # Speed:
        self.change_x = math.cos(angle) * speed
        self.change_y = math.sin(angle) * speed


class Planet_Eleven(pyglet.window.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title, fullscreen=False)

        self.frame_count = 0
        # This will get the size of the window, and set the viewport to match.
        # So if the window is 1000x1000, then so will our viewport. If
        # you want something different, then use those coordinates instead.
        width, height = self.get_size()

    def setup(self):
        global selected
        self.our_base = Base(POS_SPACE / 2 + POS_SPACE, POS_SPACE / 2 + POS_SPACE)
        selected = id(self.our_base)
        self.enemy_base = Base(POS_SPACE / 2 + POS_SPACE * 8, POS_SPACE / 2 + POS_SPACE * 8)
        '''self.walls = arcade.SpriteList(use_spatial_hash=False)
        wall_coords = [(105, 165), (105, 195), (105, 225), (105, 255), (105, 285), (105, 315), (165, 165), (165, 195),
                       (165, 225), (165, 285), (165, 315), (195, 225), (195, 285)]
        for coord in wall_coords:
            x = coord[0]
            y = coord[1]
            wall = arcade.Sprite(filename='sprites/wall.png', center_x=x, center_y=y)
            self.walls.append(wall)
            pos_coords_dict[(x, y)] = id(wall)'''

        self.defiler_button = Button(img=resources.defiler_image, x=570, y=130)
        self.tank_button = Button(img=resources.tank_image, x=615, y=130)
        self.vulture_button = Button(img=resources.vulture_image, x=660, y=130)

        self.selection_sprite = pyglet.sprite.Sprite(img=resources.selection_image, x=self.our_base.center_x,
                                                     y=self.our_base.center_y, batch=utilities_batch)
        self.rally_point_sprite = pyglet.sprite.Sprite(img=resources.rally_point_image, x=self.our_base.rally_point_x,
                                                       y=self.our_base.rally_point_y)

        #self.control_panel = pyglet.resource.image("control_panel.png")

        self.dots = []
        for x, y in POS_COORDS:
            dot = pyglet.sprite.Sprite(img=resources.minimap_ally_image, x=x, y=y, batch=utilities_batch)
            self.dots.append(dot)

        '''self.terrain = arcade.SpriteList(use_spatial_hash=False)
        for coord in POS_COORDS:
            angle = random.choice([0, 90, 180, 270])
            filename = random.choice(['sprites/sand1.png'])
            sand = arcade.Sprite(filename=filename, center_x=coord[0], center_y=coord[1])
            #sand._set_angle(angle)
            self.terrain.append(sand)'''

    def on_draw(self):
        """
        Render the screen.
        """
        self.clear()

        '''for x, y in POS_COORDS:
            draw_dot(x, y, 2)'''

        ground_batch.draw()
        utilities_batch.draw()

        #self.walls.draw()
        '''self.shadows.draw()
        self.unit_list.draw()
        self.selection_sprite.draw()'''

        if selected == id(self.our_base):  # Our base
            buttons_batch.draw()
            self.rally_point_sprite.draw()

        for _key, value in pos_coords_dict.items():
            x = _key[0]
            y = _key[1]
            if value:
                draw_dot(x, y, 10)

        #self.control_panel.blit(300, 0)

        minimap_pixels_batch.draw()


    def update(self, delta_time):
        global minimap_pixels_dict
        self.frame_count += 1
        # Units
        # Movement
        for unit in unit_list:
            shadow = shadows_dict[id(unit)]
            # Selection
            if selected == id(unit):
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
                        shadow.x = unit.target_x + 3
                        shadow.y = unit.target_y - 3
                        pos_coords_dict[(unit.target_x, unit.target_y)] = id(unit)
                        if unit.x == unit.destination_x and unit.y == unit.destination_y:
                            unit.destination_reached = True
                        else:
                            unit.update_movement()
                    else:
                        unit.x = unit.target_x
                        unit.y = unit.target_y
                        shadow.x = unit.target_x + 3
                        shadow.y = unit.target_y - 3
                        pos_coords_dict[(unit.target_x, unit.target_y)] = id(unit)
                        unit.destination_reached = True
                        unit.move(unit.new_dest_x, unit.new_dest_y)
                        unit.movement_interrupted = False


        '''# Shooting at enemy base:
        projectile_list.update()
        for unit in self.unit_list:
            if not unit.on_cooldown:
                if ((self.enemy_base.center_x - unit.center_x) ** 2 +
                    (self.enemy_base.center_y - unit.center_y) ** 2) ** 0.5 <= 100:
                    unit.shoot(self.frame_count, self.enemy_base.center_x, self.enemy_base.center_y)
            else:
                if (self.frame_count - unit.cooldown_started) % unit.cooldown == 0:
                    unit.on_cooldown = False
        projectile_hit_list = arcade.check_for_collision_with_list(self.enemy_base, projectile_list)
        for projectile in projectile_hit_list:
            projectile.kill()
            projectile_list.update()
            self.enemy_base.hp -= projectile.damage'''

        # Building units
        if self.our_base.building_queue:
            if self.frame_count - self.our_base.building_start_time == self.our_base.current_building_time:
                if pos_coords_dict[(self.our_base.x + POS_SPACE, self.our_base.y + POS_SPACE)] is None:
                    unit = self.our_base.building_queue.pop(0)
                    unit_list.append(unit)
                    self.our_base.building_start_time += self.our_base.current_building_time
                    unit.move(self.our_base.rally_point_x, self.our_base.rally_point_y)
                    pixel = pyglet.sprite.Sprite(img=resources.minimap_ally_image, x=unit.x, y=unit.y,
                                                 batch=minimap_pixels_batch)
                    minimap_pixels_dict[id(unit)] = pixel
                    shadow = pyglet.sprite.Sprite(img=resources.vulture_shadow_image, x=unit.x + 3, y=unit.y - 3,
                                                  batch=shadows_batch)
                    shadows_dict[id(unit)] = shadow
                else:
                    self.our_base.building_start_time += 1
                    print('No space')

    def on_key_press(self, symbol, modifiers):
        """Called whenever a key is pressed. """
        global selected, reversed_left_view_border, reversed_bottom_view_border
        if symbol == key.F:
            self.set_fullscreen(True)
        elif symbol == key.W:
            self.set_fullscreen(False)
        elif symbol == key.LEFT:
            reversed_left_view_border += POS_SPACE
            self.update_viewport()
        elif symbol == key.RIGHT:
            reversed_left_view_border -= POS_SPACE
            self.update_viewport()
        elif symbol == key.DOWN:
            reversed_bottom_view_border += POS_SPACE
            self.update_viewport()
        elif symbol == key.UP:
            reversed_bottom_view_border -= POS_SPACE
            self.update_viewport()
        elif symbol == key.DELETE:
            for unit in self.unit_list:
                if selected == id(unit):
                    unit.kill()
                    pos_coords_dict[(self.selection_sprite.center_x, self.selection_sprite.center_y)] = None
                    selected = None
        elif symbol == key.ESCAPE:
            sys.exit()
        '''elif symbol == key.Z:
            for key, value in pos_coords_dict.items():
                if value is None:
                    unit = Vulture(key[0], key[1])
                    self.unit_list.append(unit)
                    pos_coords_dict[key] = id(unit)'''


    def update_viewport(self):
        global reversed_left_view_border, reversed_bottom_view_border
        # Viewport limits
        if reversed_left_view_border > 0:
            reversed_left_view_border = 0
        if reversed_bottom_view_border > 0:
            reversed_bottom_view_border = 0
        elif abs(reversed_bottom_view_border) > POS_COORDS_N_ROWS * POS_SPACE - SCREEN_HEIGHT:
            reversed_bottom_view_border = -(POS_COORDS_N_ROWS * POS_SPACE - SCREEN_HEIGHT)

        gl.glViewport(reversed_left_view_border, reversed_bottom_view_border, SCREEN_WIDTH, SCREEN_HEIGHT)

        self.control_panel.center_x = SCREEN_WIDTH - 139 / 2 + reversed_left_view_border
        self.control_panel.center_y = SCREEN_HEIGHT / 2 + reversed_bottom_view_border
        self.soldier_button.center_x = 570 + reversed_left_view_border
        self.soldier_button.center_y = 130 + reversed_bottom_view_border
        self.tank_button.center_x = 615 + reversed_left_view_border
        self.tank_button.center_y = 130 + reversed_bottom_view_border
        self.vulture_button.center_x = 660 + reversed_left_view_border
        self.vulture_button.center_y = 130 + reversed_bottom_view_border
        print(self.soldier_button.center_y)
        print(self.left_view_border)
        print(self.bottom_view_border)


    def on_mouse_press(self, x, y, button, modifiers):
        global selected, minimap_pixels_dict, unit_list
        print('click coords: ', x, y)
        if button == mouse.LEFT:
            # Create defiler:
            '''if abs(x - self.defiler_button.center_x) <= SELECTION_RADIUS \
                    and abs(y - self.defiler_button.center_y) <= SELECTION_RADIUS:
                unit = Defiler(center_x=self.our_base.center_x + POS_SPACE, center_y=self.our_base.center_y + POS_SPACE)
                self.our_base.building_queue.append(unit)
                self.our_base.current_building_time = Defiler.building_time
                if len(self.our_base.building_queue) == 1:
                    self.our_base.building_start_time = self.frame_count
            # Create tank:
            elif abs(x - self.tank_button.center_x) <= SELECTION_RADIUS \
                    and abs(y - self.tank_button.center_y) <= SELECTION_RADIUS:
                unit = Tank(center_x=self.our_base.center_x + POS_SPACE, center_y=self.our_base.center_y + POS_SPACE)
                self.our_base.building_queue.append(unit)
                self.our_base.current_building_time = Tank.building_time
                if len(self.our_base.building_queue) == 1:
                    self.our_base.building_start_time = self.frame_count'''
            # Create vulture:
            if abs(x - self.vulture_button.x) <= SELECTION_RADIUS \
                    and abs(y - self.vulture_button.y) <= SELECTION_RADIUS:
                unit = Vulture(x=self.our_base.x + POS_SPACE, y=self.our_base.y + POS_SPACE)
                self.our_base.building_queue.append(unit)
                self.our_base.current_building_time = Vulture.building_time
                if len(self.our_base.building_queue) == 1:
                    self.our_base.building_start_time = self.frame_count
            # Selection:
            else:
                # Closest coordinate:
                sel_x, sel_y = round_coords(x, y)
                selected = None
                for key, value in pos_coords_dict.items():
                    if sel_x == key[0] and sel_y == key[1]:
                        selected = value
                        print((sel_x, sel_y))
                        self.selection_sprite.x = sel_x
                        self.selection_sprite.y = sel_y
                print('SELECTED =', selected)

        elif button == mouse.RIGHT:
            x, y = round_coords(x, y)
            # Base rally point:
            if selected == id(self.our_base):  # Our base
                self.our_base.rally_point_x = x
                self.our_base.rally_point_y = y
                self.rally_point_sprite.x = x
                self.rally_point_sprite.y = y
                print('Rally set to ({}, {})'.format(x, y))
            # A unit is selected:
            else:
                print('else')
                for unit in unit_list:
                    print(id(unit))
                    if id(unit) == selected:
                        if (x, y) in pos_coords_dict:
                            if unit.destination_reached:
                                unit.move(x, y)
                            else:  # Movement interruption
                                unit.destination_x = unit.target_x
                                unit.destination_y = unit.target_y
                                unit.movement_interrupted = True
                                unit.new_dest_x = x
                                unit.new_dest_y = y

def main():
    game_window = Planet_Eleven(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    game_window.setup()
    pyglet.clock.schedule_interval(game_window.update, 1/120)
    pyglet.app.run()


if __name__ == "__main__":
    main()
