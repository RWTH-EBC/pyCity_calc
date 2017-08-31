# coding=utf-8
"""
Pytest script for BuildingExtended
"""

from __future__ import division
import pycity_calc.buildings.building as build_ex
import pycity_base.classes.demand.DomesticHotWater as DHW

from pycity_calc.test.pycity_calc_fixtures import fixture_th_demand, \
    fixture_environment, fixture_el_demand, fixture_apartment, fixture_building


class Test_BuildingExtended():
    """
    Test class for BuildingExtende object
    """

    def test_building_init(self, fixture_environment):
        """
        Test method for building object initialization

        Parameters
        ----------
        fixture_environment : object
            Fixture environment object of pycity_calc
        """
        #  Create extended building object
        extended_building = build_ex.BuildingExtended(fixture_environment,
                                                      build_year=1962,
                                                      mod_year=2003,
                                                      build_type=0)

        #  Check if inheritance from pycity is working correctly
        assert extended_building._kind == 'building'

    def test_get_apartment_nb(self, fixture_building, fixture_apartment):
        """
        Test method to get number of apartments.

        Parameters
        ----------
        fixture_building : object
            Fixture building object
        fixture_apartment : object
            Fixture apartment object
        """
        building = fixture_building

        nb_apartments = building.get_number_of_apartments()

        assert nb_apartments == 1

        #  Add further apartment
        building.addEntity(fixture_apartment)
        nb_apartments = building.get_number_of_apartments()

        assert nb_apartments == 2

    def test_get_nb_occupants(self, fixture_building, fixture_apartment):
        """
        Test method to get number of occupants.

        Parameters
        ----------
        fixture_building : object
            Fixture building object
        fixture_apartment : object
            Fixture apartment object
        """
        building = fixture_building

        #  Get number of occupants
        nb_occ = building.get_number_of_occupants()

        nb_occ == None

        #  Generate new apartment
        apartment = fixture_apartment
        #  Add new occupants
        apartment.nb_of_occupants = 2

        #  Add two more apartments to building
        building.addMultipleEntities([apartment, apartment])

        #  Get number of occupants
        nb_occ = building.get_number_of_occupants()

        nb_occ == 4

    def test_get_nb_occupants_2(self, fixture_building, fixture_apartment):
        """
        Test method to get number of occupants.

        Parameters
        ----------
        fixture_building : object
            Fixture building object
        fixture_apartment : object
            Fixture apartment object
        """
        building = fixture_building

        #  Get number of occupants
        nb_occ = building.get_number_of_occupants()

        nb_occ == None

        #  Generate new apartment
        apartment = fixture_apartment

        #  Add new occupants
        apartment.nb_of_occupants = 2

        #  Add two more apartments to building
        building.addEntity(apartment)

        #  Get number of occupants
        nb_occ = building.get_number_of_occupants()

        nb_occ == 2

    def test_get_nfa_occupants(self, fixture_building, fixture_apartment):
        """
        Test method to get total net floor area of building.

        Parameters
        ----------
        fixture_building : object
            Fixture building object
        fixture_apartment : object
            Fixture apartment object
        """
        building = fixture_building
        #  Access apartment
        building.apartments[0].net_floor_area = 150

        #  Generate new apartment
        apartment = fixture_apartment
        #  Add new occupants
        apartment.net_floor_area = 100

        #  Add two more apartments to building
        building.addEntity(apartment)

        #  Get number of occupants
        nfa = building.get_net_floor_area_of_building()

        nfa == 250

    def test_get_annual_space_heat_demand(self, fixture_building):
        """

        Parameters
        ----------
        fixture_building : object
            Fixture building object
        """
        assert abs(fixture_building.get_annual_space_heat_demand() - 13000) \
               / 13000 <= 0.001

    def test_get_annual_el_demand(self, fixture_building):
        """

        Parameters
        ----------
        fixture_building : object
            Fixture building object
        """
        assert abs(fixture_building.get_annual_el_demand() - 3000) \
               / 3000 <= 0.001

    def test_get_annual_dhw_demand(self, fixture_building):
        """

        Parameters
        ----------
        fixture_building : object
            Fixture building object
        """
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

        assert abs(fixture_building.get_annual_dhw_demand() - ref_energy) \
               / ref_energy <= 0.001

    def test_get_build_total_height(self, fixture_building):
        """

        Parameters
        ----------
        fixture_building : object
            Fixture building object
        """

        assert fixture_building.get_build_total_height() is None

        fixture_building.nb_of_floors = 2
        fixture_building.height_of_floors = 3

        assert fixture_building.get_build_total_height() == 6
