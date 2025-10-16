"""
Hub Embodied CO2 catalog for materials
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2019 - 2025 Concordia CERC group
Project Coder Koa Wells kekoa.wells@concordia.ca
"""


class EmbodiedCo2Material:
  """
  EmbodiedCo2Material class
  """
  def __init__(self, name, embodied_carbon):
    self._name = name
    self._embodied_carbon = embodied_carbon

  @property
  def name(self):
    """
    :getter: Get material name
    :return: str
    """
    return self._name

  @property
  def embodied_carbon(self):
    """
    :getter: Get embodied carbon emissions factor for the material in TODO: add units
    :return: None or float
    """
    return self._embodied_carbon

  def to_dictionary(self):
    """
    Convert class attributes to a dictionary
    :return: dict
    """
    content = {'Material': {'name': self.name,
                            'embodied_carbon': self.embodied_carbon
                           }
               }
    return content
