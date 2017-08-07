#!/usr/bin/env python
# coding=utf-8
"""
Test script for BoilerExtended class
"""
from __future__ import division
import pycity_calc.energysystems.electricalHeater as eHeater

from pycity_calc.test.pycity_calc_fixtures import fixture_environment, \
    fixture_electricalHeater
from decimal import *


class Test_ElectricalHeater():
    def test_electricalHeater_init(self, fixture_environment):
        Heater = eHeater.ElectricalHeaterExtended(
            environment=fixture_environment,
            q_nominal=7520, eta=0.78)

        assert Heater._kind == 'electricalheater'

    def test_calc_el_heater_thermal_power_output(self,
                                                 fixture_electricalHeater):
        # thermal power is 10000 W
        # lower_activation_limit is 0 -> always on
        control_signal = -1000
        th_power = fixture_electricalHeater.calc_el_heater_thermal_power_output(
            control_signal)
        assert th_power == 0

        control_signal = 6000
        th_power = fixture_electricalHeater.calc_el_heater_thermal_power_output(
            control_signal)
        assert th_power == 6000

        control_signal = 12000
        th_power = fixture_electricalHeater.calc_el_heater_thermal_power_output(
            control_signal)
        assert th_power == 10000

    def test_calc_el_heater_electric_power_input(self,
                                                 fixture_electricalHeater):
        # thermal power=10000 W, eta=0.9

        control_signal = 0
        el_power = fixture_electricalHeater.calc_el_heater_electric_power_input(
            control_signal)
        assert el_power == 0

        control_signal = 6000
        el_power = fixture_electricalHeater.calc_el_heater_electric_power_input(
            control_signal)
        assert round(el_power, 2) == 6666.67

