import shutil
import tempfile
import os
from typing import Optional
from nicegui import ui, events, app
from PySimultan2.geometry import GeometryModel

from ... import user_manager
from . import GeometryView
from ..type_view_manager import TypeViewManager
from ... import user_manager


try:
    try:
        from ...core import freecad_utils
    except ImportError:
        pass

    import FreeCAD
    import Part as FCPart
    freecad_supported = True

    from ...core.freecad_utils.tools import import_freecad

except ImportError:
    freecad_supported = False


class GeometryManager(TypeViewManager):

    columns = [{'name': 'id',
                'label': 'Key',
                'field': 'id',
                'sortable': True,
                'align': 'left'},
               {'name': 'name',
                'label': 'Name',
                'field': 'name',
                'sortable': True,
                'align': 'left'},
               {'name': 'file_name',
                'label': 'File Name',
                'field': 'file_name',
                'sortable': True,
                'align': 'left'},
               {'name': 'file_size',
                'label': 'File Size',
                'field': 'file_size',
                'sortable': True,
                'align': 'left'},
               {'name': 'actions',
                'label': 'Actions',
                'field': 'actions',
                'sortable': False,
                'align': 'left'},
               ]

    item_view_name = 'Geometry Models'
    item_view_cls = GeometryView
    cls = GeometryModel

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.new_model_dialog = None
        self.table: Optional[ui.table] = None

    @property
    def user(self):
        return user_manager[app.storage.user['username']]

    @property
    def mapper(self):
        return self.user.mapper

    @property
    def project_manager(self):
        return self.user.project_manager

    @property
    def selected_items(self):
        selected_keys = [int(x['id']) for x in self.table.selected]
        return [x for x in self.items if x.key in selected_keys]

    def update_items(self) -> list[any]:
        if self.data_model is None:
            return []

        return [GeometryModel(wrapped_object=x,
                              object_mapper=self.mapper,
                              data_model=self.data_model) for x in
                self.data_model.models.values()]

    def button_create_ui_content(self):
        ui.button('Create new', on_click=self.create_new_model)

    @ui.refreshable
    def ui_content(self):
        self.items = self.update_items()
        self.methods_ui_content()

        rows = [{'id': f'{item.key}',
                 'name': item.name,
                 'file_name': item.resource_file_entry.Name if item.resource_file_entry is not None else 'None',
                 'file_size': f'{os.path.getsize(item.resource_file_entry.File.FullPath) / 1024:.2f} kB'
                 }
                for item in self.items]

        with ui.table(columns=self.columns,
                      rows=rows,
                      title='Geometry Models',
                      selection='single',
                      row_key='id',
                      pagination={'rowsPerPage': 10, 'sortBy': 'id', 'page': 1}).classes('w-full bordered') as self.table:

            # self.table.add_slot('body', r'''
            #                     <q-tr :props="props">
            #                         <q-td v-for="col in props.cols" :key="col.name" :props="props">
            #                             {{ col.value }}
            #                         </q-td>
            #                         <q-td auto-width>
            #                             <q-btn size="sm" color="blue" round dense
            #                                    @click="$parent.$emit('show_detail', props)"
            #                                    icon="launch" />
            #                         </q-td>
            #                     </q-tr>
            #                 ''')

            self.table.add_slot('body-cell-actions', r'''
                                            <q-td key="actions" :props="props">
                                                <q-btn size="sm" color="blue" round dense
                                                    @click="$parent.$emit('show_detail', props)"
                                                    icon="launch" />
                                            </q-td>
                                        ''')

            self.table.on('show_detail', self.show_detail)

        self.button_create_ui_content()

    def show_detail(self, e: events.GenericEventArguments):
        from ..detail_views import show_detail
        geo_model: GeometryModel = next((x for x in self.items if x.key == int(e.args['row']['id'])), None)
        show_detail(geo_model)

    def add_item_to_view(self, item: GeometryModel):

        if item.key not in (int(x['id']) for x in self.table.rows):
            self.table.add_rows({'id': f'{item.key}',
                                 'name': item.name,
                                 'file_name': item.resource_file_entry.Name if item.resource_file_entry is not None else 'None',
                                 'file_size': f'{os.path.getsize(item.resource_file_entry.File.FullPath) / 1024:.2f} kB'
                                 })

    # @ui.refreshable
    # def ui_content(self):
    #
    #     with ui.row().classes('w-full h-full') as self.expansion:
    #
    #     # with ui.expansion(icon='format_list_bulleted',
    #     #                   text=f'{self.item_view_name if self.item_view_name is not None else self.cls._taxonomy} '
    #     #                        f'({len(self.items)})').classes('w-full h-full') as self.expansion:
    #     #
    #     #     self.expansion.bind_text_from(self,
    #     #                                   'items',
    #     #                                   lambda x: f'{self.item_view_name} ({len(x)})'
    #     #                                   )
    #
    #         self.methods_ui_content()
    #         self.items_ui_element = ui.row().classes('w-full h-full')
    #
    #         if len(self.items) == 0:
    #             with self.items_ui_element:
    #                 ui.label('No items to display')
    #         else:
    #             for item in self.items:
    #                 self.add_item_to_view(item)
    #
    #         with ui.row().classes('w-full h-full'):
    #             self.button_create_ui_content()
    #
    #     # super().ui_content()

    def create_new_model(self):
        def create_new_model_action():
            try:

                new_model = GeometryModel(data_model=self.user.data_model,
                                          name=self.new_model_dialog.project_name.value)
                self._geometry_models = None
                self._geometry_model_views = None
                self.new_model_dialog.close()
                ui.notify('New model created', type='positive')
                self.add_item_to_view(new_model)
                self.items = self.update_items()
            except Exception as e:
                ui.notify(f'Error creating new model: {e}', type='negative')

        with ui.dialog() as self.new_model_dialog, ui.card():
            ui.label('Create new fc_geometry model')
            self.new_model_dialog.project_name = ui.input('Name')
            with ui.row().classes('justify-between'):
                ui.button('Create', on_click=create_new_model_action)
                ui.button('Cancel', on_click=self.new_model_dialog.close)

        self.new_model_dialog.open()

    def import_from_file(self):
        # check if only one model is selected:
        if len(self.selected_items) != 1:
            ui.notify('Please select exactly one model to import to', type='negative')
            return

        # create dialog to upload file
        with ui.dialog() as dialog, ui.card():
            dialog.scale_input = ui.input(label='Scale Model', value='0.001').classes('w-full')

            upload = ui.upload(label='Upload asset',
                               on_upload=lambda e: self.upload_geometry(e, dialog=dialog)).on(
                'finish', lambda: ui.notify('Finish!')
            ).classes('max-w-full')
            upload.scale_input = dialog.scale_input
            ui.button('Cancel', on_click=lambda e: dialog.close()).classes('mt-4')
        dialog.open()

    def upload_geometry(self,
                        e: events.UploadEventArguments,
                        dialog: ui.dialog,
                        *args,
                        **kwargs):

        dialog.close()

        try:

            with tempfile.TemporaryDirectory() as tmpdirname:
                temp_file_path = os.path.join(tmpdirname, e.name)
                with open(temp_file_path, 'wb') as f:
                    shutil.copyfileobj(e.content, f)
                ui.notify(f'Project {e.name} uploaded!')

                if e.name.endswith('.fcstd') or e.name.endswith('.FCStd'):
                    doc = FreeCAD.open(temp_file_path)
                else:
                    doc = FreeCAD.newDocument()
                    s = FCPart.read(temp_file_path)
                    doc.addObject("Part::Feature", "Part").Shape = s

                num_created = import_freecad(doc=doc,
                                             geo_model=self.selected_items[0],
                                             data_model=self.data_model,
                                             object_mapper=self.user.mapper,
                                             scale=float(e.sender.scale_input.value))

            # local_path = f'/tmp/{e.name}'
            # shutil.copyfileobj(e.content, open(local_path, 'wb'))
            # ui.notify(f'Project {e.name} uploaded!')
            #
            # # open file in FreeCAD
            # doc = FreeCAD.open(local_path)
            # num_created = import_freecad(doc=doc,
            #                              geo_model=self.selected_items[0],
            #                              data_model=self.data_model,
            #                              object_mapper=self.user.mapper,
            #                              scale=float(e.sender.scale_input.value))

            ui.notify(f'Imported {num_created[0]} Vertices, '
                      f'{num_created[1]} Edges, '
                      f'{num_created[2]} EdgeLoops, '
                      f'{num_created[3]} Faces, '
                      f'{num_created[4]} Volumes.', type='positive')

            # create new fc_geometry model
            # self.ui_content.refresh()
        except Exception as e:
            ui.notify(f'Error uploading file: {e}', type='negative')

    def methods_ui_content(self):
        with ui.expansion(icon='code', text='Methods').classes('w-full bg-stone-300'):
            with ui.list().classes('w-full h-full'):
                if freecad_supported:
                    with ui.row().classes('w-full h-full'):
                        ui.label('Import from file')
                        ui.button('Import', on_click=self.import_from_file).classes('q-ml-auto')
                else:
                    ui.label('No Methods registered (FreeCAD not supported)')
