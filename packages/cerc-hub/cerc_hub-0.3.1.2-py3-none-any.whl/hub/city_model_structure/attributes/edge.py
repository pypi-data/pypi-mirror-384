"""
Node module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""
import uuid
from typing import List, TypeVar

Node = TypeVar('Node')


class Edge:
  """
  Generic edge class to be used as base for the network edges
  """
  def __init__(self, name, nodes=None):
    if nodes is None:
      nodes = []
    self._name = name
    self._id = None
    self._nodes = nodes

  @property
  def name(self):
    """
    Get edge name
    :return: str
    """
    return self._name

  @property
  def id(self):
    """
    Get edge id, a universally unique identifier randomly generated
    :return: str
    """
    if self._id is None:
      self._id = uuid.uuid4()
    return self._id

  @property
  def nodes(self) -> List[Node]:
    """
    Get delimiting nodes for the edge
    :return: [Node]
    """
    return self._nodes
