from nicegui import ui
from typing import Optional, Union, Any
from ..type_view import TypeView
from nicegui import ui, events, app

from numpy import ndarray
from pandas import DataFrame

from ..component_detail_base_view import ComponentDetailBaseView

from ...core.edit_dialog import DictEditDialog
from ...core.edit_dialog import ContentEditDialog
from ...core.geo_associations import GeoEditDialog

from PySimultan2.simultan_object import SimultanObject
from PySimultan2.default_types import ComponentDictionary
from PySimultan2.files import FileInfo, DirectoryInfo
from PySimultan2.geometry import GeometryModel

from ..parameter_view import ParameterView
from ..mapped_cls.mapped_cls_view import ContentItemView

from SIMULTAN.Data.Components import (SimEnumParameter, SimIntegerParameter, SimStringParameter, SimDoubleParameter)


class DictItemView(object):

    def __init__(self, *args, **kwargs):
        self.component: SimultanObject = kwargs.get('component')
        self.parent = kwargs.get('parent')
        self.key = kwargs.get('key')

    @property
    def view_manager(self):
        return self.parent.view_manager

    @ui.refreshable
    def ui_content(self):

        from ..detail_views import show_detail

        with ui.item().classes('w-full'):
            with ui.item_section():
                ui.label(f'{self.key}:')

            val = self.component
            if isinstance(val, SimultanObject):
                if not hasattr(val, '__ui_element__'):
                    val.__ui_element__ = None
                if val.__ui_element__ is None:
                    self.view_manager.views[val._taxonomy]['item_view_manager'].add_item_to_view(val)
                with ui.item_section():
                    ui.label(f'{val.name}')
                    ui.button('Details', on_click=lambda e: show_detail(val))
                with ui.item_section():
                    ui.label(f'{val.id}')
            elif isinstance(val, (int, float, str)):
                with ui.item_section():
                    raw_val = self.parent.component.get_raw_attr(self.key)
                    ParameterView(component=val,
                                  raw_val=raw_val,
                                  parent=self).ui_content()
            else:
                with ui.item_section():
                    if hasattr(val, 'name'):
                        ui.label(f'{val.name}:')
                    else:
                        ui.label('No Name')
                with ui.item_section():
                    if hasattr(val, 'id'):
                        ui.label(f'{val.id}:')
                    else:
                        ui.label('No ID')

    def edit(self, event):
        ui.notify('Edit not implemented yet', type='negative')
        raise NotImplementedError

    def remove(self, event):
        ui.notify('Edit not implemented yet', type='negative')
        raise NotImplementedError


class DictView(object):

    def __init__(self, *args, **kwargs):
        self.component: ComponentDictionary = kwargs.get('component')
        self.parent = kwargs.get('parent')
        self.card = None

        self.content_item_views: dict[str: ContentItemView] = {}

    @property
    def view_manager(self):
        return self.parent.view_manager

    @ui.refreshable
    def list_content(self):
        with ui.list().classes('w-full'):

            for key, value in self.component.items():
                if self.content_item_views.get(key, None) is None or self.content_item_views[key].component != value:
                    self.content_item_views[key] = DictItemView(component=self.component,
                                                                parent=self,
                                                                key=key)

                    self.content_item_views[key].ui_content()
                    ui.separator()

        ui.button(f'Add new item to {self.component.name}',
                  on_click=self.parent.add_new_item, icon='add').classes('q-ml-auto')

    @ui.refreshable
    def ui_content(self):
        with ui.expansion(icon='format_list_bulleted',
                          text=f'Content ({len(self.component)})',
                          value=True
                          ).classes('w-full').bind_text_from(self,
                                                                    'data',
                                                                    lambda x: f'Content ({len(self.component)})'
                                                                    ) as self.card:
            self.list_content()


class DictDetailView(ComponentDetailBaseView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content_view = DictView(component=self.component, parent=self)

    def add_new_item(self, event):
        self.parent.add_new_item(event)

    @property
    def parameters(self) -> tuple[list[tuple[str,
                                             Union[int, float, str],
                                             Union[SimIntegerParameter,
                                                   SimStringParameter,
                                                   SimEnumParameter,
                                                   SimDoubleParameter]
                                             ],
                                  list[tuple[str, SimultanObject]],
                                  list[tuple[str, Union[ndarray, DataFrame]]],
                                  list[tuple[str, FileInfo]],
                                  list[tuple[str, Any]],
                                  list[tuple[str, GeometryModel]],
                                  list[tuple[str, Any]]:
                                       ]
                                  ]:

        parameters = []
        components = []
        arrays = []
        assets = []
        undefined = []
        other = []
        geometry = []

        for key, val in self.component.items():
            if isinstance(val, SimultanObject):
                components.append((key, val))
            elif isinstance(val, (int, float, str)):
                raw_val = self.component.get_raw_attr(key)
                parameters.append((key, val, raw_val))
            elif isinstance(val, (ndarray, DataFrame)):
                arrays.append((key, val))
            elif isinstance(val, FileInfo):
                assets.append((key, val))
            elif val is None:
                undefined.append((key, val))
            else:
                other.append((key, val))

        return parameters, components, arrays, assets, other, geometry, undefined

    @ui.refreshable
    def ui_content(self, *args, **kwargs):
        super().ui_content()
        parameters, components, arrays, assets, other, geometry, undefined = self.parameters

        self.ui_dict_table()

        with ui.expansion(icon='format_list_bulleted',
                          text=f'Content ({len(self.component)})',
                          value=False,
                          ).classes('w-full').bind_text_from(self,
                                                                    'data',
                                                                    lambda x: f'Content ({len(self.component)})'
                                                                    ) as self.card:
            self.ui_param_table(parameters)
            self.ui_component_table(components)
            self.ui_array_table(arrays)
            self.ui_assets_table(assets)
            self.ui_undefined_table(undefined)

            ui.button(f'Add new item to {self.component.name}',
                      on_click=self.add_new_item, icon='add').classes('q-ml-auto')

    def ui_dict_table(self, title: Optional[str] = None):

        columns = [{'name': 'Key', 'label': 'Key', 'field': 'key', 'sortable': True},
                   {'name': 'value', 'label': 'Value', 'field': 'value', 'sortable': True}]

        value_names = [None] * len(self.component.items())

        for i, (key, value) in enumerate(self.component.items()):
            if isinstance(value, SimultanObject):
                value_names[i] = f'{value.name} ({value.id.LocalId})'
            elif isinstance(value, (ndarray, DataFrame)):
                val = self.component.get_raw_attr(key)
                value_names[i] = f'ND Array {val.ValueSource.Field.Name} ({val.ValueSource.Field.LocalID})'
            elif isinstance(value, FileInfo):
                value_names[i] = f'File {value.name} ({value.full_path})'
            elif isinstance(value, DirectoryInfo):
                value_names[i] = f'Directory {value.name} ({value.full_path})'
            else:
                value_names[i] = str(value)

        rows = [{'key': param[0],
                 'value': value_names[i],
                 }
                for i, param in enumerate(self.component.items())]

        if title is None:
            title = 'Dictionary'
        elif title == '':
            title = None

        dict_table = ui.table(columns=columns,
                              rows=rows,
                              title=title,
                              row_key='id').classes('w-full bordered')

        dict_table.add_slot('body', r'''
            <q-tr :props="props">
                <q-td v-for="col in props.cols" :key="col.name" :props="props">
                    {{ col.value }}
                </q-td>
                <q-td auto-width>
                    <q-btn size="sm" color="blue" round dense
                           @click="$parent.$emit('show_val', props)"
                           icon="launch" />
                    <q-btn size="sm" color="blue" round dense
                           @click="$parent.$emit('edit_val', props)"
                           icon="edit" />
                    <q-btn size="sm" color="red" round dense
                           @click="$parent.$emit('delete_val', props)"
                           icon="delete" />
                </q-td>
            </q-tr>
        ''')
        dict_table.on('edit_val', self.edit_key)
        dict_table.on('delete_val', self.delete_key)
        dict_table.on('show_val', self.show_val)

        ui.button(f'Add new item to {self.component.name}',
                  on_click=self.add_new_item, icon='add').classes('q-ml-auto')

    def show_val(self, e: events.GenericEventArguments):

        from ..detail_views import show_detail

        key = e.args['row'].get('key')
        val = self.component[key]
        if isinstance(val, (ndarray, DataFrame)):
            val = self.component.get_raw_attr(key).ValueSource.Field
        show_detail(val)

    def edit_key(self, e: events.GenericEventArguments):
        key = e.args['row'].get('key')
        val = self.component[key]
        content = self.component._taxonomy_map.content_dict['__dict_key__' + key]
        # val = getattr(self.component, content.property_name)
        edit_dialog = ContentEditDialog(component=self.component,
                                        parent=self,
                                        content=content,
                                        raw_val=self.component.get_raw_attr(content.property_name))
        edit_dialog.create_edit_dialog()

    def delete_key(self, e: events.GenericEventArguments):
        key = e.args['row'].get('key')
        del self.component[key]
        self.ui_content.refresh()

    def ui_param_table(self, parameters):
        # create int/float/str table
        columns = [{'name': 'id', 'label': 'ID', 'field': 'id', 'sortable': True},
                   {'name': 'name', 'label': 'Key', 'field': 'name', 'sortable': True},
                   {'name': 'value', 'label': 'Value', 'field': 'value', 'sortable': True},
                   {'name': 'min', 'label': 'Min', 'field': 'min', 'sortable': True},
                   {'name': 'max', 'label': 'Max', 'field': 'max', 'sortable': True},
                   {'name': 'unit', 'label': 'Unit', 'field': 'unit', 'sortable': True},
                   {'name': 'description', 'label': 'Description', 'field': 'description', 'sortable': False}]

        rows = [{'id': i,
                 'name': param[0],
                 'value': str(param[2].Value),
                 'min': str(param[2].ValueMin) if hasattr(param[2], 'ValueMin') else '',
                 'max': str(param[2].ValueMax) if hasattr(param[2], 'ValueMax') else '',
                 'unit': param[2].Unit if hasattr(param[2], 'Unit') else '',
                 'description': param[2].Description if hasattr(param[2], 'Description') else ''}
                for i, param in enumerate(parameters)]

        param_table = ui.table(columns=columns,
                               rows=rows,
                               title='Parameters',
                               row_key='id').classes('w-full bordered')

        param_table.add_slot('body', r'''
            <q-tr :props="props">
                <q-td v-for="col in props.cols" :key="col.name" :props="props">
                    {{ col.value }}
                </q-td>
                <q-td auto-width>
                    <q-btn size="sm" color="blue" round dense
                           @click="$parent.$emit('edit_val', props)"
                           icon="edit" />
                </q-td>
            </q-tr>
        ''')
        param_table.on('edit_val', self.edit_val)

    def ui_component_table(self, components):

        columns = [{'name': 'id', 'label': 'ID', 'field': 'id', 'sortable': True},
                   {'name': 'Key', 'label': 'Name', 'field': 'name', 'sortable': True},
                   {'name': 'component_id', 'label': 'Component ID', 'field': 'component_id', 'sortable': True},
                   {'name': 'component_name', 'label': 'Component Name', 'field': 'component_name', 'sortable': True},
                   {'name': 'component_type', 'label': 'Component Type', 'field': 'component_type', 'sortable': True},
                   {'name': 'type', 'label': 'Type', 'field': 'type', 'sortable': True},
                   ]

        rows = [{'id': str(i),
                 'component_id': str(comp[1].id),
                 'name': comp[0],
                 'component_name': comp[1].name,
                 'component_type': comp[1].__class__.__name__,
                 'type': 'Subcomponent' if comp[1]._wrapped_obj in
                                           [y.Component for y in self.component._wrapped_obj.Components]
                 else 'Reference'}
                for i, comp in enumerate(components)]

        comp_table = ui.table(columns=columns,
                              rows=rows,
                              title='Components',
                              row_key='id').classes('w-full bordered')

        comp_table.add_slot('body', r'''
                    <q-tr :props="props">
                        <q-td v-for="col in props.cols" :key="col.name" :props="props">
                            {{ col.value }}
                        </q-td>
                        <q-td auto-width>
                            <q-btn size="sm" color="blue" round dense
                                   @click="$parent.$emit('detail', props)"
                                   icon="launch" />
                            <q-btn size="sm" color="blue" round dense
                                   @click="$parent.$emit('edit_val', props)"
                                   icon="edit" />
                        </q-td>
                    </q-tr>
                ''')
        comp_table.on('edit_val', self.edit_val)
        comp_table.on('detail', self.show_detail)

    def ui_array_table(self, arrays):
        columns = [{'name': 'id', 'label': 'ID', 'field': 'id', 'sortable': True},
                   {'name': 'Key', 'label': 'Name', 'field': 'name', 'sortable': True},
                   {'name': 'type', 'label': 'Type', 'field': 'type', 'sortable': True}]

        rows = [{'id': str(i),
                 'name': str(comp[0]),
                 'type': 'ND Array' if isinstance(comp[1], ndarray) else 'Table'} for i, comp in enumerate(arrays)]

        comp_table = ui.table(columns=columns,
                              rows=rows,
                              title='Arrays',
                              row_key='id').classes('w-full bordered')

        comp_table.add_slot('body', r'''
                            <q-tr :props="props">
                                <q-td v-for="col in props.cols" :key="col.name" :props="props">
                                    {{ col.value }}
                                </q-td>
                                <q-td auto-width>
                                    <q-btn size="sm" color="blue" round dense
                                           @click="$parent.$emit('detail', props)"
                                           icon="launch" />
                                    <q-btn size="sm" color="blue" round dense
                                           @click="$parent.$emit('edit_val', props)"
                                           icon="edit" />
                                </q-td>
                            </q-tr>
                        ''')
        comp_table.on('edit_val', self.edit_val)
        comp_table.on('detail', self.show_detail)

    def ui_assets_table(self, assets):

        columns = [{'name': 'id', 'label': 'ID', 'field': 'id', 'sortable': True},
                   {'name': 'Key', 'label': 'Name', 'field': 'name', 'sortable': True},
                   {'name': 'path', 'label': 'Path', 'field': 'path', 'sortable': True}]

        rows = [{'id': i,
                 'name': asset[0],
                 'path': asset[1].full_path if isinstance(asset[1], FileInfo) else asset[1].path}
                for i, asset in enumerate(assets)]

        asset_table = ui.table(columns=columns,
                               rows=rows,
                               title='Assets',
                               row_key='id').classes('w-full bordered')

        asset_table.add_slot('body', r'''
            <q-tr :props="props">
                <q-td v-for="col in props.cols" :key="col.name" :props="props">
                    {{ col.value }}
                </q-td>
                <q-td auto-width>
                    <q-btn size="sm" color="blue" round dense
                           @click="$parent.$emit('edit_val', props)"
                           icon="edit" />
                </q-td>
            </q-tr>
        ''')
        asset_table.on('edit_val', self.edit_val)

    def ui_undefined_table(self, other):

        columns = [{'name': 'id', 'label': 'ID', 'field': 'id', 'sortable': True},
                   {'name': 'Key', 'label': 'Name', 'field': 'name', 'sortable': True},
                   {'name': 'value', 'label': 'Value', 'field': 'value', 'sortable': True}]

        rows = [{'id': i,
                 'name': param[0],
                 'value': str(param[1])}
                for i, param in enumerate(other)]

        comp_table = ui.table(columns=columns,
                              rows=rows,
                              title='Undefined Properties',
                              row_key='id').classes('w-full bordered')

        comp_table.add_slot('body', r'''
                            <q-tr :props="props">
                                <q-td v-for="col in props.cols" :key="col.name" :props="props">
                                    {{ col.value }}
                                </q-td>
                                <q-td auto-width>
                                    <q-btn size="sm" color="blue" round dense
                                           @click="$parent.$emit('edit_val', props)"
                                           icon="edit" />
                                </q-td>
                            </q-tr>
                        ''')
        comp_table.on('edit_val', self.edit_val)

    def edit_val(self, e: events.GenericEventArguments):

        content = next((content for content in self.component._taxonomy_map.content
                        if content.property_name == e.args['row'].get('name')), None)
        val = self.component[content.property_name]

        # val = getattr(self.component, content.property_name)
        edit_dialog = ContentEditDialog(component=val,
                                        parent=self,
                                        content=content,
                                        raw_val=self.component.get_raw_attr(content.property_name))
        edit_dialog.create_edit_dialog()

    def get_cb_instance(self, e: events.GenericEventArguments):
        key = e.args['row'].get('name')
        instance = self.component.get(key, None)
        if isinstance(instance, (ndarray, )):
            return self.component.get_raw_attr(key).ValueSource.Field
        elif isinstance(instance, DataFrame):
            return self.component.get_raw_attr(key).ValueSource.Table
        else:
            return instance

    def show_detail(self, e: events.GenericEventArguments):
        from ..detail_views import show_detail
        instance = self.get_cb_instance(e)
        show_detail(value=instance)

    def add_new_item(self, event):

        parent = self

        component = self.component
        edit_dialog = DictEditDialog(component=None,
                                     key=None,
                                     parent=self,
                                     options=['Component'])

        def save(self, *args, **kwargs):

            edit_diag = edit_dialog.edit_dialog.edit_dialog

            value = edit_diag.value
            key = edit_dialog.key
            component[key] = value

            if isinstance(value, (int, float)):
                raw_val = component.get_raw_attr(key)
                setattr(raw_val, 'ValueMin', edit_diag.min)
                setattr(raw_val, 'ValueMax', edit_diag.max)
                setattr(raw_val, 'Unit', edit_diag.unit)

            parent.ui_content.refresh()
            edit_dialog.close()

        edit_dialog.save = save
        edit_dialog.create_edit_dialog()


class ComponentDictView(TypeView):

    detail_view = DictDetailView

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def view_manager(self):
        return self.parent.view_manager

    @ui.refreshable
    def ui_content(self):
        from ..detail_views import show_detail

        with ui.card().classes(f"{self.colors['item']} w-full") as self.card:
            self.card.on('click', lambda e: show_detail(self.component,
                                                        parent=self.parent)
                         )
            with ui.row().classes(f"{self.colors['item']} w-full") as self.row:
                self.row.on('click', lambda e: show_detail(self.component,
                                                           parent=self.parent)
                            )
                self.checkbox = ui.checkbox(on_change=self.select)
                ui.input(label='Name', value=self.component.name).bind_value(self.component, 'name')
                ui.label(f'{str(self.component.id)}')

    def add_new_item(self, event):

        parent = self

        component = self.component
        edit_dialog = DictEditDialog(component=None,
                                     key=None,
                                     parent=self,
                                     options=['Component'])

        def save(self, *args, **kwargs):

            edit_diag = edit_dialog.edit_dialog.edit_dialog

            value = edit_diag.value
            key = edit_dialog.key
            component[key] = value

            if value in [int, float]:
                raw_val = component[key]
                setattr(raw_val, 'ValueMin', edit_diag.min)
                setattr(raw_val, 'ValueMax', edit_diag.max)
                setattr(raw_val, 'Unit', edit_diag.unit)

            parent.content_view.ui_content.refresh()
            edit_dialog.close()

        edit_dialog.save = save
        edit_dialog.create_edit_dialog()
