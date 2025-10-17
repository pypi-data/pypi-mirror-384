from nicegui import ui
from logging import getLogger
from PySimultan2.default_types import ComponentDictionary
from ..type_view_manager import TypeViewManager


logger = getLogger('py_simultan_ui')


class ComponentDictManager(TypeViewManager):

    cls = ComponentDictionary

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def button_create_ui_content(self):
        ui.button('Create new Component dict', on_click=self.create_new_item, icon='add')

    def create_new_item(self, event):
        if self.data_model is None:
            ui.notify('No data model selected! Please load a data model first.')
            return

        new_item = self.cls(data_model=self.data_model)
        self.add_item_to_view(new_item)

    def update_items(self) -> list[any]:
        if self.cls is None:
            return []

        mapped_cls = self.mapped_cls

        if hasattr(mapped_cls, 'cls_instances'):
            logger.info(f'Found {len(mapped_cls.cls_instances)} instances for TVM {self.taxonomy}')
            return mapped_cls.cls_instances
        return []
