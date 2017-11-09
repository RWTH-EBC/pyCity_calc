#!/usr/bin/env python
# coding=utf-8

import os
import math
import copy
import pickle
import numpy as np
import warnings
import shutil
import matplotlib.pyplot as plt

import ebc_ues_plot.hist_plot as ebchist
import ebc_ues_plot.line_plots as ebcline

import pycity_calc.toolbox.others.analyze_mc_sh_load_and_energy as mcan

def make_boxplot(list_sh, ref_val, fontsize=12, dpi=300, with_outliners=True):

    plt.rc('font', family='Arial', size=fontsize)

    fig = plt.figure()

    ax = fig.gca()

    pb = ax.boxplot(list_sh, showfliers=with_outliners)

    plt.ylabel('Net space heating\ndemand in MWh')

    # ax.set_xticklabels('')

    ax.plot([0.93, 1.07], [ref_val, ref_val],
            label='Reference', color='#1058B0', linestyle='--',
            linewidth=1)

    for median in pb['medians']:
        median.set(color='#E53027')

    for flier in pb['fliers']:
        flier.set(marker='.', markersize=1)

    fig.autofmt_xdate()

    plt.tight_layout()

    #  Generate legend
    import matplotlib.lines as mlines
    #  Generate proxy arist for legend
    median_proxy = mlines.Line2D([], [], color='#E53027', label='Median')
    ref_proxy = mlines.Line2D([], [], color='#1058B0', label='Reference'
                              , linestyle='--')

    box_factor = 0.1
    for ax in fig.axes:
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * box_factor,
                         box.width, box.height * (1 - box_factor)])

    # Put a legend below current axis
    lgd = ax.legend(handles=[median_proxy, ref_proxy],
                    loc='upper center', bbox_to_anchor=(-1.8, -0.4), ncol=2)

    plt.legend(handles=[median_proxy, ref_proxy], loc='best')

    plt.show()

    # gen_path(output_path)
    #
    # #  Generate file names for different formats
    # file_pdf = output_filename + '.pdf'
    # file_eps = output_filename + '.eps'
    # file_png = output_filename + '.png'
    # file_tiff = output_filename + '.tiff'
    # file_tikz = output_filename + '.tikz'
    #
    # #  Generate saving pathes
    # path_pdf = os.path.join(output_path, file_pdf)
    # path_eps = os.path.join(output_path, file_eps)
    # path_png = os.path.join(output_path, file_png)
    # path_tiff = os.path.join(output_path, file_tiff)
    # path_tikz = os.path.join(output_path, file_tikz)
    #
    # #  Save figure in different formats
    # plt.savefig(path_pdf, format='pdf')
    # plt.savefig(path_eps, format='eps')
    # plt.savefig(path_png, format='png')
    # # plt.savefig(path_tiff, format='tiff', dpi=dpi)
    # tikz_save(path_tikz, figureheight='\\figureheight',
    #           figurewidth='\\figurewidth')

    # plt.show()
    plt.close()

def make_hist(list_sh, output_path, output_folder_name, sim_val):
    #  English infos
    title_engl = None  # Add 'u' in front of string to define it as unicode
    # (e.g. when using non-ascii characters)
    xlab_engl = 'Normalized space heating net\nenergy demand in MWh'
    ylab_engl = 'Number of demand values'

    #  German infos
    title_dt = None  # Add 'u' in front of string to define it as unicode
    # (e.g. when using non-ascii characters)
    xlab_dt = u'Normierter Raumwärmebedarf\n in MWh'
    ylab_dt = 'Anzahl Energiebedarfswerte'
    #  ylab only used if plot_sub == False

    #  Fontsize
    fontsize = 10
    #  dpi size
    dpi = 300
    #  Linewidth
    linewidth = 1

    #  Plot figures?
    show_plot = False

    #  Use tight layout?
    use_tight = True

    #  Adjust figure size to default (None), 'a4' or 'a4_half', 'a5'
    fig_adjust = 'a4_half'  # 'a4_half', 'a5'
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

    dict_v_lines = {'Reference\nsimulation': sim_val}

    #  #--------------------------------------------------------------

    ebchist.plot_multi_lang_multi_color_hist(list_data=list_sh,
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

    plt.close()


if __name__ == '__main__':
    ref_val = 1004  # MWh
    sim_val = 990  # MWh
    sim_val /= ref_val

    this_path = os.path.dirname(os.path.abspath(__file__))

    #  Generate results object
    mc_res = mcan.McCityRes()

    city_res_name = 'wm_bb_city_gen_jana_data_enrich_mc_city_samples_1000.pkl'

    load_path = os.path.join(this_path, 'input', city_res_name)

    mc_res = pickle.load(open(load_path, mode='rb'))

    (list_sh, list_el, list_dhw, list_sh_curves) = mc_res

    for i in range(len(list_sh)):
        #  Convert kWh to MWh
        list_sh[i] /= (1000 * ref_val)

    output_path = os.path.join(this_path, 'output', 'mc_sh_res')
    output_folder_name = 'mc_sh_res'

    make_hist(list_sh=list_sh, output_path=output_path,
              output_folder_name=output_folder_name,
              sim_val=sim_val)

    print('Norm. sim. ref value: ', sim_val)
    print()

    mean = np.mean(list_sh)
    print('Norm. mean: ', mean)
    print()

    median = np.median(list_sh)
    print('Norm. median: ', median)
    print()

    std = np.std(list_sh)
    print('Norm. std: ', std)
    print()

    minv = min(list_sh)
    print('Norm. min.: ', minv)
    print()

    maxv = max(list_sh)
    print('Norm. max.: ', maxv)
    print()



    # make_boxplot(list_sh=list_sh, ref_val=ref_val)
