"""
Constant module
SPDX - License - Identifier: LGPL - 3.0 - or -later
Copyright © 2022 Concordia CERC group
Project Coder Pilar Monsalvete Alvarez de Uribarri pilar.monsalvete@concordia.ca
"""

# universal constants

KELVIN = 273.15
WATER_DENSITY = 1000  # kg/m3
WATER_HEAT_CAPACITY = 4182  # J/kgK
WATER_THERMAL_CONDUCTIVITY = 0.65  # W/mK
NATURAL_GAS_LHV = 36.6e6  # J/m3
AIR_DENSITY = 1.293  # kg/m3
AIR_HEAT_CAPACITY = 1005.2  # J/kgK

# converters
HOUR_TO_MINUTES = 60
MINUTES_TO_SECONDS = 60
HOUR_TO_SECONDS = 3600
METERS_TO_FEET = 3.28084
BTU_H_TO_WATTS = 0.29307107
KILO_WATTS_HOUR_TO_JULES = 3600000
WATTS_HOUR_TO_JULES = 3600
GALLONS_TO_QUBIC_METERS = 0.0037854117954011185
INFILTRATION_75PA_TO_4PA = (4 / 75) ** 0.65

# time
SECOND = 'second'
MINUTE = 'minute'
HOUR = 'hour'
DAY = 'day'
WEEK = 'week'
MONTH = 'month'
YEAR = 'year'

# day types
MONDAY = 'monday'
TUESDAY = 'tuesday'
WEDNESDAY = 'wednesday'
THURSDAY = 'thursday'
FRIDAY = 'friday'
SATURDAY = 'saturday'
SUNDAY = 'sunday'
HOLIDAY = 'holiday'
WINTER_DESIGN_DAY = 'winter_design_day'
SUMMER_DESIGN_DAY = 'summer_design_day'
WEEK_DAYS = 'Weekdays'
WEEK_ENDS = 'Weekends'
ALL_DAYS = 'Alldays'

JANUARY = 'January'
FEBRUARY = 'February'
MARCH = 'March'
APRIL = 'April'
MAY = 'May'
JUNE = 'June'
JULY = 'July'
AUGUST = 'August'
SEPTEMBER = 'September'
OCTOBER = 'October'
NOVEMBER = 'November'
DECEMBER = 'December'

MONTHS = [JANUARY, FEBRUARY, MARCH, APRIL, MAY, JUNE, JULY, AUGUST, SEPTEMBER, OCTOBER, NOVEMBER, DECEMBER]

WEEK_DAYS_A_MONTH = {JANUARY: {MONDAY: 5,
                               TUESDAY: 5,
                               WEDNESDAY: 5,
                               THURSDAY: 4,
                               FRIDAY: 4,
                               SATURDAY: 4,
                               SUNDAY: 4,
                               HOLIDAY: 0},
                     FEBRUARY: {MONDAY: 4,
                                TUESDAY: 4,
                                WEDNESDAY: 4,
                                THURSDAY: 4,
                                FRIDAY: 4,
                                SATURDAY: 4,
                                SUNDAY: 4,
                                HOLIDAY: 0},
                     MARCH: {MONDAY: 4,
                             TUESDAY: 4,
                             WEDNESDAY: 4,
                             THURSDAY: 5,
                             FRIDAY: 5,
                             SATURDAY: 5,
                             SUNDAY: 4,
                             HOLIDAY: 0},
                     APRIL: {MONDAY: 5,
                             TUESDAY: 4,
                             WEDNESDAY: 4,
                             THURSDAY: 4,
                             FRIDAY: 4,
                             SATURDAY: 4,
                             SUNDAY: 5,
                             HOLIDAY: 0},
                     MAY: {MONDAY: 4,
                           TUESDAY: 5,
                           WEDNESDAY: 5,
                           THURSDAY: 5,
                           FRIDAY: 4,
                           SATURDAY: 4,
                           SUNDAY: 4,
                           HOLIDAY: 0},
                     JUNE: {MONDAY: 4,
                            TUESDAY: 4,
                            WEDNESDAY: 4,
                            THURSDAY: 4,
                            FRIDAY: 5,
                            SATURDAY: 5,
                            SUNDAY: 4,
                            HOLIDAY: 0},
                     JULY: {MONDAY: 5,
                            TUESDAY: 5,
                            WEDNESDAY: 4,
                            THURSDAY: 4,
                            FRIDAY: 4,
                            SATURDAY: 4,
                            SUNDAY: 5,
                            HOLIDAY: 0},
                     AUGUST: {MONDAY: 4,
                              TUESDAY: 4,
                              WEDNESDAY: 5,
                              THURSDAY: 5,
                              FRIDAY: 5,
                              SATURDAY: 4,
                              SUNDAY: 4,
                              HOLIDAY: 0},
                     SEPTEMBER: {MONDAY: 4,
                                 TUESDAY: 4,
                                 WEDNESDAY: 4,
                                 THURSDAY: 4,
                                 FRIDAY: 4,
                                 SATURDAY: 5,
                                 SUNDAY: 5,
                                 HOLIDAY: 0},
                     OCTOBER: {MONDAY: 5,
                               TUESDAY: 5,
                               WEDNESDAY: 5,
                               THURSDAY: 4,
                               FRIDAY: 4,
                               SATURDAY: 4,
                               SUNDAY: 4,
                               HOLIDAY: 0},
                     NOVEMBER: {MONDAY: 4,
                                TUESDAY: 4,
                                WEDNESDAY: 4,
                                THURSDAY: 5,
                                FRIDAY: 5,
                                SATURDAY: 4,
                                SUNDAY: 4,
                                HOLIDAY: 0},
                     DECEMBER: {MONDAY: 5,
                                TUESDAY: 4,
                                WEDNESDAY: 4,
                                THURSDAY: 4,
                                FRIDAY: 4,
                                SATURDAY: 5,
                                SUNDAY: 5,
                                HOLIDAY: 0},
                     }

WEEK_DAYS_A_YEAR = {MONDAY: 51,
                    TUESDAY: 50,
                    WEDNESDAY: 50,
                    THURSDAY: 50,
                    FRIDAY: 50,
                    SATURDAY: 52,
                    SUNDAY: 52,
                    HOLIDAY: 10}

DAYS_A_MONTH = {JANUARY: 31,
                FEBRUARY: 28,
                MARCH: 31,
                APRIL: 30,
                MAY: 31,
                JUNE: 30,
                JULY: 31,
                AUGUST: 31,
                SEPTEMBER: 30,
                OCTOBER: 31,
                NOVEMBER: 30,
                DECEMBER: 31}

HOURS_A_MONTH = {JANUARY: 744,
                 FEBRUARY: 672,
                 MARCH: 744,
                 APRIL: 720,
                 MAY: 744,
                 JUNE: 720,
                 JULY: 744,
                 AUGUST: 744,
                 SEPTEMBER: 720,
                 OCTOBER: 744,
                 NOVEMBER: 720,
                 DECEMBER: 744}

PERIODS = [MONTH, YEAR, HOUR]

HOURS_A_YEAR = 8760

# data types
ANY_NUMBER = 'any_number'
FRACTION = 'fraction'
ON_OFF = 'on_off'
TEMPERATURE = 'temperature'
HUMIDITY = 'humidity'
CONTROL_TYPE = 'control_type'
CONTINUOUS = 'continuous'
DISCRETE = 'discrete'
CONSTANT = 'constant'
INTERNAL_GAINS = 'internal_gains'

# surface types
WALL = 'Wall'
GROUND_WALL = 'Ground wall'
GROUND = 'Ground'
ATTIC_FLOOR = 'Attic floor'
ROOF = 'Roof'
INTERIOR_SLAB = 'Interior slab'
INTERIOR_WALL = 'Interior wall'
VIRTUAL_INTERNAL = 'Virtual internal'
WINDOW = 'Window'
DOOR = 'Door'
SKYLIGHT = 'Skylight'

# functions and usages
RESIDENTIAL = 'residential'
SINGLE_FAMILY_HOUSE = 'single family house'
MULTI_FAMILY_HOUSE = 'multifamily house'
ROW_HOUSE = 'row house'
MID_RISE_APARTMENT = 'mid rise apartment'
HIGH_RISE_APARTMENT = 'high rise apartment'
OFFICE_AND_ADMINISTRATION = 'office and administration'
SMALL_OFFICE = 'small office'
MEDIUM_OFFICE = 'medium office'
LARGE_OFFICE = 'large office'
COURTHOUSE = 'courthouse'
FIRE_STATION = 'fire station'
PENITENTIARY = 'penitentiary'
POLICE_STATION = 'police station'
POST_OFFICE = 'post office'
LIBRARY = 'library'
EDUCATION = 'education'
PRIMARY_SCHOOL = 'primary school'
PRIMARY_SCHOOL_WITH_SHOWER = 'school with shower'
SECONDARY_SCHOOL = 'secondary school'
UNIVERSITY = 'university'
LABORATORY_AND_RESEARCH_CENTER = 'laboratory and research centers'
STAND_ALONE_RETAIL = 'stand alone retail'
HOSPITAL = 'hospital'
OUT_PATIENT_HEALTH_CARE = 'out-patient health care'
HEALTH_CARE = 'health care'
RETIREMENT_HOME_OR_ORPHANAGE = 'retirement home or orphanage'
COMMERCIAL = 'commercial'
STRIP_MALL = 'strip mall'
SUPERMARKET = 'supermarket'
RETAIL_SHOP_WITHOUT_REFRIGERATED_FOOD = 'retail shop without refrigerated food'
RETAIL_SHOP_WITH_REFRIGERATED_FOOD = 'retail shop with refrigerated food'
RESTAURANT = 'restaurant'
QUICK_SERVICE_RESTAURANT = 'quick service restaurant'
FULL_SERVICE_RESTAURANT = 'full service restaurant'
HOTEL = 'hotel'
HOTEL_MEDIUM_CLASS = 'hotel medium class'
SMALL_HOTEL = 'small hotel'
LARGE_HOTEL = 'large hotel'
DORMITORY = 'dormitory'
EVENT_LOCATION = 'event location'
CONVENTION_CENTER = 'convention center'
HALL = 'hall'
GREEN_HOUSE = 'green house'
INDUSTRY = 'industry'
WORKSHOP = 'workshop'
WAREHOUSE = 'warehouse'
WAREHOUSE_REFRIGERATED = 'warehouse refrigerated'
SPORTS_LOCATION = 'sports location'
SPORTS_ARENA = 'sports arena'
GYMNASIUM = 'gymnasium'
MOTION_PICTURE_THEATRE = 'motion picture theatre'
MUSEUM = 'museum'
PERFORMING_ARTS_THEATRE = 'performing arts theatre'
TRANSPORTATION = 'transportation'
AUTOMOTIVE_FACILITY = 'automotive facility'
PARKING_GARAGE = 'parking garage'
RELIGIOUS = 'religious'
NON_HEATED = 'non-heated'
DATACENTER = 'datacenter'
FARM = 'farm'

LIGHTING = 'Lights'
OCCUPANCY = 'Occupancy'
APPLIANCES = 'Appliances'
HVAC_AVAILABILITY = 'HVAC Avail'
INFILTRATION = 'Infiltration'
VENTILATION = 'Ventilation'
COOLING_SET_POINT = 'ClgSetPt'
HEATING_SET_POINT = 'HtgSetPt'
EQUIPMENT = 'Equipment'
ACTIVITY = 'Activity'
PEOPLE_ACTIVITY_LEVEL = 'People Activity Level'
DOMESTIC_HOT_WATER = 'Domestic Hot Water'
HEATING = 'Heating'
COOLING = 'Cooling'
ELECTRICITY = 'Electricity'
RENEWABLE = 'Renewable'
WOOD = 'Wood'
GAS = 'Gas'
DIESEL = 'Diesel'
COAL = 'Coal'
BIOMASS = 'Biomass'
BUTANE = 'Butane'
AIR = 'Air'
WATER = 'Water'
GEOTHERMAL = 'Geothermal'
DISTRICT_HEATING_NETWORK = 'District Heating'
GRID = 'Grid'
ONSITE_ELECTRICITY = 'Onsite Electricity'
PHOTOVOLTAIC = 'Photovoltaic'
BOILER = 'Boiler'
FURNACE = 'Furnace'
HEAT_PUMP = 'Heat Pump'
BASEBOARD = 'Baseboard'
ELECTRICITY_GENERATOR = 'Electricity generator'
CHILLER = 'Chiller'
SPLIT = 'Split'
JOULE = 'Joule'
BUTANE_HEATER = 'Butane Heater'
SENSIBLE = 'sensible'
LATENT = 'Latent'
LITHIUMION = 'Lithium Ion'
NICD = 'NiCd'
LEADACID = 'Lead Acid'

# Geometry
EPSILON = 0.0000001

# HVAC types
ONLY_HEATING = 'Heating'
ONLY_COOLING = 'Colling'
ONLY_VENTILATION = 'Ventilation'
HEATING_AND_VENTILATION = 'Heating and ventilation'
COOLING_AND_VENTILATION = 'Cooling and ventilation'
HEATING_AND_COLLING = 'Heating and cooling'
FULL_HVAC = 'Heating and cooling and ventilation'

# Floats
MAX_FLOAT = float('inf')
MIN_FLOAT = float('-inf')

# Tools
SRA = 'sra'
INSEL_MEB = 'insel meb'

# Costs units
CURRENCY_PER_SQM = 'currency/m2'
CURRENCY_PER_CBM = 'currency/m3'
CURRENCY_PER_KW = 'currency/kW'
CURRENCY_PER_KWH = 'currency/kWh'
CURRENCY_PER_MONTH = 'currency/month'
CURRENCY_PER_LITRE = 'currency/l'
CURRENCY_PER_KG = 'currency/kg'
CURRENCY_PER_CBM_PER_HOUR = 'currency/(m3/h)'
PERCENTAGE = '%'

# Costs chapters
SUPERSTRUCTURE = 'B_shell'
ENVELOPE = 'D_services'
ALLOWANCES_OVERHEAD_PROFIT = 'Z_allowances_overhead_profit'

# Co2 emission types
ENVELOPE_CO2 = 'envelope_co2'
OPENING_CO2 = 'opening_co2'
