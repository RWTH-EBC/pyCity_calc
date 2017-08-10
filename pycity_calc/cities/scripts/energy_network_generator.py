#!/usr/bin/env python
# coding=utf-8
"""
Script to generate energy networks within city district (heating and/or
electrical networks).

Requires city district as input (should include buildings with loads, but
without energy systems)

Annotation: Current input limit for single network is 1000 characters
(see load_en_network_input_data --> genfromtxt call)
"""

import os
import csv
import pickle

import pycity_calc.visualization.city_visual as citvis
import pycity_calc.toolbox.dimensioning.dim_networks as dimnet


def load_en_network_input_data(network_path):
    """
    Load energy network input data from network_path (should point on
    csv/txt file, which is tab separated and holds information about
    planed lhn and/or deg networks)

    Parameters
    ----------
    network_path : str
        Path to input file

    Returns
    -------
    dict_data : dict
        Dictionary with network ids as keys and value dictionary as values.
        The values dictionaries hold keys:
        'type' (value: network type string)
        'method' (value: method integer)
        'nodelist' (value: list (of node ids))
    """

    #  Generate empty data dictionary
    dict_data = {}

    with open(network_path, 'r') as file:
        next(file)  # Skip header

        reader = csv.reader(file, delimiter='\t')
        for id, node_string, type, method in reader:

            #  Open dictionary
            dict_inner = {}

            #  Split string by commas
            nodelist = node_string.split(',')
            #  Convert strings into integers
            for i in range(len(nodelist)):
                nodelist[i] = int(nodelist[i])

            #  Add values to inner dictionary
            dict_inner['nodelist'] = nodelist
            dict_inner['type'] = type
            dict_inner['method'] = int(method)

            #  Add to data dict
            dict_data[id] = dict_inner

    return dict_data


def add_energy_networks_to_city(city, dict_data):
    """
    Function adds energy networks to city object.

    Parameters
    ----------
    city : object
        City object of pycity_calc
    dict_data : dict
        Dictionary with network ids as keys and value dictionary as values.
        The values dictionaries hold keys:
        'type' (value: network type string)
        Which type of network should be implemented ('heating', 'electricity'
        or 'heating_and_deg'
        'method' (value: method integer)
        Which method should be used for generation and dimensioning of
        network.
        'nodelist' (value: list (of node ids))
        Which nodes should be connected via network
    """

    #  Check if every network node in data dict is within city object
    for key in dict_data:
        for node in dict_data[key]['nodelist']:
            assert node in city.nodes(), ('Node ' + str(node) + ' is not' +
                                          ' within city object!')

    for key in dict_data:
        dataset = dict_data[key]
        nodelist = dataset['nodelist']  # list of nodes to be connected
        type = dataset['type']  # Type of network
        method = dataset['method']  # Method of network generation
        #  Street or no street

        if method == 1:
            use_street_network = False
        elif method == 2:
            use_street_network = True
        else:  # pragma: no cover
            raise ValueError('Unknown method. Please check dict_data!')

        if type == 'heating' or type == 'heating_and_deg':
            dimnet.add_lhn_to_city(city=city, list_build_node_nb=nodelist,
                                   network_type=type,
                                   use_street_network=use_street_network)

        elif type == 'electricity':
            dimnet.add_deg_to_city(city=city, list_build_node_nb=nodelist,
                                   use_street_network=use_street_network)

        else:  # pragma: no cover
            raise ValueError('Unknown networktype. Please check dict_data!')


if __name__ == '__main__':

    #  Path to city pickle file
    city_filename = 'city_3_buildings.p'
    this_path = os.path.dirname(os.path.abspath(__file__))
    city_path = os.path.join(this_path, 'input_en_network_generator',
                             city_filename)

    #  Path to energy network input file (csv/txt; tab separated)
    network_filename = 'city_3_buildings_networks.txt'
    network_path = os.path.join(this_path, 'input_en_network_generator',
                                network_filename)

    #  Path to save pickle city file with networks
    save_filename = 'city_3_buildings_with_networks.p'
    save_path = os.path.join(this_path, 'output_en_network_generator',
                             save_filename)

    #  Load city object
    city = pickle.load(open(city_path, mode='rb'))

    #  Load energy networks planing data
    dict_data = load_en_network_input_data(network_path)

    #  Add energy networks to city
    add_energy_networks_to_city(city=city, dict_data=dict_data)

    #  Plot city
    citvis.plot_city_district(city=city, plot_street=True,
                              plot_lhn=True, plot_deg=True)

    #  Save city pickle file
    pickle.dump(city, open(save_path, mode='wb'))
