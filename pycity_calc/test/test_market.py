# coding=utf-8
"""
Pytest file for market class
"""

import pycity_calc.environments.market as mark
from pycity_calc.test.pycity_calc_fixtures import fixture_market


class Test_Market(object):
    """
    Test class for market object
    """

    def test_gas_price_res(self, fixture_market):
        year = 2012
        res_demand = 15000

        spec_cost = fixture_market.get_spec_gas_cost(type='res', year=year,
                                                     annual_demand=res_demand)
        assert spec_cost == 0.0648

    def test_el_price_res(self, fixture_market):
        year = 2012
        res_demand = 3000

        spec_cost = fixture_market.get_spec_el_cost(type='res', year=year,
                                                     annual_demand=res_demand)
        assert spec_cost == 0.2676

    def test_gas_price_ind(self, fixture_market):
        year = 2012
        ind_demand = 300000

        spec_cost = fixture_market.get_spec_gas_cost(type='ind', year=year,
                                                     annual_demand=ind_demand)
        assert spec_cost == 0.0396

    def test_el_price_ind(self, fixture_market):
        year = 2012
        ind_demand = 600000

        spec_cost = fixture_market.get_spec_el_cost(type='ind', year=year,
                                                     annual_demand=ind_demand)
        assert spec_cost == 0.1297
