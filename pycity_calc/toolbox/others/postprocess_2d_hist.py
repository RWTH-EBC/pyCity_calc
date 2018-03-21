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

    list_ids.sort()

    fig = plt.figure()

    list_colors = ['#E53027', '#1058B0', '#F47328', '#5F379B',
                   '#9B231E', '#BE4198', '#008746']

    for i in range(len(list_ids)):
        id = list_ids[i]

        print('Process id: ', id)
        res = dict_res[id]

        array_cost = res['annuity'] / 1000
        array_co2 = res['co2'] / 1000

        median_cost = np.median(array_cost)
        median_co2 = np.median(array_co2)

        print('Median cost ', median_cost)
        print('Median co2: ', median_co2)

        iqr_cost = stats.iqr(array_cost)
        iqr_co2 = stats.iqr(array_co2)

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

        er_low_b_cost = median_cost - low_bound_cost
        er_up_b_cost = up_bound_cost - median_cost
        er_low_b_co2 = median_co2 - low_bound_co2
        er_up_b_co2 = up_bound_co2 - median_co2

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

        #  Plot all whiskers manually
        for j in range(len(array_cost)):
            curr_cost = array_cost[j]
            if (curr_cost > up_bound_cost or
                    curr_cost < low_bound_cost - 1.5 * iqr_cost) \
                    and curr_cost > 0:
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