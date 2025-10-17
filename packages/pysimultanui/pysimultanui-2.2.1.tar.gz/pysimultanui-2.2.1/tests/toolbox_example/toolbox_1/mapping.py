from PySimultan2 import TaxonomyMap, PythonMapper
from PySimultanUI.src.pysimultanui import MethodMapper, ViewManager

from .classes import Class1
from .content import contents


mapper = PythonMapper()
method_mapper = MethodMapper()
view_manager = ViewManager()


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
