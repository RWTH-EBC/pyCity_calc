#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Code extracts and saves load profiles of all buildings of city object
"""

import os
import pickle

import pycity_calc.visualization.city_visual as citvis


def gen_path_if_not_existent(dir):
    """
    Generate directory, if not existent

    Parameters
    ----------
    dir : str
        Directory path
    """
    if not os.path.exists(dir):
        os.makedirs(dir)


def save_city_load_profiles(city, out_path):
    pass


if __name__ == '__main__':

    this_path = os.path.dirname(os.path.abspath(__file__))

    city_f_name = 'aachen_tuerme_mod_7_el_resc_2.pkl'

    input_path = os.path.join(this_path, 'input', city_f_name)

    out_name = city_f_name[:-4]

    out_path = os.path.join(this_path, 'output', 'extracted', out_name)

    #  Make out_path, if not existent
    gen_path_if_not_existent(out_path)


    city = pickle.load(open(input_path, mode='rb'))

    save_city_load_profiles(city=city, out_path=out_path)



    citvis.plot_city_district(city=city)