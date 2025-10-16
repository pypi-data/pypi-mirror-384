"""
InternalGain module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

from typing import Union, List
from hub.city_model_structure.attributes.schedule import Schedule


class InternalGain:
  """
  InternalGain class
  """

  def __init__(self):
    self._type = None
    self._average_internal_gain = None
    self._convective_fraction = None
    self._radiative_fraction = None
    self._latent_fraction = None
    self._schedules = None

  @property
  def type(self) -> Union[None, str]:
    """
    Get internal gains type
    :return: None or string
    """
    return self._type

  @type.setter
  def type(self, value):
    """
    Set internal gains type
    :param value: string
    """
    if value is not None:
      self._type = str(value)

  @property
  def average_internal_gain(self) -> Union[None, float]:
    """
    Get internal gains average internal gain in W/m2
    :return:  None or float
    """
    return self._average_internal_gain

  @average_internal_gain.setter
  def average_internal_gain(self, value):
    """
    Set internal gains average internal gain in W/m2
    :param value: float
    """
    if value is not None:
      self._average_internal_gain = float(value)

  @property
  def convective_fraction(self) -> Union[None, float]:
    """
    Get internal gains convective fraction
    :return:  None or float
    """
    return self._convective_fraction

  @convective_fraction.setter
  def convective_fraction(self, value):
    """
    Set internal gains convective fraction
    :param value: float
    """
    if value is not None:
      self._convective_fraction = float(value)

  @property
  def radiative_fraction(self) -> Union[None, float]:
    """
    Get internal gains radiative fraction
    :return:  None or float
    """
    return self._radiative_fraction

  @radiative_fraction.setter
  def radiative_fraction(self, value):
    """
    Set internal gains convective fraction
    :param value: float
    """
    if value is not None:
      self._radiative_fraction = float(value)

  @property
  def latent_fraction(self) -> Union[None, float]:
    """
    Get internal gains latent fraction
    :return: None or float
    """
    return self._latent_fraction

  @latent_fraction.setter
  def latent_fraction(self, value):
    """
    Set internal gains latent fraction
    :param value: float
    """
    if value is not None:
      self._latent_fraction = float(value)

  @property
  def schedules(self) -> Union[None, List[Schedule]]:
    """
    Get internal gain schedules
    data type = any number
    time step = 1 hour
    time range = 1 day
    :return: [Schedule]
    """
    return self._schedules

  @schedules.setter
  def schedules(self, value):
    """
    Set internal gain schedules
    data type = any number
    time step = 1 hour
    time range = 1 day
    :param value: [Schedule]
    """
    self._schedules = value
