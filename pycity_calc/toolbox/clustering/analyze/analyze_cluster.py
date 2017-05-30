#!/usr/bin/env python
# coding=utf-8
"""
Script to analyze cluster_dict
"""

import os
import pickle

import pycity_calc.visualization.city_visual as citvis


def run_cluster_analysis(city, clust_dict, plot_build_labels=False,
                         plot_clust_keys=True, plot_str_dist=None,
                         x_label=None, y_label=None):

    print('\nClusters dictionary:')
    print(clust_dict)

    print('Print all cluster lists')
    print('#######################################')
    for key in clust_dict:
        print(clust_dict[key])
    print('#######################################')

    print('\nTotal number of clusters: ', len(clust_dict))

    max_size = 0
    #  Find largest cluster size
    for key in clust_dict:
        if len(clust_dict[key]) > max_size:
            max_size = len(clust_dict[key])

    min_size = max_size + 1
    #  Find smallest cluster size
    for key in clust_dict:
        if len(clust_dict[key]) < min_size:
            min_size = len(clust_dict[key])

    list_size = []
    for key in clust_dict:
        list_size.append(len(clust_dict[key]))

    def nb_clustersize(list_size, max_size):
        print()
        for i in range(1, max_size + 1):
            print('Number of clusters with size ' + str(i) + ': '
                  + str(list_size.count(i)))

    print('Minimum cluster size: ' + str(min_size) + ' building nodes.')
    print('Maximum cluster size: ' + str(max_size) + ' building nodes.')

    nb_clustersize(list_size, max_size)

    #  Plot city district clusters
    citvis.plot_cluster_results(city=city, cluster_dict=clust_dict,
                                plot_street=True,
                                plot_clust_keys=plot_clust_keys,
                                plot_build_labels=plot_build_labels,
                                use_bw=False,
                                offset=15, plot_str_dist=plot_str_dist,
                                x_label=x_label, y_label=y_label)


if __name__ == '__main__':

    clust_filename = 'cluster_dict_wm_res_south_23.p'
    city_filename = 'wm_res_south_23.p'

    plot_build_labels = False
    plot_clust_keys = True

    #  Maximum distance from streetnode to cluster graph, which should be
    #  plotted.
    plot_str_dist = 50

    x_label = 'x-coordinate in m'
    y_label = 'y-coordinate in m'

    #  #--------------------------------------------------

    this_path = os.path.dirname(os.path.abspath(__file__))
    clust_path = os.path.dirname(this_path)
    file_path = os.path.join(clust_path, 'output', clust_filename)

    city_path = os.path.join(clust_path, 'test_city_object', city_filename)

    #  Load cluster dict
    clust_dict = pickle.load(open(file_path, mode='rb'))

    #  Load city object
    city = pickle.load(open(city_path, mode='rb'))

    run_cluster_analysis(city=city, clust_dict=clust_dict,
                         plot_clust_keys=plot_clust_keys,
                         plot_build_labels=plot_build_labels,
                         plot_str_dist=plot_str_dist,
                         x_label=x_label, y_label=y_label)
