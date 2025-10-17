import FreeCAD
import Part as FCPart

from typing import List, Optional, Union

from .scene import ExtendedScene
from .three_views import display_vertices, display_edges, display_wire, display_face, display_solid
# from nicegui.elements.scene_objects import Group
from nicegui.elements.scene.scene_objects import Group


def rgb_to_hex(rgb: List[int]) -> str:
    if rgb is None:
        return '#000000'
    return f'#{rgb[0] << 16 | rgb[1] << 8 | rgb[2]:06x}'


def hex_to_rgb(hex_color) -> List[int]:
    # Remove the '#' character if present
    hex_color = hex_color.strip('#')

    # Convert the hex color to RGB values
    r = int(hex_color[0:2], 16)  # Convert the first two hex digits to a base-10 integer
    g = int(hex_color[2:4], 16)  # Convert the middle two hex digits to a base-10 integer
    b = int(hex_color[4:6], 16)  # Convert the last two hex digits to a base-10 integer

    return [r, g, b]


def get_color(feature: FCPart.Feature,
              color: Optional[Union[List, str]]
              ) -> Optional[List]:
    if color is None:
        rgba_string = feature.ShapeMaterial.Properties['AmbientColor']
        rgba_values = rgba_string.strip('()').split(',')
        rgb = [int(float(value.strip()) * 255) for value in rgba_values[:3]]
    elif isinstance(color, list):
        rgb = color
    elif isinstance(color, str):
        rgb = hex_to_rgb(color)
    else:
        raise ValueError(f'Invalid color type: {color}')
    return rgb


def display_feature(feature: FCPart.Feature,
                    scene: ExtendedScene,
                    geo_id: str = None,
                    color: any = None
                    ) -> tuple[Group, tuple[float, float, float]]:

    x_height = feature.Shape.BoundBox.XMax
    y_height = feature.Shape.BoundBox.YMax
    z_height = feature.Shape.BoundBox.ZMax

    rgb = get_color(feature, color)

    with scene.group() as group:
        if hasattr(feature.Shape, 'Vertexes'):
            display_vertices(feature.Shape.Vertexes,
                             scene,
                             geo_id or str(feature.ID),
                             colors=[rgb] * feature.Shape.Vertexes.__len__()
                             )

        if hasattr(feature.Shape, 'Edges'):
            display_edges(feature.Shape.Edges,
                          scene,
                          geo_id or str(feature.ID),
                          rgb)

        if hasattr(feature.Shape, 'Wires'):
            for wire in feature.Shape.Wires:
                display_wire(wire,
                             scene,
                             geo_id or str(feature.ID),
                             rgb)

        if hasattr(feature.Shape, 'Faces'):
            for face in feature.Shape.Faces:
                display_face(face,
                             scene,
                             geo_id or str(feature.ID),
                             rgb)

        if hasattr(feature.Shape, 'Solids'):
            for solid in feature.Shape.Solids:
                display_solid(solid,
                              scene,
                              geo_id or str(feature.ID),
                              rgb)

    scene.move_camera(x=x_height, y=-y_height, z=z_height * 2, duration=2)

    return group, (x_height, y_height, z_height)
