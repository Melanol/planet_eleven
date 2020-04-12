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

CONTROL_PANEL_CENTER_X = SCREEN_W - 139 + 139 / 2
MM0X = CONTROL_PANEL_CENTER_X - 50
MM0Y = SCREEN_H / 2 - 50
# Generate control button coords
cp_c_x = CONTROL_PANEL_CENTER_X
cp_c_y = (SCREEN_H / 2 - 50) / 2
x_space = 34
y_space = 34
CTRL_B_COORDS = [(cp_c_x - x_space, cp_c_y + y_space),
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
zap_batch = pyglet.graphics.Batch()
explosions_batch = pyglet.graphics.Batch()

minerals = []
LIST_OF_FLYING = ["<class '__main__.Defiler'>",
                  "<class '__main__.Apocalypse'>"]
our_units = []
workers = []
our_structures = []
enemy_structures = []
offensive_structures = []
guardian_dummies = []
enemy_units = []
projectiles = []

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
