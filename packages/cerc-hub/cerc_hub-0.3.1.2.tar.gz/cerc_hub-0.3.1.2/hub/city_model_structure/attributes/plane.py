"""
Plane module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from typing import TypeVar
import numpy as np

Point = TypeVar('Point')


class Plane:
  """
  Plane class
  """

  def __init__(self, origin, normal):
    self._origin = origin
    self._normal = normal
    self._equation = None
    self._opposite_normal = None

  @property
  def origin(self) -> Point:
    """
    Get plane origin point
    :return: Point
    """
    return self._origin

  @property
  def normal(self):
    """
    Get plane normal [x, y, z]
    :return: np.ndarray
    """
    return self._normal

  @property
  def equation(self) -> (float, float, float, float):
    """
    Get the plane equation components Ax + By + Cz + D = 0
    :return: (A, B, C, D)
    """
    if self._equation is None:
      a = self.normal[0]
      b = self.normal[1]
      c = self.normal[2]
      d = -1 * self.origin.coordinates[0] * self.normal[0]
      d += -1 * self.origin.coordinates[1] * self.normal[1]
      d += -1 * self.origin.coordinates[2] * self.normal[2]
      self._equation = a, b, c, d
    return self._equation

  def distance_to_point(self, point):
    """
    Distance between the given point and the plane
    :return: float
    """
    p = point
    e = self.equation
    denominator = np.abs((p[0] * e[0]) + (p[1] * e[1]) + (p[2] * e[2]) + e[3])
    numerator = np.sqrt((e[0]**2) + (e[1]**2) + (e[2]**2))
    return float(denominator / numerator)

  @property
  def opposite_normal(self):
    """
    get plane normal in the opposite direction [x, y, z]
    :return: np.ndarray
    """
    if self._opposite_normal is None:
      coordinates = []
      for coordinate in self.normal:
        coordinates.append(-coordinate)
      self._opposite_normal = np.array(coordinates)
    return self._opposite_normal
