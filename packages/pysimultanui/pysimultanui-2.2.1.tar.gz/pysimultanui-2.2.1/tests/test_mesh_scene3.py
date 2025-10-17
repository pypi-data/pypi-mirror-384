import os
from nicegui import ui, app
from nicegui.elements.scene import Scene as NGScene
from PySimultanUI.src.pysimultanui.geometry_3d.scene import ExtendedScene
from PySimultanUI.src.pysimultanui.geometry_3d.three_views import (display_vertices,
                                                                   display_edges,
                                                                   display_wire,
                                                                   display_face,
                                                                   display_solid)

import numpy as np

import FreeCAD
import Part as FCPart

# Define your vertices and indices
vertices = np.array([
    [0, 0, 0],
    [1, 0, 0],
    [1, 1, 0],
    [0, 1, 0]
], dtype=float).flatten()

indices = np.array([
    0, 1, 2,
    0, 2, 3
], dtype=int)


@ui.page('/3d_test')
def index_page1() -> None:
    with ui.card():
        ui.label('3D Test')
        with ExtendedScene().classes('w-full h-full') as scene:
            vertices = np.array([
                [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1],
                [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
            ], dtype=float)
            indices = np.array([[0, 1, 2,],
                                [0, 2, 3],
                                [4, 5, 6],
                                [4, 6, 7],
                                [0, 4, 5],
                                [0, 5, 1],
                                [1, 5, 6],
                                [1, 6, 2],
                                [2, 6, 7],
                                [2, 7, 3],
                                [3, 7, 4],
                                [3, 4, 0]
                                ], dtype=int)
            # material_props = {'color': 0xff0000, 'wireframe': True}
            scene.curve([-4, 0, 0], [-4, -1, 0], [-3, -1, 0], [-3, 0, 0]).material('#008800')
            # scene.sphere().material('#4488ff')
            scene.mesh(vertices, indices).material('#4488ff')

            scene.wire(np.array([[-4, 0, 0], [-4, -1, 0], [-3, -1, 0], [-3, 0, 0]])).material('#ff0000')


storage_secret = os.environ.get('STORAGE_SECRET', 'my_secret6849')

# set_storage_secret(storage_secret)
ui.run(storage_secret=storage_secret,
       title='Py Simultan',
       dark=False,
       reload=True,
       port=8080,
       uvicorn_logging_level='info',
       )
