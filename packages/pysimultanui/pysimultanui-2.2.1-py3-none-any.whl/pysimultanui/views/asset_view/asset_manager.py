import os
import shutil
import tempfile
from typing import Optional, Union
from nicegui import ui, events

from . import AssetView
from PySimultan2.files import FileInfo, create_asset_from_file, DirectoryInfo

from SIMULTAN.Data.Assets import ResourceFileEntry, ResourceDirectoryEntry


from ..type_view_manager import TypeViewManager
from ... import core


class AssetManager(TypeViewManager):

    columns = [
        {'name': 'id',
         'label': 'Key',
         'field': 'id',
         'align': 'left',
         'sortable': True},
        {'name': 'name',
         'label': 'Name',
         'field': 'name',
         'sortable': True},
        {'name': 'size',
         'label': 'File Size',
         'field': 'size',
         'align': 'left',
         'sortable': True},
        {'name': 'last_modified',
         'label': 'Last modified',
         'field': 'last_modified',
         'align': 'left',
         'sortable': True}
    ]

    item_view_name = 'Assets'
    item_view_cls = AssetView
    cls = FileInfo

    @property
    def items(self) -> list[FileInfo]:
        return self.update_items()

    @items.setter
    def items(self, value):
        pass

    @property
    def selected_resource(self) -> Optional[Union[ResourceFileEntry, ResourceDirectoryEntry]]:
        if self.tree.props['selected'] is not None:
            return self.data_model.project_data_manager.AssetManager.GetResource(self.tree.props['selected'])
        else:
            return None

    @property
    def selected_file_info(self) -> Optional[FileInfo]:
        if isinstance(self.selected_resource, ResourceFileEntry):
            return FileInfo(resource_entry=self.selected_resource,
                            data_model=self.data_model)
        else:
            return None

    @property
    def selected_directory_info(self) -> Optional[DirectoryInfo]:
        if isinstance(self.selected_resource, ResourceDirectoryEntry):
            return DirectoryInfo(resource_entry=self.selected_resource,
                                 data_model=self.data_model)
        else:
            return None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table: Optional[ui.table] = None
        self.tree = None

    def update_items(self) -> list[any]:
        if self.data_model is None:
            return []
        # assets = self.data_model.assets
        # return [FileInfo(resource_entry=asset) for asset in assets]
        return self.data_model.get_file_infos()

    def button_create_ui_content(self):
        ui.button('Upload new Asset', on_click=self.create_new_item)

    def create_new_item(self, event):
        if self.data_model is None:
            ui.notify('No data model selected! Please select a data model first.')
            return

        with ui.dialog() as dialog, ui.card():
            ui.label(f'Upload new asset in {self.selected_directory_info.full_path if self.selected_directory_info is not None else "root-directory"}')
            ui.upload(label='Upload asset',
                      on_upload=self.upload_project).on(
                'finish', lambda: ui.notify('Finish!')
            ).classes('max-w-full')
            ui.button('Cancel', on_click=lambda e: dialog.close()).classes('mt-4')

        dialog.open()

    async def upload_project(self,
                       e: events.UploadEventArguments,
                       *args,
                       **kwargs):

        if hasattr(e, 'name'):
            name = e.name
        else:
            name = e.file.name

        if self.selected_directory_info is not None:
            new_file = self.selected_directory_info.add_file(filename=name,
                                                             content='')
        else:

            new_file = FileInfo.from_string(filename=name,
                                            content='',
                                            data_model=self.data_model)

        await e.file.save(new_file.full_path)

        # with open(new_file.full_path, 'wb') as f:
        #      shutil.copyfileobj(e.content, f)


        # with tempfile.TemporaryDirectory() as tmpdirname:
        #     temp_file_path = os.path.join(tmpdirname, e.name)
        #     with open(temp_file_path, 'wb') as f:
        #         shutil.copyfileobj(e.content, f)
        # # local_path = f'/tmp/{e.name}'
        # # shutil.copyfileobj(e.content, open(local_path, 'wb'))
        #     ui.notify(f'Project {e.name} uploaded!')
        #     new_fi = FileInfo(file_path=temp_file_path)
        #     new_asset = create_asset_from_file(new_fi,
        #                                        data_model=self.data_model,
        #                                        tag=None)

        self.ui_content.refresh()
        ui.notify(f'Asset {new_file.filename} uploaded!')

    def add_item_to_view(self, asset: FileInfo):
        if self.table is not None:
            self.table.add_rows({'id': f'{asset.resource_entry.Key}',
                                 'name': asset.name,
                                 'size': f'{asset.file_size / 1024:.3f} KB' if asset.file_size/1024 < 1024
                                 else f'{asset.file_size / 1024 / 1024:.3f} MB',
                                 'last_modified': asset.last_modified
                                 })
            self.table.run_method('scrollTo', len(self.table.rows) - 1)

    @ui.refreshable
    def ui_content(self, show_detail_fcn=None):

        # self.update_items()

        if self.data_model is None:
            self.tree = ui.tree([],
                                label_key='id',
                                on_select=lambda e: ui.notify(e.value))
            return

        def description(file):
            return f'File size: {file.file_size:.3f} KB\n' \
                   f'Last modified: {file.last_modified}'

        def get_children(directory):
            return [*[{'id': subdir.key,
                       'name': os.path.basename(subdir.full_path),
                       'icon': 'folder',
                       'key': subdir.key,
                       'children': get_children(subdir)}
                      for subdir in directory.sub_directories],
                    *[{'id': file.key,
                       'name': file.filename,
                       'icon': 'description',
                       'key': file.key,
                       'description': description(file),}
                      for file in directory.files]]

        tree_content = []

        for directory in self.data_model.get_directory_infos():
            tree_content.append({'id': directory.key,
                                 'name': os.path.basename(directory.full_path),
                                 'icon': 'folder',
                                 'key': directory.key,
                                 'children': get_children(directory)})
        for file in self.data_model.get_file_infos():
            tree_content.append({'id': file.key,
                                 'name': file.filename,
                                 'description': description(file),
                                 'key': file.key,
                                 'icon': 'description'})

        if show_detail_fcn is None:
            self.tree = ui.tree(tree_content,
                                label_key='name',
                                on_select=lambda e: self.show_details(e)).classes('w-full')
        else:
            self.tree = ui.tree(tree_content,
                                label_key='name',
                                on_select=lambda e: show_detail_fcn(e)).classes('w-full')

        self.tree.add_slot('default-header', '''
            <span class="default-header" :props="props">
              <q-icon v-if="props.node.icon" :name="props.node.icon" class="icon" />
              <strong>{{ props.node.name }}</strong>
              <span v-if="props.node.description" class="small-text">: {{ props.node.description }}</span>
            </span>
        ''')

        ui.input('filter').bind_value_to(self.tree, 'filter')

        # rows = [{'id': f'{asset.resource_entry.Key}',
        #          'name': asset.name,
        #          'size': f'{asset.file_size / 1024:.3f} KB' if asset.file_size/1024 < 1024
        #          else f'{asset.file_size / 1024 / 1024:.3f} MB',
        #          'last_modified': asset.last_modified
        #          }
        #         for asset in self.items]
        #
        # with ui.table(columns=self.columns,
        #               rows=rows,
        #               title='Assets',
        #               row_key='id').classes('w-full bordered') as self.table:
        #
        #     self.table.add_slot('body', r'''
        #                         <q-tr :props="props">
        #                             <q-td v-for="col in props.cols" :key="col.name" :props="props">
        #                                 {{ col.value }}
        #                             </q-td>
        #                             <q-td auto-width>
        #                                 <q-btn size="sm" color="blue" round dense
        #                                            @click="$parent.$emit('show_detail', props)"
        #                                            icon="launch" />
        #                                 <q-btn size="sm" color="blue" round dense
        #                                        @click="$parent.$emit('download', props)"
        #                                        icon="download" />
        #                             </q-td>
        #                         </q-tr>
        #                     ''')
        #
        #     self.table.on('download', self.download)
        #     self.table.on('show_detail', self.show_details)

        self.button_create_ui_content()

    def download(self, e: events.GenericEventArguments):
        asset = next(asset for asset in self.items if asset.resource_entry.Key == int(e.args['row']['id']))
        ui.download(f'assets/{asset.name}')

    def update_items_views(self):

        self.item_views = {}
        self._items = self.update_items()
        print(f'Updating items: {len(self.items)}')
        self.ui_content.refresh()

    def get_instance_row(self, props):
        return next((asset for asset in self.items if asset._resource_entry.Key == int(props.args['row']['id'])), None)

    def show_details(self, props):
        resource = self.selected_resource
        if isinstance(resource, ResourceFileEntry):
            from ..detail_views import show_detail
            show_detail(FileInfo(resource_entry=resource,
                                 data_model=self.data_model))
        else:
            return
