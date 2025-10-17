from nicegui import ui, app
from typing import Optional, Any, Callable, Union
import logging

from numpy import ndarray

from .. import user_manager
from ..core.user import User
from .. import core
from ..views.utils import create_new_component
from PySimultan2.simultan_object import SimultanObject
from PySimultan2.taxonomy_maps import Content
from PySimultan2.files import FileInfo, DirectoryInfo
from PySimultan2.default_types import ComponentDictionary
from PySimultan2.multi_values import simultan_multi_value_field_3d_to_numpy
from math import inf

from SIMULTAN.Data.MultiValues import (SimMultiValueField3D, SimMultiValueField3DParameterSource, SimMultiValueBigTable,
                                       SimMultiValueBigTableHeader, SimMultiValueBigTableParameterSource)


logger = logging.getLogger('py_simultan_ui')


def get_value_content_type(value):
    if value is None:
        return 'None'
    if isinstance(value, str):
        return 'str'
    elif isinstance(value, int):
        return 'int'
    elif isinstance(value, float):
        return 'float'
    elif isinstance(value, SimultanObject):
        return 'Component'
    else:
        return 'None'


class ParameterEditDialog(object):

    def __init__(self, *args, **kwargs):
        self.sim_parameter = kwargs.get('sim_parameter', None)


class BoolEditDialog(ParameterEditDialog):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value_input = None

    def ui_content(self):
        with ui.row():
            self.value_input = ui.checkbox(value=self.sim_parameter.Value if self.sim_parameter is not None else False)

    @property
    def value(self):
        return bool(self.value_input.value)


class IntEditDialog(ParameterEditDialog):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.value_input = None
        self.min_input = None
        self.max_input = None
        self.unit_input = None

    def ui_content(self):
        with ui.row():
            self.value_input = ui.number(value=int(self.sim_parameter.Value) if self.sim_parameter is not None else 0,
                                         precision=0,
                                         validation=self.validate, label='Value')

            if hasattr(self.sim_parameter, 'ValueMin'):
                min_val = self.sim_parameter.ValueMin
            else:
                min_val = -inf

            self.min_input = ui.number(value=min_val if (min_val != -inf and min_val != inf) else None,
                                       precision=0,
                                       validation=self.validate, label='Min. Value')
            if hasattr(self.sim_parameter, 'ValueMax'):
                max_val = self.sim_parameter.ValueMax
            else:
                max_val = -inf
            self.max_input = ui.number(value=max_val if (max_val != inf and max_val != -inf) else None,
                                       precision=0,
                                       validation=self.validate, label='Max. Value')

            if hasattr(self.sim_parameter, 'Unit'):
                unit = self.sim_parameter.Unit
            else:
                unit = ''

            self.unit_input = ui.input(value=unit,
                                       label='Unit')

    @staticmethod
    def validate(value):
        try:
            int(value)
        except ValueError:
            return "Value must be an integer!"

    @property
    def value(self):
        return int(self.value_input.value)

    @property
    def min(self):
        if self.min_input.value is None:
            return -999999999
        return int(self.min_input.value) if self.min_input.value != -inf else -999999999

    @property
    def max(self):
        if self.max_input is None:
            return 999999999

        if self.max_input.value is None:
            return 999999999
        return int(self.max_input.value) if self.max_input.value != inf else 999999999

    @property
    def unit(self):
        return self.unit_input.value


class FloatEditDialog(IntEditDialog):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def ui_content(self):
        with ui.row():
            self.value_input = ui.number(value=float(self.sim_parameter.Value) if self.sim_parameter is not None else 0,
                                         validation=self.validate, label='Value')

            if hasattr(self.sim_parameter, 'ValueMin'):
                min_val = self.sim_parameter.ValueMin
            else:
                min_val = None

            self.min_input = ui.number(value=min_val if min_val != -inf else None,
                                       validation=self.validate, label='Min. Value')
            if hasattr(self.sim_parameter, 'ValueMax'):
                max_val = self.sim_parameter.ValueMax
            else:
                max_val = None
            self.max_input = ui.number(value=max_val if max_val != inf else None,
                                       validation=self.validate, label='Max. Value')

            if hasattr(self.sim_parameter, 'Unit'):
                unit = self.sim_parameter.Unit
            else:
                unit = ''

            self.unit_input = ui.input(value=unit,
                                       label='Unit')

    @staticmethod
    def validate(value):
        try:
            float(value)
        except ValueError:
            return "Value must be an float!"

    @property
    def value(self):
        return float(self.value_input.value)

    @property
    def min(self):
        if self.min_input.value is None:
            return -inf
        return float(self.min_input.value)

    @property
    def max(self):
        if self.max_input.value is None:
            return inf
        return float(self.max_input.value)


class StrEditDialog(ParameterEditDialog):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value_input = None

    def ui_content(self):
        with ui.row():
            self.value_input = ui.input(value=self.sim_parameter.Value if self.sim_parameter is not None else '')

    @property
    def value(self):
        return self.value_input.value


class ComponentEditDialog(object):

    def __init__(self, *args, **kwargs):
        self.select_multiple = kwargs.get('select_multiple', True)
        self.component = kwargs.get('component', None)
        self.content = kwargs.get('content', None)
        self.parent = kwargs.get('parent', None)
        self.dialog = None

        self.class_select = None
        self.component_select = None

        self.component_name_map: dict = {}

    @property
    def value(self):
        if len(self.component_select.value) == 0:
            return None
        elif isinstance(self.component_select.value, list):
            return [self.component_name_map[x] for x in self.component_select.value]
        else:
            return self.component_name_map[self.component_select.value]

    @ui.refreshable
    def ui_content(self):
        with ui.card():
            ui.label('Select component')
            mapper = user_manager[app.storage.user['username']].mapper
            classes = mapper.mapped_classes

            if isinstance(self.component, ComponentDictionary):
                select_value = self.component[self.content.property_name]
                if select_value is not None and hasattr(select_value, '_taxonomy'):
                    select_value = select_value._taxonomy
                else:
                    select_value = 'All'
            elif isinstance(self.component, SimultanObject):
                select_value = getattr(self.component, self.content.property_name)
                if select_value is not None and hasattr(select_value, '_taxonomy'):
                    select_value = select_value._taxonomy
                else:
                    select_value = 'All'
            else:
                select_value = 'All'

            self.class_select = ui.select(['All', *classes.keys()],
                                          label='Select class',
                                          value=select_value if select_value is not None else None,
                                          multiple=False,
                                          on_change=self.on_cls_change,
                                          with_input=True
                                          ).classes('w-full').props('use-chips')
            self.component_ui_content()

    @ui.refreshable
    def component_ui_content(self):

        components = []
        self.component_name_map = {}

        mapper = user_manager[app.storage.user['username']].mapper

        if 'All' in self.class_select.value:
            for cls in mapper.mapped_classes.values():
                components.extend(cls.cls_instances)
        else:
            if isinstance(self.class_select.value, str):
                selected_val = [self.class_select.value]
            else:
                selected_val = self.class_select.value

            for cls in [mapper.get_mapped_class(x) for x in selected_val]:
                components.extend(cls.cls_instances)

        self.component_name_map = dict(zip([f'{component.name} ({component.id})' for component in components], [component for component in components]))

        if isinstance(self.component, ComponentDictionary):
            sel_comp = self.component[self.content.property_name]
            if sel_comp is not None:
                select_value = [f'{sel_comp.name} ({sel_comp.id})']
            else:
                select_value = []
        elif isinstance(self.component, SimultanObject):
            sel_comp = getattr(self.component, self.content.property_name)
            if isinstance(sel_comp, SimultanObject):
                select_value = [f'{sel_comp.name} ({sel_comp.id})']
            else:
                select_value = None
        else:
            select_value = []

        self.component_select = ui.select(list(self.component_name_map.keys()),
                                          label='Select component',
                                          value=select_value,
                                          multiple=self.select_multiple,
                                          with_input=True,
                                          on_change=self.on_component_change
                                          ).classes('w-64').props('use-chips')

        ui.button(icon='add',
                  on_click=self.new_component).classes('q-ml-auto')

    def on_cls_change(self, event):
        self.component_ui_content.refresh()

    def on_component_change(self, event):
        pass

    async def new_component(self):
        mapper = user_manager[app.storage.user['username']].mapper
        classes = mapper.mapped_classes

        with ui.dialog() as dialog, ui.card():

            ui.label('Create New Component')
            class_select = ui.select(['All', *classes.keys()],
                                          label='Select class',
                                          value=None,
                                          multiple=False,
                                          with_input=True
                                          ).classes('w-full').props('use-chips')

            with ui.row():
                ui.button('OK', on_click=lambda: dialog.submit({'ok': True,
                                                                'cls': class_select.value,}
                                                               )
                          )
                ui.button('Cancel', on_click=lambda: dialog.submit({'ok': False}))

        result = await dialog

        if result and result.get('ok', False):
            cls = result.get('cls', None)
        else:
            return None

        if cls is not None:
            new_component = await create_new_component(mapper.mapped_classes[cls],
                                                       mapper=mapper,
                                                       data_model=user_manager[app.storage.user['username']].data_model)
            if new_component is not None:
                if self.select_multiple:
                    value = [f'{new_component.name} ({new_component.id})']
                else:
                    value = f'{new_component.name} ({new_component.id})'

                self.class_select.value = cls
                self.component_select.set_options([*self.component_select.options, f'{new_component.name} ({new_component.id})'],
                                                  value=value)
                self.component_select.update()

        print('done')

class AssetEditDialog(object):

    def __init__(self, *args, **kwargs):

        self.asset_select = None

        asset = kwargs.get('asset', None)

        self.asset = asset if isinstance(asset, FileInfo) else None
        self.content = kwargs.get('content', None)
        self.parent = kwargs.get('parent', None)
        self.dialog = None

        self.asset_name_map = {}

    def ui_content(self):
        with ui.card():
            ui.label('Select asset')
            assets = user_manager[app.storage.user['username']].asset_manager.items
            self.asset_name_map = {x.name: x for x in assets}
            self.asset_select = ui.select([x.name for x in assets],
                                          label='Select asset',
                                          value=self.asset.name if self.asset is not None else None,
                                          on_change=self.asset_select,
                                          with_input=True
                                          ).classes('w-64').props('use-chips')

    @property
    def value(self):
        if len(self.asset_select.value) == 0:
            return None

        return self.asset_name_map[self.asset_select.value]


class ArrayEditDialog(object):

    def __init__(self, *args, **kwargs):
        self.array_select = None
        asset = kwargs.get('array', None)

        self.array: SimMultiValueField3D = asset if isinstance(asset, ndarray) else None
        self.content = kwargs.get('content', None)
        self.parent = kwargs.get('parent', None)
        self.dialog = None

        self.array_name_map = {}

    @property
    def user(self) -> User:
        return user_manager[app.storage.user['username']]

    def ui_content(self):
        with ui.card():
            ui.label('Select Array')
            arrays = self.user.array_manager.np_items
            self.array_name_map = {x.Name: x for x in arrays.values()}
            self.array_select = ui.select([x.Name for x in arrays.values()],
                                          label='Select asset',
                                          value=self.array.Name if self.array is not None else None,
                                          on_change=self.array_select,
                                          with_input=True
                                          ).classes('w-64').props('use-chips')

    @property
    def value(self):
        if len(self.array_select.value) == 0:
            return None

        return self.array_name_map[self.array_select.value]


default_options = ['None', 'str', 'int', 'float', 'bool', 'Component', 'Asset', 'Array', 'Table']


class ContentTypeChooser(object):

    def __init__(self, *args, **kwargs):
        self.content_type = kwargs.get('content_type', str)
        self.select = None
        self.value = None
        self.options = kwargs.get('options', default_options)

        self.on_change = kwargs.get('on_change', None)

    def ui_content(self):
        self.select = ui.select(self.options,
                                value=self.content_type if self.content_type in self.options else self.options[0],
                                label='Content type',
                                on_change=self.on_change).classes('w-full')

    def on_change(self, event):
        if self.on_change is not None:
            self.on_change(event, self.value)


class ContentEditDialog(object):

    def __init__(self, *args, **kwargs):

        self._raw_val = None

        self._options = None

        self.select_multiple = kwargs.get('select_multiple', False)
        self.component = kwargs.get('component')
        self.raw_val = kwargs.get('raw_val', None)
        self.parent = kwargs.get('parent', None)
        self.content = kwargs.get('content')
        self.taxonomy = kwargs.get('taxonomy', None)
        self.object_mapper = kwargs.get('object_mapper', None)
        self.dialog = None

        if self.component is not None:
            if isinstance(self.component, ComponentDictionary):
                val_type = get_value_content_type(self.component[self.content.property_name])
            else:
                val_type = get_value_content_type(getattr(self.component, self.content.property_name))
        else:
            val_type = 'None'

        self.content_type = ContentTypeChooser(on_change=self.on_type_change,
                                               content_type=val_type,
                                               options=self.options)
        self.options = kwargs.get('options', default_options)


        self.edit_dialog = None

    @property
    def options(self):
        return self._options

    @options.setter
    def options(self, value):
        self._options = value
        if self.content_type is not None:
            self.content_type.options = value

    @property
    def raw_val(self):
        try:
            if self._raw_val is None:
                self._raw_val = self.component.get_raw_attr(self.content.property_name)
            return self._raw_val
        except Exception as e:
            return None

    @raw_val.setter
    def raw_val(self, value):
        self._raw_val = value

    def create_edit_dialog(self):
        with ui.dialog() as self.dialog, ui.card():
            # ui.label(f'Edit {self.content.name}')
            self.content_type.ui_content()
            self.ui_content()
            with ui.row():
                ui.button('Ok', on_click=self.save)
                ui.button('Cancel', on_click=self.close)
            self.dialog.open()

    @ui.refreshable
    def ui_content(self):
        if self.content_type.select.value == 'str':
            self.edit_dialog = StrEditDialog(sim_parameter=self.raw_val)
            self.edit_dialog.ui_content()
        elif self.content_type.select.value == 'bool':
            self.edit_dialog = BoolEditDialog(sim_parameter=self.raw_val)
            self.edit_dialog.ui_content()
        elif self.content_type.select.value == 'int':
            self.edit_dialog = IntEditDialog(sim_parameter=self.raw_val)
            self.edit_dialog.ui_content()
        elif self.content_type.select.value == 'float':
            self.edit_dialog = FloatEditDialog(sim_parameter=self.raw_val)
            self.edit_dialog.ui_content()
        elif self.content_type.select.value == 'Component':
            self.edit_dialog = ComponentEditDialog(component=self.component,
                                                   content=self.content,
                                                   parent=self.parent,
                                                   select_multiple=self.select_multiple)
            self.edit_dialog.ui_content()
        elif self.content_type.select.value == 'Asset':
            self.edit_dialog = AssetEditDialog(asset=self.component,
                                               content=self.content,
                                               parent=self.parent)
            self.edit_dialog.ui_content()
        elif self.content_type.select.value == 'Array':
            self.edit_dialog = ArrayEditDialog(array=self.component,
                                               content=self.content,
                                               parent=self.parent)
            self.edit_dialog.ui_content()
        else:
            ui.label('Not implemented content type!')

    def on_type_change(self):
        self.ui_content.refresh()

    def close(self, *args, **kwargs):
        if self.dialog is not None:
            self.dialog.close()
            self.dialog = None

    def save(self, *args, **kwargs):

        if self.content_type.select.value == 'None':
            val = None
        else:
            val = self.edit_dialog.value

        setattr(self.parent.component, self.content.property_name, val)
        if self.content_type.select.value in ['int', 'float']:
            if self.raw_val is None:
                self.raw_val = self.parent.component.get_raw_attr(self.content.property_name)
            setattr(self.raw_val, 'ValueMin', self.edit_dialog.min)
            setattr(self.raw_val, 'ValueMax', self.edit_dialog.max)
            setattr(self.raw_val, 'Unit', self.edit_dialog.unit)

        logger.info(f'Updated {self.content.name} to {self.edit_dialog.value}')

        if self.parent is not None:
            if hasattr(self.parent, 'refresh'):
                self.parent.refresh()
            elif hasattr(self.parent, 'ui_content') and hasattr(self.parent.ui_content, 'refresh'):
                self.parent.ui_content.refresh()

        self.close()

        from ..views.detail_views import show_detail
        show_detail(value=self.parent.component)


class DictEditDialog(object):

    def __init__(self, *args, **kwargs):
        self.component = kwargs.get('component', None)
        self._key = None

        self.parent = kwargs.get('parent', None)
        self.dialog = None

        self.key_edit = None
        self.edit_dialog = None
        self.key = kwargs.get('key', None)

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, value):
        self._key = value
        if self.key_edit is not None:
            self.key_edit.value = value

    def create_edit_dialog(self):
        with ui.dialog() as self.dialog, ui.card():
            ui.label(f'Edit {self.key}')
            self.ui_content()
            with ui.row():
                ui.button('Save', on_click=self.save)
                ui.button('Cancel', on_click=self.close)
            self.dialog.open()

    @ui.refreshable
    def ui_content(self):
        self.key_edit = ui.input(value=self.key, label='Key', on_change=self.on_key_change)
        self.edit_dialog = ContentEditDialog(component=getattr(self.parent.component, self.key) if self.key is not None else None,
                                             content=None,
                                             parent=self.parent,
                                             select_multiple=False)
        self.edit_dialog.content_type.ui_content()
        self.edit_dialog.ui_content()

    def on_key_change(self, event):
        self.key = self.key_edit.value

    def close(self, *args, **kwargs):
        if self.dialog is not None:
            self.dialog.close()
            self.dialog = None

    def save(self, *args, **kwargs):
        setattr(self.parent.component, self.key, self.edit_dialog.value)

        logger.info(f'Updated {self.key} to {self.edit_dialog.value}')

        if self.parent is not None:
            self.parent.ui_content.refresh()
        self.close()


class TypedComponentEditDialog(ui.dialog):

    def __init__(self,
                 simultan_object: SimultanObject,
                 content: Content,
                 type_options: list[Union[type(FileInfo), type(DirectoryInfo), type(SimultanObject)]],
                 select_multiple=False,
                 parent_ui_content=None,
                 value_options: Optional[list[SimultanObject, FileInfo, DirectoryInfo]] = None,
                 refresh_fcn: Optional[Callable] = None,
                 add_super_instances: bool = False,
                 *args,
                 **kwargs):

        self._value_options = None

        self.simultan_object = simultan_object
        self.content = content
        self.select_multiple = select_multiple
        self.parent_ui_content = parent_ui_content

        self.refresh_fcn = refresh_fcn
        self.type_options = type_options
        self.value_options = value_options
        self.add_super_instances = add_super_instances

        self.value_select = None

        super().__init__(value=True)

        with self, ui.card():
            self.value_select_ui_content()
            with ui.row():
                ui.button('Save', on_click=self.save)
                ui.button('Cancel', on_click=self.btn_close)

    @property
    def mapper(self):
        return self.simultan_object._object_mapper

    @property
    def value_options(self) -> Optional[list[SimultanObject, FileInfo, DirectoryInfo]]:
        if self._value_options is None:
            options = set()
            for cls in self.type_options:
                options.update(cls.cls_instances)
                if self.add_super_instances:
                    for super_cls in cls.super_class_instances:
                        options.update(super_cls.cls_instances)
            self._value_options = list(options)
        return self._value_options

    @value_options.setter
    def value_options(self, value):
        self._value_options = value

    @property
    def value_options_dict(self) -> dict:
        return {hash(x): x.name for x in self.value_options}

    @property
    def current_value(self) -> Any:
        return getattr(self.simultan_object, self.content.property_name)

    @ui.refreshable
    def value_select_ui_content(self):

        if self.current_value is None:
            value = None
        else:
            value = hash(self.current_value)

        self.value_select = ui.select(label='Select value',
                                      options=self.value_options_dict,
                                      value=value,
                                      with_input=True,
                                      multiple=self.select_multiple,
                                      ).classes('w-full').props('use-chips')

    def btn_close(self, *args, **kwargs):
        self.submit({'ok': False, 'value': self.current_value})
        self.close()

    def save(self, *args, **kwargs):

        self.submit({'ok': True, 'value': self.current_value})
        self.close()

        selected_value = next((x for x in self.value_options if hash(x) == self.value_select.value), None)

        if self.current_value is not selected_value:
            setattr(self.simultan_object, self.content.property_name, selected_value)

        if self.refresh_fcn is not None:
            self.refresh_fcn()
        elif hasattr(self.parent_ui_content, 'refresh'):
            self.parent_ui_content.refresh()
