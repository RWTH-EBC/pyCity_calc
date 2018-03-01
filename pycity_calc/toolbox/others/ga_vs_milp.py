#!/usr/bin/env python
# coding=utf-8
"""

"""
from __future__ import division

import os
import pickle
import warnings
import numpy as np
import matplotlib.pyplot as plt

try:
    from matplotlib2tikz import save as tikz_save
except:
    msg = 'Could not import matplotlib2tikz'
    warnings.warn(msg)

import pycity_resilience.ga.opt_ga  # Necessary to load pickle files!
import pycity_resilience.ga.postprocess.analyze_generation_dev as gadev
from deap import base, creator, tools, algorithms

if __name__ == '__main__':
    #  Define pathes
    #  ####################################################################
    this_path = os.path.dirname(os.path.abspath(__file__))
    path_in_folder = os.path.join(this_path, 'input')

    # name_ga_res_folder = 'ga_run_ref_run_with_rescaling'
    # name_ga_res_folder = 'ga_run_aachen_kronenberg_6_peak_resc_2'
    name_ga_res_folder = 'ga_run_kronen_6_resc_2_ref_with_chp_pen_meanshift'
    path_ga_results = os.path.join(path_in_folder, name_ga_res_folder)

    path_save_gen_dev = os.path.join(this_path, 'output', 'ga_gen_dev')

    #  Path to save figures to
    path_save = os.path.join(this_path, 'output', 'pareto_front')
    output_filename = 'pareto_front'
    dpi = 100

    out_name = name_ga_res_folder + '_dict_par_front_sol.pkl'
    path_save_par = os.path.join(this_path, 'output', 'ga_opt', out_name)

    # #  Complete analysis call
    # gadev.analyze_pareto_sol(path_results_folder=path_ga_results)

    #  Process GA results
    #  #############################################################

    #  Load GA results
    dict_gen = gadev.load_res(dir=path_ga_results)

    # #  Plot development of generations
    # gadev.print_gen_sol_dev(dict_gen=dict_gen, path_save=path_save_gen_dev)

    # #  Extract final population
    # (final_pop, list_ann, list_co2) = gadev.get_final_pop(dict_gen=dict_gen)

    file_par_front = name_ga_res_folder + '_pareto_front.pkl'
    path_save_par = os.path.join(this_path, 'output', file_par_front)

    try:
        dict_pareto_sol = pickle.load(open(path_save_par, mode='rb'))
    except:
        msg = 'Could not load file from ' + str(path_save_par)
        warnings.warn(msg)
        #  Extract list of pareto optimal results
        list_inds_pareto = gadev.get_pareto_front(dict_gen=dict_gen,
                                                  size_used=None,  # Nb. Gen.
                                                  nb_ind_used=400)  # Nb. ind.
        #  Parse list of pareto solutions to dict (nb. as keys to re-identify
        #  each solution
        dict_pareto_sol = {}
        for i in range(len(list_inds_pareto)):
            dict_pareto_sol[int(i + 1)] = list_inds_pareto[i]

        #  Save pareto-frontier solution
        pickle.dump(dict_pareto_sol, open(path_save_par, mode='wb'))

    #  Write down obj. of MILP runs (Min. Cost --> Min. CO2)
    #  #############################################################
    list_mip_cost = [67550, 68873, 70808,
                     # 72441, # Min. CO2 with cost constraint of 72441
                     73201, 74233, 75915
                     # , 143544
                     ]

    list_mip_co2 = [134143, 129035, 124125,
                    # 119261, # Min. CO2 with cost constraint of 72441
                    119214, 114304, 109393
                    # ,104479
                    ]

    #  Extract pareto solutions (blue) - print suboptimal solutions in grey
    #  MILP red

    fig = plt.figure()

    max_key = len(dict_gen) - 1
    array_allowed_keys = np.arange(max_key, 0, -10)
    list_allowed_keys = array_allowed_keys.tolist()

    for key in sorted(list(dict_gen.keys()), reverse=True):
        #  Get population
        pop = dict_gen[key]

        list_ann = []
        list_co2 = []

        #  Loop over individuals
        for ind in pop:
            #  Get annuity
            ann = ind.fitness.values[0]
            co2 = ind.fitness.values[1]

            if isinstance(ann, float) and isinstance(co2, float):
                if ann < 10 ** 90:  # Smaller than penalty function
                    list_ann.append(ann)
                if co2 < 10 ** 90:  # Smaller than penalty function
                    list_co2.append(co2)

        #  Convert from Euro to kilo-Euro and kilograms to tons CO2
        for i in range(len(list_ann)):
            list_ann[i] /= 1000
            list_co2[i] /= 1000

        if key == 1:
            plt.plot(list_ann, list_co2, marker='o', linestyle='',
                     markersize=3,
                     c='orange', label='GA (start solutions)')
        if key == 2:
            plt.plot(list_ann, list_co2, marker='o', linestyle='',
                     markersize=3,
                     c='gray', label='GA (dominated solutions)')
        elif key in list_allowed_keys:
            plt.plot(list_ann, list_co2, marker='o', linestyle='',
                     markersize=3, c='gray')

    for i in range(len(dict_pareto_sol)):
        sol = dict_pareto_sol[i + 1]
        cost = sol.fitness.values[0] / 1000
        co2 = sol.fitness.values[1] / 1000

        if i == 0:
            plt.plot([cost],
                     [co2], linestyle='',
                     marker='o', markersize=3, c='#E53027',
                     label='GA (non-dominated solutions)')
        else:
            plt.plot([cost],
                     [co2], c='#E53027', linestyle='',
                     marker='o', markersize=3)

    for i in range(len(list_mip_cost)):
        cost = list_mip_cost[i] / 1000
        co2 = list_mip_co2[i] / 1000
        if i == 0:
            plt.plot([cost],
                     [co2], linestyle='',
                     marker='o', markersize=3, c='#1058B0',
                     label='MILP (optimal solutions)')
        else:
            plt.plot([cost],
                     [co2], linestyle='',
                     marker='o', markersize=3, c='#1058B0')

    ax = fig.gca()

    #  Add annotations with arrows
    ax.annotate('BOI+PV', xy=(64, 132), xytext=(62, 125),
                arrowprops=dict(  # facecolor='black',
                    arrowstyle='->'
                    # ,shrink=0.01
                ))

    ax.annotate('1-2 CHPs+PV\nor 1 HP+PV', xy=(68, 126), xytext=(62, 115),
                arrowprops=dict(  # facecolor='black',
                    arrowstyle='->'
                    # ,shrink=0.01
                ))

    ax.annotate('1-2 CHPs and\n1 HPs+PV', xy=(72, 121), xytext=(62, 105),
                arrowprops=dict(  # facecolor='black',
                    arrowstyle='->'
                    # ,shrink=0.01
                ))

    ax.annotate('1 LHN (3 nodes\n+1 CHP)+PV', xy=(76, 111), xytext=(62, 95),
                arrowprops=dict(  # facecolor='black',
                    arrowstyle='->'
                    # ,shrink=0.01
                ))

    ax.annotate('2 LHN (3 nodes\n+1 CHP)+PV', xy=(81, 106), xytext=(74, 95),
                arrowprops=dict(  # facecolor='black',
                    arrowstyle='->'
                    # ,shrink=0.01
                ))

    plt.xlabel('Total annualized cost in thousand-Euro/a')
    plt.ylabel('CO2 emissions in t/a')
    plt.legend()
    plt.tight_layout()

    if path_save is not None:

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
