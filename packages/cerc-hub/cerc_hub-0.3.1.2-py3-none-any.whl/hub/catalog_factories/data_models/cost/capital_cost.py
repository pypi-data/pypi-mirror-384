"""
Capital costs included in the catalog
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2023 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

from typing import List
from hub.catalog_factories.data_models.cost.chapter import Chapter


class CapitalCost:
  """
  Capital cost class
  """
  def __init__(self, general_chapters, design_allowance, overhead_and_profit):
    self._general_chapters = general_chapters
    self._design_allowance = design_allowance
    self._overhead_and_profit = overhead_and_profit

  @property
  def general_chapters(self) -> List[Chapter]:
    """
    Get general chapters in capital costs
    :return: [Chapter]
    """
    return self._general_chapters

  @property
  def design_allowance(self):
    """
    Get design allowance in percentage (-)
    :return: float
    """
    return self._design_allowance

  @property
  def overhead_and_profit(self):
    """
    Get overhead profit in percentage (-)
    :return: float
    """
    return self._overhead_and_profit

  def chapter(self, name) -> Chapter:
    """
    Get specific chapter by name
    :return: Chapter
    """
    for chapter in self.general_chapters:
      if chapter.chapter_type == name:
        return chapter
    raise KeyError(f'Chapter name {name} not found')

  def to_dictionary(self):
    """Class content to dictionary"""
    _chapters = []
    for _chapter in self.general_chapters:
      _chapters.append(_chapter.to_dictionary())
    content = {'Capital cost': {'design allowance': self.design_allowance,
                                'overhead and profit': self.overhead_and_profit,
                                'chapters': _chapters
                                }
               }

    return content
