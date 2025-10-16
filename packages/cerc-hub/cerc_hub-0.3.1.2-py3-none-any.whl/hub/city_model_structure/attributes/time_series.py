"""
Time series module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from typing import List
from hub.city_model_structure.attributes.record import Record


class TimeSeries:
  """
  TimeSeries class
  """

  def __init__(self, time_series_type=None, records=None):
    self._time_series_type = time_series_type
    self._records = records

  @property
  def time_series_type(self):
    """
    Add explanation here
    :return: add type of variable here
    """
    return self._time_series_type

  @property
  def records(self) -> List[Record]:
    """
    Add explanation here
    :return: List[Record]
    """
    return self._records
