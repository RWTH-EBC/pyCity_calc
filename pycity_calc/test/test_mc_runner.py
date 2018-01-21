#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to test mc_runner.py McRunner class
"""
from __future__ import division

import os

import pycity_calc.toolbox.mc_helpers.mc_runner as mcrun
import pycity_calc.toolbox.modifiers.mod_city_esys_size as modesys
import pycity_calc.economic.city_economic_calc as citecon
import pycity_calc.environments.germanmarket as gmarket
import pycity_calc.simulation.energy_balance.city_eb_calc as citeb
import pycity_calc.economic.annuity_calculation as annu
import pycity_calc.cities.scripts.city_generator.city_generator as citygen
import pycity_calc.cities.scripts.overall_gen_and_dimensioning as overall


class TestMcRunner():
    def test_perform_mc_run(self):
        this_path = os.path.dirname(os.path.abspath(__file__))

        #  # Userinputs
        #  #----------------------------------------------------------------------

        #  Generate environment
        #  ######################################################
        year = 2017
        timestep = 900  # Timestep in seconds
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
        th_gen_method = 1
        #  For non-residential buildings, SLPs are generated automatically.

        #  Manipulate thermal slp to fit to space heating demand?
        slp_manipulate = True
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
        el_gen_method = 1
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
        dhw_method = 1  # Only relevant for residential buildings

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
        filename = 'city_clust_simple_no_deg.txt'

        txt_path = os.path.join(this_path, 'input_generator', filename)

        #  #####################################
        t_set_heat = 20  # Heating set temperature in degree Celsius
        t_set_night = 16  # Night set back temperature in degree Celsius
        t_set_cool = 70  # Cooling set temperature in degree Celsius

        #  Air exchange rate (required for th_gen_method = 3 (VDI 6007 sim.))
        air_vent_mode = 0
        #  int; Define mode for air ventilation rate generation
        #  0 : Use constant value (vent_factor in 1/h)
        #  1 : Use deterministic, temperature-dependent profile
        #  2 : Use stochastic, user-dependent profile
        #  False: Use static ventilation rate value

        vent_factor = 0.3  # Constant. ventilation rate
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
        log_path = os.path.join(this_path, 'input_generator',
                                'city_gen_overall_log.txt')

        #  Generate street networks
        gen_str = True  # True - Generate street network

        #  Street node and edges input filenames
        str_node_filename = 'street_nodes_cluster_simple.csv'
        str_edge_filename = 'street_edges_cluster_simple.csv'

        #  Load street data from csv
        str_node_path = os.path.join(this_path, 'input_generator',
                                     str_node_filename)
        str_edge_path = os.path.join(this_path, 'input_generator',
                                     str_edge_filename)

        #  Add energy networks to city
        gen_e_net = True  # True - Generate energy networks

        #  Path to energy network input file (csv/txt; tab separated)
        network_filename = 'city_clust_simple_networks_no_deg.txt'
        network_path = os.path.join(this_path, 'input_generator',
                                    network_filename)

        #  Add energy systems to city
        gen_esys = True  # True - Generate energy networks

        #  Path to energy system input file (csv/txt; tab separated)
        esys_filename = 'city_clust_simple_enersys_no_deg.txt'
        esys_path = os.path.join(this_path, 'input_generator',
                                 esys_filename)

        #  #----------------------------------------------------------------------

        #  Load district_data file
        district_data = citygen.get_district_data_from_txt(txt_path)

        city = overall.run_overall_gen_and_dim(timestep=timestep,
                                               year_timer=year,
                                               year_co2=year,
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
                                               save_path=None,
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

        #  Increase system size (to prevent running into
        #  EnergyBalanceExceptions during testing)
        modesys.incr_esys_size_city(city=city,  base_factor=10, tes_factor=4)

        #  Generate german market instance
        #  (if not already included in environment)
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
        mc_run = mcrun.McRunner(city_eco_calc=city_eco_calc)

        #  Perform Monte-Carlo uncertainty analysis
        #  Allow max. failure tolerance to prevent errors during mc run
        mc_run.run_mc_analysis(nb_runs=2,
                               failure_tolerance=1,
                               do_sampling=True,
                               prevent_printing=False,
                               sampling_method='random')
