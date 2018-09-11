#!/usr/bin/env python
# coding=utf-8
"""
Script to estimate cost of electric batteries
"""
from __future__ import division

import numpy as np
import matplotlib.pyplot as plt

def calc_spec_cost_bat(cap, method='sma'):
    """
    Calculate specific battery cost in Euro / kWh.

    Parameters
    ----------
    cap : float
        Capacity of battery in kWh
    method : str, optional
        Method for calculation (default: 'sma')
        Options:
        - 'carmen'
        based on:
        Centrales Agrar-Rohstoff Marketing- und Energie-Netzwerk,
        Marktübersicht Batteriespeicher, 2015.
        - 'sma' (#81)
        based on:
        http://www.photovoltaik4all.de/pv-strompeicher-kaufen-als-komplettset
        Discrete values have been fitted into potential function

    Returns
    -------
    spec_bat : float
        Specific cost of battery in
    """

    assert cap > 0, 'Capacity has to be larger than zero.'
    assert method in ['carmen', 'sma'], 'Unknown method'

    if method == 'carmen':
        spec_bat = (5000 + 1225 * cap) / cap
    elif method == 'sma':
        spec_bat = 2094.9 * (cap ** -0.521)

    return spec_bat

def calc_invest_cost_bat(cap, method='sma'):
    """
    Calculate investment cost of electric batteries in Euro.

    Parameters
    ----------
    cap : float
        Capacity of battery in kWh
    method : str, optional
        Method for calculation (default: 'sma')
        Options:
        - 'carmen'
        based on:
        Centrales Agrar-Rohstoff Marketing- und Energie-Netzwerk,
        Marktübersicht Batteriespeicher, 2015.
        - 'sma' (#81)
        based on:
        http://www.photovoltaik4all.de/pv-strompeicher-kaufen-als-komplettset
        Discrete values have been fitted into potential function

    Returns
    -------
    invest_bat : float
        Investment cost for battery in Euro
    """

    #  Calculate specific cost of battery
    spec_cost = calc_spec_cost_bat(cap=cap, method=method)

    return cap * spec_cost


if __name__ == '__main__':

    bat_cap = 5  # kWh
    list_methods = ['sma', 'carmen']

    for method in list_methods:
        #  Calculate specific cost for battery
        spec_cost = calc_spec_cost_bat(cap=bat_cap, method=method)
        print('Specific cost for battery in Euro/kWh (method ' +
              str(method) +'):')
        print(round(spec_cost, 2))
        print()

    print('##################################')
    for method in list_methods:
        #  Calculate investment cost for battery
        inv_cost = calc_invest_cost_bat(cap=bat_cap, method=method)
        print('Investment cost for battery in Euro (method '
              + str(method) +'):')
        print(round(inv_cost, 2))
        print()

    array_in = np.arange(start=1, stop=20, step=1)

    array_out = np.zeros(len(array_in))
    array_out2 = np.zeros(len(array_in))

    for i in range(len(array_in)):
        power = array_in[i]
        array_out[i] = calc_invest_cost_bat(cap=power, method='carmen')
        array_out2[i] = calc_invest_cost_bat(cap=power, method='sma')

    plt.plot(array_in, array_out, label='carmen')
    plt.plot(array_in, array_out2, label='sma')
    plt.xlabel('Electric capacity in kWh')
    plt.ylabel('Investment in Euro')
    plt.legend()
    plt.show()
    plt.close()
