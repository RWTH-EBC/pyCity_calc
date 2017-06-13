#!/usr/bin/env python
# coding=utf-8
"""
Script to analyze pickle city file
"""

import os
import pickle
import numpy as np

import pycity_calc.toolbox.analyze.analyze_city_pickle_file as ancit
import ebc_ues_plot.line_plots as uesline


if __name__ == '__main__':
    #  City pickle filename
    city_file = 'aachen_forsterlinde_5.pkl'

    print('Analyse city file: ', city_file)

    #  Path to load file
    this_path = os.path.dirname(os.path.abspath(__file__))
    pycity_path = os.path.dirname(os.path.dirname(this_path))

    file_path = os.path.join(this_path, 'input', city_file)
    # file_path = os.path.join(pycity_path, 'cities', 'scripts',
    #                          'output_complex_city_gen', city_file)

    #  Load city object from pickle file
    city = ancit.load_pickled_city_file(file_path)

    (sh_power_curve, el_power_curve, dhw_power_curve) = \
        ancit.get_power_curves(city, print_out=False)

    timestep = city.environment.timer.timeDiscretization


    idx_start = int(0)
    idx_stop = int(idx_start + 3600 * 24 * 365 / timestep)

    #  Generate time array
    time_array = np.arange(start=0, stop=365 * 24 * 3600, step=timestep) / (
    3600 * 24)

    # idx_start = int(3 * 24 * 3600 / timestep)
    # idx_stop = int(idx_start + 3600 * 24 * 1 / timestep)

    # time_array = time_array[idx_start:idx_stop]
    # q_heat = q_heat[idx_start:idx_stop] / 1000
    # temp_in = temp_in[idx_start:idx_stop]
    # temp_out = temp_out[idx_start:idx_stop]

    plot_data = uesline.PlottingData()

    plot_data.add_data_entry(time_array, sh_power_curve/1000)
    plot_data.add_data_entry(time_array, el_power_curve/1000)
    plot_data.add_data_entry(time_array, dhw_power_curve/1000)

    #  Plot into one figure or use subplots?
    plot_sub = False  # Plot into multiple subplots with same x-axis

    #  Use legend labels
    use_labels = True

    this_path = os.path.dirname(os.path.abspath(__file__))
    output_filename = 'city_mod_res_forsterlinde'
    output_path = os.path.join(this_path, 'output', output_filename)

    #  English infos
    title_engl = ''  # Add 'u' in front of string to define it as unicode
    # (e.g. when using non-ascii characters)
    xlab_engl = 'Time in days'
    ylab_engl = u'Power in kW'
    #  ylab only used if plot_sub == False

    #  If use_labels == True --> Define labels!
    label_1_engl = u'Space heating'  # u'Space heating\npower in kW'
    label_2_engl = u'Electrical load' #  in kW'
    label_3_engl = u'Hot water' #\npower in kW'
    label_4_engl = ''
    label_5_engl = ''
    label_6_engl = ''
    #  If  plot_sub == True, define ylabs as labels!

    #  German infos
    title_dt = ''  # Add 'u' in front of string to define it as unicode
    # (e.g. when using non-ascii characters)
    xlab_dt = 'Zeit in Tagen'
    ylab_dt = u'Leistung in kW'
    #  ylab only used if plot_sub == False

    #  If use_labels == True --> Define labels!
    label_1_dt = u'Raumwärme'  #u'Heizleistung\nin kW'
    label_2_dt = 'Elektrische Last'  #  u'Elektrische\nLast in kW'
    label_3_dt = 'Warmwasser'  #  u'Warmwasser-\nleistung in kW'
    label_4_dt = ''
    label_5_dt = ''
    label_6_dt = ''
    #  If  plot_sub == True, define ylabs as labels!

    #  Fontsize
    fontsize = 12
    #  dpi size
    dpi = 1000
    #  Linewidth
    linewidth = 1

    #  Additionally save as tikz for latex?
    save_tikz = True

    #  Plot figures?
    show_plot = False

    #  Use tight layout?
    use_tight = True

    #  Use black and white or regular colors?
    # (only relevant for generate_line_plots)
    bw_usage = True  # True - greyscale; False - regular colors

    #  Legend within box? False: Outside of box
    legend_pos_within = True

    #  If legend_pos_within == False, define outside position
    put_leg = 'below'  # 'right' or 'below'

    #  Adjust figure size to default (None), 'a4' or 'a4_half', 'a5'
    fig_adjust = 'a5'  # 'a4_half', 'a5'
    #  fig_adjust = None  # default

    #  Set base point to (0 / 0)
    set_zero_point = True

    set_x_limits = True
    xmin = 0
    xmax = 365
    set_y_limits = False
    ymin = 0
    ymax = 1.2

    #  Rotate x labels?
    rotate_x_labels = False

    #  Copy Python code into output folder?
    copy_py = True

    #  Copy input file into output folder?
    copy_input = False

    #  Save data array as pickle file?
    save_data_array = True

    #  #------------------------------------------------------------

    if use_labels:
        list_labels_engl = [label_1_engl, label_2_engl, label_3_engl,
                            label_4_engl, label_5_engl, label_6_engl]
        list_labels_dt = [label_1_dt, label_2_dt, label_3_dt,
                          label_4_dt, label_5_dt, label_6_dt]
    else:
        list_labels_engl = None
        list_labels_dt = None

    # dataset: numpy
    # array
    # ND - Numpy
    # array(rows: define
    # paramters;
    # columns: define
    # values)

    uesline.plot_multi_language_multi_color(plot_data=plot_data,
                                            plot_sub=plot_sub,
                                            output_path=output_path,
                                            output_filename=output_filename,
                                            show_plot=show_plot,
                                            use_tight=use_tight,
                                            title_engl=title_engl,
                                            xlab_engl=xlab_engl,
                                            ylab_engl=ylab_engl,
                                            list_labels_engl=list_labels_engl,
                                            title_dt=title_dt, xlab_dt=xlab_dt,
                                            ylab_dt=ylab_dt,
                                            list_labels_dt=list_labels_dt,
                                            fontsize=fontsize,
                                            fig_adjust=fig_adjust,
                                            legend_pos_within=legend_pos_within,
                                            put_leg=put_leg, dpi=dpi,
                                            linewidth=linewidth,
                                            set_zero_point=set_zero_point,
                                            set_x_limits=set_x_limits,
                                            xmin=xmin, xmax=xmax,
                                            set_y_limits=set_y_limits,
                                            ymin=ymin, ymax=ymax,
                                            use_grid=False,
                                            copy_py=copy_py,
                                            copy_input=copy_input,
                                            input_path=None,
                                            save_data_array=save_data_array,
                                            save_tikz=save_tikz,
                                            rotate_x_labels=rotate_x_labels)