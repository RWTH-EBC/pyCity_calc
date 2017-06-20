#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for GermanMarket class
"""

import pycity_calc.environments.germanmarket as germanmarket


class Test_GermanMarket():
    def test_german_market_init(self):
        germanmarket.GermanMarket()

    def test_chp_subsidies(self):
        gmarket = germanmarket.GermanMarket()

        # gmarket._sub_chp = [0.08, 0.06, 0.05, 0.044, 0.031]
        # gmarket._sub_chp_self = [0.04, 0.03, 0]

        assert gmarket.get_sub_chp(p_nom=49000) == 0.08
        assert gmarket.get_sub_chp(p_nom=90000) == 0.06
        assert gmarket.get_sub_chp(p_nom=240000) == 0.05
        assert gmarket.get_sub_chp(p_nom=1900000) == 0.044
        assert gmarket.get_sub_chp(p_nom=2100000) == 0.031

        assert gmarket.get_sub_chp_self(p_nom=49000) == 0.04
        assert gmarket.get_sub_chp_self(p_nom=99000) == 0.03
        assert gmarket.get_sub_chp_self(p_nom=110000) == 0

    def test_pv_subsidies(self):
        gmarket = germanmarket.GermanMarket()

        # gmarket._sub_pv = [0.123, 0.1196, 0.1069, 0.0851]

        assert gmarket.get_sub_pv(pv_peak_load=9000, is_res=True) == 0.123
        assert gmarket.get_sub_pv(pv_peak_load=39000, is_res=True) == 0.1196
        assert gmarket.get_sub_pv(pv_peak_load=99000, is_res=True) == 0.1069
        assert gmarket.get_sub_pv(pv_peak_load=99000, is_res=False) == 0.0851

    def test_get_eeg_payments(self):
        gmarket = germanmarket.GermanMarket()

        # eeg_pay = 0.0688
        # gmarket._dict_eeg_self = {'pv': 0.4 * eeg_pay, 'chp': 0.4 * eeg_pay}

        assert abs(gmarket.get_eeg_payment(type='chp') - 0.0688 * 0.4) \
               / gmarket.get_eeg_payment(type='chp') <= 0.001
        assert abs(gmarket.get_eeg_payment(type='pv') - 0.0688 * 0.4) \
               / gmarket.get_eeg_payment(type='pv') <= 0.001
