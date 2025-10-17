from typing import Any, Mapping, Union
from PySimultan2 import Content, TaxonomyMap
from PySimultan2.default_types import ComponentDictionary

from .core.user import UserManager
user_manager = UserManager()

import nicegui.binding
nicegui.binding.MAX_PROPAGATION_TIME = 0.1


def _new_set_attribute(obj: Union[object, Mapping], name: str, value: Any) -> None:
    if isinstance(obj, (dict, ComponentDictionary)):
        obj[name] = value
    else:
        setattr(obj, name, value)

nicegui.binding._set_attribute = _new_set_attribute


from .main_ui import run_ui
from .views.detail_views import DetailView
from .core.mappers import MethodMapper, Mapping, ViewManager


__all__ = ['run_ui', 'user_manager', 'Content', 'TaxonomyMap', 'DetailView', 'MethodMapper', 'Mapping', 'ViewManager']
