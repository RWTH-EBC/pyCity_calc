#!/usr/bin/env python
# coding=utf-8
"""
Exampel script for MeanShift algorithm usage
(http://scikit-learn.org/stable/index.html)
"""

import numpy as np
import matplotlib.pyplot as plt
from itertools import cycle
import copy

from sklearn.cluster import MeanShift, estimate_bandwidth
from sklearn.datasets.samples_generator import make_blobs


def run_meanshift_example():
    """
    meanshift exampel script ((http://scikit-learn.org/stable/index.html))
    """

    # ####################################################
    #  Generate sample data
    centers = [[1, 1], [-1, -1], [1, -1]]
    X, _ = make_blobs(n_samples=10000, centers=centers, cluster_std=0.6)

    print(X)
    print(len(X))

    #  ###################################################
    #  Compute clustering with MeanShift

    # The following bandwidth can be automatically detected using
    bandwidth = estimate_bandwidth(X, quantile=0.2, n_samples=500)

    print('bandwidth', bandwidth)

    ms = MeanShift(bandwidth=bandwidth, bin_seeding=True)

    print('ms', ms)
    ms.fit(X)
    labels = ms.labels_
    cluster_centers = ms.cluster_centers_

    labels_unique = np.unique(labels)
    n_clusters_ = len(labels_unique)

    print("number of estimated clusters : %d" % n_clusters_)

    # #########################################################
    # Plot result

    plt.figure(1)
    plt.clf()

    colors = cycle('bgrcmykbgrcmykbgrcmykbgrcmyk')
    for k, col in zip(range(n_clusters_), colors):
        my_members = labels == k
        cluster_center = cluster_centers[k]
        plt.plot(X[my_members, 0], X[my_members, 1], col + '.')
        plt.plot(cluster_center[0], cluster_center[1], 'o',
                 markerfacecolor=col,
                 markeredgecolor='k', markersize=14)
    plt.title('Estimated number of clusters: %d' % n_clusters_)
    plt.show()


def meanshift_cluster(city, plot_results=False):
    """
    Perform meanshift clustering on city object of pycity_calc

    Parameters
    ----------
    city : city object
        City object of pycity_calc
    plot_results : bool, optional
        Define if results should be plotted (default: False)

    Returns
    -------
    cluster_dict : dict
            Dictionary with cluster numbers (int) as keys and node ids (int)
            as values
    """

    #  Get number of buildings
    nb_buildings = len(city.nodelist_building)

    #  Generate numpy position array (init with zeros)
    x_array = np.zeros((nb_buildings, 2))

    #  Extract building ndoe positions and add to X
    for i in range(nb_buildings):
        node = city.nodelist_building[i]
        point = city.nodes[node]['position']
        x_array[i][0] = point.x
        x_array[i][1] = point.y

    # The following bandwidth can be automatically detected using
    bandwidth = estimate_bandwidth(x_array, quantile=0.2,
                                   n_samples=nb_buildings)

    print('bandwidth', bandwidth)

    ms = MeanShift(bandwidth=bandwidth, bin_seeding=True)

    print('ms', ms)
    ms.fit(x_array)

    labels = ms.labels_
    print('Labels', labels)

    cluster_centers = ms.cluster_centers_

    labels_unique = np.unique(labels)
    n_clusters_ = len(labels_unique)

    print("number of estimated clusters : %d" % n_clusters_)

    if plot_results:
        # #########################################################
        # Plot result
        plt.figure(1)
        plt.clf()

        colors = cycle('bgrcmykbgrcmykbgrcmykbgrcmyk')
        for k, col in zip(range(n_clusters_), colors):
            my_members = labels == k
            cluster_center = cluster_centers[k]
            plt.plot(x_array[my_members, 0], x_array[my_members, 1], col + 'o')
            # plt.plot(cluster_center[0], cluster_center[1], 'o',
            #          markerfacecolor=col,
            #          markeredgecolor='k', markersize=14)
        plt.title('Estimated number of clusters: %d' % n_clusters_)
        plt.rc('text', usetex=True)
        font = {'family': 'serif', 'size': 16}
        plt.rc('font', **font)
        plt.gca().set_aspect('equal', adjustable='box')
        plt.tight_layout()
        plt.show()

    #  Sort copy of building node list according to labels list
    node_list = copy.deepcopy(city.nodelist_building)
    labels, node_list = zip(*sorted(zip(labels, node_list)))

    print(labels)
    print(node_list)

    #  Generate cluster_dict
    cluster_dict = {}
    for i in range(len(labels)):
        label = labels[i]
        node_id = node_list[i]
        #  Append (or generate) list with cluster number as key
        cluster_dict.setdefault(label, []).append(node_id)

    return cluster_dict

if __name__ == '__main__':
    run_meanshift_example()