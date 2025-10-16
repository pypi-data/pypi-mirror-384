"""
Cerc Idf exports one city or some buildings to idf format
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Guille Guillermo.GutierrezMorote@concordia.ca
Code contributors: Oriol Gavalda Torrellas oriol.gavalda@concordia.ca
"""

import hub.helpers.constants as cte

BUILDING_SURFACE = '\nBUILDINGSURFACE:DETAILED,\n'
WINDOW_SURFACE = '\nFENESTRATIONSURFACE:DETAILED,\n'
COMPACT_SCHEDULE = '\nSCHEDULE:COMPACT,\n'
FILE_SCHEDULE = '\nSCHEDULE:FILE,\n'
NOMASS_MATERIAL = '\nMATERIAL:NOMASS,\n'
SOLID_MATERIAL = '\nMATERIAL,\n'
WINDOW_MATERIAL = '\nWINDOWMATERIAL:SIMPLEGLAZINGSYSTEM,\n'
CONSTRUCTION = '\nCONSTRUCTION,\n'
ZONE = '\nZONE,\n'
GLOBAL_GEOMETRY_RULES = '\nGlobalGeometryRules,\n'
PEOPLE = '\nPEOPLE,\n'
LIGHTS = '\nLIGHTS,\n'
APPLIANCES = '\nOTHEREQUIPMENT,\n'
OUTPUT_CONTROL = '\nOutputControl:IlluminanceMap:Style,\n'
INFILTRATION = '\nZONEINFILTRATION:DESIGNFLOWRATE,\n'
VENTILATION = '\nZONEVENTILATION:DESIGNFLOWRATE,\n'
THERMOSTAT = '\nHVACTEMPLATE:THERMOSTAT,\n'
IDEAL_LOAD_SYSTEM = '\nHVACTEMPLATE:ZONE:IDEALLOADSAIRSYSTEM,\n'
DHW = '\nWATERUSE:EQUIPMENT,\n'
SHADING = '\nSHADING:BUILDING:DETAILED,\n'
CONTROL_FILES = '\nOutputControl:Files,\n'
METER = '\nOutput:Meter,\n'
VARIABLE = '\nOUTPUT:VARIABLE,\n'

AUTOCALCULATE = 'autocalculate'
ROUGHNESS = 'MediumRough'
OUTDOORS = 'Outdoors'
GROUND = 'Ground'
SURFACE = 'Surface'
SUN_EXPOSED = 'SunExposed'
WIND_EXPOSED = 'WindExposed'
NON_SUN_EXPOSED = 'NoSun'
NON_WIND_EXPOSED = 'NoWind'
EMPTY = ''

idf_surfaces_dictionary = {
  cte.WALL: 'wall',
  cte.GROUND: 'floor',
  cte.ROOF: 'roof'
}

idf_type_limits = {
  cte.ON_OFF: 'on/off',
  cte.FRACTION: 'Fraction',
  cte.ANY_NUMBER: 'Any Number',
  cte.CONTINUOUS: 'Continuous',
  cte.DISCRETE: 'Discrete'
}

idf_day_types = {
  cte.MONDAY: 'Monday',
  cte.TUESDAY: 'Tuesday',
  cte.WEDNESDAY: 'Wednesday',
  cte.THURSDAY: 'Thursday',
  cte.FRIDAY: 'Friday',
  cte.SATURDAY: 'Saturday',
  cte.SUNDAY: 'Sunday',
  cte.HOLIDAY: 'Holidays',
  cte.WINTER_DESIGN_DAY: 'WinterDesignDay',
  cte.SUMMER_DESIGN_DAY: 'SummerDesignDay'
}