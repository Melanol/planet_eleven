import png


arr = [[255, 255, 255, 255],
       [255, 255, 255, 255]]
image = png.from_array(arr, mode='LA')
image.save('minimap_cam_frame.png')