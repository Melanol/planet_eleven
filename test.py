arr = [(1, 1), (2, 2)]
def kill():
    del arr[0]

kill()
print(arr)