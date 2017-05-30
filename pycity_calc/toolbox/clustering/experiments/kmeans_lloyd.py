#!/usr/bin/env python
# coding=utf-8
"""
https://datasciencelab.wordpress.com/2013/12/12/clustering-with-k-means-in-python/
"""

import numpy as np
import random
import matplotlib.pyplot as plt


def init_board(N):
    X = np.array(
            [(random.uniform(-1, 1), random.uniform(-1, 1)) for i in range(N)])
    return X


def init_board_gauss(N, k):
    n = float(N)/k
    X = []
    for i in range(k):
        c = (random.uniform(-1, 1), random.uniform(-1, 1))
        s = random.uniform(0.05,0.5)
        x = []
        while len(x) < n:
            a, b = np.array([np.random.normal(c[0], s), np.random.normal(c[1], s)])
            # Continue drawing points from the distribution in the range [-1,1]
            if abs(a) < 1 and abs(b) < 1:
                x.append([a,b])
        X.extend(x)
    X = np.array(X)[:N]
    return X


def cluster_points(X, mu):
    clusters = {}
    for x in X:
        bestmukey = min([(i[0], np.linalg.norm(x - mu[i[0]])) \
                         for i in enumerate(mu)], key=lambda t: t[1])[0]
        try:
            clusters[bestmukey].append(x)
        except KeyError:
            clusters[bestmukey] = [x]
    return clusters


def reevaluate_centers(mu, clusters):
    newmu = []
    keys = sorted(clusters.keys())
    for k in keys:
        newmu.append(np.mean(clusters[k], axis=0))
    return newmu


def has_converged(mu, oldmu):
    return (set([tuple(a) for a in mu]) == set([tuple(a) for a in oldmu]))


def find_centers(X, K):
    # Initialize to K random centers
    oldmu = random.sample(list(X), K)
    mu = random.sample(list(X), K)#
    # clusters = cluster_points(X, mu)
    nb_iterations = 0
    while not has_converged(mu, oldmu):
        oldmu = mu
        # Assign all points in X to clusters
        clusters = cluster_points(X, mu)
        # Reevaluate centers
        mu = reevaluate_centers(oldmu, clusters)
        nb_iterations += 1
    print('nb_iterations: ', nb_iterations)
    return (mu, clusters)


def convert_array_list_to_x_y_lists(array_list):
    """
    Returns two lists (first, x values, second, y values of array in
    array_list.

    Parameters
    ----------
    array_list : list (of arrays)
        List with numpy.arrays (with x, y coordinates)

    Returns
    -------
    list_x : list (of floats)
        List with x coordinates
    list_y : list (of floats)
        List with y coordinates
    """
    list_x = []
    list_y = []
    for i in range(len(array_list)):
        list_x.append(array_list[i][0])
        list_y.append(array_list[i][1])
    return list_x, list_y


if __name__ == '__main__':
    #  Get initial configuration
    nb_points = 100
    init_array = init_board(nb_points)
    # init_array = init_board_gauss(nb_points, 5)

    #  Number of desired clusters
    K = 5

    print(init_array)

    mu, clusters = find_centers(init_array, K)
    print(clusters)
    color_list = ['r', 'b', 'm', 'g', 'k']
    counter = 0
    fig = plt.figure()
    for key in clusters:
        curr_cluster = clusters[key]
        curr_mu = mu[counter]
        x_list, y_list = convert_array_list_to_x_y_lists(curr_cluster)
        color = color_list[counter]
        plt.plot(x_list, y_list,  c=color, marker='o', linestyle='')
        plt.plot(curr_mu[0], curr_mu[1], mfc=color, marker='*', linestyle='',
                 markersize=25)
        counter += 1
    plt.show()
