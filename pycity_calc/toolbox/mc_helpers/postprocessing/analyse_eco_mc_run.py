#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
from __future__ import division

import os
import copy
import pickle
import numpy as np
import matplotlib.pyplot as plt


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

        self._city = None
        self._list_idx_failed_runs = None
        self._nb_runs = None
        self._failure_tolerance = None
        self._heating_off = None

        self._array_ann_mod = None
        self._array_co2_mod = None
        self._array_sh_dem_mod = None
        self._array_el_dem_mod = None
        self._array_dhw_dem_mod = None

        #  Net energy to annuity / to CO2
        self._array_en_to_an = None
        self._array_en_to_co2 = None

        #  Net exergy to annuity / to CO2
        self._array_ex_to_an = None
        self._array_ex_to_co2 = None

        #  Annuity / CO2 to net exergy
        self._array_ann_to_ex = None
        self._array_co2_to_ex = None

        self._array_ann_to_en = None
        self._array_co2_to_en = None

        #  Dimensionless parameters for annuity and co2
        self._array_dimless_cost = None
        self._array_dimless_co2 = None

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

    def extract_basic_results(self, remove_failed=True):
        """
        Extract basic results and sample data and save it to EcoMCRunAnalyze
        object

        Parameters
        ----------
        remove_failed : bool, optional
            Remove failed runs (default: True). Failed runs are identified by
            _list_idx_failed_runs
        """

        if self.dict_results is None:
            msg = 'Cannot extract results, as dict_results is empty!'
            raise AssertionError(msg)

        # Extract settings
        self._nb_runs = self.dict_setup['nb_runs']
        self._failure_tolerance = self.dict_setup['failure_tolerance']
        self._heating_off = self.dict_setup['heating_off']
        self._list_idx_failed_runs = self.dict_setup['idx_failed_runs']

        #  Extract annuity and CO2 values
        array_ann = self.dict_results['annuity']
        array_co2 = self.dict_results['co2']

        #  Extract city net energy demand values
        array_sh_dem = self.dict_results['sh_dem']
        array_el_dem = self.dict_results['el_dem']
        array_dhw_dem = self.dict_results['dhw_dem']

        array_ann_mod = copy.copy(array_ann)
        array_co2_mod = copy.copy(array_co2)
        array_sh_dem_mod = copy.copy(array_sh_dem)
        array_el_dem_mod = copy.copy(array_el_dem)
        array_dhw_dem_mod = copy.copy(array_dhw_dem)

        if remove_failed:
            if len(self._list_idx_failed_runs) > 0:

                nb_fails = len(self._list_idx_failed_runs)

                #  Create new result arrays with zeros
                array_ann_mod = np.zeros(len(array_ann) - nb_fails)
                array_co2_mod = np.zeros(len(array_ann) - nb_fails)
                array_sh_dem_mod = np.zeros(len(array_ann) - nb_fails)
                array_el_dem_mod = np.zeros(len(array_ann) - nb_fails)
                array_dhw_dem_mod = np.zeros(len(array_ann) - nb_fails)

                idx = 0
                for i in range(len(array_ann)):
                    if i not in self._list_idx_failed_runs:
                        array_ann_mod[idx] = array_ann[i]
                        array_co2_mod[idx] = array_co2[i]
                        array_sh_dem_mod[idx] = array_sh_dem[i]
                        array_el_dem_mod[idx] = array_el_dem[i]
                        array_dhw_dem_mod[idx] = array_dhw_dem[i]
                        #  Count mod array idx up
                        idx += 1

        # Save new modified result arrays
        self._array_ann_mod = array_ann_mod
        self._array_co2_mod = array_co2_mod
        self._array_sh_dem_mod = array_sh_dem_mod
        self._array_el_dem_mod = array_el_dem_mod
        self._array_dhw_dem_mod = array_dhw_dem_mod

    def get_nb_failed_runs(self):
        """
        Returns nb. of failed runs

        Returns
        -------
        nb_failed : int
            Number of failed runs (EnergyBalanceException)
        """
        if self._list_idx_failed_runs is None:
            msg = '_list_idx_failed_runs is None. Thus, cannot return nb. ' \
                  'of failed runs!'
            raise AssertionError(msg)

        return len(self._list_idx_failed_runs)

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

    def calc_net_energy_to_co2_ratio(self, save_res=True):
        """
        Calculates net energy to co2 ratio as estimator for
        ecologic efficiency.

        Parameters
        ----------
        save_res : bool, optional
            Defines, if results should be saved to _array_en_to_an
            (default: True)

        Returns
        -------
        array_en_to_co2 : np.array (of floats)
            Numpy array holding net energy to co2 ratios in kWh / kg (CO2)
        """

        if (self._array_co2_mod is None
                or self._array_sh_dem_mod is None
                or self._array_el_dem_mod is None
                or self._array_dhw_dem_mod is None):
            msg = 'Cannot calculate net energy to annuity ratio, as inputs ' \
                  'are missing. Have you loaded all results files and called' \
                  ' extract_basic_results?'
            raise AssertionError(msg)

        # Dummy arrays
        array_en_to_co2 = np.zeros(len(self._array_co2_mod))

        #  Sum up energy values
        array_total_net_en = self._array_sh_dem_mod \
                             + self._array_el_dem_mod \
                             + self._array_dhw_dem_mod

        for i in range(len(array_en_to_co2)):
            if self._array_co2_mod[i] == 0:
                co2_mod = 0.00000000001
            else:
                co2_mod = self._array_co2_mod[i]

            array_en_to_co2[i] = array_total_net_en[i] / co2_mod

        if save_res:
            self._array_en_to_co2 = array_en_to_co2

        return array_en_to_co2

    #  TODO: Add exergy calculation
    # def calc_net_exergy_to_co2_ratio(self, save_res=True):
    #     """
    #     Calculates net exergy to co2 ratio as estimator for
    #     ecologic efficiency.
    #
    #     Parameters
    #     ----------
    #     save_res : bool, optional
    #         Defines, if results should be saved to _array_en_to_an
    #         (default: True)
    #
    #     Returns
    #     -------
    #     array_ex_to_co2 : np.array (of floats)
    #         Numpy array holding net exergy to co2 ratios in kWh / kg (CO2)
    #     """
    #
    #     if (self._array_co2_mod is None
    #         or self._array_sh_dem_mod is None
    #         or self._array_el_dem_mod is None
    #         or self._array_dhw_dem_mod is None):
    #         msg = 'Cannot calculate net energy to annuity ratio, as inputs ' \
    #               'are missing. Have you loaded all results files and called' \
    #               ' extract_basic_results?'
    #         raise AssertionError(msg)
    #
    #     # Dummy arrays
    #     array_ex_to_co2 = np.zeros(len(self._array_co2_mod))
    #
    #     #  Use net exergy concept
    #     array_net_ex_sh = self._array_sh_dem_mod * (1 - 20 / 70)
    #     array_net_ex_dhw = self._array_dhw_dem_mod * (1 - 20 / 80)
    #
    #     #  Total net exergy
    #     array_net_ex_total = array_net_ex_sh \
    #                          + array_net_ex_dhw \
    #                          + self._array_el_dem_mod
    #
    #     for i in range(len(array_ex_to_co2)):
    #         array_ex_to_co2[i] = array_net_ex_total[i] / self._array_co2_mod[i]
    #
    #     if save_res:
    #         self._array_ex_to_co2 = array_ex_to_co2
    #
    #     return array_ex_to_co2

    def calc_net_energy_to_annuity_ratio(self, save_res=True):
        """
        Calculates net energy to annuity ratio as estimator for
        economic efficiency.

        Parameters
        ----------
        save_res : bool, optional
            Defines, if results should be saved to _array_en_to_an
            (default: True)

        Returns
        -------
        array_en_to_an : np.array (of floats)
            Numpy array holding net energy to annuity ratios in kWh / Euro
        """

        if (self._array_ann_mod is None
                or self._array_sh_dem_mod is None
                or self._array_el_dem_mod is None
                or self._array_dhw_dem_mod is None):
            msg = 'Cannot calculate net energy to annuity ratio, as inputs ' \
                  'are missing. Have you loaded all results files and called' \
                  ' extract_basic_results?'
            raise AssertionError(msg)

        # Dummy arrays
        array_en_to_an = np.zeros(len(self._array_ann_mod))

        #  Sum up energy values
        array_total_net_en = self._array_sh_dem_mod \
                             + self._array_el_dem_mod \
                             + self._array_dhw_dem_mod

        for i in range(len(array_en_to_an)):
            if self._array_ann_mod[i] == 0:
                ann_mod = 0.000000000001
            else:
                ann_mod = self._array_ann_mod[i]

            array_en_to_an[i] = array_total_net_en[i] / ann_mod

        if save_res:
            self._array_en_to_an = array_en_to_an

        return array_en_to_an

    #  TODO: Add exergy calculation
    # def calc_net_exergy_to_annuity_ratio(self, save_res=True):
    #     """
    #     Calculates net exergy to annuity ratio as estimator for
    #     economic efficiency.
    #
    #     Parameters
    #     ----------
    #     save_res : bool, optional
    #         Defines, if results should be saved to _array_en_to_an
    #         (default: True)
    #
    #     Returns
    #     -------
    #     array_ex_to_an : np.array (of floats)
    #         Numpy array holding net exergy to annuity ratios in kWh / Euro
    #     """
    #
    #     if (self._array_ann_mod is None
    #         or self._array_sh_dem_mod is None
    #         or self._array_el_dem_mod is None
    #         or self._array_dhw_dem_mod is None):
    #         msg = 'Cannot calculate net energy to annuity ratio, as inputs ' \
    #               'are missing. Have you loaded all results files and called' \
    #               ' extract_basic_results?'
    #         raise AssertionError(msg)
    #
    #     # Dummy arrays
    #     array_ex_to_an = np.zeros(len(self._array_ann_mod))
    #
    #     #  Use net exergy concept
    #     array_net_ex_sh = self._array_sh_dem_mod * (1 - 20 / 70)
    #     array_net_ex_dhw = self._array_dhw_dem_mod * (1 - 20 / 80)
    #
    #     #  Total net exergy
    #     array_net_ex_total = array_net_ex_sh \
    #                          + array_net_ex_dhw \
    #                          + self._array_el_dem_mod
    #
    #     for i in range(len(array_ex_to_an)):
    #         array_ex_to_an[i] = array_net_ex_total[i] / self._array_ann_mod[i]
    #
    #     if save_res:
    #         self._array_ex_to_an = array_ex_to_an
    #
    #     return array_ex_to_an

    def calc_net_energy_to_co2_mean(self):
        """
        Calculates and returns mean of net energy to CO2 values

        Returns
        -------
        net_e_to_co2_mean : float
            Mean of net energy to CO2 values
        """

        return np.mean(a=self._array_en_to_co2)

    def calc_net_energy_to_ann_mean(self):
        """
        Calculates and returns mean of net energy to annuity values

        Returns
        -------
        net_e_to_ann_mean : float
            Mean of net energy to annuity values
        """

        return np.mean(a=self._array_en_to_an)

    def calc_net_energy_to_co2_std(self):
        """
        Calculates and returns standard deviation of net energy to CO2 values

        Returns
        -------
        net_e_to_co2_std : float
            Standard deviation of net energy to CO2 values
        """

        return np.std(a=self._array_en_to_co2)

    def calc_net_energy_to_ann_std(self):
        """
        Calculates and returns standard deviation of net energy to annuity
        values

        Returns
        -------
        net_e_to_ann_std : float
            Standard deviation of net energy to annuity values
        """

        return np.std(a=self._array_en_to_an)

    #  TODO: Add exergy calculation
    # def calc_co2_to_net_exergy_ratio(self, save_res=True):
    #     """
    #     Calculates CO2 to net exergy to co2 ratio as estimator for
    #     ecologic efficiency.
    #
    #     Parameters
    #     ----------
    #     save_res : bool, optional
    #         Defines, if results should be saved
    #         (default: True)
    #
    #     Returns
    #     -------
    #     array_co2_to_ex: np.array (of floats)
    #         Numpy array holding CO2 to net exergy to ratios in kg (CO2) / kWh
    #     """
    #
    #     if (self._array_co2_mod is None
    #         or self._array_sh_dem_mod is None
    #         or self._array_el_dem_mod is None
    #         or self._array_dhw_dem_mod is None):
    #         msg = 'Cannot calculate net energy to annuity ratio, as inputs ' \
    #               'are missing. Have you loaded all results files and called' \
    #               ' extract_basic_results?'
    #         raise AssertionError(msg)
    #
    #     # Dummy arrays
    #     array_co2_to_ex = np.zeros(len(self._array_co2_mod))
    #
    #     #  Use net exergy concept
    #     array_net_ex_sh = self._array_sh_dem_mod * (1 - 20 / 70)
    #     array_net_ex_dhw = self._array_dhw_dem_mod * (1 - 20 / 80)
    #
    #     #  Total net exergy
    #     array_net_ex_total = array_net_ex_sh \
    #                          + array_net_ex_dhw \
    #                          + self._array_el_dem_mod
    #
    #     for i in range(len(array_co2_to_ex)):
    #         array_co2_to_ex[i] = self._array_co2_mod[i] / array_net_ex_total[i]
    #
    #     if save_res:
    #         self._array_co2_to_ex = array_co2_to_ex
    #
    #     return array_co2_to_ex

    #  TODO: Add exergy calculation
    # def calc_annuity_to_net_exergy_ratio(self, save_res=True):
    #     """
    #     Calculates annuity to net exergy to co2 ratio as estimator for
    #     ecologic efficiency.
    #
    #     Parameters
    #     ----------
    #     save_res : bool, optional
    #         Defines, if results should be saved
    #         (default: True)
    #
    #     Returns
    #     -------
    #     array_ann_to_ex: np.array (of floats)
    #         Numpy array holding annuity to net exergy to ratios in Euro / kWh
    #     """
    #
    #     if (self._array_ann_mod is None
    #         or self._array_sh_dem_mod is None
    #         or self._array_el_dem_mod is None
    #         or self._array_dhw_dem_mod is None):
    #         msg = 'Cannot calculate net energy to annuity ratio, as inputs ' \
    #               'are missing. Have you loaded all results files and called' \
    #               ' extract_basic_results?'
    #         raise AssertionError(msg)
    #
    #     # Dummy arrays
    #     array_ann_to_ex = np.zeros(len(self._array_ann_mod))
    #
    #     #  Use net exergy concept
    #     array_net_ex_sh = self._array_sh_dem_mod * (1 - 20 / 70)
    #     array_net_ex_dhw = self._array_dhw_dem_mod * (1 - 20 / 80)
    #
    #     #  Total net exergy
    #     array_net_ex_total = array_net_ex_sh \
    #                          + array_net_ex_dhw \
    #                          + self._array_el_dem_mod
    #
    #     for i in range(len(array_ann_to_ex)):
    #         array_ann_to_ex[i] = array_net_ex_total[i] / self._array_co2_mod[i]
    #
    #     if save_res:
    #         self._array_ann_to_ex = array_ann_to_ex
    #
    #     return array_ann_to_ex

    def calc_co2_to_net_energy_ratio(self, save_res=True):
        """
        Calculates CO2 to net energy to co2 ratio as estimator for
        ecologic efficiency.

        Parameters
        ----------
        save_res : bool, optional
            Defines, if results should be saved
            (default: True)

        Returns
        -------
        array_co2_to_en: np.array (of floats)
            Numpy array holding CO2 to net energy to ratios in kg (CO2) / kWh
        """

        if (self._array_co2_mod is None
                or self._array_sh_dem_mod is None
                or self._array_el_dem_mod is None
                or self._array_dhw_dem_mod is None):
            msg = 'Cannot calculate net energy to annuity ratio, as inputs ' \
                  'are missing. Have you loaded all results files and called' \
                  ' extract_basic_results?'
            raise AssertionError(msg)

        # Dummy arrays
        array_co2_to_en = np.zeros(len(self._array_co2_mod))

        array_total_en = self._array_sh_dem_mod + self._array_el_dem_mod \
                         + self._array_dhw_dem_mod

        for i in range(len(array_co2_to_en)):
            array_co2_to_en[i] = self._array_co2_mod[i] / array_total_en[i]

        if save_res:
            self._array_co2_to_en = array_co2_to_en

        return array_co2_to_en

    def calc_annuity_to_net_energy_ratio(self, save_res=True):
        """
        Calculates annuity to net energy to co2 ratio as estimator for
        ecologic efficiency.

        Parameters
        ----------
        save_res : bool, optional
            Defines, if results should be saved
            (default: True)

        Returns
        -------
        array_ann_to_en: np.array (of floats)
            Numpy array holding annuity to net energy to ratios in Euro / kWh
        """

        if (self._array_ann_mod is None
                or self._array_sh_dem_mod is None
                or self._array_el_dem_mod is None
                or self._array_dhw_dem_mod is None):
            msg = 'Cannot calculate net energy to annuity ratio, as inputs ' \
                  'are missing. Have you loaded all results files and called' \
                  ' extract_basic_results?'
            raise AssertionError(msg)

        # Dummy arrays
        array_ann_to_en = np.zeros(len(self._array_ann_mod))

        array_total_en = self._array_sh_dem_mod + self._array_el_dem_mod \
                         + self._array_dhw_dem_mod

        for i in range(len(array_ann_to_en)):
            array_ann_to_en[i] = self._array_ann_mod[i] / array_total_en[i]

        if save_res:
            self._array_ann_to_en = array_ann_to_en

        return array_ann_to_en

    @staticmethod
    def calc_res_factor(array_in, obj, q=-1):
        """
        Calculate resilience factor

        Parameters
        ----------
        array_in : np.array  (of floats)
            Array holding result values
        obj : str
            Objective. Options:
            - 'min' : Minimization
            - 'max' : Maximization
        q : float
            Preference value for mu-sigma-evaluation (default: -1)

        Returns
        -------
        risk_av_factor : float
            Risk aversion factor to evaluate solution
        """

        assert obj in ['min', 'max'], 'Unknown objective!'

        #  Calculate mean
        mean = np.mean(a=array_in)

        #  Calculate standard deviation
        std = np.std(a=array_in)

        if obj == 'max':
            # risk_av_factor = mean / (std ** (10 / 25))
            risk_av_factor = mean + q * std ** 2
        elif obj == 'min':
            # risk_av_factor = mean + 10 * std ** 2 / mean
            risk_av_factor = mean - q * std ** 2
        return risk_av_factor

    @staticmethod
    def calc_risk_friendly_factor(array_in, obj, q=1):
        """
        Calculate risk friendly factor

        Parameters
        ----------
        array_in : np.array  (of floats)
            Array holding result values
        obj : str
            Objective. Options:
            - 'min' : Minimization
            - 'max' : Maximization
        q : float
            Preference value for mu-sigma-evaluation (default: 1)

        Returns
        -------
        risk_friendly_factor : float
            Risk aversion factor to evaluate solution
        """

        assert obj in ['min', 'max'], 'Unknown objective!'

        #  Calculate mean
        mean = np.mean(a=array_in)

        #  Calculate standard deviation
        std = np.std(a=array_in)

        if obj == 'max':
            # risk_friendly_factor = mean / (std ** (25 / 10))
            risk_friendly_factor = mean + q * std ** 2

        elif obj == 'min':
            # risk_friendly_factor = mean - 10 * std ** 2 / mean
            risk_friendly_factor = mean - q * std ** 2

        return risk_friendly_factor

    def calc_risk_averse_parameters(self, type, risk_factor=-1):
        """
        Calculate and returns risk averse parameter, depending on input type.
        Uses mean and standard deviation of result parameters for evaluation.
        Differentiates between objectives for minimization and maximization

        Parameters
        ----------
        type : str
            Type of evaluated result parameter. Options:
            - 'annuity' : Annualized cost
            - 'co2' : Emissions
            - 'en_to_an' : Net energy to annuity ratio
            - 'en_to_co2' : Net energy to co2 ratio
            - 'ex_to_an' : Net exergy to annuity ratio
            - 'ex_to_co2' : Net exergy to co2 ratio
            - 'dimless_an' : Dimensionless annuity
            - 'dimless_co2' : Dimensionless emissions
        risk_factor : float, optional
            Preference/risk value for mu-sigma-evaluation for risk averse
            preference (default: -1)

        Returns
        -------
        risk_av_factor : float
            Risk aversion factor to evaluate solution
        """

        if type not in ['annuity', 'co2', 'en_to_an', 'en_to_co2',
                        'ex_to_an', 'ex_to_co2', 'an_to_en', 'co2_to_en',
                        'dimless_an', 'dimless_co2']:
            msg = 'Unknown input type for calc_risk_averse_parameters()'
            raise AssertionError(msg)

        if type == 'annuity':
            array_in = self._array_ann_mod
            obj = 'min'
        elif type == 'co2':
            array_in = self._array_co2_mod
            obj = 'min'
        elif type == 'en_to_an':
            array_in = self._array_en_to_an
            obj = 'max'
        elif type == 'en_to_co2':
            array_in = self._array_en_to_co2
            obj = 'max'
        elif type == 'ex_to_an':
            array_in = self._array_ex_to_an
            obj = 'max'
        elif type == 'ex_to_co2':
            array_in = self._array_ex_to_co2
            obj = 'max'
        elif type == 'an_to_en':
            array_in = self._array_ann_to_en
            obj = 'min'
        elif type == 'co2_to_en':
            array_in = self._array_co2_to_en
            obj = 'min'
        elif type == 'dimless_an':
            array_in = self._array_dimless_cost
            obj = 'min'
        elif type == 'dimless_co2':
            array_in = self._array_dimless_co2
            obj = 'min'

        risk_av_factor = self.calc_res_factor(array_in=array_in, obj=obj,
                                              q=risk_factor)

        return risk_av_factor

    def calc_risk_friendly_parameters(self, type, risk_factor=1):
        """
        Calculate and returns risk friendly parameter, depending on input type.
        Uses mean and standard deviation of result parameters for evaluation.
        Differentiates between objectives for minimization and maximization

        Parameters
        ----------
        type : str
            Type of evaluated result parameter. Options:
            - 'annuity' : Annualized cost
            - 'co2' : Emissions
            - 'en_to_an' : Net energy to annuity ratio
            - 'en_to_co2' : Net energy to co2 ratio
            - 'ex_to_an' : Net exergy to annuity ratio
            - 'ex_to_co2' : Net exergy to co2 ratio
            - 'dimless_an' : Dimensionless annuity
            - 'dimless_co2' : Dimensionless emissions
        risk_factor : float, optional
            Preference/risk value for mu-sigma-evaluation for risk
            friendly preference (default: 1)

        Returns
        -------
        risk_friendly_factor : float
            Risk friendly factor to evaluate solution
        """

        if type not in ['annuity', 'co2', 'en_to_an', 'en_to_co2',
                        'ex_to_an', 'ex_to_co2', 'an_to_en', 'co2_to_en',
                        'dimless_an', 'dimless_co2']:
            msg = 'Unknown input type for calc_risk_averse_parameters()'
            raise AssertionError(msg)

        if type == 'annuity':
            array_in = self._array_ann_mod
            obj = 'min'
        elif type == 'co2':
            array_in = self._array_co2_mod
            obj = 'min'
        elif type == 'en_to_an':
            array_in = self._array_en_to_an
            obj = 'max'
        elif type == 'en_to_co2':
            array_in = self._array_en_to_co2
            obj = 'max'
        elif type == 'ex_to_an':
            array_in = self._array_ex_to_an
            obj = 'max'
        elif type == 'ex_to_co2':
            array_in = self._array_ex_to_co2
            obj = 'max'
        elif type == 'an_to_en':
            array_in = self._array_ann_to_en
            obj = 'min'
        elif type == 'co2_to_en':
            array_in = self._array_co2_to_en
            obj = 'min'
        elif type == 'dimless_an':
            array_in = self._array_dimless_cost
            obj = 'min'
        elif type == 'dimless_co2':
            array_in = self._array_dimless_co2
            obj = 'min'

        risk_friendly_factor = self. \
            calc_risk_friendly_factor(array_in=array_in,
                                      obj=obj, q=risk_factor)

        return risk_friendly_factor

    def calc_dimless_cost_co2(self, dict_ref_run, save_res=True):
        """
        Calculate dimensionless cost and co2 values. Requires external
        mc run results dict (of reference run with boilers, only)

        Parameters
        ----------
        dict_ref_run : dict
            Results dict of MC runner (ref. run with boilers, only)
        save_res : bool, optional
            Defines, if results should be saved
            (default: True)

        Returns
        -------
        tup_res : tuple (of arrays)
            2d tuple holding arrays with dimensionless parameters for cost
            and emissions (array_dimless_cost, array_dimless_co2)
        """

        #  Extract dict_ref_run values for successful runs of opt. run
        self._list_idx_failed_runs

        #  Extract result arrays (full length)
        array_cost_ref = dict_ref_run['annuity']
        array_co2_ref = dict_ref_run['co2']

        #  Dummy arrays with length of successful opt. runs
        array_cost_extr = np.zeros(len(array_cost_ref) -
                                   len(self._list_idx_failed_runs))
        array_co2_extr = np.zeros(len(array_co2_ref) -
                                  len(self._list_idx_failed_runs))

        #  Write results to new arrays (length of sucessful runs)
        j = 0
        for i in range(len(array_cost_ref)):
            if i not in self._list_idx_failed_runs:
                array_cost_extr[j] = array_cost_ref[i]
                array_co2_extr[j] = array_co2_ref[i]
                j += 1

        #  Generate dummy arrays for dimensionless cost and co2 factors
        array_dimless_cost = np.zeros(len(array_cost_extr))
        array_dimless_co2 = np.zeros(len(array_co2_extr))

        for i in range(len(array_dimless_cost)):
            if array_cost_extr[i] != 0:
                #  Annuity of optimized system to annuity of ref. system
                array_dimless_cost[i] = \
                    self._array_ann_mod[i] / array_cost_extr[i]
            else:
                array_dimless_cost[i] = \
                    self._array_ann_mod[i] / 0.0000000000000000000000000001

            if array_co2_extr[i] != 0:
                array_dimless_co2[i] = \
                    self._array_co2_mod[i] / array_co2_extr[i]
            else:
                array_dimless_co2[i] = \
                    self._array_co2_mod[i] / 0.0000000000000000000000000001

        if save_res:
            self._array_dimless_cost = array_dimless_cost
            self._array_dimless_co2 = array_dimless_co2

        return (array_dimless_cost, array_dimless_co2)

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

    #  Extract basic results
    #  ####################################################################
    mc_analyze.extract_basic_results()
    mc_analyze.calc_net_energy_to_annuity_ratio()
    mc_analyze.calc_net_energy_to_co2_ratio()
    # mc_analyze.calc_net_exergy_to_annuity_ratio()
    # mc_analyze.calc_net_exergy_to_co2_ratio()
    # mc_analyze.calc_co2_to_net_exergy_ratio()
    # mc_analyze.calc_annuity_to_net_exergy_ratio()
    mc_analyze.calc_annuity_to_net_energy_ratio()
    mc_analyze.calc_co2_to_net_energy_ratio()

    # #  Evaluate means
    # mean_net_e_to_ann = mc_analyze.calc_net_energy_to_ann_mean()
    # mean_net_e_to_co2 = mc_analyze.calc_net_energy_to_co2_mean()
    #
    # print('Mean of net energy to annuity ratios:')
    # print(round(mean_net_e_to_ann, 2))
    #
    # print('Mean of net energy to CO2 ratios:')
    # print(round(mean_net_e_to_co2, 2))
    # print()
    #
    # #  Evaluate standard deviations
    # std_net_e_to_ann = mc_analyze.calc_net_energy_to_ann_std()
    # std_net_e_to_co2 = mc_analyze.calc_net_energy_to_co2_std()
    #
    # print('Standard deviation of net energy to annuity ratios:')
    # print(round(std_net_e_to_ann, 2))
    #
    # print('Standard deviation of net energy to CO2 ratios:')
    # print(round(std_net_e_to_co2, 2))
    # print()

    # #  Evaluate risk aversion
    # win_en_to_an = mc_analyze.calc_risk_averse_parameters(type='en_to_an')
    # win_en_to_co2 = mc_analyze.calc_risk_averse_parameters(type='en_to_co2')
    #
    # print('Risk aversion evaluation factor of net energy to annuity ratio:')
    # print(round(win_en_to_an, 2))
    #
    # print('Risk aversion evaluation factor of net energy to co2 ratio:')
    # print(round(win_en_to_co2, 2))
    # print()
    #
    # #  Evaluate risk aversion (exergy)
    # win_ex_to_an = mc_analyze.calc_risk_averse_parameters(type='ex_to_an')
    # win_ex_to_co2 = mc_analyze.calc_risk_averse_parameters(type='ex_to_co2')
    #
    # print('Risk aversion evaluation factor of net exergy to annuity ratio:')
    # print(round(win_ex_to_an, 2))
    #
    # print('Risk aversion evaluation factor of net exergy to co2 ratio:')
    # print(round(win_ex_to_co2, 2))
    # print()

    #  Evaluate risk aversion
    win_an_to_en = mc_analyze.calc_risk_averse_parameters(type='an_to_en')
    win_co2_to_en = mc_analyze.calc_risk_averse_parameters(type='co2_to_en')

    print('Risk aversion evaluation factor of annuity to net energy ratio:')
    print(round(win_an_to_en, 2))

    print('Risk aversion evaluation factor of co2 to net energy ratio:')
    print(round(win_co2_to_en, 2))
    print()

    # #  Evaluation
    # #  ####################################################################
    array_annuity = mc_analyze.get_annuity_results()
    array_co2 = mc_analyze.get_co2_results()

    plt.hist(array_annuity, bins='auto', label='annuity', alpha=0.7)
    plt.hist(array_co2, bins='auto', label='CO2', alpha=0.7)
    plt.ylabel('Nb. of occurence')
    plt.legend()
    plt.tight_layout()
    plt.show()
    plt.close()

    plt.hist(mc_analyze._array_ann_to_en, bins='auto')
    plt.xlabel('Effort in annualized cost per net energy unit in Euro/kWh')
    plt.ylabel('Nb. of occurence')
    plt.show()
    plt.close()

    plt.hist(mc_analyze._array_co2_to_en, bins='auto')
    plt.xlabel('Effort in emissions per net energy unit in kg/kWh')
    plt.ylabel('Nb. of occurence')
    plt.show()
    plt.close()
