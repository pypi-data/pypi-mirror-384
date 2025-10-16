"""
Construction catalog construction
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

from hub.catalog_factories.data_models.construction.layer import Layer
from hub.catalog_factories.data_models.construction.window import Window


class Construction:
  """
  Construction class
  """
  def __init__(self, construction_id, construction_type, name, layers, window_ratio=None, window=None):
    self._id = construction_id
    self._type = construction_type
    self._name = name
    self._layers = layers
    self._window_ratio = window_ratio
    self._window = window

  @property
  def id(self):
    """
    Get construction id
    :return: str
    """
    return self._id

  @property
  def type(self):
    """
    Get construction type
    :return: str
    """
    return self._type

  @property
  def name(self):
    """
    Get construction name
    :return: str
    """
    return self._name

  @property
  def layers(self) -> [Layer]:
    """
    Get construction layers
    :return: [layer]
    """
    return self._layers

  @property
  def window_ratio(self):
    """
    Get construction window ratio
    :return: dict
    """
    return self._window_ratio

  @property
  def window(self) -> Window:
    """
    Get construction window
    :return: Window
    """
    return self._window

  def to_dictionary(self):
    """Class content to dictionary"""
    _layers = []
    for _layer in self.layers:
      _layers.append(_layer.to_dictionary())
    _window = None
    if self.window is not None:
      _window = self.window.to_dictionary()
    content = {'Construction': {'id': self.id,
                                'name': self.name,
                                'type': self.type,
                                'window ratio': self.window_ratio,
                                'window': _window,
                                'layers': _layers
                                }
               }
    return content
