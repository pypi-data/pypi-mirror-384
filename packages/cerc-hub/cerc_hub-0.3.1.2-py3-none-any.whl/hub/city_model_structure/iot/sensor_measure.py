"""
Sensor measure module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""


class SensorMeasure:
  """
  Sensor measure class
  """
  def __init__(self, latitude, longitude, utc_timestamp, value):
    self._latitude = latitude
    self._longitude = longitude
    self._utc_timestamp = utc_timestamp
    self._value = value

  @property
  def latitude(self):
    """
    Get measure latitude
    """
    return self._latitude

  @property
  def longitude(self):
    """
    Get measure longitude
    """
    return self._longitude

  @property
  def utc_timestamp(self):
    """
    Get measure timestamp in utc
    """
    return self._utc_timestamp

  @property
  def value(self):
    """
    Get sensor measure value
    """
    return self._value
