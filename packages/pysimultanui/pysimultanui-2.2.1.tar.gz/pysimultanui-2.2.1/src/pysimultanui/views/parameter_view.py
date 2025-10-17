from nicegui import Client, app, ui, events
from .type_view import TypeView

from ..core.edit_dialog import ContentEditDialog


class ParameterView(TypeView):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.taxonomy = kwargs.get('taxonomy', None)
        self.raw_val = kwargs.get('raw_val', None)
        self.content = kwargs.get('content', None)

    @property
    def component(self):
        return self._component

    @component.setter
    def component(self, value):
        self._component = value

    @ui.refreshable
    def ui_content(self):

        with ui.item().classes('w-full h-full'):
            with ui.item_section():
                ui.label(f'{self.component}')

            if self.raw_val is None:
                with ui.item_section():
                    ui.label(f': {None}')
            else:
                if isinstance(self.raw_val.Value, (int, float)):
                    with ui.item_section():
                        if hasattr(self.raw_val, 'Unit'):
                            ui.label(f': {self.raw_val.Unit}')
                        else:
                            ui.label('')
                    with ui.item_section():
                        if hasattr(self.raw_val, 'ValueMin'):
                            ui.label(f': {self.raw_val.ValueMin}')
                        else:
                            ui.label('')
                    with ui.item_section():
                        if hasattr(self.raw_val, 'ValueMax'):
                            ui.label(f': {self.raw_val.ValueMax}')
                        else:
                            ui.label('')

            with ui.item_section():
                ui.button(icon='edit', on_click=self.edit).classes('q-ml-auto')

    def edit(self, event):
        edit_dialog = ContentEditDialog(component=self.component,
                                        raw_val=self.raw_val,
                                        parent=self.parent,
                                        content=self.content,
                                        taxonomy=self.taxonomy)
        edit_dialog.create_edit_dialog()
