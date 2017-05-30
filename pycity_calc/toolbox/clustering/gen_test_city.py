#!/usr/bin/env python
# coding=utf-8
"""
Script to generate test city for clustering
"""

import os

import shapely.geometry.point as point

import pycity_calc.cities.scripts.street_generator.street_generator as str_gen
import pycity_calc.cities.scripts.city_generator.city_generator as city_gen
import pycity_calc.cities.scripts.complex_city_generator as comcity

import uesgraphs.visuals as uesvis


def gen_city_w_buildings(district_data):
    """
    Returns city object with buildings.

    Parameters
    ----------
    district_data : np.array
        Numpy 2d array with district data
    """

    city = city_gen.run_city_generator(generation_mode=0, timestep=3600,
                                       year=2010,
                                       location=(51.529086, 6.944689),
                                       el_gen_method=1, use_dhw=False,
                                       dhw_method=1, th_gen_method=2,
                                       district_data=district_data,
                                       pickle_city_filename='city_cluster.p',
                                       eff_factor=0.85, show_city=False)

    return city


def add_street_to_city(city, path_str_nodes, path_str_edges):
    name_list, pos_list, edge_list = \
        str_gen.load_street_data_from_csv(path_str_nodes, path_str_edges)

    str_gen.add_street_network_to_city(city, name_list, pos_list,
                                       edge_list)


def set_up_test_city():
    this_path = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.dirname(os.path.dirname(this_path))

    str_node_file = 'street_nodes_cluster.csv'
    str_edge_file = 'street_edges_cluster.csv'

    path_str_nodes = os.path.join(src_path, 'cities', 'scripts',
                                  'street_generator', 'input', str_node_file)
    path_str_edges = os.path.join(src_path, 'cities', 'scripts',
                                  'street_generator', 'input', str_edge_file)

    filename = 'city_clust_simple.txt'

    txt_path = os.path.join(src_path, 'cities', 'scripts', 'city_generator',
                            'input', filename)

    #  Load district_data file
    district_data = city_gen.get_district_data_from_txt(txt_path)

    #  Generate city object
    city = gen_city_w_buildings(district_data)

    #  Add streets to city
    add_street_to_city(city=city, path_str_nodes=path_str_nodes,
                       path_str_edges=path_str_edges)

    return city


if __name__ == '__main__':

    city = set_up_test_city()

    this_file_path = os.path.dirname(os.path.abspath(__file__))
    filename = 'test_city.p'
    city_path = os.path.join(this_file_path, 'test_city_object', filename)

    #  Save city file
    comcity.save_pickle_city_file(city, path_to_save=city_path)

    #  Plot street network
    visual = uesvis.Visuals(city)
    visual.show_network(save_as=None, show_plot=True, labels='building',
                        show_diameters=False)
