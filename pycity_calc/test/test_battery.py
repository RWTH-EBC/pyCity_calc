#!/usr/bin/env python
# coding=utf-8
"""
Test script for BatteryExtended class
"""

import pycity_calc.energysystems.battery as batt

from pycity_calc.test.pycity_calc_fixtures import fixture_environment, \
    fixture_battery


class Test_Battery():
    def test_battery_init(self, fixture_environment):
        battery = batt.BatteryExtended(environment=fixture_environment,
                                       soc_init_ratio=1, capacity_kwh=100)
        assert battery._kind == 'battery'

    def test_get_capacity_in_kwh(self, fixture_environment, fixture_battery):
        cap_kwh = fixture_battery.get_battery_capacity_in_kwh()
        assert cap_kwh == 100

    def test_calc_battery_max_p_el_out(self, fixture_environment):
        #  Battery should be able to have maximal output power of 400 kW
        #  over 900 seconds
        soc_init_ratio = 1
        battery = batt.BatteryExtended(environment=fixture_environment,
                                       soc_init_ratio=soc_init_ratio,
                                       capacity_kwh=100, self_discharge=0,
                                       eta_charge=1, eta_discharge=1)
        p_out_max = battery.calc_battery_max_p_el_out(soc_ratio_current=
                                                      soc_init_ratio)
        assert p_out_max == 400000  # Max output power is 400 kW

        p_out_max = battery.calc_battery_max_p_el_out()
        assert p_out_max == 400000  # Max output power is 400 kW


    def test_discharge_possible(self, fixture_environment):
        soc_init_ratio = 1
        battery = batt.BatteryExtended(environment=fixture_environment,
                                       soc_init_ratio=soc_init_ratio,
                                       capacity_kwh=100, self_discharge=0,
                                       eta_charge=1, eta_discharge=1)
        bol_value = battery.battery_discharge_possible(p_el_out=390000,
                                                       soc_ratio_current=soc_init_ratio)
        assert bol_value == True

        bol_value = battery.battery_discharge_possible(p_el_out=410000)
        assert bol_value == False

    def test_calc_battery_max_p_el_in(self, fixture_environment):
        battery = batt.BatteryExtended(environment=fixture_environment,
                                       soc_init_ratio=0,
                                       capacity_kwh=100, self_discharge=0,
                                       eta_charge=1, eta_discharge=1)
        p_max_in = battery.calc_battery_max_p_el_in()

        assert p_max_in == 400000

        soc_ratio_new = 0.5
        p_max_in = battery.calc_battery_max_p_el_in(soc_ratio_current=soc_ratio_new)

        assert p_max_in == 200000



    def battery_charge_possible(self, fixture_environment):
        soc_init_ratio = 0.5
        battery = batt.BatteryExtended(environment=fixture_environment,
                                       soc_init_ratio=soc_init_ratio,
                                       capacity_kwh=100, self_discharge=0,
                                       eta_charge=1, eta_discharge=1)
        bol_value = battery.battery_discharge_possible(p_el_out=195000,
                                                       soc_ratio_current=0.5)
        assert bol_value == True

        bol_value = battery.battery_discharge_possible(p_el_out=205000)

        assert bol_value == False

    def test_self_discharging(self, fixture_environment):
        soc_init_ratio = 1
        battery = batt.BatteryExtended(environment=fixture_environment,
                                       soc_init_ratio=soc_init_ratio,
                                       capacity_kwh=100, self_discharge=0.5,
                                       eta_charge=1, eta_discharge=1)

        new_soc_share = battery.calc_battery_soc_next_timestep(p_el_out=0,
                                                               soc_ratio_current=
                                                               soc_init_ratio,
                                                               p_el_in=0,
                                                               set_new_soc=True)
        assert new_soc_share == 0.5
        assert battery.soc_ratio_current == 0.5

    def test_eta_discharging(self, fixture_environment):
        soc_init_ratio = 1
        battery = batt.BatteryExtended(environment=fixture_environment,
                                       soc_init_ratio=soc_init_ratio,
                                       capacity_kwh=100, self_discharge=0,
                                       eta_charge=1, eta_discharge=0.5)

        new_soc_share = battery.calc_battery_soc_next_timestep(p_el_out=200000,
                                                               p_el_in=0,
                                                               soc_ratio_current=
                                                               soc_init_ratio,
                                                               set_new_soc=True)
        assert new_soc_share == 0
        assert battery.soc_ratio_current == 0

    def test_eta_charging(self, fixture_environment):
        soc_init_ratio = 0
        battery = batt.BatteryExtended(environment=fixture_environment,
                                       soc_init_ratio=soc_init_ratio,
                                       capacity_kwh=100, self_discharge=0,
                                       eta_charge=0.5, eta_discharge=1)

        new_soc_share = battery.calc_battery_soc_next_timestep(p_el_out=0,
                                                               p_el_in=800000,
                                                               soc_ratio_current=
                                                               soc_init_ratio)
        assert new_soc_share == 1
