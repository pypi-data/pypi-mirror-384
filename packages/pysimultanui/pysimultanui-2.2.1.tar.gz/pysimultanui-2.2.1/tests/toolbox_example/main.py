import os

from PySimultanUI.src.pysimultanui import run_ui, user_manager

from toolbox_1.mapping import mapper as mapper1, method_mapper as method_mapper1, view_manager as view_manager1
from toolbox_2.mapping import mapper as mapper2, method_mapper as method_mapper2, view_manager as view_manager2

project_dir = os.environ.get('PROJECT_DIR', '/simultan_projects')
if not os.path.exists(project_dir):
    os.makedirs(project_dir)


mapping = user_manager.mapper_manager.create_mapping(name='Toolbox 1',
                                                     mapper=mapper1,
                                                     method_mapper=method_mapper1,
                                                     view_manager=view_manager1)

mapping2 = user_manager.mapper_manager.create_mapping(name='Toolbox 2',
                                                      mapper=mapper2,
                                                      method_mapper=method_mapper2,
                                                      view_manager=view_manager2)

run_ui()
print('Done!')
