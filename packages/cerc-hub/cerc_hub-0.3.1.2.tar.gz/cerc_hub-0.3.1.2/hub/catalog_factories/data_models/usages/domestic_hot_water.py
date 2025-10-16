"""
Usage catalog domestic hot water
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from typing import Union, List

from hub.catalog_factories.data_models.usages.schedule import Schedule


class DomesticHotWater:
  """
  DomesticHotWater class
  """
  def __init__(self, density, peak_flow, service_temperature, schedules):
    self._density = density
    self._peak_flow = peak_flow
    self._service_temperature = service_temperature
    self._schedules = schedules

  @property
  def density(self) -> Union[None, float]:
    """
    Get domestic hot water load density in Watts per m2
    :return: None or float
    """
    return self._density

  @property
  def peak_flow(self) -> Union[None, float]:
    """
    Get domestic hot water peak_flow density in m3 per second and m2
    :return: None or float
    """
    return self._peak_flow

  @property
  def service_temperature(self) -> Union[None, float]:
    """
    Get service temperature in degrees Celsius
    :return: None or float
    """
    return self._service_temperature

  @property
  def schedules(self) -> Union[None, List[Schedule]]:
    """
    Get schedules
    dataType = fraction of loads
    :return: None or [Schedule]
    """
    return self._schedules

  def to_dictionary(self):
    """Class content to dictionary"""
    _schedules = []
    for _schedule in self.schedules:
      _schedules.append(_schedule.to_dictionary())
    content = {'Domestic hot water': {'density [W/m2]': self.density,
                                      'peak flow [m3/sm2]': self.peak_flow,
                                      'service temperature [Celsius]': self.service_temperature,
                                      'schedules': _schedules}
               }
    return content
