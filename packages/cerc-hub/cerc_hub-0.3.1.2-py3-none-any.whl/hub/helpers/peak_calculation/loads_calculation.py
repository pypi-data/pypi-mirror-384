"""
Calculation of loads for peak heating and cooling
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

import hub.helpers.constants as cte


class LoadsCalculation:
  """
  LoadsCalculation class
  """

  def __init__(self, building):
    self._building = building

  @staticmethod
  def _get_load_transmitted(thermal_zone, internal_temperature, ambient_temperature, ground_temperature):
    load_transmitted_opaque = 0
    load_transmitted_transparent = 0
    for thermal_boundary in thermal_zone.thermal_boundaries:
      if thermal_boundary.type == cte.GROUND:
        external_temperature = ground_temperature
      elif thermal_boundary.type == cte.INTERIOR_WALL:
        external_temperature = internal_temperature
      else:
        external_temperature = ambient_temperature

      load_transmitted_opaque += (
          thermal_boundary.u_value * thermal_boundary.opaque_area * (internal_temperature - external_temperature)
      )
      for thermal_opening in thermal_boundary.thermal_openings:
        load_transmitted_transparent += thermal_opening.overall_u_value \
                                        * (internal_temperature - external_temperature)
    load_transmitted_opaque += (
        thermal_zone.additional_thermal_bridge_u_value * thermal_zone.footprint_area *
        (internal_temperature - ambient_temperature)
    )
    load_transmitted = load_transmitted_opaque + load_transmitted_transparent
    return load_transmitted

  @staticmethod
  def _get_load_ventilation(thermal_zone, internal_temperature, ambient_temperature):
    load_renovation_sensible = 0
    for usage in thermal_zone.usages:
      load_renovation_sensible += cte.AIR_DENSITY * cte.AIR_HEAT_CAPACITY * usage.mechanical_air_change \
                                  * thermal_zone.volume * (internal_temperature - ambient_temperature)

    load_infiltration_sensible = (
        cte.AIR_DENSITY * cte.AIR_HEAT_CAPACITY * thermal_zone.infiltration_rate_system_off * thermal_zone.volume
        * (internal_temperature - ambient_temperature)
    )

    load_ventilation = load_renovation_sensible + load_infiltration_sensible

    return load_ventilation

  def get_heating_transmitted_load(self, ambient_temperature, ground_temperature):
    """
    Calculates the heating transmitted load
    :return: int
    """
    heating_load_transmitted = 0
    for thermal_zone in self._building.thermal_zones_from_internal_zones:
      internal_temperature = thermal_zone.thermal_control.mean_heating_set_point
      heating_load_transmitted += self._get_load_transmitted(thermal_zone, internal_temperature, ambient_temperature,
                                                             ground_temperature)
    return heating_load_transmitted

  def get_cooling_transmitted_load(self, ambient_temperature, ground_temperature):
    """
    Calculates the cooling transmitted load
    :return: int
    """
    cooling_load_transmitted = 0
    for thermal_zone in self._building.thermal_zones_from_internal_zones:
      internal_temperature = thermal_zone.thermal_control.mean_cooling_set_point
      cooling_load_transmitted += self._get_load_transmitted(thermal_zone, internal_temperature, ambient_temperature,
                                                             ground_temperature)
    return cooling_load_transmitted

  def get_heating_ventilation_load_sensible(self, ambient_temperature):
    """
    Calculates the heating ventilation load sensible
    :return: int
    """
    heating_ventilation_load = 0
    for thermal_zone in self._building.thermal_zones_from_internal_zones:
      internal_temperature = thermal_zone.thermal_control.mean_heating_set_point
      heating_ventilation_load += self._get_load_ventilation(thermal_zone, internal_temperature, ambient_temperature)
    return heating_ventilation_load

  def get_cooling_ventilation_load_sensible(self, ambient_temperature):
    """
    Calculates the cooling ventilation load sensible
    :return: int
    """
    cooling_ventilation_load = 0
    for thermal_zone in self._building.thermal_zones_from_internal_zones:
      internal_temperature = thermal_zone.thermal_control.mean_cooling_set_point
      cooling_ventilation_load += self._get_load_ventilation(thermal_zone, internal_temperature, ambient_temperature)
    return cooling_ventilation_load

  def get_internal_load_sensible(self):
    """
    Calculates the internal load sensible
    :return: int
    """
    cooling_load_occupancy_sensible = 0
    cooling_load_lighting = 0
    cooling_load_equipment_sensible = 0
    for thermal_zone in self._building.thermal_zones_from_internal_zones:
      cooling_load_occupancy_sensible += (thermal_zone.occupancy.sensible_convective_internal_gain
                                          + thermal_zone.occupancy.sensible_radiative_internal_gain) \
                                         * thermal_zone.footprint_area
      cooling_load_lighting += (
          thermal_zone.lighting.density * thermal_zone.lighting.convective_fraction + thermal_zone.lighting.density *
          thermal_zone.lighting.radiative_fraction
      ) * thermal_zone.footprint_area
      cooling_load_equipment_sensible += (
          thermal_zone.appliances.density * thermal_zone.appliances.convective_fraction +
          thermal_zone.appliances.density * thermal_zone.appliances.radiative_fraction
      ) * thermal_zone.footprint_area
    internal_load = cooling_load_occupancy_sensible + cooling_load_lighting + cooling_load_equipment_sensible
    return internal_load

  def get_radiation_load(self, hour):
    """
    Calculates the radiation load
    :return: int
    """
    cooling_load_radiation = 0
    for thermal_zone in self._building.thermal_zones_from_internal_zones:
      for thermal_boundary in thermal_zone.thermal_boundaries:
        for thermal_opening in thermal_boundary.thermal_openings:
          radiation = thermal_boundary.parent_surface.global_irradiance[cte.HOUR][hour] * cte.WATTS_HOUR_TO_JULES
          cooling_load_radiation += (
              thermal_opening.area * (1 - thermal_opening.frame_ratio) * thermal_opening.g_value * radiation
          )
    return cooling_load_radiation
