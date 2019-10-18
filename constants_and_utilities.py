import pyglet
from screeninfo import get_monitors
import png


SCREEN_WIDTH = get_monitors()[0].width // 2
SCREEN_HEIGHT = get_monitors()[0].height // 2
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

CONTROL_PANEL_CENTER_X = SCREEN_WIDTH - 139 + 139 / 2
MINIMAP_ZERO_COORDS = CONTROL_PANEL_CENTER_X - 50, SCREEN_HEIGHT / 2 - 50
# Generate control button coords
center_x = CONTROL_PANEL_CENTER_X
center_y = (SCREEN_HEIGHT / 2 - 50) / 2
x_space = 34
y_space = 34
CONTROL_BUTTONS_COORDS = [(center_x - x_space, center_y + y_space), (center_x, center_y + y_space), (center_x + x_space, center_y + y_space),
                          (center_x - x_space, center_y), (center_x, center_y), (center_x + x_space, center_y),
                          (center_x - x_space, center_y - y_space), (center_x, center_y - y_space), (center_x + x_space, center_y - y_space)
                          ]

# Generate minimap_cam_frame
fully_visible_width = (SCREEN_WIDTH - 139) // POS_SPACE
fully_visible_height = SCREEN_HEIGHT // POS_SPACE
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
image.save('sprites/minimap_cam_frame.png')

DISTANCE_PER_JUMP = (2 * POS_SPACE ** 2) ** 0.5

buildings_batch = pyglet.graphics.Batch()
ground_units_batch = pyglet.graphics.Batch()
air_batch = pyglet.graphics.Batch()
utilities_batch = pyglet.graphics.Batch()
minimap_pixels_batch = pyglet.graphics.Batch()
shadows_batch = pyglet.graphics.Batch()
air_shadows_batch = pyglet.graphics.Batch()
turret_batch = pyglet.graphics.Batch()

LIST_OF_FLYING = ['defiler']
our_units_list = []
builders_list = []
our_buildings_list = []
shooting_buildings_list = []
enemy_buildings_list = []
projectile_list = []

minimap_fow_x = MINIMAP_ZERO_COORDS[0] - 1
minimap_fow_y = MINIMAP_ZERO_COORDS[1] - 1


def round_angle(angle):
    return 45 * round(angle / 45)


def round_coords(x, y):
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
