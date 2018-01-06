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
import shapely.geometry.point as point

import pycity_base.classes.Weather as Weather
import pycity_base.classes.demand.SpaceHeating as spaceheat
import pycity_base.classes.demand.ElectricalDemand as elecdemand
import pycity_base.classes.supply.BES as BES
import pycity_base.classes.supply.PV as PV
import pycity_base.classes.demand.Apartment as apart

import pycity_calc.cities.city as cit
import pycity_calc.buildings.building as build
import pycity_calc.environments.co2emissions as co2em
import pycity_calc.environments.environment as env
import pycity_calc.environments.timer as time
import pycity_calc.environments.germanmarket as germanmarket
import pycity_calc.energysystems.boiler as boil
import pycity_calc.cities.scripts.energy_sys_generator as esysgen
import pycity_calc.simulation.energy_balance.city_eb_calc as citeb
import pycity_calc.economic.annuity_calculation as annu
import pycity_calc.economic.city_economic_calc as citecon
import pycity_calc.toolbox.modifiers.mod_city_sh_dem as modsh
import pycity_calc.toolbox.modifiers.mod_city_dhw_dem as moddhw
import pycity_calc.toolbox.modifiers.mod_city_el_dem as model


def perform_pv_eb_annuity_check(city, dhw_scale=True, zero_sh_dhw=False,
                                zero_el=False, eeg_pv_limit=True):
    """

    Parameters
    ----------
    city
    dhw_scale
    zero_sh_dhw
    zero_el
    eeg_pv_limit

    Returns
    -------

    """

    dict_res = {}

    for i in range(30):
        city_scen = copy.deepcopy(city)

        list_esys = [  # (1001, 0, 1),
            (1001, 3, 1 / 0.125 * (i + 1)),
        ]

        #  Generate energy systems
        esysgen.gen_esys_for_city(city=city_scen,
                                  list_data=list_esys,
                                  dhw_scale=dhw_scale)

        if zero_sh_dhw:
            modsh.mod_sh_city_dem(city=city_scen, sh_dem=0)
            moddhw.mod_dhw_city_dem(city=city_scen, dhw_dem=0)
        if zero_el:
            model.mod_el_city_dem(city=city_scen, el_dem=0)

        # Generate annuity object instance
        annuity_obj = annu.EconomicCalculation()

        #  Generate energy balance object for city
        energy_balance = citeb.CityEBCalculator(city=city_scen)

        #  Generate city economic calculator instances
        city_eco_calc = citecon.CityAnnuityCalc(annuity_obj=annuity_obj,
                                                energy_balance=energy_balance)

        (total_annuity, co2) = city_eco_calc. \
            perform_overall_energy_balance_and_economic_calc(
            eeg_pv_limit=eeg_pv_limit)

        label = 'Area ' + str(1 / 0.125 * (i + 1))

        if i < 10:
            marker = 'o'
        elif i < 20:
            marker = '+'
        else:
            marker = '*'

        plt.plot([total_annuity], [co2], label=label,
                 marker=marker)

        dict_res[i] = city_scen

    plt.xlabel('Total annualized cost in Euro/a')
    plt.ylabel('Total CO2 emissions in kg/a')
    plt.legend()
    plt.tight_layout()
    plt.show()
    plt.close()



    # #  Scenario 1: Boilers with small PV
    # #  #####################################################################
    #
    # city_scen_1 = copy.deepcopy(city)
    #
    # list_esys = [#(1001, 0, 1),
    #              (1001, 3, 10),
    #              ]
    #
    # #  Generate energy systems
    # esysgen.gen_esys_for_city(city=city_scen_1,
    #                           list_data=list_esys,
    #                           dhw_scale=dhw_scale)
    #
    # #  Scenario 2: Boilers with medium PV
    # #  #####################################################################
    #
    # city_scen_2 = copy.deepcopy(city)
    #
    # list_esys = [#(1001, 0, 1),
    #              (1001, 3, 20),
    #              ]
    #
    # #  Generate energy systems
    # esysgen.gen_esys_for_city(city=city_scen_2,
    #                           list_data=list_esys,
    #                           dhw_scale=dhw_scale)
    #
    # #  Scenario 3: Boilers with large PV
    # #  #####################################################################
    #
    # city_scen_3 = copy.deepcopy(city)
    #
    # list_esys = [#(1001, 0, 1),
    #              (1001, 3, 30),
    #              ]

    # #  Generate energy systems
    # esysgen.gen_esys_for_city(city=city_scen_3,
    #                           list_data=list_esys,
    #                           dhw_scale=dhw_scale)
    #
    # if zero_sh_dhw:
    #     for city_ind in [city_scen_1, city_scen_2, city_scen_3]:
    #         modsh.mod_sh_city_dem(city=city_ind, sh_dem=0)
    #         moddhw.mod_dhw_city_dem(city=city_ind, dhw_dem=0)
    # if zero_el:
    #     for city_ind in [city_scen_1, city_scen_2, city_scen_3]:
    #         model.mod_el_city_dem(city=city_ind, el_dem=0)

    # #####################################################################
    #  Generate object instances
    #  #####################################################################

    # #  Generate annuity object instance
    # annuity_obj1 = annu.EconomicCalculation(interest=0.000000001,
    #                                            #  Zero interest undefined,
    #                                            #  thus, using small value
    #                                            price_ch_cap=1,
    #                                            price_ch_dem_gas=1,
    #                                            price_ch_dem_el=1,
    #                                            price_ch_dem_cool=1,
    #                                            price_ch_op=1,
    #                                            price_ch_proc_chp=1.0,
    #                                            price_ch_proc_pv=1.0,
    #                                            price_ch_eeg_chp=1.0,
    #                                            price_ch_eeg_pv=1,
    #                                            price_ch_eex=1,
    #                                            price_ch_grid_use=1,
    #                                            price_ch_chp_sub=1,
    #                                            price_ch_chp_self=1,
    #                                            price_ch_chp_tax_return=1,
    #                                            price_ch_pv_sub=1,
    #                                            price_ch_dem_el_hp=1)
    # annuity_obj2 = annu.EconomicCalculation(interest=0.000000001,
    #                                            #  Zero interest undefined,
    #                                            #  thus, using small value
    #                                            price_ch_cap=1,
    #                                            price_ch_dem_gas=1,
    #                                            price_ch_dem_el=1,
    #                                            price_ch_dem_cool=1,
    #                                            price_ch_op=1,
    #                                            price_ch_proc_chp=1.0,
    #                                            price_ch_proc_pv=1.0,
    #                                            price_ch_eeg_chp=1.0,
    #                                            price_ch_eeg_pv=1,
    #                                            price_ch_eex=1,
    #                                            price_ch_grid_use=1,
    #                                            price_ch_chp_sub=1,
    #                                            price_ch_chp_self=1,
    #                                            price_ch_chp_tax_return=1,
    #                                            price_ch_pv_sub=1,
    #                                            price_ch_dem_el_hp=1)
    # annuity_obj3 = annu.EconomicCalculation(interest=0.000000001,
    #                                            #  Zero interest undefined,
    #                                            #  thus, using small value
    #                                            price_ch_cap=1,
    #                                            price_ch_dem_gas=1,
    #                                            price_ch_dem_el=1,
    #                                            price_ch_dem_cool=1,
    #                                            price_ch_op=1,
    #                                            price_ch_proc_chp=1.0,
    #                                            price_ch_proc_pv=1.0,
    #                                            price_ch_eeg_chp=1.0,
    #                                            price_ch_eeg_pv=1,
    #                                            price_ch_eex=1,
    #                                            price_ch_grid_use=1,
    #                                            price_ch_chp_sub=1,
    #                                            price_ch_chp_self=1,
    #                                            price_ch_chp_tax_return=1,
    #                                            price_ch_pv_sub=1,
    #                                            price_ch_dem_el_hp=1)

    # #  Generate annuity object instance
    # annuity_obj1 = annu.EconomicCalculation()
    # annuity_obj2 = annu.EconomicCalculation()
    # annuity_obj3 = annu.EconomicCalculation()
    #
    # #  Generate energy balance object for city
    # energy_balance1 = citeb.CityEBCalculator(city=city_scen_1)
    # energy_balance2 = citeb.CityEBCalculator(city=city_scen_2)
    # energy_balance3 = citeb.CityEBCalculator(city=city_scen_3)
    #
    # #  Generate city economic calculator instances
    # city_eco_calc1 = citecon.CityAnnuityCalc(annuity_obj=annuity_obj1,
    #                                          energy_balance=energy_balance1)
    # city_eco_calc2 = citecon.CityAnnuityCalc(annuity_obj=annuity_obj2,
    #                                          energy_balance=energy_balance2)
    # city_eco_calc3 = citecon.CityAnnuityCalc(annuity_obj=annuity_obj3,
    #                                          energy_balance=energy_balance3)

    # list_ann = []
    # list_co2 = []
    #
    # print()
    # print('Small PV')
    # print('#################################################################')
    # #  Perform energy balance and annuity calculations for all scenarios
    # (total_annuity_1, co2_1) = city_eco_calc1. \
    #     perform_overall_energy_balance_and_economic_calc(eeg_pv_limit=False)
    # list_ann.append(total_annuity_1)
    # list_co2.append(co2_1)
    #
    # print()
    # print('Medium PV')
    # print('#################################################################')
    # (total_annuity_2, co2_2) = city_eco_calc2. \
    #     perform_overall_energy_balance_and_economic_calc(eeg_pv_limit=False)
    # list_ann.append(total_annuity_2)
    # list_co2.append(co2_2)
    #
    # print()
    # print('Large PV')
    # print('#################################################################')
    # (total_annuity_3, co2_3) = city_eco_calc3. \
    #     perform_overall_energy_balance_and_economic_calc(eeg_pv_limit=False)
    # list_ann.append(total_annuity_3)
    # list_co2.append(co2_3)

    # plt.plot([total_annuity_1], [co2_1], label='Scen. 1 (BOI/small PV)',
    #          marker='o')
    # plt.plot([total_annuity_2], [co2_2], label='Scen. 2 (BOI/medium PV)',
    #          marker='o')
    # plt.plot([total_annuity_3], [co2_3], label='Scen. 3 (BOI/large PV)',
    #          marker='o')
    # plt.xlabel('Total annualized cost in Euro/a')
    # plt.ylabel('Total CO2 emissions in kg/a')
    # plt.legend()
    # plt.tight_layout()
    # plt.show()
    # plt.close()

    #  Compare PV production vs. el. demands for single building
    #  ###################################################################

    n_id = 1001

    #  Pointers to ref. buildings
    build_pv_small = dict_res[6].nodes[n_id]['entity']
    build_pv_medium = dict_res[8].nodes[n_id]['entity']
    build_pv_large = dict_res[10].nodes[n_id]['entity']

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
    #  Create extended environment of pycity_calc
    year = 2017
    timestep = 3600  # Timestep in seconds
    location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop
    altitude = 55  # Altitude of Bottrop

    #  Generate environment
    #  Generate timer object
    timer = time.TimerExtended(timestep=timestep, year=year)

    #  Generate weather object
    weather = Weather.Weather(timer, useTRY=True, location=location,
                              altitude=altitude)

    #  Generate market object
    gmarket = germanmarket.GermanMarket()

    #  Generate co2 emissions object
    co2emissions = co2em.Emissions(year=year)

    #  Generate environment
    environment = env.EnvironmentExtended(timer, weather,
                                          prices=gmarket,
                                          location=location,
                                          co2em=co2emissions)

    #  City
    city = cit.City(environment=environment)

    #  One building
    building = build.BuildingExtended(environment=environment,
                                      build_type=0)

    #  One apartment
    apartment = apart.Apartment(environment=environment)

    p_nom = 0  # in W

    array_el = np.ones(environment.timer.timestepsTotal) * p_nom
    el_demand = elecdemand.ElectricalDemand(
        environment=environment,
        method=1,
        annualDemand=3000
        # loadcurve=array_el
    )

    #  Add energy demands to apartment
    apartment.addEntity(el_demand)

    #  Add apartment to extended building
    building.addEntity(entity=apartment)

    #  Add building to city
    pos = point.Point(0, 0)
    city.add_extended_building(extended_building=building, position=pos)

    #  BES
    bes = BES.BES(environment=environment)

    boiler = boil.BoilerExtended(environment=environment,
                                 q_nominal=0.00000000000001,  # Dummy value
                                 eta=1)

    #  Add devices to BES
    bes.addMultipleDevices([boiler])

    #  Add BES to building
    building.addEntity(bes)

    perform_pv_eb_annuity_check(city=city)
