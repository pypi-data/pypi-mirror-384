"""
Soil module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""


class Soil:
  """
  Soil class
  """
  def __init__(self, name, roughness, dry_conductivity, dry_density, dry_specific_heat, thermal_absorptance,
               solar_absorptance, visible_absorptance, saturation_volumetric_moisture_content,
               residual_volumetric_moisture_content):
    self._name = name
    self._roughness = roughness
    self._dry_conductivity = dry_conductivity
    self._dry_density = dry_density
    self._dry_specific_heat = dry_specific_heat
    self._thermal_absorptance = thermal_absorptance
    self._solar_absorptance = solar_absorptance
    self._visible_absorptance = visible_absorptance
    self._saturation_volumetric_moisture_content = saturation_volumetric_moisture_content
    self._residual_volumetric_moisture_content = residual_volumetric_moisture_content
    self._initial_volumetric_moisture_content = None

  @property
  def name(self):
    """
    Get soil name
    :return: string
    """
    return self._name

  @property
  def roughness(self):
    """
    Get soil roughness
    :return: string
    """
    return self._roughness

  @property
  def dry_conductivity(self):
    """
    Get soil dry conductivity in W/mK
    :return: float
    """
    return self._dry_conductivity

  @property
  def dry_density(self):
    """
    Get soil dry density in kg/m3
    :return: float
    """
    return self._dry_density

  @property
  def dry_specific_heat(self):
    """
    Get soil dry specific heat in J/kgK
    :return: float
    """
    return self._dry_specific_heat

  @property
  def thermal_absorptance(self):
    """
    Get soil thermal absortance
    :return: float
    """
    return self._thermal_absorptance

  @property
  def solar_absorptance(self):
    """
    Get soil solar absortance
    :return: float
    """
    return self._solar_absorptance

  @property
  def visible_absorptance(self):
    """
    Get soil visible absortance
    :return: float
    """
    return self._visible_absorptance

  @property
  def saturation_volumetric_moisture_content(self):
    """
    Get soil saturation volumetric moisture content
    :return: float
    """
    return self._saturation_volumetric_moisture_content

  @property
  def residual_volumetric_moisture_content(self):
    """
    Get soil residual volumetric moisture content
    :return: None or float
    """
    return self._residual_volumetric_moisture_content

  @residual_volumetric_moisture_content.setter
  def residual_volumetric_moisture_content(self, value):
    """
    Set soil residual volumetric moisture content
    :param value: float
    """
    self._residual_volumetric_moisture_content = value

  @property
  def initial_volumetric_moisture_content(self):
    """
    Get soil initial volumetric moisture content
    :return: None or float
    """
    return self._initial_volumetric_moisture_content

  @initial_volumetric_moisture_content.setter
  def initial_volumetric_moisture_content(self, value):
    """
    Set soil initial volumetric moisture content
    :param value: float
    """
    self._initial_volumetric_moisture_content = value
