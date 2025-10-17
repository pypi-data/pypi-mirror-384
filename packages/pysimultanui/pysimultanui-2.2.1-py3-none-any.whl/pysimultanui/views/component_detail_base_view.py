from nicegui import ui, events, app
from functools import partial
# from .detail_views import show_detail
# import pdb

from .. import user_manager
from ..core.geo_associations import GeoEditDialog
from ..core.method_mapper import MethodMapper, methods_content

from PySimultan2.simultan_object import SimultanObject


class ComponentDetailBaseView(object):

    def __init__(self, *args, **kwargs):
        self.component: SimultanObject = kwargs.get('component')
        self.parent = kwargs.get('parent')
        self.card = None
        self.row = None

        self.table = None
        self.association_table = None

    @property
    def user(self):
        return user_manager[app.storage.user['username']]

    @ui.refreshable
    def ui_content(self, *args, **kwargs):

        if kwargs.get('plain', False):
            return

        def content():

            with ui.row().classes('w-full'):
                c_name_input = ui.input(label='Name', value=self.component.name)
                c_name_input.bind_value(self.component, 'name').classes('w-full').style('font-size: 1.25em;')
                with c_name_input.add_slot('append'):
                    with ui.element('q-fab').props('icon=menu_open color=blue width=20 direction=down').classes('q-ml-auto'):
                        with ui.element('q-fab-action').props(
                                'icon="file_copy" color="blue" label="" external-label="True" label-position="bottom"'
                        ).on('click', self.create_copy):
                            ui.tooltip('Create a copy of this component')

                        with ui.element('q-fab-action').props(
                                'icon="delete" color="red" label="" external-label="True" label-position="bottom"'
                        ).on('click', self.delete_component):
                            ui.tooltip('Delete this component')

                        from .detail_views import show_detail
                        with ui.element('q-fab-action').props(
                                'icon="update" color="blue" label="" external-label="True" label-position="bottom"'
                        ).on('click', lambda x: show_detail(self.component)):
                            ui.tooltip('Refresh this component')

                # with c_name_input.add_slot('append'):
                #     with ui.button(icon='file_copy', on_click=self.create_copy):
                #         ui.tooltip('Create a copy of this component')
                #     with ui.button(icon='delete', on_click=self.delete_component) as delete_button:
                #         ui.tooltip('Delete this component')
                #         delete_button.props('color=red-5')

            with ui.row():
                ui.label('Global ID: ')
                ui.label(f'{self.component.id.GlobalId.ToString()}')
                ui.label('Local ID: ')
                ui.label(f'{self.component.id.LocalId}')

            self.ui_content_taxonomies()
            self.ui_content_associate_geometry()

        if hasattr(self.component, 'image_path'):
            with ui.list().classes('w-full'):
                with ui.item():
                    with ui.item_section().classes('w-1/6'):
                        ui.image(self.component.image_path).props('fit=scale-down').style(
                            f'width: {kwargs.get("image_width", 200)}px; height: {kwargs.get("image_height", 200)}px;')
                    with ui.item_section().classes('w-5/6'):
                        content()
        else:
            content()

        # with ui.card().classes('w-full h-full'):

    def ui_content_associate_geometry(self):
        with ui.expansion(icon='format_list_bulleted',
                          text=f'Associated Geometry').classes('w-full') as exp:

            columns = [{'name': 'id', 'label': 'ID', 'field': 'id', 'sortable': True},
                       {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True},
                       {'name': 'type', 'label': 'Type', 'field': 'type', 'sortable': True},
                       {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'sortable': False}]

            rows = [{'id': x.id,
                     'name': x.name,
                     'type': x.__class__.__name__}
                    for x in self.component.associated_geometry]

            self.association_table = ui.table(columns=columns,
                                              rows=rows,
                                              title='Associated Geometry',
                                              pagination={'rowsPerPage': 5, 'sortBy': 'id', 'page': 1},
                                              row_key='id').classes('w-full h-full bordered')

            self.association_table.add_slot('body-cell-actions', r'''
                                                        <q-td key="actions" :props="props">
                                                            <q-btn size="sm" color="blue" round dense
                                                                @click="$parent.$emit('show_detail', props)"
                                                                icon="launch" />
                                                            <q-btn size="sm" color="negative" round dense
                                                                @click="$parent.$emit('delete_association', props)"
                                                                icon="delete" />
                                                        </q-td>
                                                    ''')

            self.association_table.on('show_detail', self.show_geo_detail)
            self.association_table.on('delete_association', self.delete_association)

            with ui.button(icon='add', on_click=self.edit_association):
                ui.tooltip('Add a new association to this component')

    def ui_content_taxonomies(self):

        def add_taxonomy():
            ui.notify('Add taxonomy not implemented yet')

        row = ui.row().classes('w-full')
        with row:
            ui.label('Taxonomies:')
            for taxonomy in self.component.taxonomy_keys:
                ui.chip(taxonomy).classes('m-1')
            with ui.button(icon='add', on_click=add_taxonomy).props('round dense flat justify=end items=center'):
                ui.tooltip('Add a new taxonomy entry to this component')

    def methods_ui_content(self):

        methods_button = methods_content(user=self.user,
                                         component=self.component,
                                         method_type='mapped',
                                         label='Methods',
                                         )

        # with ui.element('q-fab').props('icon=menu_open color=blue') as methods_button:
        #     user = self.user
        #     methods = user.method_mapper.mapped_methods.get_inherited_mapped_methods(self.component.__class__)
        #     for method in methods:
        #         method_run_fcn = partial(method.run, selected_instances=[self.component])
        #         with ui.element('q-fab-action').props(
        #                 f'icon="{method.icon}" color="{method.color}" label="{method.name}" direction="down" external-label="True" label-position="bottom"'
        #         ).on('click', method_run_fcn):
        #             ui.tooltip(method.description)
        return methods_button

    def refresh(self):
        self.ui_content.refresh()

    def show_geo_detail(self, e: events.GenericEventArguments):
        from .detail_views import show_detail
        instance = next((x for x in self.component.associated_geometry if x.id == e.args['row'].get('id')), None)._geometry_model
        show_detail(value=instance)

    def edit_association(self):
        edit_dialog = GeoEditDialog(component=self.component,
                                    parent=self)
        edit_dialog.create_edit_dialog()

    def delete_association(self, e: events.GenericEventArguments):
        instance = next((x for x in self.component.associated_geometry if x.id == e.args['row'].get('id')), None)
        instance.disassociate(self.component)
        ui.notify(f'Removed associated {instance.name} from {self.component.name}')
        self.ui_content.refresh()

    def create_copy(self, e: events.GenericEventArguments):
        new_instance = self.component.copy()
        self.user.project_manager.mapped_data.append(new_instance)
        self.user.grid_view.add_item_to_view(new_instance)
        ui.notify(f'Created copy {new_instance.name} {new_instance.id} of {self.component.name}, {self.component.id}')

    async def delete_component(self, e: events.GenericEventArguments):

        with ui.dialog() as dialog, ui.card():
            ui.label(f'Are you sure you want to delete {self.component.name} {self.component.id}?')
            with ui.row():
                with ui.button(on_click=lambda: dialog.submit({'ok': True})):
                    ui.label('Yes')
                with ui.button(on_click=lambda: dialog.submit({'ok': False})):
                    ui.label('No')
        result = await dialog

        if not result.get('ok', False):
            return

        self.component.remove_from_datamodel()
        ui.notify(f'Deleted {self.component.name} {self.component.id}')
