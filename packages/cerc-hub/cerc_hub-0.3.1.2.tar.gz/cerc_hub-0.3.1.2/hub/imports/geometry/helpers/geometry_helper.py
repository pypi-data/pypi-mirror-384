"""
Geometry helper
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""
import math
import sys

import numpy as np
from numpy import ndarray


class GeometryHelper:
  """
  Geometry helper
  """
  @staticmethod
  def to_points_matrix(points):
    """
    Transform a point vector into a point matrix
    :param points: [x, y, z, x, y, z ...]
    :return: [[x,y,z],[x,y,z]...]
    """
    rows = points.size // 3
    points = points.reshape(rows, 3)
    return points

  @staticmethod
  def gml_surface_to_hub(surface):
    """
    Transform citygml surface names into hub names
    """
    if surface == 'WallSurface':
      return 'Wall'
    if surface == 'GroundSurface':
      return 'Ground'
    return 'Roof'

  @staticmethod
  def points_from_string(coordinates) -> np.ndarray:
    """
    Creates a ndarray from a string
    :return: [Point]
    """
    points = np.fromstring(coordinates, dtype=float, sep=' ')
    points = GeometryHelper.to_points_matrix(points)
    return points

  @staticmethod
  def remove_last_point_from_string(points) -> [ndarray]:
    """
    Return the point list without the last element
    :return [ndarray]
    """
    array = points.split(' ')
    res = " "
    return res.join(array[0:len(array) - 3])

  @staticmethod
  def invert_points(points) -> [ndarray]:
    """
    Invert the point list
    :return: [ndarray]
    """
    res = []
    for point in points:
      res.insert(0, point)
    return res

  @staticmethod
  def ground_area(points):
    """
    Get ground surface area in square meters
    :return: float
    """
    # New method to calculate area

    if len(points) < 3:
      sys.stderr.write('Warning: the area of a line or point cannot be calculated 1. Area = 0\n')
      return 0
    alpha = 0
    vec_1 = points[1] - points[0]
    for i in range(2, len(points)):
      vec_2 = points[i] - points[0]
      alpha += GeometryHelper.angle_between_vectors(vec_1, vec_2)
    if alpha == 0:
      sys.stderr.write('Warning: the area of a line or point cannot be calculated 2. Area = 0\n')
      return 0
    #
    horizontal_points = points
    area = 0
    for i in range(0, len(horizontal_points) - 1):
      point = horizontal_points[i]
      next_point = horizontal_points[i + 1]
      area += (next_point[1] + point[1]) / 2 * (next_point[0] - point[0])
    next_point = horizontal_points[0]
    point = horizontal_points[len(horizontal_points) - 1]
    area += (next_point[1] + point[1]) / 2 * (next_point[0] - point[0])
    _area = abs(area)
    return _area

  @staticmethod
  def angle_between_vectors(vec_1, vec_2):
    """
    angle between vectors in radians
    :param vec_1: vector
    :param vec_2: vector
    :return: float
    """
    if np.linalg.norm(vec_1) == 0 or np.linalg.norm(vec_2) == 0:
      sys.stderr.write("Warning: impossible to calculate angle between planes' normal. Return 0\n")
      return 0
    cosine = np.dot(vec_1, vec_2) / np.linalg.norm(vec_1) / np.linalg.norm(vec_2)
    if cosine > 1 and cosine - 1 < 1e-5:
      cosine = 1
    elif cosine < -1 and cosine + 1 > -1e-5:
      cosine = -1
    alpha = math.acos(cosine)
    return alpha
