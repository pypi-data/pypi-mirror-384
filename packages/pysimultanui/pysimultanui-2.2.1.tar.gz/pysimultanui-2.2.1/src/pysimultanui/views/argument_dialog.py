from __future__ import annotations
import sys
import logging
import traceback
from nicegui import ui
from copy import copy
import typing
from typing import (Callable, Union, _GenericAlias, TYPE_CHECKING, Optional, Any, GenericAlias, Literal,
                    _LiteralGenericAlias, get_args, get_type_hints, reveal_type, _UnionGenericAlias, ForwardRef)
from PySimultan2 import PythonMapper
from functools import partial
import inspect
from enum import EnumType
from PySimultan2.simultan_object import SimultanObject
from nicegui.functions.refreshable import refreshable
from PySimultan2.default_types import ComponentList, ComponentDictionary
from PySimultan2.files import DirectoryInfo, FileInfo

from SIMULTAN.Data import SimId
from System import Guid

logger = logging.getLogger('pysimultan_ui')
logger.setLevel(logging.DEBUG)
# check if the logger has handlers, if not, add a StreamHandler
if not logger.hasHandlers():
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def create_backward_fcn(cls: type):

    class BackwardFcn(object):
        def __init__(self, *args, **kwargs):
            self.cls = kwargs.get('cls', cls)

        def __call__(self, x):
            if x is None:
                return None
            return next((instance for instance in self.cls.cls_instances
                         if f'{instance.name}_{instance.id}' == x),
                        None)

    backward_fcn = BackwardFcn(cls=cls)

    return lambda x: backward_fcn(x)


if TYPE_CHECKING:
    from ..core.method_mapper import UnmappedMethod, MappedMethod


class TypedList(ui.card):

    def __init__(self,
                 mapper: Optional[PythonMapper] = None,
                 parameter: Optional[inspect.Parameter] = None,
                 options: list[Any] = None,
                 value: list[Any] = None):

        ui.card.__init__(self)

        self.parameter = parameter
        self.mapper = mapper
        self.options = options if options is not None else []
        self.component_dict = {}
        self.card = None

        self.value = value

    @ui.refreshable
    def ui_content(self):
        with ui.list().classes('w-full') as item_card:
            if self.value is None:
                pass
            else:
                for i, value in enumerate(self.value):
                    with ListItem(index=i,
                                  parent=self).classes('w-full') as item:
                        pass

        ui.button('Add', icon='add', on_click=self.add).classes('bg-green-500 text-white')

    @property
    def list_options(self) -> dict[int, str]:
        self.component_dict = {}
        option_types = self.parameter.annotation.__args__
        options = {}
        for option_type in option_types:
            if option_type in self.mapper.registered_classes.values():
                mapped_cls = self.mapper.get_mapped_class_for_python_type(option_type)
            else:
                mapped_cls = option_type

            if isinstance(mapped_cls, _UnionGenericAlias):
                for cls in get_args(mapped_cls):
                    if cls in self.mapper.registered_classes.values():
                        mapped_cls = self.mapper.get_mapped_class_for_python_type(cls)
                    elif hasattr(cls, 'cls_instances'):
                        mapped_cls = cls

                    for instance in mapped_cls.cls_instances:
                        if hasattr(instance, 'id') and hasattr(instance, 'name'):
                            options[instance.id.LocalId] = f'{instance.name}, ID: {instance.id.LocalId}'
                            self.component_dict[instance.id.LocalId] = instance
                        elif instance.__class__ in (DirectoryInfo, FileInfo):
                            options[instance.key] = instance.__repr__()
                            self.component_dict[instance.key] = instance
                        else:
                            options[instance.id.LocalId] = instance.__repr__()
                            self.component_dict[instance.id.LocalId] = instance


            else:
                for instance in mapped_cls.cls_instances:
                    options[instance.id.LocalId] = f'{instance.name}, ID: {instance.id.LocalId}'
                    self.component_dict[instance.id.LocalId] = instance

        return options

    def __enter__(self):
        self.default_slot.__enter__()
        self.ui_content()
        return self

    async def add(self):
        list_options = self.list_options

        with ui.dialog() as dialog, ui.card():
            ui.label(f'Add new item')
            select_component = ui.select(options=list_options,
                                         clearable=True,
                                         value=None,
                                         with_input=False).classes('w-full')

            with ui.row():
                ui.button('OK', on_click=lambda: dialog.submit({'ok': True,
                                                                'component': select_component})

                          )
                ui.button('Cancel', on_click=lambda: dialog.submit({'ok': False}))

        result = await dialog
        if result is None:
            return
        if result['ok']:
            if self.value is None:
                self.value = []
            self.value.append(self.component_dict[result['component'].value])
            self.ui_content.refresh()


class ListItem(ui.card):

    def __init__(self,
                 index: int,
                 parent: TypedList):

        ui.card.__init__(self)

        self.parent = parent
        self.index = index
        self.card = None

    @property
    def item_value(self):
        return self.parent.value[self.index]

    @item_value.setter
    def item_value(self, value):
        self.parent.value[self.index] = value

    @ui.refreshable
    def ui_content(self):

        with ui.list().classes('w-full'):
            with ui.item().classes('w-full'):
                with ui.item_section().classes('w-full'):
                    ui.label(f'{self.index}').classes('text-bold')
                with ui.item_section().classes('w-full'):

                    options = self.parent.list_options
                    if self.item_value.id.LocalId not in options.keys():
                        options[self.item_value.id.LocalId] = f'{self.item_value.name}, ID: {self.item_value.id.LocalId}'
                        self.style(add='border: 2px solid red')
                    else:
                        self.style(remove='border: 2px solid red')

                    ui.select(label=f'Item {self.index}',
                              options=options,
                              value=self.item_value.id.LocalId,
                              on_change=partial(self.item_changed),
                              with_input=False).classes('w-full')
                with ui.item_section().classes('w-full'):
                    ui.button(icon='delete', on_click=partial(self.delete)).classes('q-ml-auto').props('color=red')

    def item_changed(self, x):
        if x.value is None:
            return
        print(f'setting value to {self.parent.component_dict[int(x.value)]} at index {self.index}')
        self.parent.value[self.index] = self.parent.component_dict[int(x.value)]
        if not self.parent.value[self.index] == self.parent.component_dict[int(x.value)]:
            raise ValueError('Value not set correctly')
        self.ui_content.refresh()
        self.parent.ui_content.refresh()

    def delete(self):
        del self.parent.value[self.index]
        self.parent.ui_content.refresh()

    def __enter__(self):
        self.default_slot.__enter__()
        self.ui_content()
        return self


class CombinedInput:

    def __init__(self,
                 key: str,
                 fcn_args: Union[dict[str, Any], Any],  # function arguments to be passed to the function
                 mapper: Optional[PythonMapper] = None,
                 parameter: Optional[inspect.Parameter] = None,  # parameter to be passed to the function
                 options: Optional[dict[str, Any]] = None,  # options for the input field
                 *args,
                 **kwargs):

        from ..core.edit_dialog import ContentEditDialog

        self.key = key
        self.parameter = parameter
        self.options = options if options is not None else {}
        self.fcn_args = fcn_args
        self.mapper = mapper
        self.args = args
        self.kwargs = kwargs

        if self.options and self.options.get('default', None) is not None:
            self.fcn_args[self.key] = self.options['default']
        else:
            if self.parameter is not None:
                self.fcn_args[self.key] = self.parameter.default if self.parameter.default != inspect._empty else None

        self.parameter_type_select = None


        self.content_edit_dialog = ContentEditDialog()

    @ui.refreshable
    def ui_content(self):

        reveal_type(self.parameter.annotation)

        if get_args(self.parameter.annotation):
            if self.parameter.annotation.__origin__ is Literal:
                StringInput(key=self.key,
                            parameter=self.parameter,
                            options=dict(zip(get_args(self.parameter.annotation), get_args(self.parameter.annotation))),
                            fcn_args=self.fcn_args,
                            mapper=self.mapper).ui_content()
            elif self.parameter.annotation.__origin__ is list or self.parameter.annotation.__origin__ is typing.List:

                ComponentList = self.mapper.get_mapped_class('ComponentList')

                options = dict(zip([None, *[x.id.LocalId for x in ComponentList.cls_instances]],
                                   ['None', *[f'{x.name}; ID: {x.id.LocalId}' for x in ComponentList.cls_instances]],
                                   ))

                def selection_changed(e):
                    if e.value is None:
                        self.fcn_args[self.key] = None
                    else:
                        self.fcn_args[self.key] = ComponentList._cls_instances_dict[
                            SimId(self.mapper.current_data_model.project.GlobalID, int(e.value))]
                    self.ui_content.refresh()

                ui.select(label='Select list',
                          options=options,
                          value=self.fcn_args[self.key].id.LocalId if self.fcn_args[self.key] is not None else None,
                          on_change=lambda e: selection_changed(e),
                          with_input=False).classes("min-width-80 w-1/3")

                if self.fcn_args[self.key] is None:
                    self.fcn_args[self.key] = self.parameter.default

                if self.fcn_args[self.key] is None:
                    ui.label('None').classes('w-1/3')
                else:
                    with TypedList(mapper=self.mapper,
                                   parameter=self.parameter,
                                   options=self.options.get(self.key, []),
                                   value=self.fcn_args[self.key]).classes('w-full') as typed_list_element:
                        pass

                async def create_new_list(*args, **kwargs):
                    with ui.dialog() as dialog, ui.card():
                        ui.label('Create new list')
                        name_input = ui.input('Name').classes('w-full')
                        with ui.row():
                            ui.button('OK', on_click=lambda e: dialog.submit({'ok': True,
                                                                              'name': name_input.value}))
                            ui.button('Cancel', on_click=lambda e: dialog.submit({'ok': False}))

                    result = await dialog
                    if result is None:
                        return

                    if result['ok']:
                        new_list = ComponentList(name=result['name'])
                        self.fcn_args[self.key] = new_list
                        self.ui_content.refresh()

                with ui.button(icon='add', on_click=lambda e: create_new_list(e)).classes('q-ml-auto') as add_button:
                    ui.tooltip('Create new list')

            else:
                with ui.row().classes('w-full'):

                    options = {}
                    for option in get_args(self.parameter.annotation):
                        if hasattr(option, '__origin__') and option.__origin__ is Literal:
                            options[id(Literal)] = 'Literal'
                        else:
                            if isinstance(option, ForwardRef):
                                self.mapper.registered_classes(option.__forward_arg__)


                                options = option._evaluate(globals(), locals(), {})
                            else:
                                options[id(option)] = option.__name__ if hasattr(option, '__name__') else option

                    value = id(type(self.parameter.default)) if self.parameter.default != None else id(type(None))

                    if id(type(value)) not in options.keys():
                        for param in get_args(self.parameter.annotation):
                            if type(self.parameter.default) in [type(x) for x in get_args(param)]:
                                if hasattr(param, '__origin__') and param.__origin__ is Literal:
                                    value = id(Literal)
                                else:
                                    value = id(param)
                                break

                    if id(type(self.parameter.default)) not in options.keys():
                        options[id(type(self.parameter.default))] = type(self.parameter.default).__name__ if hasattr(type(self.parameter.default), '__name__') else type(self.parameter.default).__repr__()

                    self.parameter_type_select = ui.select(label='Type',
                                                           options=options,
                                                           value=value,
                                                           with_input=False).classes("min-width-80 w-1/3")
                    self.value_edit_dialog()
                    self.parameter_type_select.on_value_change(self.value_edit_dialog.refresh)

        else:
            ui.label('Combined input')

    def __repr__(self):
        return f'CombinedInput({self.key})'

    @refreshable
    def value_edit_dialog(self):

        if self.parameter_type_select.value in select_value_lookup.keys():
            select_value_lookup[self.parameter_type_select.value](key=self.key,
                                                                  parameter=self.parameter,
                                                                  options=self.options.get(self.key, {}),
                                                                  fcn_args=self.fcn_args,
                                                                  mapper=self.mapper).ui_content()
            return

        elif self.parameter_type_select.value in [id(x) for x in self.mapper.registered_classes.values()]:

            taxonomy = next((taxonomy for taxonomy, cls  in self.mapper.registered_classes.items() if id(cls) == self.parameter_type_select.value), None)
            mapped_cls = self.mapper.get_mapped_class(taxonomy)

            ComponentInput(key=self.key,
                           parameter=self.parameter,
                           options=self.options.get(self.key, {}),
                           fcn_args=self.fcn_args,
                           cls=mapped_cls,
                           mapper=self.mapper).ui_content()
            return
        elif self.parameter_type_select.value in [id(x) for x in self.mapper.mapped_classes.values()]:
            mapped_cls = next((cls for cls in self.mapper.mapped_classes.values() if id(cls) == self.parameter_type_select.value), None)
            ComponentInput(key=self.key,
                           parameter=self.parameter,
                           options=self.options.get(self.key, {}),
                           fcn_args=self.fcn_args,
                           cls=mapped_cls,
                           mapper=self.mapper).ui_content()
            return
        elif self.parameter_type_select.value == id(Literal):
            literal = None
            while literal is None:
                opts = get_args(self.parameter.annotation)
                for opt in opts:
                    if isinstance(opt, _LiteralGenericAlias):
                        literal = opt
                        break

            StringInput(key=self.key,
                        parameter=self.parameter,
                        options=dict(zip(get_args(literal), get_args(literal))),
                        fcn_args=self.fcn_args,
                        mapper=self.mapper).ui_content()
            return
        else:
            return

        if self.parameter_type_select.value == 'NoneType':
            self.fcn_args[self.key] = None
            ui.input(label=self.key,
                     value='None').disable()
        if self.parameter_type_select.value == 'str':
            StringInput(key=self.key,
                        parameter=self.parameter,
                        options=self.options.get(self.key, {}),
                        fcn_args=self.fcn_args,
                        mapper=self.mapper).ui_content()
        elif self.parameter_type_select.value == 'int':
            IntegerInput(key=self.key,
                         parameter=self.parameter,
                         options=self.options.get(self.key, {}),
                         fcn_args=self.fcn_args,
                         mapper=self.mapper).ui_content()
        elif self.parameter_type_select.value == 'float':
            FloatInput(key=self.key,
                       parameter=self.parameter,
                       options=self.options.get(self.key, {}),
                       fcn_args=self.fcn_args,
                       mapper=self.mapper).ui_content()
        elif self.parameter_type_select.value == 'bool':
            BooleanInput(key=self.key,
                         parameter=self.parameter,
                         options=self.options.get(self.key, {}),
                         fcn_args=self.fcn_args,
                         mapper=self.mapper).ui_content()
        elif self.parameter_type_select.value == 'list':
            ComponentListInput(key=self.key,
                               parameter=self.parameter,
                               options=self.options.get(self.key, {}),
                               fcn_args=self.fcn_args,
                               mapper=self.mapper).ui_content()
        elif self.parameter_type_select.value == 'dict':
            ComponentDictInput(key=self.key,
                               parameter=self.parameter,
                               options=self.options.get(self.key, {}),
                               fcn_args=self.fcn_args,
                               mapper=self.mapper).ui_content()
        elif self.parameter_type_select.value == 'enum':
            EnumInput(key=self.key,
                      parameter=self.parameter,
                      options=self.options.get(self.key, {}),
                      fcn_args=self.fcn_args,
                      mapper=self.mapper).ui_content()
        elif self.parameter_type_select.value == 'Literal':
            literal = None
            while literal is None:
                opts = get_args(self.parameter.annotation)
                for opt in opts:
                    if isinstance(opt, _LiteralGenericAlias):
                        literal = opt
                        break

            StringInput(key=self.key,
                        parameter=self.parameter,
                        options=dict(zip(get_args(literal), get_args(literal))),
                        fcn_args=self.fcn_args,
                        mapper=self.mapper).ui_content()

        elif self.parameter_type_select.value in self.mapper.registered_classes.keys():
            ComponentInput(key=self.key,
                           parameter=self.parameter,
                           options=self.options.get(self.key, {}),
                           fcn_args=self.fcn_args,
                           cls=self.mapper.get_mapped_class(self.parameter_type_select.value),
                           mapper=self.mapper).ui_content()

        elif self.parameter_type_select.value in self.mapper.registered_classes.values():
            taxonomy = next((key for key, cls in self.mapper.registered_classes.items() if
                             cls == self.parameter_type_select.value), None)
            try:
                ComponentInput(key=self.key,
                               parameter=self.parameter,
                               options=self.options.get(self.key, {}),
                               fcn_args=self.fcn_args,
                               cls=self.mapper.get_mapped_class(taxonomy),
                               mapper=self.mapper).ui_content()
            except Exception as e:
                print(f'Error displaying edges: {e}\n')
                print('\n'.join(traceback.format_exception(*sys.exc_info())))

                logger.error(f'Error displaying edges: {e}\n'
                             f'{traceback.format_exception(*sys.exc_info())}')
                raise e


class ParameterInput:

    def __init__(self,
                 key: str,
                 fcn_args: Union[dict[str, Any], Any],  # function arguments to be passed to the function
                 mapper: Optional[PythonMapper] = None,
                 parameter: Optional[inspect.Parameter] = None,  # parameter to be passed to the function
                 options: Optional[dict[str, Any]] = None,  # options for the input field
                 *args,
                 **kwargs):

        self.key = key
        self.parameter = parameter
        self.options = options if options is not None else {}
        self.fcn_args = fcn_args
        self.mapper = mapper
        self.args = args
        self.kwargs = kwargs

        if self.options and self.options.get('default', None) is not None:
            self.fcn_args[self.key] = self.options['default']
        else:
            if self.parameter is not None:
                self.fcn_args[self.key] = self.parameter.default if self.parameter.default != inspect._empty else None

    def ui_content(self):
        pass


class BooleanInput(ParameterInput):

    def ui_content(self):
        ui.checkbox(text=self.key).bind_value(self.fcn_args,
                                              self.key).classes('w-full')


class NoneTypeInput(ParameterInput):

    def ui_content(self):
        self.fcn_args[self.key] = None
        ui.input(label=self.key,
                 value='None').disable()


class IntegerInput(ParameterInput):

    def ui_content(self):
        ui.input(label=self.key,
                 validation=self.validate).bind_value(self.fcn_args,
                                                      self.key,
                                                      forward=lambda x: int(x) if x is not None else None,
                                                      backward=lambda x: str(x) if x is not None else None,
                                                      ).classes('w-full')

    @staticmethod
    def validate(x):
        try:
            int(x)
        except Exception as e:
            return 'Not an integer'


class FloatInput(ParameterInput):

    def ui_content(self):

        def forward(x):
            try:
                return float(x)
            except Exception as e:
                return None

        def backward(x):
            try:
                return str(x)
            except Exception as e:
                return None

        ui.input(label=self.key,
                 validation=self.validate).bind_value(self.fcn_args,
                                                      self.key,
                                                      forward=lambda x: forward(x) if x is not None else None,
                                                      backward=lambda x: backward(x) if x is not None else None,
                                                      ).classes('w-full')

    @staticmethod
    def validate(x):
        try:
            float(x)
        except Exception as e:
            return 'Not a float'


class StringInput(ParameterInput):

    @property
    def default_value(self):
        return list(self.options.keys())[0] if self.options else None

    def ui_content(self):
        if self.options:
            ui.select(label=self.key,
                      options=self.options,
                      value=self.default_value,
                      with_input=False).bind_value(self.fcn_args,
                                                   self.key).classes('w-full')
        else:
            ui.input(label=self.key).bind_value(self.fcn_args,
                                                self.key).classes('w-full')


class EnumInput(ParameterInput):

    @property
    def value_options(self):
        return {x.value: x.name for x in [*self.parameter.annotation]}

    @property
    def default_value(self):
        self.fcn_args[self.key] = self.parameter.default.name if self.parameter.default != inspect._empty else None
        return self.fcn_args[self.key]

    def ui_content(self):
        self.fcn_args[self.key] = self.parameter.default.name if self.parameter.default != inspect._empty else None

        ui.select(label=self.key,
                  options=self.value_options,
                  value=self.default_value,
                  with_input=False).bind_value(self.fcn_args,
                                               self.key,
                                               forward=lambda x: self.parameter.annotation[x],
                                               backward=lambda x: x.value if x is not None else None,
                                               ).classes('w-full')


class ComponentInput(ParameterInput):

    def __init__(self,
                 key: str,
                 fcn_args: Union[dict[str, Any], Any],  # function arguments to be passed to the function
                 mapper: Optional[PythonMapper] = None,
                 parameter: Optional[inspect.Parameter] = None,  # parameter to be passed to the function
                 options: Optional[dict[str, Any]] = None,  # options for the input field
                 cls: type(SimultanObject) = None,
                 *args,
                 **kwargs):
        super().__init__(key=key,
                         parameter=parameter,
                         options=options,
                         fcn_args=fcn_args,
                         mapper=mapper,
                         *args,
                         **kwargs)
        self.cls: SimultanObject = cls
        self._value_options = None

    @property
    def value_options(self):
        if self._value_options is None:
            try:
                options = {}
                if self.options:
                    if 'options' in self.options.keys():
                        for option in self.options.get('options', []):
                            options[f'{option.name}_{option.id}'] = option

                    elif 'classes' in self.options.keys():
                        for cls in self.options.get('classes', []):
                            try:
                                if cls in self.mapper.registered_classes.values():
                                    mapped_cls = self.mapper.get_mapped_class_for_python_type(cls)
                                else:
                                    mapped_cls = cls
                                for instance in mapped_cls.cls_instances:
                                    options[f'{instance.name}_{instance.id}'] = instance
                            except Exception as e:
                                continue
                else:
                    if self.cls is not None:
                        classes = [self.cls]
                    else:
                        classes = self.mapper.mapped_classes.values()

                    for mapped_cls in classes:
                        for instance in mapped_cls.cls_instances:
                            options[f'{instance.name}_{instance.id}'] = instance
                self._value_options = options
            except Exception as e:
                print(traceback.format_exception(*sys.exc_info()))
                raise e
        return self._value_options

    def ui_content(self):

        if self.parameter.default is not inspect._empty:
            if not isinstance(self.parameter.default, SimultanObject):
                value = None
            else:
                value = f'{self.parameter.default.name}_{self.parameter.default.id}'
        else:
            value = None

        ui.select(label=f'{self.key} ({self.cls._taxonomy if self.cls is not None else "Any"})',
                  options=list(self.value_options.keys()),
                  value=value,
                  with_input=True).bind_value(self.fcn_args,
                                              self.key,
                                              backward=self.backward_fcn,
                                              forward=self.forward_fcn
                                              ).classes('w-full')

    @staticmethod
    def backward_fcn(x: Optional[SimultanObject]):
        if hasattr(x, 'name') and hasattr(x, 'id'):
            return f'{x.name}_{x.id}' if x is not None else ''
        else:
            return x.__repr__()

    def forward_fcn(self, x: Optional[str]):
        if x in (None, 'None', ''):
            return None
        return self.value_options[x]


class ComponentListInput(ComponentInput):

    def __init__(self, *args, **kwargs):
        super().__init__(cls=kwargs.get('mapper').get_mapped_class('ComponentList'),
                         *args,
                         **kwargs)


class ComponentDictInput(ComponentInput):

    def __init__(self, *args, **kwargs):
        super().__init__(cls=kwargs.get('mapper').get_mapped_class('ComponentDict'),
                         *args,
                         **kwargs)


class DirectoryInfoInput(ComponentInput):

    def __init__(self, *args, **kwargs):
        super().__init__(cls=DirectoryInfo,
                         *args,
                         **kwargs)

    @property
    def value_options(self):
        if self._value_options is None:
            try:
                options = {}
                if self.options:
                    if 'options' in self.options.keys():
                        for option in self.options.get('options', []):
                            options[f'{option.__repr__()}'] = option

                    elif 'classes' in self.options.keys():
                        for cls in self.options.get('classes', []):
                            try:
                                if cls in self.mapper.registered_classes.values():
                                    mapped_cls = self.mapper.get_mapped_class_for_python_type(cls)
                                else:
                                    mapped_cls = cls
                                for instance in mapped_cls.cls_instances:
                                    options[f'{instance.__repr__()}'] = instance
                            except Exception as e:
                                continue
                else:
                    if self.cls is not None:
                        classes = [self.cls]
                    else:
                        classes = self.mapper.mapped_classes.values()

                    for mapped_cls in classes:
                        for instance in mapped_cls.cls_instances:
                            options[f'{instance.__repr__()}'] = instance
                self._value_options = options
            except Exception as e:
                print(traceback.format_exception(*sys.exc_info()))
                raise e
        return self._value_options

    def ui_content(self):

        if self.parameter.default is inspect._empty:
            value = None
        elif self.parameter.default is None:
            value = None
        else:
            value = f'{self.parameter.default.name}_{self.parameter.default.id}'

        ui.select(label=f'{self.key} ({self.cls._taxonomy if self.cls is not None else "Any"})',
                  options=list(self.value_options.keys()),
                  value=value,
                  with_input=True).bind_value(self.fcn_args,
                                              self.key,
                                              backward=self.backward_fcn,
                                              forward=self.forward_fcn
                                              ).classes('w-full')


class FileInfoInput(ComponentInput):

    def __init__(self, *args, **kwargs):
        super().__init__(cls=FileInfo,
                         *args,
                         **kwargs)

    @property
    def value_options(self):
        if self._value_options is None:
            try:
                options = {}
                if self.options:
                    if 'options' in self.options.keys():
                        for option in self.options.get('options', []):
                            options[f'{option.__repr__()}'] = option

                    elif 'classes' in self.options.keys():
                        for cls in self.options.get('classes', []):
                            try:
                                if cls in self.mapper.registered_classes.values():
                                    mapped_cls = self.mapper.get_mapped_class_for_python_type(cls)
                                else:
                                    mapped_cls = cls
                                for key, file_info in mapped_cls._cls_instances.items():
                                    options[f'FileInfo {file_info.name} ({key})'] = file_info
                            except Exception as e:
                                continue
                else:
                    if self.cls is not None:
                        classes = [self.cls]
                    else:
                        classes = self.mapper.mapped_classes.values()

                    for mapped_cls in classes:
                        for key, file_info in mapped_cls._cls_instances.items():
                            options[f'FileInfo {file_info.name} ({key})'] = file_info
                self._value_options = options
            except Exception as e:
                print(traceback.format_exception(*sys.exc_info()))
                raise e
        return self._value_options

    @property
    def ui_content(self):

        if self.parameter.default is inspect._empty:
            value = None
        elif self.parameter.default is None:
            value = None
        else:
            value = f'{self.parameter.default.name}_{self.parameter.default.id}'

        ui.select(label=f'{self.key} ({self.cls._taxonomy if self.cls is not None else "Any"})',
                  options=list(self.value_options.keys()),
                  value=value,
                  with_input=True).bind_value(self.fcn_args,
                                              self.key,
                                              backward=self.backward_fcn,
                                              forward=self.forward_fcn
                                              ).classes('w-full')

    @staticmethod
    def backward_fcn(x: Optional[FileInfo]):

        if hasattr(x, 'name') and hasattr(x, 'key'):
            return f'FileInfo {x.name} ({x.key})' if x is not None else ''
        else:
            return x.__repr__()

    def forward_fcn(self, x: Optional[str]):
        if x in (None, 'None', ''):
            return None
        return self.value_options[x]


class AnyInput(ParameterInput):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parameter_type_select = None

    def ui_content(self):

        options = {id(int): 'int',
                   id(float): 'float',
                   id(str): 'str',
                   id(bool): 'bool',
                   id(list): 'list',
                   id(dict): 'dict',
                   id(DirectoryInfo): 'DirectoryInfo',
                   id(FileInfo): 'FileInfo',
                   id('Component'): 'Component',
                   id(type(None)): 'None'}

        if self.parameter.default is not inspect._empty:
            value = id(type(self.parameter.default))
        else:
            value = id(type(None))

        def selection_changed(e):
            choice = options[e.value]
            self.value_edit_dialog.refresh()

        self.parameter_type_select = ui.select(label='Type',
                                               options=options,
                                               value=value,
                                               with_input=False,
                                               on_change=selection_changed).classes("min-width-80 w-1/3")

        self.value_edit_dialog()

    @ui.refreshable
    def value_edit_dialog(self):
        if self.parameter_type_select.value in select_value_lookup.keys():
            select_value_lookup[self.parameter_type_select.value](key=self.key,
                                                                  parameter=self.parameter,
                                                                  options=self.options.get(self.key, {}),
                                                                  fcn_args=self.fcn_args,
                                                                  mapper=self.mapper).ui_content()
            return


input_lookup = {int: IntegerInput,
                float: FloatInput,
                str: StringInput,
                bool: BooleanInput,
                list: ComponentListInput,
                dict: ComponentDictInput,
                Any: AnyInput}


class ArgumentDialog(ui.dialog):

    def __init__(self,
                 name: str = None,
                 description: str = None,
                 mapper: PythonMapper = None,
                 fnc: Callable = None,
                 method: Union['UnmappedMethod', 'MappedMethod'] = None,
                 options: Optional[dict[Any, Any]] = None,
                 additional_parameters: Optional[dict[Any, inspect.Parameter]] = None,
                 **kwargs):

        """

        :param name:
        :param description:
        :param mapper:
        :param fnc:
        :param method:
        :param options: Example: {'arg1': {'default': 1,
                                           'options': [1, 5, 7]},
                                  'arg2': {'default': 'test'},
                                           'options': ['opt1', 'opt2', 'opt3']
                                           }
                                  'arg2': {'default': 'test'},
                                           'classes': [type1, type2, type3]
                                           }
                                  }
        :param kwargs:
        """

        if options is None:
            options = {}

        if name is None:
            name = method.name

        if description is None:
            description = method.description

        if mapper is None:
            mapper: PythonMapper = method.user.mapper

        if fnc is None:
            fnc = method.method

        super().__init__(value=True)
        self.props("fullWidth fullHeight")

        self.fcn_args = {}
        parameters = dict(inspect.signature(fnc).parameters)

        if additional_parameters is not None:
            parameters.update(additional_parameters)

        with self, ui.card().classes('w-full h-full'):
            ui.label(f'Edit method arguments for {name}').classes('text-h5')

            ui.label(description).classes('text-caption')

            with ui.row():
                ui.button('OK', on_click=lambda e: self.submit({'ok': True, 'args': copy(self.fcn_args)}))
                ui.button('Cancel', on_click=lambda e: self.submit({'ok': False}))

            with ui.list().classes('w-full border-top border-bottom').props('bordered separator'):

                for key, parameter in parameters.items():
                    if key in ('args', 'kwargs', 'self'):
                        continue

                    try:
                        cls = None

                        with ui.item():
                            with ui.item_section():
                                with ui.item_section():
                                    ui.label(key).classes('text-bold').style('color: blue')
                                with ui.item_section():
                                    if hasattr(parameter.annotation, '__name__'):
                                        if parameter.annotation.__name__ == 'Optional':
                                            ui.label(f"{[x.__name__ if hasattr(x, '__name__') else str(x) for x in get_args(parameter.annotation)]}")
                                        else:
                                            ui.label(str(parameter.annotation.__name__))
                                    else:
                                        ui.label(str(parameter.annotation))
                            with ui.item_section().classes('w-full'):
                                logger.debug(f'Creating input for {key} with parameter {parameter}')
                                self.create_parameter_input(key, parameter, options, mapper)
                    except Exception as e:
                        print(f'Error displaying edges: {e}\n')
                        print(traceback.format_exception(*sys.exc_info()))

                        logger.error(f'Error displaying edges: {e}\n'
                                     f'{traceback.format_exception(*sys.exc_info())}')
                        raise e

    def create_parameter_input(self,
                               key: str,
                               parameter: inspect.Parameter,
                               options: dict[str, Any],
                               mapper: PythonMapper):

        if parameter.annotation is inspect._empty:
            AnyInput(key=key,
                     parameter=parameter,
                     options=options.get(key, {}),
                     fcn_args=self.fcn_args,
                     mapper=mapper).ui_content()
            return

        if get_args(parameter.annotation):
            CombinedInput(key=key,
                          parameter=parameter,
                          options=options.get(key, {}),
                          fcn_args=self.fcn_args,
                          mapper=mapper).ui_content()
            return

        if parameter.annotation in input_lookup.keys():
            input_lookup[parameter.annotation](key=key,
                                               parameter=parameter,
                                               options=options.get(key, {}),
                                               fcn_args=self.fcn_args,
                                               mapper=mapper).ui_content()
            return


        if parameter.annotation is int:
            IntegerInput(key=key,
                         parameter=parameter,
                         options=options.get(key, {}),
                         fcn_args=self.fcn_args,
                         mapper=mapper).ui_content()
            return
        elif parameter.annotation is float:
            FloatInput(key=key,
                       parameter=parameter,
                       options=options.get(key, {}),
                       fcn_args=self.fcn_args,
                       mapper=mapper).ui_content()
            return
        elif isinstance(parameter.annotation, EnumType):
            EnumInput(key=key,
                      parameter=parameter,
                      options=options.get(key, {}),
                      fcn_args=self.fcn_args,
                      mapper=mapper).ui_content()
            return
        elif parameter.annotation is bool:
            BooleanInput(key=key,
                         parameter=parameter,
                         options=options.get(key, {}),
                         fcn_args=self.fcn_args,
                         mapper=mapper).ui_content()
            return
        elif parameter.annotation is str:
            StringInput(key=key,
                        parameter=parameter,
                        options=options.get(key, {}),
                        fcn_args=self.fcn_args,
                        mapper=mapper).ui_content()
            return
        elif parameter.annotation is list or parameter.annotation is typing.List:
            ComponentListInput(key=key,
                               parameter=parameter,
                               options=options.get(key, {}),
                               fcn_args=self.fcn_args,
                               mapper=mapper).ui_content()
            return
        elif parameter.annotation is dict or parameter.annotation is typing.Dict:
            ComponentDictInput(key=key,
                               parameter=parameter,
                               options=options.get(key, {}),
                               fcn_args=self.fcn_args,
                               mapper=mapper).ui_content()
            return
        elif parameter.annotation in mapper.registered_classes.keys():
            ComponentInput(key=key,
                           parameter=parameter,
                           options=options.get(key, {}),
                           fcn_args=self.fcn_args,
                           cls=mapper.get_mapped_class(parameter.annotation),
                           mapper=mapper).ui_content()
            return
        elif parameter.annotation in mapper.registered_classes.values():
            taxonomy = next((key for key, cls in mapper.registered_classes.items() if
                             cls == parameter.annotation), None)
            try:
                ComponentInput(key=key,
                               parameter=parameter,
                               options=options.get(key, {}),
                               fcn_args=self.fcn_args,
                               cls=mapper.get_mapped_class(taxonomy),
                               mapper=mapper).ui_content()
            except Exception as e:
                print(f'Error displaying edges: {e}\n')
                print('\n'.join(traceback.format_exception(*sys.exc_info())))

                logger.error(f'Error displaying edges: {e}\n'
                             f'{traceback.format_exception(*sys.exc_info())}')
                raise e
        elif isinstance(parameter.annotation, _GenericAlias) or isinstance(parameter.annotation, GenericAlias):
            if parameter.annotation.__origin__ is list or parameter.annotation.__origin__ is typing.List:
                ComponentListInput(key=key,
                                   parameter=parameter,
                                   options=options.get(key, {}),
                                   fcn_args=self.fcn_args,
                                   mapper=mapper).ui_content()
                return
            elif parameter.annotation.__origin__ is dict or parameter.annotation.__origin__ is typing.Dict:
                ComponentDictInput(key=key,
                                   parameter=parameter,
                                   options=options.get(key, {}),
                                   fcn_args=self.fcn_args,
                                   mapper=mapper).ui_content()
            elif parameter.annotation.__origin__ is Literal:
                StringInput(key=key,
                            parameter=parameter,
                            options=dict(zip(get_args(parameter.annotation), get_args(parameter.annotation))),
                            fcn_args=self.fcn_args,
                            mapper=mapper).ui_content()
                return
            elif parameter.annotation.__origin__ is Union:
                raise NotImplementedError(
                    f'Unions are not supported yet. Please use CombinedInput for {key} with parameter {parameter}')

        if hasattr(parameter.annotation, '__bases__'):
            if SimultanObject in parameter.annotation.__bases__:
                ComponentInput(key=key,
                               parameter=parameter,
                               options=options.get(key, {}),
                               fcn_args=self.fcn_args,
                               cls=mapper.mapped_classes.get(parameter.annotation._taxonomy, None),
                               mapper=mapper).ui_content()
        else:
            ComponentInput(key=key,
                           parameter=parameter,
                           options=options.get(key, {}),
                           fcn_args=self.fcn_args,
                           cls=None,
                           mapper=mapper).ui_content()


select_value_lookup = {id(type(None)): NoneTypeInput,
                       id(int): IntegerInput,
                       id(float): FloatInput,
                       id(str): StringInput,
                       id(bool): BooleanInput,
                       id(list): ComponentListInput,
                       id(dict): ComponentDictInput,
                       id(EnumType): EnumInput,
                       id(DirectoryInfo): DirectoryInfoInput,
                       id(FileInfo): FileInfoInput,
                       id('Component'): ComponentInput,
                       id(Any): AnyInput
                       }
