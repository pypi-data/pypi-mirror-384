import os

from PySimultan2.geometry import GeometryModel
from nicegui import ui, events, app

# from ..detail_views import show_detail
from .tools import create_stl_file
from ..type_view import TypeView
from ...geometry_3d.three_simgeo import display_simgeo
from ...geometry_3d.scene import ExtendedScene
from ... import user_manager

if not os.path.exists('/static/stl'):
    os.makedirs('/static/stl')

app.add_static_files('/stl', '/static/stl')


class GeometryDetailView(object):

    def __init__(self, *args, **kwargs):
        self.component: GeometryModel = kwargs.get('component')
        self.parent: GeometryView = kwargs.get('parent')
        self.file_lookup = None

    @property
    def geometry_model(self) -> GeometryModel:
        return self.component

    def ui_content(self, *args, **kwargs):
        with ui.row():
            ui.input(label='Name', value=self.component.name).bind_value(self.component, 'name')

        with ui.row():
            ui.label('Key:')
            ui.label(self.geometry_model.key)

        with ExtendedScene(on_click=self.handle_click).classes('w-full h-full') as self.scene_3d:
            self.scene_3d.axes_helper()
            for volume in self.component.volumes:
                display_simgeo(volume, self.scene_3d)
            for face in self.component.faces:
                display_simgeo(face, self.scene_3d)
            for edge_loop in self.component.edge_loops:
                display_simgeo(edge_loop, self.scene_3d)
            for edge in self.component.edges:
                display_simgeo(edge, self.scene_3d)
            for vertex in self.component.vertices:
                display_simgeo(vertex, self.scene_3d)

        ui.button('Show Fullscreen', on_click=self.show_geometry)

        with ui.expansion(icon='format_list_bulleted', text='Geometry').classes('w-full'):

            self.ui_vertices_table()
            self.ui_edges_table()
            self.ui_faces_table()
            self.ui_volumes_table()

        ui.button('Delete', on_click=self.delete_model)

    def ui_vertices_table(self):
        with ui.expansion(icon='format_list_bulleted',
                          text=f'Vertices ({len(self.geometry_model.vertices)})').classes('w-full h-full') as exp:
            columns = [{'name': 'id', 'label': 'ID', 'field': 'id', 'sortable': True},
                       {'name': 'x', 'label': 'X', 'field': 'x', 'sortable': True},
                       {'name': 'y', 'label': 'Y', 'field': 'y', 'sortable': True},
                       {'name': 'z', 'label': 'Z', 'field': 'z', 'sortable': True}]
            rows = [{'id': vertex.id, 'x': vertex.x, 'y': vertex.y, 'z': vertex.z}
                    for vertex in self.geometry_model.vertices]
            ui.table(columns=columns,
                     rows=rows,
                     title='Vertices',
                     pagination={'rowsPerPage': 5, 'sortBy': 'id', 'page': 1}).classes('w-full h-full')

    def ui_edges_table(self):
        with ui.expansion(icon='format_list_bulleted',
                          text=f'Edges ({len(self.geometry_model.edges)})').classes('w-full h-full') as exp:
            columns = [{'name': 'id', 'label': 'ID', 'field': 'id', 'sortable': True},
                       {'name': 'vertex_0', 'label': 'Vertex 0', 'field': 'vertex_0', 'sortable': True},
                       {'name': 'vertex_1', 'label': 'Vertex 1', 'field': 'vertex_1', 'sortable': True},
                       {'name': 'length', 'label': 'Length', 'field': 'length', 'sortable': True}]
            rows = [{'id': edge.id, 'vertex_0': edge.vertex_0.id, 'vertex_1': edge.vertex_1.id, 'length': edge.length}
                    for edge in self.geometry_model.edges]
            ui.table(columns=columns,
                     rows=rows,
                     title='Edges',
                     pagination={'rowsPerPage': 5, 'sortBy': 'id', 'page': 1}).classes('w-full h-full')

    def ui_faces_table(self):
        with ui.expansion(icon='format_list_bulleted',
                          text=f'Faces ({len(self.geometry_model.faces)})').classes('w-full h-full') as exp:
            columns = [{'name': 'id', 'label': 'ID', 'field': 'id', 'sortable': True},
                       {'name': 'area', 'label': 'Area', 'field': 'area', 'sortable': True}]
            rows = [{'id': face.id, 'area': face.area}
                    for face in self.geometry_model.faces]
            ui.table(columns=columns,
                     rows=rows,
                     title='Faces',
                     pagination={'rowsPerPage': 5, 'sortBy': 'id', 'page': 1}).classes('w-full h-full')

    def ui_volumes_table(self):
        with ui.expansion(icon='format_list_bulleted',
                          text=f'Volumes ({len(self.geometry_model.volumes)})').classes('w-full h-full') as exp:
            columns = [{'name': 'id', 'label': 'ID', 'field': 'id', 'sortable': True},
                       {'name': 'volume', 'label': 'Volume', 'field': 'volume', 'sortable': True}]
            rows = [{'id': volume.id, 'volume': volume.volume}
                    for volume in self.geometry_model.volumes]
            ui.table(columns=columns,
                     rows=rows,
                     title='Volumes',
                     pagination={'rowsPerPage': 5, 'sortBy': 'id', 'page': 1}).classes('w-full h-full')

    def delete_model(self, *args, **kwargs):
        ui.notify('Delete not implemented yet', type='negative')

    def show_geometry(self):
        # create dialog with fc_geometry
        with ui.dialog() as dialog, ui.card().classes('w-full h-full'):

            if self.file_lookup is None:
                self.file_lookup = create_stl_file(self.geometry_model)
            with ui.scene(on_click=self.handle_click).classes('w-full h-full') as self.scene_3d:
                self.scene_3d.spot_light(distance=100, intensity=0.5).move(-10, 0, 10)
                for f_id, f in self.file_lookup.items():
                    self.scene_3d.stl(f[0]).with_name(str(f_id)).material(f[1])

            ui.button('Cancel', on_click=dialog.close)

        dialog.open()

    def handle_click(self, e: events.SceneClickEventArguments, *args, **kwargs):
        if e.hits:
            hit = e.hits[0]
            name = hit.object_name or hit.object_id
            ui.notify(f'You clicked on the {name} at ({hit.x:.2f}, {hit.y:.2f}, {hit.z:.2f})')

    def refresh(self):
        self.ui_content()


class GeometryView(TypeView):

    detail_view = GeometryDetailView

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def geometry_model(self) -> GeometryModel:
        return self.component

    @ui.refreshable
    def ui_content(self):
        from ..detail_views import show_detail
        with ui.card().classes(f"{self.colors['item']} w-full h-full") as self.card:
            self.card.on('click', lambda e: show_detail(value=self.component,
                                                        parent=self)
                         )
            with ui.row().classes('h-full w-full') as self.row:
                self.row.on('click', lambda e: show_detail(value=self.component,
                                                           parent=self)
                            )
                self.checkbox = ui.checkbox(on_change=self.select)
                ui.label('Name:')
                ui.label(self.geometry_model.name)
                ui.label('Key:')
                ui.label(self.geometry_model.key)

    def delete_model(self, *args, **kwargs):
        ui.notify('Delete not implemented yet', type='negative')
