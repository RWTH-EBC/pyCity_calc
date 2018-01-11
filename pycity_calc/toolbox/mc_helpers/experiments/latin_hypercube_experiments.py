#!/usr/bin/env python
# coding=utf-8
"""

"""
from __future__ import division

import numpy as np
import pyDOE
import matplotlib.pylab as plt
from scipy.stats import nakagami
from scipy import stats
import scipy.stats.distributions as distr


def gen_equal_dist_samples(nb_samples=100000, low=0, high=100):

    return np.random.uniform(low=low, high=high, size=nb_samples)

def gen_norm_dist_samples(nb_samples=100000, mean=10, std=2):

    return np.random.normal(loc=mean, scale=std, size=nb_samples)

def gen_nakagami_dist(nb_samples=100000):

    return nakagami.rvs(0.6, scale=0.4, size=nb_samples)

def gen_log_norm_dist(nb_samples=100000, mean=0, sigma=0.4):

    return np.random.lognormal(mean=mean, sigma=sigma, size=nb_samples)

if __name__ == '__main__':

    nb_red = 100

    design = pyDOE.lhs(n=3, samples=nb_red, criterion='center')

    #  Check if normal distribution is valid

    list_norm_sample = distr.norm(loc=10, scale=2).ppf(design[:, 0])

    list_norm = gen_norm_dist_samples()

    plt.hist(list_norm, label='Normal', normed=True)
    plt.hist(list_norm_sample, label='LatinHypercube', normed=True)
    plt.legend()
    plt.show()
    plt.close()

    mean, std = stats.norm.fit(data=list_norm)

    print('Mean/std of latin hypercube samples: ')
    print(mean, std)
    print()

    #  Check if log-normal distribution is valid

    list_log_samples = distr.lognorm(s=1).ppf(design[:, 1])

    list_log = gen_log_norm_dist()
    print('min/max of lat. hypercube samples:')
    print(min(list_log_samples), max(list_log_samples))
    print('min/max of regular samples:')
    print(min(list_log), max(list_log))
    print()

    plt.hist(list_log, label='Log', normed=True)
    plt.hist(list_log_samples, label='LatinHypercube', normed=True)
    plt.legend()
    plt.show()
    plt.close()

    shape, loc, scale = stats.lognorm.fit(data=list_log, floc=0)

    print('shape: ', shape)
    print('loc:', loc)
    print('scale: ', scale)
