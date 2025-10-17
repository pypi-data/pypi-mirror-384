from nicegui import ui, events, app
from functools import partial
from typing import Optional, Union, Any
from numpy import ndarray
from pandas import DataFrame

from ..type_view import TypeView

from SIMULTAN.Data.Components import (SimEnumParameter, SimIntegerParameter, SimStringParameter, SimDoubleParameter)

from ... import user_manager
from ...core.geo_associations import GeoEditDialog
from ...core.edit_dialog import ContentEditDialog

from ..component_detail_base_view import ComponentDetailBaseView
from ...core.method_mapper import methods_content

from PySimultan2.simultan_object import SimultanObject
from PySimultan2.files import FileInfo
from PySimultan2.taxonomy_maps import Content
from PySimultan2.geometry import GeometryModel


from ..parameter_view import ParameterView


class ContentItemView(object):
    def __init__(self, *args, **kwargs):
        self.component: SimultanObject = kwargs.get('component')
        self.parent = kwargs.get('parent')
        self.content = kwargs.get('content')

    @property
    def view_manager(self):
        return self.parent.view_manager

    @ui.refreshable
    def ui_content(self):
        with ui.item().classes('w-full h-full'):

            with ui.item_section():
                ui.label(f'{self.content.name}:')

            val = getattr(self.component, self.content.property_name)
            if isinstance(val, SimultanObject):
                ui_simultan_object_ref(val, self)
            elif isinstance(val, (int, float, str)):
                with ui.item_section():
                    raw_val = self.component.get_raw_attr(self.content.property_name)
                    ParameterView(component=val,
                                  raw_val=raw_val,
                                  content=self.content,
                                  parent=self.parent,
                                  taxonomy=self.content).ui_content()

            elif isinstance(val, (ndarray, DataFrame)):
                ui_ndarray_ref(val, self)
            else:
                if val is None:
                    with ui.item_section():
                        ui.label('None')
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
                with ui.item_section():
                    button = ui.button(on_click=self.edit,
                                       icon='edit').classes('q-ml-auto')
                    button.item = val
                    button.content = self.content

    def edit(self, event):
        edit_dialog = ContentEditDialog(component=event.sender.item,
                                        parent=self.parent,
                                        content=event.sender.content)
        edit_dialog.create_edit_dialog()


def ui_simultan_object_ref(val: SimultanObject,
                           parent: ContentItemView):
    from ..detail_views import show_detail

    # show_detail(val)

    # if not hasattr(val, '__ui_element__') or val.__ui_element__ is None:
    #
    #     view_manager = user_manager[app.storage.user['username']].project_manager.view_manager
    #     cls_view = view_manager.cls_views.get(val.__class__, None)[
    #         'item_view_manager'] if view_manager.cls_views.get(val.__class__,
    #                                                            None) is not None else None
    #     if cls_view is None:
    #         cls_view: TypeViewManager = view_manager.create_mapped_cls_view_manager(taxonomy=val.__class__._taxonomy)[
    #             'item_view_manager']
    #         if cls_view is None:
    #             ui.label(f'No View for this class: {val.__class__}')
    #             return
    #     try:
    #         cls_view.add_item_to_view(val)
    #     except KeyError:
    #         with ui.item_section():
    #             ui.label(f'No View for this class: {val.__class__}')
    # if val.__ui_element__ is None:
    #     ui.label(f'No View for this object: {str(val), val.__class__}')
    #     return

    if hasattr(val, 'image_path'):
        with ui.item_section():
            ui.image(val.image_path).classes('w-12 h-12')

    with ui.item_section():
        ui.item_label(val.name)
    with ui.item_section():
        with ui.item():
            with ui.item_section():
                ui.item_label(f'{val.id.GlobalId.ToString()}')
            with ui.item_section():
                ui.item_label(f'{val.id.LocalId}')
    with ui.item_section():
        with ui.element('q-fab').props('icon=menu_open color=blue width=20 direction=left').classes(
                'q-ml-auto'):
            with ui.element('q-fab-action').props(
                    'icon="launch" color="blue" label="" external-label="True" label-position="bottom"'
            ).on('click', lambda e: show_detail(value=val,
                                                 parent=parent)):
                ui.tooltip('Show details')

            with ui.element('q-fab-action').props(
                    'icon="edit" color="blue" label="" external-label="True" label-position="bottom"'
            ).on('click', parent.edit) as btn:
                ui.tooltip('Edit')
                btn.item = val
                btn.content = parent.content


def ui_ndarray_ref(val: (ndarray, DataFrame),
                   parent: ContentItemView):
    from ..detail_views import show_detail

    raw_val = parent.component.get_raw_attr(parent.content.property_name)
    # view_manager = user_manager[app.storage.user['username']].project_manager.view_manager
    #
    # def get_ui_element():
    #     ui_element = view_manager.cls_views[val.__class__]['item_view_manager'].item_views.get(
    #         str(raw_val.ValueSource.ValueField.Id), None)
    #     return ui_element
    #
    # ui_element = get_ui_element()
    #
    # if ui_element is None:
    #     view_manager.cls_views[val.__class__]['item_view_manager'].add_item_to_view(val, raw_val)
    # ui_element = get_ui_element()

    with ui.item_section():

        ui.label(raw_val.ValueSource.ValueField.Name)
        ui.button(on_click=lambda e: show_detail(value=val,
                                                 parent=parent),
                  icon='launch').classes('q-ml-auto')
    with ui.item_section():
        ui.label(f'{raw_val.ValueSource.ValueField.Id}')
    with ui.item_section():
        edit_btn = ui.button(on_click=parent.edit, icon='edit').classes('q-ml-auto')
        edit_btn.item = val
        edit_btn.content = parent.content


class ContentView(object):

    def __init__(self, *args, **kwargs):
        self.component: SimultanObject = kwargs.get('component')
        self.parent = kwargs.get('parent')
        self.card = None
        self.row = None

    @property
    def parameters(self) -> tuple[list[tuple[Content,
    Union[int, float, str],
    Union[SimIntegerParameter,
    SimStringParameter,
    SimEnumParameter,
    SimDoubleParameter]
                                       ],
                                  list[tuple[Content, SimultanObject]],
                                  list[tuple[Content, Union[ndarray, DataFrame]]],
                                  list[tuple[Content, FileInfo]],
                                  list[tuple[Content, Any]],
                                  list[tuple[Content, GeometryModel]]:,
                                  ]
    ]:

        parameters = []
        components = []
        arrays = []
        assets = []
        undefined = []
        other = []
        geometry = []

        for content in self.component._taxonomy_map.content:
            val = getattr(self.component, content.property_name)
            if isinstance(val, SimultanObject):
                components.append((content, val))
            elif isinstance(val, (int, float, str)):
                raw_val = self.component.get_raw_attr(content.property_name)
                parameters.append((content, val, raw_val))
            elif isinstance(val, (ndarray, DataFrame)):
                arrays.append((content, val))
            elif isinstance(val, FileInfo):
                assets.append((content, val))
            elif val is None:
                undefined.append((content, val))
            else:
                other.append((content, val))

        return parameters, components, arrays, assets, other, geometry, undefined

    @property
    def view_manager(self):
        return self.parent.view_manager

    @ui.refreshable
    def ui_content(self,
                   add_methods_button: bool = True,
                   add_referenced_by_content: bool = True):

        parameters, components, arrays, assets, other, geometry, undefined = self.parameters
        # self.ui_methods_content()

        if add_methods_button:
            self.ui_methods_button_content()

        self.ui_param_table(parameters)
        self.ui_component_table(components)
        self.ui_array_table(arrays)
        self.ui_assets_table(assets)
        self.ui_undefined_table(undefined)

        if add_referenced_by_content:
            self.ui_referenced_by_content()

        self.ui_parent_content()

    def ui_assets_table(self, assets):

        columns = [{'name': 'id', 'label': 'ID', 'field': 'id', 'sortable': True},
                   {'name': 'index', 'label': 'Index', 'field': 'index', 'sortable': True},
                   {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True},
                   {'name': 'path', 'label': 'Path', 'field': 'path', 'sortable': True}]

        rows = [{'index': i,
                 'id': asset[1].key,
                 'name': asset[0].name,
                 'path': asset[1].name}
                for i, asset in enumerate(assets)]

        asset_table = ui.table(columns=columns,
                               rows=rows,
                               title='Assets',
                               row_key='id').classes('w-full bordered text-sm')

        asset_table.add_slot('body', r'''
            <q-tr :props="props">
                <q-td v-for="col in props.cols" :key="col.name" :props="props">
                    {{ col.value }}
                </q-td>
                <q-td auto-width>
                    <q-btn size="sm" color="blue" round dense
                           @click="$parent.$emit('edit_val', props)"
                           icon="edit" />
                    <q-btn size="sm" color="blue" round dense
                           @click="$parent.$emit('show_detail', props)"
                           icon="launch" />
                </q-td>
            </q-tr>
        ''')
        asset_table.on('edit_val', self.edit_val)
        asset_table.on('show_detail', self.show_asset_detail)

    def ui_undefined_table(self, other):

        columns = [{'name': 'id', 'label': 'ID', 'field': 'id', 'sortable': True},
                   {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True},
                   {'name': 'value', 'label': 'Value', 'field': 'value', 'sortable': True}]

        rows = [{'id': i,
                 'name': param[0].name,
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

    def ui_param_table(self, parameters):
        # create int/float/str table
        columns = [{'name': 'id', 'label': 'ID', 'field': 'id', 'sortable': True},
                   {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True},
                   {'name': 'value', 'label': 'Value', 'field': 'value', 'sortable': True},
                   {'name': 'min', 'label': 'Min', 'field': 'min', 'sortable': True},
                   {'name': 'max', 'label': 'Max', 'field': 'max', 'sortable': True},
                   {'name': 'unit', 'label': 'Unit', 'field': 'unit', 'sortable': True},
                   {'name': 'description', 'label': 'Description', 'field': 'description', 'sortable': False}]

        rows = [{'id': i,
                 'name': param[0].name,
                 'value': str(param[2].Value),
                 'min': str(param[2].ValueMin) if hasattr(param[2], 'ValueMin') else '',
                 'max': str(param[2].ValueMax) if hasattr(param[2], 'ValueMax') else '',
                 'unit': param[2].Unit if hasattr(param[2], 'Unit') else '',
                 'description': param[2].Description if hasattr(param[2], 'Description') else ''}
                for i, param in enumerate(parameters)]

        param_table = ui.table(columns=columns,
                               rows=rows,
                               title='Parameters',
                               row_key='id').classes('w-full bordered text-sm')

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
                   {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True},
                   {'name': 'component_id', 'label': 'Component ID', 'field': 'component_id', 'sortable': True},
                   {'name': 'component_name', 'label': 'Component Name', 'field': 'component_name', 'sortable': True},
                   {'name': 'component_type', 'label': 'Component Type', 'field': 'component_type', 'sortable': True},
                   {'name': 'type', 'label': 'Type', 'field': 'type', 'sortable': True},
                   ]

        rows = [{'id': str(i),
                 'component_id': str(comp[1].id),
                 'name': comp[0].name,
                 'component_name': comp[1].name,
                 'component_type': comp[1].__class__.__name__,
                 'type': 'Subcomponent' if comp[1]._wrapped_obj in
                                           [y.Component for y in self.component._wrapped_obj.Components]
                 else 'Reference'}
                for i, comp in enumerate(components)]

        comp_table = ui.table(columns=columns,
                              rows=rows,
                              title='Components',
                              row_key='id').classes('w-full bordered text-sm')

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
                   {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True},
                   {'name': 'type', 'label': 'Type', 'field': 'type', 'sortable': True}]

        rows = [{'id': str(i),
                 'name': str(comp[0].name),
                 'type': 'ND Array' if isinstance(comp[1], ndarray) else 'Table'} for i, comp in enumerate(arrays)]

        comp_table = ui.table(columns=columns,
                              rows=rows,
                              title='Arrays',
                              row_key='id').classes('w-full bordered text-sm')

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

    def ui_referenced_by_content(self):

        columns = [{'name': 'id', 'label': 'ID', 'field': 'id', 'sortable': True},
                   {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True},
                   {'name': 'component_id', 'label': 'Component ID', 'field': 'component_id', 'sortable': True},
                   {'name': 'component_name', 'label': 'Component Name', 'field': 'component_name', 'sortable': True},
                   {'name': 'component_type', 'label': 'Component Type', 'field': 'component_type', 'sortable': True},
                   ]

        rows = [{'id': str(i),
                 'component_id': str(comp.id),
                 'name': comp.name,
                 'component_name': comp.name,
                 'component_type': comp.__class__.__name__}
                for i, comp in enumerate(self.component.referenced_by)]

        comp_table = ui.table(columns=columns,
                              rows=rows,
                              title='Referenced by',
                              row_key='id').classes('w-full bordered text-sm')

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

    def ui_parent_content(self):

        columns = [{'name': 'id', 'label': 'ID', 'field': 'id', 'sortable': True},
                   {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True},
                   {'name': 'component_id', 'label': 'Component ID', 'field': 'component_id', 'sortable': True},
                   {'name': 'component_name', 'label': 'Component Name', 'field': 'component_name', 'sortable': True},
                   {'name': 'component_type', 'label': 'Component Type', 'field': 'component_type', 'sortable': True},
                   ]

        if self.component.parent:
            rows = [{'id': str(i),
                     'component_id': str(comp.id),
                     'name': comp.name,
                     'component_name': comp.name,
                     'component_type': comp.__class__.__name__}
                    for i, comp in enumerate([self.component.parent])]
        else:
            rows = []

        comp_table = ui.table(columns=columns,
                              rows=rows,
                              title='Parent:',
                              row_key='id').classes('w-full bordered text-sm')

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
        comp_table.on('detail', self.show_parent)

    def ui_methods_content(self):

        with ui.expansion('Methods',
                          icon='play_circle').classes('w-full'):

            user = self.parent.user

            cls = next((cls for cls in user.method_mapper.mapped_methods.keys() if
                        self.component.__class__.__name__ == cls.__name__), None)

            if cls is None:
                return

            columns = [{'name': 'id', 'label': 'ID', 'field': 'id', 'sortable': True},
                       {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True}]

            rows = [{'id': i,
                     'name': method.name}
                    for i, method in enumerate(user.method_mapper.mapped_methods[cls])]

            methods_table = ui.table(columns=columns,
                                     rows=rows,
                                     row_key='id').classes('w-full bordered')

            methods_table.add_slot('body', r'''
                                                <q-tr :props="props">
                                                    <q-td v-for="col in props.cols" :key="col.name" :props="props">
                                                        {{ col.value }}
                                                    </q-td>
                                                    <q-td auto-width>
                                                        <q-btn size="sm" color="blue" round dense
                                                               @click="$parent.$emit('run_method', props)"
                                                               icon="play_circle" />
                                                    </q-td>
                                                </q-tr>
                                            ''')
            methods_table.on('run_method', lambda x: user.method_mapper.run_method(x,
                                                                                   cls=cls,
                                                                                   selected_instances=[self.component])
                             )

    def ui_methods_button_content(self):

        return methods_content(user=self.parent.user,
                               component=self.component)

        # with ui.element('q-fab').props('icon=menu_open color=blue') as methods_button:
        #
        #     user = self.parent.user
        #     methods = user.method_mapper.mapped_methods.get_inherited_mapped_methods(self.component.__class__)
        #
        #     with ui.card().classes('w-400') as self.card:
        #         with ui.list():
        #             for method in methods:
        #                 with ui.item().classes('w-full'):
        #                     with ui.item_section().classes('w-full'):
        #                         ui.label(method.name)
        #                     with ui.item_section().classes('w-full'):
        #                         method_run_fcn = partial(method.run, selected_instances=[self.component])
        #                         ui.button(on_click=method_run_fcn,
        #                                   icon='play_circle').classes('q-ml-auto')
        #                     with ui.item_section().classes('w-full'):
        #                         ui.label(method.description)

            # for method in methods:
            #     method_run_fcn = partial(method.run, selected_instances=[self.component])
            #     with ui.element('q-fab-action').props(
            #             f'icon="{method.icon}" color="{method.color}" label="{method.name}" direction="down" external-label="True" label-position="bottom"'
            #     ).on('click', method_run_fcn):
            #         ui.tooltip(method.description)
        # return methods_button

    def get_cb_instance(self, e: events.GenericEventArguments):
        content = next((content for content in self.component._taxonomy_map.content
                        if content.name == e.args['row'].get('name')), None)
        instance = getattr(self.component, content.property_name)
        if isinstance(instance, (ndarray, )):
            return self.component.get_raw_attr(content.property_name).ValueSource.Field
        elif isinstance(instance, DataFrame):
            return self.component.get_raw_attr(content.property_name).ValueSource.Table
        else:
            return instance

    def edit_val(self, e: events.GenericEventArguments):

        content = next((content for content in self.component._taxonomy_map.content
                        if content.name == e.args['row'].get('name')), None)
        val = getattr(self.component, content.property_name)

        if isinstance(val, (str, int, float)):
            raw_val = self.component.get_raw_attr(content.property_name)
        else:
            raw_val = None

        edit_dialog = ContentEditDialog(component=self.component,
                                        parent=self,
                                        content=content,
                                        raw_val=raw_val)
        edit_dialog.create_edit_dialog()

    def show_asset_detail(self, e: events.GenericEventArguments):
        from ..detail_views import show_detail
        asset = getattr(self.component, e.args['row']['name'])
        show_detail(value=asset)

    def refresh(self):
        self.ui_content.refresh()

    def show_parent(self):
        from ..detail_views import show_detail
        show_detail(value=self.component.parent)

    def show_referenced_by(self, e: events.GenericEventArguments):
        from ..detail_views import show_detail
        instance = next((x for x in self.component.referenced_by if str(x.id) == e.args['row']['id']), None)
        show_detail(value=instance)

    def show_detail(self, e: events.GenericEventArguments):
        from ..detail_views import show_detail
        instance = self.get_cb_instance(e)
        show_detail(value=instance)


class MappedClsDetailView(ComponentDetailBaseView):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

    @ui.refreshable
    def ui_content(self, *args, **kwargs):
        super().ui_content(*args, **kwargs)
        content_view = ContentView(component=self.component, parent=self)
        content_view.ui_content()


class MappedClsView(TypeView):

    colors = {'item': 'bg-stone-100',
              'cls_color': 'bg-stone-300',
              'selected': 'bg-blue-200'}

    detail_view = MappedClsDetailView

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def view_manager(self):
        return self.parent.view_manager

    @ui.refreshable
    def ui_content(self):
        from ..detail_views import show_detail
        # with ui.list().classes('w-full h-full').props('bordered separator'):
        #     with ui.item(on_click=self.show_details).classes('w-full h-full') as self.card:
        #         with ui.item_section().classes('q-ml-auto'):
        #             self.checkbox = ui.checkbox().classes('q-ml-auto')
        #         with ui.item_section().classes('w-full h-full'):
        #             ui.input(label='Name', value=self.component.name).bind_value(self.component, 'name')
        #         with ui.item_section().classes('w-full h-full'):
        #             ui.label(f'{str(self.component.id)}')

        with ui.card().classes(f"{self.colors['item']} w-full h-full") as self.card:
            self.card.on('click', lambda e: show_detail(value=self.component,
                                                        parent=self)
                         )
            with ui.row().classes(f"{self.colors['item']} w-full") as self.row:
                self.row.on('click', lambda e: show_detail(value=self.component,
                                                           parent=self.component)
                            )
                self.checkbox = ui.checkbox(on_change=self.select)
                ui.input(label='Name', value=self.component.name).bind_value(self.component, 'name')
                with ui.row():
                    with ui.row():
                        ui.label('Global ID: ')
                        ui.label(f'{self.component.id.GlobalId.ToString()}')
                    with ui.row():
                        ui.label('Local ID: ')
                        ui.label(f'{self.component.id.LocalId}')

                # with ui.item_section():
                #     ui.button(on_click=self.show_details, icon='launch').classes('q-ml-auto')
            # self.content_view.ui_content()

    def show_details(self, *args, **kwargs):
        self.detail_view(component=self.component,
                         parent=self).ui_content()
