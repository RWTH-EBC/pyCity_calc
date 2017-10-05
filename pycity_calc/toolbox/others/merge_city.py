#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
from __future__ import division

import os
import pickle

import pycity_calc.visualization.city_visual as citvis
import pycity_calc.toolbox.modifiers.merge_buildings as mergebuild


if __name__ == '__main__':

    #  List merge Frankenberg
    list_unite = [[1020, 1015, 1017],
                  [1025, 1026, 1010],
                  [1003, 1002, 1023],
                  [1004, 1022, 1018],
                  [1007, 1011, 1012],
                  [1024, 1021, 1014],
                  [1005, 1008],
                  [1009, 1006],
                  [1019, 1016, 1013]]

    #  Pathes
    #  ######################################################################
    this_path = os.path.dirname(os.path.abspath(__file__))

    city_input_name = 'aachen_frankenberg_mod_new_1.pkl'
    city_path = os.path.join(this_path, 'input', 'ref_cities',
                             city_input_name)

    city_save_name = 'aachen_frankenberg_mod_new_1_merged.pkl'
    path_save = os.path.join(this_path, 'output', city_save_name)
    #  ######################################################################

    city_object = pickle.load(open(city_path, mode='rb'))

    citvis.plot_city_district(city=city_object)

    #  Merge buildings together
    city_new = mergebuild.merge_buildings_in_city(city=city_object,
                                                  list_lists_merge=list_unite)

    citvis.plot_city_district(city=city_new)

    pickle.dump(city_new, open(path_save, mode='wb'))
