"""
Cerc Idf result import
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Guillermo.GutierrezMorote@concordia.ca
Code contributors: Saeed Ranjbar saeed.ranjbar@concordia.ca
"""
import csv
import logging
from pathlib import Path

from sympy.physics.units import energy

import hub.helpers.constants as cte


class EnergyPlus:
  """
  Energy plus class
  """

  def _extract_fields_from_headers(self, headers):
    for header in headers:
      header_parts = header.split(':')
      building_name = header_parts[0]
      variable = ':'.join(header_parts[1:]).strip()  # concat the rest and ensure that : it's reintroduced just in case
      if variable == '':
        continue
      if building_name not in self._summary_variables:
        self._building_energy_demands[variable] = []  # initialize the list of variables
      else:
        self._building_energy_demands[header] = []

  def __init__(self, city, file_path):
    self._city = city
    self._building_energy_demands = {}
    self._lines = []
    self._summary_variables = ['DistrictCooling:Facility [J](Hourly)',
                               'InteriorEquipment:Electricity [J](Hourly)',
                               'InteriorLights:Electricity [J](Hourly) ']

    if Path(file_path).is_dir():
      logging.warning('The path should contain the result CSV file, fallback to default %s_out.csv', city.name)
      file_path = Path(file_path) / f'{city.name}_out.csv'
    if not Path(file_path).exists():
      logging.error('No result file found, check the given path')
    with open(file_path, 'r', encoding='utf8') as csv_file:
      csv_output = csv.reader(csv_file)
      self._headers = next(csv_output)
      self._extract_fields_from_headers(self._headers)
      for line in csv_output:
        self._lines.append(line)

  def enrich(self):
    """
    Enrich the city by using the energy plus workflow output files (J)
    :return: None
    """
    for building in self._city.buildings:
      building_name = building.name.upper()
      for index, zone in enumerate(building.internal_zones):
        _energy_demands = {}
        for header in self._building_energy_demands:
          if header == 'Zone Ideal Loads Supply Air Total Heating Energy [J](Hourly)':
            field_name = f'{building_name}_{index} IDEAL LOADS AIR SYSTEM:{header}'
          elif header == 'Zone Ideal Loads Supply Air Total Cooling Energy [J](Hourly)':
            field_name = f'{building_name}_{index} IDEAL LOADS AIR SYSTEM:{header}'
          else:
            field_name = f'{building_name}_{index}:{header}'
          position = -1
          if field_name in self._headers:
            position = self._headers.index(field_name)
          if position == -1:
            continue
          for line in self._lines:
            if header not in _energy_demands.keys():
              _energy_demands[header] = []
            _energy_demands[header].append(line[position])
        EnergyPlus._set_building_zone_demands(building, index, _energy_demands)
      EnergyPlus._set_building_demands(building)

  @staticmethod
  def _set_building_zone_demands(building, zone, energy_demands):
    if not energy_demands.keys():
      logging.warning('No simulation results for building %s', building.name)
      return
    heating = [float(x) for x in energy_demands['Zone Ideal Loads Supply Air Total Heating Energy [J](Hourly)']]
    cooling = [float(x) for x in energy_demands['Zone Ideal Loads Supply Air Total Cooling Energy [J](Hourly)']]
    dhw = [float(x) * cte.WATTS_HOUR_TO_JULES for x in energy_demands['Water Use Equipment Heating Rate [W](Hourly)']]
    appliances = [float(x) * cte.WATTS_HOUR_TO_JULES for x in energy_demands['Other Equipment Electricity Rate [W](Hourly)']]
    lighting = [float(x) * cte.WATTS_HOUR_TO_JULES for x in energy_demands['Zone Lights Electricity Rate [W](Hourly)']]

    building.internal_zones[zone].heating_demand[cte.HOUR] = heating
    building.internal_zones[zone].cooling_demand[cte.HOUR] = cooling
    building.internal_zones[zone].domestic_hot_water_heat_demand[cte.HOUR] = dhw
    building.internal_zones[zone].appliances_electrical_demand[cte.HOUR] = appliances
    building.internal_zones[zone].lighting_electrical_demand[cte.HOUR] = lighting
    building.internal_zones[zone].heating_demand[cte.MONTH] = []
    building.internal_zones[zone].cooling_demand[cte.MONTH] = []
    building.internal_zones[zone].domestic_hot_water_heat_demand[cte.MONTH] = []
    building.internal_zones[zone].appliances_electrical_demand[cte.MONTH] = []
    building.internal_zones[zone].lighting_electrical_demand[cte.MONTH] = []

    start = 0
    for hours in cte.HOURS_A_MONTH.values():
      end = hours + start
      building.internal_zones[zone].heating_demand[cte.MONTH].append(sum(heating[start: end]))
      building.internal_zones[zone].cooling_demand[cte.MONTH].append(sum(cooling[start: end]))
      building.internal_zones[zone].domestic_hot_water_heat_demand[cte.MONTH].append(sum(dhw[start: end]))
      building.internal_zones[zone].appliances_electrical_demand[cte.MONTH].append(sum(appliances[start: end]))
      building.internal_zones[zone].lighting_electrical_demand[cte.MONTH].append(sum(lighting[start: end]))
      start = end
    building.internal_zones[zone].heating_demand[cte.YEAR] = [sum(heating)]
    building.internal_zones[zone].cooling_demand[cte.YEAR] = [sum(cooling)]
    building.internal_zones[zone].domestic_hot_water_heat_demand[cte.YEAR] = [sum(dhw)]
    building.internal_zones[zone].appliances_electrical_demand[cte.YEAR] = [sum(appliances)]
    building.internal_zones[zone].lighting_electrical_demand[cte.YEAR] = [sum(lighting)]

  @staticmethod
  def _sum(zone, building):
    return [x + y for x, y in zip(zone, building)]

  @staticmethod
  def _set_building_demands(building):
    building.heating_demand[cte.YEAR] = [0]
    building.heating_demand[cte.MONTH] = [0] * 12
    building.heating_demand[cte.HOUR] = [0] * cte.HOURS_A_YEAR

    building.cooling_demand[cte.YEAR] = [0]
    building.cooling_demand[cte.MONTH] = [0] * 12
    building.cooling_demand[cte.HOUR] = [0] * cte.HOURS_A_YEAR

    building.domestic_hot_water_heat_demand[cte.YEAR] = [0]
    building.domestic_hot_water_heat_demand[cte.MONTH] = [0] * 12
    building.domestic_hot_water_heat_demand[cte.HOUR] = [0] * cte.HOURS_A_YEAR

    building.appliances_electrical_demand[cte.YEAR] = [0]
    building.appliances_electrical_demand[cte.MONTH] = [0] * 12
    building.appliances_electrical_demand[cte.HOUR] = [0] * cte.HOURS_A_YEAR

    building.lighting_electrical_demand[cte.YEAR] = [0]
    building.lighting_electrical_demand[cte.MONTH] = [0] * 12
    building.lighting_electrical_demand[cte.HOUR] = [0] * cte.HOURS_A_YEAR

    for zone in building.internal_zones:
      for period in cte.PERIODS:
        building.heating_demand[period] = EnergyPlus._sum(zone.heating_demand[period], building.heating_demand[period])
        building.cooling_demand[period] = EnergyPlus._sum(zone.cooling_demand[period], building.cooling_demand[period])
        building.domestic_hot_water_heat_demand[period] = EnergyPlus._sum(zone.domestic_hot_water_heat_demand[period], building.domestic_hot_water_heat_demand[period])
        building.appliances_electrical_demand[period] = EnergyPlus._sum(zone.appliances_electrical_demand[period], building.appliances_electrical_demand[period])
        building.lighting_electrical_demand[period] = EnergyPlus._sum(zone.lighting_electrical_demand[period], building.lighting_electrical_demand[period])
