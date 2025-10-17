import numpy as np
import pandas as pd
from copy import deepcopy
from typing import Type, Optional
from functools import partial
from nicegui import Client, app, ui, events
from .type_view import TypeView
from .type_view_manager import TypeViewManager
from .utils import FloatInput, IntegerInput

import plotly.graph_objects as go

# from .detail_views import show_detail
from .. import user_manager
from ..core.edit_dialog import ContentEditDialog

from System.Collections.Generic import List as NetList
from System.Collections.Generic import ICollection as NetICollection
from System import Array, Double, Object, Boolean, String

from SIMULTAN.Data.MultiValues import (SimMultiValueField3D, SimMultiValueField3DParameterSource, SimMultiValueBigTable,
                                       SimMultiValueBigTableHeader, SimMultiValueBigTableParameterSource)

from PySimultan2.multi_values import simultan_multi_value_field_3d_to_numpy, add_row


class NDArrayDetailView(object):

    def __init__(self, *args, **kwargs) -> None:
        self.component: SimMultiValueField3D = kwargs.get('component')
        self.parent = kwargs.get('parent')
        self.array = None
        self.dim_slider = None
        self.table = None

        self.editable = kwargs.get('editable', False)
        self.changed = False

    def ui_content(self, *args, **kwargs):

        from .detail_views import show_detail

        with ui.row().classes('w-full'):
            ui.input(label='Name',
                     value=self.component.Name).classes('w-full').bind_value(self.component, 'Name')
        with ui.row().classes('w-full'):
            ui.label('ID:').classes('w-full')
            with ui.row():
                with ui.row():
                    ui.label(f'{self.component.Id.GlobalId.ToString()}')
                with ui.row():
                    ui.label(f'{self.component.Id.LocalId}')

        self.array = simultan_multi_value_field_3d_to_numpy(self.component, squeeze=False)

        with ui.row().classes('w-full'):
            with ui.column():
                ui.label('Shape:')
                ui.label(f'{self.array.shape}')

        ui.separator()
        with ui.card().classes('w-full h-full'):
            ui.label('Dimension to display:')
            self.dim_slider = ui.slider(min=0, max=self.component.ZAxis.Count - 1,
                                        step=1,
                                        value=0,
                                        on_change=self.table_ui_content.refresh)
            ui.input(value='0').bind_value(self.dim_slider,
                                           'value',
                                           forward=lambda x: int(x),
                                           backward=lambda x: str(x))

        ui.checkbox(text='Edit',
                    value=self.editable,
                    on_change=lambda e: self.table_ui_content.refresh()).bind_value(self,
                                                                                    'editable')
        self.table_ui_content()

    @ui.refreshable
    def array_edit_ui_content(self, disp_array):

        def edit_cell_value(e: events.GenericEventArguments,
                            *args,
                            **kwargs) -> None:
            self.edit_cell(e, i,j, *args, **kwargs)

        with ui.grid(columns=disp_array.shape[1]).classes('w-full h-full gap-0'):
            for i, row in enumerate(disp_array):
                for j, col in enumerate(row):
                    FloatInput(value=col,
                               on_change=partial(edit_cell_value,
                                                 i=deepcopy(i),
                                                 j=deepcopy(j)
                                                 ),
                               ).classes('w-full h-full')
        ui.separator()

        ui.button('Add Row',
                  icon='add',
                  on_click=self.add_row)

        # ui.button(icon='save',
        #           on_click=self.save_array)
        # ui.button(icon='cancel',
        #           on_click=self.cancel_changes)

    @ui.refreshable
    def array_view_ui_content(self, disp_array):
        self.table = ui.table.from_pandas(pd.DataFrame(disp_array),
                                          ).classes('w-full h-full').props('virtual-scroll')
        with self.table.add_slot('top-left'):
            def toggle() -> None:
                self.table.toggle_fullscreen()
                button.props('icon=fullscreen_exit' if self.table.is_fullscreen else 'icon=fullscreen')

            button = ui.button('Toggle fullscreen', icon='fullscreen', on_click=toggle).props('flat')


        self.table.add_slot('body-cell-name', r'''
            <q-td key="name" :props="props">
                <q-input
                    v-model="props.row.name"
                    dense
                    borderless
                    @blur="saveEdit(props.row)"
                  />
            </q-td>
        ''')

        self.table.on('edit_cell', self.edit_cell)

    @ui.refreshable
    def table_ui_content(self, edit: Optional[bool] = None) -> None:
        if self.array.shape.__len__() > 2:
            disp_array = self.array[:, :, int(self.dim_slider.value if self.dim_slider is not None else 0)]
        else:
            disp_array = self.array

        if disp_array.shape.__len__() == 1:
            disp_array = np.expand_dims(disp_array, axis=1)

        if edit is None:
            edit = self.editable

        if edit:
            self.array_edit_ui_content(disp_array)
        else:
            self.array_view_ui_content(disp_array)

    def edit_cell(self, *args, **kwargs) -> None:

        try:
            new_value = float(args[0].value)
        except ValueError:
            return

        if self.array.shape.__len__() == 1:
            self.component[kwargs['i'], kwargs['j'], 0] = new_value
        elif self.array.shape.__len__() in (2, 3):
            self.component[kwargs['i'],
            kwargs['j'],
            int(self.dim_slider.value if self.dim_slider is not None else 0)] = new_value
        else:
            raise NotImplementedError('Array editing dor array with more than 3 dimensions not implemented yet')

    async def add_row(self):
        with ui.dialog() as dialog, ui.card():
            ui.label(f'Add new item')
            dim_input = IntegerInput(label='Dimension',
                                     value=0,
                                     )

            with ui.row():
                ui.button('OK', on_click=lambda: dialog.submit({'ok': True,
                                                                'dim': dim_input.value})

                          )
                ui.button('Cancel', on_click=lambda: dialog.submit({'ok': False}))

        result = await dialog
        if result is None:
            return
        if result['ok']:
            dim = int(result['dim'])
            self.component = add_row(self.component,
                                     dim)
            self.array = simultan_multi_value_field_3d_to_numpy(self.component, squeeze=False)
            self.table_ui_content.refresh()
            ui.notify('Row added!')

    def cancel_changes(self, *args, **kwargs) -> None:
        self.array = simultan_multi_value_field_3d_to_numpy(self.component, squeeze=False)

        self.parent.refresh()
        ui.notify('Changes cancelled!')



class NDArrayView(TypeView):

    detail_view = NDArrayDetailView

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.content = kwargs.get('content', None)

    @ui.refreshable
    def ui_content(self):
        from .detail_views import show_detail
        with ui.card().classes(f"{self.colors['item']} w-full h-full") as self.card:
            self.card.on('click', lambda e: show_detail(value=self.component,
                                                        parent=self))
            with ui.row().classes('bg-stone-100 w-full') as self.row:
                self.row.on('click', lambda e: show_detail(value=self.component,
                                                           parent=self))
                self.checkbox = ui.checkbox(on_change=self.select)
                ui.label(f'{self.component.Id}')
                ui.label(f'{self.component.Name}')


class NDArrayManager(TypeViewManager):

    cls: np.ndarray = np.ndarray
    item_view_cls: Type[TypeView] = NDArrayView
    item_view_name = 'ND Arrays'

    def update_items(self) -> list[SimMultiValueField3D]:
        if self.data_model is None:
            return []
        return [x for x in self.data_model.value_fields if type(x) == SimMultiValueField3D]

    def button_create_ui_content(self):
        ui.button('Create new ND-Array', on_click=self.create_new_item, icon='add')

    @ui.refreshable
    def add_item_to_view(self,
                         item: any,
                         raw_val=None):

        if isinstance(item, SimMultiValueField3D):
            val_source = item
        elif isinstance(item, np.ndarray):
            val_source: SimMultiValueField3D = raw_val.ValueSource.ValueField

        if self.items_ui_element is None:
            return

        if val_source not in self.items:
            self.items.append(val_source)
        item_view = self.item_views.get(str(val_source.Id), None)

        if item_view is None:
            item_view = self.item_view_cls(component=val_source,
                                           parent=self)
            self.item_views[str(val_source.Id)] = item_view
            with self.items_ui_element:
                item_view.ui_content()
        else:
            if item_view.card.parent_slot.parent.parent_slot.parent is not self.items_ui_element:
                with self.items_ui_element:
                    item_view.ui_content()
        return item_view
