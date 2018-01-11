#!/usr/bin/env python
# coding=utf-8
"""
Script to cluster city with mean-shift algorithm
"""

import os
import numpy as np
from sklearn.cluster import MeanShift, estimate_bandwidth

import pycity_calc.cities.scripts.complex_city_generator as cocity


def cluster():

    #  Generate city district
     #  Year, timestep and location
    year = 2010
    timestep = 3600  # Timestep in seconds
    location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop
    #  Choose electric load profile generation method (1 - SLP; 2 - Stochastic)
    #  Stochastic profile is only generated for residential buildings,
    #  which have a defined number of occupants (otherwise, SLP is used)
    el_gen_method = 1
    #  Generate DHW profiles? (True/False)
    use_dhw = False
    #  DHW generation method? (1 - Annex 42; 2 - Stochastic profiles)
    #  Stochastic profiles require defined nb of occupants per residential
    #  building
    dhw_method = 1

    #  Define city district input data filename
    # filename = 'test_data.txt'
    filename = 'wm_res_only_res_areal_without_dist_heat.txt'

    #  Define ouput data filename (pickled city object)
    save_city = None

    str_node_filename = 'street_nodes.csv'
    str_edge_filename = 'street_edges.csv'

     #  Load street data from csv
    this_path = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.dirname(os.path.dirname(os.path.dirname(this_path)))
    print(src_path)
    str_node_path = os.path.join(src_path, 'cities', 'scripts',
                                 'street_generator' ,'input',
                                      str_node_filename)
    str_edge_path = os.path.join(src_path,'cities', 'scripts',
                                 'street_generator' ,'input',
                                      str_edge_filename)
    #  #----------------------------------------------------------------------

    city_object = \
        cocity.gen_city_with_street_network_from_csvfile(timestep,
                                                         year,
                                                         year,
                                                         location,
                                                         el_gen_method,
                                                         use_dhw,
                                                         dhw_method, filename,
                                                         str_node_path,
                                                         str_edge_path,
                                                         generation_mode=0,
                                                         eff_factor=0.85,
                                                         save_city=save_city,
                                                         show_complex_city=False)

    length = len(city_object.nodelist_building)

    #  Save all building node positions into separate array
    pos_array = np.zeros((length, 2))

    for i in range(length):
        curr_id = city_object.nodelist_building[i]
        curr_position = city_object.nodes[curr_id]['position']
        pos_array[i][0] = curr_position.x
        pos_array[i][1] = curr_position.y

    print(pos_array)
    # The following bandwidth can be automatically detected using
    bandwidth = estimate_bandwidth(pos_array, quantile=0.2, n_samples=500)

    ms = MeanShift(bandwidth=bandwidth, bin_seeding=True)

    print('ms', ms)
    ms.fit(pos_array)
    labels = ms.labels_
    cluster_centers = ms.cluster_centers_

    labels_unique = np.unique(labels)
    n_clusters_ = len(labels_unique)

    print("number of estimated clusters : %d" % n_clusters_)

    # #########################################################################
    # Plot result
    import matplotlib.pyplot as plt
    from itertools import cycle

    plt.figure(1)
    plt.clf()

    colors = cycle('bgrcmykbgrcmykbgrcmykbgrcmyk')
    for k, col in zip(range(n_clusters_), colors):
        my_members = labels == k
        cluster_center = cluster_centers[k]
        plt.plot(pos_array[my_members, 0], pos_array[my_members, 1], col + '.')
        plt.plot(cluster_center[0], cluster_center[1], 'o', markerfacecolor=col,
                 markeredgecolor='k', markersize=14)
    plt.title('Estimated number of clusters: %d' % n_clusters_)
    plt.show()

if __name__ == '__main__':
    cluster()