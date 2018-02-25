#!/usr/bin/env python
# coding=utf-8
"""

"""
from __future__ import division

import os
import pickle
import copy

import pycity_calc.toolbox.analyze.analyze_city_pickle_file as citan
import pycity_calc.visualization.city_visual as citvis

if __name__ == '__main__':
    #  City pickle filename
    city_file = 'aachen_kronenberg_6.pkl'

    print('Analyse city file: ', city_file)

    #  Path to load file
    this_path = os.path.dirname(os.path.abspath(__file__))
    pycity_path = os.path.dirname(os.path.dirname(this_path))

    file_path = os.path.join(this_path, 'input', city_file)

    #  Load city object from pickle file
    city = citan.load_pickled_city_file(file_path)

    check_sh = True  # Check space heating
    check_el = True  # Check electrical demand object
    check_dhw = True  # Check hot water demand object
    check_occ = True  # Check occupancy object
    check_base_par = True  # Check existence of base parameters of building
    check_bes = False  # Check existence of BES on building
    check_typebuilding = False  # Check existence of TEASER typebuilding

    #  Check consistency of file
    citan.check_city_consinstency(city=city, check_sh=check_sh,
                                  check_el=check_el,
                                  check_dhw=check_dhw, check_occ=check_occ,
                                  check_base_par=check_base_par,
                                  check_bes=check_bes,
                                  check_typebuilding=check_typebuilding)

    #  Run analyzation script
    citan.run_c_file_an(city_object=city)

    citan.get_min_max_th_sh_powers(city, print_out=True)

    #  Extract subcity
    #  ####################################################################
    list_remove1 = [1001, 1002, 1003]
    list_remove2 = [1004, 1005, 1006]

    city_1 = copy.deepcopy(city)
    city_2 = copy.deepcopy(city)

    for n in list_remove1:
        city_1.remove_building(n)
    for n in list_remove2:
        city_2.remove_building(n)

    citvis.plot_city_district(city=city_1)
    citvis.plot_city_district(city=city_2)

    save_path1 = os.path.join(this_path, 'output',
                              'kronen_123.pkl')
    save_path12 = os.path.join(this_path, 'output',
                               'kronen_456.pkl')

    pickle.dump(city_1, open(save_path1, mode='wb'))
    pickle.dump(city_2, open(save_path12, mode='wb'))
