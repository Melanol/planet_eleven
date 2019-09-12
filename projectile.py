import math
import pyglet
import resources as res


class Projectile(pyglet.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y, damage, speed):
        img = res.projectile_image
        super().__init__(img=img, x=x, y=y)
        self.damage = damage
        self.speed = speed
        x_diff = target_x - x
        y_diff = target_y - y
        angle = math.atan2(y_diff, x_diff)
        self.rotation = -math.degrees(angle)
        self.velocity_x = math.cos(angle) * speed
        self.velocity_y = math.sin(angle) * speed

    def update(self):
        self.x, self.y = self.x + self.velocity_x, self.y + self.velocity_y
