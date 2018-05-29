#!/usr/bin/env python
# coding=utf-8
"""
Script to estimate kkm investment cost

Be aware of correct use of units!
"""
from __future__ import division

import warnings
import numpy as np
import matplotlib.pyplot as plt


def calc_spec_cost_kkm(q_nom):
    """
    Estimate specific KKM cost in Euro/kW, based on nominal thermal power
    in kW.

    Parameters
    ----------
    q_nom : float
        Nominal thermal power of KKM in kW

    Returns
    -------
    spec_cost : float
        Specific cost of KKM in Euro/kW
    """
    if q_nom > 0:
        spec_cost = 888.07 * ((q_nom) ** (-0.311))

    else:
        warnings.warn('q_nom cannot be negative')

    return spec_cost


def calc_abs_kkm_cost(q_nom):
    """
    Calculate absolute investment cost for kkm (input for q_nom is kW)

    Parameters
    ----------
    q_nom : float
        Nominal thermal power of KKM in kW


    Returns
    -------
    kkm_inv : float
        KKM investment cost in Euro
    """

    if q_nom > 0:
        spec_cost = calc_spec_cost_kkm(q_nom=q_nom)
        kkm_inv = spec_cost * q_nom

    else:
        warnings.warn('q_nom cannot be negative')

    return kkm_inv


if __name__ == '__main__':
    kkm_size = 40  # in kW

    #  Specific cost according to dbi
    spec_cost = calc_spec_cost_kkm(q_nom=kkm_size)
    abs = calc_abs_kkm_cost(q_nom=kkm_size)
    print('Specific KKM cost in Euro/kW:')
    print(round(spec_cost, 2))
    print('Sbsolut KKM cost in Euro:')
    print(round(abs, 2))
    print()

    array_ref_sizes = np.arange(1, 500, 1)  # in kW
    array_cost = np.zeros(len(array_ref_sizes))

    for i in range(len(array_ref_sizes)):
        size = array_ref_sizes[i]  # in kW
        array_cost[i] = calc_abs_kkm_cost(q_nom=size)

    plt.plot(array_ref_sizes, array_cost, label='absolute costs')
    plt.legend()
    plt.show()
    plt.close()
