import sys
import inspect
import traceback
from nicegui import events, ui, app

from PySimultan2.object_mapper import PythonMapper
from PySimultan2.simultan_object import SimultanObject
from PySimultan2.data_model import DataModel

from ..core.method_mapper import ArgumentDialog


def float_validator(val):
    try:
        float(val)
        return None
    except:
        return 'Value must be a float'


def int_validator(val):
    try:
        int(val)
        return None
    except:
        return 'Value must be an integer'


class IntegerInput(ui.number):

    def __init__(self, *args, **kwargs):
        super().__init__(*args,
                         validation=int_validator,
                         precision=0,
                         **kwargs)




class FloatInput(ui.number):
    def __init__(self, *args, **kwargs):
        super().__init__(*args,
                         validation=float_validator,
                         **kwargs)


async def create_new_component(cls: type[SimultanObject],
                               mapper:PythonMapper,
                               data_model: DataModel):
    try:
        init_fcn = cls.__bases__[1].__init__

        parameters = dict(inspect.signature(init_fcn).parameters)
        if set(parameters.keys()) - {'args', 'kwargs', 'self'}:
            res = await ArgumentDialog(name='Start API',
                                       description='Start API',
                                       mapper=mapper,
                                       fnc=init_fcn)
        else:
            res = {'ok': True, 'args': {}}

        if not res['ok']:
            return
    except Exception as e:
        error = '\n'.join(traceback.format_exception(*sys.exc_info()))
        ui.notify(f'Error getting arguments for method: {e}\n {error}')
        return

    try:
        new_item: SimultanObject = cls(data_model=data_model,
                                       object_mapper=mapper,
                                       **res['args']
                                       )
        new_item.name = f'New {cls.__name__}_{new_item.id}'
    except Exception as e:
        error = '\n'.join(traceback.format_exception(*sys.exc_info()))
        ui.notify(f'Error creating new item: {e}\n {error}')
        return

    return new_item
