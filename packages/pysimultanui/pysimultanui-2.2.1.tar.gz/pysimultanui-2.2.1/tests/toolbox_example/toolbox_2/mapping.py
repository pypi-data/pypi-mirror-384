from PySimultan2 import TaxonomyMap, PythonMapper
from PySimultanUI.src.pysimultanui import MethodMapper, ViewManager

from .classes import Class2, Class3
from .content import contents


mapper = PythonMapper()
method_mapper = MethodMapper()
view_manager = ViewManager()


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
