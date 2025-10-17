import os

from PySimultanUI.src.pysimultanui import user_manager, run_ui
from pysimultan_freecad.src.pysimultan_freecad import mapper, method_mapper, view_manager

project_dir = os.environ.get('PROJECT_DIR', '/simultan_projects')
if not os.path.exists(project_dir):
    os.makedirs(project_dir)

mapping = user_manager.mapper_manager.create_mapping(name='FreeCAD Toolbox')
mapping.mapper = mapper
mapping.method_mapper = method_mapper
mapping.view_manager = view_manager

run_ui()
print('Done!')
