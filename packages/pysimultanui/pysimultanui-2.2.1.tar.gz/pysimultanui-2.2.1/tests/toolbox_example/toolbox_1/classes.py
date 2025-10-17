

class Class1:
    def __init__(self, *args, **kwargs):
        self.param_a = kwargs.get('param_a', None)
        self.param_b = kwargs.get('param_b', None)
        self.param_c = kwargs.get('param_c', None)

    def add(self):
        self.param_c = self.param_a + self.param_b
