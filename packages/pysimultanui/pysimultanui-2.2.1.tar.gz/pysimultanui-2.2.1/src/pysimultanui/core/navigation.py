from typing import Optional, Type
from nicegui import ui, app

from .. import user_manager
from ..import core
from ..views.type_view_manager import TypeViewManager
from ..views.view_manager import ViewManager


class Navigation(object):

    def __init__(self, *args, **kwargs):
        pass
        # self._view_manager = None
        # self.data_model = kwargs.get('data_model', core.data_model)
        # self.navigation_drawer = core.navigation_drawer
        # self.view_manager: Optional[Type[ViewManager]] = kwargs.get('view_manager', core.view_manager)
        # self.geometry_manager: Optional[Type[TypeViewManager]] = kwargs.get('geometry_manager', core.geometry_manager)
        # self.asset_manager: Type[TypeViewManager] = kwargs.get('asset_manager')

    @property
    def data_model(self):
        return user_manager[app.storage.user['username']].data_model

    @property
    def navigation_drawer(self):
        return user_manager[app.storage.user['username']].navigation_drawer

    @property
    def view_manager(self):
        return user_manager[app.storage.user['username']].view_manager

    @property
    def geometry_manager(self):
        return user_manager[app.storage.user['username']].geometry_manager

    @property
    def asset_manager(self):
        return user_manager[app.storage.user['username']].asset_manager

    @property
    def obj_mapper(self) -> core.PythonMapper:
        return self.view_manager.mapper

    @ui.refreshable
    def ui_content(self):
        with self.navigation_drawer:
            with ui.expansion(icon='format_list_bulleted',
                              text=f'Mapped Classes ({len(self.view_manager.cls_views)})').classes('w-full'):

                for cls, cls_view_dict in self.view_manager.cls_views.items():
                    item_view_manager = cls_view_dict.get('item_view_manager', None)
                    if item_view_manager is None:
                        continue
                    else:
                        with ui.row():
                            def add_link(cls, cls_view_dict):
                                taxonomy = cls._taxonomy if hasattr(cls, '_taxonomy') else cls.__name__
                                cls_instances = cls.cls_instances if hasattr(cls, 'cls_instances') else []

                                ui.link(f'{taxonomy} ({len(cls_instances)})',
                                        cls_view_dict['item_view_manager'].expansion
                                        ).bind_text_from(cls,
                                                         'cls_instances'
                                                         , lambda x: f'{cls._taxonomy} ({len(x)})')

                            add_link(cls, cls_view_dict)

            if self.geometry_manager.expansion is not None:
                ui.link('Geometry models', self.geometry_manager.expansion)

            if self.asset_manager.expansion is not None:
                ui.link('Assets', self.asset_manager.expansion)
