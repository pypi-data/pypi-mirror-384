"""
Node module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

import uuid
from typing import List, TypeVar
from hub.city_model_structure.attributes.time_series import TimeSeries
Edge = TypeVar('Edge')


class Node:
  """
  Generic node class to be used as base for the network nodes
  """
  def __init__(self, name, edges=None):
    if edges is None:
      edges = []
    self._name = name
    self._id = None
    self._edges = edges
    self._time_series = None

  @property
  def name(self):
    """
    Get node name
    :return: str
    """
    return self._name

  @property
  def id(self):
    """
    Get node id, a universally unique identifier randomly generated
    :return: str
    """
    if self._id is None:
      self._id = uuid.uuid4()
    return self._id

  @property
  def edges(self) -> List[Edge]:
    """
    Get edges delimited by the node
    :return: [Edge]
    """
    return self._edges

  @property
  def time_series(self) -> TimeSeries:
    """
    Add explanation here
    :return: add type of variable here
    """
    return self._time_series
