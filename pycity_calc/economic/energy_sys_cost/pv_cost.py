#!/usr/bin/env python
# coding=utf-8
"""
Calculate investment cost for photovoltaic systems
"""
from __future__ import division

import numpy as np
import matplotlib.pyplot as plt


def calc_pv_invest(area, kw_to_area=0.125, method='EuPD'):
    """
    Calculate PV investment cost in Euro

    Parameters
    ----------
    area : float
        Photovoltaic area
    kw_to_area : float , optional
        Ratio of peak power to area (default: 0.125)
        For instance, 0.125 means 0.125 kWp / m2 area
        (http://www.solaranlagen-portal.com/photovoltaik/leistung)
    method : str, optional
        Method to calculate cost (default: 'EuPD')
        Options:
        - 'sap':
        Based on: Solaranlagenportal
        http://www.solaranlagen-portal.com/photovoltaik/kosten
        - 'EuPD':
        Based on: EuPD Research, Photovoltaik-Preismonitor Deutschland: German PV
        ModulePriceMonitor.

    Returns
    -------
    pv_invest : float
        Investcost into PV system in Euro
    """

    assert method in ['sap', 'EuPD'], 'Unknown method'
    assert area > 0, 'Area has to be larger than zero.'
    assert kw_to_area > 0, 'kWp / area ratio has to be larger than zero.'

    if method == 'sap':
        kw_peak = area * kw_to_area  # kW peak load

        #  kw_peak * (spec_price + spec_install_cost) + inverter cost
        pv_invest = kw_peak * (1100 + 120) + 2000

    if method == 'EuPD':
        kw_peak = area * kw_to_area  # kW peak load

        #  kw_peak * (spec_cost) + inverter cost
        pv_invest = kw_peak * 1400 + 2000

    return pv_invest


if __name__ == '__main__':
    area = 10

    #  Calculate PV investment cost
    pv_invest = calc_pv_invest(area=area)

    print('PV investment cost in Euro:')
    print(round(pv_invest, 2))

    array_in = np.arange(start=1, stop=150, step=1)

    array_out = np.zeros(len(array_in))
    array_out2 = np.zeros(len(array_in))

    for i in range(len(array_in)):
        area = array_in[i]
        array_out[i] = calc_pv_invest(area=area, method='EuPD')
        array_out2[i] = calc_pv_invest(area=area, method='sap')


    plt.plot(array_in, array_out, label='EuPD')
    plt.plot(array_in, array_out2, label='sap')
    plt.xlabel('PV module area in m$^2$')
    plt.ylabel('Investment in Euro')
    plt.legend()
    plt.show()
    plt.close()
