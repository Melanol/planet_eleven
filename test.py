class MyClass:
    def __init__(self, outer):
        self.hp = outer.hp


class AnotherClass:
    def __init__(self):
        self.hp = 100

poop = AnotherClass