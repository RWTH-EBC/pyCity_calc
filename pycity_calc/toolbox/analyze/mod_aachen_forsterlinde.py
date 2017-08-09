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
    city_file = 'aachen_forsterlinde_osm.pkl'

    #  Path to load file
    this_path = os.path.dirname(os.path.abspath(__file__))
    pycity_path = os.path.dirname(os.path.dirname(this_path))

    file_path = os.path.join(this_path, 'input', 'aachen', city_file)

    out_file = city_file[:-4] + '_mod_1.pkl'

    out_path = os.path.join(this_path, 'output', 'aachen', out_file)

    #  Load city object from pickle file
    city = pickle.load(open(file_path, mode='rb'))

    #  Erase buildings 1001 and 1008
    for n in [1001, 1006, 1008]:
        city.remove_building(n)

    pickle.dump(city, open(out_path, mode='wb'))

    citvis.plot_city_district(city=city)
