#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script holds class to calculate energy balance of whole city district
"""
from __future__ import division

import os
import copy
import pickle
import warnings
import numpy as np
import networkx as nx

import pycity_calc.simulation.energy_balance.check_eb_requ as check_eb
import pycity_calc.toolbox.networks.network_ops as netop
import pycity_calc.simulation.energy_balance.building_eb_calc as beb
import pycity_calc.toolbox.dimensioning.dim_networks as dimnet


def get_list_lhn_build_without_th_esys(city, list_buildings=None):
    """
    Return list of ids of building nodes, which do not have any internal
    thermal supply, except LHN connection.

    Parameters
    ----------
    city : object
        City object of pyCity_calc
    list_buildings list (of ints), optional
        List of buildings (default: None). If None, searches for
        all buildings

    Returns
    -------
    list_no_th_esys : list (of li ints)
        List of buildings without own thermal energy supply unit
    """

    if list_buildings is None:
        list_buildings = city.get_list_build_entity_node_ids()

    list_no_th_esys = []

    for n in list_buildings:

        build = city.node[n]['entity']

        has_th_supply = False

        if build.hasBes:

            if build.bes.hasBoiler:
                assert build.bes.boiler._kind == 'boiler'
                has_th_supply = True

            if build.bes.hasChp:
                assert build.bes.chp._kind == 'chp'
                has_th_supply = True

            if build.bes.hasElectricalHeater:
                assert build.bes.electricalHeater._kind == 'electricalheater'
                has_th_supply = True

            if build.bes.hasHeatpump:
                assert build.bes.heatpump._kind == 'heatpump'
                has_th_supply = True

        if has_th_supply is False:
            print('Found building without own thermal energy supply:')
            print('ID: ', n)
            list_no_th_esys.append(n)

    return list_no_th_esys


class CityEBCalculator(object):
    def __init__(self, city, copy_city=False, check_city=True):
        """
        Constructor of city energy balance
        Parameters
        ----------
        city : object
            City object of pyCity_calc
        copy_city : bool, optional
            Defines, if original city should be used for energy balance run
            or if city should be copied (default: False). If True, copies
            city. Chosen city object is going to be modified by energy
            balance
        check_city : bool, optional
            Check, if city object fulfills requirements for energy balance
            calculation (default: True)
        """

        if check_city:
            check_eb.check_eb_requirements(city=city)

        if copy_city:
            self.city = copy.deepcopy(city)
        else:
            self.city = city

        self._list_lists_lhn_ids = None
        self._list_lists_lhn_ids_build = None
        self._list_lists_deg_ids = None
        self._list_lists_deg_ids_build = None
        self._list_single_build = None
        self._list_no_th_esys = None

        #  Get list of sub-cities
        self.set_subcity_lists()

    def set_subcity_lists(self):
        """
        Calculate values subcity lists:
        _list_lists_lhn_ids
        _list_lists_lhn_ids_build
        _list_lists_deg_ids
        _list_lists_deg_ids_build
        _list_single_build
        _list_lists_lhn_no_th_supply
        """

        #  List of lists of local heating network connected nodes
        self._list_lists_lhn_ids = \
            netop.get_list_with_energy_net_con_node_ids(city=self.city,
                                                        network_type='heating')

        #  List of lists of building interconnected nodes (heating)
        self._list_lists_lhn_ids_build = \
            netop.get_list_with_energy_net_con_node_ids(city=self.city,
                                                        network_type='heating',
                                                        build_node_only=True)

        #  List of lists of electricity network connected nodes
        self._list_lists_deg_ids = \
            netop.get_list_with_energy_net_con_node_ids(city=self.city,
                                                        network_type='electricity')

        #  List of lists of building interconnected nodes (electricity)
        self._list_lists_deg_ids_build = \
            netop.get_list_with_energy_net_con_node_ids(city=self.city,
                                                        network_type='electricity',
                                                        build_node_only=True)

        #  Get list of single building ids (not connected to energy networks)
        self._list_single_build = \
            netop.get_list_build_without_energy_network(city=self.city)

        #  Get list of all buildings, which do not have own internal
        #  thermal energy supply
        self._list_no_th_esys = \
            get_list_lhn_build_without_th_esys(city=self.city)

    def calc_city_energy_balance(self):
        """
        Calculate energy balance of whole city. Save results on city object
        """

        # #  Loop over buildings, which are not connected to energy networks
        # for n in self._list_single_build:
        #     print()
        #     print('########################################################')
        #     print('Process stand-alone building with id: ', n)
        #
        #     building = self.city.node[n]['entity']
        #
        #     #  Calculate single building thermal energy balance
        #     beb.calc_build_therm_eb(build=building, id=n)
        #
        #     #  Calculate single building electrical energy balance
        #     beb.calc_build_el_eb(build=building)

        # LHN energy balance
        #  ################################################################
        #  Add weights to edges
        netop.add_weights_to_edges(graph=self.city)

        #  Loop over subcities
        for list_lhn_build_ids in self._list_lists_lhn_ids_build:

            print()
            print('########################################################')
            print('Process LHN network with buildings: ')
            print(list_lhn_build_ids)
            print()

            #  Start with buildings without own thermal energy supply units
            #  Identify all buildings in list_lhn_build_ids, which do
            #  not have own thermal energy supply
            list_no_th_esys = []
            list_th_esys = []
            for n in list_lhn_build_ids:
                if n in self._list_no_th_esys:
                    list_no_th_esys.append(n)
                else:
                    list_th_esys.append(n)

            print('Buildings within LHN network without thermal energy '
                  'supply:')
            print(list_no_th_esys)

            print('Buildings within LHN network with feeder supply:')
            print(list_th_esys)
            print()

            timestep = self.city.environment.timer.timeDiscretization

            #  Sum up thermal energy demand of all buildings without own th.
            #  supply system
            th_lhn_power = np.zeros(int(365 * 24 * 3600 / timestep))

            for n in list_no_th_esys:
                build = self.city.node[n]['entity']

                th_lhn_power += build.get_space_heating_power_curve()
                th_lhn_power += build.get_dhw_power_curve()

            # Estimate energy network losses

            #  Get lhn network temperatures, env. temperature and diameter

            #  TODO: Implement better way to extract LHN pipe data instead of
            #  TODO: Choosing from first node

            ref_id = list_no_th_esys[0]

            #  Identify neighbors of first building
            list_neighb = nx.neighbors(G=self.city, n=ref_id)

            temp_vl = None

            #  Extract data
            for n in list_neighb:

                if 'network_type' in self.city.edge[ref_id][n]:

                    if (self.city.edge[ref_id][n]['network_type'] == 'heating'
                        or self.city.edge[ref_id][n][
                            'network_type'] == 'heating_and_deg'):
                        #  Extract lhn data
                        temp_vl = self.city.edge[ref_id][n]['temp_vl']
                        temp_rl = self.city.edge[ref_id][n]['temp_rl']
                        d_i = self.city.edge[ref_id][n]['d_i']

                        #  Estimate u-value of pipe in W/mK
                        u_value = dimnet.estimate_u_value(d_i)
                        break

            if temp_vl is None:
                msg = 'Could not find network of type heating or network' \
                      ' does not have temp_vl as attribute!'
                raise AssertionError(msg)

            # Get LHN network length
            list_lhn_weights = \
                list(self.city.edges_iter(nbunch=list_lhn_build_ids,
                                          data='weight'))
            # print(list_lhn_weights)

            #  Sum up weights to get total network lenght
            lhn_len = 0
            for tup_lhn in list_lhn_weights:
                lhn_len += tup_lhn[2]

            print('Total LHN network length in m: ')
            print(round(lhn_len, 0))
            print()

            #  Estimate heat pipe losses per timestep, where LHN is used
            temp_env = self.city.environment.temp_ground

            q_lhn_loss_if = u_value * lhn_len * (temp_vl - temp_env)
            q_lhn_loss_rf = u_value * lhn_len * (temp_rl - temp_env)

            q_lhn_loss = q_lhn_loss_if + q_lhn_loss_rf

            print('Total heating power loss of LHN in kW:')
            print(round(q_lhn_loss / 1000, 2))
            print()

            #  Add LHN losses to total thermal power demand
            th_lhn_power += q_lhn_loss

            #  Add LHN electric power demand for pumps
            #  TODO: Add pump el. power demand calculation

            #  Hand over network energy demand to feeder node buildings
            #  and solve thermal energy balance
            #  ##########################################################

            th_lhn_power_remain = copy.deepcopy(th_lhn_power)

            for n in list_th_esys:

                build = self.city.node[n]['entity']

                #  Solve thermal energy balance for single building with
                #  remaining LHN power demand
                beb.calc_build_therm_eb(build=build,
                                        id=n,
                                        th_lhn_pow_rem=th_lhn_power)

        #  Electrical energy balance of subcity (deg subcities)

            #  Share with deg

            #  Single el. energy balance for remaining buildings


if __name__ == '__main__':

    this_path = os.path.dirname(os.path.abspath(__file__))

    import pycity_calc.cities.scripts.city_generator.city_generator as citygen
    import pycity_calc.cities.scripts.overall_gen_and_dimensioning as overall

    this_path = os.path.dirname(os.path.abspath(__file__))

    #  Check requirements for pycity_deap
    pycity_deap = False

    try:
        #  Try loading city pickle file
        filename = 'city_clust_simple_with_esys.pkl'
        file_path = os.path.join(this_path, 'input', filename)
        city_object = pickle.load(open(file_path, mode='rb'))

    except:
        print('Could not load city pickle file. Going to generate a new one.')
        #  # Userinputs
        #  #----------------------------------------------------------------------

        #  Generate environment
        #  ######################################################
        year = 2010
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

        city_object = overall.run_overall_gen_and_dim(timestep=timestep,
                                                      year=year,
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

        # Save new pickle file
        filename = 'city_clust_simple_with_esys.pkl'
        file_path = os.path.join(this_path, 'input', filename)
        pickle.dump(city_object, open(file_path, mode='wb'))

    # Upscale boiler size of building 1006
    # city_object.node[1006]['entity'].bes.boiler.qNominal *= 10
    # city_object.node[1006]['entity'].bes.tes.capacity *= 10
    # city_object.node[1006]['entity'].bes.tes.t_current = 80
    #
    # print(city_object.node[1006]['entity'].bes.boiler.qNominal)
    # print(city_object.node[1006]['entity'].bes.tes.capacity)
    # print(city_object.node[1006]['entity'].bes.tes.t_current)
    #
    # sh_power = city_object.node[1006]['entity'].get_space_heating_power_curve()
    # dhw_power = city_object.node[1006]['entity'].get_electric_power_curve()
    #
    # import matplotlib.pyplot as plt
    #
    # plt.plot(sh_power)
    # plt.plot(dhw_power)
    # plt.show()
    # plt.close()

    # Construct energy balance
    energy_balance = CityEBCalculator(city=city_object)

    #  Calc. city energy balance
    energy_balance.calc_city_energy_balance()
