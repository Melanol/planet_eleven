class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

import time

point = Point(0, 0)
start_time = time.time()
for _ in range(1000000):
    point.x
elapsed_time = time.time() - start_time
print(elapsed_time)


class Unit:
    def __init__(self, x, y):
        self.loc = Point(x, y)

unit = Unit(0, 0)
start_time = time.time()
for _ in range(1000000):
    unit.loc.x
elapsed_time = time.time() - start_time
print(elapsed_time)

x = unit.loc.x
start_time = time.time()
for _ in range(1000000):
    x
elapsed_time = time.time() - start_time
print(elapsed_time)