"""
Cerc Idf exports one city or some buildings to idf format
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Guillermo.GutierrezMorote@concordia.ca
Code contributors: Oriol Gavalda Torrellas oriol.gavalda@concordia.ca
"""

from pathlib import Path

import hub.exports.building_energy.idf_helper as idf_cte


class IdfBase:
  def __init__(self, city, output_path, idf_file_path, idd_file_path, epw_file_path, target_buildings=None,
               _calculate_with_new_infiltration=True):
    self.city = city
    self.output_path = str(output_path.resolve())
    self._output_file_path = str((output_path / f'{city.name}.idf').resolve())
    self._file_paths = {
      'schedules': str((output_path / 'schedules.idf').resolve()),
      'file_schedules': str((output_path / 'file_schedules.idf').resolve()),
      'solid_materials': str((output_path / 'solid_materials.idf').resolve()),
      'nomass_materials': str((output_path / 'nomass_materials.idf').resolve()),
      'window_materials': str((output_path / 'window_materials.idf').resolve()),
      'constructions': str((output_path / 'constructions.idf').resolve()),
      'zones': str((output_path / 'zones.idf').resolve()),
      'surfaces': str((output_path / 'surfaces.idf').resolve()),
      'fenestration': str((output_path / 'fenestration.idf').resolve()),
      'occupancy': str((output_path / 'occupancy.idf').resolve()),
      'lighting': str((output_path / 'lights.idf').resolve()),
      'appliances': str((output_path / 'appliances.idf').resolve()),
      'shading': str((output_path / 'shading.idf').resolve()),
      'infiltration': str((output_path / 'infiltration.idf').resolve()),
      'ventilation': str((output_path / 'ventilation.idf').resolve()),
      'thermostat': str((output_path / 'thermostat.idf').resolve()),
      'ideal_load_system': str((output_path / 'ideal_load_system.idf').resolve()),
      'dhw': str((output_path / 'dhw.idf').resolve()),
      'outputs': str((output_path / 'outputs.idf').resolve()),
      'control_files': str((output_path / 'control_files.idf').resolve())
    }

    self.files = {}
    for key, value in self._file_paths.items():
      self.files[key] = open(value, 'w', encoding='UTF-8')

    self._idd_file_path = str(idd_file_path)
    self._idf_file_path = str(idf_file_path)
    self._epw_file_path = str(epw_file_path)

    self._target_buildings = target_buildings
    self._adjacent_buildings = []

    if target_buildings is None:
      self._target_buildings = [building.name for building in self.city.buildings]
    else:
      for building_name in target_buildings:
        building = city.city_object(building_name)
        if building.neighbours is not None:
          self._adjacent_buildings += building.neighbours
    self._calculate_with_new_infiltration = _calculate_with_new_infiltration

  def _create_output_control_lighting(self):
    file = self.files['appliances']
    self.write_to_idf_format(file, idf_cte.OUTPUT_CONTROL)
    self.write_to_idf_format(file, 'Comma', 'Column Separator', ';')

  @staticmethod
  def write_to_idf_format(file, field, comment='', eol=','):
    if comment != '':
      comment = f'    !- {comment}'
      field = f'    {field}{eol}'.ljust(26, ' ')
      file.write(f'{field}{comment}\n')
    else:
      file.write(f'{field}{comment}')

  @staticmethod
  def matrix_to_list(points, lower_corner):
    lower_x = lower_corner[0]
    lower_y = lower_corner[1]
    lower_z = lower_corner[2]
    points_list = []
    for point in points:
      point_tuple = (point[0] - lower_x, point[1] - lower_y, point[2] - lower_z)
      points_list.append(point_tuple)
    return points_list
