#!/usr/bin/env python
# coding=utf-8
"""
Test script for BatteryExtended class
"""
from decimal import *

import pycity_calc.energysystems.chp as Chp

from pycity_calc.test.pycity_calc_fixtures import fixture_environment, \
    fixture_chp_el, fixture_chp_th


class Test_Chp():
    def test_chp_init(self, fixture_environment):
        chp = Chp.ChpExtended(environment=fixture_environment,
                              q_nominal=1000, p_nominal=300)

        assert chp._kind == 'chp'
        assert chp.chp_type == 'ASUE_2015'

        # TODO test both operation modi

    def test_thOperation_calc_chp_th_power_output(self, fixture_chp_th):
        # thermal power is 10000 W
        # lower_activation_limit is 0.6 -> 6000 W
        control_signal = 5000
        th_power = fixture_chp_th.thOperation_calc_chp_th_power_output(
            control_signal)
        assert th_power == 0

        control_signal = 6000
        th_power = fixture_chp_th.thOperation_calc_chp_th_power_output(
            control_signal)
        assert th_power == 6000

        control_signal = 12000
        th_power = fixture_chp_th.thOperation_calc_chp_th_power_output(
            control_signal)
        assert th_power == 10000

    def test_thOperation_calc_chp_el_power_output(self, fixture_chp_th):
        # thermal power is 10000 W
        # lower_activation_limit is 0.6 -> 6000 W
        control_signal = 5000
        el_power = fixture_chp_th.thOperation_calc_chp_el_power_output(
            control_signal)
        assert el_power == 0

        control_signal = 6000
        el_power = fixture_chp_th.thOperation_calc_chp_el_power_output(
            control_signal)
        assert round(el_power, 2) == 2262.05

        control_signal = 12000
        el_power = fixture_chp_th.thOperation_calc_chp_el_power_output(
            control_signal)
        assert round(el_power, 2) == 4127.95

    def test_thOperation_calc_chp_fuel_power_input(self, fixture_chp_th):
        control_signal = 5000
        fuel_power = fixture_chp_th.thOperation_calc_chp_fuel_power_input(
            control_signal)
        assert fuel_power == 0

        control_signal = 6000
        fuel_power = fixture_chp_th.thOperation_calc_chp_fuel_power_input(
            control_signal)
        assert round(fuel_power, 2) == 9496.61

        control_signal = 12000
        fuel_power = fixture_chp_th.thOperation_calc_chp_fuel_power_input(
            control_signal)
        assert round(fuel_power, 2) == 16239.03

    def test_thOperation_calc_chp_th_efficiency(self, fixture_chp_th):
        control_signal = 5000
        th_eff = fixture_chp_th.thOperation_calc_chp_th_efficiency(
            control_signal)
        assert th_eff == 0

        control_signal = 6000
        th_eff = fixture_chp_th.thOperation_calc_chp_th_efficiency(
            control_signal)
        assert round(th_eff, 4) == 0.6318

        control_signal = 12000
        th_eff = fixture_chp_th.thOperation_calc_chp_th_efficiency(
            control_signal)
        assert round(th_eff, 4) == 0.6158

    def test_thOperation_calc_chp_el_efficiency(self, fixture_chp_th):
        control_signal = 5000
        el_eff = fixture_chp_th.thOperation_calc_chp_el_efficiency(
            control_signal)
        assert el_eff == 0

        control_signal = 6000
        el_eff = fixture_chp_th.thOperation_calc_chp_el_efficiency(
            control_signal)
        assert round(el_eff, 4) == 0.2382

        control_signal = 12000
        el_eff = fixture_chp_th.thOperation_calc_chp_el_efficiency(
            control_signal)
        assert round(el_eff, 4) == 0.2542

    def test_elOperation_calc_chp_el_power_output(self, fixture_chp_el):
        # electrical power is 4500 W
        # lower_activation_limit is 0.6 -> 2700 W
        control_signal = 2500
        th_power = fixture_chp_el.elOperation_calc_chp_el_power_output(
            control_signal)
        assert th_power == 0

        control_signal = 3000
        th_power = fixture_chp_el.elOperation_calc_chp_el_power_output(
            control_signal)
        assert th_power == 3000

        control_signal = 6000
        th_power = fixture_chp_el.elOperation_calc_chp_el_power_output(
            control_signal)
        assert th_power == 4500

    def test_elOperation_calc_chp_th_power_output(self, fixture_chp_el):
        # electrical power is 4500 W
        # lower_activation_limit is 0.6 -> 2700 W
        control_signal = 2500
        el_power = fixture_chp_el.elOperation_calc_chp_th_power_output(
            control_signal)
        assert el_power == 0

        control_signal = 3000
        el_power = fixture_chp_el.elOperation_calc_chp_th_power_output(
            control_signal)
        assert round(el_power, 2) == 7635.91

        control_signal = 6000
        el_power = fixture_chp_el.elOperation_calc_chp_th_power_output(
            control_signal)
        assert round(el_power, 2) == 10770.31

    def test_elOperation_calc_chp_fuel_power_input(self, fixture_chp_el):
        # electrical power is 4500 W
        # lower_activation_limit is 0.6 -> 2700 W
        control_signal = 2500
        fuel_power = fixture_chp_el.elOperation_calc_chp_fuel_power_input(
            control_signal)
        assert fuel_power == 0

        control_signal = 3000
        fuel_power = fixture_chp_el.elOperation_calc_chp_fuel_power_input(
            control_signal)
        assert round(fuel_power, 2) == 12225.18

        control_signal = 6000
        fuel_power = fixture_chp_el.elOperation_calc_chp_fuel_power_input(
            control_signal)
        assert round(fuel_power, 2) == 17552.08

    def test_elOperation_calc_chp_th_efficiency(self, fixture_chp_el):
        # electrical power is 4500 W
        # lower_activation_limit is 0.6 -> 2700 W
        control_signal = 2500
        th_eff = fixture_chp_el.elOperation_calc_chp_th_efficiency(
            control_signal)
        assert th_eff == 0

        control_signal = 3000
        th_eff = fixture_chp_el.elOperation_calc_chp_th_efficiency(
            control_signal)
        assert round(th_eff, 4) == 0.6246

        control_signal = 6000
        th_eff = fixture_chp_el.elOperation_calc_chp_th_efficiency(
            control_signal)
        assert round(th_eff, 4) == 0.6136

    def test_elOperation_calc_chp_el_efficiency(self, fixture_chp_el):
        # electrical power is 4500 W
        # lower_activation_limit is 0.6 -> 2700 W
        control_signal = 2500
        el_eff = fixture_chp_el.elOperation_calc_chp_el_efficiency(
            control_signal)
        assert el_eff == 0

        control_signal = 3000
        el_eff = fixture_chp_el.elOperation_calc_chp_el_efficiency(
            control_signal)
        assert round(el_eff, 4) == 0.2454

        control_signal = 6000
        el_eff = fixture_chp_el.elOperation_calc_chp_el_efficiency(
            control_signal)
        assert round(el_eff, 4) == 0.2564
