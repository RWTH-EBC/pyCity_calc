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
    name_ga_res_folder = 'ga_run_ref_run_with_rescaling_opt_limit'
    path_ga_results = os.path.join(path_in_folder, name_ga_res_folder)

    path_save_gen_dev = os.path.join(this_path, 'output', 'ga_gen_dev')

    #  Path to save figures to
    path_save = os.path.join(this_path, 'output', 'pareto_front')
    output_filename = 'pareto_front'
    dpi = 100

    #  Complete analysis call
    gadev.analyze_pareto_sol(path_results_folder=path_ga_results)

    #  Process GA results
    #  #############################################################

    #  Load GA results
    dict_gen = gadev.load_res(dir=path_ga_results)

    # #  Plot development of generations
    # gadev.print_gen_sol_dev(dict_gen=dict_gen, path_save=path_save_gen_dev)

    #  Extract final population
    (final_pop, list_ann, list_co2) = gadev.get_final_pop(dict_gen=dict_gen)

    #  Extract list of pareto optimal results
    list_inds_pareto = gadev.get_pareto_front_list(final_pop)

    #  Write down obj. of MILP runs (Min. Cost --> Min. CO2)
    list_mip_cost = [68698, 68873, 70808, 72441, 73201, 74233, 75915, 143544]
    list_mip_co2 = [133946, 129035, 124125, 119261, 119214, 114304, 109393,
                    104479]

    #  Extract pareto solutions (blue) - print suboptimal solutions in grey
    #  MILP red

    fig = plt.figure()

    for key in sorted(list(dict_gen.keys())):
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
                     c='gray', label='GA (dominated solutions)')
        else:
            plt.plot(list_ann, list_co2, marker='o', linestyle='',
                     markersize=3, c='gray')

    for i in range(len(list_inds_pareto)):
        sol = list_inds_pareto[i]
        cost = sol.fitness.values[0] / 1000
        co2 = sol.fitness.values[1] / 1000

        if i == 0:
            plt.plot([cost],
                     [co2], linestyle='',
                     marker='o', markersize=3, c='#E53027',
                     label='GA (pareto optimal)')
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
                     label='MILP (pareto optimal)')
        else:
            plt.plot([cost],
                     [co2], linestyle='',
                     marker='o', markersize=3, c='#1058B0')

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
