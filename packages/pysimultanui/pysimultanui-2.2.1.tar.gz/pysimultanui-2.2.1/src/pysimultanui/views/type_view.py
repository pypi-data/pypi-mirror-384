import logging
from typing import Optional
from nicegui import ui, events
# from ..config import logger

logger = logging.getLogger('pysimultanui')


class TypeView:

    colors = {'item': 'bg-stone-100',
              'cls_color': 'bg-stone-300',
              'selected': 'bg-blue-200'}

    detail_view = None

    def __init__(self,
                 *args,
                 **kwargs) -> None:

        self._component = None
        self.checkbox = None
        self.component = kwargs.get('component', None)
        self.parent = kwargs.get('parent', None)

        self.row = None
        self.card: Optional[ui.card, None] = None

    @property
    def component(self):
        return self._component

    @component.setter
    def component(self, value):
        self._component = value

        try:
            self._component.__ui_element__ = self
        except Exception as e:
            logger.error(f'Error setting __ui_element__ attribute: {e}')

    @property
    def selected(self):
        if self.checkbox is None:
            return False
        return self.checkbox.value

    @ui.refreshable
    def ui_content(self):

        from .detail_views import show_detail

        with ui.list().classes('w-full h-full') as self.card:
        # with ui.card().classes('w-full h-full').props('color="blue-800" keep-color') as self.card:
            with ui.item().classes('w-full h-full'):
                with ui.item_section():
                    self.checkbox = ui.checkbox()
                with ui.item_section():
                    ui.input(label='Name', value=self.component.name).bind_value(self.component, 'name')
                with ui.item_section():
                    ui.label(f'{str(self.component.id)}')
                with ui.item_section():
                    ui.button(on_click=lambda e: show_detail(value=self.component,
                                                             parent=self), icon='open')

    def select(self, e: events.ClickEventArguments):
        if self.selected:
            self.row.classes(remove=f"{self.colors['item']}", add=f"{self.colors['selected']}")
            self.card.classes(remove=f"{self.colors['item']}", add=f"{self.colors['selected']}")
        else:
            self.row.classes(add=f"{self.colors['item']}", remove=f"{self.colors['selected']}")
            self.card.classes(add=f"{self.colors['item']}", remove=f"{self.colors['selected']}")
