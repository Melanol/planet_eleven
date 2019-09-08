import math
import pyglet


class Projectile(pyglet.sprite.Sprite):
    def __init__(self, img, x, y, target_x, target_y, damage, speed, projectile_color):
        super().__init__(img=img, x=x, y=y)
        self._set_color(projectile_color)
        self.damage = damage
        self.speed = speed

        x_diff = target_x - x
        y_diff = target_y - y
        angle = math.atan2(y_diff, x_diff)
        self.angle = math.degrees(angle)

        # Speed:
        self.change_x = math.cos(angle) * speed
        self.change_y = math.sin(angle) * speed
