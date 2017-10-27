#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to rescale all dhw load curves within city to match to specific
given, annual dhw energy demand in kWh (for whole city)
"""
from __future__ import division

import os
import pickle
import copy
import warnings

def rescale_dhw_build(building, dhw_dem):
    """
    Rescale domestic hot water (dhw) demand on building object

    Parameters
    ----------
    building : object
        Building object of pyCity_calc
    dhw_dem : float
        Domestic hot water thermal net energy demand in kWh/a (used for
        rescaling)
    """

    timestep = building.environment.timer.timeDiscretization

    nb_app = len(building.apartments)

    dhw_dem_app = dhw_dem / nb_app

    for app in building.apartments:

        #  Reference demand in kWh/a
        ref_dhw = sum(app.demandDomesticHotWater.loadcurve) * timestep / \
                  (3600 * 1000)

        if ref_dhw == 0:
            msg = 'Reference hot water energy demand is zero! Rescaling' \
                  ' cannot be performed!'
            warnings.warn(msg)
            con_factor = 1
        else:
            con_factor = dhw_dem_app / ref_dhw

        app.demandDomesticHotWater.loadcurve *= con_factor
        if hasattr(app.demandDomesticHotWater, 'water'):
            app.demandDomesticHotWater.water *= con_factor


def mod_dhw_city_dem(city, dhw_dem, list_nodes=None, makecopy=False):
    """

    Parameters
    ----------
    city : object
        City object of pycity_calc
    dhw_dem : float
        Annual dhw demand for rescaling in kWh
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

    if city.get_annual_dhw_demand(nodelist=list_nodes) == 0:
        msg = 'City dhw energy demand is zero. Rescaling cannot be applied.'
        raise AssertionError(msg)

    if makecopy:
        #  Generate copy of city
        city = copy.deepcopy(city)

    if list_nodes is None:
        #  Use all building node ids
        list_nodes = city.get_list_build_entity_node_ids()

    #  Calculate conversion factor
    curr_city_dhw_dem = city.get_annual_dhw_demand(nodelist=list_nodes)
    con_factor = dhw_dem / curr_city_dhw_dem

    for n in list_nodes:
        curr_b = city.node[n]['entity']

        dhw_resc = con_factor * curr_b.get_annual_dhw_demand()

        rescale_dhw_build(building=curr_b, dhw_dem=dhw_resc)

    return city


if __name__ == '__main__':

    this_path = os.path.dirname(os.path.abspath(__file__))

    #  User input
    #  ###################################################################
    dhw_dem = 5000  # El. energy demand for rescaling in kWh/a

    city_f_name = 'city_3_buildings.pkl'

    save_f_name = city_f_name[:-4] + '_dhw_resc.pkl'

    #  ###################################################################

    path_city = os.path.join(this_path, 'input', city_f_name)
    path_save = os.path.join(this_path, 'output', save_f_name)

    city = pickle.load(open(path_city, mode='rb'))

    print('City dhw energy demand in kWh/a before conversion:')
    print(city.get_annual_dhw_demand())

    #  Modify city object
    mod_dhw_city_dem(city=city, dhw_dem=dhw_dem)

    print('City dhw energy demand in kWh/a after conversion:')
    print(city.get_annual_dhw_demand())

    #  Save city object
    pickle.dump(city, open(path_save, mode='wb'))
