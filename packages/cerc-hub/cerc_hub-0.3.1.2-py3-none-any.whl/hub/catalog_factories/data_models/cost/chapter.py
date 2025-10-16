"""
Cost chapter description
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from typing import List
from hub.catalog_factories.data_models.cost.item_description import ItemDescription


class Chapter:
  """
  Chapter class
  """
  def __init__(self, chapter_type, items):

    self._chapter_type = chapter_type
    self._items = items

  @property
  def chapter_type(self):
    """
    Get chapter type
    :return: str
    """
    return self._chapter_type

  @property
  def items(self) -> List[ItemDescription]:
    """
    Get list of items contained in the chapter
    :return: [str]
    """
    return self._items

  def item(self, name) -> ItemDescription:
    """
    Get specific item by name
    :return: ItemDescription
    """
    for item in self.items:
      if item.type == name:
        return item
    raise KeyError(f'Item name {name} not found')

  def to_dictionary(self):
    """Class content to dictionary"""
    _items = []
    for _item in self.items:
      _items.append(_item.to_dictionary())
    content = {'Chapter': {'chapter type': self.chapter_type,
                           'items': _items
                           }
               }

    return content
