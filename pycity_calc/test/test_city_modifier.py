#!/usr/bin/env python
# coding=utf-8
"""
Test script for mod_city_geo_pos.py
"""
from __future__ import division
import pycity_calc.toolbox.modifiers.mod_city_geo_pos as citymod

# import sympy.geometry.point as point
import shapely.geometry.point as point

import pycity_calc.cities.scripts.city_generator.city_generator as citgen

import pycity.classes.demand.SpaceHeating as SpaceHeating
import pycity.classes.demand.ElectricalDemand as ElectricalDemand
import pycity.classes.demand.Apartment as Apartment
import pycity_calc.buildings.building as build_ex
import pycity_calc.cities.city as cit

from pycity_calc.test.pycity_calc_fixtures import fixture_building, \
    fixture_environment, fixture_city, fixture_apartment, fixture_th_demand, \
    fixture_el_demand


class TestCityModifier():

    def test_set_zero_coord_and_get_min_x_y_coord(self, fixture_environment):
        #  Generate city object
        city = cit.City(environment=fixture_environment)

        list_x_coord = [15, 25, 40]
        list_y_coord = [25, 12, 45]

        for i in range(0, 3):
            #  Create demands (with standardized load profiles (method=1))
            heat_demand = SpaceHeating.SpaceHeating(fixture_environment,
                                                    method=1,
                                                    profile_type='HEF',
                                                    livingArea=100,
                                                    specificDemand=130)

            el_demand = ElectricalDemand.ElectricalDemand(fixture_environment,
                                                          method=1,
                                                          annualDemand=3000,
                                                          profileType="H0")

            #  Create apartment
            apartment = Apartment.Apartment(fixture_environment)

            #  Add demands to apartment
            apartment.addMultipleEntities([heat_demand, el_demand])

            #  Create extended building object
            extended_building = build_ex.BuildingExtended(fixture_environment,
                                                          build_year=1970,
                                                          mod_year=2003,
                                                          build_type=0)

            #  Add apartment to extended building
            extended_building.addEntity(entity=apartment)

            position = point.Point(list_x_coord[i], list_y_coord[i])

            #  Add 3 extended buildings to city object
            city.add_extended_building(extended_building=extended_building,
                                       position=position)

        # Add street network
        #  Add str nodes
        node_1 = city.add_street_node(position=point.Point(10, 20))
        node_2 = city.add_street_node(position=point.Point(30, 20))
        node_3 = city.add_street_node(position=point.Point(50, 20))

        #  Add edges
        city.add_edge(node_1, node_2, network_type='street')
        city.add_edge(node_2, node_3, network_type='street')

        tuple_min = citymod.get_min_x_y_coord(city)

        assert tuple_min[0] == 10
        assert tuple_min[1] == 12

        #  Convert points
        citymod.set_zero_coordinate(city, buffer=0)

        tuple_min = citymod.get_min_x_y_coord(city)

        assert tuple_min[0] == 0
        assert tuple_min[1] == 0

        #  Convert points
        citymod.set_zero_coordinate(city, buffer=10)

        tuple_min = citymod.get_min_x_y_coord(city)

        assert tuple_min[0] == 10
        assert tuple_min[1] == 10
