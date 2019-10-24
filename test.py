class MyClass:
    def __init__(self):
        self.a = 1
        self.b = 1

    def stop(self):
        self.a = 0

class AnotherClass(MyClass):
    def __init__(self):
        super().__init__()

    def stop(self):
        super().stop()
        self.b = 0

unit = AnotherClass()
unit.stop()
print(unit.a)
print(unit.b)