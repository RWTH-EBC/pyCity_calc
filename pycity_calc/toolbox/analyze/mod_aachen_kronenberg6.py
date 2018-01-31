#!/usr/bin/env python
# coding=utf-8
"""
Script to analyze pickle city file
"""
from __future__ import division
import os
import pickle
import copy
import warnings
import numpy as np
import matplotlib.pyplot as plt

import pycity_calc.toolbox.dimensioning.dim_functions as dimfunc
import pycity_calc.visualization.city_visual as citvis
import pycity_calc.toolbox.teaser_usage.teaser_use as tusage
import pycity_calc.toolbox.networks.network_ops as netop



if __name__ == '__main__':
    #  City pickle filename
    city_file = 'aachen_kronenberg_mod_new_1.pkl'

    #  Path to load file
    this_path = os.path.dirname(os.path.abspath(__file__))
    pycity_path = os.path.dirname(os.path.dirname(this_path))

    file_path = os.path.join(this_path, 'input', city_file)

    out_file = 'aachen_kronenberg_6.pkl'

    out_path = os.path.join(this_path, 'output', 'aachen', out_file)

    #  Load city object from pickle file
    city = pickle.load(open(file_path, mode='rb'))

    #  Erase buildings
    for n in [1001, 1002, 1003, 1004, 1011, 1013, 1008, 1016, 1015, 1005]:
        city.remove_building(n)

    #  Create empty city object (without buildings, but with identical
    #  environment and streets
    #  ###############################################
    city_new = copy.deepcopy(city)

    for n in [1009, 1014, 1007, 1006, 1012, 1010]:
        city_new.remove_building(n)

    city_new.next_node_number = 1001
    #  ###############################################

    for n in [1009, 1014, 1007, 1010, 1012, 1006]:
        build = city.nodes[n]['entity']
        pos = city.nodes[n]['position']

        city_new.addEntity(entity=build, position=pos)

    pickle.dump(city_new, open(out_path, mode='wb'))

    citvis.plot_city_district(city=city_new)