# coding=utf-8
"""
Example script of Nadine Lermer for pypower usage with pycity
"""
from __future__ import division
__author__ = 'jsc-nle'

import warnings

import pycity_base.classes.Weather as Weather
import pycity_base.classes.Environment as Environment
import pycity_base.classes.Prices as Prices
import pycity_calc.buildings.building as Building
import pycity_base.classes.demand.ElectricalDemand as ElectricalDemand
import pycity_base.classes.demand.Apartment as Apartment

import pycity_calc.extern_el_grid.PowerGrid as PowerGrid
import pycity_calc.environments.timer as Timer


def run_example_1():

    print('Start generation of reference city district')
    print('###########################################')
    print()

    #   generate timer, weather and price objects
    timer = Timer.TimerExtended(timestep=900, year=2010)
    weather = Weather.Weather(timer)
    prices = Prices.Prices()

    #   generate environment
    environment = Environment.Environment(timer, weather, prices)

    #   generate buildings
    building_1 = Building.BuildingExtended(environment)
    building_2 = Building.BuildingExtended(environment)
    building_3 = Building.BuildingExtended(environment)
    building_4 = Building.BuildingExtended(environment)
    building_5 = Building.BuildingExtended(environment)
    building_6 = Building.BuildingExtended(environment)
    building_7 = Building.BuildingExtended(environment)
    building_8 = Building.BuildingExtended(environment)

    #   generate apartments
    #   apartment 1
    apartment_1 = Apartment.Apartment(environment)
    el_demand_1 = ElectricalDemand.ElectricalDemand(environment,
                                                    method=1,
                                                    # Standard load profile
                                                    annualDemand=300000)
                                                    # in kWh
    apartment_1.addEntity(el_demand_1)

    #   apartment 2
    apartment_2 = Apartment.Apartment(environment)
    el_demand_2 = ElectricalDemand.ElectricalDemand(environment,
                                                    method=1,
                                                    # Standard load profile
                                                    annualDemand=1000)
    apartment_2.addEntity(el_demand_2)

    #   apartment 3
    apartment_3 = Apartment.Apartment(environment)
    el_demand_3 = ElectricalDemand.ElectricalDemand(environment,
                                                    method=1,
                                                    # Standard load profile
                                                    annualDemand=2500)
    apartment_3.addEntity(el_demand_3)

    #   apartment 4
    apartment_4 = Apartment.Apartment(environment)
    el_demand_4 = ElectricalDemand.ElectricalDemand(environment,
                                                    method=1,
                                                    # Standard load profile
                                                    annualDemand=6000)

    apartment_4.addEntity(el_demand_4)

    #   add apartments to buildings
    building_1.addMultipleEntities([apartment_1, apartment_2])
    building_2.addEntity(apartment_1)
    building_3.addMultipleEntities([apartment_1, apartment_1])
    building_4.addEntity(apartment_3)
    building_5.addMultipleEntities([apartment_4, apartment_2])
    building_6.addMultipleEntities([apartment_4, apartment_2, apartment_3])
    building_7.addMultipleEntities([apartment_3, apartment_1])
    building_8.addEntity(apartment_4)

    #   generate list of buildings
    building_list = [building_1, building_2, building_3, building_4,
                     building_5, building_6, building_7, building_8]

    print('Start generation of reference power grid')
    print('###########################################')
    print()

    #   create power grid
    power_grid = PowerGrid.PowerGrid(building_list=building_list,
                                     environment=environment,
                                     grid_type="ruralcable1")

    print('Start adding buildings to el. grid')
    print('###########################################')
    print()

    #   generate city district
    power_grid.create_city_district(plot=False)

    print('Perform power flow calculation')
    print('###########################################')
    print()

    #   power flow calculation
    results = power_grid.power_flow_calculation(save=False, start=25, end=45)

    msg = 'Evaluate power flow and power flow animation are currently ' \
          'uncommented, as they cause errors (see #61 on Github)'
    warnings.warn(msg)

    # print('Evaluate power flow results')
    # print('###########################################')
    # print()

    #  FIXME: Not working, any more (see #61)

    # #   power flow evaluation
    # res_city_district = power_grid.power_flow_evaluation(results)
    #
    #
    # #   check results for off-limit conditions
    # power_grid.check_off_limit_conditions(res_city_district)
    #
    # print('Start power flow visualization')
    # print('###########################################')
    # print()
    #
    # #   animation
    # power_grid.power_flow_animation(res_city_district)

    print("END")


def run_example_2():
    #   generate timer, weather and price objects
    timer = Timer.TimerExtended(timestep=60)
    weather = Weather.Weather(timer)
    prices = Prices.Prices()

    #   generate environment
    environment = Environment.Environment(timer, weather, prices)

    #   generate buildings
    building_1 = Building.BuildingExtended(environment)
    building_2 = Building.BuildingExtended(environment)
    building_3 = Building.BuildingExtended(environment)
    building_4 = Building.BuildingExtended(environment)
    building_5 = Building.BuildingExtended(environment)
    building_6 = Building.BuildingExtended(environment)
    building_7 = Building.BuildingExtended(environment)
    building_8 = Building.BuildingExtended(environment)
    building_9 = Building.BuildingExtended(environment)
    building_10 = Building.BuildingExtended(environment)
    building_11 = Building.BuildingExtended(environment)
    building_12 = Building.BuildingExtended(environment)
    building_13 = Building.BuildingExtended(environment)
    building_14 = Building.BuildingExtended(environment)
    building_15 = Building.BuildingExtended(environment)
    building_16 = Building.BuildingExtended(environment)
    building_17 = Building.BuildingExtended(environment)
    building_18 = Building.BuildingExtended(environment)
    building_19 = Building.BuildingExtended(environment)
    building_20 = Building.BuildingExtended(environment)

    #   generate apartments
    #   apartment 1
    apartment_1 = Apartment.Apartment(environment)
    el_demand_1 = ElectricalDemand.ElectricalDemand(environment,
                                                    method=1,
                                                    # Standard load profile
                                                    annualDemand=100000)
                                                    # in kWh
    apartment_1.addEntity(el_demand_1)

    #   apartment 2
    apartment_2 = Apartment.Apartment(environment)
    el_demand_2 = ElectricalDemand.ElectricalDemand(environment,
                                                    method=1,
                                                    # Standard load profile
                                                    annualDemand=5000)
    apartment_2.addEntity(el_demand_2)

    #   add apartments to buildings
    building_1.addEntity(apartment_1)
    building_2.addEntity(apartment_2)
    building_3.addEntity(apartment_1)
    building_4.addEntity(apartment_2)
    building_5.addEntity(apartment_1)
    building_6.addEntity(apartment_1)
    building_7.addEntity(apartment_2)
    building_8.addEntity(apartment_1)
    building_9.addEntity(apartment_2)
    building_10.addEntity(apartment_2)
    building_11.addEntity(apartment_1)
    building_12.addEntity(apartment_2)
    building_13.addEntity(apartment_1)
    building_14.addEntity(apartment_2)
    building_15.addEntity(apartment_2)
    building_16.addEntity(apartment_1)
    building_17.addEntity(apartment_1)
    building_18.addEntity(apartment_2)
    building_19.addEntity(apartment_1)
    building_20.addEntity(apartment_2)

    #   generate list of buildings
    building_list = [building_1, building_2, building_3, building_4,
                     building_5, building_6, building_7, building_8,
                     building_9, building_10, building_11, building_12,
                     building_13, building_14, building_15,
                     building_16, building_17, building_18, building_19,
                     building_20]

    #   create power grid
    power_grid = PowerGrid.PowerGrid(building_list=building_list,
                                     environment=environment,
                                     grid_type="ruraloverhead2")
    #   generate city district
    power_grid.create_city_district(plot=False)
    #   power flow calculation
    results = power_grid.power_flow_calculation(save=False, start=3, end=10)
    #   power flow evaluation
    res_city_district = power_grid.power_flow_evaluation(results)
    #   check results for off-limit conditions
    power_grid.check_off_limit_conditions(res_city_district)
    #   animation
    power_grid.power_flow_animation(res_city_district, interval=1000)

    print("END")


if __name__ == '__main__':
    run_example_1()
    # run_example_2()
