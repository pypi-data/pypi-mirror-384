"""
Insel monthly energy balance
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guillermo.GutierrezMorote@concordia.ca
"""
import logging
from pathlib import Path
import csv

import hub.helpers.constants as cte


class InselMonthlyEnergyBalance:
  """
  Import insel monthly energy balance results
  """
  def __init__(self, city, base_path):

    self._city = city
    self._base_path = base_path

  @staticmethod
  def _conditioning_demand(insel_output_file_path):
    heating = []
    cooling = []
    with open(Path(insel_output_file_path).resolve(), 'r', encoding='utf8') as csv_file:
      csv_reader = csv.reader(csv_file)
      for line in csv_reader:
        demand = str(line).replace("['", '').replace("']", '').split()
        for i in range(0, 2):
          if demand[i] != 'NaN':
            aux = float(demand[i]) * cte.WATTS_HOUR_TO_JULES * 1000  # kWh to J
            demand[i] = str(aux)
          else:
            demand[i] = '0'
        heating.append(float(demand[0]))
        cooling.append(float(demand[1]))
    return heating, cooling

  def _dhw_and_electric_demand(self):
    for building in self._city.buildings:
      domestic_hot_water_demand = []
      lighting_demand = []
      appliances_demand = []

      # todo: REFACTOR after retrofit project, this is a hack for the pickle files
      try:
        if building.internal_zones[0].thermal_zones_from_internal_zones is None:
          domestic_hot_water_demand = [0] * 12
          lighting_demand = [0] * 12
          appliances_demand = [0] * 12
        else:
          thermal_zone = building.internal_zones[0].thermal_zones_from_internal_zones[0]
          area = thermal_zone.total_floor_area
          cold_water = building.cold_water_temperature[cte.MONTH]
          peak_flow = thermal_zone.domestic_hot_water.peak_flow
          service_temperature = thermal_zone.domestic_hot_water.service_temperature
          lighting_density = thermal_zone.lighting.density
          appliances_density = thermal_zone.appliances.density

          for i_month, month in enumerate(cte.MONTHS):
            total_dhw_demand = 0
            total_lighting = 0
            total_appliances = 0

            for schedule in thermal_zone.lighting.schedules:
              total_day = 0
              for value in schedule.values:
                total_day += value
              for day_type in schedule.day_types:
                total_lighting += total_day * cte.WEEK_DAYS_A_MONTH[month][day_type] \
                                  * lighting_density * cte.WATTS_HOUR_TO_JULES
            lighting_demand.append(total_lighting * area)

            for schedule in thermal_zone.appliances.schedules:
              total_day = 0
              for value in schedule.values:
                total_day += value
              for day_type in schedule.day_types:
                total_appliances += total_day * cte.WEEK_DAYS_A_MONTH[month][day_type] \
                                    * appliances_density * cte.WATTS_HOUR_TO_JULES
            appliances_demand.append(total_appliances * area)

            for schedule in thermal_zone.domestic_hot_water.schedules:
              total_day = 0
              for value in schedule.values:
                total_day += value
              for day_type in schedule.day_types:
                demand = (
                    peak_flow * cte.WATER_DENSITY * cte.WATER_HEAT_CAPACITY
                    * (service_temperature - cold_water[i_month]) * cte.WATTS_HOUR_TO_JULES
                )
                total_dhw_demand += total_day * cte.WEEK_DAYS_A_MONTH[month][day_type] * demand
            domestic_hot_water_demand.append(total_dhw_demand * area)
      except AttributeError:
        domestic_hot_water_demand = [0] * 12
        lighting_demand = [0] * 12
        appliances_demand = [0] * 12
        logging.warning('Building internal zone raised an error, most likely the building has missing archetypes')

      building.domestic_hot_water_heat_demand[cte.MONTH] = domestic_hot_water_demand
      building.domestic_hot_water_heat_demand[cte.YEAR] = [sum(domestic_hot_water_demand)]
      building.lighting_electrical_demand[cte.MONTH] = lighting_demand
      building.lighting_electrical_demand[cte.YEAR] = [sum(lighting_demand)]
      building.appliances_electrical_demand[cte.MONTH] = appliances_demand
      building.appliances_electrical_demand[cte.YEAR] = [sum(appliances_demand)]

  def enrich(self):
    """
    Enrich the city by using the insel monthly energy balance output files (J)
    :return: None
    """
    for building in self._city.buildings:
      file_name = f'{building.name}.out'
      insel_output_file_path = Path(self._base_path / file_name).resolve()
      if insel_output_file_path.is_file():
        building.heating_demand[cte.MONTH], building.cooling_demand[cte.MONTH] \
          = self._conditioning_demand(insel_output_file_path)
        building.heating_demand[cte.YEAR] = [sum(building.heating_demand[cte.MONTH])]
        building.cooling_demand[cte.YEAR] = [sum(building.cooling_demand[cte.MONTH])]
    self._dhw_and_electric_demand()
