#!/usr/bin/env python
# coding=utf-8
"""
Script to generate uncertain sets of building/building physics uncertain
parameters
"""

import math
import random as rd
import numpy as np
import matplotlib.pyplot as plt


def calc_list_mod_years_single_build(nb_samples, year_of_constr, max_year,
                                     time_sp_force_retro=40):
    """
    Calculate list of modification years for single building. Assumes
    equal distribution of mod. year probability density function.
    If time_sp_force_retro is set and smaller than time span between max_year
    (e.g. current year) and year_of_constr (year of construction), time span
    is only considered between max_year and (max_year - time_sp_force_retro).
    This should guarantee, that at least on modernization happened in the span
    of time_sp_force_retro.

    Parameters
    ----------
    nb_samples : int
        Number of samples
    year_of_constr : int
        Year of construction of building
    max_year : int
        Last possible year of retrofit (e.g. current year)
        Should be larger than year_of_constr
    time_sp_force_retro : int, optional
        Timespan to force retrofit (default: 40). If value is set, forces
        retrofit within its time span. If set to None, time span is not
        considered.

    Returns
    -------
    list_mod_years : list (of ints)
        List of modernization years.
    """

    list_mod_years = []

    #  Currently unused: List with TEASER years of modernization
    list_teaser_mod_y = [1982, 1995, 2002, 2009]

    #  Calc min_year
    if time_sp_force_retro is not None:
        if max_year - year_of_constr > time_sp_force_retro:
            min_year = int(max_year - time_sp_force_retro)
        else:
            min_year = int(year_of_constr + 1)
    else:
        min_year = int(year_of_constr + 1)

    # Do sampling
    for i in range(nb_samples):
        chosen_year = rd.randint(min_year, max_year)

        list_mod_years.append(chosen_year)

    return list_mod_years


def calc_inf_samples(nb_samples, mean=0, sdev=1, max_val=2):
    """
    Performs building infiltration rate sampling based on log normal
    distribution.
    Reset values larger than max_val to 0.26 (1/h, average value)

    Parameters
    ----------
    nb_samples : int
        Number of samples
    mean : float, optional
        Mean of log normal distribution (default: 0)
    sdev : float, optional
        Standard deviation of log normal distribution (default: 1)
    max_val : float, optional
        Maximal allowed value for natural infiltration rate (default: 2)

    Returns
    -------
    list_inf : list (of floats)
        List of infiltration rates in 1/h

    References
    ----------
    For reference values:
    Münzenberg, Uwe (2004): Der natürliche Luftwechsel in Gebäuden und seine
    Bedeutung bei der Beurteilung von Schimmelpilzschäden. In: Umwelt,
    Gebäude & Gesundheit: Innenraumhygiene, Raumluftqualität und
    Energieeinsparung. Ergebnisse des 7, S. 263–271.
    """
    list_inf = np.random.lognormal(mean=mean, sigma=sdev, size=nb_samples)

    list_inf /= 6

    #  Reset values larger than 2 to 0.26
    for i in range(len(list_inf)):
        if list_inf[i] > max_val:
            list_inf[i] = 0.26

    return list_inf


def calc_sh_demand_samples(nb_samples, sh_ref, norm_std=0.5791):
    """
    Calculate space heating demand samples in kWh/a, based on Aachen
    space heating demand uncertainty analysis.
    Sampling values below zero are set to zero demand!

    Parameters
    ----------
    nb_samples : int
        Number of samples
    sh_ref : float
        Reference space heating demand in kWh/a. Used as mean value!
    norm_std : float, optional
        Normalized standard deviation (default. 0.5791). Results of
        Aachen space heating demand uncertainty analysis (#239)

    Returns
    -------
    array_sh : array (of floats)
        Array with space heating demand samples in kWh/a for each sample
    """

    array_sh = np.random.normal(loc=sh_ref, scale=norm_std * sh_ref,
                               size=nb_samples)

    for i in range(len(array_sh)):
        if array_sh[i] < 0:
            array_sh[i] = 0

    return array_sh





def calc_list_net_floor_area_sampling(mean, sigma, nb_of_samples):
    """

    Parameters
    ----------
    mean
    sigma
    nb_of_samples

    Returns
    -------

    """

    list_of_net_floor_area = np.random.normal(loc=mean, scale=sigma,
                                              size=nb_of_samples)

    return list_of_net_floor_area


def calc_list_dormer_samples(nb_samples):
    """
     Performs building component sampling based on uniform distribution
    distribution.

    Parameters:
        nb samples: int
        Number of samples

    Returns:    tuples of integers lists
                list_dormer,list_attic,list_cellar,list_const

    """

    list_dormer = np.random.random_integers(0, 1, size=nb_samples)
    # 0: No dormer
    # 1: Dormer

    list_attic = np.random.random_integers(0, 3, size=nb_samples)
    # 0: no attic
    # 1: Roof no n heated
    # 2: Roof partially heated
    # 3: Roof fully heated

    list_cellar = np.random.random_integers(0, 3, size=nb_samples)
    # 0: No basement
    # 1: Non heated cellar
    # 2: Partially heated basement
    # 3: Fully heated cellar

    list_const = np.random.random_integers(0, 1, size=nb_samples)
    # 0: heavy construction
    # 1: light construction

    return list_dormer, list_attic, list_cellar, list_const


if __name__ == '__main__':

    nb_samples = 10000
    year_of_constr = 1960
    max_year = 2016
    time_sp_force_retro = 40

    #  Calculate modernization years
    list_mod = calc_list_mod_years_single_build(nb_samples=nb_samples,
                                                year_of_constr=year_of_constr,
                                                max_year=max_year,
                                                time_sp_force_retro=
                                                time_sp_force_retro)

    print('List of modernization years for single building')
    print(list_mod)

    #  Plausibility checks
    for year in list_mod:
        assert year > year_of_constr
        assert year <= max_year
        if time_sp_force_retro is not None:
            assert year >= (max_year - time_sp_force_retro)

    fig = plt.figure()
    plt.hist(x=list_mod)
    plt.xlabel('Modernization year')
    plt.ylabel('Number of years')
    plt.show()
    plt.close()

    #  Calculate infiltration rates
    #  ################################################################
    list_inf = calc_inf_samples(nb_samples=nb_samples)

    #  Infiltration rate analysis
    #  ################################################################

    print('List of infiltration rate values in 1/h:')
    print(list_inf)
    print()

    print('Average infiltration rate:')
    print(sum(list_inf) / len(list_inf))

    below_05 = 0
    below_04 = 0
    below_018 = 0
    below_01 = 0

    for inf in list_inf:
        if inf <= 0.5:
            below_05 += 1
        if inf <= 0.4:
            below_04 += 1
        if inf <= 0.18:
            below_018 += 1
        if inf <= 0.1:
            below_01 += 1

    # Reference Muenzberg
    #  20 % below 0.1
    #  50 % below 0.18
    #  85 % below 0.4
    #  90 % unter 0.5

    print('Share of buildings with air exchange below 0.1 1/h in %:')
    print(below_01 * 100 / len(list_inf))
    print('Reference: 20 %')
    print()

    print('Share of buildings with air exchange below 0.18 1/h in %:')
    print(below_018 * 100 / len(list_inf))
    print('Reference: 50 %')
    print()

    print('Share of buildings with air exchange below 0.4 1/h in %:')
    print(below_04 * 100 / len(list_inf))
    print('Reference: 85 %')
    print()

    print('Share of buildings with air exchange below 0.5 1/h in %:')
    print(below_05 * 100 / len(list_inf))
    print('Reference: 90 %')
    print()

    print('Max. value of air exchange rate:')
    print(max(list_inf))

    import matplotlib.pyplot as plt

    count, bins, ignored = plt.hist(list_inf, bins='auto')
    # x = np.linspace(min(bins), max(bins), 10000)
    # pdf = (np.exp(-(np.log(x) - mean) ** 2 / (2 * sdev ** 2)) /
    #        (x * sdev * np.sqrt(2 * np.pi)))
    # plt.plot(x, pdf, linewidth=2, color='r')
    plt.xlabel('Infiltration rate in 1/h')
    plt.ylabel('Number of values')
    plt.axis('tight')
    plt.show()
    plt.close()

    #  SH demand sampling
    #  ##################################################################
    sh_ref = 10000  # kWh/a

    list_sh = calc_sh_demand_samples(nb_samples=nb_samples, sh_ref=sh_ref)

    # list_sh_ref = np.random.lognormal(mean=1, sigma=1.068623577, size=nb_samples)

    count, bins, ignored = plt.hist(list_sh, bins='auto')
    plt.hist(list_sh, bins='auto')
    # plt.hist(list_sh_ref, bins='auto')
    plt.xlabel('Space heating demand in kWh/a')
    plt.ylabel('Number of values')
    plt.axis('tight')
    plt.show()
    plt.close()



    # #   Building components
    # #  ################################################################
    #
    # list_dormer, list_attic, list_cellar, list_const = calc_list_dormer_samples(
    #     nb_samples)
    #
    # fig2, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2)
    # ax1.hist(x=list_dormer)
    # ax1.set_title('Dormer')
    # ax2.hist(x=list_attic)
    # ax2.set_title('Attic')
    # ax3.hist(x=list_cellar)
    # ax3.set_title('Cellar')
    # ax4.hist(x=list_const)
    # ax4.set_title('Construction type')
    # plt.show()
    # plt.close()
    #
    # #   Net floor area sampling analysis
    # #  ################################################################
    #
    # list_net_floor_area = \
    #     calc_list_net_floor_area_sampling(mean=500,
    #                                       sigma=0.5,
    #                                       nb_of_samples=nb_samples)
    #
    # plt.hist(list_net_floor_area)
    # plt.xlabel('Net floor area sampling')
    # plt.show()
    # plt.close()
