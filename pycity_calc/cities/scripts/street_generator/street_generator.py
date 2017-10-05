#!/usr/bin/env python
# coding=utf-8
"""
Script to generate street graphs
"""

import os
import numpy as np
import shapely.geometry.point as point

import pycity_calc.cities.city as cit
import pycity_calc.cities.scripts.city_generator.city_generator as city_gen

import uesgraphs.visuals as uesvis


def load_street_data_from_csv(path_str_nodes, path_str_edges):
    """
    Load and returns street data from csv files.

    Parameters
    ----------
    path_str_nodes : str
        Path to file with street node data (name, position)
    path_str_edges : str
        Path to file with street edge data (node_1, node_2)

    Returns
    -------
    name_list : list
        List of street node names/ids
    pos_list : list (of tuples)
        List with node positions
    edge_list : list (of tuples)
        List with edge data (start and stop nodes)
    """

    node_data = np.genfromtxt(path_str_nodes, delimiter=';', skip_header=1)
    edge_data = np.genfromtxt(path_str_edges, delimiter=';', skip_header=1)

    name_list = []
    pos_list = []

    #  Extract node ids and positions
    for i in range(len(node_data)):
        curr_id = int(node_data[i][0])
        # Position tuple (e.g. (2.5, 11.2))
        curr_pos = (node_data[i][1], node_data[i][2])
        name_list.append(curr_id)
        pos_list.append(curr_pos)

    edge_list = []

    #  Extract edge information
    if edge_data.ndim > 1:
        #  If array is multidimensional (more than one street)
        for i in range(len(edge_data)):
            curr_edge_tuple = (edge_data[i][0], edge_data[i][1])
            edge_list.append(curr_edge_tuple)

    elif edge_data.ndim == 1:  # Only one street edge
        edge_list = [(edge_data[0], edge_data[1])]

    return name_list, pos_list, edge_list

def add_street_network_to_city(city_object, name_list, pos_list, edge_list):
    """
    Add street network to city object. Based on street network functions
    of uesgraphs.

    Parameters
    ----------
    city_object : object
        City object of pycity_calc
    name_list : list
        List of street node names
    pos_list : list (of shapely Points)
        List holding positions of street nodes
    edge_list : list (of tuples)
        List holding data of start and stop nodes for street edges

    Returns
    -------
    name_node_nb_dict : dict
        Dictionary with street node names as keys and street_ids as values
    """

    #  Assert (check that name_list and pos_list have the same length)
    assert len(name_list) == len(pos_list)

    #  Generate name, node_nb dict
    name_node_nb_dict = {}

    #  Loop over name_list
    for i in range(len(name_list)):
        #  Current name
        curr_name = name_list[i]

        #  Current position
        curr_pos = point.Point(pos_list[i][0], pos_list[i][1])

        #  Add street node
        node_nb = city_object.add_street_node(position=curr_pos)

        #  Add new id to dict (with name as key)
        name_node_nb_dict[curr_name] = node_nb

    #  Loop over edge_list to add edges
    for i in range(len(edge_list)):
        #  Original node names
        start_node = edge_list[i][0]
        stop_node = edge_list[i][1]
        #  Find corresponding node_id (uesgraphs labeling)
        start_id = name_node_nb_dict[start_node]
        stop_id = name_node_nb_dict[stop_node]
        #  Add street edge
        city_object.add_edge(start_id, stop_id, network_type='street')

    return name_node_nb_dict

if __name__ == '__main__':

    #  Generate environment
    year = 2017
    timestep = 3600  # Timestep in seconds
    location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop
    altitude = 55  # Altitude of Bottrop

    str_node_filename = 'street_nodes.csv'
    str_edge_filename = 'street_edges.csv'

    environment = city_gen.generate_environment(timestep=timestep,
                                                year_timer=year,
                                                year_co2=year,
                                                location=location,
                                                altitude=altitude)

    #  Generate city object
    city = cit.City(environment)

    #  Load data from csv
    this_path = os.path.dirname(os.path.abspath(__file__))
    path_str_node_data = os.path.join(this_path, 'input', str_node_filename)
    path_str_edge_data = os.path.join(this_path, 'input', str_edge_filename)

    name_list, pos_list, edge_list = load_street_data_from_csv(path_str_nodes=
                                                               path_str_node_data,
                                                               path_str_edges=
                                                               path_str_edge_data)

    #  Add street to city object
    add_street_network_to_city(city, name_list, pos_list, edge_list)

    #  Plot street network
    visual = uesvis.Visuals(city)
    visual.show_network(save_as=None, show_plot=True, labels=None,
                        show_diameters=False)
