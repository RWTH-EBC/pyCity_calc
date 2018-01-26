#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for city energy balance calculation
"""
from __future__ import division

import os
import copy
import numpy as np
import shapely.geometry.point as point

import pycity_base.classes.supply.BES as BES
import pycity_base.classes.supply.PV as PV
import pycity_base.classes.demand.Apartment as Apartment

import pycity_calc.buildings.building as build
import pycity_calc.simulation.energy_balance.building_eb_calc as buildeb
import pycity_calc.simulation.energy_balance.city_eb_calc as cityeb
import pycity_calc.energysystems.chp as chpsys
import pycity_calc.energysystems.battery as bat
import pycity_calc.energysystems.boiler as boil
import pycity_calc.energysystems.electricalHeater as ehsys
import pycity_calc.energysystems.heatPumpSimple as hpsys
import pycity_calc.energysystems.thermalEnergyStorage as sto
import pycity_calc.energysystems.Input.chp_asue_2015 as asue
import pycity_calc.cities.scripts.city_generator.city_generator as citygen
import pycity_calc.cities.scripts.overall_gen_and_dimensioning as overall
import pycity_calc.toolbox.dimensioning.dim_networks as dimnet

from pycity_calc.test.pycity_calc_fixtures import fixture_building, \
    fixture_environment, fixture_city, fixture_apartment, fixture_th_demand, \
    fixture_el_demand


class TestCityEnergyBalance():
    def test_city_eb_calc(self):
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

        #  ##################################################################

        id = 1005
        exbuild = city.nodes[id]['entity']
        exbuild.bes.boiler.qNominal *= 10
        exbuild.bes.tes.capacity *= 1
        #  Comment: Rescaling is necessary, as dhw_method = 1 is used.
        #  This leads to dhw peaks for all buildings at the same timesteps

        id = 1006
        exbuild = city.nodes[id]['entity']
        exbuild.bes.boiler.qNominal *= 10
        exbuild.bes.tes.capacity *= 1
        #  Comment: Rescaling is necessary, as dhw_method = 1 is used.
        #  This leads to dhw peaks for all buildings at the same timesteps

        id = 1012
        exbuild = city.nodes[id]['entity']
        exbuild.bes.boiler.qNominal *= 10
        exbuild.bes.tes.capacity *= 1

        #  Run city energy balance test
        energy_balance = cityeb.CityEBCalculator(city=city)

        #  Calc. city energy balance
        energy_balance.calc_city_energy_balance()

        #  Calc. final energy balance
        energy_balance.calc_final_energy_balance_city()

        #  Calc. co2 emissions
        energy_balance.calc_co2_emissions()

        #  ##################################################################

    def test_city_eb_with_chp_boiler_lhn(self, fixture_city):
        """
        Check city energy balance for city with two buildings,
        """

        city = copy.deepcopy(fixture_city)

        building_1 = build.BuildingExtended(environment=city.environment)
        building_2 = build.BuildingExtended(environment=city.environment)

        apart1 = Apartment.Apartment(environment=city.environment)
        apart2 = Apartment.Apartment(environment=city.environment)

        building_1.addEntity(apart1)
        building_2.addEntity(apart2)

        timestep = city.environment.timer.timeDiscretization
        nb_timesteps = 365 * 24 * 3600 / timestep

        sh_1 = np.ones(int(nb_timesteps)) * 6000
        sh_2 = np.ones(int(nb_timesteps)) * 6000
        el_1 = np.zeros(int(nb_timesteps))
        el_2 = np.zeros(int(nb_timesteps))

        building_1.apartments[0].demandSpaceheating.loadcurve = sh_1
        building_2.apartments[0].demandSpaceheating.loadcurve = sh_2

        building_1.apartments[0].power_el.loadcurve = el_1
        building_2.apartments[0].power_el.loadcurve = el_2

        q_nom = 10000
        eta_total = 1

        p_nom = asue.calc_el_power_with_th_power(th_power=q_nom,
                                                 eta_total=eta_total)

        chp = chpsys.ChpExtended(environment=city.environment,
                                 q_nominal=q_nom,
                                 p_nominal=p_nom,
                                 eta_total=eta_total)

        boiler = boil.BoilerExtended(environment=city.environment,
                                     q_nominal=10000, eta=1)

        #  Add small tes to prevent start-check assertion error
        tes = sto.thermalEnergyStorageExtended(environment=city.environment,
                                               capacity=0.1, k_loss=0,
                                               t_init=80)

        bes = BES.BES(environment=city.environment)

        bes.addDevice(chp)
        bes.addDevice(boiler)
        bes.addDevice(tes)

        building_1.addEntity(bes)

        city.add_extended_building(extended_building=building_1,
                                   position=point.Point(0, 0))
        city.add_extended_building(extended_building=building_2,
                                   position=point.Point(50, 0))

        dimnet.add_lhn_to_city(city=city)

        city.environment.temp_ground = 10

        #  Set inlet-flow and return-flow temperatures to environment
        #  temperatures to eliminate losses of LHN system
        city.edges[1001, 1002]['temp_vl'] = 10
        city.edges[1001, 1002]['temp_rl'] = 9.999999999999

        #  Calculate city energy balance
        city_eb = cityeb.CityEBCalculator(city=city)

        city_eb.calc_city_energy_balance()

        sh_dem_1 = building_1.get_annual_space_heat_demand()
        sh_dem_2 = building_2.get_annual_space_heat_demand()
        el_dem_1 = building_1.get_annual_el_demand()

        assert el_dem_1 <= 0.001

        #  CHP
        q_chp_out = building_1.bes.chp.totalQOutput
        p_el_chp_out = building_1.bes.chp.totalPOutput
        fuel_chp_in = building_1.bes.chp.array_fuel_power

        chp_th_energy = sum(q_chp_out) * timestep / (1000 * 3600)  # in kWh
        fuel_chp_energy = sum(fuel_chp_in) * timestep / (1000 * 3600)  # in kWh
        chp_el_energy = sum(p_el_chp_out) * timestep / (1000 * 3600)  # in kWh

        #  Boiler
        q_boiler = building_1.bes.boiler.totalQOutput
        sum_q_boiler = sum(q_boiler) * timestep / (1000 * 3600)  # in kWh

        fuel_in = building_1.bes.boiler.array_fuel_power
        fuel_boiler_energy = sum(fuel_in) * timestep / (1000 * 3600)  # in kWh

        chp_self_dem = building_1.dict_el_eb_res['chp_self_dem']
        chp_feed = building_1.dict_el_eb_res['chp_feed']

        sum_chp_self_dem = sum(chp_self_dem) * timestep / (1000 * 3600)
        sum_chp_feed = sum(chp_feed) * timestep / (1000 * 3600)

        assert abs(sum_q_boiler - fuel_boiler_energy) <= 0.001

        assert abs(chp_th_energy + chp_el_energy - fuel_chp_energy) <= 0.001

        assert chp_el_energy > 0
        assert sum_chp_self_dem <= 0.001
        assert sum_chp_feed > 0

        #  Check thermal net energy balance
        assert abs(sh_dem_1 + sh_dem_2
                   - (sum_q_boiler + chp_th_energy)) <= 0.01

        #  Electric energy balance
        assert abs(sum_chp_feed - chp_el_energy) <= 0.001

        #  Check fuel thermal energy balance
        assert abs(sh_dem_1 + sh_dem_2 + sum_chp_feed
                   - (fuel_boiler_energy + fuel_chp_energy)) <= 0.01

        #  Check if pump energy is required for LHN usage
        assert max(city_eb.list_pump_energy) > 0

    def test_city_lhn_eb_with_feeders_only(self, fixture_city):
        """
        Check city energy balance with LHN and feeder nodes, only
        """

        city = copy.deepcopy(fixture_city)

        building_1 = build.BuildingExtended(environment=city.environment)
        building_2 = build.BuildingExtended(environment=city.environment)

        apart1 = Apartment.Apartment(environment=city.environment)
        apart2 = Apartment.Apartment(environment=city.environment)

        building_1.addEntity(apart1)
        building_2.addEntity(apart2)

        timestep = city.environment.timer.timeDiscretization
        nb_timesteps = 365 * 24 * 3600 / timestep

        sh_1 = np.ones(int(nb_timesteps)) * 6000
        sh_2 = np.ones(int(nb_timesteps)) * 6000
        el_1 = np.zeros(int(nb_timesteps))
        el_2 = np.zeros(int(nb_timesteps))

        building_1.apartments[0].demandSpaceheating.loadcurve = sh_1
        building_2.apartments[0].demandSpaceheating.loadcurve = sh_2

        building_1.apartments[0].power_el.loadcurve = el_1
        building_2.apartments[0].power_el.loadcurve = el_2

        q_nom = 2000
        eta_total = 1

        p_nom = asue.calc_el_power_with_th_power(th_power=q_nom,
                                                 eta_total=eta_total)

        chp = chpsys.ChpExtended(environment=city.environment,
                                 q_nominal=q_nom,
                                 p_nominal=p_nom,
                                 eta_total=eta_total)

        boiler = boil.BoilerExtended(environment=city.environment,
                                     q_nominal=10000, eta=1)

        boiler2 = boil.BoilerExtended(environment=city.environment,
                                     q_nominal=6000, eta=1)

        #  Add small tes to prevent start-check assertion error
        tes = sto.thermalEnergyStorageExtended(environment=city.environment,
                                               capacity=0.01, k_loss=0,
                                               t_init=80)

        tes2 = copy.deepcopy(tes)

        bes = BES.BES(environment=city.environment)
        bes.addDevice(chp)
        bes.addDevice(boiler)
        bes.addDevice(tes)

        bes2 = BES.BES(environment=city.environment)
        bes2.addDevice(boiler2)
        bes2.addDevice(tes2)

        building_1.addEntity(bes)
        building_2.addEntity(bes2)

        city.add_extended_building(extended_building=building_1,
                                   position=point.Point(0, 0))
        city.add_extended_building(extended_building=building_2,
                                   position=point.Point(50, 0))

        dimnet.add_lhn_to_city(city=city)

        city.environment.temp_ground = 10

        #  Calculate city energy balance
        city_eb = cityeb.CityEBCalculator(city=city)

        city_eb.calc_city_energy_balance()

        sh_dem_1 = building_1.get_annual_space_heat_demand()
        sh_dem_2 = building_2.get_annual_space_heat_demand()
        el_dem_1 = building_1.get_annual_el_demand()

        assert el_dem_1 <= 0.001

        #  CHP
        q_chp_out = building_1.bes.chp.totalQOutput
        p_el_chp_out = building_1.bes.chp.totalPOutput
        fuel_chp_in = building_1.bes.chp.array_fuel_power

        chp_th_energy = sum(q_chp_out) * timestep / (1000 * 3600)  # in kWh
        fuel_chp_energy = sum(fuel_chp_in) * timestep / (1000 * 3600)  # in kWh
        chp_el_energy = sum(p_el_chp_out) * timestep / (1000 * 3600)  # in kWh

        #  Boiler1
        q_boiler = building_1.bes.boiler.totalQOutput
        sum_q_boiler = sum(q_boiler) * timestep / (1000 * 3600)  # in kWh

        fuel_in = building_1.bes.boiler.array_fuel_power
        fuel_boiler_energy = sum(fuel_in) * timestep / (1000 * 3600)  # in kWh

        #  Boiler2
        q_boiler2 = building_2.bes.boiler.totalQOutput
        sum_q_boiler2 = sum(q_boiler2) * timestep / (1000 * 3600)  # in kWh

        fuel_in2 = building_2.bes.boiler.array_fuel_power
        fuel_boiler_energy2 = sum(fuel_in2) * timestep / (1000 * 3600)  # in kWh

        chp_self_dem = building_1.dict_el_eb_res['chp_self_dem']
        chp_feed = building_1.dict_el_eb_res['chp_feed']

        sum_chp_self_dem = sum(chp_self_dem) * timestep / (1000 * 3600)
        sum_chp_feed = sum(chp_feed) * timestep / (1000 * 3600)

        assert abs(sum_q_boiler - fuel_boiler_energy) <= 0.001

        assert abs(chp_th_energy + chp_el_energy - fuel_chp_energy) <= 0.001

        assert chp_el_energy > 0
        assert sum_chp_self_dem <= 0.001
        assert sum_chp_feed > 0

        #  Check thermal net energy balance
        assert abs(sh_dem_1 + sh_dem_2
                   - (sum_q_boiler + sum_q_boiler2 + chp_th_energy)) <= 0.001

        #  Electric energy balance
        assert abs(sum_chp_feed - chp_el_energy) <= 0.001

        #  Check fuel thermal energy balance
        assert abs(sh_dem_1 + sh_dem_2 + sum_chp_feed
                   - (fuel_boiler_energy+ fuel_boiler_energy2
                      + fuel_chp_energy)) <= 0.001

    def test_city_eb_calc_lhn_multi_feeders(self):
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
        filename = 'city_3_build.txt'

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
        gen_str = False  # True - Generate street network

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
        network_filename = 'city_3_build_networks_no_deg.txt'
        network_path = os.path.join(this_path, 'input_generator',
                                    network_filename)

        #  Add energy systems to city
        gen_esys = True  # True - Generate energy networks

        #  Path to energy system input file (csv/txt; tab separated)
        esys_filename = 'city_3_build_enersys_no_deg.txt'
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

        #  ##################################################################

        # id = 1001
        # exbuild = city.nodes[id]['entity']
        # exbuild.bes.boiler.qNominal *= 2
        # exbuild.bes.tes.capacity *= 1
        # #  Comment: Rescaling is necessary, as dhw_method = 1 is used.
        # #  This leads to dhw peaks for all buildings at the same timesteps
        #
        # id = 1002
        # exbuild = city.nodes[id]['entity']
        # exbuild.bes.boiler.qNominal *= 2
        # exbuild.bes.tes.capacity *= 1
        # #  Comment: Rescaling is necessary, as dhw_method = 1 is used.
        # #  This leads to dhw peaks for all buildings at the same timesteps

        #  Run city energy balance test
        energy_balance = cityeb.CityEBCalculator(city=city)

        #  Calc. city energy balance
        energy_balance.calc_city_energy_balance()

        #  Calc. final energy balance
        energy_balance.calc_final_energy_balance_city()

        #  Calc. co2 emissions
        energy_balance.calc_co2_emissions()

        #  ##################################################################
