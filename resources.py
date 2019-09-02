import pyglet


def center_image(image):
    """Sets an image's anchor point to its center"""
    image.anchor_x = image.width / 2
    image.anchor_y = image.height / 2


pyglet.resource.path = ['sprites']
pyglet.resource.reindex()

base_image = pyglet.resource.image("base.png")
center_image(base_image)

tank_image = pyglet.resource.image("tank.png")
center_image(tank_image)

vulture_image = pyglet.resource.image("vulture.png")
center_image(vulture_image)

defiler_image = pyglet.resource.image("defiler.png")
center_image(defiler_image)