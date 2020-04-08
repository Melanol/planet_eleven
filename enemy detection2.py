rad_mat = [[(0, 0)]]
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
    rad_mat.append(rad_arr)
print(rad_mat)
arr_2_print = []
for arr in rad_mat:
    arr_2_print.append(len(arr))
print(arr_2_print)

rad_clipped = []
rad = 0
for arr in rad_mat:
    rad_arr = []
    print('rad =', rad)
    for coord in arr:
        d = (coord[0] ** 2 + coord[1] ** 2) ** 0.5
        if d <= rad:
            rad_arr.append(coord)
    rad_clipped.append(rad_arr)
    rad += 1

print(rad_clipped)
arr_2_print = []
for arr in rad_clipped:
    arr_2_print.append(len(arr))
print(arr_2_print)
