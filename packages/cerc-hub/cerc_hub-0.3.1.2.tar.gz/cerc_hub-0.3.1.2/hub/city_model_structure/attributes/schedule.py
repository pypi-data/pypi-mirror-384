"""
Schedule module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

import uuid
from typing import Union, List


class Schedule:
  """
  Schedule class
  """

  def __init__(self):
    self._id = None
    self._type = None
    self._values = None
    self._data_type = None
    self._time_step = None
    self._time_range = None
    self._day_types = None

  @property
  def id(self):
    """
    Get schedule id, a universally unique identifier randomly generated
    :return: str
    """
    if self._id is None:
      self._id = uuid.uuid4()
    return self._id

  @property
  def type(self) -> Union[None, str]:
    """
    Get schedule type
    :return: None or str
    """
    return self._type

  @type.setter
  def type(self, value):
    """
    Set schedule type
    :param: str
    """
    if value is not None:
      self._type = str(value)

  @property
  def values(self):
    """
    Get schedule values
    :return: [Any]
    """
    return self._values

  @values.setter
  def values(self, value):
    """
    Set schedule values
    :param: [Any]
    """
    self._values = value

  @property
  def data_type(self) -> Union[None, str]:
    """
    Get schedule data type from:
    ['any_number', 'fraction', 'on_off', 'temperature', 'humidity', 'control_type']
    :return: None or str
    """
    return self._data_type

  @data_type.setter
  def data_type(self, value):
    """
    Set schedule data type
    :param: str
    """
    if value is not None:
      self._data_type = str(value)

  @property
  def time_step(self) -> Union[None, str]:
    """
    Get schedule time step from:
    ['second', 'minute', 'hour', 'day', 'week', 'month']
    :return: None or str
    """
    return self._time_step

  @time_step.setter
  def time_step(self, value):
    """
    Set schedule time step
    :param: str
    """
    if value is not None:
      self._time_step = str(value)

  @property
  def time_range(self) -> Union[None, str]:
    """
    Get schedule time range from:
    ['minute', 'hour', 'day', 'week', 'month', 'year']
    :return: None or str
    """
    return self._time_range

  @time_range.setter
  def time_range(self, value):
    """
    Set schedule time range
    :param: str
    """
    if value is not None:
      self._time_range = str(value)

  @property
  def day_types(self) -> Union[None, List[str]]:
    """
    Get schedule day types, as many as needed from:
    ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'holiday', 'winter_design_day',
    'summer_design_day']
    :return: None or [str]
    """
    return self._day_types

  @day_types.setter
  def day_types(self, value):
    """
    Set schedule day types
    :param: [str]
    """
    if value is not None:
      self._day_types = [str(i) for i in value]
