#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
from __future__ import division

import warnings
import numpy as np
import matplotlib.pyplot as plt

import pycity_calc.toolbox.dimensioning.slp_th_manipulator as slpman


def calc_heat_timesteps(outdoor_temp, days=365, timestep=3600,
                        temp_heat_lim=15):
    """
    Returns array with 0 (no heat timestep) or 1 (heating timestep)
    as possible values.

    Parameters
    ----------
    outdoor_temp : array-like
        List or array with outdoor temperature in degree Celsius
    days : int, optional
        Defines number of days chosen for array generation (default: 365)
    timestep : int, optional
        Defines time discretization in seconds (default: 3600)
    temp_heat_lim : float, optional
        Limit temperature for heating in degree Celsius (default: 15),
        related to DIN 4108 T6 and VDI 2067

    Returns
    -------
    heat_array : np.array
        Numpy array to define heating timesteps
    """

    assert days > 0
    assert timestep > 0
    assert isinstance(days, int)
    assert isinstance(timestep, int)

    if days != 365:
        msg = 'You are not using 365 days for calculation of heat timpsteps.' \
              ' Instead, going to use ' + str(days) + ' days.'
        warnings.warn(msg)

    if temp_heat_lim <= 10 or temp_heat_lim >= 22:
        msg = str(temp_heat_lim) + ' degree Celius seems to be an ' \
                                   'unrealistic heating limit temperature.' \
                                   ' Please check temp_heat_lim input.'
        warnings.warn(msg)

    #  Generate dummy array
    heat_array = np.zeros(len(outdoor_temp))

    #  Get average daily temperatures
    temp_av_array = slpman.calc_av_daily_temp(timestep=timestep,
                                              outdoor_temp=outdoor_temp)

    count_hour = 0
    #  Loop over days (for average temperatures)
    for i in range(len(temp_av_array)):

        curr_av_temp = temp_av_array[i]

        #  If average temperature is larger or equal to limit temperature
        if curr_av_temp >= temp_heat_lim:  # Set power in timeframe to zero

            #  Loop over hours
            for h in range(int(24 * 3600 / timestep)):
                heat_array[count_hour + h] = 0  # Set to zero

        else:  # Set slp_mod values to th_slp_curve values

            #  Loop over hours
            for h in range(int(24 * 3600 / timestep)):
                heat_array[count_hour + h] = 1

        # Count up day counter
        count_hour += int(24 * 3600 / timestep)

    return heat_array


if __name__ == '__main__':
    timestep = 3600
    days = 365
    temp_heat_lim = 15  # degree Celsius

    environment = slpman.gen_pycity_environment(timestep=timestep)

    temp_out = environment.weather.tAmbient

    heat_array = calc_heat_timesteps(outdoor_temp=temp_out, days=days,
                                     timestep=timestep,
                                     temp_heat_lim=temp_heat_lim)

    plt.plot(heat_array)
    plt.xlabel('Time in ' + str(timestep/3600) + ' hours')
    plt.ylabel('Heating day (0: No) / (1: Yes)')
    plt.show()