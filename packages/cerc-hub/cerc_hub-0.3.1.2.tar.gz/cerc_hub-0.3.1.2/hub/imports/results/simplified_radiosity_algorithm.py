"""
Simplified Radiosity Algorithm
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guillermo.GutierrezMorote@concordia.ca
"""

import pandas as pd
import hub.helpers.constants as cte
from hub.helpers.monthly_values import MonthlyValues


class SimplifiedRadiosityAlgorithm:
  """
  Import SRA results
  """
  def __init__(self, city, base_path):

    self._city = city
    self._base_path = base_path
    self._input_file_path = (self._base_path / f'{self._city.name}_sra_SW.out').resolve()
    try:
      self._results = pd.read_csv(self._input_file_path, sep='\s+', header=0).to_dict(orient='list')
    except FileNotFoundError as err:
      raise FileNotFoundError('No SRA output file found') from err

  def enrich(self):
    """
    saves in building surfaces the correspondent irradiance at different time-scales depending on the mode
    if building is None, it saves all buildings' surfaces in file, if building is specified, it saves only that
    specific building values
    :return: none
    """
    for key in self._results:
      _irradiance = {}
      header_name = key.split(':')
      result = [x for x in self._results[key]]
      city_object_name = header_name[1]
      building = self._city.city_object(city_object_name)
      surface_id = header_name[2]
      surface = building.surface_by_id(surface_id)
      monthly_result = MonthlyValues.get_total_month(result)
      yearly_result = [sum(result)]
      _irradiance[cte.YEAR] = yearly_result
      _irradiance[cte.MONTH] = monthly_result
      _irradiance[cte.HOUR] = result
      surface.global_irradiance = _irradiance

    self._city.level_of_detail.surface_radiation = 2
    for building in self._city.buildings:
      building.level_of_detail.surface_radiation = 2
