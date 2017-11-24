#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to rescale all electric load curves within city to match to specific
given, annual electric energy demand in kWh (for whole city)
"""
from __future__ import division

import os
import pickle
import copy
import warnings

import pycity_calc.toolbox.teaser_usage.teaser_use as teaseruse


def rescale_el_app(apartment, el_dem):
    """
    Rescale electric energy demand of apartment

    Parameters
    ----------
    apartment : object
        Apartment object of pyCity
    el_dem : float
        Electric energy demand of apartment in kWh/a
    """

    assert el_dem >= 0

    timestep = apartment.environment.timer.timeDiscretization

    #  Reference demand in kWh/a
    ref_el = sum(apartment.power_el.loadcurve) * timestep / \
             (3600 * 1000)

    if ref_el == 0:
        msg = 'Reference electric energy demand is zero! Rescaling' \
              ' cannot be performed!'
        warnings.warn(msg)
        con_factor = 1
    else:
        con_factor = el_dem / ref_el

    apartment.power_el.loadcurve *= con_factor


def rescale_el_dem_build(building, el_dem):
    """
    Rescale electric energy demand of building

    Parameters
    ----------
    building : object
        Building object of pyCity_calc
    el_dem : float
        Electric energy demand of building in kWh/a
    """

    assert el_dem >= 0

    nb_app = len(building.apartments)

    el_dem_app = el_dem / nb_app

    for app in building.apartments:
        rescale_el_app(apartment=app, el_dem=el_dem_app)


def mod_el_city_dem(city, el_dem, list_nodes=None, makecopy=False):
    """
    Modify city by rescaling el. load curves to el_dem value for whole city
    district or specific number of building nodes.

    Parameters
    ----------
    city : object
        City object of pycity_calc
    el_dem : float
        Annual electric demand for rescaling in kWh
    list_nodes : list (of ints), optional
        List of node ids, which should be used for being rescaled (default:
        None). If set to none, uses all buildings for rescaling.
    makecopy : bool, optional
        Defines, if city object should be copied or if original city is
        going to be modified (default: False)
        If set to False, modifies original city object.
        If set to True, modifies copy of city object.

    Returns
    -------
    city : object
        Modified city object of pycity_calc with rescaled, el. energy demand
    """

    if city.get_annual_el_demand(nodelist=list_nodes) == 0:
        msg = 'City el. energy demand is zero. Rescaling cannot be applied.'
        raise AssertionError(msg)

    if makecopy:
        #  Generate copy of city
        city = copy.deepcopy(city)

    if list_nodes is None:
        #  Use all building node ids
        list_nodes = city.get_list_build_entity_node_ids()

    # Calculate conversion factor
    curr_city_el_dem = city.get_annual_el_demand(nodelist=list_nodes)
    con_factor = el_dem / curr_city_el_dem

    for n in list_nodes:
        curr_b = city.nodes[n]['entity']

        el_resc = con_factor * curr_b.get_annual_el_demand()

        rescale_el_dem_build(building=curr_b, el_dem=el_resc)

    return city


if __name__ == '__main__':
    this_path = os.path.dirname(os.path.abspath(__file__))

    #  User input
    #  ###################################################################
    el_dem = 12000  # El. energy demand for rescaling in kWh/a

    city_f_name = 'city_3_buildings.pkl'

    save_f_name = city_f_name[:-4] + '_el_resc.pkl'

    #  ###################################################################

    path_city = os.path.join(this_path, 'input', city_f_name)
    path_save = os.path.join(this_path, 'output', save_f_name)

    city = pickle.load(open(path_city, mode='rb'))

    print('City el. energy demand in kWh/a before conversion:')
    print(city.get_annual_el_demand())

    #  Modify city object
    mod_el_city_dem(city=city, el_dem=el_dem)

    print('City el. energy demand in kWh/a after conversion:')
    print(city.get_annual_el_demand())

    #  #########################################################
    air_vent_mode = 0
    vent_factor = 0.5

    print('City space heating net energy demand in kWh/a before conversion:')
    print(city.get_annual_space_heating_demand())

    #  Recalculate space heating loads with new el. demands
    teaseruse.calc_and_add_vdi_6007_loads_to_city(city=city,
                                                  air_vent_mode=air_vent_mode,
                                                  vent_factor=vent_factor)

    print('City space heating net energy demand in kWh/a after conversion:')
    print(city.get_annual_space_heating_demand())
    #  #########################################################

    #  Save city object
    pickle.dump(city, open(path_save, mode='wb'))
