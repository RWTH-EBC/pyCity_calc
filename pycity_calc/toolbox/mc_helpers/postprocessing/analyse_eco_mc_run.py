#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
from __future__ import division

import os
import pickle
import numpy as np


def count_zeros(res_array):
    """
    Count zeros (failed runs) in result array

    Parameters
    ----------
    res_array : np.array
        Numpy results array

    Returns
    -------
    nb_zeros : int
        Number of zeros
    """
    nb_zeros = 0

    for i in range(len(res_array)):
        if res_array[i] == 0:
            nb_zeros += 1

    return nb_zeros


def get_zero_idx(res_array):
    """
    Returns list with indexes of zeros in res_array

    Parameters
    ----------
    res_array : np.array
        Numpy results array

    Returns
    -------
    list_idx : list (of ints)
        List holding zero indexes
    """

    list_idx = []

    for i in range(len(res_array)):
        if res_array[i] == 0:
            list_idx.append(i)

    return list_idx


def remove_zeros(res_array):
    """
    Erase all zeros in res_array and return (reduced) array without zeros.

    Parameters
    ----------
    res_array : np.array
        Numpy results array

    Returns
    -------
    res_no_zeros : np.array
        Numpy results array without zeros (shorter than res_array, if zeros
        existed before)
    """

    nb_zeros = count_zeros(res_array=res_array)

    res_no_zeros = np.zeros(len(res_array) - nb_zeros)

    idx = 0
    for i in range(len(res_array)):
        if res_array[i] != 0:
            res_no_zeros[idx] = res_array[i]
            idx += 1

    return res_no_zeros


class EcoMCRunAnalyze(object):
    def __init__(self):
        """
        Constructor of EcoMCRunAnalyze object
        """

        self.__dict_results = None
        self.__dict_samples_const = None
        self.__dict_sample_esys = None
        self.__dict_setup = None
        self._list_idx = None
        self._city = None

    def __repr__(self):
        return 'EcoMCRunAnalyze object of pyCity_resilience. Can be used ' \
               'to analyze results of economic Monte-Carlo uncertainty run.'

    @property
    def dict_results(self):
        """
        dict_results property

        Returns
        -------
        dict_results : dict
            Dict with result values of MC run
        """
        return self.__dict_results

    @property
    def dict_samples_const(self):
        return self.__dict_samples_const

    @property
    def dict_samples_esys(self):
        return self.__dict_samples_esys

    @property
    def dict_setup(self):
        return self.__dict_setup

    @dict_results.setter
    def dict_results(self, dict_res):
        """
        Setter for dict_results property

        Parameters
        ----------
        dict_res : dict
            Dict with result values of MC run
        """
        self.__dict_results = dict_res

    @dict_samples_const.setter
    def dict_samples_const(self, dict_sam):
        """
        Setter for dict_samples_const property

        Parameters
        ----------
        dict_sam : dict
            Dict with sampling values of MC run
        """
        self.__dict_samples_const = dict_sam

    @dict_samples_esys.setter
    def dict_samples_esys(self, dict_sam):
        """
        Setter for dict_samples_esys property

        Parameters
        ----------
        dict_sam : dict
            Dict with sampling values of MC run
        """
        self.__dict_samples_esys = dict_sam

    @dict_setup.setter
    def dict_setup(self, dict_setup):
        """
        Setter for dict_setup property

        Parameters
        ----------
        dict_setup : dict
            Dict with setup values of MC run
        """
        self.__dict_setup = dict_setup

    def load_dict_res_from_path(self, dir):
        """
        Load dict_results from path and saves it to self.__dict_results

        Parameters
        ----------
        dir : str
            Path to dict_results pickle file
        """

        dict_res = pickle.load(open(dir, mode='rb'))

        self.dict_results = dict_res

    def load_dict_sample_const_from_path(self, dir):
        """
        Load dict_samples_const from path and saves it to
        self.__dict_samples_const

        Parameters
        ----------
        dir : str
            Path to dict_samples_const pickle file
        """

        dict_sam = pickle.load(open(dir, mode='rb'))

        self.dict_sample_const = dict_sam

    def load_dict_sample_esys_from_path(self, dir):
        """
        Load dict_sample_esys from path and saves it to
        self.__dict_sample_esys

        Parameters
        ----------
        dir : str
            Path to dict_sample_esys pickle file
        """

        dict_sam = pickle.load(open(dir, mode='rb'))

        self.dict_sample_esys = dict_sam

    def load_dict_setup_from_path(self, dir):
        """
        Load dict_setup from path and saves it to
        self.__ddict_setup

        Parameters
        ----------
        dir : str
            Path to dict_setup pickle file
        """

        dict_sam = pickle.load(open(dir, mode='rb'))

        self.dict_setup = dict_sam

    def load_city_obj_from_path(self, dir):
        """
        Load pickled city object and save it to self._city

        Parameters
        ----------
        dir : str
            Path to dict_setup pickle file
        """

        city = pickle.load(open(dir, mode='rb'))

        self._city = city

    # def get_idx_of_failed_runs(self, save_idx=True):
    #     """
    #     Try to identify failed runs by searching for indexes with zero entries
    #     in annuity results
    #
    #     Parameters
    #     ----------
    #     save_idx : bool, optional
    #         Defines if list_idx should be saved to EcoMCRunAnalyze object
    #
    #     Returns
    #     -------
    #     list_idx : list (of ints)
    #         List holding zero indexes
    #     """
    #
    #     array_annuity = self.get_annuity_results(erase_zeros=False)
    #
    #     list_idx = get_zero_idx(res_array=array_annuity)
    #
    #     if len(list_idx) > 0:
    #         print('Found zeros in annuity results array at indexes:')
    #         print(list_idx)
    #         print()
    #         print('Nb. of failed runs: ', str(len(list_idx)))
    #         print()
    #
    #     if save_idx:
    #         self._list_idx = list_idx

    def extract_basic_results(self):
        """
        Extract basic results and sample data
        """

        array_ann = self.dict_results['annuity']
        array_co2 = self.dict_results['co2']
        array_sh_dem = self.dict_results['sh_dem']
        array_el_dem = self.dict_results['el_dem']
        array_dhw_dem = self.dict_results['dhw_dem']

    def get_annuity_results(self, erase_zeros=True):
        """
        Returns array of annuity results

        Parameters
        ----------
        erase_zeros : bool, optional
            Defines, if zeros (failed runs) should be erased (default: True)
            If True, eliminates

        Returns
        -------
        array_ann : np.array (of float)
            Array holding annuity result values in Euro/a
        """

        if self.dict_results is None:
            msg = 'Cannot extract annuity results, as dict_results is empty!'
            raise AssertionError(msg)

        array_ann = self.dict_results['annuity']

        if erase_zeros:
            array_ann = remove_zeros(res_array=array_ann)

        return array_ann

    def get_co2_results(self, erase_zeros=True):
        """
        Returns array of co2 results

        Parameters
        ----------
        erase_zeros : bool, optional
            Defines, if zeros (failed runs) should be erased (default: True)
            If True, eliminates

        Returns
        -------
        array_ann : np.array (of float)
            Array holding co2 result values in kg/a
        """

        if self.dict_results is None:
            msg = 'Cannot extract annuity results, as dict_results is empty!'
            raise AssertionError(msg)

        array_co2 = self.dict_results['co2']

        if erase_zeros:
            array_co2 = remove_zeros(res_array=array_co2)

        return array_co2


if __name__ == '__main__':
    this_path = os.path.dirname(os.path.abspath(__file__))

    #  Filenames and path definitions
    #  ####################################################################
    file_res = 'mc_run_results_dict.pkl'
    file_sam_const = 'mc_run_sample_dict_const.pkl'
    file_sam_esys = 'mc_run_sample_dict_esys.pkl'
    file_setup = 'mc_run_setup_dict.pkl'
    file_city = 'city_clust_simple_with_esys.pkl'

    path_res = os.path.join(this_path, 'input', file_res)
    path_sam_const = os.path.join(this_path, 'input', file_sam_const)
    path_sam_esys = os.path.join(this_path, 'input', file_sam_esys)
    path_setup = os.path.join(this_path, 'input', file_setup)
    path_city = os.path.join(this_path, 'input', file_city)

    #  Generate EcoMRRunAnalyze object
    #  ####################################################################
    mc_analyze = EcoMCRunAnalyze()

    #  Add results and sample dict
    #  ####################################################################
    mc_analyze.load_dict_res_from_path(dir=path_res)
    mc_analyze.load_dict_sample_const_from_path(dir=path_sam_const)
    mc_analyze.load_dict_sample_esys_from_path(dir=path_sam_esys)
    mc_analyze.load_dict_setup_from_path(dir=path_setup)
    mc_analyze.load_city_obj_from_path(dir=path_city)

    #  Evaluation
    #  ####################################################################
    array_annuity = mc_analyze.get_annuity_results()
    array_co2 = mc_analyze.get_co2_results()

    import matplotlib.pyplot as plt

    plt.hist(array_annuity, bins='auto')
    plt.show()
    plt.close()

    plt.hist(array_co2, bins='auto')
    plt.show()
    plt.close()
