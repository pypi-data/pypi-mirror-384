"""
Emission system module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""


class EmissionSystem:
  """
  EmissionSystem class
  """
  def __init__(self):
    self._model_name = None
    self._type = None
    self._parasitic_energy_consumption = 0

  @property
  def model_name(self):
    """
    Get model name
    :return: string
    """
    return self._model_name

  @model_name.setter
  def model_name(self, value):
    """
    Set model name
    :param value: string
    """
    self._model_name = value

  @property
  def type(self):
    """
    Get type
    :return: string
    """
    return self._type

  @type.setter
  def type(self, value):
    """
    Set type
    :param value: string
    """
    self._type = value

  @property
  def parasitic_energy_consumption(self):
    """
    Get parasitic_energy_consumption in ratio (W/W)
    :return: float
    """
    return self._parasitic_energy_consumption

  @parasitic_energy_consumption.setter
  def parasitic_energy_consumption(self, value):
    """
    Set parasitic_energy_consumption in ratio (W/W)
    :param value: float
    """
    self._parasitic_energy_consumption = value
