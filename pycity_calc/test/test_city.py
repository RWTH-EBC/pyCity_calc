#!/usr/bin/env python
# coding=utf-8
"""
Pytest script for city object of pycity_calc
"""

import shapely.geometry.point as point

import pycity_calc.cities.city as city

from pycity_calc.test.pycity_calc_fixtures import fixture_building, \
    fixture_environment, fixture_city, fixture_apartment, fixture_th_demand, \
    fixture_el_demand


class Test_City():
    """
    Pytest class for city object
    """
    def test_init(self, fixture_environment):
        """
        Test method to check initialization of city object.

        Parameters
        ----------
        fixture_environment : object
            Fixture environment object of pycity_calc
        """

        #  Generate city object
        city_object = city.City(environment=fixture_environment)

        #  Check inheritance from citydistrict object of pycity
        assert city_object._kind == 'citydistrict'

    def test_add_extended_building(self, fixture_building, fixture_city):
        """
        Test method to check method for adding extende buildings

        Parameters
        ----------
        fixture_building : object
            Extended building object
        fixture_city : object
            City object
        """

        building = fixture_building
        city = fixture_city

        assert city.nodelist_building == []

        #  Add two buildings to city
        city.add_extended_building(building, position=point.Point(0, 0))
        city.add_extended_building(building, position=point.Point(0, 10))

        assert len(city.nodelist_building) == 2
