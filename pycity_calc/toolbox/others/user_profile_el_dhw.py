#!/usr/bin/env python
# coding=utf-8
"""

"""

import os
import numpy as np
import matplotlib.pylab as plt
from scipy.interpolate import spline
from scipy.interpolate import interp1d

import ebc_ues_plot.line_plots as uesline

import pycity.classes.demand.ElectricalDemand as elec
import pycity.classes.demand.Occupancy as occ
import pycity.classes.demand.DomesticHotWater as DomesticHotWater
import pycity.classes.Weather as weath
import pycity.functions.changeResolution as chres

import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.environment as env
import pycity_calc.environments.market as mark
import pycity_calc.environments.timer as time


def gen_user_dep_profiles():
    """

    """

    #  Create extended environment of pycity_calc
    year = 2010
    timestep = 60  # Timestep in seconds
    location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop
    altitude = 55  # Altitude of Bottrop

    #  Generate timer object
    timer = time.TimerExtended(timestep=timestep, year=year)

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

    occupancy = occ.Occupancy(environment=environment, number_occupants=3)

    occ_profile = occupancy.occupancy[:]

    el_stoch_obj = elec.ElectricalDemand(environment,
                                             method=2,
                                             annualDemand=3500,
                                             total_nb_occupants=3,
                                             randomizeAppliances=True,
                                             lightConfiguration=10,
                                             occupancy=occupancy.occupancy,
                                             do_normalization=True,
                                             prev_heat_dev=True)

    stoch_load = el_stoch_obj.loadcurve[:]

    dhw_stochastical = DomesticHotWater.DomesticHotWater(environment,
                                                         tFlow=60,
                                                         thermal=True,
                                                         method=2,
                                                         supplyTemperature=25,
                                                         occupancy=occ_profile)

    dhw_power_curve = dhw_stochastical.get_power(currentValues=False,
                                                 returnTemperature=False)


    #  Change resolution of occupancy profile
    occ_profile = chres.changeResolution(values=occ_profile, newResolution=timestep,
                                         oldResolution=600)


    idx_start = int(0)
    idx_stop = int(idx_start + 3600 * 24 / timestep)

    #  Generate time array
    time_array = np.arange(start=0, stop=365 * 24 * 3600, step=timestep) / 3600

    time_array = time_array[idx_start:idx_stop]
    occ_profile = occ_profile[idx_start:idx_stop]
    stoch_load = stoch_load[idx_start:idx_stop] / 1000
    dhw_power_curve = dhw_power_curve[idx_start:idx_stop] / 1000



    plot_data = uesline.PlottingData()

    plot_data.add_data_entry(time_array, occ_profile)
    plot_data.add_data_entry(time_array, stoch_load)
    plot_data.add_data_entry(time_array, dhw_power_curve)


    #  Plot into one figure or use subplots?
    # plot_sub = False  # Plot into single figure
    plot_sub = True  # Plot into multiple subplots with same x-axis

    #  Use legend labels
    use_labels = True

    this_path = os.path.dirname(os.path.abspath(__file__))
    output_filename = 'user_profile_el_dhw'
    output_path = os.path.join(this_path, 'output', output_filename)

    #  English infos
    title_engl = ''  # Add 'u' in front of string to define it as unicode
    # (e.g. when using non-ascii characters)
    xlab_engl = 'Time in hours'
    ylab_engl = u''
    #  ylab only used if plot_sub == False

    #  If use_labels == True --> Define labels!
    label_1_engl = 'Active\noccu-\npants'
    label_2_engl = 'Electrical\npower\nin kW'
    label_3_engl = 'Hot water\npower\nin kW'
    label_4_engl = ''
    label_5_engl = ''
    label_6_engl = ''
    #  If  plot_sub == True, define ylabs as labels!

    #  German infos
    title_dt = ''  # Add 'u' in front of string to define it as unicode
    # (e.g. when using non-ascii characters)
    xlab_dt = 'Zeit in Stunden'
    ylab_dt = u''
    #  ylab only used if plot_sub == False

    #  If use_labels == True --> Define labels!
    label_1_dt = 'Aktive\nPersonen'
    label_2_dt = 'Elektrische\nLeistung\nin kW'
    label_3_dt = 'Warmwasser-\nLeistung\nin kW'
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

    gen_user_dep_profiles()