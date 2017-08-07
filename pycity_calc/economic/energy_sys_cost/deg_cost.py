#!/usr/bin/env python
# coding=utf-8
"""
Script to estimate cost of decentralized electrical grid / microgrid
"""
from __future__ import division

def calc_invest_cost_deg(length, nb_con, nb_sub, share_lhn=0):
    """
    Calculate investment cost into multiple deg networks

    Parameters
    ----------
    length : float
        Total length of deg cables
    nb_con : int
        Number of buildings connected to deg (defines number of smart meters)
    nb_sub : int
        Number of sub-degs (defines number of controllers (one per deg))
    share_lhn : float, optional
        Share of cables, which are installed parallel with local heating
        network (LHN). (default: 0)
        E.g. share_lhn = 0.3 means, that 30 % of deg cables are installed
        together with lhn pipes. Thus installation cost is saved.

    Returns
    -------
    invest_deg : float
        Investment cost into decentralized electrical grid (deg) system in Euro
        (including cables, controllers, meters)

    Annotations
    -----------
    Cable cost based on:
    G. Kerber, Aufnahmefähigkeit von Niederspannungsverteilnetzen für die
    Einspeisung aus Photovoltaikkleinanlagen: Dissertation, 2011.

    Smart meter cost based on:
    Ernst & Young, Kosten-Nutzen-Analyse für einen flächendeckenden Einsatz
    intelligenter Zähler, 2013.

    Micro controller cost (per deg) based on:
    E.D. Mehleri, H. Sarimveis, N.C. Markatos, L.G. Papageorgiou,
    A mathematical programming approach for optimal design of distributed
    energy systems at the neighbourhood level, Energy 44 (1) (2012) 96–104.
    """

    assert length > 0, 'Length should be larger than zero'
    assert nb_con >= 2, ''

    #  Cable cost
    cable_cost = share_lhn * 26 * length + \
                 (1 - share_lhn) * (26 + 35) * length

    #  Meter cost
    meter_cost = nb_con * 500

    #  Controller cost
    con_cost = nb_sub * 1500

    return cable_cost + meter_cost + con_cost


if __name__ == '__main__':
    deg_len = 300  # in m
    nb_con = 10  # 10 Buildings
    nb_sub = 1  # 1 (sub-)deg
    share_lhn = 0.75

    deg_invest = \
        calc_invest_cost_deg(length=deg_len, nb_con=nb_con, nb_sub=nb_sub,
                             share_lhn=share_lhn)

    print('Investment cost into DEG in Euro:')
    print(round(deg_invest, 2))
