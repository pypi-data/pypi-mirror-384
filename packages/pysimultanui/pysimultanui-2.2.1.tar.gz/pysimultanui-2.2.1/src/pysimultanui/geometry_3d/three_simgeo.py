import sys
import traceback
from typing import Any, Optional, List, Union
from .scene import ExtendedScene
import numpy as np

import logging

from SIMULTAN.Data.Geometry import (Layer, Vertex, Edge, PEdge, Face, Volume, EdgeLoop, OperationPermission,
                                             GeometryModelOperationPermissions, GeometryOperationPermissions,
                                             LayerOperationPermissions, GeometryModelData, GeometricOrientation,
                                             BaseEdgeContainer)

from PySimultan2.geometry.geometry_base import (SimultanVolume, SimultanFace, SimultanEdge, SimultanVertex,
                                                                SimultanLayer, SimultanEdgeLoop, GeometryModel)



logger = logging.getLogger('PySimultanUI')


def rgb_to_hex(rgb: List[int]) -> str:
    if rgb is None:
        return '#000000'
    return f'#{rgb[0] << 16 | rgb[1] << 8 | rgb[2]:06x}'


def display_simgeo(simgeo: Union[Layer, Vertex, Edge, PEdge, Face, Volume, EdgeLoop],
                   scene: ExtendedScene,
                   obj_id: str = '',
                   color: Optional[list[int]] = None):
    try:

        with scene.group() as group:
            rgb_color = rgb_to_hex([simgeo._wrapped_object.Color.Color.R,
                                    simgeo._wrapped_object.Color.Color.G,
                                    simgeo._wrapped_object.Color.Color.B])

            if isinstance(simgeo, SimultanVertex):
                scene.point_cloud([simgeo.position],
                                  colors=[[simgeo._wrapped_object.Color.Color.R,
                                           simgeo._wrapped_object.Color.Color.G,
                                           simgeo._wrapped_object.Color.Color.B]],
                                  point_size=0.1).with_name(simgeo.id)
            elif isinstance(simgeo, SimultanEdge):
                scene.line(simgeo.vertex_0.position,
                           simgeo.vertex_1.position).material(rgb_color).with_name(simgeo.id)
            elif isinstance(simgeo, SimultanFace):
                tris = simgeo.triangulate()
                scene.mesh(tris[0], tris[1]).material(rgb_color).with_name(simgeo.id)
            elif isinstance(simgeo, SimultanVolume):
                for face in simgeo.faces:
                    tris = face.triangulate()
                    scene.mesh(tris[0], tris[1]).material(rgb_color).with_name(simgeo.id)

            return group

    except Exception as e:
        logger.error(f'Error displaying simgeo: {e}\n'
                     f'{traceback.format_exception(*sys.exc_info())}')
