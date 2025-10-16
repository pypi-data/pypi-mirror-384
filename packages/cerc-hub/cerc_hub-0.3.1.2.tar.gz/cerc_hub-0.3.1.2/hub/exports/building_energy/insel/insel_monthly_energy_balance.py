"""
InselMonthlyEnergyBalance exports models to insel format
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

import logging
from pathlib import Path

import numpy as np

import hub.helpers.constants as cte
from hub.imports.weather.helpers.weather import Weather

_CONSTRUCTION_CODE = {
  cte.WALL: '1',
  cte.GROUND: '2',
  cte.ROOF: '3',
  cte.INTERIOR_WALL: '5',
  cte.GROUND_WALL: '6',
  cte.ATTIC_FLOOR: '7',
  cte.INTERIOR_SLAB: '8'
}

_NUMBER_DAYS_PER_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


class InselMonthlyEnergyBalance:
  """
  Insel monthly energy balance class
  """
  def __init__(self, city, path, custom_insel_block):
    self._city = city
    self._path = path
    self._custom_insel_block = custom_insel_block
    self._results = None
    self._contents = []
    self._insel_files_paths = []
    self._sanity_check()
    for building in city.buildings:
      self._insel_files_paths.append(building.name + '.insel')
      file_name_out = building.name + '.out'
      output_path = Path(self._path / file_name_out).resolve()
      skip_building = False
      for internal_zone in building.internal_zones:
        if internal_zone.thermal_archetype is None:
          logging.warning('Building %s has missing values. Monthly Energy Balance cannot be processed', building.name)
          skip_building = True
          break
      if skip_building:
        continue
      if building.thermal_zones_from_internal_zones is None:
        logging.warning('Building %s has missing values. Monthly Energy Balance cannot be processed', building.name)

      self._contents.append(
        self._generate_meb_template(building, output_path, self._custom_insel_block)
      )
    self._export()

  @staticmethod
  def _add_block(file, block_number, block_type, inputs=None, parameters=None):
    file += "S " + str(block_number) + " " + block_type + "\n"
    if inputs is not None:
      for block_input in inputs:
        file += str(block_input) + "\n"
    if parameters is not None:
      if len(parameters) > 0:
        file += "P " + str(block_number) + "\n"
      for block_parameter in parameters:
        file += str(block_parameter) + "\n"
    return file

  def _export(self):
    for i_file, content in enumerate(self._contents):
      file_name = self._insel_files_paths[i_file]
      with open(Path(self._path / file_name).resolve(), 'w', encoding='utf8') as insel_file:
        insel_file.write(content)

  def _sanity_check(self):
    levels_of_detail = self._city.level_of_detail
    if levels_of_detail.geometry is None:
      raise AttributeError('Level of detail of geometry not assigned')
    if levels_of_detail.geometry < 1:
      raise AttributeError(f'Level of detail of geometry = {levels_of_detail.geometry}. Required minimum level 1')
    if levels_of_detail.construction is None:
      raise AttributeError('Level of detail of construction not assigned')
    if levels_of_detail.construction < 1:
      raise AttributeError(f'Level of detail of construction = {levels_of_detail.construction}. Required minimum level 1')
    if levels_of_detail.usage is None:
      raise AttributeError('Level of detail of usage not assigned')
    if levels_of_detail.usage < 1:
      raise AttributeError(f'Level of detail of usage = {levels_of_detail.usage}. Required minimum level 1')
    if levels_of_detail.weather is None:
      raise AttributeError('Level of detail of weather not assigned')
    if levels_of_detail.weather < 1:
      raise AttributeError(f'Level of detail of weather = {levels_of_detail.weather}. Required minimum level 1')
    if levels_of_detail.surface_radiation is None:
      raise AttributeError('Level of detail of surface radiation not assigned')
    if levels_of_detail.surface_radiation < 1:
      raise AttributeError(f'Level of detail of surface radiation = {levels_of_detail.surface_radiation}. '
                           f'Required minimum level 1')

  @staticmethod
  def _generate_meb_template(building, insel_outputs_path, custom_insel_block):
    file = ""
    i_block = 1
    parameters = ["1", "12", "1"]
    file = InselMonthlyEnergyBalance._add_block(file, i_block, 'DO', parameters=parameters)

    i_block = 4
    inputs = ["1.1", "20.1", "21.1"]
    surfaces = building.surfaces
    for i in range(1, len(surfaces) + 1):
      inputs.append(f"{str(100 + i)}.1 % Radiation surface {str(i)}")

    number_of_storeys = int(building.eave_height / building.average_storey_height)
    attic_heated = building.attic_heated
    basement_heated = building.basement_heated
    if building.attic_heated is None:
      attic_heated = 0
    if building.basement_heated is None:
      basement_heated = 0

    # BUILDING PARAMETERS
    parameters = [f'{building.volume} % BP(1) Heated Volume (m3)',
                  f'{building.average_storey_height} % BP(2) Average storey height (m)',
                  f'{number_of_storeys} % BP(3) Number of storeys above ground',
                  f'{attic_heated} % BP(4) Attic heating type (0=no room, 1=unheated, 2=heated)',
                  f'{basement_heated} % BP(5) Cellar heating type (0=no room, 1=unheated, 2=heated, '
                  f'99=invalid)']

    # todo: this method and the insel model have to be reviewed for more than one internal zone
    internal_zone = building.internal_zones[0]
    thermal_zone = internal_zone.thermal_zones_from_internal_zones[0]
    parameters.append(f'{thermal_zone.indirectly_heated_area_ratio} % BP(6) Indirectly heated area ratio')
    parameters.append(f'{thermal_zone.effective_thermal_capacity / 3600 / building.average_storey_height}'
                      f' % BP(7) Effective heat capacity (Wh/m2K)')
    parameters.append(f'{thermal_zone.additional_thermal_bridge_u_value} '
                      f'% BP(8) Additional U-value for heat bridge (W/m2K)')
    parameters.append('1 % BP(9) Usage type (0=standard, 1=IWU)')

    # ZONES AND SURFACES
    parameters.append(f'{len(internal_zone.usages)} %  BP(10) Number of zones')

    for i, usage in enumerate(internal_zone.usages):
      percentage_usage = usage.percentage
      parameters.append(f'{internal_zone.thermal_zones_from_internal_zones[0].total_floor_area * percentage_usage} '
                        f'% BP(11) #1 Area of zone {i + 1} (m2)')
      total_internal_gain = 0
      for i_gain in usage.internal_gains:
        internal_gain = i_gain.average_internal_gain * (i_gain.convective_fraction + i_gain.radiative_fraction)
        for schedule in i_gain.schedules:
          total_values = sum(schedule.values)
          total_hours = 0
          for day_type in schedule.day_types:
            total_hours += cte.WEEK_DAYS_A_YEAR[day_type] / 365 / 24
          total_values *= total_hours
          total_internal_gain += internal_gain * total_values

      parameters.append(f'{total_internal_gain} % BP(12) #2 Internal gains of zone {i + 1}')
      parameters.append(f'{usage.thermal_control.mean_heating_set_point} % BP(13) #3 Heating setpoint temperature '
                        f'zone {i + 1} (degree Celsius)')
      parameters.append(f'{usage.thermal_control.heating_set_back} % BP(14) #4 Heating setback temperature '
                        f'zone {i + 1} (degree Celsius)')
      parameters.append(f'{usage.thermal_control.mean_cooling_set_point} % BP(15) #5 Cooling setpoint temperature '
                        f'zone {i + 1} (degree Celsius)')
      parameters.append(f'{usage.hours_day} %  BP(16) #6 Usage hours per day zone {i + 1}')
      parameters.append(f'{usage.days_year} %  BP(17) #7 Usage days per year zone {i + 1}')

      ventilation = 0
      infiltration = 0
      for schedule in usage.thermal_control.hvac_availability_schedules:
        ventilation_day = 0
        infiltration_day = 0
        for value in schedule.values:
          if value == 0:
            infiltration_day += internal_zone.thermal_zones_from_internal_zones[0].infiltration_rate_system_off / 24 * cte.HOUR_TO_SECONDS
            ventilation_day += 0
          else:
            ventilation_value = usage.mechanical_air_change * value * cte.HOUR_TO_SECONDS
            infiltration_value = internal_zone.thermal_zones_from_internal_zones[0].infiltration_rate_system_off * value * cte.HOUR_TO_SECONDS
            if ventilation_value >= infiltration_value:
              ventilation_day += ventilation_value / 24
              infiltration_day += 0
            else:
              ventilation_day += 0
              infiltration_day += infiltration_value / 24
        for day_type in schedule.day_types:
          infiltration += infiltration_day * cte.WEEK_DAYS_A_YEAR[day_type] / 365
          ventilation += ventilation_day * cte.WEEK_DAYS_A_YEAR[day_type] / 365

      ventilation_infiltration = ventilation + infiltration
      parameters.append(f'{ventilation_infiltration} % BP(18) #8 Minimum air change rate zone {i + 1} (ACH)')

    parameters.append(f'{len(thermal_zone.thermal_boundaries)}  % Number of surfaces = BP(11+8z) \n'
                      f'% 1. Surface type (1=wall, 2=ground 3=roof, 4=flat roof)\n'
                      f'% 2. Areas above ground (m2)\n'
                      f'% 3. Areas below ground (m2)\n'
                      f'% 4. U-value (W/m2K)\n'
                      f'% 5. Window area (m2)\n'
                      f'% 6. Window frame fraction\n'
                      f'% 7. Window U-value (W/m2K)\n'
                      f'% 8. Window g-value\n'
                      f'% 9. Short-wave reflectance\n'
                      f'% #1     #2       #3      #4      #5     #6     #7     #8     #9\n')

    for thermal_boundary in thermal_zone.thermal_boundaries:
      type_code = _CONSTRUCTION_CODE[thermal_boundary.type]
      wall_area = thermal_boundary.opaque_area * (1 + thermal_boundary.window_ratio)
      if thermal_boundary.type == cte.WALL:
        if thermal_boundary.parent_surface.percentage_shared is not None:
          wall_area = wall_area * (1 - thermal_boundary.parent_surface.percentage_shared)
      window_area = wall_area * thermal_boundary.window_ratio

      parameters.append(type_code)
      if thermal_boundary.type != cte.GROUND:
        parameters.append(wall_area)
        parameters.append('0.0')
      else:
        parameters.append('0.0')
        parameters.append(wall_area)
      parameters.append(thermal_boundary.u_value)
      parameters.append(window_area)

      if window_area <= 0.001:
        parameters.append(0.0)
        parameters.append(0.0)
        parameters.append(0.0)
      else:
        thermal_opening = thermal_boundary.thermal_openings[0]
        parameters.append(thermal_opening.frame_ratio)
        parameters.append(thermal_opening.overall_u_value)
        parameters.append(thermal_opening.g_value)
      if thermal_boundary.type is not cte.GROUND:
        parameters.append(thermal_boundary.external_surface.short_wave_reflectance)
      else:
        parameters.append(0.0)
    file = InselMonthlyEnergyBalance._add_block(file, i_block, custom_insel_block, inputs=inputs, parameters=parameters)

    i_block = 20
    inputs = ['1']
    parameters = ['12 % Monthly ambient temperature (degree Celsius)']

    external_temperature = building.external_temperature[cte.MONTH]
    for i in range(0, len(external_temperature)):
      parameters.append(f'{i + 1} {external_temperature[i]}')

    file = InselMonthlyEnergyBalance._add_block(file, i_block, 'polyg', inputs=inputs, parameters=parameters)

    i_block = 21
    inputs = ['1']
    parameters = ['12 % Monthly sky temperature']

    sky_temperature = Weather.sky_temperature(external_temperature)
    for i, temperature in enumerate(sky_temperature):
      parameters.append(f'{i + 1} {temperature}')

    file = InselMonthlyEnergyBalance._add_block(file, i_block, 'polyg', inputs=inputs, parameters=parameters)
    for i, surface in enumerate(surfaces):
      i_block = 101 + i
      inputs = ['1 % Monthly surface radiation (W/m2)']
      parameters = [f'12 % Azimuth {np.rad2deg(surface.azimuth)}, '
                    f'inclination {np.rad2deg(surface.inclination)} (degrees)']

      if surface.type != 'Ground':
        if cte.MONTH not in surface.global_irradiance:
          raise ValueError(f'surface: {surface.name} from building {building.name} has no global irradiance!')

        global_irradiance = surface.global_irradiance[cte.MONTH]
        for j in range(0, len(global_irradiance)):
          parameters.append(f'{j + 1} '
                            f'{global_irradiance[j] / 24 / _NUMBER_DAYS_PER_MONTH[j]}')
      else:
        for j in range(0, 12):
          parameters.append(f'{j + 1} 0.0')

      file = InselMonthlyEnergyBalance._add_block(file, i_block, 'polyg', inputs=inputs, parameters=parameters)

    i_block = 300 + len(surfaces)
    inputs = ['4.1', '4.2']
    file = InselMonthlyEnergyBalance._add_block(file, i_block, 'cum', inputs=inputs)

    in_1 = f'{i_block}.1'
    in_2 = f'{i_block}.2'
    i_block = 303 + len(surfaces)
    inputs = [in_1, in_2]
    file = InselMonthlyEnergyBalance._add_block(file, i_block, 'atend', inputs=inputs)

    i_block = 310 + len(surfaces)
    inputs = ['4.1', '4.2']
    parameters = ['1 % Mode',
                  '0 % Suppress FNQ inputs',
                  f"'{str(insel_outputs_path)}' % File name",
                  "'*' % Fortran format"]
    file = InselMonthlyEnergyBalance._add_block(file, i_block, 'WRITE', inputs=inputs, parameters=parameters)
    return file
