#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
from __future__ import division

import os
import sys
import copy
import warnings
import pickle
import time
import random as rd
import numpy as np
import traceback

import matplotlib.pyplot as plt

import pycity_calc.economic.city_economic_calc as citecon
import pycity_calc.environments.germanmarket as gmarket
import pycity_calc.simulation.energy_balance.city_eb_calc as citeb
import pycity_calc.economic.annuity_calculation as annu
import pycity_calc.cities.scripts.city_generator.city_generator as citygen
import pycity_calc.cities.scripts.overall_gen_and_dimensioning as overall
import pycity_calc.toolbox.mc_helpers.city.city_sampling as citysample
import pycity_calc.toolbox.mc_helpers.building.build_unc_set_gen as buildsample
import pycity_calc.toolbox.mc_helpers.user.user_unc_sampling as usersample
import pycity_calc.toolbox.mc_helpers.esys.esyssampling as esyssample
import pycity_calc.toolbox.modifiers.mod_city_sh_dem as shmod
import pycity_calc.toolbox.modifiers.mod_city_el_dem as elmod
import pycity_calc.toolbox.modifiers.mod_city_dhw_dem as dhwmod
import pycity_calc.toolbox.networks.network_ops as netop
import pycity_calc.simulation.energy_balance.building_eb_calc as buildeb
import pycity_calc.toolbox.modifiers.mod_city_esys_size as modesys
import pycity_calc.energysystems.thermalEnergyStorage as tessys
import pycity_calc.visualization.city_visual as citvis
import pycity_calc.toolbox.mc_helpers.lhc_sampling.lhc_sample_run as lhcrun
import pycity_calc.cities.scripts.energy_sys_generator as esysgen


# Disable printing
#  From https://stackoverflow.com/questions/8391411/suppress-calls-to-print-python
def block_print():
    sys.stdout = open(os.devnull, 'w')


# Restore printing
def enable_print():
    sys.stdout = sys.__stdout__


def penalize_switching(city, max_switch):
    """
    Returns True, if number of switching commands per CHP is always below or
    equal to max_switches. False, if, at least, one CHP has more switching
    commands.
    Returns True, if no CHP exists.

    Parameters
    ----------
    city : object
        City object of pyCity_calc. Should have been processed with energy
        balance calculation to hold results on every CHP object
    max_switch

    Returns
    -------
    switching_okay: bool
        True, if number of switching commands per CHP is always below or
        equal to max_switches. False, if, at least, one CHP has more switching
        commands. Returns True, if no CHP exists.
    """

    assert max_switch > 0

    list_build_ids = city.get_list_build_entity_node_ids()

    switching_okay = True  # Initial value

    for n in list_build_ids:
        build = city.nodes[n]['entity']
        if build.hasBes:
            if build.bes.hasChp:
                nb_switches = build.bes.chp.calc_nb_on_off_switching()

                # assert nb_switches is not None

                if nb_switches is not None:
                    nb_per_day = build.bes.chp.calc_nb_on_off_switching() / 365
                    if nb_per_day > max_switch:
                        switching_okay = False
                        break
                else:
                    switching_okay = None
                    break

    return switching_okay


class McToleranceException(Exception):
    def __init__(self, message):
        """
        Constructor of McToleranceException

        Parameters
        ----------
        message : str
            Error message
        """

        super(McToleranceException, self).__init__(message)


class McRunner(object):
    """
    Monte-carlo runner class. Holds CityAnnuityCalc object (city_eco_calc),
    which holds:
    - annuity_obj (Annuity calculation object) and
    - energy_balance (Energy balance object)
    City ojbect is stored on energy balance object
    """

    def __init__(self, city_eco_calc, get_build_ids=True, search_lhn=True):
        """
        Constructor of Monte-Carlo runner class

        Parameters
        ----------
        city_eco_calc : object
            City economic calculation object of pyCity_calc. Has
            to hold city object, annuity object and energy balance object
        get_build_ids : bool, optional
            Defines, if all building node ids should be extracted and stored on
            _list_build_ids (default: True)
        search_lhn : bool, optional
            Defines, if LHN should be searched (default: True). Result is saved
            to
        """

        self._city_eco_calc = city_eco_calc
        self._list_build_ids = None  # List with building node ids in city

        self._dict_samples_const = None  # List of samples, which are constant
        #  for different energy system MC runs (e.g. city params, building
        #  energy demand samples)
        self._dict_samples_esys = None  # List of samples, which change for
        #  every energy system change (energy system paramters)

        self._has_lhn = None  # Defines, if energy system holds local heating
        #  network or not
        self._list_lhn_tuples = None  # List holding LHN edge tuples

        self._nb_failed_runs = None  # Counter for failed runs
        self._list_failed_runs = []

        self._tuple_ref_results = None
        #  Tuple with results of reference run (annuity, co2, space heating,
        #  electric demand, dhw demand)
        self._dict_fe_ref_run = None
        #  Final energy demand results dictionary of reference run

        #  Attributes to store sampling results of latin hypercube sampling
        self._dict_city_sample_lhc = None
        self._dict_build_samples_lhc = None
        self._dict_profiles_lhc = None

        self._count_none_chp_switch = 0

        if get_build_ids:
            #  Extract building node ids
            self._list_build_ids = self._city_eco_calc.energy_balance.city \
                .get_list_build_entity_node_ids()

        if search_lhn:
            self.search_lhn()

    def search_lhn(self, save_res=True):
        """
        Search for existing LHN system in city

        Parameters
        ----------
        save_res : bool, optional
            Defines, if search results (has_lhn) should be saved to mc_runner
            object (default: True)

        Returns
        -------
        has_lhn : bool
            Defines, if LHN system exists in city
        """

        city = self._city_eco_calc.energy_balance.city

        # has_lhn = netop.search_lhn(city=city)

        list_lhn_tuples = netop.search_lhn_all_edges(city=city)

        if len(list_lhn_tuples) > 0:
            has_lhn = True
        elif (len(list_lhn_tuples)) == 0:
            has_lhn = False

        if save_res:
            self._has_lhn = has_lhn
            self._list_lhn_tuples = list_lhn_tuples

    @staticmethod
    def perform_sampling_build_dem(nb_runs, building, dem_unc=True):
        """
        Perform sampling for building demand side

        Parameters
        ----------
        nb_runs : int
            Number of runs
        building : object
            Building object of pyCity_calc

        Returns
        -------
        dict_build_dem : dict (of arrays and dicts)
            Dictionary storing building demand samples
            dict_build_samples['occ'] = array_occupants
            dict_build_samples['el_dem'] = array_el_dem
            dict_build_samples['dhw_dem'] = array_dhw_dem
            dict_build_samples['on_off'] = array_sh_on_off
        dict_esys : dict (of arrays)
            Dictionary holding energy system parameters
        dem_unc : bool, optional
            Defines, if thermal, el. and dhw demand are assumed to be uncertain
            (default: True). If True, samples demands. If False, uses reference
            demands.
        """

        #  Initial dict
        dict_build_dem = {}

        #  Res. building type (sfh or mfh)
        if len(building.apartments) == 1:
            type = 'sfh'
        elif len(building.apartments) > 1:
            type = 'mfh'

        # Empty result arrays for apartment sampling
        array_occupants = np.zeros(nb_runs)
        array_el_dem = np.zeros(nb_runs)
        array_dhw_dem = np.zeros(nb_runs)

        if dem_unc:
            #  Sample for apartments
            #  ##############################################################
            for ap in building.apartments:

                #  Loop over nb. of samples
                for i in range(nb_runs):
                    #  Sample occupants
                    occ_p_app = usersample. \
                        calc_sampling_occ_per_app(nb_samples=1)[0]

                    #  Sample el. demand per apartment (depending on nb.
                    #  persons)
                    el_per_app = usersample. \
                        calc_sampling_el_demand_per_apartment(
                        nb_samples=1,
                        nb_persons=occ_p_app,
                        type=type)[0]

                    #  Sample dhw demand per apartment (depending on nb.
                    # persons)
                    dhw_vol_app = usersample. \
                        calc_sampling_dhw_per_apartment(nb_samples=1,
                                                        nb_persons=occ_p_app,
                                                        b_type=type)

                    #  Convert liters/app*day to kWh/app*year
                    dhw_per_app = \
                        usersample.recalc_dhw_vol_to_energy(vol=dhw_vol_app)

                    #  Sum up values on building level
                    array_occupants[i] += occ_p_app
                    array_el_dem[i] += el_per_app
                    array_dhw_dem[i] += dhw_per_app

        else:   # Demand is assumed to be certain
            timestep = building.environment.timer.timeDiscretization

            #  Demand is assumed to be certain
            for ap in building.apartments:

                #  Get ref. el. demand of apartment (in kWh)
                el_dem_app = sum(ap.power_el.loadcurve) * timestep / 3600000

                #  Get ref. dhw demand per apartment (in kWh)
                dhw_dem_app = sum(ap.demandDomesticHotWater.loadcurve) * \
                              timestep / 3600000

                #  Reference number of occupants within apartment
                nb_occ_per_app = ap.occupancy.number_occupants

                array_occupants = np.ones(nb_runs) * nb_occ_per_app
                array_el_dem = np.ones(nb_runs) * el_dem_app
                array_dhw_dem = np.ones(nb_runs) * dhw_dem_app


        # Sample building attributes
        #  ################################################################
        #  Calculate space heating demand sample
        sh_ref = building.get_annual_space_heat_demand()  # in kWh

        if dem_unc:
            array_sh_dem = buildsample.calc_sh_demand_samples(
                nb_samples=nb_runs,
                sh_ref=sh_ref)
        else:
            array_sh_dem = np.ones(nb_runs) * sh_ref

        # array_sh_on_off = buildsample. \
        #     calc_sh_summer_on_off_samples(nb_samples=nb_runs)

        #  Save results to dict
        #  ################################################################
        dict_build_dem['occ'] = array_occupants
        dict_build_dem['el_dem'] = array_el_dem
        dict_build_dem['dhw_dem'] = array_dhw_dem
        dict_build_dem['sh_dem'] = array_sh_dem
        # dict_build_samples['on_off'] = array_sh_on_off

        return dict_build_dem

    @staticmethod
    def perform_sampling_build_esys(nb_runs, building):
        """
        Perform sampling for building energy systems

        Parameters
        ----------
        nb_runs : int
            Number of runs
        building : object
            Building object of pyCity_calc

        Returns
        -------
        dict_esys : dict (of arrays)
            Dictionary holding energy system parameters
        """

        #  Res. building type (sfh or mfh)
        if len(building.apartments) == 1:
            type = 'sfh'
        elif len(building.apartments) > 1:
            type = 'mfh'

        # Sample energy system attributes
        #  ################################################################

        dict_esys = {}

        #  Check if building holds bes
        if building.hasBes:

            #  Check which devices do exist on bes
            if building.bes.hasBattery:
                dict_bat = {}

                dict_bat['self_discharge'] = \
                    esyssample.sample_bat_self_disch(nb_samples=nb_runs)

                dict_bat['eta_charge'] = \
                    esyssample.sample_bat_eta_charge(nb_samples=nb_runs)

                dict_bat['eta_discharge'] = \
                    esyssample.sample_bat_eta_discharge(nb_samples=nb_runs)

                dict_bat['bat_lifetime'] = \
                    esyssample.sample_lifetime(nb_samples=nb_runs)

                dict_bat['bat_maintain'] = \
                    esyssample.sample_maintain(nb_samples=nb_runs)

                #  Sample investment uncertainty (normalized to investment
                #  cost of 1)
                dict_bat['bat_inv'] = \
                    esyssample.sample_invest_unc(nb_samples=nb_runs,
                                                 ref_inv=1)

                dict_esys['bat'] = dict_bat

            if building.bes.hasBoiler:
                dict_boi = {}

                dict_boi['eta_boi'] = \
                    esyssample.sample_boi_eff(nb_samples=nb_runs)

                dict_boi['boi_lifetime'] = \
                    esyssample.sample_lifetime(nb_samples=nb_runs)

                dict_boi['boi_maintain'] = \
                    esyssample.sample_maintain(nb_samples=nb_runs)

                #  Sample investment uncertainty (normalized to investment
                #  cost of 1)
                dict_boi['boi_inv'] = \
                    esyssample.sample_invest_unc(nb_samples=nb_runs,
                                                 ref_inv=1)

                dict_esys['boi'] = dict_boi

            if building.bes.hasChp:
                dict_chp = {}

                dict_chp['omega_chp'] = \
                    esyssample.sample_chp_omega(nb_samples=nb_runs)

                dict_chp['chp_lifetime'] = \
                    esyssample.sample_lifetime(nb_samples=nb_runs)

                dict_chp['chp_maintain'] = \
                    esyssample.sample_maintain(nb_samples=nb_runs)

                #  Sample investment uncertainty (normalized to investment
                #  cost of 1)
                dict_chp['chp_inv'] = \
                    esyssample.sample_invest_unc(nb_samples=nb_runs,
                                                 ref_inv=1)

                dict_esys['chp'] = dict_chp

            if building.bes.hasHeatpump:
                dict_hp = {}

                dict_hp['quality_grade_aw'] = \
                    esyssample.sample_quality_grade_hp_aw(nb_samples=
                                                          nb_runs)

                dict_hp['quality_grade_ww'] = \
                    esyssample.sample_quality_grade_hp_bw(nb_samples=
                                                          nb_runs)

                dict_hp['t_sink'] = esyssample.sample_hp_t_sink(nb_samples=
                                                                nb_runs)

                dict_hp['hp_lifetime'] = \
                    esyssample.sample_lifetime(nb_samples=nb_runs)

                dict_hp['hp_maintain'] = \
                    esyssample.sample_maintain(nb_samples=nb_runs)

                #  Sample investment uncertainty (normalized to investment
                #  cost of 1)
                dict_hp['hp_inv'] = \
                    esyssample.sample_invest_unc(nb_samples=nb_runs,
                                                 ref_inv=1)

                dict_esys['hp'] = dict_hp

            if building.bes.hasElectricalHeater:
                dict_eh = {}

                dict_eh['eh_lifetime'] = \
                    esyssample.sample_lifetime(nb_samples=nb_runs)

                dict_eh['eh_maintain'] = \
                    esyssample.sample_maintain(nb_samples=nb_runs)

                #  Sample investment uncertainty (normalized to investment
                #  cost of 1)
                dict_eh['eh_inv'] = \
                    esyssample.sample_invest_unc(nb_samples=nb_runs,
                                                 ref_inv=1)

                dict_esys['eh'] = dict_eh

            if building.bes.hasPv:
                dict_pv = {}

                dict_pv['eta_pv'] = esyssample.sample_pv_eta(nb_samples=
                                                             nb_runs)
                dict_pv['beta'] = esyssample.sample_pv_beta(nb_samples=
                                                            nb_runs)
                dict_pv['gamma'] = esyssample.sample_pv_gamma(nb_samples=
                                                              nb_runs)

                dict_pv['pv_lifetime'] = \
                    esyssample.sample_lifetime(nb_samples=nb_runs)

                dict_pv['pv_maintain'] = \
                    esyssample.sample_maintain(nb_samples=nb_runs)

                #  Sample investment uncertainty (normalized to investment
                #  cost of 1)
                dict_pv['pv_inv'] = \
                    esyssample.sample_invest_unc(nb_samples=nb_runs,
                                                 ref_inv=1)

                dict_esys['PV'] = dict_pv

            if building.bes.hasTes:
                dict_tes = {}

                dict_tes['k_loss'] = esyssample.sample_tes_k_loss(nb_samples=
                                                                  nb_runs)

                dict_tes['tes_lifetime'] = \
                    esyssample.sample_lifetime(nb_samples=nb_runs)

                dict_tes['tes_maintain'] = \
                    esyssample.sample_maintain(nb_samples=nb_runs)

                #  Sample investment uncertainty (normalized to investment
                #  cost of 1)
                dict_tes['tes_inv'] = \
                    esyssample.sample_invest_unc(nb_samples=nb_runs,
                                                 ref_inv=1)

                dict_esys['tes'] = dict_tes

        return dict_esys

    def perform_esys_resampling(self, nb_runs, save_samples=True):
        """
        Re-sample all energy system parameters on city object

        Parameters
        ----------
        nb_runs : int
            Number of runs
        save_samples : bool, optional
            Defines, if sampling results should be saved on MC results object
            (default: True)

        Returns
        -------
        dict_samples_esys : dict (of dicts)
            Dictionary holding dictionaries with energy system sampling
            data for MC run
            dict_samples_esys['<building_id>'] = dict_esys
            (of building with id <building_id>)
        """

        dict_samples_esys = {}

        for n in self._list_build_ids:
            build = self._city_eco_calc.energy_balance.city.nodes[n]['entity']

            dict_esys = self.perform_sampling_build_esys(nb_runs=nb_runs,
                                                         building=build)

            dict_samples_esys[str(n)] = dict_esys

        if save_samples:
            #  Save sampling dict to MC runner object
            self._dict_samples_esys = dict_samples_esys

        return dict_samples_esys

    def perform_sampling_city(self, nb_runs):
        """
        Perform sampling for city district parameters:
        - interest
        - price_ch_cap
        - price_ch_dem_gas
        - price_ch_dem_el
        - price_ch_op
        - price_ch_eeg_chp
        - price_ch_eeg_pv
        - price_ch_eex
        - price_ch_grid_use
        - summer heating on/off

        Parameters
        ----------
        nb_runs : int
            Number of runs

        Returns
        -------
        dict_city_samples : dict
            Dictionary holding city samples
        """

        dict_city_samples = {}

        array_interest = citysample.sample_interest(nb_samples=nb_runs)
        array_ch_cap = citysample.sample_price_ch_cap(nb_samples=nb_runs)
        array_ch_dem_gas = citysample.sample_price_ch_dem_gas(nb_samples=
                                                              nb_runs)
        array_ch_dem_el = citysample.sample_price_ch_dem_el(nb_samples=
                                                            nb_runs)
        array_ch_op = citysample.sample_price_ch_op(nb_samples=nb_runs)
        array_ch_eeg_chp = citysample.sample_price_ch_eeg_chp(nb_samples=
                                                              nb_runs)
        array_ch_eeg_pv = citysample.sample_price_ch_eeg_pv(nb_samples=
                                                            nb_runs)
        array_ch_eex = citysample.sample_price_ch_eex(nb_samples=nb_runs)
        array_ch_grid_use = citysample.sample_price_ch_grid_use(nb_samples=
                                                                nb_runs)
        array_grid_av_fee = citysample.sample_grid_av_fee(nb_samples=nb_runs)
        array_temp_ground = citysample.sample_temp_ground(nb_samples=nb_runs)

        array_summer_heat_on = citysample. \
            sample_quota_summer_heat_on(nb_samples=nb_runs)

        list_s_heat_on_id_arrays = citysample. \
            sample_list_sum_heat_on_arrays(nb_samples=nb_runs,
                                           array_ratio_on=array_summer_heat_on,
                                           list_b_ids=self._list_build_ids)

        #  Only used, if LHN exists, but required to prevent ref.
        #  before assignment error #289
        #  If LHN exists, sample for LHN with ref. investment cost of 1
        array_lhn_inv = esyssample.sample_invest_unc(nb_samples=nb_runs,
                                                     ref_inv=1)
        #  If LHN exists, sample losses for LHN (ref loss 1)
        array_lhn_loss = esyssample.sample_lhn_loss_unc(nb_samples=nb_runs,
                                                        ref_loss=1)

        dict_city_samples['interest'] = array_interest
        dict_city_samples['ch_cap'] = array_ch_cap
        dict_city_samples['ch_dem_gas'] = array_ch_dem_gas
        dict_city_samples['ch_dem_el'] = array_ch_dem_el
        dict_city_samples['ch_op'] = array_ch_op
        dict_city_samples['ch_eeg_chp'] = array_ch_eeg_chp
        dict_city_samples['ch_eeg_pv'] = array_ch_eeg_pv
        dict_city_samples['ch_eex'] = array_ch_eex
        dict_city_samples['ch_grid_use'] = array_ch_grid_use
        dict_city_samples['grid_av_fee'] = array_grid_av_fee
        dict_city_samples['temp_ground'] = array_temp_ground
        # dict_city_samples['summer_on'] = array_summer_heat_on
        dict_city_samples['list_sum_on'] = list_s_heat_on_id_arrays
        dict_city_samples['lhn_inv'] = array_lhn_inv
        dict_city_samples['lhn_loss'] = array_lhn_loss

        return dict_city_samples

    def perform_sampling(self, nb_runs, save_samples=True, dem_unc=True):
        """
        Perform parameter sampling for Monte-Carlo analysis

        Parameters
        ----------
        nb_runs : int
            Number of runs
        save_samples : bool, optional
            Defines, if sampling results should be saved on MC results object
            (default: True)
        dem_unc : bool, optional
            Defines, if thermal, el. and dhw demand are assumed to be uncertain
            (default: True). If True, samples demands. If False, uses reference
            demands.

        Returns
        -------
        tuple_res : tuple (of dicts)
            2d tuple (dict_samples_const, dict_samples_esys)
            dict_samples_const : dict (of dicts)
                Dictionary holding dictionaries with constant
                sample data for MC run
                dict_samples_const['city'] = dict_city_samples
                dict_samples_const['<building_id>'] = dict_build_dem
                (of building with id <building_id>)
            dict_samples_esys : dict (of dicts)
                Dictionary holding dictionaries with energy system sampling
                data for MC run
                dict_samples_esys['<building_id>'] = dict_esys
                (of building with id <building_id>)
        """

        #  Initial sample dict. Holds further sample dicts for
        #  'city' and each building node id
        dict_samples_const = {}
        dict_samples_esys = {}

        #  Perform city sampling
        dict_city_samples = self.perform_sampling_city(nb_runs=nb_runs)

        dict_samples_const['city'] = dict_city_samples

        #  Perform building sampling
        #  Loop over node ids and add samples to result dict with building
        #  id as key
        for n in self._list_build_ids:
            build = self._city_eco_calc.energy_balance.city.nodes[n]['entity']

            dict_build_dem = self.perform_sampling_build_dem(nb_runs=nb_runs,
                                                             building=build,
                                                             dem_unc=dem_unc)
            dict_esys = self.perform_sampling_build_esys(nb_runs=nb_runs,
                                                         building=build)

            dict_samples_const[str(n)] = dict_build_dem
            dict_samples_esys[str(n)] = dict_esys

        if save_samples:
            #  Save sampling dict to MC runner object
            self._dict_samples_const = dict_samples_const
            self._dict_samples_esys = dict_samples_esys

        return (dict_samples_const, dict_samples_esys)

    def perform_lhc_sampling(self, nb_runs,
                             load_sh_mc_res=False,
                             path_mc_res_folder=None,
                             use_profile_pool=False,
                             gen_use_prof_method=0,
                             path_profile_dict=None,
                             save_res=True,
                             nb_profiles=None,
                             load_city_n_build_samples=False,
                             path_city_sample_dict=None,
                             path_build_sample_dict=None,
                             dem_unc=True
                             ):
        """
        Perform latin hypercube sampling

        Parameters
        ----------
        nb_runs : int
            Number of runs
        load_sh_mc_res : bool, optional
            If True, tries to load space heating monte-carlo uncertainty run
            results for each building and uses result to sample space heating
            values. If False, uses default distribution to sample space heating
            values (default: False)
        path_mc_res_folder : str, optional
            Path to folder, where sh mc run results are stored (default: None).
            Only necessary if load_sh_mc_res is True
        use_profile_pool : bool, optional
            Defines, if user/el. load/dhw profile pool should be generated
            (default: False). If True, generates profile pool.
        save_res : bool, optional
            Save results back to mc_runner object (default: True)
        gen_use_prof_method : int, optional
            Defines method for el. profile pool usage (default: 0).
            Options:
            - 0: Generate new el. profile pool
            - 1: Load profile pool from path_profile_dict
        path_profile_dict : str, optional
            Path to dict with el. profile pool (default: None).
        nb_profiles : int, optional
            Desired number of profile samples per building, when profile pool
            is generated (default: None). If None, uses nb_runs.
        load_city_n_build_samples : bool, optional
            Defines, if existing city and building sample dicts should be
            loaded (default: False). If False, generates new sample dicts.
        path_city_sample_dict : str, optional
            Defines path to city sample dict (default: None). Only relevant,
            if load_city_n_build_samples is True
        path_build_sample_dict : str, optional
            Defines path to building sample dict (default: None).
            Only relevant, if load_city_n_build_samples is True
        dem_unc : bool, optional
            Defines, if thermal, el. and dhw demand are assumed to be uncertain
            (default: True). If True, samples demands. If False, uses reference
            demands.

        Returns
        -------
        tup_res : tuple (of dicts)
            Tuple holding 3 dicts
            (dict_city_sample_lhc, dict_build_samples_lhc, dict_profiles_lhc)
            dict_city_sample_lhc : dict
                Dict holding city parameter names as keys and numpy arrays with
                samples as dict values
            dict_build_samples_lhc : dict
                Dict. holding building ids as keys and dict of samples as
                values.
                These dicts hold paramter names as keys and numpy arrays with
                samples as dict values
            dict_profiles_lhc : dict
                Dict. holding building ids as keys and dict with numpy arrays
                with different el. and dhw profiles for each building as value
                fict_profiles_build['el_profiles'] = el_profiles
                dict_profiles_build['dhw_profiles'] = dhw_profiles
                When use_profile_pool is False, dict_profiles is None
        """
        if use_profile_pool and gen_use_prof_method == 1:
            if path_profile_dict is None:
                msg = 'path_profile_dict cannot be None, if ' \
                      'gen_use_prof_method==1 (load el. profile pool)!'
                raise AssertionError(msg)

        if nb_profiles is None:
            nb_profiles = int(nb_runs)

        (dict_city_sample_lhc, dict_build_samples_lhc, dict_profiles_lhc) \
            = lhcrun. \
            run_overall_lhc_sampling(
            city=self._city_eco_calc.energy_balance.city,
            nb_samples=nb_runs,
            load_sh_mc_res=load_sh_mc_res,
            path_mc_res_folder=path_mc_res_folder,
            use_profile_pool=use_profile_pool,
            gen_use_prof_method=gen_use_prof_method,
            path_profile_dict=path_profile_dict,
            nb_profiles=nb_profiles,
            load_city_n_build_samples=load_city_n_build_samples,
            path_city_sample_dict=path_city_sample_dict,
            path_build_sample_dict=path_build_sample_dict,
            dem_unc=dem_unc
        )

        if save_res:
            self._dict_city_sample_lhc = dict_city_sample_lhc
            self._dict_build_samples_lhc = dict_build_samples_lhc
            self._dict_profiles_lhc = dict_profiles_lhc

        return (dict_city_sample_lhc, dict_build_samples_lhc,
                dict_profiles_lhc)

    def perform_mc_runs(self, nb_runs, sampling_method, failure_tolerance=0.05,
                        heating_off=True, eeg_pv_limit=False,
                        random_profile=False, use_kwkg_lhn_sub=False,
                        calc_th_el_cov=False, el_mix_for_chp=True,
                        el_mix_for_pv=True):
        """
        Perform mc runs.
        - Extract sample values
        - Add sample values to city, environment, buildings and energy systems
        - Calls energy balance and economic calculation
        - Saves results to result arrays

        Parameters
        ----------
        nb_runs : int
            Number of runs
        sampling_method : str
            Defines method used for sampling.
            Options:
            - 'lhc': latin hypercube sampling
            - 'random': randomized sampling
        failure_tolerance : float, optional
            Allowed EnergyBalanceException failure tolerance (default: 0.05).
            E.g. 0.05 means, that 5% of runs are allowed to fail with
            EnergyBalanceException.
        heating_off : bool, optional
            Defines, if sampling to deactivate heating during summer should
            be used (default: True)
        eeg_pv_limit : bool, optional
            Defines, if EEG PV feed-in limitation of 70 % of peak load is
            active (default: False). If limitation is active, maximal 70 %
            of PV peak load are fed into the grid.
            However, self-consumption is used, first.
        random_profile : bool, optional
            Defines, if random samples should be kused from profile pool
            (default: False). Only relevant, if profile pool has been given,
            sampling_method == 'lhc' and nb. of profiles is equal to nb.
            of samples
        use_kwkg_lhn_sub : bool, optional
            Defines, if KWKG LHN subsidies are used (default: False).
            If True, can get 100 Euro/m as subdidy, if share of CHP LHN fed-in
            is equal to or higher than 60 %
        calc_th_el_cov : bool, optional
            Defines, if thermal and electric coverage of different types of
            devices should be calculated (default: False)
        el_mix_for_chp : bool, optional
            Defines, if el. mix should be used for CHP fed-in electricity
            (default: True). If False, uses specific fed-in CHP factor,
            defined in co2emissions object (co2_factor_el_feed_in)
        el_mix_for_pv : bool, optional
            Defines, if el. mix should be used for PV fed-in electricity
            (default: True). If False, uses specific fed-in PV factor,
            defined in co2emissions object (co2_factor_pv_fed_in)

        Returns
        -------
        tuple_res : tuple (of dicts)
            Tuple holding two dictionaries (dict_mc_res, dict_mc_setup)
            dict_mc_res : dict
                Dictionary with result arrays for each run
                dict_mc_res['annuity'] = array_annuity
                dict_mc_res['co2'] = array_co2
                dict_mc_res['sh_dem'] = array_net_sh
                dict_mc_res['el_dem'] = array_net_el
                dict_mc_res['dhw_dem'] = array_net_dhw
                dict_mc_res['gas_boiler'] = array_gas_boiler
                dict_mc_res['gas_chp'] = array_gas_chp
                dict_mc_res['grid_imp_dem'] = array_grid_imp_dem
                dict_mc_res['grid_imp_hp'] = array_grid_imp_hp
                dict_mc_res['grid_imp_eh'] = array_grid_imp_eh
                dict_mc_res['lhn_pump'] = array_lhn_pump
                dict_mc_res['grid_exp_chp'] = array_grid_exp_chp
                dict_mc_res['grid_exp_pv'] = array_grid_exp_pv
            dict_mc_setup : dict
                Dictionary holding mc run settings
                dict_mc_setup['nb_runs'] = nb_runs
                dict_mc_setup['failure_tolerance'] = failure_tolerance
                dict_mc_setup['heating_off'] = heating_off
                dict_mc_setup['idx_failed_runs'] = self._list_failed_runs
            dict_mc_cov : dict
                Dictionary holding thermal/electrical coverage factors
                dict_mc_cov['th_cov_boi'] = array_th_cov_boi
                dict_mc_cov['th_cov_chp'] = array_th_cov_chp
                dict_mc_cov['th_cov_hp_aw'] = array_th_cov_hp_aw
                dict_mc_cov['th_cov_hp_ww'] = array_th_cov_hp_ww
                dict_mc_cov['th_cov_eh'] = array_th_cov_eh
                dict_mc_cov['el_cov_chp'] = array_el_cov_chp
                dict_mc_cov['el_cov_pv'] = array_el_cov_pv
        """

        if sampling_method not in ['lhc', 'random']:
            msg = 'Sampling method ' + str(sampling_method) + ' is unknown!'
            raise AssertionError(msg)

        if nb_runs <= 0:
            msg = 'nb_runs has to be larger than zero!'
            raise AssertionError(msg)

        #  Initialize result dict an arrays
        #  #################################################################
        dict_mc_res = {}

        dict_mc_setup = {}

        #  Add chosen settings to dict_mc_setup
        dict_mc_setup['nb_runs'] = nb_runs
        dict_mc_setup['failure_tolerance'] = failure_tolerance
        dict_mc_setup['heating_off'] = heating_off

        #  Initial zero result arrays
        array_annuity = np.zeros(nb_runs)
        array_co2 = np.zeros(nb_runs)

        #  # Uncommented, as already existent on sampling dicts
        array_net_sh = np.zeros(nb_runs)
        array_net_el = np.zeros(nb_runs)
        array_net_dhw = np.zeros(nb_runs)

        array_gas_boiler = np.zeros(nb_runs)
        array_gas_chp = np.zeros(nb_runs)
        array_grid_imp_dem = np.zeros(nb_runs)
        array_grid_imp_hp = np.zeros(nb_runs)
        array_grid_imp_eh = np.zeros(nb_runs)
        array_lhn_pump = np.zeros(nb_runs)
        array_grid_exp_chp = np.zeros(nb_runs)
        array_grid_exp_pv = np.zeros(nb_runs)

        #  Set failure counter to zero
        self._nb_failed_runs = 0
        self._list_failed_runs = []

        if calc_th_el_cov:
            #  Calculate thermal and electric coverage by device

            dict_mc_cov = {}

            array_th_cov_boi = np.zeros(nb_runs)
            array_th_cov_chp = np.zeros(nb_runs)
            array_th_cov_hp_aw = np.zeros(nb_runs)
            array_th_cov_hp_ww = np.zeros(nb_runs)
            array_th_cov_eh = np.zeros(nb_runs)

            array_el_cov_chp = np.zeros(nb_runs)
            array_el_cov_pv = np.zeros(nb_runs)
            array_el_cov_grid = np.zeros(nb_runs)
        else:
            dict_mc_cov = None

        #  Run energy balance and economic analysis
        #  #################################################################
        for i in range(nb_runs):
            #  Copy city economic calculator, to prevent modification of
            #  original objects
            c_eco_copy = copy.deepcopy(self._city_eco_calc)

            #  For simplification, add pointers to submodules of c_eco_copy
            city = c_eco_copy.energy_balance.city
            energy_balance = c_eco_copy.energy_balance
            annuity_obj = c_eco_copy.annuity_obj
            #  Add sampling results to environment, city and buildings
            #  ###############################################################

            # dict_build_samples : dict (of arrays and dicts)
            # Dictionary storing building samples
            # dict_build_samples['occ'] = array_occupants
            # dict_build_samples['el_dem'] = array_el_dem
            # dict_build_samples['dhw_dem'] = array_dhw_dem
            # dict_build_samples['sh_dem'] = array_sh_dem
            # dict_build_samples['on_off'] = array_sh_on_off

            #  Add building sample input data
            #  ###############################################################
            if sampling_method == 'random':
                for n in self._list_build_ids:
                    curr_build = city.nodes[n]['entity']

                    dict_build_dem = self._dict_samples_const[str(n)]
                    dict_esys = self._dict_samples_esys[str(n)]

                    #  Add function to rescale sh, el, dhw demands
                    #  #######################################################

                    sh_dem = dict_build_dem['sh_dem'][i]
                    shmod.rescale_sh_dem_build(building=curr_build,
                                               sh_dem=sh_dem)

                    el_dem = dict_build_dem['el_dem'][i]
                    elmod.rescale_el_dem_build(building=curr_build,
                                               el_dem=el_dem)

                    dhw_dem = dict_build_dem['dhw_dem'][i]
                    dhwmod.rescale_dhw_build(building=curr_build,
                                             dhw_dem=dhw_dem)

                    #  Add energy system data
                    #  #######################################################

                    if curr_build.hasBes:

                        #  Check which devices do exist on bes
                        if curr_build.bes.hasBattery:
                            dict_bat = dict_esys['bat']

                            bat = curr_build.bes.battery

                            #  Add new parameters to battery
                            bat.selfDischarge = dict_bat['self_discharge'][i]
                            bat.etaCharge = dict_bat['eta_charge'][i]
                            bat.etaDischarge = dict_bat['eta_discharge'][i]

                        # dict_bat['bat_lifetime'] = \
                        #         esyssample.sample_lifetime(nb_samples=nb_runs)
                        #
                        #     dict_bat['bat_maintain'] = \
                        #         esyssample.sample_maintain(nb_samples=nb_runs)

                        if curr_build.bes.hasBoiler:
                            dict_boi = dict_esys['boi']

                            boi = curr_build.bes.boiler

                            #  Add new boiler parameters
                            boi.eta = dict_boi['eta_boi'][i]

                            # dict_boi['boi_lifetime'] = \
                            #     esyssample.sample_lifetime(nb_samples=nb_runs)
                            #
                            # dict_boi['boi_maintain'] = \
                            #     esyssample.sample_maintain(nb_samples=nb_runs)

                        if curr_build.bes.hasChp:
                            dict_chp = dict_esys['chp']

                            chp = curr_build.bes.chp

                            #  Get omega sample
                            omega = dict_chp['omega_chp'][i]
                            #  Get current nominal thermal power
                            curr_th_eta = chp.qNominal

                            #  Recalculate corresponding thermal and electrical
                            #  nominal power values with new omega
                            (th_power, el_power) = \
                                chp.run_precalculation(q_nominal=curr_th_eta,
                                                       p_nominal=None,
                                                       eta_total=omega,
                                                       thermal_operation_mode=True)

                            #  Overwrite existing values
                            chp.qNominal = th_power
                            chp.pNominal = el_power

                            # dict_chp['chp_lifetime'] = \
                            #     esyssample.sample_lifetime(nb_samples=nb_runs)
                            #
                            # dict_chp['chp_maintain'] = \
                            #     esyssample.sample_maintain(nb_samples=nb_runs)

                        if curr_build.bes.hasHeatpump:
                            dict_hp = dict_esys['hp']

                            hp = curr_build.bes.heatpump

                            hp.quality_grade_aw = dict_hp['quality_grade_aw'][
                                i]
                            hp.quality_grade_ww = dict_hp['quality_grade_ww'][
                                i]
                            hp.t_sink = dict_hp['t_sink'][i]

                            # dict_hp['hp_lifetime'] = \
                            #     esyssample.sample_lifetime(nb_samples=nb_runs)
                            #
                            # dict_hp['hp_maintain'] = \
                            #     esyssample.sample_maintain(nb_samples=nb_runs)

                        if curr_build.bes.hasElectricalHeater:
                            dict_eh = dict_esys['eh']

                            eh = curr_build.bes.electricalHeater

                            # dict_eh['eh_lifetime'] = \
                            #     esyssample.sample_lifetime(nb_samples=nb_runs)
                            #
                            # dict_eh['eh_maintain'] = \
                            #     esyssample.sample_maintain(nb_samples=nb_runs)

                        if curr_build.bes.hasPv:
                            dict_pv = dict_esys['PV']

                            pv = curr_build.bes.pv

                            pv.eta = dict_pv['eta_pv'][i]

                            pv.beta = dict_pv['beta'][i]

                            pv.gamma = dict_pv['gamma'][i]

                            # dict_pv['hp_lifetime'] = \
                            #     esyssample.sample_lifetime(nb_samples=nb_runs)
                            #
                            # dict_pv['hp_maintain'] = \
                            #     esyssample.sample_maintain(nb_samples=nb_runs)

                        if curr_build.bes.hasTes:
                            dict_tes = dict_esys['tes']

                            tes = curr_build.bes.tes

                            tes.k_loss = dict_tes['k_loss'][i]

                            # dict_tes['hp_lifetime'] = \
                            #     esyssample.sample_lifetime(nb_samples=nb_runs)
                            #
                            # dict_tes['hp_maintain'] = \
                            #     esyssample.sample_maintain(nb_samples=nb_runs)

            elif sampling_method == 'lhc':
                #  #########################################################
                for n in self._list_build_ids:
                    curr_build = city.nodes[n]['entity']

                    dict_build_lhc = self._dict_build_samples_lhc[n]

                    #  If profile pool is given, overwrite existing profiles
                    if self._dict_profiles_lhc is not None:
                        el_prof_pool = \
                            self._dict_profiles_lhc[n]['el_profiles']
                        dhw_prof_pool = \
                            self._dict_profiles_lhc[n]['dhw_profiles']

                        #  Get number of apartments in current building
                        nb_app = len(curr_build.apartments)

                        #  Add new el. profile from profile pool
                        if random_profile or len(el_prof_pool) < nb_runs:

                            msg = 'Number of el. profiles in el_prof_pool ' \
                                  'is smaller than number of runs. Thus, ' \
                                  'profiles are randomly chosen instead ' \
                                  'of looping over them.'
                            warnings.warn(msg)

                            idx = rd.randint(0, len(el_prof_pool) - 1)
                            el_profile = el_prof_pool[idx]
                            for app in city.nodes[n]['entity'].apartments:
                                app.power_el.loadcurve = el_profile / nb_app
                        else:
                            for app in city.nodes[n]['entity'].apartments:
                                app.power_el.loadcurve = el_prof_pool[i] / \
                                                         nb_app

                        if self._dict_profiles_lhc is not None:
                            #  Add new dhw. profile from profile pool
                            if random_profile or len(dhw_prof_pool) < nb_runs:
                                #  Add new dhw. profile from profile pool, if
                                #  available
                                idx = rd.randint(0, len(dhw_prof_pool) - 1)
                                dhw_profile = dhw_prof_pool[idx]
                                for app in city.nodes[n]['entity'].apartments:
                                    app.power_el.loadcurve = \
                                        dhw_profile / nb_app
                            else:
                                for app in city.nodes[n]['entity'].apartments:
                                    app.demandDomesticHotWater.loadcurve = \
                                        dhw_prof_pool[i] / nb_app

                    #  Add function to rescale sh, el, dhw demands
                    #  #######################################################

                    sh_dem = dict_build_lhc['sh_dem'][i]
                    shmod.rescale_sh_dem_build(building=curr_build,
                                               sh_dem=sh_dem)

                    el_dem = dict_build_lhc['el_dem'][i]
                    elmod.rescale_el_dem_build(building=curr_build,
                                               el_dem=el_dem)

                    dhw_dem = dict_build_lhc['dhw_dem'][i]
                    dhwmod.rescale_dhw_build(building=curr_build,
                                             dhw_dem=dhw_dem)

                    #  Uncommented, due to issue #465
                    #  ####################################################
                    # el_dem = 0
                    # for a in range(len(dict_build_lhc['app_el_dem'])):
                    #     #  Sum up el. demand
                    #     el_dem += dict_build_lhc['app_el_dem'][a][i]
                    #
                    # nb_app = len(city.nodes[n]['entity'].apartments)
                    #
                    # if self._dict_profiles_lhc is not None:
                    #     #  Add new el. profile from profile pool, if available
                    #     if random_profile or len(el_prof_pool) < nb_runs:
                    #
                    #         msg = 'Number of el. profiles in el_prof_pool ' \
                    #               'is smaller than number of runs. Thus, ' \
                    #               'profiles are randomly chosen instead ' \
                    #               'of looping over them.'
                    #         warnings.warn(msg)
                    #
                    #         idx = rd.randint(0, len(el_prof_pool) - 1)
                    #         el_profile = el_prof_pool[idx]
                    #         for app in city.nodes[n]['entity'].apartments:
                    #             app.power_el.loadcurve = el_profile / nb_app
                    #     else:
                    #         for app in city.nodes[n]['entity'].apartments:
                    #             app.power_el.loadcurve = el_prof_pool[i] / \
                    #                                      nb_app
                    #
                    # #  Rescale profile to el_dem sample
                    # elmod.rescale_el_dem_build(building=curr_build,
                    #                            el_dem=el_dem)
                    # dhw_dem = 0
                    # for a in range(len(dict_build_lhc['app_dhw_dem'])):
                    #     dhw_dem += dict_build_lhc['app_dhw_dem'][a][i]
                    #
                    # if self._dict_profiles_lhc is not None:
                    #     #  Add new dhw. profile from profile pool, if available
                    #     if random_profile or len(dhw_prof_pool) < nb_runs:
                    #         #  Add new dhw. profile from profile pool, if
                    #         #  available
                    #         idx = rd.randint(0, len(dhw_prof_pool) - 1)
                    #         dhw_profile = dhw_prof_pool[idx]
                    #         for app in city.nodes[n]['entity'].apartments:
                    #             app.power_el.loadcurve = dhw_profile / nb_app
                    #     else:
                    #         for app in city.nodes[n]['entity'].apartments:
                    #             app.demandDomesticHotWater.loadcurve = \
                    #                 dhw_prof_pool[i] / nb_app
                    #
                    # #  Rescale demand to dhw_dem sample
                    # dhwmod.rescale_dhw_build(building=curr_build,
                    #                          dhw_dem=dhw_dem)

                    #  Add energy system data
                    #  #######################################################

                    if curr_build.hasBes:

                        #  Check which devices do exist on bes
                        if curr_build.bes.hasBattery:
                            bat = curr_build.bes.battery

                            #  Add new parameters to battery
                            bat.selfDischarge = \
                                dict_build_lhc['self_discharge'][i]
                            bat.etaCharge = \
                                dict_build_lhc['eta_charge'][i]
                            bat.etaDischarge = \
                                dict_build_lhc['eta_discharge'][i]

                        # dict_bat['bat_lifetime'] = \
                        #         esyssample.sample_lifetime(nb_samples=nb_runs)
                        #
                        #     dict_bat['bat_maintain'] = \
                        #         esyssample.sample_maintain(nb_samples=nb_runs)

                        if curr_build.bes.hasBoiler:
                            boi = curr_build.bes.boiler

                            #  Add new boiler parameters
                            boi.eta = dict_build_lhc['eta_boi'][i]

                            # dict_boi['boi_lifetime'] = \
                            #     esyssample.sample_lifetime(nb_samples=nb_runs)
                            #
                            # dict_boi['boi_maintain'] = \
                            #     esyssample.sample_maintain(nb_samples=nb_runs)

                        if curr_build.bes.hasChp:
                            chp = curr_build.bes.chp

                            #  Get omega sample
                            omega = dict_build_lhc['omega_chp'][i]
                            #  Get current nominal thermal power
                            curr_th_eta = chp.qNominal

                            #  Recalculate corresponding thermal and electrical
                            #  nominal power values with new omega
                            (th_power, el_power) = \
                                chp.run_precalculation(q_nominal=curr_th_eta,
                                                       p_nominal=None,
                                                       eta_total=omega,
                                                       thermal_operation_mode=True)

                            #  Overwrite existing values
                            chp.qNominal = th_power
                            chp.pNominal = el_power

                            # dict_chp['chp_lifetime'] = \
                            #     esyssample.sample_lifetime(nb_samples=nb_runs)
                            #
                            # dict_chp['chp_maintain'] = \
                            #     esyssample.sample_maintain(nb_samples=nb_runs)

                        if curr_build.bes.hasHeatpump:
                            hp = curr_build.bes.heatpump

                            hp.quality_grade_aw = \
                                dict_build_lhc['qual_grade_aw'][i]
                            hp.quality_grade_ww = \
                                dict_build_lhc['qual_grade_ww'][i]
                            hp.t_sink = dict_build_lhc['t_sink'][i]

                            # dict_hp['hp_lifetime'] = \
                            #     esyssample.sample_lifetime(nb_samples=nb_runs)
                            #
                            # dict_hp['hp_maintain'] = \
                            #     esyssample.sample_maintain(nb_samples=nb_runs)

                        if curr_build.bes.hasElectricalHeater:
                            eh = curr_build.bes.electricalHeater

                            # dict_eh['eh_lifetime'] = \
                            #     esyssample.sample_lifetime(nb_samples=nb_runs)
                            #
                            # dict_eh['eh_maintain'] = \
                            #     esyssample.sample_maintain(nb_samples=nb_runs)

                        if curr_build.bes.hasPv:
                            pv = curr_build.bes.pv

                            pv.eta = dict_build_lhc['eta_pv'][i]

                            pv.beta = dict_build_lhc['beta'][i]

                            pv.gamma = dict_build_lhc['gamma'][i]

                            # dict_pv['hp_lifetime'] = \
                            #     esyssample.sample_lifetime(nb_samples=nb_runs)
                            #
                            # dict_pv['hp_maintain'] = \
                            #     esyssample.sample_maintain(nb_samples=nb_runs)

                        if curr_build.bes.hasTes:
                            tes = curr_build.bes.tes

                            tes.k_loss = dict_build_lhc['k_loss'][i]

                            # dict_tes['hp_lifetime'] = \
                            #     esyssample.sample_lifetime(nb_samples=nb_runs)
                            #
                            # dict_tes['hp_maintain'] = \
                            #     esyssample.sample_maintain(nb_samples=nb_runs)

            # Extract city sampling data
            #  #############################################################
            if sampling_method == 'random':

                dict_city_samples = self._dict_samples_const['city']

                # dict_city_samples['interest'] = array_interest
                # dict_city_samples['ch_cap'] = array_ch_cap
                # dict_city_samples['ch_dem_gas'] = array_ch_dem_gas
                # dict_city_samples['ch_dem_el'] = array_ch_dem_el
                # dict_city_samples['ch_op'] = array_ch_op
                # dict_city_samples['ch_eeg_chp'] = array_ch_eeg_chp
                # dict_city_samples['ch_eeg_pv'] = array_ch_eeg_pv
                # dict_city_samples['ch_eex'] = array_ch_eex
                # dict_city_samples['ch_grid_use'] = array_ch_grid_use
                # dict_city_samples['grid_av_fee'] = array_grid_av_fee
                # dict_city_samples['temp_ground'] = array_temp_ground
                # dict_city_samples['list_sum_on'] = list_s_heat_on_id_arrays
                # dict_city_samples['lhn_inv'] = array_lhn_inv
                # dict_city_samples['lhn_loss'] = array_lhn_loss

                if heating_off:
                    #  Use sampling to switch demand of some heating systems off
                    #  during summer period

                    #  Get array with building ids with summer heating mode on
                    array_heat_on = dict_city_samples['list_sum_on'][i]

                    #  Calculate list of building ids, where heating is off during
                    #  summer
                    list_heat_off = list(set(self._list_build_ids) -
                                         set(array_heat_on))

                    for n in list_heat_off:
                        curr_build = city.nodes[n]['entity']

                        #  Modify space heating (switch off during summer)
                        shmod.sh_curve_summer_off_build(building=curr_build)

                # Save inputs to city, market and environment
                city.environment.temp_ground = \
                dict_city_samples['temp_ground'][i]
                city.environment.prices.grid_av_fee = \
                    dict_city_samples['grid_av_fee'][i]

                #  Save inputs to annuity_obj
                annuity_obj.interest = dict_city_samples['interest'][i]
                annuity_obj.price_ch_cap = dict_city_samples['ch_cap'][i]
                annuity_obj.price_ch_dem_gas = dict_city_samples['ch_dem_gas'][
                    i]
                annuity_obj.price_ch_dem_el = dict_city_samples['ch_dem_el'][i]
                # Reuse ch_dem_el for hp price change
                annuity_obj.price_ch_dem_el_hp = \
                dict_city_samples['ch_dem_el'][i]
                annuity_obj.price_ch_op = dict_city_samples['ch_op'][i]
                annuity_obj.price_ch_eeg_chp = dict_city_samples['ch_eeg_chp'][
                    i]
                annuity_obj.price_ch_eeg_pv = dict_city_samples['ch_eeg_pv'][i]
                annuity_obj.price_ch_eex = dict_city_samples['ch_eex'][i]
                annuity_obj.price_ch_grid_use = \
                dict_city_samples['ch_grid_use'][i]

            elif sampling_method == 'lhc':

                dict_city_lhc = self._dict_city_sample_lhc

                # #  City sample dict
                # #  Uncertain interest
                # dict_city_sample['interest']
                # #  Uncertain price change capital
                # dict_city_sample['price_ch_cap']
                # #  Uncertain price change demand gas
                # dict_city_sample['price_ch_dem_gas']
                # #  Uncertain price change demand electricity
                # dict_city_sample['price_ch_dem_el']
                # #  Uncertain price change operation
                # dict_city_sample['price_ch_op']
                # #  Uncertain price change eeg payments for self-con. chp el.
                # dict_city_sample['price_ch_eeg_chp']
                # #  Uncertain price change eeg payments for self-con. PV el.
                # dict_city_sample['price_ch_eeg_pv']
                # #  Uncertain price change EEX baseload price
                # dict_city_sample['price_ch_eex']
                # #  Uncertain price change grid usage fee
                # dict_city_sample['price_ch_grid_use']
                # #  Uncertain ground temperature
                # dict_city_sample['temp_ground']
                # #  Uncertain LHN loss factor change
                # dict_city_sample['lhn_loss']
                # #  Uncertain LHN investment cost change
                # dict_city_sample['lhn_inv']
                # # Uncertain summer mode on / off
                # #  Holding list holding arrays with building node ids with
                #  heating during
                # # summer
                # dict_city_sample['list_sum_on']

                if heating_off:
                    #  Use sampling to switch demand of some heating systems off
                    #  during summer period

                    #  Get array with building ids with summer heating mode on
                    array_heat_on = dict_city_lhc['list_sum_on'][i]

                    #  Calculate list of building ids, where heating is off during
                    #  summer
                    list_heat_off = list(set(self._list_build_ids) -
                                         set(array_heat_on))

                    for n in list_heat_off:
                        curr_build = city.nodes[n]['entity']

                        #  Modify space heating (switch off during summer)
                        shmod.sh_curve_summer_off_build(building=curr_build)

                # Save inputs to city, market and environment
                city.environment.temp_ground = \
                    dict_city_lhc['temp_ground'][i]
                city.environment.prices.grid_av_fee = \
                    dict_city_lhc['grid_av_fee'][i]

                #  Save inputs to annuity_obj
                annuity_obj.interest = dict_city_lhc['interest'][i]
                annuity_obj.price_ch_cap = dict_city_lhc['price_ch_cap'][i]
                annuity_obj.price_ch_dem_gas = \
                dict_city_lhc['price_ch_dem_gas'][
                    i]
                annuity_obj.price_ch_dem_el = dict_city_lhc['price_ch_dem_el'][
                    i]
                # Reuse ch_dem_el for hp price change
                annuity_obj.price_ch_dem_el_hp = \
                    dict_city_lhc['price_ch_dem_el'][i]
                annuity_obj.price_ch_op = dict_city_lhc['price_ch_op'][i]
                annuity_obj.price_ch_eeg_chp = \
                dict_city_lhc['price_ch_eeg_chp'][
                    i]
                annuity_obj.price_ch_eeg_pv = dict_city_lhc['price_ch_eeg_pv'][
                    i]
                annuity_obj.price_ch_eex = dict_city_lhc['price_ch_eex'][i]
                annuity_obj.price_ch_grid_use = \
                    dict_city_lhc['price_ch_grid_use'][i]

            #  Rerun initial parameter calculation of annuity_obj
            annuity_obj.initial_calc()
            #  Necessary to recalculate values, that depend on sampling data

            #  Run energy balance and annuity calculation
            #  ###############################################################
            try:
                (total_annuity, co2) = c_eco_copy. \
                    perform_overall_energy_balance_and_economic_calc(
                    run_mc=True,
                    sampling_method=sampling_method,
                    dict_samples_const=self._dict_samples_const,
                    dict_samples_esys=self._dict_samples_esys,
                    dict_city_sample_lhc=self._dict_city_sample_lhc,
                    dict_build_samples_lhc=self._dict_build_samples_lhc,
                    run_idx=i,
                    eeg_pv_limit=eeg_pv_limit,
                    use_kwkg_lhn_sub=use_kwkg_lhn_sub,
                    el_mix_for_chp=el_mix_for_chp,
                    el_mix_for_pv=el_mix_for_pv
                )

                #  Extract further results
                sh_dem = c_eco_copy.energy_balance. \
                    city.get_annual_space_heating_demand()
                el_dem = c_eco_copy.energy_balance. \
                    city.get_annual_el_demand()
                dhw_dem = c_eco_copy.energy_balance. \
                    city.get_annual_dhw_demand()

                gas_boiler = c_eco_copy.energy_balance.dict_fe_city_balance[
                    'fuel_boiler']
                gas_chp = c_eco_copy.energy_balance.dict_fe_city_balance[
                    'fuel_chp']
                grid_imp_dem = c_eco_copy.energy_balance.dict_fe_city_balance[
                    'grid_import_dem']
                grid_imp_hp = c_eco_copy.energy_balance.dict_fe_city_balance[
                    'grid_import_hp']
                grid_imp_eh = c_eco_copy.energy_balance.dict_fe_city_balance[
                    'grid_import_eh']
                lhn_pump = c_eco_copy.energy_balance.dict_fe_city_balance[
                    'pump_energy']

                grid_exp_chp = c_eco_copy.energy_balance.dict_fe_city_balance[
                    'chp_feed']
                grid_exp_pv = c_eco_copy.energy_balance.dict_fe_city_balance[
                    'pv_feed']

                #  Save results
                array_annuity[i] = total_annuity
                array_co2[i] = co2
                array_net_sh[i] = sh_dem
                array_net_el[i] = el_dem
                array_net_dhw[i] = dhw_dem

                array_gas_boiler[i] = gas_boiler
                array_gas_chp[i] = gas_chp
                array_grid_imp_dem[i] = grid_imp_dem
                array_grid_imp_hp[i] = grid_imp_hp
                array_grid_imp_eh[i] = grid_imp_eh
                array_lhn_pump[i] = lhn_pump
                array_grid_exp_chp[i] = grid_exp_chp
                array_grid_exp_pv[i] = grid_exp_pv

                dict_mc_res['annuity'] = array_annuity
                dict_mc_res['co2'] = array_co2
                dict_mc_res['sh_dem'] = array_net_sh
                dict_mc_res['el_dem'] = array_net_el
                dict_mc_res['dhw_dem'] = array_net_dhw
                dict_mc_res['gas_boiler'] = array_gas_boiler
                dict_mc_res['gas_chp'] = array_gas_chp
                dict_mc_res['grid_imp_dem'] = array_grid_imp_dem
                dict_mc_res['grid_imp_hp'] = array_grid_imp_hp
                dict_mc_res['grid_imp_eh'] = array_grid_imp_eh
                dict_mc_res['lhn_pump'] = array_lhn_pump
                dict_mc_res['grid_exp_chp'] = array_grid_exp_chp
                dict_mc_res['grid_exp_pv'] = array_grid_exp_pv

                if calc_th_el_cov:
                    #  #####################################################
                    #  Calculate thermal and electric coverage by device

                    timestep = city.environment.timer.timeDiscretization

                    nb_timesteps = int((365 * 24 * 3600) / timestep)

                    #  Initial zero result arrays (on city district level)
                    array_chp_q_out = np.zeros(nb_timesteps)
                    array_chp_el_out = np.zeros(nb_timesteps)
                    array_boi_q_out = np.zeros(nb_timesteps)
                    array_hp_aw_q_out = np.zeros(nb_timesteps)
                    array_hp_aw_el_in = np.zeros(nb_timesteps)
                    array_hp_ww_q_out = np.zeros(nb_timesteps)
                    array_hp_ww_el_in = np.zeros(nb_timesteps)
                    array_eh_q_out = np.zeros(nb_timesteps)
                    array_pv_el_out = np.zeros(nb_timesteps)

                    #  Loop over each building in city and extract generated
                    #  power

                    for n in c_eco_copy._list_buildings:
                        curr_b = city.nodes[n]['entity']
                        if curr_b.hasBes:
                            if curr_b.bes.hasBoiler:
                                array_boi_q_out += \
                                    curr_b.bes.boiler.totalQOutput
                            if curr_b.bes.hasChp:
                                array_chp_q_out += \
                                    curr_b.bes.chp.totalQOutput
                                array_chp_el_out += \
                                    curr_b.bes.chp.totalPOutput
                            if curr_b.bes.hasHeatpump:
                                if curr_b.bes.heatpump.hp_type == 'aw':
                                    array_hp_aw_q_out += \
                                        curr_b.bes.heatpump.totalQOutput
                                    array_hp_aw_el_in += \
                                        curr_b.bes.heatpump.array_el_power_in
                                elif curr_b.bes.heatpump.hp_type == 'ww':
                                    array_hp_ww_q_out += \
                                        curr_b.bes.heatpump.totalQOutput
                                    array_hp_ww_el_in += \
                                        curr_b.bes.heatpump.array_el_power_in
                                else:
                                    msg = 'Unkown heat pump type'
                                    raise AssertionError(msg)
                            if curr_b.bes.hasElectricalHeater:
                                array_eh_q_out += \
                                    curr_b.bes.electricalHeater.totalQOutput
                            if curr_b.bes.hasPv:
                                array_pv_el_out += \
                                    curr_b.bes.pv.totalPower

                    #  Calculate coverage factors
                    th_energy_boi = sum(array_boi_q_out) * timestep \
                                    / (3600 * 1000)
                    th_energy_chp = sum(array_chp_q_out) * timestep \
                                    / (3600 * 1000)
                    el_energy_chp = sum(array_chp_el_out) * timestep \
                                    / (3600 * 1000)
                    th_energy_hp_aw = sum(array_hp_aw_q_out) * timestep \
                                    / (3600 * 1000)
                    el_energy_hp_aw = sum(array_hp_aw_el_in) * timestep \
                                      / (3600 * 1000)
                    th_energy_hp_ww = sum(array_hp_ww_q_out) * timestep \
                                      / (3600 * 1000)
                    el_energy_hp_ww = sum(array_hp_ww_el_in) * timestep \
                                      / (3600 * 1000)
                    th_energy_eh = sum(array_eh_q_out) * timestep \
                                      / (3600 * 1000)
                    el_energy_pv = sum(array_pv_el_out) * timestep \
                                   / (3600 * 1000)

                    #  Also includes LHN and storage losses (thus, not using
                    #  sh_dem value)
                    th_energy_overall_gen = (th_energy_boi + th_energy_chp
                                             + th_energy_hp_aw
                                             + th_energy_hp_ww + th_energy_eh)

                    #  Thermal coverage factors
                    th_cov_boi = th_energy_boi / th_energy_overall_gen
                    th_cov_chp = th_energy_chp / th_energy_overall_gen
                    th_cov_hp_aw = th_energy_hp_aw / th_energy_overall_gen
                    th_cov_hp_ww = th_energy_hp_ww / th_energy_overall_gen
                    th_cov_eh = th_energy_eh / th_energy_overall_gen

                    #  El. ref. demand (100 % eff. of electr. heater)
                    el_ref_dem = (el_dem + el_energy_hp_aw + el_energy_hp_ww
                                  + th_energy_eh)

                    #  Electric coverage factors
                    el_cov_chp = (el_energy_chp - grid_exp_chp) / el_ref_dem
                    el_cov_pv = (el_energy_pv - grid_exp_pv) / el_ref_dem
                    el_cov_grid = (grid_imp_dem + grid_imp_hp
                                   + grid_imp_eh) / el_ref_dem

                    #  Add coverage factors to results file
                    array_th_cov_boi[i] = th_cov_boi
                    array_th_cov_chp[i] = th_cov_chp
                    array_th_cov_hp_aw[i] = th_cov_hp_aw
                    array_th_cov_hp_ww[i] = th_cov_hp_ww
                    array_th_cov_eh[i] = th_cov_eh

                    array_el_cov_chp[i] = el_cov_chp
                    array_el_cov_pv[i] = el_cov_pv
                    array_el_cov_grid[i] = el_cov_grid

                    #  Save results to dict
                    dict_mc_cov['th_cov_boi'] = array_th_cov_boi
                    dict_mc_cov['th_cov_chp'] = array_th_cov_chp
                    dict_mc_cov['th_cov_hp_aw'] = array_th_cov_hp_aw
                    dict_mc_cov['th_cov_hp_ww'] = array_th_cov_hp_ww
                    dict_mc_cov['th_cov_eh'] = array_th_cov_eh
                    dict_mc_cov['el_cov_chp'] = array_el_cov_chp
                    dict_mc_cov['el_cov_pv'] = array_el_cov_pv
                    dict_mc_cov['el_cov_grid'] = array_el_cov_grid

            except buildeb.EnergyBalanceException as ermessage:
                print(ermessage)
                traceback.print_exc()
                #  Count failure nb. up
                self._nb_failed_runs += 1
                self._list_failed_runs.append(i)
                msg = 'Run %d failed with EnergyBalanceException' % (i)
                warnings.warn(msg)

            except tessys.TESChargingException as ermessage:
                print(ermessage)
                traceback.print_exc()
                #  Count failure nb. up
                self._nb_failed_runs += 1
                self._list_failed_runs.append(i)
                msg = 'Run %d failed with EnergyBalanceException' % (i)
                warnings.warn(msg)

            #  Write results to dict



            if self._nb_failed_runs > failure_tolerance * nb_runs:
                msg = 'Number of failed runs exceeds ' \
                      'allowed limit of %d runs!' % (
                              failure_tolerance * nb_runs)
                raise McToleranceException(msg)

            # Save failed run information to dict_mc_setup
            dict_mc_setup['idx_failed_runs'] = self._list_failed_runs

        return (dict_mc_res, dict_mc_setup, dict_mc_cov)

    def run_mc_analysis(self, nb_runs, sampling_method,
                        do_sampling=True,
                        failure_tolerance=0.05,
                        prevent_printing=False,
                        heating_off=True,
                        load_sh_mc_res=False,
                        path_mc_res_folder=None,
                        use_profile_pool=False,
                        gen_use_prof_method=0,
                        path_profile_dict=None,
                        save_res=True,
                        nb_profiles=None,
                        random_profile=False,
                        load_city_n_build_samples=False,
                        path_city_sample_dict=None,
                        path_build_sample_dict=None,
                        eeg_pv_limit=False,
                        use_kwkg_lhn_sub=False,
                        calc_th_el_cov=False,
                        dem_unc=True,
                        el_mix_for_chp=True,
                        el_mix_for_pv=True
                        ):
        """
        Perform monte-carlo run with:
        - sampling
        - energy balance calculation
        - annuity calculation
        - return of results

        Parameters
        ----------
        nb_runs : int
            Number of Monte-Carlo loops
        sampling_method : str
            Defines method used for sampling.
            Options:
            - 'lhc': latin hypercube sampling
            - 'random': randomized sampling
        do_sampling : bool, optional
            Defines, if sampling should be performed/samples should be loaded
            from path (default: True). Else: Use existing sample data on
            mc_runner.py object
        failure_tolerance : float, optional
            Allowed EnergyBalanceException failure tolerance (default: 0.05).
            E.g. 0.05 means, that 5% of runs are allowed to fail with
            EnergyBalanceException.
        prevent_printing : bool, optional
            Defines, if printing statements should be suppressed
        heating_off : bool, optional
            Defines, if sampling to deactivate heating during summer should
            be used (default: True)
        load_sh_mc_res : bool, optional
            If True, tries to load space heating monte-carlo uncertainty run
            results for each building and uses result to sample space heating
            values. If False, uses default distribution to sample space heating
            values (default: False)
        path_mc_res_folder : str, optional
            Path to folder, where sh mc run results are stored (default: None).
            Only necessary if load_sh_mc_res is True
        use_profile_pool : bool, optional
            Defines, if user/el. load/dhw profile pool should be generated
            (default: False). If True, generates profile pool.
        gen_use_prof_method : int, optional
            Defines method for el. profile pool usage (default: 0).
            Options:
            - 0: Generate new el. profile pool
            - 1: Load profile pool from path_profile_dict
        path_profile_dict : str, optional
            Path to dict with el. profile pool (default: None).
        save_res : bool, optional
            Save results back to mc_runner object (default: True)
        nb_profiles : int, optional
            Desired number of profile samples per building, when profile pool
            is generated (default: None). If None, uses nb_runs.
        random_profile : bool, optional
            Defines, if random samples should be used from profile pool
            (default: False). Only relevant, if profile pool has been given,
            sampling_method == 'lhc' and nb. of profiles is equal to nb.
            of samples
        load_city_n_build_samples : bool, optional
            Defines, if existing city and building sample dicts should be
            loaded (default: False). If False, generates new sample dicts.
        path_city_sample_dict : str, optional
            Defines path to city sample dict (default: None). Only relevant,
            if load_city_n_build_samples is True
        path_build_sample_dict : str, optional
            Defines path to building sample dict (default: None). Only relevant,
            if load_city_n_build_samples is True
        eeg_pv_limit : bool, optional
            Defines, if EEG PV feed-in limitation of 70 % of peak load is
            active (default: False). If limitation is active, maximal 70 %
            of PV peak load are fed into the grid.
            However, self-consumption is used, first.
        use_kwkg_lhn_sub : bool, optional
            Defines, if KWKG LHN subsidies are used (default: True).
            If True, can get 100 Euro/m as subdidy, if share of CHP LHN fed-in
            is equal to or higher than 60 %
        calc_th_el_cov : bool, optional
            Defines, if thermal and electric coverage of different types of
            devices should be calculated (default: False)
        dem_unc : bool, optional
            Defines, if thermal, el. and dhw demand are assumed to be uncertain
            (default: True). If True, samples demands. If False, uses reference
            demands.
        el_mix_for_chp : bool, optional
            Defines, if el. mix should be used for CHP fed-in electricity
            (default: True). If False, uses specific fed-in CHP factor,
            defined in co2emissions object (co2_factor_el_feed_in)
        el_mix_for_pv : bool, optional
            Defines, if el. mix should be used for PV fed-in electricity
            (default: True). If False, uses specific fed-in PV factor,
            defined in co2emissions object (co2_factor_pv_fed_in)

        Returns
        -------
        tuple_res : tuple (of dicts)
            Tuple holding five dictionaries
            For sampling_method == 'random':
            (dict_samples_const, dict_samples_esys, dict_mc_res, dict_mc_setup,
            None)
            dict_samples_const : dict (of dicts)
                Dictionary holding dictionaries with constant
                sample data for MC run
                dict_samples_const['city'] = dict_city_samples
                dict_samples_const['<building_id>'] = dict_build_dem
                (of building with id <building_id>)
            dict_samples_esys : dict (of dicts)
                Dictionary holding dictionaries with energy system sampling
                data for MC run
                dict_samples_esys['<building_id>'] = dict_esys
                (of building with id <building_id>)
            dict_mc_res : dict
                Dictionary with result arrays for each run
                dict_mc_res['annuity'] = array_annuity
                dict_mc_res['co2'] = array_co2
                dict_mc_res['sh_dem'] = array_net_sh
                dict_mc_res['el_dem'] = array_net_el
                dict_mc_res['dhw_dem'] = array_net_dhw
                dict_mc_res['gas_boiler'] = array_gas_boiler
                dict_mc_res['gas_chp'] = array_gas_chp
                dict_mc_res['grid_imp_dem'] = array_grid_imp_dem
                dict_mc_res['grid_imp_hp'] = array_grid_imp_hp
                dict_mc_res['grid_imp_eh'] = array_grid_imp_eh
                dict_mc_res['lhn_pump'] = array_lhn_pump
                dict_mc_res['grid_exp_chp'] = array_grid_exp_chp
                dict_mc_res['grid_exp_pv'] = array_grid_exp_pv
            dict_mc_setup : dict
                Dictionary holding mc run settings
                dict_mc_setup['nb_runs'] = nb_runs
                dict_mc_setup['failure_tolerance'] = failure_tolerance
                dict_mc_setup['heating_off'] = heating_off
                dict_mc_setup['idx_failed_runs'] = self._list_failed_runs
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

            For sampling_method == 'lhc':
            (dict_city_sample_lhc, dict_build_samples_lhc, dict_mc_res,
                    dict_mc_setup, dict_profiles_lhc)
            dict_city_sample_lhc : dict
                Dict holding city parameter names as keys and numpy arrays with
                samples as dict values
            dict_build_samples_lhc : dict
                Dict. holding building ids as keys and dict of samples as
                values.
                These dicts hold paramter names as keys and numpy arrays with
                samples as dict values
            dict_mc_res : dict
                Dictionary with result arrays for each run
                dict_mc_res['annuity'] = array_annuity
                dict_mc_res['co2'] = array_co2
                dict_mc_res['sh_dem'] = array_net_sh
                dict_mc_res['el_dem'] = array_net_el
                dict_mc_res['dhw_dem'] = array_net_dhw
                dict_mc_res['gas_boiler'] = array_gas_boiler
                dict_mc_res['gas_chp'] = array_gas_chp
                dict_mc_res['grid_imp_dem'] = array_grid_imp_dem
                dict_mc_res['grid_imp_hp'] = array_grid_imp_hp
                dict_mc_res['grid_imp_eh'] = array_grid_imp_eh
                dict_mc_res['lhn_pump'] = array_lhn_pump
                dict_mc_res['grid_exp_chp'] = array_grid_exp_chp
                dict_mc_res['grid_exp_pv'] = array_grid_exp_pv
            dict_mc_setup : dict
                Dictionary holding mc run settings
                dict_mc_setup['nb_runs'] = nb_runs
                dict_mc_setup['failure_tolerance'] = failure_tolerance
                dict_mc_setup['heating_off'] = heating_off
                dict_mc_setup['idx_failed_runs'] = self._list_failed_runs
            dict_profiles_lhc : dict
                Dict. holding building ids as keys and dict with numpy arrays
                with different el. and dhw profiles for each building as value
                fict_profiles_build['el_profiles'] = el_profiles
                dict_profiles_build['dhw_profiles'] = dhw_profiles
                When use_profile_pool is False, dict_profiles is None
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

        if sampling_method not in ['lhc', 'random']:
            msg = 'Sampling method ' + str(sampling_method) + ' is unknown!'
            raise AssertionError(msg)

        if nb_runs <= 0:
            msg = 'nb_runs has to be larger than zero!'
            raise AssertionError(msg)

        if do_sampling:
            if sampling_method == 'random':
                #  Call sampling and save sample data to _dict_samples_const
                #  and _dict_samples_esys
                (dict_samples_const, dict_samples_esys) = \
                    self.perform_sampling(nb_runs=nb_runs,
                                          dem_unc=dem_unc)
            elif sampling_method == 'lhc':
                #  Perform latin hypercube sampling
                (dict_city_sample_lhc, dict_build_samples_lhc,
                 dict_profiles_lhc) = self.\
                    perform_lhc_sampling(nb_runs=nb_runs,
                                         load_sh_mc_res=load_sh_mc_res,
                                         path_mc_res_folder=path_mc_res_folder,
                                         use_profile_pool=use_profile_pool,
                                         gen_use_prof_method=gen_use_prof_method,
                                         path_profile_dict=path_profile_dict,
                                         save_res=save_res,
                                         nb_profiles=nb_profiles,
                                         load_city_n_build_samples=load_city_n_build_samples,
                                         path_city_sample_dict=path_city_sample_dict,
                                         path_build_sample_dict=path_build_sample_dict,
                                         dem_unc=dem_unc)
        else:
            dict_samples_const = None
            dict_samples_esys = None
            dict_city_sample_lhc = None
            dict_build_samples_lhc = None
            dict_profiles_lhc = None

        if prevent_printing:
            block_print()

        # Perform monte-carlo runs
        (dict_mc_res, dict_mc_setup, dict_mc_cov) = \
            self.perform_mc_runs(nb_runs=nb_runs,
                                 sampling_method=sampling_method,
                                 failure_tolerance=failure_tolerance,
                                 heating_off=heating_off,
                                 random_profile=random_profile,
                                 eeg_pv_limit=eeg_pv_limit,
                                 use_kwkg_lhn_sub=use_kwkg_lhn_sub,
                                 calc_th_el_cov=calc_th_el_cov,
                                 el_mix_for_chp=el_mix_for_chp,
                                 el_mix_for_pv=el_mix_for_pv
                                 )

        if prevent_printing:
            enable_print()

        if do_sampling and sampling_method == 'random':
            return (dict_samples_const, dict_samples_esys, dict_mc_res,
                    dict_mc_setup, None, dict_mc_cov)
        elif do_sampling and sampling_method == 'lhc':
            return (dict_city_sample_lhc, dict_build_samples_lhc, dict_mc_res,
                    dict_mc_setup, dict_profiles_lhc, dict_mc_cov)
        else:
            return (None, None, dict_mc_res, dict_mc_setup, None, dict_mc_cov)

    def perform_ref_run(self, save_res=True, eeg_pv_limit=False,
                        use_kwkg_lhn_sub=False, chp_switch_pen=False,
                        max_switch=None, obj='min', el_mix_for_chp=True,
                        el_mix_for_pv=True):
        """
        Perform reference energy balance and annuity run with default values
        given by city object, environment etc.

        Parameters
        ----------
        save_res : bool, optional
            Defines, if results should be saved on McRunner object
            (default: True)
        eeg_pv_limit : bool, optional
            Defines, if EEG PV feed-in limitation of 70 % of peak load is
            active (default: False). If limitation is active, maximal 70 %
            of PV peak load are fed into the grid.
            However, self-consumption is used, first.
        use_kwkg_lhn_sub : bool, optional
            Defines, if KWKG LHN subsidies are used (default: False).
            If True, can get 100 Euro/m as subdidy, if share of CHP LHN fed-in
            is equal to or higher than 60 %
        chp_switch_pen : bool, optional
            Defines, if too many switchings per day (CHP) should be penalized
            (default: False).
        max_switch : int, optional
            Defines maximum number of allowed average switching commands per
            CHP for a single day (default: None), e.g. 8 means that a
            maximum of 8 on/off or off/on switching commands is allowed as
            average per day. Only relevant, if chp_switch_pen is True
        obj : str, optional
            Defines if objective should be maximized or minimized (if
            optimization is used (default: 'min').
            Options:
            - 'max': Maximization
            - 'min': Minimization
            Only relevant, if CHP switching penalty is used
        el_mix_for_chp : bool, optional
            Defines, if el. mix should be used for CHP fed-in electricity
            (default: True). If False, uses specific fed-in CHP factor,
            defined in co2emissions object (co2_factor_el_feed_in)
        el_mix_for_pv : bool, optional
            Defines, if el. mix should be used for PV fed-in electricity
            (default: True). If False, uses specific fed-in PV factor,
            defined in co2emissions object (co2_factor_pv_fed_in)

        Returns
        -------
        tuple_res : tuple
            Results tuple (total_annuity, co2, sh_dem, el_dem, dhw_dem)
            total_annuity : float
                Total annuity in Euro/a
            co2 : float
                Total CO2 emissions in kg/a
            sh_dem : float
                Net space heating demand in kWH/a
            el_dem : float
                Net electric demand in kWH/a
            dhw_dem : float
                Net hot water thermal energy demand in kWH/a
        """

        assert obj in ['min', 'max'], 'Unknown objective'

        if chp_switch_pen:
            if max_switch is None:
                msg = 'max_switch cannot be None, if chp_switch_pen is ' \
                      'True. Please set a maximum number of allowed ' \
                      'switching CHP commands per day (e.g. max_switch = 8).'
                raise AssertionError(msg)

        #  Copy CityAnnuityCalc object
        c_eco_copy = copy.deepcopy(self._city_eco_calc)

        (total_annuity, co2) = c_eco_copy. \
            perform_overall_energy_balance_and_economic_calc(run_mc=False,
                                                             eeg_pv_limit=
                                                             eeg_pv_limit,
                                                             use_kwkg_lhn_sub=
                                                             use_kwkg_lhn_sub,
                                                             el_mix_for_chp=
                                                             el_mix_for_chp,
                                                             el_mix_for_pv=
                                                             el_mix_for_pv
                                                             )

        if chp_switch_pen:
            #  #####################################################
            #  Penalize too many switching commands
            #  Relevant for pyCity_resilience
            switch_okay = penalize_switching(
                city=c_eco_copy.energy_balance.city,
                max_switch=max_switch)
            if switch_okay is False:
                msg = 'Too many CHP switchings per day. ' \
                      'Penalize solution.'
                warnings.warn(msg)
                if obj == 'max':
                    total_annuity = -10 ** 100
                    co2 = -10 ** 100
                elif obj == 'min':
                    total_annuity = 10 ** 100
                    co2 = 10 ** 100

            if switch_okay is None:
                msg = 'penalize_switching retunred None. Thus, CHP results' \
                      ' array is empty / one CHP might not have been used.' \
                      'Penalized solution.'
                warnings.warn(msg)
            #  #####################################################

        #  Extract further results
        sh_dem = c_eco_copy.energy_balance. \
            city.get_annual_space_heating_demand()
        el_dem = c_eco_copy.energy_balance. \
            city.get_annual_el_demand()
        dhw_dem = c_eco_copy.energy_balance. \
            city.get_annual_dhw_demand()

        if save_res:
            self._tuple_ref_results = (total_annuity, co2, sh_dem,
                                       el_dem, dhw_dem)
            self._dict_fe_ref_run = c_eco_copy. \
                energy_balance.dict_fe_city_balance

        return (total_annuity, co2, sh_dem, el_dem, dhw_dem)


def main():

    #  Generate city district or load city district

    #  Dimension energy systems, if not already included

    this_path = os.path.dirname(os.path.abspath(__file__))

    try:
        #  Try loading city pickle file
        filename = 'city_with_esys.pkl'
        file_path = os.path.join(this_path, 'input', filename)
        city = pickle.load(open(file_path, mode='rb'))

    except:

        print('Could not load city pickle file. Going to generate a new one.')

        #  # Userinputs
        #  #----------------------------------------------------------------------

        #  Generate environment
        #  ######################################################
        year_timer = 2017
        year_co2 = 2017
        timestep = 3600  # Timestep in seconds
        # location = (51.529086, 6.944689)  # (latitude, longitude) of Bottrop
        location = (50.775346, 6.083887)  # (latitude, longitude) of Aachen
        altitude = 266  # Altitude of location in m (Aachen)

        #  Weather path
        try_path = None
        #  If None, used default TRY (region 5, 2010)

        new_try = False
        #  new_try has to be set to True, if you want to use TRY data of 2017
        #  or newer! Else: new_try = False

        #  Space heating load generation
        #  ######################################################
        #  Thermal generation method
        #  1 - SLP (standardized load profile)
        #  2 - Load and rescale Modelica simulation profile
        #  (generated with TRY region 12, 2010)
        #  3 - VDI 6007 calculation (requires el_gen_method = 2)
        th_gen_method = 3
        #  For non-residential buildings, SLPs are generated automatically.

        #  Manipulate thermal slp to fit to space heating demand?
        slp_manipulate = False
        #  True - Do manipulation
        #  False - Use original profile
        #  Only relevant, if th_gen_method == 1
        #  Sets thermal power to zero in time spaces, where average daily outdoor
        #  temperature is equal to or larger than 12 °C. Rescales profile to
        #  original demand value.

        #  Manipulate vdi space heating load to be normalized to given annual net
        #  space heating demand in kWh
        vdi_sh_manipulate = False

        #  Electrical load generation
        #  ######################################################
        #  Choose electric load profile generation method (1 - SLP; 2 - Stochastic)
        #  Stochastic profile is only generated for residential buildings,
        #  which have a defined number of occupants (otherwise, SLP is used)
        el_gen_method = 2
        #  If user defindes method_3_nb or method_4_nb within input file
        #  (only valid for non-residential buildings), SLP will not be used.
        #  Instead, corresponding profile will be loaded (based on measurement
        #  data, see ElectricalDemand.py within pycity)

        #  Do normalization of el. load profile
        #  (only relevant for el_gen_method=2).
        #  Rescales el. load profile to expected annual el. demand value in kWh
        do_normalization = True

        #  Randomize electrical demand value (residential buildings, only)
        el_random = False

        #  Prevent usage of electrical heating and hot water devices in
        #  electrical load generation
        prev_heat_dev = True
        #  True: Prevent electrical heating device usage for profile generation
        #  False: Include electrical heating devices in electrical load generation

        #  Use cosine function to increase winter lighting usage and reduce
        #  summer lighting usage in richadson el. load profiles
        #  season_mod is factor, which is used to rescale cosine wave with
        #  lighting power reference (max. lighting power)
        season_mod = 0.3
        #  If None, do not use cosine wave to estimate seasonal influence
        #  Else: Define float
        #  (only relevant if el_gen_method == 2)

        #  Hot water profile generation
        #  ######################################################
        #  Generate DHW profiles? (True/False)
        use_dhw = True  # Only relevant for residential buildings

        #  DHW generation method? (1 - Annex 42; 2 - Stochastic profiles)
        #  Choice of Anex 42 profiles NOT recommended for multiple builings,
        #  as profile stays the same and only changes scaling.
        #  Stochastic profiles require defined nb of occupants per residential
        #  building
        dhw_method = 2  # Only relevant for residential buildings

        #  Define dhw volume per person and day (use_dhw=True)
        dhw_volumen = None  # Only relevant for residential buildings

        #  Randomize choosen dhw_volume reference value by selecting new value
        #  from gaussian distribution with 20 % standard deviation
        dhw_random = False

        #  Use dhw profiles for esys dimensioning
        dhw_dim_esys = True

        #  Plot city district with pycity_calc visualisation
        plot_pycity_calc = False

        #  Efficiency factor of thermal energy systems
        #  Used to convert input values (final energy demand) to net energy demand
        eff_factor = 1

        #  Define city district input data filename
        filename = 'city_clust_simple.txt'

        txt_path = os.path.join(this_path, 'input', filename)

        #  Define city district output file
        save_filename = None
        # save_path = os.path.join(this_path, 'output_overall', save_filename)
        save_path = None

        #  #####################################
        t_set_heat = 20  # Heating set temperature in degree Celsius
        t_set_night = 16  # Night set back temperature in degree Celsius
        t_set_cool = 70  # Cooling set temperature in degree Celsius

        #  Air exchange rate (required for th_gen_method = 3 (VDI 6007 sim.))
        air_vent_mode = 2
        #  int; Define mode for air ventilation rate generation
        #  0 : Use constant value (vent_factor in 1/h)
        #  1 : Use deterministic, temperature-dependent profile
        #  2 : Use stochastic, user-dependent profile
        #  False: Use static ventilation rate value

        vent_factor = 0.5  # Constant. ventilation rate
        #  (only used, if air_vent_mode = 0)
        #  #####################################

        #  Use TEASER to generate typebuildings?
        call_teaser = False
        teaser_proj_name = filename[:-4]

        merge_windows = False
        # merge_windows : bool, optional
        # Defines TEASER project setting for merge_windows_calc
        # (default: False). If set to False, merge_windows_calc is set to False.
        # If True, Windows are merged into wall resistances.

        #  Log file for city_generator
        do_log = False  # True, generate log file
        log_path = os.path.join(this_path, 'input',
                                'city_gen_overall_log.txt')

        #  Generate street networks
        gen_str = True  # True - Generate street network

        #  Street node and edges input filenames
        str_node_filename = 'street_nodes_cluster_simple.csv'
        str_edge_filename = 'street_edges_cluster_simple.csv'

        #  Load street data from csv
        str_node_path = os.path.join(this_path, 'input',
                                     str_node_filename)
        str_edge_path = os.path.join(this_path, 'input',
                                     str_edge_filename)

        #  Add energy networks to city
        gen_e_net = True  # True - Generate energy networks

        #  Path to energy network input file (csv/txt; tab separated)
        network_filename = 'city_clust_simple_networks.txt'
        network_path = os.path.join(this_path, 'input',
                                    network_filename)

        #  Add energy systems to city
        gen_esys = True  # True - Generate energy networks

        #  Path to energy system input file (csv/txt; tab separated)
        esys_filename = 'city_clust_simple_enersys.txt'
        esys_path = os.path.join(this_path, 'input',
                                 esys_filename)

        #  #----------------------------------------------------------------------

        #  Load district_data file
        district_data = citygen.get_district_data_from_txt(txt_path)

        city = overall.run_overall_gen_and_dim(timestep=timestep,
                                               year_timer=year_timer,
                                               year_co2=year_co2,
                                               location=location,
                                               try_path=try_path,
                                               th_gen_method=th_gen_method,
                                               el_gen_method=el_gen_method,
                                               use_dhw=use_dhw,
                                               dhw_method=dhw_method,
                                               district_data=district_data,
                                               gen_str=gen_str,
                                               str_node_path=str_node_path,
                                               str_edge_path=str_edge_path,
                                               generation_mode=0,
                                               eff_factor=eff_factor,
                                               save_path=save_path,
                                               altitude=altitude,
                                               do_normalization=do_normalization,
                                               dhw_volumen=dhw_volumen,
                                               gen_e_net=gen_e_net,
                                               network_path=network_path,
                                               gen_esys=gen_esys,
                                               esys_path=esys_path,
                                               dhw_dim_esys=dhw_dim_esys,
                                               plot_pycity_calc=plot_pycity_calc,
                                               slp_manipulate=slp_manipulate,
                                               call_teaser=call_teaser,
                                               teaser_proj_name=teaser_proj_name,
                                               do_log=do_log,
                                               log_path=log_path,
                                               air_vent_mode=air_vent_mode,
                                               vent_factor=vent_factor,
                                               t_set_heat=t_set_heat,
                                               t_set_cool=t_set_cool,
                                               t_night=t_set_night,
                                               vdi_sh_manipulate=vdi_sh_manipulate,
                                               el_random=el_random,
                                               dhw_random=dhw_random,
                                               prev_heat_dev=prev_heat_dev,
                                               season_mod=season_mod,
                                               merge_windows=merge_windows,
                                               new_try=new_try)

        #  Increase system size
        modesys.incr_esys_size_city(city=city)

        # Save new pickle file
        filename = 'city_clust_simple_with_esys.pkl'
        file_path = os.path.join(this_path, 'input', filename)
        pickle.dump(city, open(file_path, mode='wb'))



    # # #  TODO: Uncomment later
    # #  Temporary add energy systems to buildings
    # #  Generate energy systems
    # #  Generate one feeder with CHP, boiler and TES
    # list_esys = [(1001, 0, 1),
    #              (1002, 0, 2),
    #              (1003, 1, 1),
    #              (1004, 1, 1),
    #              (1005, 1, 1),
    #              (1006, 2, 1),
    #              (1007, 2, 2),
    #              (1001, 3, 10),
    #              (1002, 3, 20),
    #              (1003, 3, 30),
    #              (1004, 3, 40),
    #              (1005, 3, 50),
    #              (1006, 3, 60),
    #              (1007, 3, 70)
    #              ]
    #
    # esysgen.gen_esys_for_city(city=city,
    #                           list_data=list_esys,
    #                           dhw_scale=True)



    # Uncomment, if you require further increase of energy system size
    #  Increase system size
    modesys.incr_esys_size_city(city=city, base_factor=3)

    # #  Uncomment, if you want to plot city district
    # #  Plot city district
    # citvis.plot_city_district(city=city, plot_lhn=True, plot_deg=True,
    #                           plot_esys=True)

    # User inputs
    #  ####################################################################
    nb_runs = 100  # Number of MC runs
    do_sampling = True  # Perform initial sampling or use existing samples

    sampling_method = 'lhc'
    #  Options: 'lhc' (latin hypercube) or 'random'

    dem_unc = True
    # dem_unc : bool, optional
    # Defines, if thermal, el. and dhw demand are assumed to be uncertain
    # (default: True). If True, samples demands. If False, uses reference
    # demands.

    failure_tolerance = 0.5
    #  Allowed share of runs, which fail with EnergyBalanceException.
    #  If failure_tolerance is exceeded, mc runner exception is raised.

    #  Defines, if pre-generated sample file should be loaded
    #  ##############################

    load_city_n_build_samples = True
    #  Defines, if city and building sample dictionaries should be loaded
    #  instead of generating new samples

    city_sample_name = 'kronen_6_resc_2_dict_city_samples.pkl'
    build_sample_name = 'kronen_6_resc_2_dict_build_samples.pkl'

    path_city_sample_dict = os.path.join(this_path,
                                         'input',
                                         'sample_dicts',
                                         city_sample_name)

    path_build_sample_dict = os.path.join(this_path,
                                          'input',
                                          'sample_dicts',
                                          build_sample_name)

    load_sh_mc_res = True
    #  If load_sh_mc_res is True, tries to load monte-carlo space heating
    #  uncertainty run results for each building from given folder
    #  If load_sh_mc_res is False, uses default value to sample sh demand
    #  uncertainty per building

    #  Path to FOLDER with mc sh results (searches for corresponding building
    #  ids)
    path_mc_res_folder = os.path.join(this_path,
                                      'input',
                                      'sh_mc_run')

    #  Generate el. and dhw profile pool to sample from (time consuming)
    use_profile_pool = True
    #  Only relevant, if sampling_method == 'lhc'
    random_profile = False
    #  Defines, if random samples should be used from profiles. If False,
    #  loops over given profiles (if enough profiles exist).

    gen_use_prof_method = 1
    #  Options:
    #  0: Generate new profiles during runtime
    #  1: Load pre-generated profile sample dictionary

    el_profile_dict = 'kronen_6_resc_2_dict_profile_20_samples.pkl'
    path_profile_dict = os.path.join(this_path,
                                     'input',
                                     'mc_el_profile_pool',
                                     el_profile_dict)

    heating_off = True
    #  Defines, if heating can be switched of during summer

    eeg_pv_limit = True
    use_kwkg_lhn_sub = False

    calc_th_el_cov = True

    el_mix_for_chp = True  # Use el. mix for CHP fed-in electricity
    el_mix_for_pv = True  # Use el. mix for PV fed-in electricity

    #  Output options
    #  ##############################

    #  Suppress print and warnings statements during MC-run
    prevent_printing = False

    #  Path to save results dict
    res_name = 'mc_run_results_dict.pkl'
    path_res = os.path.join(this_path, 'output', res_name)

    #  Path to sampling dict const
    sample_name_const = 'mc_run_sample_dict_const.pkl'
    path_sample_const = os.path.join(this_path, 'output', sample_name_const)

    #  Path to sampling dict esys
    sample_name_esys = 'mc_run_sample_dict_esys.pkl'
    path_sample_esys = os.path.join(this_path, 'output', sample_name_esys)

    #  Path to save mc settings to
    setup_name = 'mc_run_setup_dict.pkl'
    path_setup = os.path.join(this_path, 'output', setup_name)

    profiles_name = 'mc_run_profile_pool_dict.pkl'
    path_profiles = os.path.join(this_path, 'output', profiles_name)

    cov_dict_name = 'mc_cov_dict.pkl'
    path_mc_cov = os.path.join(this_path, 'output', cov_dict_name)

    #  #####################################################################
    #  Generate object instances
    #  #####################################################################

    start_time = time.time()

    #  Generate german market instance (if not already included in environment)
    ger_market = gmarket.GermanMarket()

    #  Add GermanMarket object instance to city
    city.environment.prices = ger_market

    #  Generate annuity object instance
    annuity_obj = annu.EconomicCalculation()

    #  Generate energy balance object for city
    energy_balance = citeb.CityEBCalculator(city=city)

    city_eco_calc = citecon.CityAnnuityCalc(annuity_obj=annuity_obj,
                                            energy_balance=energy_balance)

    #  Hand over initial city object to mc_runner
    mc_run = McRunner(city_eco_calc=city_eco_calc)

    #  Perform Monte-Carlo uncertainty analysis
    #  #####################################################################
    (dict_samples_const, dict_samples_esys, dict_res, dict_mc_setup,
     dict_profiles_lhc, dict_mc_cov) = \
        mc_run.run_mc_analysis(nb_runs=nb_runs,
                               failure_tolerance=failure_tolerance,
                               do_sampling=do_sampling,
                               prevent_printing=prevent_printing,
                               heating_off=heating_off,
                               sampling_method=sampling_method,
                               load_sh_mc_res=load_sh_mc_res,
                               path_mc_res_folder=path_mc_res_folder,
                               use_profile_pool=use_profile_pool,
                               gen_use_prof_method=gen_use_prof_method,
                               path_profile_dict=path_profile_dict,
                               random_profile=random_profile,
                               load_city_n_build_samples=
                               load_city_n_build_samples,
                               path_city_sample_dict=path_city_sample_dict,
                               path_build_sample_dict=path_build_sample_dict,
                               eeg_pv_limit=eeg_pv_limit,
                               use_kwkg_lhn_sub=use_kwkg_lhn_sub,
                               calc_th_el_cov=calc_th_el_cov,
                               dem_unc=dem_unc,
                               el_mix_for_chp=el_mix_for_chp,
                               el_mix_for_pv=el_mix_for_pv
                               )

    #  Perform reference run:
    #  #####################################################################
    (total_annuity, co2, sh_dem, el_dem, dhw_dem) = \
        mc_run.perform_ref_run(eeg_pv_limit=eeg_pv_limit,
                               use_kwkg_lhn_sub=use_kwkg_lhn_sub,
                               el_mix_for_chp=el_mix_for_chp,
                               el_mix_for_pv=el_mix_for_pv
                               )

    print()
    print('Total annualized cost in Euro/a of reference run:')
    print(round(total_annuity, 2))
    print('Total CO2 emissions in kg/a of reference run:')
    print(round(co2, 2))
    print()

    #  Evaluation
    #  #####################################################################
    pickle.dump(dict_res, open(path_res, mode='wb'))
    print('Saved results dict to: ', path_res)
    print()

    pickle.dump(dict_samples_const, open(path_sample_const, mode='wb'))
    print('Saved sample dict to: ', path_sample_const)
    print()

    pickle.dump(dict_samples_esys, open(path_sample_esys, mode='wb'))
    print('Saved sample dict to: ', path_sample_esys)
    print()

    pickle.dump(dict_mc_setup, open(path_setup, mode='wb'))
    print('Saved mc settings dict to: ', path_setup)
    print()

    if dict_profiles_lhc is not None:
        pickle.dump(dict_profiles_lhc, open(path_profiles, mode='wb'))
        print('Saved profiles dict to: ', path_profiles)
        print()

    if calc_th_el_cov and dict_mc_cov is not None:
        pickle.dump(dict_mc_cov, open(path_mc_cov, mode='wb'))
        print('Saved dict_mc_cov to: ', path_mc_cov)
        print()

    print('Nb. failed runs: ', str(len(dict_mc_setup['idx_failed_runs'])))
    print()

    print('Indexes of failed runs: ', str(dict_mc_setup['idx_failed_runs']))
    print()

    stop_time = time.time()
    time_delta = round(stop_time - start_time)

    print('Execution time for MC-Analysis (without city generation) in'
          ' seconds: ', time_delta)

    array_annuity = dict_res['annuity']
    array_co2 = dict_res['co2']
    array_sh = dict_res['sh_dem']

    plt.hist(array_annuity, bins='auto')
    plt.xlabel('Annuity in Euro/a')
    plt.ylabel('Number')
    plt.show()
    plt.close()

    plt.hist(array_co2, bins='auto')
    plt.xlabel('Emissions in kg/a')
    plt.ylabel('Number')
    plt.show()
    plt.close()

    plt.hist(array_sh, bins='auto')
    plt.xlabel('Space heating demand in kWh/a')
    plt.ylabel('Number')
    plt.show()
    plt.close()

if __name__ == '__main__':
    main()