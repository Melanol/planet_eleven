import pyglet
from pyglet import gl

def draw_dot(x, y, thickness):
    point_coords = []
    point_coords.append(int(x - thickness / 2))
    point_coords.append(int(y - thickness / 2))
    point_coords.append(int(x + thickness / 2))
    point_coords.append(int(y - thickness / 2))
    point_coords.append(int(x + thickness / 2))
    point_coords.append(int(y + thickness / 2))
    point_coords.append(int(x - thickness / 2))
    point_coords.append(int(y + thickness / 2))
    pyglet.graphics.draw(4, pyglet.gl.GL_QUADS, ('v2i', point_coords))