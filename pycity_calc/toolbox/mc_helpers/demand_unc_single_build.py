#!/usr/bin/env python
# coding=utf-8
"""
Script to perform thermal demand uncertainty analysis for single building with
single thermal zone and apartment
"""

from __future__ import division

import os
import copy
import pickle
import warnings
import random as rd
import scipy
import numpy as np
import matplotlib.pyplot as plt

import pycity_base.classes.Weather as Weather
import pycity_base.classes.demand.Occupancy as occ
import pycity_base.classes.demand.ElectricalDemand as eldem
import pycity_base.classes.demand.Apartment as Apartment
import pycity_base.classes.demand.DomesticHotWater as dhwater

import pycity_calc.buildings.building as build_ex
import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.environment as env
import pycity_calc.environments.market as mark
import pycity_calc.environments.timer as time

import pycity_calc.toolbox.mc_helpers.building.build_unc_set_gen as bunc
import pycity_calc.toolbox.mc_helpers.user.user_unc_sampling as usunc
import pycity_calc.toolbox.mc_helpers.weather.gen_weather_set as weaunc
import pycity_calc.toolbox.teaser_usage.teaser_use as tus


def building_unc_sampling(exbuilding, nb_samples, max_retro_year=2014,
                          time_sp_force_retro=40, nb_occ_unc=True,
                          buil_physic_unc=True):
    """
    Perform uncertain parameter sampling for single residential building.
    Accounts for years of modernization, infiltration rate, number of
    occupants, electrical and dhw loads as well as user air exchange rate as
    uncertain parameters.

    Parameters
    ----------
    exbuilding : object
        Extended building object of pycity_calc (should hold occupancy profile)
    nb_samples : int
        Number of samples
    max_retro_year : int, optional
        Maximal / youngest possible retrofit year for sampling (default: 2014)
    time_sp_force_retro : int, optional
        Timespan, in which a retrofit action is forced to the system.
        (default: 40).
    nb_occ_unc : bool, optional
        Defines, if number of occupants in known or uncertain (default: True)
        True - Number of occupants is uncertain
        False - Number of occupants is known and taken from apartment.occupancy
        objects
    buil_physic_unc: bool, optional
        Defines, if building physics unknown or not (default: True)
        True - Building physics is unknown
        False - Building physics is known

    Returns
    -------
    dict_samples : dict (of lists)
        Dictionary holding lists with samples for different uncertain parameters
        Keys:
        'mod_year' : Holding modification year sample lists
        'inf' : Holding infiltration rate sample lists
        'occ' : Holding occupants per apartment sample lists
        'el' : Holding electrical demand sample lists
        'set_temp' : Holding set temperature sample lists
        'user_air' : Holding user air exchange rate sample lists
        'dormer' : Holding dormer samples list
        'cellar' : Holding cellar samples list
        'attic' : Holding attic samples list
        'const_type' : Holding construction type samples list
        'net_floor_area' : Holding net floor area samples list
        'height_of_floor': Holding average_height_of_floor list

    """

    print('Start building uncertainty sampling')
    print()

    dict_samples = {}

    #  Extract year of construction
    year_of_constr = copy.copy(exbuilding.build_year)

    #  Building physics uncertainty
    #  #####################################

    #  Do retrofit year sampling
    if buil_physic_unc:
        list_mod_years = bunc.calc_array_mod_years_single_build(
            nb_samples=nb_samples,
            year_of_constr=year_of_constr,
            max_year=max_retro_year,
            time_sp_force_retro=
            time_sp_force_retro)

        dict_samples['mod_year'] = list_mod_years

        # Dormer, attic, cellar, construction_type sampling
        (list_dormer, list_attic, list_cellar,
         list_const_type) = bunc.calc_list_dormer_samples(nb_samples)
        dict_samples['dormer'] = list_dormer
        dict_samples['cellar'] = list_cellar
        dict_samples['attic'] = list_attic
        dict_samples['const_type'] = list_const_type

        # Net floor area sampling
        list_nf_area = bunc.calc_list_net_floor_area_sampling(
            nb_of_samples=nb_samples,
            sigma=(exbuilding.net_floor_area * 0.01),
            mean=exbuilding.net_floor_area)
        dict_samples['net_floor_area'] = list_nf_area

        #  Infiltration rate sampling
        list_inf = bunc.calc_inf_samples(nb_samples=nb_samples)
        dict_samples['inf'] = list_inf

        # Average height of floor sampling
        list_average_height_of_floor = bunc.calc_list_net_floor_area_sampling(nb_of_samples=nb_samples,
                                                                              sigma=(
                                                                              exbuilding.height_of_floors * 0.01),
                                                                              mean=exbuilding.height_of_floors)
        dict_samples['height_of_floor'] = list_average_height_of_floor

    else:
        # Net floor area sampling
        list_nf_area = bunc.calc_list_net_floor_area_sampling(
            nb_of_samples=nb_samples,
            sigma=(exbuilding.net_floor_area * 0.005),
            mean=exbuilding.net_floor_area)
        dict_samples['net_floor_area'] = list_nf_area

        # Average height of floor sampling
        list_average_height_of_floor = bunc.calc_list_net_floor_area_sampling(nb_of_samples=nb_samples,
                                                                              sigma=(exbuilding.height_of_floors*0.005),
                                                                              mean=exbuilding.height_of_floors)
        dict_samples['height_of_floor'] = list_average_height_of_floor

        #  Infiltration rate sampling
        if year_of_constr < 1990:
            list_inf = bunc.calc_inf_samples(nb_samples=nb_samples)
        else:
            list_inf = bunc.calc_inf_samples(nb_samples=nb_samples, mean=0.26)

        dict_samples['inf'] = list_inf

    # User uncertainty
    #  #####################################

    list_of_lists_of_nb_of_occ_per_app = []
    list_of_lists_of_el_dem_per_app = []

    if len(exbuilding.apartments) > 1:
        type = 'mfh'
    else:
        type = 'sfh'

    if nb_occ_unc:

        #  Select samples of occupants for every apartment (for nb_samples)
        for i in range(len(exbuilding.apartments)):

            #  Sampling for occupants per apartment
            list_nb_occ = usunc.calc_sampling_occ_per_app(nb_samples=
                                                          nb_samples)
            list_of_lists_of_nb_of_occ_per_app.append(list_nb_occ)

            list_el_dem = []

            for j in range(nb_samples):
                nb_occ = list_nb_occ[j]

                #  As number of occupants changes, only one sample is chosen
                el_dem = \
                    usunc.calc_sampling_el_demand_per_apartment(nb_samples=1,
                                                                nb_persons=
                                                                nb_occ,
                                                                type=type)[0]

                list_el_dem.append(el_dem)

            list_of_lists_of_el_dem_per_app.append(list_el_dem)

    else:

        for app in exbuilding.apartments:
            nb_occ = app.get_max_nb_occupants()
            list_of_lists_of_nb_of_occ_per_app.append(nb_occ)

            #  Electrical demand per apartment, based on nb. of users
            list_el_demands = \
                usunc.calc_sampling_el_demand_per_apartment(
                    nb_samples=nb_samples,
                    nb_persons=nb_occ,
                    type=type)
            list_of_lists_of_el_dem_per_app.append(list_el_demands)

    dict_samples['occ'] = list_of_lists_of_nb_of_occ_per_app
    dict_samples['el'] = list_of_lists_of_el_dem_per_app

    # List of lists (for each apartment) with dhw volume per apartment and day
    list_of_lists_of_dhw_volume = []

    if nb_occ_unc:

        #  Select samples of occupants for every apartment (for nb_samples)
        for i in range(len(exbuilding.apartments)):

            list_dhw_vol = []

            for j in range(nb_samples):
                nb_occ = list_nb_occ[j]

                #  As number of occupants changes, only one sample is chosen
                dhw_vol_ap = \
                    usunc.calc_sampling_dhw_per_apartment(
                        nb_samples=1,
                        nb_persons=nb_occ)[0]

                list_dhw_vol.append(dhw_vol_ap)

            list_of_lists_of_dhw_volume.append(list_dhw_vol)

    else:

        for app in exbuilding.apartments:
            #  Hot water energy demands per apartment
            list_dhw_vol = \
                usunc.calc_sampling_dhw_per_apartment(
                    nb_samples=nb_samples,
                    nb_persons=nb_occ)
            list_of_lists_of_dhw_volume.append(list_dhw_vol)

    # List of lists (for each apartment) with set temperatures per apartment
    list_of_lists_of_set_temp_per_app = []

    #  List of lists (for each apartment) with air exchange rates per apartment
    list_of_lists_of_air_ex_per_app = []

    #  Select samples of occupants for every apartment (for nb_samples)
    for i in range(len(exbuilding.apartments)):
        list_set_temp = usunc.calc_set_temp_samples(nb_samples=nb_samples)
        list_air_ex = usunc.calc_user_air_ex_rates(nb_samples=nb_samples)

        list_of_lists_of_set_temp_per_app.append(list_set_temp)
        list_of_lists_of_air_ex_per_app.append(list_air_ex)

    list_av_set_temp = []
    list_av_air_ex = []

    #  Build average values of set temperatures and user air exchange for
    #  building level
    for j in range(nb_samples):

        sum_t_set = 0
        sum_air_ex = 0

        for i in range(len(exbuilding.apartments)):
            sum_t_set += list_of_lists_of_set_temp_per_app[i][j]
            sum_air_ex += list_of_lists_of_air_ex_per_app[i][j]

        # Generate average values
        av_t_set = sum_t_set / len(exbuilding.apartments)
        av_air_ex = sum_air_ex / len(exbuilding.apartments)

        list_av_set_temp.append(av_t_set)
        list_av_air_ex.append(av_air_ex)

    dict_samples['dhw'] = list_of_lists_of_dhw_volume

    dict_samples['set_temp'] = list_av_set_temp

    dict_samples['user_air'] = list_av_air_ex

    print('Finished building uncertainty sampling')
    print()

    return dict_samples


def non_res_build_unc_sampling(exbuilding, nb_samples, sh_unc=True,
                               el_unc=True, th_factor=0.5, el_factor=0.5):
    """
    Perform uncertainty sampling for non-residential building by rescaling
    thermal and electrical demands.

    Parameters
    ----------
    exbuilding : object
        Extended building object of pycity_calc (should hold occupancy profile)
    nb_samples : int
        Number of samples
    sh_unc : bool, optional
        Defines, if space heating demand is assumed to be uncertain
        (default: True)
    el_unc : bool, optional
        Defines, if electrical demand is assumed to be uncertain
        (default: True)
    th_factor : float, optional
        Maximal rescaling factor to sample thermal demand (default 0.5).
        E.g. 0.5 means nominal_demand * (1 +/- 0.5) is max/min possible
        random value
    el_factor : float, optional
        Maximal rescaling factor to sample electr. demand (default 0.5).
        E.g. 0.5 means nominal_demand * (1 +/- 0.5) is max/min possible
        random value

    Returns
    -------
    res_tuple : tuple (of lists)
        Results tuple (list_sh_net_demand, list_sh_power_curves,
        list_el_net_demand, list_dhw_energies)
        1. Entry: list holding net space heating demands in kWh as float
        2. Entry: list holding net electric energy demands in kWh
    """

    list_sh_net_demand = []
    list_el_net_demand = []

    curr_sh_demand = exbuilding.get_annual_space_heat_demand()
    curr_el_demand = exbuilding.get_annual_el_demand()

    for i in range(nb_samples):

        if sh_unc:
            sh_resc = rd.uniform(1 - th_factor, 1 + th_factor)
            sample_sh_demand = curr_sh_demand * sh_resc
            list_sh_net_demand.append(sample_sh_demand)

        if el_unc:
            el_resc = rd.uniform(1 - el_factor, 1 + el_factor)
            sample_el_demand = curr_el_demand * el_resc
            list_el_net_demand.append(sample_el_demand)

    return (list_sh_net_demand, list_el_net_demand)


def mod_single_build_w_samples(exbuilding, dict_samples, list_wea,
                               i, MC_analysis=False, build_physic_unc=True):
    """
    Copies exbuilding and modifies copy according to sample lists

    Parameters
    ----------
    exbuilding : object
        Extended building object of py
    dict_samples : dict
        Dictionary holding lists with samples for different uncertain parameters
        Keys:
        'mod_year' : Holding modification year sample lists
        'inf' : Holding infiltration rate sample lists
        'occ' : Holding occupants per apartment sample lists
        'el' : Holding electrical demand sample lists
        'set_temp' : Holding set temperature sample lists
        'user_air' : Holding user air exchange rate sample lists
        'dormer' : Holding dormer samples list
        'cellar' : Holding cellar samples list
        'attic' : Holding attic samples list
        'const_type' : Holding construction type samples list
        'net_floor_area' : Holding net floor area samples list
    list_wea : list (of weather objects)
        List holding weather objects from sampling
    i : int
        Sampling index (0 to nb_samples - 1)
    MC_analysis: boolean, optional
            Defines extra modifications for monte carlo analysis
            (dormer,attic,cellar, construction_type, net_floor_area)
    buil_physic_unc: bool, optional
        Defines,if building physics unknown or not (default: True)
        True - Building physics is unknown
        False - Building physics is known

    Returns
    -------
    building : object
        Modified extended building object
    """

    print('Start modification of building copy with sample data')
    print()

    #  Create deepcopy of building, as building object is going to be
    #  modified within Monte-Carlo simulation
    building = copy.deepcopy(exbuilding)

    timestep = building.environment.timer.timeDiscretization

    #  Select sample data
    #  ##################################################################
    #  Overwrite mod year (or year of construction)
    #  If mod_year is smaller than 1982 (smallest retrofit option in teaser)
    #  add mod_year as new year of construction
    if build_physic_unc:
        if dict_samples['mod_year'][i] < 1982:
            building.build_year = dict_samples['mod_year'][i]
            building.mod_year = None
        else:
            #  Else, define new year of modernization
            building.mod_year = dict_samples['mod_year'][i]

    if building.mod_year is not None and building.build_year is not None:
        assert building.build_year < building.mod_year

    print('Constr. year: ', building.build_year)
    print('Mod. year: ', building.mod_year)

    for j in range(len(building.apartments)):
        #  Sampled electrical demand
        el_dem_app = dict_samples['el'][j][i]
        print('Sampled el. demand in kWh: ', el_dem_app)

        #  Current electrical demand
        curr_dem = \
            sum(building.apartments[j].get_total_el_power(
                currentValues=False) \
                * timestep / (3600 * 1000))
        print('Original el. demand in kWh: ', curr_dem)

        #  Rescale el. load curve
        building.apartments[j].power_el.loadcurve *= \
            (el_dem_app / curr_dem)

    for j in range(len(building.apartments)):
        #  Sampled dhw volumes per apartment
        dhw_vol_app_n_day = dict_samples['dhw'][j][i]
        print('Sampled dhw. volume in liters per apartment and day: ',
              dhw_vol_app_n_day)

        #  Substituted volume calculation with energy to volume calc #153
        try:
            volume = sum(building.apartments[j].demandDomesticHotWater.water) \
                     * timestep / 3600
        except:
            #  Hot water energy per apartment per year in Joule
            dhw_energy = \
                sum(building.apartments[j].demandDomesticHotWater.loadcurve) * \
                timestep

            volume = dhw_energy * 1000 / (990 * 4180 * 35)

        print('Original annual volume in liters: ', volume)
        volume_per_day = volume / 365
        print('Original volume in liters per day and apartment; ',
              volume_per_day)

        conv_dhw = dhw_vol_app_n_day / volume_per_day

        #  Substituted volume calculation with energy to volume calc #153
        #  Convert water volume
        try:
            building.apartments[j].demandDomesticHotWater.water *= conv_dhw
        except:
            warnings.warn('Did not find attribute water on dhw object.'
                          ' Thus, only going to convert loadcurve values.')

        # Convert dhw heat power
        building.apartments[j].demandDomesticHotWater.loadcurve *= conv_dhw

    weather_new = list_wea[i]

    #  Overwrite current weather
    building.environment.weather = weather_new

    # Extra modifications for Monte Carlo analysis
    if MC_analysis:
        if build_physic_unc:

            # Overwrite building physic
            building.dormer = dict_samples['dormer'][i]
            print('dormer: ', building.dormer)
            building.attic = dict_samples['attic'][i]
            print('attic: ', building.attic)
            building.cellar = dict_samples['cellar'][i]
            print('cellar :', building.cellar)
            #if dict_samples['const_type'][i] == 0:
                #building.construction_type = "heavy"
            #else:
                #building.construction_type = "light"
            #print('construction type: ', building.construction_type)

        building.net_floor_area = dict_samples['net_floor_area'][i]

        building.height_of_floors = dict_samples['height_of_floor'][i]

    print('Finished modification of building copy with sample data')
    print()

    return building


def mc_call_single_building(exbuilding, dict_samples, list_wea,
                            MC_analysis=False, build_physic_unc=True):
    """
    Performs uncertainty calculation of space heating demands for building
    object. Number of samples is defined by length of dict_sample list entries.

    Parameters
    ----------
    exbuilding : object
        Extendec building object of pycity_calc (should hold occupancy profile)
    dict_samples : dict (of lists)
        Dictionary holding lists with samples for different uncertain parameters
        Keys:
        'mod_year' : Holding modification year sample lists
        'inf' : Holding infiltration rate sample lists
        'occ' : Holding occupants per apartment sample lists
        'el' : Holding electrical demand sample lists
        'set_temp' : Holding set temperature sample lists
        'user_air' : Holding user air exchange rate sample lists
        'dormer' : Holding dormer samples list
        'cellar' : Holding cellar samples list
        'attic' : Holding attic samples list
        'const_type' : Holding construction type samples list
        'net_floor_area' : Holding net floor area samples list
        'height_of_floor': Holding average_height_of_floor list
    list_wea : list (of weather objects)
        List holding different pycity weather objects for uncertainty
        analysis
    MC_analysis: boolean, optional
            Defines extra modifications for monte carlo analysis
            (dormer,attic,cellar, construction_type, net_floor_area)
    buil_physic_unc: bool, optional
        Defines,if building physics unknown or not (default: True)
        True - Building physics is unknown
        False - Building physics is known

    Returns
    -------
    res_tuple : tuple (of lists)
        Results tuple (list_sh_net_demand, list_sh_power_curves,
        list_el_net_demand, list_dhw_energies)
        1. Entry: list holding net space heating demands in kWh as float
        2. Entry: list holding space heating power curves in W as arrays
        3. Entry: list holding net electric energy demands in kWh
        4. Entry: list holding hot water net energy demands in kWh
        5. Entry: dict_problem : dict (of list)
            Dictionary of inputs with problems
            Keys:
            'year' : Holding modification year sample lists
            'infiltration' : Holding infiltration rate sample lists
            'dormer' : Holding dormer samples list
            'cellar' : Holding cellar samples list
            'attic' : Holding attic samples list
            'const_type' : Holding construction type samples list
            'user_air' : Holding user air ventilation factor sampling
    """

    print('Start Monte-Carlo space heating simulation for single building')
    print()

    timestep = exbuilding.environment.timer.timeDiscretization

    list_sh_net_demand = []
    list_sh_power_curves = []

    list_el_net_demand = []
    list_dhw_energies = []

    dict_problem = {}
    dict_problem['infiltration'] = []
    dict_problem['const_type'] = []
    dict_problem['dormer'] = []
    dict_problem['attic'] = []
    dict_problem['cellar'] = []
    dict_problem['user_air'] = []
    dict_problem['year'] = []

    nb_of_samples = len(dict_samples['inf'])

    for n_samp in range(nb_of_samples):

        #  Get modified building (use uncertain parameter samples to modify
        #  building)
        modbuild = \
            mod_single_build_w_samples(exbuilding=exbuilding,
                                       dict_samples=dict_samples,
                                       list_wea=list_wea, i=n_samp,
                                       MC_analysis=MC_analysis,
                                       build_physic_unc=build_physic_unc)

        #  Get samples for parameters, which are not stored on building object
        inf_rate = dict_samples['inf'][n_samp]
        print('Inf. rate: ', inf_rate)
        usr_air_ex_rate = dict_samples['user_air'][n_samp]
        print('User air exchange rate: ', usr_air_ex_rate)

        # vent_array = list_air_ex_profiles[i]
        vent_array = np.zeros(len(modbuild.environment.weather.tAmbient))

        vent_array += inf_rate + usr_air_ex_rate
        #  Sum up user air exchange and infiltration

        temp_set = dict_samples['set_temp'][n_samp]
        print('Set temperature: ', temp_set)

        #  #  Uncomment, if you want to save and/or load a building pickle file
        #  ##################################################################

        # this_path = os.path.dirname(os.path.abspath(__file__))
        # save_path = os.path.join(this_path, 'mc_building.pkl')
        #
        # #  Pickle and dump building object
        # pickle.dump(modbuild, open(save_path, 'output', mode='wb'))
        #
        # this_path = os.path.dirname(os.path.abspath(__file__))
        # load_path = os.path.join(this_path, 'mc_building.pkl')
        #
        # building = pickle.load(open(load_path, mode='rb'))


        #  Perform VDI 6007 simulation
        #  ##################################################################
        (temp_in, q_heat_cool, q_in_wall, q_out_wall) = \
            tus.calc_th_load_build_vdi6007_ex_build(exbuild=modbuild,
                                                    add_th_load=False,
                                                    vent_factor=None,
                                                    array_vent_rate=vent_array,
                                                    t_set_heat=temp_set,
                                                    t_set_cool=100,
                                                    t_night=16,
                                                    heat_lim_val=1000000000)

        print('result VDI:', temp_in, q_heat_cool, q_in_wall, q_out_wall)

        #  Results
        #  #####################################
        q_heat = np.zeros(len(q_heat_cool))
        for i in range(len(q_heat_cool)):
            if q_heat_cool[i] > 0:
                q_heat[i] = q_heat_cool[i]

        sum_heat = sum(q_heat) * timestep / (3600 * 1000)  # in kWh
        print('Sum net space heating energy in kWh: ', sum_heat)
        print()

        if sum_heat < 0:
            msg = 'Net space heating demand is smaller than zero!'
            raise AssertionError(msg)
        if sum_heat == 0:
            msg = 'Net space heating demand is equal to zero. Check if ' \
                  'this is possible (e.g. high retrofit with low set temp ' \
                  'and high internal loads.)'
            warnings.warn(msg)

        dict_problem['infiltration'].append(dict_samples['inf'][n_samp])
        dict_problem['const_type'].append(dict_samples['const_type'][n_samp])
        dict_problem['dormer'].append(dict_samples['dormer'][n_samp])
        dict_problem['attic'].append(dict_samples['attic'][n_samp])
        dict_problem['cellar'].append(dict_samples['cellar'][n_samp])
        dict_problem['user_air'].append(dict_samples['user_air'][n_samp])
        dict_problem['year'].append(dict_samples['mod_year'][n_samp])

        #  Store space heating results
        list_sh_net_demand.append(sum_heat)
        print('net sh demand', sum_heat)
        list_sh_power_curves.append(q_heat)

        #  Store el. demand and dhw energy
        el_demand = modbuild.get_annual_el_demand()
        list_el_net_demand.append(el_demand)
        dhw_energy = modbuild.get_annual_dhw_demand()
        list_dhw_energies.append(dhw_energy)

        print('El. energy demand in kWh per building:')
        print(el_demand)
        print('Dhw energy demand in kWh per building:')
        print(dhw_energy)
        print('Dhw volume per day in liters (per building):')
        print((dhw_energy * 3600 * 1000) / (4200 * 35 * 365))
        print('############################################################')
        print()

    print('Finished Monte-Carlo space heating simulation for single building')
    print()

    return (list_sh_net_demand, list_sh_power_curves, list_el_net_demand,
            list_dhw_energies, dict_problem)


def run_mc_sh_uncertain_single_building(building, nb_samples,
                                        time_sp_force_retro=40,
                                        max_retro_year=2014,
                                        weather_region=5,
                                        weather_year=2010,
                                        nb_occ_unc=True,
                                        MC_analysis=False,
                                        build_physic_unc=True):
    """
    Perform Monte-Carlo simulation for thermal space heating power generation
    for a single building

    Parameters
    ----------
    building : object
        Extended building object of pycity_calc (should hold occupancy profile)
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
    MC_analysis: boolean, optional
        Defines extra modifications for monte carlo analysis
        (dormer,attic,cellar, construction_type, net_floor_area)
    buil_physic_unc: bool, optional
        Defines,if building physics unknown or not (default: True)
        True - Building physics is unknown
        False - Building physics is known (year of modernisation, dormer, cellar , construction type
                and attic are fixed, net floor area variation is smaller)

    Returns
    -------
    res_tuple : tuple (of lists)
        Results tuple (list_sh, list_sh_curves, list_el, list_dhw)
        1. Entry: list holding net space heating demands in kWh as float
        2. Entry: list holding space heating power curves in W as arrays
        3. Entry: list holding net electric energy demands in kWh
        4. Entry: list holding hot water net energy demands in kWh
    dict_problem : dict (of list)
        Dictionary of inputs with problems
        Keys:
        'year' : Holding modification year sample lists
        'infiltration' : Holding infiltration rate sample lists
        'dormer' : Holding dormer samples list
        'cellar' : Holding cellar samples list
        'attic' : Holding attic samples list
        'const_type' : Holding construction type samples list
        'user_air' : Holding user air ventilation factor sampling

    """

    #  Check, if building holds necessary information
    assert building.build_year is not None
    assert len(building.apartments) >= 1
    for ap in building.apartments:
        assert ap.occupancy is not None, 'Apartment has no occupants!'

    exbuilding = copy.deepcopy(building)

    #  1. Extract parameters
    #  ##################################################################
    timestep = copy.copy(building.environment.timer.timeDiscretization)

    #  2. Perform sampling
    #  ##################################################################

    #  Individual building and user uncertainty sampling
    #  #####################################
    print('Start uncertain parameter sampling for single building')
    dict_samples = \
        building_unc_sampling(exbuilding=exbuilding, nb_samples=nb_samples,
                              max_retro_year=max_retro_year,
                              time_sp_force_retro=time_sp_force_retro,
                              nb_occ_unc=nb_occ_unc,
                              buil_physic_unc=build_physic_unc)

    #  Weather uncertainty
    #  #####################################

    list_wea = \
        weaunc.gen_set_of_weathers(nb_weath=nb_samples, year=weather_year,
                                   timestep=timestep, region_nb=weather_region)

    print('Finished uncertain parameter sampling for single building')
    print()

    #  3. Monte-Carlo simulation
    #  ##################################################################
    print('Start Monte-Carlo simulation for single building')

    (list_sh, list_sh_curves, list_el, list_dhw, dict_problem) = \
        mc_call_single_building(exbuilding, dict_samples, list_wea,
                                MC_analysis=MC_analysis,
                                build_physic_unc=build_physic_unc)

    print('Finished Monte-Carlo simulation for single building')
    print()

    return (list_sh, list_sh_curves, list_el, list_dhw, dict_samples,
            dict_problem)


if __name__ == '__main__':

    #  Current python module path
    this_path = os.path.dirname(os.path.abspath(__file__))

    #  User inputs for Monte-Carlo Simulation
    #  ###############################################################
    nb_samples = 1000
    time_sp_force_retro = 50  # years
    max_retro_year = 2000
    weather_region = 5
    weather_year = 2010
    build_physic_unc = True  # Building physics are uncertain --> True

    #  Defines, if number of occupants per apartment is unknown
    nb_occ_unc = True
    #  nb_occ_unc == True: Number of occupants is unknown
    #  nb_occ_unc == False: Number of occupants is known

    #  Save path
    #  Define path to save result pickle file to
    #  ###############################################################
    # save_file = 'mc_building_res_forsterlinde_1011.pkl'
    # save_path = os.path.join(this_path, 'output', save_file)

    #  Building object generation
    #  ###############################################################
    #  Decide, if you want to load a city object and extract a building or
    #  ir you want to load a pickled building object or
    #  if you want to generate a new building object instance
    use_build_mode = 0
    #  use_build_mode == 0: Load city object and extract specific building
    #  use_build_mode == 1: Load pickled building object   w
    #  use_build_mode == 2: Generate own building object instance

    # #  Data to save building object
    # #  ###############################################################
    save_building = True
    building_save_file = 'building_obj.pkl'
    build_path = os.path.join(this_path, 'output', building_save_file)

    #  Settings of MA Laura Esling
    MC_analysis = False  # Enable usage of further uncertain parameters

    #  Load city object and extract building below
    # #  ###############################################################
    if use_build_mode == 0:

        #  City object pickle file, which should be loaded
        #city_f_name = 'aachen_forsterlinde_mod_new_1.pkl'
        #city_f_name = 'aachen_frankenberg_mod_new_1.pkl'
        #city_f_name = 'aachen_kronenberg_mod_new_1.pkl'
        #city_f_name = 'aachen_preusweg_mod_new_1.pkl'
        #city_f_name = 'aachen_tuerme_mod_new_1.pkl'
        # city_f_name = 'aachen_huenefeld_mod_new_1.pkl'
        city_f_name = 'aachen_kronenberg_6.pkl'

        #  Building node number, which should be used to extract building data
        #build_node_nb = 1011  # Forsterlinde
        #build_node_nb = 1020   # Frankenberg
        #build_node_nb = 1002  # Kronenberg
        #build_node_nb = 1092  # Preusweg
        #build_node_nb = 1010  # Tuerme
        build_node_nb = 1001  # Huenefeld

        #  Path to load city file
        load_city_path = os.path.join(this_path, 'input', city_f_name)

        #  Load city object instance
        city = pickle.load(open(load_city_path, mode='rb'))

        extended_building = city.nodes[build_node_nb]['entity']

        #  Mod. building build year
        extended_building.build_year = 1990

        save_file = city_f_name[:-4] + '_single_b_new_dhw_' + str(
            build_node_nb) + '.pkl'
        save_path = os.path.join(this_path, 'output', save_file)

    # Load building object
    # #  ###############################################################
    elif use_build_mode == 1:

        #  Building object filename
        building_f_name = 'building.pkl'

        #  Path to load city file
        load_build_path = os.path.join(this_path, 'input', building_f_name)

        #  Load building object instance
        extended_building = pickle.load(open(load_build_path, mode='rb'))

    # User inputs for building generation
    #  ###############################################################
    elif use_build_mode == 2:
        #  Define simulation settings
        build_year = 1990  # Year of construction
        mod_year = 2000  # Year of retrofit
        net_floor_area = 200  # m2
        height_of_floors = 2.8  # m
        nb_of_floors = 2  # m
        num_occ = 3  # Set fix to prevent long run time for multiple new occupancy
        #  and electrical load profiles

        #  #  Create PyCity_Calc environment
        #  ###############################################################

        #  Create extended environment of pycity_calc
        year = 2010
        timestep = 3600  # Timestep in seconds
        location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop
        altitude = 55  # Altitude of Bottrop

        #  ###############################################################

        #  Generate timer object
        timer = time.TimerExtended(timestep=timestep, year=year)

        #  Generate weather object
        weather = Weather.Weather(timer, useTRY=True, location=location,
                                  altitude=altitude)

        #  Generate market object
        market = mark.Market()

        #  Generate co2 emissions object
        co2em = co2.Emissions(year=year)

        #  Generate environment
        environment = env.EnvironmentExtended(timer, weather, prices=market,
                                              location=location, co2em=co2em)

        #  #  Create occupancy profile
        #  #####################################################################

        print('Calculate occupancy.\n')
        #  Generate occupancy profile
        occupancy_obj = occ.Occupancy(environment, number_occupants=num_occ)

        print('Finished occupancy calculation.\n')

        # #  Create electrical load
        #  #####################################################################

        print('Calculate el. load.\n')

        el_dem_stochastic = eldem.ElectricalDemand(environment,
                                                   method=2,
                                                   annualDemand=3000,
                                                   # Dummy value
                                                   do_normalization=True,
                                                   total_nb_occupants=num_occ,
                                                   randomizeAppliances=True,
                                                   lightConfiguration=10,
                                                   occupancy=occupancy_obj.occupancy[
                                                             :])

        print('Finished el. load calculation.\n')

        #  # Create dhw load
        #  #####################################################################
        dhw_stochastical = dhwater.DomesticHotWater(environment,
                                                    tFlow=60,
                                                    thermal=True,
                                                    method=2,
                                                    supplyTemperature=20,
                                                    occupancy=occupancy_obj.occupancy)

        #  #  Create apartment and building object
        #  #####################################################################

        #  Create apartment
        apartment = Apartment.Apartment(environment)

        #  Add demands to apartment
        apartment.addMultipleEntities([el_dem_stochastic, occupancy_obj,
                                       dhw_stochastical])

        #  Create extended building object
        extended_building = build_ex.BuildingExtended(environment,
                                                      build_year=build_year,
                                                      mod_year=mod_year,
                                                      build_type=0,
                                                      roof_usabl_pv_area=30,
                                                      net_floor_area=net_floor_area,
                                                      height_of_floors=height_of_floors,
                                                      nb_of_floors=nb_of_floors,
                                                      neighbour_buildings=0,
                                                      residential_layout=0,
                                                      attic=1, cellar=1,
                                                      construction_type='heavy',
                                                      dormer=1)

        #  Add apartment to extended building
        extended_building.addEntity(entity=apartment)

    (list_sh, list_sh_curves, list_el, list_dhw, dict_samples, dict_problem) = \
        run_mc_sh_uncertain_single_building(building=extended_building,
                                            nb_samples=nb_samples,
                                            time_sp_force_retro=
                                            time_sp_force_retro,
                                            max_retro_year=max_retro_year,
                                            weather_region=weather_region,
                                            weather_year=weather_year,
                                            nb_occ_unc=nb_occ_unc,
                                            MC_analysis=MC_analysis,
                                            build_physic_unc=build_physic_unc)

    list_max_power = []
    for power in list_sh_curves:
        list_max_power.append(max(power))

    if save_building:
        try:
            pickle.dump(extended_building, open(build_path, mode='wb'))
            print('Saved building pickle file to')
            print(str(build_path))
        except:
            warnings.warn('Could not pickle and dump building object instance')

    # Save results
    try:
        pickle.dump((list_sh, list_sh_curves, list_el, list_dhw),
                    open(save_path, mode='wb'))
        print('Saved results of Monte-Carlo analysis of building into ')
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

    print('Problem:', dict_problem)
    print('modification year: ', dict_problem['year'])
    print('infiltration', dict_problem['infiltration'])
    print('user air: ', dict_problem['user_air'])
    print('const_type', dict_problem['const_type'])
    print('dormer : ', dict_problem['dormer'])
    print('cellar : ', dict_problem['cellar'])
    print('attic : ', dict_problem['attic'])

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
    plt.xlabel('Space heating maximal power value in Watt')
    plt.ylabel('Number of values')
    plt.show()
    plt.close()

    fig = plt.figure()
    # the histogram of the data
    plt.hist(list_el, bins='auto')
    plt.xlabel('Electric energy demand in kWh')
    plt.ylabel('Number of values')
    plt.show()
    plt.close()

    fig = plt.figure()
    # the histogram of the data
    plt.hist(list_dhw, bins='auto')
    plt.xlabel('Hot water energy demand in kWh')
    plt.ylabel('Number of values')
    plt.show()
    plt.close()

    list_vol = []
    for dhw in list_dhw:
        list_vol.append((dhw * 3600 * 1000) / (4200 * 35 * 365))
    # the histogram of the data
    plt.hist(list_vol, bins='auto')
    plt.xlabel('Hot water volume in liters')
    plt.ylabel('Number of values')
    plt.show()
    plt.close()

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2)
    # the histogram of the sampling
    ax1.hist(dict_samples['inf'], 100)
    ax1.set_title('Infiltration')

    ax2.hist(dict_samples['mod_year'], 100)
    ax2.set_title('modification year')

    ax3.hist(dict_samples['attic'], 100)
    ax3.set_title('attic')

    ax4.hist(dict_samples['net_floor_area'], 100)
    ax4.set_title('net floor area')

    plt.show()
    plt.close()
