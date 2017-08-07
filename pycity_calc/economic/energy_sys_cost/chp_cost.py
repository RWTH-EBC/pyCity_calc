#!/usr/bin/env python
# coding=utf-8
"""
Script to estimate boiler investment cost

Be aware of correct use of units!
"""
from __future__ import division
import pycity_calc.energysystems.Input.chp_asue_2015 as chp_asue


def calc_spec_cost_chp(p_el_nom, method='asue2015', with_inst=True,
                       use_el_input=True, q_th_nom=None):
    """
    Calculate specific cost of CHP in Euro/kW

    Parameters
    ----------
    p_el_nom : float
        Nominal electrical power in kW
    method : str, optional
        Method for calculation of specific cost (default: 'asue2016')
        Options:
        - 'asue2015' (for gas CHPs)
        Based on
        Arbeitsgemeinschaft für sparsamen und umweltfreundlichen
        Energieverbrauch e.V., BHKW-Kenndaten 2014/15, Essen, 2015.
        - 'spieker' (linearized function)
        Based on
        S. Spieker, Dimensionierung von Mini-KWK-Anlagen zur Teilnahme am
        liberalisierten Strommarkt, Optimierung in der Energiewirtschaft 2011,
        VDI Berichte 2157 (2011).
    with_inst : bool, optional
        With installation and transport cost (default: True).
        If False, only use unit cost
    use_el_input : bool, optional
        Defines, if electrical nominal power input should be used
        (default: True)
        True - Use p_el_nom for calculation
        False - Use q_th_nom for calculation
        These factors are based on ASUE 2015, too.
    q_th_nom : float, optional
        Nominal thermal power of CHP system (default: None)

    Returns
    -------
    spec_cost_chp : float
        Specific CHP cost in Euro/kW
    """

    list_methods = ['asue2015', 'spieker']

    assert method in list_methods, 'Unknown method. Check input!'

    if use_el_input is False:
        assert q_th_nom is not None, 'Require thermal power as input!'
        assert q_th_nom > 0, 'Power has to be positive'
    else:
        assert p_el_nom > 0, 'Power has to be positive'

    if use_el_input is False:
        #  Estimate electrical, nominal power, based on thermal power
        el_th_ration = \
            chp_asue.calc_asue_el_th_ratio(q_th_nom * 1000)  # Watt input

        p_el_nom = el_th_ration * q_th_nom

    if method == 'asue2015':

        if p_el_nom <= 10:
            spec_cost_chp = 9585 * p_el_nom ** (-0.542)

        elif p_el_nom <= 100:
            spec_cost_chp = 5438 * p_el_nom ** (-0.351)

        elif p_el_nom <= 1000:
            spec_cost_chp = 4907 * p_el_nom ** (-0.352)

        elif p_el_nom <= 19000:
            spec_cost_chp = 460.89 * p_el_nom ** (-0.015)

        else:
            raise AssertionError('Calculation not valid for powers > 19 MW')

    elif method == 'spieker':

        spec_cost_chp = (19725 + 1365 * p_el_nom) /p_el_nom

    if with_inst:  # Use percentage for installation and transport cost

        if p_el_nom <= 3:
            spec_cost_chp *= 1.59

        elif p_el_nom <= 10:
            spec_cost_chp *= 1.51

        elif p_el_nom <= 100:
            spec_cost_chp *= 1.46

        elif p_el_nom <= 350:
            spec_cost_chp *= 1.51

        elif p_el_nom <= 500:
            spec_cost_chp *= 1.60

        elif p_el_nom <= 750:
            spec_cost_chp *= 1.66

        elif p_el_nom <= 1000:
            spec_cost_chp *= 1.74

        else:
            spec_cost_chp *= 2

    return spec_cost_chp


def calc_invest_cost_chp(p_el_nom, method='asue2015', with_inst=True,
                         use_el_input=True, q_th_nom=None):
    """
    Calculate total investment cost into CHP system

    Parameters
    ----------
    p_el_nom : float
        Nominal electrical power in kW
    method : str, optional
        Method for calculation of specific cost (default: 'asue2016')
        Options:
        - 'asue2015' (for gas CHPs)
        Based on Arbeitsgemeinschaft für sparsamen und umweltfreundlichen
        Energieverbrauch e.V., BHKW-Kenndaten 2014/15, Essen, 2015.
        - 'spieker' (linearized function)
        Based on
        S. Spieker, Dimensionierung von Mini-KWK-Anlagen zur Teilnahme am
        liberalisierten Strommarkt, Optimierung in der Energiewirtschaft 2011,
        VDI Berichte 2157 (2011).
    with_inst : bool, optional
        With installation and transport cost (default: True).
        If False, only use unit cost
    use_el_input : bool, optional
        Defines, if electrical nominal power input should be used
        (default: True)
        True - Use p_el_nom for calculation
        False - Use q_th_nom for calculation
        These factors are based on ASUE 2015, too.
    q_th_nom : float, optional
        Nominal thermal power of CHP system (default: None)

    Returns
    -------
    total_inv_chp : float
        Total investment cost in Euro
    """

    #  Calculate specific chp cost in Euro/kW
    spec_cost = calc_spec_cost_chp(p_el_nom=p_el_nom, method=method,
                                   with_inst=with_inst,
                                   use_el_input=use_el_input,
                                   q_th_nom=q_th_nom)

    if use_el_input is False:
        assert q_th_nom is not None, 'Require thermal power as input!'
        assert q_th_nom > 0, 'Power has to be positive'
    else:
        assert p_el_nom > 0, 'Power has to be positive'

    if use_el_input is False:
        #  Estimate electrical, nominal power, based on thermal power
        el_th_ration = \
            chp_asue.calc_asue_el_th_ratio(q_th_nom * 1000)  # Watt input

        p_el_nom = el_th_ration * q_th_nom

    return spec_cost * p_el_nom


if __name__ == '__main__':
    chp_nom_el_power = 30000  # in Watt
    method = 'asue2015'
    with_inst = True  # With cost for transport and installation

    chp_el_kW = chp_nom_el_power / 1000

    #  Calculate specific cost of CHP
    spec_cost = calc_spec_cost_chp(p_el_nom=chp_el_kW, method=method,
                                   with_inst=with_inst)
    print('Specific CHP cost in Euro/kW:')
    print(round(spec_cost, 2))
    print()

    #  Calculate total investment cost for CHP
    total_cost = calc_invest_cost_chp(p_el_nom=chp_el_kW, method=method,
                                      with_inst=with_inst)
    print('Total investment cost for CHP in Euro:')
    print(round(total_cost, 2))
