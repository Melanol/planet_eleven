import math
import random
import sys
import arcade
from pprint import pprint

'''TODO: Do not implement your angle-avoiding algorithm: it can create infinite loops
(unless it prohibits from moving back)'''
# TODO: FPS
# TODO: Proper pathfinding
# TODO: Diagonal movement interception
# TODO: Waypoint shooting
# TODO: Unit following unit movement
# TODO: Fix coordinates and UI
# TODO: No-space spawning
# TODO: Finalize minimap
SCREEN_WIDTH = 683
SCREEN_HEIGHT = 384
SCREEN_TITLE = "Stalagon"
POS_SPACE = 32
SELECTION_RADIUS = 20
selected = None

MINIMAP_ZERO_COORDS = (SCREEN_WIDTH - 120, SCREEN_HEIGHT - 230)

# Generate positional coordinates:
POS_COORDS_N_COLUMNS = 100
POS_COORDS_N_ROWS = 100
POS_COORDS = []
for yi in range(1, POS_COORDS_N_ROWS + 1):
    for xi in range(1, POS_COORDS_N_COLUMNS + 1):
        POS_COORDS.append((xi * POS_SPACE - POS_SPACE / 2, yi * POS_SPACE - POS_SPACE / 2))
pos_coords_dict = {}
for x, y in POS_COORDS:
    pos_coords_dict[(x, y)] = None

DISTANCE_PER_JUMP = (2 * POS_SPACE ** 2) ** 0.5
projectile_list = arcade.SpriteList()
minimap_pixels_dict = {}
shadows_dict = {}


def round_coords(x, y):
    sel_x = POS_SPACE / 2 * round(x / (POS_SPACE / 2))
    sel_y = POS_SPACE / 2 * round(y / (POS_SPACE / 2))
    print(sel_x, sel_y)
    if sel_x % 32 == 0:
        if x > sel_x:
            sel_x += POS_SPACE / 2
        else:
            sel_x -= POS_SPACE / 2
    if sel_y % 32 == 0:
        if y > sel_y:
            sel_y += POS_SPACE / 2
        else:
            sel_y -= POS_SPACE / 2
    print(sel_x, sel_y)
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


class Button(arcade.Sprite):
    def __init__(self, sprite, center_x, center_y):
        super().__init__(filename=sprite, center_x=center_x, center_y=center_y)

    def click(self):
        pass


class Base(arcade.Sprite):
    def __init__(self, center_x, center_y):
        super().__init__(filename='sprites/base.png', center_x=center_x, center_y=center_y)
        self.center_x = center_x
        self.center_y = center_y
        self.hp = 100
        pos_coords_dict[(center_x, center_y)] = id(self)
        self.rally_point_x = POS_SPACE * 2 - POS_SPACE / 2
        self.rally_point_y = POS_SPACE * 2 - POS_SPACE / 2
        self.building_queue = []
        self.current_building_time = None
        self.building_complete = True
        self.building_start_time = 0


class Unit(arcade.Sprite):
    def __init__(self, sprite, hp, damage, cooldown, speed, center_x, center_y,
                 projectile_sprite, projectile_speed, projectile_color=(255, 255, 255)):
        super().__init__(filename=sprite, center_x=center_x, center_y=center_y)
        self.center_x = center_x
        self.center_y = center_y
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
        if self.center_x == destination_x and self.center_y == destination_y:
            pos_coords_dict[(self.center_x, self.center_y)] = id(self)
            self.destination_reached = True
            return

        pos_coords_dict[(self.center_x, self.center_y)] = None
        self.destination_reached = False
        self.destination_x = destination_x
        self.destination_y = destination_y
        diff_x = self.destination_x - self.center_x
        diff_y = self.destination_y - self.center_y
        angle = math.atan2(diff_y, diff_x)  # Rad
        d_angle = math.degrees(angle)
        target = give_next_target(self.center_x, self.center_y, round_angle(d_angle))
        if target:
            self.target_x = target[0]
            self.target_y = target[1]
        else:
            self.destination_reached = True
            pos_coords_dict[(self.center_x, self.center_y)] = id(self)
            return
        diff_x = self.target_x - self.center_x
        diff_y = self.target_y - self.center_y
        angle = math.atan2(diff_y, diff_x)  # Rad
        self.angle = math.degrees(angle) - 90
        self.change_x = math.cos(angle) * self.speed
        self.change_y = math.sin(angle) * self.speed
        shadow = shadows_dict[id(self)]
        shadow.angle = math.degrees(angle) - 90
        shadow.change_x = math.cos(angle) * self.speed
        shadow.change_y = math.sin(angle) * self.speed

        pos_coords_dict[(self.target_x, self.target_y)] = id(self)

    def distance_to_target(self):
        return ((self.target_x - self.center_x) ** 2 + (self.target_y - self.center_y) ** 2) ** 0.5

    def eta(self):
        return self.distance_to_target() / self.speed

    def update_movement(self):
        # Called by update to move to the next point
        print('\nupdate_movement({}, {})'.format(self.center_x, self.center_y))
        pos_coords_dict[(self.center_x, self.center_y)] = None
        shadow = shadows_dict[id(self)]
        diff_x = self.destination_x - self.center_x
        diff_y = self.destination_y - self.center_y
        angle = math.atan2(diff_y, diff_x)  # Rad
        d_angle = math.degrees(angle)
        self.angle = d_angle - 90
        shadow.angle = math.degrees(angle) - 90
        next_target = give_next_target(self.center_x, self.center_y, round_angle(d_angle))
        print('next_target =', next_target)
        if next_target:
            pos_coords_dict[(self.center_x, self.center_y)] = None
            self.target_x = next_target[0]
            self.target_y = next_target[1]
            pixel = minimap_pixels_dict[id(self)]
            pixel.center_x, pixel.center_y = convert_to_minimap(self.target_x, self.target_y)
            pos_coords_dict[(self.target_x, self.target_y)] = id(self)
            diff_x = self.target_x - self.center_x
            diff_y = self.target_y - self.center_y
            angle = math.atan2(diff_y, diff_x)  # Rad
            d_angle = math.degrees(angle)
            self.angle = d_angle - 90
            self.change_x = math.cos(angle) * self.speed
            self.change_y = math.sin(angle) * self.speed
            shadow.angle = math.degrees(angle) - 90
            shadow.change_x = math.cos(angle) * self.speed
            shadow.change_y = math.sin(angle) * self.speed
        else:
            pos_coords_dict[(self.center_x, self.center_y)] = id(self)
            self.destination_reached = True
        if self.center_x == self.destination_x and self.center_y == self.destination_y:
            print('Destination reached')
            self.destination_reached = True
            print('self.destination_reached =', self.destination_reached)
        print()

    def shoot(self, frame_count, enemy_base_x, enemy_base_y):
        projectile = Projectile(sprite=self.projectile_sprite, center_x=self.center_x, center_y=self.center_y,
                                target_x=enemy_base_x, target_y=enemy_base_y,
                                damage=self.damage, speed=self.projectile_speed, projectile_color=self.projectile_color)
        x_diff = enemy_base_x - self.center_x
        y_diff = enemy_base_y - self.center_y
        self.angle = math.degrees(math.atan2(y_diff, x_diff)) - 90
        self.on_cooldown = True
        self.cooldown_started = frame_count


class Soldier(Unit):
    building_time = 30

    def __init__(self, center_x, center_y):
        super().__init__(sprite='sprites/soldier.png', hp=5, damage=1, cooldown=60, speed=1, center_x=center_x,
                         center_y=center_y,
                         projectile_sprite='sprites/laserBlue01.png',
                         projectile_speed=10, projectile_color=(255, 0, 0))


class Tank(Unit):
    building_time = 60

    def __init__(self, center_x, center_y):
        super().__init__(sprite='sprites/tank.png', hp=100, damage=10, cooldown=60, speed=0.6, center_x=center_x,
                         center_y=center_y, projectile_sprite='sprites/laserBlue01.png',
                         projectile_speed=10)


class Vulture(Unit):
    building_time = 10

    def __init__(self, center_x, center_y):
        super().__init__(sprite='sprites/vulture.png', hp=50, damage=10, cooldown=60, speed=10,
                         center_x=center_x, center_y=center_y, projectile_sprite='sprites/laserBlue01.png',
                         projectile_speed=10)


class Projectile(arcade.Sprite):
    def __init__(self, sprite, center_x, center_y, target_x, target_y, damage, speed, projectile_color):
        super().__init__(filename=sprite, center_x=center_x, center_y=center_y)
        self._set_color(projectile_color)
        self.damage = damage
        self.speed = speed

        x_diff = target_x - center_x
        y_diff = target_y - center_y
        angle = math.atan2(y_diff, x_diff)
        self.angle = math.degrees(angle)

        # Speed:
        self.change_x = math.cos(angle) * speed
        self.change_y = math.sin(angle) * speed

        projectile_list.append(self)


class Stalagon(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title, fullscreen=False, antialiasing=False, update_rate=1/60)
        arcade.set_background_color(arcade.color.BLACK)
        self.left_view_border = 0
        self.bottom_view_border = 0

        self.frame_count = 0

        # This will get the size of the window, and set the viewport to match.
        # So if the window is 1000x1000, then so will our viewport. If
        # you want something different, then use those coordinates instead.
        width, height = self.get_size()
        self.set_viewport(0, width, 0, height)

    def setup(self):
        global selected
        self.our_base = Base(POS_SPACE / 2, POS_SPACE / 2)
        selected = id(self.our_base)
        self.enemy_base = Base(POS_COORDS[-1][0], POS_COORDS[-1][1])
        '''self.walls = arcade.SpriteList(use_spatial_hash=False)
        wall_coords = [(105, 165), (105, 195), (105, 225), (105, 255), (105, 285), (105, 315), (165, 165), (165, 195),
                       (165, 225), (165, 285), (165, 315), (195, 225), (195, 285)]
        for coord in wall_coords:
            x = coord[0]
            y = coord[1]
            wall = arcade.Sprite(filename='sprites/wall.png', center_x=x, center_y=y)
            self.walls.append(wall)
            pos_coords_dict[(x, y)] = id(wall)'''

        self.soldier_button = Button(sprite='sprites/soldier.png', center_x=570, center_y=130)
        self.tank_button = Button(sprite='sprites/tank.png', center_x=615, center_y=130)
        self.vulture_button = Button(sprite='sprites/vulture.png', center_x=660, center_y=130)

        self.selection_sprite = arcade.Sprite(filename='sprites/selection.png', center_x=self.our_base.center_x,
                                              center_y=self.our_base.center_y)
        self.buttons_list = arcade.SpriteList(use_spatial_hash=False)
        self.buttons_list.append(self.soldier_button)
        self.buttons_list.append(self.tank_button)
        self.buttons_list.append(self.vulture_button)
        self.rally_point_sprite = arcade.Sprite(filename='sprites/rally_point.png',
                                                center_x=self.our_base.rally_point_x,
                                                center_y=self.our_base.rally_point_y)
        self.unit_list = arcade.SpriteList(use_spatial_hash=False)
        self.control_panel = arcade.Sprite(filename='sprites/control_panel.png',
                                           center_x=SCREEN_WIDTH - 139/2, center_y=SCREEN_HEIGHT / 2)
        self.minimap_pixels = arcade.SpriteList(use_spatial_hash=False)

        self.terrain = arcade.SpriteList(use_spatial_hash=False)
        for coord in POS_COORDS:
            angle = random.choice([0, 90, 180, 270])
            filename = random.choice(['sprites/sand1.png'])
            sand = arcade.Sprite(filename=filename, center_x=coord[0], center_y=coord[1])
            #sand._set_angle(angle)
            self.terrain.append(sand)

        self.shadows = arcade.SpriteList(use_spatial_hash=False)

    def on_draw(self):
        """
        Render the screen.
        """
        arcade.start_render()
        self.terrain.draw()
        #arcade.draw_points(POS_COORDS, arcade.color.WHITE, 2)

        self.our_base.draw()
        self.enemy_base.draw()

        projectile_list.draw()

        #self.walls.draw()
        self.shadows.draw()
        self.unit_list.draw()
        self.selection_sprite.draw()

        if selected == pos_coords_dict[(POS_SPACE / 2, POS_SPACE / 2)]:  # Our base
            self.buttons_list.draw()
            self.rally_point_sprite.draw()

        '''for key, value in pos_coords_dict.items():
            if value:
                arcade.draw_point(key[0], key[1], color=arcade.color.RED, size = 10)'''

        self.control_panel.draw()
        if selected == pos_coords_dict[(POS_SPACE / 2, POS_SPACE / 2)]:  # Our base
            self.buttons_list.draw()
            self.rally_point_sprite.draw()

        self.minimap_pixels.draw()


    def update(self, delta_time):
        global minimap_pixels_dict
        self.frame_count += 1
        # Units
        # Movement
        for unit in self.unit_list:
            shadow = shadows_dict[id(unit)]
            # Selection
            if selected == id(unit):
                self.selection_sprite.center_x = unit.center_x
                self.selection_sprite.center_y = unit.center_y

            # Do not jump
            if not unit.destination_reached:
                if not unit.eta() <= 1:
                    unit.update()
                    shadow.update()
                # Jump
                else:
                    if not unit.movement_interrupted:
                        unit.center_x = unit.target_x
                        unit.center_y = unit.target_y
                        shadow.center_x = unit.target_x + 3
                        shadow.center_y = unit.target_y - 3
                        pos_coords_dict[(unit.target_x, unit.target_y)] = id(unit)
                        if unit.center_x == unit.destination_x and unit.center_y == unit.destination_y:
                            unit.destination_reached = True
                        else:
                            unit.update_movement()
                    else:
                        unit.center_x = unit.target_x
                        unit.center_y = unit.target_y
                        shadow.center_x = unit.target_x + 3
                        shadow.center_y = unit.target_y - 3
                        pos_coords_dict[(unit.target_x, unit.target_y)] = id(unit)
                        unit.destination_reached = True
                        unit.move(unit.new_dest_x, unit.new_dest_y)
                        unit.movement_interrupted = False

                    # Stop to attack enemy base:
                    '''if ((self.enemy_base.center_x - unit.center_x) ** 2 + (
                            self.enemy_base.center_y - unit.center_y) ** 2) ** 0.5 > 100:
                        unit.update()'''

        # Shooting at enemy base:
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
            self.enemy_base.hp -= projectile.damage

        # Building units
        if self.our_base.building_queue:
            if self.frame_count - self.our_base.building_start_time == self.our_base.current_building_time:
                if pos_coords_dict[(self.our_base.center_x + POS_SPACE, self.our_base.center_y + POS_SPACE)] is None:
                    unit = self.our_base.building_queue.pop(0)
                    self.our_base.building_start_time += self.our_base.current_building_time
                    self.unit_list.append(unit)
                    unit.move(self.our_base.rally_point_x, self.our_base.rally_point_y)
                    pixel = arcade.Sprite(filename='sprites/minimap_ally.png',
                                          center_x=unit.center_x,
                                          center_y=unit.center_y)
                    self.minimap_pixels.append(pixel)
                    minimap_pixels_dict[id(unit)] = pixel
                    shadow = arcade.Sprite(filename='sprites/vulture_shadow.png',
                                           center_x=unit.center_x + 3,
                                           center_y=unit.center_y - 3)
                    self.shadows.append(shadow)
                    shadows_dict[id(unit)] = shadow
                else:
                    self.our_base.building_start_time += 1
                    print('No space')

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed. """
        global selected
        if key == arcade.key.F:
            # User hits f. Flip between full and not full screen.
            self.set_fullscreen(not self.fullscreen)

            # Get the window coordinates. Match viewport to window coordinates
            # so there is a one-to-one mapping.
            width, height = self.get_size()
            self.set_viewport(0, width, 0, height)

        elif key == arcade.key.S:
            # User hits s. Flip between full and not full screen.
            self.set_fullscreen(not self.fullscreen)

            # Instead of a one-to-one mapping, stretch/squash window to match the
            # constants. This does NOT respect aspect ratio. You'd need to
            # do a bit of math for that.
            self.set_viewport(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT)

        elif key == arcade.key.LEFT:
            self.left_view_border -= POS_SPACE
            self.update_viewport()

        elif key == arcade.key.RIGHT:
            self.left_view_border += POS_SPACE
            self.update_viewport()

        elif key == arcade.key.DOWN:
            self.bottom_view_border -= POS_SPACE
            self.update_viewport()

        elif key == arcade.key.UP:
            self.bottom_view_border += POS_SPACE
            self.update_viewport()

        elif key == arcade.key.Z:
            for key, value in pos_coords_dict.items():
                if value is None:
                    unit = Vulture(key[0], key[1])
                    self.unit_list.append(unit)
                    pos_coords_dict[key] = id(unit)

        elif key == arcade.key.H:
            print(minimap_pixels_dict)

        elif key == arcade.key.DELETE:
            for unit in self.unit_list:
                if selected == id(unit):
                    unit.kill()
                    pos_coords_dict[(self.selection_sprite.center_x, self.selection_sprite.center_y)] = None
                    selected = None

        elif key == arcade.key.ESCAPE:
            sys.exit()

    def update_viewport(self):
        # Viewport limits
        if self.left_view_border < 0:
            self.left_view_border = 0
        elif self.left_view_border > POS_COORDS_N_COLUMNS * POS_SPACE - SCREEN_WIDTH + 139:
            self.left_view_border = POS_COORDS_N_COLUMNS * POS_SPACE - SCREEN_WIDTH + 139
        if self.bottom_view_border < 0:
            self.bottom_view_border = 0
        elif self.bottom_view_border > POS_COORDS_N_ROWS * POS_SPACE - SCREEN_HEIGHT:
            self.bottom_view_border = POS_COORDS_N_ROWS * POS_SPACE - SCREEN_HEIGHT

        arcade.set_viewport(self.left_view_border, self.left_view_border + SCREEN_WIDTH,
                            self.bottom_view_border, self.bottom_view_border + SCREEN_HEIGHT)
        self.control_panel.center_x = SCREEN_WIDTH - 139/2 + self.left_view_border
        self.control_panel.center_y = SCREEN_HEIGHT / 2 + self.bottom_view_border
        self.soldier_button.center_x = 570 + self.left_view_border
        self.soldier_button.center_y = 130 + self.bottom_view_border
        self.tank_button.center_x = 615 + self.left_view_border
        self.tank_button.center_y = 130 + self.bottom_view_border
        self.vulture_button.center_x = 660 + self.left_view_border
        self.vulture_button.center_y = 130 + self.bottom_view_border
        print(self.soldier_button.center_y)
        print(self.left_view_border)
        print(self.bottom_view_border)

    def on_mouse_press(self, x, y, button, key_modifiers):
        global selected, minimap_pixels_dict
        print(x, y)
        x += self.left_view_border
        y += self.bottom_view_border
        if button == arcade.MOUSE_BUTTON_LEFT:
            # Create soldier:
            if abs(x - self.soldier_button.center_x) <= SELECTION_RADIUS \
                    and abs(y - self.soldier_button.center_y) <= SELECTION_RADIUS:
                unit = Soldier(center_x=self.our_base.center_x + POS_SPACE, center_y=self.our_base.center_y + POS_SPACE)
                self.our_base.building_queue.append(unit)
                self.our_base.current_building_time = Soldier.building_time
                if len(self.our_base.building_queue) == 1:
                    self.our_base.building_start_time = self.frame_count
            # Create tank:
            elif abs(x - self.tank_button.center_x) <= SELECTION_RADIUS \
                    and abs(y - self.tank_button.center_y) <= SELECTION_RADIUS:
                unit = Tank(center_x=self.our_base.center_x + POS_SPACE, center_y=self.our_base.center_y + POS_SPACE)
                self.our_base.building_queue.append(unit)
                self.our_base.current_building_time = Tank.building_time
                if len(self.our_base.building_queue) == 1:
                    self.our_base.building_start_time = self.frame_count
            # Create vulture:
            elif abs(x - self.vulture_button.center_x) <= SELECTION_RADIUS \
                    and abs(y - self.vulture_button.center_y) <= SELECTION_RADIUS:
                unit = Vulture(center_x=self.our_base.center_x + POS_SPACE, center_y=self.our_base.center_y + POS_SPACE)
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
                        self.selection_sprite.center_x = sel_x
                        self.selection_sprite.center_y = sel_y
                print('SELECTED =', selected)

        elif button == arcade.MOUSE_BUTTON_RIGHT:
            x, y = round_coords(x, y)
            # Base rally point:
            if selected == id(self.our_base):  # Our base
                self.our_base.rally_point_x = x
                self.our_base.rally_point_y = y
                self.rally_point_sprite.center_x = x
                self.rally_point_sprite.center_y = y
                print('Rally set to ({}, {})'.format(x, y))
            # A unit is selected:
            else:
                for unit in self.unit_list:
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

    '''def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.frame_count % 5 == 0:
            if dx > 0:
                self.left_view_border -= POS_SPACE
                self.update_viewport()
            elif dx < 0:
                self.left_view_border += POS_SPACE
                self.update_viewport()
            if dy > 0:
                self.bottom_view_border -= POS_SPACE
                self.update_viewport()
            elif dy < 0:
                self.bottom_view_border += POS_SPACE
                self.update_viewport()'''

def main():
    game = Stalagon(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    game.setup()

    arcade.run()


if __name__ == "__main__":
    main()
