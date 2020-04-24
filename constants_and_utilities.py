import pyglet
from screeninfo import get_monitors
import png


SCREEN_W = get_monitors()[0].width // 2
SCREEN_H = get_monitors()[0].height // 2
SCREEN_TITLE = "Planet Eleven"
POS_COORDS_N_ROWS = 100  # Should be 100 for the minimap to work
POS_COORDS_N_COLUMNS = 100  # Should be 100 for the minimap to work
PS = 32
selected = None
MMB_PAN_SPEED = 4
TXT_OUT_DECAY = 60
# LEFT_SCREEN_SCROLL_ZONE = (0, POS_SPACE)
# BOTTOM_SCREEN_SCROLL_ZONE = (0, POS_SPACE)
# RIGHT_SCREEN_SCROLL_ZONE = (16 * POS_SPACE, 17 * POS_SPACE)
# TOP_SCREEN_SCROLL_ZONE = (11 * POS_SPACE, 12 * POS_SPACE)

CP_CENTER_X = SCREEN_W - 139 + 139 / 2
MM0X = CP_CENTER_X - 50
MM0Y = SCREEN_H / 2 - 50
# Generate control button coords
cp_c_x = CP_CENTER_X
cp_c_y = (SCREEN_H / 2 - 50) / 2
x_space = 34
y_space = 34
CB_COORDS = [(cp_c_x - x_space, cp_c_y + y_space),
             (cp_c_x, cp_c_y + y_space),
             (cp_c_x + x_space, cp_c_y + y_space),
             (cp_c_x - x_space, cp_c_y),
             (cp_c_x, cp_c_y), (cp_c_x + x_space, cp_c_y),
             (cp_c_x - x_space, cp_c_y - y_space),
             (cp_c_x, cp_c_y - y_space),
             (cp_c_x + x_space, cp_c_y - y_space)
             ]

# Generate minimap_cam_frame
fully_visible_width = (SCREEN_W - 139) // PS
fully_visible_height = SCREEN_H // PS
arr = []
non_transparent_row = []
for _ in range(fully_visible_width + 2):
    non_transparent_row += [255, 255]
arr.append(non_transparent_row)
for _ in range(fully_visible_height):
    row = [255, 255]
    for _ in range(fully_visible_width):
        row += [255, 0]
    row += [255, 255]
    arr.append(row)
arr.append(non_transparent_row)
image = png.from_array(arr, mode='LA')
image.save('sprites/mm_cam_frame.png')

DISTANCE_PER_JUMP = (2 * PS ** 2) ** 0.5

OUR_TEAM_COLOR = (14, 241, 237)
# OUR_TEAM_COLOR = (0, 0, 0)
ENEMY_TEAM_COLOR = (255, 88, 140)

menu_b_batch = pyglet.graphics.Batch()
options_batch = pyglet.graphics.Batch()
check_batch = pyglet.graphics.Batch()
structures_batch = pyglet.graphics.Batch()
ground_units_batch = pyglet.graphics.Batch()
air_batch = pyglet.graphics.Batch()
ground_team_color_batch = pyglet.graphics.Batch()
air_team_color_batch = pyglet.graphics.Batch()
utilities_batch = pyglet.graphics.Batch()
minimap_pixels_batch = pyglet.graphics.Batch()
ground_shadows_batch = pyglet.graphics.Batch()
air_shadows_batch = pyglet.graphics.Batch()
explosions_batch = pyglet.graphics.Batch()

minerals = []
LIST_OF_FLYING = ["<class '__main__.Defiler'>",
                  "<class '__main__.Apocalypse'>"]
our_units = []
workers = []
our_structs = []
enemy_structs = []
prod_structs = []
offensive_structs = []
guardian_dummies = []
enemy_units = []

minimap_fow_x = MM0X - 1
minimap_fow_y = MM0Y - 1


def dist(obj1, obj2):
    return ((obj1.x - obj2.x) ** 2 + (obj1.y - obj2.y) ** 2) ** 0.5


def round_coords(x, y):
    """Receives mouse clicks. Returns closest positional coords."""
    global left_view_border, bottom_view_border
    sel_x = PS / 2 * round(x / (PS / 2))
    sel_y = PS / 2 * round(y / (PS / 2))
    if sel_x % PS == 0:
        if x > sel_x:
            sel_x += PS / 2
        else:
            sel_x -= PS / 2
    if sel_y % PS == 0:
        if y > sel_y:
            sel_y += PS / 2
        else:
            sel_y -= PS / 2
    if sel_x < 0:
        sel_x += PS
    if sel_y < 0:
        sel_y += PS
    return sel_x, sel_y


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

lvb = 0
bvb = 0

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
    for _x, _y in POS_COORDS:
        g_pos_coord_d[(_x, _y)] = None
    a_pos_coord_d = {}
    for _x, _y in POS_COORDS:
        a_pos_coord_d[(_x, _y)] = None

gen_pos_coords()


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
    game field, minimap, control panel."""
    if len(kwargs) == 1:
        try:
            return kwargs['x'] + lvb
        except KeyError:
            return kwargs['y'] + bvb
    else:
        return kwargs['x'] + lvb, kwargs['y'] + bvb


def closest_enemy_2_att(entity, enemy_entities):
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
    return closest_enemy

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
                    closest_enemy = closest_enemy_2_att(entity,
                                                        enemy_entities)
                    if closest_enemy:
                        entity.has_target_p = True
                        entity.target_p = closest_enemy
                        entity.target_p_x = closest_enemy.x
                        entity.target_p_y = closest_enemy.y
                        entity.target_p.attackers.append(entity)
                # Has target_p
                elif dist(entity, entity.target_p) <= entity.shooting_radius:
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
