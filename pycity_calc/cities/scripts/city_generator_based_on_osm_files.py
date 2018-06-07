# coding=utf-8

"""
City generator, based on osm call, by Jana Rudnick

This generator provides an automatical identification of the building types and followed data enrichment of the OSM-data.


Results can be saved in a pickle and CSV files and can be converted into the TEASER-TypeBuildings with the PyCity_Calc "teaser_use.py" (/Users/PyCity_Calc/pycity_calc/toolbox/teaser_usage/teaser_use.py).


The generator is devided into

- "main"-function                                   input of OSM-file  and chance to influnce the results by the user-defined options

- functions: pickle_dumper & pickle_load            enable to save large files to the pickle format

- functions: get_list to get_residential layout     to get and use the information from the OSM-data for the further identification and data enrichment

- functions: get district_type to get_nb_of_occupants_user_defined
                                                    needed for the most important function "def data_enrichment"


- function data_enrichment                          most important function of the generator.
                                                    1. Identification of the building type (Single Family House, Multi Family House, Non residential building)
                                                    2. Identification of the city district (residential, non residential and city)
                                                    3. Deletion of the non relevant buildings
                                                    4. Data enrichment of the buildings with
                                                        - build type
                                                        - build year
                                                        - mod year
                                                        - netto floor area
                                                        - retrofit state
                                                        - nb of apartments
                                                        - nb of occupants
                                                        - nb of floors
                                                        - height of floors
                                                        - useable roof area for PV systems
                                                        - type of heating in cellars and attic
                                                        - availability of dormers
                                                        - residential layout




"""


import os
import pickle
import math
import pandas as pd
import random
import xml.etree.ElementTree
import copy
import time
from collections import Counter
from copy import deepcopy
import sys

import os.path
import numpy
import utm

import pycity_base.classes.demand.Apartment as Apartment
import pycity_calc.cities.scripts.city_generator.city_generator as citgen
import pycity_base.classes.demand.Occupancy as occup
import pycity_calc.buildings.building as build_ex
import uesgraphs.uesgraph as ues

import pycity_calc.cities.scripts.osm_call as osm

def main():  # pragma: no cover

    """
    BEGINNING OF USER INPUT

    overview:
    1. integration of the OSM-data
    2. setting the minimal ground area
    3. setting the parameters for the environment

    4. setting the building distrbution (optional)
    5. setting the build year (optional)
    6. setting of the modifcation year (optional)
    7. set forced modification after a certain time (optional)
    8. set number of occupants (optional)
    9. set number of apartments (optional)
    10. Get electical, thermal or domestic hot water demand(optional)
    11. set considered squared area around every building
    12. set variance of the buildings with same ground area

    13. Option to save object as pickle-file
    14. Option to save object as CSV-file
    15. Option to plot the district


    To be able to run this test, you need to download the dataset from
    OpenStreetMap:

    - Download file through http://www.overpass-api.de/api/xapi_meta?*[bbox=7.1450,50.6813,7.1614,50.6906]  --> change to the new coordinates
    - Save in your input_osm as .../pycity_calc/cities/scripts/input_osm/name.osm
    """
    #-------------------------------------------------------------

    start_time = time.time()

    # 1. osm filename

    filename = 'test.osm'

    # 2. Minimal required building area in m2
    min_house_area = 50     # --> double garages eliminated ( 34,95 m^2)
    #  All objects with smaller area size are going to be erased

    # ------------------------------------------------------
    # 3. Parameters for the ENVIRONMENT

    # #timestep : int
    # Timestep in seconds
    timestep = 3600

    # year : int, optional
    #     Chosen year of analysis (default: 2010)
    #     (influences initial day for profile generation, market prices
    #     and co2 factors)
    #     If year is set to None, user has to define day_init!
    year = 2010

    # try_path : str, optional
    #     Path to TRY weather file (default: None)
    #     If set to None, uses default weather TRY file (2010, region 5)
    try_path = None

    new_try = False
    #  new_try has to be set to True, if you want to use TRY data of 2017
    #  or newer! Else: new_try = False

    # location : Tuple, optional
    #     (latitude , longitude) of the simulated system's position,
    #     (default: (50.775346, 6.083887) for Aachen, Germany.
    location = (50.775346, 6.083887)

    # altitude : float, optional
    #     Altitute of location in m (default: 55 - City of Bottrop)
    altitude = 55

    # ------------------------------------------------------

    # 4. User defined BUILDING DISTRIBUTION of the city file

    # percentage of building distribution (Single Family House, Multi Family House, Non-residential, specific building (e.g. schools, universities))
    # Sum of percentages has to be 100
    user_defined_building_distribution = False
    percentage_sfh = 0
    percentage_mfh = 0
    percentage_non_res = 100
    # if specific buildings = False, all buildings like schools, universities, hospitals, houses of prayer,
    # civic and public buildings are NOT included
    # just working in case user_defined_building_distribution == True and the OSM data offers information regarding specific buildings
    specific_buildings = False


    # 5. specified period of BUILD YEAR
    user_defined_build_year = True
    specified_build_year_beginning = 1970
    specified_build_year_end = 1975

    # ------------------------------------------------------

    # 6. specified MOD YEAR after a certain time
    user_defined_mod_year = False
    mod_year_method = 1                     # Methods are seen below

    # mod year method = 0; in the given range (beginnning - end) a modification has to be done.
    # Modification takes place every 30 (mod_year_beginning) to 36 (mod_year_end) until the difference of the mod_year to the build_year is smaller than build_year - mod_year_beginning
    specified_range_mod_year_beginning = 30
    specified_range_mod_year_end = 36

    # mod year method = 1;
    # states the years of modification after the building was build
    # has to be filled with 11 mod years after the build year
    range_of_mod_years = [30, 36, 50, 60, 72, 90, 100, 108, 120, 144, 150]

    # 7. Forced modification of buildings after a certain time.
    # Retrofit state has to be slightly retrofitted or mainly retrofitted.
    forced_modification = False
    forced_modification_after = 40 # years

    # ------------------------------------------------------

    # 8. specified NUMBER of OCCUPANTS
    user_defined_number_of_occupants = False
    specified_number_occupants = 800

    # 9. specified NUMBER of APARTMENTS
    user_defined_number_of_apartments = False
    specified_number_apartments = 300

    # ------------------------------------------------------

    # 10. Get electical, thermal or domestic hot water demand

    # ELECTRICAL DEMAND
    user_defined_el_demand = True

    # SPACE HEATING DEMAND
    user_defined_therm_demand = True

    # DOMESTIC HOT WATER
    user_defined_dhw = True

    # ------------------------------------------------------

    # 11. considered area to create a square around each building for getting buildings with the same parameters and the district type
    considered_area_around_building = 10000     # 10000 m^2 is a hectar

    # 12. Variance for the comparision of the buildings with the same ground area
    variance_same_ground_area = 5

    # ------------------------------------------------------

    #  13. SAVE generated city object as PICKLE file?
    save_city = True
    city_filename = 'city_osm_ac.p'

    #  14. SAVE generated city object as CSV file?
    save_city_CSV = True
    csv_filename = str("city_generator/input/") + filename[:-4] + str(".txt")

    ## 15. PLOT CITY DISTRICT
    # for plotting code underneath has to be untagged
    #
    # citvis.plot_city_district(city=city, node_size=10, plot_build_labels=False)

    # Used NODELIST
    # if true, generates nodes from CityDistrict-function "get_list_id_of_spec_node_type"
    # if false, generates node from city.nodelist_building

    generate_nodelist_from_function_of_citydistrict = True


    # END USER INPUT
    #---------------------------------------------------------------------
    #---------------------------------------------------------------------

    #  Convert lat/long to utm coordinates in meters?
    #  Only necessary, if no conversion is done within uesgraph itself
    conv_utm = False
    zone_number = 32

    this_path = os.path.dirname(os.path.abspath(__file__))
    osm_path = os.path.join(this_path, 'input_osm', filename)

    # Generate environment
    environment = citgen.generate_environment(timestep=timestep,
                                              year_timer=year,
                                              try_path=try_path,
                                              location=location,
                                              altitude=altitude,
                                              new_try=new_try)

    #  Generate city topology based on osm data
    min_area = 0  # --> Do NOT change! Needed to get all buildings at first and to delete the small buildings later on.  The small buildings are needed for identification of the building types!
    city = osm.gen_osm_city_topology(osm_path=osm_path,
                                     environment=environment,
                                     name=None,
                                     check_boundary=False,
                                     min_area=min_area)

    if user_defined_building_distribution == True:
        print("User-defined city distrubution with", percentage_sfh, " % SFH, ", percentage_mfh, "% MFH and ",
              percentage_non_res, "% non residential buildings.")

    if user_defined_building_distribution == True and (percentage_sfh + percentage_mfh + percentage_non_res) != 100:
        print("Sum of percentages is unequal 100.  Try again...")
        assert (user_defined_building_distribution == True and (
        percentage_sfh + percentage_mfh + percentage_non_res) != 100), "Sum of percentages is unequal 100.  Try again..."

    deleted_buildings, nodelist_buildings = delete_not_relevant_buildings(city=city, min_house_area=min_house_area, generate_nodelist_from_function_of_citydistrict=generate_nodelist_from_function_of_citydistrict)

    if conv_utm:
        # Convert latitude, longitude to utm
        city = osm.conv_city_long_lat_to_utm(city, zone_number=zone_number)
        conv_outlines_of_buildings_long_lat_to_utm(city=city, zone_number=zone_number, min_house_area=min_house_area, nodelist_buildings=nodelist_buildings, generate_nodelist_from_function_of_citydistrict=generate_nodelist_from_function_of_citydistrict)

    if save_city_CSV == False:
        # DEF data_enrichment
        data_enrichment(city=city, osm_path=osm_path, zone_number=zone_number, min_house_area=min_house_area,
                                          considered_area_around_a_building=considered_area_around_building, \
                        user_defined_building_distribution= user_defined_building_distribution, \
                        percentage_sfh=percentage_sfh, percentage_mfh=percentage_mfh, percentage_non_res=percentage_non_res, \
                        specific_buildings=specific_buildings, \
                        user_defined_build_year=user_defined_build_year,
                        specified_build_year_beginning=specified_build_year_beginning, \
                        specified_build_year_end=specified_build_year_end, user_defined_mod_year=user_defined_mod_year,
                        mod_year_method = mod_year_method, range_of_mod_years= range_of_mod_years, specified_range_mod_year_beginning=specified_range_mod_year_beginning, \
                        specified_range_mod_year_end=specified_range_mod_year_end,
                        user_defined_number_of_occupants=user_defined_number_of_occupants, \
                        specified_number_occupants=specified_number_occupants,
                        user_defined_number_of_apartments=user_defined_number_of_apartments, \
                        specified_number_apartments=specified_number_apartments, forced_modification = forced_modification, forced_modification_after=forced_modification_after, timestep=timestep, year=year, try_path=try_path, location=location, altitude=altitude, generate_nodelist_from_function_of_citydistrict=generate_nodelist_from_function_of_citydistrict, save_city_CSV=save_city_CSV, user_defined_el_demand=user_defined_el_demand, user_defined_therm_demand=user_defined_therm_demand, user_defined_dhw=user_defined_dhw)

    # DEF put_building_data_into_csv()
    if save_city_CSV == True:
        put_building_data_into_csv(city=city, csv_filename = csv_filename, osm_path=osm_path, zone_number=zone_number, min_house_area=min_house_area,
                                   considered_area_around_a_building=considered_area_around_building, \
                        user_defined_building_distribution= user_defined_building_distribution, \
                        percentage_sfh=percentage_sfh, percentage_mfh=percentage_mfh, percentage_non_res=percentage_non_res, \
                        specific_buildings=specific_buildings, \
                        user_defined_build_year=user_defined_build_year,
                        specified_build_year_beginning=specified_build_year_beginning, \
                        specified_build_year_end=specified_build_year_end, user_defined_mod_year=user_defined_mod_year,
                        specified_range_mod_year_beginning=specified_range_mod_year_beginning, \
                        specified_range_mod_year_end=specified_range_mod_year_end,
                        forced_modification=forced_modification,
                        forced_modification_after=forced_modification_after,
                        user_defined_number_of_occupants=user_defined_number_of_occupants, \
                        specified_number_occupants=specified_number_occupants,
                        user_defined_number_of_apartments=user_defined_number_of_apartments, \
                        specified_number_apartments=specified_number_apartments, mod_year_method = mod_year_method, range_of_mod_years = range_of_mod_years,  nodelist_buildings=nodelist_buildings, deleted_buildings=deleted_buildings, timestep=timestep, year=year, try_path=try_path, location=location, altitude=altitude, generate_nodelist_from_function_of_citydistrict=generate_nodelist_from_function_of_citydistrict, save_city_CSV=save_city_CSV, user_defined_el_demand=user_defined_el_demand,user_defined_therm_demand=user_defined_therm_demand, user_defined_dhw=user_defined_dhw)
        print("Saved city object as CSV to ", csv_filename)

    osm_out_path = os.path.join(this_path, 'output_osm', city_filename)
    print(osm_out_path)

    #Dump as pickle file
    if save_city == True:

        # pickle.dump(city, open(osm_out_path, mode='wb'))
        pickle_dumper(city,osm_out_path)
        print()
        print('Saved city object as pickle file to ', osm_out_path)

    print_statements(city=city, zone_number=zone_number, osm_path=osm_path, \
                     considered_area_around_building=considered_area_around_building, min_house_area=min_house_area,
                     filename=filename, \
                     variance_same_ground_area=variance_same_ground_area, \
                     user_defined_building_distribution=user_defined_building_distribution,
                     percentage_sfh=percentage_sfh, \
                     percentage_mfh=percentage_mfh, percentage_non_res=percentage_non_res,
                     specific_buildings=specific_buildings, \
                     user_defined_build_year=user_defined_build_year,
                     specified_build_year_beginning=specified_build_year_beginning, \
                     specified_build_year_end=specified_build_year_end, user_defined_mod_year=user_defined_mod_year,
                     specified_range_mod_year_beginning=specified_range_mod_year_beginning, \
                     specified_range_mod_year_end=specified_range_mod_year_end,
                     user_defined_number_of_occupants=user_defined_number_of_occupants, \
                     specified_number_occupants=specified_number_occupants,
                     user_defined_number_of_apartments=user_defined_number_of_apartments, \
                     specified_number_apartments=specified_number_apartments, mod_year_method=mod_year_method,
                     range_of_mod_years=range_of_mod_years, deleted_buildings=deleted_buildings, nodelist_buildings=nodelist_buildings,generate_nodelist_from_function_of_citydistrict=generate_nodelist_from_function_of_citydistrict)

    # Time for execution of the programm
    print("--- %s seconds ---" % (time.time() - start_time))

    print("----------------------------------------------------------------------------------")
    print(filename)


def pickle_dumper(obj, filepath):
    """
    This is a defensive way to write pickle.write, allowing for very large files on all platforms
    """
    max_bytes = 2 ** 31 - 1
    bytes_out = pickle.dumps(obj)
    n_bytes = sys.getsizeof(bytes_out)
    with open(filepath, 'wb') as f_out:
        for idx in range(0, n_bytes, max_bytes):
            f_out.write(bytes_out[idx:idx + max_bytes])


def pickle_load(filepath):
    """
    This is a defensive way to write pickle.load, allowing for very large files on all platforms
    """
    max_bytes = 2 ** 31 - 1
    try:
        input_size = os.path.getsize(filepath)
        bytes_in = bytearray(0)
        with open(filepath, 'rb') as f_in:
            for _ in range(0, input_size, max_bytes):
                bytes_in += f_in.read(max_bytes)
        obj = pickle.loads(bytes_in)
    except:
        return None
    return obj


def get_lists(city, min_house_area, nodelist_buildings):
    """
    Serveral list regarding the following parameters:

    addr_building_not_found                         -->a
    addr_building_found                             -->b
    area_building_not_found                         -->c
    coordinates_from_buildings_without_adress       -->d
    buildings_not_found                             -->e
    street_names_of_all_buildings                   -->f        - to every building the known street name
    street_names                                    -->g        - just the names of the streets

    :param city: str, city-object
    :param min_house_area: int, defines the minimal area of a building. Buildings with a lower area are not considered.
    :return:
    """

    #buildings
    addr_building_not_found = [i for i in nodelist_buildings if not 'addr_street' in city.nodes[i]]      #-->a
    addr_building_found = [i for i in nodelist_buildings if 'addr_street' in city.nodes[i]]              #-->b
    house_nb_building_found = [i for i in nodelist_buildings if 'addr_housenumber' in city.nodes[i]]
    area_building_not_found = [i for i in nodelist_buildings if not 'area' in city.nodes[i]]             #-->c

    coordinates_from_buildings_without_adress = {}                                                          #-->d
    for i in addr_building_not_found:
        coordinates_from_buildings_without_adress[i] = [city.nodes[i]["position"].x, city.nodes[i]["position"].y]

    buildings_not_found = set(range(nodelist_buildings[0], nodelist_buildings[len(nodelist_buildings) - 1] + 1)) - set(nodelist_buildings)
                                                                                                            #-->e

    #streets

    street_names_of_all_buildings = []                                                                      #-->f
    street_names_of_all_buildings = [city.nodes[i]['addr_street'] for i in nodelist_buildings if
                                     'addr_street' in city.nodes[i] and not city.nodes[i][
                                                                               'addr_street'] in street_names_of_all_buildings]
    street_names = []
    for i in street_names_of_all_buildings:
        if i not in street_names:
            street_names.append(i)                                                                          #-->g

    # NOT WORKING IN AACHEN
    # buildings_with_housenumber = []                                                                         #--> h
    # house_nb_on_street = {key: [] for key in street_names}                                                  #--> i
    # for i in nodelist_buildings:
    #     if "addr_housenumber" in city.nodes[i]:
    #         buildings_with_housenumber.append(i)
    #         a=buildings_with_housenumber
    #         b=city.nodes[i]["addr_street"]
    #         c=city.nodes[i]["addr_housenumber"]
    #         d=house_nb_on_street
    #         house_nb_on_street[city.nodes[i]["addr_street"]].append(city.nodes[i]["addr_housenumber"])

            # alphabet = ["a","b","c","d","e","f","g","h","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]
            # for city.nodes[i]["addr_housenumber"] in house_nb_on_street:
            #     for letter in alphabet:
            #         city.nodes[i]["addr_housenumber"][-1].discard(letter)
            #

    ## NOT WORKING SO FAR; BECAUSE IT IS A STRING !
    # min_max_house_nb_per_street= {key: [] for key in street_names}
    # for street in street_names:
    #     min_house_nb = min(house_nb_on_street[street], key=int)
    #     max_house_nb = max(house_nb_on_street[street], key=int)
    #     missing_elements()
    #     min_max_house_nb_per_street[street] = min_house_nb, max_house_nb

    return addr_building_not_found, addr_building_found, area_building_not_found, house_nb_building_found, coordinates_from_buildings_without_adress,\
           buildings_not_found, street_names_of_all_buildings, street_names


def print_statements(city, zone_number, nodelist_buildings, deleted_buildings, osm_path, considered_area_around_building, min_house_area, filename, user_defined_building_distribution, \
                    percentage_sfh, percentage_mfh, percentage_non_res, specific_buildings, user_defined_build_year,\
                    specified_build_year_beginning, specified_build_year_end, user_defined_mod_year, range_of_mod_years, specified_range_mod_year_beginning,\
                    specified_range_mod_year_end,
                    user_defined_number_of_occupants ,specified_number_occupants, user_defined_number_of_apartments , specified_number_apartments, mod_year_method,\
                     variance_same_ground_area, generate_nodelist_from_function_of_citydistrict):
    """
    Print statements for checking or getting information

    :param city:            str     - city-object
    :param zone_number:     int     - UTM zone number
    :param osm_path:        int     - path of the osm-file

    :return: print statement as followed
    """

    print("----------------------------------------------------------------------------------")
    print(filename)

    # ------------------------------
    # DEF get_lists
    addr_building_not_found, addr_building_found, area_building_not_found, house_nb_building_found, coordinates_from_buildings_without_adress, \
    buildings_not_found, street_names_of_all_buildings, street_names \
            = get_lists(city=city, min_house_area=min_house_area, nodelist_buildings=nodelist_buildings)

    # lists for buildings, which have no adress, an adress and no ground_area.
    print("Number of buildings without adress", len(addr_building_not_found))
    print("Number of buildings with adress", len(addr_building_found))
    print()
    #
    buildings_without_adress_and_ground_area_smaller_50 = []
    for i in addr_building_not_found:

        if city.nodes[i]["area"] < 50:
            buildings_without_adress_and_ground_area_smaller_50.append(i)

    # # lists the names of the streets
    # print()
    # print("all street names due to frequency", street_names_of_all_buildings)
    # print("Street names", street_names)
    # print()


    # list
    print("letztes Gebäude in der Liste", nodelist_buildings[-1])
    print()
    print("Anzahl Gebäude", len(nodelist_buildings))

    print(" ----------------------------------------------------------------------------------------")

    # # DEF buildings_within_spezified_square

    # building_list_within_spezified_square, number_of_buildings_within_spezified_square = \
    #     get_buildings_within_spezified_square(city=city, zone_number=zone_number, considered_area = considered_area_around_building, nodelist_buildings=nodelist_buildings)
    # print()
    # print("Buildings within a spezified square", building_list_within_spezified_square)


    # DEF get_ground_area_of_building
    #
    # # print("nodelist_street", city.nodelist_street)
    # print()
    # print("Ground area of buildings", get_ground_area_of_building(city=city, min_house_area=min_house_area, nodelist_buildings=nodelist_buildings))
    # print()

    print()
    print("----------------------------------------------------------------------------------------")
    print()

    ## DEF get_buildings_parameter

    buildings_with_comment, comments, apartment_buildings, house_buildings, residential_buildings, terrace_buildings, \
    detached_buildings, bungalow_buildings, dormitory_buildings, garages_and_roofs, \
    schools, universities, houses_of_prayer, hospitals, civic, public, commercial_buildings, \
    industrial_buildings, office_buildings, retail_buildings, warehouse_buildings, \
    residential, non_residential, special_building_types, buildings_with_shop, \
    buildings_with_amenity, buildings_with_name, buildings_with_levels, \
    buildings_with_roof_shape, buildings_buildyear, buildings_condition, buildings_height, buildings_without_parameters, buildings_with_leisure\
        = get_buildings_parameters(city=city, min_house_area=min_house_area, nodelist_buildings=nodelist_buildings, generate_nodelist_from_function_of_citydistrict=generate_nodelist_from_function_of_citydistrict)

    # print("Buildings with Comment: ", buildings_with_comment)
    print("Comments", comments)
    print("Nb of buildings with Comment: ", len(buildings_with_comment))
    print()
    # print("Apartment buildings: ", apartment_buildings)
    print("Nb of apartment buildings: ", len(apartment_buildings))
    print()
    # print("House- buildings from OSM: ", house_buildings)
    print("Nb of house buildings: ", len(house_buildings))
    print()
    # print("Residential buildings: ", residential_buildings)
    print("Nb of residential buildings: ", len(residential_buildings))
    print()
    # print("Terraced House", terrace_buildings)
    print("Nb of Terraced Houses", terrace_buildings)
    print()
    # print("Schools", schools)
    print("Nb of schools", len(schools))
    # print("Universities", universities)
    print("Nb of universities: ", len(universities))
    # print("Houses of prayer", houses_of_prayer)
    print("Nb of houses of prayer: ", len(houses_of_prayer))
    # print("Hospitals", hospitals)
    print("Nb of hospitals: ", len(hospitals))
    # print("Civic", civic)
    print("Nb of civic: ", len(civic))
    # print("Public", public)
    print("Nb of public: ", len(public))
    print()
    # print("Commerialbulding: ", commercial_buildings)
    print("Nb of commercial buildings: ", len(commercial_buildings))
    # print("Industrialbulding: ", industrial_buildings)
    print("Nb of industrial buildings: ", len(industrial_buildings))
    # print("Officebulding: ", office_buildings)
    print("Nb of office buildings: ", len(office_buildings))
    # print("Retail building: ", retail_buildings)
    print("Nb of warehouse buldings: ", len(warehouse_buildings))
    print()
    print("SHOPS & CO")
    print("Buildings with Shops: ", buildings_with_shop)
    print("Nb of buildings with shops: ", len(buildings_with_shop.keys()))
    print()
    print("Buildings with Amenity: ", buildings_with_amenity)
    print("Nb of buildings with Amenity: ", len(buildings_with_amenity.keys()))
    print()
    print("Buildings with name: ", buildings_with_name)
    print("Nb of buildings with name: ", len(buildings_with_name.keys()))
    print()
    print("Buildings with nb of floors: ", buildings_with_levels)
    print("Nb of buildings with nb of floors: ", len(buildings_with_levels.keys()))
    print()
    print("Buildings with attic: ", buildings_with_roof_shape)
    print("Buildings with build year: ", buildings_buildyear)
    print("Buildings with condition: ", buildings_condition)
    print("Buildings with building height: ", buildings_height)


    # # DEF get_shops_within_spezified_square

    # shops_in_spezified_square, percentage_of_shops_to_houses \
    #     = get_shops_within_spezified_square(city=city, min_house_area=min_house_area, zone_number=zone_number, considered_area=considered_area_around_building, nodelist_buildings=nodelist_buildings, generate_nodelist_from_function_of_citydistrict=generate_nodelist_from_function_of_citydistrict)
    #
    # print(" Shops in spezified square", shops_in_spezified_square)
    # print(" Percentage of shops to houses", percentage_of_shops_to_houses)

    # # DEF is_ground_area_almost_the_same(city=city, variance = variance_same_ground_area, nodelist_buildings=nodelist_buildings):

    # print()
    # print("Same ground area: ", is_ground_area_almost_the_same(city=city, min_house_area = min_house_area, nodelist_buildings=nodelist_buildings))
    #
    # # # DEF get_min_and_max_coordinates_of_building

    # print()
    # print("Min und max", get_min_and_max_coordinates_of_building(city=city))

    # DEF check_neighbour_building

    # print()
    # buildings_neighbours, number_neighbour_buildings, no_neigbours, one_neigbour, two_neigbours, more_than_two_neighbours,  three_neigbours, four_neigbours, \
    # five_neigbours, six_neigbours, more_than_six_neigbours, coordinates_of_shared_walls \
    #     = get_neighbour_building(city, zone_number= zone_number, min_house_area=min_house_area,  considered_area_around_buildings= considered_area_around_building, nodelist_buildings=nodelist_buildings)
    # print("Nachbargebäude", buildings_neighbours)
    # print("Anzahl an Nachbargebäuden", number_neighbour_buildings)
    # print()
    # print("Buildings with no neighbours", no_neigbours)
    # print("Number of buildings without neighbours", len(no_neigbours))
    # print("Buildings with one neighbour", one_neigbour)
    # print("Number of buildings with one neighbour", len(one_neigbour))
    # print("Buildings with two neighbours", two_neigbours)
    # print("Number of buildings with two neighbours", len(two_neigbours))
    # print("Buildings with three neighbours", three_neigbours)
    # print("Number of buildings with three neighbours", len(three_neigbours))
    # print("Buildings with four neighbours", four_neigbours)
    # print("Number of buildings with four neighbours", len(four_neigbours))
    # print("Buildings with five neighbours", five_neigbours)
    # print("Number of buildings with five neighbours", len(five_neigbours))
    # print("Buildings with six neighbours", six_neigbours)
    # print("Number of buildings with six neighbours", len(six_neigbours))
    # print("Buildings with more than six neighbours", more_than_six_neigbours)
    # print("Number of buildings with more than six neighbours", len(more_than_six_neigbours))
    # print()

    # for i in three_neigbours:
    #     print("Building with three neighbours", i, city.nodes[i]["position"])
    # print()
    # for i in four_neigbours:
    #     print("Building with four neighbours", i, city.nodes[i]["position"])
    # print()
    # for i in five_neigbours:
    #     print("Building with four neighbours", i, city.nodes[i]["position"])
    # print()
    # for i in six_neigbours:
    #     print("Building with four neighbours", i, city.nodes[i]["position"])
    # print()
    # for i in more_than_six_neigbours:
    #     print("Building with more than four neighbours", i, city.nodes[i]["position"])
    #
    # print("Shared walls coordinates", coordinates_of_shared_walls)

    #print()
    ##print("Length of shared walls", length_of_shared_walls)

    ##print("Number of no length for shared walls", counter)

    # # DEF get_buildings_on_street

    # print()
    # print("Buildings on a street", get_buildings_on_street(city=city, min_house_area=min_house_area, nodelist_buildings=nodelist_buildings))
    #
    # # DEF get_street_information

    # print()
    # streets_parameters, street_parameters_ordered_by_street_name = get_street_information(osm_path=osm_path)
    # print("streets_parameters", streets_parameters)
    # print("street_parameters_ordered_by_street_name", street_parameters_ordered_by_street_name)
    #
    # DEF  check_correlation_between_buildings

    # print()
    # print("Verbindung von Nähe und Area",
    #       check_correlation_between_buildings(city=city, zone_number = zone_number, min_house_area=min_house_area, considered_area_around_buildings=considered_area_around_building, nodelist_buildings=nodelist_buildings))


def conv_outlines_of_buildings_long_lat_to_utm(city, min_house_area, nodelist_buildings, generate_nodelist_from_function_of_citydistrict, zone_number=None):
    """
    Converts all point object coordinates within city from latitude,
    longitute to utm coordinates in meters

    Parameters
    ----------
    city : object               City object with latitude, longitude coordinates
    min_house_area:     int     consideration of buildings with a larger area

    zone_number : int, optional
        Zone number of utm as integer (default: None)
        If set to none, utm modul chooses zone automatically.

    Returns
    -------
    city_new : object
        City object in UTM
    """
    if generate_nodelist_from_function_of_citydistrict == True:
        nodelist_buildings_from_osm = city.get_list_id_of_spec_node_type()
    else:
        nodelist_buildings_from_osm = nodelist_buildings

    #  Loop over every node in city
    for n in nodelist_buildings_from_osm:
        #  Current node
        cur_pos = city.nodes[n]['outlines']


        # for i in range(1, (len(city.nodes[n]['outlines'].keys())+1)):
        for i in range(len(city.nodes[n]['outlines'])):
        #  Current x/y coordinates
            x_cor = city.nodes[n]['outlines'][i][1]  # Longitude
            y_cor= city.nodes[n]['outlines'][i][0]  # Latitude

        #  Convert lat, long to utm
            (x_new, y_new, zone_nb, zone_str) = utm.from_latlon(y_cor, x_cor,
                                                            zone_number)

        #  New shapely point
            cur_point = ((x_new, y_new))

        #  Overwrite positional attributes
            city.nodes[n]['outlines'][i] = cur_point

    return city


def get_buildings_within_spezified_square(city, zone_number, considered_area, min_house_area, nodelist_buildings):
    """
    returns the buildings, which are within a square of 100 m * 100 m in default.
    The coordinates of the "start_building" are the center of the square.

    :param city: str, city-object
    :param considered_area:         int, default = 10000    -  Area in m^2 around a building, which includes other buildings.
    :param min_house_area:          int, default = 35       - minimal area of a considered building

    :return: building_list_within_spezified_square         - return of list with all the buildings within spezified square  -> a
    :return: number_of_buildings_within_spezified_square   - list with the number of buildings within spezified square      -> b
    """

    building_list_within_spezified_square = {key: [] for key in nodelist_buildings}
    for building_a in nodelist_buildings:
        #create area
        side_length = math.sqrt(considered_area)
        displacement_of_corrdinates = side_length / 2
        possible_x_high = city.nodes[building_a]["position"].x + displacement_of_corrdinates
        possible_x_low = city.nodes[building_a]["position"].x  - displacement_of_corrdinates
        possible_y_high = city.nodes[building_a]["position"].y + displacement_of_corrdinates
        possible_y_low = city.nodes[building_a]["position"].y - displacement_of_corrdinates
        for building_b in nodelist_buildings:
            if building_a != building_b:
                for edge in range(1, len(city.nodes[building_b]["outlines"])): #--> it is fine, because the last edge is just the same as the first one

                    if possible_x_low < city.nodes[building_b]["outlines"][edge][0] < possible_x_high:
                        if possible_y_low < city.nodes[building_b]["outlines"][edge][1] < possible_y_high:
                            if building_b not in building_list_within_spezified_square[building_a]:
                                building_list_within_spezified_square[building_a].append(building_b)

        number_of_buildings_within_spezified_square = {key: 0 for key in nodelist_buildings}
    for i in building_list_within_spezified_square:
        number_of_buildings_within_spezified_square[i] = len(building_list_within_spezified_square[i]) + 1 # --> + 1 so the house itself is considered, and in percentage of shop it is never divided with zero.

    return building_list_within_spezified_square, number_of_buildings_within_spezified_square


def get_distance_between_2_buildings(city, start_building, end_building):
    """
    Calculation of the distance of two buildings

    :param city: str, city-object
    :param start_building: int, id of a building
    :param end_building: int, id of a building
    :return:
    """

    dist = math.hypot((city.nodes[start_building]["position"].x - city.nodes[end_building]["position"].x),\
                      (city.nodes[start_building]["position"].y - city.nodes[end_building]["position"].y))
    return dist


def get_distances(city, zone_number, considered_area_around_buildings, min_house_area, nodelist_buildings, ):
    """
    This function creates a dictionary with all the distances between a building to every other building within the square from their centres.

     1. Creates empty dictionaries "distance_buildings" and "closest, and a list "distance_buildingstupel"
     2. Fills the dictionary with empty tuples.
     3. For every building in nodelist_buildings
           - the distance between a building to itself = 0
     4. Finds the closest building out of the "distance_buildings" --> "closest"
     5 Returns "closest" and " distance_buildings"

    :param city:                                str, city-object
    :param zone_number:                         int, default: 32            zone number is needed
    :param considered_area_around_buildings:    int, default: 10000 m^2     squared area around a building
    :param min_house_area                       int, default: 35            minimal area for a considered building


    :return: min_distance_within_square           - dict with just the nearest building
    :return: distance_buildings_within_square     - dict with all the distances within the city

    """

    building_list_within_spezified_square, number_of_buildings_within_spezified_square = get_buildings_within_spezified_square(city=city,min_house_area=min_house_area, zone_number=zone_number, considered_area= considered_area_around_buildings, nodelist_buildings=nodelist_buildings)

    distance_buildings_within_square = {}
    for building_a in nodelist_buildings:
        buildings_distances = {}
        for building_b in building_list_within_spezified_square[building_a]:
            dists = []
            if building_a != building_b:
                for edge_a in range(len(city.nodes[building_a]["outlines"])):

                    for edge_b in range(len(city.nodes[building_b]["outlines"])):
                        a =city.nodes[building_a]["outlines"][edge_a][1]
                        b =city.nodes[building_b]["outlines"][edge_b][1]
                        c=city.nodes[building_a]["outlines"][edge_a][0]
                        d= city.nodes[building_b]["outlines"][edge_b][0]
                        dists.append(math.hypot((a - b),(c - d)))
                buildings_distances[building_b] = dists
            distance_buildings_within_square[building_a]  = buildings_distances

    min_distance_to_building_within_square = {}
    min_distance_within_square = {key: [] for key in nodelist_buildings}
    for building_a in nodelist_buildings:
        buildings_distances = {}
        for building_b in building_list_within_spezified_square[building_a]:
            min_dist = min(distance_buildings_within_square[building_a][building_b])
            buildings_distances[building_b] = min_dist
            min_distance_within_square[building_a].append(min_dist)
            min_distance_to_building_within_square[building_a] = buildings_distances

    return distance_buildings_within_square, min_distance_within_square


def get_buildings_parameters(city, min_house_area, nodelist_buildings, generate_nodelist_from_function_of_citydistrict):
    """
    Get information about the spezific usage building and buildings parameters from the OpenStreetMap data
    Just possible, if specific data is given

    :param city: str, name of city-object
    :return:
                comment     see below
                shops
                amenity
                leisure
                building names
                levels of building
                roof shape
                buildyear
                condition (eg. renovated)
                height
                buildings without any specific parameters
    """

    #empty dicts

    # residential
    buildings_with_comment = {}
    comments = []
    apartment_buildings = []        # --> big building with different flats and maybe shops in the lower floor
    house_buildings= []             # --> detached, double house or terrace
    residential_buildings = []      # --> mainly used for living
    terrace_buildings = []          # --> terrace building
    detached_buildings = []         # --> single family house
    bungalow_buildings = []
    dormitory_buildings = []

    garages_and_roofs = []

    # special building types
    schools= []
    universities = []
    houses_of_prayer = []
    hospitals = []
    civic = []
    public = []

    # non-residential
    commercial_buildings = []
    industrial_buildings = []
    office_buildings = []
    retail_buildings = []
    warehouse_buildings = []

    # building type
    residential = []
    non_residential = []
    special_building_types = []


    buildings_with_shop = {}
    buildings_with_amenity = {}
    buildings_with_leisure = {}
    buildings_with_name = {}
    buildings_with_levels = {}
    buildings_with_roof_shape = {}
    buildings_buildyear = {}
    buildings_condition = {}
    buildings_height  = {}

    buildings_without_parameters = []

    if generate_nodelist_from_function_of_citydistrict == True:
        nodelist_buildings_from_osm = city.get_list_id_of_spec_node_type()
    else:
        nodelist_buildings_from_osm = nodelist_buildings


    for i in nodelist_buildings_from_osm:
        if city.nodes[i]["comment"] not in comments:
            comments.append(city.nodes[i]["comment"])
        elif city.nodes[i]["comment"] != "yes":
            buildings_with_comment[i] = [city.nodes[i]["comment"]]
        elif city.nodes[i]["comment"] == "apartments":
            apartment_buildings.append(i)
            residential.append(i)
        elif city.nodes[i]["comment"] == "house":
            house_buildings.append(i)
            residential.append(i)
        elif city.nodes[i]["comment"] == "residential":
            residential_buildings.append(i)
            residential.append(i)
        elif city.nodes[i]["comment"] == "terrace":
            terrace_buildings.append(i)
            residential.append(i)
        elif city.nodes[i]["comment"] == "detached":
            detached_buildings.append(i)
            residential.append(i)
        elif city.nodes[i]["comment"] == "bungalow":
            bungalow_buildings.append(i)
            residential.append(i)
        elif city.nodes[i]["comment"] == "dormitory":
            dormitory_buildings.append(i)
            residential.append(i)

        # Non residential
        elif city.nodes[i]["comment"] == "garages" or city.nodes[i]["comment"] == "garage" or city.nodes[i][
            "comment"] == "roof":
            garages_and_roofs.append(i)
        elif city.nodes[i]["comment"] == "school":
            schools.append(i)
            special_building_types.append(i)
        elif city.nodes[i]["comment"] == "university":
            universities.append(i)
            special_building_types.append(i)
        elif city.nodes[i]["comment"] == "cathedral" or city.nodes[i]["comment"] == "church" or city.nodes[i][
            "comment"] == "chapel" \
                or city.nodes[i]["comment"] == "monastery" or city.nodes[i]["comment"] == "mosque" or city.nodes[i][
            "comment"] == "temple" \
                or city.nodes[i]["comment"] == "synagogue" or city.nodes[i]["comment"] == "shrine":
            houses_of_prayer.append(i)
            special_building_types.append(i)
        elif city.nodes[i]["comment"] == "hospital":
            hospitals.append(i)
            special_building_types.append(i)
        elif city.nodes[i]["comment"] == "civic":
            civic.append(i)
            special_building_types.append(i)
        elif city.nodes[i]["comment"] == "public":
            public.append(i)
            special_building_types.append(i)

        elif city.nodes[i]["comment"] == "commercial":
            commercial_buildings.append(i)
            non_residential.append(i)
        elif city.nodes[i]["comment"] == "industrial":
            industrial_buildings.append(i)
            non_residential.append(i)
        elif city.nodes[i]["comment"] == "office":
            office_buildings.append(i)
            non_residential.append(i)
        elif city.nodes[i]["comment"] == "retail":
            retail_buildings.append(i)
            non_residential.append(i)
        elif city.nodes[i]["comment"] == "warehouse":
            warehouse_buildings.append(i)
            non_residential.append(i)

        if "shop" in city.nodes[i]:
            buildings_with_shop[i] = [city.nodes[i]["shop"]]

        if "amenity" in city.nodes[i]:
            buildings_with_amenity[i] = [city.nodes[i]["amenity"]]

        if "leisure" in city.nodes[i]:
            buildings_with_leisure[i] = [city.nodes[i]["leisure"]]

        if "name" in city.nodes[i] and city.nodes[i]["name"] != i:
            buildings_with_name[i] = [city.nodes[i]["name"]]

        if "building_levels" in city.nodes[i] and city.nodes[i]["building_levels"] != i:
            buildings_with_levels[i] = [city.nodes[i]["building_levels"]]

        if "building_roof_shape" in city.nodes[i] and city.nodes[i]["building_roof_shape"] != i:
            buildings_with_roof_shape[i] = [city.nodes[i]["building_roof_shape"]]

        if "building_buildyear" in city.nodes[i] and city.nodes[i]["building_buildyear"] != i:
            buildings_buildyear[i] = [city.nodes[i]["building_buildyear"]]

        if "building_condition" in city.nodes[i] and city.nodes[i]["building_condition"] != i:
            buildings_condition[i] = [city.nodes[i]["building_condition"]]

        if "building_height" in city.nodes[i] and city.nodes[i]["building_height"] != i:
            buildings_height[i] = [city.nodes[i]["building_height"]]

        else:
            buildings_without_parameters.append(i)

    return buildings_with_comment, comments,  apartment_buildings, house_buildings, residential_buildings, terrace_buildings, \
           detached_buildings, bungalow_buildings, dormitory_buildings, garages_and_roofs, \
           schools, universities, houses_of_prayer, hospitals, civic, public, commercial_buildings,\
           industrial_buildings, office_buildings, retail_buildings, warehouse_buildings, \
           residential , non_residential, special_building_types, buildings_with_shop, \
           buildings_with_amenity, buildings_with_name,  buildings_with_levels, \
           buildings_with_roof_shape, buildings_buildyear, buildings_condition, buildings_height, buildings_without_parameters, buildings_with_leisure


def get_shops_within_spezified_square(city, zone_number,considered_area, min_house_area, nodelist_buildings, generate_nodelist_from_function_of_citydistrict):
    '''
    Function to check if shops are within the squared defined area.
    Aim to get the percentage of the shops within the area to identify the city district.

    :param city:                                str, city-object
    :param zone_number:                         int, default: 32            zone number is needed
    :param considered_area_around_buildings:    int, default: 10000 m^2     squared area around a building
    :param min_house_area                       int, default: 35            minimal area for a considered building

    :return: shops_in_spezified_square          dict, str,                  list of certain shops within the area of every building
    :return: percentage_of_shops_to_houses      dict, int                   percentage of shops for the area around every buildings

    '''

    building_list_within_spezified_square, number_of_buildings_within_spezified_square \
        = get_buildings_within_spezified_square(city=city, min_house_area=min_house_area, zone_number= zone_number, considered_area = considered_area, nodelist_buildings=nodelist_buildings)

    buildings_with_comment, comments, apartment_buildings, house_buildings, residential_buildings, terrace_buildings, \
    detached_buildings, bungalow_buildings, dormitory_buildings, garages_and_roofs, \
    schools, universities, houses_of_prayer, hospitals, civic, public, commercial_buildings, \
    industrial_buildings, office_buildings, retail_buildings, warehouse_buildings, \
    residential, non_residential, special_building_types, buildings_with_shop, \
    buildings_with_amenity, buildings_with_name, buildings_with_levels, \
    buildings_with_roof_shape, buildings_buildyear, buildings_condition, buildings_height, buildings_without_parameters, buildings_with_leisure\
        = get_buildings_parameters(city=city, min_house_area=min_house_area, nodelist_buildings=nodelist_buildings, generate_nodelist_from_function_of_citydistrict=generate_nodelist_from_function_of_citydistrict)

    shops_in_spezified_square = {}

    for building_id in nodelist_buildings:
        counter = 0
        for buildings_in_square in building_list_within_spezified_square[building_id]:
            if buildings_in_square in buildings_with_shop:
                counter +=1

        shops_in_spezified_square[building_id] = counter

    percentage_of_shops_to_houses = {}

    for building_id in nodelist_buildings:
        percentage_of_shops_to_houses[building_id] = shops_in_spezified_square[building_id] / number_of_buildings_within_spezified_square[building_id]

    return shops_in_spezified_square, percentage_of_shops_to_houses


def delete_not_relevant_buildings(city, min_house_area, generate_nodelist_from_function_of_citydistrict):
    '''
    Deleting of buildings with an area smaller than the minimal house area
    and of not heated buildings. --> See at OSM (http://wiki.openstreetmap.org/wiki/DE:Key:building)

    :param city:                                str, city-object
    :param zone_number:                         int, default: 32            zone number is needed

    :return: deleted_buildings                  list                        list of the deleted building from city.nodelist_building
    :return: nodelist_buildings                 list                        NEW NODE LIST OF BUILDING without the buildings with an area smaller 35 m^2
    '''

    if generate_nodelist_from_function_of_citydistrict == True:
        nodelist_buildings_from_osm = city.get_list_id_of_spec_node_type()
    else:
        nodelist_buildings_from_osm = city.nodelist_building

    nodelist_buildings = copy.deepcopy(nodelist_buildings_from_osm)
    deleted_buildings = []

    for i in nodelist_buildings_from_osm:
        if city.nodes[i]["comment"] == "garages" \
            or city.nodes[i]["comment"] == "garage" \
            or city.nodes[i]["comment"] == "roof"\
            or city.nodes[i]["comment"] == "construction" \
            or city.nodes[i]["comment"] == "hanger" \
            or city.nodes[i]["comment"] == "shed" \
            or city.nodes[i]["comment"] == "stable" \
            or city.nodes[i]["comment"] == "sty" \
            or city.nodes[i]["comment"] == "transformer_tower" \
            or city.nodes[i]["comment"] == "ruins" \
            or city.nodes[i]["comment"] == "bridge" \
            or city.nodes[i]["comment"] == "bunker" \
            or city.nodes[i]["comment"] == "cabin" \
            or city.nodes[i]["comment"] == "cowshed" \
            or city.nodes[i]["comment"] == "digester" \
            or city.nodes[i]["comment"] == "greenhouse" \
            or city.nodes[i]["comment"] == "barn" \
            or city.nodes[i]["comment"] == "hut" \
            or city.nodes[i]["comment"] == "farm auxiliary"\
            or city.nodes[i]["area"] <= min_house_area:

            deleted_buildings.append(i)
            #NEW NODELIST !
            nodelist_buildings.remove(i)

    return deleted_buildings, nodelist_buildings


def get_buildings_with_garages(city, zone_number, min_house_area, deleted_buildings, nodelist_buildings):
    '''
    Get the buildings who do have a garage. Garages are defined as buildings with have an area below 35 m^2.
    This function is needed to identify SFH which have a big ground area. In comparision to the MFH those do have a garage in general.

    :param city:                                str, city-object
    :param zone_number:                         int, default: 32            zone number is needed
    :param min_house_area                       int, default: 35            minimal area for a considered building

    :return: buildings_with_garages             list                        list of buildings, which have a neighbour building with an area smaller 35 m^2
    '''


    buildings_with_garages= []
    for garage_id in deleted_buildings:
        building_counter = 0
        for building_id in nodelist_buildings:
            counter = 0
            if garage_id != building_id:
                # for i in range(1, (len(city.nodes[garage_id]['outlines'].keys()) + 1)):
                for i in range(len(city.nodes[garage_id]['outlines'])):
                    x_a = city.nodes[garage_id]['outlines'][i][1]
                    y_a = city.nodes[garage_id]['outlines'][i][0]
                    # for j in range(1, (len(city.nodes[building_id]['outlines'].keys()) + 1)):
                    for j in range(len(city.nodes[building_id]['outlines'])):
                        x_b = city.nodes[building_id]['outlines'][j][1]
                        y_b = city.nodes[building_id]['outlines'][j][0]
                        if x_a == x_b and y_a == y_b:
                            counter += 1  # --> avoiding, that same cornered edges are going to be count as neighbour buildings
                            # if x_a and y_a not in shared_wall:
                            #     shared_wall_coord.append(x_a)
                            #     shared_wall_coord.append(y_a)

                    if counter >= 2:
                        if building_id not in buildings_with_garages:
                            buildings_with_garages.append(building_id)

    return buildings_with_garages


def get_ground_area_of_building(city, min_house_area, nodelist_buildings):
    """
    Ground area of the buildings of a city

    :param city:                        str,                name of city-object
    :param min_house_area               int, default: 35    minimal area for a considered building

    :return: building_areas             dict                with building nodes and their ground area

    """

    building_areas = {}
    for i in nodelist_buildings:
        building_areas[i] = city.nodes[i]['area']

    return building_areas


def is_ground_area_almost_the_same(city, min_house_area, nodelist_buildings, variance = 2):
    """
    Get the buildings with nearly the same ground area within a city.

    :param city:                           str,                        name of city-object
    :param min_house_area                  int, default: 35            minimal area for a considered building
    :param variance:                       int, default = 2            variance of the ground area in m^2

    :return: same_ground_areas             Dict                        with the area as the key and buildings with the same area appended.

    """

    area = []
    for i in nodelist_buildings:
        x = round(city.nodes[i]["area"], 0)
        if i not in area:
            area.append(x)
    same_ground_areas = {key: [] for key in area}
    for i in nodelist_buildings:
        for areas in area:
            if (areas - variance ) < city.nodes[i]["area"] < (areas+variance):
                if i not in same_ground_areas[areas]:
                    same_ground_areas[areas].append(i)

    return same_ground_areas


def get_neighbour_building(city, zone_number, considered_area_around_buildings, min_house_area, nodelist_buildings):
    """
     Checks, if the coordinates of the outlines of the buildings within the squared defined area are the same as from another building --> buildings attached to each other.
     If yes, addition to dict "building_neigbours" with the neighbour building/s
     Dict "number_of_neighbours" shows the exact number of neighbours

    :param city:                                    str, city-object
    :param variance_overlap:                    int, default = 1                -  variance of how much the coordinates of the buildings are allowed to overlap due to a certain uncertainty. --> NO NEED ANYMORE; because the coordinates are exactly the same to the neigbour building !
    :param zone_number:                         int, default = zone_number      -  UTM zone number. Needed for the convertion to utm.
    :param considered_area_around_buildings:    int, default: 10000 m^2         - squared area around a building


    :return: buildings_neigbours            - dict with a key-building and their neighbour buildings.
    :return: number_neighbour_buildings     - dict with just the number of neighbour buildings for the key-building.

    :return: List for a specific number of neighbour buildings, seen below.
    """

    building_list_within_spezified_square, number_of_buildings_within_spezified_square \
        = get_buildings_within_spezified_square(city=city, min_house_area=min_house_area, zone_number=zone_number, considered_area=considered_area_around_buildings, nodelist_buildings=nodelist_buildings)

    buildings_neighbours = {key: [] for key in nodelist_buildings}
    coordinates_of_shared_walls = {key: [] for key in nodelist_buildings}
    for building_a in nodelist_buildings:
        shared_wall = {}

        building_counter = 0
        for building_b in building_list_within_spezified_square[building_a]:
            counter = 0
            building_counter += 1
            shared_wall_coord = []
            if building_a != building_b:
                # for i in range(1, (len(city.nodes[building_a]['outlines'].keys()) + 1)):
                for i in range(len(city.nodes[building_a]['outlines'])):
                    x_a = city.nodes[building_a]['outlines'][i][1]
                    y_a = city.nodes[building_a]['outlines'][i][0]
                    # for j in range(1, (len(city.nodes[building_b]['outlines'].keys()) + 1)):
                    for j in range(len(city.nodes[building_b]['outlines'])):
                        x_b = city.nodes[building_b]['outlines'][j][1]
                        y_b = city.nodes[building_b]['outlines'][j][0]
                        if x_a==x_b and y_a==y_b:
                            counter +=1               # --> avoiding, that same cornered edges are going to be count as neighbour buildings
                            # if x_a and y_a not in shared_wall:
                            #     shared_wall_coord.append(x_a)
                            #     shared_wall_coord.append(y_a)

                    if counter >=2:
                        if building_b not in buildings_neighbours[building_a]:
                            buildings_neighbours[building_a].append(building_b)

           # shared_wall[building_counter] = shared_wall_coord # --> hier der Fehler. Es handelt sich um ein DICT im DICT. Integrieren oder zurück gehen.

        coordinates_of_shared_walls[building_a] = shared_wall

    # Number of neighbours
    number_neighbour_buildings = {key: 0 for key in nodelist_buildings}
    for i in nodelist_buildings:
        if buildings_neighbours[i] != []:
            number_neighbour_buildings[i] += len(buildings_neighbours[i])

    #TODO get the length of the shared walls and compare the results to the coverage of the building
    # Length of shared walls

    # length_of_shared_walls = {key: [] for key in nodelist_buildings}
    # for building in nodelist_buildings:
    #     length = []
    #     if coordinates_of_shared_walls[building] != []:
    #         number_of_coordinates = len(coordinates_of_shared_walls[building])
    #
    #         if number_of_coordinates % 4 ==0:
    #             nb_shared_walls = int(number_of_coordinates/4)
    #             for i in range(0, nb_shared_walls):
    #                 d = coordinates_of_shared_walls[building]
    #                 e = coordinates_of_shared_walls[building][0]
    #                 x_1 = i*4
    #                 x_2 = 2 + i*4
    #                 y_1 = 1 + i*4
    #                 y_2 = 3 + i*4
    #                 x =  math.hypot((coordinates_of_shared_walls[building][x_1] - coordinates_of_shared_walls[building][x_2]), \
    #                                      (coordinates_of_shared_walls[building][y_1] - coordinates_of_shared_walls[building][y_2]))
    #                 length.append(x)
    #     length_of_shared_walls[building] = sum(length)

    # counter = 0
    # for i in nodelist_buildings:
    #     if length_of_shared_walls[i] == 0:
    #         counter += 1

    # list regarding the number of neighbours

    no_neigbours= []
    one_neigbour = []
    two_neigbours = []
    more_than_two_neighbours = []
    three_neigbours = []
    four_neigbours = []
    five_neigbours = []
    six_neigbours = []
    more_than_six_neigbours= []

    for i in number_neighbour_buildings:
        if number_neighbour_buildings[i] == 0:
            no_neigbours.append(i)
        if number_neighbour_buildings[i] == 1:
            one_neigbour.append(i)
        if number_neighbour_buildings[i] == 2:
            two_neigbours.append(i)
        if number_neighbour_buildings[i] >= 2:
            more_than_two_neighbours.append(i)
        if number_neighbour_buildings[i] == 3:
            three_neigbours.append(i)
        if number_neighbour_buildings[i] == 4:
            four_neigbours.append(i)
        if number_neighbour_buildings[i] == 5:
            five_neigbours.append(i)
        if number_neighbour_buildings[i] == 6:
            six_neigbours.append(i)
        if number_neighbour_buildings[i] >= 6:
            more_than_six_neigbours.append(i)

    return buildings_neighbours, number_neighbour_buildings, no_neigbours, one_neigbour, two_neigbours , more_than_two_neighbours, three_neigbours , \
           four_neigbours, five_neigbours,  six_neigbours, more_than_six_neigbours, coordinates_of_shared_walls #, length_of_shared_walls, counter


def get_buildings_on_street(city, min_house_area, nodelist_buildings):
    """
    Get all building with the same address.
    Using "streets". This is a list of the street names in the city, which was created in the function "get_lists(city)".

    :param city:                           str,                        city-object
    :param min_house_area                  int, default: 35            minimal area for a considered building

    :return: streets - list with street names and the attached buildings.
    """

    a, b, c, d, e, f, streets = get_lists(city, min_house_area=min_house_area, nodelist_buildings=nodelist_buildings)
    streets = {key: 0 for key in streets}
    for i in nodelist_buildings:
        if "addr_street" in city.nodes[i]:
            streets[city.nodes[i]["addr_street"]] += 1

    return streets


def get_street_information(osm_path):
    '''
    Function to get specific information about the street type, name, max speed, surface and service.
    Just possible, if given in the OSM data.

    :param osm_path:                    path for the OpenStreetMap data

    :return: streets_parameters                              dict       streets and their specific information
    :return: street_parameters_ordered_by_street_name        dict       ordered by the street name
    '''
    root = xml.etree.ElementTree.parse(osm_path).getroot()

    # Define street tags to be used in uesgraph
    street_tags = ['motorway',      # Autobahn
                   'trunk',         # autobahnähnliche Straße
                   'primary',       # Bundesstraße
                   'secondary',     # Landesstraße
                   'tertiary',      # Kreisstraße
                   'unclassified',  # Gemeindestraße
                   'residential',   # Anliegerstraße zum Wohnhaus
                   'service',       # Erschließungsstraßen
                   'living_street', # Wohnstraße / Spielstraße
                   'pedestrian'     # Fußgängerzone
                   ]

    streets = {}
    for way in root.findall('way'):
        streets[way.get('id')] = {}
        for tag in way.findall('tag'):

                if tag.get('k') == 'highway' and tag.get('v') in street_tags:
                    streets[way.get('id')]["street_tag"] = tag.get('v')

                if tag.get('k') == "name":
                    streets[way.get('id')]["name"] =  tag.get('v')

                if tag.get('k') == "maxspeed":
                    streets[way.get('id')]["maxspeed"] = tag.get('v')

                if tag.get('k') == "service":
                    streets[way.get('id')]["service"] = tag.get('v')

                if tag.get('k') == "surface":
                    streets[way.get('id')]["surface"] = tag.get('v')

    streets_parameters = {}
    for every_street in streets.keys():
        if streets[every_street] != {}:
            streets_parameters[every_street] = streets[every_street]

    street_parameters_ordered_by_street_name = {}
    for every_street in streets_parameters.keys():
        x = streets_parameters[every_street]
        if 'name' in streets_parameters[str(every_street)]:
            name = streets_parameters[str(every_street)]["name"]
            if name not in street_parameters_ordered_by_street_name:
                street_parameters_ordered_by_street_name[name] = {}
                if 'street_tag' in streets_parameters[str(every_street)]:
                    street_parameters_ordered_by_street_name[name]["street_tag"] = [streets_parameters[str(every_street)]["street_tag"]]

                if 'maxspeed' in streets_parameters[str(every_street)]:
                    street_parameters_ordered_by_street_name[name]["maxspeed"] = [streets_parameters[str(every_street)]["maxspeed"]]

                if 'service' in streets_parameters[str(every_street)]:
                    street_parameters_ordered_by_street_name[name]["service"] = [streets_parameters[str(every_street)]["service"]]

                if 'surface' in streets_parameters[str(every_street)]:
                    street_parameters_ordered_by_street_name[name]["surface"] = [streets_parameters[str(every_street)]["surface"]]

                if street_parameters_ordered_by_street_name[name] == {}:
                    del street_parameters_ordered_by_street_name[name]
            else:
                if 'street_tag' in streets_parameters[str(every_street)]:
                    if "street_tag" in street_parameters_ordered_by_street_name[name]:

                        street_parameters_ordered_by_street_name[name]["street_tag"].append(streets_parameters[str(every_street)]["street_tag"])

                if 'maxspeed' in streets_parameters[str(every_street)]:
                    if "maxspeed" in street_parameters_ordered_by_street_name[name]:
                        street_parameters_ordered_by_street_name[name]["maxspeed"].append(streets_parameters[str(every_street)]["maxspeed"])

                if 'service' in streets_parameters[str(every_street)]:
                    if "service" in street_parameters_ordered_by_street_name[name]:
                        street_parameters_ordered_by_street_name[name]["service"].append(streets_parameters[str(every_street)]["service"])

                if 'surface' in streets_parameters[str(every_street)]:
                    if "surface" in street_parameters_ordered_by_street_name[name]:
                        street_parameters_ordered_by_street_name[name]["surface"].append(streets_parameters[str(every_street)]["surface"])

                if street_parameters_ordered_by_street_name[name] == {}:
                    del street_parameters_ordered_by_street_name[name]

    return streets_parameters, street_parameters_ordered_by_street_name


def check_correlation_between_buildings(city, zone_number, considered_area_around_buildings, min_house_area, nodelist_buildings, variance_for_same_ground_area = 2):
    """
    Function to get to know, if there is a correlation between the same ground area within a considered area around a building.
    Aim is to figure out, if building of the same type are built.

    :param city:                                str, city-object
    :param zone_number:                         int, default = zone_number      -  UTM zone number. Needed for the convertion to utm.
    :param variance_for_same_ground_area:       int, default = 2                -  variance for the ground area of different buildings in m^2
    :param considered_area_around_buildings:    int, default = 10000            -  building within this area area considered in m^2
    :param min_house_area                       int, default: 35                -  minimal area for a considered building


    :return: near_by_buildings_with_same_area  -  dict with the building id and a attached list of the building within
                                                  area and the the same ground area.

    """

    same_area = is_ground_area_almost_the_same(city= city, min_house_area=min_house_area, variance=variance_for_same_ground_area, nodelist_buildings=nodelist_buildings)
    building_list_within_spezified_square, number_of_buildings_within_spezified_square = get_buildings_within_spezified_square(city = city, min_house_area=min_house_area, zone_number=zone_number, considered_area= considered_area_around_buildings,nodelist_buildings=nodelist_buildings)
    near_by_buildings_with_same_area = {key: [] for key in nodelist_buildings}
    for i in same_area.keys():
        if len(same_area.get(i)) > 1:
            for j in range(0, (len(same_area.get(i)))):
                for k in range(0, (len(same_area.get(i)))):
                    x = same_area[i][k]
                    if same_area[i][k] in building_list_within_spezified_square[same_area[i][j]]:
                        if same_area[i][k] not in near_by_buildings_with_same_area[same_area[i][k]]:
                            if same_area[i][k] != same_area[i][j]:
                                if x not in near_by_buildings_with_same_area[same_area[i][j]]:
                                    near_by_buildings_with_same_area[same_area[i][j]].append(x)

    results_near_by_buildings_with_same_area = {}
    for i in near_by_buildings_with_same_area:
        if near_by_buildings_with_same_area[i] != []:
            results_near_by_buildings_with_same_area[i] = near_by_buildings_with_same_area[i]

    return near_by_buildings_with_same_area


def get_residential_layout(city, zone_number, min_house_area, nodelist_buildings,  generate_nodelist_from_function_of_citydistrict, factor_compact = 1.5, variance = 0.99):
    '''
    NOT FULLFILLING ITS AIM.
    PROBLEMS WITH THE COMPLEXITY OF OUTLINES STRUCTURE OF THE BUILDINGS.

    It is not clear from the length of the outlines if those are going into the same direction. Walls can be splitted into several outlines, which causes the problem.

    Aim to get the residential layout of a building, which shows, if the building has a compact structure or is complex and wider structured.

    :param city:                    str, city-object
    :param variance_overlap:        int, default = 1                -  variance of how much the coordinates of the buildings are allowed to overlap due to a certain uncertainty. --> NO NEED ANYMORE; because the coordinates are exactly the same to the neigbour building !
    :param zone_number:             int, default = zone_number      -  UTM zone number. Needed for the convertion to utm.
    :param factor_compact:          int, default 1.5                -  factor with defines a compact building, if the factor is above the building is coomplex
    :param variance:

    :return:
    '''

    conv_outlines_of_buildings_long_lat_to_utm(city=city, zone_number=zone_number, nodelist_buildings=nodelist_buildings, generate_nodelist_from_function_of_citydistrict=generate_nodelist_from_function_of_citydistrict)

    dist = {key: [] for key in nodelist_buildings}
    dist_from_edge_to_edge = {key: [] for key in nodelist_buildings}
    dist_6 = {key: [] for key in nodelist_buildings}
    dist_7 = {key: [] for key in nodelist_buildings}

    list_with_ids_6_coordinates = []
    list_with_ids_7_coordinates = []

    compact = []
    complex = []

    nb_5_nodes = []
    nb_6_nodes = []
    nb_7_nodes = []
    nb_8_nodes = []
    nb_9_nodes = []
    nb_10_nodes = []
    nb_11_nodes = []
    nb_12_nodes = []
    nb_13_nodes = []
    nb_14_nodes = []
    nb_15_nodes = []

    building_geometry = {key: {} for key in nodelist_buildings}
    for i in nodelist_buildings:

        if len(city.nodes[i]["outlines"]) == 5:
            nb_5_nodes.append(city.nodes[i])
        if len(city.nodes[i]["outlines"]) == 6:
            nb_6_nodes.append(city.nodes[i])
        if len(city.nodes[i]["outlines"]) == 7:
            nb_7_nodes.append(city.nodes[i])
        if len(city.nodes[i]["outlines"]) == 8:
            nb_8_nodes.append(city.nodes[i])
        if len(city.nodes[i]["outlines"]) == 9:
            nb_9_nodes.append(city.nodes[i])
        if len(city.nodes[i]["outlines"]) == 10:
            nb_10_nodes.append(city.nodes[i])
        if len(city.nodes[i]["outlines"]) == 11:
            nb_11_nodes.append(city.nodes[i])
        if len(city.nodes[i]["outlines"]) == 12:
            nb_12_nodes.append(city.nodes[i])
        if len(city.nodes[i]["outlines"]) == 13:
            nb_13_nodes.append(city.nodes[i])
        if len(city.nodes[i]["outlines"]) == 14:
            nb_14_nodes.append(city.nodes[i])
        if len(city.nodes[i]["outlines"]) == 15:
            nb_15_nodes.append(city.nodes[i])

        # TODO: Längste Seite eines Gebäudes erkennen, Struktur des Gebäudes / Geometrie --> Kompakte oder Komplexe Bauweise

        # get the distance from edge to edge of the building
        for j in range(1, (len(city.nodes[i]["outlines"]))-1):
            dist_from_edge_to_edge[i].append(math.hypot((city.nodes[i]["outlines"][j][1] - city.nodes[i]["outlines"][j+1][1]), \
                                      (city.nodes[i]["outlines"][j][0] - city.nodes[i]["outlines"][j+1][0])))

        # get the distance from the last edge to the first edge of the building
        dist_from_edge_to_edge[i].append(math.hypot((city.nodes[i]["outlines"][len(city.nodes[i]["outlines"])-1][1] - city.nodes[i]["outlines"][1][1]), \
                                      (city.nodes[i]["outlines"][len(city.nodes[i]["outlines"])-1][0] - city.nodes[i]["outlines"][1][0])))


        #building with 5 edges

        if len(dist_from_edge_to_edge[i]) == 5:
            list_with_ids_6_coordinates.append(i)
            for edge in range(0, len(dist_from_edge_to_edge[i])-1):
                if dist_from_edge_to_edge[i][edge] <=1:
                    del(dist_from_edge_to_edge[i][edge])

        #building with 6 edges / 7 nodes

        if len(dist_from_edge_to_edge[i]) == 6:
            help_list_7 = []
            list_with_ids_7_coordinates.append(i)
            for edge_a in range(0, len(dist_from_edge_to_edge[i]) - 1):
                for edge_b in range(0, len(dist_from_edge_to_edge[i]) - 1):
                    if edge_a != edge_b:

                        if dist_from_edge_to_edge[i][edge_b] + variance <= dist_from_edge_to_edge[i][edge_a] + dist_from_edge_to_edge[i][edge_a +1] <= dist_from_edge_to_edge[i][edge_b] + variance:
                            help_list_7.append(dist_from_edge_to_edge[i][edge_b])
                            if dist_from_edge_to_edge[i][edge_b] - variance <= dist_from_edge_to_edge[i][edge_a] <= \
                                            dist_from_edge_to_edge[i][edge_b] + variance:
                                help_list_7.append(dist_from_edge_to_edge[i][edge_b])

                                width = min(help_list_7)
                                length = max(help_list_7)

                                building_geometry[i] = [width, length]

        if len(dist_from_edge_to_edge[i]) == 4:
            diff_min = sorted(dist_from_edge_to_edge[i])[0] - sorted(dist_from_edge_to_edge[i])[1]
            diff_max = sorted(dist_from_edge_to_edge[i])[2] - sorted(dist_from_edge_to_edge[i])[3]
            if diff_min <= 1:
                width = min(dist_from_edge_to_edge[i])
            if diff_max <= 1:
                length = max(dist_from_edge_to_edge[i])
                # length = sorted(dist[i])[1]
            building_geometry[i] = [width, length]

        if len(building_geometry[i]) == 2:
            if building_geometry[i][1] > building_geometry[i][0] * factor_compact:
                complex.append(i)
            else:
                compact.append(i)

    return dist, dist_from_edge_to_edge, dist_6, dist_7, building_geometry, complex, compact, nb_5_nodes, nb_6_nodes, nb_7_nodes, \
           nb_8_nodes, nb_9_nodes, nb_10_nodes, nb_11_nodes, nb_12_nodes, nb_13_nodes, nb_14_nodes, nb_15_nodes, list_with_ids_6_coordinates, list_with_ids_7_coordinates

#-----------------------------------------------------------------------------------------
# Functions for data enrichment

def get_district_type(city, zone_number, considered_area_around_building, min_house_area, nodelist_buildings):
    '''
    Needed for city district.
    Function gives information about the cropped area with buildings and the average neighbour building within the squared defined area.
    Streets are not included in the calculation of the cropped area.

    :param city:                                str, city-object
    :param zone_number:                         int, default = zone_number      -  UTM zone number. Needed for the convertion to utm.
    :param considered_area_around_buildings:    int, default = 10000            -  building within this area area considered in m^2
    :param min_house_area                       int, default: 35                -  minimal area for a considered building

    :return: cropped_area_within_square
    :return: percentage_cropped_area_within_square
    :return: average_buildings_neighbours
    '''

    building_list_within_spezified_square, number_of_buildings_within_spezified_square = \
        get_buildings_within_spezified_square(city = city, min_house_area=min_house_area, zone_number=zone_number, considered_area= considered_area_around_building, nodelist_buildings=nodelist_buildings)
    buildings_neighbours, number_neighbour_buildings, no_neigbours, one_neigbour, two_neigbours, more_than_two_neighbours, three_neigbours, \
    four_neigbours, five_neigbours, six_neigbours, more_than_six_neigbours, coordinates_of_shared_walls \
        = get_neighbour_building(city=city, min_house_area=min_house_area, zone_number=zone_number,
                                 considered_area_around_buildings=considered_area_around_building, nodelist_buildings=nodelist_buildings)

    cropped_area_within_square = {key: [] for key in nodelist_buildings}
    percentage_cropped_area_within_square = {key: [] for key in nodelist_buildings}
    average_buildings_neighbours = {key: [] for key in nodelist_buildings}
    for building_id in nodelist_buildings:
        cropped_area = 0
        building_neighbours = 0
        for building_in_square in building_list_within_spezified_square[building_id]:
            cropped_area += city.nodes[building_in_square]["area"]
            building_neighbours += number_neighbour_buildings[building_in_square]

        cropped_area_within_square[building_id] = cropped_area
        percentage_cropped_area_within_square[building_id] = cropped_area / considered_area_around_building
        average_buildings_neighbours[building_id] = building_neighbours / number_of_buildings_within_spezified_square[building_id]

    return cropped_area_within_square, percentage_cropped_area_within_square, average_buildings_neighbours


def get_build_year_sfh(building_id, terraced_houses, double_houses):
    '''
    Function to identify the build year for Single Familiy Houses regarding their frequency in general in Germany.
    Gives further information about the height of floors, cellar, attic and dormer, which are related to the build year.

    # Frequency of the different building types regarding the build year
    # Source: DE_TABULA_TypologyBrochure_IWU.pdf Table 4

    # for SFH --> numpy.random.choice(numpy.arange(0, 10), p=[0.0326,0.0950,0.1112,0.0845,0.1484,0.1482,0.0692,0.1141,0.1018,0.0762,0.0188])
    # for TH and DH --> numpy.random.choice(numpy.arange(0, 10), p=[0.0287,0.0960,0.1385,0.0872,0.1235,0.1192,0.0653,0.1272,0.1207,0.0749,0.0188])

    # Number to the age of the building classes
    # 0: before 1890
    # 1: 1980 - 1918
    # 2: 1919 - 1948
    # 3: 1949 - 1958
    # 4: 1959 - 1968
    # 5: 1969 - 1978
    # 6: 1979 - 1983
    # 7: 1984 - 1994
    # 8: 1995 - 2001
    # 9: 2002 - 2008
    # 10 : after 2009

    # Data for the height of floors, cellar, roof, dormer from the IWU
    # http://www.iwu.de/fileadmin/user_upload/dateien/energie/klima_altbau/Gebaeudetypologie_Deutschland.pdf


    :param building_id:         specific building
    :param terraced_houses:     list of all the buildings with the building typ "Terraced house"
    :param double_houses:       list of all the buildings with the building typ "Double house"

    :return: build_year, height_of_floors, cellar, attic, dormer

    '''

    height_of_floors_sfh = [2.3, 2.6, 2.75, 2.36, 2.52, 2.6, 2.5, 2.5, 2.5, 2.39, 2.39]
    height_of_floors_th = [2.9, 2.9, 2.6, 2.55, 2.51, 2.5, 2.5, 2.5, 2.53, 2.5, 2.5]

    # Cellar:       0: no cellar; 1: non heated cellar; 2: partly heated cellar; 3: heated cellar
    cellar_sfh = 1
    cellar_th = [3, 3, 1, 1, 1, 1, 1, 2, 1, 2, 2]

    # Attic:        0: flat roof; 1: non heated attic; 2: partly heated attic; 3: heated attic
    attic_sfh = [3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3]
    attic_th = [1, 1, 1, 0, 0, 1, 1, 3, 3, 3, 3]


    if  building_id in terraced_houses or building_id in double_houses:
        range_build_year = numpy.random.choice(numpy.arange(0, 11), p=[0.0287,0.0960,0.1385,0.0872,0.1235,0.1192,0.0653,0.1272,0.1207,0.0749,0.0188])
        height_of_floors = height_of_floors_th[range_build_year]
        cellar = cellar_th[range_build_year]
        attic = attic_th[range_build_year]
        if range_build_year == 6:
            dormer = 1
        else:
            dormer = None
    else: # SFH
        range_build_year = numpy.random.choice(numpy.arange(0, 11), p=[0.0326,0.0950,0.1112,0.0845,0.1484,0.1482,0.0692,0.1141,0.1018,0.0762,0.0188])
        height_of_floors = height_of_floors_sfh[range_build_year]
        cellar = 1
        attic = attic_sfh[range_build_year]
        if range_build_year in [1, 2, 5, 7]:
            dormer = 1
        else:
            dormer = None

    if range_build_year == 0:
        build_year = 1889

    elif range_build_year == 1:
        build_year = random.randint(1890, 1918)

    elif range_build_year == 2:
        build_year = random.randint(1919, 1948)

    elif range_build_year == 3:
        build_year = random.randint(1949, 1958)

    elif range_build_year == 4:
        build_year = random.randint(1959, 1968)

    elif range_build_year == 5:
        build_year = random.randint(1969, 1978)

    elif range_build_year == 6:
        build_year = random.randint(1979, 1983)

    elif range_build_year == 7:
        build_year = random.randint(1984, 1994)

    elif range_build_year == 8:
        build_year = random.randint(1995, 2001)

    elif range_build_year == 9:
        build_year = random.randint(2002, 2008)

    # assumption of the same parameters as in the previous years
    elif range_build_year == 10:
        build_year = random.randint(2009, int(time.strftime("%Y")))

    return build_year, height_of_floors, cellar, attic, dormer


def get_build_year_sfh_user_defined(building_id, terraced_houses, double_houses, specified_build_year_beginning, specified_build_year_end):
    '''
    Function to get the user defined build year within a specific range.
    Limits the normal distribution of the build year for Single Family Houses.

    # Number to the age of the building classes
    # 0: before 1890
    # 1: 1980 - 1918
    # 2: 1919 - 1948
    # 3: 1949 - 1958
    # 4: 1959 - 1968
    # 5: 1969 - 1978
    # 6: 1979 - 1983
    # 7: 1984 - 1994
    # 8: 1995 - 2001
    # 9: 2002 - 2008
    # 10 : after 2009

    # Data for the height of floors, cellar, roof, dormer from the IWU
    # http://www.iwu.de/fileadmin/user_upload/dateien/energie/klima_altbau/Gebaeudetypologie_Deutschland.pdf

    :param building_id:
    :param terraced_houses:
    :param double_houses:
    :param specified_build_year_beginning:
    :param specified_build_year_end:

    :return: build_year, height_of_floors, cellar, attic, dormer
    '''

    height_of_floors_sfh = [2.3, 2.6, 2.75, 2.36, 2.52, 2.6, 2.5, 2.5, 2.5, 2.39, 2.39]
    height_of_floors_th = [2.9, 2.9, 2.6, 2.55, 2.51, 2.5, 2.5, 2.5, 2.53, 2.5, 2.5]

    # Cellar:       0: no cellar; 1: non heated cellar; 2: partly heated cellar; 3: heated cellar
    cellar_sfh = 1
    cellar_th = [3, 3, 1, 1, 1, 1, 1, 2, 1, 2, 2]

    # Attic:        0: flat roof; 1: non heated attic; 2: partly heated attic; 3: heated attic
    attic_sfh = [3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3]
    attic_th = [1, 1, 1, 0, 0, 1, 1, 3, 3, 3, 3]

    # Identification of the range of the build year
    build_year_in_range = [1890, 1918, 1948, 1958, 1968, 1978, 1983, 1994, 2001, 2008, int(time.strftime("%Y"))]

    for i in build_year_in_range:
        if specified_build_year_beginning <= i:
            range_build_year_low = build_year_in_range.index(i)
            break
        else:
            continue

    for i in build_year_in_range:
        if specified_build_year_end <= i:
            range_build_year_high = build_year_in_range.index(i)
            break
        else:
            continue

    if building_id in terraced_houses or building_id in double_houses:
        p = [0.0287,0.0960,0.1385,0.0872,0.1235,0.1192,0.0653,0.1272,0.1207,0.0749,0.0188]
    else:
        p = [0.0326, 0.0950, 0.1112, 0.0845, 0.1484, 0.1482, 0.0692, 0.1141,
                                                      0.1018, 0.0762, 0.0188]

    # Identification of the build year

    if range_build_year_high - range_build_year_low == 0:
        build_year = random.randint(specified_build_year_beginning, specified_build_year_end)

        if building_id in terraced_houses:
            height_of_floors = height_of_floors_th[range_build_year_high]
            cellar = cellar_th[range_build_year_high]
            attic = attic_th[range_build_year_high]
            if range_build_year_high == 6:
                dormer = 1
            else:
                dormer = None
        else:
            height_of_floors = height_of_floors_sfh[range_build_year_high]
            cellar = 1
            attic = attic_sfh[range_build_year_high]
            if range_build_year_high in [1, 2, 5, 7]:
                dormer = 1
            else:
                dormer = None

    elif (range_build_year_high - range_build_year_low) >= 1:
        percentage_unequal_1 = []
        sum_percentage = 0
        percentage_equal_1 = []
        for i in range(range_build_year_low, range_build_year_high + 1):
            percentage_unequal_1.append(p[i])
            sum_percentage += p[i]

        multiplication_factor = 1 / sum_percentage
        for i in range(0, len(percentage_unequal_1)):
            percentage_equal_1.append(percentage_unequal_1[i] * multiplication_factor)
        range_build_year = numpy.random.choice(
            numpy.arange(range_build_year_low, range_build_year_high + 1), p=percentage_equal_1)

        # Data Enrichment for height of floors, cellar, attic and dormer
        if building_id in terraced_houses:
            height_of_floors = height_of_floors_th[range_build_year]
            cellar = cellar_th[range_build_year]
            attic = attic_th[range_build_year]
            if range_build_year_high == 6:
                dormer = 1
            else:
                dormer = None
        else:
            height_of_floors = height_of_floors_sfh[range_build_year]
            cellar = 1
            attic = attic_sfh[range_build_year]
            if range_build_year_high in [1, 2, 5, 7]:
                dormer = 1
            else:
                dormer = None

        if range_build_year == 0:
            build_year = 1889

        elif range_build_year == 1:
            if range_build_year_low == range_build_year:
                build_year = random.randint(specified_build_year_beginning, 1918)
            elif range_build_year_high == range_build_year:
                build_year = random.randint(1890, specified_build_year_end)
            else:
                build_year = random.randint(1890, 1918)

        elif range_build_year == 2:
            if range_build_year_low == range_build_year:
                build_year = random.randint(specified_build_year_beginning, 1948)
            elif range_build_year_high == range_build_year:
                build_year = random.randint(1919, specified_build_year_end)
            else:
                build_year = random.randint(1919, 1948)

        elif range_build_year == 3:
            if range_build_year_low == range_build_year:
                build_year = random.randint(specified_build_year_beginning, 1958)
            elif range_build_year_high == range_build_year:
                build_year = random.randint(1949, specified_build_year_end)
            else:
                build_year = random.randint(1949, 1958)

        elif range_build_year == 4:
            if range_build_year_low == range_build_year:
                build_year = random.randint(specified_build_year_beginning, 1968)
            elif range_build_year_high == range_build_year:
                build_year = random.randint(1959, specified_build_year_end)
            else:
                build_year = random.randint(1959, 1968)

        elif range_build_year == 5:
            if range_build_year_low == range_build_year:
                build_year = random.randint(specified_build_year_beginning, 1978)
            elif range_build_year_high == range_build_year:
                build_year = random.randint(1969, specified_build_year_end)
            else:
                build_year = random.randint(1969, 1978)

        elif range_build_year == 6:
            if range_build_year_low == range_build_year:
                build_year = random.randint(specified_build_year_beginning, 1983)
            elif range_build_year_high == range_build_year:
                build_year = random.randint(1979, specified_build_year_end)
            else:
                build_year = random.randint(1979, 1983)

        elif range_build_year == 7:
            if range_build_year_low == range_build_year:
                build_year = random.randint(specified_build_year_beginning, 1994)
            elif range_build_year_high == range_build_year:
                build_year = random.randint(1984, specified_build_year_end)
            else:
                build_year = random.randint(1984, 1994)

        elif range_build_year == 8:
            if range_build_year_low == range_build_year:
                build_year = random.randint(specified_build_year_beginning, 2001)
            elif range_build_year_high == range_build_year:
                build_year = random.randint(1995, specified_build_year_end)
            else:
                build_year = random.randint(1995, 2001)

        elif range_build_year == 9:
            if range_build_year_low == range_build_year:
                build_year = random.randint(specified_build_year_beginning, int(time.strftime("%Y")))
            elif range_build_year_high == range_build_year:
                build_year = random.randint(2002, specified_build_year_end)
            else:
                build_year = random.randint(2002, 2008)

        elif range_build_year == 10:
            if range_build_year_low == range_build_year:
                build_year = random.randint(specified_build_year_beginning, int(time.strftime("%Y")))
            elif range_build_year_high == range_build_year:
                build_year = random.randint(2009, specified_build_year_end)
            else:
                build_year = random.randint(2009, int(time.strftime("%Y")))

    return build_year, height_of_floors , cellar, attic, dormer


def get_build_year_mfh(building_id, high_rise_houses):
    '''
    Function to identify the build year for Multi Familiy Houses regarding their frequency in general in Germany.
    Gives further information about the height of floors, cellar, attic and dormer, which are related to the build year.

    Frequency of the different building types regarding the build year
    Source: DE_TABULA_TypologyBrochure_IWU.pdf Table 4

    for MFH --> numpy.random.choice(numpy.arange(0, 10), p=[0.0179, 0.1444, 0.1267, 0.1163, 0.1914, 0.1346, 0.0477, 0.1009, 0.0797, 0.0278, 0.0126])
    for High rise --> numpy.random.choice(numpy.arange(0, 10), p=[0.0028, 0.1336, 0.0348, 0.0813, 0.1599, 0.2356, 0.0705, 0.1349, 0.0983, 0.0357, 0.0126])

    # Number to the age of the building classes
    # 0: before 1890
    # 1: 1980 - 1918
    # 2: 1919 - 1948
    # 3: 1949 - 1958
    # 4: 1959 - 1968
    # 5: 1969 - 1978
    # 6: 1979 - 1983
    # 7: 1984 - 1994
    # 8: 1995 - 2001
    # 9: 2002 - 2008
    # 10: after 2009

    Data for the height of floors, cellar, roof, dormer from the IWU
    http://www.iwu.de/fileadmin/user_upload/dateien/energie/klima_altbau/Gebaeudetypologie_Deutschland.pdf


    :param building_id:
    :param high_rise_houses:

    :return: build_year, height_of_floors, cellar, attic, dormer
    '''

    height_of_floors_mfh = [2.62, 3, 2.8, 2.65, 2.61, 2.51, 2.75, 2.71, 2.71, 2.5, 2.5]
    height_of_floors_high_rise = [2.62, 2.82, 2.9, 2.75, 2.5, 2.55, 2.75, 2.71, 2.71, 2.5, 2.5]

    # Cellar:       0: no cellar; 1: non heated cellar; 2: partly heated cellar; 3: heated cellar
    cellar_mfh = [1, 3, 2, 1, 1, 1, 1, 1, 1, 1, 1]

    # Attic:        0: flat roof; 1: non heated attic; 2: partly heated attic; 3: heated attic
    attic_mfh = [3, 1, 3, 1, 1, 1, 1, 1, 1, 2, 2]

    if building_id in high_rise_houses:
        range_build_year = numpy.random.choice(numpy.arange(0, 11),
                                           p=[0.0028,0.1336,0.0348,0.0813,0.1599,0.2356,0.0705,0.1349,0.0983,0.0357,0.0126])
        height_of_floors = height_of_floors_high_rise[range_build_year]
        cellar = 1
        attic = 0
        dormer = None
    else:
        range_build_year = numpy.random.choice(numpy.arange(0, 11),
                                           p=[0.0179,0.1444,0.1267,0.1163,0.1914,0.1346,0.0477,0.1009,0.0797,0.0278,0.0126])
        height_of_floors = height_of_floors_mfh[range_build_year]
        cellar = cellar_mfh[range_build_year]
        attic = attic_mfh[range_build_year]
        if range_build_year == 0:
            dormer = 1
        else:
            dormer = None

    if range_build_year == 0:
        build_year = build_year = 1889

    elif range_build_year == 1:
        build_year = random.randint(1890, 1918)

    elif range_build_year == 2:
        build_year = random.randint(1919, 1948)

    elif range_build_year == 3:
        build_year = random.randint(1949, 1958)

    elif range_build_year == 4:
        build_year = random.randint(1959, 1968)

    elif range_build_year == 5:
        build_year = random.randint(1969, 1978)

    elif range_build_year == 6:
        build_year = random.randint(1979, 1983)

    elif range_build_year == 7:
        build_year = random.randint(1984, 1994)

    elif range_build_year == 8:
        build_year = random.randint(1995, 2001)

    elif range_build_year == 9:
        build_year = random.randint(2002, 2008)

    elif range_build_year == 10:
        build_year = random.randint(2009, int(time.strftime("%Y")))

    return build_year, height_of_floors, cellar, attic, dormer


def get_build_year_mfh_user_defined(building_id, high_rise_houses, specified_build_year_beginning, specified_build_year_end):
    '''
    Function to get the user defined build year within a specific range.
    Limits the normal distribution of the build year for Multi Family Houses.

    # Number to the age of the building classes
    # 0: before 1890
    # 1: 1980 - 1918
    # 2: 1919 - 1948
    # 3: 1949 - 1958
    # 4: 1959 - 1968
    # 5: 1969 - 1978
    # 6: 1979 - 1983
    # 7: 1984 - 1994
    # 8: 1995 - 2001
    # 9: 2002 - 2008
    # 10: after 2009

    # Data for the height of floors, cellar, roof, dormer from the IWU
    # http://www.iwu.de/fileadmin/user_upload/dateien/energie/klima_altbau/Gebaeudetypologie_Deutschland.pdf

    :param building_id:
    :param high_rise_houses:
    :param specified_build_year_beginning:
    :param specified_build_year_end:

    :return: build_year, height_of_floors, cellar, attic, dormer
    '''

    build_year_in_range = [1890, 1918, 1948, 1958, 1968, 1978, 1983, 1994, 2001, 2008, int(time.strftime("%Y"))]
    height_of_floors_mfh = [2.62, 3, 2.8, 2.65, 2.61, 2.51, 2.75, 2.71, 2.71, 2.5, 2.5]
    height_of_floors_high_rise = [2.62, 2.82, 2.9, 2.75, 2.5, 2.55, 2.75, 2.71, 2.71, 2.5, 2.5]

    # Cellar:       0: no cellar; 1: non heated cellar; 2: partly heated cellar; 3: heated cellar
    cellar_mfh = [1, 3, 2, 1, 1, 1, 1, 1, 1, 1, 1]

    # Attic:        0: flat roof; 1: non heated attic; 2: partly heated attic; 3: heated attic
    attic_mfh = [3, 1, 3, 1, 1, 1, 1, 1, 1, 2, 2]

    for i in build_year_in_range:
        if specified_build_year_beginning <= i:
            range_build_year_low = build_year_in_range.index(i)
            break
        else:
            continue

    for i in build_year_in_range:
        if specified_build_year_end <= i:
            range_build_year_high = build_year_in_range.index(i)
            break
        else:
            continue

    if building_id in high_rise_houses:
        p = [0.0028, 0.1336, 0.0348, 0.0813, 0.1599, 0.2356, 0.0705, 0.1349, 0.0983, 0.0357, 0.0126]
    else:
        p = [0.0179, 0.1444, 0.1267, 0.1163, 0.1914, 0.1346, 0.0477, 0.1009, 0.0797, 0.0278, 0.0126]


    if range_build_year_high - range_build_year_low == 0:
        build_year = random.randint(specified_build_year_beginning, specified_build_year_end)
        if building_id in high_rise_houses:
            height_of_floors = height_of_floors_high_rise[range_build_year_high]
            cellar = 1
            attic = 0
            dormer = None
        else:
            height_of_floors = height_of_floors_mfh[range_build_year_high]
            cellar = cellar_mfh[range_build_year_high]
            attic = attic_mfh[range_build_year_high]
            if range_build_year_high == 0:
                dormer = 1
            else:
                dormer = None


    elif (range_build_year_high - range_build_year_low) >= 1:
        percentage_unequal_1 = []
        sum_percentage = 0
        percentage_equal_1 = []
        for i in range(range_build_year_low, range_build_year_high + 1):
            percentage_unequal_1.append(p[i])
            sum_percentage += p[i]

        multiplication_factor = 1 / sum_percentage
        for i in range(0, len(percentage_unequal_1)):
            percentage_equal_1.append(percentage_unequal_1[i] * multiplication_factor)
        range_build_year = numpy.random.choice(
            numpy.arange(range_build_year_low, range_build_year_high + 1), p=percentage_equal_1)

        # Data Enrichment for height of floors, cellar, attic and dormer
        if building_id in high_rise_houses:
            height_of_floors = height_of_floors_high_rise[range_build_year]
            cellar = 1
            attic = 0
            dormer = None
        else:
            height_of_floors = height_of_floors_mfh[range_build_year]
            cellar = cellar_mfh[range_build_year]
            attic = attic_mfh[range_build_year]
            if range_build_year == 0:
                dormer = 1
            else:
                dormer = None

        if range_build_year == 0:
            build_year = build_year = 1889

        elif range_build_year == 1:
            if range_build_year_low == range_build_year:
                build_year = random.randint(specified_build_year_beginning, 1918)
            elif range_build_year_high == range_build_year:
                build_year = random.randint(1890, specified_build_year_end)
            else:
                build_year = random.randint(1890, 1918)

        elif range_build_year == 2:
            if range_build_year_low == range_build_year:
                build_year = random.randint(specified_build_year_beginning, 1948)
            elif range_build_year_high == range_build_year:
                build_year = random.randint(1919, specified_build_year_end)
            else:
                build_year = random.randint(1919, 1948)

        elif range_build_year == 3:
            if range_build_year_low == range_build_year:
                build_year = random.randint(specified_build_year_beginning, 1958)
            elif range_build_year_high == range_build_year:
                build_year = random.randint(1949, specified_build_year_end)
            else:
                build_year = random.randint(1949, 1958)

        elif range_build_year == 4:
            if range_build_year_low == range_build_year:
                build_year = random.randint(specified_build_year_beginning, 1968)
            elif range_build_year_high == range_build_year:
                build_year = random.randint(1959, specified_build_year_end)
            else:
                build_year = random.randint(1959, 1968)

        elif range_build_year == 5:
            if range_build_year_low == range_build_year:
                build_year = random.randint(specified_build_year_beginning, 1978)
            elif range_build_year_high == range_build_year:
                build_year = random.randint(1969, specified_build_year_end)
            else:
                build_year = random.randint(1969, 1978)

        elif range_build_year == 6:
            if range_build_year_low == range_build_year:
                build_year = random.randint(specified_build_year_beginning, 1983)
            elif range_build_year_high == range_build_year:
                build_year = random.randint(1979, specified_build_year_end)
            else:
                build_year = random.randint(1979, 1983)

        elif range_build_year == 7:
            if range_build_year_low == range_build_year:
                build_year = random.randint(specified_build_year_beginning, 1994)
            elif range_build_year_high == range_build_year:
                build_year = random.randint(1984, specified_build_year_end)
            else:
                build_year = random.randint(1984, 1994)

        elif range_build_year == 8:
            if range_build_year_low == range_build_year:
                build_year = random.randint(specified_build_year_beginning, 2001)
            elif range_build_year_high == range_build_year:
                build_year = random.randint(1995, specified_build_year_end)
            else:
                build_year = random.randint(1995, 2001)

        elif range_build_year == 9:
            if range_build_year_low == range_build_year:
                build_year = random.randint(specified_build_year_beginning, int(time.strftime("%Y")))
            elif range_build_year_high == range_build_year:
                build_year = random.randint(2002, specified_build_year_end)
            else:
                build_year = random.randint(2002, 2008)

        elif range_build_year == 10:
            if range_build_year_low == range_build_year:
                build_year = random.randint(specified_build_year_beginning, int(time.strftime("%Y")))
            elif range_build_year_high == range_build_year:
                build_year = random.randint(2009, specified_build_year_end)
            else:
                build_year = random.randint(2009, int(time.strftime("%Y")))

    return build_year, height_of_floors, cellar, attic, dormer


def get_build_year_non_res():

    '''
    Function to identify the build year for Single Familiy Houses regarding their frequency in general in Germany.
    Gives further information about the height of floors is related to the height of Multi Family Houses.

    frequency distribution of non residential buildings based on table 1 of "Typologische Kenngrößen von Nichtwohngebäuden im Bestand" of the IWU


    :return: build_year, height_of_floors
    '''
    range_build_year = numpy.random.choice(numpy.arange(1, 7),
                                           p=[0.1075, 0.054, 0.4086, 0.2793, 0.0753, 0.0753])

    if range_build_year == 1:
        build_year = random.randint(1890, 1919)
        height_of_floors = 3  # --> same as in MFH, because not found for non res

    elif range_build_year == 2:
        build_year = random.randint(1919, 1948)
        height_of_floors = 2.8

    elif range_build_year == 3:
        build_year = random.randint(1949, 1977)
        height_of_floors = 2.65

    elif range_build_year == 4:
        build_year = random.randint(1978, 1994)
        height_of_floors = 2.75

    elif range_build_year == 5:
        build_year = random.randint(1995, 2001)
        height_of_floors = 2.71

    elif range_build_year == 6:
        build_year = random.randint(2002, int(time.strftime("%Y")))
        height_of_floors = 2.5

    return build_year, height_of_floors


def get_building_information_based_on_build_year(building, specified_build_year_beginning, specified_build_year_end, build_year_buildings, floor_height_buildings, cellar_buildings, attic_buildings, dormer_buildings, single_family_house, double_houses, terraced_houses, multi_family_houses, commercial, individual_buildings, high_rise_houses):
    '''
    Gets build year and parameter, which are based on the build year (celler,attic,dormer,height of floors) for the
    right building type (SFH, MFH, Non residential).

    :param building:
    :param specified_build_year_beginning:
    :param specified_build_year_end:
    :param build_year_buildings:
    :param floor_height_buildings:
    :param cellar_buildings:
    :param attic_buildings:
    :param dormer_buildings:
    :param single_family_house:
    :param double_houses:
    :param terraced_houses:
    :param multi_family_houses:
    :param commercial:
    :param individual_buildings:
    :param high_rise_houses:

    :return: build_year, height_of_floors, cellar, attic, dormer
    '''

    if building in single_family_house:

        build_year, height_of_floors, cellar, attic, dormer = get_build_year_sfh_user_defined(
            building_id=building, terraced_houses=terraced_houses, double_houses=double_houses,
            specified_build_year_beginning=specified_build_year_beginning,
            specified_build_year_end=specified_build_year_end)

    else:

        build_year, height_of_floors, cellar, attic, dormer = get_build_year_mfh_user_defined(
            building_id=building, high_rise_houses=high_rise_houses,
            specified_build_year_beginning=specified_build_year_beginning,
            specified_build_year_end=specified_build_year_end)

        # if it is not a residential building, the building gets a build year with the distribution of the MFH
        if building in commercial and building in individual_buildings:
            cellar = None
            attic = None
            dormer = None

    return build_year, height_of_floors, cellar, attic, dormer


def get_relation_build_year(ref_building, stop_code, building_list_within_spezified_square, build_year_buildings,
                            buildings_neighbours, near_by_buildings_with_same_area, double_houses,
                            floor_height_buildings, cellar_buildings, attic_buildings, dormer_buildings,
                            total_ref_year, single_family_house, terraced_houses, multi_family_houses, commercial, individual_buildings,
                            nodelist_build_year, high_rise_houses):
    '''
    Function states the way to get the build year depending on the build type and the relations of the buildings

    1. checks of terrace or double house --> build year is the same as ref year
    2. checks if building with same area --> build year +/- 1 years
    3. checks buildings within the squared area --> build year +/- 5 years
    4. checks relations  between the buildings within the squared area

    :param ref_building:
    :param stop_code:
    :param building_list_within_spezified_square:
    :param build_year_buildings:
    :param buildings_neighbours:
    :param near_by_buildings_with_same_area:
    :param double_houses:
    :param floor_height_buildings:
    :param cellar_buildings:
    :param attic_buildings:
    :param dormer_buildings:
    :param total_ref_year:
    :param single_family_house:
    :param terraced_houses:
    :param multi_family_houses:
    :param commercial:
    :param individual_buildings:
    :param nodelist_build_year:
    :param high_rise_houses:

    :return: build_year_buildings, floor_height_buildings, cellar_buildings, attic_buildings, dormer_buildings
    '''

    while ref_building != stop_code:

        for building_within_square in building_list_within_spezified_square[ref_building]:

            if building_within_square != ref_building:

                if ref_building in double_houses:
                    build_year_buildings[buildings_neighbours[ref_building][0]] = build_year_buildings[ref_building]
                    floor_height_buildings[buildings_neighbours[ref_building][0]] = floor_height_buildings[ref_building]
                    cellar_buildings[buildings_neighbours[ref_building][0]] = cellar_buildings[ref_building]
                    attic_buildings[buildings_neighbours[ref_building][0]] = attic_buildings[ref_building]
                    dormer_buildings[buildings_neighbours[ref_building][0]] = dormer_buildings[ref_building]

                elif ref_building in terraced_houses:
                    for neighbour in buildings_neighbours[ref_building]:

                        build_year_buildings[neighbour] = build_year_buildings[ref_building]
                        floor_height_buildings[neighbour] = floor_height_buildings[
                            ref_building]
                        cellar_buildings[neighbour] = cellar_buildings[ref_building]
                        attic_buildings[neighbour] = attic_buildings[ref_building]
                        dormer_buildings[neighbour] = dormer_buildings[ref_building]


                # if build year for the buildings within the square is not already given
                if build_year_buildings[building_within_square] == []:

                    # if building within the square has almost the same area as the ref building
                    if building_within_square in near_by_buildings_with_same_area[ref_building]:

                        # if it is a double or terraced house
                        if (building_within_square in double_houses or building_within_square in terraced_houses): #and buildings_neighbours[building_within_square] == [ref_building]:
                            build_year_buildings[building_within_square] = build_year_buildings[ref_building]
                            floor_height_buildings[building_within_square] = floor_height_buildings[ref_building]
                            cellar_buildings[building_within_square] = cellar_buildings[ref_building]
                            attic_buildings[building_within_square] = attic_buildings[ref_building]
                            dormer_buildings[building_within_square] = dormer_buildings[ref_building]

                        # if it is not a double or terraced house
                        else:
                            build_year_buildings[building_within_square] = min(
                                (build_year_buildings[ref_building] + random.randint(-1, 1)),
                                int(time.strftime("%Y")))

                            specified_build_year_beginning = build_year_buildings[building_within_square]
                            specified_build_year_end = build_year_buildings[building_within_square]

                            build_year, height_of_floors, cellar, attic, dormer = get_building_information_based_on_build_year(building= building_within_square, specified_build_year_beginning=specified_build_year_beginning,
                                                                             specified_build_year_end=specified_build_year_end,
                                                                             build_year_buildings=build_year_buildings,
                                                                             floor_height_buildings=floor_height_buildings, cellar_buildings=cellar_buildings,
                                                                             attic_buildings=attic_buildings, dormer_buildings=dormer_buildings,
                                                                             single_family_house=single_family_house, double_houses=double_houses,
                                                                             terraced_houses=terraced_houses, multi_family_houses=multi_family_houses,
                                                                             commercial=commercial, individual_buildings=individual_buildings,
                                                                             high_rise_houses=high_rise_houses)
                            build_year_buildings[building_within_square] = build_year
                            floor_height_buildings[building_within_square] = height_of_floors
                            cellar_buildings[building_within_square] = cellar
                            attic_buildings[building_within_square] = attic
                            dormer_buildings[building_within_square] = dormer


                    # if it the building has not the same area as the ref building
                    elif building_within_square not in near_by_buildings_with_same_area[ref_building]:

                        specified_build_year_beginning = total_ref_year - 5
                        specified_build_year_end = min((total_ref_year + 5), int(time.strftime("%Y")))

                        build_year, height_of_floors, cellar, attic, dormer = get_building_information_based_on_build_year(
                            building=building_within_square,
                            specified_build_year_beginning=specified_build_year_beginning,
                            specified_build_year_end=specified_build_year_end,
                            build_year_buildings=build_year_buildings,
                            floor_height_buildings=floor_height_buildings, cellar_buildings=cellar_buildings,
                            attic_buildings=attic_buildings, dormer_buildings=dormer_buildings,
                            single_family_house=single_family_house, double_houses=double_houses,
                            terraced_houses=terraced_houses, multi_family_houses=multi_family_houses,
                            commercial=commercial, individual_buildings=individual_buildings,
                            high_rise_houses=high_rise_houses)

                        build_year_buildings[building_within_square] = build_year
                        floor_height_buildings[building_within_square] = height_of_floors
                        cellar_buildings[building_within_square] = cellar
                        attic_buildings[building_within_square] = attic
                        dormer_buildings[building_within_square] = dormer

                        # Checks if building within the square, which does not have the same area as the ref building, has a building with the almost same area
                        if near_by_buildings_with_same_area[building_within_square] != 0:
                            for i in near_by_buildings_with_same_area[building_within_square]:
                                if i in double_houses and buildings_neighbours[i] == [building_within_square]:
                                    build_year_buildings[i] = build_year_buildings[building_within_square]
                                    floor_height_buildings[i] = floor_height_buildings[building_within_square]
                                    cellar_buildings[i] = cellar_buildings[building_within_square]
                                    attic_buildings[i] = attic_buildings[building_within_square]
                                    dormer_buildings[i] = dormer_buildings[building_within_square]

                                else:
                                    build_year_buildings[i] = min(
                                        (build_year_buildings[building_within_square] + random.randint(-1, 1)),
                                        int(time.strftime("%Y")))

                                    specified_build_year_beginning = build_year_buildings[i]
                                    specified_build_year_end = build_year_buildings[i]

                                    build_year, height_of_floors, cellar, attic, dormer = get_building_information_based_on_build_year(
                                        building=i,
                                        specified_build_year_beginning=specified_build_year_beginning,
                                        specified_build_year_end=specified_build_year_end,
                                        build_year_buildings=build_year_buildings,
                                        floor_height_buildings=floor_height_buildings,
                                        cellar_buildings=cellar_buildings,
                                        attic_buildings=attic_buildings, dormer_buildings=dormer_buildings,
                                        single_family_house=single_family_house, double_houses=double_houses,
                                        terraced_houses=terraced_houses, multi_family_houses=multi_family_houses,
                                        commercial=commercial, individual_buildings=individual_buildings,
                                        high_rise_houses=high_rise_houses)

                                    build_year_buildings[i] = build_year
                                    floor_height_buildings[i] = height_of_floors
                                    cellar_buildings[i] = cellar
                                    attic_buildings[i] = attic
                                    dormer_buildings[i] = dormer

                # If building within square already has a build year
                else:

                    # check if there are other buildings with the same area in the square
                    if building_within_square in double_houses and build_year_buildings[buildings_neighbours[building_within_square][0]] != build_year_buildings[building_within_square]:
                        build_year_buildings[buildings_neighbours[building_within_square][0]] = build_year_buildings[building_within_square]
                        floor_height_buildings[buildings_neighbours[building_within_square][0]] = floor_height_buildings[building_within_square]
                        cellar_buildings[buildings_neighbours[building_within_square][0]] = cellar_buildings[building_within_square]
                        attic_buildings[buildings_neighbours[building_within_square][0]] = attic_buildings[building_within_square]
                        dormer_buildings[buildings_neighbours[building_within_square][0]] = dormer_buildings[building_within_square]


                    elif building_within_square in terraced_houses:
                        for i in buildings_neighbours[building_within_square]:
                            if build_year_buildings[i] != build_year_buildings[building_within_square]:
                                build_year_buildings[i] = build_year_buildings[building_within_square]
                                if len(buildings_neighbours[i]) == 2:
                                    for j in buildings_neighbours[i]:
                                        build_year_buildings[j] = build_year_buildings[building_within_square]



                    if near_by_buildings_with_same_area[building_within_square] != []:
                        for i in near_by_buildings_with_same_area[building_within_square]:

                            if i in double_houses or i in terraced_houses:
                                build_year_buildings[i] = build_year_buildings[building_within_square]
                                floor_height_buildings[i] = floor_height_buildings[building_within_square]
                                cellar_buildings[i] = cellar_buildings[building_within_square]
                                attic_buildings[i] = attic_buildings[building_within_square]
                                dormer_buildings[i] = dormer_buildings[building_within_square]

                            elif (build_year_buildings[ref_building] - 1) > build_year_buildings[building_within_square] or \
                                            build_year_buildings[building_within_square] > (
                                        build_year_buildings[ref_building] + 1):
                                build_year_buildings[building_within_square] = min(
                                    (build_year_buildings[ref_building] + random.randint(-1, 1)),
                                    int(time.strftime("%Y")))
                                floor_height_buildings[building_within_square] = floor_height_buildings[ref_building]
                                cellar_buildings[building_within_square] = cellar_buildings[ref_building]
                                attic_buildings[building_within_square] = attic_buildings[ref_building]
                                dormer_buildings[building_within_square] = dormer_buildings[ref_building]

            else:
                pass

        nodelist_build_year.remove(ref_building)

        if nodelist_build_year != []:
            for i in range(0, len(building_list_within_spezified_square[ref_building])):
                # has to be bigger than 1, because if it is 1 the only building within the square
                # is the ref_building and we are looking for a new one.
                if len(building_list_within_spezified_square[building_list_within_spezified_square[ref_building][
                    i]]) != 1 and i in nodelist_build_year:
                    ref_building = i

                    break
                else:
                    ref_building = 0

                break
        else:
            break
        break

    return build_year_buildings, floor_height_buildings, cellar_buildings, attic_buildings, dormer_buildings


def get_mod_year(user_defined_mod_year, mod_year_method, build_year, specified_range_mod_year_beginning, specified_range_mod_year_end, range_of_mod_years):
    '''
    Get mod year, either automatically or with the user defined information.
    If it is user defined it can be choosen between the first and second method.

    :param build_year:                          int         build year of certain building
    :param user_defined_mod_year:               boolean                     True: user defines the mod year  ; False: automatic determination
    :param specified_range_mod_year_beginning:  int                         beginning of the range for modifaction after the build year
    :param specified_range_mod_year_end:        int                         end of the range for modifaction after the build year
    :param mod_year_method:                     int                         decides which method is used for the identification of the mod year; fixed ranges (0) or a list of modifiaction years
    :param range_of_mod_years:                  list                        list of mod years (method 1)

    :return: mod_year
    '''
    # Data input regarding the mod year are based on "Entwicklung und energetische Bewertung alternativer Sanierungsfahrpläne" of the Fraunhofer-Institut für Bauphysik (IBP)

    if user_defined_mod_year == False or (user_defined_mod_year == True and mod_year_method == 1):

        if user_defined_mod_year == False:
            # approx mod years after the build year due to the change of installation engineering, windows and material of walls
            mod_years = [30, 36, 50, 60, 72, 90, 100, 108, 120, 144, 150]

        elif user_defined_mod_year == True:
            mod_years = range_of_mod_years

        if int(build_year + mod_years[0]) <= int(time.strftime("%Y")):
            if int(build_year + mod_years[0]) >= int(int(time.strftime("%Y")) - mod_years[0]):
                mod_year = min(int(build_year + mod_years[0] + random.randint(-3,3)), int(time.strftime("%Y")))
            elif int(build_year + mod_years[0]) <= int(int(time.strftime("%Y")) - mod_years[0]):
                if int(build_year + mod_years[1]) >= int(int(time.strftime("%Y")) - mod_years[0]):
                    mod_year = min(int(build_year + mod_years[1] + random.randint(-3,3)), int(time.strftime("%Y")))
                elif int(build_year + mod_years[1]) <= int(int(time.strftime("%Y")) - mod_years[0]):
                    if int(build_year + mod_years[2]) >= int(int(time.strftime("%Y")) - mod_years[0]):
                        mod_year = min(int(build_year + mod_years[2] + random.randint(-3,3)), int(time.strftime("%Y")))
                    elif int(build_year + mod_years[2]) <= int(int(time.strftime("%Y")) - mod_years[0]):
                        if int(build_year + mod_years[3]) >= int(int(time.strftime("%Y")) - mod_years[0]):
                            mod_year = min(int(build_year + mod_years[3] + random.randint(-3,3)), int(time.strftime("%Y")))
                        elif int(build_year + mod_years[3]) <= int(int(time.strftime("%Y")) - mod_years[0]):
                            if int(build_year + mod_years[4]) >= int(int(time.strftime("%Y")) - mod_years[0]):
                                mod_year = min(int(build_year + mod_years[4] + random.randint(-3,3)), int(time.strftime("%Y")))
                            elif int(build_year + mod_years[4]) <= int(int(time.strftime("%Y")) - mod_years[0]):
                                if int(build_year + mod_years[5]) >= int(int(time.strftime("%Y")) - mod_years[0]):
                                    mod_year = min(int(build_year + mod_years[5] + random.randint(-3,3)), int(time.strftime("%Y")))
                                elif int(build_year + mod_years[5]) <= int(int(time.strftime("%Y")) - mod_years[0]):
                                    if int(build_year + mod_years[6]) >= int(int(time.strftime("%Y")) - mod_years[0]):
                                        mod_year = min(int(build_year + mod_years[6] + random.randint(-3,3)), int(time.strftime("%Y")))
                                    elif int(build_year + mod_years[6]) <= int(int(time.strftime("%Y")) - mod_years[0]):
                                        if int(build_year + mod_years[7]) >= int(int(time.strftime("%Y")) - mod_years[0]):
                                            mod_year = min(int(build_year + mod_years[7] + random.randint(-3,3)), int(time.strftime("%Y")))
                                        elif int(build_year + mod_years[7]) <= int(int(time.strftime("%Y")) - mod_years[0]):
                                            if int(build_year + mod_years[8]) >= int(int(time.strftime("%Y")) - mod_years[0]):
                                                mod_year = min(int(build_year + mod_years[8] + random.randint(-3, 3)),int(time.strftime("%Y")))
                                            elif int(build_year + mod_years[8]) <= int(int(time.strftime("%Y")) - mod_years[0]):
                                                if int(build_year + mod_years[9]) >= int(int(time.strftime("%Y")) - mod_years[0]):
                                                    mod_year = min(int(build_year + mod_years[9] + random.randint(-3, 3)),int(time.strftime("%Y")))
                                                elif int(build_year + mod_years[9]) >= int(int(time.strftime("%Y")) - mod_years[0]):
                                                    mod_year = min(int(build_year + mod_years[10] + random.randint(-3,3)), int(time.strftime("%Y")))
        else:
            mod_year = None

    elif user_defined_mod_year == True and mod_year_method == 0:

        year_for_mod_1 = random.randint(specified_range_mod_year_beginning, specified_range_mod_year_end)
        year_for_mod_2 = random.randint(specified_range_mod_year_beginning, specified_range_mod_year_end)
        year_for_mod_3 = random.randint(specified_range_mod_year_beginning, specified_range_mod_year_end)
        year_for_mod_4 = random.randint(specified_range_mod_year_beginning, specified_range_mod_year_end)

        if int(build_year + year_for_mod_1) <= int(time.strftime("%Y")):
            if int(build_year + year_for_mod_1) >= int(int(time.strftime("%Y")) - year_for_mod_1):
                mod_year = build_year + year_for_mod_1
            elif int(build_year + year_for_mod_1) <= int(int(time.strftime("%Y")) - year_for_mod_1):
                if int(build_year + year_for_mod_1 + year_for_mod_2) >= int(
                                int(time.strftime("%Y")) - year_for_mod_1):
                    mod_year = build_year + year_for_mod_1 + year_for_mod_2
                elif int(build_year + year_for_mod_1 + year_for_mod_2) <= int(
                                int(time.strftime("%Y")) - year_for_mod_1):
                    if int(build_year + year_for_mod_1 + year_for_mod_2 + year_for_mod_3) >= int(
                                    int(time.strftime("%Y")) - year_for_mod_1):
                        mod_year = build_year + year_for_mod_1 + year_for_mod_2 + year_for_mod_3
                    else:
                        mod_year = build_year + year_for_mod_1 + year_for_mod_2 + year_for_mod_3 + year_for_mod_4
        else:
            mod_year = None

    return mod_year


def get_retrofit_state_sfh(build_year, user_defined_mod_year,
                                    specified_range_mod_year_beginning,
                                    specified_range_mod_year_end, mod_year_method, range_of_mod_years, forced_modification, forced_modification_after):

    """
    Mod year and grade of renovation based on "ARGE_Kiel_Wohnungsbau_in_Deutschland" till 2008
    adapted the data from 2008 to the current year
    Differation between "not renovated", "slightly renovated" and "medium till mainly renovated"

   Modification year and renovation status based on ARGE.

    :param build_year:                          int                         build year of certain building
    :param user_defined_mod_year:               boolean                     True: user defines the mod year  ; False: automatic determination
    :param specified_range_mod_year_beginning:  int                         beginning of the range for modifaction after the build year
    :param specified_range_mod_year_end:        int                         end of the range for modifaction after the build year
    :param mod_year_method:                     int                         decides which method is used for the identification of the mod year; fixed ranges (0) or a list of modifiaction years
    :param range_of_mod_years:                  list                        list of mod years (method 1)
    :param forced_modification:                 boolean                     True: a kind of modification has to be done after the fixed time
    :param forced_modification_after:           int                         fixed time for modification


    :return: mod_year, retrofit_state for certain building (of the building id)
    """

    # Build year 90 years ago and more
    if build_year < (int(time.strftime("%Y")) - 89):

        if forced_modification == True and build_year < ((int(time.strftime("%Y")) - forced_modification_after)):
            retrofit_state = numpy.random.choice(numpy.arange(0, 2),
                                                 p=[0.34, 0.66])
        else:
            retrofit_state = numpy.random.choice(numpy.arange(0, 3),
                                                 p=[0.33, 0.64,
                                                      0.03])

        if retrofit_state == 0 or retrofit_state == 1:
            mod_year = get_mod_year(user_defined_mod_year=user_defined_mod_year, mod_year_method=mod_year_method,
                                    build_year=build_year, \
                                    specified_range_mod_year_beginning=specified_range_mod_year_beginning,
                                    specified_range_mod_year_end=specified_range_mod_year_end, range_of_mod_years=range_of_mod_years)
        else:
            mod_year = None

    ## Build year from 60 to 89 years ago
    elif (int(time.strftime("%Y")) - 60) >= build_year >= (int(time.strftime("%Y")) - 89):

        if forced_modification == True and build_year < ((int(time.strftime("%Y")) - forced_modification_after)):
            retrofit_state = numpy.random.choice(numpy.arange(0, 2),
                                                 p=[0.326, 0.674])
        else:
            retrofit_state = numpy.random.choice(numpy.arange(0, 3),
                                                    p=[0.31, 0.67,
                                                       0.02])
        if retrofit_state == 0 or retrofit_state == 1:
            mod_year = get_mod_year(user_defined_mod_year=user_defined_mod_year, mod_year_method=mod_year_method,
                                    build_year=build_year, \
                                    specified_range_mod_year_beginning=specified_range_mod_year_beginning,
                                    specified_range_mod_year_end=specified_range_mod_year_end, range_of_mod_years=range_of_mod_years)
        else:
            mod_year = None

    # Build year from 50 to 59 years ago
    elif (int(time.strftime("%Y")) - 50) >= build_year >= (int(time.strftime("%Y")) - 59):

        if forced_modification == True and build_year < ((int(time.strftime("%Y")) - forced_modification_after)):
            retrofit_state = numpy.random.choice(numpy.arange(0, 2),
                                                 p=[0.25, 0.75])
        else:
            retrofit_state = numpy.random.choice(numpy.arange(0, 3),
                                                p=[0.24, 0.73,
                                                   0.03])
        if retrofit_state == 0 or retrofit_state == 1:
            mod_year = get_mod_year(user_defined_mod_year=user_defined_mod_year, mod_year_method=mod_year_method,
                                    build_year=build_year, \
                                    specified_range_mod_year_beginning=specified_range_mod_year_beginning,
                                    specified_range_mod_year_end=specified_range_mod_year_end, range_of_mod_years=range_of_mod_years)
        else:
            mod_year = None

    # Build year from 40 to 49 years ago
    elif (int(time.strftime("%Y")) - 40) >= build_year >= (int(time.strftime("%Y")) - 49):

        if forced_modification == True and build_year < ((int(time.strftime("%Y")) - forced_modification_after)):
            retrofit_state = numpy.random.choice(numpy.arange(0, 2),
                                                 p=[0.22, 0.78])
        else:
            retrofit_state = numpy.random.choice(numpy.arange(0, 3),
                                                p=[0.21, 0.74,
                                                   0.05])
        if retrofit_state == 0 or retrofit_state == 1:
            mod_year = get_mod_year(user_defined_mod_year=user_defined_mod_year, mod_year_method=mod_year_method,
                                    build_year=build_year, \
                                    specified_range_mod_year_beginning=specified_range_mod_year_beginning,
                                    specified_range_mod_year_end=specified_range_mod_year_end, range_of_mod_years=range_of_mod_years)

        else:
            mod_year = None

    # Build year from 30 to 39 years ago
    elif (int(time.strftime("%Y")) - 30) >= build_year >= (int(time.strftime("%Y")) - 39):

        if forced_modification == True and build_year < ((int(time.strftime("%Y")) - forced_modification_after)):
            retrofit_state = numpy.random.choice(numpy.arange(0, 2),
                                                 p=[0.17, 0.83])
        else:
            retrofit_state = numpy.random.choice(numpy.arange(0, 3),
                                                p=[0.15, 0.74,
                                                   0.11])
        if retrofit_state == 0 or retrofit_state == 1:
            mod_year = get_mod_year(user_defined_mod_year=user_defined_mod_year, mod_year_method=mod_year_method,
                                    build_year=build_year, \
                                    specified_range_mod_year_beginning=specified_range_mod_year_beginning,
                                    specified_range_mod_year_end=specified_range_mod_year_end, range_of_mod_years=range_of_mod_years)

        else:
            mod_year = None

    # Build year from 21 to 29 years ago
    elif (int(time.strftime("%Y")) - 21) >= build_year >= (int(time.strftime("%Y")) - 29):

        if forced_modification == True and build_year < ((int(time.strftime("%Y")) - forced_modification_after)):
            retrofit_state = numpy.random.choice(numpy.arange(0, 2),
                                                 p=[0.10, 0.90])
        else:
            retrofit_state = numpy.random.choice(numpy.arange(0, 3),
                                                p=[0.07, 0.64,
                                                   0.29])
        if retrofit_state == 0 or retrofit_state == 1:
            mod_year = random.randint((build_year+1), (int(time.strftime("%Y"))))
        else:
            mod_year = None

    # Build year from 15 to 20 years ago
    elif (int(time.strftime("%Y")) - 15) >= build_year >= (int(time.strftime("%Y")) - 20):

        if forced_modification == True and build_year < ((int(time.strftime("%Y")) - forced_modification_after)):
            retrofit_state = numpy.random.choice(numpy.arange(0, 2),
                                                 p=[0.0625, 0.9375])
        else:
            retrofit_state = numpy.random.choice(numpy.arange(0, 3),
                                                p=[0.05, 0.75,
                                                   0.2])
        if retrofit_state == 0 or retrofit_state == 1:
            mod_year = random.randint((build_year+1), (int(time.strftime("%Y"))))
        else:
            mod_year = None

    # Build year from 7 to 14 years ago
    elif (int(time.strftime("%Y")) - 7) >= build_year >= (int(time.strftime("%Y")) - 14):

        if forced_modification == True and build_year < ((int(time.strftime("%Y")) - forced_modification_after)):
            retrofit_state = 1
        else:
            retrofit_state = numpy.random.choice(numpy.arange(0, 3),
                                                p=[0.0, 0.15,
                                                   0.85])
        if retrofit_state == 1:
            mod_year = random.randint((build_year+1), (int(time.strftime("%Y"))))
        else:
            mod_year = None

    # Build year from now to 6 years ago
    elif (int(time.strftime("%Y")) - 6) <= build_year <= (int(time.strftime("%Y"))):

        if forced_modification == True and build_year < ((int(time.strftime("%Y")) - forced_modification_after)):
            retrofit_state = 1
        else:
            retrofit_state = numpy.random.choice(numpy.arange(0, 3),
                                                p=[0.0, 0.05,
                                                   0.95])
        if retrofit_state == 1:

            if build_year < ((int(time.strftime("%Y"))) - 1):
                mod_year = random.randint((build_year + 1), (int(time.strftime("%Y"))))
            else:
                mod_year = (int(time.strftime("%Y")))
        else:
            mod_year = None

    return mod_year, retrofit_state


def get_retrofit_state_mfh(build_year, user_defined_mod_year,
                                    specified_range_mod_year_beginning,
                                    specified_range_mod_year_end, mod_year_method, range_of_mod_years, forced_modification, forced_modification_after):

    """
    Modification year and renovation status based on ARGE.

    :param build_year:                          int         build year of certain building
    :param user_defined_mod_year:               boolean                     True: user defines the mod year  ; False: automatic determination
    :param specified_range_mod_year_beginning:  int                         beginning of the range for modifaction after the build year
    :param specified_range_mod_year_end:        int                         end of the range for modifaction after the build year
    :param mod_year_method:                     int                         decides which method is used for the identification of the mod year; fixed ranges (0) or a list of modifiaction years
    :param range_of_mod_years:                  list                        list of mod years (method 1)
    :param forced_modification:                 boolean                     True: a kind of modification has to be done after the fixed time
    :param forced_modification_after:           int                         fixed time for modification


    :return: mod_year, retrofit_state for certain building (of the building id)
    """

    # Build year 90 years ago and more
    if build_year < (int(time.strftime("%Y")) - 89):

        if forced_modification == True and build_year < ((int(time.strftime("%Y")) - forced_modification_after)):
            retrofit_state = numpy.random.choice(numpy.arange(0, 2),
                                                 p=[0.38, 0.62])
        else:
            retrofit_state = numpy.random.choice(numpy.arange(0, 3),
                                                p=[0.37, 0.61, 0.02])

        if retrofit_state == 0 or retrofit_state == 1:
            mod_year = get_mod_year(user_defined_mod_year=user_defined_mod_year, build_year=build_year, \
                                    specified_range_mod_year_beginning=specified_range_mod_year_beginning,
                                    specified_range_mod_year_end=specified_range_mod_year_end, mod_year_method=mod_year_method, range_of_mod_years=range_of_mod_years)
        else:
            mod_year = None

    ## Build year from 60 till 69 years ago
    elif (int(time.strftime("%Y")) - 60) >= build_year >= (int(time.strftime("%Y")) - 89):

        if forced_modification == True and build_year < ((int(time.strftime("%Y")) - forced_modification_after)):
            retrofit_state = numpy.random.choice(numpy.arange(0, 2),
                                                 p=[0.32, 0.68])
        else:
            retrofit_state = numpy.random.choice(numpy.arange(0, 3),
                                                p=[0.31, 0.67, 0.02])
        if retrofit_state == 0 or retrofit_state == 1:
            mod_year = get_mod_year(user_defined_mod_year=user_defined_mod_year, build_year=build_year, \
                                    specified_range_mod_year_beginning=specified_range_mod_year_beginning,
                                    specified_range_mod_year_end=specified_range_mod_year_end,
                                    mod_year_method=mod_year_method, range_of_mod_years=range_of_mod_years)

        else:
            mod_year = None

    # Build year from 50 till 59 years ago
    elif (int(time.strftime("%Y")) - 50) >= build_year >= (int(time.strftime("%Y")) - 59):

        if forced_modification == True and build_year < ((int(time.strftime("%Y")) - forced_modification_after)):
            retrofit_state = numpy.random.choice(numpy.arange(0, 2),
                                                 p=[0.34, 0.66])
        else:
            retrofit_state = numpy.random.choice(numpy.arange(0, 3),
                                                p=[0.33, 0.64, 0.03])
        if retrofit_state == 0 or retrofit_state == 1:
            mod_year = get_mod_year(user_defined_mod_year=user_defined_mod_year, build_year=build_year, \
                                    specified_range_mod_year_beginning=specified_range_mod_year_beginning,
                                    specified_range_mod_year_end=specified_range_mod_year_end,
                                    mod_year_method=mod_year_method, range_of_mod_years=range_of_mod_years)

        else:
            mod_year = None

    # Build year from 40 till 49 years ago
    elif (int(time.strftime("%Y")) - 40) >= build_year >= (int(time.strftime("%Y")) - 49):

        if forced_modification == True and build_year < ((int(time.strftime("%Y")) - forced_modification_after)):
            retrofit_state = numpy.random.choice(numpy.arange(0, 2),
                                                 p=[0.28, 0.72])
        else:
            retrofit_state = numpy.random.choice(numpy.arange(0, 3),
                                                p=[0.27, 0.69, 0.04])
        if retrofit_state == 0 or retrofit_state == 1:
            mod_year = get_mod_year(user_defined_mod_year=user_defined_mod_year, build_year=build_year, \
                                    specified_range_mod_year_beginning=specified_range_mod_year_beginning,
                                    specified_range_mod_year_end=specified_range_mod_year_end,
                                    mod_year_method=mod_year_method, range_of_mod_years=range_of_mod_years)

        else:
            mod_year = None

    # Build year from 30 till 39 years ago
    elif (int(time.strftime("%Y")) - 30) >= build_year >= (int(time.strftime("%Y")) - 39):

        if forced_modification == True and build_year < ((int(time.strftime("%Y")) - forced_modification_after)):
            retrofit_state = numpy.random.choice(numpy.arange(0, 2),
                                                 p=[0.18, 0.82])
        else:
            retrofit_state = numpy.random.choice(numpy.arange(0, 3),
                                                p=[0.16, 0.74, 0.10])
        if retrofit_state == 0 or retrofit_state == 1:
            mod_year = get_mod_year(user_defined_mod_year=user_defined_mod_year, build_year=build_year, \
                                    specified_range_mod_year_beginning=specified_range_mod_year_beginning,
                                    specified_range_mod_year_end=specified_range_mod_year_end,
                                    mod_year_method=mod_year_method, range_of_mod_years=range_of_mod_years)

        else:
            mod_year = None

    # Build year from 21 till 29 years ago
    elif (int(time.strftime("%Y")) - 21) >= build_year >= (int(time.strftime("%Y")) - 29):

        if forced_modification == True and build_year < ((int(time.strftime("%Y")) - forced_modification_after)):
            retrofit_state = numpy.random.choice(numpy.arange(0, 2),
                                                 p=[0.16, 0.84])
        else:
            retrofit_state = numpy.random.choice(numpy.arange(0, 3),
                                                p=[0.10, 0.54, 0.36])
        if retrofit_state == 0 or retrofit_state == 1:
            mod_year = random.randint((build_year+1), (int(time.strftime("%Y"))))
        else:
            mod_year = None

    # Build year from 15 till 20 years ago
    elif (int(time.strftime("%Y")) - 15) >= build_year >= (int(time.strftime("%Y")) - 20):

        if forced_modification == True and build_year < ((int(time.strftime("%Y")) - forced_modification_after)):
            retrofit_state = numpy.random.choice(numpy.arange(0, 2),
                                                 p=[0.25, 0.75])
        else:
            retrofit_state = numpy.random.choice(numpy.arange(0, 3),
                                                p=[0.07, 0.21, 0.72])
        if retrofit_state == 0 or retrofit_state == 1:
            mod_year = random.randint((build_year+1), (int(time.strftime("%Y"))))
        else:
            mod_year = None

    # Build year from 7 till 14 years ago
    elif (int(time.strftime("%Y")) - 7) >= build_year >= (int(time.strftime("%Y")) - 14):

        if forced_modification == True and build_year < ((int(time.strftime("%Y")) - forced_modification_after)):
            retrofit_state = 1
        else:
            retrofit_state = numpy.random.choice(numpy.arange(0, 3),
                                                p=[0.0, 0.12, 0.88])
        if retrofit_state == 1:
            mod_year = random.randint((build_year+1), (int(time.strftime("%Y"))))
        else:
            mod_year = None

    # Build year from now till 6 years ago
    elif (int(time.strftime("%Y")) - 6) <= build_year <= (int(time.strftime("%Y"))):

        if forced_modification == True and build_year < ((int(time.strftime("%Y")) - forced_modification_after)):
            retrofit_state = 1
        else:
            retrofit_state = numpy.random.choice(numpy.arange(0, 3),
                                                p=[0.0, 0.03, 0.97])
        if retrofit_state == 1:
            if build_year < ((int(time.strftime("%Y"))) - 1):
                mod_year = random.randint((build_year + 1), (int(time.strftime("%Y"))))
            else:
                mod_year =  (int(time.strftime("%Y")))
        else:
            mod_year = None

    return mod_year, retrofit_state


def get_nb_of_apartments_user_defined(user_defined_number_of_apartments, nodelist_buildings, area, specified_number_apartments, commercial, individual_buildings, list_nb_of_apartments, single_family_house, multi_family_houses, high_rise_houses):
    '''
        Function to get the number of apartments.

    If user_defined_number_of_apartments == True
    Randomly collects an apartment and  rises or lowers the nb of apartments, depending on the total number of apartments (user defined).

    :param user_defined_number_of_apartments:           boolean     True: User defined nb of occupants
    :param nodelist_buildings:                          list        nodelist of all relevant buildings
    :param area:                                        list       list of the areas of all buildings
    :param specified_number_apartments:                 int        nb of apartments given by the user
    :param commercial:                                  list
    :param individual_buildings:                        list
    :param list_nb_of_apartments:                       list
    :param single_family_house:                         list
    :param multi_family_houses:                         list
    :param high_rise_houses:                            list

    :return: enriched list_nb_of_apartments
    '''

    # Number of apartments user defined

    if user_defined_number_of_apartments == True:

        general_nb_apartments_per_building = specified_number_apartments / (len(nodelist_buildings) - len(commercial) - len(individual_buildings))

        if general_nb_apartments_per_building < 1:
            assert "Not enough apartments given for the number of residential buildings"
        elif general_nb_apartments_per_building == 1:
            for building_id in nodelist_buildings:
                if building_id not in commercial and building_id not in individual_buildings:
                    list_nb_of_apartments[building_id] = 1
                else:
                    list_nb_of_apartments[building_id] = 0
        elif general_nb_apartments_per_building >= 1:
            for building_id in nodelist_buildings:
                if building_id in single_family_house:
                    jchv = multi_family_houses
                    if multi_family_houses != []:
                        list_nb_of_apartments[building_id] = 1
                    else:


                        nb_of_sfh_with_one_apartment = (len(single_family_house) * 2) - specified_number_apartments

                        biggest_ground_area_of_sfh_with_one_apartment = sorted(area.values())[
                            nb_of_sfh_with_one_apartment - 1]

                        if area[building_id] <= biggest_ground_area_of_sfh_with_one_apartment:
                            list_nb_of_apartments[building_id] = 1
                        else:
                            list_nb_of_apartments[building_id] = 2

                elif building_id in multi_family_houses:

                    nb_of_apartments_for_mfh = specified_number_apartments - len(single_family_house)

                    nb_res_per_nb_mfh = (len(multi_family_houses) - len(high_rise_houses)) / len(multi_family_houses)
                    nb_high_rise_per_nb_mfh = len(high_rise_houses) * 5 / len(
                        multi_family_houses)  # --> 5 is the factor, because a high building fits usually around 5 times more apartments than a MFH in the country sideor the city.

                    nb_apartments_in_res_district = nb_res_per_nb_mfh * nb_of_apartments_for_mfh
                    assert (nb_apartments_in_res_district / nb_of_apartments_for_mfh) < 30, "Too many apartments for MFH"

                    nb_apartments_in_high_rise_district = nb_high_rise_per_nb_mfh * nb_of_apartments_for_mfh
                    assert (nb_apartments_in_high_rise_district ) < 110, "Too many apartments for high rise buildings"

                    total_ground_area_high_rise = 0
                    for i in high_rise_houses:
                        total_ground_area_high_rise += area[i]

                    total_ground_area_mfh_without_high_rise = 0
                    for i in multi_family_houses:
                        total_ground_area_mfh_without_high_rise += area[i]

                    if building_id in high_rise_houses:
                        list_nb_of_apartments[building_id] = round(
                            area[building_id] / total_ground_area_high_rise * nb_apartments_in_high_rise_district)

                    if building_id in multi_family_houses and building_id not in high_rise_houses:
                        list_nb_of_apartments[building_id] = round(
                            area[building_id] / total_ground_area_mfh_without_high_rise * nb_apartments_in_res_district)

    return list_nb_of_apartments


def get_nb_of_occupants(city, building_id, list_nb_of_floors, list_nb_of_apartments, dict_nb_of_apartments_with_occupants):
    """
    Statistic of the Zensus2011 on page 20
    Nb of occupants depends on the living area of the dwelling.

    :param city:                                    str         city-object
    :param building_id:                             int         specific building
    :param list_nb_of_floors:                       list        nb of floors for every building
    :param list_nb_of_apartments:                   list        nb of apartments for every building
    :param dict_nb_of_apartments_with_occupants:    dict        nb of occupants for every apartments

    :return: enriched dict_nb_of_apartments_with_occupants
    """

    medium_net_area_of_apartment = 0.812 * city.nodes[building_id]["area"] * list_nb_of_floors[building_id] / list_nb_of_apartments[building_id]

    for i in range(0, list_nb_of_apartments[building_id]):
        if list_nb_of_apartments[building_id] != 0:

            if medium_net_area_of_apartment < 40:
                dict_nb_of_apartments_with_occupants[building_id][i] = numpy.random.choice(numpy.arange
                                    (1, 6), p=[0.8914, 0.0851, 0.0154, 0.0057, 0.0024])
            elif 40 <= medium_net_area_of_apartment <= 60:
                dict_nb_of_apartments_with_occupants[building_id][i] = numpy.random.choice(numpy.arange
                                                                                           (1, 6),
                                                                                           p= [0.6943, 0.2401, 0.0448, 0.0150, 0.0058])
            elif 60 <= medium_net_area_of_apartment <= 80:
                dict_nb_of_apartments_with_occupants[building_id][i] = numpy.random.choice(numpy.arange
                                                                                           (1, 6),
                                                                                           p= [0.4182, 0.3796, 0.1264, 0.0548, 0.0210])
            elif 80 <= medium_net_area_of_apartment <= 100:
                dict_nb_of_apartments_with_occupants[building_id][i] = numpy.random.choice(numpy.arange
                                                                                           (1, 6),
                                                                                           p= [0.2838, 0.3913, 0.1724, 0.1058, 0.0467])
            elif 100 <= medium_net_area_of_apartment <= 120:
                dict_nb_of_apartments_with_occupants[building_id][i] = numpy.random.choice(numpy.arange
                                                                                           (1, 6),
                                                                                           p= [0.2040, 0.3891, 0.2002, 0.1464, 0.0603])
            elif 120 <= medium_net_area_of_apartment <= 140:
                dict_nb_of_apartments_with_occupants[building_id][i] = numpy.random.choice(numpy.arange
                                                                                           (1, 6),
                                                                                           p= [0.1529, 0.3573, 0.2177, 0.1929, 0.0792])
            elif 140 <= medium_net_area_of_apartment <= 160:
                dict_nb_of_apartments_with_occupants[building_id][i] = numpy.random.choice(numpy.arange
                                                                                           (1, 6),
                                                                                           p= [0.1285, 0.3314, 0.2185, 0.2192, 0.1024])
            elif 160 <= medium_net_area_of_apartment <= 180:
                dict_nb_of_apartments_with_occupants[building_id][i] = numpy.random.choice(numpy.arange
                                                                                           (1, 6),
                                                                                           p= [0.1171, 0.3049, 0.2160, 0.2372, 0.1248])
            elif 180 <= medium_net_area_of_apartment <= 200:
                dict_nb_of_apartments_with_occupants[building_id][i] = numpy.random.choice(numpy.arange
                                                                                           (1, 6),
                                                                                           p= [0.1116, 0.2928, 0.2115, 0.2389, 0.1452])
            elif 200 <= medium_net_area_of_apartment:
                dict_nb_of_apartments_with_occupants[building_id][i] = numpy.random.choice(numpy.arange
                                                                                           (1, 6),
                                                                                           p= [0.1110, 0.2722, 0.1990, 0.2334, 0.1844])
        else:
            dict_nb_of_apartments_with_occupants[building_id][i] = 0

    return dict_nb_of_apartments_with_occupants


def get_nb_of_occupants_user_defined(user_defined_number_of_occupants, specified_number_occupants, nodelist_buildings, building_id, dict_nb_of_apartments_with_occupants, list_nb_of_occupants, list_nb_of_apartments):
    """
    Function to get the number of occupants.

    If user_defined_number_of_occupants == True
    Randomly collects an apartment and if the number of occupants is below 5 and above 1 the number of occupants rises or gets lower, depending on the total number of occupants.

    :param user_defined_number_of_occupants:            boolean     True: User defined nb of occupants
    :param specified_number_occupants:                  int         number of occupants given by he user
    :param nodelist_buildings:                          list        nodelist of all relevant building
    :param building_id:                                 int         id of certain building
    :param dict_nb_of_apartments_with_occupants:        dict        dict with apartments and their occupants
    :param list_nb_of_occupants:                        list
    :param list_nb_of_apartments:                       list        nb of apartments for every building

    :return: enriched dict_nb_of_apartments_with_occupants
    """

    if user_defined_number_of_occupants == True:

        #apartments_with_occ = {key: {} for key in nodelist_buildings}

        counter_apartments = 0
        for apart in list_nb_of_apartments:
            counter_apartments += list_nb_of_apartments[apart]

        assert (specified_number_occupants / counter_apartments) <= 5

        if (specified_number_occupants / counter_apartments) == 5:
            for building_id in nodelist_buildings:
                for apart in range(0, list_nb_of_apartments[building_id]):
                    dict_nb_of_apartments_with_occupants[building_id][apart] = 5

        elif (specified_number_occupants / counter_apartments) == 1:
            for building_id in nodelist_buildings:
                for apart in range(0, list_nb_of_apartments[building_id]):
                    dict_nb_of_apartments_with_occupants[building_id][apart] = 1

        elif (specified_number_occupants / counter_apartments) < 1:
            apartments_with_1_occ = counter_apartments - specified_number_occupants
            apartment_with_0_occ = counter_apartments - apartments_with_1_occ

            apartments_wihout_occupants = []
            while len(apartments_wihout_occupants) < apartment_with_0_occ:
                apartment_without_occ = random.choice(nodelist_buildings)
                if list_nb_of_occupants[apartment_without_occ] == []:
                    for building_id in nodelist_buildings:
                        for apart in range(0, list_nb_of_apartments[building_id]):
                            dict_nb_of_apartments_with_occupants[building_id][apart] = 0
                            list_nb_of_occupants[apartment_without_occ] = 0
                            apartments_wihout_occupants.append[apartment_without_occ]

            for building_id in nodelist_buildings and building_id not in apartments_wihout_occupants:
                for apart in range(0, list_nb_of_apartments[building_id]):
                    dict_nb_of_apartments_with_occupants[building_id][apart] = 1

        elif 1 < (specified_number_occupants / counter_apartments) < 4:
            # numpy.random.dirichlet(numpy.ones(counter_apartments), size=specified_number_occupants, min = 0, max = 5)
            average = specified_number_occupants / counter_apartments
            percentage_lower_nb_of_occ = math.ceil(average) - average
            percentage_higher_nb_of_occ = 1 - percentage_lower_nb_of_occ

            higher_nb_of_occ = math.ceil(average)
            lower_nb_of_occ = math.ceil(average) - 1

            nb_of_apart_with_lower_nb_of_occ = round(counter_apartments * percentage_lower_nb_of_occ)
            nb_of_apart_with_higher_nb_of_occ = round(counter_apartments * percentage_higher_nb_of_occ)

            if (nb_of_apart_with_lower_nb_of_occ * lower_nb_of_occ + nb_of_apart_with_higher_nb_of_occ * higher_nb_of_occ) == specified_number_occupants:
                x = 0
            elif (nb_of_apart_with_lower_nb_of_occ * lower_nb_of_occ + nb_of_apart_with_higher_nb_of_occ * higher_nb_of_occ) < specified_number_occupants:
                x = specified_number_occupants - (nb_of_apart_with_lower_nb_of_occ * lower_nb_of_occ + nb_of_apart_with_higher_nb_of_occ * higher_nb_of_occ)

            counter_nb_of_apart_with_lower_nb_of_occ = nb_of_apart_with_lower_nb_of_occ

            for building_id in nodelist_buildings:
                if counter_nb_of_apart_with_lower_nb_of_occ > 0:
                    list_nb_of_occupants[building_id] = lower_nb_of_occ
                    for apart in range(0, list_nb_of_apartments[building_id]):
                        dict_nb_of_apartments_with_occupants[building_id][apart] = lower_nb_of_occ
                        counter_nb_of_apart_with_lower_nb_of_occ -= 1
                elif counter_nb_of_apart_with_lower_nb_of_occ <= 0:
                    for apart in range(0, list_nb_of_apartments[building_id]):
                        dict_nb_of_apartments_with_occupants[building_id][apart] = higher_nb_of_occ
                        list_nb_of_occupants[building_id] = higher_nb_of_occ


        elif 4 < (specified_number_occupants / counter_apartments) < 5:
            apartments_with_4_occ = (5 * counter_apartments) - specified_number_occupants
            apartment_with_5_occ = counter_apartments - apartments_with_4_occ

            apartments_five_occupants = []
            while len(apartments_five_occupants) < apartment_with_5_occ:
                apartment_5_occ = random.choice(nodelist_buildings)
                if list_nb_of_occupants[apartment_5_occ] == []:
                    list_nb_of_occupants[apartment_5_occ] = 5
                    apartments_five_occupants.append[random.choice(nodelist_buildings)]
                    for apart in range(0, list_nb_of_apartments[apartment_5_occ]):
                        dict_nb_of_apartments_with_occupants[apartment_5_occ][apart] = 5

            for building_id in nodelist_buildings and building_id not in apartments_five_occupants:
                list_nb_of_occupants[building_id] = 4
                for apart in range(0, list_nb_of_apartments[building_id]):
                    dict_nb_of_apartments_with_occupants[building_id][apart] = 4

    return dict_nb_of_apartments_with_occupants

#--------------------------------------------------------

def data_enrichment(city, osm_path, zone_number, min_house_area,  considered_area_around_a_building, user_defined_building_distribution, \
                    percentage_sfh, percentage_mfh, percentage_non_res, specific_buildings, user_defined_build_year,\
                    specified_build_year_beginning, specified_build_year_end, user_defined_mod_year, specified_range_mod_year_beginning,\
                    specified_range_mod_year_end, mod_year_method, range_of_mod_years, forced_modification, forced_modification_after,
                    user_defined_number_of_occupants ,specified_number_occupants, user_defined_number_of_apartments , specified_number_apartments, timestep, year, try_path, location, altitude, generate_nodelist_from_function_of_citydistrict, save_city_CSV, user_defined_el_demand, user_defined_therm_demand, user_defined_dhw):
    '''
    Main function for identification  the building type and to do the data enrichment.

    1. Identification of the building type
    2. Identification of district
    3. Deletion of non-relevant buildings
    4. Data enrichment for the Single Family Houses, Multi Family Houses and Non Residential buildings
        4.1 build year and the parameters which depend on the build year (height of floors, cellar, attic, dormer)
        4.2 nb. of apartments, occupants and floors
        4.3 setting of the environment
        4.4 mod_year and retrofit
        4.5 usable roof area for PV
        4.6 netto floor area
        4.7 residential layout

    :param city:                                str,                        city-object
    :param zone_number:                         int, default: 32            zone number is needed
    :param considered_area_around_buildings:    int, default: 10000 m^2     squared area around a building
    :param min_house_area                       int, default: 35            minimal area for a considered building
    :param osm_path:                            str                         path of osm
    :param user_defined_building_distribution:  boolean                     True: user defines the distribution; False: automatic distribution
    :param percentage_sfh:                      int                         percentage of Single Family Houses. In between 0 and 100.
    :param percentage_mfh:                      int                         percentage of Multi Family Houses. In between 0 and 100.
    :param percentage_non_res:                  int                         percentage of Non residential Houses. In between 0 and 100.
    :param specific_buildings:                  boolean
    :param user_defined_build_year:             boolean                     True: user defines the build year or range for the build year ; False: automatic determination
    :param specified_build_year_beginning:      int                         start year of the range for the build year
    :param specified_build_year_end:            int                         end year of the range for the build year
    :param user_defined_mod_year:               boolean                     True: user defines the mod year  ; False: automatic determination
    :param specified_range_mod_year_beginning:  int                         beginning of the range for modifaction after the build year
    :param specified_range_mod_year_end:        int                         end of the range for modifaction after the build year
    :param mod_year_method:                     int                         decides which method is used for the identification of the mod year; fixed ranges (0) or a list of modifiaction years
    :param range_of_mod_years:                  list                        list of mod years (method 1)
    :param forced_modification:                 boolean                     True: a kind of modification has to be done after the fixed time
    :param forced_modification_after:           int                         fixed time for modification
    :param user_defined_number_of_occupants:    boolean                     True: number of occupants are given by the user; False: automatic determination
    :param specified_number_occupants:          int                         number of occupants, if user_defined_number_of_occupants == True
    :param user_defined_number_of_apartments:   boolean                     True: number of apartments are given by the user; False: automatic determination
    :param specified_number_apartments:         int                         number of apartments, if user_defined_number_of_apartments == True

    :return: enriched city object
    '''

    # list of deleted buildings is needed for the identification of buildings with garages and these buildings have to be deleted from the city object afterwards
    deleted_buildings, nodelist_buildings = delete_not_relevant_buildings(city=city, min_house_area=min_house_area, generate_nodelist_from_function_of_citydistrict=generate_nodelist_from_function_of_citydistrict)


    addr_building_not_found, addr_building_found, area_building_not_found,house_nb_building_found, coordinates_from_buildings_without_adress, \
    buildings_not_found, street_names_of_all_buildings, street_names = get_lists(city=city, min_house_area=min_house_area, nodelist_buildings=nodelist_buildings)

    # Building attributes are needed to get the information from the OSM data
    buildings_with_comment, comments, apartment_buildings, house_buildings, residential_buildings, terrace_buildings, \
    detached_buildings, bungalow_buildings, dormitory_buildings, garages_and_roofs, \
    schools, universities, houses_of_prayer, hospitals, civic, public, commercial_buildings, \
    industrial_buildings, office_buildings, retail_buildings, warehouse_buildings, \
    residential, non_residential, special_building_types, buildings_with_shop, \
    buildings_with_amenity, buildings_with_name, buildings_with_levels, \
    buildings_with_roof_shape, buildings_buildyear, buildings_condition, buildings_height, buildings_without_parameters, buildings_with_leisure \
        = get_buildings_parameters(city=city, min_house_area=min_house_area, nodelist_buildings=nodelist_buildings, generate_nodelist_from_function_of_citydistrict=generate_nodelist_from_function_of_citydistrict)

     # get_buildings_within_spezified_square; useful for the comparision of the buildings within a square
    building_list_within_spezified_square, number_of_buildings_within_spezified_square = \
        get_buildings_within_spezified_square(city=city,zone_number=zone_number, considered_area=considered_area_around_a_building, min_house_area=min_house_area, nodelist_buildings=nodelist_buildings )

    # Neighbour buildings
    buildings_neighbours, number_neighbour_buildings, no_neigbours, one_neigbour, two_neigbours, more_than_two_neighbours, three_neigbours, \
    four_neigbours, five_neigbours, six_neigbours, more_than_six_neigbours, coordinates_of_shared_walls \
        = get_neighbour_building(city=city, min_house_area=min_house_area, zone_number=zone_number,
                                 considered_area_around_buildings=considered_area_around_a_building, nodelist_buildings=nodelist_buildings)

    # Correlation between buildings regarding area within a certain distance
    near_by_buildings_with_same_area = check_correlation_between_buildings(city=city, min_house_area=min_house_area, zone_number=zone_number,
                                                                           considered_area_around_buildings=considered_area_around_a_building, nodelist_buildings=nodelist_buildings)

    # get_shops_within_spezified_square
    shops_in_spezified_square, percentage_of_shops_to_houses = get_shops_within_spezified_square(
        city=city, min_house_area=min_house_area,  zone_number=zone_number, considered_area=considered_area_around_a_building, nodelist_buildings=nodelist_buildings, generate_nodelist_from_function_of_citydistrict=generate_nodelist_from_function_of_citydistrict)

    # get_district_type needed to identify the usage of the city district (residentail, city or non residential area)
    cropped_area_within_square, percentage_cropped_area_within_square, average_buildings_neighbours = \
        get_district_type(city=city, zone_number=zone_number, considered_area_around_building=considered_area_around_a_building, \
                          min_house_area= min_house_area, nodelist_buildings=nodelist_buildings)

    # Set building_parameters for CSV file

    building_parameters = ["id", "X", "Y", "building_type", "net_floor_area", "build_year", \
                           "mod_year", "retrofit_state", "building", \
                           "Usable_pv_roof_area_in_m2", "Number_of_apartments", "Total_number_of_occupants",
                           "Number_of_floors", \
                           "Height_of_floors", "with_ahu", "residential_layout", "neighbour_buildings", "attic",
                           "cellar", \
                           "dormer", "construction_type", "method_3_type", "method_4_type"]

    building_parameters_for_analysis = {key: {key: [] for key in building_parameters} for key in nodelist_buildings}

    # -------------------------------------------------------------------------


    # List for different building types

    # Individual buildings
    individual_buildings = []

    # SFH
    single_family_house = []

    detached_single_family_houses = []
    terraced_houses = []
    double_houses = []

    # MFH
    multi_family_houses = []
    high_rise_houses = []


    # Commerical building
    commercial = []
    commercial_hall = []
    commercial_office_building = []

    # Lists for the buildings with similar ground floor area within in block
    build_type_buildings = {key: [] for key in nodelist_buildings}
    build_year_buildings = {key: [] for key in nodelist_buildings}
    mod_year_buildings = {key: [] for key in nodelist_buildings}
    range_build_year_buildings = {key: [] for key in nodelist_buildings}
    list_nb_of_floors = {key: [] for key in nodelist_buildings}
    floor_height_buildings = {key: [] for key in nodelist_buildings}
    cellar_buildings = {key: [] for key in nodelist_buildings}
    attic_buildings = {key: [] for key in nodelist_buildings}
    dormer_buildings = {key: [] for key in nodelist_buildings}
    dict_nb_of_apartments_with_occupants = {key: {} for key in nodelist_buildings}
    list_nb_of_apartments = {key: [] for key in nodelist_buildings}
    list_nb_of_occupants = {key: [] for key in nodelist_buildings}

    # ----------------------------------------------------------------------

    # BUILDING TYPE IDENTIFICATION

    # DEF get_ground_area
    area = get_ground_area_of_building(city=city, min_house_area=min_house_area, nodelist_buildings=nodelist_buildings)

    # DEF get_buildings_with_garages
    building_with_garages = get_buildings_with_garages(city=city, zone_number=zone_number,
                                                       min_house_area=min_house_area,
                                                       deleted_buildings=deleted_buildings,
                                                       nodelist_buildings=nodelist_buildings)
    # DEF get_distances
    distance_buildings_within_square, min_distance_within_square = get_distances(city=city,
                                                                                 min_house_area=min_house_area,
                                                                                 zone_number=zone_number,
                                                                                 considered_area_around_buildings=considered_area_around_a_building,
                                                                                 nodelist_buildings=nodelist_buildings)

    for building_id in nodelist_buildings:


        # ----------------------------------------------------------------------

        # USER DEFINED BUILDING DISTRIBUTION  == FALSE

        if user_defined_building_distribution == False:

            #spezified_building = identification_of_specific_buildings()

            if (building_id) in schools:

                individual_buildings.append(building_id)

                # Spec_demand_non_res.xlsx --> found in PyCity_Calc/pycity_calc/data/BaseData/Specific_Demand_Data
                if building_id in buildings_with_name:
                    dict_schools = {"Grundschule": 16, "Gesamtschule": 16, "Behindertenschule": 17, "Realschule": 18, "Gymnasium": 18, "Berufsschule": 19}
                    for school in dict_schools.keys():
                        if school in city.nodes[building_id]["name"]:
                            individual_buildings.append(building_id)
                            build_type_buildings[building_id] = dict_schools[school]
                            continue
                        else:
                            build_type_buildings[building_id] = 16
                            continue
                else:
                    build_type_buildings[building_id] = 16
                    continue

            elif building_id in houses_of_prayer:

                individual_buildings.append(building_id)

                # Spec_demand_non_res.xlsx --> found in PyCity_Calc/pycity_calc/data/BaseData/Specific_Demand_Data
                # build_type ist not given for houses of prayer
                build_type_buildings[building_id] = None

                continue

            elif building_id in universities:

                individual_buildings.append(building_id)

                # Spec_demand_non_res.xlsx --> found in PyCity_Calc/pycity_calc/data/BaseData/Specific_Demand_Data
                # build_type = University
                build_type_buildings[building_id] = 20

                continue

            elif building_id in hospitals:
                individual_buildings.append(building_id)

                # Spec_demand_non_res.xlsx --> found in PyCity_Calc/pycity_calc/data/BaseData/Specific_Demand_Data
                # build_type = hospital
                build_type_buildings[building_id] = 32

                continue

            elif building_id in civic:
                individual_buildings.append(building_id)

                # Spec_demand_non_res.xlsx --> found in PyCity_Calc/pycity_calc/data/BaseData/Specific_Demand_Data
                # build_type =  public institution
                build_type_buildings[building_id] = 4
                continue

            elif building_id in public:
                individual_buildings.append(building_id)

                # Spec_demand_non_res.xlsx --> found in PyCity_Calc/pycity_calc/data/BaseData/Specific_Demand_Data
                # build_type =  public institution
                build_type_buildings[building_id] = 4
                continue

            elif building_id in residential:
                if building_id in apartment_buildings:
                    if building_id not in multi_family_houses:
                        multi_family_houses.append(building_id)
                elif building_id in residential_buildings:
                    if 30 < area[building_id] < 110:  # --> SFH
                        if building_id in no_neigbours:
                            single_family_house.append(building_id)
                            detached_single_family_houses.append(building_id)
                            continue
                        elif building_id in one_neigbour:
                            for i in range(0, len(buildings_neighbours[building_id])):
                                if (60 < area[buildings_neighbours[building_id][i]] < 110) and \
                                                buildings_neighbours[building_id][i] in one_neigbour:
                                    single_family_house.append(building_id)
                                    double_houses.append(building_id)
                                    continue
                            if buildings_neighbours[building_id][i] in two_neigbours:
                                single_family_house.append(building_id)
                                terraced_houses.append(building_id)
                                continue
                            elif building_id in two_neigbours:
                                single_family_house.append(building_id)
                                terraced_houses.append(building_id)
                                continue
                    else:  # --> MFH
                        if building_id not in multi_family_houses:
                            multi_family_houses.append(building_id)
                            continue

                elif building_id in bungalow_buildings:
                    single_family_house.append(building_id)
                    continue
                elif building_id in house_buildings:
                    if building_id in no_neigbours:
                        single_family_house.append(building_id)
                        detached_single_family_houses.append(building_id)
                        continue
                    elif building_id in one_neigbour:
                        for i in range(0, len(buildings_neighbours[building_id])):
                            if (60 < area[buildings_neighbours[building_id][i]] < 110) and \
                                            buildings_neighbours[building_id][i] in one_neigbour:
                                single_family_house.append(building_id)
                                double_houses.append(building_id)
                                continue
                            elif buildings_neighbours[building_id][i] in two_neigbours:
                                single_family_house.append(building_id)
                                terraced_houses.append(building_id)
                                continue
                            elif buildings_neighbours[building_id][i] in one_neigbour:
                                single_family_house.append(building_id)
                                double_houses.append(building_id)
                                continue
                    elif building_id in two_neigbours:
                        single_family_house.append(building_id)
                        terraced_houses.append(building_id)
                        continue

                elif building_id in detached_buildings:
                    single_family_house.append(building_id)
                    detached_single_family_houses.append(building_id)
                    continue
                elif building_id in terrace_buildings and (building_id in one_neigbour or building_id in two_neigbours):
                    if building_id in one_neigbour:
                        single_family_house.append(building_id)
                        terraced_houses.append(building_id)
                        continue
                    else:
                        single_family_house.append(building_id)
                        terraced_houses.append(building_id)
                        continue
                elif building_id in dormitory_buildings:
                    if building_id not in multi_family_houses:
                        multi_family_houses.append(building_id)
                        continue

            elif building_id in commercial_buildings:
                commercial.append(building_id)
                build_type_buildings[building_id] = 1

            elif building_id in industrial_buildings:
                individual_buildings.append(building_id)
                if building_id in buildings_with_name:
                    if "Metall" in city.nodes[building_id]["name"]:
                        build_type_buildings[building_id] = 8
                        continue
                    elif "KFZ" in city.nodes[building_id]["name"]:
                        build_type_buildings[building_id] = 9
                        continue
                    elif "Wood" in city.nodes[building_id]["name"] or "Holz" in city.nodes[building_id]["name"]:
                        build_type_buildings[building_id] = 10
                        continue
                    elif "Papier" in city.nodes[building_id]["name"] or "Paper" in city.nodes[building_id]["name"]:
                        build_type_buildings[building_id] = 11
                        continue
                else:
                    build_type_buildings[building_id] = 7

            elif building_id in office_buildings:
                individual_buildings.append(building_id)
                build_type_buildings[building_id] = 3 #  banks and insurances

            # todo depends on food or non food
            elif building_id in retail_buildings:
                individual_buildings.append(building_id)
                build_type_buildings[building_id] = 12 # or 13

            elif building_id in warehouse_buildings:
                individual_buildings.append(building_id)
                build_type_buildings[building_id] = 39 # multi function hall
                continue

            elif building_id in buildings_with_leisure:
                dict_leisure = {"fitness_centre": 42, "sports_centre": 38, "water_park": 40, "swimming_pool": 40}
                for leisure in dict_leisure.keys():
                    if leisure in city.nodes[building_id]["leisure"]:
                        individual_buildings.append(building_id)
                        build_type_buildings[building_id] = dict_leisure[leisure]
                        continue
                    else:
                        pass

            elif building_id in buildings_with_amenity:

                list_amenity = {"college", "university", "library", "sports_centre", "school", "bank", "clinic", "hospital", "cinema", "community_centre", "social_center", "theatre", "courthouse", "fire_station", "police", "embassy", "prison", "post_office"}
                list_amenity_food = {"bar", "cafe", "fast_food", "food_court", "pub", "restaurant"}

                dict_amenity = {"college": 20, "university": 20, "library": 33, "school": 16, "bank":3, "clinic":32, "hospital": 32, "cinema": 35, "community_centre": 37, "social_center": 37, "theatre": 36, "courthouse": 4, "fire_station": 4, "police": 4, "embassy": 4, "prison": 34, "post_office": 7}
                dict_amenity_food = {"bar": 22, "cafe": 22, "fast_food": 22, "food_court": 22, "pub": 22, "restaurant" : 22}
                for amenity in list_amenity:
                    if amenity in city.nodes[building_id]['amenity']:
                        individual_buildings.append(building_id)
                        build_type_buildings[building_id] = dict_amenity[amenity]
                        continue
                    else:
                        pass

                for amenity in list_amenity_food:
                    if amenity in city.nodes[building_id]['amenity']:
                        individual_buildings.append(building_id)
                        build_type_buildings[building_id] = dict_amenity_food[amenity]
                    else:
                        pass

            elif building_id in buildings_with_shop:
                list_shops = ["bakery", "pastry", "butcher", "mall", "department_store", "dry_cleaning", "laundry", "general", "supermarket", "beauty", "chemist", "cosmetics", "erotic", "hairdresser", "hairdresser_supply", "hearing_aids", "herbalist", "massage",
                        "medical_supply", "nutrition_supplement", "optican", "perfumery", "tattoo", "alcohol", "beverages", "brewing_supplies", "cheese", "chocolate", "coffee", "convenience", "deli", "diary",
                        "farm", "greengrocer", "ice_cream", "pasta", "seafood", "spices", "tea"]
                dict_shops =  {"bakery": 24, "pastry": 24, "butcher": 25, "mall": 15, "department_store": 15, "dry_cleaning": 26, "laundry": 26, "general": 13, "supermarket": 14, "beauty": 7, "chemist": 7, "cosmetics": 7, "erotic": 7, "hairdresser": 7, "hairdresser_supply": 7, "hearing_aids": 7, "herbalist": 7, "massage": 7,
                        "medical_supply": 7, "nutrition_supplement": 7, "optican": 7, "perfumery": 7, "tattoo": 7, "alcohol": 12, "beverages": 12, "brewing_supplies": 12, "cheese": 12, "chocolate": 12, "coffee": 12, "convenience": 12, "deli": 12, "diary": 12,
                        "farm": 12, "greengrocer": 12, "ice_cream": 12, "pasta": 12, "seafood": 12, "spices": 12, "tea": 12}
                for shop in list_shops:
                    if shop in city.nodes[building_id]["shop"]:
                        individual_buildings.append(building_id)
                        build_type_buildings[building_id] = dict_shops[shop]
                        pass
                    else:
                        pass

                non_foods = ["baby_goods", "bag", "boutique", "clothes", "fabric", "fashion", "jewelry", "leather", "shoes",
                        "tailor", "watches", "charity", "second_hand", "variety_store", "agrarian", "bathroom_furnishing", "doityourself", "electrical", "energy", "florist", "garden_centre", "garden_furniture", "gas", "glaziery", "hardware", "houseware", "looksmith", "paint", "security", "trade", "antiques", "bed", "candles", "carpet", "curtain", "furniture", "interior_decoration", "kitchen", "lamps", "tiles", "window_blind", "computer", "electronics", " hifi", " mobile_phone", "radiotechnics", " vacuum_cleaner", "bicycle", "car", " car_repair", "car_parts", "fuel", "fishing", "free_flying", "hunting", "motorcycle", "outdoor", "scuba_diving", "sports", "swimming_pool", "tyres", "art", "collector", "craft", "frame", "games", "model", "music", "musicial_instruments", "photo", "camera", "trophy", "video", "video_games", "anime", "books", "gift", "lottery", "newsagent", "stationery", "ticket", "bookmaker", "copyshop", "e_cigarette", "funeral_directors", "money_lender", "pawnbroker", "pet", "pyrotechnics", "tabacco", "toys", "travel_agency", "vacant", "weapons"]

                for non_food in range(0, len(non_foods)):
                    if non_foods[non_food] in city.nodes[building_id]["shop"]:
                        individual_buildings.append(building_id)
                        if city.nodes[building_id]["area"] <= 100:
                            # Spec_demand_non_res.xlsx --> found in PyCity_Calc/pycity_calc/data/BaseData/Specific_Demand_Data
                            # build_type = small shop with no food
                            build_type_buildings[building_id] = 13
                            pass
                        else:
                            build_type_buildings[building_id] = 15
                            pass
                    else:
                        pass

            # ----------------------------------------------------------------------------------
            # Single Family House detached
            elif (building_id in no_neigbours) and (30 < area[building_id] < 110): # based on Manfred Heggers "Energetische Stadtraumtypen"
                if building_id not in single_family_house:
                    single_family_house.append(building_id)
                if building_id not in detached_single_family_houses:
                    detached_single_family_houses.append(building_id)
                    continue


            # ----------------------------------------------------------------------------------
            # Multi Family House


            elif (110 < area[building_id] < 437) and (percentage_of_shops_to_houses[building_id] <= 0.3): # --> Combination of  EST 1b, village building, old city and inner city
                # SFH with garages and great ground area
                if building_id in building_with_garages:
                    if building_id not in single_family_house:
                        single_family_house.append(building_id)
                        detached_single_family_houses.append(building_id)
                    continue


                # MFH
                else:
                    # --> Combination of  EST 1b, village building, old city and inner city
                    # Multi Family House
                    if building_id not in multi_family_houses:
                        multi_family_houses.append(building_id)
                        continue


                if building_id in one_neigbour or building_id in two_neigbours or building_id in more_than_two_neighbours:
                    for i in range(0, len(buildings_neighbours[building_id])):
                        # SFH with garage
                        if building_id in building_with_garages or area[buildings_neighbours[building_id][i]] <= 45 and number_neighbour_buildings[building_id] <=1:
                            if building_id not in single_family_house:
                                single_family_house.append(building_id)
                            if number_neighbour_buildings[building_id] == 1:
                                if building_id not in double_houses:
                                    double_houses.append(building_id)
                            if number_neighbour_buildings[building_id] == 2:
                                if building_id not in terraced_houses:
                                    terraced_houses.append(building_id)
                            break


                        # SFH, just if the neigbour building is an single family house due to the small ground area
                        if area[buildings_neighbours[building_id][i]] < 110:

                            if building_id not in single_family_house:
                                single_family_house.append(building_id)
                            if number_neighbour_buildings[building_id] == 1:
                                if building_id not in double_houses:
                                    double_houses.append(building_id)
                            if number_neighbour_buildings[building_id] == 2:
                                if building_id not in terraced_houses:
                                    terraced_houses.append(building_id)
                            break

                        # MFH
                        else:
                            ## --> Combination of  EST 1b, village building, old city and inner city
                            # Multi Family House
                            if building_id not in multi_family_houses:
                                multi_family_houses.append(building_id)
                            break


                # MFH
                else:
                    # # --> Combination of  EST 1b, village building, old city and inner city
                    # Multi Family House
                    if building_id not in multi_family_houses and building_id not in single_family_house:
                        multi_family_houses.append(building_id)
                    continue


            # ----------------------------------------------------------------------------------
            # Double House
            elif (building_id in one_neigbour) and (30 < area[building_id] < 110) : # based on Manfred Hegger
                if 60 < area[building_id] < 110:
                    for i in range(0, len(buildings_neighbours[building_id])):
                        if (60 < area[buildings_neighbours[building_id][i]] < 110) and buildings_neighbours[building_id][i] in one_neigbour: # DH
                            if building_id not in single_family_house:
                                single_family_house.append(building_id)
                            if building_id not in double_houses:
                                double_houses.append(building_id)
                            continue


                        # ----------------------------------------------------------------------------------

                        #Terraced building or SFH or MFH
                        if 53 < area[building_id] < 84 and (percentage_of_shops_to_houses[building_id] <= 0.05):  # --> area based on IWU data for terrace buildings (Min to Max)
                            for i in range(0, len(buildings_neighbours[building_id])):

                                # Terraced House
                                if (building_id in one_neigbour and buildings_neighbours[building_id][
                                    i] in two_neigbours) or ((building_id in two_neigbours and
                                                                      buildings_neighbours[building_id][
                                                                          i] in two_neigbours) or (
                                                building_id in two_neigbours and buildings_neighbours[building_id][
                                            i] in one_neigbour)):
                                    if building_id not in single_family_house:
                                        single_family_house.append(building_id)
                                    if building_id not in terraced_houses:
                                        terraced_houses.append(building_id)
                                    continue


                                # SFH or MFH with a neighbour building, which has more than two neighbours --> prob city
                                if (building_id in one_neigbour and (buildings_neighbours[building_id][
                                    i] in more_than_two_neighbours or buildings_neighbours[building_id][
                                    i] in one_neigbour or buildings_neighbours[building_id][
                                    i] in two_neigbours )):

                                    continue

                        # # Single Family House with neighbour but not double house
                        elif (building_id in one_neigbour) and (30 < area[building_id] < 110):
                            if building_id not in single_family_house:
                                single_family_house.append(building_id)
                                double_houses.append(building_id)
                            continue


                # Terraced building
                elif 53 < area[building_id] < 84 and (percentage_of_shops_to_houses[building_id] <= 0.05) and(building_id in two_neigbours or building_id in one_neigbour):
                    for i in range(0, len(buildings_neighbours[building_id])):
                        if (building_id in one_neigbour and buildings_neighbours[building_id][
                            i] in two_neigbours) or ((building_id in two_neigbours and
                                                              buildings_neighbours[building_id][
                                                                  i] in two_neigbours) or (
                                        building_id in two_neigbours and buildings_neighbours[building_id][
                                    i] in one_neigbour)):
                            if building_id not in single_family_house:
                                single_family_house.append(building_id)
                            if building_id not in terraced_houses:
                                terraced_houses.append(building_id)
                            continue


                        # SFH or MFH with more than two neighbours --> probably city
                        elif building_id in one_neigbour and buildings_neighbours[building_id][i] in more_than_two_neighbours:

                            continue

                        # # Single Family House with neighbour but not double house
                        elif 30 < area[building_id] <= 60:
                            if building_id not in single_family_house:
                                single_family_house.append(building_id)
                                double_houses.append(building_id)
                            continue


                # # Single Family House with neighbour but not double house
                elif 30 < area[building_id] <= 60:
                    if building_id not in single_family_house:
                        single_family_house.append(building_id)
                        double_houses.append(building_id)
                    continue


            #----------------------------------------------------------------------------------
            # Terraced building

            elif (building_id in two_neigbours or building_id in one_neigbour) and (53 < area[building_id] < 437) and (percentage_of_shops_to_houses[building_id] <= 0.3): #--> area based on IWU data for terrace buildings (Min to Max)

                for i in range(0, len(buildings_neighbours[building_id])):
                    if (building_id in one_neigbour and buildings_neighbours[building_id][i] in two_neigbours) or ((building_id in two_neigbours and buildings_neighbours[building_id][i] in two_neigbours) or (building_id in two_neigbours and buildings_neighbours[building_id][i] in one_neigbour)):
                        # Terraced building
                        if 53 < area[building_id] < 84:
                            if building_id not in single_family_house:
                                single_family_house.append(building_id)
                            if building_id not in terraced_houses:
                                terraced_houses.append(building_id)
                            if building_id in multi_family_houses:
                                multi_family_houses.remove(building_id)
                            break


                        # MFH through the way of a terraced building
                        else:
                            if building_id not in multi_family_houses:
                                multi_family_houses.append(building_id)
                            continue


                    # MFH through the way of a terraced building
                    else:
                        if building_id not in multi_family_houses:
                            multi_family_houses.append(building_id)
                        continue


            # # ----------------------------------------------------------------------------------

            # Commercial buildings
            elif buildings_with_amenity != [] or buildings_with_name != [] or buildings_with_shop != []:

                # Office building
                if 225 < area[building_id] < 3200  and (building_id in buildings_with_amenity or building_id in buildings_with_name or building_id in buildings_with_shop): # 1 Quartil bis 3. Quartil für Büro
                    if building_id not in commercial:
                        commercial.append(building_id)
                    if building_id not in commercial_office_building:
                        commercial_office_building.append(building_id)
                    continue

                # Hall
                elif 1500 < area[building_id] and (building_id in no_neigbours or building_id in one_neigbour)  and (building_id in buildings_with_amenity or building_id in buildings_with_name or building_id in buildings_with_shop):# no upper-restriction for the area, to include
                    if building_id not in commercial:
                        commercial.append(building_id)
                    if building_id not in commercial_hall:
                        commercial_hall.append(building_id)
                    continue

                elif 290 < area[building_id]< 2000: # High rise
                    if building_id not in high_rise_houses:
                        high_rise_houses.append(building_id)
                    if building_id not in multi_family_houses:
                        multi_family_houses.append(building_id)

                else:
                    pass


            # ----------------------------------------------------------------------------------
            # High rise
            # --> High rise buildings often do not have neighbours and border to other high rise buildings.


            elif 290 < area[building_id]< 2000 and (((building_id in one_neigbour or building_id in two_neigbours or building_id in more_than_two_neighbours) \
                                                              and sorted(min_distance_within_square[building_id])[
                                                                  len(buildings_neighbours[building_id])] >= 15) \
                                                             or (building_id in no_neigbours and sorted(
                        min_distance_within_square[building_id]) >= 15)) and (percentage_of_shops_to_houses[
                                                                            building_id] <= 0.05):

                    # min distance is calculated with the Tabula data and
                    if building_id not in high_rise_houses:
                        high_rise_houses.append(building_id)
                    if building_id not in multi_family_houses:
                        multi_family_houses.append(building_id)


    # ----------------------------------------------------------------------------------

        # USER DEFINED BUILDING DISTRIBUTION  == TRUE

        elif user_defined_building_distribution == True:
            if specific_buildings == True:
                if (building_id) in schools:

                    individual_buildings.append(building_id)

                    # Spec_demand_non_res.xlsx --> found in PyCity_Calc/pycity_calc/data/BaseData/Specific_Demand_Data
                    if building_id in buildings_with_name:
                        dict_schools = {"Grundschule": 16, "Gesamtschule": 16, "Behindertenschule": 17,
                                        "Realschule": 18, "Gymnasium": 18, "Berufsschule": 19}
                        for school in dict_schools.keys():
                            if school in city.nodes[building_id]["name"]:
                                individual_buildings.append(building_id)
                                build_type_buildings[building_id] = dict_schools[school]
                                continue
                            else:
                                build_type_buildings[building_id] = 16
                                continue
                    else:
                        build_type_buildings[building_id] = 16
                        continue

                elif building_id in houses_of_prayer:

                    individual_buildings.append(building_id)

                    # Spec_demand_non_res.xlsx --> found in PyCity_Calc/pycity_calc/data/BaseData/Specific_Demand_Data
                    # build_type ist not given for houses of prayer
                    build_type_buildings[building_id] = None
                    continue

                elif building_id in universities:

                    individual_buildings.append(building_id)

                    # Spec_demand_non_res.xlsx --> found in PyCity_Calc/pycity_calc/data/BaseData/Specific_Demand_Data
                    # build_type = University
                    build_type_buildings[building_id] = 20
                    continue

                elif building_id in hospitals:
                    individual_buildings.append(building_id)

                    # Spec_demand_non_res.xlsx --> found in PyCity_Calc/pycity_calc/data/BaseData/Specific_Demand_Data
                    # build_type = hospital
                    build_type_buildings[building_id] = 32
                    continue

                elif building_id in civic:
                    individual_buildings.append(building_id)

                    # Spec_demand_non_res.xlsx --> found in PyCity_Calc/pycity_calc/data/BaseData/Specific_Demand_Data
                    # build_type =  public institution
                    build_type_buildings[building_id] = 4
                    continue

                elif building_id in public:
                    individual_buildings.append(building_id)

                    # Spec_demand_non_res.xlsx --> found in PyCity_Calc/pycity_calc/data/BaseData/Specific_Demand_Data
                    # build_type =  public institution
                    build_type_buildings[building_id] = 4
                    continue

                elif building_id in residential:
                    if building_id in apartment_buildings:
                        if building_id not in multi_family_houses:
                            multi_family_houses.append(building_id)
                    elif building_id in residential_buildings:
                        if 30 < area[building_id] < 110:  # --> SFH
                            if building_id in no_neigbours:
                                single_family_house.append(building_id)
                                detached_single_family_houses.append(building_id)
                                continue
                            elif building_id in one_neigbour:
                                for i in range(0, len(buildings_neighbours[building_id])):
                                    if (60 < area[buildings_neighbours[building_id][i]] < 110) and \
                                                    buildings_neighbours[building_id][i] in one_neigbour:
                                        single_family_house.append(building_id)
                                        double_houses.append(building_id)
                                        continue
                                if buildings_neighbours[building_id][i] in two_neigbours:
                                    single_family_house.append(building_id)
                                    terraced_houses.append(building_id)
                                    continue
                            elif building_id in two_neigbours:
                                single_family_house.append(building_id)
                                terraced_houses.append(building_id)
                                continue
                        else:  # --> MFH
                            if building_id not in multi_family_houses:
                                multi_family_houses.append(building_id)
                                continue

                    elif building_id in bungalow_buildings:
                        single_family_house.append(building_id)
                        continue
                    elif building_id in house_buildings:
                        if building_id in no_neigbours:
                            single_family_house.append(building_id)
                            detached_single_family_houses.append(building_id)
                            continue
                        elif building_id in one_neigbour:
                            for i in range(0, len(buildings_neighbours[building_id])):
                                if (60 < area[buildings_neighbours[building_id][i]] < 110) and \
                                                buildings_neighbours[building_id][i] in one_neigbour:
                                    single_family_house.append(building_id)
                                    double_houses.append(building_id)
                                    continue
                                elif buildings_neighbours[building_id][i] in two_neigbours:
                                    single_family_house.append(building_id)
                                    terraced_houses.append(building_id)
                                    continue
                                elif buildings_neighbours[building_id][i] in one_neigbour:
                                    single_family_house.append(building_id)
                                    double_houses.append(building_id)
                                    continue
                        elif building_id in two_neigbours:
                            single_family_house.append(building_id)
                            terraced_houses.append(building_id)
                            continue

                    elif building_id in detached_buildings:
                        single_family_house.append(building_id)
                        detached_single_family_houses.append(building_id)
                        continue
                    elif building_id in terrace_buildings and (
                            building_id in one_neigbour or building_id in two_neigbours):
                        if building_id in one_neigbour:
                            single_family_house.append(building_id)
                            terraced_houses.append(building_id)
                            continue
                        else:
                            single_family_house.append(building_id)
                            terraced_houses.append(building_id)
                            continue
                    elif building_id in dormitory_buildings:
                        if building_id not in multi_family_houses:
                            multi_family_houses.append(building_id)
                        continue

                elif building_id in commercial_buildings:
                    individual_buildings.append(building_id)
                    build_type_buildings[building_id] = 1

                elif building_id in industrial_buildings:
                    individual_buildings.append(building_id)
                    if building_id in buildings_with_name:
                        if "Metall" in city.nodes[building_id]["name"]:
                            build_type_buildings[building_id] = 8
                        elif "KFZ" in city.nodes[building_id]["name"]:
                            build_type_buildings[building_id] = 9
                        elif "Wood" in city.nodes[building_id]["name"] or "Holz" in city.nodes[building_id]["name"]:
                            build_type_buildings[building_id] = 10
                        elif "Papier" in city.nodes[building_id]["name"] or "Paper" in city.nodes[building_id]["name"]:
                            build_type_buildings[building_id] = 11
                    else:
                        build_type_buildings[building_id] = 7

                elif building_id in office_buildings:
                    individual_buildings.append(building_id)
                    build_type_buildings[building_id] = 3  # banks and insurances

                    # todo depends on food or non food

                elif building_id in retail_buildings:
                    individual_buildings.append(building_id)
                    build_type_buildings[building_id] = 12  # or 13

                elif building_id in warehouse_buildings:
                    individual_buildings.append(building_id)
                    build_type_buildings[building_id] = 39  # multi function hall

                elif building_id in buildings_with_leisure:
                    dict_leisure = {"fitness_centre": 42, "sports_centre": 38, "water_park": 40, "swimming_pool": 40}
                    for leisure in dict_leisure.keys():
                        if leisure in city.nodes[building_id]["leisure"]:
                            individual_buildings.append(building_id)
                            build_type_buildings[building_id] = dict_leisure[leisure]
                        else:
                            continue

                elif building_id in buildings_with_amenity:
                    dict_amenity = {"college": 20, "university": 20, "library": 33, "school": 16, "bank": 3,
                                    "clinic": 32, "hospital": 32, "cinema": 35, "community_centre": 37,
                                    "social_center": 37, "theatre": 36, "courthouse": 4, "fire_station": 4, "police": 4,
                                    "embassy": 4, "prison": 34, "post_office": 7, "bar": 22, "cafe": 22,
                                    "fast_food": 22, "food_court": 22, "pub": 22, "restaurant": 22}
                    for amenity in dict_amenity.keys():
                        if amenity in city.nodes[building_id]["amenity"]:
                            individual_buildings.append(building_id)
                            build_type_buildings[building_id] = dict_amenity[amenity]
                        else:
                            continue

                elif building_id in buildings_with_shop:
                    dict_shops = {"bakery": 24, "pastry": 24, "butcher": 25, "mall": 15, "department_store": 15,
                                  "dry_cleaning": 26, "laundry": 26, "general": 13, "supermarket": 14, "beauty": 7,
                                  "chemist": 7, "cosmetics": 7, "erotic": 7, "hairdresser": 7, "hairdresser_supply": 7,
                                  "hearing_aids": 7, "herbalist": 7, "massage": 7,
                                  "medical_supply": 7, "nutrition_supplement": 7, "optican": 7, "perfumery": 7,
                                  "tattoo": 7, "alcohol": 12, "beverages": 12, "brewing_supplies": 12, "cheese": 12,
                                  "chocolate": 12, "coffee": 12, "convenience": 12, "deli": 12, "diary": 12,
                                  "farm": 12, "greengrocer": 12, "ice_cream": 12, "pasta": 12, "seafood": 12,
                                  "spices": 12, "tea": 12}
                    for shop in dict_shops.keys():
                        if shop in city.nodes[building_id]["shop"]:
                            individual_buildings.append(building_id)
                            build_type_buildings[building_id] = dict_shops[shop]
                        else:
                            continue

                    non_foods = ["baby_goods", "bag", "boutique", "clothes", "fabric", "fashion", "jewelry", "leather",
                                 "shoes",
                                 "tailor", "watches", "charity", "second_hand", "variety_store", "agrarian",
                                 "bathroom_furnishing", "doityourself", "electrical", "energy", "florist",
                                 "garden_centre", "garden_furniture", "gas", "glaziery", "hardware", "houseware",
                                 "looksmith", "paint", "security", "trade", "antiques", "bed", "candles", "carpet",
                                 "curtain", "furniture", "interior_decoration", "kitchen", "lamps", "tiles",
                                 "window_blind", "computer", "electronics", " hifi", " mobile_phone", "radiotechnics",
                                 " vacuum_cleaner", "bicycle", "car", " car_repair", "car_parts", "fuel", "fishing",
                                 "free_flying", "hunting", "motorcycle", "outdoor", "scuba_diving", "sports",
                                 "swimming_pool", "tyres", "art", "collector", "craft", "frame", "games", "model",
                                 "music", "musicial_instruments", "photo", "camera", "trophy", "video", "video_games",
                                 "anime", "books", "gift", "lottery", "newsagent", "stationery", "ticket", "bookmaker",
                                 "copyshop", "e_cigarette", "funeral_directors", "money_lender", "pawnbroker", "pet",
                                 "pyrotechnics", "tabacco", "toys", "travel_agency", "vacant", "weapons"]

                    for non_food in range(0, len(non_foods)):
                        if non_foods[non_food] in city.nodes[building_id]["shop"]:
                            individual_buildings.append(building_id)

                            if city.nodes[building_id]["area"] <= 100:
                                # Spec_demand_non_res.xlsx --> found in PyCity_Calc/pycity_calc/data/BaseData/Specific_Demand_Data
                                # build_type = small shop with no food
                                build_type_buildings[building_id] = 13

                            else:
                                build_type_buildings[building_id] = 15

                number_of_spezific_buildings = (len(schools) + len(universities) + len(houses_of_prayer) + len(hospitals) + len(civic) + len(public) + len(commercial_buildings) + len(warehouse_buildings) + len(retail_buildings) +  len(industrial_buildings) + len(office_buildings) + len(buildings_with_shop) + len(buildings_with_amenity) + len(buildings_with_leisure))
                number_of_sfh_before_substraction_of_spezific_buildings_sfh = ((len(nodelist_buildings) - number_of_spezific_buildings) * percentage_sfh / 100)
                number_of_sfh = number_of_sfh_before_substraction_of_spezific_buildings_sfh - len(single_family_house)
                number_of_mfh_before_substraction_of_spezific_buildings_mfh = ((len(nodelist_buildings) - number_of_spezific_buildings) * percentage_mfh / 100)
                number_of_mfh = number_of_mfh_before_substraction_of_spezific_buildings_mfh - len(multi_family_houses)
                number_of_non_residential = (len(nodelist_buildings) - number_of_spezific_buildings) * percentage_non_res / 100

            else:
                number_of_sfh = (len(nodelist_buildings) * percentage_sfh / 100)
                number_of_mfh = (len(nodelist_buildings)* percentage_mfh / 100)
                number_of_non_residential = len(nodelist_buildings) * percentage_non_res / 100

            # SFH houses
            sfh_areas = []
            areas_from_small_to_large = sorted(area.values())

            for sfh in range(0, int(number_of_sfh)):
                sfh_areas.append(areas_from_small_to_large[sfh])

            for sfh_area in sfh_areas:
                if sfh_area == area[building_id]:
                    single_family_house.append(building_id)

            # MFH houses
            mfh_areas = []

            for mfh in range(int(number_of_sfh), int(number_of_mfh + number_of_sfh)):
                mfh_areas.append(areas_from_small_to_large[mfh])

            for mfh_area in mfh_areas:
                if mfh_area == area[building_id]:
                    if building_id not in multi_family_houses:
                        multi_family_houses.append(building_id)


            # Non-residential houses
            non_res_areas = []

            for non_res in range(int(number_of_mfh + number_of_sfh), int(number_of_mfh + number_of_sfh + number_of_non_residential)):
                non_res_areas.append(areas_from_small_to_large[non_res])

            for non_res_area in non_res_areas:
                if non_res_area == area[building_id]:
                    commercial.append(building_id)

    # -----------------------------------------------------------------------------------

    # if user-defined is False:
    if user_defined_building_distribution == False:
        percentage_sfh = len(single_family_house) / len(nodelist_buildings)
        percentage_mfh = len(multi_family_houses) / len(nodelist_buildings)
        percentage_non_res = (len(commercial) + len(individual_buildings)) / len(nodelist_buildings)

    # IDENTIFICATION OF DISTRICT( residential area, non residential area or inner city)
    city_district = {key: [] for key in nodelist_buildings}

    counter_res = 0
    counter_inner_city = 0
    counter_non_res = 0

    for building_id in nodelist_buildings:
        # residential
        if percentage_cropped_area_within_square[building_id] <= 0.4 and average_buildings_neighbours[
            building_id] <= 1.5 and percentage_sfh > percentage_mfh > percentage_non_res:
            city_district[building_id] = "residential"
            counter_res += 1

        # inner city
        elif percentage_cropped_area_within_square[building_id] >= 0.4 and 1 <= average_buildings_neighbours[
            building_id] and percentage_mfh > percentage_non_res and  percentage_mfh > percentage_sfh:
            city_district[building_id] = "inner city"
            counter_inner_city += 1

        # non residential
        elif 0.5 >= average_buildings_neighbours[
            building_id] and percentage_non_res > percentage_mfh and  percentage_non_res > percentage_sfh:
            city_district[building_id] = "non residential"
            counter_non_res += 1

        else:
            if city_district[building_id] == []:
                for i in building_list_within_spezified_square[building_id]:
                    if city_district[i] =="residential":
                        counter_res += 1
                    elif city_district[i] == "inner city":
                        counter_inner_city += 1
                    elif city_district[i] == "non residential":
                        counter_non_res += 1
                    else:
                        continue

                if counter_res > counter_inner_city and counter_res > counter_non_res:
                    city_district[building_id] = "residential"
                elif counter_inner_city > counter_res and counter_inner_city > counter_non_res:
                    city_district[building_id] = "inner city"
                elif counter_non_res > counter_inner_city and counter_non_res > counter_res:
                    city_district[building_id] = "non residential"


        # Identification of the building type of the missing building (SFH or MFH)
        if building_id not in single_family_house and building_id not in multi_family_houses and building_id not in commercial and building_id not in individual_buildings:
            if city_district[building_id]== "residential":
                single_family_house.append(building_id)
                if buildings_neighbours[building_id] == []:
                    detached_single_family_houses.append(building_id)
                elif number_neighbour_buildings[building_id] == 1 and number_neighbour_buildings[buildings_neighbours[building_id][0]] == 1:
                    double_houses.append(building_id)
                else:
                    terraced_houses.append(building_id)

            elif city_district[building_id] == "inner city":
                multi_family_houses.append(building_id)

            elif city_district[building_id] == "non residential":
                commercial.append(building_id)
            else:
                multi_family_houses.append(building_id)

        if city_district[building_id] == "inner city" and building_id in single_family_house:
            single_family_house.remove(building_id)
            if building_id not in multi_family_houses:
                multi_family_houses.append(building_id)

    # -----------------------------------------------------------------------------------

    # Deleting of the not considered building nodes
    for i in deleted_buildings:
        ues.UESGraph.remove_building(city, i)

    # -----------------------------------------------------------------------------------
    # ---------------------------------------------------------------------------

    # DATA ENRICHMENT

    # BUILD YEAR

    if user_defined_build_year == True:
        for building_id in nodelist_buildings:

            build_year, height_of_floors, cellar, attic, dormer = get_building_information_based_on_build_year(
                    building=building_id,
                    specified_build_year_beginning=specified_build_year_beginning,
                    specified_build_year_end=specified_build_year_end,
                    build_year_buildings=build_year_buildings,
                    floor_height_buildings=floor_height_buildings, cellar_buildings=cellar_buildings,
                    attic_buildings=attic_buildings, dormer_buildings=dormer_buildings,
                    single_family_house=single_family_house, double_houses=double_houses,
                    terraced_houses=terraced_houses, multi_family_houses=multi_family_houses,
                    commercial=commercial, individual_buildings=individual_buildings,
                    high_rise_houses=high_rise_houses)

            build_year_buildings[building_id] = build_year
            floor_height_buildings[building_id] = height_of_floors
            cellar_buildings[building_id] = cellar
            attic_buildings[building_id] = attic
            dormer_buildings[building_id] = dormer

    elif user_defined_build_year == False:

        nodelist_build_year = deepcopy(nodelist_buildings)
        buildings_with_buildyear_from_osm = deepcopy(buildings_buildyear)

        counter_build_year = 0

        while nodelist_build_year != []:
            counter_build_year+=1
            if counter_build_year == 1:
                total_ref_building = nodelist_build_year[0]
                ref_building =  nodelist_build_year[0]
                stop_code = 0

                if buildings_with_buildyear_from_osm != {}:
                    for building_with_build_year_from_osm in buildings_with_buildyear_from_osm[0]:
                        buildings_with_buildyear_from_osm.remove(building_with_build_year_from_osm)
                        build_year_buildings[building_with_build_year_from_osm] = int(
                            city.nodes[building_with_build_year_from_osm]['building_buildyear'])

                        specified_build_year_beginning = build_year_buildings[building_with_build_year_from_osm]
                        specified_build_year_end = build_year_buildings[building_with_build_year_from_osm]


                        if building_with_build_year_from_osm in single_family_house:

                            build_year, height_of_floors, cellar, attic, dormer = get_build_year_sfh_user_defined(building_id=i,
                                                                                                                  terraced_houses=terraced_houses,
                                                                                                                  double_houses=double_houses,
                                                                                                                  specified_build_year_beginning=specified_build_year_beginning,
                                                                                                                  specified_build_year_end=specified_build_year_end)

                            build_year_buildings[building_with_build_year_from_osm] = build_year
                            floor_height_buildings[building_with_build_year_from_osm] = height_of_floors
                            cellar_buildings[building_with_build_year_from_osm] = cellar
                            attic_buildings[building_with_build_year_from_osm] = attic
                            dormer_buildings[building_with_build_year_from_osm] = dormer


                        elif building_with_build_year_from_osm in multi_family_houses:

                            build_year, height_of_floors, cellar, attic, dormer = get_build_year_mfh_user_defined(
                                building_id=i, high_rise_houses=high_rise_houses,
                                specified_build_year_beginning=specified_build_year_beginning,
                                specified_build_year_end=specified_build_year_end)

                            build_year_buildings[building_with_build_year_from_osm] = build_year
                            floor_height_buildings[building_with_build_year_from_osm] = height_of_floors
                            cellar_buildings[building_with_build_year_from_osm] = cellar
                            attic_buildings[building_with_build_year_from_osm] = attic
                            dormer_buildings[building_with_build_year_from_osm] = dormer


                        elif building_with_build_year_from_osm in commercial or building_with_build_year_from_osm in individual_buildings:

                            build_year, height_of_floors = get_build_year_non_res()

                            build_year_buildings[building_with_build_year_from_osm] = build_year
                            floor_height_buildings[building_with_build_year_from_osm] = height_of_floors

                        # ----------------------------------

                        ref_building = building_with_build_year_from_osm

                        build_year_buildings, floor_height_buildings, cellar_buildings, attic_buildings, dormer_buildings = get_relation_build_year(ref_building= ref_building, stop_code=stop_code, building_list_within_spezified_square=building_list_within_spezified_square, build_year_buildings=build_year_buildings,
                                    buildings_neighbours=buildings_neighbours, near_by_buildings_with_same_area=near_by_buildings_with_same_area, double_houses=double_houses,
                                    floor_height_buildings=floor_height_buildings, cellar_buildings=cellar_buildings, attic_buildings=attic_buildings, dormer_buildings=dormer_buildings,
                                    total_ref_year=total_ref_year, single_family_house=single_family_house, terraced_houses=terraced_houses, multi_family_houses=multi_family_houses, commercial= commercial, individual_buildings=individual_buildings,
                                    nodelist_build_year=nodelist_build_year, high_rise_houses= high_rise_houses)

                elif ref_building in single_family_house:
                    if user_defined_build_year == False:
                        build_year, height_of_floors, cellar, attic, dormer = get_build_year_sfh(
                            building_id=building_id,
                            terraced_houses=terraced_houses, double_houses=double_houses)
                    elif user_defined_build_year == True:
                        build_year, height_of_floors, cellar, attic, dormer = get_build_year_sfh_user_defined(
                            building_id=building_id,
                            specified_build_year_beginning=specified_build_year_beginning,
                            specified_build_year_end=specified_build_year_end,
                            terraced_houses=terraced_houses, double_houses=double_houses)

                    build_year_buildings[ref_building] = build_year
                    floor_height_buildings[ref_building] = height_of_floors
                    cellar_buildings[ref_building] = cellar
                    attic_buildings[ref_building] = attic
                    dormer_buildings[ref_building] = dormer

                elif ref_building in multi_family_houses:
                    if user_defined_build_year == False:
                        build_year, height_of_floors, cellar, attic, dormer = get_build_year_mfh(
                            building_id=building_id, high_rise_houses=high_rise_houses)
                    elif user_defined_build_year == True:
                        build_year, height_of_floors, cellar, attic, dormer = get_build_year_mfh_user_defined(
                            building_id=building_id,
                            specified_build_year_beginning=specified_build_year_beginning,
                            specified_build_year_end=specified_build_year_end,
                            high_rise_houses=high_rise_houses)

                    build_year_buildings[ref_building] = build_year
                    floor_height_buildings[ref_building] = height_of_floors
                    cellar_buildings[ref_building] = cellar
                    attic_buildings[ref_building] = attic
                    dormer_buildings[ref_building] = dormer

                elif ref_building in commercial or ref_building in individual_buildings:
                    if user_defined_build_year == False:
                        build_year, height_of_floors = get_build_year_non_res()

                    elif user_defined_build_year == True:
                        build_year, height_of_floors, cellar, attic, dormer = get_build_year_mfh_user_defined(
                            building_id=building_id,
                            specified_build_year_beginning=specified_build_year_beginning,
                            specified_build_year_end=specified_build_year_end,
                            high_rise_houses=high_rise_houses)

                    build_year_buildings[ref_building] = build_year
                    floor_height_buildings[ref_building] = height_of_floors


                total_ref_year = build_year_buildings[ref_building]

            else:
                ref_building = nodelist_build_year[0]

                specified_build_year_beginning = total_ref_year - 3
                specified_build_year_end = min((total_ref_year + 3), int(time.strftime("%Y")))

                build_year, height_of_floors, cellar, attic, dormer= get_building_information_based_on_build_year(
                    building=ref_building,
                    specified_build_year_beginning=specified_build_year_beginning,
                    specified_build_year_end=specified_build_year_end,
                    build_year_buildings=build_year_buildings,
                    floor_height_buildings=floor_height_buildings, cellar_buildings=cellar_buildings,
                    attic_buildings=attic_buildings, dormer_buildings=dormer_buildings,
                    single_family_house=single_family_house, double_houses=double_houses,
                    terraced_houses=terraced_houses, multi_family_houses=multi_family_houses,
                    commercial=commercial, individual_buildings=individual_buildings,
                    high_rise_houses=high_rise_houses)

                build_year_buildings[ref_building] = build_year
                floor_height_buildings[ref_building] = height_of_floors
                cellar_buildings[ref_building] = cellar
                attic_buildings[ref_building] = attic
                dormer_buildings[ref_building] = dormer

                total_ref_year =  build_year_buildings[ref_building]

            build_year_buildings, floor_height_buildings, cellar_buildings, attic_buildings, dormer_buildings = get_relation_build_year(
                ref_building=ref_building, stop_code=stop_code,
                building_list_within_spezified_square=building_list_within_spezified_square,
                build_year_buildings=build_year_buildings,
                buildings_neighbours=buildings_neighbours,
                near_by_buildings_with_same_area=near_by_buildings_with_same_area, double_houses=double_houses,
                floor_height_buildings=floor_height_buildings, cellar_buildings=cellar_buildings,
                attic_buildings=attic_buildings, dormer_buildings=dormer_buildings,
                total_ref_year=total_ref_year, single_family_house=single_family_house, terraced_houses=terraced_houses,
                multi_family_houses=multi_family_houses, commercial=commercial, individual_buildings=individual_buildings,
                nodelist_build_year=nodelist_build_year, high_rise_houses=high_rise_houses)


    # NB of APARTMENTS and OCCUPANTS and NB of FLOORS

    for building_id in nodelist_buildings:

        if building_id in single_family_house:

            # NB of APARTMENTS

            if building_id in terraced_houses:
                list_nb_of_apartments[building_id] = 1  # Manfreds Heggers "Energetische Stadtraumtypen" of EST 2
            else:
                list_nb_of_apartments[building_id] = numpy.random.choice(numpy.arange(1, 3), p=[0.75,
                                                                                                0.25])  # Manfreds Heggers "Energetische Stadtraumtypen" of EST 1a

            # NB of FLOORS

            # neighbour buildings usually do have the same number of floors
            if number_neighbour_buildings[building_id] >= 1:
                for i in range(0, number_neighbour_buildings[building_id]):
                    if list_nb_of_floors[buildings_neighbours[building_id][i]] != []:
                        list_nb_of_floors[building_id] = list_nb_of_floors[buildings_neighbours[building_id][i]]

            if building_id in buildings_with_levels:
                if "." in city.nodes[building_id]["building_levels"]:
                    list_nb_of_floors[building_id] = float(city.nodes[building_id]["building_levels"])
                else:
                    list_nb_of_floors[building_id] = int(city.nodes[building_id]["building_levels"])

            elif building_id in bungalow_buildings:
                list_nb_of_floors[building_id] = 1

            else:
                nb_of_floors = numpy.random.choice(numpy.arange(2, 4), p=[0.75,
                                                                          0.25])  # Manfreds Heggers "Energetische Stadtraumtypen" of EST 1a
                if nb_of_floors == 2:
                    list_nb_of_floors[building_id] = 1.5
                else:
                    list_nb_of_floors[building_id] = 2.5


        elif building_id in multi_family_houses:

            # neighbour buildings usually do have the same number of floors
            if number_neighbour_buildings[building_id] >= 1:
                for i in range(0, number_neighbour_buildings[building_id]):
                    if list_nb_of_floors[buildings_neighbours[building_id][i]] != []:
                        list_nb_of_floors[building_id] = list_nb_of_floors[buildings_neighbours[building_id][i]]
                        list_nb_of_apartments[building_id] = round(
                            list_nb_of_apartments[buildings_neighbours[building_id][i]] * area[building_id] / area[
                                buildings_neighbours[building_id][i]])

            if building_id in buildings_with_levels:
                if "." in city.nodes[building_id]["building_levels"]:
                    list_nb_of_floors[building_id] = float(city.nodes[building_id]["building_levels"])
                else:
                    list_nb_of_floors[building_id] = int(city.nodes[building_id]["building_levels"])
                if city_district[building_id] == "residential":
                    nb_of_apartments = numpy.random.choice(numpy.arange
                                                           (6, 9), p=[0.25, 0.5,
                                                                      0.25])  # --> Min to Max of Manfred Heggers "Energetische Stadtraumtypen" of EST 1b
                    if nb_of_apartments == 7:
                        list_nb_of_apartments[building_id] = random.randint(7, 8)
                    elif nb_of_apartments == 8:
                        list_nb_of_apartments[building_id] = random.randint(9, 10)
                    elif nb_of_apartments == 6:
                        list_nb_of_apartments[building_id] = 6

                elif city_district[building_id] == "inner city":
                    nb_of_apartments = numpy.random.choice(numpy.arange(6, 9), p=[0.25, 0.5,
                                                                                  0.25])  # --> Min to Max of Manfred Heggers "Energetische Stadtraumtypen" of EST 8 "Innenstadt"
                    if nb_of_apartments == 6:
                        list_nb_of_apartments[building_id] = random.randint(4, 6)
                    elif nb_of_apartments == 7:
                        list_nb_of_apartments[building_id] = random.randint(7, 10)
                    elif nb_of_apartments == 8:
                        list_nb_of_apartments[building_id] = random.randint(11, 12)

                else:
                    list_nb_of_apartments[building_id] = 9

            elif building_id in high_rise_houses:
                nb_of_floors = numpy.random.choice(numpy.arange(6, 9), p=[0.25, 0.5,
                                                                          0.25])  # --> 1. Quartil till 3. Quartil of Manfred Heggers "Energetische Stadtraumtypen" of EST 4 "Anzahl Vollgeschosse"
                if nb_of_floors == 6:
                    list_nb_of_floors[building_id] = random.randint(7, 8)
                    list_nb_of_apartments[building_id] = random.randint(29,
                                                                        34)  # --> Min to Max of Manfred Heggers "Energetische Stadtraumtypen" of EST 4 "Anzahl Wohneinheiten", calculated through the Median of the nb of buildings per hectar.
                elif nb_of_floors == 7:
                    list_nb_of_floors[building_id] = random.randint(8, 11)
                    max_nb_of_apartments = round(
                        0.812 * list_nb_of_floors[building_id] * city.nodes[building_id]["area"] / 25)
                    if max_nb_of_apartments <= 35:
                        list_nb_of_apartments[building_id] = max_nb_of_apartments
                    elif max_nb_of_apartments >= 55:
                        list_nb_of_apartments[building_id] = random.randint(35, 55)
                    else:
                        list_nb_of_apartments[building_id] = random.randint(35, max_nb_of_apartments)
                else:
                    list_nb_of_floors[building_id] = random.randint(11, 19)
                    max_nb_of_apartments = round(
                        0.812 * list_nb_of_floors[building_id] * city.nodes[building_id]["area"] / 25)
                    if max_nb_of_apartments <= 56:
                        list_nb_of_apartments[building_id] = max_nb_of_apartments
                    elif max_nb_of_apartments >= 110:
                        list_nb_of_apartments[building_id] = random.randint(56, 110)  # --> might be to high !
                    else:
                        list_nb_of_apartments[building_id] = random.randint(56, max_nb_of_apartments)

            # district type "RESIDENTIAL"
            elif city_district[building_id] == "residential":
                list_nb_of_floors[building_id] = 2.5
                list_nb_of_apartments[building_id] = numpy.random.choice(numpy.arange
                                                       (4, 7), p=[0.25, 0.5,
                                                                  0.25])  # --> Min to Max of Manfred Heggers "Energetische Stadtraumtypen" of EST 1b

            # District type "INNER CITY"
            elif city_district[building_id] == "inner city":
                list_nb_of_floors[building_id] = numpy.random.choice(numpy.arange(3, 5), p=[0.75, 0.25])

                nb_of_apartments = numpy.random.choice(numpy.arange(6, 9), p=[0.25, 0.5,
                                                                              0.25])  # --> Min to Max of Manfred Heggers "Energetische Stadtraumtypen" of EST "Innenstadt"
                if nb_of_apartments == 6:
                    list_nb_of_apartments[building_id] = random.randint(4, 6)
                elif nb_of_apartments == 7:
                    list_nb_of_apartments[building_id] = random.randint(7, 10)
                elif nb_of_apartments == 8:
                    list_nb_of_apartments[building_id] = random.randint(11, 12)

            else:
                list_nb_of_floors[building_id] = 3
                list_nb_of_apartments[building_id] = 9

        elif building_id in commercial or building_id in individual_buildings:
            #  Add single apartment to prevent problems in further processing
            #  within pycity
            list_nb_of_apartments[building_id] = 1
            dict_nb_of_apartments_with_occupants[building_id] = 0

        else:
            print("Building is neither SGH nor MFH")

    if user_defined_number_of_apartments == True:
        counter_total_apart = 0
        for building_id in nodelist_buildings:
            counter_total_apart += list_nb_of_apartments[building_id]

        difference_apart = specified_number_apartments - counter_total_apart

        while difference_apart > 0:
            random_building_id = random.choice(nodelist_buildings)

            if random_building_id in single_family_house and list_nb_of_apartments[random_building_id] == 1:
                list_nb_of_apartments[random_building_id] += 1
                difference_apart -= 1
                break
            elif random_building_id in multi_family_houses and list_nb_of_apartments[random_building_id] < 12:
                list_nb_of_apartments[random_building_id] += 1
                difference_apart -= 1
                break
            elif random_building_id in high_rise_houses and list_nb_of_apartments[random_building_id] < 110:
                list_nb_of_apartments[random_building_id] += 1
                difference_apart -= 1
                break
            else:
                continue

        while difference_apart < 0:
            random_building_id = random.choice(nodelist_buildings)

            if random_building_id in single_family_house and list_nb_of_apartments[random_building_id] == 1:
                list_nb_of_apartments[random_building_id] -= 1
                difference_apart += 1
                break
            elif random_building_id in multi_family_houses and list_nb_of_apartments[random_building_id] > 4:
                list_nb_of_apartments[random_building_id] -= 1
                difference_apart += 1
                break
            elif random_building_id in high_rise_houses and list_nb_of_apartments[random_building_id] > 12:
                list_nb_of_apartments[random_building_id] -= 1
                difference_apart += 1
                break
            else:
                continue

    # NB of OCCUPANTS
    for building_id in nodelist_buildings:

        # If building has apartment enrich those with occupants
        if dict_nb_of_apartments_with_occupants[building_id] == {}:
            dict_nb_of_apartments_with_occupants = get_nb_of_occupants(city=city, building_id=building_id,
                                                                       list_nb_of_floors=list_nb_of_floors,
                                                                       list_nb_of_apartments=list_nb_of_apartments,
                                                                       dict_nb_of_apartments_with_occupants=dict_nb_of_apartments_with_occupants)
        # Building does not have apartments and therefore no occupants
        else:
            pass

    if user_defined_number_of_occupants == True:
        counter_total_occ = 0
        for building_id in nodelist_buildings:
            for i in range(0, list_nb_of_apartments[building_id]):
                counter_total_occ += dict_nb_of_apartments_with_occupants[building_id][i]

        difference_occ = specified_number_occupants - counter_total_occ

        while difference_occ > 0:
            random_building_id = random.choice(nodelist_buildings)

            for i in range(0, list_nb_of_apartments[random_building_id]):
                if dict_nb_of_apartments_with_occupants[random_building_id][i] <= 4:
                    dict_nb_of_apartments_with_occupants[random_building_id][i] += 1
                    difference_occ -= 1
                    break
                else:
                    continue

        while difference_occ < 0:
            random_building_id = random.choice(nodelist_buildings)

            for i in range(0, list_nb_of_apartments[random_building_id]):
                if dict_nb_of_apartments_with_occupants[random_building_id][i] >= 2:
                    dict_nb_of_apartments_with_occupants[random_building_id][i] -= 1
                    difference_occ += 1
                    break
                else:
                    continue

    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------


    for building_id in nodelist_buildings:

        # # Generate environment
        # environment = citgen.generate_environment(timestep=timestep, year=year, try_path=try_path, location=location, altitude=altitude)

        # SINGLE FAMILY HOUSE

        if building_id in single_family_house:

            # RETROFIT STATE

            build_year = build_year_buildings[building_id]

            mod_year, retrofit_state = get_retrofit_state_sfh(build_year = build_year, user_defined_mod_year = user_defined_mod_year,
                                    specified_range_mod_year_beginning = specified_range_mod_year_beginning,
                                    specified_range_mod_year_end = specified_range_mod_year_end, mod_year_method=mod_year_method, range_of_mod_years=range_of_mod_years, forced_modification=forced_modification, forced_modification_after=forced_modification_after)

            if save_city_CSV == True:
                building_parameters_for_analysis[building_id]["id"] = (building_id)
                building_parameters_for_analysis[building_id]["X"] = (city.nodes[building_id]["position"].x)
                building_parameters_for_analysis[building_id]["Y"] = (city.nodes[building_id]["position"].y)
                if build_type_buildings[building_id] == []:
                    building_parameters_for_analysis[building_id]["building_type"] = 0
                else:
                    building_parameters_for_analysis[building_id]["building_type"] = build_type_buildings[building_id]

                # Netto floor area has the factor 0.812 of the total floor area of the building  (Udo Blecken in "Grundflächen und Planungskennwerte von Wohngebäuden" in Abb. 1)
                building_parameters_for_analysis[building_id]["net_floor_area"] = (
                    int(city.nodes[building_id]["area"]) * 0.812 * list_nb_of_floors[building_id])
                building_parameters_for_analysis[building_id]["build_year"] = build_year_buildings[building_id]
                building_parameters_for_analysis[building_id]["mod_year"] = mod_year
                building_parameters_for_analysis[building_id][
                    "retrofit_state"] = retrofit_state
                if number_neighbour_buildings[building_id] == 0:
                    building_parameters_for_analysis[building_id]["building"] = "SFH_detached"
                elif number_neighbour_buildings[building_id] == 1 and number_neighbour_buildings[
                    buildings_neighbours[building_id][0]] == 1:
                    building_parameters_for_analysis[building_id]["building"] = "DH"
                elif number_neighbour_buildings[building_id] == 1 and number_neighbour_buildings[
                    buildings_neighbours[building_id][0]] == 2:
                    building_parameters_for_analysis[building_id][
                        "building"] = "Terrace_building"
                elif number_neighbour_buildings[building_id] == 2:
                    building_parameters_for_analysis[building_id][
                        "building"] = "Terrace_building"
                building_parameters_for_analysis[building_id]["Usable_pv_roof_area_in_m2"] = 0.5 * city.nodes[building_id]["area"]
                building_parameters_for_analysis[building_id]["Number_of_apartments"] = list_nb_of_apartments[building_id]
                counter_occ = 0
                for i in range(0, list_nb_of_apartments[building_id]):
                    counter_occ += dict_nb_of_apartments_with_occupants[building_id][i]
                building_parameters_for_analysis[building_id]["Total_number_of_occupants"] = counter_occ
                building_parameters_for_analysis[building_id]["Number_of_floors"] = list_nb_of_floors[building_id]
                building_parameters_for_analysis[building_id]["Height_of_floors"] = floor_height_buildings[building_id]
                building_parameters_for_analysis[building_id]["with_ahu"] = city_district[building_id]
                building_parameters_for_analysis[building_id]["residential_layout"] = 0
                if number_neighbour_buildings[building_id] <= 2:
                    building_parameters_for_analysis[building_id]["neighbour_buildings"] = number_neighbour_buildings[
                        building_id]
                else:
                    building_parameters_for_analysis[building_id]["neighbour_buildings"] = 2
                building_parameters_for_analysis[building_id]["attic"] = attic_buildings[building_id]
                building_parameters_for_analysis[building_id]["cellar"] = cellar_buildings[building_id]
                building_parameters_for_analysis[building_id]["dormer"] = dormer_buildings[building_id]
                building_parameters_for_analysis[building_id]["construction_type"]
                if building_id in addr_building_found:
                    building_parameters_for_analysis[building_id]["method_3_type"] = city.nodes[building_id]["addr_street"]
                else:
                    building_parameters_for_analysis[building_id]["method_3_type"]
                if building_id in house_nb_building_found:
                    building_parameters_for_analysis[building_id]["method_4_type"] = city.nodes[building_id]["addr_housenumber"]
                else:
                    building_parameters_for_analysis[building_id]["method_4_type"]

            build_year = build_year_buildings[building_id]
            mod_year = mod_year
            if build_type_buildings[building_id] == []:
                build_type = 0
            else:
                build_type =  build_type_buildings[building_id]
            ground_area = city.nodes[building_id]["area"]

            # Usable roof area equates to half of the ground area
            # "Abschätzung des Photovoltaik-Potentials auf Dachflächen in Deutschland" of Lödl at al.
            # https: // mediatum.ub.tum.de / doc / 969497 / 969497.pdf
            pv_use_area = city.nodes[building_id]["area"] * 0.5

            net_floor_area = city.nodes[building_id]["area"] * 0.812 * list_nb_of_floors[building_id]
            height_of_floors = floor_height_buildings[building_id]
            if number_neighbour_buildings[building_id] <= 2:
                neighbour_buildings = number_neighbour_buildings[building_id]
            else:
                neighbour_buildings = 2
            residential_layout = 0  # IWU standardised for SFH and TH
            attic = attic_buildings[building_id]
            cellar = cellar_buildings[building_id]
            construction_type = None
            dormer = dormer_buildings[building_id]
            curr_central_ahu = None
            retrofit_state = retrofit_state

            extended_building = \
                build_ex.BuildingExtended(city.environment,
                                          build_year=build_year,
                                          mod_year=mod_year,
                                          build_type=build_type,
                                          roof_usabl_pv_area=pv_use_area,
                                          ground_area = ground_area, net_floor_area=net_floor_area,
                                          height_of_floors=height_of_floors,
                                          nb_of_floors=list_nb_of_floors[building_id],
                                          neighbour_buildings=neighbour_buildings,
                                          residential_layout=residential_layout,
                                          attic=attic,
                                          cellar=cellar,
                                          construction_type=construction_type,
                                          dormer=dormer,
                                          with_ahu=
                                          curr_central_ahu, retrofit_state= retrofit_state)

            # Create apartment
            for apart in range(0, int(list_nb_of_apartments[building_id])):

                number_occupants = dict_nb_of_apartments_with_occupants[building_id][apart]
                occupancy_object = occup.Occupancy(city.environment,
                                                   number_occupants=number_occupants)

                apartment = Apartment.Apartment(city.environment, occupancy=occupancy_object,
                                                net_floor_area=net_floor_area)

                #  Add apartment to extended building
                extended_building.addEntity(entity=apartment)

            # Add extended building to city
            city.nodes[building_id]["entity"] = extended_building

            continue

    # ---------------------------------------------------------------------------

        # MULTI FAMILY HOUSE
        elif building_id in multi_family_houses or building_id in high_rise_houses:

            # RETROFIT STATE

            build_year = build_year_buildings[building_id]

            mod_year, retrofit_state = get_retrofit_state_mfh(build_year = build_year, user_defined_mod_year = user_defined_mod_year,
                                    specified_range_mod_year_beginning = specified_range_mod_year_beginning,
                                    specified_range_mod_year_end = specified_range_mod_year_end, mod_year_method=mod_year_method, range_of_mod_years=range_of_mod_years, forced_modification=forced_modification, forced_modification_after=forced_modification_after)


            # just for the CSV file
            if save_city_CSV == True:
                building_parameters_for_analysis[building_id]["id"] = (building_id)
                building_parameters_for_analysis[building_id]["X"] = (city.nodes[building_id]["position"].x)
                building_parameters_for_analysis[building_id]["Y"] = (city.nodes[building_id]["position"].y)


                if build_type_buildings[building_id] ==[]:
                    building_parameters_for_analysis[building_id]["building_type"] = 0
                else:
                    building_parameters_for_analysis[building_id]["building_type"] = build_type_buildings[building_id]
                building_parameters_for_analysis[building_id]["net_floor_area"] = (
                    int(city.nodes[building_id]["area"]) * 0.812 * list_nb_of_floors[building_id])
                building_parameters_for_analysis[building_id]["build_year"] = build_year_buildings[building_id]
                building_parameters_for_analysis[building_id]["mod_year"] = mod_year
                building_parameters_for_analysis[building_id][
                    "retrofit_state"] = retrofit_state

                if building_id in high_rise_houses:
                    building_parameters_for_analysis[building_id]["building"] = "High_rise"
                else:
                    building_parameters_for_analysis[building_id]["building"] = "MFH"
                building_parameters_for_analysis[building_id]["Usable_pv_roof_area_in_m2"] = 0.5 * city.nodes[building_id]["area"]
                building_parameters_for_analysis[building_id]["Number_of_apartments"] = list_nb_of_apartments[building_id]
                counter_occ = 0
                for i in range(0, list_nb_of_apartments[building_id]):
                    counter_occ += dict_nb_of_apartments_with_occupants[building_id][i]
                building_parameters_for_analysis[building_id]["Total_number_of_occupants"] = counter_occ
                building_parameters_for_analysis[building_id]["Number_of_floors"] = list_nb_of_floors[building_id]
                building_parameters_for_analysis[building_id]["Height_of_floors"] = floor_height_buildings[building_id]
                building_parameters_for_analysis[building_id]["with_ahu"]  = city_district[building_id]
                building_parameters_for_analysis[building_id]["residential_layout"]
                if number_neighbour_buildings[building_id] <= 2:
                    building_parameters_for_analysis[building_id]["neighbour_buildings"] = number_neighbour_buildings[
                        building_id]
                else:
                    building_parameters_for_analysis[building_id]["neighbour_buildings"] = 2
                building_parameters_for_analysis[building_id]["attic"] = attic_buildings[building_id]
                building_parameters_for_analysis[building_id]["cellar"] = cellar_buildings[building_id]
                building_parameters_for_analysis[building_id]["dormer"] = dormer_buildings[building_id]
                building_parameters_for_analysis[building_id]["construction_type"]
                if building_id in addr_building_found:
                    building_parameters_for_analysis[building_id]["method_3_type"] = city.nodes[building_id]["addr_street"]
                else:
                    building_parameters_for_analysis[building_id]["method_3_type"]
                if building_id in house_nb_building_found:
                    building_parameters_for_analysis[building_id]["method_4_type"] = city.nodes[building_id]["addr_housenumber"]
                else:
                    building_parameters_for_analysis[building_id]["method_4_type"]


            build_year = build_year_buildings[building_id]
            mod_year = mod_year
            height_of_floors = floor_height_buildings[building_id]
            if build_type_buildings[building_id] == []:
                build_type = 0
            else:
                build_type =  build_type_buildings[building_id]

            # Usable roof area equates to half of the ground area
            # "Abschätzung des Photovoltaik-Potentials auf Dachflächen in Deutschland" of Lödl at al.
            # https: // mediatum.ub.tum.de / doc / 969497 / 969497.pdf
            pv_use_area = city.nodes[building_id]["area"] * 0.5
            net_floor_area = city.nodes[building_id]["area"] * 0.812 * list_nb_of_floors[building_id]

            if number_neighbour_buildings[building_id] <= 2:
                neighbour_buildings = number_neighbour_buildings[building_id]
            else:
                neighbour_buildings =  2

            residential_layout = None
            attic = attic_buildings[building_id]
            cellar = cellar_buildings[building_id]
            construction_type = None
            dormer = dormer_buildings[building_id]
            curr_central_ahu = None
            retrofit_state = retrofit_state

            extended_building = \
                build_ex.BuildingExtended(city.environment,
                                          build_year=build_year,
                                          mod_year=mod_year,
                                          build_type=build_type,
                                          roof_usabl_pv_area=pv_use_area,
                                          net_floor_area=net_floor_area,
                                          height_of_floors=height_of_floors,
                                          nb_of_floors=list_nb_of_floors[building_id],
                                          neighbour_buildings=neighbour_buildings,
                                          residential_layout=residential_layout,
                                          attic=attic,
                                          cellar=cellar,
                                          construction_type=construction_type,
                                          dormer=dormer,
                                          with_ahu=
                                          curr_central_ahu, retrofit_state= retrofit_state)


            for apart in range(0, list_nb_of_apartments[building_id]):

                number_occupants = dict_nb_of_apartments_with_occupants[building_id][apart]

                occupancy_object = occup.Occupancy(city.environment,
                                                   number_occupants=number_occupants)

                # Create apartments

                apartment = Apartment.Apartment(city.environment, occupancy=occupancy_object,
                                                net_floor_area=net_floor_area)

                apartment.get_power_curves(
                    getElectrical=user_defined_el_demand,
                    getDomesticHotWater=user_defined_dhw,
                    getSpaceheating=user_defined_therm_demand,
                    currentValues=True)

                #  Add apartment to extended building
                extended_building.addEntity(entity=apartment)

            # Add extended building to city
            city.nodes[building_id]["entity"] = extended_building

            continue

        # ------------------------------------------------------------------------------------------------------------------

        # NON RESIDENTIAL
        elif building_id in commercial or building_id in individual_buildings:

            # BUILD TYPE
            build_type = build_type_buildings[building_id]

            # NUMBER of FLOORS AND APARTMENTS and BUILD YEAR and HEIGHT OF FLOORS
            # depend on the number of floors of the neighbour buildings. Expecting the number of floors as the most floors in the area.

            nb_of_floor_non_res = []

            if number_neighbour_buildings[building_id] >=1 and  buildings_neighbours[building_id] != []:
                for i in range(0, len(buildings_neighbours[building_id])):
                    if list_nb_of_floors[buildings_neighbours[building_id][i]] != []:
                        list_nb_of_floors[building_id] = list_nb_of_floors[buildings_neighbours[building_id][i]]

                    else:
                        for buildings_in_square in building_list_within_spezified_square[building_id]:
                            if buildings_in_square not in high_rise_houses and list_nb_of_floors[buildings_in_square] != []:
                                list_nb_of_floors[building_id] = list_nb_of_floors[buildings_in_square]


                            else:
                                list_nb_of_floors[building_id] = 3

            elif building_list_within_spezified_square[building_id] != []:
                nb_of_floor_non_res = []
                for buildings_in_square in building_list_within_spezified_square[building_id]:
                    if list_nb_of_floors[buildings_in_square] != [] and buildings_in_square in high_rise_houses:
                        nb_of_floor_non_res.append(list_nb_of_floors[buildings_in_square])
                        list_nb_of_floors[building_id] = sorted(nb_of_floor_non_res)[-1]

                    else:
                        list_nb_of_floors[building_id] = random.randint(1,7) #--> Nb of floors for Non_res of Manfred Heggers

            else:
                list_nb_of_floors[building_id] = random.randint(1,7)  # --> Nb of floors for Non_res of Manfred Heggers

            if building_id in buildings_with_levels:
                if "." in city.nodes[building_id]["building_levels"]:
                    list_nb_of_floors[building_id] = float(city.nodes[building_id]["building_levels"])
                else:
                    list_nb_of_floors[building_id] = int(city.nodes[building_id]["building_levels"])

            # MOD YEAR and RETROFIT STATE
            # based on the data of MFH

            build_year = build_year_buildings[building_id]

            mod_year, retrofit_state = get_retrofit_state_mfh(build_year=build_year, user_defined_mod_year=user_defined_mod_year,
                                                    specified_range_mod_year_beginning=specified_range_mod_year_beginning,
                                                    specified_range_mod_year_end=specified_range_mod_year_end, mod_year_method=mod_year_method, range_of_mod_years=range_of_mod_years, forced_modification=forced_modification, forced_modification_after=forced_modification_after)

            # just for the CSV file
            if save_city_CSV == True:
                building_parameters_for_analysis[building_id]["id"] = (building_id)
                building_parameters_for_analysis[building_id]["X"] = (city.nodes[building_id]["position"].x)
                building_parameters_for_analysis[building_id]["Y"] = (city.nodes[building_id]["position"].y)
                building_parameters_for_analysis[building_id]["building_type"] = build_type
                building_parameters_for_analysis[building_id]["net_floor_area"] = (
                    int(city.nodes[building_id]["area"]) * 0.812 * list_nb_of_floors[building_id])
                building_parameters_for_analysis[building_id]["build_year"] = build_year_buildings[building_id]
                building_parameters_for_analysis[building_id]["mod_year"] = mod_year
                building_parameters_for_analysis[building_id][
                    "retrofit_state"] = retrofit_state
                building_parameters_for_analysis[building_id]["building"] = "Non_residential"
                building_parameters_for_analysis[building_id]["Usable_pv_roof_area_in_m2"] = 0.5 * city.nodes[building_id]["area"]
                building_parameters_for_analysis[building_id]["Number_of_apartments"] = 0
                building_parameters_for_analysis[building_id]["Total_number_of_occupants"] = 0
                building_parameters_for_analysis[building_id]["Number_of_floors"] = list_nb_of_floors[building_id]
                building_parameters_for_analysis[building_id]["Height_of_floors"] = floor_height_buildings[building_id]
                building_parameters_for_analysis[building_id]["with_ahu"] = city_district[building_id]
                building_parameters_for_analysis[building_id]["residential_layout"]
                if number_neighbour_buildings[building_id] <= 2:
                    building_parameters_for_analysis[building_id]["neighbour_buildings"] = number_neighbour_buildings[
                        building_id]
                else:
                    building_parameters_for_analysis[building_id]["neighbour_buildings"] = 2
                building_parameters_for_analysis[building_id]["attic"]
                building_parameters_for_analysis[building_id]["cellar"]
                building_parameters_for_analysis[building_id]["dormer"]
                building_parameters_for_analysis[building_id]["construction_type"]
                if building_id in addr_building_found:
                    building_parameters_for_analysis[building_id]["method_3_type"] = city.nodes[building_id]["addr_street"]
                else:
                    building_parameters_for_analysis[building_id]["method_3_type"]
                if building_id in house_nb_building_found:
                    building_parameters_for_analysis[building_id]["method_4_type"] = city.nodes[building_id]["addr_housenumber"]
                else:
                    building_parameters_for_analysis[building_id]["method_4_type"]

            build_year = build_year_buildings[building_id]
            mod_year = mod_year
            height_of_floors = floor_height_buildings[building_id]
            build_type = build_type

            # Usable roof area equates to half of the ground area
            # "Abschätzung des Photovoltaik-Potentials auf Dachflächen in Deutschland" of Lödl at al.
            # https: // mediatum.ub.tum.de / doc / 969497 / 969497.pdf
            pv_use_area = city.nodes[building_id]["area"] * 0.5
            net_floor_area = city.nodes[building_id]["area"] * 0.812 * list_nb_of_floors[building_id]
            if number_neighbour_buildings[building_id] <= 2:
                neighbour_buildings = number_neighbour_buildings[building_id]
            else:
                neighbour_buildings =  2
            residential_layout = None
            attic = None
            cellar = None
            construction_type = None
            dormer = None
            curr_central_ahu = None
            retrofit_state = retrofit_state

            extended_building = \
                build_ex.BuildingExtended(city.environment,
                                          build_year=build_year,
                                          mod_year=mod_year,
                                          build_type=build_type,
                                          roof_usabl_pv_area=pv_use_area,
                                          net_floor_area=net_floor_area,
                                          height_of_floors=height_of_floors,
                                          nb_of_floors=list_nb_of_floors[building_id],
                                          neighbour_buildings=neighbour_buildings,
                                          residential_layout=residential_layout,
                                          attic=attic,
                                          cellar=cellar,
                                          construction_type=construction_type,
                                          dormer=dormer,
                                          with_ahu=
                                          curr_central_ahu, retrofit_state= retrofit_state)


            for apartment in range(0, list_nb_of_apartments[building_id]):

                occupancy_object = None  # Dummy value for non-residential

                # Create apartments
                apartment = Apartment.Apartment(city.environment,
                                                occupancy=occupancy_object,
                                                net_floor_area=net_floor_area)

                #  Add apartment to extended building
                extended_building.addEntity(entity=apartment)

            # Add extended building to city
            city.nodes[building_id]["entity"] = extended_building

            continue


    # Prints of Data Enrichment

    # MFHs regarding their ground floor area
    mfh_very_small = []             # old town              A < 110 m^2
    mfh_small = []                  # residential area      110 < A < 140 m^2
    mfh_medium = []                 # inner city            140 < A < 437 m^2
    mfh_large = []                  # high rise

    #build_year
    build_year_of_all = []

    # occupants
    occ_mfh = []
    occ_high_rise = []
    occ_sfh = []
    occ_detached_sfh = []
    occ_double = []
    occ_terraced = []
    occ_non_res = []

    # occupants
    apart_mfh = []
    apart_high_rise = []
    apart_sfh = []
    apart_detached_sfh = []
    apart_double = []
    apart_terraced = []
    apart_non_res = []

    print("DATA ENRICHMENT")

    print()
    print("Building distribution")
    print()

    print("Number of  SFH: ", len(single_family_house), "   and percentage regarding all buildings: ", (len(single_family_house)/len(nodelist_buildings)*100), " %")
    print("Number of detached SFH: ", len(detached_single_family_houses), "and percentage regarding all buildings: ", (len(detached_single_family_houses)/len(nodelist_buildings)*100), " %")
    print("Number of Double House: ", len(double_houses), "and percentage regarding all buildings: ", (len(double_houses)/len(nodelist_buildings)*100), " %")
    print("Number of Terrace buildings: ", len(terraced_houses), "and percentage regarding all buildings: ", (len(terraced_houses)/len(nodelist_buildings)*100), " %")
    print()
    print("Number of MFH: ", len(multi_family_houses), "and percentage regarding all buildings: ", (len(multi_family_houses)/len(nodelist_buildings)*100), " %")
    print("Number of High rise building: ", len(high_rise_houses), "and percentage regarding all buildings: ", (len(high_rise_houses)/len(nodelist_buildings)*100), " %")

    for i in multi_family_houses:
        if city.nodes[i]["area"] <= 110:
            mfh_very_small.append(i)
        elif 110 < city.nodes[i]["area"] < 140:
            mfh_small.append(i)
        elif 140 < city.nodes[i]["area"] < 437:
            mfh_medium.append(i)
        else:
            mfh_large.append(i)

    if len(multi_family_houses) > 0:
        print("Number of MFH with an area < 110 m^2: ", len(mfh_very_small), "and their percentage: ", (len(mfh_very_small) / len(multi_family_houses)* 100))
        print("Number of MFH with an area in between 110 and 140 m^2: ", len(mfh_small), "and their percentage: ",
              (len(mfh_small) / len(multi_family_houses) * 100))
        print("Number of MFH with an area in between 140 and 437 m^2: ", len(mfh_medium), "and their percentage: ",
              (len(mfh_medium) / len(multi_family_houses) * 100))
        print("Number of MFH with an area > 437 m^2 : ", len(mfh_large), "and their percentage: ",
              (len(mfh_large) / len(multi_family_houses) * 100))

    print()
    print("Number of Commericial buildings: ", len(commercial), "and percentage regarding all buildings: ", (len(commercial)/len(nodelist_buildings)*100), " %")
    print("Number of individual buildings: ", len(individual_buildings), "and percentage regarding all buildings: ",
          (len(individual_buildings) / len(nodelist_buildings)*100), " %")

    print()
    print("Nb of buildings in residential city area", counter_res)
    print("Nb of buildings in inner city area", counter_inner_city)
    print("Nb of buildings in non residential city area", counter_non_res)

    print()
    print()
    print("BUILD YEAR")

    list_before_1890 = []
    list_1890_1918 = []
    list_1919_1948 = []
    list_1949_1958 = []
    list_1959_1968 = []
    list_1969_1978 = []
    list_1979_1983 = []
    list_1984_1994 = []
    list_1995_2001 = []
    list_2002_2008 = []
    list_after_2009 = []


    # build year
    for building_id in nodelist_buildings:
        build_year_of_all.append(build_year_buildings[building_id])

        if build_year_buildings[building_id]  <= 1890:
            list_before_1890.append(building_id)
        elif 1890 < build_year_buildings[building_id] <=1918:
            list_1890_1918.append(building_id)
        elif 1918 < build_year_buildings[building_id] <= 1948:
            list_1919_1948.append(building_id)
        elif 1948 < build_year_buildings[building_id] <= 1958:
            list_1949_1958.append(building_id)
        elif 1958 < build_year_buildings[building_id] <= 1968:
            list_1959_1968.append(building_id)
        elif 1968 < build_year_buildings[building_id] <= 1978:
            list_1969_1978.append(building_id)
        elif 1978 < build_year_buildings[building_id] <= 1983:
            list_1979_1983.append(building_id)
        elif 1983 < build_year_buildings[building_id] <= 1994:
            list_1984_1994.append(building_id)
        elif 1994 < build_year_buildings[building_id] <= 2001:
            list_1995_2001.append(building_id)
        elif 2001 < build_year_buildings[building_id] <= 2008:
            list_2002_2008.append(building_id)
        elif 2008 < build_year_buildings[building_id]:
            list_after_2009.append(building_id)


    # ##  PLOT CITY DISTRICT
    # # for plotting code underneath has to be untagged
    # citvis.plot_city_district(city=city, nodelist=nodelist_buildings, list_before_1890 ,list_1890_1918 ,list_1919_1948 ,list_1949_1958 , list_1959_1968 ,list_1969_1978 ,list_1979_1983, list_1984_1994 ,list_1995_2001,list_2002_2008,list_after_2009 , node_size=50, plot_build_labels=False,
    #                           save_plot=True, plt_title="Baujahrsverteilung")


    print()
    distribution_build_year_of_all = Counter(build_year_of_all)
    print("Distribution of the build year of all building", distribution_build_year_of_all)
    print()

    # Apartments
    for building_id in nodelist_buildings:
        if building_id in multi_family_houses:
            if building_id in high_rise_houses:
                apart_high_rise.append(list_nb_of_apartments[building_id])
            else:
                apart_mfh.append(list_nb_of_apartments[building_id])
        elif building_id in single_family_house:
            apart_sfh.append(list_nb_of_apartments[building_id])
            if building_id in terraced_houses:
                apart_terraced.append(list_nb_of_apartments[building_id])
            elif building_id in detached_single_family_houses:
                apart_detached_sfh.append(list_nb_of_apartments[building_id])
            elif building_id in double_houses:
                apart_double.append(list_nb_of_apartments[building_id])
        elif building_id in commercial or building_id in individual_buildings:
            apart_non_res.append(list_nb_of_apartments[building_id])

    print()
    print("APARTMENTS")
    print()
    distribution_apart_mfh = Counter(apart_mfh)
    print("Distribution apartments MFH", distribution_apart_mfh)
    distribution_apart_high_rise = Counter(apart_high_rise)
    print("Distribution apartments High rise", distribution_apart_high_rise)
    print()
    distribution_apart_sfh = Counter(apart_sfh)
    distribution_apart_sfh_detached = Counter(apart_detached_sfh)
    print("Distribution apartments detached SFH", distribution_apart_sfh_detached)
    print("Distribution apartments SFH", distribution_apart_sfh)
    distribution_apart_terraced = Counter(apart_terraced)
    print("Distribution apartments terraced buildings", distribution_apart_terraced)
    distribution_apart_double = Counter(apart_double)
    print("Distribution apartments double houses", distribution_apart_double)
    print()
    distribution_apart_non_res = Counter(apart_non_res)
    print("Distribution apartments Non residential", distribution_apart_non_res)

    # Occupants
    for building_id in nodelist_buildings:
        for apartment in range(0, list_nb_of_apartments[building_id]):
            if building_id in multi_family_houses:
                if building_id in high_rise_houses:
                    occ_high_rise.append(dict_nb_of_apartments_with_occupants[building_id][apartment])
                else:
                    occ_mfh.append(dict_nb_of_apartments_with_occupants[building_id][apartment])
            elif building_id in single_family_house:
                occ_sfh.append(dict_nb_of_apartments_with_occupants[building_id][apartment])
                if building_id in terraced_houses:
                    occ_terraced.append(dict_nb_of_apartments_with_occupants[building_id][apartment])
                elif building_id in detached_single_family_houses:
                    occ_detached_sfh.append(dict_nb_of_apartments_with_occupants[building_id][apartment])
                elif building_id in double_houses:
                    occ_double.append(dict_nb_of_apartments_with_occupants[building_id][apartment])
            # elif building_id in commercial or building_id in individual_buildings:
            #     occ_non_res.append(dict_nb_of_apartments_with_occupants[building_id][apartment])

    print()
    print("OCCUPANTS")
    print()
    distribution_occ_mfh = Counter(occ_mfh)
    print("Distribution occupants MFH", distribution_occ_mfh)
    distribution_occ_high_rise = Counter(occ_high_rise)
    print("Distribution occupants High rise", distribution_occ_high_rise)
    print()
    distribution_occ_sfh = Counter(occ_sfh)
    distribution_occ_sfh_detached = Counter(occ_detached_sfh)
    print("Distribution occupants detached SFH", distribution_occ_sfh_detached)
    print("Distribution occupants SFH", distribution_occ_sfh)
    distribution_occ_terraced = Counter(occ_terraced)
    print("Distribution occupants terraced buildings", distribution_occ_terraced)
    distribution_occ_double = Counter(occ_double)
    print("Distribution occupants double houses", distribution_occ_double)
    print()


    print()
    print("OTHERS")
    print()
    print("list_nb_of_floors", list_nb_of_floors)
    print("Distribution nb of floors", Counter(list_nb_of_floors.values()))
    print("floor_height_buildings", floor_height_buildings)
    # print("Distribution floor height", Counter(floor_height_buildings.values()))

    print("cropped_area_within_square", cropped_area_within_square)
    print("percentage_cropped_area_within_square", percentage_cropped_area_within_square)

    print()
    print("____________________________________________")
    print()
    print("End of Data Enrichtment")



    return building_parameters_for_analysis, individual_buildings, single_family_house, detached_single_family_houses, terraced_houses, double_houses,multi_family_houses,high_rise_houses, commercial, city_district


def put_building_data_into_csv(city, csv_filename, osm_path, zone_number, min_house_area, considered_area_around_a_building,  user_defined_building_distribution, \
                    percentage_sfh, percentage_mfh, percentage_non_res, specific_buildings, user_defined_build_year,\
                    specified_build_year_beginning, specified_build_year_end, user_defined_mod_year, specified_range_mod_year_beginning,\
                    specified_range_mod_year_end, mod_year_method, range_of_mod_years, forced_modification, forced_modification_after,
                    user_defined_number_of_occupants ,specified_number_occupants, user_defined_number_of_apartments , specified_number_apartments, nodelist_buildings, deleted_buildings, timestep, year, try_path, location, altitude, generate_nodelist_from_function_of_citydistrict, save_city_CSV, user_defined_el_demand, user_defined_therm_demand, user_defined_dhw):
    building_parameters_for_analysis, individual_buildings, single_family_house, detached_single_family_houses, terraced_houses, double_houses,multi_family_houses,  high_rise_houses,  commercial, city_district \
        = data_enrichment(city=city, osm_path=osm_path, zone_number=zone_number, min_house_area=min_house_area, considered_area_around_a_building=considered_area_around_a_building, \
                          user_defined_building_distribution=user_defined_building_distribution,
                          percentage_sfh=percentage_sfh, \
                          percentage_mfh=percentage_mfh, percentage_non_res=percentage_non_res, \
                          specific_buildings=specific_buildings, \
                          user_defined_build_year=user_defined_build_year,
                          specified_build_year_beginning=specified_build_year_beginning, \
                          specified_build_year_end=specified_build_year_end,
                          user_defined_mod_year=user_defined_mod_year,
                          mod_year_method = mod_year_method, range_of_mod_years = range_of_mod_years, specified_range_mod_year_beginning=specified_range_mod_year_beginning, \
                          specified_range_mod_year_end=specified_range_mod_year_end,
                          forced_modification = forced_modification, forced_modification_after =forced_modification_after,
                          user_defined_number_of_occupants=user_defined_number_of_occupants, \
                          specified_number_occupants=specified_number_occupants,
                          user_defined_number_of_apartments=user_defined_number_of_apartments, \
                          specified_number_apartments=specified_number_apartments,  timestep=timestep, year=year, try_path=try_path, location=location, altitude=altitude, generate_nodelist_from_function_of_citydistrict=generate_nodelist_from_function_of_citydistrict, save_city_CSV=save_city_CSV, user_defined_el_demand=user_defined_el_demand, user_defined_therm_demand=user_defined_therm_demand, user_defined_dhw=user_defined_dhw)

    my_dict = building_parameters_for_analysis

    columns = ['X', 'Y', 'building_type', 'net_floor_area', 'build_year', \
               'mod_year', 'retrofit_state', 'building', \
               'Usable_pv_roof_area_in_m2', 'Number_of_apartments', 'Total_number_of_occupants', 'Number_of_floors', \
               'Height_of_floors', 'with_ahu', 'residential_layout', 'neighbour_buildings', 'attic', 'cellar', 'dormer', \
               'construction_type', 'method_3_type', 'method_4_type']

    df = pd.DataFrame(my_dict).T.reindex(columns=columns)
    df.to_csv(csv_filename, sep='\t', na_rep=" ")


if __name__ == '__main__':
    main()




