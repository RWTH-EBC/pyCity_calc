#!/usr/bin/env python
# coding=utf-8
"""

"""
from __future__ import division

import os
import pickle
import numpy as np

import ebc_ues_plot.hist_plot as ebchist

def main():
    #  Get path of this file
    this_path = os.path.dirname(os.path.abspath(__file__))

    #  Load mc results data
    filename_res = 'aachen_kronenberg_6_single_b_1003.pkl'

    #  Design heat load for building
    heat_load_design = 70  # in kW

    path_res = os.path.join(this_path,
                            'input',
                            'kronen_6_b_1003_mc_run_results',
                            filename_res)

    dict_res = pickle.load(open(path_res, mode='rb'))
    #  Dict holding (list_sh, list_sh_curves, list_el, list_dhw)

    array_max_sh_powers = np.zeros(len(dict_res[0]))

    #  Extract max power values
    for i in range(len(array_max_sh_powers)):
        #  Get max power value for given space heating power array in dict_res
        array_max_sh_powers[i] = max(dict_res[1][i]) / 1000 # in kW

    nb_beyond_design_hl = 0
    #  Extract number of runs with higher space heating power requirements
    #  than design heat load
    for power in array_max_sh_powers:
        if power > heat_load_design:
            nb_beyond_design_hl += 1

    print('Nb. of runs with power requirements beyond design load: ')
    print(nb_beyond_design_hl)
    print()

    print('Share at overall number of runs: ',
          nb_beyond_design_hl/len(array_max_sh_powers))
    print()


    #  User inputs
    #  #--------------------------------------------------------------
    output_folder_name = 'kronen_6_b_1003_mc_run_results'

    output_path = os.path.join(this_path, 'output', 'hist_plots',
                               output_folder_name)

    if not os.path.dirname(output_path):
        os.makedirs(output_path)

    #  English infos
    title_engl = None  # Add 'u' in front of string to define it as unicode
    # (e.g. when using non-ascii characters)
    xlab_engl = 'Maximum space heating power in kW'
    ylab_engl = 'Number of power values'

    #  German infos
    title_dt = None  # Add 'u' in front of string to define it as unicode
    # (e.g. when using non-ascii characters)
    xlab_dt = 'Maximale Raumwärmelast in kW'
    ylab_dt = 'Anzahl Heizlastwerte'
    #  ylab only used if plot_sub == False

    #  Fontsize
    fontsize = 12
    #  dpi size
    dpi = 200
    #  Linewidth
    linewidth = 1

    #  Plot figures?
    show_plot = False

    #  Use tight layout?
    use_tight = True

    #  Adjust figure size to default (None), 'a4' or 'a4_half', 'a5'
    fig_adjust = 'a4'  # 'a4_half', 'a5'
    #  fig_adjust = None  # default

    #  Font type
    # use_font = 'tex'  # Latex font
    use_font = 'arial'  # Arial font
    #  Pre-defines used font in matplotlib rc parameters
    #  Options:
    #  - 'tex' : Use Latex fonts in plots
    #  - 'arial' : Use arial fonts

    #  Copy Python code into output folder?
    copy_py = True

    #  Additionally save as tikz for latex?
    save_tikz = True

    #  Save data array as pickle file?
    save_data_array = True

    #  Rotate x labels?
    rotate_x_labels = False

    plot_edgecolor = True

    plot_mean = True

    plot_std = True

    dict_v_lines = {'Design heat load': heat_load_design}

    #  #--------------------------------------------------------------

    ebchist.plot_multi_lang_multi_color_hist(
        list_data=array_max_sh_powers,
        output_path=output_path,
        output_filename=output_folder_name,
        show_plot=show_plot,
        use_tight=use_tight,
        title_engl=title_engl,
        xlab_engl=xlab_engl,
        ylab_engl=ylab_engl,
        title_dt=title_dt, xlab_dt=xlab_dt,
        ylab_dt=ylab_dt,
        fontsize=fontsize,
        fig_adjust=fig_adjust,
        dpi=dpi, copy_py=copy_py,
        save_data_array=save_data_array,
        save_tikz=save_tikz,
        rotate_x_labels=rotate_x_labels,
        use_font=use_font,
        plot_edgecolor=plot_edgecolor,
        plot_mean=plot_mean,
        plot_std=plot_std,
        dict_v_lines=dict_v_lines)


if __name__ == '__main__':
    main()