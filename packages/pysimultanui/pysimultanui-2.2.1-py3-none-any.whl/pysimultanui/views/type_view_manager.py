import os
import shutil
import asyncio
from logging import getLogger
from typing import Optional, Type

# from .. import core
from .. import user_manager
from nicegui import Client, app, ui, events
from .type_view import TypeView
from PySimultan2.simultan_object import SimultanObject


logger = getLogger('py_simultan_ui')


class TypeViewManager(object):

    cls: Optional[Type[SimultanObject]] = None
    item_view_cls: type[TypeView] = TypeView
    item_view_name = 'Item'

    def __init__(self, *args, **kwargs):

        self._mapped_cls = None
        self._data_model = None
        self._items = []
        self._item_views: dict[any, any] = {}

        self.items_ui_element = kwargs.get('items_ui_element', None)
        self.no_items_label = None

        self.data_model = kwargs.get('data_model', None)
        self.expansion: Optional[ui.expansion] = kwargs.get('expansion', None)

    @property
    def project_manager(self):
        return self.user.project_manager

    @property
    def mapper(self):
        return self.user.mapper

    @property
    def mapped_cls(self):
        if self._mapped_cls is None:
            self._mapped_cls = self.mapper.mapped_classes.get(self.taxonomy, None)
        return self._mapped_cls

    @property
    def user(self):
        return user_manager[app.storage.user['username']]

    @property
    def taxonomy(self):
        if self.cls is not None:
            return self.cls._taxonomy if hasattr(self.cls, '_taxonomy') else self.cls

    @property
    def items(self) -> list[any]:
        if self._items is None:
            self.items = self.update_items()
        return self._items

    @items.setter
    def items(self, value: list[any]):

        old_value = self._items
        for removed_item in [x for x in old_value if x not in value]:
            self.remove_item_from_view(removed_item)
        self._items = value
        for item in self.items:
            self.add_item_to_view(item)

        self.update_no_items_label()

    @property
    def item_views(self):
        return self._item_views

    @item_views.setter
    def item_views(self, value: dict[any, any]):
        self._item_views = value

    @property
    def data_model(self):
        return self._data_model

    @property
    def selected_items(self):
        return [x for x in self.items if x.__ui_element__.selected]

    @data_model.setter
    def data_model(self, value):
        logger.debug(f'View Manager setting data model to {value}')
        # self._item_views = {}
        self._data_model = value
        self._items = self.update_items()
        self.ui_content.refresh()

    @ui.refreshable
    def ui_content(self):

        logger.info(f'Creating UI content for TVM {self.taxonomy}')

        with ui.row().classes('w-full h-full') as self.expansion:

        # with ui.expansion(icon='format_list_bulleted',
        #                   text=f'{self.item_view_name if self.item_view_name is not None else self.cls._taxonomy} '
        #                        f'({len(self.items)})'
        #                   ).classes('w-full h-full').bind_text_from(self,
        #                                                             'items',
        #                                                             lambda x: f'{self.item_view_name} ({len(x)})'
        #                                                             ) as self.expansion:
            self.ui_expand_content()

    @ui.refreshable
    def ui_expand_content(self):

        logger.info(f'Creating UI expand content for TVM {self.taxonomy}')

        self.items_ui_element = ui.row().classes('w-full h-full')
        with self.items_ui_element:
            if len(self.items) == 0:
                with ui.item():
                    self.no_items_label = ui.label('No items to display')

        for item in self.items:
            self.add_item_to_view(item)

        with ui.row().classes('w-full h-full'):
            self.button_create_ui_content()

    def button_create_ui_content(self):
        ui.button('Upload new Asset', on_click=self.create_new_item, icon='add')

    def update_items(self) -> list[any]:



        logger.info(f'Updating items for TVM {self.taxonomy}')

        # return self.cls.cls_instances

        if self.cls is None:
            return []
        mapped_cls = self.mapped_cls

        if mapped_cls is None:
            logger.warning(f'mapped_cls for TVM {self.taxonomy} is None!')
            return []
        if hasattr(mapped_cls, 'cls_instances'):
            logger.info(f'Found {len(mapped_cls.cls_instances)} instances for TVM {self.taxonomy}')
            return mapped_cls.cls_instances
        return []

    def create_new_item(self, event):

        logger.info(f'Updating items for TVM {self.taxonomy}')

        if self.data_model is None:
            ui.notify('No data model selected! Please load a data model first.')
            return

        new_item = self.cls()
        self.add_item_to_view(new_item)

    def update_expansion_text(self):
        if self.expansion is not None:
            self.expansion.text = f'{self.item_view_name if self.item_view_name is not None else self.cls._taxonomy} ' \
                                  f'({len(self.items)})'

    def add_item_to_view(self, item: any):

        logger.info(f'Adding item to TVM {self.taxonomy} view: {item}')

        if self.items_ui_element is None:
            return

        if item not in self.items:
            self.items.append(item)
        item_view: TypeView = self.item_views.get(item, None)

        if item_view is None:
            item_view: TypeView = self.item_view_cls(component=item,
                                                     parent=self)
            self.item_views[item] = item_view
            item.__ui_element__ = self.item_views[item]
            with self.items_ui_element:
                item_view.ui_content()
        else:
            if item_view.card.parent_slot.parent.parent_slot.parent is not self.items_ui_element:
                with self.items_ui_element:
                    item_view.ui_content()

        self.update_expansion_text()
        return item_view

    def remove_item_from_view(self, item: any):

        logger.info(f'Removing item from TVM {self.taxonomy} view: {item}')

        try:
            item_view = self.item_views.get(item, None)
            if item_view is not None:
                self.items_ui_element.remove(item_view.card)
                self.item_views.pop(item)
                item.__ui_element__ = None
        except Exception as e:
            pass

    def update_no_items_label(self):
        if self.items.__len__() == 0 and self.no_items_label is None and self.items_ui_element is not None:
            with self.items_ui_element:
                self.no_items_label = ui.label('No items to display')
        elif self.items.__len__() > 0 and self.no_items_label is not None and self.items_ui_element is not None:
            try:
                self.items_ui_element.remove(self.no_items_label)
                self.no_items_label = None
            except Exception as e:
                pass

    def new_instance_created(self, instance: any):
        self.add_item_to_view(instance)

    def update_items_views(self):

        # logger.info(f'Updating item views for TVM {self.taxonomy}')

        self.item_views = {}
        self._items = self.update_items()
        print(f'Updating items: {len(self.items)}')
        self.ui_expand_content.refresh()
