#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to rescale all space heating load curves within city to match to
specific given, annual space heating energy demand in kWh (for whole city)
"""
from __future__ import division

import os
import pickle
import copy
import warnings


def rescale_sh_app(apartment, sh_dem):
    """
    Rescale space heating net energy demand of apartment

    Parameters
    ----------
    apartment : object
        Apartment object of pyCity
    sh_dem : float
        Space heating net energy demand of apartment in kWh/a
    """

    assert sh_dem >= 0

    timestep = apartment.environment.timer.timeDiscretization

    #  Reference demand in kWh/a
    ref_sh = sum(apartment.demandSpaceheating.loadcurve) * timestep / \
             (3600 * 1000)

    if ref_sh == 0:
        msg = 'Reference space heating energy demand is zero! Rescaling' \
              ' cannot be performed!'
        warnings.warn(msg)
        con_factor = 1
    else:
        con_factor = sh_dem / ref_sh

    apartment.demandSpaceheating.loadcurve *= con_factor


def rescale_sh_dem_build(building, sh_dem):
    """
    Rescale space heating net energy demand of building

    Parameters
    ----------
    building : object
        Building object of pyCity_calc
    sh_dem : float
        Space heating net energy demand of building in kWh/a
    """

    assert sh_dem >= 0

    nb_app = len(building.apartments)

    sh_dem_app = sh_dem / nb_app

    for app in building.apartments:
        rescale_sh_app(apartment=app, sh_dem=sh_dem_app)


def mod_sh_city_dem(city, sh_dem, list_nodes=None, makecopy=False):
    """
    Modify city by rescaling sh. load curves to sh_dem value for whole city
    district or specific number of building nodes.

    Parameters
    ----------
    city : object
        City object of pycity_calc
    sh_dem : float
        Annual space heating net energy demand for rescaling in kWh
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

    if city.get_annual_space_heating_demand(nodelist=list_nodes) == 0:
        msg = 'City el. energy demand is zero. Rescaling cannot be applied.'
        raise AssertionError(msg)

    if makecopy:
        #  Generate copy of city
        city = copy.deepcopy(city)

    if list_nodes is None:
        #  Use all building node ids
        list_nodes = city.get_list_build_entity_node_ids()

    # Calculate conversion factor
    curr_city_el_dem = city.get_annual_space_heating_demand(nodelist=
                                                            list_nodes)
    con_factor = sh_dem / curr_city_el_dem

    for n in list_nodes:
        curr_b = city.node[n]['entity']

        sh_resc = con_factor * curr_b.get_annual_space_heat_demand()

        rescale_sh_dem_build(building=curr_b, sh_dem=sh_resc)

    return city


if __name__ == '__main__':
    this_path = os.path.dirname(os.path.abspath(__file__))

    #  User input
    #  ###################################################################
    sh_dem = 120000  # El. energy demand for rescaling in kWh/a

    city_f_name = 'city_3_buildings.pkl'

    save_f_name = city_f_name[:-4] + '_el_resc.pkl'

    #  ###################################################################

    path_city = os.path.join(this_path, 'input', city_f_name)
    path_save = os.path.join(this_path, 'output', save_f_name)

    city = pickle.load(open(path_city, mode='rb'))

    print('City space heating energy demand in kWh/a before conversion:')
    print(city.get_annual_space_heating_demand())

    #  Modify city object
    mod_sh_city_dem(city=city, sh_dem=sh_dem)

    print('City space heating demand in kWh/a after conversion:')
    print(city.get_annual_space_heating_demand())

    #  Save city object
    pickle.dump(city, open(path_save, mode='wb'))
