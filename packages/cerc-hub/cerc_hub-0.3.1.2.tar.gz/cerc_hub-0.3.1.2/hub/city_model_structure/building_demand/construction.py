"""
Construction thermal parameters
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from hub.city_model_structure.building_demand.layer import Layer


class Construction:
  """
  Construction class
  """
  def __init__(self):
    self._type = None
    self._name = None
    self._layers = None
    self._window_ratio = None
    self._window_frame_ratio = None
    self._window_g_value = None
    self._window_overall_u_value = None
    self._window_type = None

  @property
  def type(self):
    """
    Get construction type
    :return: str
    """
    return self._type

  @type.setter
  def type(self, value):
    """
    Set construction type
    :param value: str
    """
    self._type = value

  @property
  def name(self):
    """
    Get construction name
    :return: str
    """
    return self._name

  @name.setter
  def name(self, value):
    """
    Set construction name
    :param value: str
    """
    self._name = value

  @property
  def layers(self) -> [Layer]:
    """
    Get layers
    :return: [layer]
    """
    return self._layers

  @layers.setter
  def layers(self, value):
    """
    Set layers
    :param value: [layer]
    """
    self._layers = value

  @property
  def window_ratio(self):
    """
    Get window ratio
    :return: dict
    """
    return self._window_ratio

  @window_ratio.setter
  def window_ratio(self, value):
    """
    Set window ratio
    :param value: dict
    """
    self._window_ratio = value

  @property
  def window_frame_ratio(self):
    """
    Get window frame ratio
    :return: float
    """
    return self._window_frame_ratio

  @window_frame_ratio.setter
  def window_frame_ratio(self, value):
    """
    Set window frame ratio
    :param value: float
    """
    self._window_frame_ratio = value

  @property
  def window_g_value(self):
    """
    Get transparent surface g-value
    :return: float
    """
    return self._window_g_value

  @window_g_value.setter
  def window_g_value(self, value):
    """
    Set transparent surface g-value
    :param value: float
    """
    self._window_g_value = value

  @property
  def window_overall_u_value(self):
    """
    Get transparent surface overall U-value in W/m2K
    :return: float
    """
    return self._window_overall_u_value

  @window_overall_u_value.setter
  def window_overall_u_value(self, value):
    """
    Set transparent surface overall U-value in W/m2K
    :param value: float
    """
    self._window_overall_u_value = value

  @property
  def window_type(self):
    """
    Get transparent surface type, 'window' or 'skylight'
    :return: str
    """
    return self._window_type

  @window_type.setter
  def window_type(self, value):
    """
    Set transparent surface type, 'window' or 'skylight'
    :return: str
    """
    self._window_type = value
