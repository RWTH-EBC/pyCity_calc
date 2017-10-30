#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to generate samples for economic calculation
"""
from __future__ import division

import numpy as np


def sample_interest(nb_samples, minval=1.01, maxval=1.0675):
    """
    Returns array of interest rate samples

    Parameters
    ----------
    nb_samples : int
        Number of samples
    minval : float, optional
        Minimal possible interest rate (default: 1.01)
    maxval : float, optional
        Maximal possible interest rate (default: 1.0675)

    Returns
    -------
    array_interest : np.array
        Array with interest rate samples
    """

    assert nb_samples > 0

    array_interest = np.random.uniform(low=minval, high=maxval,
                                       size=nb_samples)

    return array_interest


def sample_price_ch_cap(nb_samples, minval=1.0, maxval=1.0575):
    """
    Returns samples for price change rates on capital

    Parameters
    ----------
    nb_samples : int
        Number of samples
    minval : float, optional
        Minimal value (default: 1.0)
    maxval : float, optional
        Maximal value (default: 1.0575)

    Returns
    -------
    array_ch_cap : np.array (of floats)
        Numpy array holding price change rate samples for capital
    """

    assert nb_samples > 0

    array_ch_cap = np.random.uniform(low=minval, high=maxval,
                                     size=nb_samples)

    return array_ch_cap


def sample_price_ch_dem_gas(nb_samples, minval=0.96, maxval=1.06):
    """
    Returns samples for price change rates on demand related cost for gas

    Parameters
    ----------
    nb_samples : int
        Number of samples
    minval : float, optional
        Minimal value (default: 0.96)
    maxval : float, optional
        Maximal value (default: 1.06)

    Returns
    -------
    array_ch_dem_gas : np.array (of floats)
        Numpy array holding price change rate samples for demand related cost
        for gas
    """

    assert nb_samples > 0

    array_ch_dem_gas = np.random.uniform(low=minval, high=maxval,
                                         size=nb_samples)

    return array_ch_dem_gas


def sample_price_ch_dem_el(nb_samples, minval=0.98, maxval=1.1):
    """
    Returns samples for price change rates for demand related cost on
    electricity

    Parameters
    ----------
    nb_samples : int
        Number of samples
    minval : float, optional
        Minimal value (default: 0.98)
    maxval : float, optional
        Maximal value (default: 1.1)

    Returns
    -------
    array_ch_dem_el : np.array (of floats)
        Numpy array holding price change rate samples for demand related cost
        for electricity
    """

    assert nb_samples > 0

    array_ch_dem_el = np.random.uniform(low=minval, high=maxval,
                                        size=nb_samples)

    return array_ch_dem_el


def sample_price_ch_op(nb_samples, minval=1, maxval=1.0575):
    """
    Returns samples for price change rates for operation related cost

    Parameters
    ----------
    nb_samples : int
        Number of samples
    minval : float, optional
        Minimal value (default: 1)
    maxval : float, optional
        Maximal value (default: 1.0575)

    Returns
    -------
    array_ch_op : np.array (of floats)
        Numpy array holding price change rate samples for operation
        related cost
    """

    assert nb_samples > 0

    array_ch_op = np.random.uniform(low=minval, high=maxval,
                                    size=nb_samples)

    return array_ch_op


def sample_price_ch_eeg_chp(nb_samples, minval=0.98, maxval=1.02):
    """
    Returns samples for price change rates for CHP EEG payment

    Parameters
    ----------
    nb_samples : int
        Number of samples
    minval : float, optional
        Minimal value (default: 0.98)
    maxval : float, optional
        Maximal value (default: 1.02)

    Returns
    -------
    array_ch_eeg_chp : np.array (of floats)
        Numpy array holding price change rate samples for CHP EEG payment
    """

    assert nb_samples > 0

    array_ch_eeg_chp = np.random.uniform(low=minval, high=maxval,
                                         size=nb_samples)

    return array_ch_eeg_chp


def sample_price_ch_eeg_pv(nb_samples, minval=0.98, maxval=1.02):
    """
    Returns samples for price change rates for PV EEG payment

    Parameters
    ----------
    nb_samples : int
        Number of samples
    minval : float, optional
        Minimal value (default: 0.98)
    maxval : float, optional
        Maximal value (default: 1.02)

    Returns
    -------
    array_ch_eeg_pv : np.array (of floats)
        Numpy array holding price change rate samples for PV EEG payment
    """

    assert nb_samples > 0

    array_ch_eeg_pv = np.random.uniform(low=minval, high=maxval,
                                        size=nb_samples)

    return array_ch_eeg_pv


def sample_price_ch_eex(nb_samples, minval=0.94, maxval=1.02):
    """
    Returns samples for price change rates for EEX baseload price

    Parameters
    ----------
    nb_samples : int
        Number of samples
    minval : float, optional
        Minimal value (default: 0.94)
    maxval : float, optional
        Maximal value (default: 1.02)

    Returns
    -------
    array_ch_eex : np.array (of floats)
        Numpy array holding price change rate samples for EEX baseload price
    """

    assert nb_samples > 0

    array_ch_eex = np.random.uniform(low=minval, high=maxval,
                                     size=nb_samples)

    return array_ch_eex


def sample_price_ch_grid_use(nb_samples, minval=0.98, maxval=1.04):
    """
    Returns samples for price change rates for grid usage fee

    Parameters
    ----------
    nb_samples : int
        Number of samples
    minval : float, optional
        Minimal value (default: 0.98)
    maxval : float, optional
        Maximal value (default: 1.04)

    Returns
    -------
    array_ch_grid_use : np.array (of floats)
        Numpy array holding price change rate samples for grid usage fee
    """

    assert nb_samples > 0

    array_ch_grid_use = np.random.uniform(low=minval, high=maxval,
                                          size=nb_samples)

    return array_ch_grid_use


def sample_grid_av_fee(nb_samples, minval=0.0001, maxval=0.015):
    """
    Returns samples for grid usage avoidance fee in Euro/kWh

    Parameters
    ----------
    nb_samples : int
        Number of samples
    minval : float, optional
        Minimal value (default: 0.0001)
    maxval : float, optional
        Maximal value (default: 0.015)

    Returns
    -------
    array_grid_av_fee : np.array (of floats)
        Numpy array holding samples for grid usage avoicance fee
    """

    assert nb_samples > 0

    array_grid_av_fee = np.random.uniform(low=minval, high=maxval,
                                          size=nb_samples)

    return array_grid_av_fee


def sample_temp_ground(nb_samples, minval=8, maxval=12):
    """
    Returns samples for ground temperature in degree Celsius (relevant for
    LHN loss estimation)

    Parameters
    ----------
    nb_samples : int
        Number of samples
    minval : float, optional
        Minimal value (default: 8)
    maxval : float, optional
        Maximal value (default: 12)

    Returns
    -------
    array_temp_ground : np.array (of floats)
        Numpy array holding price change rate samples for grid usage fee
    """

    assert nb_samples > 0

    array_temp_ground = np.random.uniform(low=minval, high=maxval,
                                          size=nb_samples)

    return array_temp_ground


def sample_quota_summer_heat_on(nb_samples, minval=0, maxval=1):
    """
    Returns sample array with ratios of buildings where heating is activated
    during summer.

    Parameters
    ----------
    nb_samples : int
        Number of samples
    minval : float, optional
        Minimal possible interest rate (default: 0)
    maxval : float, optional
        Maximal possible interest rate (default: 1)

    Returns
    -------
    array_interest : np.array
        Array with interest rate samples
    """

    assert nb_samples > 0

    lowv = minval * 100
    highv = maxval * 100

    array_interest = np.random.\
                         randint(low=lowv, high=highv, size=nb_samples) / 100

    return array_interest


def sample_ids_houses_summer_on(ratio_on, list_b_ids):
    """
    Returns array with samples of list of building ids, which use heating
    during summer. Length of output array is defined by ratio_on and
    list_b_ids length (Length represents number of buildings with heating
    during summer)

    Parameters
    ----------
    ratio_on : float
        Ratio of buildings with activated heating during summer
        (e.g. ratio_on = 0.4 --> 40 % of buildings have heating activated
        during summer)
    list_b_ids : list (of ints)
        List of building node ids

    Returns
    -------
    array_heat_ids : np.array (of lists of ints)
        Numpy array with list holding all buildings node ids, which have
        summer heating mode on.
    """

    assert ratio_on >= 0
    assert ratio_on <= 1

    nb_buildings = len(list_b_ids)

    nb_build_heat = int(round(nb_buildings * ratio_on, ndigits=0))

    array_heat_ids = np.random.choice(a=list_b_ids, size=nb_build_heat,
                                      replace=False)

    return array_heat_ids


def sample_list_sum_heat_on_arrays(nb_samples, ratio_on, list_b_ids):
    """
    Returns list with arrays holding building node ids for each run

    Parameters
    ----------
    nb_samples : int
        Number of samples
    ratio_on : float
        Ratio of buildings with activated heating during summer
        (e.g. ratio_on = 0.4 --> 40 % of buildings have heating activated
        during summer)
    list_b_ids : list (of ints)
        List of building node ids

    Returns
    -------
    list_sum_heat_id_arrays : list (of np.arrays)
        List holding arrays with building node ids with heating during summer
    """

    list_sum_heat_id_arrays = []

    for i in range(nb_samples):
        array_ids = sample_ids_houses_summer_on(ratio_on=ratio_on,
                                                list_b_ids=list_b_ids)
        list_sum_heat_id_arrays.append(array_ids)

    return list_sum_heat_id_arrays


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    nb_samples = 1000

    array_int = sample_interest(nb_samples=nb_samples)

    plt.hist(array_int)
    plt.xlabel('Interest rate')
    plt.ylabel('Number of values')
    plt.show()
    plt.close()

    # array_heat_ids = sample_ids_houses_summer_on(ratio_on=1,
    #                             list_b_ids=[1001, 1002, 1003, 1004, 1005,
    #                                         1006, 1007, 1008, 1009, 1010])
    #
    # print('Len: ', len(array_heat_ids))
    # print(array_heat_ids)