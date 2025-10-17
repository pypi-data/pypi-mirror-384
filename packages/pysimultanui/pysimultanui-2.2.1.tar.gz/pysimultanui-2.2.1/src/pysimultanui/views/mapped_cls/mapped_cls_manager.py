from nicegui import ui
from ..type_view_manager import TypeViewManager
from PySimultan2.simultan_object import SimultanObject


class MappedClsManager(TypeViewManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def button_create_ui_content(self):
        ui.button(f'Create new {self.item_view_name}', on_click=self.create_new_item, icon='add')

    def create_new_item(self, event):

        if self.data_model is None:
            ui.notify('No data model selected! Please load a data model first.')
            return

        new_item: SimultanObject = self.cls(data_model=self.data_model,
                                            object_mapper=self.mapper,
                                            )
        self.add_item_to_view(new_item)

    @ui.refreshable
    def ui_content(self):

        with ui.expansion(icon='format_list_bulleted',
                          text=f'{self.item_view_name if self.item_view_name is not None else self.cls._taxonomy} '
                               f'({len(self.items)})'
                          ).classes('w-full h-full bg-stone-100'
                                    ).bind_text_from(self,
                                                     'items',
                                                     lambda x: f'{self.item_view_name} ({len(x)})'
                                                     ) as self.expansion:
            self.methods_content()
            self.ui_expand_content()

    @ui.refreshable
    def ui_expand_content(self):
        self.items_ui_element = ui.row().classes('w-full h-full')
        with self.items_ui_element:
            if len(self.items) == 0:
                with ui.item():
                    self.no_items_label = ui.label('No items to display')

        for item in self.items:
            self.add_item_to_view(item)

        with ui.row().classes('w-full h-full'):
            self.button_create_ui_content()

    @ui.refreshable
    def methods_content(self):

        cls = self.user.mapper.mapped_classes.get(self.cls._taxonomy)
        if cls not in self.user.method_mapper.mapped_methods.keys():
            self.user.method_mapper.resolve_classes()

        mapped_methods = self.user.method_mapper.mapped_methods.get(cls, [])

        with ui.expansion(icon='code', text='Methods').classes('w-full h-full bg-stone-200'):
            with ui.list().classes('w-full h-full'):
                for method in mapped_methods:
                    with ui.item():
                        with ui.item_section():
                            ui.label(method.name)

                        with ui.item_section():
                            ui.button('Run', on_click=method.run).classes('q-ml-auto')
