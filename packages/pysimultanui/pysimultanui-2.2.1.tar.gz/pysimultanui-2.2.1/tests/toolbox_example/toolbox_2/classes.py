class Class2:
    def __init__(self, *args, **kwargs):
        self.param_a = kwargs.get('param_a', None)
        self.param_b = kwargs.get('param_b', None)
        self.param_c = kwargs.get('param_c', None)
        self.param_d = kwargs.get('param_d', None)

    def multiply(self):
        self.param_d = self.param_a * self.param_b


class Class3:
    def __init__(self, *args, **kwargs):
        self.thermal_conductivity = kwargs.get('thermal_conductivity', 15)
        self.thermal_resistance = kwargs.get('thermal_resistance', 30)

    def test_method(self):
        print(f'This is a test method {self}')
