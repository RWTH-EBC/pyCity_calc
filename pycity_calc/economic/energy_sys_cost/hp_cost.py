#!/usr/bin/env python
# coding=utf-8
"""
Script to calculate heat pump investment cost
"""
from __future__ import division

import numpy as np
import matplotlib.pyplot as plt


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
        - 'stinner':
        #  Fixme: Add reference
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

    assert method in ['wolf', 'stinner'], 'Unkown heat pump method. ' \
                                          'Check ' \
                                          'input.'
    assert hp_type in ['aw', 'ww', 'bw'], 'Unknown heat pump type. Check input'
    assert q_nom > 0, 'Heat pump nominal power has to be larger than zero!'

    if method == 'stinner':  # pragma: no cover
        if hp_type != 'aw':  # pragma: no cover
            msg = 'Method stinner can only handle air water heat pump costs.'
            raise AssertionError(msg)

    if method == 'wolf':

        if hp_type == 'aw':  # Air/water heat pump

            spec_cost_hp = 2610.2 * q_nom ** (-0.558)

        elif hp_type == 'ww':  # Water/water heat pump

            spec_cost_hp = 3468.35 * q_nom ** (-0.53)

        elif hp_type == 'bw':  # Brine/water heat pump

            spec_cost_hp = 3468.35 * q_nom ** (-0.53)

    if method == 'stinner':

        if hp_type == 'aw':  # Air/water heat pump

            spec_cost_hp = 495.4 * q_nom ** (0.9154 - 1) + 7888 / q_nom

    return spec_cost_hp


def calc_invest_cost_hp(q_nom, method='wolf', hp_type='aw',
                        with_source_cost=True, with_inst=True):
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
        - 'stinner':
        #  Fixme: Add reference
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

    if method == 'wolf':
        if with_source_cost is True:

            if hp_type == 'aw':
                #  According to
                #  M. Platt, S. Exner, R. Bracke, Analyse des deutschen
                #  Wärmepumpenmarktes: Bestandsaufnahme und Trends, 2010.
                hp_invest = spec_cost * q_nom / 0.825
            elif hp_type == 'ww' or hp_type == 'bw':
                #  According to
                #  M. Platt, S. Exner, R. Bracke, Analyse des deutschen
                #  Wärmepumpenmarktes: Bestandsaufnahme und Trends, 2010.
                hp_invest = spec_cost * q_nom / 0.5

        else:
            hp_invest = spec_cost * q_nom

    elif method == 'stinner':
        hp_invest = spec_cost * q_nom + with_inst * 2361

    return hp_invest


if __name__ == '__main__':
    hp_th_pow = 10000  # Heat pump thermal power in Watt
    method = 'stinner'
    hp_type = 'aw'  # Brine/water
    with_source_cost = False  # With/Without cost for heat source preparation

    hp_kw = hp_th_pow / 1000  # in kW

    #  Calculate specific heat pump cost
    spec_cost = calc_spec_cost_hp(q_nom=hp_kw, method=method, hp_type=hp_type)
    print('Specific heat pump cost in Euro/kW:')
    print(round(spec_cost, 2))
    print()

    #  Calculate heat pump investment cost
    invest_hp = calc_invest_cost_hp(q_nom=hp_kw, method=method,
                                    hp_type=hp_type,
                                    with_source_cost=with_source_cost,
                                    with_inst=True)
    print('Investment cost for heat pump in Euro:')
    print(round(invest_hp, 2))

    array_ref_sizes = np.arange(1, 200, 1)
    array_cost_wolf_aw = np.zeros(len(array_ref_sizes))
    array_cost_stinner_aw = np.zeros(len(array_ref_sizes))
    array_cost_wolf_ww = np.zeros(len(array_ref_sizes))

    for i in range(len(array_ref_sizes)):
        size = array_ref_sizes[i]
        array_cost_wolf_aw[i] = \
            calc_invest_cost_hp(q_nom=size,
                                method='wolf',
                                hp_type='aw',
                                with_source_cost=with_source_cost,
                                with_inst=True)
        array_cost_wolf_ww[i] = \
            calc_invest_cost_hp(q_nom=size,
                                method='wolf',
                                hp_type='ww',
                                with_source_cost=with_source_cost,
                                with_inst=True)
        array_cost_stinner_aw[i] = \
            calc_invest_cost_hp(q_nom=size,
                                method='stinner',
                                hp_type='aw',
                                with_source_cost=with_source_cost,
                                with_inst=True)

    plt.plot(array_ref_sizes, array_cost_wolf_aw, label='wolf_aw')
    plt.plot(array_ref_sizes, array_cost_wolf_ww, label='wolf_ww')
    plt.plot(array_ref_sizes, array_cost_stinner_aw, label='stinner_aw')
    plt.xlabel('Heat pump nominal thermal power in kW')
    plt.ylabel('Capital cost in Euro')
    plt.legend()
    plt.show()
    plt.close()
