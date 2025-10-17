
# pysimultanui - PySimultan User Interface

Python library for creating simple user interfaces 
for PySimultan


![img.png](resources/screen.png)

## Installation

pysimultanui can be installed using pip:

```bash
pip install pysimultanui
```

## Usage

### Running the UI

In the command line, run the following command:

```bash
pysimultanui_run
```

To view the help message, run the following command:

```bash
pysimultanui_run --help
```




# Adding Toolboxes

PySimultanUI allows you to add toolboxes to the UI. The toolboxes are installed and imported as Python packages.

The package can be included in the UI by creating a new mapping and adding the mapper, method_mapper and view_manager 
to the mapping:


```python
from pysimultanui import user_manager, run_ui
from my_new_package import mapper, method_mapper, view_manager

mapping = user_manager.mapper_manager.create_mapping(name='FreeCAD Toolbox')
mapping.mapper = mapper
mapping.method_mapper = method_mapper
mapping.view_manager = view_manager

run_ui()
```

As shown in the example above, a mapping is created with the name 'FreeCAD Toolbox'. The mapper, method_mapper and 
view_manager of the package are then added to the mapping. The UI is then run using the run_ui() function.

- The mapper is used to map the class to be used in the UI.
- The method_mapper is used to map the methods of the class to be used in the UI. (optional)
- The view_manager is used to create the view of the class in the UI. (optional)


# Importing toolboxes in the UI

The toolboxes can be imported in the UI by clicking on the "Menu" -> "Add Toolbox" button in the UI. 
The toolboxes are imported as Python packages.

![img.png](resources/img.png)

If the package is missing, it will be installed automatically. Then, the mapper, method_mapper and view_manager
of the package are imported and added to a new mapping as shown in the previous section.



Example of a toolbox:


```python

import pysimultanui as psui
from PySimultan2.object_mapper import PythonMapper
from PySimultan2.taxonomy_maps import TaxonomyMap, Content

# example class to be mapped:
class ExampleClass:
    def __init__(self, *args, **kwargs):
        self.a = kwargs.get('a', None)
        self.b = kwargs.get('b', None)
        self.c = None

    def add(self):
        self.c = self.a + self.b

    def subtract(self):
        self.c = self.a - self.b

    def multiply(self):
        self.c = self.a * self.b


# create content and taxonomy map:
contents = {}

contents['a'] = Content(text_or_key='a_in_simultan',
                        property_name='a',
                        type=None,
                        unit=None,
                        documentation='Content a',
                        component_policy='subcomponent')

contents['b'] = Content(text_or_key='b_in_simultan',
                        property_name='b',
                        type=None,
                        unit=None,
                        documentation='Content b')

contents['c'] = Content(text_or_key='c_in_simultan',
                        property_name='c',
                        type=None,
                        unit=None,
                        documentation='Content c')

example_class_map = TaxonomyMap(taxonomy_name='PySimultanUI',
                                taxonomy_key='PySimultanUI',
                                taxonomy_entry_name='ExampleClass',
                                taxonomy_entry_key='ExampleClass',
                                content=[contents['a'],
                                         contents['b'],
                                         contents['c']
                                         ],
                                )

# get the mapper:
mapper = PythonMapper()

# register the class to be mapped:
mapper.register(example_class_map.taxonomy_entry_key,
                ExampleClass,
                taxonomy_map=example_class_map)


# register methods:
cls = mapper.get_mapped_class('ExampleClass')

# get the method mapper:
method_mapper = psui.MethodMapper()

method_mapper.register_method(cls=cls,
                              name='subtract',
                              method=cls.subtract,
                              args=[],
                              kwargs={})

method_mapper.register_method(cls=cls,
                              name='add',
                              method=cls.add,
                              args=[],
                              kwargs={})

method_mapper.register_method(cls=cls,
                              name='multiply',
                              method=cls.multiply,
                              args=[],
                              kwargs={})

if __name__ == '__main__':
    # run the UI if not imported as a package
    psui.run_ui()
```

## Method Mapper

The method mapper is used to map the methods of the class to be used in the UI. The method mapper is optional and can be
used to customize the methods of the class in the UI.

Example of a method mapper:

```python
from pysimultanui import MethodMapper

method_mapper = MethodMapper()

def my_first_method(*args, **kwargs):

    user = kwargs.get('user', None)
    data_model = kwargs.get('data_model', None)
    
    
method_mapper.register_method(
    name='My first method',
    method=my_first_method,
    add_data_model_to_kwargs=True,  # add the data model to the kwargs
    add_user_to_kwargs=True,        # add the user to the kwargs
    kwargs={'io_bound': False}      # add additional kwargs
)

```

Also typed methods can be registered:

```python
from pysimultanui import MethodMapper
from .mapper import mapper

method_mapper = MethodMapper()
example_class = mapper.get_mapped_class('ExampleClass'),

def my_first_method(
        arg2:str,
        arg3:float,
        arg4:example_class,
        arg1:int = 5,
        **kwargs):

    user = kwargs.get('user', None)
    data_model = kwargs.get('data_model', None)
    
    
method_mapper.register_method(
    name='My first method',
    method=my_first_method,
    add_data_model_to_kwargs=True,  # add the data model to the kwargs
    add_user_to_kwargs=True,        # add the user to the kwargs
    kwargs={'io_bound': False}      # add additional kwargs
)

```

The type hints of the method are used to create the input fields in the UI.


- add_data_model_to_kwargs: If True, the data model is added to the kwargs of the method. It is used to access the data
  model of the current user.
- add_user_to_kwargs: If True, the user is added to the kwargs of the method.
- kwargs: Additional kwargs to be added to the method. io_bound: If True, the method is run as an IO bound method in a separate thread. 
This is useful for long-running methods, but UI updates are not possible during the execution of the method.



## View Manager

The view manager is used to create the view of the class in the UI. The view manager is optional and can be used to
customize the view of the class in the UI.

Example of a view manager:

```python
from pysimultanui import ViewManager
from pysimultanui.views.component_detail_base_view import ComponentDetailBaseView

view_manager = ViewManager()

from nicegui import ui

class FeatureDetailView(ComponentDetailBaseView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @ui.refreshable
    def ui_content(self, *args, **kwargs):
        super().ui_content(*args, **kwargs)
        ui.label('This is a custom view for the class Feature')


# add the view to the view manager. The view is then used to create the view of instances with the taxonomy key '
# feature' in the UI.
view_manager.views['feature'] = FeatureDetailView

```
