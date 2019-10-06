from PIL import Image
im = Image.open('sprites/test_image.png')
px = im.load()
print (px[4,4])
px[4,4] = (0,0,0)
print (px[4,4])