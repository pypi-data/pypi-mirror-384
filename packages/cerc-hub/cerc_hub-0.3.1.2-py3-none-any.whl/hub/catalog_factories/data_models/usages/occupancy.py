"""
Usage catalog occupancy
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez Guillermo.GutierrezMorote@concordia.ca
"""
from typing import Union, List

from hub.catalog_factories.data_models.usages.schedule import Schedule


class Occupancy:
  """
  Occupancy class
  """
  def __init__(self,
               occupancy_density,
               sensible_convective_internal_gain,
               sensible_radiative_internal_gain,
               latent_internal_gain,
               schedules):
    self._occupancy_density = occupancy_density
    self._sensible_convective_internal_gain = sensible_convective_internal_gain
    self._sensible_radiative_internal_gain = sensible_radiative_internal_gain
    self._latent_internal_gain = latent_internal_gain
    self._schedules = schedules

  @property
  def occupancy_density(self) -> Union[None, float]:
    """
    Get density in persons per m2
    :return: None or float
    """
    return self._occupancy_density

  @property
  def sensible_convective_internal_gain(self) -> Union[None, float]:
    """
    Get sensible convective internal gain in Watts per m2
    :return: None or float
    """
    return self._sensible_convective_internal_gain

  @property
  def sensible_radiative_internal_gain(self) -> Union[None, float]:
    """
    Get sensible radiant internal gain in Watts per m2
    :return: None or float
    """
    return self._sensible_radiative_internal_gain

  @property
  def latent_internal_gain(self) -> Union[None, float]:
    """
    Get latent internal gain in Watts per m2
    :return: None or float
    """
    return self._latent_internal_gain

  @property
  def schedules(self) -> Union[None, List[Schedule]]:
    """
    Get occupancy schedules
    dataType = fraction
    :return: None or [Schedule]
    """
    return self._schedules

  def to_dictionary(self):
    """Class content to dictionary"""
    _schedules = []
    for _schedule in self.schedules:
      _schedules.append(_schedule.to_dictionary())
    content = {'Occupancy': {'occupancy density [persons/m2]': self.occupancy_density,
                             'sensible convective internal gain [W/m2]': self.sensible_convective_internal_gain,
                             'sensible radiative internal gain [W/m2]': self.sensible_radiative_internal_gain,
                             'latent internal gain [W/m2]': self.latent_internal_gain,
                             'schedules': _schedules}
               }
    return content
