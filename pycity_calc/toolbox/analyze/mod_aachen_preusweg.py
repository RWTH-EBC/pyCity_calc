#!/usr/bin/env python
# coding=utf-8
"""
Script to analyze pickle city file
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



if __name__ == '__main__':
    #  City pickle filename
    city_file = 'aachen_preusweg_osm.pkl'

    #  Path to load file
    this_path = os.path.dirname(os.path.abspath(__file__))
    pycity_path = os.path.dirname(os.path.dirname(this_path))

    file_path = os.path.join(this_path, 'input', 'aachen', city_file)

    out_file = city_file[:-4] + '_mod_1.pkl'

    out_path = os.path.join(this_path, 'output', 'aachen', out_file)

    #  Load city object from pickle file
    city = pickle.load(open(file_path, mode='rb'))

    list_extract = [1092, 1079, 1094, 1097, 1098, 1036, 1048, 1109]

    for n in city.nodes():
        if n not in list_extract:
            city.remove_building(n)

    # list_remove = [1111, 1096, 1085, 1021, 1089, 1024, 1003, 1023, 1052]
    #
    # for n in list_remove:
    #     city.remove_building(n)

    pickle.dump(city, open(out_path, mode='wb'))

    citvis.plot_city_district(city=city)