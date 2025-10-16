"""
ThermalOpening module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
Code contributors: Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""
import uuid
from typing import TypeVar, Union
from hub.helpers.configuration_helper import ConfigurationHelper as ch

Polygon = TypeVar('Polygon')


class ThermalOpening:
  """
  ThermalOpening class
  """
  def __init__(self):
    self._id = None
    self._area = None
    self._conductivity = None
    self._frame_ratio = None
    self._g_value = None
    self._thickness = None
    self._overall_u_value = None
    self._hi = ch().convective_heat_transfer_coefficient_interior
    self._he = ch().convective_heat_transfer_coefficient_exterior
    self._construction_name = None

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
  def area(self) -> Union[None, float]:
    """
    Get thermal opening area in square meters
    :return: None or float
    """
    return self._area

  @area.setter
  def area(self, value):
    """
    Set thermal opening area in square meters
    :param value: float
    """
    if value is not None:
      self._area = float(value)

  @property
  def conductivity(self) -> Union[None, float]:
    """
    Get thermal opening conductivity in W/mK
    :return: None or float
    """
    return self._conductivity

  @conductivity.setter
  def conductivity(self, value):
    """
    Set thermal opening conductivity in W/mK
    :param value: float
    """
    # The code to calculate overall_u_value is duplicated here and in thickness_m.
    # This ensures a more robust code that returns the overall_u_value regardless the order the parameters are read.
    if value is not None:
      self._conductivity = float(value)
      if self._overall_u_value is None and self.thickness is not None:
        h_i = self.hi
        h_e = self.he
        r_value = 1 / h_i + 1 / h_e + float(self.thickness) / float(self._conductivity)
        self._overall_u_value = 1 / r_value

  @property
  def frame_ratio(self) -> Union[None, float]:
    """
    Get thermal opening frame ratio
    :return: None or float
    """
    return self._frame_ratio

  @frame_ratio.setter
  def frame_ratio(self, value):
    """
    Set thermal opening frame ratio
    :param value: float
    """
    if value is not None:
      self._frame_ratio = float(value)

  @property
  def g_value(self) -> Union[None, float]:
    """
    Get thermal opening transmittance at normal incidence
    :return: None or float
    """
    return self._g_value

  @g_value.setter
  def g_value(self, value):
    """
    Set thermal opening transmittance at normal incidence
    :param value: float
    """
    if value is not None:
      self._g_value = float(value)

  @property
  def thickness(self) -> Union[None, float]:
    """
    Get thermal opening thickness in meters
    :return: None or float
    """
    return self._thickness

  @thickness.setter
  def thickness(self, value):
    """
    Set thermal opening thickness in meters
    :param value: float
    """
    # The code to calculate overall_u_value is duplicated here and in conductivity.
    # This ensures a more robust code that returns the overall_u_value regardless the order the parameters are read.
    if value is not None:
      self._thickness = float(value)
      if self._overall_u_value is None and self.conductivity is not None:
        h_i = self.hi
        h_e = self.he
        r_value = 1 / h_i + 1 / h_e + float(self._thickness) / float(self.conductivity)
        self._overall_u_value = 1 / r_value

  @property
  def overall_u_value(self) -> Union[None, float]:
    """
    Get thermal opening overall U-value in W/m2K
    :return: None or float
    """
    return self._overall_u_value

  @overall_u_value.setter
  def overall_u_value(self, value):
    """
    Set thermal opening overall U-value in W/m2K
    :param value: float
    """
    if value is not None:
      self._overall_u_value = float(value)

  @property
  def hi(self) -> Union[None, float]:
    """
    Get internal convective heat transfer coefficient (W/m2K)
    :return: None or float
    """
    return self._hi

  @hi.setter
  def hi(self, value):
    """
    Set internal convective heat transfer coefficient (W/m2K)
    :param value: float
    """
    if value is not None:
      self._hi = float(value)

  @property
  def he(self) -> Union[None, float]:
    """
    Get external convective heat transfer coefficient (W/m2K)
    :return: None or float
    """
    return self._he

  @he.setter
  def he(self, value):
    """
    Set external convective heat transfer coefficient (W/m2K)
    :param value: float
    """
    if value is not None:
      self._he = float(value)

  @property
  def construction_name(self):
    """
    Get thermal opening construction name
    """
    return self._construction_name

  @construction_name.setter
  def construction_name(self, value):
    """
    Set thermal opening construction name
    """
    self._construction_name = value
