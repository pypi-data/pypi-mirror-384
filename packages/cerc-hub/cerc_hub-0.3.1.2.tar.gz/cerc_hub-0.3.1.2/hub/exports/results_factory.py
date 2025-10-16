"""
ExportsFactory export a city and the buildings of a city
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2019 - 2025 Concordia CERC group
Code Contributor: Koa Wells kekoa.wells@concordia.ca
Project Coder Connor Brackley connor.brackley@concordia.ca
"""

from pathlib import Path

from hub.city_model_structure.city import City
from hub.exports.results.csv import Csv
from hub.exports.results.geojson import Geojson
from hub.helpers.utils import validate_import_export_type


class ResultsExportFactory:
  """
  Exports factory class for results and hub building data
  """

  def __init__(self, city: City, handler: str, path: Path | str, filename: str | None = None):
    """
    :param city: the city object to export
    :param handler: the handler object determine output file format
    :param path: the path to export results
    :param filename: The base name of the output file, uses city name if None
    """

    self._city = city
    self._handler = '_' + handler.lower()
    validate_import_export_type(ResultsExportFactory, handler)
    if isinstance(path, str):
      path = Path(path)
    self._path = path
    self._filename = filename

  def _csv(self):
    """
    Export city results to csv file
    :return: none
    """
    return Csv(self._city, self._path, self._filename)

  def _geojson(self):
    """
    Export city results to a geojson file
    :return: none
    """
    return Geojson(self._city, self._path, self._filename)

  def _parquet(self):
    """
    Export city results to a parquet file
    :return: none
    """
    # todo: add parquet handler
    raise NotImplementedError()

  def export(self):
    """
    Export the city given to the class using the given export type handler
    :return: None
    """
    _handlers = {
      '_csv': self._csv,
      '_geojson': self._geojson,
      '_parquet': self._parquet
    }
    return _handlers[self._handler]()
