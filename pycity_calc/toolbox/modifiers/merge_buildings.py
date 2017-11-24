#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script enables merging of existing building entities into a single
building entity within a city object instance.
The new building object instance is saved on an existing building node
within the city. The building nodes, where buildings have been extracted for
merge, are going to be deleted.

Important: Energy systems are going to be lost, if they exist!
"""
from __future__ import division

import os
import copy
import pickle
import warnings

import shapely.geometry.point as point

import pycity_base.classes.Weather as Weather
import pycity_base.classes.demand.SpaceHeating as SpaceHeating
import pycity_base.classes.demand.ElectricalDemand as ElectricalDemand
import pycity_base.classes.demand.Apartment as Apartment

import pycity_calc.buildings.building as build_ex
import pycity_calc.cities.city as cit
import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.environment as env
import pycity_calc.environments.germanmarket as germarkt
import pycity_calc.environments.timer as time


def check_if_all_entries_are_none(list_values):
    """
    Checks if all entries in list are None

    Parameters
    ----------
    list_values : list
        List with different values

    Returns
    -------
    is_all_none : bool
        Boolean. True, if all values are None. False, if, at least, one
        value is not None
    """

    #  Initial value
    is_all_none = True

    for val in list_values:
        if val is not None:
            is_all_none = False
            break

    return is_all_none


def erase_none_val_from_list(list_values):
    """

    Parameters
    ----------
    list_values : list
        List with different values

    Returns
    -------
    list_no_nones : list
        List with extract of list_values. No more None values included
    """

    list_no_nones = []

    for val in list_values:
        if val is not None:
            list_no_nones.append(val)

    return list_no_nones


def check_compare_list_val(list_comp, name=None):
    """
    Compares list values. Yields warning, if list values are different

    Parameters
    ----------
    list_comp : list (of floats)
        List of float values for comparison
    name : str (optional)
        Name of list / parameters
    """

    for i in range(len(list_comp) - 1):

        val_1 = list_comp[i]
        val_2 = list_comp[i + 1]

        if val_1 is not None and val_2 is not None:

            if val_1 != val_2:
                msg = 'Value %d at index %d is different from value ' \
                      '%d at index %d for list %s' % (val_1, i, val_2, i + 1,
                                                      name)
                warnings.warn(msg)

        else:
            if (val_1 is None and val_2 is not None or
                    (val_1 is not None and val_2 is None)):
                msg = 'At least one value in %s is None, while at least ' \
                      'one other value is not None' % (name)
                warnings.warn(msg)


def make_building_merge(environment, list_building_obj):
    """
    Merges building object within list_building_obj to new building entity

    Important: Energy systems are going to be lost, if they exist!

    Parameters
    ----------
    environment : object
        Environment object of pyCity_calc
    list_building_obj : list (of objects)
        list holding building objects of pyCity_calc

    Returns
    -------
    build_new : object
        New building entity, merge results of input buildings
    """

    #  Check if objects are kind building
    for build in list_building_obj:
        assert build._kind == 'building'

        if build.hasBes:
            msg = 'Building has building energy system (BES), which is ' \
                  'going to be lost during merge!'
            warnings.warn(msg)

    # Generate new, empty building
    build_new = build_ex.BuildingExtended(environment=environment)

    #  Copy and add all apartments to new building
    for build in list_building_obj:
        for ap in build.apartments:
            #  Copy apartment
            ap_copy = copy.deepcopy(ap)
            #  Add copy to building new
            build_new.addEntity(ap_copy)

    list_build_years = []
    list_mod_years = []
    list_build_types = []
    list_usabl_pv_areas = []
    list_net_floor_areas = []
    list_ground_areas = []
    list_height_of_floors = []
    list_nb_floors = []
    list_neighbour_buildings = []
    list_residential_layout = []
    list_attics = []
    list_cellars = []
    list_construction_types = []
    list_dormers = []
    list_with_ahu = []

    #  Extract all building attributes and merge them
    for build in list_building_obj:
        list_build_years.append(copy.copy(build.build_year))
        list_mod_years.append(copy.copy(build.mod_year))
        list_build_types.append(copy.copy(build.build_type))
        list_usabl_pv_areas.append(copy.copy(build.roof_usabl_pv_area))
        list_net_floor_areas.append(copy.copy(build.net_floor_area))
        list_ground_areas.append(copy.copy(build.ground_area))
        list_height_of_floors.append(copy.copy(build.height_of_floors))
        list_nb_floors.append(copy.copy(build.nb_of_floors))
        list_neighbour_buildings.append(copy.copy(build.neighbour_buildings))
        list_residential_layout.append(copy.copy(build.residential_layout))
        list_attics.append(copy.copy(build.attic))
        list_cellars.append(copy.copy(build.cellar))
        list_construction_types.append(copy.copy(build.construction_type))
        list_dormers.append(copy.copy(build.dormer))
        list_with_ahu.append(copy.copy(build.with_ahu))

    # Make list checks
    check_compare_list_val(list_comp=list_build_years, name='build_year')
    check_compare_list_val(list_comp=list_mod_years, name='mod_year')
    check_compare_list_val(list_comp=list_build_types, name='build_type')
    check_compare_list_val(list_comp=list_height_of_floors,
                           name='height_of_floors')
    check_compare_list_val(list_comp=list_nb_floors, name='nb_of_floors')
    check_compare_list_val(list_comp=list_residential_layout,
                           name='residential_layout')
    check_compare_list_val(list_comp=list_attics, name='attic')
    check_compare_list_val(list_comp=list_cellars, name='cellar')
    check_compare_list_val(list_comp=list_construction_types,
                           name='construction_type')
    check_compare_list_val(list_comp=list_dormers, name='dormer')
    check_compare_list_val(list_comp=list_with_ahu, name='with_ahu')

    #  Generate and save new parameters
    all_none = check_if_all_entries_are_none(list_values=list_build_years)
    if all_none is True:
        build_new.build_year = None
    else:
        list_build_years = erase_none_val_from_list(list_values=
                                                    list_build_years)
        #  Use average value of build_years
        build_new.build_year = int(
            sum(list_build_years) / len(list_build_years))

    all_none = check_if_all_entries_are_none(list_values=list_mod_years)
    if all_none is True:
        build_new.mod_year = None
    else:
        list_mod_years = erase_none_val_from_list(list_values=
                                                  list_mod_years)
        #  Use average value of build_years
        build_new.mod_year = int(
            sum(list_mod_years) / len(list_mod_years))

    # Use first index for build type
    build_new.build_type = list_build_types[0]

    all_none = check_if_all_entries_are_none(list_values=list_usabl_pv_areas)
    if all_none is True:
        build_new.roof_usabl_pv_area = None
    else:
        list_usabl_pv_areas = erase_none_val_from_list(list_values=
                                                       list_usabl_pv_areas)
        #  Build sum of usable pv areas
        build_new.roof_usabl_pv_area = sum(list_usabl_pv_areas)

    all_none = check_if_all_entries_are_none(list_values=list_net_floor_areas)
    if all_none is True:
        build_new.net_floor_area = None
    else:
        list_net_floor_areas = erase_none_val_from_list(list_values=
                                                        list_net_floor_areas)
        #  Build sum
        build_new.net_floor_area = sum(list_net_floor_areas)

    all_none = check_if_all_entries_are_none(list_values=list_ground_areas)
    if all_none is True:
        build_new.ground_area = None
    else:
        list_ground_areas = erase_none_val_from_list(list_values=
                                                     list_ground_areas)
        #  Build sum
        build_new.ground_area = sum(list_ground_areas)

    all_none = check_if_all_entries_are_none(list_values=list_height_of_floors)
    if all_none is True:
        build_new.height_of_floors = None
    else:
        list_height_of_floors = erase_none_val_from_list(list_values=
                                                         list_height_of_floors)
        #  Build average
        build_new.height_of_floors = sum(list_height_of_floors) / \
                                     len(list_height_of_floors)

    all_none = check_if_all_entries_are_none(list_values=list_nb_floors)
    if all_none is True:
        build_new.nb_of_floors = None
    else:
        list_nb_floors = erase_none_val_from_list(list_values=
                                                  list_nb_floors)
        #  Build average
        build_new.nb_of_floors = sum(list_nb_floors) / \
                                 len(list_nb_floors)

    all_none = check_if_all_entries_are_none(
        list_values=list_neighbour_buildings)
    if all_none is True:
        build_new.neighbour_buildings = None
    else:
        list_neighbour_buildings = erase_none_val_from_list(list_values=
                                                            list_neighbour_buildings)
        #  Build min
        build_new.neighbour_buildings = min(list_neighbour_buildings)

    all_none = check_if_all_entries_are_none(
        list_values=list_residential_layout)
    if all_none is True:
        build_new.residential_layout = None
    else:
        list_residential_layout = erase_none_val_from_list(list_values=
                                                           list_residential_layout)
        #  Build max
        build_new.residential_layout = max(list_residential_layout)

    all_none = check_if_all_entries_are_none(
        list_values=list_attics)
    if all_none is True:
        build_new.attic = None
    else:
        list_attics = erase_none_val_from_list(list_values=
                                               list_attics)
        #  Build average
        build_new.attic = int(sum(list_attics) / len(list_attics))

    all_none = check_if_all_entries_are_none(
        list_values=list_cellars)
    if all_none is True:
        build_new.cellar = None
    else:
        list_cellars = erase_none_val_from_list(list_values=
                                                list_cellars)
        #  Build average
        build_new.cellar = int(sum(list_cellars) / len(list_cellars))

    # Use first index
    build_new.construction_type = list_construction_types[0]

    all_none = check_if_all_entries_are_none(
        list_values=list_dormers)
    if all_none is True:
        build_new.dormer = None
    else:
        list_dormers = erase_none_val_from_list(list_values=
                                                list_dormers)
        #  Build max
        build_new.dormer = max(list_dormers)

    all_none = check_if_all_entries_are_none(
        list_values=list_with_ahu)
    if all_none is True:
        build_new.with_ahu = None
    else:
        list_with_ahu = erase_none_val_from_list(list_values=
                                                 list_with_ahu)
        #  Build max
        build_new.with_ahu = max(list_with_ahu)

    return build_new


def merge_buildings_in_city(city, list_lists_merge):
    """
    Function merges buildings to new building object instances.
    Old buildings/building nodes are going to be erased.

    Important: Energy systems are going to be lost, if they exist!

    Parameters
    ----------
    city : object
        City object of pyCity_calc
    list_lists_merge : list (of lists of ints)
        List of lists of building node ids, which should be merged.
        Every list within list_lists_merge holds the ids of existing buildings,
        which are going to be used to be merged to a new building.

    Returns
    -------
    city_copy : object
        Modified city object with merged buildings
    """

    city_copy = copy.deepcopy(city)

    for list_merge in list_lists_merge:

        #  Extract building objects
        list_build = []
        for n in list_merge:
            build = city_copy.nodes[n]['entity']
            list_build.append(build)

        # Generate new building entity
        new_build = make_building_merge(environment=city_copy.environment,
                                        list_building_obj=list_build)

        #  Save building entity to first index / node id in list_merge
        city_copy.nodes[list_merge[0]]['entity'] = new_build

        #  Erase all remaining building nodes, which have been merged
        for i in range(len(list_merge)):
            if i != 0:
                id = list_merge[i]
                #  Remove building node with uesgraph method
                city_copy.remove_building(id)

    return city_copy


if __name__ == '__main__':

    #  Decide, if you want to load an existing city district pickle file
    #  or if you want to generate a test city
    load_city = False
    #  If True, load city pickle file (requires name and path)
    #  If False, runs test city generation below

    #  Save city
    do_save = False

    #  Pathes
    #  ######################################################################
    this_path = os.path.dirname(os.path.abspath(__file__))

    city_input_name = 'city.pkl'
    city_path = os.path.join(this_path, 'input', city_input_name)

    city_save_name = 'city_merged.pkl'
    path_save = os.path.join(this_path, 'output', city_save_name)
    #  ######################################################################

    #  List of lists of buildings, which should be merged together
    list_lists_merge = [[1001, 1002], [1003, 1004]]

    if load_city:
        city_object = pickle.load(open(city_path, mode='rb'))

    else:
        #  Generate test city
        #  ######################################################################

        #  Create extended environment of pycity_calc
        year = 2017
        timestep = 900  # Timestep in seconds
        location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop
        altitude = 55  # Altitude of Bottrop

        #  Generate timer object
        timer = time.TimerExtended(timestep=timestep, year=year)

        #  Generate weather object
        weather = Weather.Weather(timer, useTRY=True, location=location,
                                  altitude=altitude)

        #  Generate market object
        market = germarkt.GermanMarket()

        #  Generate co2 emissions object
        co2em = co2.Emissions(year=year)

        #  Generate environment
        environment = env.EnvironmentExtended(timer, weather, prices=market,
                                              location=location, co2em=co2em)

        #  Generate city object
        city_object = cit.City(environment=environment)

        #  Iterate 4 times to generate 3 building objects
        for i in range(4):
            #  Create demands (with standardized load profiles (method=1))
            heat_demand = SpaceHeating.SpaceHeating(environment,
                                                    method=1,
                                                    profile_type='HEF',
                                                    livingArea=100,
                                                    specificDemand=120)

            el_demand = ElectricalDemand.ElectricalDemand(environment,
                                                          method=1,
                                                          annualDemand=3000,
                                                          profileType="H0")

            #  Create apartment
            apartment = Apartment.Apartment(environment)

            #  Add demands to apartment
            apartment.addMultipleEntities([heat_demand, el_demand])

            extended_building = \
                build_ex.BuildingExtended(environment,
                                          build_year=1962,
                                          mod_year=2003,
                                          build_type=0,
                                          roof_usabl_pv_area=30,
                                          net_floor_area=150,
                                          height_of_floors=3,
                                          nb_of_floors=2,
                                          neighbour_buildings=0,
                                          residential_layout=0,
                                          attic=0, cellar=1,
                                          construction_type='heavy',
                                          dormer=0)

            #  Add apartment to extended building
            extended_building.addEntity(entity=apartment)

            position = point.Point(i * 10, 0)

            city_object.add_extended_building(
                extended_building=extended_building,
                position=position)

    # ######################################################################

    # #  Checker for comparison function
    # city_object.nodes[1004]['entity'].build_year = None

    #  Merge buildings together
    city_new = merge_buildings_in_city(city=city_object,
                                       list_lists_merge=list_lists_merge)

    if do_save:
        pickle.dump(city_new, open(path_save, mode='wb'))
