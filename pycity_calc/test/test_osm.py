#!/usr/bin/env python
# coding=utf-8
"""
Pytest script for city generators
"""
from __future__ import division
import os

import pycity_calc.cities.scripts.osm_call as osm_call
import pycity_calc.cities.scripts.city_generator.city_generator as citgen
import pycity_calc.cities.scripts.city_generator_based_on_osm_files as osmgen

from pycity_calc.test.pycity_calc_fixtures import fixture_building, \
    fixture_environment, fixture_city, fixture_apartment, fixture_th_demand, \
    fixture_el_demand


class Test_OSM():
    def test_osm_call(self):

        this_path = os.path.dirname(os.path.abspath(__file__))

        #  Beginn of user input

        filename = 'example_ac.osm'

        file_path = os.path.join(this_path, 'input_generator', filename)

        min_allowed_ground_area = 50  # m2

        #  Add building entities?
        add_entities = True
        #  True: Add building object instances to building nodes
        #  False: Only use building nodes, do not generate building objects
        add_ap = True
        #  Add single apartment to every building (True/False)

        #  Parameters for environment
        timestep = 3600  # in seconds
        year = 2017
        location = (50.781743, 6.083470)
        altitude = 55
        try_path = None
        show_stats = False

        #   End of user input  ###############################################

        #  Generate environment
        environment = citgen.generate_environment(timestep=timestep,
                                                  year_timer=year,
                                                  year_co2=year,
                                                  try_path=try_path,
                                                  location=location,
                                                  altitude=altitude)

        #  Generate city topology based on osm data
        city = osm_call.gen_osm_city_topology(osm_path=file_path,
                                              environment=environment,
                                              min_area=min_allowed_ground_area,
                                              show_graph_stats=show_stats)

        #  If building entities should be added
        if add_entities:
            osm_call.add_build_entities(city=city, add_ap=add_ap)

    def test_osm_city_data_enrichment(self):

        # 1. osm filename

        filename = 'example_ac.osm'

        # 2. Minimal required building area in m2
        min_house_area = 50  # --> double garages eliminated ( 34,95 m^2)
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
        year = 2017

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
        specified_build_year_end = 1985

        # ------------------------------------------------------

        # 6. specified MOD YEAR after a certain time
        user_defined_mod_year = False
        mod_year_method = 1  # Methods are seen below

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
        forced_modification = True
        forced_modification_after = 40  # years

        # ------------------------------------------------------

        # 8. specified NUMBER of OCCUPANTS
        user_defined_number_of_occupants = True
        specified_number_occupants = 36

        # 9. specified NUMBER of APARTMENTS
        user_defined_number_of_apartments = True
        specified_number_apartments = 12

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
        considered_area_around_building = 10000  # 10000 m^2 is a hectar

        # 12. Variance for the comparision of the buildings with the same ground area
        variance_same_ground_area = 5

        # ------------------------------------------------------

        #  13. SAVE generated city object as PICKLE file?
        save_city = False
        city_filename = 'city_osm_ac.p'

        #  14. SAVE generated city object as CSV file?
        save_city_CSV = False
        csv_filename = str("city_generator/input/") + filename[:-4] + str(
            ".txt")

        ## 15. PLOT CITY DISTRICT
        # for plotting code underneath has to be untagged
        #
        # citvis.plot_city_district(city=city, node_size=10, plot_build_labels=False)

        # Used NODELIST
        # if true, generates nodes from CityDistrict-function "get_list_id_of_spec_node_type"
        # if false, generates node from city.nodelist_building

        generate_nodelist_from_function_of_citydistrict = True

        # END USER INPUT
        # ---------------------------------------------------------------------
        # ---------------------------------------------------------------------

        #  Convert lat/long to utm coordinates in meters?
        #  Only necessary, if no conversion is done within uesgraph itself
        conv_utm = False
        zone_number = 32

        this_path = os.path.dirname(os.path.abspath(__file__))
        osm_path = os.path.join(this_path, 'input_generator', filename)

        # Generate environment
        environment = citgen.generate_environment(timestep=timestep,
                                                  year_timer=year,
                                                  year_co2=year,
                                                  try_path=try_path,
                                                  location=location,
                                                  altitude=altitude,
                                                  new_try=new_try)

        #  Generate city topology based on osm data
        min_area = 0  # --> Do NOT change! Needed to get all buildings at first and to delete the small buildings later on.  The small buildings are needed for identification of the building types!
        city = osm_call.gen_osm_city_topology(osm_path=osm_path,
                                         environment=environment,
                                         name=None,
                                         check_boundary=False,
                                         min_area=min_area,
                                         show_graph_stats=True)

        if user_defined_building_distribution == True:
            print("User-defined city distrubution with", percentage_sfh,
                  " % SFH, ", percentage_mfh, "% MFH and ",
                  percentage_non_res, "% non residential buildings.")

        if user_defined_building_distribution == True and (
                        percentage_sfh + percentage_mfh + percentage_non_res) != 100:
            print("Sum of percentages is unequal 100.  Try again...")
            assert (user_defined_building_distribution == True and (
                percentage_sfh + percentage_mfh + percentage_non_res) != 100), "Sum of percentages is unequal 100.  Try again..."

        deleted_buildings, nodelist_buildings = osmgen.delete_not_relevant_buildings(
            city=city, min_house_area=min_house_area,
            generate_nodelist_from_function_of_citydistrict=generate_nodelist_from_function_of_citydistrict)

        if conv_utm:
            # Convert latitude, longitude to utm
            city = osm_call.conv_city_long_lat_to_utm(city, zone_number=zone_number)
            osmgen.conv_outlines_of_buildings_long_lat_to_utm(city=city,
                                                       zone_number=zone_number,
                                                       min_house_area=min_house_area,
                                                       nodelist_buildings=nodelist_buildings,
                                                       generate_nodelist_from_function_of_citydistrict=generate_nodelist_from_function_of_citydistrict)

        if save_city_CSV == False:
            # DEF data_enrichment
            osmgen.data_enrichment(city=city, osm_path=osm_path,
                            zone_number=zone_number,
                            min_house_area=min_house_area,
                            considered_area_around_a_building=considered_area_around_building, \
                            user_defined_building_distribution=user_defined_building_distribution, \
                            percentage_sfh=percentage_sfh,
                            percentage_mfh=percentage_mfh,
                            percentage_non_res=percentage_non_res, \
                            specific_buildings=specific_buildings, \
                            user_defined_build_year=user_defined_build_year,
                            specified_build_year_beginning=specified_build_year_beginning, \
                            specified_build_year_end=specified_build_year_end,
                            user_defined_mod_year=user_defined_mod_year,
                            mod_year_method=mod_year_method,
                            range_of_mod_years=range_of_mod_years,
                            specified_range_mod_year_beginning=specified_range_mod_year_beginning, \
                            specified_range_mod_year_end=specified_range_mod_year_end,
                            user_defined_number_of_occupants=user_defined_number_of_occupants, \
                            specified_number_occupants=specified_number_occupants,
                            user_defined_number_of_apartments=user_defined_number_of_apartments, \
                            specified_number_apartments=specified_number_apartments,
                            forced_modification=forced_modification,
                            forced_modification_after=forced_modification_after,
                            timestep=timestep, year=year, try_path=try_path,
                            location=location, altitude=altitude,
                            generate_nodelist_from_function_of_citydistrict=generate_nodelist_from_function_of_citydistrict,
                            save_city_CSV=save_city_CSV,
                            user_defined_el_demand=user_defined_el_demand,
                            user_defined_therm_demand=user_defined_therm_demand,
                            user_defined_dhw=user_defined_dhw)

        # DEF put_building_data_into_csv()
        if save_city_CSV == True:
            osmgen.put_building_data_into_csv(city=city, csv_filename=csv_filename,
                                       osm_path=osm_path,
                                       zone_number=zone_number,
                                       min_house_area=min_house_area,
                                       considered_area_around_a_building=considered_area_around_building, \
                                       user_defined_building_distribution=user_defined_building_distribution, \
                                       percentage_sfh=percentage_sfh,
                                       percentage_mfh=percentage_mfh,
                                       percentage_non_res=percentage_non_res, \
                                       specific_buildings=specific_buildings, \
                                       user_defined_build_year=user_defined_build_year,
                                       specified_build_year_beginning=specified_build_year_beginning, \
                                       specified_build_year_end=specified_build_year_end,
                                       user_defined_mod_year=user_defined_mod_year,
                                       specified_range_mod_year_beginning=specified_range_mod_year_beginning, \
                                       specified_range_mod_year_end=specified_range_mod_year_end,
                                       forced_modification=forced_modification,
                                       forced_modification_after=forced_modification_after,
                                       user_defined_number_of_occupants=user_defined_number_of_occupants, \
                                       specified_number_occupants=specified_number_occupants,
                                       user_defined_number_of_apartments=user_defined_number_of_apartments, \
                                       specified_number_apartments=specified_number_apartments,
                                       mod_year_method=mod_year_method,
                                       range_of_mod_years=range_of_mod_years,
                                       nodelist_buildings=nodelist_buildings,
                                       deleted_buildings=deleted_buildings,
                                       timestep=timestep, year=year,
                                       try_path=try_path, location=location,
                                       altitude=altitude,
                                       generate_nodelist_from_function_of_citydistrict=generate_nodelist_from_function_of_citydistrict,
                                       save_city_CSV=save_city_CSV,
                                       user_defined_el_demand=user_defined_el_demand,
                                       user_defined_therm_demand=user_defined_therm_demand,
                                       user_defined_dhw=user_defined_dhw)
            print("Saved city object as CSV to ", csv_filename)

        osm_out_path = os.path.join(this_path, 'output_osm', city_filename)
        print(osm_out_path)

        # Dump as pickle file
        if save_city == True:
            # pickle.dump(city, open(osm_out_path, mode='wb'))
            osmgen.pickle_dumper(city, osm_out_path)
            print()
            print('Saved city object as pickle file to ', osm_out_path)

        osmgen.print_statements(city=city, zone_number=zone_number, osm_path=osm_path, \
                         considered_area_around_building=considered_area_around_building,
                         min_house_area=min_house_area,
                         filename=filename, \
                         variance_same_ground_area=variance_same_ground_area, \
                         user_defined_building_distribution=user_defined_building_distribution,
                         percentage_sfh=percentage_sfh, \
                         percentage_mfh=percentage_mfh,
                         percentage_non_res=percentage_non_res,
                         specific_buildings=specific_buildings, \
                         user_defined_build_year=user_defined_build_year,
                         specified_build_year_beginning=specified_build_year_beginning, \
                         specified_build_year_end=specified_build_year_end,
                         user_defined_mod_year=user_defined_mod_year,
                         specified_range_mod_year_beginning=specified_range_mod_year_beginning, \
                         specified_range_mod_year_end=specified_range_mod_year_end,
                         user_defined_number_of_occupants=user_defined_number_of_occupants, \
                         specified_number_occupants=specified_number_occupants,
                         user_defined_number_of_apartments=user_defined_number_of_apartments, \
                         specified_number_apartments=specified_number_apartments,
                         mod_year_method=mod_year_method,
                         range_of_mod_years=range_of_mod_years,
                         deleted_buildings=deleted_buildings,
                         nodelist_buildings=nodelist_buildings,
                         generate_nodelist_from_function_of_citydistrict=generate_nodelist_from_function_of_citydistrict)
