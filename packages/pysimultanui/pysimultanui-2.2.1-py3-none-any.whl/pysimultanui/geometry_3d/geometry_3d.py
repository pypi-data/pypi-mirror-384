from nicegui import ui
from .scene import Scene

import numpy as np

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


with Scene() as scene:
    vertices = np.array([
        [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]
    ], dtype=float)
    indices = np.array([0, 1, 2, 0, 2, 3], dtype=int)
    material_props = {'color': 0xff0000, 'wireframe': True}

    scene.mesh(vertices, indices)

ui.run()
