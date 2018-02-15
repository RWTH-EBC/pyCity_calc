#!/usr/bin/env python
# coding=utf-8
"""
Script to evaluate the space heating demand uncertainty for different
levels of knowledge regarding building retrofit

building_level_mc_results

max_uncertainty - aachen_kronenberg_mod_new_1_single_b_new_dhw_1002.pkl
span_1980_to_2000 - aachen_kronenberg_mod_new_1_single_b_new_dhw_1002.pkl
fixed_to_1990 - aachen_kronenberg_mod_new_1_single_b_new_dhw_10021990.pkl

city_level_mc_results

max_uncertainty - aachen_kronenberg_mod_new_1_mc_city_samples_10000.pkl
span_1980_to_2000 - aachen_kronenberg_mod_new_1_red_mc_city_samples_10000_red_year_span.pkl
fixed_to_1990 - aachen_kronenberg_mod_new_1_red_mc_city_samples_10000_fixed_year.pkl

Each res.pkl file is of type tuple (with 4 elements)
(list_sh, list_el, list_dhw, list_sh_curves)
"""
from __future__ import division

import os
import pickle
import matplotlib.pyplot as plt



if __name__ == '__main__':

    this_path = os.path.dirname(os.path.abspath(__file__))
    path_in_folder = os.path.join(this_path,
                                  'input',
                                  '2e_analysis_sh_mc_red_unc_year')

    dict_res = {}

    #  Load results on building level
    #  #####################################################
    #  Building level
    #  ##################
    #  Building level - High uncertainty
    res_name = 'aachen_kronenberg_mod_new_1_single_b_new_dhw_1002.pkl'
    path_results = os.path.join(path_in_folder,
                                'building_level_mc_results',
                                'max_uncertainty',
                                res_name)
    res_build_high_unc = pickle.load(open(path_results, mode='rb'))
    list_build_high_unc = res_build_high_unc[0]
    dict_res['sh_b_high'] = list_build_high_unc

    #  Building level - Medium uncertainty
    res_name = 'aachen_kronenberg_mod_new_1_single_b_new_dhw_1002.pkl'
    path_results = os.path.join(path_in_folder,
                                'building_level_mc_results',
                                'span_1980_to_2000',
                                res_name)
    res_build_med_unc = pickle.load(open(path_results, mode='rb'))
    list_build_med_unc = res_build_med_unc[0]
    dict_res['sh_b_med'] = list_build_med_unc

    #  Building level - Small uncertainty
    res_name = 'aachen_kronenberg_mod_new_1_single_b_new_dhw_10021990.pkl'
    path_results = os.path.join(path_in_folder,
                                'building_level_mc_results',
                                'fixed_to_1990',
                                res_name)
    res_build_low_unc = pickle.load(open(path_results, mode='rb'))
    list_build_low_unc = res_build_low_unc[0]
    dict_res['sh_b_low'] = list_build_low_unc

    #  City level
    #  ################
    #  City level - High uncertainty
    res_name = 'aachen_kronenberg_mod_new_1_mc_city_samples_10000.pkl'
    path_results = os.path.join(path_in_folder,
                                'city_level_mc_results',
                                'max_uncertainty',
                                res_name)
    res_city_high_unc = pickle.load(open(path_results, mode='rb'))
    list_city_high_unc = res_city_high_unc[0]
    dict_res['sh_c_high'] = list_city_high_unc

    #  Building level - Medium uncertainty
    res_name = 'aachen_kronenberg_mod_new_1_red_mc_city_samples_10000_red_year_span.pkl'
    path_results = os.path.join(path_in_folder,
                                'city_level_mc_results',
                                'timespan_1980_2000',
                                res_name)
    res_city_med_unc = pickle.load(open(path_results, mode='rb'))
    list_city_med_unc = res_city_med_unc[0]
    dict_res['sh_c_med'] = list_city_med_unc

    #  Building level - Small uncertainty
    res_name = 'aachen_kronenberg_mod_new_1_red_mc_city_samples_10000_fixed_year.pkl'
    path_results = os.path.join(path_in_folder,
                                'city_level_mc_results',
                                'fixed_1990',
                                res_name)
    res_city_low_unc = pickle.load(open(path_results, mode='rb'))
    list_city_low_unc = res_city_low_unc[0]
    dict_res['sh_c_low'] = list_city_low_unc



