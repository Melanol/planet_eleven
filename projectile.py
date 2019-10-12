import math
from movable import Movable
import resources as res


class Projectile(Movable):
    def __init__(self, x, y, target_x, target_y, damage, speed, target_obj, vs_air=False):
        img = res.projectile_image
        super().__init__(img=img, x=x, y=y)
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
