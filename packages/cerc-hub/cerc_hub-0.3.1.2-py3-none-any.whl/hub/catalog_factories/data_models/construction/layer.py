"""
Construction catalog layer
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

from hub.catalog_factories.data_models.construction.material import Material


class Layer:
  """
  Layer class
  """
  def __init__(self, layer_id, name, material, thickness):
    self._id = layer_id
    self._name = name
    self._material = material
    self._thickness = thickness

  @property
  def id(self):
    """
    Get layer id
    :return: str
    """
    return self._id

  @property
  def name(self):
    """
    Get layer name
    :return: str
    """
    return self._name

  @property
  def material(self) -> Material:
    """
    Get layer material
    :return: Material
    """
    return self._material

  @property
  def thickness(self):
    """
    Get layer thickness in meters
    :return: None or float
    """
    return self._thickness

  def to_dictionary(self):
    """Class content to dictionary"""
    content = {'Layer': {'id': self.id,
                         'name': self.name,
                         'thickness [m]': self.thickness,
                         'material': self.material.to_dictionary()
                         }
               }
    return content
