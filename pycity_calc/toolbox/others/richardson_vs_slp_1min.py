#!/usr/bin/env python
# coding=utf-8
"""
Script to generate 24 hour el. SlP and stochastic Richardson profile
"""

import os
import numpy as np
import matplotlib.pylab as plt
from scipy.interpolate import spline
from scipy.interpolate import interp1d

import ebc_ues_plot.line_plots as uesline

import pycity_base.classes.demand.ElectricalDemand as elec
import pycity_base.classes.demand.Occupancy as occ
import pycity_base.classes.Weather as weath
import pycity_base.functions.changeResolution as chres

import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.environment as env
import pycity_calc.environments.market as mark
import pycity_calc.environments.timer as time


def gen_1_min_el_profiles():
    """
    Generate electrical load profiles with 60 seconds resolution

    Returns
    -------

    """

    #  Create extended environment of pycity_calc
    year = 2010
    timestep = 60  # Timestep in seconds
    location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop
    altitude = 55  # Altitude of Bottrop

    #  Generate timer object
    timer = time.TimerExtended(timestep=timestep, year=year)

    timer_600 = time.TimerExtended(timestep=600, year=year)

    #  Generate weather object
    weather = weath.Weather(timer, useTRY=True, location=location,
                              altitude=altitude)

    #  Generate market object
    market = mark.Market()

    #  Generate co2 emissions object
    co2em = co2.Emissions(year=year)

    #  Generate environment
    environment = env.EnvironmentExtended(timer, weather, prices=market,
                                          location=location, co2em=co2em)

    el_slp_obj = elec.ElectricalDemand(environment=environment,
                                    method=1,  # Standard load profile
                                    profileType="H0",
                                    annualDemand=1000)

    slp_load = el_slp_obj.loadcurve[:]

    occupancy = occ.Occupancy(environment=environment, number_occupants=3)

    el_stoch_obj = elec.ElectricalDemand(environment,
                                             method=2,
                                             annualDemand=1000,
                                             total_nb_occupants=3,
                                             randomizeAppliances=True,
                                             lightConfiguration=10,
                                             occupancy=occupancy.occupancy,
                                             do_normalization=True,
                                             prev_heat_dev=True)

    print(len(el_stoch_obj.loadcurve))

    stoch_load = el_stoch_obj.loadcurve[:]

    idx_start = int(0)
    idx_stop = int(idx_start + 3600 * 24 / timestep)

    #  Generate time array
    time_array = np.arange(start=0, stop=365 * 24 * 3600, step=timestep) / 3600

    time_array = time_array[idx_start:idx_stop]
    slp_load = slp_load[idx_start:idx_stop]
    stoch_load = stoch_load[idx_start:idx_stop]

    # plt.plot(time_array, slp_load)
    # plt.plot(time_array, stoch_load)
    # plt.show()
    # plt.close()

    x_smooth = np.linspace(time_array.min(), time_array.max(), 144/2)
    # x_smooth = np.linspace(time_array.min(), time_array.max(),
    #                        int((idx_stop-idx_start)/60))
    y_smooth = spline(time_array, slp_load, x_smooth)
    # from scipy import interpolate
    # y_smooth = interpolate.splev(time_array, slp_load, der=0)

    plt.plot(x_smooth, y_smooth)
    plt.plot(time_array, stoch_load)
    plt.show()
    plt.close()

    print('Len. time_array: ', len(time_array))
    print('Len. smooth time array: ', len(x_smooth))


    plot_data = uesline.PlottingData()

    plot_data.add_data_entry(x_smooth, y_smooth)
    plot_data.add_data_entry(time_array, stoch_load)


    #  Plot into one figure or use subplots?
    plot_sub = False  # Plot into single figure
    # plot_sub = True  # Plot into multiple subplots with same x-axis

    #  Use legend labels
    use_labels = True

    this_path = os.path.dirname(os.path.abspath(__file__))
    output_filename = 'slp_vs_rich_24_h'
    output_path = os.path.join(this_path, 'output', output_filename)

    #  English infos
    title_engl = ''  # Add 'u' in front of string to define it as unicode
    # (e.g. when using non-ascii characters)
    xlab_engl = 'Time in hours'
    ylab_engl = u'Electrical\npower in Watt'
    #  ylab only used if plot_sub == False

    #  If use_labels == True --> Define labels!
    label_1_engl = 'SLP'
    label_2_engl = 'Stochastic\nprofile'
    label_3_engl = ''
    label_4_engl = ''
    label_5_engl = ''
    label_6_engl = ''
    #  If  plot_sub == True, define ylabs as labels!

    #  German infos
    title_dt = ''  # Add 'u' in front of string to define it as unicode
    # (e.g. when using non-ascii characters)
    xlab_dt = 'Zeit in Stunden'
    ylab_dt = u'Elektrische\nLeistung in Watt'
    #  ylab only used if plot_sub == False

    #  If use_labels == True --> Define labels!
    label_1_dt = 'SLP'
    label_2_dt = 'Stochastisches\nLastprofil'
    label_3_dt = ''
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
    xmax = 24
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
    save_data_array = False

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

    uesline.plot_multi_language_multi_color(plot_data=plot_data, plot_sub=plot_sub,
                                            output_path=output_path,
                                            output_filename=output_filename,
                                            show_plot=show_plot,
                                            use_tight=use_tight, title_engl=title_engl,
                                    xlab_engl=xlab_engl,
                                    ylab_engl=ylab_engl,
                                            list_labels_engl=list_labels_engl,
                                    title_dt=title_dt, xlab_dt=xlab_dt,
                                    ylab_dt=ylab_dt,
                                            list_labels_dt=list_labels_dt,
                                    fontsize=fontsize,
                                    fig_adjust=fig_adjust,
                                            legend_pos_within=legend_pos_within,
                                    put_leg=put_leg, dpi=dpi, linewidth=linewidth,
                                    set_zero_point=set_zero_point,
                                            set_x_limits=set_x_limits,
                                    xmin=xmin, xmax=xmax,
                                            set_y_limits=set_y_limits,
                                    ymin=ymin, ymax=ymax,
                                            use_grid=False,
                                    copy_py=copy_py, copy_input=copy_input,
                                    input_path=None, save_data_array=save_data_array,
                                    save_tikz=save_tikz, rotate_x_labels=rotate_x_labels)



if __name__ == '__main__':

    gen_1_min_el_profiles()