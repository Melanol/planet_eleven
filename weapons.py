import math
import pyglet
import resources as res


weapons_batch = pyglet.graphics.Batch()
zaps = []
ZAPS_LAST_F = 5

class Projectile(pyglet.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y, damage, speed, target_obj,
                 img=res.laser_img):
        super().__init__(img=img, x=x, y=y, batch=weapons_batch)
        self.damage = damage
        self.speed = speed
        self.target_x = target_x
        self.target_y = target_y
        x_diff = target_x - x
        y_diff = target_y - y
        angle = math.atan2(y_diff, x_diff)
        self.rotation = -math.degrees(angle)
        self.velocity_x = math.cos(angle) * speed
        self.velocity_y = math.sin(angle) * speed
        self.target_obj = target_obj

    def update(self):
        self.x, self.y = self.x + self.velocity_x, self.y + self.velocity_y

    def distance_to_target(self):
        return ((self.target_x - self.x) ** 2 +
                (self.target_y - self.y) ** 2) ** 0.5

    def eta(self):
        return self.distance_to_target() / self.speed


class Zap(pyglet.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y, f_started):
        self.f_started = f_started
        super().__init__(res.zap_anim, x, y, batch=weapons_batch)
        zaps.append(self)
        diff_x = target_x - self.x
        diff_y = target_y - self.y
        _dist = (diff_x ** 2 + diff_y ** 2) ** 0.5
        self.scale_x = _dist / 32
        angle = math.atan2(diff_y, diff_x)  # Rad
        self.rotation = -math.degrees(angle)
