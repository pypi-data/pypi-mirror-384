"""
export a city from trimesh into Triangular format (obj or stl)
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""
from pathlib import Path
from trimesh import Trimesh


class Triangular:
  """
  Superclass to export to triangular format (STL or OBJ)
  """
  def __init__(self, city, path, triangular_format, write_mode='w'):
    self._city = city
    self._path = path
    self._triangular_format = triangular_format
    self._write_mode = write_mode
    self._export()

  def _export(self):
    if self._city.name is None:
      self._city.name = 'unknown_city'
    file_name = self._city.name + '.' + self._triangular_format
    file_path = (Path(self._path).resolve() / file_name).resolve()
    trimesh = Trimesh()
    for building in self._city.buildings:
      trimesh = trimesh.union(building.simplified_polyhedron.trimesh)

    with open(file_path, self._write_mode) as file:
      file.write(trimesh.export(file_type=self._triangular_format))
