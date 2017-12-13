#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script checks, if city object fulfills all energy balance requirements
"""
from __future__ import division

import os
import pickle
import warnings

import pycity_calc.toolbox.networks.network_ops as netop



class EnergySupplyException(Exception):
    def __init__(self, message):
        """
        Constructor of own Energy Supply Exception

        Parameters
        ----------
        message : str
            Error message
        """

        super(EnergySupplyException, self).__init__(message)  # pragma: no cover

def check_eb_build_requ(build):
    """
    Check requirements for energy balance for single building.
    Raises AssertionError, if requirements are not fulfilled.

    Parameters
    ----------
    build : object
        Extended building object of pyCity_calc
    """

    #  Dummy value for status (assumes missing thermal supply, until
    #  thermal supply or lhn is found)
    status_okay = False

    #  Dummy value for TES (assumes correct TES usage)
    tes_okay = True

    #  Check if building has bes
    if build.hasBes is True:

        #  Check, if at least one thermal energy supply system exists
        if build.bes.hasBoiler is True:
            status_okay = True

        if build.bes.hasChp is True:
            status_okay = True
            if build.bes.hasTes is False:  # pragma: no cover
                tes_okay = False

        if build.bes.hasHeatpump is True:
            status_okay = True
            if build.bes.hasTes is False:  # pragma: no cover
                tes_okay = False
            if (build.bes.hasElectricalHeater is False
                and build.bes.hasBoiler is False):  # pragma: no cover
                msg = 'Building does have heatpump, but no electric heater' \
                      ' or boiler for hot water supply! If your building ' \
                      'has hot water demand, the energy balance is going to ' \
                      'crash!'
                warnings.warn(msg)

        if build.bes.hasElectricalHeater is True:
            status_okay = True

    if status_okay is False:  # pragma: no cover
        msg = 'Building has no thermal energy' \
              ' supply! Cannot run' \
              ' energy balance!'
        raise EnergySupplyException(msg)

    if tes_okay is False:  # pragma: no cover
        msg = 'Building has CHP or HP, but no TES, which is required for ' \
              'energy balance calculation!'
        raise EnergySupplyException(msg)

def check_eb_requirements(city, pycity_deap=False):
    """
    Check, if city fulfills all requirements to be used in energy balance
    calculation (such as thermal energy supply of all buildings, either
    provided by heating network and/or energy supply unit...),
    Raises AssertionError, if requirements are not met.

    Parameters
    ----------
    city : object
        City object of pyCity_calc
    pycity_deap : bool, optional
        Check pycity_deap requirements (all buildings need to hold bes!)
    """

    has_lhn = False  # Dummy value (assumes, that no LHN exists)

    #  Get list of all building ids
    list_build_ids = city.get_list_build_entity_node_ids()

    #  Loop over all buildings and check, if energy supply is present
    for id in list_build_ids:
        build = city.nodes[id]['entity']

        #  Dummy value for status (assumes missing thermal supply, until
        #  thermal supply or lhn is found)
        status_okay = False

        #  Check if building has bes
        if build.hasBes is True:

            #  Check, if at least one thermal energy supply system exists
            if build.bes.hasBoiler is True:
                status_okay = True
            if build.bes.hasChp is True:
                status_okay = True
            if build.bes.hasHeatpump is True:
                status_okay = True
            if build.bes.hasElectricalHeater is True:
                status_okay = True

        else:
            if pycity_deap:  # pragma: no cover
                msg = 'Building with id ' + str(id) + ' has no bes' \
                                                      ' which is required' \
                                                      ' for pycity deap!'
                raise AssertionError(msg)

        #  Check, if building is connected to heating network
        #  This part is not included into else statement, as buildings
        #  might hold BES without having any thermal supply system (and
        #  they still might be connected to an lhn system)

        #  Get neighbour nodes, if existent
        list_neigh = city.neighbors(id)

        #  Check, if at least one edge is of type
        for i in list_neigh:
            if 'network_type' in city.edges[i, id]:
                if (city.edges[i, id]['network_type'] == 'heating' or
                    city.edges[id, i]['network_type'] == 'heating' or
                    city.edges[i, id]['network_type'] == 'heating_and_deg' or
                    city.edges[id, i]['network_type'] == 'heating_and_deg'):
                    status_okay = True
                    has_lhn = True
                    break

        if status_okay is False:  # pragma: no cover
            msg = 'Building with id ' \
                  + str(id) + ' has no thermal energy supply (no th. energy' \
                              ' system and no LHN connection)! ' \
                              'Cannot run energy balance!'
            raise EnergySupplyException(msg)

    if has_lhn:
        #  Check, if each LHN network has, at least, one feeder node

        #  Get list of lists of lhn connected buildings
        list_lists_lhn = \
            netop.get_list_with_energy_net_con_node_ids(city=city,
                                                        build_node_only=True)

        for list_sub_lhn in list_lists_lhn:
            assert len(list_sub_lhn) > 1

        list_stati = []
        list_lhn_no_sup =[]

        for list_lhn in list_lists_lhn:
            #  Dummy value (assumes, that no feeder exists in LHN)
            lhn_status = False

            for n in list_lhn:
                build = city.nodes[n]['entity']

                #  Check if building has bes
                if build.hasBes is True:

                    #  Check, if at least one thermal energy supply system
                    #  exists
                    if build.bes.hasBoiler is True:
                        lhn_status = True
                        list_stati.append(lhn_status)
                        break
                    if build.bes.hasChp is True:
                        lhn_status = True
                        list_stati.append(lhn_status)
                        break
                    if build.bes.hasElectricalHeater is True:
                        lhn_status = True
                        list_stati.append(lhn_status)
                        break
            list_stati.append(lhn_status)
            list_lhn_no_sup.append(list_lhn)

        for status in list_stati:
            msg = ''
            if status is False:  # pragma: no cover
                for list_lhn in list_lhn_no_sup:
                    for n in list_lhn:
                        print('n', n)
                        msg += 'n ' + str(n) + ' \n'
                        build = city.nodes[n]['entity']
                        if build.hasBes:
                            bes = build.bes
                            if bes.hasBoiler:
                                print('Has boiler')
                                msg += 'has boiler' + ' \n'
                            if bes.hasChp:
                                print('Has CHP')
                                msg += 'has CHP' + ' \n'
                            if bes.hasElectricalHeater:
                                print('Has EH')
                                msg += 'has EH' + ' \n'
                            if bes.hasHeatpump:
                                print('Has HP')
                                msg += 'has HP' + ' \n'
                            if bes.hasTes:
                                print('Has TES')
                                msg += 'has TES' + ' \n'

                msg += 'LHN network has no feeder node (LHN network ' \
                      'with node ids ' + str(list_lhn_no_sup) + '.'
                raise EnergySupplyException(msg)

    print('Energy balance input check has been sucessful')


if __name__ == '__main__':

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
        th_gen_method = 1
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
        el_random = True

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
        use_dhw = False  # Only relevant for residential buildings

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
        dhw_random = True

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
        air_vent_mode = 1
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

        # Save new pickle file
        filename = 'city_clust_simple_with_esys.pkl'
        file_path = os.path.join(this_path, 'input', filename)
        pickle.dump(city_object, open(file_path, mode='wb'))

    check_eb_requirements(city=city_object, pycity_deap=pycity_deap)
