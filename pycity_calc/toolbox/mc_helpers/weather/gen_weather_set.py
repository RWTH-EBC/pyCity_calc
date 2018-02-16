#!/usr/bin/env python
# coding=utf-8
"""
Script to generate set of weather files for uncertainty analysis.

Outdoor temperature, direct and diffuse radiation are interpolated lineary
between warm, standard and cold test reference years (TRY)
"""

import os
import random
import copy
import numpy as np

import pycity_base.classes.Timer as time
import pycity_base.classes.Weather as wea


def calc_lin_ipl_array(ref_array, side_array, factor):
    """
    Calculate linear interpolation for every value between two arrays.
    Asssumes 1d arrays. Interpolations starts relative to reference array.

    Parameters
    ----------
    ref_array : array (of floats)
        Reference array
    side_array : array (of floats)
        Second array
    factor : float
        Interpolation factor (between 0 and 1)
        0 is reference, 1 is side array

    Returns
    -------
    ipl_array : array (of float)
        Result array
    """

    assert factor <= 1
    assert factor >= 0
    assert len(ref_array) == len(side_array), 'Arrays have different length!'

    ipl_array = np.zeros(len(ref_array))

    for i in range(len(ipl_array)):

        if ref_array[i] < side_array[i]:
            ipl_value = ref_array[i] + factor * \
                                       abs(side_array[i] - ref_array[i])
        elif ref_array[i] > side_array[i]:
            ipl_value = ref_array[i] - factor * \
                                       abs(side_array[i] - ref_array[i])
        else:
            ipl_value = ref_array[i] + 0.0

        ipl_array[i] = ipl_value

    return ipl_array


def calc_lin_ipl_weath(weath_dict, factor):
    """
    Calculate result weather (outdoor temperature, direct and diffuse radiation)
    with weather dictionary and interpolation factor. New weather is based
    on regular TRY.

    Parameters
    ----------
    weath_dict : dict (of weather objects)
        Dictionary with weather objects as values. Keys are TRY type names
        'cold', 'warm', 'regular'
    factor : float
        Factor for linear interpolation (between - 1 and 1)
        0: Use regular TRY
        1: Use warm TRY
        -1: Use cold TRY
        else: interpolate

    Returns
    -------
    new_weather : object
       Weather object with interpolated temperature and radiation values
    """

    assert factor <= 1
    assert factor >= -1

    new_weather = copy.deepcopy(weath_dict['regular'])
    cold_weather = copy.deepcopy(weath_dict['cold'])
    warm_weather = copy.deepcopy(weath_dict['warm'])

    if factor == 0:
        return new_weather
    elif factor == -1:
        return cold_weather
    elif factor == 1:
        return warm_weather

    if factor > 0:
        #  Interpolate between warm and regular TRY

        new_weather.tAmbient = \
            calc_lin_ipl_array(ref_array=weath_dict['regular'].tAmbient+273.15,
                               side_array=weath_dict['warm'].tAmbient+273.15,
                               factor=factor)
        new_weather.tAmbient -= 273.15

        new_weather.qDirect = \
            calc_lin_ipl_array(ref_array=weath_dict['regular'].qDirect,
                               side_array=weath_dict['warm'].qDirect,
                               factor=factor)

        new_weather.qDiffuse = \
            calc_lin_ipl_array(ref_array=weath_dict['regular'].qDiffuse,
                               side_array=weath_dict['warm'].qDiffuse,
                               factor=factor)

    elif factor < 0:
        #  Interpolate between regular and cold TRY

        new_weather.tAmbient = \
            calc_lin_ipl_array(ref_array=weath_dict['regular'].tAmbient+273.15,
                               side_array=weath_dict['cold'].tAmbient+273.15,
                               factor=abs(factor))
        new_weather.tAmbient -= 273.15

        new_weather.qDirect = \
            calc_lin_ipl_array(ref_array=weath_dict['regular'].qDirect,
                               side_array=weath_dict['cold'].qDirect,
                               factor=abs(factor))

        new_weather.qDiffuse = \
            calc_lin_ipl_array(ref_array=weath_dict['regular'].qDiffuse,
                               side_array=weath_dict['cold'].qDiffuse,
                               factor=abs(factor))

    return new_weather


def get_warm_cold_regular_weather(year=2010, timestep=3600, region_nb=5):
    """
    Function loads and returns 3 TRY weather files (warm, cold, regular)
    for uncertainty analysis.

    Parameters
    ----------
    year : int, optional
        TRY year (default: 2010).
        Options: 2010 or 2035
    timestep : int, optional
        Time discretization in seconds (default: 3600)
    region_nb : int, optional
        Integer defining TRY region number (default: 5)

    Returns
    -------
    dict_weather : dict
        Dictionary with weather objects as values. Keys are TRY type names
        'cold', 'warm', 'regular'
    """

    dict_weather = {}

    #  Initialize timer object
    timer = time.Timer(timeDiscretization=timestep)

    #  pycity pathes
    #  #################################################################
    path_pycity = \
        os.path.dirname(os.path.dirname(os.path.abspath(wea.__file__)))

    path_weat_data = os.path.join(path_pycity, 'inputs', 'weather')

    #  Generate pathes to load data
    #  #################################################################

    if region_nb < 10:
        region_name = '0' + str(region_nb)
    else:
        region_name = str(region_nb)

    name_regular = 'TRY' + str(year) + '_' + str(region_name) + '_Jahr.dat'
    name_warm = 'TRY' + str(year) + '_' + str(region_name) + '_Somm.dat'
    name_cold = 'TRY' + str(year) + '_' + str(region_name) + '_Wint.dat'

    path_regular = os.path.join(path_weat_data, name_regular)
    path_warm = os.path.join(path_weat_data, name_warm)
    path_cold = os.path.join(path_weat_data, name_cold)

    #  Initialize weather objects
    weather_regular = wea.Weather(timer=timer, pathTRY=path_regular)
    weather_warm = wea.Weather(timer=timer, pathTRY=path_warm)
    weather_cold = wea.Weather(timer=timer, pathTRY=path_cold)

    #  Add weather object instances to dictionary
    dict_weather['regular'] = weather_regular
    dict_weather['warm'] = weather_warm
    dict_weather['cold'] = weather_cold

    return dict_weather


def gen_set_of_weathers(nb_weath, year=2010, timestep=3600, region_nb=5,
                        random_method='uniform'):
    """
    Generates and returns list of weather objects for uncertainty analysis.
    Outdoor temperatures and radiations are approximated between warm and
    regular respectively regular and cold TRY based on random numbers.

    Parameters
    ----------
    nb_weath : int
        Number of requested weather objects in output list
    year : int, optional
        TRY year (default: 2010).
        Options: 2010 or 2035
    timestep : int, optional
        Time discretization in seconds (default: 3600)
    region_nb : int, optional
        Integer defining TRY region number (default: 5)
    random_method : str, optional)
        Method to select random number for interpolation (default: 'uniform')
        Options:
        'uniform' --> Use uniform distribution between -1 and 1
        'normal' --> Normal distribution

    Returns
    -------
    list_weather : list (of weather objects)
        List holding different weather objects
    """

    assert random_method in ['uniform', 'normal'], \
        'Unknown method for random numbers.'

    list_weather = []

    #  Get dictionary with cold, regular and warm TRY weather objects
    dict_weather = get_warm_cold_regular_weather(year=year, timestep=timestep,
                                                 region_nb=region_nb)

    for i in range(nb_weath):

        #  Choose random number
        if random_method == 'uniform':
            rand_nb = random.uniform(-1, 1)

        elif random_method == 'normal':
            rand_nb = np.random.normal(loc=0, scale=0.23)

        new_weather = \
            calc_lin_ipl_weath(weath_dict=dict_weather, factor=rand_nb)

        list_weather.append(new_weather)

    return list_weather


if __name__ == '__main__':
    timestep = 3600
    region_nb = 5  # Region number for TRY usage
    #  (currently, 5 and 12 are available. More TRY datasets can be found
    #   on DWD website for download)
    year = 2010  # Year of TRY (2010 for current TRY or 2035 for future TRY)
    nb_weather = 5
    random_method = 'uniform'  # 'normal' or 'uniform'

    list_wea = gen_set_of_weathers(nb_weath=nb_weather, year=year,
                                   timestep=timestep, region_nb=region_nb,
                                   random_method=random_method)

    import matplotlib.pyplot as plt

    fig = plt.figure()

    for weather in list_wea:
        plt.plot(weather.tAmbient, alpha=0.3)
    plt.xlabel('Time in hours')
    plt.ylabel('Outdoor temperature\nin degree Celsius')
    plt.show()
    plt.close()

    for weather in list_wea:
        plt.plot(weather.qDirect, alpha=0.3)
    plt.xlabel('Time in hours')
    plt.ylabel('Direct radiation in W/m2')
    plt.show()
    plt.close()

    for weather in list_wea:
        plt.plot(weather.qDiffuse, alpha=0.3)
    plt.xlabel('Time in hours')
    plt.ylabel('Diffuse radiation in W/m2')
    plt.show()
    plt.close()

    #  Further analysis
    #  ###########################################################

    weath_dict = get_warm_cold_regular_weather(year=year,
                                               timestep=timestep,
                                               region_nb=region_nb)

    av_reg_temp = np.mean(weath_dict['regular'].tAmbient)
    av_cold_temp = np.mean(weath_dict['cold'].tAmbient)
    av_warm_temp = np.mean(weath_dict['warm'].tAmbient)

    print('Average cold temperature in degree C:')
    print(av_cold_temp)
    print('Average regular temperature in degree C:')
    print(av_reg_temp)
    print('Average warm temperature in degree C:')
    print(av_warm_temp)
    print()

    new_weather_cold = calc_lin_ipl_weath(weath_dict, -1)
    print('Average interpol cold (-1) temperature in degree C:')
    av_interp_cold_temp = np.mean(new_weather_cold.tAmbient)
    print(av_interp_cold_temp)

    new_weather_reg = calc_lin_ipl_weath(weath_dict, 0)
    print('Average interpol reg (0) temperature in degree C:')
    av_interp_reg_temp = np.mean(new_weather_reg.tAmbient)
    print(av_interp_reg_temp)

    new_weather_warm = calc_lin_ipl_weath(weath_dict, 1)
    print('Average interpol reg (1) temperature in degree C:')
    av_interp_reg_warm = np.mean(new_weather_warm.tAmbient)
    print(av_interp_reg_warm)

    new_weather_warm_075 = calc_lin_ipl_weath(weath_dict, 0.75)
    print('Average interpol reg (0.75) temperature in degree C:')
    av_interp_reg_warm_075 = np.mean(new_weather_warm_075.tAmbient)
    print(av_interp_reg_warm_075)
