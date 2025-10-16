"""
Polyhedron module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
Code contributors: Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from typing import List, Union
import sys
import math
import numpy as np
from trimesh import Trimesh
from hub.helpers.configuration_helper import ConfigurationHelper


class Polyhedron:
  """
  Polyhedron class
  """

  def __init__(self, polygons):
    self._polygons = polygons
    self._polyhedron = None
    self._triangulated_polyhedron = None
    self._volume = None
    self._faces = None
    self._vertices = None
    self._trimesh = None
    self._centroid = None
    self._max_z = None
    self._max_y = None
    self._max_x = None
    self._min_z = None
    self._min_y = None
    self._min_x = None

  def _position_of(self, point, face):
    """
    position of a specific point in the list of points that define a face
    :return: int
    """
    vertices = self.vertices
    for i, vertex in enumerate(vertices):
      # ensure not duplicated vertex
      power = 0
      vertex2 = vertex
      for dimension in range(0, 3):
        power += math.pow(vertex2[dimension] - point[dimension], 2)
      distance = math.sqrt(power)
      if i not in face and distance == 0:
        return i
    return -1

  @property
  def vertices(self) -> np.ndarray:
    """
    Get polyhedron vertices
    :return: np.ndarray(int)
    """
    if self._vertices is None:
      vertices, self._vertices = [], []
      _ = [vertices.extend(s.coordinates) for s in self._polygons]
      for vertex_1 in vertices:
        found = False
        for vertex_2 in self._vertices:
          found = False
          power = 0
          for dimension in range(0, 3):
            power += math.pow(vertex_2[dimension] - vertex_1[dimension], 2)
          distance = math.sqrt(power)
          if distance == 0:
            found = True
            break
        if not found:
          self._vertices.append(vertex_1)
      self._vertices = np.asarray(self._vertices)
    return self._vertices

  @property
  def faces(self) -> List[List[int]]:
    """
    Get polyhedron triangular faces
    :return: [face]
    """
    if self._faces is None:
      self._faces = []

      for polygon in self._polygons:

        face = []
        points = polygon.coordinates
        if len(points) != 3:
          sub_polygons = polygon.triangles
          if len(sub_polygons) < 1:
            continue
          for sub_polygon in sub_polygons:
            face = []
            points = sub_polygon.coordinates
            for point in points:
              face.append(self._position_of(point, face))
            self._faces.append(face)
        else:
          for point in points:
            face.append(self._position_of(point, face))
          self._faces.append(face)
    return self._faces

  @property
  def trimesh(self) -> Union[Trimesh, None]:
    """
    Get polyhedron trimesh
    :return: Trimesh
    """
    if self._trimesh is None:
      for face in self.faces:
        if len(face) != 3:
          sys.stderr.write('Not able to generate trimesh\n')
          return None
      self._trimesh = Trimesh(vertices=self.vertices, faces=self.faces)
    return self._trimesh

  @property
  def volume(self):
    """
    Get polyhedron volume in cubic meters
    :return: float
    """
    if self._volume is None:
      if self.trimesh is None:
        self._volume = np.inf
      elif not self.trimesh.is_volume:
        self._volume = np.inf
      else:
        self._volume = self.trimesh.volume
    return self._volume

  @property
  def max_z(self):
    """
    Get polyhedron maximal z value in meters
    :return: float
    """
    if self._max_z is None:
      self._max_z = ConfigurationHelper().min_coordinate
      for polygon in self._polygons:
        for point in polygon.coordinates:
          self._max_z = max(self._max_z, point[2])
    return self._max_z

  @property
  def max_y(self):
    """
    Get polyhedron maximal y value in meters
    :return: float
    """
    if self._max_y is None:
      self._max_y = ConfigurationHelper().min_coordinate
      for polygon in self._polygons:
        for point in polygon.coordinates:
          if self._max_y < point[1]:
            self._max_y = point[1]
    return self._max_y

  @property
  def max_x(self):
    """
    Get polyhedron maximal x value in meters
    :return: float
    """
    if self._max_x is None:
      self._max_x = ConfigurationHelper().min_coordinate
      for polygon in self._polygons:
        for point in polygon.coordinates:
          self._max_x = max(self._max_x, point[0])
    return self._max_x

  @property
  def min_z(self):
    """
    Get polyhedron minimal z value in meters
    :return: float
    """
    if self._min_z is None:
      self._min_z = self.max_z
      for polygon in self._polygons:
        for point in polygon.coordinates:
          if self._min_z > point[2]:
            self._min_z = point[2]
    return self._min_z

  @property
  def min_y(self):
    """
    Get polyhedron minimal y value in meters
    :return: float
    """
    if self._min_y is None:
      self._min_y = self.max_y
      for polygon in self._polygons:
        for point in polygon.coordinates:
          if self._min_y > point[1]:
            self._min_y = point[1]
    return self._min_y

  @property
  def min_x(self):
    """
    Get polyhedron minimal x value in meters
    :return: float
    """
    if self._min_x is None:
      self._min_x = self.max_x
      for polygon in self._polygons:
        for point in polygon.coordinates:
          if self._min_x > point[0]:
            self._min_x = point[0]
    return self._min_x

  @property
  def centroid(self) -> Union[None, List[float]]:
    """
    Get polyhedron centroid
    :return: [x,y,z]
    """
    if self._centroid is None:
      trimesh = self.trimesh
      if trimesh is None:
        return None
      self._centroid = self.trimesh.centroid
    return self._centroid

  def stl_export(self, full_path):
    """
    Export the polyhedron to stl given file
    :param full_path: str
    :return: None
    """
    self.trimesh.export(full_path, 'stl_ascii')

  def obj_export(self, full_path):
    """
    Export the polyhedron to obj given file
    :param full_path: str
    :return: None
    """
    self.trimesh.export(full_path, 'obj')

  def show(self):
    """
    Auxiliary function to render the polyhedron
    :return: None
    """
    self.trimesh.show()
