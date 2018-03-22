#!/usr/bin/env python
# coding=utf-8
"""

"""
from __future__ import division

import os
import pickle
import warnings
import numpy as np
import scipy.stats as stats

import matplotlib.pyplot as plt

try:
    from matplotlib2tikz import save as tikz_save
except:
    msg = 'Could not import matplotlib2tikz'
    warnings.warn(msg)

def ident_whisker(array_val, use_low_bound, bound):
    """
    Identify whisker

    Parameters
    ----------
    array_val : np.array
    use_low_bound : bool
    bound : float

    Returns
    -------
    whisker : float
    """

    #  Generate start solutions
    if use_low_bound:
        whisker = bound + 10000000000000000000000000000000000000
    else:
        whisker = bound - 10000000000000000000000000000000000000

    for i in range(len(array_val)):
        curr_val = array_val[i]

        if use_low_bound:
            if curr_val > bound:
                if curr_val < whisker:
                    whisker = curr_val
        else:
            if curr_val < bound:
                if curr_val > whisker:
                    whisker = curr_val

    return whisker


def main():
    this_path = os.path.dirname(os.path.abspath(__file__))

    name_folder_in = '4b_eco_mc_run'

    path_folder_in = os.path.join(this_path, 'input', name_folder_in)

    dict_name = 'mc_run_results_dict'

    list_pathes_res = []
    #  Search for mc_run_results_dict.pkl results dict in each subdirectory
    for root, dirs, files in os.walk(path_folder_in):
        for file in files:
            if dict_name in file:
                list_pathes_res.append(str(os.path.join(root, file)))

    print('Found result dicts in dirs:')
    for dir in list_pathes_res:
        print(dir)
    print()

    dict_res = {}
    dict_setups = {}
    list_ids = []

    for dir in list_pathes_res:
        #  Extract ind number
        dirpath = os.path.dirname(dir)
        ind_nb = dirpath.split('_')[len(dirpath.split('_')) - 1]
        print('Extracted solution nb:')
        print(ind_nb)
        print()

        res = pickle.load(open(dir, mode='rb'))
        dict_res[int(ind_nb)] = res
        list_ids.append(int(ind_nb))

        path_setup = os.path.join(dirpath, 'mc_run_setup_dict.pkl')
        setup = pickle.load(open(path_setup, mode='rb'))
        dict_setups[int(ind_nb)] = setup

    #  Sort keys in list_ids
    list_ids.sort()

    print('Postprocess')
    #  Postprocess (erase entries of failed runs)
    for i in range(len(list_ids)):
        id = list_ids[i]
        print('Id: ', id)

        setup = dict_setups[id]
        res = dict_res[id]

        list_idx_failed = setup['idx_failed_runs']

        nb_failed_runs = len(list_idx_failed)
        len_org = len(res['annuity'])
        len_test_array = len(res['annuity']) - nb_failed_runs

        array_cost = np.zeros(len_test_array)
        array_co2 = np.zeros(len_test_array)
        array_sh = np.zeros(len_test_array)
        array_el = np.zeros(len_test_array)
        array_dhw = np.zeros(len_test_array)

        array_idx_zeros = np.where(res['annuity'] == 0)[0]
        print(array_idx_zeros)

        i = 0
        for j in range(len_org):
            if j not in list_idx_failed:
                array_cost[i] = res['annuity'][j]
                array_co2[i] = res['co2'][j]
                array_sh[i] = res['sh_dem'][j]
                array_el[i] = res['el_dem'][j]
                array_dhw[i] = res['dhw_dem'][j]
                i += 1

        #  Save new arrays to results object
        res['annuity'] = array_cost
        res['co2'] = array_co2
        res['sh_dem'] = array_sh
        res['el_dem'] = array_el
        res['dhw_dem'] = array_dhw

        print('Nb. failed runs: ', nb_failed_runs)
        print('New array length: ', len(array_cost))
        print()

    fig = plt.figure()

    list_colors = ['#E53027', '#1058B0', '#F47328', '#5F379B',
                   '#9B231E', '#BE4198', '#008746']

    for i in range(len(list_ids)):
        id = list_ids[i]

        print('Process id: ', id)
        res = dict_res[id]

        array_cost = res['annuity'] / 1000
        array_co2 = res['co2'] / 1000

        array_sh = res['sh_dem']
        array_el = res['el_dem']
        array_dhw = res['dhw_dem']

        array_net_energy = array_sh + array_el + array_dhw

        # count_zeros = 0
        # for j in range(len(array_el)):
        #     if array_el[j] == 0:
        #         count_zeros += 1
        #
        # print(count_zeros)
        # print('pause')
        # input()

        # for j in range(len(array_cost)):
        #     if array_net_energy[i] > 0:
        #         array_cost[i] = array_cost[i] / array_net_energy[i]
        #         array_co2[i] = array_co2[i] / array_net_energy[i]

        median_cost = np.median(array_cost)
        median_co2 = np.median(array_co2)
        median_sh = np.median(array_sh)
        median_el = np.median(array_el)
        median_dhw = np.median(array_dhw)

        print('Median cost ', median_cost)
        print('Av. cost: ', sum(array_cost) / len(array_cost))
        print('Median co2: ', median_co2)
        print('Av. CO2: ', sum(array_co2) / len(array_co2))
        print('Median SH ', median_sh)
        print('Median El.: ', median_el)
        print('Median DHW: ', median_dhw)
        print('Av. DHW: ', sum(array_dhw) / len(array_dhw))

        iqr_cost = stats.iqr(array_cost)
        iqr_co2 = stats.iqr(array_co2)

        riqr_cost = iqr_cost / median_cost
        riqr_co2 = iqr_co2 / median_co2

        print('RIQR (cost): ', riqr_cost)
        print('RIQR (CO2): ', riqr_co2)

        q_25_cost = np.percentile(array_cost, q=25)
        q_25_co2 = np.percentile(array_co2, q=25)
        q_75_cost = np.percentile(array_cost, q=75)
        q_75_co2 = np.percentile(array_co2, q=75)

        # plt.plot([median_cost], [median_co2],
        #          linestyle='',
        #          marker='o',
        #          # markersize=3,
        #          c='#E53027'
        #          # ,label='Selected solutions'
        #          )

        er_1_cost = median_cost - q_25_cost
        er_2_cost = q_75_cost - median_cost
        er_1_co2 = median_co2 - q_25_co2
        er_2_co2 = q_75_co2 - median_co2

        up_bound_cost = q_75_cost + 1.5 * iqr_cost
        low_bound_cost = q_25_cost - 1.5 * iqr_cost
        up_bound_co2 = q_75_co2 + 1.5 * iqr_co2
        low_bound_co2 = q_25_co2 - 1.5 * iqr_co2

        whisker_low_cost = ident_whisker(array_val=array_cost,
                                         use_low_bound=True,
                                         bound=low_bound_cost)
        whisker_high_cost = ident_whisker(array_val=array_cost,
                                         use_low_bound=False,
                                         bound=up_bound_cost)
        whisker_low_co2 = ident_whisker(array_val=array_co2,
                                         use_low_bound=True,
                                         bound=low_bound_co2)
        whisker_high_co2 = ident_whisker(array_val=array_co2,
                                          use_low_bound=False,
                                          bound=up_bound_co2)

        er_low_b_cost = median_cost - whisker_low_cost
        er_up_b_cost = whisker_high_cost - median_cost
        er_low_b_co2 = median_co2 - whisker_low_co2
        er_up_b_co2 = whisker_high_co2 - median_co2

        color = list_colors[i]

        plt.errorbar(x=median_cost,
                     y=median_co2,
                     xerr=[[er_1_cost], [er_2_cost]],
                     yerr=[[er_1_co2], [er_2_co2]],
                     elinewidth=8,
                     markeredgewidth=8,
                     alpha=0.5,
                     color=color,
                     fmt='o')

        plt.errorbar(x=median_cost,
                     y=median_co2,
                     xerr=[[er_low_b_cost], [er_up_b_cost]],
                     yerr=[[er_low_b_co2], [er_up_b_co2]],
                     capsize=5,
                     color=color)

        #  Plot all outliers manually
        for j in range(len(array_cost)):
            curr_cost = array_cost[j]
            if (curr_cost > up_bound_cost or
                    curr_cost < low_bound_cost - 1.5 * iqr_cost):
                plt.plot([curr_cost], [median_co2],
                         linestyle='',
                         marker='o',
                         markersize=2,
                         c=color
                         )
            curr_co2 = array_co2[i]
            if (curr_co2 > up_bound_co2 or
                    curr_co2 < low_bound_co2 - 1.5 * iqr_co2) \
                    and curr_co2 > 0:
                plt.plot([curr_co2], [median_co2],
                         linestyle='',
                         marker='o',
                         markersize=2,
                         c=color
                         )


        print()

    list_cost = [68369,
                 71194,
                 75005,
                 78085,
                 80534,
                 88221
                 ]

    list_co2 = [129979,
                126105,
                116708,
                107570,
                101366,
                91737
                ]

    # for i in range(len(list_cost)):
    #     cost = list_cost[i] / 1000
    #     co2 = list_co2[i] / 1000
    #     # if i == 0:
    #     #     plt.plot([cost],
    #     #              [co2], linestyle='',
    #     #              marker='o',
    #     #              # markersize=3,
    #     #              c='#E53027',
    #     #              label='Selected solutions')
    #     # else:
    #     plt.plot([cost],
    #              [co2], linestyle='',
    #              marker='o',
    #              markersize=5,
    #              c=list_colors[i])

    plt.xlabel('Total annualized cost in thousand-Euro/a')
    plt.ylabel('CO2 emissions in t/a')

    # plt.xlim([0, 100])
    # plt.ylim([0, 160])

    this_path = os.path.dirname(os.path.abspath(__file__))
    path_save = os.path.join(this_path, 'output', '2d_hist_eco_unc')

    output_filename = '2d_hist_eco_unc'

    dpi = 100

    if not os.path.exists(path_save):
        os.makedirs(path_save)

    #  Generate file names for different formats
    file_pdf = output_filename + '.pdf'
    file_eps = output_filename + '.eps'
    file_png = output_filename + '.png'
    file_tikz = output_filename + '.tikz'
    file_svg = output_filename + '.svg'

    #  Generate saving pathes
    path_pdf = os.path.join(path_save, file_pdf)
    path_eps = os.path.join(path_save, file_eps)
    path_png = os.path.join(path_save, file_png)
    path_tikz = os.path.join(path_save, file_tikz)
    path_svg = os.path.join(path_save, file_svg)

    #  Save figure in different formats
    plt.savefig(path_pdf, format='pdf', dpi=dpi)
    plt.savefig(path_eps, format='eps', dpi=dpi)
    plt.savefig(path_png, format='png', dpi=dpi)
    plt.savefig(path_svg, format='svg', dpi=dpi)

    try:
        tikz_save(path_tikz, figureheight='\\figureheight',
                  figurewidth='\\figurewidth')
    except:
        msg = 'tikz_save command failed. Could not save figure to tikz.'
        warnings.warn(msg)

    plt.show()
    plt.close()

if __name__ == '__main__':
    main()