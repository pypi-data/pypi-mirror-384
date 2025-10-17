from typing import List, Optional
import os
import numpy as np
import pandas as pd
from pysimultanui.main_ui import run_ui
from PySimultan2 import config
from pysimultanui.core import mapper, method_mapper, mapped_method
from PySimultan2.taxonomy_maps import TaxonomyMap, Content
from PySimultan2.files import FileInfo
from PySimultan2 import DataModel
from PySimultan2.geometry.geometry_base import (GeometryModel)
from PySimultan2.geometry.utils import create_cube
# from py_simultan_ui.src.core.method_mapper import method_mapper, mapped_method

project_dir = os.environ.get('PROJECT_DIR', '/simultan_projects')
if not os.path.exists(project_dir):
    os.makedirs(project_dir)

new_data_model = DataModel.create_new_project(project_path=os.path.join(project_dir, 'steady_state.simultan'),
                                              user_name='admin',
                                              password='admin')


def create_geometry_model(name='new_geometry_test',
                          data_model: DataModel = new_data_model):
    return GeometryModel(name=name,
                         data_model=data_model)


def create_classes() -> dict[str, type]:

    class TypeTestClass(object):

        def __init__(self, *args, **kwargs):
            self.name = kwargs.get('name', 'Type test class')
            self.int_value = kwargs.get('int_value', 1459)
            self.float_value = kwargs.get('float_value', 259.0)
            self.str_value = kwargs.get('str_value', 'string value')
            self.bool_value = kwargs.get('bool_value', True)
            self.list_value = kwargs.get('list_value', [])
            self.dict_value = kwargs.get('dict_value', {'a': 1, 'b': 2})
            self.none_value = kwargs.get('none_value', None)
            self.obj_value = kwargs.get('obj_value')
            self.numpy_value = kwargs.get('numpy_value', np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                                                                  dtype=np.int32).reshape(4, 3))
            self.pandas_value = kwargs.get('pandas_value', pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]}))
            self.file_value = kwargs.get('file_value', None)

    class Source(object):
        def __init__(self, *args, **kwargs):
            self.name = kwargs.get('name')
            self.temperature = kwargs.get('temperature')
            self.heat_flux = kwargs.get('heat_flux')

    class TemperatureBoundaryCondition(object):
        def __init__(self, *args, **kwargs):
            self.name = kwargs.get('name')
            self.temperature = kwargs.get('temperature', 293.0)

    class HeatFluxBoundaryCondition(object):
        def __init__(self, *args, **kwargs):
            self.name = kwargs.get('name')
            self.heat_flux = kwargs.get('heat_flux')

    class Material(object):
        def __init__(self, *args, **kwargs):
            self.name = kwargs.get('name')
            self.thermal_conductivity = kwargs.get('thermal_conductivity', 0.15)
            self.density = kwargs.get('density', 1000)
            self.specific_heat = kwargs.get('specific_heat', 800)

    class WallLayer(object):
        def __init__(self, *args, **kwargs):
            self.name = kwargs.get('name')
            self.thickness = kwargs.get('thickness', 0.10)
            self.material: Optional[Material] = kwargs.get('material', None)

        @property
        def r_value(self):
            return self.thickness / self.material.thermal_conductivity

    class Construction(object):
        def __init__(self, *args, **kwargs):
            self.name = kwargs.get('name')
            self.layers: List[WallLayer] = kwargs.get('layers', [])
            self.r_value = kwargs.get('r_value', None)

        @mapped_method(name='calculate_r_value')
        def calculate_r_value(self):
            self.r_value = sum([layer.r_value for layer in self.layers])
            return self.r_value

    class Wall(object):
        h_c_lookup = {0.1: 5,
                      0.13: 7.69,
                      0.17: 5.88}

        def __init__(self, *args, **kwargs):
            self.name = kwargs.get('name')
            self.r_si = kwargs.get('r_si')
            self.r_se = kwargs.get('r_se')
            self.construction: Construction = kwargs.get('construction')
            self.u_value = kwargs.get('u_value', None)

            self.boundary_condition = kwargs.get('boundary_condition', None)

        @property
        def area(self):
            return sum((x.area for x in self.associated_geometry))

        @property
        def h_c(self):
            """
            return the convective heat transfer coefficient h_c in W/m2K
            :return:
            """
            return self.h_c_lookup[self.r_si]

        def calculate_u_value(self) -> float:
            self.u_value = 1 / (self.r_si + self.r_se + self.construction.calculate_r_value())
            return self.u_value

    class Zone(object):
        def __init__(self, *args, **kwargs):
            self.name = kwargs.get('name')
            self.walls: List[Wall] = kwargs.get('walls', [])
            self.volume = kwargs.get('volume')
            self.area = kwargs.get('area')
            self.u_value = kwargs.get('u_value', None)

            self.sources: List[Source] = kwargs.get('sources', [])
            self.steady_state_temperature = kwargs.get('steady_state_temperature', None)

        def calculate_area(self):
            self.area = self.associated_geometry[0].area_brutto_netto.Item1
            return self.area

        def calculate_steady_state_temperature(self):
            phi_ti = []
            for wall in self.walls:
                phi_i = wall.area * wall.calculate_u_value() * wall.r_si * wall.h_c
                phi_ti.append((phi_i * wall.boundary_condition.temperature, phi_i))

            phi_hc_id = sum(x.heat_flux for x in self.sources)

            t_steady = (sum(x[0] for x in phi_ti) + phi_hc_id) / sum(x[1] for x in phi_ti)
            self.steady_state_temperature = t_steady

            return t_steady

    class Volume(object):
        def __init__(self, *args, **kwargs):
            self.name = kwargs.get('name')
            self.geometry_file = kwargs.get('geometry_file')

    class Mesh(object):
        def __init__(self, *args, **kwargs):
            self.name = kwargs.get('name')
            self.mesh_file = kwargs.get('mesh_file')

    class Assembly(object):
        def __init__(self, *args, **kwargs):
            self.name = kwargs.get('name', 'Unnamed Assembly')
            self.volumes = kwargs.get('volumes', [])
            self.mesh = kwargs.get('mesh', None)
            self.features = kwargs.get('features', [])

    class ReferenceFace(object):
        def __init__(self, *args, **kwargs):
            self.construction: Construction = kwargs.get('construction')
            self.assembly: Assembly = kwargs.get('assembly')
            self.mesh_size = 15

    cls_dict = {'Material': Material,
                'WallLayer': WallLayer,
                'Wall': Wall,
                'Zone': Zone,
                'TemperatureBoundaryCondition': TemperatureBoundaryCondition,
                'HeatFluxBoundaryCondition': HeatFluxBoundaryCondition,
                'Source': Source,
                'Construction': Construction,
                'TypeTestClass': TypeTestClass,
                'Assembly': Assembly,
                'ReferenceFace': ReferenceFace,
                'Volume': Volume,
                'Mesh': Mesh}

    return cls_dict


def create_mapped_classes(classes: dict[str, type]) -> dict[str, type]:

    def create_contents() -> dict[str, Content]:
        contents = {}

        contents['thermal_conductivity'] = Content(text_or_key='thermal_conductivity',
                                                   property_name='thermal_conductivity',
                                                   type=None,
                                                   unit='W/mK',
                                                   documentation='thermal_conductivity in W/mK')

        contents['density'] = Content(text_or_key='density',
                                      property_name='density',
                                      type=None,
                                      unit='kg/m3',
                                      documentation='density in kg/m3')

        contents['specific_heat'] = Content(text_or_key='specific_heat',
                                            property_name='specific_heat',
                                            type=None,
                                            unit='J/kgK',
                                            documentation='specific_heat in J/kgK')

        contents['thickness'] = Content(text_or_key='thickness',
                                        property_name='thickness',
                                        type=None,
                                        unit='m',
                                        documentation='thickness in m')

        contents['material'] = Content(text_or_key='material',
                                       property_name='material',
                                       type=None,
                                       unit=None,
                                       documentation='material')

        contents['construction'] = Content(text_or_key='construction',
                                           property_name='construction',
                                           type=None,
                                           unit=None,
                                           documentation='construction')

        contents['r_si'] = Content(text_or_key='r_si',
                                   property_name='r_si',
                                   type=None,
                                   unit='m2K/W',
                                   documentation='r_si in m2K/W')

        contents['r_se'] = Content(text_or_key='r_se',
                                   property_name='r_se',
                                   type=None,
                                   unit=None,
                                   documentation='r_se in m2K/W')

        contents['layers'] = Content(text_or_key='layers',
                                     property_name='layers',
                                     type=None,
                                     unit=None,
                                     documentation='layers of the wall',
                                     component_policy='subcomponent')

        contents['u_value'] = Content(text_or_key='u_value',
                                      property_name='u_value',
                                      type=None,
                                      unit='W/m2K',
                                      documentation='u_value of the wall in W/m2K')

        contents['r_value'] = Content(text_or_key='r_value',
                                      property_name='r_value',
                                      type=None,
                                      unit='m2K/W',
                                      documentation='r_value of the wall in W/m2K')

        contents['boundary_condition'] = Content(text_or_key='boundary_condition',
                                                 property_name='boundary_condition',
                                                 type=None,
                                                 unit=None,
                                                 documentation='boundary_condition')

        contents['walls'] = Content(text_or_key='walls',
                                    property_name='walls',
                                    type=None,
                                    unit=None,
                                    documentation='walls of the zone')

        contents['volume'] = Content(text_or_key='volume',
                                     property_name='volume',
                                     type=None,
                                     unit=None,
                                     documentation='volume of the zone in m3')

        contents['area'] = Content(text_or_key='area',
                                   property_name='area',
                                   type=None,
                                   unit='m2',
                                   documentation='area of the zone in m2')

        contents['sources'] = Content(text_or_key='sources',
                                      property_name='sources',
                                      type=None,
                                      unit=None,
                                      documentation='sources of the zone')

        contents['steady_state_temperature'] = Content(text_or_key='steady_state_temperature',
                                                       property_name='steady_state_temperature',
                                                       type=None,
                                                       unit='K',
                                                       documentation='steady_state_temperature of the zone')

        contents['temperature'] = Content(text_or_key='temperature',
                                          property_name='temperature',
                                          type=None,
                                          unit='K',
                                          documentation='temperature in K')

        contents['heat_flux'] = Content(text_or_key='heat_flux',
                                        property_name='heat_flux',
                                        type=None,
                                        unit='W',
                                        documentation='heat_flux in W')

        contents['int_value'] = Content(text_or_key='int_value',
                                        property_name='int_value',
                                        type=int,
                                        unit=None,
                                        documentation='int_value')

        contents['float_value'] = Content(text_or_key='float_value',
                                          property_name='float_value',
                                          type=float,
                                          unit=None,
                                          documentation='float_value')

        contents['str_value'] = Content(text_or_key='str_value',
                                        property_name='str_value',
                                        type=str,
                                        unit=None,
                                        documentation='str_value')

        contents['bool_value'] = Content(text_or_key='bool_value',
                                         property_name='bool_value',
                                         type=bool,
                                         unit=None,
                                         documentation='bool_value')

        contents['list_value'] = Content(text_or_key='list_value',
                                         property_name='list_value',
                                         type=list,
                                         unit=None,
                                         documentation='list_value')

        contents['dict_value'] = Content(text_or_key='dict_value',
                                         property_name='dict_value',
                                         type=dict,
                                         unit=None,
                                         documentation='dict_value')

        contents['none_value'] = Content(text_or_key='none_value',
                                         property_name='none_value',
                                         type=None,
                                         unit=None,
                                         documentation='none_value')

        contents['obj_value'] = Content(text_or_key='obj_value',
                                        property_name='obj_value',
                                        type=None,
                                        unit=None,
                                        documentation='obj_value')

        contents['numpy_value'] = Content(text_or_key='numpy_value',
                                          property_name='numpy_value',
                                          type=None,
                                          unit=None,
                                          documentation='numpy_value')

        contents['pandas_value'] = Content(text_or_key='pandas_value',
                                           property_name='pandas_value',
                                           type=None,
                                           unit=None,
                                           documentation='pandas_value')

        contents['assembly'] = Content(text_or_key='assembly',
                                       property_name='assembly',
                                       type=None,
                                       unit=None,
                                       documentation='assembly')

        contents['volumes'] = Content(text_or_key='volumes',
                                      property_name='volumes',
                                      type=None,
                                      unit=None,
                                      documentation='volumes')

        contents['features'] = Content(text_or_key='features',
                                       property_name='features',
                                       type=None,
                                       unit=None,
                                       documentation='features')

        contents['mesh'] = Content(text_or_key='mesh',
                                   property_name='mesh',
                                   type=None,
                                   unit=None,
                                   documentation='mesh')

        contents['geometry_file'] = Content(text_or_key='geometry_file',
                                            property_name='geometry_file',
                                            type=None,
                                            unit=None,
                                            documentation='geometry_file')

        contents['mesh_file'] = Content(text_or_key='mesh_file',
                                        property_name='mesh_file',
                                        type=None,
                                        unit=None,
                                        documentation='mesh_file')

        contents['mesh_size'] = Content(text_or_key='mesh_size',
                                        property_name='mesh_size',
                                        type=float,
                                        unit='cm',
                                        documentation='mesh_size')

        return contents

    def create_mapped_type_test_class(cls, contents: dict[str, Content]):
        cls_map = TaxonomyMap(taxonomy_name='PySimultan',
                              taxonomy_key='PySimultan',
                              taxonomy_entry_name='TypeTestClass',
                              taxonomy_entry_key='TypeTestClass',
                              content=[contents['int_value'],
                                       contents['float_value'],
                                       contents['str_value'],
                                       contents['bool_value'],
                                       contents['list_value'],
                                       contents['dict_value'],
                                       contents['none_value'],
                                       contents['obj_value'],
                                       contents['numpy_value'],
                                       contents['pandas_value']],
                              )

        mapper.register(cls_map.taxonomy_entry_key, cls, taxonomy_map=cls_map)
        mapped_cls = mapper.get_mapped_class(cls_map.taxonomy_entry_key)
        return mapped_cls

    def create_mapped_material(cls, contents: dict[str, Content]):
        cls_map = TaxonomyMap(taxonomy_name='PySimultan',
                              taxonomy_key='PySimultan',
                              taxonomy_entry_name='Material',
                              taxonomy_entry_key='Material',
                              content=[contents['thermal_conductivity'],
                                       contents['density'],
                                       contents['specific_heat']],
                              )

        mapper.register(cls_map.taxonomy_entry_key, cls, taxonomy_map=cls_map)
        mapped_cls = mapper.get_mapped_class(cls_map.taxonomy_entry_key)
        return mapped_cls

    def create_layer_cls(cls, contents: dict[str, Content]):
        cls_map = TaxonomyMap(taxonomy_name='PySimultan',
                              taxonomy_key='PySimultan',
                              taxonomy_entry_name='Layer',
                              taxonomy_entry_key='Layer',
                              content=[contents['thickness'], contents['material']],
                              )

        mapper.register(cls_map.taxonomy_entry_key, cls, taxonomy_map=cls_map)
        mapped_cls = mapper.get_mapped_class(cls_map.taxonomy_entry_key)
        return mapped_cls

    def create_construction_cls(cls, contents: dict[str, Content]):
        cls_map = TaxonomyMap(taxonomy_name='PySimultan',
                              taxonomy_key='PySimultan',
                              taxonomy_entry_name='Construction',
                              taxonomy_entry_key='Construction',
                              content=[contents['layers'], contents['r_value']],
                              )

        mapper.register(cls_map.taxonomy_entry_key, cls, taxonomy_map=cls_map)
        mapped_cls = mapper.get_mapped_class(cls_map.taxonomy_entry_key)
        return mapped_cls

    def create_wall_cls(cls, contents: dict[str, Content]):
        cls_map = TaxonomyMap(taxonomy_name='PySimultan',
                              taxonomy_key='PySimultan',
                              taxonomy_entry_name='Wall',
                              taxonomy_entry_key='Wall',
                              content=[contents['r_si'],
                                       contents['r_se'],
                                       contents['construction'],
                                       contents['u_value'],
                                       contents['boundary_condition']],
                              )

        mapper.register(cls_map.taxonomy_entry_key, cls, taxonomy_map=cls_map)
        mapped_cls = mapper.get_mapped_class(cls_map.taxonomy_entry_key)
        return mapped_cls

    def create_zone_cls(cls, contents: dict[str, Content]):
        cls_map = TaxonomyMap(taxonomy_name='PySimultan',
                              taxonomy_key='PySimultan',
                              taxonomy_entry_name='Zone',
                              taxonomy_entry_key='Zone',
                              content=[contents['walls'],
                                       contents['volume'],
                                       contents['area'],
                                       contents['u_value'],
                                       contents['sources'],
                                       contents['steady_state_temperature']],
                              )

        mapper.register(cls_map.taxonomy_entry_key, cls, taxonomy_map=cls_map)
        mapped_cls = mapper.get_mapped_class(cls_map.taxonomy_entry_key)
        return mapped_cls

    def create_temperature_bc_cls(cls, contents: dict[str, Content]):
        cls_map = TaxonomyMap(taxonomy_name='PySimultan',
                              taxonomy_key='PySimultan',
                              taxonomy_entry_name='TemperatureBoundaryCondition',
                              taxonomy_entry_key='TemperatureBoundaryCondition',
                              content=[contents['temperature']],
                              )

        mapper.register(cls_map.taxonomy_entry_key, cls, taxonomy_map=cls_map)
        mapped_cls = mapper.get_mapped_class(cls_map.taxonomy_entry_key)
        return mapped_cls

    def create_heat_flux_bc_cls(cls, contents: dict[str, Content]):
        cls_map = TaxonomyMap(taxonomy_name='PySimultan',
                              taxonomy_key='PySimultan',
                              taxonomy_entry_name='HeatFluxBoundaryCondition',
                              taxonomy_entry_key='HeatFluxBoundaryCondition',
                              content=[contents['heat_flux']],
                              )

        mapper.register(cls_map.taxonomy_entry_key, cls, taxonomy_map=cls_map)
        mapped_cls = mapper.get_mapped_class(cls_map.taxonomy_entry_key)
        return mapped_cls

    def create_source_cls(cls, contents: dict[str, Content]):
        cls_map = TaxonomyMap(taxonomy_name='PySimultan',
                              taxonomy_key='PySimultan',
                              taxonomy_entry_name='Source',
                              taxonomy_entry_key='Source',
                              content=[contents['temperature'],
                                       contents['heat_flux']],
                              )

        mapper.register(cls_map.taxonomy_entry_key, cls, taxonomy_map=cls_map)
        mapped_cls = mapper.get_mapped_class(cls_map.taxonomy_entry_key)
        return mapped_cls

    def create_reference_face_cls(cls, contents: dict[str, Content]):
        cls_map = TaxonomyMap(taxonomy_name='PySimultan',
                              taxonomy_key='PySimultan',
                              taxonomy_entry_name='ReferenceFace',
                              taxonomy_entry_key='ReferenceFace',
                              content=[contents['construction'],
                                       contents['assembly'],
                                       contents['mesh_size']
                                       ],
                              )
        mapper.register(cls_map.taxonomy_entry_key, cls, taxonomy_map=cls_map)
        mapped_cls = mapper.get_mapped_class(cls_map.taxonomy_entry_key)
        return mapped_cls

    def create_assembly_cls(cls, contents: dict[str, Content]):

        cls_map = TaxonomyMap(taxonomy_name='PySimultan',
                              taxonomy_key='PySimultan',
                              taxonomy_entry_name='Assembly',
                              taxonomy_entry_key='Assembly',
                              content=[contents['volumes'],
                                       contents['mesh'],
                                       contents['features']],
                              )

        mapper.register(cls_map.taxonomy_entry_key, cls, taxonomy_map=cls_map)
        mapped_cls = mapper.get_mapped_class(cls_map.taxonomy_entry_key)
        return mapped_cls

    def create_volume_cls(cls, contents: dict[str, Content]):
        cls_map = TaxonomyMap(taxonomy_name='PySimultan',
                              taxonomy_key='PySimultan',
                              taxonomy_entry_name='Volume',
                              taxonomy_entry_key='Volume',
                              content=[contents['geometry_file']],
                              )

        mapper.register(cls_map.taxonomy_entry_key, cls, taxonomy_map=cls_map)
        mapped_cls = mapper.get_mapped_class(cls_map.taxonomy_entry_key)
        return mapped_cls

    def create_mesh_cls(cls, contents: dict[str, Content]):
        cls_map = TaxonomyMap(taxonomy_name='PySimultan',
                              taxonomy_key='PySimultan',
                              taxonomy_entry_name='Mesh',
                              taxonomy_entry_key='Mesh',
                              content=[contents['mesh_file']],
                              )

        mapper.register(cls_map.taxonomy_entry_key, cls, taxonomy_map=cls_map)
        mapped_cls = mapper.get_mapped_class(cls_map.taxonomy_entry_key)
        return mapped_cls

    tax_contents = create_contents()

    mapped_type_test_class = create_mapped_type_test_class(classes['TypeTestClass'], tax_contents)
    mapped_material_cls = create_mapped_material(classes['Material'], tax_contents)
    mapped_layer_cls = create_layer_cls(classes['WallLayer'], tax_contents)
    mapped_construction_cls = create_construction_cls(classes['Construction'], tax_contents)
    mapped_wall_cls = create_wall_cls(classes['Wall'], tax_contents)
    mapped_zone_cls = create_zone_cls(classes['Zone'], tax_contents)
    mapped_temperature_bc_cls = create_temperature_bc_cls(classes['TemperatureBoundaryCondition'], tax_contents)
    mapped_heat_flux_bc_cls = create_heat_flux_bc_cls(classes['HeatFluxBoundaryCondition'], tax_contents)
    mapped_source_cls = create_source_cls(classes['Source'], tax_contents)
    mapped_reference_face_cls = create_reference_face_cls(classes['ReferenceFace'], tax_contents)
    mapped_assembly_cls = create_assembly_cls(classes['Assembly'], tax_contents)
    mapped_volume_cls = create_volume_cls(classes['Volume'], tax_contents)
    mapped_mesh_cls = create_mesh_cls(classes['Mesh'], tax_contents)

    mapped_cls_dict = {'Material': mapped_material_cls,
                       'Layer': mapped_layer_cls,
                       'Construction': mapped_construction_cls,
                       'Wall': mapped_wall_cls,
                       'Zone': mapped_zone_cls,
                       'TemperatureBoundaryCondition': mapped_temperature_bc_cls,
                       'HeatFluxBoundaryCondition': mapped_heat_flux_bc_cls,
                       'Source': mapped_source_cls,
                       'TypeTestClass': mapped_type_test_class,
                       'Assembly': mapped_assembly_cls,
                       'ReferenceFace': mapped_reference_face_cls,
                       'Volume': mapped_volume_cls,
                       'Mesh': mapped_mesh_cls}

    return mapped_cls_dict


def create_new_steady_state_zone(mapped_classes,
                                 data_model: Optional[DataModel] = None):
    geo_model = create_geometry_model(name='new_geometry_test',
                                      data_model=data_model)
    cube = create_cube(data_model, geo_model, scale=10)
    TypeTestClass = mapped_classes['TypeTestClass']
    Material = mapped_classes['Material']
    WallLayer = mapped_classes['Layer']
    Construction = mapped_classes['Construction']
    Wall = mapped_classes['Wall']
    Zone = mapped_classes['Zone']
    TemperatureBoundaryCondition = mapped_classes['TemperatureBoundaryCondition']
    HeatFluxBoundaryCondition = mapped_classes['HeatFluxBoundaryCondition']
    Source = mapped_classes['Source']
    Assembly = mapped_classes['Assembly']
    ReferenceFace = mapped_classes['ReferenceFace']
    Volume = mapped_classes['Volume']
    Mesh = mapped_classes['Mesh']

    t_out_1 = TemperatureBoundaryCondition(name='t_out_1',
                                           temperature=273.15,
                                           data_model=data_model)

    t_out_2 = TemperatureBoundaryCondition(name='t_out_2',
                                           temperature=283.15,
                                           data_model=data_model)

    concrete = Material(name='concrete',
                        thermal_conductivity=1.5,
                        density=2000,
                        specific_heat=800,
                        data_model=data_model)

    insulation = Material(name='insulation',
                          thermal_conductivity=0.03,
                          density=150,
                          specific_heat=1500,
                          data_model=data_model)

    plaster = Material(name='plaster',
                       thermal_conductivity=0.6,
                       density=1200,
                       specific_heat=700,
                       data_model=data_model)

    construction_1 = Construction(name='construction_1',
                                  layers=[WallLayer(name='concrete_layer', thickness=0.2, material=concrete),
                                          WallLayer(name='insulation_layer', thickness=0.1, material=insulation),
                                          WallLayer(name='plaster_layer', thickness=0.01, material=plaster)],
                                  data_model=data_model)

    construction_2 = Construction(name='construction_2',
                                  layers=[WallLayer(name='concrete_layer', thickness=0.15, material=concrete),
                                          WallLayer(name='insulation_layer', thickness=0.2, material=insulation)
                                          ],
                                  data_model=data_model
                                  )

    wall1 = Wall(name='Wall1',
                 r_si=0.13,
                 r_se=0.04,
                 construction=construction_1,
                 boundary_condition=t_out_1,
                 data_model=data_model)
    wall1.associate(cube.faces[0])

    wall2 = Wall(name='Wall2',
                 r_si=0.13,
                 r_se=0.04,
                 construction=construction_2,
                 boundary_condition=t_out_2,
                 data_model=data_model)
    wall2.associate(cube.faces[1])

    wall3 = Wall(name='Wall3',
                 r_si=0.13,
                 r_se=0.04,
                 construction=construction_1,
                 boundary_condition=t_out_1,
                 data_model=data_model)
    wall3.associate(cube.faces[2])

    wall4 = Wall(name='Wall4',
                 r_si=0.13,
                 r_se=0.04,
                 construction=construction_2,
                 boundary_condition=t_out_2,
                 data_model=data_model)
    wall4.associate(cube.faces[3])

    wall5 = Wall(name='Wall5',
                 r_si=0.13,
                 r_se=0.04,
                 construction=construction_2,
                 boundary_condition=t_out_1,
                 data_model=data_model)
    wall5.associate(cube.faces[4])

    wall6 = Wall(name='Wall6',
                 r_si=0.13,
                 r_se=0.04,
                 construction=construction_2,
                 boundary_condition=t_out_2,
                 data_model=data_model)
    wall6.associate(cube.faces[5])

    convective_heat_source = Source(name='convective_heat_source',
                                    heat_flux=1000,
                                    data_model=data_model)

    zone1 = Zone(name='zone_1',
                 walls=[wall1, wall2, wall3, wall4, wall5, wall6],
                 sources=[convective_heat_source],
                 data_model=data_model)
    zone1.associate(cube)

    print(cube.components)
    print(list(zone1.associated_geometry))

    steady_state_temperature = zone1.calculate_steady_state_temperature()
    print(steady_state_temperature)


def init_project(data_model: DataModel = None) -> dict[str, type]:

    classes = create_classes()
    mapped_classes = create_mapped_classes(classes)

    TypeTestClass = mapped_classes['TypeTestClass']
    Material = mapped_classes['Material']
    WallLayer = mapped_classes['Layer']
    Construction = mapped_classes['Construction']
    Wall = mapped_classes['Wall']
    Zone = mapped_classes['Zone']
    TemperatureBoundaryCondition = mapped_classes['TemperatureBoundaryCondition']
    HeatFluxBoundaryCondition = mapped_classes['HeatFluxBoundaryCondition']
    Source = mapped_classes['Source']
    Assembly = mapped_classes['Assembly']
    ReferenceFace = mapped_classes['ReferenceFace']
    Volume = mapped_classes['Volume']
    Mesh = mapped_classes['Mesh']

    type_test = TypeTestClass(name='type_test',
                              int_value=1,
                              float_value=1.0,
                              str_value='test',
                              bool_value=True,
                              list_value=[Material(name='material 1'),
                                          Material(name='material 2'),
                                          Material(name='material 3')],
                              dict_value={'a': 1, 'b': 2},
                              none_value=None,
                              obj_value=Material(name='material'),
                              numpy_value=np.array([
                                  [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
                                  [[10, 11, 12], [13, 14, 15], [16, 17, 18]],
                                  [[19, 20, 21], [22, 23, 24], [25, 26, 27]],
                                  [[28, 29, 30], [31, 32, 33], [34, 35, 36]]
                              ]),
                              pandas_value=pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]}),
                              file_value=None)

    create_new_steady_state_zone(mapped_classes,
                                 data_model=data_model)

    data_model.save()
    data_model.cleanup()
    mapper.clear()

    return mapped_classes


def map_methods(mapped_classes):

    def create_asset(*args, **kwargs):

        data_model = kwargs.get('data_model')

        new_asset = FileInfo.from_string(filename='new_asset.txt',
                                         data_model=data_model,
                                         content='This is a new asset file')

        print('Asset created')

    cls = mapper.get_mapped_class('Zone')

    method_mapper.register_method(cls=cls,
                                  name='calculate_steady_state_temperature',
                                  method=cls.calculate_steady_state_temperature,
                                  args=[],
                                  kwargs={})

    method_mapper.register_method(cls=cls,
                                  name='calculate_area',
                                  method=cls.calculate_area,
                                  args=[],
                                  kwargs={})

    method_mapper.register_method(name='Create new steady state zone',
                                  method=create_new_steady_state_zone,
                                  args=[mapped_classes],
                                  add_data_model_to_kwargs=True)

    method_mapper.register_method(name='create_asset',
                                  method=create_asset,
                                  add_data_model_to_kwargs=True)

    method_mapper.register_method(name='Say hello',
                                  method=lambda: print('Hello!'),
                                  args=[],
                                  kwargs={})


mapper.clear()

mapped_classes = init_project(data_model=new_data_model)
map_methods(mapped_classes)
run_ui()

print('Test passed 48 47 2')
