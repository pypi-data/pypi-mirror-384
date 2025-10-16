"""
ThermalZone module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
Code contributors: Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

import uuid
import copy
from typing import List, Union, TypeVar
import numpy

from hub.city_model_structure.building_demand.occupancy import Occupancy
from hub.city_model_structure.building_demand.appliances import Appliances
from hub.city_model_structure.building_demand.lighting import Lighting
from hub.city_model_structure.building_demand.internal_gain import InternalGain
from hub.city_model_structure.building_demand.thermal_control import ThermalControl
from hub.city_model_structure.building_demand.domestic_hot_water import DomesticHotWater
from hub.city_model_structure.attributes.schedule import Schedule
import hub.helpers.constants as cte

ThermalBoundary = TypeVar('ThermalBoundary')
InternalZone = TypeVar('InternalZone')


class ThermalZone:
  """
  ThermalZone class
  """

  def __init__(self, thermal_boundaries,
               parent_internal_zone,
               volume,
               footprint_area,
               number_of_storeys,
               usages=None):
    self._id = None
    self._parent_internal_zone = parent_internal_zone
    self._footprint_area = footprint_area
    self._thermal_boundaries = thermal_boundaries
    self._additional_thermal_bridge_u_value = None
    self._effective_thermal_capacity = None
    self._indirectly_heated_area_ratio = None
    self._infiltration_rate_system_on = None
    self._infiltration_rate_system_off = None
    self._infiltration_rate_area_system_on = None
    self._infiltration_rate_area_system_off = None
    self._volume = volume
    self._ordinate_number = None
    self._view_factors_matrix = None
    self._total_floor_area = None
    self._number_of_storeys = number_of_storeys
    self._hours_day = None
    self._days_year = None
    self._mechanical_air_change = None
    self._occupancy = None
    self._lighting = None
    self._appliances = None
    self._internal_gains = None
    self._thermal_control = None
    self._domestic_hot_water = None
    self._usage_name = None
    self._usages = usages
    self._usage_from_parent = False
    if usages is None:
      self._usage_from_parent = True
     

  @property
  def parent_internal_zone(self) -> InternalZone:
    """
    Get the internal zone to which this thermal zone belongs
    :return: InternalZone
    """
    return self._parent_internal_zone

  @property
  def usages(self):
    """
    Get the thermal zone usages
    :return: str
    """
    if self._usage_from_parent:
      self._usages = copy.deepcopy(self._parent_internal_zone.usages)
    return self._usages

  @property
  def id(self):
    """
    Get thermal zone id, a universally unique identifier randomly generated
    :return: str
    """
    if self._id is None:
      self._id = uuid.uuid4()
    return self._id

  @property
  def footprint_area(self) -> float:
    """
    Get thermal zone footprint area in m2
    :return: float
    """
    return self._footprint_area

  @property
  def thermal_boundaries(self) -> [ThermalBoundary]:
    """
    Get thermal boundaries bounding with the thermal zone
    :return: [ThermalBoundary]
    """
    return self._thermal_boundaries

  @property
  def additional_thermal_bridge_u_value(self) -> Union[None, float]:
    """
    Get thermal zone additional thermal bridge u value per footprint area W/m2K
    :return: None or float
    """
    self._additional_thermal_bridge_u_value = self.parent_internal_zone.thermal_archetype.extra_loses_due_to_thermal_bridges
    return self._additional_thermal_bridge_u_value

  @property
  def effective_thermal_capacity(self) -> Union[None, float]:
    """
    Get thermal zone effective thermal capacity in J/m3K
    :return: None or float
    """
    self._effective_thermal_capacity = self._parent_internal_zone.thermal_archetype.thermal_capacity
    return self._effective_thermal_capacity

  @property
  def indirectly_heated_area_ratio(self) -> Union[None, float]:
    """
    Get thermal zone indirectly heated area ratio
    :return: None or float
    """
    self._indirectly_heated_area_ratio = self._parent_internal_zone.thermal_archetype.indirect_heated_ratio
    return self._indirectly_heated_area_ratio

  @property
  def infiltration_rate_system_on(self):
    """
    Get infiltration rate for ventilation system on in ACH
    :return: None or float
    """
    self._infiltration_rate_system_on = self._parent_internal_zone.thermal_archetype.infiltration_rate_for_ventilation_system_on
    return self._infiltration_rate_system_on

  @property
  def infiltration_rate_system_off(self):
    """
    Get infiltration rate for ventilation system off in ACH
    :return: None or float
    """
    self._infiltration_rate_system_off = self._parent_internal_zone.thermal_archetype.infiltration_rate_for_ventilation_system_off
    return self._infiltration_rate_system_off

  @property
  def infiltration_rate_area_system_on(self):
    """
    Get infiltration rate for ventilation system on in m3/s/m2
    :return: None or float
    """
    self._infiltration_rate_area_system_on = self._parent_internal_zone.thermal_archetype.infiltration_rate_area_for_ventilation_system_on
    return self._infiltration_rate_area_system_on

  @property
  def infiltration_rate_area_system_off(self):
    """
    Get infiltration rate for ventilation system off in m3/s/m2
    :return: None or float
    """
    self._infiltration_rate_area_system_off = self._parent_internal_zone.thermal_archetype.infiltration_rate_area_for_ventilation_system_off
    return self._infiltration_rate_area_system_off

  @property
  def volume(self):
    """
    Get thermal zone volume
    :return: float
    """
    return self._volume

  @property
  def ordinate_number(self) -> Union[None, int]:
    """
    Get the order in which the thermal_zones need to be enumerated
    :return: None or int
    """
    return self._ordinate_number

  @ordinate_number.setter
  def ordinate_number(self, value):
    """
    Set a specific order of the zones to be called
    :param value: int
    """
    if value is not None:
      self._ordinate_number = int(value)

  @property
  def view_factors_matrix(self):
    """
    Get thermal zone view factors matrix
    :return: [[float]]
    """
    # todo: review method if windows not in window_ratio but in geometry
    if self._view_factors_matrix is None:
      total_area = 0
      for thermal_boundary in self.thermal_boundaries:
        total_area += thermal_boundary.opaque_area
        for thermal_opening in thermal_boundary.thermal_openings:
          total_area += thermal_opening.area

      view_factors_matrix = []
      for thermal_boundary_1 in self.thermal_boundaries:
        values = []
        for thermal_boundary_2 in self.thermal_boundaries:
          value = 0
          if thermal_boundary_1.id != thermal_boundary_2.id:
            value = thermal_boundary_2.opaque_area / (total_area - thermal_boundary_1.opaque_area)
          values.append(value)
        for thermal_boundary in self.thermal_boundaries:
          for thermal_opening in thermal_boundary.thermal_openings:
            value = thermal_opening.area / (total_area - thermal_boundary_1.opaque_area)
            values.append(value)
        view_factors_matrix.append(values)

      for thermal_boundary_1 in self.thermal_boundaries:
        values = []
        for thermal_opening_1 in thermal_boundary_1.thermal_openings:
          for thermal_boundary_2 in self.thermal_boundaries:
            value = thermal_boundary_2.opaque_area / (total_area - thermal_opening_1.area)
            values.append(value)
          for thermal_boundary in self.thermal_boundaries:
            for thermal_opening_2 in thermal_boundary.thermal_openings:
              value = 0
              if thermal_opening_1.id != thermal_opening_2.id:
                value = thermal_opening_2.area / (total_area - thermal_opening_1.area)
              values.append(value)
          view_factors_matrix.append(values)
      self._view_factors_matrix = view_factors_matrix
    return self._view_factors_matrix

  @property
  def usage_name(self) -> Union[None, str]:
    """
    Get thermal zone usage name
    :return: None or str
    """
    if self._usage_from_parent:
      if self._parent_internal_zone.usages is None:
        return None
      self._usage_name = ''
      for usage in self._parent_internal_zone.usages:
        self._usage_name += str(round(usage.percentage * 100)) + '-' + usage.name + '_'
      self._usage_name = self._usage_name[:-1]
    return self._usage_name

  @staticmethod
  def _get_schedule_of_day(requested_day_type, schedules):
    for schedule in schedules:
      for day_type in schedule.day_types:
        if day_type == requested_day_type:
          return schedule
      return None

  @property
  def hours_day(self) -> Union[None, float]:
    """
    Get thermal zone usage hours per day
    :return: None or float
    """
    if self.usages is None:
      return None
    if self._hours_day is None:
      self._hours_day = 0
      for usage in self.usages:
        self._hours_day += usage.percentage * usage.hours_day
    return self._hours_day

  @property
  def days_year(self) -> Union[None, float]:
    """
    Get thermal zone usage days per year
    :return: None or float
    """
    if self.usages is None:
      return None
    if self._days_year is None:
      self._days_year = 0
      for usage in self.usages:
        self._days_year += usage.percentage * usage.days_year
    return self._days_year

  @property
  def mechanical_air_change(self) -> Union[None, float]:
    """
    Get thermal zone mechanical air change in air change per second (1/s)
    :return: None or float
    """
    if self.usages is None:
      return None
    if self._mechanical_air_change is None:
      self._mechanical_air_change = 0
      for usage in self.usages:
        if usage.mechanical_air_change is None:
          return None
        self._mechanical_air_change += usage.percentage * usage.mechanical_air_change
    return self._mechanical_air_change

  @property
  def occupancy(self) -> Union[None, Occupancy]:
    """
    Get occupancy in the thermal zone
    :return: None or Occupancy
    """
    if self.usages is None:
      return None

    if self._occupancy is None:
      self._occupancy = Occupancy()
      _occupancy_density = 0
      _convective_part = 0
      _radiative_part = 0
      _latent_part = 0
      for usage in self.usages:
        if usage.occupancy is None:
          return None
        _occupancy_density += usage.percentage * usage.occupancy.occupancy_density
        if usage.occupancy.sensible_convective_internal_gain is not None:
          _convective_part += usage.percentage * usage.occupancy.sensible_convective_internal_gain
          _radiative_part += usage.percentage * usage.occupancy.sensible_radiative_internal_gain
          _latent_part += usage.percentage * usage.occupancy.latent_internal_gain
      self._occupancy.occupancy_density = _occupancy_density
      self._occupancy.sensible_convective_internal_gain = _convective_part
      self._occupancy.sensible_radiative_internal_gain = _radiative_part
      self._occupancy.latent_internal_gain = _latent_part

      _occupancy_reference = self.usages[0].occupancy
      if _occupancy_reference.occupancy_schedules is not None:
        _schedules = []
        for schedule_index, schedule_value in enumerate(_occupancy_reference.occupancy_schedules):
          schedule = Schedule()
          schedule.type = schedule_value.type
          schedule.day_types = schedule_value.day_types
          schedule.data_type = schedule_value.data_type
          schedule.time_step = schedule_value.time_step
          schedule.time_range = schedule_value.time_range

          new_values = []
          for i_value, _ in enumerate(schedule_value.values):
            _new_value = 0
            for usage in self.usages:
              _new_value += usage.percentage * usage.occupancy.occupancy_schedules[schedule_index].values[i_value]
            new_values.append(_new_value)
          schedule.values = new_values
          _schedules.append(schedule)
        self._occupancy.occupancy_schedules = _schedules
    return self._occupancy

  @property
  def lighting(self) -> Union[None, Lighting]:
    """
    Get lighting information
    :return: None or Lighting
    """
    if self.usages is None:
      return None

    if self._lighting is None:
      self._lighting = Lighting()
      _lighting_density = 0
      _convective_part = 0
      _radiative_part = 0
      _latent_part = 0
      for usage in self.usages:
        if usage.lighting is None:
          return None
        _lighting_density += usage.percentage * usage.lighting.density
        if usage.lighting.convective_fraction is not None:
          _convective_part += (
              usage.percentage * usage.lighting.density * usage.lighting.convective_fraction
          )
          _radiative_part += (
              usage.percentage * usage.lighting.density * usage.lighting.radiative_fraction
          )
          _latent_part += (
              usage.percentage * usage.lighting.density * usage.lighting.latent_fraction
          )
      self._lighting.density = _lighting_density
      if _lighting_density > 0:
        self._lighting.convective_fraction = _convective_part / _lighting_density
        self._lighting.radiative_fraction = _radiative_part / _lighting_density
        self._lighting.latent_fraction = _latent_part / _lighting_density
      else:
        self._lighting.convective_fraction = 0
        self._lighting.radiative_fraction = 0
        self._lighting.latent_fraction = 0

      _lighting_reference = self.usages[0].lighting
      if _lighting_reference.schedules is not None:
        _schedules = []
        for schedule_index, schedule_value in enumerate(_lighting_reference.schedules):
          schedule = Schedule()
          schedule.type = schedule_value.type
          schedule.day_types = schedule_value.day_types
          schedule.data_type = schedule_value.data_type
          schedule.time_step = schedule_value.time_step
          schedule.time_range = schedule_value.time_range

          new_values = []
          for i_value, _ in enumerate(schedule_value.values):
            _new_value = 0
            for usage in self.usages:
              _new_value += usage.percentage * usage.lighting.schedules[schedule_index].values[i_value]
            new_values.append(_new_value)
          schedule.values = new_values
          _schedules.append(schedule)
        self._lighting.schedules = _schedules
    return self._lighting

  @property
  def appliances(self) -> Union[None, Appliances]:
    """
    Get appliances information
    :return: None or Appliances
    """
    if self.usages is None:
      return None

    if self._appliances is None:
      self._appliances = Appliances()
      _appliances_density = 0
      _convective_part = 0
      _radiative_part = 0
      _latent_part = 0
      for usage in self.usages:
        if usage.appliances is None:
          return None
        _appliances_density += usage.percentage * usage.appliances.density
        if usage.appliances.convective_fraction is not None:
          _convective_part += (
              usage.percentage * usage.appliances.density * usage.appliances.convective_fraction
          )
          _radiative_part += (
              usage.percentage * usage.appliances.density * usage.appliances.radiative_fraction
          )
          _latent_part += (
              usage.percentage * usage.appliances.density * usage.appliances.latent_fraction
          )
      self._appliances.density = _appliances_density
      if _appliances_density > 0:
        self._appliances.convective_fraction = _convective_part / _appliances_density
        self._appliances.radiative_fraction = _radiative_part / _appliances_density
        self._appliances.latent_fraction = _latent_part / _appliances_density
      else:
        self._appliances.convective_fraction = 0
        self._appliances.radiative_fraction = 0
        self._appliances.latent_fraction = 0

      _appliances_reference = self.usages[0].appliances
      if _appliances_reference.schedules is not None:
        _schedules = []
        for schedule_index, schedule_value in enumerate(_appliances_reference.schedules):
          schedule = Schedule()
          schedule.type = schedule_value.type
          schedule.day_types = schedule_value.day_types
          schedule.data_type = schedule_value.data_type
          schedule.time_step = schedule_value.time_step
          schedule.time_range = schedule_value.time_range

          new_values = []
          for i_value, _ in enumerate(schedule_value.values):
            _new_value = 0
            for usage in self.usages:
              _new_value += usage.percentage * usage.appliances.schedules[schedule_index].values[i_value]
            new_values.append(_new_value)
          schedule.values = new_values
          _schedules.append(schedule)
        self._appliances.schedules = _schedules
    return self._appliances

  @property
  def internal_gains(self) -> Union[None, List[InternalGain]]:
    """
    Calculates and returns the list of all internal gains defined
    :return: [InternalGain]
    """
    if self.usages is None:
      return None

    if self._internal_gains is None:
      _internal_gain = InternalGain()
      _days = [cte.MONDAY, cte.TUESDAY, cte.WEDNESDAY, cte.THURSDAY, cte.FRIDAY, cte.SATURDAY, cte.SUNDAY, cte.HOLIDAY]
      _average_internal_gain = 0
      _convective_fraction = 0
      _radiative_fraction = 0
      _latent_fraction = 0
      _schedules = None
      _base_schedule = Schedule()
      _base_schedule.type = cte.INTERNAL_GAINS
      _base_schedule.time_range = cte.DAY
      _base_schedule.time_step = cte.HOUR
      _base_schedule.data_type = cte.ANY_NUMBER
      _schedules_defined = True
      values = numpy.zeros([24, 8])
      for usage in self.usages:
        for internal_gain in usage.internal_gains:
          _average_internal_gain += internal_gain.average_internal_gain * usage.percentage
          _convective_fraction += (
              internal_gain.average_internal_gain * usage.percentage * internal_gain.convective_fraction
          )
          _radiative_fraction += (
              internal_gain.average_internal_gain * usage.percentage * internal_gain.radiative_fraction
          )
          _latent_fraction += (
            internal_gain.average_internal_gain * usage.percentage * internal_gain.latent_fraction
          )
      for usage in self.usages:
        for internal_gain in usage.internal_gains:
          if internal_gain.schedules is None:
            _schedules_defined = False
            break
          if len(internal_gain.schedules) == 0:
            _schedules_defined = False
            break
          for day, _schedule in enumerate(internal_gain.schedules):
            for v_index, value in enumerate(_schedule.values):
              values[v_index, day] += value * usage.percentage

      if _schedules_defined:
        _schedules = []
        for day_index, day in enumerate(_days):
          _schedule = copy.deepcopy(_base_schedule)
          _schedule.day_types = [day]
          _schedule.values = values[:day_index]
          _schedules.append(_schedule)

      _internal_gain.average_internal_gain = _average_internal_gain
      _internal_gain.convective_fraction = 0
      _internal_gain.radiative_fraction = 0
      _internal_gain.latent_fraction = 0
      if _average_internal_gain != 0:
        _internal_gain.convective_fraction = _convective_fraction / _average_internal_gain
        _internal_gain.radiative_fraction = _radiative_fraction / _average_internal_gain
        _internal_gain.latent_fraction = _latent_fraction / _average_internal_gain
      _internal_gain.type = 'mean_value'
      _internal_gain.schedules = _schedules
      self._internal_gains = [_internal_gain]
    return self._internal_gains

  @property
  def thermal_control(self) -> Union[None, ThermalControl]:
    """
    Get thermal control of this thermal zone
    :return: None or ThermalControl
    """
    if self.usages is None:
      return None

    if self._thermal_control is not None:
      return self._thermal_control
    self._thermal_control = ThermalControl()
    _mean_heating_set_point = 0
    _heating_set_back = 0
    _mean_cooling_set_point = 0
    for usage in self.usages:
      _mean_heating_set_point += usage.percentage * usage.thermal_control.mean_heating_set_point
      _heating_set_back += usage.percentage * usage.thermal_control.heating_set_back
      _mean_cooling_set_point += usage.percentage * usage.thermal_control.mean_cooling_set_point
    self._thermal_control.mean_heating_set_point = _mean_heating_set_point
    self._thermal_control.heating_set_back = _heating_set_back
    self._thermal_control.mean_cooling_set_point = _mean_cooling_set_point

    _thermal_control_reference = self.usages[0].thermal_control
    _types_reference = []
    if _thermal_control_reference.hvac_availability_schedules is not None:
      _types_reference.append([cte.HVAC_AVAILABILITY, _thermal_control_reference.hvac_availability_schedules])
    if _thermal_control_reference.heating_set_point_schedules is not None:
      _types_reference.append([cte.HEATING_SET_POINT, _thermal_control_reference.heating_set_point_schedules])
    if _thermal_control_reference.cooling_set_point_schedules is not None:
      _types_reference.append([cte.COOLING_SET_POINT, _thermal_control_reference.cooling_set_point_schedules])

    for i_type, _ in enumerate(_types_reference):
      _schedules = []
      _schedule_type = _types_reference[i_type][1]
      for i_schedule, schedule_value in enumerate(_schedule_type):
        schedule = Schedule()
        schedule.type = schedule_value.type
        schedule.day_types = schedule_value.day_types
        schedule.data_type = schedule_value.data_type
        schedule.time_step = schedule_value.time_step
        schedule.time_range = schedule_value.time_range

        new_values = []
        for i_value, _ in enumerate(schedule_value.values):
          _new_value = 0
          for usage in self.usages:
            if _types_reference[i_type][0] == cte.HVAC_AVAILABILITY:
              _new_value += usage.percentage * \
                            usage.thermal_control.hvac_availability_schedules[i_schedule].values[i_value]
            elif _types_reference[i_type][0] == cte.HEATING_SET_POINT:
              _new_value += usage.percentage * \
                            usage.thermal_control.heating_set_point_schedules[i_schedule].values[i_value]
            elif _types_reference[i_type][0] == cte.COOLING_SET_POINT:
              _new_value += usage.percentage * \
                            usage.thermal_control.cooling_set_point_schedules[i_schedule].values[i_value]
          new_values.append(_new_value)
        schedule.values = new_values
        _schedules.append(schedule)
      if i_type == 0:
        self._thermal_control.hvac_availability_schedules = _schedules
      elif i_type == 1:
        self._thermal_control.heating_set_point_schedules = _schedules
      elif i_type == 2:
        self._thermal_control.cooling_set_point_schedules = _schedules
    return self._thermal_control

  @property
  def domestic_hot_water(self) -> Union[None, DomesticHotWater]:
    """
    Get domestic hot water information of this thermal zone
    :return: None or DomesticHotWater
    """
    self._domestic_hot_water = DomesticHotWater()
    _mean_peak_density_load = 0
    _mean_peak_flow = 0
    _mean_service_temperature = 0
    for usage in self.usages:
      if usage.domestic_hot_water.density is not None:
        _mean_peak_density_load += usage.percentage * usage.domestic_hot_water.density
      if usage.domestic_hot_water.peak_flow is not None:
        _mean_peak_flow += usage.percentage * usage.domestic_hot_water.peak_flow
      if usage.domestic_hot_water.service_temperature is not None:
        _mean_service_temperature += usage.percentage * usage.domestic_hot_water.service_temperature
    self._domestic_hot_water.density = _mean_peak_density_load
    self._domestic_hot_water.peak_flow = _mean_peak_flow
    self._domestic_hot_water.service_temperature = _mean_service_temperature

    _domestic_hot_water_reference = self.usages[0].domestic_hot_water
    if _domestic_hot_water_reference.schedules is not None:
      _schedules = []
      for schedule_index, schedule_value in enumerate(_domestic_hot_water_reference.schedules):
        schedule = Schedule()
        schedule.type = schedule_value.type
        schedule.day_types = schedule_value.day_types
        schedule.data_type = schedule_value.data_type
        schedule.time_step = schedule_value.time_step
        schedule.time_range = schedule_value.time_range

        new_values = []
        for i_value, _ in enumerate(schedule_value.values):
          _new_value = 0
          for usage in self.usages:
            _new_value += usage.percentage * usage.domestic_hot_water.schedules[schedule_index].values[i_value]
          new_values.append(_new_value)
        schedule.values = new_values
        _schedules.append(schedule)
      self._domestic_hot_water.schedules = _schedules

    return self._domestic_hot_water

  @property
  def total_floor_area(self):
    """
    Get the total floor area of this thermal zone in m2
    :return: float
    """
    self._total_floor_area = self.footprint_area * self._number_of_storeys
    return self._total_floor_area
