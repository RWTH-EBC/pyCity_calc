#!/usr/bin/env python
# coding=utf-8
"""
Script to calculate capital- and operation-related annuity
"""
from __future__ import division
import os
import pickle

import pycity_calc.visualization.city_visual as citvis
import pycity_calc.economic.annuity_calculation as annuity_calc
import pycity_calc.economic.city_economic_calc as ec_city


def run_example():
    """
    Runs example annuity calculation for city district
    """

    this_path = os.path.dirname(os.path.abspath(__file__))

    filename = 'city_ex.p'

    input_path = os.path.join(this_path, 'inputs', filename)

    #  Load city object from pickle file
    city = pickle.load(open(input_path, mode='rb'))

    citvis.plot_city_district(city=city, plot_lhn=True, plot_esys=True)

    time = 10  # Years
    interest = 0.05  # Interest rate

    #  Generate economic calculator object
    eco_calc = annuity_calc.EconomicCalculation(time=time, interest=interest)

    #  Perform capital-related annuity calculation for all energy systems in
    #  city district
    (cap_rel_ann, op_rel_ann) = \
        ec_city.calc_cap_and_op_rel_annuity_city(city=city, eco_calc=eco_calc)

    print('Capital-related annuity of all energy systems in Euro:')
    print(round(cap_rel_ann, 2))
    print()

    print('Operation-related annuity for all energy systems in Euro:')
    print(round(op_rel_ann, 2))


if __name__ == '__main__':
    run_example()
