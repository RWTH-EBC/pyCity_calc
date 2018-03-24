#!/usr/bin/env python
# coding=utf-8
"""
Script to sample uncertain user parameters
"""
from __future__ import division

import random as rd
import numpy as np
from scipy.stats import nakagami


def calc_set_temp_samples(nb_samples, mean=20, sdev=2.5):
    """
    Calculate array of indoor set temperature values from gaussian
    distribution.

    Parameters
    ----------
    nb_samples : int
        Number of samples
    mean : float, optional
        Mean temperature value in degree Celsius for gaussian distribution
        (default: 20)
    sdev : float, optional
        Standard deviation in degree Celsius for gaussian distribution
        (default: 2.5)

    Returns
    -------
    array_set_temp : np.array (of floats)
        Numpy array of indoor set temperatures in degree Celsius
    """

    array_set_temp = np.random.normal(loc=mean, scale=sdev, size=nb_samples)

    return array_set_temp


def calc_user_air_ex_rates(nb_samples, min_value=0, max_value=1.2,
                           pdf='nakagami'):
    """
    Calculate array of user air exchange rate samples

    Parameters
    ----------
    nb_samples : int
        Number of samples
    min_value : float, optional
        Minimum user air exchange rate (default: 0)
    max_value : float, optional
        Maximum user air exchange rate (default: 1.2)
    dist : str, optional
        Probability density function to choose samples (default: 'nakagami')
        Options:
        - 'equal' : Equal distribution between min_value and max_value
        - 'triangle' : Triangular distribution
        - 'nakagami' : Nakagami distribution

    Returns
    -------
    array_usr_inf : np.array (of floats)
        Numpy array holding user infiltration rates in 1/h
    """

    assert pdf in ['equal', 'triangle', 'nakagami'], \
        'Unknown value for pdf input.'

    # list_usr_inf = []

    array_usr_inf = np.zeros(nb_samples)

    if pdf == 'equal':
        min_value *= 1000
        max_value *= 1000

        for i in range(nb_samples):
            array_usr_inf[i] = rd.randint(min_value, max_value)

        for i in range(len(array_usr_inf)):
            array_usr_inf[i] /= 1000

    elif pdf == 'triangle':
        mode = min_value + (max_value - min_value) * 0.2

        for i in range(nb_samples):
            val = np.random.triangular(left=min_value,
                                       right=max_value,
                                       mode=mode)
            array_usr_inf[i] = val

    elif pdf == 'nakagami':
        array_usr_inf = nakagami.rvs(0.6, scale=0.4, size=nb_samples)

    return array_usr_inf


#  Led to problems within monte-carlo simulation, as extrem air exchange
#  rates can lead to unrealistic thermal peak loads within space heating
#  profiles
# def calc_user_air_ex_profiles_factors(nb_samples, occ_profile, temp_profile,
#                                       random_gauss=True):
#     """
#     Calculate set of user air exchange rate profiles. Uses stochastic
#     air exchange rate user profile generation, based on user_air_exchange.py.
#     Moreover, random rescaling, based on gaussion distribution, can be
#     activated
#
#     Parameters
#     ----------
#     nb_samples : int
#         Number of samples
#     occ_profile : array (of ints)
#         Occupancy profile per timestep
#     temp_profile : array (of floats)
#         Outdoor temperature profile in degree Celsius per timestep
#     random_gauss : bool, optional
#         Defines, if resulting profile should randomly be rescaled with
#         gaussian distribution rescaling factor (default: True)
#
#     Returns
#     -------
#     list_air_ex_profiles : list (of arrays)
#         List of air exchange profiles
#     """
#
#     list_air_ex_profiles = []
#
#     for i in range(nb_samples):
#
#         air_exch = usair.gen_user_air_ex_rate(occ_profile=occ_profile,
#                                               temp_profile=temp_profile,
#                                               b_type='res',
#                                               inf_rate=None)
#
#         if random_gauss:
#             rescale_factor = np.random.normal(loc=1, scale=0.25)
#             if rescale_factor < 0:
#                 rescale_factor = 0
#             air_exch *= rescale_factor
#
#         list_air_ex_profiles.append(air_exch)
#
#     return list_air_ex_profiles


def calc_sampling_occ_per_app(nb_samples, method='destatis',
                              min_occ=1, max_occ=5):
    """
    Calculate array of nb. of occupants samples

    Parameters
    ----------
    nb_samples : int
        Number of samples
    method : str, optional
        Method to calculate occupants per apartment samples
        (default: 'destatis')
        Options:
        - 'equal' : Select samples between min_occ and max_occ from equal
        distribution
        - 'destatis' : Select samples with random numbers from Destatis
        statistics from 2015
    min_occ : int, optional
        Minimal possible number of occupants per apartment (default: 1)
        Only relevant for method == 'equal'
    max_occ : int, optional
        Maximal possible number of occupants per apartment (default: 5)
        Only relevant for method == 'equal'

    Returns
    -------
    array_nb_occ : np.array (of ints)
        Numpy array holding number of occupants per apartment

    Reference
    ---------
    Statistisches Bundesamt (Destatis) (2017): Bevoelkerung in Deutschland.
    Online verfuegbar unter
    https://www.destatis.de/DE/ZahlenFakten/Indikatoren/LangeReihen/
    Bevoelkerung/lrbev05.html;jsessionid=4AACC10D2225591EC88C40EDEFB5EDAC.cae2,
    zuletzt geprueft am 05.04.2017.
    """
    assert method in ['equal', 'destatis']

    # list_nb_occ = []

    array_nb_occ = np.zeros(nb_samples)

    if method == 'equal':
        for i in range(nb_samples):
            curr_val = rd.randint(int(min_occ), int(max_occ))
            array_nb_occ[i] = curr_val

    elif method == 'destatis':
        for i in range(nb_samples):
            rand_nb = rd.randint(0, 100)

            #  Destatis values from 2015 about nb. of occupants per apartment
            if rand_nb <= 41.4:
                array_nb_occ[i] = 1
            elif rand_nb <= 41.4 + 34.2:
                array_nb_occ[i] = 2
            elif rand_nb <= 41.4 + 34.2 + 12.1:
                array_nb_occ[i] = 3
            elif rand_nb <= 41.4 + 34.2 + 12.1 + 9:
                array_nb_occ[i] = 4
            # elif rand_nb <= 41.4 + 34.2 + 12.1 + 9 + 3.2:
            else:
                array_nb_occ[i] = 5

    return array_nb_occ


def calc_sampling_el_demand_per_apartment(nb_samples, nb_persons, type,
                                          method='stromspiegel2017'):
    """
    Choose samples for electric energy demand, depending on nb_of_persons.

    Parameters
    ----------
    nb_samples : int
        Number of samples
    nb_persons : int
        Total number of persons within apartment
    type : str
        Residential building type
        Options:
        - 'sfh' : Single-family house
        - 'mfh' : Multi-family house
    method : str, optional
        Method to estimate electrical demand (default: 'stromspiegel2017')
        Options:
        - 'stromspiegel2017' : co2online Stromspiegel Deutschland 2017

    Returns
    -------
    array_el_demands : np.array (of floats)
        Numpy array holding annual electric demand values in kWh per apartment
    """

    assert type in ['sfh', 'mfh']
    assert method in ['stromspiegel2017']
    assert nb_persons > 0
    assert nb_persons <= 5

    # list_el_demands = []
    array_el_demands = np.zeros(nb_samples)

    if method == 'stromspiegel2017':
        #  Stromspiegel data for electric demand without hot water coverage
        dict_sfh = {1: [1300, 4000],
                    2: [2100, 4400],
                    3: [2600, 5200],
                    4: [2900, 5900],
                    5: [3500, 7500]}

        dict_mfh = {1: [800, 2200],
                    2: [1300, 3100],
                    3: [1700, 3900],
                    4: [1900, 4500],
                    5: [2200, 5700]}

        if type == 'sfh':
            use_dict = dict_sfh
        elif type == 'mfh':
            use_dict = dict_mfh

        # Select min. and max. possible value
        minv = use_dict[nb_persons][0]
        maxv = use_dict[nb_persons][1]

        for i in range(nb_samples):
            array_el_demands[i] = rd.randint(minv, maxv)

    return array_el_demands


def calc_sampling_dhw_per_person(nb_samples, pdf='equal', equal_diff=34,
                                 mean=64, std=10):
    """

    Perform domestic hot water sampling (hot water volume in liters per person
    and day; temperature split of 35 Kelvin, according to Annex 42 results).

    Parameters
    ----------
    nb_samples : int
        Number of samples
    pdf : str, optional
        Probability density function (default: 'equal')
        Options:
        'equal' : Equal distribution
        'gaussian' : Gaussian distribution
    equal_diff : float, optional
        Difference from mean within equal distribution (default: 34)
    mean : float, optional
        Mean domestic hot water volume per person and day in liter
        (default: 64)
    std : float, optional
        Standard deviation of domestic hot water volume per person and day
        in liter (default: 10)

    Returns
    -------
    array_dhw_vol : np.array (of floats)
        Numpy array of hot water volumes per person and day in liters
    """

    assert pdf in ['gaussian', 'equal']

    # list_dhw_vol = []
    array_dhw_vol = np.zeros(nb_samples)

    if pdf == 'gaussian':
        list_dhw_vol = np.random.normal(loc=mean, scale=std, size=nb_samples)
    elif pdf == 'equal':
        for i in range(nb_samples):
            array_dhw_vol[i] = rd.randint(int((mean - equal_diff) * 1000),
                                    int((mean + equal_diff) * 1000)) / 1000

    return array_dhw_vol


def calc_dhw_ref_volume_for_multiple_occ(nb_occ, ref_one_occ=64):
    """
    Calculate reference hot water volume demand per person, depending on number
    of occupants per apartment

    Parameters
    ----------
    nb_occ : int
        Number of occupants within apartment
    ref_one_occ : float, optional
        Reference hot water demand in liter per person and day (for single
        person apartment) (default: 64)

    Returns
    -------
    new_ref_dhw_per_occ : float
        Hot water volume per person and day
    """

    if nb_occ == 1:
        new_ref_dhw_per_occ = ref_one_occ + 0.0  # Use default mean value
    elif nb_occ == 2:
        new_ref_dhw_per_occ = ref_one_occ * 0.9375  # 64 --> 60 Liters
    elif nb_occ == 3:
        new_ref_dhw_per_occ = ref_one_occ * 0.9333  # 64 --> 57 Liters
    elif nb_occ == 4:
        new_ref_dhw_per_occ = ref_one_occ * 0.9298  # 64 --> 55 Liters
    elif nb_occ >= 5:
        new_ref_dhw_per_occ = ref_one_occ * 0.9259  # 64 --> 54 Liters

    return new_ref_dhw_per_occ


def calc_sampling_dhw_per_apartment(nb_samples, nb_persons,
                                    method='stromspiegel_2017', pdf='equal',
                                    equal_diff=34, mean=64, std=10,
                                    b_type='sfh', delta_t=35, c_p_water=4182,
                                    rho_water=995):
    """
    Perform domestic hot water sampling (hot water volume in liters per
    apartment and day; temperature split of 35 Kelvin, according to
    Annex 42 results). Assumes gaussian distribution.

    Parameters
    ----------
    nb_samples : int
        Number of samples
    nb_persons : int
        Number of persons
    method : str, optional
        Method to sample dhw volumina per person (default: 'nb_occ_dep')
        Options:
        'nb_occ_dep' : Dependend on number of occupants (reduced
        demand per person, if more persons are present)
        'indep' : Independent from total number of occupants
        'stromspiegel_2017' : Based on hot water consumption data of
        Stromspiegel 2017.
    pdf : str, optional
        Probability density function (default: 'equal')
        Options:
        'equal' : Equal distribution
        'gaussian' : Gaussian distribution
    mean : float, optional
        Mean domestic hot water volume per person and day in liter
        (default: 64)
    equal_diff : float, optional
        Difference from mean within equal distribution (default: 34)
    std : float, optional
        Standard deviation of domestic hot water volume per person and day
        in liter for gaussian distribution (default: 10)
    b_type : str, optional
        Building type (default: 'sfh')
        Options:
        - 'sfh' : Apartment is within single family house
        - 'mfh' : Apartment is within multi-family house
    delta_t : float, optional
        Temperature split of heated up water in Kelvin (default: 35)
    c_p_water : float, optional
        Specific heat capacity of water in J/kgK (default: 4182)
    rho_water : float, optional
        Density of water in kg/m3 (default: 995)

    Returns
    -------
    array_dhw_vol : np.array (of floats)
        Numpy array of hot water volumes per apartment and day in liters
    """

    assert method in ['nb_occ_dep', 'indep', 'stromspiegel_2017']
    assert pdf in ['equal', 'gaussian']
    assert b_type in ['sfh', 'mfh']

    # list_dhw_vol = []
    array_dhw_vol = np.zeros(nb_samples)

    if method == 'nb_occ_dep':
        #  Dhw consumption per occupants depends on total number of occupants

        #  Calculate new reference value for dhw volume per person and day
        #  depending on total number of occupants
        new_mean = calc_dhw_ref_volume_for_multiple_occ(nb_occ=nb_persons,
                                                        ref_one_occ=mean)

        for i in range(nb_samples):
            dhw_value = 0
            for p in range(nb_persons):
                dhw_value += \
                    calc_sampling_dhw_per_person(nb_samples=1,
                                                 mean=new_mean,
                                                 pdf=pdf,
                                                 equal_diff=equal_diff,
                                                 std=std)[0]
            array_dhw_vol[i] = dhw_value

    elif method == 'indep':
        #  Dhw consumpton per occupants is independend from total number of
        #  occupants

        for i in range(nb_samples):
            dhw_value = 0
            for p in range(nb_persons):
                dhw_value += \
                    calc_sampling_dhw_per_person(nb_samples=1,
                                                 mean=mean,
                                                 pdf=pdf,
                                                 equal_diff=equal_diff,
                                                 std=std)[0]
            array_dhw_vol[i] = dhw_value

    elif method == 'stromspiegel_2017':

        if nb_persons > 5:
            nb_persons = 5

        #  Dictionaries holding min/max dhw energy demand values in kWh per
        #  capital and year (for apartments)
        dict_sfh = {1: [200, 1000],
                    2: [400, 1400],
                    3: [400, 2100],
                    4: [600, 2100],
                    5: [700, 3400]}

        dict_mfh = {1: [400, 800],
                    2: [700, 1100],
                    3: [900, 1700],
                    4: [900, 2000],
                    5: [1300, 3300]}

        for i in range(nb_samples):
            if b_type == 'sfh':
                dhw_range = dict_sfh[nb_persons]
                dhw_energy = rd.randrange(start=dhw_range[0],
                                          stop=dhw_range[1])
            elif b_type == 'mfh':
                dhw_range = dict_mfh[nb_persons]
                dhw_energy = rd.randrange(start=dhw_range[0],
                                          stop=dhw_range[1])

            #  DHW volume in liter per apartment and day
            dhw_value = dhw_energy * 3600 * 1000 * 1000 \
                        / (rho_water * c_p_water * delta_t * 365)

            array_dhw_vol[i] = dhw_value

    return array_dhw_vol


def recalc_dhw_vol_to_energy(vol, delta_t=35, c_p_water=4182, rho_water=995):
    """
    Calculates hot water energy in kWh/a from input hot water volume in
    liters/apartment*day

    Parameters
    ----------
    vol : float
        Input hot water volume in liters/apartment*day
    delta_t : float, optional
        Temperature split of heated up water in Kelvin (default: 35)
    c_p_water : float, optional
        Specific heat capacity of water in J/kgK (default: 4182)
    rho_water : float, optional
        Density of water in kg/m3 (default: 995)

    Returns
    -------
    dhw_annual_kwh : float
        Annual hot water energy demand in kWh/a
    """

    en_per_day = vol / 1000 * rho_water * c_p_water * delta_t \
                 / (3600 * 1000) # in kWh
    dhw_annual_kwh = en_per_day * 365

    return dhw_annual_kwh


if __name__ == '__main__':

    nb_samples = 100000

    import matplotlib.pyplot as plt

    #  Get samples of set temperatures within building
    list_set_temp = calc_set_temp_samples(nb_samples=nb_samples)

    print('List of set temperatures in degree Celsius:')
    print(list_set_temp)
    print()


    fig = plt.figure()
    # the histogram of the data
    plt.hist(list_set_temp, bins='auto')
    plt.xlabel('Set temperatures in degree Celsius')
    plt.ylabel('Number of temperatures')
    plt.show()
    plt.close()

    #  Create constant user air exchange rates
    list_usr_airx = calc_user_air_ex_rates(nb_samples)

    print('List of user air exchange rates in 1/h:')
    print(list_usr_airx)
    print()

    fig = plt.figure()
    # the histogram of the data
    plt.hist(list_usr_airx, bins='auto')
    plt.xlabel('User air exchange rates in 1/h')
    plt.ylabel('Number of values')
    plt.show()
    plt.close()

    method = 'destatis'
    # method = 'equal'

    #  Sample number of occupants in apartments:
    list_occ_in_app = calc_sampling_occ_per_app(nb_samples=nb_samples,
                                                method=method)

    fig = plt.figure()
    # the histogram of the data
    plt.hist(list_occ_in_app, 5)
    plt.xlabel('Number of occupants per apartment')
    plt.ylabel('Number of values')
    plt.show()
    plt.close()

    #  Annual electric demand sampling per apartment (3 persons, SFH)
    list_el_dem = calc_sampling_el_demand_per_apartment(nb_samples=nb_samples,
                                                        nb_persons=3,
                                                        type='sfh')

    fig = plt.figure()
    # the histogram of the data
    plt.hist(list_el_dem, bins='auto')
    plt.xlabel('Number of electric energy demands in kWh')
    plt.ylabel('Number of values')
    plt.title('Electric energy demand for\napartment with '
              '3 occupants')
    plt.show()
    plt.close()

    list_el_dem_2 = []
    for nb_occ in list_occ_in_app:
        sample_el = \
            calc_sampling_el_demand_per_apartment(nb_samples=1,
                                                  nb_persons=nb_occ,
                                                  type='sfh')[0]
        list_el_dem_2.append(sample_el)

    fig = plt.figure()
    # the histogram of the data
    plt.hist(list_el_dem_2, bins='auto')
    plt.xlabel('Number of electric energy demands in kWh')
    plt.ylabel('Number of values')
    plt.title('Electric energy demand for\napartment with '
              'different number of occupants')
    plt.show()
    plt.close()

    # list_dhw = calc_sampling_dhw_per_person(nb_samples=nb_samples)
    #
    # fig = plt.figure()
    # # the histogram of the data
    # plt.hist(list_dhw, bins='auto')
    # plt.xlabel('Hot water volumes per person and day in liters')
    # plt.ylabel('Number of values')
    # plt.show()
    # plt.close()

    nb_persons = 5

    list_dhw_vol_per_app = \
        calc_sampling_dhw_per_apartment(nb_samples=nb_samples,
                                        nb_persons=nb_persons)

    fig = plt.figure()
    # the histogram of the data
    plt.hist(list_dhw_vol_per_app, bins='auto')
    plt.xlabel('Hot water volumes per apartment and day in liters')
    plt.ylabel('Number of values')
    plt.title('Hot water volumes per person and day for ' + str(nb_persons)
              + ' person apartment')
    plt.show()
    plt.close()

    list_dhw_per_app_2 = []
    for nb_occ in list_occ_in_app:
        sample_dhw = calc_sampling_dhw_per_apartment(nb_samples=1,
                                                     nb_persons=nb_occ)[0]
        list_dhw_per_app_2.append(sample_dhw)

    fig = plt.figure()
    # the histogram of the data
    plt.hist(list_dhw_per_app_2, bins='auto')
    plt.xlabel('Hot water volumes per apartment and day in liters')
    plt.ylabel('Number of values')
    plt.title('Hot water volumes per person and day for\napartment with '
              'different number of occupants')
    plt.show()
    plt.close()


    # #  Create environment
    # #  ####################################################################
    #
    # #  Create extended environment of pycity_calc
    # year = 2010
    # timestep = 3600  # Timestep in seconds
    # location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop
    # altitude = 55  # Altitude of Bottrop
    #
    # #  Generate timer object
    # timer = time.TimerExtended(timestep=timestep, year=year)
    #
    # #  Generate weather object
    # weather = Weather.Weather(timer, useTRY=True, location=location,
    #                           altitude=altitude)
    #
    # #  Generate market object
    # market = mark.Market()
    #
    # #  Generate co2 emissions object
    # co2em = co2.Emissions(year=year)
    #
    # #  Generate environment
    # environment = env.EnvironmentExtended(timer, weather, prices=market,
    #                                       location=location, co2em=co2em)
    #
    # #  #  Create occupancy profile
    # #  #####################################################################
    #
    # num_occ = 3
    #
    # print('Calculate occupancy.\n')
    # #  Generate occupancy profile
    # occupancy_obj = occ.Occupancy(environment, number_occupants=num_occ)
    #
    # print('Finished occupancy calculation.\n')

    # #  Generate user air exchange rate profiles
    # #  #####################################################################
    # list_air_ex_profiles = \
    #     calc_user_air_ex_profiles_factors(nb_samples=
    #                                       nb_samples,
    #                                       occ_profile=occupancy_obj.occupancy,
    #                                       temp_profile=
    #                                       environment.weather.tAmbient,
    #                                       random_gauss=True)
    #
    # list_av_air_ex_rates = []
    #
    # for profile in list_air_ex_profiles:
    #     plt.plot(profile, alpha=0.5)
    #
    #     av_rate = np.mean(profile)
    #
    #     print('Average air exchange rate in 1/h:')
    #     print(av_rate)
    #
    #     list_av_air_ex_rates.append(av_rate)
    #
    # plt.xlabel('Time in hours')
    # plt.ylabel('User air exchange rate in 1/h')
    # plt.show()
    # plt.close()
    #
    # fig2 = plt.figure()
    # # the histogram of the data
    # plt.hist(list_av_air_ex_rates, 50)
    # plt.xlabel('Average user air exchange rate in 1/h')
    # plt.ylabel('Number of air exchange rates')
    # plt.show()
    # plt.close()
