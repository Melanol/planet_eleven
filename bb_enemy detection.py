rad_matx = [[(0, 0)]]
max_rad = 10
for r in range(1, max_rad + 1):
    rad_arr = []
    width = r * 2 + 1
    x = -r
    y = -r
    for _ in range(width):
        rad_arr.append((x, y))
        x += 1
    x -= 1
    y += 1
    for _ in range(width - 1):
        rad_arr.append((x, y))
        y += 1
    y -= 1
    x -= 1
    for _ in range(width - 1):
        rad_arr.append((x, y))
        x -= 1
    x += 1
    y -= 1
    for _ in range(width - 2):
        rad_arr.append((x, y))
        y -= 1
    print('rad_arr =', rad_arr)
    rad_matx.append(rad_arr)
lengths = []
for arr in rad_matx:
    lengths.append(len(arr))
print('arr_2_print =', lengths)

rad_clipped = []
rad = 0
too_far = [[]]
i = 0
for arr in rad_matx:
    rad_arr = []
    # print('rad =', rad)
    print(i)
    inner_arr = []
    for coord in arr + too_far[i]:
        d = (coord[0] ** 2 + coord[1] ** 2) ** 0.5
        if d <= rad:
            rad_arr.append(coord)
        else:
            inner_arr.append(coord)
    rad_clipped.append(rad_arr)
    too_far.append(inner_arr)
    rad += 1
    i += 1

print('rad_clipped =', rad_clipped)
lengths = []
for arr in rad_clipped:
    lengths.append(len(arr))
print(lengths)
