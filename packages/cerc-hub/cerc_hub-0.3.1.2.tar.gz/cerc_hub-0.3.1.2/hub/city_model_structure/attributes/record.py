"""
Record module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""


class Record:
  """
  Record class
  """

  def __init__(self, time=None, value=None, flag=None):
    self._time = time
    self._value = value
    self._flag = flag

  @property
  def time(self):
    """
    Add explanation here
    :return: add type of variable here
    """
    return self._time

  @property
  def value(self):
    """
    Add explanation here
    :return: add type of variable here
    """
    return self._value

  @property
  def flag(self):
    """
    Add explanation here
    :return: add type of variable here
    """
    return self._flag
