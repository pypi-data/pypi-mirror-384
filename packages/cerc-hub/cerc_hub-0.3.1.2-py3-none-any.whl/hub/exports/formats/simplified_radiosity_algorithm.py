"""
Simplified Radiosity Algorithm
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guillermo.GutierrezMorote@concordia.ca
"""
from pathlib import Path

import xmltodict

from hub.imports.weather_factory import WeatherFactory
import hub.helpers.constants as cte
from hub.helpers.configuration_helper import ConfigurationHelper


class SimplifiedRadiosityAlgorithm:
  """
  Export to SRA format
  """

  def __init__(self,
               city,
               file_name,
               target_buildings=None,
               begin_month=1,
               begin_day=1,
               end_month=12,
               end_day=31):
    self._file_name = file_name
    self._begin_month = begin_month
    self._begin_day = begin_day
    self._end_month = end_month
    self._end_day = end_day
    self._city = city
    self._city.climate_file = str((Path(file_name).parent / f'{city.name}.cli').resolve())
    self._city.climate_reference_city = city.location
    self._target_buildings = target_buildings
    self._export()

  def _correct_point(self, point):
    # correct the x, y, z values into the reference frame set by city lower_corner
    x = point[0] - self._city.lower_corner[0]
    y = point[1] - self._city.lower_corner[1]
    z = point[2] - self._city.lower_corner[2]
    return [x, y, z]

  def _export(self):
    self._export_sra_cli()
    self._export_sra_xml()

  def _export_sra_cli(self):
    file = self._city.climate_file
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    WeatherFactory('epw', self._city).enrich()
    content = self._city.name + '\n'
    content += str(self._city.latitude) + ',' + str(self._city.longitude) + ',0.0,' + str(self._city.time_zone) + '\n'
    content += '\ndm  m h G_Dh  G_Bn\n'
    total_days = 0
    for month in range(1, 13):
      if month > 1:
        total_days += days_in_month[month - 2]
      for day in range(1, days_in_month[month - 1] + 1):
        for hour in range(1, 25):
          if month == 1:
            i = 24 * (day - 1) + hour - 1
          else:
            i = (total_days + day - 1) * 24 + hour - 1
          representative_building = self._city.buildings[0]
          _global = representative_building.diffuse[cte.HOUR][i]
          _beam = representative_building.direct_normal[cte.HOUR][i]
          content += f'{day}  {month}  {hour}  {_global}  {_beam}\n'
    with open(file, 'w', encoding='utf-8') as file:
      file.write(content)

  def _export_sra_xml(self):
    buildings = []
    for building_index, building in enumerate(self._city.buildings):
      if self._target_buildings is None:
        simulate = 'true'
      else:
        simulate = 'false'
        for target_building in self._target_buildings:
          if building.name == target_building.name:
            simulate = 'true'
      building_dict = {
        '@Name': f'{building.name}',
        '@id': f'{building_index}',
        '@key': f'{building.name}',
        '@Simulate': f'{simulate}'
      }
      walls, roofs, floors = [], [], []
      default_short_wave_reflectance = ConfigurationHelper().short_wave_reflectance
      for surface in building.surfaces:
        if surface.short_wave_reflectance is None:
          short_wave_reflectance = default_short_wave_reflectance
        else:
          short_wave_reflectance = surface.short_wave_reflectance
        surface_dict = {
          '@id': f'{surface.id}',
          '@ShortWaveReflectance': f'{short_wave_reflectance}'
        }
        for point_index, point in enumerate(surface.perimeter_polygon.coordinates):
          point = self._correct_point(point)
          surface_dict[f'V{point_index}'] = {
            '@x': f'{point[0]}',
            '@y': f'{point[1]}',
            '@z': f'{point[2]}'
          }
        if surface.type == 'Wall':
          walls.append(surface_dict)
        elif surface.type == 'Roof':
          roofs.append(surface_dict)
        else:
          floors.append(surface_dict)
      building_dict['Wall'] = walls
      building_dict['Roof'] = roofs
      building_dict['Floor'] = floors
      buildings.append(building_dict)
    sra = {
      'CitySim': {
        '@name': f'{self._file_name.name}',
        'Simulation': {
          '@beginMonth': f'{self._begin_month}',
          '@beginDay': f'{self._begin_day}',
          '@endMonth': f'{self._end_month}',
          '@endDay': f'{self._end_day}',
        },
        'Climate': {
          '@location': f'{self._city.climate_file}',
          '@city': f'{self._city.climate_reference_city}'
        },
        'District': {
          'FarFieldObstructions': None,
          'Building': buildings
        }
      }
    }
    with open(self._file_name, 'w', encoding='utf-8') as file:
      file.write(xmltodict.unparse(sra, pretty=True, short_empty_elements=True))
