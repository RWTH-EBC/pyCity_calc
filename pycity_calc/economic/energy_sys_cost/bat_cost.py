#!/usr/bin/env python
# coding=utf-8
"""
Script to estimate cost of electric batteries
"""


def calc_spec_cost_bat(cap, method='carmen'):
    """
    Calculate specific battery cost in Euro / kWh.

    Parameters
    ----------
    cap : float
        Capacity of battery in kWh
    method : str, optional
        Method for calculation (default: 'carmen')
        Options:
        - 'carmen'
        based on:
        Centrales Agrar-Rohstoff Marketing- und Energie-Netzwerk,
        Marktübersicht Batteriespeicher, 2015.

    Returns
    -------
    spec_bat : float
        Specific cost of battery in
    """

    assert cap > 0, 'Capacity has to be larger than zero.'
    assert method in ['carmen'], 'Unknown method'

    spec_bat = (5000 + 1225 * cap) / cap

    return spec_bat

def calc_invest_cost_bat(cap, method='carmen'):
    """
    Calculate investment cost of electric batteries in Euro.

    Parameters
    ----------
    cap : float
        Capacity of battery in kWh
    method : str, optional
        Method for calculation (default: 'carmen')
        Options:
        - 'carmen'
        based on:
        Centrales Agrar-Rohstoff Marketing- und Energie-Netzwerk,
        Marktübersicht Batteriespeicher, 2015.

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

    #  Calculate specific cost for battery
    spec_cost = calc_spec_cost_bat(cap=bat_cap)
    print('Specific cost for battery in Euro/kWh:')
    print(round(spec_cost, 2))
    print()

    #  Calculate investment cost for battery
    inv_cost = calc_invest_cost_bat(cap=bat_cap)
    print('Investment cost for battery in Euro:')
    print(round(inv_cost, 2))
