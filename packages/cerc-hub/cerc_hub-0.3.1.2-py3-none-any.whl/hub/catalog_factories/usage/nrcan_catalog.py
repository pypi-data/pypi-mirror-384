"""
NRCAN usage catalog
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
Code contributors: Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

import json
import urllib.request
from pathlib import Path

import xmltodict

import hub.helpers.constants as cte
from hub.catalog_factories.catalog import Catalog
from hub.catalog_factories.data_models.usages.appliances import Appliances
from hub.catalog_factories.data_models.usages.content import Content
from hub.catalog_factories.data_models.usages.lighting import Lighting
from hub.catalog_factories.data_models.usages.occupancy import Occupancy
from hub.catalog_factories.data_models.usages.domestic_hot_water import DomesticHotWater
from hub.catalog_factories.data_models.usages.schedule import Schedule
from hub.catalog_factories.data_models.usages.thermal_control import ThermalControl
from hub.catalog_factories.data_models.usages.usage import Usage
from hub.catalog_factories.usage.usage_helper import UsageHelper


class NrcanCatalog(Catalog):
  """
  Nrcan catalog class
  """
  def __init__(self, path):
    self._schedules_path = Path(path / 'nrcan_schedules.json').resolve()
    self._space_types_path = Path(path / 'nrcan_space_types.json').resolve()
    self._space_compliance_path = Path(path / 'nrcan_space_compliance_2015.json').resolve()
    self._content = None
    self._schedules = {}
    self._load_schedules()
    self._content = Content(self._load_archetypes())

  @staticmethod
  def _extract_schedule(raw):
    nrcan_schedule_type = raw['category']
    if 'Heating' in raw['name'] and 'Water' not in raw['name']:
      nrcan_schedule_type = f'{nrcan_schedule_type} Heating'
    elif 'Cooling' in raw['name']:
      nrcan_schedule_type = f'{nrcan_schedule_type} Cooling'
    if nrcan_schedule_type not in UsageHelper().nrcan_schedule_type_to_hub_schedule_type:
      return None
    hub_type = UsageHelper().nrcan_schedule_type_to_hub_schedule_type[nrcan_schedule_type]
    data_type = UsageHelper().nrcan_data_type_to_hub_data_type[raw['units']]
    time_step = UsageHelper().nrcan_time_to_hub_time[raw['type']]
    # nrcan only uses daily range for the schedules
    time_range = cte.DAY
    day_types = UsageHelper().nrcan_day_type_to_hub_days[raw['day_types']]
    return Schedule(hub_type, raw['values'], data_type, time_step, time_range, day_types)

  def _load_schedules(self):
    _schedule_types = []
    with open(self._schedules_path, 'r') as f:
      schedules_type = json.load(f)
    for schedule_type in schedules_type['tables']['schedules']['table']:
      schedule = NrcanCatalog._extract_schedule(schedule_type)
      if schedule_type['name'] not in _schedule_types:
        _schedule_types.append(schedule_type['name'])
        if schedule is not None:
          self._schedules[schedule_type['name']] = [schedule]
      else:
        if schedule is not None:
          _schedules = self._schedules[schedule_type['name']]
          _schedules.append(schedule)
          self._schedules[schedule_type['name']] = _schedules

  def _get_schedules(self, name):
    schedule = None
    if name in self._schedules:
      schedule = self._schedules[name]
    return schedule

  def _load_archetypes(self):
    usages = []
    with open(self._space_types_path, 'r') as f:
      space_types = json.load(f)['tables']['space_types']['table']
    space_types = [st for st in space_types if st['space_type'] == 'WholeBuilding']
    with open(self._space_compliance_path, 'r') as f:
      space_types_compliance = json.load(f)['tables']['space_compliance']['table']
    space_types_compliance = [st for st in space_types_compliance if st['space_type'] == 'WholeBuilding']
    space_types_dictionary = {}
    for space_type in space_types_compliance:
      usage_type = space_type['building_type']
      # people/m2
      occupancy_density = space_type['occupancy_per_area_people_per_m2']
      # W/m2
      lighting_density = space_type['lighting_per_area_w_per_m2']
      # W/m2
      appliances_density = space_type['electric_equipment_per_area_w_per_m2']
      # peak flow in gallons/h/m2
      domestic_hot_water_peak_flow = (
          space_type['service_water_heating_peak_flow_per_area'] *
          cte.GALLONS_TO_QUBIC_METERS / cte.HOUR_TO_SECONDS
      )
      space_types_dictionary[usage_type] = {'occupancy_per_area': occupancy_density,
                                            'lighting_per_area': lighting_density,
                                            'electric_equipment_per_area': appliances_density,
                                            'service_water_heating_peak_flow_per_area': domestic_hot_water_peak_flow
                                            }

    for space_type in space_types:
      usage_type = space_type['building_type']
      space_type_compliance = space_types_dictionary[usage_type]
      occupancy_density = space_type_compliance['occupancy_per_area']
      lighting_density = space_type_compliance['lighting_per_area']
      appliances_density = space_type_compliance['electric_equipment_per_area']
      domestic_hot_water_peak_flow = space_type_compliance['service_water_heating_peak_flow_per_area']

      occupancy_schedule_name = space_type['occupancy_schedule']
      lighting_schedule_name = space_type['lighting_schedule']
      appliance_schedule_name = space_type['electric_equipment_schedule']
      hvac_schedule_name = space_type['exhaust_schedule']
      if 'FAN' in hvac_schedule_name:
        hvac_schedule_name = hvac_schedule_name.replace('FAN', 'Fan')
      heating_setpoint_schedule_name = space_type['heating_setpoint_schedule']
      cooling_setpoint_schedule_name = space_type['cooling_setpoint_schedule']
      domestic_hot_water_schedule_name = space_type['service_water_heating_schedule']
      occupancy_schedule = self._get_schedules(occupancy_schedule_name)
      lighting_schedule = self._get_schedules(lighting_schedule_name)
      appliance_schedule = self._get_schedules(appliance_schedule_name)
      heating_schedule = self._get_schedules(heating_setpoint_schedule_name)
      cooling_schedule = self._get_schedules(cooling_setpoint_schedule_name)
      hvac_availability = self._get_schedules(hvac_schedule_name)
      domestic_hot_water_load_schedule = self._get_schedules(domestic_hot_water_schedule_name)

      # ACH -> 1/s
      mechanical_air_change = space_type['ventilation_air_changes'] / cte.HOUR_TO_SECONDS
      # cfm/ft2 to m3/m2.s
      ventilation_rate = space_type['ventilation_per_area'] / (cte.METERS_TO_FEET * cte.MINUTES_TO_SECONDS)
      # cfm/person to m3/m2.s
      ventilation_rate += space_type['ventilation_per_person'] / (
          pow(cte.METERS_TO_FEET, 3) * cte.MINUTES_TO_SECONDS
      ) * occupancy_density

      lighting_radiative_fraction = space_type['lighting_fraction_radiant']
      lighting_convective_fraction = 0
      if lighting_radiative_fraction is not None:
        lighting_convective_fraction = 1 - lighting_radiative_fraction
      lighting_latent_fraction = 0
      appliances_radiative_fraction = space_type['electric_equipment_fraction_radiant']
      appliances_latent_fraction = space_type['electric_equipment_fraction_latent']
      appliances_convective_fraction = 0
      if appliances_radiative_fraction is not None and appliances_latent_fraction is not None:
        appliances_convective_fraction = 1 - appliances_radiative_fraction - appliances_latent_fraction

      domestic_hot_water_service_temperature = space_type['service_water_heating_target_temperature']

      occupancy = Occupancy(occupancy_density,
                            None,
                            None,
                            None,
                            occupancy_schedule)
      lighting = Lighting(lighting_density,
                          lighting_convective_fraction,
                          lighting_radiative_fraction,
                          lighting_latent_fraction,
                          lighting_schedule)
      appliances = Appliances(appliances_density,
                              appliances_convective_fraction,
                              appliances_radiative_fraction,
                              appliances_latent_fraction,
                              appliance_schedule)
      thermal_control = ThermalControl(None,
                                       None,
                                       None,
                                       hvac_availability,
                                       heating_schedule,
                                       cooling_schedule)
      domestic_hot_water = DomesticHotWater(None,
                                            domestic_hot_water_peak_flow,
                                            domestic_hot_water_service_temperature,
                                            domestic_hot_water_load_schedule)

      hours_day = None
      days_year = None
      usages.append(Usage(usage_type,
                          hours_day,
                          days_year,
                          mechanical_air_change,
                          ventilation_rate,
                          occupancy,
                          lighting,
                          appliances,
                          thermal_control,
                          domestic_hot_water))
    return usages

  def names(self, category=None):
    """
    Get the catalog elements names
    :parm: for usage catalog category filter does nothing as there is only one category (usages)
    """
    _names = {'usages': []}
    for usage in self._content.usages:
      _names['usages'].append(usage.name)
    return _names

  def entries(self, category=None):
    """
    Get the catalog elements
    :parm: for usage catalog category filter does nothing as there is only one category (usages)
    """
    return self._content

  def get_entry(self, name):
    """
    Get one catalog element by names
    :parm: entry name
    """
    for usage in self._content.usages:
      if usage.name.lower() == name.lower():
        return usage
    raise IndexError(f"{name} doesn't exists in the catalog")
