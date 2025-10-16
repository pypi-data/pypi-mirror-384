"""
export a city into Stl format
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

from hub.exports.formats.triangular import Triangular


class Stl(Triangular):
  """
  Export to STL
  """
  def __init__(self, city, path):
    super().__init__(city, path, 'stl', write_mode='wb')
