"""
Usage catalog lighting
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

from typing import Union, List

from hub.catalog_factories.data_models.usages.schedule import Schedule


class Lighting:
  """
  Lighting class
  """
  def __init__(self, density, convective_fraction, radiative_fraction, latent_fraction, schedules):
    self._density = density
    self._convective_fraction = convective_fraction
    self._radiative_fraction = radiative_fraction
    self._latent_fraction = latent_fraction
    self._schedules = schedules

  @property
  def density(self) -> Union[None, float]:
    """
    Get lighting density in Watts per m2
    :return: None or float
    """
    return self._density

  @property
  def convective_fraction(self) -> Union[None, float]:
    """
    Get convective fraction
    :return: None or float
    """
    return self._convective_fraction

  @property
  def radiative_fraction(self) -> Union[None, float]:
    """
    Get radiant fraction
    :return: None or float
    """
    return self._radiative_fraction

  @property
  def latent_fraction(self) -> Union[None, float]:
    """
    Get latent fraction
    :return: None or float
    """
    return self._latent_fraction

  @property
  def schedules(self) -> Union[None, List[Schedule]]:
    """
    Get schedules
    dataType = fraction
    :return: None or [Schedule]
    """
    return self._schedules

  def to_dictionary(self):
    """Class content to dictionary"""
    _schedules = []
    for _schedule in self.schedules:
      _schedules.append(_schedule.to_dictionary())
    content = {'Lighting': {'density [W/m2]': self.density,
                            'convective fraction': self.convective_fraction,
                            'radiative fraction': self.radiative_fraction,
                            'latent fraction': self.latent_fraction,
                            'schedules': _schedules}
               }
    return content
