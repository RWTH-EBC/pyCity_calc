#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
from __future__ import division

import copy
import shapely.geometry.point as point

import pycity_base.classes.Weather as Weather
import pycity_base.classes.demand.SpaceHeating as SpaceHeating
import pycity_base.classes.demand.ElectricalDemand as ElectricalDemand
import pycity_base.classes.demand.Apartment as Apartment

import pycity_calc.buildings.building as build_ex
import pycity_calc.cities.city as cit
import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.environment as env
import pycity_calc.environments.germanmarket as germarkt
import pycity_calc.environments.timer as time
import pycity_calc.cities.scripts.energy_network_generator as enetgen
import pycity_calc.cities.scripts.energy_sys_generator as esysgen
import pycity_calc.simulation.energy_balance.check_eb_requ as checkeb


class TestCheckEBRequ():
    def test_check_eb_requirements(self):
        #  Generate test city

        #  Create extended environment of pycity_calc
        year = 2010
        timestep = 900  # Timestep in seconds
        location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop
        altitude = 55  # Altitude of Bottrop

        #  Generate timer object
        timer = time.TimerExtended(timestep=timestep, year=year)

        #  Generate weather object
        weather = Weather.Weather(timer, useTRY=True, location=location,
                                  altitude=altitude)

        #  Generate market object
        market = germarkt.GermanMarket()

        #  Generate co2 emissions object
        co2em = co2.Emissions(year=year)

        #  Generate environment
        environment = env.EnvironmentExtended(timer, weather, prices=market,
                                              location=location, co2em=co2em)

        #  Generate city object
        city_object = cit.City(environment=environment)

        #  Iterate 7 times to generate 3 building objects
        for i in range(7):
            #  Create demands (with standardized load profiles (method=1))
            heat_demand = SpaceHeating.SpaceHeating(environment,
                                                    method=1,
                                                    profile_type='HEF',
                                                    livingArea=100,
                                                    specificDemand=130)

            el_demand = ElectricalDemand.ElectricalDemand(environment,
                                                          method=1,
                                                          annualDemand=3000,
                                                          profileType="H0")

            #  Create apartment
            apartment = Apartment.Apartment(environment)

            #  Add demands to apartment
            apartment.addMultipleEntities([heat_demand, el_demand])

            extended_building = build_ex.BuildingExtended(environment,
                                                          build_year=1962,
                                                          mod_year=2003,
                                                          build_type=0,
                                                          roof_usabl_pv_area=30,
                                                          net_floor_area=150,
                                                          height_of_floors=3,
                                                          nb_of_floors=2,
                                                          neighbour_buildings=0,
                                                          residential_layout=0,
                                                          attic=0, cellar=1,
                                                          construction_type='heavy',
                                                          dormer=0)

            #  Add apartment to extended building
            extended_building.addEntity(entity=apartment)

            position = point.Point(i * 10, 0)

            city_object.add_extended_building(
                extended_building=extended_building,
                position=position)

        city = copy.deepcopy(city_object)

        #  Energy network generator
        list_lhn_1 = [1001, 1002, 1003, 1004, 1005, 1006, 1007]

        dict_lhn = {}
        dict_lhn[1] = {'type': 'heating', 'method': 1,
                       'nodelist': list_lhn_1}

        enetgen.add_energy_networks_to_city(city=city,
                                            dict_data=dict_lhn)

        #  Generate energy systems
        list_esys = [(1001, 1, 1)]

        esysgen.gen_esys_for_city(city=city, list_data=list_esys)

        #  Check if requirements are fulfilld
        checkeb.check_eb_requirements(city=city)

        #  ##############################################################

        city = copy.deepcopy(city_object)

        #  Energy network generator
        list_lhn_1 = [1001, 1003]
        list_lhn_2 = [1002, 1004, 1005, 1006, 1007]

        dict_lhn = {}
        dict_lhn[1] = {'type': 'heating', 'method': 1,
                       'nodelist': list_lhn_1}
        dict_lhn[2] = {'type': 'heating', 'method': 1,
                       'nodelist': list_lhn_2}

        enetgen.add_energy_networks_to_city(city=city,
                                            dict_data=dict_lhn)

        #  Generate energy systems
        list_esys = [(1001, 1, 1)]

        esysgen.gen_esys_for_city(city=city, list_data=list_esys)

        #  Check if requirements are fulfilld
        try:
            checkeb.check_eb_requirements(city=city)
        except checkeb.EnergySupplyException:
            print('Raised EnergySupplyException --> Passed')
        except:
            raise AssertionError()

        #  ##############################################################

        city = copy.deepcopy(city_object)

        #  Energy network generator
        list_lhn_1 = [1001, 1003]
        list_lhn_2 = [1002, 1004, 1005, 1006, 1007]

        dict_lhn = {}
        dict_lhn[1] = {'type': 'heating', 'method': 1,
                       'nodelist': list_lhn_1}
        dict_lhn[2] = {'type': 'heating', 'method': 1,
                       'nodelist': list_lhn_2}

        enetgen.add_energy_networks_to_city(city=city,
                                            dict_data=dict_lhn)

        #  Generate energy systems
        list_esys = [(1001, 1, 1), (1002, 1, 1)]

        esysgen.gen_esys_for_city(city=city, list_data=list_esys)

        #  Check if requirements are fulfilld
        checkeb.check_eb_requirements(city=city)

        #  ##############################################################

        city = copy.deepcopy(city_object)

        #  Energy network generator
        list_lhn_1 = [1001, 1003]
        list_lhn_2 = [1002, 1004, 1005, 1006, 1007]

        dict_lhn = {}
        dict_lhn[1] = {'type': 'heating', 'method': 1,
                       'nodelist': list_lhn_1}
        dict_lhn[2] = {'type': 'heating', 'method': 1,
                       'nodelist': list_lhn_2}

        enetgen.add_energy_networks_to_city(city=city,
                                            dict_data=dict_lhn)

        #  Generate energy systems
        list_esys = [(1001, 1, 1), (1002, 1, 1)]

        esysgen.gen_esys_for_city(city=city, list_data=list_esys)

        #  Check if requirements are fulfilld
        try:
            checkeb.check_eb_requirements(city=city)
        except checkeb.EnergySupplyException:
            print('Raised EnergySupplyException --> Passed')
        except:
            raise AssertionError()

        #  ##############################################################

        city = copy.deepcopy(city_object)

        #  Energy network generator
        list_lhn_1 = [1001, 1003]
        list_lhn_2 = [1002, 1004, 1005, 1006, 1007]

        dict_lhn = {}
        dict_lhn[1] = {'type': 'heating', 'method': 1,
                       'nodelist': list_lhn_1}
        dict_lhn[2] = {'type': 'heating', 'method': 1,
                       'nodelist': list_lhn_2}

        enetgen.add_energy_networks_to_city(city=city,
                                            dict_data=dict_lhn)

        #  Generate energy systems
        list_esys = [(1001, 1, 1), (1002, 1, 1), (1003, 1, 1)]

        esysgen.gen_esys_for_city(city=city, list_data=list_esys)

        checkeb.check_eb_requirements(city=city)
