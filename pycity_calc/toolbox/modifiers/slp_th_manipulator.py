#!/usr/bin/env python
# coding=utf-8
"""
Script to to manipulate thermal slp profiles. Sets power to zero for days
with specific temperature levels and rescales power curve to fit to original
annual energy demand value in kWh
"""

import numpy as np
import matplotlib.pyplot as plt

import pycity_base.classes.Timer
import pycity_base.classes.Weather
import pycity_base.classes.Prices
import pycity_base.classes.Environment
import pycity_base.classes.demand.SpaceHeating as SpaceHeating


def gen_pycity_environment(timestep=3600):
    """
    Generate pycity (NOT pycity_calc) environment

    Parameters
    ----------
    timestep : int
        Timestep in seconds

    Returns
    -------
    env : object
        Environment object of pycity
    """

    timer = pycity_base.classes.Timer.Timer(timeDiscretization=timestep)
    weather = pycity_base.classes.Weather.Weather(timer, useTRY=True)
    prices = pycity_base.classes.Prices.Prices()
    env = pycity_base.classes.Environment.Environment(timer, weather, prices)

    return env


def gen_th_slp(environment, living_area=150, spec_dem=100):
    """
    Generate thermal SLP

    Parameters
    ----------
    environment : object
        Environment object
    living_area : float, optional
        Living area in m2 (default: 150)
    spec_dem : float, optional
        Specific thermal energy demand in kWh/m2a (default: 100)

    Returns
    -------
    slp_object : object
        Thermal SLP object
    """

    slp_object = SpaceHeating.SpaceHeating(environment,
                                           method=1,  # Standard load profile
                                           livingArea=living_area,
                                           specificDemand=spec_dem)

    return slp_object


def slp_th_manipulator(timestep, th_slp_curve, temp_array, temp_av_cut=12):
    """

    Parameters
    ----------
    timestep : int
        Timestep in seconds
    th_slp_curve : array-like
        Annual thermal SLP power curve in W (per timestep)
    temp_array : array-like
        Annual outdoor temperature array in °C (per timestep)
    temp_av_cut : float, optional
        Average daily temperature in °C, where power is cut of (default: 12)

    Returns
    -------
    slp_mod_curve : array-like
        Modified thermal SLP curve in W (per timestep)
    """

    assert len(th_slp_curve) * timestep == 365 * 24 * 3600
    assert len(temp_array) * timestep == 365 * 24 * 3600

    timesteps_per_day = len(th_slp_curve)/365

    slp_org_th_energy = sum(th_slp_curve) * timestep / (3600 * 1000)  # kWh

    #  Calculate average, daily temperatures
    temp_average_array = np.zeros(365)
    count_timestep = 0

    #  Loop over days
    for i in range(len(temp_average_array)):

        temp_average = 0

        #  Loop over hours
        for h in range(int(timesteps_per_day)):
            #  Sum up values
            temp_average += temp_array[count_timestep + h]

        # and divide by 24 hours
        temp_average /= timesteps_per_day

        temp_average_array[i] = temp_average

        #  Count up day counter
        count_timestep += int(timesteps_per_day)

    slp_mod_curve = np.zeros(len(th_slp_curve))

    count_timestep = 0
    #  Loop over days (for average temperatures)
    for i in range(len(temp_average_array)):

        curr_av_temp = temp_average_array[i]

        #  If average temperature is larger or equal to limit temperature
        if curr_av_temp >= temp_av_cut:  # Set power in timeframe to zero

            #  Loop over hours
            for h in range(int(timesteps_per_day)):
                slp_mod_curve[count_timestep + h] = 0  # Set to zero

        else:  # Set slp_mod values to th_slp_curve values

            #  Loop over hours
            for h in range(int(timesteps_per_day)):
                slp_mod_curve[count_timestep + h] = th_slp_curve[count_timestep + h]

        # Count up day counter
        count_timestep += int(timesteps_per_day)

    # Rescale to original energy demand
    con_factor = slp_org_th_energy / (
    sum(slp_mod_curve) * timestep / (3600 * 1000))
    slp_mod_curve *= con_factor

    return slp_mod_curve


if __name__ == '__main__':
    timestep = 3600

    #  Generate environment
    environment = gen_pycity_environment(timestep=timestep)

    #  Generate slp object
    slp_object = gen_th_slp(environment)

    #  Pointer to temperature curve
    temp_curve = environment.weather.tAmbient

    #  Pointer to slp curve
    slp_curve = slp_object.loadcurve

    #  Manipulate slp profile
    slp_mod_curve = slp_th_manipulator(timestep, th_slp_curve=slp_curve,
                                       temp_array=temp_curve)

    plt.plot(slp_curve, label='Org. SLP')
    plt.plot(slp_mod_curve, label='Mod. SLP')
    plt.xlabel('Time in hours')
    plt.ylabel('Thermal power in W')
    plt.legend()
    plt.show()
