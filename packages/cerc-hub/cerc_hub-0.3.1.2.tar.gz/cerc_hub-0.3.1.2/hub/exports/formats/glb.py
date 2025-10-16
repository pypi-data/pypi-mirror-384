"""
export a city into Glb format
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""
import os
import shutil
import subprocess

from hub.city_model_structure.city import City
from hub.exports.formats.obj import Obj


class GltExceptionError(Exception):
  """
  Glt execution error
  """


class Glb:
  """
  Glb class
  """
  def __init__(self, city, path, target_buildings=None):
    self._city = city
    self._path = path
    if target_buildings is None:
      target_buildings = [b.name for b in self._city.buildings]
    self._target_buildings = target_buildings
    self._export()

  @property
  def _obj2gltf(self):
    return shutil.which('obj2gltf')

  def _export(self):
    try:
      for building in self._city.buildings:
        city = City(self._city.lower_corner, self._city.upper_corner, self._city.srs_name)
        city.add_city_object(building)
        city.name = building.name
        Obj(city, self._path)
        glb = f'{self._path}/{building.name}.glb'
        subprocess.run([
          self._obj2gltf,
          '-i', f'{self._path}/{building.name}.obj',
          '-b',
          '-o', f'{glb}'
        ])
        os.unlink(f'{self._path}/{building.name}.obj')
        os.unlink(f'{self._path}/{building.name}.mtl')
    except (subprocess.SubprocessError, subprocess.TimeoutExpired, subprocess.CalledProcessError) as err:
      raise GltExceptionError from err
