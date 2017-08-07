#!/usr/bin/env python
# coding=utf-8
"""
Pytest script for city object of pycity_calc
"""

from __future__ import division
import copy
import shapely.geometry.point as point

import pycity.classes.demand.DomesticHotWater as DHW
import pycity_calc.cities.city as cit

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
        city_object = cit.City(environment=fixture_environment)

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

    def test_get_annual_space_heating_demand(self, fixture_environment,
                                             fixture_building):
        """

        Parameters
        ----------
        fixture_building
        """

        #  Generate city object
        city = cit.City(environment=fixture_environment)

        for i in range(3):
            pos = point.Point(0, i)
            build_copy = copy.deepcopy(fixture_building)
            city.add_extended_building(extended_building=build_copy,
                                       position=pos)

        assert abs(city.get_annual_space_heating_demand() - 3 * 13000) \
               / (3 * 13000) <= 0.001

        assert abs(city.get_annual_space_heating_demand(nodelist=[1001, 1002])
                   - 2 * 13000) / (2 * 13000) <= 0.001

    def test_get_annual_el_demand(self, fixture_environment,
                                  fixture_building):
        """

        Parameters
        ----------
        fixture_building
        """

        #  Generate city object
        city = cit.City(environment=fixture_environment)

        for i in range(3):
            pos = point.Point(0, i)
            build_copy = copy.deepcopy(fixture_building)
            city.add_extended_building(extended_building=build_copy,
                                       position=pos)

        assert abs(city.get_annual_el_demand() - 3 * 3000) \
               / (3 * 3000) <= 0.001

        assert abs(city.get_annual_el_demand(nodelist=[1001, 1002])
                   - 2 * 3000) / (2 * 3000) <= 0.001

    def test_get_annual_space_heating_demand2(self, fixture_environment,
                                             fixture_building):
        """

        Parameters
        ----------
        fixture_building
        """

        #  Generate city object
        city = cit.City(environment=fixture_environment)

        t_high = 60
        t_low = 25

        #  Generate dhw object
        dhw_obj = \
            DHW.DomesticHotWater(environment=fixture_building.environment,
                                 tFlow=t_high,
                                 thermal=True,
                                 method=1,  # Annex 42
                                 dailyConsumption=100,
                                 supplyTemperature=t_low)

        ref_energy = 100 * 4180 * (t_high - t_low) / (3600 * 1000) * 365

        #  Add dhw object to bulding
        fixture_building.apartments[0].addEntity(dhw_obj)

        for i in range(3):
            pos = point.Point(0, i)
            build_copy = copy.deepcopy(fixture_building)
            city.add_extended_building(extended_building=build_copy,
                                       position=pos)

        assert abs(city.get_annual_dhw_demand() - 3 * ref_energy) \
               / (3 * ref_energy) <= 0.001

        assert abs(city.get_annual_dhw_demand(nodelist=[1001, 1002])
                   - 2 * ref_energy) / (2 * ref_energy) <= 0.001

        assert abs(city.get_total_annual_th_demand() - 3 *
                   (ref_energy + 13000)) \
               / (3 * (ref_energy + 13000)) <= 0.001

        assert abs(city.get_total_annual_th_demand(nodelist=[1001, 1002]) - 2 *
                   (ref_energy + 13000)) \
               / (2 * (ref_energy + 13000)) <= 0.001
