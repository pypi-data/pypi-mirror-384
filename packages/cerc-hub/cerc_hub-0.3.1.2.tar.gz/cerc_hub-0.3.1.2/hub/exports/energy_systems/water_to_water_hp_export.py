"""
WaterToWaterHPExport exports water to water values after executing insel.
Multiple files are generated for the export
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Peter Yefi peteryefi@gmail.com
"""
from hub.exports.energy_systems.heat_pump_export import HeatPumpExport
from typing import List, Dict, Union


class WaterToWaterHPExport(HeatPumpExport):
  """
  Exports heat pump values as multiple output files
  after executing insel
  """

  def __init__(self, base_path, city, output_path, sim_type, demand_path):
    """
    :param base_path: path to energy system files
    :param city: the city object
    :param output_path: the file to hold insel simulation results
    :param sim_type: the simulation type to run: 1 for series, 0 for parallel
    :param demand_path: path to hourly energy demand file
    """
    tmp_file = 'heat_pumps/w2w_series.txt' if sim_type == 0 else 'heat_pumps/w2w_parallel.txt'
    template_path = (base_path / tmp_file)
    water_temp = (base_path / 'heat_pumps/wt_hourly3.txt')
    super().__init__(base_path=base_path, city=city, output_path=output_path, template=template_path,
                     demand_path=demand_path, water_temp=water_temp)

  def _extract_model_coefficient(self, hp_model: str) -> Union[List, None]:
    """
    Extracts heat pump coefficient data for a specific
    model. e.g. ClimateMaster 156 kW, etc.
    :param hp_model: the model type
    :return:
    """
    for energy_system in self._city.energy_systems:
      if energy_system.water_to_water_hp.model == hp_model:
        return energy_system.water_to_water_hp.power_demand_coff
    return None

  def execute_insel(self, user_input, hp_model) -> Union[Dict, None]:
    """
    Runs insel and produces output files
    Runs insel and write the necessary files
    :param user_input: a dictionary containing the user
    values necessary to run insel
    :param hp_model: a string that indicates the heat
    pump model to be used e.g. 012, 015
    :return:
    """
    pow_demand_coefficient = self._extract_model_coefficient(hp_model)
    return super(WaterToWaterHPExport, self)._run_insel(user_input, pow_demand_coefficient, 'w2w.insel')
