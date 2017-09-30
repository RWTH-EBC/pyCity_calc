#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

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


class TestBuildingEnergyBalance():
    def test_building_eb_calc(self):
        """
        Generate city district and perform logic checks for thermal and
        electric energy balances
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
        filename = 'city_clust_simple_eb.txt'

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
        network_filename = 'city_clust_simple_networks.txt'
        network_path = os.path.join(this_path, 'input_generator',
                                    network_filename)

        #  Add energy systems to city
        gen_esys = True  # True - Generate energy networks

        #  Path to energy system input file (csv/txt; tab separated)
        esys_filename = 'city_clust_simple_enersys.txt'
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

        #  ##################################################################
        #  Get buiding 1007 (boiler, only)
        #  Add EH to test energy balance for boiler and eh without tes
        id = 1007
        exbuild = city.node[id]['entity']

        #  Calculate thermal energy balance
        buildeb.calc_build_therm_eb(build=exbuild, id=id)

        #  Calculate electric energy balance
        buildeb.calc_build_el_eb(build=exbuild)

        q_out = exbuild.bes.boiler.totalQOutput
        fuel_in = exbuild.bes.boiler.array_fuel_power
        sh_p_array = exbuild.get_space_heating_power_curve()
        dhw_p_array = exbuild.get_dhw_power_curve()

        sh_net_energy = sum(sh_p_array) * timestep / (1000 * 3600)  # in kWh
        dhw_net_energy = sum(dhw_p_array) * timestep / (1000 * 3600)  # in kWh
        boil_th_energy = sum(q_out) * timestep / (1000 * 3600)  # in kWh
        fuel_boiler_energy = sum(fuel_in) * timestep / (1000 * 3600)  # in kWh

        assert fuel_boiler_energy >= boil_th_energy
        assert abs(boil_th_energy - (sh_net_energy + dhw_net_energy)) <= 0.001

        #  ##################################################################

        #  ##################################################################
        #  Get buiding 1001 (CHP, boiler, tes)
        #  Add EH to test energy balance for CHP, boiler, EH with TES
        id = 1001
        exbuild = city.node[id]['entity']

        # eh = elheat.ElectricalHeaterExtended(environment=exbuild.environment,
        #                                      q_nominal=10000)
        #
        # exbuild.bes.addDevice(eh)

        #  Calculate thermal energy balance
        buildeb.calc_build_therm_eb(build=exbuild, id=id)

        #  Calculate electric energy balance
        buildeb.calc_build_el_eb(build=exbuild)

        #  Get space heating results
        sh_p_array = exbuild.get_space_heating_power_curve()
        dhw_p_array = exbuild.get_dhw_power_curve()

        #  Get boiler results
        q_out = exbuild.bes.boiler.totalQOutput
        fuel_in = exbuild.bes.boiler.array_fuel_power

        #  Get CHP results
        q_chp_out = exbuild.bes.chp.totalQOutput
        p_el_chp_out = exbuild.bes.chp.totalPOutput
        fuel_chp_in = exbuild.bes.chp.array_fuel_power

        tes_temp = exbuild.bes.tes.array_temp_storage

        #  Checks
        sh_net_energy = sum(sh_p_array) * timestep / (1000 * 3600)  # in kWh
        dhw_net_energy = sum(dhw_p_array) * timestep / (1000 * 3600)  # in kWh
        boil_th_energy = sum(q_out) * timestep / (1000 * 3600)  # in kWh
        chp_th_energy = sum(q_chp_out) * timestep / (1000 * 3600)  # in kWh
        fuel_boiler_energy = sum(fuel_in) * timestep / (1000 * 3600)  # in kWh
        fuel_chp_energy = sum(fuel_chp_in) * timestep / (1000 * 3600)  # in kWh
        chp_el_energy = sum(p_el_chp_out) * timestep / (1000 * 3600)  # in kWh

        assert sh_net_energy + dhw_net_energy <= boil_th_energy + chp_th_energy
        assert fuel_chp_energy >= chp_th_energy + chp_el_energy
        assert boil_th_energy <= fuel_boiler_energy

        #  ##################################################################

        # #  ################################################################
        #  Extract building 1008 (HP, EH, PV and TES)
        id = 1008
        exbuild = city.node[id]['entity']

        #  Modify size of electrical heater
        exbuild.bes.electricalHeater.qNominal *= 1.5

        #  Modify tes
        exbuild.bes.tes.tMax = 45
        print('Capacity of TES in kg: ', exbuild.bes.tes.capacity)

        #  Calculate thermal energy balance
        buildeb.calc_build_therm_eb(build=exbuild, id=id)

        #  Calculate electric energy balance
        buildeb.calc_build_el_eb(build=exbuild)

        #  Get space heating results
        sh_p_array = exbuild.get_space_heating_power_curve()
        dhw_p_array = exbuild.get_dhw_power_curve()

        q_hp_out = exbuild.bes.heatpump.totalQOutput
        el_hp_in = exbuild.bes.heatpump.array_el_power_in

        q_eh_out = exbuild.bes.electricalHeater.totalQOutput
        el_eh_in = exbuild.bes.electricalHeater.totalPConsumption

        tes_temp = exbuild.bes.tes.array_temp_storage

        sh_en = sum(sh_p_array) * timestep / (1000 * 3600)
        dhw_en = sum(dhw_p_array) * timestep / (1000 * 3600)

        q_hp_out_en = sum(q_hp_out) * timestep / (1000 * 3600)
        q_eh_out_en = sum(q_eh_out) * timestep / (1000 * 3600)

        el_eh_in_en = sum(el_eh_in) * timestep / (1000 * 3600)
        el_hp_in_en = sum(el_hp_in) * timestep / (1000 * 3600)

        assert sh_en + dhw_en <= (q_hp_out_en + q_eh_out_en)
        assert dhw_en <= q_eh_out_en
        assert abs(q_eh_out_en - el_eh_in_en) < 0.001
        assert el_hp_in_en <= q_hp_out_en

        # #  #################################################################

        #  ##################################################################
        #  Get buiding 1006 (boiler, tes, PV, battery)
        #  Add EH to test energy balance for boiler and eh without tes
        id = 1006
        exbuild = city.node[id]['entity']

        exbuild.bes.boiler.qNominal *= 5
        exbuild.bes.tes.capacity *= 2

        #  Calculate thermal energy balance
        buildeb.calc_build_therm_eb(build=exbuild, id=id)

        #  Calculate electric energy balance
        buildeb.calc_build_el_eb(build=exbuild)

        q_out = exbuild.bes.boiler.totalQOutput
        fuel_in = exbuild.bes.boiler.array_fuel_power
        sh_p_array = exbuild.get_space_heating_power_curve()
        dhw_p_array = exbuild.get_dhw_power_curve()

        sh_net_energy = sum(sh_p_array) * timestep / (1000 * 3600)  # in kWh
        dhw_net_energy = sum(dhw_p_array) * timestep / (1000 * 3600)  # in kWh
        boil_th_energy = sum(q_out) * timestep / (1000 * 3600)  # in kWh
        fuel_boiler_energy = sum(fuel_in) * timestep / (1000 * 3600)  # in kWh

        #  Thermal storage
        q_tes_in = exbuild.bes.tes.array_q_charge
        q_tes_out = exbuild.bes.tes.array_q_discharge

        sum_q_tes_in = sum(q_tes_in) * timestep / (1000 * 3600)
        sum_q_tes_out = sum(q_tes_out) * timestep / (1000 * 3600)

        assert fuel_boiler_energy >= boil_th_energy
        assert abs(boil_th_energy + sum_q_tes_out >=
                   (sh_net_energy + dhw_net_energy + sum_q_tes_in))

        #  ##################################################################

        #  ##################################################################
        #  Get building 1002 (no thermal energy system)
        #  and calculate electric energy balance
        id = 1002
        exbuild = city.node[id]['entity']

        #  Calculate electric energy balance
        buildeb.calc_build_el_eb(build=exbuild)

        el_energy = exbuild.get_annual_el_demand()

        grid_import_dem = exbuild.dict_el_eb_res['grid_import_dem']
        sum_grid_import = sum(grid_import_dem) * timestep / (1000 * 3600)

        assert abs(el_energy - sum_grid_import) <= 0.001

        #  ##################################################################

        #  ##################################################################

        id = 1005
        exbuild = city.node[id]['entity']
        exbuild.bes.boiler.qNominal *= 10
        exbuild.bes.tes.capacity *= 1
        #  Comment: Rescaling is necessary, as dhw_method = 1 is used.
        #  This leads to dhw peaks for all buildings at the same timesteps

        id = 1012
        exbuild = city.node[id]['entity']
        exbuild.bes.boiler.qNominal *= 10
        exbuild.bes.tes.capacity *= 1

        #  Run city energy balance test
        energy_balance = cityeb.CityEBCalculator(city=city)

        #  Calc. city energy balance
        energy_balance.calc_city_energy_balance()

        #  ##################################################################

    def test_building_eb_2(self, fixture_building):
        """
        Test, if share of CHP self-consumed and fed-in electric energy is
        correct
        """

        build = copy.deepcopy(fixture_building)

        timestep = build.environment.timer.timeDiscretization
        nb_timesteps = int(365 * 24 * 3600 / timestep)

        q_nom = 1000
        eta_total = 0.9

        p_nom = asue.calc_el_power_with_th_power(th_power=q_nom,
                                                 eta_total=eta_total)

        sh_power = np.ones(nb_timesteps) * q_nom  # 1000 W

        el_power = np.ones(nb_timesteps) * p_nom / 4  # 1/4 p_nom in W

        build.apartments[0].demandSpaceheating.loadcurve = sh_power
        build.apartments[0].power_el.loadcurve = el_power

        chp = chpsys.ChpExtended(environment=build.environment,
                                 q_nominal=q_nom,
                                 p_nominal=p_nom, eta_total=eta_total)

        tes = sto.thermalEnergyStorageExtended \
            (environment=build.environment, t_init=75, capacity=100)

        bes = BES.BES(environment=build.environment)

        bes.addDevice(chp)
        bes.addDevice(tes)

        build.addEntity(bes)

        #  Calculate energy balances
        buildeb.calc_build_therm_eb(build=build)

        buildeb.calc_build_el_eb(build=build)

        #  Check results
        sh_energy = build.get_annual_space_heat_demand()

        chp_self = build.dict_el_eb_res['chp_self']
        chp_feed = build.dict_el_eb_res['chp_feed']

        sum_chp_self = sum(chp_self) * timestep / (1000 * 3600)
        sum_chp_feed = sum(chp_feed) * timestep / (1000 * 3600)

        chp_th_power = build.bes.chp.totalQOutput
        chp_el_power = build.bes.chp.totalPOutput

        chp_th_energy = sum(chp_th_power) * timestep / (1000 * 3600)
        chp_el_energy = sum(chp_el_power) * timestep / (1000 * 3600)

        #  Assert CHP el. energy balance
        assert abs(chp_el_energy - (sum_chp_self + sum_chp_feed)) <= 0.001
        #  Assert that share of CHP self consumption is around 1/4
        assert abs(
            sum_chp_self / (sum_chp_self + sum_chp_feed) - 1 / 4) < 0.001
        #  Assert that produced CHP thermal energy is larger (losses of TES)
        #  or equal to space heating net energy demand
        assert chp_th_energy >= sh_energy

    def test_eb_boiler_chp_tes_no_losses(self, fixture_building):
        """
        Check energy balance without losses for CHP, boiler and TES system
        """

        build = copy.deepcopy(fixture_building)

        timestep = build.environment.timer.timeDiscretization

        sh_day = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           40, 30, 20, 10, 5, 5, 5, 5, 5, 5, 5, 5,
                           5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,
                           5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,
                           2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
                           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
                           ]) * 1000

        el_day = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           20, 50, 10, 5, 0, 0, 0, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 0,
                           0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2,
                           100, 100, 100, 100, 2, 2, 2, 2, 2, 2, 2, 2,
                           50, 20, 10, 10, 2, 2, 2, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
                           ]) * 1000

        build.apartments[0].demandSpaceheating.loadcurve = np.tile(sh_day, 365)
        build.apartments[0].power_el.loadcurve = np.tile(el_day, 365)

        q_nom = 10000
        eta_total = 1

        p_nom = asue.calc_el_power_with_th_power(th_power=q_nom,
                                                 eta_total=eta_total)

        chp = chpsys.ChpExtended(environment=build.environment,
                                 q_nominal=q_nom,
                                 p_nominal=p_nom, eta_total=eta_total)

        tes = sto.thermalEnergyStorageExtended \
            (environment=build.environment, t_init=80, capacity=500, k_loss=0)

        boiler = boil.BoilerExtended(environment=build.environment,
                                     q_nominal=30000, eta=1)

        bes = BES.BES(environment=build.environment)

        bes.addDevice(chp)
        bes.addDevice(tes)
        bes.addDevice(boiler)

        build.addEntity(bes)

        #  Calculate energy balances
        buildeb.calc_build_therm_eb(build=build)

        buildeb.calc_build_el_eb(build=build)

        #  Get results

        sh_energy = build.get_annual_space_heat_demand()
        dhw_energy = build.get_annual_dhw_demand()
        el_energy = build.get_annual_el_demand()

        chp_th_power = build.bes.chp.totalQOutput
        chp_el_power = build.bes.chp.totalPOutput
        chp_fuel_in = build.bes.chp.array_fuel_power

        chp_th_energy = sum(chp_th_power) * timestep / (1000 * 3600)
        chp_el_energy = sum(chp_el_power) * timestep / (1000 * 3600)
        sum_chp_fuel_in = sum(chp_fuel_in) * timestep / (1000 * 3600)

        chp_self = build.dict_el_eb_res['chp_self']
        chp_self_dem = build.dict_el_eb_res['chp_self_dem']
        chp_feed = build.dict_el_eb_res['chp_feed']

        sum_chp_self = sum(chp_self) * timestep / (1000 * 3600)
        sum_chp_self_dem = sum(chp_self_dem) * timestep / (1000 * 3600)
        sum_chp_feed = sum(chp_feed) * timestep / (1000 * 3600)

        grid_import_dem = build.dict_el_eb_res['grid_import_dem']
        sum_grid_import = sum(grid_import_dem) * timestep / (1000 * 3600)

        boiler_th_power = build.bes.boiler.totalQOutput
        boiler_fuel_in = build.bes.boiler.array_fuel_power

        sum_boiler_th_energy = sum(boiler_th_power) * timestep / (1000 * 3600)
        sum_boiler_fuel = sum(boiler_fuel_in) * timestep / (1000 * 3600)

        #  Thermal storage
        q_tes_in = build.bes.tes.array_q_charge
        q_tes_out = build.bes.tes.array_q_discharge

        sum_q_tes_in = sum(q_tes_in) * timestep / (1000 * 3600)
        sum_q_tes_out = sum(q_tes_out) * timestep / (1000 * 3600)

        #  Assert CHP el. energy balance
        assert abs(chp_el_energy - (sum_chp_self + sum_chp_feed)) <= 0.001

        assert abs(chp_el_energy + chp_th_energy - sum_chp_fuel_in) <= 0.001

        #  Assert thermal energy balance of system
        assert abs(sh_energy + dhw_energy - chp_th_energy
                   - sum_boiler_th_energy
                   - sum_q_tes_out + sum_q_tes_in) <= 0.001

        #  Check electric energy balance
        assert abs(el_energy - (sum_chp_self
                                + sum_grid_import)) <= 0.001

        #  Check overall energy balance (without losses)
        assert abs((sh_energy + dhw_energy + el_energy) - (sum_chp_fuel_in
                                                           - sum_chp_feed
                                                           - sum_q_tes_in
                                                           + sum_q_tes_out
                                                           + sum_boiler_fuel
                                                           + sum_grid_import)) \
               <= 0.001

        #  Check overall energy balance (without losses)
        assert abs((sh_energy + dhw_energy + el_energy) - (chp_th_energy
                                                           + sum_chp_self_dem
                                                           - sum_q_tes_in
                                                           + sum_q_tes_out
                                                           + sum_boiler_th_energy
                                                           + sum_grid_import)) \
               <= 0.001

    def test_eb_chp_pv_tes_no_losses(self, fixture_building):
        """
        Check energy balance without losses for CHP and PV system
        """

        build = copy.deepcopy(fixture_building)

        timestep = build.environment.timer.timeDiscretization
        nb_timesteps = int(365 * 24 * 3600 / timestep)

        q_nom = 20000
        eta_total = 1

        p_nom = asue.calc_el_power_with_th_power(th_power=q_nom,
                                                 eta_total=eta_total)

        sh_power = np.ones(nb_timesteps) * 20000
        el_power = np.ones(nb_timesteps) * 12000

        build.apartments[0].demandSpaceheating.loadcurve = sh_power
        build.apartments[0].power_el.loadcurve = el_power

        chp = chpsys.ChpExtended(environment=build.environment,
                                 q_nominal=q_nom,
                                 p_nominal=p_nom, eta_total=eta_total)

        tes = sto.thermalEnergyStorageExtended \
            (environment=build.environment, t_init=80, capacity=500, k_loss=0)

        pv = PV.PV(environment=build.environment, area=10, eta=1)

        pv.totalPower = np.ones(nb_timesteps) * 10000

        bes = BES.BES(environment=build.environment)

        bes.addDevice(chp)
        bes.addDevice(tes)
        bes.addDevice(pv)

        build.addEntity(bes)

        #  Calculate energy balances
        buildeb.calc_build_therm_eb(build=build)

        buildeb.calc_build_el_eb(build=build)

        #  Get results

        sh_energy = build.get_annual_space_heat_demand()
        dhw_energy = build.get_annual_dhw_demand()
        el_energy = build.get_annual_el_demand()

        chp_th_power = build.bes.chp.totalQOutput
        chp_el_power = build.bes.chp.totalPOutput
        chp_fuel_in = build.bes.chp.array_fuel_power

        chp_th_energy = sum(chp_th_power) * timestep / (1000 * 3600)
        chp_el_energy = sum(chp_el_power) * timestep / (1000 * 3600)
        sum_chp_fuel_in = sum(chp_fuel_in) * timestep / (1000 * 3600)

        chp_self = build.dict_el_eb_res['chp_self']
        chp_self_dem = build.dict_el_eb_res['chp_self_dem']
        chp_feed = build.dict_el_eb_res['chp_feed']
        pv_self = build.dict_el_eb_res['pv_self']
        pv_feed = build.dict_el_eb_res['pv_feed']

        sum_chp_self = sum(chp_self) * timestep / (1000 * 3600)
        sum_chp_self_dem = sum(chp_self_dem) * timestep / (1000 * 3600)
        sum_chp_feed = sum(chp_feed) * timestep / (1000 * 3600)
        sum_pv_self = sum(pv_self) * timestep / (1000 * 3600)
        sum_pv_feed = sum(pv_feed) * timestep / (1000 * 3600)

        grid_import_dem = build.dict_el_eb_res['grid_import_dem']
        sum_grid_import = sum(grid_import_dem) * timestep / (1000 * 3600)

        #  Thermal storage
        q_tes_in = build.bes.tes.array_q_charge
        q_tes_out = build.bes.tes.array_q_discharge

        sum_q_tes_in = sum(q_tes_in) * timestep / (1000 * 3600)
        sum_q_tes_out = sum(q_tes_out) * timestep / (1000 * 3600)

        #  Assert CHP el. energy balance
        assert abs(chp_el_energy - (sum_chp_self + sum_chp_feed)) <= 0.001

        #  Assert thermal energy balance of system
        assert abs(sh_energy + dhw_energy - chp_th_energy
                   - sum_q_tes_out + sum_q_tes_in) <= 0.001

        #  Check electric energy balance
        assert abs(el_energy - (sum_chp_self + sum_pv_self
                                + sum_grid_import)) <= 0.001

        #  Check that PV self consumption share is around zero
        assert abs(sum_pv_self / (sum_pv_feed + sum_pv_self) - 1) \
               <= 0.001

        #  Check overall energy balance (without losses)
        assert abs((sh_energy + dhw_energy + el_energy) - (sum_chp_fuel_in
                                                           - sum_chp_feed
                                                           - sum_q_tes_in
                                                           + sum_q_tes_out
                                                           + sum_pv_self
                                                           + sum_grid_import)) \
               <= 0.001

        #  Check overall energy balance (without losses)
        assert abs((sh_energy + dhw_energy + el_energy) - (chp_th_energy
                                                           + sum_chp_self_dem
                                                           - sum_q_tes_in
                                                           + sum_q_tes_out
                                                           + sum_pv_self
                                                           + sum_grid_import)) \
               <= 0.001

    def test_el_eb_pv(self, fixture_building):
        """
        Test el. energy balance with PV
        """

        build = copy.deepcopy(fixture_building)

        timestep = build.environment.timer.timeDiscretization
        nb_timesteps = int(365 * 24 * 3600 / timestep)

        build.apartments[0].power_el.loadcurve = np.ones(nb_timesteps) * 1000

        pv = PV.PV(environment=build.environment, area=100, eta=0.15,
                   temperature_nominal=45,
                   alpha=0, beta=0, gamma=0, tau_alpha=0.9)

        pv_power = pv.getPower(currentValues=False, updatePower=True)

        sum_pv_energy = sum(pv_power) * timestep / (3600 * 1000)

        bes = BES.BES(environment=build.environment)

        bes.addDevice(pv)
        # bes.addDevice(battery)

        build.addEntity(bes)

        buildeb.calc_build_el_eb(build=build)

        pv_self = build.dict_el_eb_res['pv_self']
        pv_feed = build.dict_el_eb_res['pv_feed']
        grid_import_dem = build.dict_el_eb_res['grid_import_dem']

        sum_pv_self = sum(pv_self) * timestep / (1000 * 3600)
        sum_pv_feed = sum(pv_feed) * timestep / (1000 * 3600)
        sum_grid_import = sum(grid_import_dem) * timestep / (1000 * 3600)

        el_demand = build.get_annual_el_demand()

        assert abs(el_demand - (sum_pv_self + sum_grid_import)) <= 0.001
        assert abs(sum_pv_energy - (sum_pv_self + sum_pv_feed)) <= 0.001

    def test_eb_pv_hp_eh_tes_static(self, fixture_building):
        """

        """

        build = copy.deepcopy(fixture_building)

        timestep = build.environment.timer.timeDiscretization
        nb_timesteps = int(365 * 24 * 3600 / timestep)

        build.apartments[0].power_el.loadcurve = np.ones(nb_timesteps) * 1000
        build.apartments[0].demandSpaceheating.loadcurve = \
            np.ones(nb_timesteps) * 2000

        pv = PV.PV(environment=build.environment, area=20, eta=0.15,
                   temperature_nominal=45,
                   alpha=0, beta=0, gamma=0, tau_alpha=0.9)

        bes = BES.BES(environment=build.environment)

        hp = hpsys.heatPumpSimple(environment=build.environment,
                                  q_nominal=6000)

        eh = ehsys.ElectricalHeaterExtended(environment=build.environment,
                                            q_nominal=10000)

        tes = sto.thermalEnergyStorageExtended(environment=build.environment,
                                               t_init=45, t_max=45,
                                               capacity=100, k_loss=0)

        bes.addDevice(pv)
        bes.addDevice(hp)
        bes.addDevice(eh)
        bes.addDevice(tes)

        build.addEntity(bes)

        buildeb.calc_build_therm_eb(build=build)
        buildeb.calc_build_el_eb(build=build)

        sh_energy = build.get_annual_space_heat_demand()
        dhw_energy = build.get_annual_dhw_demand()
        el_energy = build.get_annual_el_demand()

        pv_power = pv.getPower(currentValues=False, updatePower=True)
        sum_pv_energy = sum(pv_power) * timestep / (3600 * 1000)

        hp_th_power = build.bes.heatpump.totalQOutput
        hp_el_power = build.bes.heatpump.array_el_power_in

        eh_th_power = build.bes.electricalHeater.totalQOutput
        eh_el_power = build.bes.electricalHeater.totalPConsumption

        sum_hp_th_energy = sum(hp_th_power) * timestep / (1000 * 3600)
        sum_hp_el_energy = sum(hp_el_power) * timestep / (1000 * 3600)
        sum_eh_th_energy = sum(eh_th_power) * timestep / (1000 * 3600)
        sum_eh_el_energy = sum(eh_el_power) * timestep / (1000 * 3600)

        pv_self = build.dict_el_eb_res['pv_self']
        pv_self_dem = build.dict_el_eb_res['pv_self_dem']
        pv_self_eh = build.dict_el_eb_res['pv_self_eh']
        pv_feed = build.dict_el_eb_res['pv_feed']
        grid_import_dem = build.dict_el_eb_res['grid_import_dem']
        grid_import_hp = build.dict_el_eb_res['grid_import_hp']
        grid_import_eh = build.dict_el_eb_res['grid_import_eh']

        sum_pv_self = sum(pv_self) * timestep / (1000 * 3600)
        sum_pv_self_dem = sum(pv_self_dem) * timestep / (1000 * 3600)
        sum_pv_self_eh = sum(pv_self_eh) * timestep / (1000 * 3600)
        sum_pv_feed = sum(pv_feed) * timestep / (1000 * 3600)

        sum_grid_import_dem = sum(grid_import_dem) * timestep / (1000 * 3600)
        sum_grid_import_hp = sum(grid_import_hp) * timestep / (1000 * 3600)
        sum_grid_import_eh = sum(grid_import_eh) * timestep / (1000 * 3600)

        #  Thermal storage
        q_tes_in = build.bes.tes.array_q_charge
        q_tes_out = build.bes.tes.array_q_discharge

        sum_q_tes_in = sum(q_tes_in) * timestep / (1000 * 3600)
        sum_q_tes_out = sum(q_tes_out) * timestep / (1000 * 3600)

        assert abs(el_energy + sum_hp_el_energy + sum_eh_el_energy \
                   - (sum_pv_self + sum_grid_import_dem + sum_grid_import_hp +
                      sum_grid_import_eh)) <= 0.001
        assert sum_hp_el_energy <= sum_grid_import_hp + sum_pv_self
        assert sum_eh_el_energy <= sum_grid_import_eh + sum_pv_self
        assert abs(sum_pv_energy - (sum_pv_self + sum_pv_feed)) <= 0.001

        assert abs(sh_energy + dhw_energy - (sum_hp_th_energy +
                                             sum_eh_th_energy)) <= 0.001

        #  Assert total energy balance
        assert abs(sh_energy + dhw_energy
                   + el_energy - (sum_hp_th_energy
                                  + sum_eh_th_energy
                                  + sum_pv_self_dem
                                  + sum_grid_import_dem
                                  - sum_q_tes_in
                                  + sum_q_tes_out)) <= 0.001

    def test_pv_with_battery_eb(self, fixture_building):
        """

        """

        build = copy.deepcopy(fixture_building)

        timestep = build.environment.timer.timeDiscretization
        nb_timesteps = int(365 * 24 * 3600 / timestep)

        bes = BES.BES(environment=build.environment)

        battery = bat.BatteryExtended(environment=build.environment,
                                      soc_init_ratio=0.5, capacity_kwh=1000,
                                      self_discharge=0, eta_charge=1,
                                      eta_discharge=1)

        pv = PV.PV(environment=build.environment, area=20, eta=0.15,
                   temperature_nominal=45,
                   alpha=0, beta=0, gamma=0, tau_alpha=0.9)

        pv_power = pv.getPower(currentValues=False, updatePower=True)
        pv_power_mean = np.mean(pv_power)
        sum_pv_energy = sum(pv_power) * timestep / (1000 * 3600)

        #  Set building el. power to 0.99 pv_power_mean
        build.apartments[0].power_el.loadcurve = np.ones(nb_timesteps) \
                                                 * 0.99 * pv_power_mean

        bes.addMultipleDevices([battery, pv])

        build.addEntity(bes)

        #  Calculate el. energy balance
        buildeb.calc_build_el_eb(build=build)

        el_energy = build.get_annual_el_demand()

        pv_self = build.dict_el_eb_res['pv_self']
        pv_feed = build.dict_el_eb_res['pv_feed']
        grid_import_dem = build.dict_el_eb_res['grid_import_dem']

        bat_charge = build.bes.battery.totalPCharge
        bat_discharge = build.bes.battery.totalPDischarge

        sum_pv_self = sum(pv_self) * timestep / (1000 * 3600)
        sum_pv_feed = sum(pv_feed) * timestep / (1000 * 3600)
        sum_grid_import = sum(grid_import_dem) * timestep / (1000 * 3600)

        sum_bat_charge = sum(bat_charge) * timestep / (1000 * 3600)
        sum_bat_discharge = sum(bat_discharge) * timestep / (1000 * 3600)

        assert sum_grid_import == 0
        assert abs(sum_pv_energy - sum_pv_self - sum_pv_feed) <= 0.001

        #  Assert electric energy balance
        assert abs(el_energy - (sum_pv_self
                                - sum_bat_charge
                                + sum_bat_discharge
                                + sum_grid_import)) <= 0.001

    def test_pv_with_battery_eb_with_feed_in(self, fixture_building):
        """

        """

        build = copy.deepcopy(fixture_building)

        timestep = build.environment.timer.timeDiscretization

        bes = BES.BES(environment=build.environment)

        battery = bat.BatteryExtended(environment=build.environment,
                                      soc_init_ratio=0.5, capacity_kwh=20,
                                      self_discharge=0, eta_charge=1,
                                      eta_discharge=1)

        pv = PV.PV(environment=build.environment, area=100, eta=0.15,
                   temperature_nominal=45,
                   alpha=0, beta=0, gamma=0, tau_alpha=0.9)

        pv_power = pv.getPower(currentValues=False, updatePower=True)
        sum_pv_energy = sum(pv_power) * timestep / (1000 * 3600)

        el_day = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           20, 50, 10, 5, 0, 0, 0, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 0,
                           0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2,
                           100, 100, 100, 100, 2, 2, 2, 2, 2, 2, 2, 2,
                           50, 20, 10, 10, 2, 2, 2, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
                           ]) * 100

        build.apartments[0].power_el.loadcurve = np.tile(el_day, 365)

        bes.addMultipleDevices([battery, pv])

        build.addEntity(bes)

        #  Calculate el. energy balance
        buildeb.calc_build_el_eb(build=build)

        el_energy = build.get_annual_el_demand()

        pv_self = build.dict_el_eb_res['pv_self']
        pv_feed = build.dict_el_eb_res['pv_feed']
        grid_import_dem = build.dict_el_eb_res['grid_import_dem']

        bat_charge = build.bes.battery.totalPCharge
        bat_discharge = build.bes.battery.totalPDischarge

        sum_pv_self = sum(pv_self) * timestep / (1000 * 3600)
        sum_pv_feed = sum(pv_feed) * timestep / (1000 * 3600)
        sum_grid_import = sum(grid_import_dem) * timestep / (1000 * 3600)

        sum_bat_charge = sum(bat_charge) * timestep / (1000 * 3600)
        sum_bat_discharge = sum(bat_discharge) * timestep / (1000 * 3600)

        assert abs(sum_pv_energy - sum_pv_self - sum_pv_feed) <= 0.001

        #  Assert electric energy balance
        assert abs(el_energy - (sum_pv_self
                                - sum_bat_charge
                                + sum_bat_discharge
                                + sum_grid_import)) <= 0.001

    def test_pv_chp_eh_boiler_dynamic(self, fixture_building):
        """

        """
        build = copy.deepcopy(fixture_building)

        timestep = build.environment.timer.timeDiscretization

        bes = BES.BES(environment=build.environment)

        pv = PV.PV(environment=build.environment, area=1000, eta=0.15,
                   temperature_nominal=45,
                   alpha=0, beta=0, gamma=0, tau_alpha=0.9)

        eh = ehsys.ElectricalHeaterExtended(environment=build.environment,
                                            q_nominal=50000)

        t_init = 70

        tes = sto.thermalEnergyStorageExtended(environment=build.environment,
                                               capacity=1000, k_loss=0,
                                               t_init=t_init)

        q_nom = 20000
        eta_total = 1

        p_nom = asue.calc_el_power_with_th_power(th_power=q_nom,
                                                 eta_total=eta_total)

        chp = chpsys.ChpExtended(environment=build.environment,
                                 q_nominal=q_nom,
                                 p_nominal=p_nom, eta_total=eta_total)

        boiler = boil.BoilerExtended(environment=build.environment,
                                     q_nominal=50000, eta=1)

        bes.addMultipleDevices([pv, eh, tes, chp, boiler])

        build.addEntity(bes)

        sh_day = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           100, 100, 100, 100, 30, 30, 30, 30, 30, 30, 30, 30,
                           10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
                           5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,
                           2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
                           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
                           ]) * 1000

        el_day = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           20, 20, 20, 20, 30, 30, 30, 30, 30, 30, 30, 30,
                           10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
                           5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,
                           100, 100, 100, 100, 2, 2, 2, 2, 2, 2, 2, 2,
                           50, 50, 50, 50, 0, 0, 0, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
                           ]) * 1000

        build.apartments[0].demandSpaceheating.loadcurve = np.tile(sh_day, 365)
        build.apartments[0].power_el.loadcurve = np.tile(el_day, 365)

        #  Calculate energy balances
        buildeb.calc_build_therm_eb(build=build)
        buildeb.calc_build_el_eb(build=build)

        #  Analyse results

        #  Demands
        sh_energy = build.get_annual_space_heat_demand()
        dhw_energy = build.get_annual_dhw_demand()
        el_energy = build.get_annual_el_demand()

        #  PV
        pv_power = pv.getPower(currentValues=False, updatePower=True)
        sum_pv_energy = sum(pv_power) * timestep / (3600 * 1000)

        #  CHP
        q_chp_out = build.bes.chp.totalQOutput
        p_el_chp_out = build.bes.chp.totalPOutput
        fuel_chp_in = build.bes.chp.array_fuel_power

        chp_th_energy = sum(q_chp_out) * timestep / (1000 * 3600)  # in kWh
        fuel_chp_energy = sum(fuel_chp_in) * timestep / (1000 * 3600)  # in kWh
        chp_el_energy = sum(p_el_chp_out) * timestep / (1000 * 3600)  # in kWh

        #  Boiler
        q_boiler = build.bes.boiler.totalQOutput
        sum_q_boiler = sum(q_boiler) * timestep / (1000 * 3600)  # in kWh

        fuel_in = build.bes.boiler.array_fuel_power
        fuel_boiler_energy = sum(fuel_in) * timestep / (1000 * 3600)  # in kWh

        #  Electric heater
        eh_th_power = build.bes.electricalHeater.totalQOutput
        eh_el_power = build.bes.electricalHeater.totalPConsumption

        sum_eh_th_energy = sum(eh_th_power) * timestep / (1000 * 3600)
        sum_eh_el_energy = sum(eh_el_power) * timestep / (1000 * 3600)

        #  Thermal storage
        q_tes_in = build.bes.tes.array_q_charge
        q_tes_out = build.bes.tes.array_q_discharge

        sum_q_tes_in = sum(q_tes_in) * timestep / (1000 * 3600)
        sum_q_tes_out = sum(q_tes_out) * timestep / (1000 * 3600)

        pv_self = build.dict_el_eb_res['pv_self']
        pv_feed = build.dict_el_eb_res['pv_feed']
        pv_self_dem = build.dict_el_eb_res['pv_self_dem']
        pv_self_eh = build.dict_el_eb_res['pv_self_eh']

        chp_self_dem = build.dict_el_eb_res['chp_self_dem']
        chp_self = build.dict_el_eb_res['chp_self']
        chp_feed = build.dict_el_eb_res['chp_feed']
        chp_self_eh = build.dict_el_eb_res['chp_self_eh']

        grid_import_dem = build.dict_el_eb_res['grid_import_dem']
        grid_import_eh = build.dict_el_eb_res['grid_import_eh']

        sum_pv_self = sum(pv_self) * timestep / (1000 * 3600)
        sum_pv_feed = sum(pv_feed) * timestep / (1000 * 3600)
        sum_pv_self_dem = sum(pv_self_dem) * timestep / (1000 * 3600)
        sum_pv_self_eh = sum(pv_self_eh) * timestep / (1000 * 3600)

        sum_chp_self_dem = sum(chp_self_dem) * timestep / (1000 * 3600)
        sum_chp_self = sum(chp_self) * timestep / (1000 * 3600)
        sum_chp_feed = sum(chp_feed) * timestep / (1000 * 3600)
        sum_chp_self_eh = sum(chp_self_eh) * timestep / (1000 * 3600)

        sum_grid_import_dem = sum(grid_import_dem) * timestep / (1000 * 3600)
        sum_grid_import_eh = sum(grid_import_eh) * timestep / (1000 * 3600)

        tes = build.bes.tes

        delta_q_tes = tes.capacity * tes.c_p * (tes.t_current - t_init) \
                      / (1000 * 3600)

        #  Assert PV energy balance
        assert abs(sum_pv_energy -
                   (sum_pv_feed + sum_pv_self_dem + sum_pv_self_eh)) <= 0.001

        assert abs(sum_pv_self - (sum_pv_self_dem + sum_pv_self_eh)) <= 0.001

        #  Assert CHP internal energy balance
        assert abs(fuel_chp_energy - (chp_th_energy + chp_el_energy)) <= 0.001

        #  Assert CHP electric energy balance
        assert abs(fuel_chp_energy - chp_th_energy) - \
               (sum_chp_feed + sum_chp_self_dem + sum_chp_self_eh) <= 0.001

        assert abs(
            sum_chp_self - (sum_chp_self_dem + sum_chp_self_eh)) <= 0.001

        #  Assert electric heater energy balance
        assert abs(sum_eh_th_energy - sum_eh_el_energy) <= 0.001
        assert abs(sum_eh_th_energy
                   - (sum_pv_self_eh
                      + sum_chp_self_eh + sum_grid_import_eh)) <= 0.001

        #  Assert net thermal energy balance
        assert abs(sh_energy + dhw_energy - (chp_th_energy + sum_q_boiler
                                             + sum_eh_th_energy + sum_q_tes_out - sum_q_tes_in)) <= 0.001

        #  Assert net electric energy balance
        assert abs(el_energy - (sum_chp_self_dem + sum_pv_self_dem +
                                sum_grid_import_dem)) \
               <= 0.001

        assert abs((sh_energy + dhw_energy + el_energy) - (fuel_chp_energy
                                                           + fuel_boiler_energy - sum_chp_feed + sum_q_tes_out
                                                           - sum_q_tes_in
                                                           + sum_pv_self_dem + sum_pv_self_eh
                                                           + sum_grid_import_dem
                                                           + sum_grid_import_eh)) <= 0.001

        assert abs((sh_energy + dhw_energy + el_energy) - (sum_chp_self_dem
                                                           + chp_th_energy
                                                           + sum_q_tes_out - sum_q_tes_in
                                                           + sum_q_boiler + sum_eh_th_energy
                                                           + sum_pv_self_dem
                                                           + sum_grid_import_dem)) <= 0.001

    def test_pv_chp_eh_boiler_static(self, fixture_building):
        """

        """
        build = copy.deepcopy(fixture_building)

        timestep = build.environment.timer.timeDiscretization
        nb_timesteps = int(365 * 24 * 3600 / timestep)

        bes = BES.BES(environment=build.environment)

        pv = PV.PV(environment=build.environment, area=100, eta=0.15,
                   temperature_nominal=45,
                   alpha=0, beta=0, gamma=0, tau_alpha=0.9)

        eh = ehsys.ElectricalHeaterExtended(environment=build.environment,
                                            q_nominal=50000)

        tes = sto.thermalEnergyStorageExtended(environment=build.environment,
                                               capacity=1, k_loss=0,
                                               t_init=70)

        q_nom = 10000
        eta_total = 1

        p_nom = asue.calc_el_power_with_th_power(th_power=q_nom,
                                                 eta_total=eta_total)

        chp = chpsys.ChpExtended(environment=build.environment,
                                 q_nominal=q_nom,
                                 p_nominal=p_nom, eta_total=eta_total)

        boiler = boil.BoilerExtended(environment=build.environment,
                                     q_nominal=50000, eta=1)

        bes.addMultipleDevices([
            # battery,
            pv,
            eh,
            tes,
            chp,
            boiler
        ])

        build.addEntity(bes)

        sh_day = np.ones(nb_timesteps) * 15000
        el_day = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           20, 20, 20, 20, 30, 30, 30, 30, 30, 30, 30, 30,
                           10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
                           5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,
                           100, 100, 100, 100, 2, 2, 2, 2, 2, 2, 2, 2,
                           50, 50, 50, 50, 0, 0, 0, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
                           ]) * 100

        build.apartments[0].demandSpaceheating.loadcurve = sh_day
        build.apartments[0].power_el.loadcurve = np.tile(el_day, 365)

        #  Calculate energy balances
        buildeb.calc_build_therm_eb(build=build)
        buildeb.calc_build_el_eb(build=build)

        #  Analyse results

        #  Demands
        sh_energy = build.get_annual_space_heat_demand()
        dhw_energy = build.get_annual_dhw_demand()
        el_energy = build.get_annual_el_demand()

        #  PV
        pv_power = pv.getPower(currentValues=False, updatePower=True)
        sum_pv_energy = sum(pv_power) * timestep / (3600 * 1000)

        #  CHP
        q_chp_out = build.bes.chp.totalQOutput
        p_el_chp_out = build.bes.chp.totalPOutput
        fuel_chp_in = build.bes.chp.array_fuel_power

        chp_th_energy = sum(q_chp_out) * timestep / (1000 * 3600)  # in kWh
        fuel_chp_energy = sum(fuel_chp_in) * timestep / (1000 * 3600)  # in kWh
        chp_el_energy = sum(p_el_chp_out) * timestep / (1000 * 3600)  # in kWh

        #  Boiler
        q_boiler = build.bes.boiler.totalQOutput
        sum_q_boiler = sum(q_boiler) * timestep / (1000 * 3600)  # in kWh

        fuel_in = build.bes.boiler.array_fuel_power
        fuel_boiler_energy = sum(fuel_in) * timestep / (1000 * 3600)  # in kWh

        #  Electric heater
        eh_th_power = build.bes.electricalHeater.totalQOutput
        eh_el_power = build.bes.electricalHeater.totalPConsumption

        sum_eh_th_energy = sum(eh_th_power) * timestep / (1000 * 3600)
        sum_eh_el_energy = sum(eh_el_power) * timestep / (1000 * 3600)

        #  Thermal storage
        q_tes_in = build.bes.tes.array_q_charge
        q_tes_out = build.bes.tes.array_q_discharge

        sum_q_tes_in = sum(q_tes_in) * timestep / (1000 * 3600)
        sum_q_tes_out = sum(q_tes_out) * timestep / (1000 * 3600)

        # #  Battery
        # bat_in = build.bes.battery.totalPCharge
        # bat_out = build.bes.battery.totalPDischarge
        #
        # sum_bat_in = sum(bat_in) * timestep / (1000 * 3600)
        # sum_bat_out = sum(bat_out) * timestep / (1000 * 3600)

        pv_self = build.dict_el_eb_res['pv_self']
        pv_feed = build.dict_el_eb_res['pv_feed']
        pv_self_dem = build.dict_el_eb_res['pv_self_dem']
        pv_self_eh = build.dict_el_eb_res['pv_self_eh']
        # pv_self_bat = build.dict_el_eb_res['pv_self_bat']

        chp_self_dem = build.dict_el_eb_res['chp_self_dem']
        chp_self = build.dict_el_eb_res['chp_self']
        chp_feed = build.dict_el_eb_res['chp_feed']
        # chp_self_bat = build.dict_el_eb_res['chp_self_bat']
        chp_self_eh = build.dict_el_eb_res['chp_self_eh']

        grid_import_dem = build.dict_el_eb_res['grid_import_dem']
        grid_import_eh = build.dict_el_eb_res['grid_import_eh']

        # bat_out_dem = build.dict_el_eb_res['bat_out_dem']
        # bat_out_eh = build.dict_el_eb_res['bat_out_eh']

        sum_pv_self = sum(pv_self) * timestep / (1000 * 3600)
        sum_pv_feed = sum(pv_feed) * timestep / (1000 * 3600)
        sum_pv_self_dem = sum(pv_self_dem) * timestep / (1000 * 3600)
        sum_pv_self_eh = sum(pv_self_eh) * timestep / (1000 * 3600)
        # sum_pv_self_bat = sum(pv_self_bat) * timestep / (1000 * 3600)

        sum_chp_self_dem = sum(chp_self_dem) * timestep / (1000 * 3600)
        sum_chp_self = sum(chp_self) * timestep / (1000 * 3600)
        sum_chp_feed = sum(chp_feed) * timestep / (1000 * 3600)
        # sum_chp_self_bat = sum(chp_self_bat) * timestep / (1000 * 3600)
        sum_chp_self_eh = sum(chp_self_eh) * timestep / (1000 * 3600)

        sum_grid_import_dem = sum(grid_import_dem) * timestep / (1000 * 3600)
        sum_grid_import_eh = sum(grid_import_eh) * timestep / (1000 * 3600)

        # sum_bat_out_dem = sum(bat_out_dem) * timestep / (1000 * 3600)
        # sum_bat_out_eh = sum(bat_out_eh) * timestep / (1000 * 3600)

        assert sum_pv_energy >= 0
        assert chp_th_energy >= 0
        assert fuel_chp_energy >= 0
        assert chp_el_energy >= 0
        assert sum_eh_th_energy >= 0
        assert sum_eh_el_energy >= 0
        assert sum_pv_self >= 0
        assert sum_pv_feed >= 0
        assert sum_pv_self_dem >= 0
        assert sum_pv_self_eh >= 0
        assert sum_chp_self_dem >= 0
        assert sum_chp_self >= 0
        assert sum_chp_feed >= 0
        assert sum_chp_self_eh >= 0
        assert sum_grid_import_dem >= 0
        assert sum_grid_import_eh >= 0

        #  Assert PV energy balance
        assert abs(sum_pv_energy -
                   (sum_pv_feed
                    + sum_pv_self_dem
                    + sum_pv_self_eh
                    # + sum_pv_self_bat
                    )) <= 0.001

        assert abs(sum_pv_self - (
            sum_pv_self_dem
            + sum_pv_self_eh
            # + sum_pv_self_bat
        )) <= 0.001

        #  Assert CHP internal energy balance
        assert abs(fuel_chp_energy - (chp_th_energy + chp_el_energy)) <= 0.001

        #  Assert CHP electric energy balance
        assert abs(fuel_chp_energy - chp_th_energy) - \
               (sum_chp_feed + sum_chp_self_dem
                # + sum_chp_self_bat
                + sum_chp_self_eh) <= 0.001

        assert abs(sum_chp_self - (
            # sum_chp_self_bat
            + sum_chp_self_dem
            + sum_chp_self_eh)) \
               <= 0.001

        #  Assert boiler energy balance
        assert abs(fuel_boiler_energy - sum_q_boiler) <= 0.001

        #  Assert electric heater energy balance
        assert abs(sum_eh_th_energy - sum_eh_el_energy) <= 0.001
        assert abs(sum_eh_el_energy
                   - (sum_pv_self_eh
                      + sum_chp_self_eh
                      + sum_grid_import_eh
                      # + sum_bat_out_eh
                      )) <= 0.001

        #  Assert net thermal energy balance
        assert abs(sh_energy + dhw_energy
                   - (chp_th_energy
                      + sum_q_boiler
                      + sum_eh_th_energy
                      + sum_q_tes_out
                      - sum_q_tes_in
                      )) <= 0.001

        #  Assert net electric energy balance
        assert abs(el_energy - (sum_chp_self_dem + sum_pv_self_dem +
                                sum_grid_import_dem
                                # + sum_bat_out_dem
                                )) <= 0.001

        # #  Assert battery energy balance
        # delta_bat_kWh = (build.bes.battery.soc_ratio_current - soc_init) * \
        #                 build.bes.battery.get_battery_capacity_in_kwh()
        # assert abs(delta_bat_kWh - (sum_bat_in - sum_bat_out)) <= 0.001
        #
        # assert abs(sum_bat_in - (sum_pv_self_bat + sum_chp_self_bat)) <= 0.001
        #
        # assert abs(sum_bat_out - (sum_bat_out_dem + sum_bat_out_eh)) <= 0.001

        assert abs(sh_energy + dhw_energy
                   + el_energy
                   - (chp_th_energy
                      + sum_chp_self_dem
                      + sum_q_boiler
                      + sum_eh_th_energy
                      - sum_q_tes_in
                      + sum_q_tes_out
                      + sum_pv_self_dem
                      + sum_grid_import_dem
                      # - sum_bat_in
                      # + sum_bat_out
                      ))

        assert abs(sh_energy
                   + dhw_energy
                   + el_energy
                   - (fuel_chp_energy
                      - sum_chp_feed
                      + fuel_boiler_energy
                      + sum_grid_import_eh
                      + sum_pv_self_eh
                      + sum_pv_self_dem
                      + sum_grid_import_dem
                      - sum_q_tes_in
                      + sum_q_tes_out
                      )) <= 0.001

    def test_pv_bat_chp_eh_boiler(self, fixture_building):
        """

        """
        build = copy.deepcopy(fixture_building)

        timestep = build.environment.timer.timeDiscretization

        bes = BES.BES(environment=build.environment)

        soc_init = 0

        battery = bat.BatteryExtended(environment=build.environment,
                                      soc_init_ratio=soc_init,
                                      capacity_kwh=100,
                                      self_discharge=0, eta_charge=1,
                                      eta_discharge=1)

        pv = PV.PV(environment=build.environment, area=100, eta=0.15,
                   temperature_nominal=45,
                   alpha=0, beta=0, gamma=0, tau_alpha=0.9)

        eh = ehsys.ElectricalHeaterExtended(environment=build.environment,
                                            q_nominal=50000)

        tes = sto.thermalEnergyStorageExtended(environment=build.environment,
                                               capacity=1000, k_loss=0,
                                               t_init=70)

        q_nom = 10000
        eta_total = 1

        p_nom = asue.calc_el_power_with_th_power(th_power=q_nom,
                                                 eta_total=eta_total)

        chp = chpsys.ChpExtended(environment=build.environment,
                                 q_nominal=q_nom,
                                 p_nominal=p_nom, eta_total=eta_total)

        boiler = boil.BoilerExtended(environment=build.environment,
                                     q_nominal=50000, eta=1)

        bes.addMultipleDevices([
            # battery,
            pv, eh, tes, chp, boiler])

        build.addEntity(bes)

        sh_day = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           100, 100, 100, 100, 30, 30, 30, 30, 30, 30, 30, 30,
                           10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
                           5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,
                           2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
                           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
                           ]) * 1000

        el_day = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           20, 20, 20, 20, 30, 30, 30, 30, 30, 30, 30, 30,
                           10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
                           5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,
                           100, 100, 100, 100, 2, 2, 2, 2, 2, 2, 2, 2,
                           50, 50, 50, 50, 0, 0, 0, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
                           ]) * 1000

        build.apartments[0].demandSpaceheating.loadcurve = np.tile(sh_day, 365)
        build.apartments[0].power_el.loadcurve = np.tile(el_day, 365)

        #  Calculate energy balances
        buildeb.calc_build_therm_eb(build=build)
        buildeb.calc_build_el_eb(build=build)

        #  Analyse results

        #  Demands
        sh_energy = build.get_annual_space_heat_demand()
        dhw_energy = build.get_annual_dhw_demand()
        el_energy = build.get_annual_el_demand()

        #  PV
        pv_power = pv.getPower(currentValues=False, updatePower=True)
        sum_pv_energy = sum(pv_power) * timestep / (3600 * 1000)

        #  CHP
        q_chp_out = build.bes.chp.totalQOutput
        p_el_chp_out = build.bes.chp.totalPOutput
        fuel_chp_in = build.bes.chp.array_fuel_power

        chp_th_energy = sum(q_chp_out) * timestep / (1000 * 3600)  # in kWh
        fuel_chp_energy = sum(fuel_chp_in) * timestep / (1000 * 3600)  # in kWh
        chp_el_energy = sum(p_el_chp_out) * timestep / (1000 * 3600)  # in kWh

        #  Boiler
        q_boiler = build.bes.boiler.totalQOutput
        sum_q_boiler = sum(q_boiler) * timestep / (1000 * 3600)  # in kWh

        fuel_in = build.bes.boiler.array_fuel_power
        fuel_boiler_energy = sum(fuel_in) * timestep / (1000 * 3600)  # in kWh

        #  Electric heater
        eh_th_power = build.bes.electricalHeater.totalQOutput
        eh_el_power = build.bes.electricalHeater.totalPConsumption

        sum_eh_th_energy = sum(eh_th_power) * timestep / (1000 * 3600)
        sum_eh_el_energy = sum(eh_el_power) * timestep / (1000 * 3600)

        #  Thermal storage
        q_tes_in = build.bes.tes.array_q_charge
        q_tes_out = build.bes.tes.array_q_discharge

        sum_q_tes_in = sum(q_tes_in) * timestep / (1000 * 3600)
        sum_q_tes_out = sum(q_tes_out) * timestep / (1000 * 3600)

        # #  Battery
        # bat_in = build.bes.battery.totalPCharge
        # bat_out = build.bes.battery.totalPDischarge

        # sum_bat_in = sum(bat_in) * timestep / (1000 * 3600)
        # sum_bat_out = sum(bat_out) * timestep / (1000 * 3600)

        pv_self = build.dict_el_eb_res['pv_self']
        pv_feed = build.dict_el_eb_res['pv_feed']
        pv_self_dem = build.dict_el_eb_res['pv_self_dem']
        pv_self_eh = build.dict_el_eb_res['pv_self_eh']
        # pv_self_bat = build.dict_el_eb_res['pv_self_bat']

        chp_self_dem = build.dict_el_eb_res['chp_self_dem']
        chp_self = build.dict_el_eb_res['chp_self']
        chp_feed = build.dict_el_eb_res['chp_feed']
        # chp_self_bat = build.dict_el_eb_res['chp_self_bat']
        chp_self_eh = build.dict_el_eb_res['chp_self_eh']

        grid_import_dem = build.dict_el_eb_res['grid_import_dem']
        grid_import_eh = build.dict_el_eb_res['grid_import_eh']

        # bat_out_dem = build.dict_el_eb_res['bat_out_dem']
        # bat_out_eh = build.dict_el_eb_res['bat_out_eh']

        sum_pv_self = sum(pv_self) * timestep / (1000 * 3600)
        sum_pv_feed = sum(pv_feed) * timestep / (1000 * 3600)
        sum_pv_self_dem = sum(pv_self_dem) * timestep / (1000 * 3600)
        sum_pv_self_eh = sum(pv_self_eh) * timestep / (1000 * 3600)
        # sum_pv_self_bat = sum(pv_self_bat) * timestep / (1000 * 3600)

        sum_chp_self_dem = sum(chp_self_dem) * timestep / (1000 * 3600)
        sum_chp_self = sum(chp_self) * timestep / (1000 * 3600)
        sum_chp_feed = sum(chp_feed) * timestep / (1000 * 3600)
        # sum_chp_self_bat = sum(chp_self_bat) * timestep / (1000 * 3600)
        sum_chp_self_eh = sum(chp_self_eh) * timestep / (1000 * 3600)

        sum_grid_import_dem = sum(grid_import_dem) * timestep / (1000 * 3600)
        sum_grid_import_eh = sum(grid_import_eh) * timestep / (1000 * 3600)

        # sum_bat_out_dem = sum(bat_out_dem) * timestep / (1000 * 3600)
        # sum_bat_out_eh = sum(bat_out_eh) * timestep / (1000 * 3600)

        assert sum_pv_energy >= 0
        assert chp_th_energy >= 0
        assert fuel_chp_energy >= 0
        assert chp_el_energy >= 0
        assert sum_q_boiler >= 0
        assert fuel_boiler_energy >= 0
        assert sum_eh_th_energy >= 0
        assert sum_eh_el_energy >= 0
        assert sum_q_tes_in >= 0
        # assert sum_bat_out >= 0
        # assert sum_bat_in >= 0
        # assert sum_bat_out >= 0
        assert sum_pv_self >= 0
        assert sum_pv_feed >= 0
        assert sum_pv_self_dem >= 0
        assert sum_pv_self_eh >= 0
        # assert sum_pv_self_bat >= 0
        assert sum_chp_self_dem >= 0
        assert sum_chp_self >= 0
        assert sum_chp_feed >= 0
        # assert sum_chp_self_bat >= 0
        assert sum_chp_self_eh >= 0
        assert sum_grid_import_dem >= 0
        assert sum_grid_import_eh >= 0
        # assert sum_bat_out_dem >= 0
        # assert sum_bat_out_eh >= 0

        #  Assert PV energy balance
        assert abs(sum_pv_energy -
                   (sum_pv_feed + sum_pv_self_dem + sum_pv_self_eh
                    #+ sum_pv_self_bat
                    )) <= 0.001

        assert abs(sum_pv_self - (sum_pv_self_dem + sum_pv_self_eh
                                  #+ sum_pv_self_bat
                                  )) <= 0.001

        #  Assert CHP internal energy balance
        assert abs(fuel_chp_energy - (chp_th_energy + chp_el_energy)) <= 0.001

        #  Assert CHP electric energy balance
        assert abs(fuel_chp_energy - chp_th_energy) - \
               (sum_chp_feed + sum_chp_self_dem
                #+ sum_chp_self_bat
                + sum_chp_self_eh) <= 0.001

        assert abs(sum_chp_self - (
            # sum_chp_self_bat
            + sum_chp_self_dem
            + sum_chp_self_eh)) \
               <= 0.001

        #  Assert boiler energy balance
        assert abs(fuel_boiler_energy - sum_q_boiler) <= 0.001

        #  Assert electric heater energy balance
        assert abs(sum_eh_th_energy - sum_eh_el_energy) <= 0.001
        assert abs(sum_eh_el_energy
                   - (sum_pv_self_eh
                      + sum_chp_self_eh
                      + sum_grid_import_eh
                      #+ sum_bat_out_eh
                      )) <= 0.001

        #  Assert net thermal energy balance
        assert abs(sh_energy + dhw_energy - (chp_th_energy + sum_q_boiler
                                             + sum_eh_th_energy + sum_q_tes_out - sum_q_tes_in)) <= 0.001

        #  Assert net electric energy balance
        assert abs(el_energy - (sum_chp_self_dem + sum_pv_self_dem +
                                sum_grid_import_dem
                                #+ sum_bat_out_dem
                                )) <= 0.001

        # #  Assert battery energy balance
        # delta_bat_kWh = (build.bes.battery.soc_ratio_current - soc_init) * \
        #                 build.bes.battery.get_battery_capacity_in_kwh()
        # assert abs(delta_bat_kWh - (sum_bat_in - sum_bat_out)) <= 0.001
        #
        # assert abs(sum_bat_in - (sum_pv_self_bat + sum_chp_self_bat)) <= 0.001
        #
        # assert abs(sum_bat_out - (sum_bat_out_dem + sum_bat_out_eh)) <= 0.001

        assert abs(sh_energy + dhw_energy
                   + el_energy
                   - (chp_th_energy + sum_chp_self_dem + sum_q_boiler
                      + sum_eh_th_energy - sum_q_tes_in + sum_q_tes_out
                      + sum_pv_self_dem + sum_grid_import_dem
                      #- sum_bat_in + sum_bat_out
                      ))

        #  Fixme: Implement working assert to check final energy, too
        assert abs(sh_energy
                   + dhw_energy
                   + el_energy
                   - (fuel_chp_energy - sum_chp_feed
                      + fuel_boiler_energy + sum_grid_import_eh
                      + sum_pv_self_eh + sum_pv_self_dem
                      + sum_grid_import_dem
                      - sum_q_tes_in + sum_q_tes_out
                     # - sum_bat_in + sum_bat_out
                      )) <= 0.001

    #  TODO: Add further battery tests, as battery seems to cause trouble

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
        city.edge[1001][1002]['temp_vl'] = 10
        city.edge[1001][1002]['temp_rl'] = 9.999999999999

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
                   - (sum_q_boiler + chp_th_energy)) <= 0.001

        #  Electric energy balance
        assert abs(sum_chp_feed - chp_el_energy) <= 0.001

        #  Check fuel thermal energy balance
        assert abs(sh_dem_1 + sh_dem_2 + sum_chp_feed
                   - (fuel_boiler_energy + fuel_chp_energy)) <= 0.001

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
