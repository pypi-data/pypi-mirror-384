"""
EilatUsageParameters extracts the usage properties from Eilat catalog and assigns to each building
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""
import copy
import logging
import numpy
import hub.helpers.constants as cte
from hub.helpers.dictionaries import Dictionaries
from hub.city_model_structure.building_demand.usage import Usage
from hub.city_model_structure.building_demand.lighting import Lighting
from hub.city_model_structure.building_demand.occupancy import Occupancy
from hub.city_model_structure.building_demand.appliances import Appliances
from hub.city_model_structure.building_demand.thermal_control import ThermalControl
from hub.city_model_structure.building_demand.domestic_hot_water import DomesticHotWater
from hub.city_model_structure.attributes.schedule import Schedule
from hub.city_model_structure.building_demand.internal_gain import InternalGain
from hub.catalog_factories.usage_catalog_factory import UsageCatalogFactory


class EilatUsageParameters:
  """
  EilatUsageParameters class
  """
  def __init__(self, city):
    self._city = city

  def enrich_buildings(self):
    """
    Returns the city with the usage parameters assigned to the buildings
    :return:
    """
    city = self._city
    eilat_catalog = UsageCatalogFactory('eilat').catalog
    for building in city.buildings:
      usage_name = Dictionaries().hub_usage_to_eilat_usage[building.function]
      try:
        archetype_usage = self._search_archetypes(eilat_catalog, usage_name)
      except KeyError:
        logging.error('Building %s has unknown usage archetype for usage %s', building.name, usage_name)
        continue

      for internal_zone in building.internal_zones:
        if internal_zone.area is None:
          raise TypeError('Internal zone area not defined, ACH cannot be calculated')
        if internal_zone.volume is None:
          raise TypeError('Internal zone volume not defined, ACH cannot be calculated')
        if internal_zone.area <= 0:
          raise TypeError('Internal zone area is zero, ACH cannot be calculated')
        volume_per_area = internal_zone.volume / internal_zone.area
        usage = Usage()
        usage.name = usage_name
        self._assign_values(usage, archetype_usage, volume_per_area, building.cold_water_temperature)
        usage.percentage = 1
        self._calculate_reduced_values_from_extended_library(usage, archetype_usage)

        internal_zone.usages = [usage]

  @staticmethod
  def _search_archetypes(eilat_catalog, usage_name):
    eilat_archetypes = eilat_catalog.entries('archetypes').usages
    for building_archetype in eilat_archetypes:
      if str(usage_name) == str(building_archetype.name):
        return building_archetype
    raise KeyError('archetype not found')

  @staticmethod
  def _assign_values(usage, archetype, volume_per_area, cold_water_temperature):
    # Due to the fact that python is not a typed language, the wrong object type is assigned to
    # usage.occupancy when writing usage.occupancy = archetype.occupancy.
    # Same happens for lighting and appliances. Therefore, this walk around has been done.
    usage.mechanical_air_change = archetype.ventilation_rate / volume_per_area
    _occupancy = Occupancy()
    _occupancy.occupancy_density = archetype.occupancy.occupancy_density
    _occupancy.sensible_radiative_internal_gain = archetype.occupancy.sensible_radiative_internal_gain
    _occupancy.latent_internal_gain = archetype.occupancy.latent_internal_gain
    _occupancy.sensible_convective_internal_gain = archetype.occupancy.sensible_convective_internal_gain
    _occupancy.occupancy_schedules = archetype.occupancy.schedules
    usage.occupancy = _occupancy
    _lighting = Lighting()
    _lighting.density = archetype.lighting.density
    _lighting.convective_fraction = archetype.lighting.convective_fraction
    _lighting.radiative_fraction = archetype.lighting.radiative_fraction
    _lighting.latent_fraction = archetype.lighting.latent_fraction
    _lighting.schedules = archetype.lighting.schedules
    usage.lighting = _lighting
    _appliances = Appliances()
    _appliances.density = archetype.appliances.density
    _appliances.convective_fraction = archetype.appliances.convective_fraction
    _appliances.radiative_fraction = archetype.appliances.radiative_fraction
    _appliances.latent_fraction = archetype.appliances.latent_fraction
    _appliances.schedules = archetype.appliances.schedules
    usage.appliances = _appliances
    _control = ThermalControl()
    _control.cooling_set_point_schedules = archetype.thermal_control.cooling_set_point_schedules
    _control.heating_set_point_schedules = archetype.thermal_control.heating_set_point_schedules
    _control.hvac_availability_schedules = archetype.thermal_control.hvac_availability_schedules
    usage.thermal_control = _control
    _domestic_hot_water = DomesticHotWater()
    _domestic_hot_water.density = archetype.domestic_hot_water.density
    _domestic_hot_water.service_temperature = archetype.domestic_hot_water.service_temperature
    peak_flow = None
    if len(cold_water_temperature) > 0:
      cold_temperature = cold_water_temperature[cte.YEAR][0]
      peak_flow = 0
      if (archetype.domestic_hot_water.service_temperature - cold_temperature) > 0:
        peak_flow = archetype.domestic_hot_water.density / cte.WATER_DENSITY / cte.WATER_HEAT_CAPACITY \
                    / (archetype.domestic_hot_water.service_temperature - cold_temperature)
    _domestic_hot_water.peak_flow = peak_flow
    _domestic_hot_water.schedules = archetype.domestic_hot_water.schedules
    usage.domestic_hot_water = _domestic_hot_water

  @staticmethod
  def _calculate_reduced_values_from_extended_library(usage, archetype):
    number_of_days_per_type = {'WD': 231, 'Fri': 52, 'Sat': 82}
    total = 0
    for schedule in archetype.thermal_control.hvac_availability_schedules:
      if schedule.day_types[0] == cte.SATURDAY:
        for value in schedule.values:
          total += value * number_of_days_per_type['Fri']
      elif schedule.day_types[0] == cte.SUNDAY:
        for value in schedule.values:
          total += value * number_of_days_per_type['Sat']
      else:
        for value in schedule.values:
          total += value * number_of_days_per_type['WD']

    usage.hours_day = total / 365
    usage.days_year = 365

    max_heating_setpoint = cte.MIN_FLOAT
    min_heating_setpoint = cte.MAX_FLOAT

    for schedule in archetype.thermal_control.heating_set_point_schedules:
      if schedule.values is None:
        max_heating_setpoint = None
        min_heating_setpoint = None
        break
      if max(schedule.values) > max_heating_setpoint:
        max_heating_setpoint = max(schedule.values)
      if min(schedule.values) < min_heating_setpoint:
        min_heating_setpoint = min(schedule.values)

    min_cooling_setpoint = cte.MAX_FLOAT
    for schedule in archetype.thermal_control.cooling_set_point_schedules:
      if schedule.values is None:
        min_cooling_setpoint = None
        break
      if min(schedule.values) < min_cooling_setpoint:
        min_cooling_setpoint = min(schedule.values)

    usage.thermal_control.mean_heating_set_point = max_heating_setpoint
    usage.thermal_control.heating_set_back = min_heating_setpoint
    usage.thermal_control.mean_cooling_set_point = min_cooling_setpoint

  @staticmethod
  def _calculate_internal_gains(archetype):

    _days = [cte.MONDAY, cte.TUESDAY, cte.WEDNESDAY, cte.THURSDAY, cte.FRIDAY, cte.SATURDAY, cte.SUNDAY, cte.HOLIDAY]
    _number_of_days_per_type = [51, 50, 50, 50, 50, 52, 52, 10]

    _mean_internal_gain = InternalGain()
    _mean_internal_gain.type = 'mean_value_of_internal_gains'
    _base_schedule = Schedule()
    _base_schedule.type = cte.INTERNAL_GAINS
    _base_schedule.time_range = cte.DAY
    _base_schedule.time_step = cte.HOUR
    _base_schedule.data_type = cte.FRACTION

    _latent_heat_gain = archetype.occupancy.latent_internal_gain
    _convective_heat_gain = archetype.occupancy.sensible_convective_internal_gain
    _radiative_heat_gain = archetype.occupancy.sensible_radiative_internal_gain
    _total_heat_gain = _latent_heat_gain + _convective_heat_gain + _radiative_heat_gain

    _schedule_values = numpy.zeros([24, 8])
    _sum = 0
    for day, _schedule in enumerate(archetype.occupancy.schedules):
      for v_index, value in enumerate(_schedule.values):
        _schedule_values[v_index, day] = value * _total_heat_gain
        _sum += value * _total_heat_gain * _number_of_days_per_type[day]

    _total_heat_gain += archetype.lighting.density + archetype.appliances.density
    _latent_heat_gain += (
        archetype.lighting.latent_fraction * archetype.lighting.density + archetype.appliances.latent_fraction *
        archetype.appliances.density
    )
    _radiative_heat_gain = (
        archetype.lighting.radiative_fraction * archetype.lighting.density + archetype.appliances.radiative_fraction *
        archetype.appliances.density
    )
    _convective_heat_gain = (
      archetype.lighting.convective_fraction * archetype.lighting.density + archetype.appliances.convective_fraction *
      archetype.appliances.density
    )

    for day, _schedule in enumerate(archetype.lighting.schedules):
      for v_index, value in enumerate(_schedule.values):
        _schedule_values[v_index, day] += value * archetype.lighting.density
        _sum += value * archetype.lighting.density * _number_of_days_per_type[day]

    for day, _schedule in enumerate(archetype.appliances.schedules):
      for v_index, value in enumerate(_schedule.values):
        _schedule_values[v_index, day] += value * archetype.appliances.density
        _sum += value * archetype.appliances.density * _number_of_days_per_type[day]

    _latent_fraction = 0
    _radiative_fraction = 0
    _convective_fraction = 0
    _average_internal_gain = 0
    if _total_heat_gain != 0:
      _latent_fraction = _latent_heat_gain / _total_heat_gain
      _radiative_fraction = _radiative_heat_gain / _total_heat_gain
      _convective_fraction = _convective_heat_gain / _total_heat_gain
      _average_internal_gain = _sum / _total_heat_gain

    _schedules = []
    for day, current_day in enumerate(_days):
      _schedule = copy.deepcopy(_base_schedule)
      _schedule.day_types = [current_day]
      _schedule.values = _schedule_values[:day]
      _schedules.append(_schedule)

    _mean_internal_gain.average_internal_gain = _average_internal_gain
    _mean_internal_gain.latent_fraction = _latent_fraction
    _mean_internal_gain.convective_fraction = _convective_fraction
    _mean_internal_gain.radiative_fraction = _radiative_fraction
    _mean_internal_gain.schedules = _schedules

    return [_mean_internal_gain]
