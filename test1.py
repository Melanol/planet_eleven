import win32api

while True:
    x, y = win32api.GetCursorPos()
    print(x, y)