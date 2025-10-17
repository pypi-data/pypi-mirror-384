from PySimultan2.taxonomy_maps import TaxonomyMap, Content
import PySimultanUI.src.pysimultanui as psui

# example class to be mapped:


class ExampleClass:
    def __init__(self, *args, **kwargs):
        self.a = kwargs.get('a', None)
        self.b = kwargs.get('b', None)
        self.c = None

    def add(self):
        self.c = self.a + self.b

    def subtract(self):
        self.c = self.a - self.b

    def multiply(self):
        self.c = self.a * self.b


# create content and taxonomy map:
contents = {}

contents['a'] = Content(text_or_key='a_in_simultan',
                        property_name='a',
                        type=None,
                        unit=None,
                        documentation='Content a')

contents['b'] = Content(text_or_key='b_in_simultan',
                        property_name='b',
                        type=None,
                        unit=None,
                        documentation='Content b')

contents['c'] = Content(text_or_key='c_in_simultan',
                        property_name='c',
                        type=None,
                        unit=None,
                        documentation='Content c')

example_class_map = TaxonomyMap(taxonomy_name='PySimultanUI',
                                taxonomy_key='PySimultanUI',
                                taxonomy_entry_name='ExampleClass',
                                taxonomy_entry_key='ExampleClass',
                                content=[contents['a'],
                                         contents['b'],
                                         contents['c']
                                         ],
                                )

# get the mapper:
mapper = psui.core.mapper

# register the class to be mapped:
mapper.register(example_class_map.taxonomy_entry_key,
                ExampleClass,
                taxonomy_map=example_class_map)


# register methods:
cls = mapper.get_mapped_class('ExampleClass')

# get the method mapper:
method_mapper = psui.core.method_mapper

method_mapper.register_method(cls=cls,
                              name='subtract',
                              method=cls.subtract,
                              args=[],
                              kwargs={})

method_mapper.register_method(cls=cls,
                              name='add',
                              method=cls.add,
                              args=[],
                              kwargs={})

method_mapper.register_method(cls=cls,
                              name='multiply',
                              method=cls.multiply,
                              args=[],
                              kwargs={})

# run the UI:
psui.run_ui()
