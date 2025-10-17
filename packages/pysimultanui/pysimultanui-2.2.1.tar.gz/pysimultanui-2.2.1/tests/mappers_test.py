from typing import List, Optional
from PySimultan2.object_mapper import PythonMapper
from nicegui import ui
import os

from PySimultanUI.src.pysimultanui import user_manager, Content, TaxonomyMap, run_ui, DetailView

from PySimultan2 import DataModel


project_dir = os.environ.get('PROJECT_DIR', '/simultan_projects')
if not os.path.exists(project_dir):
    os.makedirs(project_dir)

new_data_model = DataModel.create_new_project(project_path=os.path.join(project_dir, 'mapper_test.simultan'),
                                              user_name='admin',
                                              password='admin')


def create_first_mapping():
    mapping = user_manager.mapper_manager.create_mapping(name='Toolbox 1')
    mapper = mapping.mapper
    method_mapper = mapping.method_mapper
    view_manager = mapping.view_manager

    contents = {}

    class Class1:
        def __init__(self, *args, **kwargs):
            self.param_a = kwargs.get('param_a', None)
            self.param_b = kwargs.get('param_b', None)
            self.param_c = kwargs.get('param_c', None)

        def add(self):
            self.param_c = self.param_a + self.param_b

    contents['param_a'] = Content(text_or_key='param_a',
                                  property_name='param_a',
                                  type=None,
                                  unit=None,
                                  documentation='param_a')

    contents['param_b'] = Content(text_or_key='param_b',
                                  property_name='param_b',
                                  type=None,
                                  unit=None,
                                  documentation='param_b')

    contents['param_c'] = Content(text_or_key='param_c',
                                  property_name='param_c',
                                  type=None,
                                  unit=None,
                                  documentation='param_c')

    cls_map = TaxonomyMap(taxonomy_name='PySimultan',
                          taxonomy_key='PySimultan',
                          taxonomy_entry_name='Class1',
                          taxonomy_entry_key='Class1',
                          content=[contents['param_a'],
                                   contents['param_b'],
                                   contents['param_c'],
                                   ],
                          )

    mapper.register(cls_map.taxonomy_entry_key, Class1, taxonomy_map=cls_map)
    mapped_cls = mapper.get_mapped_class(cls_map.taxonomy_entry_key)

    method_mapper.register_method(cls=mapped_cls,
                                  name='add',
                                  method=Class1.add)

    # create detail view
    class Class1DetailView(DetailView):

        def ui_content(self, *args, **kwargs):
            ui.label('This is a detail view for Class1')
            ui.label('param_a')
            ui.input(value=self.component.param_a).bind_value(self.component, 'param_a')
            ui.input(value=self.component.param_b).bind_value(self.component, 'param_b')

    view_manager.views[cls_map.taxonomy_entry_key] = Class1DetailView

    return mapper


def create_second_mapping():
    mapping = user_manager.mapper_manager.create_mapping(name='Toolbox 2')
    mapper = mapping.mapper
    method_mapper = mapping.method_mapper
    view_manager = mapping.view_manager

    contents = {}

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


    contents['param_a'] = Content(text_or_key='param_a',
                                  property_name='param_a',
                                  type=None,
                                  unit=None,
                                  documentation='param_a')

    contents['param_b'] = Content(text_or_key='param_b',
                                  property_name='param_b',
                                  type=None,
                                  unit=None,
                                  documentation='param_b')

    contents['param_c'] = Content(text_or_key='param_c',
                                  property_name='param_c',
                                  type=None,
                                  unit=None,
                                  documentation='param_c')

    contents['param_d'] = Content(text_or_key='param_d',
                                  property_name='param_d',
                                  type=None,
                                  unit=None,
                                  documentation='param_d')

    contents['thermal_conductivity'] = Content(text_or_key='thermal_conductivity',
                                               property_name='thermal_conductivity',
                                               type=None,
                                               unit=None,
                                               documentation='thermal_conductivity')

    contents['thermal_resistance'] = Content(text_or_key='thermal_resistance',
                                             property_name='thermal_resistance',
                                             type=None,
                                             unit=None,
                                             documentation='thermal_resistance')

    cls_map = TaxonomyMap(taxonomy_name='PySimultan',
                          taxonomy_key='PySimultan',
                          taxonomy_entry_name='Class2',
                          taxonomy_entry_key='Class2',
                          content=[contents['param_a'],
                                   contents['param_b'],
                                   contents['param_c'],
                                   contents['param_d'],
                                   ],
                          )

    mapper.register(cls_map.taxonomy_entry_key, Class2, taxonomy_map=cls_map)
    mapped_cls = mapper.get_mapped_class(cls_map.taxonomy_entry_key)

    method_mapper.register_method(cls=mapped_cls,
                                  name='multiply',
                                  method=Class2.multiply)

    cls_map2 = TaxonomyMap(taxonomy_name='PySimultan',
                           taxonomy_key='PySimultan',
                           taxonomy_entry_name='Class3',
                           taxonomy_entry_key='Class3',
                           content=[contents['thermal_conductivity'],
                                    contents['thermal_resistance'],
                                    ],
                           )

    mapper.register(cls_map2.taxonomy_entry_key, Class3, taxonomy_map=cls_map2)
    mapped_cls2 = mapper.get_mapped_class(cls_map2.taxonomy_entry_key)

    method_mapper.register_method(cls=mapped_cls2,
                                  name='test_method',
                                  method=Class3.test_method)

    def test_fcn(*args, **kwargs):
        print('Test function')

    method_mapper.register_method(method=test_fcn,
                                  name='Test function',
                                  add_user_to_kwargs=True,
                                  add_data_model_to_kwargs=True,
                                  cls=None, args=[],
                                  kwargs={})

    return mapper


def create_components(data_model: DataModel,
                      mapper: 'PythonMapper',
                      mapper2: 'PythonMapper' = None):
    cls = mapper.get_mapped_class('Class1')
    cls(name='class 1 mapper 1',
        param_a=1,
        param_b=2)

    cls2 = mapper2.get_mapped_class('Class2')
    cls2(param_a=3, param_b=4, name='Test Mapper2 class2')

    cls3 = mapper2.get_mapped_class('Class3')
    cls3(name='Test Mapper2 class3', thermal_conductivity=20, thermal_resistance=40)

    data_model.save()
    data_model.cleanup()


mapper1 = create_first_mapping()
mapper2 = create_second_mapping()
create_components(new_data_model, mapper1, mapper2)

run_ui()
print('Done!')
