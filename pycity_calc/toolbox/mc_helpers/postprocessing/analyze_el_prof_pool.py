#!/usr/bin/env python
# coding=utf-8
"""

"""
from __future__ import division

import os
import pickle
import numpy as np
import matplotlib.pylab as plt

def plot_profile_pool(dict_profiles):
    """

    Parameters
    ----------
    dict_profiles

    Returns
    -------
    dict_profiles : dict
        Dict holding building ids as keys and numpy.arrays with different
        el. load profiles per building
    """

    #  Loop over building ids
    for key in dict_profiles.keys():

        fig = plt.figure()

        profile_set = dict_profiles[key]

        el_profile_matrix = profile_set['el_profiles']
        # dhw_profile_matrix = profile_set['dhw_profiles']

        av_load = np.zeros(len(el_profile_matrix[0]))

        for i in range(len(el_profile_matrix)):
            el_load = el_profile_matrix[i, :]
            plt.plot(el_load, alpha=0.5, c='gray')
            av_load += el_load

        #  Divide by number of profiles
        av_load /= (i + 1)

        plt.plot(av_load, c='black')

        plt.tight_layout()
        plt.show()
        plt.close()


if __name__ == '__main__':
    filename = 'dict_profile_samples.pkl'

    path_this = os.path.dirname(os.path.abspath(__file__))
    path_mc = os.path.dirname(path_this)
    path_input = os.path.join(path_mc, 'output', filename)

    #  Load profile dict
    dict_profiles = pickle.load(open(path_input, mode='rb'))

    plot_profile_pool(dict_profiles=dict_profiles)
