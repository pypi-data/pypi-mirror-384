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


class EnergyPlusMultipleBuildings:
  def __init__(self, city, base_path):
    self._city = city
    self._base_path = base_path

  def _building_energy_demands(self, energy_plus_output_file_path):
    buildings_energy_demands = {}

    with open(Path(energy_plus_output_file_path).resolve(), 'r', encoding='utf8') as csv_file:
      csv_output = list(csv.DictReader(csv_file))
      return
      for building in self._city.buildings:
        building_name = building.name.upper()

        buildings_energy_demands[f'Building {building_name} Heating Demand (J)'] = [
          float(
            row[f"{building_name} IDEAL LOADS AIR SYSTEM:Zone Ideal Loads Supply Air Total Heating Energy [J](Hourly)"])
          for row in csv_output
        ]
        buildings_energy_demands[f'Building {building_name} Cooling Demand (J)'] = [
          float(
            row[f"{building_name} IDEAL LOADS AIR SYSTEM:Zone Ideal Loads Supply Air Total Cooling Energy [J](Hourly)"])
          for row in csv_output
        ]
        buildings_energy_demands[f'Building {building_name} DHW Demand (W)'] = [
          float(row[f"DHW {building_name}:Water Use Equipment Heating Rate [W](Hourly)"])
          for row in csv_output
        ]
        buildings_energy_demands[f'Building {building_name} Appliances (W)'] = [
          float(row[f"{building_name}_APPLIANCE:Other Equipment Electricity Rate [W](Hourly)"])
          for row in csv_output
        ]
        buildings_energy_demands[f'Building {building_name} Lighting (W)'] = [
          float(row[f"{building_name}:Zone Lights Electricity Rate [W](Hourly)"]) for row in csv_output
        ]
    return buildings_energy_demands

  def enrich(self):
    """
    Enrich the city by using the energy plus workflow output files (J)
    :return: None
    """
    file_name = f'{self._city.name}_out.csv'
    energy_plus_output_file_path = Path(self._base_path / file_name).resolve()
    if energy_plus_output_file_path.is_file():
      building_energy_demands = self._building_energy_demands(energy_plus_output_file_path)
      for building in self._city.buildings:
        building_name = building.name.upper()
        building.heating_demand[cte.HOUR] = building_energy_demands[f'Building {building_name} Heating Demand (J)']
        building.cooling_demand[cte.HOUR] = building_energy_demands[f'Building {building_name} Cooling Demand (J)']
        building.domestic_hot_water_heat_demand[cte.HOUR] = \
            [x * cte.WATTS_HOUR_TO_JULES for x in building_energy_demands[f'Building {building_name} DHW Demand (W)']]
        building.appliances_electrical_demand[cte.HOUR] = \
            [x * cte.WATTS_HOUR_TO_JULES for x in building_energy_demands[f'Building {building_name} Appliances (W)']]
        building.lighting_electrical_demand[cte.HOUR] = \
            [x * cte.WATTS_HOUR_TO_JULES for x in building_energy_demands[f'Building {building_name} Lighting (W)']]
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

