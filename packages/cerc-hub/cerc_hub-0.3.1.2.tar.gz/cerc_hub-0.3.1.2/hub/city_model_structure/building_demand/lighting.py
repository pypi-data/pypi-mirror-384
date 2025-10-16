"""
Lighting module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""
from typing import Union, List
from hub.city_model_structure.attributes.schedule import Schedule


class Lighting:
  """
  Lighting class
  """
  def __init__(self):
    self._density = None
    self._convective_fraction = None
    self._radiative_fraction = None
    self._latent_fraction = None
    self._schedules = None

  @property
  def density(self) -> Union[None, float]:
    """
    Get lighting density in Watts per m2
    :return: None or float
    """
    return self._density

  @density.setter
  def density(self, value):
    """
    Set lighting density in Watts per m2
    :param value: float
    """
    if value is not None:
      self._density = float(value)

  @property
  def convective_fraction(self) -> Union[None, float]:
    """
    Get convective fraction
    :return: None or float
    """
    return self._convective_fraction

  @convective_fraction.setter
  def convective_fraction(self, value):
    """
    Set convective fraction
    :param value: float
    """
    if value is not None:
      self._convective_fraction = float(value)

  @property
  def radiative_fraction(self) -> Union[None, float]:
    """
    Get radiant fraction
    :return: None or float
    """
    return self._radiative_fraction

  @radiative_fraction.setter
  def radiative_fraction(self, value):
    """
    Set radiant fraction
    :param value: float
    """
    if value is not None:
      self._radiative_fraction = float(value)

  @property
  def latent_fraction(self) -> Union[None, float]:
    """
    Get latent fraction
    :return: None or float
    """
    return self._latent_fraction

  @latent_fraction.setter
  def latent_fraction(self, value):
    """
    Set latent fraction
    :param value: float
    """
    if value is not None:
      self._latent_fraction = float(value)

  @property
  def schedules(self) -> Union[None, List[Schedule]]:
    """
    Get schedules
    dataType = fraction
    :return: None or [Schedule]
    """
    return self._schedules

  @schedules.setter
  def schedules(self, value):
    """
    Set schedules
    dataType = fraction
    :param value: [Schedule]
    """
    self._schedules = value
