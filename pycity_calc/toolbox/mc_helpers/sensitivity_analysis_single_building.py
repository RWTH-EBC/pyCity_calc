#!/usr/bin/env python
# coding=utf-8
"""
Script to perform sensitivity analysis of thermal demand of single building
"""

import os
import copy
import numpy as np
import pickle
import matplotlib.pyplot as plt

import pycity_calc.toolbox.teaser_usage.teaser_use as tus
import pycity_calc.toolbox.mc_helpers.weather.gen_weather_set as uncweat


def do_single_building_sensitivity_analysis(building, fix_build_year=1990,
                                            fix_vent_rate=0.26,
                                            fix_set_temp=20):
    """
    Perform sensitivity analysis for single building

    Parameters
    ----------
    building : object
        Extended Building object of PyCity
    fix_build_year : int, optional
        Fixed building year / last year of construction
    fix_vent_rate : float, optional
        Fixed ventilation rate in 1/h for sensivity analysis
    fix_set_temp : float, optional
        Fixed set temperature for

    Returns
    -------

    """

    res_dict = {}

    exbuilding = copy.deepcopy(building)

    timestep = exbuilding.environment.timer.timeDiscretization

    #  Defines ranges for sensitivity analysis
    #  ###################################################################

    #  Influence of year of construction
    list_years = [1960, 1970, 1980, 1990, 2000, 2005, 2010, 2014]

    #  Influence of infiltration rates
    array_inf_rates = np.arange(start=0, stop=2.1, step=0.1)

    #  Influence of set temperatures
    array_temp = np.arange(start=15, stop=25+1, step=1)

    #  Influence of weather data

    #  Get weather dictionaries (cold, regular, warm weather)
    dict_weather = uncweat.get_warm_cold_regular_weather()
    list_weather = []
    array_weath_interpol = np.arange(start=-1, stop=1.25, step=0.25)
    # array_weath_interpol = np.arange(start=-1, stop=1, step=0.3)
    for interpol in array_weath_interpol:
        new_weather = \
            uncweat.calc_lin_ipl_weath(weath_dict=dict_weather,
                                       factor=interpol)
        list_weather.append(new_weather)

    #  Perform sensitivity analysis with different years of construction
    #  ##################################################################
    print('Start sensitivity analysis for construction years')

    dict_year_sh_net_demand = {}
    dict_year_sh_power_curves = {}

    for year in list_years:

        building = copy.deepcopy(exbuilding)

        if year < 1977:
            building.build_year = year
            building.mod_year = None
        else:
            building.mod_year = year
        print('build_year: ', building.build_year)
        print('mod_year: ', building.mod_year)

        #  Perform VDI 6007 thermal simulation
        (temp_in, q_heat_cool, q_in_wall, q_out_wall) = \
            tus.calc_th_load_build_vdi6007_ex_build(exbuild=building,
                                                    add_th_load=False,
                                                    vent_factor=fix_vent_rate,
                                                    array_vent_rate=None,
                                                    t_set_heat=fix_set_temp,
                                                    t_set_cool=100,
                                                    t_night=16,
                                                    heat_lim_val=1000000)

        #  Results
        #  #####################################
        q_heat = np.zeros(len(q_heat_cool))
        for i in range(len(q_heat_cool)):
            if q_heat_cool[i] > 0:
                q_heat[i] = q_heat_cool[i]

        sum_heat = sum(q_heat) * timestep / (3600 * 1000)  # in kWh

        dict_year_sh_net_demand[year] = sum_heat
        dict_year_sh_power_curves[year] = q_heat

    res_dict['years'] = [dict_year_sh_net_demand, dict_year_sh_power_curves]

    #  Perform sensitivity analysis with different infiltration rates
    #  ##################################################################
    print()
    print('Start sensitivity analysis for infiltration rates')

    dict_inf_sh_net_demand = {}
    dict_inf_sh_power_curves = {}

    for inf_r in array_inf_rates:

        print('Infiltration rate in 1/h:')
        print(inf_r)

        building = copy.deepcopy(exbuilding)
        building.mod_year = fix_build_year

        #  Perform VDI 6007 thermal simulation
        (temp_in, q_heat_cool, q_in_wall, q_out_wall) = \
            tus.calc_th_load_build_vdi6007_ex_build(exbuild=building,
                                                    add_th_load=False,
                                                    vent_factor=inf_r,
                                                    array_vent_rate=None,
                                                    t_set_heat=fix_set_temp,
                                                    t_set_cool=100,
                                                    t_night=16,
                                                    heat_lim_val=1000000)

        #  Results
        #  #####################################
        q_heat = np.zeros(len(q_heat_cool))
        for i in range(len(q_heat_cool)):
            if q_heat_cool[i] > 0:
                q_heat[i] = q_heat_cool[i]

        sum_heat = sum(q_heat) * timestep / (3600 * 1000)  # in kWh

        dict_inf_sh_net_demand[inf_r] = sum_heat
        dict_inf_sh_power_curves[inf_r] = q_heat

    res_dict['inf'] = [dict_inf_sh_net_demand, dict_inf_sh_power_curves]

    #  Perform sensitivity analysis with different set temperatures
    #  ##################################################################
    print()
    print('Start sensitivity analysis for set temperatures')

    dict_set_temp_sh_net_demand = {}
    dict_set_temp_sh_power_curves = {}

    for set_temp in array_temp:

        print('Set temperature in degree Celsius:')
        print(set_temp)

        building = copy.deepcopy(exbuilding)
        building.mod_year = fix_build_year

        #  Perform VDI 6007 thermal simulation
        (temp_in, q_heat_cool, q_in_wall, q_out_wall) = \
            tus.calc_th_load_build_vdi6007_ex_build(exbuild=building,
                                                    add_th_load=False,
                                                    vent_factor=fix_vent_rate,
                                                    array_vent_rate=None,
                                                    t_set_heat=set_temp,
                                                    t_set_cool=100,
                                                    t_night=16,
                                                    heat_lim_val=1000000)

        #  Results
        #  #####################################
        q_heat = np.zeros(len(q_heat_cool))
        for i in range(len(q_heat_cool)):
            if q_heat_cool[i] > 0:
                q_heat[i] = q_heat_cool[i]

        sum_heat = sum(q_heat) * timestep / (3600 * 1000)  # in kWh

        dict_set_temp_sh_net_demand[set_temp] = sum_heat
        dict_set_temp_sh_power_curves[set_temp] = q_heat

        res_dict['set_temp'] = [dict_set_temp_sh_net_demand,
                                dict_set_temp_sh_power_curves]

    #  Perform sensitivity analysis with different weather data
    #  interpolations
    #  ##################################################################
    print()
    print('Start sensitivity analysis for weather files')

    dict_weather_sh_net_demand = {}
    dict_weather_sh_power_curves = {}

    for i in range(len(array_weath_interpol)):

        weather = list_weather[i]
        interp = array_weath_interpol[i]

        print('Weather interpolation factor:')
        print(interp)

        building = copy.deepcopy(exbuilding)
        building.mod_year = fix_build_year
        building.environment.weather = weather

        #  Perform VDI 6007 thermal simulation
        (temp_in, q_heat_cool, q_in_wall, q_out_wall) = \
            tus.calc_th_load_build_vdi6007_ex_build(exbuild=building,
                                                    add_th_load=False,
                                                    vent_factor=fix_vent_rate,
                                                    array_vent_rate=None,
                                                    t_set_heat=fix_set_temp,
                                                    t_set_cool=100,
                                                    t_night=16,
                                                    heat_lim_val=1000000)

        #  Results
        #  #####################################
        q_heat = np.zeros(len(q_heat_cool))
        for i in range(len(q_heat_cool)):
            if q_heat_cool[i] > 0:
                q_heat[i] = q_heat_cool[i]

        sum_heat = sum(q_heat) * timestep / (3600 * 1000)  # in kWh

        dict_weather_sh_net_demand[interp] = sum_heat
        dict_weather_sh_power_curves[interp] = q_heat

    res_dict['weather'] = [dict_weather_sh_net_demand,
                           dict_weather_sh_power_curves]

    return res_dict


if __name__ == '__main__':

    this_path = os.path.dirname(os.path.abspath(__file__))

    building_file = 'building_obj.pkl'
    save_file = 'res_dict_single_build_sa.pkl'

    load_path = os.path.join(this_path, 'input', building_file)
    save_path = os.path.join(this_path, 'output', save_file)

    #  Load building object instance
    building = pickle.load(open(load_path, mode='rb'))

    res_dict = do_single_building_sensitivity_analysis(building=building)

    #pickle.dump(res_dict, open(save_path, mode='wb'))

    #  Extract results
    #  ###################################################################

    #  Retrofit year sensitivity
    dict_year = res_dict['years'][0]
    list_keys = []
    list_values = []
    for key in dict_year:
        list_keys.append(key)
        list_values.append(dict_year[key])

    list_keys, list_values = zip(*sorted(zip(list_keys, list_values)))

    print(list_keys)
    print(list_values)

    plt.plot(list_keys, list_values)
    plt.xlabel('Years')
    plt.ylabel('Space heating energy demand in kWh')
    plt.show()
    plt.close()

    #  Infiltration rate sensitivity
    dict_year = res_dict['inf'][0]
    list_keys = []
    list_values = []
    for key in dict_year:
        list_keys.append(key)
        list_values.append(dict_year[key])

    list_keys, list_values = zip(*sorted(zip(list_keys, list_values)))

    print(list_keys)
    print(list_values)

    plt.plot(list_keys, list_values)
    plt.xlabel('Infiltration rate in 1/h')
    plt.ylabel('Space heating energy demand in kWh')
    plt.show()
    plt.close()

    #  Set temperature sensitivity
    dict_year = res_dict['set_temp'][0]
    list_keys = []
    list_values = []
    for key in dict_year:
        list_keys.append(key)
        list_values.append(dict_year[key])

    list_keys, list_values = zip(*sorted(zip(list_keys, list_values)))

    print(list_keys)
    print(list_values)

    plt.plot(list_keys, list_values)
    plt.xlabel('Set temperature in °C')
    plt.ylabel('Space heating energy demand in kWh')
    plt.show()
    plt.close()

    #  Weather interpolation sensitivity
    dict_year = res_dict['weather'][0]
    list_keys = []
    list_values = []
    for key in dict_year:
        list_keys.append(key)
        list_values.append(dict_year[key])

    list_keys, list_values = zip(*sorted(zip(list_keys, list_values)))

    print(list_keys)
    print(list_values)

    plt.plot(list_keys, list_values)
    plt.xlabel('Weather interpolation factor')
    plt.ylabel('Space heating energy demand in kWh')
    plt.show()
    plt.close()
