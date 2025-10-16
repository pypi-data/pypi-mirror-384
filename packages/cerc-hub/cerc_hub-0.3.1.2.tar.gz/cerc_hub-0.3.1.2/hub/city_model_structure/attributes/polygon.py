"""
Polygon module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from __future__ import annotations

import logging
import math
import sys
from typing import List

import numpy as np
import trimesh.creation
import trimesh.geometry
import trimesh.intersections
from shapely.geometry.polygon import Polygon as shapley_polygon
from trimesh import Trimesh

from hub.city_model_structure.attributes.plane import Plane
from hub.city_model_structure.attributes.point import Point


class Polygon:
  """
  Polygon class
  """
  def __init__(self, coordinates):
    self._area = None
    self._points = None
    self._points_list = None
    self._normal = None
    self._inverse = None
    self._edges = None
    self._coordinates = coordinates
    self._triangles = None
    self._vertices = None
    self._faces = None
    self._plane = None

  @property
  def points(self) -> List[Point]:
    """
    Get the points belonging to the polygon [[x, y, z],...]
    :return: [Point]
    """
    if self._points is None:
      self._points = []
      for coordinate in self.coordinates:
        self._points.append(Point(coordinate))
    return self._points

  @property
  def plane(self) -> Plane:
    """
    Get the polygon plane
    :return: Plane
    """
    if self._plane is None:
      self._plane = Plane(normal=self.normal, origin=self.points[0])
    return self._plane

  @property
  def coordinates(self) -> List[np.ndarray]:
    """
    Get the points in the shape of its coordinates belonging to the polygon [[x, y, z],...]
    :return: [np.ndarray]
    """
    return self._coordinates

  @property
  def points_list(self) -> np.ndarray:
    """
    Get the solid surface point coordinates list [x, y, z, x, y, z,...]
    :return: np.ndarray
    """
    if self._points_list is None:
      s = self.coordinates
      self._points_list = np.reshape(s, len(s) * 3)
    return self._points_list

  @property
  def edges(self) -> List[List[Point]]:
    """
    Get polygon edges list
    :return: [[Point]]
    """
    if self._edges is None:
      self._edges = []
      for i in range(0, len(self.points) - 1):
        point_1 = self.points[i]
        point_2 = self.points[i + 1]
        self._edges.append([point_1, point_2])
      self._edges.append([self.points[len(self.points) - 1], self.points[0]])
    return self._edges

  @property
  def area(self):
    """
    Get surface area in square meters
    :return: float
    """
    if self._area is None:
      self._area = 0
      for triangle in self.triangles:
        a_b = np.zeros(3)
        a_c = np.zeros(3)
        for i in range(0, 3):
          a_b[i] = triangle.coordinates[1][i] - triangle.coordinates[0][i]
          a_c[i] = triangle.coordinates[2][i] - triangle.coordinates[0][i]
        self._area += np.linalg.norm(np.cross(a_b, a_c)) / 2
    return self._area

  @area.setter
  def area(self, value):
    self._area = value

  @property
  def normal(self) -> np.ndarray:
    """
    Get surface normal vector
    :return: np.ndarray
    """
    if self._normal is None:
      points = self.coordinates
      # todo: IF THE FIRST ONE IS 0, START WITH THE NEXT
      point_origin = points[len(points) - 2]
      vector_1 = points[len(points) - 1] - point_origin
      vector_2 = points[0] - point_origin
      vector_3 = points[1] - point_origin
      cross_product = np.cross(vector_1, vector_2)
      if np.linalg.norm(cross_product) != 0:
        cross_product = cross_product / np.linalg.norm(cross_product)
        alpha = self._angle_between_vectors(vector_1, vector_2)
      else:
        cross_product = [0, 0, 0]
        alpha = 0
      if len(points) == 3:
        return cross_product
      if np.linalg.norm(cross_product) == 0:
        return cross_product
      alpha += self._angle(vector_2, vector_3, cross_product)
      for i in range(0, len(points) - 4):
        vector_1 = points[i + 1] - point_origin
        vector_2 = points[i + 2] - point_origin
        alpha += self._angle(vector_1, vector_2, cross_product)
      vector_1 = points[len(points) - 1] - point_origin
      vector_2 = points[0] - point_origin
      if alpha < 0:
        cross_product = np.cross(vector_2, vector_1)
      else:
        cross_product = np.cross(vector_1, vector_2)
      self._normal = cross_product / np.linalg.norm(cross_product)
    return self._normal

  @staticmethod
  def _angle(vector_1, vector_2, cross_product):
    """
    alpha angle in radians
    :param vector_1: [float]
    :param vector_2: [float]
    :param cross_product: [float]
    :return: float
    """
    accepted_normal_difference = 0.01
    cross_product_next = np.cross(vector_1, vector_2)
    if np.linalg.norm(cross_product_next) != 0:
      cross_product_next = cross_product_next / np.linalg.norm(cross_product_next)
      alpha = Polygon._angle_between_vectors(vector_1, vector_2)
    else:
      cross_product_next = [0, 0, 0]
      alpha = 0
    delta_normals = 0
    for j in range(0, 3):
      delta_normals += cross_product[j] - cross_product_next[j]
    if np.abs(delta_normals) < accepted_normal_difference:
      return alpha
    return -alpha

  @staticmethod
  def triangle_mesh(vertices, normal) -> Trimesh:
    """
    Get the triangulated mesh for the polygon
    :return: Trimesh
    """
    min_x = 1e16
    min_y = 1e16
    min_z = 1e16
    for vertex in vertices:
      if vertex[0] < min_x:
        min_x = vertex[0]
      if vertex[1] < min_y:
        min_y = vertex[1]
      if vertex[2] < min_z:
        min_z = vertex[2]

    new_vertices = []
    for vertex in vertices:
      vertex = [vertex[0]-min_x, vertex[1]-min_y, vertex[2]-min_z]
      new_vertices.append(vertex)

    transformation_matrix = trimesh.geometry.plane_transform(origin=new_vertices[0], normal=normal)

    coordinates = []
    for vertex in vertices:
      transformed_vertex = [vertex[0]-min_x, vertex[1]-min_y, vertex[2]-min_z, 1]
      transformed_vertex = np.dot(transformation_matrix, transformed_vertex)
      coordinate = [transformed_vertex[0], transformed_vertex[1]]
      coordinates.append(coordinate)

    polygon = shapley_polygon(coordinates)

    try:
      _, faces = trimesh.creation.triangulate_polygon(polygon, engine='triangle')

      mesh = Trimesh(vertices=vertices, faces=faces)

      # check orientation
      normal_sum = 0
      for i in range(0, 3):
        normal_sum += normal[i] + mesh.face_normals[0][i]

      if abs(normal_sum) <= 1E-10:
        new_faces = []
        for face in faces:
          new_face = []
          for i in range(0, len(face)):
            new_face.append(face[len(face)-i-1])
          new_faces.append(new_face)
        mesh = Trimesh(vertices=vertices, faces=new_faces)
      return mesh

    except ValueError:
      logging.error('Not able to triangulate polygon\n')
      _vertices = [[0, 0, 0], [0, 0, 1], [0, 1, 0]]
      _faces = [[0, 1, 2]]
      return Trimesh(vertices=_vertices, faces=_faces)

  @property
  def triangles(self) -> List[Polygon]:
    """
    Triangulate the polygon and return a list of triangular polygons
    :return: [Polygon]
    """
    if self._triangles is None:
      self._triangles = []
      _mesh = self.triangle_mesh(self.coordinates, self.normal)
      for face in _mesh.faces:
        points = []
        for vertex in face:
          points.append(self.coordinates[vertex])
        polygon = Polygon(points)
        self._triangles.append(polygon)
    return self._triangles

  @staticmethod
  def _angle_between_vectors(vec_1, vec_2):
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

  @property
  def inverse(self):
    """
    Get the polygon coordinates in reversed order
    :return: [np.ndarray]
    """
    if self._inverse is None:
      self._inverse = self.coordinates[::-1]
    return self._inverse

  def divide(self, plane):
    """
    Divides the polygon in two by a plane
    :param plane: plane that intersects with self to divide it in two parts (Plane)
    :return: Polygon, Polygon, [Point]
    """
    tri_polygons = Trimesh(vertices=self.vertices, faces=self.faces)
    intersection = trimesh.intersections.mesh_plane(tri_polygons, plane.normal, plane.origin.coordinates)
    polys_1 = trimesh.intersections.slice_mesh_plane(tri_polygons, plane.opposite_normal, plane.origin.coordinates)
    polys_2 = trimesh.intersections.slice_mesh_plane(tri_polygons, plane.normal, plane.origin.coordinates)
    triangles_1 = []
    for triangle in polys_1.triangles:
      triangles_1.append(Polygon(triangle))
    polygon_1 = self._reshape(triangles_1)
    triangles_2 = []
    for triangle in polys_2.triangles:
      triangles_2.append(Polygon(triangle))
    polygon_2 = self._reshape(triangles_2)
    return polygon_1, polygon_2, intersection

  def _reshape(self, triangles) -> Polygon:
    edges_list = []
    for i in enumerate(triangles):
      for edge in triangles[i].edges:
        if not self._edge_in_edges_list(edge, edges_list):
          edges_list.append(edge)
        else:
          edges_list = self._remove_from_list(edge, edges_list)
    points = self._order_points(edges_list)
    return Polygon(points)

  @staticmethod
  def _edge_in_edges_list(edge, edges_list):
    for edge_element in edges_list:
      if (edge_element[0].distance_to_point(edge[0]) == 0 and edge_element[1].distance_to_point(edge[1]) == 0) or \
          (edge_element[1].distance_to_point(edge[0]) == 0 and edge_element[0].distance_to_point(
            edge[1]) == 0):
        return True
    return False

  @staticmethod
  def _order_points(edges_list):
    # todo: not sure that this method works for any case -> RECHECK
    points = edges_list[0]
    for _ in range(0, len(points)):
      for i in range(1, len(edges_list)):
        point_1 = edges_list[i][0]
        point_2 = points[len(points) - 1]
        if point_1.distance_to_point(point_2) == 0:
          points.append(edges_list[i][1])
    points.remove(points[len(points) - 1])
    array_points = []
    for point in points:
      array_points.append(point.coordinates)
    return np.array(array_points)

  @staticmethod
  def _remove_from_list(edge, edges_list):
    new_list = []
    for edge_element in edges_list:
      if not ((edge_element[0].distance_to_point(edge[0]) == 0 and edge_element[1].distance_to_point(
          edge[1]) == 0) or
              (edge_element[1].distance_to_point(edge[0]) == 0 and edge_element[0].distance_to_point(
                edge[1]) == 0)):
        new_list.append(edge_element)
    return new_list

  @property
  def vertices(self) -> np.ndarray:
    """
    Get polygon vertices
    :return: np.ndarray(int)
    """
    if self._vertices is None:
      vertices, self._vertices = [], []
      _ = [vertices.extend(s.coordinates) for s in self.triangles]
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
    Get polygon triangular faces
    :return: [face]
    """
    if self._faces is None:
      self._faces = []

      for polygon in self.triangles:
        face = []
        points = polygon.coordinates
        if len(points) != 3:
          sub_polygons = polygon.triangles
          # todo: I modified this! To be checked @Guille
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

  def _position_of(self, point, face):
    """
    position of a specific point in the list of points that define a face
    :return: int
    """
    vertices = self.vertices
    for i in enumerate(vertices):
      # ensure not duplicated vertex
      power = 0
      vertex2 = vertices[i]
      for dimension in range(0, 3):
        power += math.pow(vertex2[dimension] - point[dimension], 2)
      distance = math.sqrt(power)
      if i not in face and distance == 0:
        return i
    return -1
