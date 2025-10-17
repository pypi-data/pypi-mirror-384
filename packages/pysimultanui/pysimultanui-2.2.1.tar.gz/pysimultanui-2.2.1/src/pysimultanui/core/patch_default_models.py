from nicegui import app
from PySimultan2 import config
from PySimultan2.object_mapper import PythonMapper


def patch(user_manager):

    class GlobalData:
        def __init__(self):
            self._data_model = None
            self._mapper = None
            self._user_manager = user_manager

        @property
        def user(self):
            return self._user_manager.users[app.storage.user['username']]

        @property
        def data_model(self):
            return self._data_model

        @data_model.setter
        def data_model(self, value):
            self._data_model = value

        @property
        def mapper(self):
            if self._mapper is None:
                self._mapper = PythonMapper()
            return self._mapper

        @mapper.setter
        def mapper(self, value):
            self._mapper = value

    global_data = GlobalData()

    def get_user_default_data_model(*args, **kwargs):
        # user_manager.users[app.storage.user['username']]

        try:
            return user_manager.current_user.data_model
        except RuntimeError:
            return None

    def set_user_default_data_model(data_model, *args, **kwargs):
        # user_manager.users[app.storage.user['username']]
        # user_manager.current_user.data_model = data_model
        pass

    def get_user_default_mapper(*args, **kwargs):
        # user_manager.users[app.storage.user['username']]
        return user_manager.current_user.mapper

    def set_user_default_mapper(mapper, *args, **kwargs):
        # user_manager.users[app.storage.user['username']]
        # user_manager.current_user.mapper = mapper
        pass

    config.get_default_data_model = get_user_default_data_model
    config.set_default_data_model = set_user_default_data_model

    config.get_default_mapper = get_user_default_mapper
    config.set_default_mapper = set_user_default_mapper
