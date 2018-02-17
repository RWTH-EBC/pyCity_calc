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
import warnings
import matplotlib.pyplot as plt
import numpy as np
import scipy
import scipy.stats

try:
    from matplotlib2tikz import save as tikz_save
except:
    msg = 'Could not import matplotlib2tikz'
    warnings.warn(msg)

if __name__ == '__main__':

    this_path = os.path.dirname(os.path.abspath(__file__))
    path_in_folder = os.path.join(this_path,
                                  'input',
                                  '2e_analysis_sh_mc_red_unc_year')

    path_output = os.path.join(this_path, 'output', 'sh_mc_unc_diff_years')
    output_filename = 'sh_box_diff_years'

    dict_res = {}
    list_b_data = []
    list_c_data = []

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
    list_b_data.append(list_build_high_unc)

    #  Building level - Medium uncertainty
    res_name = 'aachen_kronenberg_mod_new_1_single_b_new_dhw_1002.pkl'
    path_results = os.path.join(path_in_folder,
                                'building_level_mc_results',
                                'span_1980_to_2000',
                                res_name)
    res_build_med_unc = pickle.load(open(path_results, mode='rb'))
    list_build_med_unc = res_build_med_unc[0]
    dict_res['sh_b_med'] = list_build_med_unc
    list_b_data.append(list_build_med_unc)

    #  Building level - Small uncertainty
    res_name = 'aachen_kronenberg_mod_new_1_single_b_new_dhw_10021990.pkl'
    path_results = os.path.join(path_in_folder,
                                'building_level_mc_results',
                                'fixed_to_1990',
                                res_name)
    res_build_low_unc = pickle.load(open(path_results, mode='rb'))
    list_build_low_unc = res_build_low_unc[0]
    dict_res['sh_b_low'] = list_build_low_unc
    list_b_data.append(list_build_low_unc)

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
    list_c_data.append(list_city_high_unc)

    #  Building level - Medium uncertainty
    res_name = 'aachen_kronenberg_mod_new_1_red_mc_city_samples_10000_red_year_span.pkl'
    path_results = os.path.join(path_in_folder,
                                'city_level_mc_results',
                                'timespan_1980_2000',
                                res_name)
    res_city_med_unc = pickle.load(open(path_results, mode='rb'))
    list_city_med_unc = res_city_med_unc[0]
    dict_res['sh_c_med'] = list_city_med_unc
    list_c_data.append(list_city_med_unc)

    #  Building level - Small uncertainty
    res_name = 'aachen_kronenberg_mod_new_1_red_mc_city_samples_10000_fixed_year.pkl'
    path_results = os.path.join(path_in_folder,
                                'city_level_mc_results',
                                'fixed_1990',
                                res_name)
    res_city_low_unc = pickle.load(open(path_results, mode='rb'))
    list_city_low_unc = res_city_low_unc[0]
    dict_res['sh_c_low'] = list_city_low_unc
    list_c_data.append(list_city_low_unc)

    #  Convert kWh to MWh
    for i in range(len(list_b_data)):
        for t in range(len(list_b_data[0])):
            list_b_data[i][t] /= 1000
            list_c_data[i][t] /= 1000

    for i in range(len(list_b_data)):
        list_dat = list_b_data[i]

        median = np.median(list_dat)
        iqr = scipy.stats.iqr(list_dat)
        riqr = iqr / median

        if i == 0:
            print('Building high uncertainty')
        elif i == 1:
            print('Building med uncertainty')
        elif i == 2:
            print('Building low uncertainty')
        print('Median: ')
        print(median)
        print('RIQR: ')
        print(riqr)
        print()

    for i in range(len(list_c_data)):
        list_dat = list_c_data[i]

        median = np.median(list_dat)
        iqr = scipy.stats.iqr(list_dat)
        riqr = iqr / median

        if i == 0:
            print('City high uncertainty')
        elif i == 1:
            print('City med uncertainty')
        elif i == 2:
            print('City low uncertainty')
        print('Median: ')
        print(median)
        print('RIQR: ')
        print(riqr)
        print()

    list_xticks = ['Building - No\nretrofit knowledge',
                   'Building - Minor\nretrofit knowledge',
                   'Building - High\nretrofit knowledge',
                   'City - No retrofit\n knowledge',
                   'City - Minor retrofit\n knowledge',
                   'City - High retrofit\n knowledge',
                   ]

    fig = plt.figure()

    fig.add_subplot(121)

    ax = fig.gca()

    pb = ax.boxplot(list_b_data[0:3], showfliers=True
                    , widths=(0.8, 0.8, 0.8)
                    )
    plt.ylabel('Net space heating\ndemand in MWh')

    ax.set_xticklabels(list_xticks[0:3])
    plt.xticks(rotation=90)

    for median in pb['medians']:
        median.set(color='#E53027')

    for flier in pb['fliers']:
        flier.set(marker='.', markersize=1)

    fig.add_subplot(122)

    ax = fig.gca()

    pb = ax.boxplot(list_c_data[0:3], showfliers=True
                    , widths=(0.8, 0.8, 0.8)
                    )

    ax.set_xticklabels(list_xticks[3:6])
    plt.xticks(rotation=90)

    for median in pb['medians']:
        median.set(color='#E53027')

    for flier in pb['fliers']:
        flier.set(marker='.', markersize=1)

    # fig.autofmt_xdate()
    plt.tight_layout()

    if not os.path.exists(path_output):
        os.makedirs(path_output)

    #  Generate file names for different formats
    file_pdf = output_filename + '.pdf'
    file_eps = output_filename + '.eps'
    file_png = output_filename + '.png'
    file_tikz = output_filename + '.tikz'

    #  Generate saving pathes
    path_pdf = os.path.join(path_output, file_pdf)
    path_eps = os.path.join(path_output, file_eps)
    path_png = os.path.join(path_output, file_png)
    path_tikz = os.path.join(path_output, file_tikz)

    #  Save figure in different formats
    plt.savefig(path_pdf, format='pdf')
    plt.savefig(path_eps, format='eps')
    plt.savefig(path_png, format='png')

    try:
        tikz_save(path_tikz, figureheight='\\figureheight',
                  figurewidth='\\figurewidth')
    except:
        msg = 'Could not use tikz_save command to save figure in tikz format'
        warnings.warn(msg)

    plt.show()
    plt.close()