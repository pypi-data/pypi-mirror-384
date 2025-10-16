"""
Configuration helper
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""
import configparser
from pathlib import Path


class ConfigurationHelper:
  """
  Configuration class
  """
  def __init__(self):
    config_file = Path(Path(__file__).parent.parent / 'config/configuration.ini').resolve()
    self._config = configparser.ConfigParser()
    self._config.read(config_file)

  @property
  def min_coordinate(self) -> float:
    """
    Get configured minimal coordinate value
    :return: -1.7976931348623157e+308
    """
    return self._config.getfloat('buildings', 'min_coordinate')

  @property
  def max_coordinate(self) -> float:
    """
    Get configured maximal coordinate value
    :return: 1.7976931348623157e+308
    """
    return self._config.getfloat('buildings', 'max_coordinate').real

  @property
  def comnet_lighting_latent(self) -> float:
    """
    Get configured latent ratio of internal gains do to lighting used for Comnet (ASHRAE) standard
    :return: 0
    """
    return self._config.getfloat('buildings', 'comnet_lighting_latent').real

  @property
  def comnet_lighting_convective(self) -> float:
    """
    Get configured convective ratio of internal gains do to lighting used for Comnet (ASHRAE) standard
    :return: 0.5
    """
    return self._config.getfloat('buildings', 'comnet_lighting_convective').real

  @property
  def comnet_lighting_radiant(self) -> float:
    """
    Get configured radiant ratio of internal gains do to lighting used for Comnet (ASHRAE) standard
    :return: 0.5
    """
    return self._config.getfloat('buildings', 'comnet_lighting_radiant').real

  @property
  def comnet_plugs_latent(self) -> float:
    """
    Get configured latent ratio of internal gains do to electrical appliances used for Comnet (ASHRAE) standard
    :return: 0
    """
    return self._config.getfloat('buildings', 'comnet_plugs_latent').real

  @property
  def comnet_plugs_convective(self) -> float:
    """
    Get configured convective ratio of internal gains do to electrical appliances used for Comnet (ASHRAE) standard
    :return: 0.75
    """
    return self._config.getfloat('buildings', 'comnet_plugs_convective').real

  @property
  def comnet_plugs_radiant(self) -> float:
    """
    Get configured radiant ratio of internal gains do to electrical appliances used for Comnet (ASHRAE) standard
    :return: 0.25
    """
    return self._config.getfloat('buildings', 'comnet_plugs_radiant').real

  @property
  def comnet_occupancy_sensible_convective(self) -> float:
    """
    Get configured convective ratio of the sensible part of internal gains do to occupancy
    used for Comnet (ASHRAE) standard
    :return: 0.9
    """
    return self._config.getfloat('buildings', 'comnet_occupancy_sensible_convective').real

  @property
  def comnet_occupancy_sensible_radiant(self) -> float:
    """
    Get configured radiant ratio of the sensible part of internal gains do to occupancy
    used for Comnet (ASHRAE) standard
    :return: 0.1
    """
    return self._config.getfloat('buildings', 'comnet_occupancy_sensible_radiant').real

  @property
  def convective_heat_transfer_coefficient_interior(self) -> float:
    """
    Get configured convective heat transfer coefficient for surfaces inside the building
    :return: 3.5 W/m2K
    """
    return self._config.getfloat('buildings', 'convective_heat_transfer_coefficient_interior').real

  @property
  def convective_heat_transfer_coefficient_exterior(self) -> float:
    """
    Get configured convective heat transfer coefficient for surfaces outside the building
    :return: 20 W/m2K
    """
    return self._config.getfloat('buildings', 'convective_heat_transfer_coefficient_exterior').real

  @property
  def soil_conductivity(self) -> float:
    """
    Get configured soil conductivity for surfaces touching the ground
    :return: 3 W/mK
    """
    return self._config.getfloat('buildings', 'soil_conductivity').real

  @property
  def soil_thickness(self) -> float:
    """
    Get configured soil thickness for surfaces touching the ground
    :return: 0.5 m
    """
    return self._config.getfloat('buildings', 'soil_thickness').real

  @property
  def short_wave_reflectance(self) -> float:
    """
    Get configured short wave reflectance for surfaces that don't have construction assigned
    :return: 0.3
    """
    return self._config.getfloat('buildings', 'short_wave_reflectance').real

  @property
  def cold_water_temperature(self) -> float:
    """
    Get configured cold water temperature in Celsius
    :return: 10
    """
    return self._config.getfloat('buildings', 'cold_water_temperature').real
