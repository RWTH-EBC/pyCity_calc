#!/usr/bin/env python
# coding=utf-8
"""
Test script for BoilerExtended class
"""
from __future__ import division
import pycity_calc.energysystems.boiler as Boil

from pycity_calc.test.pycity_calc_fixtures import fixture_environment, \
    fixture_boiler
from decimal import *


class Test_Boiler():
    def test_boiler_init(self, fixture_environment):
        boiler = Boil.BoilerExtended(environment=fixture_environment,
                                     q_nominal=7520, eta=0.78)

        assert boiler._kind == 'boiler'

    def test_calc_boiler_thermal_power_output(self, fixture_boiler):
        # thermal power is 10000 W
        # lower_activation_limit is 0 -> always on
        control_signal = -1000
        th_power = fixture_boiler.calc_boiler_thermal_power_output(
            control_signal)
        assert th_power == 0

        control_signal = 6000
        th_power = fixture_boiler.calc_boiler_thermal_power_output(
            control_signal)
        assert th_power == 6000

        control_signal = 12000
        th_power = fixture_boiler.calc_boiler_thermal_power_output(
            control_signal)
        assert th_power == 10000

    def test_calc_boiler_fuel_power_input(self, fixture_boiler):
        # thermal power=10000 W, eta=0.9

        control_signal = -1000
        fuel_power = fixture_boiler.calc_boiler_fuel_power_input(
            control_signal)
        assert fuel_power == 0

        control_signal = 6000
        fuel_power = fixture_boiler.calc_boiler_fuel_power_input(
            control_signal)
        assert round(fuel_power, 2) == 6666.67

        control_signal = 12000
        fuel_power = fixture_boiler.calc_boiler_fuel_power_input(
            control_signal)
        assert round(fuel_power, 2) == 11111.11
