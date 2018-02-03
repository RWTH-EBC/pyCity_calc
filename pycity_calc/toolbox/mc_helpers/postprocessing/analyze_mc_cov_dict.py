#!/usr/bin/env python
# coding=utf-8
"""

"""
from __future__ import division

import os
import pickle
import numpy as np
import matplotlib.pylab as plt


def analyze_cov(dict_mc_cov):
    """
    Analyze coverage dict

    Parameters
    ----------
    dict_mc_cov : dict
        Dictionary holding thermal/electrical coverage factors
        dict_mc_cov['th_cov_boi'] = array_th_cov_boi
        dict_mc_cov['th_cov_chp'] = array_th_cov_chp
        dict_mc_cov['th_cov_hp_aw'] = array_th_cov_hp_aw
        dict_mc_cov['th_cov_hp_ww'] = array_th_cov_hp_ww
        dict_mc_cov['th_cov_eh'] = array_th_cov_eh
        dict_mc_cov['el_cov_chp'] = array_el_cov_chp
        dict_mc_cov['el_cov_pv'] = array_el_cov_pv
        dict_mc_cov['el_cov_grid']
    """

    fig = plt.figure()

    list_names = ['b', 'c', 'a', 'w', 'e', 'h', 'p', 'g']


    idx = 0
    for key in dict_mc_cov.keys():
        data = dict_mc_cov[key]

        fig.add_subplot(1, int(len(dict_mc_cov)+1), int(idx+1))

        ax = fig.gca()

        pb = ax.boxplot(data)

        ax.set_xticklabels(list_names[idx])

        idx += 1

    plt.legend()
    plt.show()
    plt.close()


if __name__ == '__main__':
    filename = 'mc_cov_dict.pkl'

    path_this = os.path.dirname(os.path.abspath(__file__))
    path_mc = os.path.dirname(path_this)
    path_input = os.path.join(path_mc, 'output', filename)

    dict_cov = pickle.load(open(path_input, mode='rb'))

    analyze_cov(dict_mc_cov=dict_cov)
