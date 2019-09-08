import math
import random
import sys

import pyglet
from pyglet.gl import *
from pyglet.window import key
from pyglet.window import mouse

import resources as res
from projectile import Projectile
from draw_dot import draw_dot

# TODO: Proper pathfinding
# TODO: Diagonal movement interception
# TODO: Unit following unit movement
# TODO: No-space spawning
# TODO: Something is wrong with default rally spawning when the viewport is moved
# TODO: Finalize minimap
# TODO: On-sprite shadows
SCREEN_WIDTH = 683
SCREEN_HEIGHT = 384
SCREEN_TITLE = "Test"
POS_COORDS_N_ROWS = 100  # Should be 100 for minimap to work
POS_COORDS_N_COLUMNS = 100  # Should be 100 for minimap to work
POS_SPACE = 32
SELECTION_RADIUS = 20
selected = None

left_view_border = 0
bottom_view_border = 0


MINIMAP_ZERO_COORDS = SCREEN_WIDTH - 120, SCREEN_HEIGHT - 230

# Generate positional coordinates:
POS_COORDS = []
for yi in range(1, POS_COORDS_N_ROWS + 1):
    for xi in range(1, POS_COORDS_N_COLUMNS + 1):
        POS_COORDS.append((xi * POS_SPACE - POS_SPACE / 2, yi * POS_SPACE - POS_SPACE / 2))
pos_coords_dict = {}
for _x, _y in POS_COORDS:
    pos_coords_dict[(_x, _y)] = None

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


# Modify coords
def mc(**kwargs):
    if len(kwargs) == 1:
        try:
            return kwargs['x'] + left_view_border
        except KeyError:
            return kwargs['y'] + bottom_view_border
    else:
        return kwargs['x'] + left_view_border, kwargs['y'] + bottom_view_border


def round_coords(x, y):
    global left_view_border, bottom_view_border
    #print('left_view_border =', reversed_left_view_border, 'bottom_view_border =', reversed_bottom_view_border)
    sel_x = POS_SPACE / 2 * round(x / (POS_SPACE / 2))
    sel_y = POS_SPACE / 2 * round(y / (POS_SPACE / 2))
    #print('sel_x =', sel_x, 'sel_y =', sel_y)
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
    return sel_x, sel_y
    # return mc(x=sel_x, y=sel_y)


def round_angle(angle):
    return 45 * round(angle / 45)


def give_next_target(x, y, angle):
    print('give_next_target input:', x, y, angle)
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


class Button(pyglet.sprite.Sprite):
    def __init__(self, img, x, y):
        super().__init__(img=img, x=x, y=y, batch=buttons_batch)


class Base(pyglet.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__(img=res.base_image, x=x, y=x, batch=ground_batch)
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
                 projectile_sprite, projectile_speed, projectile_color=(255, 255, 255)):
        super().__init__(img=img, x=x, y=y, batch=ground_batch)
        self.x = x
        self.y = y
        self.hp = hp
        self.damage = damage
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

    def update(self):
        self.x, self.y = self.x + self.velocity_x, self.y + self.velocity_y

    def move(self, destination):
        # Called once by RMB or when a unit is created
        # destination_x, destination_y = mc(x=destination[0], y=destination[1])
        destination_x, destination_y = destination[0], destination[1]
        print('destination_x =', destination_x, 'destination_y =', destination_y)
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
        print('target =', target)
        if target:
            self.target_x = target[0]
            self.target_y = target[1]
            pixel = minimap_pixels_dict[id(self)]
            pixel.x, pixel.y = to_minimap(self.target_x, self.target_y)
        else:
            self.destination_reached = True
            pos_coords_dict[(self.x, self.y)] = id(self)
            return
        diff_x = self.target_x - self.x
        diff_y = self.target_y - self.y
        angle = math.atan2(diff_y, diff_x)  # Rad
        self.rotation = math.degrees(angle) - 90
        self.velocity_x = math.cos(angle) * self.speed
        self.velocity_y = math.sin(angle) * self.speed
        # shadow = shadows_dict[id(self)]
        # shadow.angle = math.degrees(angle) - 90
        # shadow.velocity_x = math.cos(angle) * self.speed
        # shadow.velocity_y = math.sin(angle) * self.speed

        pos_coords_dict[(self.target_x, self.target_y)] = id(self)

    def distance_to_target(self):
        return ((self.target_x - self.x) ** 2 + (self.target_y - self.y) ** 2) ** 0.5

    def eta(self):
        return self.distance_to_target() / self.speed

    def update_movement(self):
        # Called by update to move to the next point
        print('\nupdate_movement: self.x = {}, self.y = {})'.format(self.x, self.y))
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
            pixel.x, pixel.y = to_minimap(self.target_x, self.target_y)
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
        super().__init__(img=res.defiler_image, hp=100, damage=10, cooldown=60, speed=3, x=x,
                         y=y, projectile_sprite='sprites/laserBlue01.png',
                         projectile_speed=10)


class Tank(Unit):
    building_time = 60

    def __init__(self, x, y):
        super().__init__(img=res.tank_image, hp=100, damage=10, cooldown=60, speed=0.6, x=x,
                         y=y, projectile_sprite='sprites/laserBlue01.png',
                         projectile_speed=10)


class Vulture(Unit):
    building_time = 10

    def __init__(self, x, y):
        super().__init__(img=res.vulture_image, hp=50, damage=10, cooldown=60, speed=10,
                         x=x, y=y, projectile_sprite='sprites/laserBlue01.png',
                         projectile_speed=10)


class PlanetEleven(pyglet.window.Window):
    def __init__(self, width, height, title):
        conf = Config(sample_buffers=1,
                      samples=4,
                      depth_size=16,
                      double_buffer=True)
        super().__init__(width, height, title,  config=conf, fullscreen=False)

        self.frame_count = 0

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

        self.defiler_button = Button(img=res.defiler_image, x=570, y=130)
        self.tank_button = Button(img=res.tank_image, x=615, y=130)
        self.vulture_button = Button(img=res.vulture_image, x=660, y=130)

        self.selection_sprite = pyglet.sprite.Sprite(img=res.selection_image, x=self.our_base.center_x,
                                                     y=self.our_base.center_y, batch=utilities_batch)
        self.rally_point_sprite = pyglet.sprite.Sprite(img=res.rally_point_image, x=self.our_base.rally_point_x,
                                                       y=self.our_base.rally_point_y)

        self.control_panel_sprite = pyglet.sprite.Sprite(img=res.control_panel_image, x=SCREEN_WIDTH, y=0)

        self.dots = []
        for x, y in POS_COORDS:
            dot = pyglet.sprite.Sprite(img=res.utility_dot_image, x=x, y=y, batch=utilities_batch)
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
        glOrtho(left_view_border, left_view_border + SCREEN_WIDTH, bottom_view_border,
                bottom_view_border + SCREEN_HEIGHT, 1, -1)

        '''for x, y in POS_COORDS:
            draw_dot(x, y, 2)'''

        ground_batch.draw()
        utilities_batch.draw()
        self.control_panel_sprite.draw()

        for _key, value in pos_coords_dict.items():
            x = _key[0]
            y = _key[1]
            if value:
                draw_dot(x, y, 1)

        #self.walls.draw()
        '''self.shadows.draw()
        self.unit_list.draw()
        self.selection_sprite.draw()'''

        if selected == id(self.our_base):  # Our base
            buttons_batch.draw()
            self.rally_point_sprite.draw()

        minimap_pixels_batch.draw()

        # Remove default modelview matrix
        glPopMatrix()

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
                        unit.move((unit.new_dest_x, unit.new_dest_y))
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
                    if unit == 'defiler':
                        unit = Defiler(x=self.our_base.x + POS_SPACE, y=self.our_base.y + POS_SPACE)
                    elif unit == 'tank':
                        unit = Tank(x=self.our_base.x + POS_SPACE, y=self.our_base.y + POS_SPACE)
                    elif unit == 'vulture':
                        unit = Vulture(x=self.our_base.x + POS_SPACE, y=self.our_base.y + POS_SPACE)
                    unit_list.append(unit)
                    self.our_base.building_start_time += self.our_base.current_building_time
                    unit.move(mc(x=self.our_base.rally_point_x, y=self.our_base.rally_point_y))
                    pixel_minimap_coords = to_minimap(unit.x, unit.y)
                    pixel = pyglet.sprite.Sprite(img=res.minimap_ally_image, x=pixel_minimap_coords[0],
                                                 y=pixel_minimap_coords[1],
                                                 batch=minimap_pixels_batch)
                    minimap_pixels_dict[id(unit)] = pixel
                    shadow = pyglet.sprite.Sprite(img=res.vulture_shadow_image, x=unit.x + 3, y=unit.y - 3,
                                                  batch=shadows_batch)
                    shadows_dict[id(unit)] = shadow
                else:
                    self.our_base.building_start_time += 1
                    print('No space')

    # def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
    #     # Move camera
    #     left -= dx
    #     right -= dx
    #     bottom -= dy
    #     top -= dy

    def on_key_press(self, symbol, modifiers):
        """Called whenever a key is pressed. """
        global selected, left_view_border, bottom_view_border
        if symbol == key.F:
            self.set_fullscreen(True)
        elif symbol == key.W:
            self.set_fullscreen(False)
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
        elif symbol == key.H:
            print(self.our_base.y)
        elif symbol == key.DELETE:
            for unit in unit_list:
                if id(unit) == selected:
                    unit.delete()
                    pos_coords_dict[(self.selection_sprite.x, self.selection_sprite.y)] = None
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
        global left_view_border, bottom_view_border

        # Viewport limits
        if left_view_border < 0:
            left_view_border = 0
        elif left_view_border > POS_COORDS_N_COLUMNS * POS_SPACE - SCREEN_WIDTH:
            left_view_border = POS_COORDS_N_COLUMNS * POS_SPACE - SCREEN_WIDTH
        if bottom_view_border < 0:
            bottom_view_border = 0
        elif bottom_view_border > POS_COORDS_N_ROWS * POS_SPACE - SCREEN_HEIGHT + POS_SPACE / 2:
            bottom_view_border = POS_COORDS_N_ROWS * POS_SPACE - SCREEN_HEIGHT + POS_SPACE / 2

        self.control_panel_sprite.x = SCREEN_WIDTH + left_view_border
        self.control_panel_sprite.y = bottom_view_border
        self.defiler_button.x = 570 + left_view_border
        self.defiler_button.y = 130 + bottom_view_border
        self.tank_button.x = 615 + left_view_border
        self.tank_button.y = 130 + bottom_view_border
        self.vulture_button.x = 660 + left_view_border
        self.vulture_button.y = 130 + bottom_view_border
        for unit in unit_list:
            pixel = minimap_pixels_dict[id(unit)]
            pixel.x, pixel.y = to_minimap(unit.x, unit.y)


    def on_mouse_press(self, x, y, button, modifiers):
        global selected, minimap_pixels_dict, unit_list
        x, y = round_coords(x, y)
        x, y = mc(x=x, y=y)
        print('\nglobal click coords:', x, y)
        if button == mouse.LEFT:
            # Create defiler
            if abs(x - self.defiler_button.x) <= SELECTION_RADIUS \
                    and abs(y - self.defiler_button.y) <= SELECTION_RADIUS:
                self.our_base.building_queue.append('defiler')
                self.our_base.current_building_time = Defiler.building_time
                if len(self.our_base.building_queue) == 1:
                    self.our_base.building_start_time = self.frame_count
            # Create tank
            elif abs(x - self.tank_button.x) <= SELECTION_RADIUS \
                    and abs(y - self.tank_button.y) <= SELECTION_RADIUS:
                self.our_base.building_queue.append('tank')
                self.our_base.current_building_time = Tank.building_time
                if len(self.our_base.building_queue) == 1:
                    self.our_base.building_start_time = self.frame_count
            # Create vulture
            elif abs(x - self.vulture_button.x) <= SELECTION_RADIUS \
                    and abs(y - self.vulture_button.y) <= SELECTION_RADIUS:
                self.our_base.building_queue.append('vulture')
                self.our_base.current_building_time = Vulture.building_time
                if len(self.our_base.building_queue) == 1:
                    self.our_base.building_start_time = self.frame_count
            # Selection
            else:
                selected = None
                for key, value in pos_coords_dict.items():
                    if x == key[0] and y == key[1]:
                        selected = value
                        self.selection_sprite.x = x
                        self.selection_sprite.y = y
                print('SELECTED =', selected)

        elif button == mouse.RIGHT:
            # Base rally point
            if selected == id(self.our_base):  # Our base
                self.our_base.rally_point_x = x
                self.our_base.rally_point_y = y
                self.rally_point_sprite.x = x
                self.rally_point_sprite.y = y
                print('Rally set to ({}, {})'.format(x, y))
            # A unit is selected
            else:
                for unit in unit_list:
                    if id(unit) == selected:
                        if (x, y) in pos_coords_dict:
                            if unit.destination_reached:
                                unit.move((x, y))
                            else:  # Movement interruption
                                unit.destination_x = unit.target_x
                                unit.destination_y = unit.target_y
                                unit.movement_interrupted = True
                                unit.new_dest_x = x
                                unit.new_dest_y = y

def main():
    game_window = PlanetEleven(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    game_window.setup()
    pyglet.clock.schedule_interval(game_window.update, 1/120)
    pyglet.app.run()


if __name__ == "__main__":
    main()
