from shadowandunittc import ShadowAndUnitTC
from structs import *

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
        selected_dict = g_pos_coord_d
    else:
        selected_dict = a_pos_coord_d
    if selected_dict[(end[0], end[1])] is None:
        acc_ends = [(convert_c_to_simple(end[0]), convert_c_to_simple(end[1]))]
    else:
        width = 3
        while True:
            acc_ends = []
            dx = dy = -PS
            for i in range(width):
                coord = (end[0] + dx, end[1] + dy)
                try:
                    if selected_dict[coord] is None:
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
                    if selected_dict[coord] is None:
                        acc_ends.append((convert_c_to_simple(coord[0]),
                                         convert_c_to_simple(coord[1])))
                except KeyError:  # Out of the map borders
                    pass
            for i in range(width - 1):
                dx -= PS
                coord = (end[0] + dx, end[1] + dy)
                try:
                    if selected_dict[coord] is None:
                        acc_ends.append((convert_c_to_simple(coord[0]),
                                         convert_c_to_simple(coord[1])))
                except KeyError:  # Out of the map borders
                    pass
            for i in range(width - 2):
                dy -= PS
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
    # print("acc_ends =", acc_ends)
    start = convert_c_to_simple(start[0]), convert_c_to_simple(start[1])
    end = convert_c_to_simple(end[0]), convert_c_to_simple(end[1])
    # print('start =', start, 'end =', end)
    map = convert_map(selected_dict)
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
                 vision_radius, hp, x, y, speed, weapon_type, w_img, damage,
                 cooldown,
                 attacks_ground, attacks_air, shadow_sprite, cbs):
        self.game_inst = game_inst
        self.owner = owner
        self.team_color = ShadowAndUnitTC(team_color_img, x, y,
                                          ground_team_color_batch)
        self.icon = icon
        if owner.name == 'player1':
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
        self.vision_radius = vision_radius
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
        self.attacks_ground = attacks_ground
        self.attacks_air = attacks_air
        self.shooting_radius = vision_radius * 32
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
        if self.owner.name == 'player1':
            pixel = res.mm_our_img
            self.game_inst.update_fow(self.x, self.y, self.vision_radius)
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
        if self.attack_moving and (self.x, self.y) in POS_COORDS:
            if self.owner.name == 'player1':
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
        self.team_color.rotation = -math.degrees(angle) + 90
        self.team_color.velocity_x = math.cos(angle) * self.speed
        self.team_color.velocity_y = math.sin(angle) * self.speed
        self.shadow.rotation = -math.degrees(angle) + 90
        self.shadow.velocity_x = math.cos(angle) * self.speed
        self.shadow.velocity_y = math.sin(angle) * self.speed
        self.pos_dict[(self.x, self.y)] = None
        self.pos_dict[(self.target_x, self.target_y)] = self

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


    def stop_move(self):
        """Stops movement."""
        if not self.dest_reached:
            self.dest_x = self.target_x
            self.dest_y = self.target_y

    def kill(self, delay_del=False):
        self.pixel.delete()
        self.team_color.delete()
        self.shadow.delete()
        for attacker in self.attackers:
            attacker.has_target_p = False
        if not delay_del:
            if self.owner.name == 'player1':
                del our_units[our_units.index(self)]
            else:
                del enemy_units[enemy_units.index(self)]
        self.pos_dict[(self.target_x, self.target_y)] = None
        Explosion(self.x, self.y, 0.25)
        self.delete()
        try:
            del workers[workers.index(self)]
            self.zap_sprite.delete()
        except ValueError:
            pass


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
                         vision_radius=6, hp=100, x=x, y=y, speed=1,
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
                         vision_radius=6, hp=100, x=x, y=y, speed=1,
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
                         vision_radius=6, hp=70, x=x, y=y, speed=3,
                         weapon_type='instant', w_img=res.laser_img, damage=1,
                         cooldown=1,
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
                         vision_radius=4, hp=10, x=x, y=y, speed=10,
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
        if self.to_build == "armory":
            if not g_pos_coord_d[(self.task_x, self.task_y)]:
                Armory(self.game_inst, self.task_x, self.task_y)
            else:
                self.owner.min_c += Armory.cost
        elif self.to_build == "turret":
            if not g_pos_coord_d[(self.task_x, self.task_y)]:
                Turret(self.game_inst, self.task_x, self.task_y)
            else:
                self.owner.min_c += Turret.cost
        elif self.to_build == "mech_center":
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
                         vision_radius=3, hp=25, x=x, y=y, speed=3,
                         weapon_type='projectile', w_img=res.laser_img,
                         damage=5, cooldown=60,
                         attacks_ground=True, attacks_air=False,
                         shadow_sprite=res.wyrm_shadow_img,
                         cbs=game_inst.basic_unit_c_bs)
