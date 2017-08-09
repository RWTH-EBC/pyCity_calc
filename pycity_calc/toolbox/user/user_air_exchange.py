#!/usr/bin/env python
# coding=utf-8
"""
Script to generate stochastic, user-dependend air exchange rates
(based on window/door opening)

References:
Luftwechsel = Infiltrationsrate + Nutzerbedingtes Lüften

http://www.baubiologie.net/fileadmin/_migrated/content_uploads/VDB_Luftwechsel__Fensterlueftung_und_die_Notwendigkeit_von_Lueftungskonzepten.pdf
Infiltrationsrate: 0,1 - 0,5 (Sanierungsabhängig)
Mittelwert bei 0,26 laut:

Fenster (Kipp): 1,2 1/h
Fenster (Stoß): 8,8 1/h
http://www.agoef.de/fileadmin/user_upload/dokumente/publikationen/auszuege-kongressreader/Muenzenberg-2004--natuerlicher-Luftwechsel-in-Gebaeuden-Bedeutung-Beurteilung-Schimmelpilzschaeden.pdf

According to DIN 18599 range of natural infiltration rate should be
between 0.07 and 0.7.
(with wind coefficient of 0.07 and n50 values from 1 to 10)

"""

import copy
import random
import warnings
import numpy as np

import pycity_base.classes.Timer as Timer
import pycity_base.classes.Weather as Weather
import pycity_base.classes.Environment as Envir
import pycity_base.classes.Prices as Prices
import pycity_base.functions.changeResolution as chres
import pycity_base.classes.demand.Occupancy as Occupancy


def get_inf_rate(mod_year):
    """
    Estimate infiltration rate in 1/h, dependend on last year of modernization.
    If no modernization has been performed, use year of construction instead.

    Parameters
    ----------
    mod_year : int
        Year of last modernization

    Returns
    -------
    inf_rate : float
        Infiltration rate in 1/h (related to building air volume)
    """

    if mod_year < 1951:
        inf_rate = 1
    elif mod_year < 1969:
        inf_rate = 0.5
    elif mod_year < 1982:
        inf_rate = 0.3
    elif mod_year < 1994:
        inf_rate = 0.25
    elif mod_year < 2001:
        inf_rate = 0.2
    elif mod_year < 2009:
        inf_rate = 0.15
    elif mod_year < 2014:
        inf_rate = 0.1
    else:
        inf_rate = 0.1

    return inf_rate


def gen_det_air_ex_rate_temp_dependend(occ_profile, temp_profile,
                                       inf_rate=None):
    """
    Generate deterministic air exchange rate. In this case, air exchange rate
    is temperature dependent.

    Parameters
    ----------
    occ_profile : array (of ints)
        Occupancy profile (number of present occupants per timestep)
    temp_profile : array (of floats)
        Outdoor temperature in degree Celsius
    inf_rate : float, optional
        Infiltration rate (default: None). If value (not None) is set, value
        is added to deterministic air exchange rate profile

    Returns
    -------
    array_air_ex : array
        Air exchange rate array (in 1/h)
    """

    #  Assert statements
    if inf_rate is not None:
        assert inf_rate >= 0, 'Infiltration rate cannot be below zero!'

    # Warnings
    if len(occ_profile) != len(temp_profile):
        msg = 'Occupancy and temperature profile have different timesteps!' \
              ' Please check, if this has been done intentionally.' \
              'Timestep of temperature is used as timestep of ventilation.'
        warnings.warn(msg)

        # Calculate current timestep
        timestep_occ = 365 * 24 * 3600 / len(occ_profile)
        timestep_temp = 365 * 24 * 3600 / len(temp_profile)

        #  Copy profiles
        occ_profile = copy.copy(occ_profile)

        #  Change resolution of occupancy profile to resolution of temperature
        occ_profile = chres.changeResolution(occ_profile,
                                             oldResolution=timestep_occ,
                                             newResolution=timestep_temp)

    # Generate base air exchange rate array
    if inf_rate is None:
        array_air_ex = np.zeros(len(temp_profile))
    else:
        array_air_ex = np.ones(len(temp_profile)) * inf_rate

    for i in range(len(temp_profile)):

        #  Current temperature in degree C
        temp = temp_profile[i]

        #  Current number of occupants
        occ = occ_profile[i]

        if occ >= 1:

            if temp <= 0:

                pass  # No air exchange (except infiltration)

            elif temp <= 10:

                array_air_ex[i] += 0.1

            elif temp <= 18:

                array_air_ex[i] += 0.15

            elif temp <= 24:

                array_air_ex[i] += 0.25

            elif temp <= 28:

                array_air_ex[i] += 1

            else:

                array_air_ex[i] += 2

    return array_air_ex


def gen_user_air_ex_rate(occ_profile, temp_profile, b_type='res',
                         inf_rate=None, set_temp=20):
    """
    Generate user air exchange rate (in 1/h)

    Parameters
    ----------
    occ_profile : array (of ints)
        Occupancy profile (defining number of present occupants).
        Should have length of one year
    temp_profile : array (of floats)
        Outdoor temperature profile (in degree Celsius)
    b_type : str, optional
        Defines type of building (default: 'res')
        Options:
        - 'res' : residential building / profile
    inf_rate : float, optional
        Infiltration rate in 1/h (default: None). Values is added to
        returned air exchange rate. If set to None, only user dependend
        air exchange rate is returned (no infiltration)
    set_temp : float, optional
        Set temperature of building in degree Celsius. If outdoor temperature
        is below set temperature, full window openings are prevented.
        Instead, only partially window opening is possible.

    Returns
    -------
    air_exch : array-like
        Array of air exchange rates in 1/h per timestep
    """

    #  Assert statements
    if inf_rate is not None:
        assert inf_rate >= 0, 'Infiltration rate cannot be below zero!'
    assert b_type in ['res'], 'Unknown building type!'

    #  Warnings
    if len(occ_profile) != len(temp_profile):
        msg = 'Occupancy and temperature profile have different timesteps!' \
              ' Please check, if this has been done intentionally.' \
              'Timestep of temperature is used as timestep of ventilation.'
        warnings.warn(msg)

    # Calculate current timestep
    timestep_occ = 365 * 24 * 3600 / len(occ_profile)
    timestep_temp = 365 * 24 * 3600 / len(temp_profile)

    #  Copy profiles
    occ_profile = copy.copy(occ_profile)
    temp_profile = copy.copy(temp_profile)

    #  Change resolution to 5 minute (300 s) timestep
    occ_profile_5 = chres.changeResolution(occ_profile,
                                           oldResolution=timestep_occ,
                                           newResolution=300)
    temp_profile_5 = chres.changeResolution(temp_profile,
                                            oldResolution=timestep_temp,
                                            newResolution=300)

    #  Generate base air exchange rate array
    if inf_rate is None:
        array_air_ex = np.zeros(len(temp_profile_5))
    else:
        array_air_ex = np.ones(len(temp_profile_5)) * inf_rate

    # Initial status
    window_mode = 0

    for i in range(len(temp_profile_5)):

        if occ_profile_5[i] == 0:
            #  Set user defined air exchange rate to zero / keep value
            pass

        elif occ_profile_5[i] > 0:

            #  Generate user dependend air exchange rate
            rand_nb = random.random()

            #  If temperature is equal or below 0 degree C:
            if temp_profile_5[i] <= 0:

                #  Leave windows closed / close window
                window_mode = 0

            # If temperature is below 10 degree C:
            elif temp_profile_5[i] < 10:

                #  Leave windows closed / close window
                window_mode = 0

            # If temperature is below 16 degree C:
            elif temp_profile_5[i] < 16:

                if window_mode == 0:  # Window is closed

                    if rand_nb < 0.8:
                        #  Leave windows closed / close window
                        window_mode = 0
                    # elif rand_nb < 0.98:
                    else:
                        #  Window only partially open
                        array_air_ex[i] += 1.2
                        window_mode = 1
                        # else:
                        #     #  Fully open windows
                        #     array_air_ex[i] += 8.8
                        #     window_mode = 2

                elif window_mode == 1:  # Window is partially open

                    if rand_nb < 0.85:
                        #  Leave windows closed / close window
                        window_mode = 0
                    # if rand_nb < 0.99:
                    else:
                        #  Leave window partially open
                        array_air_ex[i] += 1.2
                        window_mode = 1
                        # else:
                        #     #  Fully open windows
                        #     array_air_ex[i] += 8.8
                        #     window_mode = 2

                elif window_mode == 2:  # Windows fully open

                    #  Leave windows closed / close window
                    window_mode = 0

            # If temperature is below set_temp degree C:
            elif temp_profile_5[i] < set_temp:

                if window_mode == 0:  # Window is closed

                    if rand_nb < 0.75:
                        #  Leave windows closed / close window
                        window_mode = 0
                    # elif rand_nb < 0.98:
                    else:
                        #  Window only partially open
                        array_air_ex[i] += 1.2
                        window_mode = 1
                        # else:
                        #     #  Fully open windows
                        #     array_air_ex[i] += 8.8
                        #     window_mode = 2

                elif window_mode == 1:  # Window is partially open

                    if rand_nb < 0.6:
                        #  Leave windows closed / close window
                        window_mode = 0
                    # if rand_nb < 0.99:
                    else:
                        #  Leave window partially open
                        array_air_ex[i] += 1.2
                        window_mode = 1
                        # else:
                        #     #  Fully open windows
                        #     array_air_ex[i] += 8.8
                        #     window_mode = 2

                elif window_mode == 2:  # Windows fully open

                    #  Leave windows closed / close window
                    window_mode = 0

            # If temperature is below set_temp degree C:
            elif temp_profile_5[i] < (set_temp + 4):

                if window_mode == 0:  # Window is closed

                    if rand_nb < 0.5:
                        #  Leave windows closed / close window
                        window_mode = 0
                    # elif rand_nb < 0.9:
                    else:
                        #  Window only partially open
                        array_air_ex[i] += 1.2
                        window_mode = 1
                    # else:
                    #     #  Fully open windows
                    #     array_air_ex[i] += 8.8
                    #     window_mode = 2

                elif window_mode == 1:  # Window is partially open

                    if rand_nb < 0.05:
                        #  Leave windows closed / close window
                        window_mode = 0
                    # if rand_nb < 0.99:
                    else:
                        #  Leave window partially open
                        array_air_ex[i] += 1.2
                        window_mode = 1
                        # else:
                        #     #  Fully open windows
                        #     array_air_ex[i] += 8.8
                        #     window_mode = 2

                elif window_mode == 2:  # Windows fully open

                    # if rand_nb < 0.7:
                    #     #  Leave windows closed / close window
                    #     window_mode = 0
                    # # elif rand_nb < 0.91:
                    # #     #  Leave window partially open
                    # #     array_air_ex[i] += 1.2
                    # #     window_mode = 1
                    # else:
                    #     #  Fully open windows
                    #     array_air_ex[i] += 8.8
                    #     window_mode = 2

                    window_mode = 0

            else:  # Outdoor temperature profile above (set_temp + 4) degree C

                if window_mode == 0:  # Window is closed

                    if rand_nb < 0.2:
                        #  Leave windows closed / close window
                        window_mode = 0
                    elif rand_nb < 0.7:
                        #  Window only partially open
                        array_air_ex[i] += 1.2
                        window_mode = 1
                    else:
                        #  Fully open windows
                        array_air_ex[i] += 8.8
                        window_mode = 2

                elif window_mode == 1:  # Window is partially open

                    if rand_nb < 0.05:
                        #  Leave windows closed / close window
                        window_mode = 0
                    # if rand_nb < 0.95:
                    else:
                        #  Leave window partially open
                        array_air_ex[i] += 1.2
                        window_mode = 1
                        # else:
                        #     #  Fully open windows
                        #     array_air_ex[i] += 8.8
                        #     window_mode = 2

                elif window_mode == 2:  # Windows fully open

                    if rand_nb < 0.1:
                        #  Leave windows closed / close window
                        window_mode = 0
                    # elif rand_nb < 0.8:
                    #     #  Leave window partially open
                    #     array_air_ex[i] += 1.2
                    #     window_mode = 1
                    else:
                        #  Fully open windows
                        array_air_ex[i] += 8.8
                        window_mode = 2

        elif occ_profile_5[i] < 0:
            raise AssertionError('Occupancy profile cannot be negative!')

    # Re-change resolution
    air_exch = chres.changeResolution(array_air_ex, oldResolution=300,
                                      newResolution=timestep_temp)

    return air_exch


if __name__ == '__main__':
    #  Generate stochastic air exchange profile
    #  ################################################################

    #  #  Uncomment, if you want to use same random number per run
    #  #  e.g. for result comparison or testing purpose
    #  random.seed(1)

    print('Generate stochastic air exchange rate')

    timestep = 3600

    timer = Timer.Timer(timeDiscretization=timestep)
    weather = Weather.Weather(timer=timer)
    prices = Prices.Prices()

    environment = Envir.Environment(timer=timer, weather=weather,
                                    prices=prices)

    #  Generate random occupancy profile
    occupancy = Occupancy.Occupancy(environment=environment,
                                    number_occupants=3)

    occ_profile = copy.copy(occupancy.occupancy)

    curr_occ_timestep = 365 * 24 * 3600 / len(occ_profile)

    #  Change resolution
    occ_profile = chres.changeResolution(occ_profile,
                                         oldResolution=curr_occ_timestep,
                                         newResolution=timestep)

    #   Calculate air exchange rate
    air_exchange = gen_user_air_ex_rate(occ_profile=occ_profile,
                                        temp_profile=weather.tAmbient)

    print('Mean air exchange rate in 1/h:')
    print(np.mean(air_exchange))

    print('Max. air exchange rate in 1/h:')
    print(max(air_exchange))

    import matplotlib.pyplot as plt

    fig = plt.figure()
    fig.add_subplot(211)
    plt.plot(occ_profile)
    plt.xlim(0, 24 * 3600 / timestep)
    plt.ylabel('Occupancy')
    plt.title('Winter day (stochastic profile)')
    fig.add_subplot(212)
    plt.plot(air_exchange)
    plt.xlim(0, 24 * 3600 / timestep)
    plt.ylabel('Air exchange rate in 1/h')
    plt.show()

    fig2 = plt.figure()
    fig2.add_subplot(211)
    plt.plot(occ_profile)
    plt.xlim(180 * 24 * 3600 / timestep, 180 * 24 * 3600 / timestep +
             24 * 3600 / timestep)
    plt.ylabel('Occupancy')
    plt.title('Summer day (stochastic profile)')
    fig2.add_subplot(212)
    plt.plot(air_exchange)
    plt.xlim(180 * 24 * 3600 / timestep, 180 * 24 * 3600 / timestep +
             24 * 3600 / timestep)
    plt.ylabel('Air exchange rate in 1/h')
    plt.show()

    fig3 = plt.figure()
    fig3.add_subplot(311)
    plt.plot(weather.tAmbient)
    plt.ylabel('Outdoor temperature in degree C')
    plt.title('Annual profile (stochastic profile)')
    fig3.add_subplot(312)
    plt.plot(occ_profile)
    plt.ylabel('Occupancy')
    fig3.add_subplot(313)
    plt.plot(air_exchange)
    plt.ylabel('Air exchange rate in 1/h')
    plt.show()

    print('\n##################################\n')

    #  Generate deterministic, temperature-dependend air exchange profile
    #  ################################################################

    print('Generate deterministic air exchange rate')

    air_ex_det = \
        gen_det_air_ex_rate_temp_dependend(occ_profile=occ_profile,
                                           temp_profile=weather.tAmbient)

    print('Mean air exchange rate in 1/h:')
    print(np.mean(air_ex_det))

    print('Max. air exchange rate in 1/h:')
    print(max(air_ex_det))

    fig4 = plt.figure()
    fig4.add_subplot(211)
    plt.plot(occ_profile)
    plt.xlim(0, 24 * 3600 / timestep)
    plt.ylabel('Occupancy')
    plt.title('Winter day (deterministic profile)')
    fig4.add_subplot(212)
    plt.plot(air_ex_det)
    plt.xlim(0, 24 * 3600 / timestep)
    plt.ylabel('Air exchange rate in 1/h')
    plt.show()

    fig5 = plt.figure()
    fig5.add_subplot(211)
    plt.plot(occ_profile)
    plt.xlim(180 * 24 * 3600 / timestep, 180 * 24 * 3600 / timestep +
             24 * 3600 / timestep)
    plt.ylabel('Occupancy')
    plt.title('Summer day (deterministic profile)')
    fig5.add_subplot(212)
    plt.plot(air_ex_det)
    plt.xlim(180 * 24 * 3600 / timestep, 180 * 24 * 3600 / timestep +
             24 * 3600 / timestep)
    plt.ylabel('Air exchange rate in 1/h')
    plt.show()

    fig6 = plt.figure()
    fig6.add_subplot(311)
    plt.plot(weather.tAmbient)
    plt.ylabel('Outdoor temperature in degree C')
    plt.title('Annual profile (deterministic profile)')
    fig6.add_subplot(312)
    plt.plot(occ_profile)
    plt.ylabel('Occupancy')
    fig6.add_subplot(313)
    plt.plot(air_ex_det)
    plt.ylabel('Air exchange rate in 1/h')
    plt.show()