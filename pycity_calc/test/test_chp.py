#!/usr/bin/env python
# coding=utf-8
"""
Test script for BatteryExtended class
"""
from __future__ import division
from decimal import *

import pycity_calc.energysystems.chp as Chp
import pycity_calc.economic.energy_sys_cost.chp_cost as chp_cost

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

    def test_chp_cost(self):

        p_el_nom = 900 # in kW

        chp_cost.calc_invest_cost_chp(p_el_nom,
                                      method='asue2015',
                                      with_inst=True,
                                      use_el_input=True,
                                      q_th_nom=None)

        p_el_nom = 1100  # in kW

        chp_cost.calc_invest_cost_chp(p_el_nom,
                                      method='asue2015',
                                      with_inst=True,
                                      use_el_input=True,
                                      q_th_nom=None)

        chp_cost.calc_invest_cost_chp(p_el_nom,
                                      method='asue2015',
                                      with_inst=True,
                                      use_el_input=False,
                                      q_th_nom=12)

        p_el_nom = 5  # in kW

        chp_cost.calc_invest_cost_chp(p_el_nom,
                                      method='spieker',
                                      with_inst=True,
                                      use_el_input=True,
                                      q_th_nom=None)

        p_el_nom = 50  # in kW

        chp_cost.calc_invest_cost_chp(p_el_nom,
                                      method='spieker',
                                      with_inst=True,
                                      use_el_input=True,
                                      q_th_nom=None)

        p_el_nom = 250  # in kW

        chp_cost.calc_invest_cost_chp(p_el_nom,
                                      method='spieker',
                                      with_inst=True,
                                      use_el_input=True,
                                      q_th_nom=None)

        p_el_nom = 450  # in kW

        chp_cost.calc_invest_cost_chp(p_el_nom,
                                      method='spieker',
                                      with_inst=True,
                                      use_el_input=True,
                                      q_th_nom=None)

        p_el_nom = 550  # in kW

        chp_cost.calc_invest_cost_chp(p_el_nom,
                                      method='spieker',
                                      with_inst=True,
                                      use_el_input=True,
                                      q_th_nom=None)

        p_el_nom = 800  # in kW

        chp_cost.calc_invest_cost_chp(p_el_nom,
                                      method='spieker',
                                      with_inst=True,
                                      use_el_input=True,
                                      q_th_nom=None)

    def test_nb_switches(self, fixture_environment):
        """
        Test checks returning of number of switching events
        """

        chp = Chp.ChpExtended(environment=fixture_environment,
                              q_nominal=1000)

        #  Manipulate results array (8 switching events)
        chp.totalQOutput[1] = 1
        chp.totalQOutput[2] = 1
        chp.totalQOutput[3] = 2
        chp.totalQOutput[4] = 3

        chp.totalQOutput[25] = 3
        chp.totalQOutput[27] = 3.9

        chp.totalQOutput[50] = 0.5

        nb_switch = chp.calc_nb_on_off_switching()

        assert nb_switch == 8
