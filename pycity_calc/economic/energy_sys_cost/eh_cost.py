#!/usr/bin/env python
# coding=utf-8
"""
Script to estimate Electrical Heater cost
"""
from __future__ import division

import numpy as np
import matplotlib.pyplot as plt


def calc_spec_cost_eh(q_nom, method='spieker'):
    """
    Estimate electrical heater (EH) cost in Euro/kW, based on nominal thermal
    power (in kW)

    Parameters
    ----------
    q_nom : float
        Nominal thermal power of EH in kW
    method : str, optional
        Method for calculation of specific cost (default: 'spieker')
        Options:
        - 'spieker' (linearized cost function)
        Based on reference:
        S. Spieker, Dimensionierung von Mini-KWK-Anlagen zur Teilnahme am
        liberalisierten Strommarkt, Optimierung in der Energiewirtschaft 2011,
        VDI Berichte 2157 (2011).

    Returns
    -------
    spec_cost : float
        Specific cost of EH in Euro/kW
    """

    list_methods = ['spieker']

    assert method in list_methods, 'Unknown method'
    assert q_nom > 0, 'Nominal boiler power should be larger than zero!'

    if method == 'spieker':
        spec_cost = (245 + 19 * q_nom) / q_nom

    return spec_cost


def calc_abs_cost_eh(q_nom, method='spieker'):
    """
    Estimate electrical heater (EH) investment cost in Euro, based on nominal
    thermal power (in kW)

    Parameters
    ----------
    q_nom : float
        Nominal thermal power in kW
    method : str, optional
        Method for calculation of investment cost (default: 'spieker')
        Options:
        - 'spieker' (linearized cost function)
        Based on reference:
        S. Spieker, Dimensionierung von Mini-KWK-Anlagen zur Teilnahme am
        liberalisierten Strommarkt, Optimierung in der Energiewirtschaft 2011,
        VDI Berichte 2157 (2011).

    Returns
    -------
    eh_inv : float
        EH investment cost in Euro
    """

    spec_cost = calc_spec_cost_eh(q_nom=q_nom, method=method)

    return spec_cost * q_nom


if __name__ == '__main__':
    eh_size = 30000  # in Watt

    eh_kw = eh_size / 1000  # in kW

    #  Specific cost
    eh_spec_cost = calc_spec_cost_eh(q_nom=eh_kw)
    print('Specific EH cost in Euro/kW:')
    print(round(eh_spec_cost, 2))
    print()

    #  Investment cost
    inv_cost = calc_abs_cost_eh(q_nom=eh_kw)
    print('Investment cost of EH in Euro:')
    print(round(inv_cost, 2))
    print()

    array_ref_sizes = np.arange(1, 100, 1)  # in kW
    array_cost = np.zeros(len(array_ref_sizes))

    for i in range(len(array_ref_sizes)):
        size = array_ref_sizes[i]  # in kW
        array_cost[i] = calc_abs_cost_eh(q_nom=size)

    plt.plot(array_ref_sizes, array_cost)
    plt.xlabel('Heating power in kW')
    plt.ylabel('Capital cost of electric heater in Euro')
    plt.show()
    plt.close()
