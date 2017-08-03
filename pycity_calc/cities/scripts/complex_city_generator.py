#!/usr/bin/env python
# coding=utf-8
"""
Script to generate city district with buildings and street network
"""

import os
import pickle
import warnings
import matplotlib.pyplot as plt

import pycity_calc.cities.scripts.city_generator.city_generator as citygen
import pycity_calc.cities.scripts.street_generator.street_generator as strgen
import pycity_calc.visualization.city_visual as citvis


def gen_city_with_street_network_from_csvfile(timestep, year, location,
                                              th_gen_method,
                                              el_gen_method,
                                              district_data,
                                              str_node_path,
                                              str_edge_path,
                                              use_dhw=False,
                                              dhw_method=1,
                                              try_path=None,
                                              generation_mode=0,
                                              eff_factor=0.85,
                                              save_city=None,
                                              show_city=False,
                                              altitude=55,
                                              do_normalization=True,
                                              dhw_volumen=64,
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
                                              el_random=False,
                                              dhw_random=False,
                                              prev_heat_dev=True,
                                              season_mod=None,
                                              merge_windows=False,
                                              new_try=False):
    """
    Run city generator and street generator to generate PyCity_Calc
    city object

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
    el_gen_method : int
        Electrical generation method
        1 - Use SLP
        2 - Generate stochastic load profile (only valid for residential
        building). Requires number of occupants.
    district_data : ndarray
        Numpy 2d-array with city district data (each column represents
        different parameter, see annotations)
    str_node_path : str
        Path to street node file
    str_edge_path : str
        Path to street edge file
    use_dhw : bool, optional
        Defines if domestic hot water profiles should be generated.
        (default: False)
    dhw_method : int, optional
        Defines method for dhw profile generation (default: 1)
        Only relevant if use_dhw=True. Options:
        - 1: Generate profiles via Annex 42
        - 2: Generate stochastic dhw profiles
    try_path : str, optional
        Path to TRY weather file (default: None). If None is set, used
        TRY 2010 for region 5 in Germany
    generation_mode : int
        Integer to define method to generate city district
        (so far, only csv/txt file import has been implemented)
        generation_mode = 0: Load data from csv/txt file (tab seperated)
    eff_factor : float, optional
         Efficiency factor of thermal boiler system (default: 0.85)
    save_city : str, optional
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
        (default: 64). Only relevant for dhw method=1 (Annex 42)
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
        array_vent_rate is None (otherwise, array_vent_rate array is used)
    t_set_heat : float, optional
        Heating set temperature in degree Celsius. If temperature drops below
        t_set_heat, model is going to be heated up. (default: 20)
    t_set_cool : float, optional
        Cooling set temperature in degree Celsius. If temperature rises above
        t_set_cool, model is going to be cooled down. (default: 70)
    t_night : float, optional
        Night set back temperature in degree Celsius (default: 16)
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

    Annotations
    -----------
    Non-residential building loads are automatically generated via SLP
    (even if el_gen_method is set to 2). Furthermore, dhw profile generation
    is automatically neglected (only valid for residential buildings)

    Electrical load profiles of residential buildings without occupants
    are automatically generated via SLP (even if el_gen_method is set to 2)

    File structure (district_data np.array)
    Columns:
    1:  id (int)
    2:  x in m (float)
    3:  y in m (float)
    4:  building_type (int, e.g. 0 for residential building)
    5:  net floor area in m2 (float)
    6:  Year of construction (int, optional)
    7:  Year of modernization (int, optional)
    8:  Annual (final) thermal energy demand in kWh (float, optional)
    9:  Annual electrical energy demand in kWh (float, optional)
    10: Usable pv roof area in m2 (float, optional)
    11: Number of apartments (int, optional)
    12: Total number of occupants (int, optional)
    13: Number of floors above the ground (int, optional)
    14: Average Height of floors (float, optional)
    15: If building has a central AHU or not (boolean, optional)
    16: Residential layout (int, optional, e.g. 0 for compact)
    17: Neighbour Buildings (int, optional)
    18: Type of attic (int, optional, e.g. 0 for flat roof)
    19: Type of cellar (int, optional, e.g. 1 for non heated cellar)
    20: Dormer (int, optional, 0: no dormer/ 1: dormer)
    21: Construction Type(heavy/light, optional)
    22: Method_3_nb (for usage of measured, weekly non-res. el. profile
    (optional)
    23: Method_4_nb (for usage of measured, annual non-res. el. profile
    (optional)
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
                                             do_log=do_log,
                                             log_path=log_path,
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
                                             new_try=new_try)

    #  Get street network data
    name_list, pos_list, edge_list = \
        strgen.load_street_data_from_csv(path_str_nodes=str_node_path,
                                         path_str_edges=str_edge_path)

    #  Add street network to city_object
    strgen.add_street_network_to_city(city_object, name_list, pos_list,
                                      edge_list)

    if save_city:
        this_path = os.path.dirname(os.path.abspath(__file__))
        path_to_save_to = os.path.join(this_path, 'output_complex_city_gen',
                                       save_city)
        save_pickle_city_file(city_object, path_to_save_to)

    return city_object


def save_pickle_city_file(city, path_to_save):
    """
    Saves city object as pickle file.

    Parameters
    ----------
    city : object
        City object
    path_to_save : str
        Path to save pickle file
    """
    try:
        #  Pickle and dump city objects
        pickle.dump(city, open(path_to_save, 'wb'))
        print('Pickled and dumped city object at', path_to_save)
    except:
        warnings.warn('Could not pickle and save city object')


def load_pickled_city_file(path_to_file):
    """
    Returns city object by loading pickled city file.

    Parameters
    ----------
    path_to_file : str
        Path to city pickled file

    Returns
    -------
    city : object
        City object
    """
    city = pickle.load(open(path_to_file, 'rb'))
    return city


if __name__ == '__main__':
    #  # Userinputs
    #  #----------------------------------------------------------------------

    #  Generate environment
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
    dhw_volumen = 64  # Only relevant for residential buildings

    #  Randomize choosen dhw_volume reference value by selecting new value
    #  from gaussian distribution with 20 % standard deviation
    dhw_random = True

    #  Input file names and pathes
    #  ######################################################
    #  Plot city district with pycity_calc visualisation
    plot_pycity_calc = True

    #  Efficiency factor of thermal energy systems
    #  Used to convert input values (final energy demand) to net energy demand
    eff_factor = 0.85

    #  Define city district input data filename
    filename = 'city_clust_simple.txt'

    #  Define ouput data filename (pickled city object)
    save_city = 'city_clust_simple.pkl'

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
    #  merge_windows : bool, optional
    #  Defines TEASER project setting for merge_windows_calc
    #  (default: False). If set to False, merge_windows_calc is set to False.
    #   If True, Windows are merged into wall resistances.

    #  Names of street node and edge files
    str_node_filename = 'street_nodes_cluster_simple.csv'
    str_edge_filename = 'street_edges_cluster_simple.csv'

    #  Load street data from csv
    this_path = os.path.dirname(os.path.abspath(__file__))

    txt_path = os.path.join(this_path, 'city_generator', 'input', filename)

    str_node_path = os.path.join(this_path, 'street_generator', 'input',
                                 str_node_filename)
    str_edge_path = os.path.join(this_path, 'street_generator', 'input',
                                 str_edge_filename)

    #  Log file
    do_log = True  # True, generate log file
    log_file_name = str('log_' + filename)

    log_path = os.path.join(this_path, 'output_complex_city_gen',
                            log_file_name)

    #  #----------------------------------------------------------------------

    print('Run complex city generator for ', filename)

    #  Load district_data file
    district_data = citygen.get_district_data_from_txt(txt_path)

    city_object = \
        gen_city_with_street_network_from_csvfile(timestep=timestep,
                                                  year=year,
                                                  location=location,
                                                  try_path=try_path,
                                                  th_gen_method=th_gen_method,
                                                  el_gen_method=el_gen_method,
                                                  use_dhw=use_dhw,
                                                  dhw_method=dhw_method,
                                                  district_data=district_data,
                                                  str_node_path=str_node_path,
                                                  str_edge_path=str_edge_path,
                                                  generation_mode=0,
                                                  eff_factor=eff_factor,
                                                  save_city=save_city,
                                                  altitude=altitude,
                                                  do_normalization=do_normalization,
                                                  dhw_volumen=dhw_volumen,
                                                  slp_manipulate=slp_manipulate,
                                                  call_teaser=call_teaser,
                                                  teaser_proj_name=
                                                  teaser_proj_name,
                                                  do_log=do_log,
                                                  log_path=log_path,
                                                  air_vent_mode=air_vent_mode,
                                                  vent_factor=vent_factor,
                                                  t_set_heat=t_set_heat,
                                                  t_set_cool=t_set_cool,
                                                  t_night=t_set_night,
                                                  vdi_sh_manipulate=
                                                  vdi_sh_manipulate,
                                                  el_random=el_random,
                                                  dhw_random=dhw_random,
                                                  prev_heat_dev=prev_heat_dev,
                                                  season_mod=season_mod,
                                                  merge_windows=merge_windows,
                                                  new_try=new_try)

    if save_city:  # Load pickle city file
        this_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(this_path, 'output_complex_city_gen',
                                 save_city)
        print('Try loading file from path:', file_path)
        city = load_pickled_city_file(file_path)
        print('Loaded city object:', city)
        print('Node data:', city.nodes(data=True))

    if plot_pycity_calc:
        citvis.plot_city_district(city=city, plot_street=True, offset=None,
                                  plot_build_labels=True,
                                  equal_axis=False, font_size=16,
                                  plt_title=None,
                                  x_label='x-Position in m',
                                  y_label='y-Position in m',
                                  show_plot=True)

        aggr_sp_heat = city.get_aggr_space_h_power_curve()
        aggr_dhw = city.get_aggr_dhw_power_curve()

        aggr_th_load_curve = aggr_sp_heat + aggr_dhw

        print(aggr_th_load_curve)

        #  Sort descending
        aggr_th_load_curve.sort()
        annual_power_curve = aggr_th_load_curve[::-1]

        plt.plot(annual_power_curve / 1000)

        plt.rc('text', usetex=False)
        font = {'family': 'serif', 'size': 24}
        plt.rc('font', **font)

        plt.xlabel('Time in hours')
        plt.ylabel('Thermal load in kW')
        plt.grid()
        plt.tight_layout()
        plt.show()
