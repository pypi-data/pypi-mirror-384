"""
Cerc Idf exports one city or some buildings to idf format
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Guillermo.GutierrezMorote@concordia.ca
Code contributors: Oriol Gavalda Torrellas oriol.gavalda@concordia.ca
"""
import copy
import os
import shutil
import subprocess
from pathlib import Path

import hub.exports.building_energy.idf_helper as idf_cte
import hub.helpers.constants as cte
from hub.city_model_structure.attributes.schedule import Schedule
from hub.exports.building_energy.idf_helper.idf_appliance import IdfAppliance
from hub.exports.building_energy.idf_helper.idf_base import IdfBase
from hub.exports.building_energy.idf_helper.idf_construction import IdfConstruction
from hub.exports.building_energy.idf_helper.idf_dhw import IdfDhw
from hub.exports.building_energy.idf_helper.idf_file_schedule import IdfFileSchedule
from hub.exports.building_energy.idf_helper.idf_heating_system import IdfHeatingSystem
from hub.exports.building_energy.idf_helper.idf_infiltration import IdfInfiltration
from hub.exports.building_energy.idf_helper.idf_lighting import IdfLighting
from hub.exports.building_energy.idf_helper.idf_material import IdfMaterial
from hub.exports.building_energy.idf_helper.idf_occupancy import IdfOccupancy
from hub.exports.building_energy.idf_helper.idf_output import IdfOutput
from hub.exports.building_energy.idf_helper.idf_output_control_files import IdfOutputControlFiles
from hub.exports.building_energy.idf_helper.idf_schedule import IdfSchedule
from hub.exports.building_energy.idf_helper.idf_shading import IdfShading
from hub.exports.building_energy.idf_helper.idf_surfaces import IdfSurfaces
from hub.exports.building_energy.idf_helper.idf_thermostat import IdfThermostat
from hub.exports.building_energy.idf_helper.idf_ventilation import IdfVentilation
from hub.exports.building_energy.idf_helper.idf_window import IdfWindow
from hub.exports.building_energy.idf_helper.idf_windows_constructions import IdfWindowsConstructions
from hub.exports.building_energy.idf_helper.idf_windows_material import IdfWindowsMaterial
from hub.exports.building_energy.idf_helper.idf_zone import IdfZone


class CercIdf(IdfBase):
  """
  Exports city to IDF
  """

  def __init__(self, city, output_path, idf_file_path, idd_file_path, epw_file_path, target_buildings=None, outputs=None):
    super().__init__(city, output_path, idf_file_path, idd_file_path, epw_file_path, target_buildings)
    self.outputs = outputs
    self._add_surfaces = IdfSurfaces.add
    self._add_file_schedule = IdfFileSchedule.add
    self._add_idf_schedule = IdfSchedule.add
    self._add_construction = IdfConstruction.add
    self._add_material = IdfMaterial.add
    self._add_windows_material = IdfWindowsMaterial.add
    self._add_windows_constructions = IdfWindowsConstructions.add
    self._add_occupancy = IdfOccupancy.add
    self._add_lighting = IdfLighting.add
    self._add_appliance = IdfAppliance.add
    self._add_infiltration = IdfInfiltration.add
    self._add_infiltration_surface = IdfInfiltration.add_surface
    self._add_ventilation = IdfVentilation.add
    self._add_zone = IdfZone.add
    self._add_thermostat = IdfThermostat.add
    self._add_heating_system = IdfHeatingSystem.add
    self._add_dhw = IdfDhw.add
    self._add_shading = IdfShading.add
    self._add_windows = IdfWindow.add
    self._add_output_control_files = IdfOutputControlFiles.add
    self._add_output = IdfOutput.add
    self.schedules_added_to_idf = {}
    self.materials_added_to_idf = {}
    self.windows_added_to_idf = {}
    self.constructions_added_to_idf = {}
    self.thermostat_added_to_idf = {}

    with open(self._idf_file_path, 'r', encoding='UTF-8') as base_idf:
      lines = base_idf.readlines()
    # Change city name
    comment = f'    !- Name'
    field = f'    Buildings in {self.city.name},'.ljust(26, ' ')
    lines[15] = f'{field}{comment}\n'
    with open(self._output_file_path, 'w', encoding='UTF-8') as self._idf_file:
      self._idf_file.writelines(lines)
      self._export()

  @property
  def idf_file(self):
    return self._idf_file

  @property
  def idf_file_path(self):
    return self._idf_file_path

  def _create_geometry_rules(self):
    file = self.files['constructions']
    self.write_to_idf_format(file, idf_cte.GLOBAL_GEOMETRY_RULES)
    self.write_to_idf_format(file, 'UpperLeftCorner', 'Starting Vertex Position')
    self.write_to_idf_format(file, 'CounterClockWise', 'Vertex Entry Direction')
    self.write_to_idf_format(file, 'World', 'Coordinate System', ';')

  def _merge_files(self):
    for file in self.files.values():
      file.close()
    for path in self._file_paths.values():
      with open(path, 'r', encoding='UTF-8') as file:
        lines = file.readlines()
      self._idf_file.writelines(lines)
    for path in self._file_paths.values():
      if Path(path).exists():
        os.unlink(path)

  @staticmethod
  def _create_infiltration_schedules(thermal_zone):
    _infiltration_schedules = []
    if thermal_zone.thermal_control is None:
      return []
    for hvac_availability_schedule in thermal_zone.thermal_control.hvac_availability_schedules:
      _schedule = Schedule()
      _schedule.type = cte.INFILTRATION
      _schedule.data_type = cte.FRACTION
      _schedule.time_step = cte.HOUR
      _schedule.time_range = cte.DAY
      _schedule.day_types = copy.deepcopy(hvac_availability_schedule.day_types)
      _infiltration_values = []
      for hvac_value in hvac_availability_schedule.values:
        if hvac_value == 0:
          _infiltration_values.append(1.0)
        else:
          if thermal_zone.infiltration_rate_area_system_off == 0:
            _infiltration_values.append(0.0)
          else:
            _infiltration_values.append(1.0)
      _schedule.values = _infiltration_values
      _infiltration_schedules.append(_schedule)
    return _infiltration_schedules

  @staticmethod
  def _create_ventilation_schedules(thermal_zone):
    _ventilation_schedules = []
    if thermal_zone.thermal_control is None:
      return []
    for hvac_availability_schedule in thermal_zone.thermal_control.hvac_availability_schedules:
      _schedule = Schedule()
      _schedule.type = cte.VENTILATION
      _schedule.data_type = cte.FRACTION
      _schedule.time_step = cte.HOUR
      _schedule.time_range = cte.DAY
      _schedule.day_types = copy.deepcopy(hvac_availability_schedule.day_types)
      _ventilation_schedules = thermal_zone.thermal_control.hvac_availability_schedules
    return _ventilation_schedules

  @staticmethod
  def _create_constant_value_schedules(value, amount):
    _schedule = Schedule()
    _schedule.type = ''
    _schedule.data_type = cte.ANY_NUMBER
    _schedule.time_step = cte.HOUR
    _schedule.time_range = cte.DAY
    _schedule.day_types = ['monday',
                           'tuesday',
                           'wednesday',
                           'thursday',
                           'friday',
                           'saturday',
                           'sunday',
                           'holiday',
                           'winter_design_day',
                           'summer_design_day']
    _schedule.values = [value for _ in range(0, amount)]
    return [_schedule]

  def _export(self):
    for building in self.city.buildings:
      is_target = building.name in self._target_buildings or building.name in self._adjacent_buildings
      for storey, internal_zone in enumerate(building.internal_zones):
        zone_name = f'{building.name}_{storey}'
        if internal_zone.thermal_zones_from_internal_zones is None:
          is_target = False
          continue
        for thermal_zone in internal_zone.thermal_zones_from_internal_zones:
          if is_target:

            service_temperature = thermal_zone.domestic_hot_water.service_temperature
            usage = thermal_zone.usage_name
            occ = thermal_zone.occupancy
            if occ.occupancy_density == 0:
              total_heat = 0
            else:
              total_heat = (
                             occ.sensible_convective_internal_gain +
                             occ.sensible_radiative_internal_gain +
                             occ.latent_internal_gain
                           ) / occ.occupancy_density
            self._add_idf_schedule(self, usage, 'Infiltration', self._create_infiltration_schedules(thermal_zone))
            self._add_idf_schedule(self, usage, 'Ventilation', self._create_ventilation_schedules(thermal_zone))
            self._add_idf_schedule(self, usage, 'Occupancy', thermal_zone.occupancy.occupancy_schedules)
            self._add_idf_schedule(self, usage, 'HVAC AVAIL', thermal_zone.thermal_control.hvac_availability_schedules)
            self._add_idf_schedule(self, usage, 'Heating thermostat',
                                   thermal_zone.thermal_control.heating_set_point_schedules)
            self._add_idf_schedule(self, usage, 'Cooling thermostat',
                                   thermal_zone.thermal_control.cooling_set_point_schedules)
            self._add_idf_schedule(self, usage, 'Lighting', thermal_zone.lighting.schedules)
            self._add_idf_schedule(self, usage, 'Appliance', thermal_zone.appliances.schedules)
            self._add_idf_schedule(self, usage, 'DHW_prof', thermal_zone.domestic_hot_water.schedules)
            self._add_idf_schedule(self, usage, 'DHW_temp',
                                   self._create_constant_value_schedules(service_temperature, 24))
            self._add_idf_schedule(self, usage, 'Activity Level', self._create_constant_value_schedules(total_heat, 24))
            self._add_file_schedule(self, usage, 'cold_temp',
                                    self._create_constant_value_schedules(building.cold_water_temperature[cte.HOUR],
                                                                          24))
            for thermal_boundary in thermal_zone.thermal_boundaries:

              self._add_material(self, thermal_boundary)
              self._add_construction(self, thermal_boundary)
              for thermal_opening in thermal_boundary.thermal_openings:
                self._add_windows_material(self, thermal_boundary, thermal_opening)
                self._add_windows_constructions(self, thermal_boundary)
            self._add_zone(self, thermal_zone, zone_name)
            self._add_occupancy(self, thermal_zone, zone_name)
            self._add_lighting(self, thermal_zone, zone_name)
            self._add_appliance(self, thermal_zone, zone_name)
            if self._calculate_with_new_infiltration:
              self._add_infiltration_surface(self, thermal_zone, zone_name)
            else:
              self._add_infiltration(self, thermal_zone, zone_name)
            self._add_ventilation(self, thermal_zone, zone_name)
            self._add_thermostat(self, thermal_zone)
            self._add_heating_system(self, thermal_zone, zone_name)
            self._add_dhw(self, thermal_zone, zone_name)
      if is_target:
        self._add_surfaces(self, building)
        self._add_windows(self, building)
      else:
        self._add_shading(self, building)

    self._create_output_control_lighting()  # Add lighting control to the lighting

    # Create base values
    self._create_geometry_rules()
    self._add_output_control_files(self)
    # Merge files
    self._merge_files()
    self._add_output(self)


  @property
  def _energy_plus(self):
    return shutil.which('energyplus')

  def run(self):
    cmd = [self._energy_plus,
           '--weather', self._epw_file_path,
           '--output-directory', self.output_path,
           '--idd', self._idd_file_path,
           '--expandobjects',
           '--readvars',
           '--output-prefix', f'{self.city.name}_',
           self._output_file_path]
    subprocess.run(cmd, cwd=self.output_path)
