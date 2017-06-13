#!/usr/bin/env python
# coding=utf-8
"""
Script to reevaluate building for Monte carlo analysis
"""

import pycity_calc.toolbox.mc_helpers.demand_unc_single_build as dem_unc_b
import numpy as np
import pycity_calc.toolbox.teaser_usage.teaser_use as tus


def new_building_evaluation_mc(building, dict_new_values):
    """
        Modifies building parameters for Monte Carlo Analysis

        Parameters
        ----------
        building : object
            Extended building object of py
        dict_new_values : dict
        Dictionary holding lists with new values for different uncertain parameters
        Keys:
        'mod_year' : Holding new modification year
        'inf' : Holding new infiltration rate
        'occ' : Holding new occupants per apartment
        'el' : Holding new electrical demand per apartment
        'set_temp' : Holding new set temperature per apartment
        'user_air' : Holding new user air exchange rate per apartment
        'weather' : Holding new weather per apartment
        'net_floor_factor' : Holding percentage of modification for net floor area

        Returns
        -------
        building : object
            Modified extended building object
        """


    new_weather = []
    new_weather.append(dict_new_values['weather'])
    area_factor = dict_new_values['net_floor_area']


    # new_physics parameters
    building = dem_unc_b.mod_single_build_w_samples(building,  dict_new_values, new_weather, 0)

    #new net floor area
    building.net_floor_area = building.net_floor_area * (1 - area_factor)

    #new space heating
    #  Get samples for parameters, which are not stored on building object
    inf_rate = dict_new_values['inf']
    print('Inf. rate: ', inf_rate)
    usr_air_ex_rate = dict_new_values['user_air']
    print('User air exchange rate: ', usr_air_ex_rate)


    vent_array = np.zeros(len(building.environment.weather.tAmbient))

    vent_array += inf_rate + usr_air_ex_rate
    #  Sum up user air exchange and infiltration

    tset_heat = dict_new_values['set_temp'][0]
    print('Set temperature: ', tset_heat)

    #  Perform VDI 6007 simulation
    #  ##################################################################
    (temp_in, q_heat_cool, q_in_wall, q_out_wall) = tus.calc_th_load_build_vdi6007_ex_build(exbuild=building,
                                                add_th_load=False,
                                                vent_factor=None,
                                                array_vent_rate=vent_array,
                                                t_set_heat=tset_heat,
                                                t_set_cool=100,
                                                t_night=16,
                                                heat_lim_val=1000000)


    return building
