"""
Insel monthly energy balance
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Saeed Ranjbar saeed.ranjbar@concordia.ca
Project collaborator Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""
from pathlib import Path
from hub.helpers.monthly_values import MonthlyValues
import csv

import hub.helpers.constants as cte


class EnergyPlusSingleBuilding:
  def __init__(self, city, base_path):
    self._city = city
    self._base_path = base_path

  @staticmethod
  def _building_energy_demands(energy_plus_output_file_path):
    with open(Path(energy_plus_output_file_path).resolve(), 'r', encoding='utf8') as csv_file:
      csv_output = csv.reader(csv_file)
      headers = next(csv_output)
      building_energy_demands = {
                                  'Heating (J)': [],
                                  'Cooling (J)': [],
                                  'DHW (J)': [],
                                  'Appliances (J)': [],
                                  'Lighting (J)': []
                                }
      heating_column_index = []
      cooling_column_index = []
      dhw_column_index = []
      appliance_column_index = []
      lighting_column_index = []
      for index, header in enumerate(headers):
        if "Total Heating" in header:
          heating_column_index.append(index)
        elif "Total Cooling" in header:
          cooling_column_index.append(index)
        elif "DHW" in header:
          dhw_column_index.append(index)
        elif "InteriorEquipment" in header:
          appliance_column_index.append(index)
        elif "InteriorLights" in header:
          lighting_column_index.append(index)

      for line in csv_output:
        total_heating_demand = 0
        total_cooling_demand = 0
        total_dhw_demand = 0
        total_appliance_demand = 0
        total_lighting_demand = 0
        for heating_index in heating_column_index:
          total_heating_demand += float(line[heating_index])
        building_energy_demands['Heating (J)'].append(total_heating_demand)
        for cooling_index in cooling_column_index:
          total_cooling_demand += float(line[cooling_index])
        building_energy_demands['Cooling (J)'].append(total_cooling_demand)
        for dhw_index in dhw_column_index:
          total_dhw_demand += float(line[dhw_index]) * cte.WATTS_HOUR_TO_JULES
        building_energy_demands['DHW (J)'].append(total_dhw_demand)
        for appliance_index in appliance_column_index:
          total_appliance_demand += float(line[appliance_index])
        building_energy_demands['Appliances (J)'].append(total_appliance_demand)
        for lighting_index in lighting_column_index:
          total_lighting_demand += float(line[lighting_index])
        building_energy_demands['Lighting (J)'].append(total_lighting_demand)

    return building_energy_demands

  def enrich(self):
    """
    Enrich the city by using the energy plus workflow output files (J)
    :return: None
    """
    for building in self._city.buildings:
      file_name = f'{building.name}_out.csv'
      energy_plus_output_file_path = Path(self._base_path / file_name).resolve()
      if energy_plus_output_file_path.is_file():
        building_energy_demands = self._building_energy_demands(energy_plus_output_file_path)
        building.heating_demand[cte.HOUR] = building_energy_demands['Heating (J)']
        building.cooling_demand[cte.HOUR] = building_energy_demands['Cooling (J)']
        building.domestic_hot_water_heat_demand[cte.HOUR] = building_energy_demands['DHW (J)']
        building.appliances_electrical_demand[cte.HOUR] = building_energy_demands['Appliances (J)']
        building.lighting_electrical_demand[cte.HOUR] = building_energy_demands['Lighting (J)']
        building.heating_demand[cte.MONTH] = MonthlyValues.get_total_month(building.heating_demand[cte.HOUR])
        building.cooling_demand[cte.MONTH] = MonthlyValues.get_total_month(building.cooling_demand[cte.HOUR])
        building.domestic_hot_water_heat_demand[cte.MONTH] = (
          MonthlyValues.get_total_month(building.domestic_hot_water_heat_demand[cte.HOUR]))
        building.appliances_electrical_demand[cte.MONTH] = (
          MonthlyValues.get_total_month(building.appliances_electrical_demand[cte.HOUR]))
        building.lighting_electrical_demand[cte.MONTH] = (
          MonthlyValues.get_total_month(building.lighting_electrical_demand[cte.HOUR]))
        building.heating_demand[cte.YEAR] = [sum(building.heating_demand[cte.MONTH])]
        building.cooling_demand[cte.YEAR] = [sum(building.cooling_demand[cte.MONTH])]
        building.domestic_hot_water_heat_demand[cte.YEAR] = [sum(building.domestic_hot_water_heat_demand[cte.MONTH])]
        building.appliances_electrical_demand[cte.YEAR] = [sum(building.appliances_electrical_demand[cte.MONTH])]
        building.lighting_electrical_demand[cte.YEAR] = [sum(building.lighting_electrical_demand[cte.MONTH])]
