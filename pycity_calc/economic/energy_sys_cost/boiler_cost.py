#!/usr/bin/env python
# coding=utf-8
"""
Script to estimate boiler investment cost

Be aware of correct use of units!
"""
from __future__ import division

import warnings
import numpy as np
import matplotlib.pyplot as plt


def calc_spec_cost_boiler(q_nom, method='buderus2017'):
    """
    Estimate specific boiler cost in Euro/kW, based on nominal thermal power
    in kW.

    Parameters
    ----------
    q_nom : float
        Nominal thermal power of boiler in kW
    method : str, optional
        Method for calculation of specific cost (default: 'buderus2017')
        Options:
        - 'dbi'
        Based on reference:
        http://www.dbi-gut.de/fileadmin/downloads/3_Veroeffentlichungen/Gaswritschaftlicher_Beirat/2011/110418_Abschlussbericht_Modernisierung-Vorwaemanlagen.pdf>
        - 'viess2013'
        Based on viessmann 2013 cost curves
        - 'spieker' (linearized cost function)
        Based on reference:
        S. Spieker, Dimensionierung von Mini-KWK-Anlagen zur Teilnahme am
        liberalisierten Strommarkt, Optimierung in der Energiewirtschaft 2011,
        VDI Berichte 2157 (2011).
        - 'buderus2017': Based on Buderus price lists
        https://www.buderus.com/ch/media/documents/buderus-preislisten/buderus-preislisten-waermeerzeuger-de/kk_de_02.pdf

    Returns
    -------
    spec_cost : float
        Specific cost of boiler in Euro/kW
    """

    list_methods = ['dbi', 'viess2013', 'spieker', 'buderus2017']

    assert method in list_methods, 'Unknown method'
    assert q_nom > 0, 'Nominal boiler power should be larger than zero!'

    if method == 'dbi':

        spec_cost = 412.85 * q_nom ** (-0.339)

    elif method == 'viess2013':

        spec_cost = 3507.7 * q_nom ** (-0.906)

    elif method == 'spieker':

        spec_cost = (3100 + q_nom * 62) / q_nom

    elif method == 'buderus2017':

        spec_cost = 549.29 * q_nom ** (-0.369)

    return spec_cost


def calc_abs_boiler_cost(q_nom, method='buderus2017'):
    """
    Calculate absolute investment cost for boiler (input for q_nom is kW)

    Parameters
    ----------
    q_nom : float
        Nominal thermal power of boiler in kW
    method : str, optional
        Method for calculation of investement cost (default: 'buderus2017')
        Options:
        - 'dbi'
        Based on reference:
        http://www.dbi-gut.de/fileadmin/downloads/3_Veroeffentlichungen/Gaswritschaftlicher_Beirat/2011/110418_Abschlussbericht_Modernisierung-Vorwaemanlagen.pdf>
        - 'viess2013'
        Based on viessmann 2013 cost curves
        - 'spieker' (linearized cost function)
        Based on reference:
        S. Spieker, Dimensionierung von Mini-KWK-Anlagen zur Teilnahme am
        liberalisierten Strommarkt, Optimierung in der Energiewirtschaft 2011,
        VDI Berichte 2157 (2011).
        - 'buderus2017': Based on Buderus price lists
        https://www.buderus.com/ch/media/documents/buderus-preislisten/buderus-preislisten-waermeerzeuger-de/kk_de_02.pdf


    Returns
    -------
    boiler_inv : float
        Boiler investment cost in Euro
    """

    if method == 'viess2013':
        if q_nom > 75:
            msg = 'Your nominal boiler th. power is ' + \
                  str(q_nom) + ' kW. The method viess2013 might lead to an ' \
                               'underestimation of capital cost for this ' \
                               'boiler! Consider changing the boiler_cost ' \
                               'method!'
            warnings.warn(msg)

    spec_cost = calc_spec_cost_boiler(q_nom=q_nom, method=method)

    return spec_cost * q_nom


if __name__ == '__main__':
    boiler_size = 40000  # in Watt

    boiler_kW = boiler_size / 1000

    #  Specific cost according to dbi
    dbi_spec_cost = calc_spec_cost_boiler(q_nom=boiler_kW, method='dbi')
    dbi_abs = calc_abs_boiler_cost(q_nom=boiler_kW, method='dbi')
    print('DBI specific boiler cost in Euro/kW:')
    print(round(dbi_spec_cost, 2))
    print('DBI absolut boiler cost in Euro:')
    print(round(dbi_abs, 2))
    print()

    #  Specific cost according to Viessmann 2013
    viess_spec_cost = \
        calc_spec_cost_boiler(q_nom=boiler_kW, method='viess2013')
    viess_abs = calc_abs_boiler_cost(q_nom=boiler_kW, method='viess2013')
    print('Viessmann specific boiler cost in Euro/kW:')
    print(round(viess_spec_cost, 2))
    print('Viessmann absolut boiler cost in Euro:')
    print(round(viess_abs, 2))
    print()

    #  Specific cost according to Spieker et al.
    spiek_spec_cost = \
        calc_spec_cost_boiler(q_nom=boiler_kW, method='spieker')
    spiek_abs = calc_abs_boiler_cost(q_nom=boiler_kW, method='spieker')
    print('Spieker et al. specific boiler cost in Euro/kW:')
    print(round(spiek_spec_cost, 2))
    print('Spieker et al.  absolut boiler cost in Euro:')
    print(round(spiek_abs, 2))
    print()

    #  Specific cost according to Buderus 2017
    spiek_spec_cost = \
        calc_spec_cost_boiler(q_nom=boiler_kW, method='buderus2017')
    spiek_abs = calc_abs_boiler_cost(q_nom=boiler_kW, method='buderus2017')
    print('buderus2017 specific boiler cost in Euro/kW:')
    print(round(spiek_spec_cost, 2))
    print('buderus2017 absolut boiler cost in Euro:')
    print(round(spiek_abs, 2))
    print()

    array_ref_sizes = np.arange(1, 500, 1)  # in kW
    array_cost_dbi = np.zeros(len(array_ref_sizes))
    array_cost_viess = np.zeros(len(array_ref_sizes))
    array_cost_spiek = np.zeros(len(array_ref_sizes))
    array_cost_buderus = np.zeros(len(array_ref_sizes))

    for i in range(len(array_ref_sizes)):
        size = array_ref_sizes[i]  # in kW
        array_cost_dbi[i] = calc_abs_boiler_cost(q_nom=size, method='dbi')
        array_cost_viess[i] = calc_abs_boiler_cost(q_nom=size,
                                                   method='viess2013')
        array_cost_spiek[i] = calc_abs_boiler_cost(q_nom=size,
                                                   method='spieker')
        array_cost_buderus[i] = calc_abs_boiler_cost(q_nom=size,
                                                     method='buderus2017')

    plt.plot(array_ref_sizes, array_cost_dbi, label='dbi')
    plt.plot(array_ref_sizes, array_cost_viess, label='viess2013')
    plt.plot(array_ref_sizes, array_cost_spiek, label='spieker')
    plt.plot(array_ref_sizes, array_cost_buderus, label='buderus2017')
    plt.legend()
    plt.show()
    plt.close()
