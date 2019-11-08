import pyglet
from screeninfo import get_monitors
import png


SCREEN_W = get_monitors()[0].width // 2
SCREEN_H = get_monitors()[0].height // 2
SCREEN_TITLE = "Planet Eleven"
POS_COORDS_N_ROWS = 100  # Should be 100 for the minimap to work
POS_COORDS_N_COLUMNS = 100  # Should be 100 for the minimap to work
POS_SPACE = 32
selected = None
MMB_PAN_SPEED = 4
# LEFT_SCREEN_SCROLL_ZONE = (0, POS_SPACE)
# BOTTOM_SCREEN_SCROLL_ZONE = (0, POS_SPACE)
# RIGHT_SCREEN_SCROLL_ZONE = (16 * POS_SPACE, 17 * POS_SPACE)
# TOP_SCREEN_SCROLL_ZONE = (11 * POS_SPACE, 12 * POS_SPACE)

CONTROL_PANEL_CENTER_X = SCREEN_W - 139 + 139 / 2
MINIMAP_ZERO_COORDS = CONTROL_PANEL_CENTER_X - 50, SCREEN_H / 2 - 50
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
fully_visible_width = (SCREEN_W - 139) // POS_SPACE
fully_visible_height = SCREEN_H // POS_SPACE
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

DISTANCE_PER_JUMP = (2 * POS_SPACE ** 2) ** 0.5

buildings_batch = pyglet.graphics.Batch()
ground_units_batch = pyglet.graphics.Batch()
air_batch = pyglet.graphics.Batch()
utilities_batch = pyglet.graphics.Batch()
minimap_pixels_batch = pyglet.graphics.Batch()
ground_shadows_batch = pyglet.graphics.Batch()
air_shadows_batch = pyglet.graphics.Batch()
zap_batch = pyglet.graphics.Batch()

minerals = []
LIST_OF_FLYING = ["<class '__main__.Defiler'>",
                  "<class '__main__.Apocalypse'>"]
our_units = []
workers = []
our_buildings = []
shooting_buildings = []
enemy_buildings = []
enemy_units = []
projectiles = []

minimap_fow_x = MINIMAP_ZERO_COORDS[0] - 1
minimap_fow_y = MINIMAP_ZERO_COORDS[1] - 1


def round_coords(x, y):
    """Receives mouse clicks. Returns closest positional coords."""
    global left_view_border, bottom_view_border
    sel_x = POS_SPACE / 2 * round(x / (POS_SPACE / 2))
    sel_y = POS_SPACE / 2 * round(y / (POS_SPACE / 2))
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
    if sel_x < 0:
        sel_x += POS_SPACE
    if sel_y < 0:
        sel_y += POS_SPACE
    return sel_x, sel_y


def is_melee_dist(unit, target_x, target_y):
    """Checks if a unit is in the 8 neighboring blocks of the target object.
    Used for melee interaction."""
    if abs(unit.x - target_x) == POS_SPACE:
        if abs(unit.y - target_y) == POS_SPACE or unit.y == target_y:
            return True
    elif unit.x == target_x and abs(unit.y - target_y) == POS_SPACE:
        return True
    return False


def dist(obj1, obj2):
    return ((obj1.x - obj2.x) ** 2 + (obj1.y - obj2.y) ** 2) ** 0.5
