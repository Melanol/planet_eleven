import math
import pyglet


SCREEN_WIDTH = 500
SCREEN_HEIGHT = 500
SCREEN_TITLE = "Solar System"

ORBIT_RADIUS_SCALE = 1
PERIOD_SCALE = 3

MERCURY_ORBIT_RADIUS_MLN_KM = 58
MERCURY_ORBIT_PERIOD_D = 88

VENUS_ORBIT_RADIUS_MLN_KM = 108
VENUS_ORBIT_PERIOD_D = 225

EARTH_ORBIT_RADIUS_MLN_KM = 150
EARTH_ORBIT_PERIOD_D = 365

MARS_ORBIT_RADIUS_MLN_KM = 228
MARS_ORBIT_PERIOD_D = 687


MERCURY_SIM_ORBIT_RADIUS = MERCURY_ORBIT_RADIUS_MLN_KM * ORBIT_RADIUS_SCALE
MERCURY_RADIANS_PER_FRAME = 1 / MERCURY_ORBIT_PERIOD_D * PERIOD_SCALE

VENUS_SIM_ORBIT_RADIUS = VENUS_ORBIT_RADIUS_MLN_KM * ORBIT_RADIUS_SCALE
VENUS_RADIANS_PER_FRAME = 1 / VENUS_ORBIT_PERIOD_D * PERIOD_SCALE

EARTH_SIM_ORBIT_RADIUS = EARTH_ORBIT_RADIUS_MLN_KM * ORBIT_RADIUS_SCALE
EARTH_RADIANS_PER_FRAME = 1 / EARTH_ORBIT_PERIOD_D * PERIOD_SCALE

MARS_SIM_ORBIT_RADIUS = MARS_ORBIT_RADIUS_MLN_KM * ORBIT_RADIUS_SCALE
MARS_RADIANS_PER_FRAME = 1 / MARS_ORBIT_PERIOD_D * PERIOD_SCALE

CENTER_X = SCREEN_WIDTH // 2
CENTER_Y = SCREEN_HEIGHT // 2


class SolarSystem(pyglet.window.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title)

    def setup(self):
        sun_image = pyglet.image.load('sprites/centurion.png')
        self.sun = pyglet.sprite.Sprite(sun_image, CENTER_X, CENTER_Y)

        mercury_image = pyglet.image.load('sprites/base.png')
        self.mercury = pyglet.sprite.Sprite(mercury_image, -100, -100)
        self.mercury_angle = 0

        venus_image = pyglet.image.load('sprites/defiler.png')
        self.venus = pyglet.sprite.Sprite(venus_image, -100, -100)
        self.venus_angle = 0

        earth_image = pyglet.image.load('sprites/vulture.png')
        self.earth = pyglet.sprite.Sprite(earth_image, -100, -100)
        self.earth_angle = 90

        mars_image = pyglet.image.load('sprites/pioneer.png')
        self.mars = pyglet.sprite.Sprite(mars_image, -100, -100)
        self.mars_angle = 0

    def on_draw(self):
        self.clear()
        self.sun.draw()
        self.mercury.draw()
        self.venus.draw()
        self.earth.draw()
        self.mars.draw()

    def update(self, delta_time):
        self.mercury_angle += MERCURY_RADIANS_PER_FRAME
        self.mercury.x = MERCURY_SIM_ORBIT_RADIUS * math.sin(self.mercury_angle) + CENTER_X
        self.mercury.y = MERCURY_SIM_ORBIT_RADIUS * math.cos(self.mercury_angle) + CENTER_Y

        self.venus_angle += VENUS_RADIANS_PER_FRAME
        self.venus.x = VENUS_SIM_ORBIT_RADIUS * math.sin(self.venus_angle) + CENTER_X
        self.venus.y = VENUS_SIM_ORBIT_RADIUS * math.cos(self.venus_angle) + CENTER_Y

        self.earth_angle += EARTH_RADIANS_PER_FRAME
        self.earth.x = EARTH_SIM_ORBIT_RADIUS * math.sin(self.earth_angle) + CENTER_X
        self.earth.y = EARTH_SIM_ORBIT_RADIUS * math.cos(self.earth_angle) + CENTER_Y

        self.mars_angle += MARS_RADIANS_PER_FRAME
        self.mars.x = MARS_SIM_ORBIT_RADIUS * math.sin(self.mars_angle) + CENTER_X
        self.mars.y = MARS_SIM_ORBIT_RADIUS * math.cos(self.mars_angle) + CENTER_Y


def main():
    game_window = SolarSystem(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    game_window.setup()
    pyglet.clock.schedule_interval(game_window.update, 1 / 60)
    pyglet.app.run()


if __name__ == "__main__":
    main()
