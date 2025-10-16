"""
CityGmlBase module abstract class to template the different level of details
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

from abc import ABC


class CityGmlBase(ABC):
  """
  CityGmlBase class inherited by the specific level of detail classes.
  """
  def __init__(self):
    self._surfaces = []

  @property
  def surfaces(self):
    """
    Get parsed surfaces
    """
    return self._surfaces

  @classmethod
  def _solid(cls, city_object_member):
    raise NotImplementedError

  @classmethod
  def _multi_surface(cls, city_object_member):
    raise NotImplementedError

  @classmethod
  def _multi_curve(cls, city_object_member):
    raise NotImplementedError
