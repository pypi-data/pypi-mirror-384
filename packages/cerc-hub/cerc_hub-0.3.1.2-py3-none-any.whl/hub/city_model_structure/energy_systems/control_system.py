"""
Energy control system module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""


class ControlSystem:
  """
  ControlSystem class
  """
  def __init__(self):
    self._control_type = None

  @property
  def type(self):
    """
    Get control type
    :return: string
    """
    return self._control_type

  @type.setter
  def type(self, value):
    """
    Set control type
    :param value: string
    """
    self._control_type = value
