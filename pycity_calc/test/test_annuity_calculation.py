#!/usr/bin/env python
# coding=utf-8
"""
Test script for EconomicCalculation
"""

from __future__ import division
import pycity_calc.economic.annuity_calculation as ann_calc


class Test_EconomicCalculation():

    def test_eco_calc_init(self):

        ann_calc.EconomicCalculation()

    def test_annuity_calculation(self):

        i = 0.05
        t = 1

        eco_calc = ann_calc.EconomicCalculation(time=t, interest=i,
                                                run_init_calc=False)

        assert eco_calc.calc_annuity_factor() == 1.05

        i = 0.05
        t = 2

        eco_calc = ann_calc.EconomicCalculation(time=t, interest=i,
                                                run_init_calc=False)

        assert abs(eco_calc.calc_annuity_factor() - 0.5378) < 0.001

    def test_nb_replacements(self):

        i = 0.05
        t = 30

        eco_calc = ann_calc.EconomicCalculation(time=t, interest=i,
                                                run_init_calc=False)

        eco_calc.dict_lifetimes = {'LHN_station': 30,
                                   'LHN_steel_pipe': 40,
                                   'LHN_plastic_pipe': 30,
                                   'B': 18,
                                   'HP': 20,
                                   'EH': 20,
                                   'CHP': 15,
                                   'TES': 20,
                                   'PV': 25,
                                   'BAT': 15,
                                   'DEG': 15}

        eco_calc.calc_nb_of_replacements()

        #  Both should only be replaced once
        assert eco_calc.dict_nb_replacements['B'] == 1
        assert eco_calc.dict_nb_replacements['CHP'] == 1

        i = 0.05
        t = 15

        eco_calc = ann_calc.EconomicCalculation(time=t, interest=i,
                                                run_init_calc=False)

        eco_calc.dict_lifetimes = {'LHN_station': 30,
                                   'LHN_steel_pipe': 40,
                                   'LHN_plastic_pipe': 30,
                                   'B': 18,
                                   'HP': 20,
                                   'EH': 20,
                                   'CHP': 15,
                                   'TES': 20,
                                   'PV': 25,
                                   'BAT': 15,
                                   'DEG': 15}

        eco_calc.calc_nb_of_replacements()

        #  No replacements necessary (since observation period is only 15 a)
        assert eco_calc.dict_nb_replacements['B'] == 0
        assert eco_calc.dict_nb_replacements['CHP'] == 0

    def test_calc_price_dyn_factor(self):

        i = 0.05
        t = 10
        r_cap = 1.05

        eco_calc = ann_calc.EconomicCalculation(time=t, interest=i,
                                                price_ch_cap=r_cap)

        price_dyn_fac = eco_calc.calc_price_dyn_factor(price_ch_factor=r_cap)

        #  Test if q and r are equal --> b = T/q
        assert abs(price_dyn_fac - 9.52381) < 0.0001

        i = 0.05
        t = 10
        r_cap = 1.0

        eco_calc = ann_calc.EconomicCalculation(time=t, interest=i,
                                                price_ch_cap=r_cap)

        price_dyn_fac = eco_calc.calc_price_dyn_factor(price_ch_factor=r_cap)

        #  Test if q > r
        assert abs(price_dyn_fac - 7.721735) < 0.0001

    def test_calc_cash_value_for_single_replacement(self):

        i = 0.05
        t = 32
        r_cap = 1.02
        n = 2
        invest = 1000

        eco_calc = ann_calc.EconomicCalculation(time=t, interest=i,
                                                price_ch_cap=r_cap)

        cash_val_repl = \
            eco_calc.calc_cash_value_for_single_replacement(invest=invest,
                                                            price_change=r_cap,
                                                            nb_replacement=n,
                                                            lifetime=15)

        #  An = A0 * r^(n * T_n) / q^(n * T_n)
        assert abs(cash_val_repl - 419.108222) < 0.0001

    def test_calc_sum_cash_value_factors_replacements(self):

        i = 0.05
        t = 32
        r_cap = 1.02
        invest = 1000

        eco_calc = ann_calc.EconomicCalculation(time=t, interest=i,
                                                price_ch_cap=r_cap)

        cash_val_repl = \
            eco_calc.calc_sum_cash_value_factors_replacements(invest=invest,
                                                              type='CHP')

        assert abs(cash_val_repl - (647.38568 + 419.108222)) < 0.0001

    def test_calc_residual_value(self):

        i = 0.05
        t = 18
        invest = 10000
        type = 'B'  # Boiler

        eco_calc = ann_calc.EconomicCalculation(time=t, interest=i)

        eco_calc.dict_lifetimes = {'LHN_station': 30,
                                   'LHN_steel_pipe': 40,
                                   'LHN_plastic_pipe': 30,
                                   'B': 18,
                                   'HP': 20,
                                   'EH': 20,
                                   'CHP': 15,
                                   'TES': 20,
                                   'PV': 25,
                                   'BAT': 15,
                                   'DEG': 15}

        residual_value = \
            eco_calc.calc_residual_value(invest=invest, type=type)

        #  No remaining value
        assert abs(residual_value) < 0.00001

        i = 0.05
        t = 15
        invest = 10000
        r_cap = 1.0
        type = 'B'  # Boiler

        eco_calc = ann_calc.EconomicCalculation(time=t, interest=i,
                                                price_ch_cap=r_cap)

        eco_calc.dict_lifetimes = {'LHN_station': 30,
                                   'LHN_steel_pipe': 40,
                                   'LHN_plastic_pipe': 30,
                                   'B': 18,
                                   'HP': 20,
                                   'EH': 20,
                                   'CHP': 15,
                                   'TES': 20,
                                   'PV': 25,
                                   'BAT': 15,
                                   'DEG': 15}

        residual_value2 = \
            eco_calc.calc_residual_value(invest=invest, type=type)

        assert abs(residual_value2 - 801.6951635) < 0.0001

    def test_vdi_example_b(self):
        """
        Pytest based on VDI2067 example B

        Simplified to only account for boiler with 31462 Euro investment cost
        """

        i = 0.07
        t = 30
        invest = 31462
        type = 'B'  # Boiler
        r_cap = 1.03
        r_dem = 1.03
        r_op = 1.02

        sum_el_energy = 417
        sum_gas_energy = 14012

        p_el = 0.2
        p_gas = 0.06

        eco_calc = ann_calc.EconomicCalculation(time=t, interest=i,
                                                price_ch_cap=r_cap,
                                                price_ch_dem_el=r_dem,
                                                price_ch_dem_gas=r_dem,
                                                price_ch_op=r_op)

        eco_calc.dict_lifetimes = {'LHN_station': 30,
                                   'LHN_steel_pipe': 40,
                                   'LHN_plastic_pipe': 30,
                                   'B': 18,
                                   'HP': 20,
                                   'EH': 20,
                                   'CHP': 15,
                                   'TES': 20,
                                   'PV': 25,
                                   'BAT': 15,
                                   'DEG': 15}

        #  Calculate capital-related annuity
        cap_rel_annuity = \
            eco_calc.calc_capital_rel_annuity_with_type(invest=invest,
                                                        type=type)

        #  Calculate demand related annuity
        dem_rel_ann = eco_calc.calc_dem_rel_annuity(
            sum_el_e=sum_el_energy, sum_gas_e=sum_gas_energy,
            price_el=p_el, price_gas=p_gas)

        #  Calculate operation related annuity
        op_rel_ann = \
            eco_calc.calc_op_rel_annuity_single_comp(invest=invest,
                                                     type=type)

        total_annuity = \
            eco_calc.calc_total_annuity(ann_capital=cap_rel_annuity,
                                        ann_demand=dem_rel_ann,
                                        ann_op=op_rel_ann,
                                        ann_proc=0)

        #  Check if dimension is correct (cannot be same value, because
        #  of simplification to one device / not taking all sub-components
        #  into account)
        assert abs(-total_annuity + 5633.44) <= 600
