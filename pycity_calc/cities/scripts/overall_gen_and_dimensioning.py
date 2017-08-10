#!/usr/bin/env python
# coding=utf-8
"""
Script to generate city district with streets, energy networks and energy
systems (executing city_generator, street_generator, energy_networks_generator
and energy_sys_generator in a row).
"""

import os
import pickle

import pycity_calc.cities.scripts.city_generator.city_generator as citygen
import pycity_calc.cities.scripts.street_generator.street_generator as strgen
import pycity_calc.cities.scripts.energy_network_generator as enetgen
import pycity_calc.cities.scripts.energy_sys_generator as esysgen
import pycity_calc.visualization.city_visual as citvis


def run_overall_gen_and_dim(timestep, year, location, th_gen_method,
                            el_gen_method,
                            district_data, gen_str,
                            str_node_path,
                            str_edge_path,
                            gen_e_net,
                            network_path,
                            gen_esys,
                            esys_path,
                            use_dhw=False,
                            dhw_method=2,
                            dhw_dim_esys=False,
                            try_path=None,
                            generation_mode=0,
                            eff_factor=0.85,
                            save_path=None,
                            show_city=False,
                            altitude=55,
                            do_normalization=True,
                            dhw_volumen=None,
                            plot_pycity_calc=False,
                            slp_manipulate=True,
                            call_teaser=False,
                            teaser_proj_name='pycity',
                            do_log=True, log_path=None,
                            air_vent_mode=1,
                            vent_factor=0.5,
                            t_set_heat=20,
                            t_set_cool=70,
                            t_night=16,
                            vdi_sh_manipulate=False,
                            el_random=False, dhw_random=False,
                            prev_heat_dev=True, season_mod=None,
                            merge_windows=False, new_try=False):
    """
    Peform overall generation and dimensioning of city object with
    street networks, energy networks and energy systems.

    Parameters
    ----------
    timestep : int
        Timestep for environment
    year : int
        Year of environment
    location : tuple (of floats)
        (latitude, longitude) of the simulated system's position.
    th_gen_method : int
        Thermal load profile generation method
        1 - Use SLP
        2 - Load Modelica simulation output profile (only residential)
            Method 2 is only used for residential buildings. For non-res.
            buildings, SLPs are generated instead
        3 - Uses TEASER VDI 6007 simulation core. Requires TEASER installation
    el_gen_method : int
        Electrical generation method
        1 - Use SLP
        2 - Generate stochastic load profile (only valid for residential
        building). Requires number of occupants.
    district_data : np.array
        Numpy 2d array with city district data
    gen_str : bool
        Defines, if street networks should be generated
    str_node_path : str
        Path to street node file
    str_edge_path : str
        Path to street edge file
    gen_e_net : bool
        Defines, if energy networks should be generated
    network_path : str
        Path to energy network data file (required if gen_e_net=True)
    gen_esys : bool
        Defines, if energy systems should be added to city
    esys_path : str
        Path to energy system input file
    use_dhw : bool, optional
        Defines if domestic hot water profiles should be generated
        within city generator (default: False)
    dhw_method : int, optional
        Defines method for dhw profile generation (default: 2)
        Only relevant if use_dhw=True. Options:
        - 1: Generate profiles via Annex 42
        - 2: Generate stochastic dhw profiles
    dhw_dim_esys : bool, optional
        Defines, if hot water thermal energy demand should be taken into
        account. (default: False)
        If False, only space heating power demand is taken into account.
    try_path : str, optional
        Path to TRY weather file (default: None). If None is set, used
        TRY 2010 for region 5 in Germany
    generation_mode : int
        Integer to define method to generate city district
        (so far, only csv/txt file import has been implemented)
        generation_mode = 0: Load data from csv/txt file (tab seperated)
    eff_factor : float, optional
         Efficiency factor of thermal boiler system (default: 0.85)
         Only necessary, if final energy is used as input within input txt to
         reconvert it to net thermal energy.
    save_path : str, optional
        Defines name of output file (default: None). If set to None,
        city file is not saved. If not None, file is pickled under given name
    show_city : bool, optional
        Defines, if city should be plotted (default: False)
    altitude : float, optional
        Altitude of location in m (default: 55 - City of Bottrop)
    do_normalization : bool, optional
        Defines, if stochastic profile (el_gen_method=2) should be
        normalized to given annualDemand value (default: True).
        If set to False, annual el. demand depends on stochastic el. load
        profile generation. If set to True, does normalization with
        annualDemand
    dhw_volumen : float, optional
        Volume of domestic hot water in liter per capita and day
        (default: None).
    plot_pycity_calc : bool, optional
        Defines, if city district should be visualized (default: False)
    slp_manipulate : bool, optional
        Defines, if thermal space heating SLP profile should be modified
        (default: True). Only used for residential buildings!
        Only relevant, if th_gen_method == 1
        True - Do manipulation
        False - Use original profile
        Sets thermal power to zero in time spaces, where average daily outdoor
        temperature is equal to or larger than 12 °C. Rescales profile to
        original demand value.
    call_teaser : bool, optional
        Defines, if teaser should be called to generate typeBuildings
        (currently, residential typeBuildings only).
        (default: False)
        If set to True, generates typeBuildings and add them to building node
        as attribute 'type_building'
    teaser_proj_name : str, optional
        TEASER project name (default: 'pycity'). Only relevant, if call_teaser
        is set to True
    do_log : bool, optional
        Defines, if log file of inputs should be generated (default: True)
    log_path : str, optional
        Path to log file (default: None). If set to None, saves log to
        .../output
    air_vent_mode : int
        Defines method to generation air exchange rate for VDI 6007 simulation
        Options:
        0 : Use constant value (vent_factor in 1/h)
        1 : Use deterministic, temperature-dependent profile
        2 : Use stochastic, user-dependent profile
    vent_factor : float, optional
        Ventilation rate factor in 1/h (default: 0.5). Only used, if
        array_vent_rate is 0
    t_set_heat : float, optional
        Heating set temperature in degree Celsius. If temperature drops below
        t_set_heat, model is going to be heated up. (default: 20)
        (Related to constraints for res. buildings in DIN V 18599)
    t_set_cool : float, optional
        Cooling set temperature in degree Celsius. If temperature rises above
        t_set_cool, model is going to be cooled down. (default: 70)
    t_night : float, optional
        Night set back temperature in degree Celsius (default: 16)
        (Related to constraints for res. buildings in DIN V 18599)
    vdi_sh_manipulate : bool, optional
        Defines, if VDI 6007 thermal space heating load curve should be
        normalized to match given annual space heating demand in kWh
        (default: False)
    el_random : bool, optional
        Defines, if annual, eletrical demand value for normalization of
        el. load profile should randomly diverge from reference value
        within specific boundaries (default: False).
        If False: Use reference value for normalization
        If True: Allow generating values that is different from reference value
    dhw_random : bool, optional
        Defines, if hot water volume per person and day value should be
        randomized by choosing value from gaussian distribution (20 %
        standard deviation) (default: False)
        If True: Randomize value
        If False: Use reference value
    prev_heat_dev : bool, optional
        Defines, if heating devices should be prevented within chosen
        appliances (default: True). If set to True, DESWH, E-INST,
        Electric shower, Storage heaters and Other electric space heating
        are set to zero. Only relevant for el_gen_method == 2
    season_mod : float, optional
        Float to define rescaling factor to rescale annual lighting power curve
        with cosine wave to increase winter usage and decrease summer usage.
        Reference is maximum lighting power (default: None). If set to None,
        do NOT perform rescaling with cosine wave
    merge_windows : bool, optional
        Defines TEASER project setting for merge_windows_calc
        (default: False). If set to False, merge_windows_calc is set to False.
        If True, Windows are merged into wall resistances.
    new_try : bool, optional
        Defines, if TRY dataset have been generated after 2017 (default: False)
        If False, assumes that TRY dataset has been generated before 2017.
        If True, assumes that TRY dataset has been generated after 2017 and
        belongs to the new TRY classes. This is important for extracting
        the correct values from the TRY dataset!

    Returns
    -------
    city_object : object
        City object of pycity_calc
    """

    #  Generate city district
    city_object = citygen.run_city_generator(generation_mode=generation_mode,
                                             timestep=timestep,
                                             year=year, location=location,
                                             th_gen_method=th_gen_method,
                                             el_gen_method=el_gen_method,
                                             use_dhw=use_dhw,
                                             dhw_method=dhw_method,
                                             district_data=district_data,
                                             pickle_city_filename=None,
                                             eff_factor=eff_factor,
                                             show_city=show_city,
                                             try_path=try_path,
                                             altitude=altitude,
                                             dhw_volumen=dhw_volumen,
                                             do_normalization=do_normalization,
                                             slp_manipulate=slp_manipulate,
                                             call_teaser=call_teaser,
                                             teaser_proj_name=teaser_proj_name,
                                             do_log=do_log, log_path=log_path,
                                             air_vent_mode=air_vent_mode,
                                             vent_factor=vent_factor,
                                             t_set_heat=t_set_heat,
                                             t_set_cool=t_set_cool,
                                             t_night=t_night,
                                             vdi_sh_manipulate=
                                             vdi_sh_manipulate,
                                             el_random=el_random,
                                             dhw_random=dhw_random,
                                             prev_heat_dev=prev_heat_dev,
                                             season_mod=season_mod,
                                             merge_windows=merge_windows,
                                             new_try=new_try,
                                             do_save=False)

    #  Generate street networks
    if gen_str:
        assert str_node_path is not None
        assert str_edge_path is not None

        #  Get street network data
        name_list, pos_list, edge_list = \
            strgen.load_street_data_from_csv(path_str_nodes=str_node_path,
                                             path_str_edges=str_edge_path)

        #  Add street network to city_object
        strgen.add_street_network_to_city(city_object, name_list, pos_list,
                                          edge_list)

    # Generate energy networks, if desired
    if gen_e_net:
        #  Load energy networks planing data
        dict_e_net_data = enetgen.load_en_network_input_data(network_path)

        #  Add energy networks to city
        enetgen.add_energy_networks_to_city(city=city_object,
                                            dict_data=dict_e_net_data)

    # Generate energy systems for city district
    if gen_esys:
        #  Load energy networks planing data
        list_esys = esysgen.load_enersys_input_data(esys_path)

        #  Generate energy systems
        esysgen.gen_esys_for_city(city=city_object, list_data=list_esys,
                                  dhw_scale=dhw_dim_esys)

    # Plot city
    if plot_pycity_calc:
        citvis.plot_city_district(city=city_object, plot_lhn=True,
                                  plot_deg=True,
                                  plot_street=True, plot_esys=True)

    # Pickle and dump city object
    if save_path is not None:
        #  Save city pickle file
        pickle.dump(city_object, open(save_path, mode='wb'))

    return city_object


if __name__ == '__main__':
    this_path = os.path.dirname(os.path.abspath(__file__))

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

    txt_path = os.path.join(this_path, 'city_generator', 'input', filename)

    #  Define city district output file
    save_filename = 'city_clust_simple_with_esys.p'
    save_path = os.path.join(this_path, 'output_overall', save_filename)

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
    do_log = True  # True, generate log file
    log_path = os.path.join(this_path, 'output_overall',
                            'city_gen_overall_log.txt')

    #  Generate street networks
    gen_str = True  # True - Generate street network

    #  Street node and edges input filenames
    str_node_filename = 'street_nodes_cluster_simple.csv'
    str_edge_filename = 'street_edges_cluster_simple.csv'

    #  Load street data from csv
    str_node_path = os.path.join(this_path, 'street_generator', 'input',
                                 str_node_filename)
    str_edge_path = os.path.join(this_path, 'street_generator', 'input',
                                 str_edge_filename)

    #  Add energy networks to city
    gen_e_net = True  # True - Generate energy networks

    #  Path to energy network input file (csv/txt; tab separated)
    network_filename = 'city_clust_simple_networks.txt'
    network_path = os.path.join(this_path, 'input_en_network_generator',
                                network_filename)

    #  Add energy systems to city
    gen_esys = True  # True - Generate energy networks

    #  Path to energy system input file (csv/txt; tab separated)
    esys_filename = 'city_clust_simple_enersys.txt'
    esys_path = os.path.join(this_path, 'input_esys_generator',
                             esys_filename)

    #  #----------------------------------------------------------------------

    #  Load district_data file
    district_data = citygen.get_district_data_from_txt(txt_path)

    run_overall_gen_and_dim(timestep=timestep,
                            year=year,
                            location=location,
                            try_path=try_path, th_gen_method=th_gen_method,
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
                            do_log=do_log, log_path=log_path,
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
