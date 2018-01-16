#!/usr/bin/env python
# coding=utf-8
"""
Test script for BoilerExtended class
"""
from __future__ import division
import pycity_calc.energysystems.heatPumpSimple as hp

from pycity_calc.test.pycity_calc_fixtures import fixture_environment
from decimal import *


class Test_heatPumpSimple():
    def test_heatPumpSimple_init(self, fixture_environment):
        heatpump = hp.heatPumpSimple(environment=fixture_environment,
                                     q_nominal=7520,
                                     hp_type='aw',
                                     t_sink=45)

        assert heatpump._kind == 'heatpump'

        heatpump = hp.heatPumpSimple(environment=fixture_environment,
                                     q_nominal=7520,
                                     hp_type='ww')

        assert heatpump._kind == 'heatpump'

    def test_calc_hp_carnot_cop(self, fixture_environment):
        # thermal power is 10000 W
        # t_sink = 45 °C
        # lower_activation_limit is 0.5
        # hp_type = 'aw' , quality_grade = 0.36

        heatpump = hp.heatPumpSimple(environment=fixture_environment,
                                     q_nominal=10000,
                                     hp_type='aw',
                                     t_sink=45,
                                     qual_grade_aw=0.36)

        t_source = 0
        cop_max = heatpump.calc_hp_carnot_cop(t_source)
        assert round(cop_max, 2) == 7.07

        t_source = 20
        cop_max = heatpump.calc_hp_carnot_cop(t_source)
        assert round(cop_max, 3) == 12.726

    def test_calc_hp_cop_with_quality_grade(self, fixture_environment):
        # thermal power is 10000 W
        # t_sink = 45 °C
        # lower_activation_limit is 0.5
        # hp_type = 'aw' , quality_grade = 0.36

        heatpump = hp.heatPumpSimple(environment=fixture_environment,
                                     q_nominal=10000,
                                     hp_type='aw',
                                     t_sink=45,
                                     qual_grade_aw=0.36)

        t_source = 20
        cop = heatpump.calc_hp_cop_with_quality_grade(t_source)
        assert round(cop, 5) == 4.58136

        t_source = 40
        cop = heatpump.calc_hp_cop_with_quality_grade(t_source)
        assert cop == 5

        t_source = 50
        cop = heatpump.calc_hp_cop_with_quality_grade(t_source)
        assert cop == 5

    def test_calc_hp_th_power_output(self, fixture_environment):
        # thermal power is 10000 W
        # t_max = 85 °C, t_sink = 45 °C
        # lower_activation_limit is 0.5
        # hp_type = 'aw' , quality_grade = 0.36

        heatpump = hp.heatPumpSimple(environment=fixture_environment,
                                     q_nominal=10000,
                                     hp_type='aw',
                                     t_sink=45,
                                     qual_grade_aw=0.36)

        control_signal = -1000
        th_output = heatpump.calc_hp_th_power_output(
            control_signal)
        assert th_output == 0

        control_signal = 5000
        th_output = heatpump.calc_hp_th_power_output(
            control_signal)
        assert th_output == 5000

        control_signal = 12000
        th_output = heatpump.calc_hp_th_power_output(
            control_signal)
        assert th_output == 10000

    def test_calc_hp_el_power_input(self, fixture_environment):
        # thermal power is 10000 W
        # t_max = 85 °C, t_sink = 45 °C
        # lower_activation_limit is 0.5
        # hp_type = 'aw' , quality_grade = 0.36

        heatpump = hp.heatPumpSimple(environment=fixture_environment,
                                     q_nominal=10000,
                                     hp_type='aw',
                                     t_sink=45,
                                     qual_grade_aw=0.36)

        # test calculation with air water type
        control_signal = -1000
        t_source = 0
        p_el_in = heatpump.calc_hp_el_power_input(control_signal,
                                                  t_source=t_source)
        assert p_el_in == 0

        control_signal = 5000
        t_source = 20
        p_el_in = heatpump.calc_hp_el_power_input(control_signal,
                                                  t_source=t_source)
        assert round(p_el_in, 4) == 1091.379

        control_signal = 12000
        t_source = 50
        p_el_in = heatpump.calc_hp_el_power_input(control_signal,
                                                  t_source=t_source)
        assert p_el_in == 2000
