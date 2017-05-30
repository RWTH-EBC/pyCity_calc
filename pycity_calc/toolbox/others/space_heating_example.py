#!/usr/bin/env python
# coding=utf-8
"""
Example script how to calculate thermal space heating load with TEASER and
VDI 6007 calculation core.

Steps:
- Generate environment
- Generate occuancy object
- Generate el. load object
- Generate apartment and add profile objects
- Generate building and add apartment
- Run VDI simulation with building
"""

import os
import numpy as np

import pycity.classes.Weather as Weather
import pycity.classes.demand.Occupancy as occ
import pycity.classes.demand.ElectricalDemand as eldem
import pycity.classes.demand.Apartment as Apartment

import pycity_calc.buildings.building as build_ex
import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.environment as env
import pycity_calc.environments.market as mark
import pycity_calc.environments.timer as time

import pycity_calc.toolbox.teaser_usage.teaser_use as tus
import pycity_calc.toolbox.user.user_air_exchange as usair
import ebc_ues_plot.line_plots as uesline


try:
    from teaser.project import Project
    import teaser.logic.simulation.VDI_6007.low_order_VDI as low_order_vdi
    import teaser.logic.simulation.VDI_6007.weather as vdiweather
except:
    raise ImportError('Could not import TEASER package. Please check your '
                      'installation. TEASER can be found at: '
                      'https://github.com/RWTH-EBC/TEASER. '
                      'Installation is possible via pip.')


def run_example_vdi_6007():
    #  Define simulation settings
    build_year = 1962  # Year of construction
    mod_year = 2000  # Year of retrofit

    el_demand = 3000  # Annual, el. demand in kWh

    t_set_heat = 20  # Heating set temperature in degree Celsius
    t_set_night = 16  # Night set back temperature in degree Celsius
    t_set_cool = 70  # Cooling set temperature in degree Celsius

    air_vent_mode = 2
    #  int; Define mode for air ventilation rate generation
    #  0 : Use constant value (vent_factor in 1/h)
    #  1 : Use deterministic, temperature-dependent profile
    #  2 : Use stochastic, user-dependent profile
    #  False: Use static ventilation rate value

    vent_factor = 0.5  # Constant. ventilation rate
    #  (only used, if air_vent_mode == 0)

    heat_lim_val = None  # Heater limit in Watt

    #  #  Create PyCity_Calc environment
    #  #####################################################################

    #  Create extended environment of pycity_calc
    year = 2010
    timestep = 3600  # Timestep in seconds
    location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop
    altitude = 55  # Altitude of Bottrop

    #  Generate timer object
    timer = time.TimerExtended(timestep=timestep, year=year)

    #  Generate weather object
    weather = Weather.Weather(timer, useTRY=True, location=location,
                              altitude=altitude)

    temp_out = weather.tAmbient[:]

    #  Generate market object
    market = mark.Market()

    #  Generate co2 emissions object
    co2em = co2.Emissions(year=year)

    #  Generate environment
    environment = env.EnvironmentExtended(timer, weather, prices=market,
                                          location=location, co2em=co2em)

    #  #  Create occupancy profile
    #  #####################################################################

    num_occ = 3

    print('Calculate occupancy.\n')
    #  Generate occupancy profile
    occupancy_obj = occ.Occupancy(environment, number_occupants=num_occ)

    print('Finished occupancy calculation.\n')

    #  #  Generate ventilation rate (window opening etc.)
    #  #####################################################################

    #  Get infiltration rate
    if mod_year is None:
        year = build_year
    else:
        year = mod_year
    inf_rate = usair.get_inf_rate(year)

    if air_vent_mode == 0:  # Use constant value
        array_vent = None  # If array_vent is None, use default values

    elif air_vent_mode == 1:  # Use deterministic, temp-dependent profile
        array_vent = \
            usair.gen_det_air_ex_rate_temp_dependend(occ_profile=
                                                     occupancy_obj.occupancy,
                                                     temp_profile=
                                                     environment.weather.tAmbient,
                                                     inf_rate=inf_rate)


    elif air_vent_mode == 2:
        #  Get ventilation rate (in 1/h, related to building air volume)
        array_vent = \
            usair.gen_user_air_ex_rate(occ_profile=occupancy_obj.occupancy,
                                       temp_profile=environment.weather.tAmbient,
                                       b_type='res',
                                       inf_rate=inf_rate)

    # #  Create electrical load
    #  #####################################################################

    print('Calculate el. load.\n')

    # el_dem_stochastic = \
    #     eldem.ElectricalDemand(environment,
    #                            method=2,
    #                            annualDemand=el_demand,
    #                            do_normalization=True,
    #                            total_nb_occupants=num_occ,
    #                            randomizeAppliances=True,
    #                            lightConfiguration=10,
    #                            occupancy=occupancy_obj.occupancy[:])

    # #  Instead of stochastic profile, use SLP to be faster with calculation
    el_dem_stochastic = eldem.ElectricalDemand(environment,
                                               method=1,
                                               # Standard load profile
                                               profileType="H0",
                                               annualDemand=el_demand)

    print('Finished el. load calculation.\n')

    #  #  Create apartment and building object
    #  #####################################################################

    #  Create apartment
    apartment = Apartment.Apartment(environment)

    #  Add demands to apartment
    apartment.addMultipleEntities([el_dem_stochastic, occupancy_obj])

    #  Create extended building object
    extended_building = build_ex.BuildingExtended(environment,
                                                  build_year=build_year,
                                                  mod_year=mod_year,
                                                  build_type=0,
                                                  roof_usabl_pv_area=30,
                                                  net_floor_area=200,
                                                  height_of_floors=2.8,
                                                  nb_of_floors=2,
                                                  neighbour_buildings=0,
                                                  residential_layout=0,
                                                  attic=1, cellar=1,
                                                  construction_type='heavy',
                                                  dormer=1)
    #  BuildingExtended holds further, optional input parameters,
    #  such as ground_area, nb_of_floors etc.

    #  Add apartment to extended building
    extended_building.addEntity(entity=apartment)

    #  Calculate thermal space heating load and add instance to building
    #  #####################################################################
    (temp_in, q_heat_cool, q_in_wall, q_out_wall) = \
        tus.calc_th_load_build_vdi6007_ex_build(exbuild=extended_building,
                                                add_th_load=True,
                                                vent_factor=vent_factor,
                                                array_vent_rate=array_vent,
                                                t_set_heat=t_set_heat,
                                                t_set_cool=t_set_cool,
                                                t_night=t_set_night,
                                                heat_lim_val=heat_lim_val)

    #  Results
    #  #####################################################################
    q_heat = np.zeros(len(q_heat_cool))
    q_cool = np.zeros(len(q_heat_cool))
    for i in range(len(q_heat_cool)):
        if q_heat_cool[i] > 0:
            q_heat[i] = q_heat_cool[i]
        elif q_heat_cool[i] < 0:
            q_cool[i] = q_heat_cool[i]

    print('Sum of heating energy in kWh:')
    print(sum(q_heat) / 1000)

    print('Sum of cooling energy in kWh:')
    print(-sum(q_cool) / 1000)

    # import matplotlib.pyplot as plt
    #
    # fig = plt.figure()
    # fig.add_subplot(311)
    # plt.plot(environment.weather.tAmbient)
    # plt.ylabel('Outdoor air\ntemperature in\ndegree Celsius')
    # fig.add_subplot(312)
    # plt.plot(temp_in)
    # plt.ylabel('Indoor air\ntemperature in\ndegree Celsius')
    # fig.add_subplot(313)
    # plt.plot(q_heat_cool / 1000)
    # plt.ylabel('Heating/cooling\npower (+/-)\nin kW')
    # plt.xlabel('Time in hours')
    # plt.show()




    idx_start = int(0)
    idx_stop = int(idx_start + 3600 * 24 * 365 / timestep)

    #  Generate time array
    time_array = np.arange(start=0, stop=365 * 24 * 3600, step=timestep) / (3600 * 24)

    # idx_start = int(3 * 24 * 3600 / timestep)
    # idx_stop = int(idx_start + 3600 * 24 * 1 / timestep)

    time_array = time_array[idx_start:idx_stop]
    q_heat = q_heat[idx_start:idx_stop] / 1000
    temp_in = temp_in[idx_start:idx_stop]
    temp_out = temp_out[idx_start:idx_stop]

    plot_data = uesline.PlottingData()

    plot_data.add_data_entry(time_array, temp_out)
    plot_data.add_data_entry(time_array, q_heat)
    plot_data.add_data_entry(time_array, temp_in)

    #  Plot into one figure or use subplots?
    plot_sub = True  # Plot into multiple subplots with same x-axis

    #  Use legend labels
    use_labels = True

    this_path = os.path.dirname(os.path.abspath(__file__))
    output_filename = 'sh_example_w_2_temp'
    output_path = os.path.join(this_path, 'output', output_filename)

    #  English infos
    title_engl = ''  # Add 'u' in front of string to define it as unicode
    # (e.g. when using non-ascii characters)
    xlab_engl = 'Time in days'
    ylab_engl = u'Thermal power in kW'
    #  ylab only used if plot_sub == False

    #  If use_labels == True --> Define labels!
    label_1_engl = u'Outdoor\ntempera-\nture in °C'
    label_2_engl = 'Thermal\npower\nin kW'
    label_3_engl = u'Indoor\ntempera-\nture in °C'
    label_4_engl = ''
    label_5_engl = ''
    label_6_engl = ''
    #  If  plot_sub == True, define ylabs as labels!

    #  German infos
    title_dt = ''  # Add 'u' in front of string to define it as unicode
    # (e.g. when using non-ascii characters)
    xlab_dt = 'Zeit in Tagen'
    ylab_dt = u'Thermi-\nsche Lei-\nstung in kW'
    #  ylab only used if plot_sub == False

    #  If use_labels == True --> Define labels!
    label_1_dt = u'Außen-\ntemperatur\nin °C'
    label_2_dt = u'Thermische\nLeistung\nin kW'
    label_3_dt = u'Innenraum-\ntemperatur\nin °C'
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
    set_zero_point = False

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
    run_example_vdi_6007()
