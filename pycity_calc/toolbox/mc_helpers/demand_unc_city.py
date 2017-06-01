#!/usr/bin/env python
# coding=utf-8
"""
Script to perform Monte-Carlo uncertainty analysis with city object of
pycity_calc. Output are uncertain demand sets.
"""

import os
import copy
import pickle
import warnings
import scipy
import numpy as np
import matplotlib.pyplot as plt

import pycity_calc.toolbox.mc_helpers.weather.gen_weather_set as weaunc
import pycity_calc.toolbox.mc_helpers.demand_unc_single_build as mcb


def run_mc_sh_uncertain_city(city, nb_samples,
                             time_sp_force_retro=40,
                             max_retro_year=2014,
                             weather_region=5,
                             weather_year=2010,
                             nb_occ_unc=True):
    """
    Runs Monte-Carlo analysis on city object. Performs sampling for uncertain
    parameters (such as user behavior on set temperatures, air exchange rate;
    building physics; weather) and analyzes the load outputs.

    Parameters
    ----------
    city : object
        City object of pycity_calc
    nb_samples : int
        Number of samples
    time_sp_force_retro : int, optional
        Timespan, in which a retrofit action is forced to the system.
        (default: 40).
    max_retro_year : int, optional
        Maximal / youngest possible retrofit year for sampling (default: 2014)
    weather_region : int, optional
        TRY weather region (default: 5)
    weather_year : int, optional
        TRY weather year (default: 2010)
    nb_occ_unc : bool, optional
        Defines, if number of occupants per apartment is unknown
        (default: True).
        If set to True, number of occupants is unknown
        If set to False, uses number of occupants on occupancy objects
        as known values.

    Returns
    -------
    list_res : list
        Lists with result lists
        (list_sh_city, list_el_city, list_dhw_city, list_sh_curves_city)
        1. Entry: list holding net space heating demands in kWh as float
        2. Entry: list holding space heating power curves in W as arrays
        3. Entry: list holding net electric energy demands in kWh
        4. Entry: list holding hot water net energy demands in kWh
    """

    #  Generate a deepcopy of city object to prevent modifying the original
    #  object instance (and sub-objects, such as buildings)
    city_copy = copy.deepcopy(city)

    timestep = city_copy.environment.timer.timeDiscretization

    #  Generate list with all building (node) entity ids
    list_build_ids = city_copy.get_list_build_entity_node_ids()

    #  1. Sampling of city uncertain parameters
    #  #####################################################################
    list_wea = weaunc.gen_set_of_weathers(nb_weath=nb_samples,
                                           year=weather_year,
                                           timestep=timestep,
                                           region_nb=weather_region)

    #  2. Perform sampling and
    #  3. Monte-Carlo simulation
    #  for each building
    #  #####################################################################

    list_sh_city = []
    list_el_city = []
    list_dhw_city = []

    list_sh_curves_city = []

    #  Loop over samples
    for i in range(nb_samples):

        #  Define results for net energy demand and sh power curve on
        #  city districts scale (to be summed up with single building values)
        sh_city = 0
        el_city = 0
        dhw_city = 0
        sh_city_curve = np.zeros(int(365 * 24 * 3600 / timestep))

        #  Sample same weather for all buildings in this sampling run
        curr_list_wea = [list_wea[i]]
        #  Necessary to prevent usage of first weather data set, as we are
        #  only going to use single sample run in building_unc_sampling (#143)

        #  Loop over buildings
        for n in list_build_ids:

            #  Get list of space heating demand samples for each building
            curr_b = city.node[n]['entity']

            #  Extract single sample dict for each parameter
            dict_samples = \
                mcb.building_unc_sampling(exbuilding=curr_b,
                                          nb_samples=1,
                                          max_retro_year=max_retro_year,
                                          time_sp_force_retro=time_sp_force_retro,
                                          nb_occ_unc=nb_occ_unc)

            #  Perform MC simulation for single building with single sample
            #  parameter --> Only one entry per list, as dict_samples list
            #  only hold a single entry (nb_samples=1 in building_unc_sampling)
            (list_sh, list_sh_curves, list_el, list_dhw) = \
                mcb.mc_call_single_building(exbuilding=curr_b,
                                            dict_samples=dict_samples,
                                            list_wea=curr_list_wea)

            #  Add single building demand values to city demand values
            sh_city += list_sh[0]
            el_city += list_el[0]
            dhw_city += list_dhw[0]

            #  Sum up each space heating power value
            for t in range(len(sh_city_curve)):
                sh_city_curve[t] += list_sh_curves[0][t]

        #  Add single city sample to sample lists
        list_sh_city.append(sh_city)
        list_el_city.append(el_city)
        list_dhw_city.append(dhw_city)
        list_sh_curves_city.append(sh_city_curve)

    return (list_sh_city, list_el_city, list_dhw_city, list_sh_curves_city)


if __name__ == '__main__':

    #  User Inputs
    #  ##############################
    nb_samples = 10000
    time_sp_force_retro = 50
    max_retro_year = 2014
    weather_region = 5
    weather_year = 2010
    nb_occ_unc = True

    #city_f_name = 'aachen_forsterlinde_mod_6.pkl'
    #city_f_name = 'aachen_frankenberg_mod_6.pkl'
    #city_f_name = 'aachen_huenefeld_mod_6.pkl'
    # city_f_name = 'aachen_kronenberg_mod_6.pkl'
    # city_f_name = 'aachen_preusweg_mod_6.pkl'
    #city_f_name = 'aachen_tuerme_mod_6.pkl'

    save_f_name = city_f_name[:-4] + '_mc_city_samples_' + str(nb_samples) + '.pkl'

    #  Define, if older years of construction should be set to enable a larger
    #  variation of modernization years
    change_constr_years = True
    #  If True, overwrite all construction years with value
    #  If False, uses existing modernization years of city object
    new_constr_year = 1970

    #  End of user Inputs
    #  ##############################

    this_path = os.path.dirname(os.path.abspath(__file__))

    city_path = os.path.join(this_path, 'input', 'ref_cities', city_f_name)

    save_path = os.path.join(this_path, 'output', save_f_name)

    city = pickle.load(open(city_path, mode='rb'))

    if change_constr_years:
        #  Change all construction years to new_consr_year
        list_build_ids = city.get_list_build_entity_node_ids()
        for n in list_build_ids:
            city.node[n]['entity'].build_year = new_constr_year

    #  Perform MC analysis for whole city
    (list_sh, list_el, list_dhw, list_sh_curves) = \
        run_mc_sh_uncertain_city(city=city, nb_samples=nb_samples,
                             time_sp_force_retro=time_sp_force_retro,
                             max_retro_year=max_retro_year,
                             weather_region=weather_region,
                             weather_year=weather_year,
                             nb_occ_unc=nb_occ_unc)

    #  Analysis
    #  ##################################################################
    list_max_power = []
    for power in list_sh_curves:
        list_max_power.append(max(power))

    # Save results
    try:
        pickle.dump((list_sh, list_sh_curves, list_el, list_dhw),
                    open(save_path, mode='wb'))
        print('Saved results of Monte-Carlo analysis of city district ')
        print(str(city_f_name))
        print('into ')
        print(str(save_path))
    except:
        warnings.warn('Could not pickle and save results.')

    print()
    print('Mean net space heating energy value in kWh:')
    mean = sum(list_sh) / len(list_sh)
    print(mean)
    print()

    print('Standard deviation of net space heating energy value in kWh:')
    stdev = np.std(a=list_sh)
    print()

    print('Median net space heating energy value in kWh:')
    median = np.median(a=list_sh)
    print(median)
    print()

    print('Interquartile range (IQR):')
    iqr = scipy.stats.iqr(x=list_sh)
    print(iqr)
    print()

    print('Relative interquartile range (RIQR):')
    riqr = iqr / median
    print(riqr)
    print()

    print('95 % confidence interval for single draw:')
    conf_int = scipy.stats.norm.interval(0.95, loc=mean, scale=stdev)
    print(conf_int)
    print()

    fig = plt.figure()
    for curve in list_sh_curves:
        plt.plot(curve / 1000, alpha=0.5)
    plt.xlabel('Time in hours')
    plt.ylabel('Space heating power in kW')
    plt.show()
    plt.close()

    fig = plt.figure()
    # the histogram of the data
    plt.hist(list_sh, 100)
    plt.xlabel('Space heating net energy demand in kWh')
    plt.ylabel('Number of values')
    plt.show()
    plt.close()

    fig = plt.figure()
    # the histogram of the data
    plt.hist(list_max_power, 100)
    plt.xlabel('Space heating maximal power value in W')
    plt.ylabel('Number of values')
    plt.show()
    plt.close()