"""
Network module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

import uuid
from typing import List

from hub.city_model_structure.city_object import CityObject
from hub.city_model_structure.attributes.edge import Edge
from hub.city_model_structure.attributes.node import Node


class Network(CityObject):
  """
  Generic network class to be used as base for the network models
  """
  def __init__(self, name, edges=None, nodes=None):
    super().__init__(name, 0)
    if nodes is None:
      nodes = []
    if edges is None:
      edges = []
    self._id = None
    self._edges = edges
    self._nodes = nodes

  @property
  def id(self):
    """
    Get network id, a universally unique identifier randomly generated
    :return: str
    """
    if self._id is None:
      self._id = uuid.uuid4()
    return self._id

  @property
  def edges(self) -> List[Edge]:
    """
    Get network edges
    :return: [Edge]
    """
    return self._edges

  @property
  def nodes(self) -> List[Node]:
    """
    Get network nodes
    :return: [Node]
    """
    return self._nodes
