#!/usr/bin/env python
# coding=utf-8
"""
Script to calculate heat pump investment cost
"""


def calc_spec_cost_hp(q_nom, method='wolf', hp_type='aw'):
    """
    Calculate specific heat pump cost in Euro/kW

    Parameters
    ----------
    q_nom : float
        Nominal heating power in kW
    method : str, optional
        Method for calculation (default: 'wolf')
        Options:
        - 'wolf':
        Based on :
        S. Wolf, U. Fahl, M. Blesl, A. Voß, Analyse des Potenzials von
        Industriewärmepumpen in Deutschland, 2014.
    hp_type : str, optional
        Type of heat pump (default 'aw')
        Options:
        - 'aw' : Air/water heat pump
        - 'ww' : Water/water heat pump
        - 'bw' : Brine/water heat pump

    Returns
    -------
    spec_cost_hp : float
        Specific cost for heat pump in Euro/kW
    """

    assert method in ['wolf'], 'Unkown heat pump method. Check input.'
    assert hp_type in ['aw', 'ww', 'bw'], 'Unknown heat pump type. Check input'
    assert q_nom > 0, 'Heat pump nominal power has to be larger than zero!'

    if method == 'wolf':

        if hp_type == 'aw':  # Air/water heat pump

            spec_cost_hp = 3468.35 * q_nom ** (-0.53)

        elif hp_type == 'ww':  # Water/water heat pump

            spec_cost_hp = 2610.2 * q_nom ** (-0.558)

        elif hp_type == 'bw':  # Brine/water heat pump

            spec_cost_hp = 2610.2 * q_nom ** (-0.558)

    return spec_cost_hp

def calc_invest_cost_hp(q_nom, method='wolf', hp_type='aw',
                        with_source_cost=True):
    """
    Calculate investment cost of heat pump in Euro.

    Parameters
    ----------
    q_nom : float
        Nominal heating power in kW
    method : str, optional
        Method for calculation (default: 'wolf')
        Options:
        - 'wolf':
        Based on :
        S. Wolf, U. Fahl, M. Blesl, A. Voß, Analyse des Potenzials von
        Industriewärmepumpen in Deutschland, 2014.
    hp_type : str, optional
        Type of heat pump (default 'aw')
        Options:
        - 'aw' : Air/water heat pump
        - 'ww' : Water/water heat pump
        - 'bw' : Brine/water heat pump
    with_source_cost : bool, optional
        Defines, if cost for heat pump source preparation should be included
        (default: True). Only necessary, if hp_type != 'aw'

    Returns
    -------
    hp_invest : float
        Heat pump investment cost in Euro
    """

    #  Get specific cost
    spec_cost = calc_spec_cost_hp(q_nom=q_nom, method=method, hp_type=hp_type)

    if with_source_cost is True and hp_type != 'aw':

        if hp_type == 'bw':
            #  According to
            #  M. Platt, S. Exner, R. Bracke, Analyse des deutschen
            #  Wärmepumpenmarktes: Bestandsaufnahme und Trends, 2010.
            hp_invest = spec_cost * q_nom / 0.5
        elif hp_type == 'ww':
            #  According to
            #  M. Platt, S. Exner, R. Bracke, Analyse des deutschen
            #  Wärmepumpenmarktes: Bestandsaufnahme und Trends, 2010.
            hp_invest = spec_cost * q_nom / 0.8

    else:
        hp_invest = spec_cost * q_nom

    return hp_invest


if __name__ == '__main__':

    hp_th_pow = 20000  # Heat pump thermal power in Watt
    method = 'wolf'
    hp_type = 'bw'  # Brine/water
    with_source_cost = True  # With/Without cost for heat source preparation

    hp_kw = hp_th_pow / 1000  # in kW

    #  Calculate specific heat pump cost
    spec_cost = calc_spec_cost_hp(q_nom=hp_kw, method=method, hp_type=hp_type)
    print('Specific heat pump cost in Euro/kW:')
    print(round(spec_cost, 2))
    print()

    #  Calculate heat pump investment cost
    invest_hp = calc_invest_cost_hp(q_nom=hp_kw, method=method,
                                    hp_type=hp_type,
                                    with_source_cost=with_source_cost)
    print('Investment cost for heat pump in Euro:')
    print(round(invest_hp, 2))
