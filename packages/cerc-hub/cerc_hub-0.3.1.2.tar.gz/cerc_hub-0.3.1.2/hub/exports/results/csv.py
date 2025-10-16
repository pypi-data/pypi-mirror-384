"""
Saves a city and buildings to a csv file
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2019 - 2025 Concordia CERC group
Project Coder Koa Wells kekoa.wells@concordia.ca
Project Coder Connor Brackley connor.brackley@concordia.ca
"""
import csv
from pathlib import Path

from hub.city_model_structure.city import City
from hub.exports.results.results_handler import ResultsHandler


class Csv:
  """
  Export to a csv file
  """

  def __init__(self, city: City, path: Path, filename: str | None):
    """
    :param city: the city object to export
    :param path: the path to export results
    :param filename: The base name of the output file, uses city name if None
    """
    self._city = city
    self._path = path
    self._filename = filename if filename else self._city.name
    self._output_file = Path(f'{self._path}/{self._filename}.csv').resolve()

    self._export()

  def _export(self):
    """
    Export the city to a csv file
    :return: None
    """
    field_names, results = ResultsHandler().collect_results(self._city.buildings)
    with open(self._output_file, 'w', newline='') as f:
      writer = csv.DictWriter(f, fieldnames=field_names, restval='')
      writer.writeheader()
      writer.writerows(results)
