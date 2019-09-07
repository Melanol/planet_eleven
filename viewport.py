import numpy as np
from numbers import Number
from pyglet.gl import *

_left = -1
_right = 1
_bottom = -1
_top = 1
_scaling = None

_window = None

_projection = None
_opengl_context = None


def create_orthogonal_projection(left, right, bottom, top, near, far, dtype=None):
    rml = right - left
    tmb = top - bottom
    fmn = far - near

    a = 2. / rml
    b = 2. / tmb
    c = -2. / fmn
    tx = -(right + left) / rml
    ty = -(top + bottom) / tmb
    tz = -(far + near) / fmn

    return np.array((
        (a, 0., 0., 0.),
        (0., b, 0., 0.),
        (0., 0., c, 0.),
        (tx, ty, tz, 1.),
    ), dtype=dtype)


def set_viewport(left: Number, right: Number, bottom: Number, top: Number):
    global _left
    global _right
    global _bottom
    global _top
    global _projection
    global _scaling

    _left = left
    _right = right
    _bottom = bottom
    _top = top

    # Needed for sprites
    if _scaling is None:
        _scaling = get_scaling_factor(_window)
    glViewport(0, 0, _window.width * _scaling, _window.height * _scaling)

    # Needed for drawing
    # gl.glMatrixMode(gl.GL_PROJECTION)
    # gl.glLoadIdentity()
    # gl.glOrtho(_left, _right, _bottom, _top, -1, 1)
    # gl.glMatrixMode(gl.GL_MODELVIEW)
    # gl.glLoadIdentity()

    _projection = create_orthogonal_projection(left=_left, right=_right, bottom=_bottom, top=_top, near=-1000,
                                               far=100, dtype=np.float32)


def get_scaling_factor(window):
    from pyglet import compat_platform
    if compat_platform == 'darwin':
        from pyglet.libs.darwin.cocoapy import NSMakeRect
        view = window.context._nscontext.view()
        content_rect = NSMakeRect(0, 0, window._width, window._height)  # Get size, possibly scaled
        bounds = view.convertRectFromBacking_(content_rect)  # Convert to actual pixel sizes
        return int(content_rect.size.width / bounds.size.width)
    else:
        return 1
