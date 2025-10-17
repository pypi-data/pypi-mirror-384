import sys
import json
import asyncio
import inspect
import traceback
from nicegui import events, ui, app

from typing import Optional, Any
from .. import user_manager
from .detail_views import show_detail

from SIMULTAN.Data import SimId
from SIMULTAN.Data.Components import SimComponent
from PySimultan2 import DataModel
from PySimultan2.default_types import ComponentList, ComponentDictionary
from PySimultan2.object_mapper import SimultanObject
from ..core.method_mapper import ArgumentDialog
from System import Guid


class ComponentTree:

    def __init__(self,
                 data_model: DataModel,
                 parent: Any,
                 components: tuple[SimultanObject],
                 *args,
                 **kwargs):

        self.tree = None

        self._data_model = data_model
        self.components = components
        self.parent = parent
        self.instance_lookup = {}
        self.tree_data = {}

    @ui.refreshable
    def ui_content(self):
        tree_content = self.generate_tree_content()

        with ui.row().classes('w-full'):
            tree_filter = ui.input(label='Filter', placeholder='Filter...')
            with ui.button('+ all') as expand_button:
                ui.tooltip('Expand all')
            with ui.button('- all') as collapse_button:
                ui.tooltip('Collapse all')

        self.tree = ui.tree(tree_content,
                            label_key='name',
                            tick_strategy='strict',
                            on_select=lambda e: self.show_detail(e)
                            )
        self.tree.classes('w-full h-full')
        tree_filter.bind_value_to(self.tree, 'filter')

        self.tree.add_slot('default-header', r'''
            <div style="display: grid; grid-template-columns: 1fr 3fr 50px 1fr; gap: 20px;">
                <span v-if="props.node.content_name" :props="props" style="color: blue;">{{ props.node.content_name }}</span>
                <span :props="props"><strong>{{ props.node.name }}</strong></span>
                <span :props="props">{{ props.node.id }}</span>
                <span :props="props">{{ props.node.taxonomy }}</span>
            </div>
        ''')

        expand_button.on('click', self.tree.expand)
        collapse_button.on('click', self.tree.collapse)

        return self.tree

    def generate_tree_content(self):

        self.instance_lookup = {}
        tree_content = []

        def create_component_tree(component):

            # if hasattr(component, 'id'):
            #     if int(component.id.LocalId) in self.instance_lookup.keys():
            #         return [{'name': 'Content not shown...'}]

            component_tree_content = []

            if isinstance(component, ComponentDictionary):
                for key, sub_component in component.items():
                    if not isinstance(sub_component, SimultanObject):
                        continue
                    try:
                        if hasattr(sub_component, 'id'):
                            if int(sub_component.id.LocalId) in self.instance_lookup.keys():
                                list_children = [{'name': 'Content not shown...'}]
                            else:
                                self.instance_lookup[int(sub_component.id.LocalId)] = sub_component
                                list_children = create_component_tree(sub_component)
                        else:
                            self.instance_lookup[int(sub_component.id.LocalId)] = sub_component
                            list_children = create_component_tree(sub_component)
                    except Exception as e:
                        list_children = [{'name': 'Content not shown...'}]

                    self.instance_lookup[int(sub_component.id.LocalId)] = sub_component
                    component_tree_content.append({'id': str(sub_component.id.LocalId),
                                                   'name': sub_component.name,
                                                   'taxonomy': sub_component._taxonomy,
                                                   'children': list_children,
                                                   'content_name': sub_component.name})

            elif isinstance(component, ComponentList):
                for i, sub_component in enumerate(component):
                    try:
                        if hasattr(sub_component, 'id'):
                            if int(sub_component.id.LocalId) in self.instance_lookup.keys():
                                list_children = [{'name': 'Content not shown...'}]
                            else:
                                self.instance_lookup[int(sub_component.id.LocalId)] = sub_component
                                list_children = create_component_tree(sub_component)
                        else:
                            self.instance_lookup[int(sub_component.id.LocalId)] = sub_component
                            list_children = create_component_tree(sub_component)
                    except Exception as e:
                        list_children = [{'name': 'Content not shown...'}]

                    self.instance_lookup[int(sub_component.id.LocalId)] = sub_component
                    component_tree_content.append({'id': str(sub_component.id.LocalId),
                                                   'name': sub_component.name,
                                                   'taxonomy': sub_component._taxonomy,
                                                   'children': list_children,
                                                   'content_name': str(i)})


            for content in component._taxonomy_map.content:

                if not hasattr(component, content.property_name):
                    continue
                else:
                    content_val = getattr(component, content.property_name)

                if isinstance(content_val, SimultanObject):

                    if content_val.id.LocalId in self.instance_lookup.keys():
                        children = [{'name': 'Content not shown...'}]
                    else:
                        self.instance_lookup[int(content_val.id.LocalId)] = content_val
                        children = create_component_tree(content_val)
                    self.instance_lookup[int(content_val.id.LocalId)] = content_val
                    component_tree_content.append({'id': str(content_val.id.LocalId),
                                                   'name': content_val.name,
                                                   'taxonomy': content_val._taxonomy,
                                                   'children': children,
                                                   'content_name': content.name})
                else:
                    continue

            return component_tree_content

        for component in self.components:
            try:
            # self.instance_lookup[int(component.id.LocalId)] = component
                tree_content.append({'id': str(component.id.LocalId),
                                     'name': component.name,
                                     'taxonomy': component._taxonomy,
                                     'children': create_component_tree(component),
                                     'content_name': None
                                     }
                                    )
                self.instance_lookup[int(component.id.LocalId)] = component
            except Exception as e:
                print(f'Error creating tree content: {e}')
                self.parent.user.logger.error(f'Error creating tree content: {e}')
                tree_content.append({'id': str(component.id.LocalId),
                                     'name': component.name,
                                     'taxonomy': component._taxonomy,
                                     'children': create_component_tree(component),
                                     'content_name': None
                                     }
                                    )

        return tree_content

    def show_detail(self, e):
        if e.value is None:
            return
        component_local_id = int(e.value)
        instance = self.instance_lookup.get(component_local_id, None)
        if instance is None:
            return
        show_detail(value=instance)

    @property
    def selected_instances(self) -> list[SimultanObject]:
        return [self.instance_lookup[int(x)] for x in self.tree.props['ticked']]


class GridView(object):

    columns = [
        {'headerName': 'Name',
         'field': 'name',
         'editable': True,
         'sortable': True,
         'filter': 'agTextColumnFilter',
         'floatingFilter': True,
         'checkboxSelection': True},
        {'headerName': 'ID',
         'field': 'id',
         'editable': False,
         'sortable': True,
         'filter': 'agTextColumnFilter',
         'floatingFilter': True},
        {'headerName': 'Mapped Class',
         'field': 'taxonomy',
         'editable': False,
         'sortable': True,
         'filter': 'agTextColumnFilter',
         'floatingFilter': True},
    ]

    def __init__(self, *args, **kwargs):

        self._data_model = None
        self.table: Optional[ui.aggrid] = None
        self.tree: Optional[ComponentTree] = None

        self.create_type_select: Optional[ui.select] = None
        self.create_type: Optional[str] = None             # type of object to create

        self.show_as_tree: bool = True

    @property
    async def selected_instances(self) -> list[SimultanObject]:
        if self.show_as_tree:
            if self.tree is None:
                return []
            else:
                await asyncio.sleep(0)
                return self.tree.selected_instances
        else:
            rows = await self.table.get_selected_rows()
            return [
                self.mapper.get_mapped_class(row['taxonomy'])._cls_instances_dict.get(SimId(Guid(row['id'].split('_')[0]),
                                                                                            int(row['id'].split('_')[1])),
                                                                                      None) for row in rows]

    @property
    def data_model(self):
        return self._data_model

    @data_model.setter
    def data_model(self, value):
        self._data_model = value
        self.ui_content.refresh()

    @property
    def mapper(self):
        return self.user.mapper

    @property
    def user(self):
        return user_manager[app.storage.user['username']]

    @property
    def items(self) -> list[dict[str: str,
                                 str: str,
                                 str: str]]:
        items = []

        for taxonomy, cls in self.mapper.registered_classes.items():
            mapped_cls = self.mapper.get_mapped_class(taxonomy)
            if hasattr(mapped_cls, 'cls_instances'):
                for instance in mapped_cls.cls_instances:
                    items.append({'name': instance.name,
                                  'id': f'{instance.id.GlobalId}_{instance.id.LocalId}',
                                  'taxonomy': taxonomy})

        return items

    @ui.refreshable
    def ui_content(self):

        if self.show_as_tree:
            with ui.row().classes('w-full gap-0'):
                with ui.column().classes('w-1/3 gap-0'):
                    self.ui_create_new_content()
                with ui.column().classes('w-1/2 gap-0'):
                    self.user.method_mapper.ui_content()

                ui.space()

                with ui.button(on_click=self.user.project_manager.refresh_all_items,
                               icon='update').props('fab color=accent').classes('h-3 justify=end items=center'):
                    ui.tooltip('Update data')

            self.ui_content_tree()
        else:
            self.table = ui.aggrid({
                'columnDefs': self.columns,
                'rowData': self.items,
                'auto_size_columns': True,
                'rowSelection': 'multiple',
                'pagination': True,
                'paginationPageSize': 25,
                'paginationPageSizeSelector': [10, 25, 50, 100, 150, 200],
                'enableFilter': True,
            },
                auto_size_columns=True).on('cellClicked', lambda e: self.show_detail(e))

            self.table.classes('w-full h-full')

            with ui.row().classes('w-full gap-0'):
                with ui.column().classes('w-1/3 gap-0'):
                    self.ui_create_new_content()
                with ui.column().classes('w-1/2 gap-0'):
                    self.user.method_mapper.ui_content()

                ui.space()

                with ui.button(on_click=self.user.project_manager.refresh_all_items,
                               icon='update').props('fab color=accent').classes('h-3 justify=end items=center'):
                    ui.tooltip('Update data')

    @ui.refreshable
    def ui_content_tree(self):
        if self.data_model is None:
            components = []
        else:
            components = self.mapper.get_typed_data(component_list=tuple(self.data_model.data.Items),
                                                    data_model=self.data_model,
                                                    create_all=False)
        self.tree = ComponentTree(components=components,
                             parent=self,
                             data_model=self.data_model)
        self.tree.ui_content()

    def ui_create_new_content(self):

        with ui.expansion(icon='add',
                          text='Create new').classes('w-full') as exp:

            with ui.column().classes('w-full'):

                if not self.user.mapper.mapped_classes:
                    _ = [self.user.mapper.get_mapped_class(x) for x in self.user.mapper.registered_classes.keys()]

                options = [taxonomy for taxonomy in self.user.mapper.mapped_classes.keys()
                           if taxonomy not in self.user.mapper.undefined_registered_classes.keys()]

                self.create_type_select = ui.select(options=options,
                                                    value=options[0]
                                                    if self.user.mapper.mapped_classes.keys() else None,
                                                    with_input=True,
                                                    label='Mapped Class').bind_value(self,
                                                                                     'create_type'
                                                                                     ).classes('w-full')
                with self.create_type_select.add_slot('append'):
                    with ui.button(icon='play_circle', on_click=self.create_new_item
                                   ).classes('h-5 justify=end items=center'):
                        ui.tooltip('Create')

    async def create_new_item(self, e):

        try:

            if None in (self.data_model, self.create_type):
                ui.notify('No data model selected! Please load a data model first.')
                return

            cls = self.user.mapper.get_mapped_class(self.create_type)
            if cls is None:
                ui.notify(f'Could not find class for taxonomy {self.create_type}.')
                return
            try:
                init_fcn = cls.__bases__[-1].__init__

                parameters = dict(inspect.signature(init_fcn).parameters)
                if set(parameters.keys()) - {'args', 'kwargs', 'self'}:
                    res = await ArgumentDialog(name='Start API',
                                               description='Start API',
                                               mapper=self.mapper,
                                               fnc=init_fcn)
                else:
                    res = {'ok': True, 'args': {}}

                if not res['ok']:
                    return
            except Exception as e:
                error = '\n'.join(traceback.format_exception(*sys.exc_info()))
                ui.notify(f'Error getting arguments for method: {e}\n {error}')
                self.user.logger.error(f'Error getting arguments for method: {e}\n {error}')
                return

            try:
                new_item: SimultanObject = cls(data_model=self.data_model,
                                               object_mapper=self.mapper,
                                               **res['args']
                                               )
                new_item.name = f'New {cls.__name__}_{new_item.id}'
            except Exception as e:
                error = '\n'.join(traceback.format_exception(*sys.exc_info()))
                ui.notify(f'Error creating new item: {e}\n {error}')
                self.user.logger.error(f'Error creating new item: {e}\n {error}')
                return

            self.user.logger.info(f'Created new {cls.__name__}, ID {new_item.id}.')

            self.user.project_manager.mapped_data.append(new_item)

            self.data_model.save()
            self.add_item_to_view(new_item)
            self.mapper.get_mapped_class(self.create_type)._cls_instances_dict.get(new_item.id, None)

            show_detail(value=new_item)
            ui.notify(f'Created new {cls.__name__}, ID {new_item.id}.')
        except Exception as e:
            err = '\n'.join(traceback.format_exception(*sys.exc_info()))
            ui.notify(f'Error creating new item: {e}')
            self.user.logger.error(f'Error creating new item: {e}:\n{err}')

    def selected_rows(self):
        rows = self.table.get_selected_rows()
        if rows:
            for row in rows:
                ui.notify(f"{row['name']}, {row['age']}")
        else:
            ui.notify('No rows selected.')

    def show_detail(self, e):

        component_id = e.args['data']['id']
        sim_id = SimId(Guid(component_id.split('_')[0]), int(component_id.split('_')[1]))
        instance = self.mapper.get_mapped_class(e.args['data']['taxonomy'])._cls_instances_dict.get(sim_id, None)
        if instance is None:
            return
        show_detail(value=instance)

    def add_item_to_view(self, component: SimultanObject):
        self.ui_content.refresh()
