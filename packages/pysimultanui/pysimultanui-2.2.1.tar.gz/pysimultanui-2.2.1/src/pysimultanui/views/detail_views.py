import asyncio
from typing import Any, Optional, TYPE_CHECKING
from nicegui import ui, app
from logging import getLogger
from PySimultan2.simultan_object import SimultanObject
from PySimultan2.geometry import GeometryModel
from PySimultan2.default_types import ComponentDictionary, ComponentList
from PySimultan2.files import FileInfo
from PySimultan2.data_model import DataModel
import inspect

from SIMULTAN.Data.MultiValues import (SimMultiValueField3D, SimMultiValueField3DParameterSource, SimMultiValueBigTable,
                                       SimMultiValueBigTableHeader, SimMultiValueBigTableParameterSource)

from SIMULTAN.Data import SimId
from System import Guid

from .. import user_manager

from .pandas_df_view import DataFrameDetailView
from .numpy_view import NDArrayDetailView
from .geometry_view.geometry_view import GeometryDetailView
from .component_list_view.component_list_view import ListDetailView
from .component_dict_view.component_dict_view import DictDetailView
from .asset_view.asset_view import AssetDetailView
from .mapped_cls.mapped_cls_view import MappedClsDetailView

if TYPE_CHECKING:
    from ..core.user import User


logger = getLogger('py_simultan_ui')


def show_next_detail(*args, **kwargs):
    user = user_manager[app.storage.user['username']]
    show_detail(value=user.detail_history.move_next(), *args, **kwargs)


def show_previous_detail(*args, **kwargs):
    user = user_manager[app.storage.user['username']]
    show_detail(value=user.detail_history.move_previous(), *args, **kwargs)


class DetailView(object):

    def __init__(self, *args, **kwargs) -> None:
        """
        Class which represents a detail view.
        :param args:
        :param kwargs:
        """

        self.component: Any = kwargs.get('component')
        self.parent = kwargs.get('parent')

    def ui_content(self, *args, **kwargs):
        """
        Method to create the ui content for the detail view of self.component.
        :param args:
        :param kwargs:
        :return:
        """
        return

    @property
    def user(self) -> Optional['User']:
        return user_manager.users[app.storage.user['username']]

    @property
    def data_model(self) -> Optional[DataModel]:
        return self.user.data_model


def show_detail_for_component_id(global_id: str,
                                 local_id: str,
                                 *args,
                                 **kwargs):
    """
    Method to show the detail view for a component with a given component_id.
    :param component_id: str
    :param args:
    :param kwargs:
    :return:
    """
    user = user_manager[app.storage.user['username']]

    component = user.data_model.get_component_by_id(SimId(Guid(global_id), int(local_id)))
    mapped_component = user.mapper.create_python_object(component)

    show_detail(value=mapped_component, *args, **kwargs)


def show_detail(value,
                *args,
                detail_view_space = None,
                **kwargs):
    user = user_manager[app.storage.user['username']]

    if detail_view_space is None:
        detail_view_space = user.detail_view
        if value is None:
            detail_view_space.clear()
            user.detail_history.clear()
            return
        user.detail_history.add_item(value)

    # current_detail = user.detail_history[-1] if user.detail_history else None
    logger.debug(f'Showing details for {value}')
    detail_view_space.clear()
    with detail_view_space:
        with ui.card().classes('w-full'):
            with ui.row():
                previous_detail = user.detail_history.get_previous_detail()
                if previous_detail is not None:
                    ui.button(on_click=show_previous_detail,
                              icon='arrow_back').classes('q-mr-md')
                ui.space()
                next_detail = user.detail_history.get_next_detail()
                if next_detail is not None:
                    ui.button(on_click=show_next_detail,
                              icon='arrow_forward').classes('q-mr-md')

            user.current_detail = value

            if hasattr(value, '_taxonomy_map') and value._taxonomy_map.taxonomy_entry_key is not None:
                detail_view_cls = user.mapping.view_manager.views.get(value._taxonomy_map.taxonomy_entry_key, None)
                if detail_view_cls is None:
                    for cls in user.mapping.view_manager.views.keys():
                        if set([x._taxonomy_map.taxonomy_entry_key for x in value.sub_classes]) & set(user.mapping.view_manager.views.keys()):
                            detail_view_cls = user.mapping.view_manager.views.get(list(set([x._taxonomy_map.taxonomy_entry_key for x in value.sub_classes]) & set(user.mapping.view_manager.views.keys()))[0])
                            break
            else:
                detail_view_cls = None

            if detail_view_cls is None:
                if isinstance(value, SimMultiValueBigTable):
                    detail_view = DataFrameDetailView(component=value, **kwargs)
                elif isinstance(value, SimMultiValueField3D):
                    detail_view = NDArrayDetailView(component=value, **kwargs)
                elif isinstance(value, GeometryModel):
                    detail_view = GeometryDetailView(component=value, **kwargs)
                elif isinstance(value, ComponentList):
                    detail_view = ListDetailView(component=value, **kwargs)
                elif isinstance(value, ComponentDictionary):
                    detail_view = DictDetailView(component=value, **kwargs)
                elif isinstance(value, SimultanObject):
                    detail_view = MappedClsDetailView(component=value, **kwargs)
                elif isinstance(value, FileInfo):
                    detail_view = AssetDetailView(component=value, **kwargs)
            else:
                detail_view = detail_view_cls(component=value, **kwargs)

            if isinstance(detail_view.ui_content, ui.refreshable):
                fcn = detail_view.ui_content.func
            else:
                fcn = detail_view.ui_content

            if inspect.iscoroutinefunction(fcn):
                asyncio.run(detail_view.ui_content())
            else:
                detail_view.ui_content()
