#!/usr/bin/env python
# coding=utf-8
"""
Script to estimate akm investment cost

Be aware of correct use of units!
"""
from __future__ import division

import warnings
import numpy as np
import matplotlib.pyplot as plt


def calc_spec_cost_akm(q_nom):
    """
    Estimate specific AKM cost in Euro/kW, based on nominal thermal power
    in kW.

    Parameters
    ----------
    q_nom : float
        Nominal thermal power of AKM in kW

    Returns
    -------
    spec_cost : float
        Specific cost of AKM in Euro/kW
    """
    if q_nom > 0:
        spec_cost = 5036.2 * ((q_nom) **(-0.487))

    else:
        warnings.warn('q_nom cannot be negative')

    return spec_cost


def calc_abs_akm_cost(q_nom):
    """
    Calculate absolute investment cost for akm (input for q_nom is kW)

    Parameters
    ----------
    q_nom : float
        Nominal thermal power of AKM in kW


    Returns
    -------
    akm_inv : float
        AKM investment cost in Euro
    """

    if q_nom > 0:
        spec_cost = calc_spec_cost_akm(q_nom=q_nom)
        akm_inv = spec_cost * q_nom

    else:
        warnings.warn('q_nom cannot be negative')

    return akm_inv


if __name__ == '__main__':
    akm_size = 40  # in kW

    #  Specific cost according to dbi
    spec_cost = calc_spec_cost_akm(q_nom=akm_size)
    abs = calc_abs_akm_cost(q_nom=akm_size)
    print('Specific AKM cost in Euro/kW:')
    print(round(spec_cost, 2))
    print('Sbsolut AKM cost in Euro:')
    print(round(abs, 2))
    print()

    array_ref_sizes = np.arange(1, 500, 1)  # in kW
    array_cost = np.zeros(len(array_ref_sizes))

    for i in range(len(array_ref_sizes)):
        size = array_ref_sizes[i]  # in kW
        array_cost[i] = calc_abs_akm_cost(q_nom=size)

    plt.plot(array_ref_sizes, array_cost, label='absolute costs')
    plt.legend()
    plt.show()
    plt.close()
