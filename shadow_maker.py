from PIL import Image


path = "D:/PycharmProjects/planet_eleven/sprites/units/apocalypse/apocalypse.png"
last_slash_i_reversed = path[::-1].index("/")
folder = path[::-1][last_slash_i_reversed:][::-1]
print("folder =", folder)
name = path[::-1][4:last_slash_i_reversed][::-1]
print("name =", name)
im = Image.open(path)
pixels = im.load()

for x in range(0, 32):
    for y in range(0, 32):
        if pixels[x, y][3] != 0:
            pixels[x, y] = (0, 0, 0, 102)

im.save(folder + name + "_shadow.png")
