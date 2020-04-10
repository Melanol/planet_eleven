class One:
    def __init__(self, x):
        self.x = x


class Two:
    def __init__(self, x):
        self.y = 2


class Three(One, Two):
    def __init__(self, x):
        super().__init__(1)
        super(Three, self).__init__(x)


inst3 = Three(1)
print(inst3.y)