from nicegui.elements.scene.scene_objects import Object3D
import numpy as np


class Mesh(Object3D):

    def __init__(self, vertices: np.ndarray,
                 indices: np.ndarray,
                 **kwargs):

        # super().__init__('sphere',
        #                  vertices.tolist(),
        #                  indices.tolist()
        #                  )
        super().__init__('mesh',
                         vertices.tolist(),
                         indices.tolist()
                         )


class Wire(Object3D):

    def __init__(self,
                 vertices: np.ndarray,
                 **kwargs):

        super().__init__('wire',
                         vertices.tolist()
                         )


class Spline(Object3D):
    """
    A spline object using CatmullRomCurve3
    """

    def __init__(self,
                 vertices: np.ndarray,
                 **kwargs):

        super().__init__('spline',
                         vertices.tolist()
                         )
