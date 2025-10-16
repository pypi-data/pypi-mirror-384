"""
ExportsFactory export a city into several formats
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Gutierrez guillermo.gutierrezmorote@concordia.ca
"""

import uuid
import datetime
from pathlib import Path
import xmltodict
import hub.helpers.constants as cte


class EnergyAde:
  """
  Export the city to citygml + energy ade
  """
  def __init__(self, city, path):
    self._city = city
    self._path = path
    self._surface_members = None

  def export(self):
    energy_ade = {
      'core:CityModel': {
        '@xmlns:brid': 'http://www.opengis.net/citygml/bridge/2.0',
        '@xmlns:tran': 'http://www.opengis.net/citygml/transportation/2.0',
        '@xmlns:frn': 'http://www.opengis.net/citygml/cityfurniture/2.0',
        '@xmlns:wtr': 'http://www.opengis.net/citygml/waterbody/2.0',
        '@xmlns:sch': 'http://www.ascc.net/xml/schematron',
        '@xmlns:veg': 'http://www.opengis.net/citygml/vegetation/2.0',
        '@xmlns:xlink': 'http://www.w3.org/1999/xlink',
        '@xmlns:tun': 'http://www.opengis.net/citygml/tunnel/2.0',
        '@xmlns:tex': 'http://www.opengis.net/citygml/texturedsurface/2.0',
        '@xmlns:gml': 'http://www.opengis.net/gml',
        '@xmlns:genobj': 'http://www.opengis.net/citygml/generics/2.0',
        '@xmlns:dem': 'http://www.opengis.net/citygml/relief/2.0',
        '@xmlns:app': 'http://www.opengis.net/citygml/appearance/2.0',
        '@xmlns:luse': 'http://www.opengis.net/citygml/landuse/2.0',
        '@xmlns:xAL': 'urn:oasis:names:tc:ciq:xsdschema:xAL:2.0',
        '@xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        '@xmlns:smil20lang': 'http://www.w3.org/2001/SMIL20/Language',
        '@xmlns:pbase': 'http://www.opengis.net/citygml/profiles/base/2.0',
        '@xmlns:smil20': 'http://www.w3.org/2001/SMIL20/',
        '@xmlns:bldg': 'http://www.opengis.net/citygml/building/2.0',
        '@xmlns:energy': "http://www.sig3d.org/citygml/2.0/energy/1.0",
        '@xmlns:core': 'http://www.opengis.net/citygml/2.0',
        '@xmlns:grp': 'http://www.opengis.net/citygml/cityobjectgroup/2.0',
        'gml:boundedBy': {
          'gml:Envelope': {
            '@srsName': self._city.srs_name,
            '@srsDimension': 3,
            'gml:lowerCorner': ' '.join([str(e) for e in self._city.lower_corner]),
            'gml:upperCorner': ' '.join([str(e) for e in self._city.upper_corner])
          }
        }
      }
    }
    buildings = []
    for building in self._city.buildings:
      building_dic = {
        'bldg:Building': {
          '@gml:id': building.name,
          'gml:description': f'Building {building.name} at {self._city.name}',
          'gml:name': f'{building.name}',
          'core:creationDate': datetime.datetime.now().strftime('%Y-%m-%d')
        }
      }
      building_dic = EnergyAde._measures(building, building_dic)
      building_dic = self._building_geometry(building, building_dic, self._city)
      building_dic['bldg:Building']['energy:volume'] = {
        'energy:VolumeType': {
          'energy:type': 'grossVolume',
          'energy:value': {
            '@uom': 'm3',
            '#text': f'{building.volume}'
          }
        }
      }
      building_dic['bldg:Building']['energy:referencePoint'] = {
        'gml:Point': {
          '@srsName': self._city.srs_name,
          '@gml:id': f'GML_{uuid.uuid4()}',
          'gml:Pos': f'{" ".join(map(str, building.centroid))}'
        }
      }
      building_dic['bldg:Building']['energy:thermalZone'] = self._thermal_zones(building, self._city)
      buildings.append(building_dic)

    energy_ade['core:CityModel']['core:cityObjectMember'] = buildings

    file_name = self._city.name + '_ade.gml'
    file_path = Path(self._path / file_name).resolve()
    with open(file_path, 'w', encoding='utf8') as file:
      file.write(xmltodict.unparse(energy_ade, pretty=True, short_empty_elements=True))

  @staticmethod
  def _measures(building, building_dic):
    # todo: this method is only for year and insel need to be generalized
    measures = []
    measure = EnergyAde._measure(building.heating_demand, cte.YEAR, 'Energy demand heating')
    if measure is not None:
      measures.append(measure)
    measure = EnergyAde._measure(building.cooling_demand, cte.YEAR, 'Energy demand cooling')
    if measure is not None:
      measures.append(measure)
    if len(measures) != 0:
      building_dic['bldg:Building']['genobj:measureAttribute'] = measures

    demands = []
    for key in building.heating_demand:
      if key != cte.YEAR:
        demand = EnergyAde._demand(building.heating_demand, key, 'Heating energy', 'INSEL')
        demands.append(demand)

    for key in building.cooling_demand:
      if key != cte.YEAR:
        demand = EnergyAde._demand(building.cooling_demand, key, 'Cooling energy', 'INSEL')
        demands.append(demand)
    if len(demands) != 0:
      building_dic['bldg:Building']['energy:demands'] = demands

    return building_dic

  @staticmethod
  def _measure(measure_dict, key_value, name):
    measure = None
    if key_value in measure_dict:
      measure = {
        '@name': name,
        'genobj:value': {
          '@uom': 'kWh',
          '#text': ' '.join([str(e / 1000) for e in measure_dict[key_value]])
        }
      }
    return measure

  @staticmethod
  def _demand(measure_dict, key_value, description, source):
    demand = {
      'energy:EnergyDemand': {
        '@gml:id': f'GML_{uuid.uuid4()}',
        'energy:energyAmount': {
          'energy:RegularTimeSeries': {
            'energy:variableProperties': {
              'energy:TimeValuesProperties': {
                'energy:acquisitionMethod': 'simulation',
                'energy:source': source,
                'energy:thematicDescription': description,
              },
              'energy:timeInterval': {
                '@unit': key_value,
                '#text': '1',
              },
              'energy:values': {
                '@uom': 'kWh',
                '#text': ' '.join([str(float(e) / 1000) for e in measure_dict[key_value]])
              }
            }
          }
        },
        'energy:endUse': 'spaceHeating'
      }
    }
    return demand

  def _building_geometry(self, building, building_dic, city):

    building_dic['bldg:Building']['bldg:function'] = building.function
    building_dic['bldg:Building']['bldg:usage'] = building.usages
    building_dic['bldg:Building']['bldg:yearOfConstruction'] = building.year_of_construction
    building_dic['bldg:Building']['bldg:roofType'] = building.roof_type
    building_dic['bldg:Building']['bldg:measuredHeight'] = {
      '@uom': 'm',
      '#text': f'{building.max_height}'
    }
    building_dic['bldg:Building']['bldg:storeysAboveGround'] = building.storeys_above_ground

    if city.level_of_detail.geometry == 1:
      building_dic = self._lod1(building, building_dic, city)
    elif city.level_of_detail.geometry == 2:
      building_dic = self._lod2(building, building_dic, city)
    else:
      raise NotImplementedError('Only lod 1 and 2 can be exported')
    return building_dic

  def _lod1(self, building, building_dic, city):
    self._surface_members = []
    boundaries = [{
      'gml:Envelope': {
        '@srsName': city.srs_name,
        '@srsDimension': 3,
        'gml:lowerCorner': ' '.join([str(e) for e in city.lower_corner]),
        'gml:upperCorner': ' '.join([str(e) for e in city.upper_corner])
      }}]
    for surface in building.surfaces:
      surface_member = {'@xlink:href': f'#PolyId{surface.name}'}
      self._surface_members.append(surface_member)
      if surface.type == 'Wall':
        surface_type = 'bldg:WallSurface'
      elif surface.type == 'Ground':
        surface_type = 'bldg:GroundSurface'
      else:
        surface_type = 'bldg:RoofSurface'
      surface_dic = {
        surface_type: {
          '@gml:id': f'GML_{uuid.uuid4()}',
          'gml:name': f'{surface.name} ({surface.type})',
          'gml:boundedBy': {
            'gml:Envelope': {
              '@srsName': city.srs_name,
              'gml:lowerCorner': f'{surface.lower_corner[0]} {surface.lower_corner[1]}'
                                 f' {surface.lower_corner[2]}',
              'gml:upperCorner': f'{surface.upper_corner[0]} {surface.upper_corner[1]}'
                                 f' {surface.upper_corner[2]}'
            }
          },
          'bldg:lod1MultiSurface': {
            'gml:MultiSurface': {
              '@srsName': city.srs_name,
              '@gml:id': f'GML_{uuid.uuid4()}',
              'surfaceMember': {
                'gml:Polygon': {
                  '@srsName': city.srs_name,
                  '@gml:id': f'PolyId{surface.name}',
                  'gml:exterior': {
                    'gml:LinearRing': {
                      '@gml:id': f'PolyId{surface.name}_0',
                      'gml:posList': {
                        '@srsDimension': '3',
                        '@count': len(surface.solid_polygon.coordinates) + 1,
                        '#text': f'{" ".join(map(str, surface.solid_polygon.points_list))} '
                                 f'{" ".join(map(str, surface.solid_polygon.coordinates[0]))}'
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
      boundaries.append(surface_dic)
    building_dic['bldg:Building']['bldg:lod1Solid'] = {
      'gml:Solid': {
        '@gml:id': f'GML_{uuid.uuid4()}',
        'gml:exterior': {
          'gml:CompositeSurface': {
            '@srsName': city.srs_name,
            '@gml:id': f'GML_{uuid.uuid4()}',
            'gml:surfaceMember': self._surface_members
          }
        }
      }
    }

    building_dic['bldg:Building']['gml:boundedBy'] = boundaries
    return building_dic

  def _lod2(self, building, building_dic, city):
    self._surface_members = []
    boundaries = [{
      'gml:Envelope': {
        '@srsName': city.srs_name,
        '@srsDimension': 3,
        'gml:lowerCorner': ' '.join([str(e) for e in city.lower_corner]),
        'gml:upperCorner': ' '.join([str(e) for e in city.upper_corner])
      }}]
    for surface in building.surfaces:
      surface_member = {'@xlink:href': f'#PolyId{surface.name}'}
      self._surface_members.append(surface_member)
      if surface.type == 'Wall':
        surface_type = 'bldg:WallSurface'
      elif surface.type == 'Ground':
        surface_type = 'bldg:GroundSurface'
      else:
        surface_type = 'bldg:RoofSurface'
      surface_dic = {
        surface_type: {
          '@gml:id': f'GML_{uuid.uuid4()}',
          'gml:name': f'{surface.name} ({surface.type})',
          'gml:boundedBy': {
            'gml:Envelope': {
              '@srsName': city.srs_name,
              'gml:lowerCorner': f'{surface.lower_corner[0]} {surface.lower_corner[1]}'
                                 f' {surface.lower_corner[2]}',
              'gml:upperCorner': f'{surface.upper_corner[0]} {surface.upper_corner[1]}'
                                 f' {surface.upper_corner[2]}'
            }
          },
          'bldg:lod2MultiSurface': {
            'gml:MultiSurface': {
              '@srsName': city.srs_name,
              '@gml:id': f'GML_{uuid.uuid4()}',
              'surfaceMember': {
                'gml:Polygon': {
                  '@srsName': city.srs_name,
                  '@gml:id': f'PolyId{surface.name}',
                  'gml:exterior': {
                    'gml:LinearRing': {
                      '@gml:id': f'PolyId{surface.name}_0',
                      'gml:posList': {
                        '@srsDimension': '3',
                        '@count': len(surface.solid_polygon.coordinates) + 1,
                        '#text': f'{" ".join(map(str, surface.solid_polygon.points_list))} '
                                 f'{" ".join(map(str, surface.solid_polygon.coordinates[0]))}'
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
      boundaries.append(surface_dic)
    building_dic['bldg:Building']['bldg:lod2Solid'] = {
      'gml:Solid': {
        '@gml:id': f'GML_{uuid.uuid4()}',
        'gml:exterior': {
          'gml:CompositeSurface': {
            '@srsName': city.srs_name,
            '@gml:id': f'GML_{uuid.uuid4()}',
            'gml:surfaceMember': self._surface_members
          }
        }
      }
    }

    building_dic['bldg:Building']['gml:boundedBy'] = boundaries
    return building_dic

  def _thermal_zones(self, building, city):
    thermal_zones = []
    for internal_zone in building.internal_zones:
      for index, thermal_zone in enumerate(internal_zone.thermal_zones_from_internal_zones):
        usages = []
        for usage in internal_zone.usages:
          usages.append({'@xlink:href': f'#GML_{usage.id}'})
        thermal_zone_dic = {
          'energy:ThermalZone': {
            '@gml:id': f'GML_{thermal_zone.id}',
            'gml:name': f'Thermal zone {index} in {building.name} building',
            'energy:contains': [],
            'energy:floorArea': {
              'energy:FloorArea': {
                'energy:type': 'grossFloorArea',
                'energy:value': {
                  '@uom': 'm2',
                  '#text': f'{thermal_zone.footprint_area}'
                }
              }
            },
            'energy:volume': {
              'energy:VolumeType': {
                'energy:type': 'grossVolume',
                'energy:value': {
                  '@uom': 'm3',
                  '#text': f'{thermal_zone.volume}'
                }
              }
            },
            'energy:isCooled': f'{building.is_conditioned}'.lower(),
            'energy:isHeated': f'{building.is_conditioned}'.lower(),
            'energy:volumeGeometry': {
              'gml:Solid': {
                '@gml:id': f'GML_{uuid.uuid4()}',
                'gml:exterior': {
                  'gml:CompositeSurface': {
                    '@srsName': f'{city.srs_name}',
                    '@gml:id': f'GML_{uuid.uuid4()}',
                    'gml:surfaceMember': self._surface_members
                  }
                }
              }
            },
            'energy:boundedBy': self._thermal_boundaries(city, thermal_zone)
          }
        }
        thermal_zone_dic['energy:ThermalZone']['energy:contains'] = usages
        thermal_zones.append(thermal_zone_dic)
    return thermal_zones

  @staticmethod
  def _thermal_boundaries(city, thermal_zone):
    thermal_boundaries = []
    for thermal_boundary in thermal_zone.thermal_boundaries:
      thermal_boundary_dic = {
        '@gml:id': f'GML_{uuid.uuid4()}',
        'gml:name': f'{thermal_boundary.construction_name}',
        'energy:thermalBoundaryType': thermal_boundary.type,
        'energy:azimuth': {
          '@uom': 'rad',
          '#text': f'{thermal_boundary.parent_surface.azimuth}'
        },
        'energy:inclination': {
          '@uom': 'rad',
          '#text': f'{thermal_boundary.parent_surface.inclination}'
        },
        'energy:area': {
          '@uom': 'm2',
          '#text': f'{thermal_boundary.opaque_area}'
        },
        'energy:surfaceGeometry': {
          'gml:MultiSurface': {
            '@srsName': city.srs_name,
            '@gml:id': f'GML_{uuid.uuid4()}',
            'gml:surfaceMember': {
              'gml:Polygon': {
                '@srsName': city.srs_name,
                '@gml:id': f'GML_{uuid.uuid4()}',
                'gml:exterior': {
                  'gml:LinearRing': {
                    '@gml:id': f'GML_{uuid.uuid4()}',
                    'gml:posList': {
                      '@srsDimension': '3',
                      '@count': len(thermal_boundary.parent_surface.solid_polygon.coordinates) + 1,
                      '#text': f'{" ".join(map(str, thermal_boundary.parent_surface.solid_polygon.points_list))} '
                               f'{" ".join(map(str, thermal_boundary.parent_surface.solid_polygon.coordinates[0]))}'
                    }
                  }
                }
              }
            }
          }
        }
      }
      construction = []
      opening_construction = []
      if thermal_boundary.layers is not None:
        construction.append(uuid.uuid4())
        thermal_boundary_dic['energy:construction'] = {
          '@xlink:href': f'#GML_{construction[0]}'
        }
      if thermal_boundary.thermal_openings is not None:
        for _ in thermal_boundary.thermal_openings:
          opening_construction.append(uuid.uuid4())
          thermal_boundary_dic['energy:contains'] = {
            'energy:ThermalOpening': {
              '@gml:id': f'GML_{uuid.uuid4()}',
              'energy:construction': f'#GML_{opening_construction}',
              'energy:surfaceGeometry': {

              }
            }
          }
      thermal_boundaries.append(thermal_boundary_dic)
    return thermal_boundaries
