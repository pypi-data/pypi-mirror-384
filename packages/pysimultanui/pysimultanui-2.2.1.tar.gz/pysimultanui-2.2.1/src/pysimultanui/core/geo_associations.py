from nicegui import ui, app

from typing import Union, Optional
from .. import user_manager
from ..core.user import User
from PySimultan2.simultan_object import SimultanObject

from PySimultan2.geometry import (GeometryModel, SimultanEdge, SimultanFace,
                                                  SimultanVertex, SimultanVolume, SimultanEdgeLoop)


class GeoEditDialog(object):

    def __init__(self, *args, **kwargs) -> None:
        self.parent = kwargs.get('parent')
        self.component: SimultanObject = kwargs.get('component')
        self.dialog = None

        self.geo_model_select = None
        self.geo_type_select = None
        self.geo_select = None

        self.current_options = {}

    @property
    def user(self) -> User:
        return user_manager[app.storage.user['username']]

    @property
    def mapper(self):
        return self.user.mapper

    @property
    def data_model(self):
        return self.user.data_model

    @property
    def geo_models(self):
        return [GeometryModel(wrapped_object=x,
                              object_mapper=self.mapper,
                              data_model=self.data_model) for x in
                self.data_model.models.values()]

    @property
    def selected_geo_model(self):
        return next((geo_model for geo_model in self.geo_models
                     if f'{geo_model.name}; ID: {geo_model.key}' == self.geo_model_select.value),
                    None)

    @property
    def geo_options(self) -> list[any]:

        options = []

        if self.selected_geo_model is None:
            return []

        def generic_options(geo_type: str):
            return [x for x in getattr(self.selected_geo_model, geo_type)]

        def vertex_options():
            return generic_options('vertices')

        def edge_options():
            return generic_options('edges')

        def edge_loop_options():
            return generic_options('edge_loops')

        def face_options():
            return generic_options('faces')

        def volume_options():
            return generic_options('volumes')

        if self.geo_type_select.value == 'All':
            options = [*vertex_options(),
                       *edge_options(),
                       *edge_loop_options(),
                       *face_options(),
                       *volume_options()
                       ]
        elif self.geo_type_select.value == 'Vertex':
            options = vertex_options()
        elif self.geo_type_select.value == 'Edge':
            options = edge_options()
        elif self.geo_type_select.value == 'EdgeLoop':
            options = edge_loop_options()
        elif self.geo_type_select.value == 'Face':
            options = face_options()
        elif self.geo_type_select.value == 'Volume':
            options = volume_options()
        else:
            options = []

        self.current_options = {x.id: x for x in options}

        return options

    @property
    def value(self) -> Union[SimultanVertex, SimultanEdge, SimultanEdgeLoop, SimultanFace, SimultanVolume, None]:
        selected_keys = [int(x['id']) for x in self.geo_select.selected][0]
        return self.current_options.get(selected_keys, None)

    @ui.refreshable
    def ui_content(self):

        self.geo_model_select = ui.select(options=[f'{geo_model.name}; ID: {geo_model.key}'
                                                   for geo_model in self.geo_models],
                                          value=f'{self.geo_models[0].name}; ID: {self.geo_models[0].key}'
                                                if self.geo_models else None,
                                          label='Geometry Model',
                                          on_change=self.on_model_change).classes('w-full')

        self.geo_type_select = ui.select(options=['All', 'Vertex', 'Edge', 'EdgeLoop', 'Face', 'Volume'],
                                         value='All',
                                         label='Geometry Type',
                                         on_change=self.on_type_change).classes('w-full')

        self.geo_ui_content()

    def on_model_change(self, *args, **kwargs):
        self.geo_ui_content.refresh()

    def on_type_change(self, *args, **kwargs):
        self.geo_ui_content.refresh()

    @ui.refreshable
    def geo_ui_content(self):
        columns = [{'name': 'id', 'label': 'ID', 'field': 'id', 'sortable': True},
                   {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True},
                   {'name': 'type', 'label': 'Type', 'field': 'type', 'sortable': True}]
        rows = [{'id': x.id, 'name': x.name, 'type': type(x).__name__} for x in self.geo_options]
        self.geo_select = ui.table(columns=columns,
                                   rows=rows,
                                   title='Geometry',
                                   selection='single',
                                   pagination={'rowsPerPage': 5, 'sortBy': 'id', 'page': 1}
                                   ).classes('w-full h-full')

    def on_geo_change(self, *args, **kwargs):
        self.geo_ui_content.refresh()

    def create_edit_dialog(self):
        with ui.dialog() as self.dialog, ui.card():
            # ui.label(f'Edit {self.content.name}')
            self.ui_content()
            with ui.row():
                ui.button('Save', on_click=self.save)
                ui.button('Cancel', on_click=self.close)
            self.dialog.open()

    def close(self, *args, **kwargs):
        if self.dialog is not None:
            self.dialog.close()
            self.dialog = None

    def save(self, *args, **kwargs):

        if self.value is None:
            ui.notify('No value selected', type='negative')
            self.close()
            return
        self.value.associate(self.component)
        # self.component.associate = self.value
        ui.notify(f'Associated {self.component.name} with {self.value.name}')
        self.close()
        self.parent.ui_content.refresh()
