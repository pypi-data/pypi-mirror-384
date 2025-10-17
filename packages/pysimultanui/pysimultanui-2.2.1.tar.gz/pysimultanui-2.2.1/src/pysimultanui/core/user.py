import os
import asyncio
from nicegui import ui, app
from .mappers import MapperManager
from typing import Union, Optional

from .logging import logger

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .method_mapper import MethodMapper
    from PySimultan2.data_model import DataModel
    from PySimultan2 import PythonMapper
    from .mappers import Mapping
    from .project_manager import ProjectManager

initial_user_name = os.environ.get('INITIAL_USER_NAME', 'admin')
initial_user_email = os.environ.get('INITIAL_USER_EMAIL', 'example@test.de')
initial_user_password = os.environ.get('INITIAL_USER_PASSWORD', 'admin')

logger.info(f'User module imported')
class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class DetailHistory:

    max_history_entries = 10

    def __init__(self):
        self.detail_history = []
        self.detail_history_index = 0
        self.current_detail = None

    def add_item(self, item):

        if len(self.detail_history) > 0:
            if item is self.detail_history[self.detail_history_index]:
                return

        if len(self.detail_history) > 0 and self.detail_history_index < (len(self.detail_history) - 1):
            self.detail_history = self.detail_history[:self.detail_history_index]
            self.detail_history_index = len(self.detail_history) - 1

        self.detail_history.append(item)
        if len(self.detail_history) > self.max_history_entries:
            self.detail_history.pop(0)
        self.detail_history_index = len(self.detail_history) - 1
        self.current_detail = item

    def get_current_detail(self):
        return self.current_detail

    def get_previous_detail(self):
        if self.detail_history_index > 0:
            return self.detail_history[self.detail_history_index - 1]

    def get_next_detail(self):
        if self.detail_history_index < (len(self.detail_history) - 1):
            return self.detail_history[self.detail_history_index + 1]

    def __len__(self):
        return len(self.detail_history)

    def move_next(self):
        if self.detail_history_index < len(self.detail_history) - 1:
            self.detail_history_index += 1
            return self.detail_history[self.detail_history_index]

    def move_previous(self):
        if self.detail_history_index > 0:
            self.detail_history_index -= 1
            return self.detail_history[self.detail_history_index]

    def clear(self):
        self.detail_history = []
        self.detail_history_index = 0
        self.current_detail = None


class User:

    def __init__(self, *args, **kwargs):

        from ..core import method_mapper, mapper

        self._project_manager = None
        self._grid_view = None
        self._view_manager = None
        self._asset_manager = None
        self._geometry_manager = None
        self._array_manager = None
        self._navigation = None
        self._data_model: Optional['DataModel'] = None
        self._ui_log = None
        self._log_tab = None
        self._ui_tasks = None
        self._task_tab = None
        self._task_manager = None
        self._selected_mapper = None
        self._load_undefined: bool = True

        self.user_manager: Optional['UserManager'] = kwargs.get('user_manager', None)
        self.detail_history = DetailHistory()

        self.name: Optional[str] = kwargs.get('name', None)
        self.email: Optional[str] = kwargs.get('email', None)
        self.password: Optional[str] = kwargs.get('password', None)

        # self.mapper: Optional[PythonMapper] = kwargs.get('mapper', mapper)
        # self.method_mapper: Optional[MethodMapper] = kwargs.get('method_mapper', method_mapper)
        self.data_model: Union[DataModel, None] = kwargs.get('data_model', None)

        self.navigation_drawer = kwargs.get('navigation_drawer', None)
        self.project_tab = kwargs.get('project_tab', None)
        self.log_tab = kwargs.get('log_tab', None)
        self.detail_view = kwargs.get('detail_view', None)
        self.home_tab = kwargs.get('home_tab', None)
        self.tool_select = kwargs.get('tool_select', None)
        self.task_tab = kwargs.get('task_tab', None)

    @property
    def mapper_manager(self) -> MapperManager:
        return self.user_manager.mapper_manager

    @property
    def mapping(self) -> Optional['Mapping']:
        return self.mapper_manager.get_mapping(user=self,
                                               name=self.selected_mapper,
                                               load_undefined=self.load_undefined)

    @property
    def mapper(self) -> Optional['PythonMapper']:
        if self.mapping is None:
            return None

        mapper = self.mapping.mapper
        return mapper

    @property
    def method_mapper(self) -> Optional['MethodMapper']:
        return self.mapping.method_mapper

    @mapper.setter
    def mapper(self, value: Optional['PythonMapper']):
        self.mapping.mapper = value

    @property
    def load_undefined(self) -> bool:
        return self._load_undefined

    @load_undefined.setter
    def load_undefined(self, value: bool):
        if value == self._load_undefined:
            return
        self._load_undefined = value
        self.mapper.load_undefined = value
        self.mapper.clear()
        self.project_manager.open_data_model()
        self.project_manager.refresh_all_items()

    @property
    def mapper_options(self) -> list[str]:
        options = list(self.mapper_manager.available_mappings.keys())
        options.sort()
        return options

    @property
    def selected_mapper(self) -> Optional[str]:
        if self._selected_mapper is None:
            self._selected_mapper = self.mapper_options[0] if len(
                self.mapper_manager.available_mappings) > 0 else None
        return self._selected_mapper

    @selected_mapper.setter
    def selected_mapper(self, value: Optional[str]):
        if value == self._selected_mapper:
            return

        old_mapper = self.mapper
        old_mapper.clear()

        self._selected_mapper = value
        self.mapper = self.mapper.copy()
        self.mapper.load_undefined = self.load_undefined
        self.method_mapper.ui_content.refresh()
        self.project_manager.open_data_model()

    @property
    def available_mappings(self) -> dict[str, 'Mapping']:
        return self.mapper_manager.available_mappings

    @property
    def data_model(self) -> Union['DataModel', None]:
        return self._data_model

    @data_model.setter
    def data_model(self, value: Union['DataModel', None]):
        self._data_model = value
        if self.detail_history is not None:
            self.detail_history = DetailHistory()

    @property
    def grid_view(self):
        if self._grid_view is None:
            from ..views.grid_view import GridView
            self._grid_view = GridView()
        return self._grid_view

    @property
    def project_manager(self) -> 'ProjectManager':
        if self._project_manager is None:
            from .project_manager import ProjectManager
            self._project_manager = ProjectManager(user_manager=self.user_manager,
                                                   mapper=self.mapper)
        return self._project_manager

    @property
    def view_manager(self):
        # if self._view_manager is None:
        #     from ..views.view_manager import ViewManager
        #     self._view_manager = ViewManager(mapper=self.mapper,
        #                                      parent=self.project_manager)
        return self._view_manager

    @property
    def task_manager(self):
        if self._task_manager is None:
            from .method_mapper import TaskManager
            self._task_manager = TaskManager()
        return self._task_manager

    @property
    def asset_manager(self):
        if self._asset_manager is None:
            from ..views.asset_view import AssetManager
            self._asset_manager = AssetManager()
        return self._asset_manager

    @property
    def array_manager(self):
        if self._array_manager is None:
            from ..views.array_view import ArrayManager
            self._array_manager = ArrayManager()
        return self._array_manager

    @property
    def geometry_manager(self):
        if self._geometry_manager is None:
            from ..views.geometry_view import GeometryManager
            self._geometry_manager = GeometryManager(data_model=self.data_model)
        return self._geometry_manager

    @property
    def navigation(self):
        # if self._navigation is None:
        #     from .navigation import Navigation
        #     self._navigation = Navigation()
        return self._navigation

    @property
    def log_tab(self):
        return self._log_tab

    @log_tab.setter
    def log_tab(self, value):
        self._log_tab = value

        if self._log_tab is not None and self._ui_log is None:
            self.add_ui_log()

    @property
    def task_tab(self):
        return self._task_tab

    @task_tab.setter
    def task_tab(self, value):
        self._task_tab = value

        if self._task_tab is not None and self._ui_tasks is None:
            self.add_ui_tasks()

    @property
    def ui_log(self):
        if self._ui_log is None and self.log_tab is not None:
            self.add_ui_log()
        return self._ui_log

    @property
    def logger(self):
        if self.ui_log is None:
            return None
        return self.ui_log.logger

    def logout(self):
        self.data_model = None

    def add_ui_log(self):
        if self.log_tab is None:
            return
        from .ui_log import UILog
        with self.log_tab:
            self._ui_log = UILog()
            self._ui_log.ui_content()

    def add_ui_tasks(self):
        self.task_manager.ui_content()
        self._ui_tasks = True

    def select_mapper(self, *args, **kwargs):

        pass

        # with ui.dialog() as dialog, ui.card():
        #     ui.label('Select mapper:')
        #
        #     select = ui.select(options=list(self.available_mappings.keys()),
        #                        value=self.selected_mapper)
        #
        #     with ui.row():
        #         ui.button('OK', on_click=lambda: dialog.submit({'ok': True,
        #                                                         'mapper_name': select.value}
        #                                                        )
        #                   )
        #         ui.button('Cancel', on_click=lambda: dialog.submit({'ok': False}))

        # mapper_select_dialog = MapperSelectDialog(user=self)
        # mapper_select_dialog.open()

        # await asyncio.sleep(0.01)
        #
        # if not result.get('ok', False):
        #     return
        #
        # self.selected_mapper = result.get('mapper_name', self.selected_mapper)
        # self.project_manager.refresh_all_items()
        #
        # ui.notify(f'Selected mapper: {self.selected_mapper}')


class Admin(User):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class UserManager(metaclass=Singleton):

    def __init__(self):
        logger.debug('UserManager created')
        self.mapper_manager = MapperManager()
        self.users = {}
        self.create_initial_users()

    @property
    def current_user(self):
        return self.users[app.storage.user['username']]

    @property
    def current_data_model(self):
        return self.current_user.data_model

    def create_initial_users(self):
        admin = Admin(name=initial_user_name,
                      email=initial_user_email,
                      password=initial_user_password,
                      user_manager=self)

        self.users[initial_user_name] = admin

        user_1 = User(name=initial_user_name + '_2',
                      email=initial_user_email + '_2',
                      password=initial_user_password + '_2',
                      user_manager=self)

        self.users[initial_user_name + '_2'] = user_1

    def authenticate(self, username, password):
        if username in self.users and self.users[username].password == password:
            return True
        return False

    def __getitem__(self, key):
        return self.users[key]


class UserSettingsDialog(ui.dialog):

    def __init__(self, user=None) -> None:
        super().__init__()
        self._user = None

        with self, ui.card().classes('w-full h-full'):
            ui.label('User settings:')
            with ui.checkbox('Load undefined components',
                             value=True) as self.load_undefined:
                ui.tooltip('Load components that are not defined in the mapping')

            with ui.row().classes('justify-center'):
                ui.button('OK', on_click=self.ok)
                ui.button('Cancel', on_click=self.cancel)

        self.user = user

    @property
    def user(self) -> 'User':
        return self._user

    @user.setter
    def user(self, value: 'User') -> None:
        self._user = value
        if self._user is not None:
            self.load_undefined.value = self._user.load_undefined
        else:
            self.load_undefined.value = True

    def cancel(self, *args, **kwargs):
        self.close()

    def ok(self, *args, **kwargs):
        print('User settings saved')
        self.user.load_undefined = self.load_undefined.value
        ui.notify('User settings saved')
        self.close()

    def open(self, *args, **kwargs):
        super().open(*args, **kwargs)
