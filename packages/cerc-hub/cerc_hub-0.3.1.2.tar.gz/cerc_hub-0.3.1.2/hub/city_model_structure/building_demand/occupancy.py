"""
Occupancy module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""
from typing import Union, List
from hub.city_model_structure.attributes.schedule import Schedule


class Occupancy:
  """
  Occupancy class
  """
  def __init__(self):
    self._occupancy_density = None
    self._sensible_convective_internal_gain = None
    self._sensible_radiative_internal_gain = None
    self._latent_internal_gain = None
    self._occupancy_schedules = None
    self._occupants = None

  @property
  def occupancy_density(self) -> Union[None, float]:
    """
    Get density in persons per m2
    :return: None or float
    """
    return self._occupancy_density

  @occupancy_density.setter
  def occupancy_density(self, value):
    """
    Set density in persons per m2
    :param value: float
    """
    if value is not None:
      self._occupancy_density = float(value)

  @property
  def sensible_convective_internal_gain(self) -> Union[None, float]:
    """
    Get sensible convective internal gain in Watts per m2
    :return: None or float
    """
    return self._sensible_convective_internal_gain

  @sensible_convective_internal_gain.setter
  def sensible_convective_internal_gain(self, value):
    """
    Set sensible convective internal gain in Watts per m2
    :param value: float
    """
    if value is not None:
      self._sensible_convective_internal_gain = float(value)

  @property
  def sensible_radiative_internal_gain(self) -> Union[None, float]:
    """
    Get sensible radiant internal gain in Watts per m2
    :return: None or float
    """
    return self._sensible_radiative_internal_gain

  @sensible_radiative_internal_gain.setter
  def sensible_radiative_internal_gain(self, value):
    """
    Set sensible radiant internal gain in Watts per m2
    :param value: float
    """
    if value is not None:
      self._sensible_radiative_internal_gain = float(value)

  @property
  def latent_internal_gain(self) -> Union[None, float]:
    """
    Get latent internal gain in Watts per m2
    :return: None or float
    """
    return self._latent_internal_gain

  @latent_internal_gain.setter
  def latent_internal_gain(self, value):
    """
    Set latent internal gain in Watts per m2
    :param value: float
    """
    if value is not None:
      self._latent_internal_gain = float(value)

  @property
  def occupancy_schedules(self) -> Union[None, List[Schedule]]:
    """
    Get occupancy schedules
    dataType = fraction
    :return: None or [Schedule]
    """
    return self._occupancy_schedules

  @occupancy_schedules.setter
  def occupancy_schedules(self, value):
    """
    Set occupancy schedules
    dataType = fraction
    :param value: [Schedule]
    """
    self._occupancy_schedules = value
