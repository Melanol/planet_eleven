class Outer(object):
    def __init__(self):
        Outer.Inner(self)

    def somemethod(self):
        print('hkhj')

    class Inner(object):
        def __init__(self, outer_instance):
            self.outer_instance = outer_instance
            self.outer_instance.somemethod()

        def inner_method(self):
            self.outer_instance.anothermethod()

Outer()