"""
Comnet usage catalog
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""
import io
from typing import Dict

import pandas as pd

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
from hub.helpers.configuration_helper import ConfigurationHelper as ch


class ComnetCatalog(Catalog):
  """
  Comnet catalog class
  """
  def __init__(self, path):
    self._comnet_archetypes_path = str(path / 'comnet_archetypes.xlsx')
    self._comnet_schedules_path = str(path / 'comnet_schedules_archetypes.xlsx')
    self._archetypes = self._read_archetype_file()
    self._schedules = self._read_schedules_file()

    sensible_convective = ch().comnet_occupancy_sensible_convective
    sensible_radiative = ch().comnet_occupancy_sensible_radiant
    lighting_convective = ch().comnet_lighting_convective
    lighting_radiative = ch().comnet_lighting_radiant
    lighting_latent = ch().comnet_lighting_latent
    appliances_convective = ch().comnet_plugs_convective
    appliances_radiative = ch().comnet_plugs_radiant
    appliances_latent = ch().comnet_plugs_latent

    usages = []
    for schedule_key in self._archetypes['schedules_key']:
      comnet_usage = schedule_key
      schedule_name = self._archetypes['schedules_key'][schedule_key]
      hours_day = None
      days_year = None
      occupancy_archetype = self._archetypes['occupancy'][comnet_usage]
      lighting_archetype = self._archetypes['lighting'][comnet_usage]
      appliances_archetype = self._archetypes['plug loads'][comnet_usage]
      mechanical_air_change = None  # comnet provides ventilation rate only
      ventilation_rate = self._archetypes['ventilation rate'][comnet_usage]
      # convert cfm/ft2 to m3/m2.s
      ventilation_rate = ventilation_rate / (cte.METERS_TO_FEET * cte.MINUTES_TO_SECONDS)
      domestic_hot_water_archetype = self._archetypes['water heating'][comnet_usage]

      # get occupancy
      occupancy_density = occupancy_archetype[0] / pow(cte.METERS_TO_FEET, 2)
      sensible_heat_gain = occupancy_archetype[1] * cte.BTU_H_TO_WATTS
      latent_heat_gain = occupancy_archetype[1] * cte.BTU_H_TO_WATTS
      if occupancy_density != 0:
        occupancy_density = 1 / occupancy_density
      sensible_convective_internal_gain = occupancy_density * sensible_heat_gain * sensible_convective
      sensible_radiative_internal_gain = occupancy_density * sensible_heat_gain * sensible_radiative
      latent_internal_gain = occupancy_density * latent_heat_gain
      occupancy = Occupancy(occupancy_density,
                            sensible_convective_internal_gain,
                            sensible_radiative_internal_gain,
                            latent_internal_gain,
                            self._schedules[schedule_name]['Occupancy'])

      # get lighting
      density = lighting_archetype[4] * pow(cte.METERS_TO_FEET, 2)
      lighting = Lighting(density,
                          lighting_convective,
                          lighting_radiative,
                          lighting_latent,
                          self._schedules[schedule_name]['Lights'])

      # get appliances
      density = appliances_archetype[0]
      if density == 'n.a.':
        density = 0
      # convert W/ft2 to W/m2
      density = float(density) * pow(cte.METERS_TO_FEET, 2)
      appliances = Appliances(density,
                              appliances_convective,
                              appliances_radiative,
                              appliances_latent,
                              self._schedules[schedule_name]['Receptacle'])

      # get thermal control
      thermal_control = ThermalControl(None,
                                       None,
                                       None,
                                       self._schedules[schedule_name]['HVAC Avail'],
                                       self._schedules[schedule_name]['HtgSetPt'],
                                       self._schedules[schedule_name]['ClgSetPt']
                                       )

      # get domestic hot water
      density = domestic_hot_water_archetype
      # convert Btu/h/occ to W/m2
      density = float(density) * cte.BTU_H_TO_WATTS * occupancy_density
      domestic_hot_water_service_temperature = self._schedules[schedule_name]['WtrHtrSetPt'][0].values[0]
      domestic_hot_water = DomesticHotWater(density,
                                            None,
                                            domestic_hot_water_service_temperature,
                                            self._schedules[schedule_name]['Service Hot Water']
                                            )
      usages.append(Usage(comnet_usage,
                          hours_day,
                          days_year,
                          mechanical_air_change,
                          ventilation_rate,
                          occupancy,
                          lighting,
                          appliances,
                          thermal_control,
                          domestic_hot_water))

    self._content = Content(usages)

  def _read_schedules_file(self) -> Dict:
    dictionary = {}
    comnet_usages = UsageHelper().comnet_schedules_key_to_comnet_schedules
    comnet_days = UsageHelper().comnet_days
    comnet_data_types = UsageHelper().comnet_data_type_to_hub_data_type
    for usage_name in comnet_usages:
      if usage_name == 'C-13 Data Center':
        continue
      with open(self._comnet_schedules_path, 'rb') as xls:
        _extracted_data = pd.read_excel(
          io.BytesIO(xls.read()),
          sheet_name=comnet_usages[usage_name],
          skiprows=[0, 1, 2, 3], nrows=39, usecols="A:AA"
        )
        _schedules = {}
        for row in range(0, 39, 3):
          _schedule_values = {}
          schedule_name = _extracted_data.loc[row:row, 'Description'].item()
          schedule_data_type = comnet_data_types[_extracted_data.loc[row:row, 'Type'].item()]
          for day in comnet_days:
            # Monday to Friday
            start = row
            end = row + 1
            if day == cte.SATURDAY:
              start = start + 1
              end = end + 1
            elif day in (cte.SUNDAY, cte.HOLIDAY):
              start = start + 2
              end = end + 2
            _schedule_values[day] = _extracted_data.iloc[start:end, 3:27].to_numpy().tolist()[0]
          _schedule = []
          for day in _schedule_values:
            if schedule_name in ('ClgSetPt', 'HtgSetPt', 'WtrHtrSetPt'):
              # to celsius
              if 'n.a.' in _schedule_values[day]:
                _schedule_values[day] = None
              else:
                _schedule_values[day] = [(float(value)-32)*5/9 for value in _schedule_values[day]]
            _schedule.append(Schedule(schedule_name, _schedule_values[day], schedule_data_type, cte.HOUR, cte.DAY, [day]))
          _schedules[schedule_name] = _schedule
        dictionary[usage_name] = _schedules
    return dictionary

  def _read_archetype_file(self) -> Dict:
    """
    reads xlsx files containing usage information into a dictionary
    :return : Dict
    """
    number_usage_types = 33
    with open(self._comnet_archetypes_path, 'rb') as xls:
      _extracted_data = pd.read_excel(
        io.BytesIO(xls.read()),
        sheet_name="Modeling Data",
        skiprows=[0, 1, 2, 24],
        nrows=number_usage_types, usecols="A:AB"
      )

    lighting_data = {}
    plug_loads_data = {}
    occupancy_data = {}
    ventilation_rate = {}
    water_heating = {}
    process_data = {}
    schedules_key = {}
    for j in range(0, number_usage_types-1):
      usage_parameters = _extracted_data.iloc[j]
      usage_type = usage_parameters.iloc[0]
      lighting_data[usage_type] = usage_parameters.iloc[1:6].values.tolist()
      plug_loads_data[usage_type] = usage_parameters.iloc[8:13].values.tolist()
      occupancy_data[usage_type] = usage_parameters.iloc[17:20].values.tolist()
      ventilation_rate[usage_type] = usage_parameters.iloc[20:21].item()
      water_heating[usage_type] = usage_parameters.iloc[23:24].item()
      process_data[usage_type] = usage_parameters.iloc[24:26].values.tolist()
      schedules_key[usage_type] = usage_parameters.iloc[27:28].item()

    return {'lighting': lighting_data,
            'plug loads': plug_loads_data,
            'occupancy': occupancy_data,
            'ventilation rate': ventilation_rate,
            'water heating': water_heating,
            'process': process_data,
            'schedules_key': schedules_key
            }

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
