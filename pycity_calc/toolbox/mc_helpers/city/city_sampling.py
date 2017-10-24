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


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    nb_samples = 1000

    array_int = sample_interest(nb_samples=nb_samples)

    plt.hist(array_int)
    plt.xlabel('Interest rate')
    plt.ylabel('Number of values')
    plt.show()
    plt.close()
