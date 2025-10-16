"""
Location module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
Code contributors: Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""


class Location:
  """
  Location
  """
  def __init__(self, country, city, region_code, climate_reference_city_latitude, climate_reference_city_longitude):
    self._country = country
    self._city = city
    self._region_code = region_code
    self._climate_reference_city_latitude = climate_reference_city_latitude
    self._climate_reference_city_longitude = climate_reference_city_longitude

  @property
  def city(self):
    """
    Get city name
    """
    return self._city

  @property
  def country(self):
    """
    Get country code
    """
    return self._country

  @property
  def region_code(self):
    """
    Get region
    """
    return self._region_code

  @property
  def climate_reference_city_latitude(self):
    """
    Get climate-reference-city latitude
    """
    return self._climate_reference_city_latitude

  @property
  def climate_reference_city_longitude(self):
    """
    Get climate-reference-city longitude
    """
    return self._climate_reference_city_longitude
