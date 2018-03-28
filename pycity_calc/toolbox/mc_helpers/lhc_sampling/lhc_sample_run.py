#!/usr/bin/env python
# coding=utf-8
"""

"""
from __future__ import division

import os
import pickle
import random as rd
import numpy as np
import warnings
import pyDOE
import matplotlib.pylab as plt
import scipy.stats.distributions as distr
from scipy import stats
from scipy.stats import lognorm

import pycity_base.classes.demand.Occupancy as occu
import pycity_base.classes.demand.ElectricalDemand as eldem
import pycity_base.classes.demand.DomesticHotWater as dhwdem

import pycity_calc.toolbox.mc_helpers.user.user_unc_sampling as useunc


#  TODO: Radiation uncertainty

def search_for_pkl_files_in_dir(dir, fileending='.pkl'):
    """
    Search for pkl files in dir and returns list with file names

    Parameters
    ----------
    dir : str
        Path to folder, where search is performed
    fileending : str, optional
        Defines fileending (default: '.pkl')

    Returns
    -------
    list_pkl_files : list (of str)
        List holding names of pkl files found in dir
    """
    list_pkl_files = []
    for file in os.listdir(dir):
        if file.endswith(fileending):
            list_pkl_files.append(file)
    return list_pkl_files


def gen_empty_res_dicts(city, nb_samples):
    """
    Generate empty result dicts (holding arrays with zeros) for mc run

    Parameters
    ----------
    city : object
        City object of pyCity_calc
    nb_samples : int
        Number of samples

    Returns
    -------
    tup_res : tuple (of dicts)
        Tuple holding 2 dicts (dict_city_sample, dict_build_samples)
        dict_city_sample : dict
            Dict holding city parameter names as keys and numpy arrays with
            samples as dict values
        dict_build_samples : dict
            Dict. holding building ids as keys and dict of samples as values.
            These dicts hold paramter names as keys and numpy arrays with
            samples as dict values
    """

    list_build_ids = city.get_list_build_entity_node_ids()

    #  Generate results sample dicts with arrays with zeros
    #  #######################################################################
    dict_city_sample = {}  # Holding city sampels
    #  Holding parameter name as key and array as value
    dict_build_samples = {}
    #  Holding building id as key and dict with arrays as values

    #  City sample dict
    #  Uncertain interest
    dict_city_sample['interest'] = np.zeros(nb_samples)
    #  Uncertain price change capital
    dict_city_sample['price_ch_cap'] = np.zeros(nb_samples)
    #  Uncertain price change demand gas
    dict_city_sample['price_ch_dem_gas'] = np.zeros(nb_samples)
    #  Uncertain price change demand electricity
    dict_city_sample['price_ch_dem_el'] = np.zeros(nb_samples)
    #  Uncertain price change operation
    dict_city_sample['price_ch_op'] = np.zeros(nb_samples)
    #  Uncertain price change eeg payments for self-con. chp el.
    dict_city_sample['price_ch_eeg_chp'] = np.zeros(nb_samples)
    #  Uncertain price change eeg payments for self-con. PV el.
    dict_city_sample['price_ch_eeg_pv'] = np.zeros(nb_samples)
    #  Uncertain price change EEX baseload price
    dict_city_sample['price_ch_eex'] = np.zeros(nb_samples)
    #  Uncertain price change grid usage fee
    dict_city_sample['price_ch_grid_use'] = np.zeros(nb_samples)
    #  Uncertain ground temperature
    dict_city_sample['temp_ground'] = np.zeros(nb_samples)
    #  Uncertain LHN loss factor change
    dict_city_sample['lhn_loss'] = np.zeros(nb_samples)
    #  Uncertain LHN investment cost change
    dict_city_sample['lhn_inv'] = np.zeros(nb_samples)
    # Uncertain summer mode on / off
    #  Holding list holding arrays with building node ids with heating during
    #  summer (each sample holds array for each building, if heating is on or
    #  off
    dict_city_sample['list_sum_on'] = []
    dict_city_sample['grid_av_fee'] = np.zeros(nb_samples)

    #  Loop over buildings
    #  ##################################
    for n in list_build_ids:
        dict_samples = {}  # Holding building, apartment and esys samples

        #  Building, apartments and esys samples
        #  Uncertain space heating demand
        dict_samples['sh_dem'] = np.zeros(nb_samples)
        #  Uncertain battery params
        dict_samples['self_discharge'] = np.zeros(nb_samples)
        dict_samples['eta_charge'] = np.zeros(nb_samples)
        dict_samples['eta_discharge'] = np.zeros(nb_samples)
        # dict_samples['bat_lifetime'] = np.zeros(nb_samples)
        # dict_samples['bat_maintain'] = np.zeros(nb_samples)
        dict_samples['bat_inv'] = np.zeros(nb_samples)
        #  Uncertain boiler params
        dict_samples['eta_boi'] = np.zeros(nb_samples)
        # dict_samples['boi_lifetime'] = np.zeros(nb_samples)
        # dict_samples['boi_maintain'] = np.zeros(nb_samples)
        dict_samples['boi_inv'] = np.zeros(nb_samples)
        #  Uncertain chp params
        dict_samples['omega_chp'] = np.zeros(nb_samples)
        # dict_samples['chp_lifetime'] = np.zeros(nb_samples)
        # dict_samples['chp_maintain'] = np.zeros(nb_samples)
        dict_samples['chp_inv'] = np.zeros(nb_samples)
        #  Uncertain HP params
        dict_samples['qual_grade_aw'] = np.zeros(nb_samples)
        dict_samples['qual_grade_ww'] = np.zeros(nb_samples)
        dict_samples['t_sink'] = np.zeros(nb_samples)
        # dict_samples['hp_lifetime'] = np.zeros(nb_samples)
        # dict_samples['hp_maintain'] = np.zeros(nb_samples)
        dict_samples['hp_inv'] = np.zeros(nb_samples)
        #  Uncertain EH params
        # dict_samples['eh_lifetime'] = np.zeros(nb_samples)
        # dict_samples['eh_maintain'] = np.zeros(nb_samples)
        dict_samples['eh_inv'] = np.zeros(nb_samples)
        #  Uncertain tes params
        dict_samples['k_loss'] = np.zeros(nb_samples)
        # dict_samples['tes_lifetime'] = np.zeros(nb_samples)
        # dict_samples['tes_maintain'] = np.zeros(nb_samples)
        dict_samples['tes_inv'] = np.zeros(nb_samples)
        #  Uncertain PV params
        dict_samples['eta_pv'] = np.zeros(
            nb_samples)  # Also including inv. loss
        dict_samples['beta'] = np.zeros(nb_samples)
        dict_samples['gamma'] = np.zeros(nb_samples)
        # dict_samples['pv_lifetime'] = np.zeros(nb_samples)
        # dict_samples['pv_maintain'] = np.zeros(nb_samples)
        dict_samples['pv_inv'] = np.zeros(nb_samples)

        #  Get nb of apartments
        nb_app = len(city.nodes[n]['entity'].apartments)

        #  Generate apartment uncertain parameters
        #  Rows (parameter array per apartment)
        dict_samples['app_nb_occ'] = np.zeros((nb_app, nb_samples))
        dict_samples['app_el_dem'] = np.zeros((nb_app, nb_samples))
        dict_samples['app_dhw_dem'] = np.zeros((nb_app, nb_samples))

        #  Save parameter dict to main building dict
        dict_build_samples[n] = dict_samples

    return (dict_city_sample, dict_build_samples)


def calc_nb_unc_par(city, nb_city_unc_par=15,
                    nb_build_unc_par=33, nb_app_unc_par=3):
    """
    Calculate total number of uncertain parameters required for LHC design

    Parameters
    ----------
    city : object
        City object of pyCity_calc
    nb_city_unc_par : int, optional
        Number of uncertain parameters on city level (default: 15)
    nb_build_unc_par : int, optional
        Number of uncertain parameters on building level (default: 33)
    nb_app_unc_par : int, optional
        Number of uncertain parameters on apartment level (default: 3)

    Returns
    -------
    nb_par : int
        Number of parameters (input for latin hypercube design)
    """

    nb_app = 0

    list_build_ids = city.get_list_build_entity_node_ids()
    nb_build = len(list_build_ids)

    for n in list_build_ids:
        build = city.nodes[n]['entity']
        nb_app += len(build.apartments)

    nb_par = nb_city_unc_par + nb_build_unc_par * nb_build \
             + nb_app_unc_par * nb_app

    return nb_par


def do_lhc_city_sampling(city, nb_par, nb_samples, dict_city_sample,
                         dict_build_samples, load_sh_mc_res=False,
                         path_mc_res_folder=None, dem_unc=True):
    """
    Performs latin hypercube sampling and adds samples to empty
    dict_city_sample, dict_build_samples

    Parameters
    ----------
    city : object
        City object of pyCity_calc
    nb_par : int
        Number of uncertain parameters
    nb_samples : int
        Number of desired samples per uncertain parameter
    dict_city_sample : dict
        Dict holding city parameter names as keys and numpy arrays with
        samples as dict values
    dict_build_samples : dict
        Dict. holding building ids as keys and dict of samples as values.
        These dicts hold paramter names as keys and numpy arrays with
        samples as dict values
    load_sh_mc_res : bool, optional
        If True, tries to load space heating monte-carlo uncertainty run
        results for each building and uses result to sample space heating
        values. If False, uses default distribution to sample space heating
        values (default: False)
    path_mc_res_folder : str, optional
        Path to folder, where sh mc run results are stored (default: None).
        Only necessary if load_sh_mc_res is True
    dem_unc : bool, optional
        Defines, if thermal, el. and dhw demand are assumed to be uncertain
        (default: True). If True, samples demands. If False, uses reference
        demands.
    """

    list_build_ids = city.get_list_build_entity_node_ids()

    design_count = 0

    #  Perform lhc design call
    design = pyDOE.lhs(n=nb_par, samples=nb_samples, criterion='center')

    # print(design)
    # plt.plot(sorted(design[0]))
    # plt.show()
    # plt.close()

    #  Assumes equal distributions for given parameters (except lhn_inv!)
    dict_ref_val_city = {'interest': [1.01, 1.0675],
                         'price_ch_cap': [1.0, 1.0575],
                         'price_ch_dem_gas': [0.96, 1.06],
                         'price_ch_dem_el': [0.98, 1.1],
                         'price_ch_op': [1, 1.0575],
                         'price_ch_eeg_chp': [0.98, 1.02],
                         'price_ch_eeg_pv': [0.98, 1.02],
                         'price_ch_eex': [0.94, 1.02],
                         'price_ch_grid_use': [0.98, 1.04],
                         'temp_ground': [8, 12],
                         'list_sum_on': [0, 1],
                         'lhn_loss': [0.75, 1.25],
                         'grid_av_fee': [0.0001, 0.015],
                         'lhn_inv': [0, 0.5]  # log mean, std
                         }

    for key in dict_ref_val_city.keys():
        if key != 'lhn_inv' and key != 'list_sum_on':
            for i in range(len(design[:, design_count])):
                val_lhc = design[i, design_count]

                min_val = dict_ref_val_city[key][0]
                max_val = dict_ref_val_city[key][1]

                val_conv = val_lhc * (max_val - min_val) + min_val

                dict_city_sample[key][i] = val_conv
        elif key == 'lhn_inv':

            # log_mean = dict_ref_val_city[key][0]
            log_scale = dict_ref_val_city[key][1]

            array_conv = lognorm(s=log_scale).ppf(design[:, design_count])

            dict_city_sample[key] = array_conv

        elif key == 'list_sum_on':
            for i in range(len(design[:, design_count])):
                val_lhc = design[i, design_count]

                min_val = dict_ref_val_city[key][0]
                max_val = dict_ref_val_city[key][1]

                val_conv = val_lhc * (max_val - min_val) + min_val
                #  val_conv defines share of buildings, which should have
                #  heating on during summer --> Select buildings with
                #  heating on

                #  Define number of buildings, which should have heating on
                #  during summer
                nb_heat_on = int(val_conv * len(list_build_ids))

                #  Randomly select number of buildings, until share is correct
                array_heat_on = np.random.choice(a=list_build_ids,
                                                 size=nb_heat_on,
                                                 replace=False)

                dict_city_sample[key].append(array_heat_on)

        design_count += 1

    # plt.plot(sorted(dict_city_sample['lhn_loss']))
    # plt.show()
    # plt.close()
    #
    # plt.plot(sorted(dict_city_sample['lhn_inv']))
    # plt.show()
    # plt.close()

    # array_summer_heat_on = citysample. \
    #     sample_quota_summer_heat_on(nb_samples=nb_runs)
    #
    # list_s_heat_on_id_arrays = citysample. \
    #     sample_list_sum_heat_on_arrays(nb_samples=nb_runs,
    #                                    array_ratio_on=array_summer_heat_on,
    #                                    list_b_ids=self._list_build_ids)
    #
    # #  Only used, if LHN exists, but required to prevent ref.
    # #  before assignment error #289
    # #  If LHN exists, sample for LHN with ref. investment cost of 1
    # array_lhn_inv = esyssample.sample_invest_unc(nb_samples=nb_runs,
    #                                              ref_inv=1)
    # #  If LHN exists, sample losses for LHN (ref loss 1)
    # array_lhn_loss = esyssample.sample_lhn_loss_unc(nb_samples=nb_runs,
    #                                                 ref_loss=1)

    dict_ref_val_build = {'sh_dem': [1, 0.5791],  # mean, std
                          'self_discharge': [0.00001, 0.001],
                          'eta_charge': [0.95, 0.005],  # mean, std
                          'eta_discharge': [0.9, 0.005],  # mean, std
                          # 'bat_lifetime': [0.9, 0.005],  # curr. const.
                          # 'bat_maintain': [0.9, 0.005],  # curr. const.
                          'bat_inv': [0, 0.3],  # log mean, std
                          'eta_boi': [0.95, 0.005],  # mean, std
                          # 'boi_lifetime': [0.9, 0.005],  # curr. const.
                          # 'boi_maintain': [0.9, 0.005],  # curr. const.
                          'boi_inv': [0, 0.2],  # log mean, std
                          'omega_chp': [0.9, 0.02],  # mean, std
                          # 'chp_lifetime': [0.9, 0.005],  # curr. const.
                          # 'chp_maintain': [0.9, 0.005],  # curr. const.
                          'chp_inv': [0, 0.3],  # log mean, std
                          'qual_grade_ww': [0.38, 0.48],
                          'qual_grade_aw': [0.29, 0.39],
                          't_sink': [31, 55],
                          # 'hp_lifetime': [0.9, 0.005],  # curr. const.
                          # 'hp_maintain': [0.9, 0.005],  # curr. const.
                          'hp_inv': [0, 0.2],  # log mean, std
                          # 'eh_lifetime': [0.9, 0.005],  # curr. const.
                          # 'eh_maintain': [0.9, 0.005],  # curr. const.
                          'eh_inv': [0, 0.2],  # log mean, std
                          'k_loss': [0.1, 0.5],
                          # 'tes_lifetime': [0.9, 0.005],  # curr. const.
                          # 'tes_maintain': [0.9, 0.005],  # curr. const.
                          'tes_inv': [0, 0.2],  # log mean, std
                          'eta_pv': [0.1275, 0.02],  # mean, std
                          'beta': [0, 60],
                          'gamma': [-180, 180],
                          # 'pv_lifetime': [0.9, 0.005],  # curr. const.
                          # 'pv_maintain': [0.9, 0.005],  # curr. const.
                          'pv_inv': [0, 0.3],  # log mean, std
                          }

    #  Try to load space heating uncertainty run results for sampling
    #  ##################################################################
    if load_sh_mc_res:
        if path_mc_res_folder is None:
            msg = 'path_mc_res_folder cannot be None, when space heating mc' \
                  ' results should be loaded!'
            raise AssertionError(msg)

        # Try to load results
        list_pkl_files = search_for_pkl_files_in_dir(dir=path_mc_res_folder)

        if len(list_pkl_files) > 0:
            print('Found mc sh run pkl. result files:')
            for entry in list_pkl_files:
                print(entry)
        else:
            msg = 'Could not find any .pkl result files in ' \
                  + str(path_mc_res_folder)
            raise AssertionError(msg)

        dict_build_mc_res = {}
        #  Add results to dict_build_mc_res
        for key in dict_build_samples.keys():
            for entry in list_pkl_files:
                if entry.find(str(key)) != -1:  # If key is substring of entry

                    path_load = os.path.join(path_mc_res_folder, entry)

                    list_mc_res = pickle.load(open(path_load, mode='rb'))

                    #  Save first result list in list_mc_res --> sh demands
                    dict_build_mc_res[key] = list_mc_res[0]

                    # plt.plot(sorted(dict_build_mc_res[1001]))
                    # plt.show()
                    # plt.close()

                    # plt.hist(dict_build_mc_res[1001], bins='auto')
                    # plt.show()
                    # plt.close()
    # ##################################################################

    #  Sampling for each building
    #  ####################################################################
    #  Loop over building ids
    for key in dict_build_samples.keys():
        #  Loop over parameters
        for parkey in dict_ref_val_build.keys():
            if parkey in ['self_discharge', 'qual_grade_ww', 'qual_grade_aw',
                          'k_loss', 'beta', 'gamma', 't_sink']:
                #  Equal distribution
                #  Loop over single parameter values
                for i in range(len(design[:, design_count])):
                    val_lhc = design[i, design_count]

                    min_val = dict_ref_val_build[parkey][0]
                    max_val = dict_ref_val_build[parkey][1]

                    val_conv = val_lhc * (max_val - min_val) + min_val

                    dict_build_samples[key][parkey][i] = val_conv

            elif parkey in ['eta_charge', 'eta_discharge', 'eta_boi',
                            'omega_chp', 'eta_pv']:
                # Gaussian distribution

                mean_val = dict_ref_val_build[parkey][0]
                std_val = dict_ref_val_build[parkey][1]

                array_conv = stats.norm(loc=mean_val,
                                        scale=std_val).ppf(
                    design[:, design_count])

                dict_build_samples[key][parkey] = array_conv

            elif parkey in ['bat_inv', 'boi_inv', 'chp_inv', 'hp_inv',
                            'eh_inv', 'tes_inv', 'pv_inv']:
                # Log normal distribution

                # log_mean = dict_ref_val_build[parkey][0]
                log_scale = dict_ref_val_build[parkey][1]

                array_conv = lognorm(s=log_scale).ppf(design[:, design_count])

                dict_build_samples[key][parkey] = array_conv

            elif parkey in ['sh_dem']:
                #  Space heating (gaussian distribution)
                #  Get reference space heating demand
                sh_dem_ref = city.nodes[key]['entity'] \
                    .get_annual_space_heat_demand()
                assert sh_dem_ref > 0

                if dem_unc:

                    #  If demand is assumed to be uncertain
                    if load_sh_mc_res:
                        #  Use loaded results

                        #  Sample from dict_build_mc_res
                        list_sh_res = dict_build_mc_res[key]

                        # #  Estimate params of gaussian distribution
                        # mean_val, std_val = stats.norm.fit(data=list_sh_res)

                        # plt.hist(list_sh_res, bins=int(len(list_sh_res)/10))
                        # plt.show()
                        # plt.close()

                        #  Estimate parameters for log. normal distribution
                        shape, loc, scale = stats.lognorm.fit(data=list_sh_res,
                                                              floc=0)

                        array_conv = distr.lognorm(s=shape).ppf(design[:,
                                                                design_count])
                        array_conv *= sh_dem_ref
                    else:
                        mean_val = sh_dem_ref * dict_ref_val_build[parkey][0]
                        std_val = sh_dem_ref * dict_ref_val_build[parkey][1]

                        array_conv = stats.norm(loc=mean_val,
                                                scale=std_val).ppf(
                            design[:, design_count])

                        #  Eliminate negative values, if necessary
                        for j in range(len(array_conv)):
                            if array_conv[j] < 0:
                                array_conv[j] = 0
                else:

                    #  Demand is certain
                    array_conv = np.ones(nb_samples) * sh_dem_ref

                dict_build_samples[key][parkey] = array_conv

            design_count += 1

        # Sample for each apartment
        #  ###################################################################

        nb_app = len(city.nodes[key]['entity'].apartments)
        #  Get building type (sfh/mfh)
        if nb_app == 1:
            res_type = 'sfh'
        elif nb_app > 1:
            res_type = 'mfh'

        if dem_unc:
            #  Demand is assumed to be uncertain

            # Loop over nb of apartments
            for i in range(nb_app):

                #  Sample nb. of occupants
                array_nb_occ = useunc.calc_sampling_occ_per_app(nb_samples=
                                                                nb_samples)

                #  Save array to results dict
                dict_build_samples[key]['app_nb_occ'][i, :] = array_nb_occ

                for k in range(len(array_nb_occ)):
                    #  Sample el. demand value per apartment
                    el_dem_per_app = useunc. \
                        calc_sampling_el_demand_per_apartment(
                        nb_samples=1,
                        nb_persons=array_nb_occ[k], type=res_type)[0]
                    #  Sample dhw demand value per apartment

                    #  Hot water volume per apartment
                    dhw_vol_per_app = useunc. \
                        calc_sampling_dhw_per_apartment(nb_samples=1,
                                                        nb_persons=
                                                        array_nb_occ[k],
                                                        b_type=res_type)

                    #  Convert liters/app*day to kWh/app*year
                    dhw_dem_per_app = \
                        useunc.recalc_dhw_vol_to_energy(vol=dhw_vol_per_app)

                    #  Save el. demand
                    dict_build_samples[key]['app_el_dem'][i, k] = \
                        el_dem_per_app
                    #  Save dhw demand
                    dict_build_samples[key]['app_dhw_dem'][i, k] = \
                        dhw_dem_per_app

                    # plt.plot(sorted(dict_build_samples[1001]['eta_pv']))
                    # plt.show()
                    # plt.close()

                    # plt.plot(sorted(dict_build_samples[1001]['app_nb_occ'][0]))
                    # plt.show()
                    # plt.close()
                    #
                    # plt.plot(sorted(dict_build_samples[1001]['app_el_dem'][0]))
                    # plt.show()
                    # plt.close()
                    #
                    # plt.plot(sorted(dict_build_samples[1001]['app_dhw_dem'][0]))
                    # plt.show()
                    # plt.close()
        else:
            #  Demand is certain

            #  Reference el. energy demand
            el_dem = city.nodes[key]['entity'].get_annual_el_demand()

            #  Reference el. energy demand
            dhw_dem = city.nodes[key]['entity'].get_annual_dhw_demand()

            el_per_app = el_dem / nb_app
            dhw_per_app = dhw_dem / nb_app

            # Loop over nb of apartments
            for i in range(nb_app):
                #  Apartment pointer
                app = city.nodes[key]['entity'].apartments[i]

                #  Get nb. of occupants within apartment
                nb_occ = app.occupancy.number_occupants

                array_nb_occ = np.ones(nb_samples) * int(nb_occ)

                #  Save array to results dict
                dict_build_samples[key]['app_nb_occ'][i, :] = array_nb_occ

                #  Now distribute reference demand equally to each apartment
                #  Save el. demand
                dict_build_samples[key]['app_el_dem'][i, :] = \
                    el_per_app
                #  Save dhw demand
                dict_build_samples[key]['app_dhw_dem'][i, :] = \
                    dhw_per_app


def gen_profile_pool(city, nb_samples, dict_build_samples, share_profiles=1):
    """
    Generate profile pool of user, el. load and dhw profiles for each building

    Parameters
    ----------
    city : object
        City object of pyCity_calc
    nb_samples : int
        Nb. of samples
    dict_build_samples : dict
        Dict. holding building ids as keys and dict of samples as values.
        These dicts hold paramter names as keys and numpy arrays with
        samples as dict values
    share_profiles : float, optional
        Defines share on nb_samples to define nb. of profiles (default: 1).
        E.g. 0.5 with 20 nb_samples means, that 10 el. profiles are generated
        for profile pool

    Returns
    -------
    dict_profiles : dict
        Dict holding building ids as keys and numpy.arrays with different
        el. load profiles per building
    """
    assert nb_samples > 0

    print()
    print('Start generation of profile pool')

    dict_profiles = {}

    profile_length = len(city.environment.weather.tAmbient)

    #  Estimate nb. of different profiles per building
    nb_profiles = int(nb_samples * share_profiles)

    #  Loop over buildings
    for key in dict_build_samples.keys():

        print('Generate profiles for building ', key)

        dict_profiles_build = {}

        #  Generate results arrays with zeros
        el_profiles = np.zeros((nb_profiles, profile_length))
        dhw_profiles = np.zeros((nb_profiles, profile_length))

        #  Access building sample dict
        dict_samples = dict_build_samples[key]

        #  Access occupants per apartment
        occ_array = dict_samples['app_nb_occ']

        #  Loop over nb. of profiles
        for i in range(nb_profiles):
            for a in range(len(city.nodes[key]['entity'].apartments)):
                occupancy = occu.Occupancy(environment=city.environment,
                                           number_occupants=int(occ_array[a,
                                                                          i]))

                el_dem_obj = eldem. \
                    ElectricalDemand(environment=city.environment,
                                     method=2,
                                     total_nb_occupants=int(occ_array[a, i]),
                                     randomizeAppliances=True,
                                     lightConfiguration=rd.randint(0, 10),
                                     occupancy=occupancy.occupancy,
                                     prev_heat_dev=True)

                dhw_dem_obj = dhwdem. \
                    DomesticHotWater(city.environment,
                                     tFlow=60,
                                     thermal=True,
                                     method=2,
                                     supplyTemperature=20,
                                     occupancy=occupancy.occupancy)

                el_profiles[i, :] += el_dem_obj.loadcurve
                dhw_profiles[i, :] += dhw_dem_obj.loadcurve

        dict_profiles_build['el_profiles'] = el_profiles
        dict_profiles_build['dhw_profiles'] = dhw_profiles

        dict_profiles[key] = dict_profiles_build

    print()
    print('Finished profile pool generation')
    print()

    return dict_profiles


def run_overall_lhc_sampling(city, nb_samples,
                             load_sh_mc_res=False,
                             path_mc_res_folder=None,
                             use_profile_pool=False,
                             gen_use_prof_method=0,
                             path_profile_dict=None,
                             nb_profiles=None,
                             load_city_n_build_samples=False,
                             path_city_sample_dict=None,
                             path_build_sample_dict=None,
                             dem_unc=True):
    """
    Generates empty sample dicts and performs latin hypercube sampling.
    Adds samples to dict_city_sample, dict_build_samples

    Parameters
    ----------
    city : object
        City object of pyCity_calc
    nb_samples : int
        Number of samples
    load_sh_mc_res : bool, optional
        If True, tries to load space heating monte-carlo uncertainty run
        results for each building and uses result to sample space heating
        values. If False, uses default distribution to sample space heating
        values (default: False)
    path_mc_res_folder : str, optional
        Path to folder, where sh mc run results are stored (default: None).
        Only necessary if load_sh_mc_res is True
    use_profile_pool : bool, optional
        Defines, if user/el. load/dhw profile pool should be generated
        (default: False). If True, generates profile pool.
    gen_use_prof_method : int, optional
        Defines method for el. profile pool usage (default: 0).
        Options:
        - 0: Generate new el. profile pool
        - 1: Load profile pool from path_profile_dict
    path_profile_dict : str, optional
        Path to dict with el. profile pool (default: None).
    nb_profiles : int, optional
        Desired number of profile samples per building, when profile pool
        is generated (default: None). If None, uses nb_samples.
    load_city_n_build_samples : bool, optional
        Defines, if existing city and building sample dicts should be
        loaded (default: False). If False, generates new sample dicts.
    path_city_sample_dict : str, optional
        Defines path to city sample dict (default: None). Only relevant,
        if load_city_n_build_samples is True
    path_build_sample_dict : str, optional
        Defines path to building sample dict (default: None). Only relevant,
        if load_city_n_build_samples is True
    dem_unc : bool, optional
        Defines, if thermal, el. and dhw demand are assumed to be uncertain
        (default: True). If True, samples demands. If False, uses reference
        demands.

    Returns
    -------
    tup_res : tuple (of dicts)
        Tuple holding 3 dicts
        (dict_city_sample, dict_build_samples, dict_profiles)
        dict_city_sample : dict
            Dict holding city parameter names as keys and numpy arrays with
            samples as dict values
        dict_build_samples : dict
            Dict. holding building ids as keys and dict of samples as values.
            These dicts hold paramter names as keys and numpy arrays with
            samples as dict values
        dict_profiles : dict
            Dict. holding building ids as keys and dict with numpy arrays
            with different el. and dhw profiles for each building as value
            fict_profiles_build['el_profiles'] = el_profiles
            dict_profiles_build['dhw_profiles'] = dhw_profiles
            When use_profile_pool is False, dict_profiles is None
    """
    assert nb_samples > 0
    assert gen_use_prof_method in [0, 1]

    if use_profile_pool and gen_use_prof_method == 1:
        if path_profile_dict is None:
            msg = 'path_profile_dict cannot be None, if ' \
                  'gen_use_prof_method==1 (load el. profile pool)!'
            raise AssertionError(msg)

    if nb_profiles is None:
        nb_profiles = int(nb_samples)

    if load_city_n_build_samples:
        #  Load existing city and building sample dictionaries
        dict_city_sample = pickle.load(open(path_city_sample_dict, mode='rb'))
        dict_build_samples = pickle.load(open(path_build_sample_dict,
                                              mode='rb'))

    else:
        #  Generate new city and building parameter sample dicts

        # Get empty result dicts
        (dict_city_sample, dict_build_samples) = \
            gen_empty_res_dicts(city=city,
                                nb_samples=nb_samples)

        #  Calc. number of uncertain parameters
        nb_par = calc_nb_unc_par(city=city)

        #  Sampling on city district level (add to dict_city_sample and
        #  dict_build_samples
        do_lhc_city_sampling(city=city, nb_samples=nb_samples, nb_par=nb_par,
                             dict_city_sample=dict_city_sample,
                             dict_build_samples=dict_build_samples,
                             load_sh_mc_res=load_sh_mc_res,
                             path_mc_res_folder=path_mc_res_folder,
                             dem_unc=dem_unc)

    if use_profile_pool:
        if gen_use_prof_method == 0:

            #  Calculate share of profiles
            share_profiles = nb_profiles / nb_samples

            #  If profile pool should be generated:
            dict_profiles = \
                gen_profile_pool(city=city, nb_samples=nb_samples,
                                 dict_build_samples=dict_build_samples,
                                 share_profiles=share_profiles)

        elif gen_use_prof_method == 1:
            #  Load profiles from pickle file
            dict_profiles = pickle.load(open(path_profile_dict, mode='rb'))
    else:
        dict_profiles = None

    return (dict_city_sample, dict_build_samples, dict_profiles)


if __name__ == '__main__':

    #  User inputs
    #  ###################################################################
    #  City pickle file name
    city_name = 'aachen_kronenberg_6_w_esys.pkl'

    #  Number of samples
    nb_samples = 100

    load_sh_mc_res = False
    #  If load_sh_mc_res is True, tries to load monte-carlo space heating
    #  uncertainty run results for each building from given folder
    #  If load_sh_mc_res is False, uses default value to sample sh demand
    #  uncertainty per building

    dem_unc = True
    # dem_unc : bool, optional
    #     Defines, if thermal, el. and dhw demand are assumed to be uncertain
    #     (default: True). If True, samples demands. If False, uses reference
    #     demands.

    save_dicts = True

    #  Defines, if profile pool should be used
    use_profile_pool = True

    gen_use_prof_method = 1
    #  Options:
    #  0: Generate new profiles during runtime
    #  1: Load pre-generated profile sample dictionary

    #  Defines number of profiles per building, which should be generated
    nb_profiles = 10

    #  Defines name of profile dict, if profiles should be loaded
    #  (gen_use_prof_method == 1)
    el_profile_dict = 'kronen_6_resc_2_dict_profile_20_samples.pkl'

    path_this = os.path.dirname(os.path.abspath(__file__))
    path_mc = os.path.dirname(path_this)
    path_city = os.path.join(path_mc, 'input', city_name)

    #  Path to el_profile_dict (gen_use_prof_method == 1)
    path_profile_dict = os.path.join(path_mc,
                                     'input',
                                     'mc_el_profile_pool',
                                     el_profile_dict)

    #  Path to space heating mc results (load_sh_mc_res is True)
    path_mc_res_folder = os.path.join(path_mc, 'input', 'sh_mc_run')

    #  Output path definitions
    path_save_res = os.path.join(path_mc, 'output')
    city_pkl_name = 'aachen_kronenberg_6_w_esys_dict_city_samples.pkl'
    building_pkl_name = 'aachen_kronenberg_6_w_esys_dict_build_samples.pkl'
    profiles_pkl_name = 'aachen_kronenberg_6_w_esys_dict_profile_samples.pkl'
    #  ###################################################################

    city = pickle.load(open(path_city, mode='rb'))

    (dict_city_sample, dict_build_samples, dict_profiles) = \
        run_overall_lhc_sampling(city=city, nb_samples=nb_samples,
                                 load_sh_mc_res=load_sh_mc_res,
                                 path_mc_res_folder=path_mc_res_folder,
                                 use_profile_pool=use_profile_pool,
                                 gen_use_prof_method=gen_use_prof_method,
                                 path_profile_dict=path_profile_dict,
                                 nb_profiles=nb_profiles,
                                 dem_unc=dem_unc)

    #  Save sample dicts
    if save_dicts:
        if not os.path.exists(path_save_res):
            os.mkdir(path_save_res)
        path_save_city_sample = os.path.join(path_save_res,
                                             city_pkl_name)
        path_save_build_sample = os.path.join(path_save_res,
                                              building_pkl_name)
        path_save_build_profiles = os.path.join(path_save_res,
                                                profiles_pkl_name)

        pickle.dump(dict_city_sample, open(path_save_city_sample, mode='wb'))
        pickle.dump(dict_build_samples,
                    open(path_save_build_sample, mode='wb'))

        print('Saved dict_city_sample to ' + str(path_save_city_sample))
        print('Saved dict_build_samples to ' + str(path_save_build_sample))

        if dict_profiles is not None:
            pickle.dump(dict_profiles,
                        open(path_save_build_profiles, mode='wb'))
            print('Saved dict_profiles to ' + str(path_save_build_profiles))

    # ###################################################################

    build_id = 1001

    plt.plot(sorted(dict_build_samples[build_id]['chp_inv']))
    plt.title('Sorted samples for chp investment factor of building '
              + str(build_id))
    plt.xlabel('Number of values')
    plt.ylabel('Change factor relative to default investment')
    plt.tight_layout()
    plt.show()
    plt.close()

    plt.hist(dict_build_samples[build_id]['chp_inv'], bins='auto')
    plt.title('Histogram of uncertainty in CHP captial cost of building '
              + str(build_id))
    plt.xlabel('Change factor relative to default investment')
    plt.ylabel('Number of values')
    plt.tight_layout()
    plt.show()
    plt.close()

    sh_dem_ref = city.nodes[build_id]['entity'].get_annual_space_heat_demand()
    plt.hist(dict_build_samples[build_id]['sh_dem'], bins=nb_samples,
             label='Log. sh. dist.')
    plt.axvline(sh_dem_ref, label='Ref. sh. dem.', c='red', linestyle='--')
    plt.title('Histogram of space heating samples of building '
              + str(build_id))
    plt.xlabel('Space heating demand in kWh/a')
    plt.ylabel('Number of values')
    plt.legend()
    plt.tight_layout()
    plt.show()
    plt.close()

    #  Loop over keys in dict_city_sample and identify zero arrays
    for key in dict_city_sample.keys():
        if key != 'list_sum_on':
            if sum(dict_city_sample[key]) == 0:
                msg = 'dict_city_sample value ' + str(key) + ' holds zero ' \
                                                             'array!'
                warnings.warn(msg)

    # Loop over keys in dict_build_samples and identify zero arrays
    for id in dict_build_samples.keys():
        sample_dict = dict_build_samples[id]
        for key in sample_dict.keys():
            if key not in ['app_nb_occ', 'app_el_dem',
                           'app_dhw_dem']:
                if sum(sample_dict[key]) == 0:
                    msg = str('sample_dict in building '
                              + str(id) + ' with value '
                              + str(key) + ' holds zero array!')
                    warnings.warn(msg)
            else:
                for i in range(len(city.nodes[id]['entity'].apartments)):
                    if sum(sample_dict[key][i, :]) == 0:
                        msg = str('sample_dict in building '
                                  + str(id) + ', apartment'
                                  + str(i) + ' with value '
                                  + str(key) + ' holds zero array!')
                        warnings.warn(msg)
