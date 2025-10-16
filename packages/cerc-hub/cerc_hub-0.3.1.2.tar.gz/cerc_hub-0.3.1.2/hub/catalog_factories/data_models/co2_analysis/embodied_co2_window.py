"""
Hub Embodied CO2 catalog for windows
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2019 - 2025 Concordia CERC group
Project Coder Koa Wells kekoa.wells@concordia.ca
"""


class EmbodiedCo2Window:
  """
  EmbodiedCo2Window class
  """
  def __init__(self, name, embodied_carbon, density):
    self._name = name
    self._embodied_carbon = embodied_carbon
    self._density = density

  @property
  def name(self):
    """
    :getter: Get window material name
    :return: str
    """
    return self._name

  @property
  def embodied_carbon(self):
    """
    :getter: Get embodied carbon emissions factor for the window material in TODO: add units
    :return: None or float
    """
    return self._embodied_carbon

  @property
  def density(self):
    """
    :getter: Get window material density in kg/m^3
    :return: None or float
    """
    return self._density

  def to_dictionary(self):
    """
    :getter: Convert class attributes to a dictionary
    :return: dict
    """
    content = {'Window': {'name': self.name,
                          'embodied_carbon': self._embodied_carbon,
                          'density': self.density,
                         }
               }
    return content
