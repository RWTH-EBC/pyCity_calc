#!/usr/bin/env python
# coding=utf-8
"""
Script to estimate thermal energy storage investment cost
"""
from __future__ import division
import warnings


def calc_spec_cost_tes(volume, method='spieker'):
    """
    Calculate specific thermal energy storage / hot water tank cost in
    Euro / m3

    Parameters
    ----------
    volume : float
        Volume in m3
    method : str, optional
        Defines method to calculate cost (default: 'spieker')
        - 'spieker' (linearized cost function)
        Based on reference:
        S. Spieker, Dimensionierung von Mini-KWK-Anlagen zur Teilnahme am
        liberalisierten Strommarkt, Optimierung in der Energiewirtschaft 2011,
        VDI Berichte 2157 (2011).
        - 'schmidt'
        Only valid for large scale storage systems (>= 100.000 liters)
        Based on:
        Saisonale Wärmespeicher - aktuelle Speichertechnologien und
        Entwicklungen bei Heißwasser-Wärmespeichern - Schmidt 2005, S.12

    Returns
    -------
    spec_cost_tes : float
        Specific tes cost in Euro/m3
    """

    list_methods = ['spieker', 'schmidt']

    assert method in list_methods, 'Method unknown. Check input.'
    assert volume > 0, 'Volume should be larger than zero.'
    if volume > 10:
        msg = 'Volume > 10 m3 is pretty large for tes. Is this input correct?'
        warnings.warn(msg)

    if method == 'spieker':

        spec_cost_tes = (500 + 1450 * volume) / volume

    elif method == 'schmidt':

        assert volume >= 100000, 'Only valid for large scale tes volumes!'

        spec_cost_tes = 8820.5 * volume ** (-0.457)

    return spec_cost_tes

def calc_invest_cost_tes(volume, method='spieker'):
    """
    Calculate investment cost in thermal energy storage / hot water tank
    in Euro.

    Parameters
    ----------
    volume : float
        Volume in m3
    method : str, optional
        Defines method to calculate cost (default: 'spieker')
        - 'spieker' (linearized cost function)
        Based on reference:
        S. Spieker, Dimensionierung von Mini-KWK-Anlagen zur Teilnahme am
        liberalisierten Strommarkt, Optimierung in der Energiewirtschaft 2011,
        VDI Berichte 2157 (2011).
        - 'schmidt'
        Based on:
        Saisonale Wärmespeicher - aktuelle Speichertechnologien und
        Entwicklungen bei Heißwasser-Wärmespeichern - Schmidt 2005, S.12

    Returns
    -------
    invest_tes : float
        Invest cost into tes in Euro
    """

    #  Get specific cost
    spec_cost = calc_spec_cost_tes(volume=volume, method=method)

    return spec_cost * volume


if __name__ == '__main__':
    volume = 300  # in literes
    method_1 = 'spieker'
    #  method_2 = 'schmidt'  # Only valid for large scale storage systems

    volume_m3 = volume / 1000

    #  Calculate specific cost for tes
    spec_cost_1 = calc_spec_cost_tes(volume=volume_m3, method=method_1)

    print('Specific cost (Spieker et al.) for tes in Euro/m3: ')
    print(round(spec_cost_1, 2))
    print()

    #  Calculate investment cost for tes
    invest_cost_1 = calc_invest_cost_tes(volume=volume_m3, method=method_1)

    print('Investment cost (Spieker et al.) for tes in Euro: ')
    print(round(invest_cost_1, 2))
