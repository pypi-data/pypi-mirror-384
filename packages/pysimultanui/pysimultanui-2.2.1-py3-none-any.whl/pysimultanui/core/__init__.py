from typing import Union
from .user import UserManager

from PySimultan2.object_mapper import PythonMapper
from PySimultan2.data_model import DataModel
from PySimultan2 import config as PySimultan2_config
from .method_mapper import method_mapper, mapped_method
from .logging import logger

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..app.home import ProjectManager
    from .navigation import Navigation


mapper = PythonMapper(module='pysimultanui')
method_mapper.mapper = mapper
mapper.method_mapper = method_mapper

PySimultan2_config.logger.setLevel('DEBUG')
PySimultan2_config.set_default_mapper(mapper)

print('mapper:', mapper)
