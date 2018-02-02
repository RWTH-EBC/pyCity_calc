#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division

import os
import copy

import networkx as nx
import shapely.geometry.point as point
import shapely.geometry.linestring as lstr

import pycity_calc.toolbox.networks.intersection as intersec
import pycity_calc.toolbox.networks.network_ops as netop
import pycity_calc.cities.city as cit
import pycity_calc.toolbox.dimensioning.dim_networks as dimnet
import pycity_calc.cities.scripts.city_generator.city_generator as citygen
import pycity_calc.cities.scripts.overall_gen_and_dimensioning as overall

import pycity_calc.energysystems.heatPumpSimple as hp

import pycity_calc.toolbox.dimensioning.emp_approach.dim_empirical_approach as emp
import pycity_calc.toolbox.dimensioning.emp_approach.dim_devices as dev

from pycity_calc.test.pycity_calc_fixtures import fixture_building, \
    fixture_environment, fixture_city, fixture_apartment, fixture_th_demand, \
    fixture_el_demand

class empirical_approach():
    def test_run_approach(self):
        """
        Generate city district and perform eligibility checks
        """

        this_path = os.path.dirname(os.path.abspath(__file__))

        #  Check requirements for pycity_deap
        pycity_deap = False

        #  # Userinputs
        #  #----------------------------------------------------------------------

        #  Generate environment
        #  ######################################################
        year_timer = 2010
        year_co2 = 2010
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

        timestep = city.environment.timer.timeDiscretization

        ########################################

        # eligibility check 1
        elig_wld = emp.get_eligibility_dhn(city=city, method=0)
        assert elig_wld >= 0
        assert elig_wld <= 4

        # eligibility check 2
        elig_ekw = emp.get_eligibility_dhn(city=city, method=1)
        assert elig_ekw > 0
        assert elig_ekw <= 5

        # age_check
        b_age = emp.get_building_age(city)
        assert b_age is 'new' or b_age is 'old'

        # check net length
        net_len = emp.get_net_len(city)
        assert net_len >= 0

        # check district type
        d_type = emp.get_district_type(city)
        assert d_type in ['big','medium','small']

        # check eta transmission
        eta_trm = emp.get_eta_transmission(d_type)
        assert eta_trm >= 0.5
        assert eta_trm <= 1

        # check area and inhabitants
        area_total = 0
        people_total = 0


        for b_node in city.nodelist_building:

            building = city.nodes[b_node]['entity']
            area_total += building.net_floor_area

            for ap in building.apartments:
                people_total += ap.occupancy.number_occupants

        assert area_total > 0
        assert people_total > 0

        ### Test HeatPump functions ###

        build = copy.deepcopy(fixture_building)

        heatpump = hp.heatPumpSimple(environment=build.environment,
                                     q_nominal=6000)

        # Calculate Seasonal Performance Factor
        spf = emp.calc_hp_spf(heatPump=heatpump,
                              environment=build.environment,
                              sh_curve=build.get_space_heating_power_curve())

        assert 0 < spf < 10

        # test emissions calculation
        assert emp.calc_emissions(q_gas=[0, 0, 0], w_el=[0, 0]) == 0
        assert emp.calc_emissions(q_gas=[100, 50], w_el=[0, 0]) > 0
        assert emp.calc_emissions(q_gas=[0, 0], w_el=[100, 50]) > 0



    def test_dim_devices(self):
        """

        """
        # test LDC
        assert dev.get_LDC([0, 2, 1]) == [2, 1, 0]

        # test t_demand_list
        th_curve = [0, 1, 2, 3, 4, 5]
        temp_outside = [10, 9, 8, 7, 6]
        t_dem_sort = [th_demand for _, th_demand in sorted(zip(temp_outside,th_curve))]
        assert t_dem_sort == [5, 4, 3, 2, 1]

        # test chp_ann_op
        th_LDC = [25, 20, 15, 10, 5, 0]
        q_nom = 10
        assert dev.get_chp_ann_op_time(q_nom, th_LDC) == (4, 3)

        # test choose hp
        # method 0 for air/water
        q_ideal_hp = 10
        best_q, best_cop_list, tMax, tSink = dev.choose_hp(q_ideal=q_ideal_hp, t_biv=-2, method=0, hp_type='aw', t_ground=10)
        assert best_q == q_ideal_hp
        for cop in best_cop_list:
            assert cop > 2
        assert 35 < tMax < 90
        assert 20 < tSink < 70
        # method 0 for brine/water
        best_q, best_cop_list, tMax, tSink = dev.choose_hp(q_ideal=q_ideal_hp, t_biv=-2, method=0, hp_type='ww',
                                                           t_ground=10)
        assert best_q == q_ideal_hp
        for cop in best_cop_list:
            assert cop > 4
        assert 35 < tMax < 90
        assert 20 < tSink < 70

        # method 1 for air/water
        q_ideal_hp = 10
        best_q, best_cop_list, tMax, tSink = dev.choose_hp(q_ideal=q_ideal_hp, t_biv=-2, method=1, hp_type='aw',
                                                           t_ground=10)
        assert best_q == q_ideal_hp
        for cop in best_cop_list:
            assert cop > 2
        assert 35 < tMax < 90
        assert 20 < tSink < 70
        # method 0 for brine/water
        best_q, best_cop_list, tMax, tSink = dev.choose_hp(q_ideal=q_ideal_hp, t_biv=-2, method=1, hp_type='ww',
                                                           t_ground=10)
        assert best_q == q_ideal_hp
        for cop in best_cop_list:
            assert cop > 4
        assert 35 < tMax < 90
        assert 20 < tSink < 70

        # test choose chp
        # method 0
        q_ideal = 10
        (eta_el, eta_th, p_nom, q_nom) = dev.choose_chp(q_ideal, method=0)
        assert q_nom == q_ideal
        assert 0 < eta_el < 1
        assert 0 < eta_th < 1
        assert 0 < p_nom
        # method 1
        q_ideal = 10
        (eta_el, eta_th, p_nom, q_nom) = dev.choose_chp(q_ideal, method=1)
        assert 0 < q_nom
        assert 0 < eta_el < 1
        assert 0 < eta_th < 1
        assert 0 < p_nom

        # test el. feedin tariff
        q_nom0 = 0
        q_nom1 = 80
        q_nom2 = 200
        q_nom3 = 1000
        q_nom4 = 3000
        t0 = dev.get_el_feedin_tariff_chp(q_nom0, el_feedin_epex=0.02978, vnn=0.01)
        t1 = dev.get_el_feedin_tariff_chp(q_nom1, el_feedin_epex=0.02978, vnn=0.01)
        t2 = dev.get_el_feedin_tariff_chp(q_nom2, el_feedin_epex=0.02978, vnn=0.01)
        t3 = dev.get_el_feedin_tariff_chp(q_nom3, el_feedin_epex=0.02978, vnn=0.01)
        t4 = dev.get_el_feedin_tariff_chp(q_nom4, el_feedin_epex=0.02978, vnn=0.01)
        assert t4 > 0
        assert t4 < t3 < t2 < t1 < t0

        # test minichp subsidy
        assert dev.get_subs_minichp(p_nom=5, q_nom=10, v_tes=0) == 0
        assert dev.get_subs_minichp(p_nom=5, q_nom=10, v_tes=700) > 0
        assert dev.get_subs_minichp(p_nom=0.5, q_nom=1, v_tes=61) > 0
        assert dev.get_subs_minichp(p_nom=0.5, q_nom=1, v_tes=10) == 0

        # test kwkg tes subsidy
        assert dev.get_subs_tes_chp(chp_ratio=0.4, v_tes=700, tes_invest=1000, p_nom=5) == 0
        assert dev.get_subs_tes_chp(chp_ratio=0.5, v_tes=50, tes_invest=1000, p_nom=5) == 0
        assert dev.get_subs_tes_chp(chp_ratio=0.5, v_tes=5000, tes_invest=1000, p_nom=5) > 0

        # test hp bafa subsidy
        assert dev.get_bafa_subs_hp(q_nom=20, spf=2) == 0
        assert dev.get_bafa_subs_hp(q_nom=20, spf=5) == 1950
        assert dev.get_bafa_subs_hp(q_nom=40, spf=5) == 2400
        assert dev.get_bafa_subs_hp(q_nom=20, spf=4) == 1300
        assert dev.get_bafa_subs_hp(q_nom=40, spf=4) == 1600

