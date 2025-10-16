"""
Saves a city and buildings to a geojson file
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2019 - 2025 Concordia CERC group
Project Coder Koa Wells kekoa.wells@concordia.ca
Project Coder Connor Brackley connor.brackley@concordia.ca
"""
import json
from pathlib import Path

from hub.city_model_structure.city import City
from hub.exports.results.results_handler import ResultsHandler
from hub.exports.formats.geojson import Geojson as GeojsonFormat


class Geojson:
  """
  Export to a geojson file
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
    self._output_file = Path(f'{self._path}/{self._filename}.geojson').resolve()

    self._export()

  def _export(self):
    """
    Export the city to a geojson file
    :return: None
    """
    geojson_exporter = GeojsonFormat(self._city, self._path, self._city.buildings, self._filename)
    geojson = geojson_exporter.geojson_skeleton
    buildings = geojson['features']

    _, results = ResultsHandler().collect_results(self._city.buildings)

    for building_result in results:
      # loop through all building results
      building_name = building_result['name']
      # loop through initial buildings in the geojson skeleton from the GeojsonFormat object
      for building in buildings:
        if building_name == building['id']:
          # loop through each field in the results; add the result if the field name doesn't already exist
          for field_name in building_result:
            if field_name not in building['properties']:
              building['properties'][field_name] = building_result[field_name]
    geojson_exporter.export()
