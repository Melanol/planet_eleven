import pyglet


class ShadowAndUnitTC(pyglet.sprite.Sprite):
    def __init__(self, img, x, y, batch=None):
        super().__init__(img=img, x=x, y=y, batch=batch)
        self.velocity_x = 0
        self.velocity_y = 0

    def update(self):
        self.x, self.y = self.x + self.velocity_x, self.y + self.velocity_y
