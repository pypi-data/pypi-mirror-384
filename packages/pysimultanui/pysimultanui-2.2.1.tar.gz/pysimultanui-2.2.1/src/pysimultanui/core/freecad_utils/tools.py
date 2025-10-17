import random
from logging import getLogger
from PySimultan2.geometry.geometry_base import (GeometryModel, SimultanVertex, SimultanEdge, SimultanEdgeLoop,
                                                SimultanFace, SimultanVolume, SimultanLayer)

import FreeCAD
import Part as FCPart

from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from PySimultan2.data_model import DataModel
    from PySimultan2.object_mapper import PythonMapper

logger = getLogger('PySimultan-FreeCAD-Tools',
                   )
logger.setLevel('DEBUG')


def import_freecad(doc: FreeCAD.Document,
                   geo_model: GeometryModel,
                   data_model: Optional['DataModel'] = None,
                   object_mapper: Optional['PythonMapper'] = None,
                   scale: float=1.0) -> tuple[int, int, int, int, int]:

    vertex_lookup: dict[FCPart.Vertex: SimultanVertex] = {}
    vertex_pos_lookup: dict[tuple[float, float, float]: SimultanVertex] = {}
    edge_lookup: dict[FCPart.Edge: SimultanEdge] = {}
    edge_v_lookup: dict[tuple[SimultanVertex, SimultanVertex]: SimultanEdge] = {}
    wire_lookup: dict[FCPart.Wire: SimultanEdgeLoop] = {}
    wire_e_lookup: dict[tuple[SimultanEdge]: SimultanEdgeLoop] = {}
    face_lookup: dict[FCPart.Face: SimultanFace] = {}
    face_w_lookup: dict[tuple[SimultanEdgeLoop]: SimultanFace] = {}
    volume_lookup: dict[FCPart.Volume: SimultanVolume] = {}

    layer = SimultanLayer(name='Layer 1',
                          geometry_model=geo_model,
                          data_model=data_model if data_model is not None else geo_model._data_model,
                          object_mapper=object_mapper if object_mapper is not None else geo_model._object_mapper)

    def vertex_from_freecad(vertex: FCPart.Vertex) -> SimultanVertex:
        if vertex in vertex_lookup:
            return vertex_lookup[vertex]
        elif (vertex.X * scale, vertex.Y * scale, vertex.Z * scale) in vertex_pos_lookup:
            return vertex_pos_lookup[(vertex.X * scale, vertex.Y * scale, vertex.Z * scale)]

        new_vertex = SimultanVertex(x=vertex.X * scale,
                                    y=vertex.Y * scale,
                                    z=vertex.Z * scale,
                                    layer=layer)
        vertex_pos_lookup[(vertex.X * scale,
                           vertex.Y * scale,
                           vertex.Z * scale)] = new_vertex
        vertex_lookup[vertex] = new_vertex
        return new_vertex

    def edge_from_freecad(edge: FCPart.Edge) -> SimultanEdge:
        if edge in edge_lookup:
            return edge_lookup[edge]
        elif (edge.Vertexes[0], edge.Vertexes[1]) in edge_v_lookup:
            return edge_v_lookup[(edge.Vertexes[0], edge.Vertexes[1])]

        new_edge = SimultanEdge(vertices=[vertex_from_freecad(edge.Vertexes[0]),
                                          vertex_from_freecad(edge.Vertexes[1])],
                                layer=layer)
        edge_lookup[edge] = new_edge
        edge_v_lookup[(edge.Vertexes[0], edge.Vertexes[1])] = new_edge

        return new_edge

    def wire_from_freecad(wire: FCPart.Wire) -> SimultanEdgeLoop:
        print(f'Wire: {wire.Edges}')
        if wire in wire_lookup:
            return wire_lookup[wire]

        edges = [edge_from_freecad(edge) for edge in wire.OrderedEdges]

        if tuple(edges) in wire_e_lookup:
            return wire_e_lookup[tuple(edges)]

        new_wire = SimultanEdgeLoop(edges=edges,
                                    layer=layer)
        wire_lookup[wire] = new_wire
        wire_e_lookup[tuple(edges)] = new_wire

        return new_wire

    def face_from_freecad(face: FCPart.Face) -> SimultanFace:
        print(f'Face: {face.Wires}')

        if face in face_lookup:
            return face_lookup[face]
        wires = [wire_from_freecad(wire) for wire in face.Wires]

        if tuple(wires) in face_w_lookup:
            return face_w_lookup[tuple(wires)]

        boundary_edge_loop = wire_from_freecad(face.OuterWire)
        holes = [wire_from_freecad(x) for x in [x for x in face.Wires if not x.isEqual(face.OuterWire)]]

        if holes:
            logger.debug(f'Face has holes: {holes}')

        new_face = SimultanFace(edge_loop=boundary_edge_loop,
                                holes=holes,
                                layer=layer)
        new_face._wrapped_object.Color.set_Color(new_face._wrapped_object.Color.
                                                 Color.FromRgb(random.randint(0, 255),
                                                               random.randint(0, 255),
                                                               random.randint(0, 255)
                                                               )
                                                 )
        face_lookup[face] = new_face
        face_w_lookup[tuple(wires)] = new_face
        return new_face

    def volume_from_freecad(volume: FCPart.Solid) -> SimultanVolume:
        print(f'Volume: {volume.Faces}')

        if volume in volume_lookup:
            return volume_lookup[volume]

        faces = [face_from_freecad(face) for face in volume.Faces]
        new_volume = SimultanVolume(faces=faces,
                                    layer=layer)

        volume_lookup[volume] = new_volume
        return new_volume

    for feature in doc.Objects:
        try:
            if isinstance(feature.Shape, FCPart.Vertex):
                vertex = vertex_from_freecad(feature)
            elif isinstance(feature.Shape, FCPart.Edge):
                edge = edge_from_freecad(feature)
            elif isinstance(feature.Shape, FCPart.Wire):
                wire = wire_from_freecad(feature.Shape)
            elif isinstance(feature.Shape, FCPart.Face):
                face = face_from_freecad(feature.Shape)
            elif isinstance(feature.Shape, FCPart.Solid):
                volume = volume_from_freecad(feature.Shape)
        except Exception as e:
            print(f'Error processing feature: {e}')
            continue

    return (vertex_lookup.__len__(), edge_lookup.__len__(),
            wire_lookup.__len__(), face_lookup.__len__(), volume_lookup.__len__())
