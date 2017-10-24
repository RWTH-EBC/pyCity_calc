#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to sample parameters for energy systems
"""
from __future__ import division

import numpy as np


def sample_bat_self_disch(nb_samples, minv=0.00001, maxv=0.001):
    """
    Return samples of battery self discharging factor per capacity and timestep

    Parameters
    ----------
    nb_samples : int
        Number of samples
    minv : float
        Minimum value (default: 0.00001)
    maxv : float
        Maximum value (default: 0.001)

    Returns
    -------
    array_bat_self_disch : np.array (of float)
        Numpy array with battery self discharging factors
    """

    assert nb_samples > 0
    assert minv >= 0
    assert maxv >= 0

    array_bat_self_disch = \
        np.random.uniform(low=minv, high=maxv, size=nb_samples)

    return array_bat_self_disch


def sample_bat_eta_charge(nb_samples, mean=0.95, std=0.005):
    """
    Returns samples of battery charging efficiencies

    Parameters
    ----------
    nb_samples : int
        Number of samples
    mean : float, optional
        Mean value of efficiency (used as mean for normal distribution)
        (default: 0.95)
    std : float, optional
        Standard deviation for efficiency
        (default: 0.005)

    Returns
    -------
    array_bat_ch_eff : np.array (of floats)
        Numpy array holding samples of battery charging efficiencies
    """

    assert nb_samples > 0
    assert mean > 0
    assert std >= 0

    array_bat_ch_eff = np.random.normal(loc=mean, scale=std, size=nb_samples)

    for i in range(len(array_bat_ch_eff)):
        assert array_bat_ch_eff[i] <= 1

    return array_bat_ch_eff


def sample_bat_eta_discharge(nb_samples, mean=0.9, std=0.005):
    """
    Returns samples of battery discharging efficiencies

    Parameters
    ----------
    nb_samples : int
        Number of samples
    mean : float, optional
        Mean value of efficiency (used as mean for normal distribution)
        (default: 0.9)
    std : float, optional
        Standard deviation for efficiency
        (default: 0.005)

    Returns
    -------
    array_bat_disch_eff : np.array (of floats)
        Numpy array holding samples of battery discharging efficiencies
    """

    assert nb_samples > 0
    assert mean > 0
    assert std >= 0

    array_bat_disch_eff = np.random.normal(loc=mean, scale=std,
                                           size=nb_samples)

    for i in range(len(array_bat_disch_eff)):
        assert array_bat_disch_eff[i] <= 1

    return array_bat_disch_eff


def sample_boi_eff(nb_samples, mean=0.92, std=0.01):
    """
    Returns samples for boiler efficiency

    Parameters
    ----------
    nb_samples : int
        Number of samples
    mean : float, optional
        Mean value of efficiency
        (default: 0.92)
    std : float, optional
        Standard deviation of efficiency
        (default: 0.01)

    Returns
    -------
    array_boi_eff : np.array (of floats)
        Numpy array holding samples of boiler efficiencies
    """

    assert nb_samples > 0
    assert mean > 0
    assert std >= 0

    array_boi_eff = np.random.normal(loc=mean, scale=std,
                                     size=nb_samples)

    for i in range(len(array_boi_eff)):
        assert array_boi_eff[i] <= 1

    return array_boi_eff


def sample_chp_omega(nb_samples, mean=0.9, std=0.02):
    """
    Returns samples for chp overall efficiency

    Parameters
    ----------
    nb_samples : int
        Number of samples
    mean : float, optional
        Mean value of efficiency
        (default: 0.9)
    std : float, optional
        Standard deviation of efficiency
        (default: 0.02)

    Returns
    -------
    array_chp_eff : np.array (of floats)
        Numpy array holding samples of boiler efficiencies
    """

    assert nb_samples > 0
    assert mean > 0
    assert std >= 0

    array_chp_eff = np.random.normal(loc=mean, scale=std,
                                     size=nb_samples)

    for i in range(len(array_chp_eff)):
        assert array_chp_eff[i] <= 1

    return array_chp_eff


def sample_quality_grade_hp_bw(nb_samples, minv=0.45, maxv=0.55):
    """
    Returns samples for brine/water (or water/water) heat pump quality
    grades.

    Parameters
    ----------
    nb_samples : int
        Number of samples
    minv : float
        Minimum value (default: 0.45)
    maxv : float
        Maximum value (default: 0.55)

    Returns
    -------
    array_hp_bw_qual : np.array (of float)
        Numpy array with brine/water heat pump quality grade samples
    """

    assert nb_samples > 0
    assert minv >= 0
    assert maxv >= 0

    array_hp_bw_qual = \
        np.random.uniform(low=minv, high=maxv, size=nb_samples)

    return array_hp_bw_qual


def sample_quality_grade_hp_bw(nb_samples, minv=0.45, maxv=0.55):
    """
    Returns samples for brine/water (or water/water) heat pump quality
    grades.

    Parameters
    ----------
    nb_samples : int
        Number of samples
    minv : float
        Minimum value (default: 0.45)
    maxv : float
        Maximum value (default: 0.55)

    Returns
    -------
    array_hp_bw_qual : np.array (of float)
        Numpy array with brine/water heat pump quality grade samples
    """

    assert nb_samples > 0
    assert minv >= 0
    assert maxv >= 0

    array_hp_bw_qual = \
        np.random.uniform(low=minv, high=maxv, size=nb_samples)

    return array_hp_bw_qual


def sample_quality_grade_hp_aw(nb_samples, minv=0.32, maxv=0.4):
    """
    Returns samples for air/water heat pump quality grades

    Parameters
    ----------
    nb_samples : int
        Number of samples
    minv : float
        Minimum value (default: 0.32)
    maxv : float
        Maximum value (default: 0.4)

    Returns
    -------
    array_hp_aw_qual : np.array (of float)
        Numpy array with air/water heat pump quality grade samples
    """

    assert nb_samples > 0
    assert minv >= 0
    assert maxv >= 0

    array_hp_aw_qual = \
        np.random.uniform(low=minv, high=maxv, size=nb_samples)

    return array_hp_aw_qual


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    nb_samples = 1000

    array_ch_eff = sample_bat_eta_charge(nb_samples=nb_samples)

    plt.hist(array_ch_eff)
    plt.xlabel('Battery charging efficiency')
    plt.ylabel('Number of values')
    plt.show()
    plt.close()
