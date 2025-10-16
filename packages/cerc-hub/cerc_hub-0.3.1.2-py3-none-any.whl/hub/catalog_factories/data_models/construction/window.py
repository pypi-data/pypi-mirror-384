"""
Construction catalog window
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""


class Window:
  """
  Window class
  """
  def __init__(self, window_id, frame_ratio, g_value, overall_u_value, name, window_type=None):
    self._id = window_id
    self._frame_ratio = frame_ratio
    self._g_value = g_value
    self._overall_u_value = overall_u_value
    self._name = name
    self._type = window_type

  @property
  def id(self):
    """
    Get window id
    :return: str
    """
    return self._id

  @property
  def name(self):
    """
    Get window name
    :return: str
    """
    return self._name

  @property
  def frame_ratio(self):
    """
    Get window frame ratio
    :return: float
    """
    return self._frame_ratio

  @property
  def g_value(self):
    """
    Get thermal opening g-value
    :return: float
    """
    return self._g_value

  @property
  def overall_u_value(self):
    """
    Get thermal opening overall U-value in W/m2K
    :return: float
    """
    return self._overall_u_value

  @property
  def type(self):
    """
    Get transparent surface type, 'window' or 'skylight'
    :return: str
    """
    return self._type

  def to_dictionary(self):
    """Class content to dictionary"""
    content = {'Window': {'id': self.id,
                          'name': self.name,
                          'type': self.type,
                          'frame ratio': self.frame_ratio,
                          'g-value': self.g_value,
                          'overall U value [W/m2K]': self.overall_u_value
                          }
               }
    return content
