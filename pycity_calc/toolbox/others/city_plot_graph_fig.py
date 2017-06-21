#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to plot graph figure of city object instance
"""

import os
import pickle

import pycity_calc.visualization.city_visual as citvis
import pycity_calc.toolbox.modifiers.mod_city_geo_pos as citmodgeo


def create_city_graph_figure(city):

    pass


if __name__ == '__main__':
    this_path = os.path.dirname(os.path.abspath(__file__))

    #  User inputs
    #  ######################################################################
    #  City pickle filename
    city_file = 'aachen_forsterlinde_mod_7.pkl'

    file_path = os.path.join(this_path, 'input', 'ref_cities', city_file)

    out_folder = city_file[:-4] + '_graph'

    save_path = os.path.join(this_path, 'output', out_folder)

    plot_buildings = True
    plot_street = True
    plot_lhn = True
    plot_deg = True
    plot_esys = True
    offset = 10
    plot_build_labels = False
    plot_str_labels = False
    equal_axis = True
    font_size = 12
    plt_title = None
    show_plot = False
    fig_adjust = None
    plot_elec_labels = False
    save_plot = True
    dpi = 1000
    plot_str_dist = None

    set_zero_coord = False
    #  ######################################################################

    print('Analyse city file: ', city_file)

    #  Generate output path, if not existent
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    #  Load city object from pickle file
    city = pickle.load(open(file_path, mode='rb'))

    if set_zero_coord:
        #  Generate new zero coordinate for city object
        citmodgeo.set_zero_coordinate(city=city, buffer=0)

    citvis.plot_multi_city_district(city=city,
                                    main_save_path=save_path,
                                    plot_buildings=plot_buildings,
                                    plot_street=plot_street,
                                    plot_lhn=plot_lhn,
                                    plot_deg=plot_deg,
                                    plot_esys=plot_esys,
                                    offset=offset,
                                    plot_build_labels=plot_build_labels,
                                    plot_str_labels=plot_str_labels,
                                    equal_axis=equal_axis,
                                    font_size=font_size,
                                    plt_title=plt_title,
                                    show_plot=show_plot,
                                    fig_adjust=fig_adjust,
                                    plot_elec_labels=plot_elec_labels,
                                    save_plot=save_plot,
                                    dpi=dpi,
                                    plot_str_dist=plot_str_dist)