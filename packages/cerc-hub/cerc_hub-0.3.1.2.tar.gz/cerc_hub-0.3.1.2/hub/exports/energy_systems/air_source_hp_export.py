"""
AirSourceHPExport exports air source values after executing insel.
Multiple files are generated for the export
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Peter Yefi peteryefi@gmail.com
"""
from hub.exports.energy_systems.heat_pump_export import HeatPumpExport
from typing import List, Dict, Union


class AirSourceHPExport(HeatPumpExport):
  """
  Exports heat pump values as multiple files
  after executing insel
  """

  def __init__(self, base_path, city, output_path, sim_type, demand_path=None):
    """

    :param base_path: path to energy system files
    :param city: the city object
    :param output_path: the file to hold insel simulation results
    :param sim_type: the simulation type to run: 0 for series, 1 for parallel
    :param demand_path: path to hourly energy demand file
    """
    tmp_file = 'heat_pumps/as_series.txt' if sim_type == 0 else 'heat_pumps/as_parallel.txt'
    template_path = (base_path / tmp_file)
    super().__init__(base_path, city, output_path, template_path, demand_path)

  def _extract_model_coff(self, hp_model: str, data_type='heat') -> Union[List, None]:
    """
    Extracts heat pump coefficient data for a specific
    model. e.g. 012, 140
    :param hp_model: the model type
    :param data_type: indicates whether we're extracting cooling
    or heating performance coefficients
    :return:
    """
    for energy_system in self._city.energy_systems:
      if energy_system.air_source_hp.model == hp_model:
        if data_type == 'heat':
          return energy_system.air_source_hp.heating_capacity_coff
        return energy_system.air_source_hp.cooling_capacity_coff
    return None

  def execute_insel(self, user_input, hp_model, data_type) -> Union[Dict, None]:
    """
    Runs insel and produces output files
    Runs insel and write the necessary files
    :param user_input: a dictionary containing the user
    values necessary to run insel
    :param hp_model: a string that indicates the heat
    pump model to be used e.g. 012, 015
    :param data_type: a string that indicates whether
    insel should run for heat or cooling performance
    :return:
    """
    capacity_coefficient = self._extract_model_coff(hp_model, data_type)
    return super(AirSourceHPExport, self)._run_insel(user_input, capacity_coefficient, 'air_source.insel')
