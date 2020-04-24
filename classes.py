from pyglet.sprite import Sprite
from weapons import *
from constants_and_utilities import *


class UI(Sprite):
    """This class is used for UI elements that need to be relocated when
    a player moves the viewport."""
    def __init__(self, game_inst, img, x, y, batch=None):
        super().__init__(img, x, y, batch=batch)
        self.org_x = x
        self.org_y = y
        game_inst.ui.append(self)

class CheckB(Sprite):
    """Check buttons."""
    def __init__(self, game_inst, x, y, checked=True):
        super().__init__(res.check_b, x, y, batch=options_batch)
        self.org_x = x
        self.org_y = y
        game_inst.ui.append(self)
        self.check = UI(game_inst, res.check, x, y, batch=check_batch)
        if not checked:
            self.check.visible = False

class Player:
    def __init__(self, name):
        self.min_c = 5000
        self.name = name

class HitAnim(Sprite):
    def __init__(self, x, y):
        super().__init__(res.hit_anim, x, y, batch=explosions_batch)

class Explosion(Sprite):
    def __init__(self, x, y, scale=1):
        super().__init__(res.explosion_anim, x, y, batch=explosions_batch)
        self.scale = scale

class Mineral(Sprite):
    def __init__(self, outer_instance, x, y, hp=5000):
        super().__init__(img=res.mineral, x=x, y=y, batch=structures_batch)
        self.outer_instance = outer_instance
        self.workers = []
        self.hp = hp
        self.cbs = None
        self.icon = res.mineral
        minerals.append(self)
        g_pos_coord_d[(x, y)] = self

    def kill(self):
        for worker in self.workers:
            worker.clear_task()
            worker.stop_move()
        g_pos_coord_d[(self.x, self.y)] = None
        self.delete()
