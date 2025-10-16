"""
Layers module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

import uuid
from typing import Union


class Layer:
  """
  Layer class
  """
  def __init__(self):
    self._thickness = None
    self._id = None
    self._material_name = None
    self._conductivity = None
    self._specific_heat = None
    self._density = None
    self._solar_absorptance = None
    self._thermal_absorptance = None
    self._visible_absorptance = None
    self._no_mass = False
    self._thermal_resistance = None

  @property
  def id(self):
    """
    Get layer id, a universally unique identifier randomly generated
    :return: str
    """
    if self._id is None:
      self._id = uuid.uuid4()
    return self._id

  @property
  def thickness(self) -> Union[None, float]:
    """
    Get layer thickness in meters
    :return: None or float
    """
    return self._thickness

  @thickness.setter
  def thickness(self, value):
    """
    Get layer thickness in meters
    :param value: float
    """
    if value is not None:
      self._thickness = float(value)

  @property
  def material_name(self):
    """
    Get material name
    :return: str
    """
    return self._material_name

  @material_name.setter
  def material_name(self, value):
    """
    Set material name
    :param value: string
    """
    self._material_name = str(value)

  @property
  def conductivity(self) -> Union[None, float]:
    """
    Get material conductivity in W/mK
    :return: None or float
    """
    return self._conductivity

  @conductivity.setter
  def conductivity(self, value):
    """
    Set material conductivity in W/mK
    :param value: float
    """
    if value is not None:
      self._conductivity = float(value)

  @property
  def specific_heat(self) -> Union[None, float]:
    """
    Get material conductivity in J/kgK
    :return: None or float
    """
    return self._specific_heat

  @specific_heat.setter
  def specific_heat(self, value):
    """
    Get material conductivity in J/kgK
    :param value: float
    """
    if value is not None:
      self._specific_heat = float(value)

  @property
  def density(self) -> Union[None, float]:
    """
    Get material density in kg/m3
    :return: None or float
    """
    return self._density

  @density.setter
  def density(self, value):
    """
    Set material density
    :param value: float
    """
    if value is not None:
      self._density = float(value)

  @property
  def solar_absorptance(self) -> Union[None, float]:
    """
    Get material solar absorptance
    :return: None or float
    """
    return self._solar_absorptance

  @solar_absorptance.setter
  def solar_absorptance(self, value):
    """
    Set material solar absorptance
    :param value: float
    """
    if value is not None:
      self._solar_absorptance = float(value)

  @property
  def thermal_absorptance(self) -> Union[None, float]:
    """
    Get material thermal absorptance
    :return: None or float
    """
    return self._thermal_absorptance

  @thermal_absorptance.setter
  def thermal_absorptance(self, value):
    """
    Set material thermal absorptance
    :param value: float
    """
    if value is not None:
      self._thermal_absorptance = float(value)

  @property
  def visible_absorptance(self) -> Union[None, float]:
    """
    Get material visible absorptance
    :return: None or float
    """
    return self._visible_absorptance

  @visible_absorptance.setter
  def visible_absorptance(self, value):
    """
    Set material visible absorptance
    :param value: float
    """
    if value is not None:
      self._visible_absorptance = float(value)

  @property
  def no_mass(self) -> Union[None, bool]:
    """
    Get material no mass flag
    :return: None or Boolean
    """
    return self._no_mass

  @no_mass.setter
  def no_mass(self, value):
    """
    Set material no mass flag
    :param value: Boolean
    """
    if value is not None:
      self._no_mass = value

  @property
  def thermal_resistance(self) -> Union[None, float]:
    """
    Get material thermal resistance in m2K/W
    :return: None or float
    """
    return self._thermal_resistance

  @thermal_resistance.setter
  def thermal_resistance(self, value):
    """
    Set material thermal resistance in m2K/W
    :param value: float
    """
    if value is not None:
      self._thermal_resistance = float(value)
