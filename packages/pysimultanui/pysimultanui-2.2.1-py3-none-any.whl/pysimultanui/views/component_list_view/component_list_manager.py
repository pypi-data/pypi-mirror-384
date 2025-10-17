from nicegui import ui
from PySimultan2.default_types import ComponentList
from ..type_view_manager import TypeViewManager


class ComponentListManager(TypeViewManager):

    cls = ComponentList

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def button_create_ui_content(self):
        ui.button('Create new Component list', on_click=self.create_new_item, icon='add')

    def create_new_item(self, event):
        if self.data_model is None:
            ui.notify('No data model selected! Please load a data model first.')
            return

        new_item = self.cls(data_model=self.data_model)
        self.add_item_to_view(new_item)
