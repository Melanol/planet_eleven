import pyglet


class Movable(pyglet.sprite.Sprite):
    def __init__(self, img, x, y, batch=None):
        super().__init__(img=img, x=x, y=y, batch=batch)
        self.velocity_x = 0
        self.velocity_y = 0
        self.target_x = None
        self.target_y = None
        self.speed = 0

    def update(self):
        self.x, self.y = self.x + self.velocity_x, self.y + self.velocity_y

    def distance_to_target(self):
        return ((self.target_x - self.x) ** 2 + (self.target_y - self.y) ** 2) ** 0.5

    def eta(self):
        return self.distance_to_target() / self.speed
