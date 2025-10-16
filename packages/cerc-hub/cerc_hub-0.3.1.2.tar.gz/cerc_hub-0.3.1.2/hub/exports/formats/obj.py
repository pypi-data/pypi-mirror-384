"""
export a city into Obj format
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""
from pathlib import Path

import numpy as np


class Obj:
  """
  Export to obj format
  """
  def __init__(self, city, path):
    self._city = city
    self._path = path
    self._export()

  def _ground(self, coordinate):
    x = coordinate[0] - self._city.lower_corner[0]
    y = coordinate[1] - self._city.lower_corner[1]
    z = coordinate[2] - self._city.lower_corner[2]
    return x, y, z

  def _to_vertex(self, coordinate):
    x, y, z = self._ground(coordinate)
    return f'v {x} {z} -{y}\n'  # to match opengl expectations

  def _to_texture_vertex(self, coordinate):
    u, v, _ = self._ground(coordinate)
    return f'vt {u} {v}\n'

  def _to_normal_vertex(self, coordinates):
    ground_vertex = []
    for coordinate in coordinates:
      x, y, z = self._ground(coordinate)
      ground_vertex.append(np.array([x, y, z]))
    # recalculate the normal to get grounded values
    edge_1 = ground_vertex[1] - ground_vertex[0]
    edge_2 = ground_vertex[2] - ground_vertex[0]
    normal = np.cross(edge_1, edge_2)
    normal = normal / np.linalg.norm(normal)
    return f'vn {normal[0]} {normal[1]} {normal[2]}\n'

  def _export(self):
    if self._city.name is None:
      self._city.name = 'unknown_city'
    obj_name = f'{self._city.name}.obj'
    mtl_name = f'{self._city.name}.mtl'
    obj_file_path = (Path(self._path).resolve() / obj_name).resolve()
    mtl_file_path = (Path(self._path).resolve() / mtl_name).resolve()
    with open(mtl_file_path, 'w', encoding='utf-8') as mtl:
      mtl.write("newmtl cerc_base_material\n")
      mtl.write("Ka 1.0 1.0 1.0      # Ambient color (white)\n")
      mtl.write("Kd 0.1 0.3 0.1      # Diffuse color (greenish)\n")
      mtl.write("Ks 1.0 1.0 1.0      # Specular color (white)\n")
      mtl.write("Ns 400.0             # Specular exponent (defines shininess)\n")
    vertices = {}
    faces = []
    vertex_index = 0
    normal_index = 0
    with open(obj_file_path, 'w', encoding='utf-8') as obj:
      obj.write("# cerc-hub export\n")
      obj.write(f'mtllib {mtl_name}\n')

      for building in self._city.buildings:
        obj.write(f'# building {building.name}\n')
        obj.write(f'g {building.name}\n')
        obj.write('s off\n')

        for surface in building.surfaces:
          obj.write(f'# surface {surface.name}\n')
          face = []
          normal = self._to_normal_vertex(surface.perimeter_polygon.coordinates)
          normal_index += 1
          textures = []
          for coordinate in surface.perimeter_polygon.coordinates:
            vertex = self._to_vertex(coordinate)
            if vertex not in vertices:
              vertex_index += 1
              vertices[vertex] = vertex_index
              current = vertex_index
              obj.write(vertex)
              textures.append(self._to_texture_vertex(coordinate))  # only append if non-existing
            else:
              current = vertices[vertex]
            face.append(f'{current}/{current}/{normal_index}')  # insert clockwise
          obj.writelines(normal)  # add the normal
          obj.writelines(textures)  # add the texture vertex

          faces.append(f"f {' '.join(face)}\n")
          obj.writelines(faces)
          faces = []
