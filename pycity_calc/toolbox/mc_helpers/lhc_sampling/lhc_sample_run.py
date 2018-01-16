#!/usr/bin/env python
# coding=utf-8
"""

"""
from __future__ import division

import os
import pickle
import numpy as np
import pyDOE
import matplotlib.pylab as plt
import scipy.stats.distributions as distr
from scipy.stats import nakagami
from scipy import stats


#  TODO: Load sh res. values per building of sh mc uncertainty run
#  TODO: Generate pool of el. load profiles per apartment
#  TODO: Radiation uncertainty

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
    # summer
    dict_city_sample['list_sum_on'] = np.zeros(nb_samples)

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
        dict_samples['bat_lifetime'] = np.zeros(nb_samples)
        dict_samples['bat_maintain'] = np.zeros(nb_samples)
        dict_samples['bat_inv'] = np.zeros(nb_samples)
        #  Uncertain boiler params
        dict_samples['eta_boi'] = np.zeros(nb_samples)
        dict_samples['boi_lifetime'] = np.zeros(nb_samples)
        dict_samples['boi_maintain'] = np.zeros(nb_samples)
        dict_samples['boi_inv'] = np.zeros(nb_samples)
        #  Uncertain chp params
        dict_samples['omega_chp'] = np.zeros(nb_samples)
        dict_samples['chp_lifetime'] = np.zeros(nb_samples)
        dict_samples['chp_maintain'] = np.zeros(nb_samples)
        dict_samples['chp_inv'] = np.zeros(nb_samples)
        #  Uncertain HP params
        dict_samples['qual_grade_aw'] = np.zeros(nb_samples)
        dict_samples['qual_grade_ww'] = np.zeros(nb_samples)
        dict_samples['t_sink'] = np.zeros(nb_samples)
        dict_samples['hp_lifetime'] = np.zeros(nb_samples)
        dict_samples['hp_maintain'] = np.zeros(nb_samples)
        dict_samples['hp_inv'] = np.zeros(nb_samples)
        #  Uncertain EH params
        dict_samples['eh_lifetime'] = np.zeros(nb_samples)
        dict_samples['eh_maintain'] = np.zeros(nb_samples)
        dict_samples['eh_inv'] = np.zeros(nb_samples)
        #  Uncertain tes params
        dict_samples['k_loss'] = np.zeros(nb_samples)
        dict_samples['tes_lifetime'] = np.zeros(nb_samples)
        dict_samples['tes_maintain'] = np.zeros(nb_samples)
        dict_samples['tes_inv'] = np.zeros(nb_samples)
        #  Uncertain PV params
        dict_samples['eta'] = np.zeros(nb_samples)  # Also including inv. loss
        dict_samples['beta'] = np.zeros(nb_samples)
        dict_samples['gamma'] = np.zeros(nb_samples)
        dict_samples['pv_lifetime'] = np.zeros(nb_samples)
        dict_samples['pv_maintain'] = np.zeros(nb_samples)
        dict_samples['pv_inv'] = np.zeros(nb_samples)

        #  Get nb of apartments
        nb_app = len(city.nodes[n]['entity'].apartments)

        #  Generate apartment uncertain parameters
        #  Rows (parameter array per apartment)
        dict_samples['app_nb_occ'] = np.zeros((nb_app, nb_samples))
        dict_samples['app_el_dem_person'] = np.zeros((nb_app, nb_samples))
        dict_samples['app_dhw_dem_person'] = np.zeros((nb_app, nb_samples))

        #  Save parameter dict to main building dict
        dict_build_samples[n] = dict_samples

    return (dict_city_sample, dict_build_samples)


def calc_nb_unc_par(city, nb_city_unc_par=14,
                    nb_build_unc_par=34, nb_app_unc_par=3):
    """
    Calculate total number of uncertain parameters required for LHC design

    Parameters
    ----------
    city : object
        City object of pyCity_calc
    nb_city_unc_par : int, optional
        Number of uncertain parameters on city level (default: 14)
    nb_build_unc_par : int, optional
        Number of uncertain parameters on building level (default: 34)
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

    nb_par = nb_city_unc_par + nb_city_unc_par * nb_build \
             + nb_app_unc_par * nb_app

    return nb_par


def do_lhc_city_sampling(city, nb_par, nb_samples, dict_city_sample,
                         dict_build_samples):
    """

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

    Returns
    -------

    """

    #  Perform lhc design call
    design = pyDOE.lhs(n=nb_par, samples=nb_samples, criterion='center')

    # print(design)


def run_overall_lhc_sampling(city, nb_samples, nb_city_unc_par=14,
                             nb_build_unc_par=34, nb_app_unc_par=3):
    """

    Parameters
    ----------
    city : object
        City object of pyCity_calc
    nb_samples : int
        Number of samples
    nb_city_unc_par : int, optional
        Number of uncertain parameters on city level (default: 14)
    nb_build_unc_par : int, optional
        Number of uncertain parameters on building level (default: 34)
    nb_app_unc_par : int, optional
        Number of uncertain parameters on apartment level (default: 3)

    Returns
    -------

    """
    #  Get empty result dicts
    (dict_city_sample, dict_build_samples) = \
        gen_empty_res_dicts(city=city,
                            nb_samples=nb_samples)

    #  Calc. number of uncertain parameters
    nb_par = calc_nb_unc_par(city=city, nb_city_unc_par=nb_city_unc_par,
                             nb_build_unc_par=nb_build_unc_par,
                             nb_app_unc_par=nb_app_unc_par)

    #  Sampling on city district level
    do_lhc_city_sampling(city=city, nb_samples=nb_samples, nb_par=nb_par,
                         dict_city_sample=dict_city_sample,
                         dict_build_samples=dict_build_samples)

    #  Loop over buildings

    #  Loop over apartments


if __name__ == '__main__':
    city_name = 'wm_res_east_7_w_street_sh_resc_wm.pkl'

    nb_samples = 100

    path_this = os.path.dirname(os.path.abspath(__file__))
    path_mc = os.path.dirname(path_this)
    path_city = os.path.join(path_mc, 'input', city_name)

    city = pickle.load(open(path_city, mode='rb'))

    run_overall_lhc_sampling(city=city, nb_samples=nb_samples)
