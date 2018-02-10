#!/usr/bin/env python
# coding=utf-8
"""
Script to estimate thermal and electrical flexibility of building energy
systems based on approach of Sebastian Stinner:
https://www.sciencedirect.com/science/article/pii/S0306261916311424
https://doi.org/10.1016/j.apenergy.2016.08.055
"""
from __future__ import division

import os
import pickle
import copy
import numpy as np
import warnings

import pycity_calc.cities.scripts.energy_sys_generator as esysgen


def calc_t_forced_build(building, id=None):
    """
    Calculate t forced array for building

    Parameters
    ----------
    building : object
        Building object of pyCity_calc
    id : int, optional
        Building id (default: None)

    Returns
    -------
    array_t_force : np.array
        Array holding t forced for each timestep. t_forced is given in seconds
    """

    #  Check if building has energy system
    #  ###########################################################
    if building.hasBes is False:
        msg = 'Building ' + str(id) + ' has no building energy system! ' \
                                      'Thus, cannot calculate t_forece array.'
        raise AssertionError(msg)

    timestep = building.environment.timer.timeDiscretization

    #  Create initial array
    array_t_forced = np.zeros(int(365 * 24 * 3600 / timestep))

    #  ###########################################################
    if building.bes.hasTes is False:
        msg = 'Building ' + str(id) + ' has no thermal storage. ' \
                                      'Thus, therm. flexibility is zero.'
        warnings.warn(msg)
        #  Flexibility is zero, return array with zeros
        return array_t_forced

    #  Get maximal thermal output power of electric heat generators
    #  (CHP, EH, HP)
    q_ehg_nom = 0  # in Watt
    if building.bes.hasChp:
        q_ehg_nom += building.bes.chp.qNominal
    if building.bes.hasHeatpump:
        q_ehg_nom += building.bes.heatpump.qNominal
    if building.bes.hasElectricalHeater:
        q_ehg_nom += building.bes.electricalHeater.qNominal

    #  ###########################################################
    if q_ehg_nom == 0:
        msg = 'Building ' \
              + str(id) + ' has no thermo-electric energy systems. ' \
                          'Thus, therm. flexibility is zero.'
        warnings.warn(msg)
        #  Flexibility is zero, return array with zeros
        return array_t_forced

    #  Extract thermal power curve of building
    sh_power = building.get_space_heating_power_curve()
    dhw_power = building.get_dhw_power_curve()
    th_power = sh_power + dhw_power

    #  Loop over each timestep
    #  ###########################################################
    for i in range(len(array_t_forced)):
        #  Copy storage and set initial / current temperature to t_min (empty)
        tes_copy = copy.deepcopy(building.bes.tes)
        tes_copy.t_current = tes_copy.t_min
        tes_copy.tInit = tes_copy.t_min

        #  Initial timestep
        for t in range(len(array_t_forced) - i):

            #  Current thermal power demand
            th_pow_cur = th_power[t + i]

            #  Calculate possible charging power
            if q_ehg_nom > th_pow_cur:
                p_charge = q_ehg_nom - th_pow_cur
            else:
                p_charge = 0
                #  TODO: Add discharging?

            #  if calc_storage_q_in_max > q_ehg_nom
            if tes_copy.calc_storage_q_in_max() > p_charge:
                t_prior = tes_copy.t_current

                #  perform calc_storage_temp_for_next_timestep
                tes_copy.calc_storage_temp_for_next_timestep(q_in=p_charge,
                                                             q_out=0,
                                                             t_prior=t_prior,
                                                             save_res=True,
                                                             time_index=t)

            else:
                #  Reduce by one increment of t, if t > 0
                if t > 0:
                    t -= 1
                #  End seconds for loop
                break

        #  Save to array_t_forced
        array_t_forced[i] = t * timestep  # in seconds

    return array_t_forced


def calc_t_delayed_build(building, id=None):
    """
    Calculate t delayed array for building

    Parameters
    ----------
    building : object
        Building object of pyCity_calc
    id : int, optional
        Building id (default: None)

    Returns
    -------
    array_t_delayed : np.array
        Array holding t delayed for each timestep.
        t_delayed is given in seconds
    """

    #  Check if building has energy system
    #  ###########################################################
    if building.hasBes is False:
        msg = 'Building ' + str(id) + ' has no building energy system! ' \
                                      'Thus, cannot calculate t_forece array.'
        raise AssertionError(msg)

    timestep = building.environment.timer.timeDiscretization

    #  Create initial array
    array_t_delayed = np.zeros(int(365 * 24 * 3600 / timestep))

    #  ###########################################################
    if building.bes.hasTes is False:
        msg = 'Building ' + str(id) + ' has no thermal storage. ' \
                                      'Thus, therm. flexibility is zero.'
        warnings.warn(msg)
        #  Flexibility is zero, return array with zeros
        return array_t_delayed

    #  Extract thermal power curve of building
    sh_power = building.get_space_heating_power_curve()
    dhw_power = building.get_dhw_power_curve()
    th_power = sh_power + dhw_power

    #  Loop over each timestep
    #  ###########################################################
    for i in range(len(array_t_delayed)):
        #  Copy storage and set initial / current temperature to t_max (full)
        tes_copy = copy.deepcopy(building.bes.tes)
        tes_copy.t_current = tes_copy.tMax
        tes_copy.tInit = tes_copy.tMax

        #  Initial timestep
        for t in range(len(array_t_delayed) - i):

            #  Current thermal power demand
            th_pow_cur = th_power[t + i]

            #  if calc_storage_q_in_max > q_ehg_nom
            if tes_copy.calc_storage_q_out_max() > th_pow_cur:
                t_prior = tes_copy.t_current

                #  perform calc_storage_temp_for_next_timestep
                tes_copy.calc_storage_temp_for_next_timestep(q_in=0,
                                                             q_out=th_pow_cur,
                                                             t_prior=t_prior,
                                                             save_res=True,
                                                             time_index=t)

            else:
                #  Reduce by one increment of t, if t > 0
                if t > 0:
                    t -= 1
                #  End seconds for loop
                break

        #  Save to array_t_forced
        array_t_delayed[i] = t * timestep  # in seconds

    return array_t_delayed


if __name__ == '__main__':

    import matplotlib.pyplot as plt

    #  Add energy system, if no energy system exists on city.pkl file
    #  Necessary to perform flexibility calculation
    add_esys = True

    city_name = 'aachen_kronenberg_6.pkl'
    path_here = os.path.dirname(os.path.abspath(__file__))
    path_city = os.path.join(path_here, 'input', city_name)

    city = pickle.load(open(path_city, mode='rb'))

    if add_esys:
        #  Add energy system
        #  Generate one feeder with CHP, boiler and TES
        list_esys = [(1001, 1, 4),  # CHP, Boiler, TES
                     (1002, 1, 4),
                     (1003, 1, 4),
                     (1004, 2, 2),  # HP (ww), EH, TES
                     (1005, 2, 2),
                     (1006, 2, 2)]

        esysgen.gen_esys_for_city(city=city,
                                  list_data=list_esys,
                                  dhw_scale=False)

    #  Get list of buildings
    list_build_ids = city.get_list_build_entity_node_ids()

    dict_array_t_forced = {}

    #  Loop over buildings
    for n in list_build_ids:
        #  Pointer to current building object
        curr_build = city.nodes[n]['entity']

        #  Calculate t_force array
        array_t_forced = calc_t_forced_build(building=curr_build, id=n)

        dict_array_t_forced[n] = array_t_forced

        if n == 1001 or n == 1004:
            plt.plot(array_t_forced / 3600)
            plt.xlabel('Time in hours')
            plt.ylabel('T_forced in hours')
            plt.show()
            plt.close()

    dict_array_t_delayed = {}

    #  Loop over buildings
    for n in list_build_ids:
        #  Pointer to current building object
        curr_build = city.nodes[n]['entity']

        #  Calculate t_force array
        array_t_delayed = calc_t_delayed_build(building=curr_build, id=n)

        dict_array_t_delayed[n] = array_t_delayed

        if n == 1001 or n == 1004:
            plt.plot(array_t_delayed / 3600)
            plt.xlabel('Time in hours')
            plt.ylabel('T_delayed in hours')
            plt.show()
            plt.close()
