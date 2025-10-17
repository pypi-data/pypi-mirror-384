import shutil
import os
from typing import Optional
from nicegui import ui, events, app

from .type_view_manager import TypeViewManager
from .. import user_manager

from SIMULTAN.Data.MultiValues import (SimMultiValueField3D, SimMultiValueField3DParameterSource, SimMultiValueBigTable,
                                       SimMultiValueBigTableHeader, SimMultiValueBigTableParameterSource)


class ArrayManager(TypeViewManager):

    columns = [{'name': 'id',
                'label': 'ID',
                'field': 'id',
                'sortable': True,
                'align': 'left'},
               {'name': 'name',
                'label': 'Name',
                'field': 'name',
                'sortable': True,
                'align': 'left'},
               {'name': 'shape',
                'label': 'Shape',
                'field': 'shape',
                'sortable': False,
                'align': 'left'},
               ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table: Optional[ui.table] = None

        self.df_items = {}
        self.np_items = {}

    @property
    def data_model(self):
        return self._data_model

    @data_model.setter
    def data_model(self, value):
        self._data_model = value
        self.df_items = self.update_df_items()
        self.np_items = self.update_np_items()
        self.ui_content.refresh()

    @property
    def user(self):
        return user_manager[app.storage.user['username']]

    @property
    def mapper(self):
        return self.user.mapper

    @property
    def project_manager(self):
        return self.user.project_manager

    def update_df_items(self) -> list[str: any]:
        if self.data_model is None:
            return {}
        return {str(x.Id): x for x in self.data_model.value_fields if isinstance(x, SimMultiValueBigTable)}

    def update_np_items(self) -> dict[str: any]:
        if self.data_model is None:
            return {}
        return {str(x.Id): x for x in self.data_model.value_fields if isinstance(x, SimMultiValueField3D)}

    def button_create_table_ui_content(self):
        ui.button('Create new table', on_click=self.create_new_table)

    def button_create_np_ui_content(self):
        ui.button('Create new array', on_click=self.create_new_array)

    @ui.refreshable
    def ui_content(self):
        self.ui_df_content()
        self.ui_np_content()

    def ui_df_content(self):
        df_items = self.update_df_items()

        rows = [{'id': f'{item.Id}',
                 'name': item.Name,
                 'shape': f'{(item.RowHeaders.Count, item.ColumnHeaders.Count)}'
                 }
                for item in df_items.values()]

        with ui.table(columns=self.columns,
                      rows=rows,
                      title='Tables',
                      selection='single',
                      row_key='id').classes('w-full bordered') as self.table:

            self.table.add_slot('body', r'''
                                <q-tr :props="props">
                                    <q-td v-for="col in props.cols" :key="col.name" :props="props">
                                        {{ col.value }}
                                    </q-td>
                                    <q-td auto-width>
                                        <q-btn size="sm" color="blue" round dense
                                               @click="$parent.$emit('show_detail', props)"
                                               icon="launch" />
                                    </q-td>
                                </q-tr>
                            ''')

            self.table.on('show_detail', self.show_df_detail)

        self.button_create_table_ui_content()

    def ui_np_content(self):
        df_items = self.update_np_items()

        rows = [{'id': f'{item.Id}',
                 'name': item.Name,
                 'shape': f'{(len(item.XAxis), len(item.YAxis), len(item.ZAxis))}'
                 }
                for item in df_items.values()]

        with ui.table(columns=self.columns,
                      rows=rows,
                      title='Arrays',
                      selection='single',
                      row_key='id').classes('w-full bordered') as self.table:

            self.table.add_slot('body', r'''
                                <q-tr :props="props">
                                    <q-td v-for="col in props.cols" :key="col.name" :props="props">
                                        {{ col.value }}
                                    </q-td>
                                    <q-td auto-width>
                                        <q-btn size="sm" color="blue" round dense
                                               @click="$parent.$emit('show_detail', props)"
                                               icon="launch" />
                                    </q-td>
                                </q-tr>
                            ''')

            self.table.on('show_detail', self.show_np_detail)

        self.button_create_np_ui_content()

    def show_df_detail(self, e: events.GenericEventArguments):
        from .detail_views import show_detail
        table: SimMultiValueBigTable = self.df_items.get(e.args['row']['id'], None)
        show_detail(table)

    def show_np_detail(self, e: events.GenericEventArguments):
        from .detail_views import show_detail
        array: SimMultiValueBigTable = self.np_items.get(e.args['row']['id'], None)
        show_detail(array)

    def add_df_item_to_view(self, item: SimMultiValueBigTable):

        if str(item.Id) not in (str(x['id']) for x in self.table.rows):
            self.table.add_rows({'id': f'{item.Id}',
                                 'name': item.Name,
                                 'shape': f'{(item.RowHeaders.Count, item.ColumnHeaders.Count)}'
                                 })

    def add_np_item_to_view(self, item: SimMultiValueBigTable):

        if str(item.Id) not in (x['id'] for x in self.table.rows):
            self.table.add_rows({'id': f'{item.Id}',
                                 'name': item.Name,
                                 'shape': f'{(len(item.XAxis), len(item.YAxis), len(item.ZAxis))}'
                                 })

    def create_new_table(self):
        ui.notify('Create new table not implemented yet!', type='negative')

    def create_new_array(self):
        ui.notify('Create new array not implemented yet!', type='negative')
