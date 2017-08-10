#!/usr/bin/env python
# coding=utf-8
"""
Script to estimate boiler investment cost

Be aware of correct use of units!
"""
from __future__ import division

def calc_spec_cost_boiler(q_nom, method='viess2013'):
    """
    Estimate specific boiler cost in Euro/kW, based on nominal thermal power
    in kW.

    Parameters
    ----------
    q_nom : float
        Nominal thermal power of boiler in kW
    method : str, optional
        Method for calculation of specific cost (default: 'viess2013')
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

    Returns
    -------
    spec_cost : float
        Specific cost of boiler in Euro/kW
    """

    list_methods = ['dbi', 'viess2013', 'spieker']

    assert method in list_methods, 'Unknown method'
    assert q_nom > 0, 'Nominal boiler power should be larger than zero!'

    if method == 'dbi':

        spec_cost = 412.85 * q_nom ** (-0.339)

    elif method == 'viess2013':

        spec_cost = 3507.7 * q_nom ** (-0.906)

    elif method == 'spieker':

        spec_cost = (3100 + q_nom * 62) / q_nom

    return spec_cost


def calc_abs_boiler_cost(q_nom, method='viess2013'):
    """
    Calculate absolute investment cost for boiler (input for q_nom is kW)

    Parameters
    ----------
    q_nom : float
        Nominal thermal power of boiler in kW
    method : str, optional
        Method for calculation of investement cost (default: 'viess2013')
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

    Returns
    -------
    boiler_inv : float
        Boiler investment cost in Euro
    """

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
