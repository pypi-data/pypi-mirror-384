from PySimultan2.geometry import GeometryModel
import os
import numpy as np
import struct


def rgba_to_hex(rgba):
    """
    Convert an RGBA color (with each component in 0-255 range) to a hexadecimal color string.

    Parameters:
        rgba (tuple): A tuple of four elements (R, G, B, A) where R, G, B are integers from 0 to 255
                      representing the color and A is a float from 0.0 to 1.0 representing the opacity.

    Returns:
        str: The hexadecimal color string including alpha channel as #RRGGBBAA.
    """
    r, g, b, a = rgba
    return f'#{r:02X}{g:02X}{b:02X}'


def create_stl_file(geometry_model: GeometryModel) -> dict[int: str]:
    stl_dir = os.path.join('/static/stl', str(geometry_model.key))
    if not os.path.exists(stl_dir):
        os.makedirs(stl_dir)

    file_lookup = {}

    for face in geometry_model.faces:
        filename = os.path.join(stl_dir, f"{face.id}.stl")
        file_lookup[face.id] = (os.path.join('/stl', str(geometry_model.key), f"{face.id}.stl"),
                                rgba_to_hex((getattr(face._wrapped_object.Color.Color,
                                                     key) for key in ('R', 'G', 'B', 'A')))
                                )
        vertices, triangles = face.triangulate()
        write_stl_from_numpy(vertices, triangles, filename=filename)

    return file_lookup


def write_stl_from_numpy(vertices, triangles, filename="output.stl"):
    """
    Write a binary STL file from numpy arrays of vertices and triangles.

    Parameters:
        vertices (np.array): Nx3 numpy array of vertices.
        triangles (np.array): Mx3 numpy array of triangle indices.
        filename (str): The filename to save the STL file to.
    """
    # Open the file in binary write mode
    with open(filename, "wb") as f:
        # Write the header
        f.write(b'\0' * 80)  # STL file header 80 bytes long
        f.write(struct.pack('<I', len(triangles)))  # Number of triangles

        # Write each triangle
        for tri in triangles:
            # Calculate the normal for the triangle
            v1 = vertices[tri[0]]
            v2 = vertices[tri[1]]
            v3 = vertices[tri[2]]
            normal = np.cross(v2 - v1, v3 - v1)
            normal = normal / np.linalg.norm(normal)

            # Pack the data in the right format and write to file
            f.write(struct.pack('<3f', *normal))  # Normal vector
            f.write(struct.pack('<3f', *v1))  # Vertex 1
            f.write(struct.pack('<3f', *v2))  # Vertex 2
            f.write(struct.pack('<3f', *v3))  # Vertex 3
            f.write(b'\0\0')  # Attribute byte count - not used

    print(f"File saved as {filename}")
