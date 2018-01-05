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

def perform_pv_eb_annuity_check(city, dhw_scale=True):
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
                 (1001, 3, 40),
                 (1002, 3, 40),
                 (1003, 3, 40),
                 (1004, 3, 40),
                 (1005, 3, 40),
                 (1006, 3, 40),
                 (1007, 3, 40)
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
                 (1001, 3, 80),
                 (1002, 3, 80),
                 (1003, 3, 80),
                 (1004, 3, 80),
                 (1005, 3, 80),
                 (1006, 3, 80),
                 (1007, 3, 80)
                 ]

    #  Generate energy systems
    esysgen.gen_esys_for_city(city=city_scen_3,
                              list_data=list_esys,
                              dhw_scale=dhw_scale)

    #  #####################################################################
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

    #  Perform energy balance and annuity calculations for all scenarios
    (total_annuity_1, co2_1) = city_eco_calc1. \
        perform_overall_energy_balance_and_economic_calc()
    list_ann.append(total_annuity_1)
    list_co2.append(co2_1)

    (total_annuity_2, co2_2) = city_eco_calc2. \
        perform_overall_energy_balance_and_economic_calc()
    list_ann.append(total_annuity_2)
    list_co2.append(co2_2)

    (total_annuity_3, co2_3) = city_eco_calc3. \
        perform_overall_energy_balance_and_economic_calc()
    list_ann.append(total_annuity_3)
    list_co2.append(co2_3)

    plt.plot([total_annuity_1], [co2_1], label='Scen. 7 (BOI/small PV)',
             marker='o')
    plt.plot([total_annuity_2], [co2_2], label='Scen. 8 (BOI/medium PV)',
             marker='o')
    plt.plot([total_annuity_3], [co2_3], label='Scen. 9 (BOI/large PV)',
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

    demand_el = build_pv_small.get_electric_power_curve()

    fig = plt.figure()

    shift = 4008

    ax = fig.add_subplot(3, 1, 1)
    ax.plot(pv_small_gen[0+shift:24+shift], label='Small PV')
    ax.plot(demand_el[0:24], label='El. demand')
    plt.legend()

    ax = fig.add_subplot(3, 1, 2)
    ax.plot(pv_medium_gen[0+shift:24+shift], label='Medium PV')
    ax.plot(demand_el[0:24], label='El. demand')
    plt.legend()

    ax = fig.add_subplot(3, 1, 3)
    ax.plot(pv_large_gen[0+shift:24+shift], label='Large PV')
    ax.plot(demand_el[0:24], label='El. demand')
    plt.legend()

    plt.tight_layout()
    plt.show()
    plt.close()


if __name__ == '__main__':

    this_path = os.path.dirname(os.path.abspath(__file__))

    city_name = 'wm_res_east_7_w_street_sh_resc_wm.pkl'

    path_city = os.path.join(this_path,
                             'input',
                             city_name)

    city = pickle.load(open(path_city, mode='rb'))

    perform_pv_eb_annuity_check(city=city)
