"""
Usage catalog schedule
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

from typing import Union, List


class Schedule:
  """
  Schedule class
  """

  def __init__(self, schedule_type, values, data_type, time_step, time_range, day_types):
    self._type = schedule_type
    self._values = values
    self._data_type = data_type
    self._time_step = time_step
    self._time_range = time_range
    self._day_types = day_types

  @property
  def type(self) -> Union[None, str]:
    """
    Get schedule type
    :return: None or str
    """
    return self._type

  @property
  def values(self):
    """
    Get schedule values
    :return: [Any]
    """
    return self._values

  @property
  def data_type(self) -> Union[None, str]:
    """
    Get schedule data type from:
    ['any_number', 'fraction', 'on_off', 'temperature', 'humidity', 'control_type']
    :return: None or str
    """
    return self._data_type

  @property
  def time_step(self) -> Union[None, str]:
    """
    Get schedule time step from:
    ['second', 'minute', 'hour', 'day', 'week', 'month']
    :return: None or str
    """
    return self._time_step

  @property
  def time_range(self) -> Union[None, str]:
    """
    Get schedule time range from:
    ['minute', 'hour', 'day', 'week', 'month', 'year']
    :return: None or str
    """
    return self._time_range

  @property
  def day_types(self) -> Union[None, List[str]]:
    """
    Get schedule day types, as many as needed from:
    ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'holiday', 'winter_design_day',
    'summer_design_day']
    :return: None or [str]
    """
    return self._day_types

  def to_dictionary(self):
    """Class content to dictionary"""
    content = {'Schedule': {'type': self.type,
                            'time range': self.time_range,
                            'time step': self.time_step,
                            'data type': self.data_type,
                            'day types': self.day_types,
                            'values': self.values}
               }
    return content
