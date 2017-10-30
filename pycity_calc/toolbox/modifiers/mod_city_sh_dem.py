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


def sh_curve_summer_off(sh_array, resc=0.2):
    """
    Modifies space heating load array to be zero during non heating period
    from April to September

    Parameters
    ----------
    sh_array : np.array (of floats)
        Numpy array with space heating power in Watt (for each timestep)
    resc : float, optional
        Defines rescaling factor, related to "cut off" space heating energy
        (default: 0.2). E.g. 0.2 means, that 20 % of "cut off" space heating
        energy are used to rescale remaining demand

    Returns
    -------
    sh_array_mod : np.array (of floats)
        Numpy array holding modified space heating power in Watt (per timestep)
    """

    sh_array_mod = copy.copy(sh_array)

    timestep = int(365 * 24 * 3600 / len(sh_array_mod))

    cut_off_energy = 0

    idx_summer_start = int(114 * 24 * 3600 / timestep)
    idx_summer_stop = int(297 * 24 * 3600 / timestep)

    #  Set sh powers to zero during non heating periode
    for i in range(idx_summer_start, idx_summer_stop, 1):
        if sh_array_mod[i] > 0:
            cut_off_energy += sh_array_mod[i] * timestep / (1000 * 3600)
            sh_array_mod[i] = 0

    sh_dem_after = sum(sh_array_mod) * timestep / (1000 * 3600)

    resc_factor = (resc * cut_off_energy + sh_dem_after) / sh_dem_after

    # Rescale remaining power curve
    sh_array_mod *= resc_factor

    return sh_array_mod


def sh_curve_summer_off_build(building, resc=0.2):
    """
    Modifies space heating curve to be zero during non heating period from
    April to September.

    Parameters
    ----------
    building : object
        Building object of pyCity_calc
    resc : float, optional
        Defines rescaling factor, related to "cut off" space heating energy
        (default: 0.2). E.g. 0.2 means, that 20 % of "cut off" space heating
        energy are used to rescale remaining demand
    """
    assert resc >= 0
    assert resc <= 1

    array_sh_building = copy.deepcopy(building.get_space_heating_power_curve())

    sh_array_mod = sh_curve_summer_off(sh_array=array_sh_building, resc=resc)

    #  Distribute to apartments
    nb_app = len(building.apartments)

    array_sh_app = sh_array_mod / nb_app

    for app in building.apartments:
        app.demandSpaceheating.loadcurve = array_sh_app


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

    #  #  Modify space heating of city object
    #  ###################################################################
    # print('City space heating energy demand in kWh/a before conversion:')
    # print(city.get_annual_space_heating_demand())
    #
    # #  Modify city object
    # mod_sh_city_dem(city=city, sh_dem=sh_dem)
    #
    # print('City space heating demand in kWh/a after conversion:')
    # print(city.get_annual_space_heating_demand())
    #
    # #  Save city object
    # pickle.dump(city, open(path_save, mode='wb'))

    #  Uncomment, if you want to test summer heating off modification
    #  ###################################################################
    ref_build = city.node[1001]['entity']
    array_sh_before = copy.deepcopy(ref_build.get_space_heating_power_curve())
    sh_dem_before = copy.copy(ref_build.get_annual_space_heat_demand())

    rescaling = 0.2

    sh_curve_summer_off_build(building=ref_build, resc=rescaling)

    sh_dem_after = ref_build.get_annual_space_heat_demand()

    print('Space heating demand before modification in kWh: ')
    print(round(sh_dem_before, 0))
    print()

    print('Space heating demand after modification in kWh: ')
    print(round(sh_dem_after, 0))
    print()

    perc = (sh_dem_after - sh_dem_before) * 100 / sh_dem_before

    print('Difference in percent: ', round(perc, 2))

    import matplotlib.pyplot as plt

    fig = plt.figure()
    plt.subplot(2, 1, 1)
    plt.plot(array_sh_before / 1000, label='Original')
    plt.ylabel('Space heating power in kW')
    plt.legend()
    plt.subplot(2, 1, 2)
    plt.plot(ref_build.get_space_heating_power_curve() / 1000,
             label='Summer off')
    plt.xlabel('Time in hours')
    plt.ylabel('Space heating power in kW')
    plt.legend()
    plt.tight_layout()
    plt.show()
    plt.close()
