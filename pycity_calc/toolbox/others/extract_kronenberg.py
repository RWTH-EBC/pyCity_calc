#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
from __future__ import division

import os
import pickle
import warnings
import numpy as np
import matplotlib.pyplot as plt

import pycity_calc.toolbox.dimensioning.dim_functions as dimfunc
import pycity_calc.visualization.city_visual as citvis
import pycity_calc.toolbox.teaser_usage.teaser_use as tusage
import pycity_calc.toolbox.networks.network_ops as netop
import pycity_calc.cities.scripts.city_generator.city_generator as citgen

import pycity_calc.toolbox.analyze.analyze_city_pickle_file as citan

if __name__ == '__main__':
    #  City pickle filename
    city_file = 'aachen_kronenberg_mod_new_1.pkl'

    print('Analyse city file: ', city_file)

    #  Path to load file
    this_path = os.path.dirname(os.path.abspath(__file__))
    pycity_path = os.path.dirname(os.path.dirname(this_path))

    file_path = os.path.join(this_path, 'input', 'ref_cities', city_file)
    # file_path = os.path.join(pycity_path, 'cities', 'scripts',
    #                          'city_generator',
    #                          'output', city_file)

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
    citan.check_city_consinstency(city=city, check_sh=check_sh, check_el=check_el,
                            check_dhw=check_dhw, check_occ=check_occ,
                            check_base_par=check_base_par, check_bes=check_bes,
                            check_typebuilding=check_typebuilding)

    #  Run analyzation script
    citan.run_c_file_an(city_object=city)

    citan.get_min_max_th_sh_powers(city, print_out=True)


    #  Extract subcity
    #  ####################################################################
    list_sub = []

    list_remove = [1001, 1002, 1003]

    # subcity = netop.get_build_str_subgraph(city=city, nodelist=list_sub)

    for n in list_remove:
        city.remove_building(n)

    save_path = os.path.join(this_path, 'output',
                             'aachen_kronenberg_extract_9.pkl')

    pickle.dump(city, open(save_path, mode='wb'))


    # #  Add KFW retrofit to buildings
    #  ###################################################################
    # tusage.add_kfw_retrofit_to_city(city=city, material=None, thickness=1)
    #
    # tusage.calc_and_add_vdi_6007_loads_to_city(city=city, air_vent_mode=0,
    #                                            vent_factor=0.05,
    #                                            use_exist_tbuild=True)
    #
    # list_non = check_kfw_standard_city(city=city)
    #
    # print('List of building ids, which do not stay within KFW limitations:')
    # print(list_non)
    #
    # #  Run analyzation script
    # run_c_file_an(city_object=city)
    #
    # out_fname = city_file[:-2] + '_kfw.p'
    # out_path = os.path.join(this_path, 'output', out_fname)
    #
    # pickle.dump(city, open(out_path, mode='wb'))




    #  Save load curves to file
    #  ###################################################################
    # build_1 = city.node[1001]['entity']
    #
    # space_h_load = build_1.get_space_heating_power_curve()
    # el_load = build_1.get_electric_power_curve()
    # dhw_load =build_1.get_dhw_power_curve()
    #
    # time_array = np.arange(0, 8760)
    #
    # dataset = np.transpose(np.vstack((time_array, space_h_load, el_load, dhw_load)))
    #
    # print(dataset)
    #
    # this_path = os.path.dirname(os.path.abspath(__file__))
    # filename = 'wm_res_east_single_profiles.txt'
    # save_path = os.path.join(this_path, filename)
    #
    # np.savetxt(save_path, dataset, delimiter='\t')
