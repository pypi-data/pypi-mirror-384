"""
Sensor type module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

from enum import Enum


class SensorType(Enum):
  """
  Sensor type enumeration
  """
  HUMIDITY = 0
  TEMPERATURE = 1
  CO2 = 2
  NOISE = 3
  PRESSURE = 4
  DIRECT_RADIATION = 5
  DIFFUSE_RADIATION = 6
  GLOBAL_RADIATION = 7
  AIR_QUALITY = 8
  GAS_FLOW = 9
  ENERGY = 10
