#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
from __future__ import division

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
import pycity_calc.toolbox.modifiers.merge_buildings as mergebuild


class TestMergeBuild(object):
    def test_build_merge_city(self):
        #  List of lists of buildings, which should be merged together
        list_lists_merge = [[1001, 1002], [1003, 1004]]

        #  Generate test city
        #  ######################################################################

        #  Create extended environment of pycity_calc
        year = 2017
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

        #  Iterate 5 times to generate 3 building objects
        for i in range(5):
            #  Create demands (with standardized load profiles (method=1))
            heat_demand = SpaceHeating.SpaceHeating(environment,
                                                    method=1,
                                                    profile_type='HEF',
                                                    livingArea=100,
                                                    specificDemand=120)

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

        # ######################################################################

        #  Modify specific attributes of buildings
        city_object.nodes[1004]['entity'].roof_usabl_pv_area = 10
        city_object.nodes[1004]['entity'].net_floor_area = 100

        #  Merge buildings together
        city_new = mergebuild.merge_buildings_in_city(city=city_object,
                                                      list_lists_merge=
                                                      list_lists_merge)

        assert len(city_new.nodes()) == 3
        assert sorted(city_new.nodes()) == [1001, 1003, 1005]

        assert len(city_new.nodes[1001]['entity'].apartments) == 2
        assert len(city_new.nodes[1003]['entity'].apartments) == 2
        assert len(city_new.nodes[1005]['entity'].apartments) == 1

        assert city_new.nodes[1001]['entity'].build_year == 1962
        assert city_new.nodes[1001]['entity'].mod_year == 2003
        assert city_new.nodes[1001]['entity'].build_type == 0
        assert city_new.nodes[1001]['entity'].net_floor_area == 300
        assert city_new.nodes[1001]['entity'].roof_usabl_pv_area == 2 * 30

        assert city_new.nodes[1003]['entity'].roof_usabl_pv_area == 10 + 30
        assert city_new.nodes[1003]['entity'].net_floor_area == 250
