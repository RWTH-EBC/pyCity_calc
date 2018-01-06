#!/usr/bin/env python
# coding=utf-8
"""

"""
from __future__ import division

import os
import pickle
import copy
import numpy as np
import matplotlib.pylab as plt

import pycity_calc.cities.scripts.energy_network_generator as enetgen
import pycity_calc.cities.scripts.energy_sys_generator as esysgen
import pycity_calc.environments.germanmarket as gmarket
import pycity_calc.simulation.energy_balance.city_eb_calc as citeb
import pycity_calc.economic.annuity_calculation as annu
import pycity_calc.economic.city_economic_calc as citecon
import pycity_calc.toolbox.modifiers.mod_city_sh_dem as modsh
import pycity_calc.toolbox.modifiers.mod_city_dhw_dem as moddhw
import pycity_calc.toolbox.modifiers.mod_city_el_dem as model


def perform_pv_eb_annuity_check(city, dhw_scale=True, zero_sh_dhw=False,
                                zero_el=False):
    """

    Parameters
    ----------
    city
    dhw_scale
    """

    #  Generate german market instance (if not already included in environment)
    ger_market = gmarket.GermanMarket()

    #  Add GermanMarket object instance to city
    city.environment.prices = ger_market

    #  Scenario 1: Boilers with small PV
    #  #####################################################################

    city_scen_1 = copy.deepcopy(city)

    #  Generate one feeder with CHP, boiler and TES
    list_esys = [(1001, 0, 1),
                 (1002, 0, 1),
                 (1003, 0, 1),
                 (1004, 0, 1),
                 (1005, 0, 1),
                 (1006, 0, 1),
                 (1007, 0, 1),
                 (1001, 3, 10),
                 (1002, 3, 10),
                 (1003, 3, 10),
                 (1004, 3, 10),
                 (1005, 3, 10),
                 (1006, 3, 10),
                 (1007, 3, 10)
                 ]

    #  Generate energy systems
    esysgen.gen_esys_for_city(city=city_scen_1,
                              list_data=list_esys,
                              dhw_scale=dhw_scale)

    #  Scenario 2: Boilers with medium PV
    #  #####################################################################

    city_scen_2 = copy.deepcopy(city)

    #  Generate one feeder with CHP, boiler and TES
    list_esys = [(1001, 0, 1),
                 (1002, 0, 1),
                 (1003, 0, 1),
                 (1004, 0, 1),
                 (1005, 0, 1),
                 (1006, 0, 1),
                 (1007, 0, 1),
                 (1001, 3, 20),
                 (1002, 3, 20),
                 (1003, 3, 20),
                 (1004, 3, 20),
                 (1005, 3, 20),
                 (1006, 3, 20),
                 (1007, 3, 20)
                 ]

    #  Generate energy systems
    esysgen.gen_esys_for_city(city=city_scen_2,
                              list_data=list_esys,
                              dhw_scale=dhw_scale)

    #  Scenario 3: Boilers with large PV
    #  #####################################################################

    city_scen_3 = copy.deepcopy(city)

    #  Generate one feeder with CHP, boiler and TES
    list_esys = [(1001, 0, 1),
                 (1002, 0, 1),
                 (1003, 0, 1),
                 (1004, 0, 1),
                 (1005, 0, 1),
                 (1006, 0, 1),
                 (1007, 0, 1),
                 (1001, 3, 30),
                 (1002, 3, 30),
                 (1003, 3, 30),
                 (1004, 3, 30),
                 (1005, 3, 30),
                 (1006, 3, 30),
                 (1007, 3, 30)
                 ]

    #  Generate energy systems
    esysgen.gen_esys_for_city(city=city_scen_3,
                              list_data=list_esys,
                              dhw_scale=dhw_scale)

    if zero_sh_dhw:
        for city_ind in [city_scen_1, city_scen_2, city_scen_3]:
            modsh.mod_sh_city_dem(city=city_ind, sh_dem=0)
            moddhw.mod_dhw_city_dem(city=city_ind, dhw_dem=0)
    if zero_el:
        for city_ind in [city_scen_1, city_scen_2, city_scen_3]:
            model.mod_el_city_dem(city=city_ind, el_dem=0)

    # #####################################################################
    #  Generate object instances
    #  #####################################################################

    #  Generate annuity object instance
    annuity_obj1 = annu.EconomicCalculation()
    annuity_obj2 = annu.EconomicCalculation()
    annuity_obj3 = annu.EconomicCalculation()

    #  Generate energy balance object for city
    energy_balance1 = citeb.CityEBCalculator(city=city_scen_1)
    energy_balance2 = citeb.CityEBCalculator(city=city_scen_2)
    energy_balance3 = citeb.CityEBCalculator(city=city_scen_3)

    #  Generate city economic calculator instances
    city_eco_calc1 = citecon.CityAnnuityCalc(annuity_obj=annuity_obj1,
                                             energy_balance=energy_balance1)
    city_eco_calc2 = citecon.CityAnnuityCalc(annuity_obj=annuity_obj2,
                                             energy_balance=energy_balance2)
    city_eco_calc3 = citecon.CityAnnuityCalc(annuity_obj=annuity_obj3,
                                             energy_balance=energy_balance3)

    list_ann = []
    list_co2 = []

    print()
    print('Small PV')
    print('#################################################################')
    #  Perform energy balance and annuity calculations for all scenarios
    (total_annuity_1, co2_1) = city_eco_calc1. \
        perform_overall_energy_balance_and_economic_calc(eeg_pv_limit=False)
    list_ann.append(total_annuity_1)
    list_co2.append(co2_1)

    print()
    print('Medium PV')
    print('#################################################################')
    (total_annuity_2, co2_2) = city_eco_calc2. \
        perform_overall_energy_balance_and_economic_calc(eeg_pv_limit=False)
    list_ann.append(total_annuity_2)
    list_co2.append(co2_2)

    print()
    print('Large PV')
    print('#################################################################')
    (total_annuity_3, co2_3) = city_eco_calc3. \
        perform_overall_energy_balance_and_economic_calc(eeg_pv_limit=False)
    list_ann.append(total_annuity_3)
    list_co2.append(co2_3)

    plt.plot([total_annuity_1], [co2_1], label='Scen. 1 (BOI/small PV)',
             marker='o')
    plt.plot([total_annuity_2], [co2_2], label='Scen. 2 (BOI/medium PV)',
             marker='o')
    plt.plot([total_annuity_3], [co2_3], label='Scen. 3 (BOI/large PV)',
             marker='o')
    plt.xlabel('Total annualized cost in Euro/a')
    plt.ylabel('Total CO2 emissions in kg/a')
    plt.legend()
    plt.tight_layout()
    plt.show()
    plt.close()

    #  Compare PV production vs. el. demands for single building
    #  ###################################################################

    n_id = 1001

    #  Pointers to ref. buildings
    build_pv_small = city_scen_1.nodes[n_id]['entity']
    build_pv_medium = city_scen_2.nodes[n_id]['entity']
    build_pv_large = city_scen_3.nodes[n_id]['entity']

    pv_small_gen = build_pv_small.bes.pv.totalPower
    pv_medium_gen = build_pv_medium.bes.pv.totalPower
    pv_large_gen = build_pv_large.bes.pv.totalPower

    el_power = build_pv_small.get_electric_power_curve()

    fig = plt.figure()

    shift = 4008

    ax = fig.add_subplot(3, 1, 1)
    ax.plot(pv_small_gen[0 + shift:24 + shift], label='Small PV')
    ax.plot(el_power[0:24], label='El. demand')
    plt.legend()

    ax = fig.add_subplot(3, 1, 2)
    ax.plot(pv_medium_gen[0 + shift:24 + shift], label='Medium PV')
    ax.plot(el_power[0:24], label='El. demand')
    plt.legend()

    ax = fig.add_subplot(3, 1, 3)
    ax.plot(pv_large_gen[0 + shift:24 + shift], label='Large PV')
    ax.plot(el_power[0:24], label='El. demand')
    plt.legend()

    plt.tight_layout()
    plt.show()
    plt.close()


if __name__ == '__main__':
    zero_sh_dhw = True
    zero_el = False

    this_path = os.path.dirname(os.path.abspath(__file__))

    city_name = 'wm_res_east_7_w_street_sh_resc_wm.pkl'

    path_city = os.path.join(this_path,
                             'input',
                             city_name)

    city = pickle.load(open(path_city, mode='rb'))

    perform_pv_eb_annuity_check(city=city, zero_sh_dhw=zero_sh_dhw,
                                zero_el=zero_el)
