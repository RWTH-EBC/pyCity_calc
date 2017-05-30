#!/usr/bin/env python
# coding=utf-8
"""
Script to manually generate cluster dictionary
"""

import os
import pickle


def gen_clust_dict():

    clust_dict = {}

    clust_dict[5] = [1009, 1003, 1015, 1018]
    clust_dict[6] = [1016, 1017]
    clust_dict[7] = [1019]
    clust_dict[8] = [1023]
    clust_dict[9] = [1022, 1021]

    filename = 'clust_dict_manual.p'
    this_path = os.path.dirname(os.path.abspath(__file__))
    save_path = os.path.join(this_path, 'output', filename)

    #  Pickle and dump cluster dictionary
    pickle._dump(clust_dict, open(save_path, mode='wb'))

if __name__ == '__main__':

    gen_clust_dict()