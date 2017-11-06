#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
from __future__ import division

import pycity_calc.economic.energy_sys_cost.hp_cost as hp_cost

class TestHpCost():
    def test_hp_cost(self):
        hp_th_pow = 10000  # Heat pump thermal power in Watt
        method = 'stinner'
        hp_type = 'aw'  # Brine/water
        with_source_cost = False
        with_inst = True

        hp_kw = hp_th_pow / 1000  # in kW

        hp_cost.calc_invest_cost_hp(q_nom=hp_kw, method=method,
                                    hp_type=hp_type,
                                    with_source_cost=with_source_cost,
                                    with_inst=with_inst)

        hp_th_pow = 10000  # Heat pump thermal power in Watt
        method = 'wolf'
        hp_type = 'aw'  # Brine/water
        with_source_cost = False
        with_inst = False

        hp_kw = hp_th_pow / 1000  # in kW

        hp_cost.calc_invest_cost_hp(q_nom=hp_kw, method=method,
                                    hp_type=hp_type,
                                    with_source_cost=with_source_cost,
                                    with_inst=with_inst)

        hp_th_pow = 20000  # Heat pump thermal power in Watt
        method = 'wolf'
        hp_type = 'ww'  # Brine/water
        with_source_cost = True
        with_inst = False

        hp_kw = hp_th_pow / 1000  # in kW

        hp_cost.calc_invest_cost_hp(q_nom=hp_kw, method=method,
                                    hp_type=hp_type,
                                    with_source_cost=with_source_cost,
                                    with_inst=with_inst)

        hp_th_pow = 30000  # Heat pump thermal power in Watt
        method = 'wolf'
        hp_type = 'bw'  # Brine/water
        with_source_cost = True
        with_inst = True

        hp_kw = hp_th_pow / 1000  # in kW

        hp_cost.calc_invest_cost_hp(q_nom=hp_kw, method=method,
                                    hp_type=hp_type,
                                    with_source_cost=with_source_cost,
                                    with_inst=with_inst)
