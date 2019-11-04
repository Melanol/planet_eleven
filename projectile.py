import math
import pyglet
import resources as res


class Projectile(pyglet.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y, damage, speed, target_obj, color=(150, 150, 255), vs_air=False):
        img = res.projectile_image
        super().__init__(img=img, x=x, y=y)
        self.color = color
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
        return ((self.target_x - self.x) ** 2 + (self.target_y - self.y) ** 2) ** 0.5

    def eta(self):
        return self.distance_to_target() / self.speed