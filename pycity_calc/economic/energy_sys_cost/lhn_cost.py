#!/usr/bin/env python
# coding=utf-8
"""
Estimate cost into local heating network (LHN)

Cost are valid for pipe-combination of inlet and return flow. You do NOT
need to multiply the resulting cost with factor 2!
"""
from __future__ import division
import math
import warnings

import numpy as np
import matplotlib.pyplot as plt


def get_dn_cost_dict():
    """
    Returns di size (in mm) and specific cost dictionary (in Euro/m)
    Cost include cost for installation and ground/street renovation.

    Returns
    -------
    dict_dn_cost : dict
        Dictionary with di sizes (int; in mm) as keys and specific cost
        (float; in Euro/m) as values
    """

    #  di (size) and specific cost dictionary, based on
    #  http://www.leitfaden-nahwaerme.de/leitfaden/pop_kosten.html

    #  di in mm; spec cost in Euro/m
    dict_dn_cost = {27: 284.5,
                    43: 285,
                    55: 301,
                    70: 324.5,
                    83: 348.5,
                    107: 397,
                    133: 443,
                    160: 485}

    return dict_dn_cost


def calc_spec_cost_lhn(d, method='fraun'):
    """
    Estimate specific cost of pipe in Euro/m.
    Cost include cost for installation and ground/street renovation.

    Parameters
    ----------
    d : float
        (Inner-)Diameter of pipe in m
    method : str, optional
        Method to calculate cost (default: 'fraun')
        Options:
        - 'fraun'
        Based on:
        http://www.leitfaden-nahwaerme.de/leitfaden/pop_kosten.html

    Returns
    -------
    spec_cost_lhn : float
        Specific cost of pipe in Euro/m
    """

    assert method in ['fraun'], 'Unknown method. Check input.'

    assert d > 0, 'Diameter has to be larger than zero'

    if d > 1:
        msg = str('Diameter d of ' + str(d) + ' m seems to be very large.')
        warnings.warn(msg)

    #  Cost function estimated with values of
    #  http://www.leitfaden-nahwaerme.de/leitfaden/pop_kosten.html

    if method == 'fraun':
        spec_cost_lhn = 241.94 * math.exp(0.0044 * (d * 1000))  # d in mm

    return spec_cost_lhn


def calc_invest_single_lhn_station(q_nom):
    """
    Calculate investment cost into single LHN building connection station,
    related to:
    Konstantin - Praxisbuch Energiewirtschaft

    Parameters
    ----------
    q_nom : float
        Nominal thermal power / station connection value in kW

    Returns
    -------
    single_inv : float
        Investment cost into single LHN building connection station in Euro
    """

    assert q_nom > 0, 'q_nom has to be larger than zero.'
    if q_nom > 100:  # Larger 100 kW
        msg = str('Thermal power value of ' + str(q_nom) + ' kW seems to be'
                                                           ' to high.')
        warnings.warn(msg)

    return 5722.3 * math.exp(0.0015 * q_nom)


def calc_invest_cost_lhn_stations(list_powers):
    """
    Calculate the investment cost for LHN building connections related to
    Konstantin - Praxisbuch Energiewirtschaft

    Parameters
    ----------
    list_powers : list (of floats)
        List holding all max. thermal power connection values of buildings
        (in kW)

    Returns
    -------
    invest_lhn_stat : float
        Invest into LHN building connection stations in Euro
    """

    invest_lhn_stat = 0  # Dummy value

    for power in list_powers:
        invest_lhn_stat += calc_invest_single_lhn_station(q_nom=power)

    return invest_lhn_stat


def calc_invest_cost_lhn_pipes(d, length, method='fraun'):
    """
    Calculate investment cost of LHN.
    Cost include cost for installation and ground/street renovation.

    Parameters
    ----------
    d : float
        (Inner-)Diameter of pipe in m
    length : float
        Total network length (in m)
    method : str, optional
        Method to calculate cost (default: 'fraun')
        Options:
        - 'fraun'
        Based on:
        http://www.leitfaden-nahwaerme.de/leitfaden/pop_kosten.html

    Returns
    -------
    invest_lhn : float
        Investment cost in LHN in Euro
    """

    spec_lhn = calc_spec_cost_lhn(d=d, method=method)

    return spec_lhn * length


def calc_total_lhn_invest_cost(d, length, list_powers, method='fraun'):
    """
    Calculate total investment cost into LHN system
    (accounting for LHN pipes and transmittion stations)

    Parameters
    ----------
    d : float
        (Inner-)Diameter of pipe in m
    length : float
        Total network length (in m)
    list_powers : list (of floats)
        List holding all max. thermal power connection values of buildings
        (in kW)
    method : str, optional
        Method to calculate cost (default: 'fraun')
        Options:
        - 'fraun'
        Based on:
        http://www.leitfaden-nahwaerme.de/leitfaden/pop_kosten.html

    Returns
    -------
    lhn_total_invest : float
        LHN total investmetn cost in Euro
    """

    #  Calculate investment cost for LHN pipes
    pipe_invest = calc_invest_cost_lhn_pipes(d=d, length=length, method=method)

    #  Calculate investment cost for LHN transmittion stations
    station_invest = calc_invest_cost_lhn_stations(list_powers=list_powers)

    return pipe_invest + station_invest


if __name__ == '__main__':
    d = 0.05  # Diameter in m
    lhn_len = 100  # Length of LHN system in m

    list_q_nom = [10, 20, 15, 25]
    # List nominal th. powers in kW (per building)

    #  Calculate specific cost of LHN pipings
    spec_lhn_cost = calc_spec_cost_lhn(d=d)
    print('Specific LHN cost in Euro/m: ')
    print(round(spec_lhn_cost, 2))
    print()

    #  Calculate investment cost of LHN pipes
    invest_lhn_pip = calc_invest_cost_lhn_pipes(d=d, length=lhn_len)
    print('Investment cost of LHN pipes in Euro:')
    print(round(invest_lhn_pip, 2))
    print()

    #  Calculate LHN invest cost for transmission stations
    invest_trans = calc_invest_cost_lhn_stations(list_powers=list_q_nom)
    print('Investment cost of LHN transmision stations in Euro:')
    print(round(invest_trans, 2))
    print()

    #  Calculate total invest
    total_invest = calc_total_lhn_invest_cost(d=d, length=lhn_len,
                                              list_powers=list_q_nom)
    print('Total investment cost for LHN:')
    print(round(total_invest, 2))

    array_len = np.arange(1, 1000, 1)  # in m
    array_cost = np.zeros(len(array_len))
    for i in range(len(array_len)):
        size = array_len[i]  # in m
        array_cost[i] = calc_invest_cost_lhn_pipes(d=0.01, length=size) / 1000

    plt.plot(array_len, array_cost)
    plt.title('LHN network cost (d_i = 0.01 m)')
    plt.xlabel('LHN network length in m')
    plt.ylabel('Capital cost of LHN pipes in thousand-Euro')
    plt.show()
    plt.close()

    array_di = np.arange(0.01, 1, 0.01)  # in m
    array_cost = np.zeros(len(array_di))
    for i in range(len(array_di)):
        size = array_di[i]  # in m
        array_cost[i] = calc_invest_cost_lhn_pipes(d=size, length=100) / 1000

    plt.plot(array_di, array_cost)
    plt.title('LHN network cost (length = 100 m)')
    plt.xlabel('Inner diameter in m')
    plt.ylabel('Capital cost of LHN pipes in thousand-Euro')
    plt.show()
    plt.close()
