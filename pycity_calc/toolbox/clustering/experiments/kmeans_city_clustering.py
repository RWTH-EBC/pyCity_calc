#!/usr/bin/env python
# coding=utf-8
"""
Script to cluster city district buildings with kmeans
"""

import os
import numpy as np
import random
import matplotlib.pyplot as plt
import shapely.geometry.point as pnt

import pycity_calc.cities.scripts.complex_city_generator as cocity
import pycity_calc.toolbox.clustering.experiments.kmeans_lloyd as kloyd
import pycity_calc.toolbox.networks.network_ops as netop


def kmeans_clustering(city, nb_clusters, show_kmeans=False):
    """
    Performs kmeans clustering on city object

    Parameters
    ----------
    city : object
        City object of pycity_calc
    nb_clusters : int
        Number of desired clusters
    show_kmeans : bool, optional
        Defines if result should be plotted (default: False)

    Returns
    -------
    clusters : dict
        Dictionary with cluster numbers (int) as key and lists  of 2d
        numpy arrays as values.
    """

    x_y_array = np.zeros((len(city.nodelist_building), 2))
    counter = 0

    for n in city.nodes():
        if 'node_type' in city.node[n]:
            #  If node_type is building
            if city.node[n]['node_type'] == 'building':
                if city.node[n]['entity']._kind == 'building':
                    curr_x = city.node[n]['position'].x
                    curr_y = city.node[n]['position'].y
                    #  Save within x_y_array
                    x_y_array[counter][0] = float(curr_x)
                    x_y_array[counter][1] = float(curr_y)
                    counter += 1

    # print('Nb of buildings:', counter+1)

    #  Perform kmeans clustering
    mu, clusters = kloyd.find_centers(x_y_array, nb_clusters)

    # print('Kmeans cluster:')
    # print(clusters)

    if show_kmeans:
        color_list = ['r', 'b', 'm', 'g', 'k', '#7600A1', '#6ACC65', '#FFFEA3',
                      '#f0f0f0', '#017517']
        counter = 0
        fig = plt.figure()
        for key in clusters:
            curr_cluster = clusters[key]
            curr_mu = mu[counter]
            x_list, y_list = kloyd.convert_array_list_to_x_y_lists(
                curr_cluster)
            # color = color_list[counter]  #  Select from color_list
            color = np.random.rand(3, 1)  # Random color
            plt.plot(x_list, y_list, c=color, marker='o', linestyle='')
            # plt.plot(curr_mu[0], curr_mu[1], mfc=color, marker='*', linestyle='',
            #          markersize=15)
            counter += 1
        # Equalize scale of x- and y-axis
        plt.gca().set_aspect('equal', adjustable='box')
        plt.show()

    return clusters


def load_n_cluster_kmeans(file_path, nb_of_clusters, show_kmeans=False):
    """
    Load city district and perform kmeans clustering

    Parameters
    ----------
    file_path : str
        Path to pickle city file (should be loaded)
    nb_of_clusters : int
        Number of desired clusters
    show_kmeans : bool, optional
        Defines if cluster results should be shown (default: False)

    Returns
    -------
    clusters : dict
        Dictionary with cluster numbers (int) as key and lists  of 2d
        numpy arrays as values.
    city_object : object
        City object of pycity_calc
    """

    #  Load pickle city file
    this_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filename = 'city_clust_simple.p'
    file_path = os.path.join(this_path, 'test_city_object', filename)

    #  Load city object
    city_object = cocity.load_pickled_city_file(file_path)

    clusters = kmeans_clustering(city=city_object, nb_clusters=nb_of_clusters,
                                 show_kmeans=show_kmeans)

    return clusters, city_object


def conv_np_array_to_point(array):
    """
    Converts 2d numpy position array into shapely Point object

    Parameters
    ----------
    array : Numpy array
        Numpy 2d position array

    Returns
    -------
    point : Point
        shapely point object
    """
    x = array[0]
    y = array[1]
    point = pnt.Point(x, y)
    return point


def conv_cluster_array_to_point(clusters):
    """
    Converts cluster dictionary with position tuples to position shapely Points

    Parameters
    ----------
    clusters : dict
        Dictionary with cluster numbers (int) as key and lists  of 2d
        numpy arrays as values.

    Returns
    -------
    point_clusters : dict
        Dictionary with cluster numbers (int) as key and lists  of shapely
        Points as values.
    """

    point_clusters = {}

    for key in clusters:

        cluster = clusters[key]
        point_cluster = []

        for i in range(len(cluster)):
            curr_array = cluster[i]
            #  Convert to point object
            point = conv_np_array_to_point(curr_array)
            #  Save entry to cluster list
            point_cluster.append(point)

        # Save cluster list to clusters dict
        point_clusters[key] = point_cluster

    return point_clusters


def conv_point_to_node_ids(city, clusters):
    """
    Convert clusters dictionary with shapely points into

    Parameters
    ----------
    city : object
        City object of pycity_calc
    clusters : dict
        Dictionary with cluster numbers (int) as key and lists  of 2d
        numpy arrays as values.

    Returns
    -------
    node_clusters : dict
        Dictionary with cluster numbers (int) as node ids of graph as
        value
    """

    node_clusters = {}

    for key in clusters:

        cluster = clusters[key]
        node_cluster = []

        for i in range(len(cluster)):
            point = cluster[i]
            node_id = netop.get_node_id_by_position(graph=city,
                                                    position=point)
            assert node_id != None, ('Position ' + str(point) + ' not ' +
                                     'found within city object.')
            node_cluster.append(node_id)

        node_clusters[key] = node_cluster

    return node_clusters


if __name__ == '__main__':

    #  Filepath
    #  Load pickle city file
    this_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filename = 'city_clust_simple.p'
    file_path = os.path.join(this_path, 'test_city_object', filename)

    #  Number of desired clusters for kmean algorithm
    nb_of_clusters = 6

    #  Plot results?
    show_kmeans = False

    #  Execute code and return clusters dict
    clusters, city = load_n_cluster_kmeans(file_path, nb_of_clusters,
                                           show_kmeans=show_kmeans)

    print('Clusters (with numpy arrays as positions):')
    print(clusters)

    #  Convert clusters array entries to Point objects
    clusters = conv_cluster_array_to_point(clusters)

    print('Clusters (with Point objects as positions):')
    print(clusters)

    clusters = conv_point_to_node_ids(city, clusters)

    print('Clusters (with node ids):')
    print(clusters)
