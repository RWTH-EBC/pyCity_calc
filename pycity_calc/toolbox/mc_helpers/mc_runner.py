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
import numpy as np

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


# Disable printing
def block_print():
    sys.stdout = open(os.devnull, 'w')

# Restore printing
def enable_print():
    sys.stdout = sys.__stdout__
#  From https://stackoverflow.com/questions/8391411/suppress-calls-to-print-python


class McRunner(object):
    """
    Monte-carlo runner class. Holds CityAnnuityCalc object (city_eco_calc),
    which holds:
    - annuity_obj (Annuity calculation object) and
    - energy_balance (Energy balance object)
    City ojbect is stored on energy balance object
    """

    def __init__(self, city_eco_calc, get_build_ids=True):
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
        """

        self._city_eco_calc = city_eco_calc
        self._list_build_ids = None  # List with building node ids in city
        self._dict_samples = None  # List of samples

        if get_build_ids:
            #  Extract building node ids
            self._list_build_ids = self._city_eco_calc.energy_balance.city\
                .get_list_build_entity_node_ids()

    @staticmethod
    def perform_sampling_build(nb_runs, building):
        """
        Perform sampling for building object

        Parameters
        ----------
        nb_runs : int
            Number of runs
        building : object
            Building object of pyCity_calc

        Returns
        -------
        dict_build_samples : dict (of arrays and dicts)
            Dictionary storing building samples
            dict_build_samples['occ'] = array_occupants
            dict_build_samples['el_dem'] = array_el_dem
            dict_build_samples['dhw_dem'] = array_dhw_dem
            dict_build_samples['sh_dem'] = array_sh_dem
            dict_build_samples['on_off'] = array_sh_on_off
            dict_build_samples['esys'] = dict_esys
        """

        #  Initial dict
        dict_build_samples = {}

        #  Res. building type (sfh or mfh)
        if len(building.apartments) == 1:
            type = 'sfh'
        elif len(building.apartments) > 1:
            type = 'mfh'

        # Empty result arrays for apartment sampling
        array_occupants = np.zeros(nb_runs)
        array_el_dem = np.zeros(nb_runs)
        array_dhw_dem = np.zeros(nb_runs)

        #  Sample for apartments
        #  ################################################################
        for ap in building.apartments:

            #  Loop over nb. of samples
            for i in range(nb_runs):
                #  Sample occupants
                occ_p_app = usersample. \
                    calc_sampling_occ_per_app(nb_samples=1)[0]

                #  Sample el. demand per apartment (depending on nb. persons)
                el_per_app = usersample. \
                    calc_sampling_el_demand_per_apartment(nb_samples=1,
                                                          nb_persons=occ_p_app,
                                                          type=type)[0]

                #  Sample dhw demand per apartment (depending on nb. persons)
                dhw_per_app = usersample. \
                    calc_sampling_dhw_per_apartment(nb_samples=1,
                                                    nb_persons=occ_p_app,
                                                    b_type=type)

                #  Sum up values on building level
                array_occupants[i] += occ_p_app
                array_el_dem[i] += el_per_app
                array_dhw_dem[i] += dhw_per_app

        # Sample building attributes
        #  ################################################################
        #  Calculate space heating demand sample
        sh_ref = building.get_annual_space_heat_demand()  # in kWh

        array_sh_dem = buildsample.calc_sh_demand_samples(nb_samples=nb_runs,
                                                          sh_ref=sh_ref)

        array_sh_on_off = buildsample. \
            calc_sh_summer_on_off_samples(nb_samples=nb_runs)

        #  Save results to dict
        #  ################################################################
        dict_build_samples['occ'] = array_occupants
        dict_build_samples['el_dem'] = array_el_dem
        dict_build_samples['dhw_dem'] = array_dhw_dem
        dict_build_samples['sh_dem'] = array_sh_dem
        dict_build_samples['on_off'] = array_sh_on_off

        #  Sample energy system attributes
        #  ################################################################

        #  Check if building holds bes
        if building.hasBes:

            dict_esys = {}

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

                dict_esys['bat'] = dict_bat

            if building.bes.hasBoiler:
                dict_boi = {}

                dict_boi['eta_boi'] = \
                    esyssample.sample_boi_eff(nb_samples=nb_runs)

                dict_boi['boi_lifetime'] = \
                    esyssample.sample_lifetime(nb_samples=nb_runs)

                dict_boi['boi_maintain'] = \
                    esyssample.sample_maintain(nb_samples=nb_runs)

                dict_esys['boi'] = dict_boi

            if building.bes.hasChp:
                dict_chp = {}

                dict_chp['omega_chp'] = \
                    esyssample.sample_chp_omega(nb_samples=nb_runs)

                dict_chp['chp_lifetime'] = \
                    esyssample.sample_lifetime(nb_samples=nb_runs)

                dict_chp['chp_maintain'] = \
                    esyssample.sample_maintain(nb_samples=nb_runs)

                dict_esys['chp'] = dict_chp

            if building.bes.hasHeatpump:

                dict_hp = {}

                if building.bes.heatpump.hp_type == 'aw':

                    dict_hp['quality_grade'] = \
                        esyssample.sample_quality_grade_hp_aw(nb_samples=
                                                              nb_runs)

                elif building.bes.heatpump.hp_type == 'ww':

                    dict_hp['quality_grade'] = \
                        esyssample.sample_quality_grade_hp_bw(nb_samples=
                                                              nb_runs)

                dict_hp['hp_lifetime'] = \
                    esyssample.sample_lifetime(nb_samples=nb_runs)

                dict_hp['hp_maintain'] = \
                    esyssample.sample_maintain(nb_samples=nb_runs)

                dict_esys['hp'] = dict_hp

            if building.bes.hasPv:
                dict_pv = {}

                dict_pv['eta_pv'] = esyssample.sample_pv_eta(nb_samples=
                                                             nb_runs)
                dict_pv['beta'] = esyssample.sample_pv_beta(nb_samples=
                                                            nb_runs)
                dict_pv['gamma'] = esyssample.sample_pv_gamma(nb_samples=
                                                              nb_runs)

                dict_pv['hp_lifetime'] = \
                    esyssample.sample_lifetime(nb_samples=nb_runs)

                dict_pv['hp_maintain'] = \
                    esyssample.sample_maintain(nb_samples=nb_runs)

            if building.bes.hasTes:
                dict_tes = {}

                dict_tes['k_loss'] = esyssample.sample_tes_k_loss(nb_samples=
                                                                  nb_runs)

                dict_tes['hp_lifetime'] = \
                    esyssample.sample_lifetime(nb_samples=nb_runs)

                dict_tes['hp_maintain'] = \
                    esyssample.sample_maintain(nb_samples=nb_runs)

            dict_build_samples['esys'] = dict_esys

        return dict_build_samples

    @staticmethod
    def perform_sampling_city(nb_runs):
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

        #  Todo: Add options for sampling ranges and values

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

        return dict_city_samples

    def perform_sampling(self, nb_runs, save_samples=True):
        """
        Perform parameter sampling for Monte-Carlo analysis

        Parameters
        ----------
        nb_runs : int
            Number of runs
        save_samples : bool, optional
            Defines, if sampling results should be saved on MC results object
            (default: True)

        Returns
        -------
        dict_samples : dict (of dicts)
            Dictionary holding dictionaries with sample data for MC run
            dict_samples['city'] = dict_city_samples
        """

        #  Initial sample dict. Holds further sample dicts for
        #  'city' and each building node id
        dict_samples = {}

        #  Perform city sampling
        dict_city_samples = self.perform_sampling_city(nb_runs=nb_runs)
        dict_samples['city'] = dict_city_samples

        #  Perform building sampling
        #  Loop over node ids and add samples to result dict with building
        #  id as key
        for n in self._list_build_ids:
            build = self._city_eco_calc.energy_balance.city.node[n]['entity']
            dict_build_samples = \
                self.perform_sampling_build(nb_runs=nb_runs, building=build)

            dict_samples[str(n)] = dict_build_samples

        if save_samples:
            #  Save sampling dict to MC runner object
            self._dict_samples = dict_samples

        return dict_samples

    def perform_mc_runs(self, nb_runs):
        """
        Perform mc runs

        Parameters
        ----------
        nb_runs : int
            Number of runs

        Returns
        -------
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
        """

        dict_mc_res = {}

        #  Initial zero result arrays
        array_annuity = np.zeros(nb_runs)
        array_co2 = np.zeros(nb_runs)
        # array_net_sh = np.zeros(nb_runs)
        # array_net_el = np.zeros(nb_runs)
        # array_net_dhw = np.zeros(nb_runs)

        array_gas_boiler = np.zeros(nb_runs)
        array_gas_chp = np.zeros(nb_runs)
        array_grid_imp_dem = np.zeros(nb_runs)
        array_grid_imp_hp = np.zeros(nb_runs)
        array_grid_imp_eh = np.zeros(nb_runs)
        array_lhn_pump = np.zeros(nb_runs)
        array_grid_exp_chp = np.zeros(nb_runs)
        array_grid_exp_pv = np.zeros(nb_runs)

        #  Run energy balance and economic analysis
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


            #  Add building sample input data
            #  TODO: Add building sample data


            #  Extract city sampling data
            dict_city_samples = self._dict_samples['city']

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

            #  Save inputs to city, market and environment
            city.environment.temp_ground = dict_city_samples['temp_ground'][i]
            city.environment.prices.grid_av_fee = \
                dict_city_samples['grid_av_fee'][i]

            #  Save inputs to annuity_obj
            annuity_obj.interest = dict_city_samples['interest'][i]
            annuity_obj.price_ch_cap = dict_city_samples['ch_cap'][i]
            annuity_obj.price_ch_dem_gas = dict_city_samples['ch_dem_gas'][i]
            annuity_obj.price_ch_dem_el = dict_city_samples['ch_dem_el'][i]
            annuity_obj.price_ch_op = dict_city_samples['ch_op'][i]
            annuity_obj.price_ch_eeg_chp = dict_city_samples['ch_eeg_chp'][i]
            annuity_obj.price_ch_eeg_pv = dict_city_samples['ch_eeg_pv'][i]
            annuity_obj.price_ch_eex = dict_city_samples['ch_eex'][i]
            annuity_obj.price_ch_grid_use = dict_city_samples['ch_grid_use'][i]

            #  Save inputs to energy_balance


            #  Save inputs to city_economic_calculator



            #  Run energy balance and annuity calculation
            #  ###############################################################
            (total_annuity, co2) = c_eco_copy. \
                perform_overall_energy_balance_and_economic_calc()

            # #  Extract further results
            # sh_dem = c_eco_copy.energy_balance. \
            #     city.get_annual_space_heating_demand()
            # el_dem = c_eco_copy.energy_balance. \
            #     city.get_annual_el_demand()
            # dhw_dem = c_eco_copy.energy_balance. \
            #     city.get_annual_dhw_demand()

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
            # array_net_sh[i] = sh_dem
            # array_net_el[i] = el_dem
            # array_net_dhw[i] = dhw_dem

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
            # dict_mc_res['sh_dem'] = array_net_sh
            # dict_mc_res['el_dem'] = array_net_el
            # dict_mc_res['dhw_dem'] = array_net_dhw
            dict_mc_res['gas_boiler'] = array_gas_boiler
            dict_mc_res['gas_chp'] = array_gas_chp
            dict_mc_res['grid_imp_dem'] = array_grid_imp_dem
            dict_mc_res['grid_imp_hp'] = array_grid_imp_hp
            dict_mc_res['grid_imp_eh'] = array_grid_imp_eh
            dict_mc_res['lhn_pump'] = array_lhn_pump
            dict_mc_res['grid_exp_chp'] = array_grid_exp_chp
            dict_mc_res['grid_exp_pv'] = array_grid_exp_pv

        return dict_mc_res

    def run_mc_analysis(self, nb_runs, do_sampling=False,
                        prevent_printing=False):
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
        do_sampling : bool, optional
            Defines, if sampling should be performed or existing samples
            should be used (default: False)
        prevent_printing : bool, optional
            Defines, if printing statements should be suppressed

        Returns
        -------
        dict_mc_res : dict
            Dictionary holding Monte-Carlo run results
        """

        if nb_runs <= 0:
            msg = 'nb_runs has to be larger than zero!'
            raise AssertionError(msg)

        if do_sampling:
            #  Call sampling and save sample data to _dict_samples
            self.perform_sampling(nb_runs=nb_runs)

        if prevent_printing:
            block_print()

        # Perform monte-carlo runs
        dict_mc_res = self.perform_mc_runs(nb_runs=nb_runs)

        if prevent_printing:
            enable_print()

        return dict_mc_res

if __name__ == '__main__':

    #  Generate city district or load city district


    #  Dimension energy systems, if not already included

    this_path = os.path.dirname(os.path.abspath(__file__))

    try:
        #  Try loading city pickle file
        filename = 'city_clust_simple_with_esys.pkl'
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

        city.node[1005]['entity'].bes.boiler.qNominal *= 10
        city.node[1005]['entity'].bes.tes.capacity *= 10
        city.node[1012]['entity'].bes.boiler.qNominal *= 10
        city.node[1012]['entity'].bes.tes.capacity *= 10
        city.node[1009]['entity'].bes.electricalHeater.qNominal *= 10

        # Save new pickle file
        filename = 'city_clust_simple_with_esys.pkl'
        file_path = os.path.join(this_path, 'input', filename)
        pickle.dump(city, open(file_path, mode='wb'))

    #  User inputs
    #  ####################################################################
    nb_runs = 2
    do_sampling = True

    #  Suppress print and warnings statements during MC-run
    prevent_printing = False

    # #####################################################################
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

    dict_res = mc_run.run_mc_analysis(nb_runs=nb_runs, do_sampling=do_sampling,
                                      prevent_printing=prevent_printing)

    stop_time = time.time()

    time_delta = round(stop_time - start_time)

    print('Execution time for MC-Analysis (without city generation) in'
          ' seconds: ', time_delta)
