# coding=utf-8
"""
Script to generate city object.
"""

import os
import math
import numpy as np
import pickle
import warnings
import random
import datetime
import shapely.geometry.point as point

import pycity.classes.Weather as weath
import pycity.classes.demand.SpaceHeating as SpaceHeating
import pycity.classes.demand.ElectricalDemand as ElectricalDemand
import pycity.classes.demand.Apartment as Apartment
import pycity.classes.demand.DomesticHotWater as DomesticHotWater
import pycity.classes.demand.Occupancy as occup

import pycity_calc.environments.timer as time
import pycity_calc.environments.market as price
import pycity_calc.environments.environment as env
import pycity_calc.environments.co2emissions as co2
import pycity_calc.buildings.building as build_ex
import pycity_calc.cities.city as city
import pycity_calc.visualization.city_visual as citvis
import pycity_calc.toolbox.dimensioning.slp_th_manipulator as slpman
import pycity_calc.toolbox.teaser_usage.teaser_use as tusage
import pycity_calc.toolbox.mc_helpers.user.user_unc_sampling as usunc

try:
    import teaser.logic.simulation.VDI_6007.weather as vdiweather
except:
    msg = 'Could not import TEASER package. If you need to use it, install ' \
          'it via pip "pip install TEASER". Alternatively, you might have ' \
          'run into trouble with XML bindings in TEASER. This can happen ' \
          'if you try to re-import TEASER within an active Python console.' \
          'Please close the active Python console and open another one. Then' \
          ' try again.'
    warnings.warn(msg)


def load_data_file_with_spec_demand_data(filename):
    """
    Function loads and returns data from
    .../src/data/BaseData/Specific_Demand_Data/filename.
    Filename should hold float (or int) values.
    Other values (e.g. strings) will be loaded as 'nan'.

    Parameter
    ---------
    filename : str
        String with name of file, e.g. 'district_data.txt'

    Returns
    -------
    dataset : numpy array
        Numpy array with data
    """
    src_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname
        (
        os.path.abspath(
            __file__)))))
    input_data_path = os.path.join(src_path, 'data', 'BaseData',
                                   'Specific_Demand_Data', filename)

    dataset = np.genfromtxt(input_data_path, delimiter='\t', skip_header=1)
    return dataset


def convert_th_slp_int_and_str(th_slp_int):
    """
    Converts thermal slp type integer into string

    Parameters
    ----------
    th_slp_int : int
        SLP type integer number

    Returns
    -------
    th_slp_tag : str
        SLP type string

    Annotations
    -----------
    - `HEF` : Single family household
    - `HMF` : Multi family household
    - `GBA` : Bakeries
    - `GBD` : Other services
    - `GBH` : Accomodations
    - `GGA` : Restaurants
    - `GGB` : Gardening
    - `GHA` : Retailers
    - `GHD` : Summed load profile business, trade and services
    - `GKO` : Banks, insurances, public institutions
    - `GMF` : Household similar businesses
    - `GMK` : Automotive
    - `GPD` : Paper and printing
    - `GWA` : Laundries
    """
    slp_th_profile_dict_tag = {0: 'HEF',
                               1: 'HMF',
                               2: 'GMF',
                               3: 'GMK',
                               4: 'GPD',
                               5: 'GHA',
                               6: 'GBD',
                               7: 'GKO',
                               8: 'GBH',
                               9: 'GGA',
                               10: 'GBA',
                               11: 'GWA',
                               12: 'GGB',
                               13: 'GHD'}

    th_slp_tag = slp_th_profile_dict_tag[th_slp_int]
    return th_slp_tag


def convert_el_slp_int_and_str(el_slp_int):
    """
    Converts el slp type integer into string

    Parameters
    ----------
    el_slp_int : int
        SLP type integer number

    Returns
    -------
    el_slp_tag : str
        SLP type string

    Annotations
    -----------
    #     0:  H0 : Residential
    #     1:  G0 : Commercial
    #     2:  G1 : Commercial Mo-Sa 08:00 to 18:00
    #     3:  G2 : Commercial, mainly evening hours
    #     4:  G3 : Commercial 24 hours
    #     5:  G4 : Shop / hairdresser
    #     6:  G5 : Backery
    #     7:  G6 : Commercial, weekend
    #     8:  L0 : Farm
    #     9:  L1 : Farm, mainly cattle and milk
    #     10:  L2 : Other farming
    """
    slp_el_profile_dict_tag = {0: 'H0',
                               1: 'G0',
                               2: 'G1',
                               3: 'G2',
                               4: 'G3',
                               5: 'G4',
                               6: 'G5',
                               7: 'G6',
                               8: 'L0',
                               9: 'L1',
                               10: 'L2'}

    el_slp_tag = slp_el_profile_dict_tag[el_slp_int]
    return el_slp_tag


def convert_method_3_nb_into_str(method_3_nb):
    """
    Converts method_3_nb into string

    Parameters
    ----------
    method_3_nb : int
        Number of method 3

    Returns
    -------
    method_3_str : str
        String of method 3
    """

    dict_method_3 = {0: 'food_pro',
                     1: 'metal',
                     2: 'rest',
                     3: 'sports',
                     4: 'repair'}

    method_3_str = dict_method_3[method_3_nb]

    return method_3_str


def convert_method_4_nb_into_str(method_4_nb):
    """
    Converts method_4_nb into string

    Parameters
    ----------
    method_4_nb : int
        Number of method 4

    Returns
    -------
    method_4_str : str
        String of method 4
    """

    dict_method_4 = {0: 'metal_1', 1: 'metal_2', 2: 'warehouse'}

    method_4_str = dict_method_4[method_4_nb]

    return method_4_str


def constrained_sum_sample_pos(n, total):
    """
    Return a randomly chosen list of n positive integers summing to total.
    Each such list is equally likely to occur.

    Parameters
    ----------
    n : int
        Number of chosen integers
    total : int
        Sum of all entries of result list

    Returns
    -------
    results_list : list (of int)
        List with result integers, which sum up to value 'total'
    """

    dividers = sorted(random.sample(range(1, total), n - 1))
    return [a - b for a, b in zip(dividers + [total], [0] + dividers)]


def redistribute_occ(occ_list):
    """
    Redistribute occupants in occ_list, so that each apartment is having at
    least 1 person and maximal 5 persons.

    Parameters
    ----------
    occ_list

    Returns
    -------
    occ_list_new : list
        List holding number of occupants per apartment
    """

    occ_list_new = occ_list[:]

    if sum(occ_list_new) / len(occ_list_new) > 5:
        msg = 'Average number of occupants per apartment is higher than 5.' \
              ' This is not valid for usage of Richardson profile generator.'
        raise AssertionError(msg)

    # Number of occupants to be redistributed
    nb_occ_redist = 0

    #  Find remaining occupants
    #  ###############################################################
    for i in range(len(occ_list_new)):
        if occ_list_new[i] > 5:
            #  Add remaining occupants to nb_occ_redist
            nb_occ_redist += occ_list_new[i] - 5
            #  Set occ_list_new entry to 5 persons
            occ_list_new[i] = 5

    if nb_occ_redist == 0:
        #  Return original list
        return occ_list_new

    # Identify empty apartments and add single occupant
    #  ###############################################################
    for i in range(len(occ_list_new)):
        if occ_list_new[i] == 0:
            #  Add single occupant
            occ_list_new[i] = 1
            #  Remove occupant from nb_occ_redist
            nb_occ_redist -= 1

        if nb_occ_redist == 0:
            #  Return original list
            return occ_list_new

    # Redistribute remaining occupants
    #  ###############################################################
    for i in range(len(occ_list_new)):
        if occ_list_new[i] < 5:
            #  Fill occupants up with remaining occupants
            for j in range(5 - occ_list_new[i]):
                #  Add single occupant
                occ_list_new[i] += 1
                #  Remove single occupant from remaining sum
                nb_occ_redist -= 1

                if nb_occ_redist == 0:
                    #  Return original list
                    return occ_list_new

    if nb_occ_redist:
        raise AssertionError('Not all occupants could be distributed.'
                             'Check inputs and/or redistribute_occ() call.')


def generate_environment(timestep=3600, year=2010, try_path=None,
                         location=(51.529086, 6.944689), altitude=55,
                         new_try=False):
    """
    Returns environment object. Total number of timesteps is automatically
    generated for one year.

    Parameters
    ----------
    timestep : int
        Timestep in seconds
    year : int, optional
        Chosen year of analysis (default: 2010)
        (influences initial day for profile generation, market prices
        and co2 factors)
        If year is set to None, user has to define day_init!
    try_path : str, optional
        Path to TRY weather file (default: None)
        If set to None, uses default weather TRY file (2010, region 5)
    location : Tuple, optional
        (latitude , longitude) of the simulated system's position,
        (default: (51.529086, 6.944689) for Bottrop, Germany.
    altitude : float, optional
        Altitute of location in m (default: 55 - City of Bottrop)
    new_try : bool, optional
        Defines, if TRY dataset have been generated after 2017 (default: False)
        If False, assumes that TRY dataset has been generated before 2017.
        If True, assumes that TRY dataset has been generated after 2017 and
        belongs to the new TRY classes. This is important for extracting
        the correct values from the TRY dataset!

    Returns
    -------
    environment : object
        Environment object
    """

    #  Create environment
    timer = time.TimerExtended(timestep=timestep, year=year)

    weather = weath.Weather(timer, useTRY=True, pathTRY=try_path,
                            location=location, altitude=altitude,
                            new_try=new_try)

    prices = price.Market()
    co2em = co2.Emissions(year=year)

    environment = env.EnvironmentExtended(timer, weather, prices, location,
                                          co2em)
    return environment


def generate_res_building_single_zone(environment, net_floor_area,
                                      spec_th_demand,
                                      th_gen_method,
                                      el_gen_method,
                                      annual_el_demand=None,
                                      use_dhw=False,
                                      dhw_method=1, number_occupants=None,
                                      build_year=None, mod_year=None,
                                      build_type=None, pv_use_area=None,
                                      height_of_floors=None, nb_of_floors=None,
                                      neighbour_buildings=None,
                                      residential_layout=None, attic=None,
                                      cellar=None, construction_type=None,
                                      dormer=None, dhw_volumen=None,
                                      do_normalization=True,
                                      slp_manipulate=True,
                                      curr_central_ahu=None,
                                      dhw_random=False, prev_heat_dev=True,
                                      season_mod=None):
    """
    Function generates and returns extended residential building object
    with single zone.

    Parameters
    ----------
    environment : object
        Environment object
    net_floor_area : float
        Net floor area of building in m2
    spec_th_demand : float
        Specific thermal energy demand in kWh/m2*a
    th_gen_method : int
        Thermal load profile generation method
        1 - Use SLP
        2 - Load Modelica simulation output profile (only residential)
            Method 2 is only used for residential buildings. For non-res.
            buildings, SLPs are generated instead
    el_gen_method : int, optional
        Electrical generation method (default: 1)
        1 - Use SLP
        2 - Generate stochastic load profile (only valid for residential
        building)
    annual_el_demand : float, optional
        Annual electrical energy demand in kWh/a (default: None)
    use_dhw : bool, optional
        Boolean to define, if domestic hot water profile should be generated
        (default: False)
        True - Generate dhw profile
    dhw_method : int, optional
        Domestic hot water profile generation method (default: 1)
        1 - Use Annex 42 profile
        2 - Use stochastic profile
    number_occupants : int, optional
        Number of occupants (default: None)
    build_year : int, optional
        Building year of construction (default: None)
    mod_year : int, optional
        Last year of modernization of building (default: None)
    build_type : int, optional
        Building type (default: None)
    pv_use_area : float, optional
        Usable pv area in m2 (default: None)
    height_of_floors : float
        average height of the floors
    nb_of_floors : int
        Number of floors above the ground
    neighbour_buildings : int
        neighbour (default = 0)
            0: no neighbour
            1: one neighbour
            2: two neighbours
    residential_layout : int
        type of floor plan (default = 0)
            0: compact
            1: elongated/complex
    attic : int
        type of attic (default = 0)
            0: flat roof
            1: non heated attic
            2: partly heated attic
            3: heated attic
    cellar : int
        type of cellar (default = 0)
            0: no cellar
            1: non heated cellar
            2: partly heated cellar
            3: heated cellar
    construction_type : str
        construction type (default = "heavy")
            heavy: heavy construction
            light: light construction
    dormer : str
        construction type
            0: no dormer
            1: dormer
    dhw_volumen : float, optional
        Volume of domestic hot water in liter per capita and day
        (default: None).
    do_normalization : bool, optional
        Defines, if stochastic profile (el_gen_method=2) should be
        normalized to given annualDemand value (default: True).
        If set to False, annual el. demand depends on stochastic el. load
        profile generation. If set to True, does normalization with
        annualDemand
    slp_manipulate : bool, optional
        Defines, if thermal space heating SLP profile should be modified
        (default: True). Only used for residential buildings!
        Only relevant, if th_gen_method == 1
        True - Do manipulation
        False - Use original profile
        Sets thermal power to zero in time spaces, where average daily outdoor
        temperature is equal to or larger than 12 °C. Rescales profile to
        original demand value.
    curr_central_ahu : bool, optional
        Defines, if building has air handling unit (AHU)
        (default: False)
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

    Returns
    -------
    extended_building : object
        BuildingExtended object
    """

    assert net_floor_area > 0
    assert spec_th_demand >= 0
    if annual_el_demand is not None:
        assert annual_el_demand >= 0
    else:
        assert number_occupants is not None
        assert number_occupants > 0

    #  Define SLP profiles for residential building with single zone
    th_slp_type = 'HEF'
    el_slp_type = 'H0'

    if number_occupants is not None:
        assert number_occupants > 0
        assert number_occupants <= 5  # Max 5 occupants for stochastic profile
        if el_gen_method == 2 or (dhw_method == 2 and use_dhw == True):
            #  Generate occupancy profile (necessary for stochastic, el. or
            #  dhw profile)
            occupancy_object = occup.Occupancy(environment,
                                               number_occupants=number_occupants)

        else:  # Generate occupancy object without profile generation
            #  Just used to store information about number of occupants
            occupancy_object = occup.Occupancy(environment,
                                               number_occupants=number_occupants,
                                               do_profile=False)

    else:
        occupancy_object = None  # Dummy object to prevent error with
        #  apartment usage

        if el_gen_method == 2:
            warnings.warn('Stochastic el. profile cannot be generated ' +
                          'due to missing number of occupants. ' +
                          'SLP is used instead.')
            #  Set el_gen_method to 1 (SLP)
            el_gen_method = 1

        elif dhw_method == 2:
            raise AssertionError('DHW profile cannot be generated' +
                                 'for residential building without' +
                                 'occupants (stochastic mode).' +
                                 'Please check your input file ' +
                                 '(missing number of occupants) ' +
                                 'or disable dhw generation.')

    if (number_occupants is None and dhw_method == 1 and use_dhw == True):
        #  Set number of occupants to 2 to enable dhw usage
        number_occupants = 2

    # Create space heating demand
    if th_gen_method == 1:
        #  Use SLP
        heat_power_curve = SpaceHeating.SpaceHeating(environment,
                                                     method=1,
                                                     profile_type=th_slp_type,
                                                     livingArea=net_floor_area,
                                                     specificDemand=spec_th_demand)

        if slp_manipulate:  # Do SLP manipulation

            timestep = environment.timer.timeDiscretization
            temp_array = environment.weather.tAmbient

            mod_curve = \
                slpman.slp_th_manipulator(timestep,
                                          th_slp_curve=heat_power_curve.loadcurve,
                                          temp_array=temp_array)

            heat_power_curve.loadcurve = mod_curve

    elif th_gen_method == 2:
        #  Use Modelica result profile
        heat_power_curve = SpaceHeating.SpaceHeating(environment,
                                                     method=3,
                                                     livingArea=net_floor_area,
                                                     specificDemand=spec_th_demand)

    # Calculate el. energy demand for apartment, if no el. energy
    #  demand is given for whole building to rescale
    if annual_el_demand is None:
        #  Generate annual_el_demand_ap
        annual_el_demand = calc_el_dem_ap(nb_occ=number_occupants,
                                             el_random=el_random,
                                             type='sfh')

    print('Annual electrical demand in kWh: ', annual_el_demand)
    if number_occupants is not None:
        print('El. demand per person in kWh: ')
        print(annual_el_demand/number_occupants)
    print()

    # Create electrical power curve
    if el_gen_method == 2:

        if season_mod is not None:
            season_light_mod = True
        else:
            season_light_mod = False

        el_power_curve = ElectricalDemand.ElectricalDemand(environment,
                                                           method=2,
                                                           total_nb_occupants=number_occupants,
                                                           randomizeAppliances=True,
                                                           lightConfiguration=0,
                                                           annualDemand=annual_el_demand,
                                                           occupancy=occupancy_object.occupancy,
                                                           do_normalization=do_normalization,
                                                           prev_heat_dev=prev_heat_dev,
                                                           season_light_mod=season_light_mod,
                                                           light_mod_fac=season_mod)

    else:  # Use el. SLP
        el_power_curve = ElectricalDemand.ElectricalDemand(environment,
                                                           method=1,
                                                           annualDemand=annual_el_demand,
                                                           profileType=el_slp_type)

    # Create domestic hot water demand
    if use_dhw:

        if dhw_volumen is None or dhw_random:
            dhw_kwh = calc_dhw_dem_ap(nb_occ=number_occupants,
                                         dhw_random=dhw_random,
                                         type='sfh')

            #  Reconvert kWh/a to Liters per day
            dhw_vol_ap = dhw_kwh * 1000 * 3600 * 1000 / (955 * 4182 * 35 * 365)

            #  DHW volume per person and day
            dhw_volumen = dhw_vol_ap / number_occupants

        if dhw_method == 1:  # Annex 42

            dhw_power_curve = DomesticHotWater.DomesticHotWater(environment,
                                                                tFlow=60,
                                                                thermal=True,
                                                                method=1,
                                                                # Annex 42
                                                                dailyConsumption=dhw_volumen * number_occupants,
                                                                supplyTemperature=25)

        else:  # Stochastic profile
            dhw_power_curve = DomesticHotWater.DomesticHotWater(environment,
                                                                tFlow=60,
                                                                thermal=True,
                                                                method=2,
                                                                supplyTemperature=25,
                                                                occupancy=occupancy_object.occupancy)

            # Rescale to reference dhw volume (liters per person
            #  and day)

            curr_dhw_vol_flow = dhw_power_curve.water
            # Water volume flow in Liter/hour

            curr_volume_year = sum(curr_dhw_vol_flow) * \
                               environment.timer.timeDiscretization / \
                               3600
            curr_vol_day = curr_volume_year / 365
            curr_vol_day_and_person = curr_vol_day / \
                                      occupancy_object.number_occupants
            print('Curr. volume per person and day: ',
                  curr_vol_day_and_person)

            dhw_con_factor = dhw_volumen / curr_vol_day_and_person
            print('Conv. factor of hot water: ', dhw_con_factor)
            print('New volume per person and day: ',
                  curr_vol_day_and_person * dhw_con_factor)

            #  Normalize water flow and power load
            dhw_power_curve.water *= dhw_con_factor
            dhw_power_curve.loadcurve *= dhw_con_factor

    # Create apartment
    apartment = Apartment.Apartment(environment, occupancy=occupancy_object,
                                    net_floor_area=net_floor_area)

    #  Add demands to apartment
    if th_gen_method == 1 or th_gen_method == 2:
        if use_dhw:
            apartment.addMultipleEntities([heat_power_curve, el_power_curve,
                                           dhw_power_curve])
        else:
            apartment.addMultipleEntities([heat_power_curve, el_power_curve])
    else:
        if use_dhw:
            apartment.addMultipleEntities([el_power_curve,
                                           dhw_power_curve])
        else:
            apartment.addEntity(el_power_curve)

    # Create extended building object
    extended_building = \
        build_ex.BuildingExtended(environment,
                                  build_year=build_year,
                                  mod_year=mod_year,
                                  build_type=build_type,
                                  roof_usabl_pv_area=pv_use_area,
                                  net_floor_area=net_floor_area,
                                  height_of_floors=height_of_floors,
                                  nb_of_floors=nb_of_floors,
                                  neighbour_buildings=neighbour_buildings,
                                  residential_layout=residential_layout,
                                  attic=attic,
                                  cellar=cellar,
                                  construction_type=construction_type,
                                  dormer=dormer,
                                  with_ahu=
                                  curr_central_ahu)

    #  Add apartment to extended building
    extended_building.addEntity(entity=apartment)

    return extended_building


def generate_res_building_multi_zone(environment,
                                     net_floor_area,
                                     spec_th_demand,
                                     th_gen_method,
                                     el_gen_method,
                                     nb_of_apartments,
                                     annual_el_demand=None,
                                     use_dhw=False,
                                     dhw_method=1,
                                     total_number_occupants=None,
                                     build_year=None, mod_year=None,
                                     build_type=None, pv_use_area=None,
                                     height_of_floors=None, nb_of_floors=None,
                                     neighbour_buildings=None,
                                     residential_layout=None, attic=None,
                                     cellar=None, construction_type=None,
                                     dormer=None, dhw_volumen=None,
                                     do_normalization=True,
                                     slp_manipulate=True,
                                     curr_central_ahu=False,
                                     dhw_random=False, prev_heat_dev=True,
                                     season_mod=None):
    """
    Function generates and returns extended residential building object
    with multiple apartments. Occupants are randomly distributed over
    number of apartments.

    Parameters
    ----------
    environment : object
        Environment object
    net_floor_area : float
        Net floor area of building in m2
    spec_th_demand : float
        Specific thermal energy demand in kWh/m2*a
    annual_el_demand : float
        Annual electrical energy demand in kWh/a
    th_gen_method : int
        Thermal load profile generation method
        1 - Use SLP
        2 - Load Modelica simulation output profile (only residential)
            Method 2 is only used for residential buildings. For non-res.
            buildings, SLPs are generated instead
    el_gen_method : int, optional
        Electrical generation method (default: 1)
        1 - Use SLP
        2 - Generate stochastic load profile (only valid for residential
        building)
    nb_of_apartments : int
        Number of apartments within building
    use_dhw : bool, optional
        Boolean to define, if domestic hot water profile should be generated
        (default: False)
        True - Generate dhw profile
    dhw_method : int, optional
        Domestic hot water profile generation method (default: 1)
        1 - Use Annex 42 profile
        2 - Use stochastic profile
    total_number_occupants : int, optional
        Total number of occupants in all apartments (default: None)
    build_year : int, optional
        Building year of construction (default: None)
    mod_year : int, optional
        Last year of modernization of building (default: None)
    build_type : int, optional
        Building type (default: None)
    pv_use_area : float, optional
        Usable pv area in m2 (default: None)
    height_of_floors : float
        average height of the floors
    nb_of_floors : int
        Number of floors above the ground
    neighbour_buildings : int
        neighbour (default = 0)
            0: no neighbour
            1: one neighbour
            2: two neighbours
    residential_layout : int
        type of floor plan (default = 0)
            0: compact
            1: elongated/complex
    attic : int
        type of attic (default = 0)
            0: flat roof
            1: non heated attic
            2: partly heated attic
            3: heated attic
    cellar : int
        type of cellar (default = 0)
            0: no cellar
            1: non heated cellar
            2: partly heated cellar
            3: heated cellar
    construction_type : str
        construction type (default = "heavy")
            heavy: heavy construction
            light: light construction
    dormer : str
        construction type
            0: no dormer
            1: dormer
    dhw_volumen : float, optional
        Volume of domestic hot water in liter per capita and day
        (default: None).
    do_normalization : bool, optional
        Defines, if stochastic profile (el_gen_method=2) should be
        normalized to given annualDemand value (default: True).
        If set to False, annual el. demand depends on stochastic el. load
        profile generation. If set to True, does normalization with
        annualDemand
    slp_manipulate : bool, optional
        Defines, if thermal space heating SLP profile should be modified
        (default: True). Only used for residential buildings!
        Only relevant, if th_gen_method == 1
        True - Do manipulation
        False - Use original profile
        Sets thermal power to zero in time spaces, where average daily outdoor
        temperature is equal to or larger than 12 °C. Rescales profile to
        original demand value.
    curr_central_ahu : bool, optional
        Defines, if building has air handling unit (AHU)
        (default: False)
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

    Returns
    -------
    extended_building : object
        BuildingExtended object

    Annotation
    ----------
    Raise assertion error when share of occupants per apartment is higher
    than 5 (necessary for stochastic, el. profile generation)
    """

    assert net_floor_area > 0
    assert spec_th_demand >= 0
    if annual_el_demand is not None:
        assert annual_el_demand >= 0

    if total_number_occupants is not None:
        assert total_number_occupants > 0
        assert total_number_occupants / nb_of_apartments <= 5, (
            'Number of occupants per apartment is ' +
            'at least once higher than 5.')
        #  Distribute occupants to different apartments
        occupancy_list = constrained_sum_sample_pos(n=nb_of_apartments,
                                                    total=total_number_occupants)
        #  While not all values are smaller or equal to 5, return run
        #  This while loop might lead to large runtimes for buildings with a
        #  large number of apartments (not finding a valid solution, see
        #  issue #147). Thus, we add a counter to exit the loop
        count = 0

        while all(i <= 5 for i in occupancy_list) is not True:
            occupancy_list = constrained_sum_sample_pos(n=nb_of_apartments,
                                                        total=total_number_occupants)

            if count == 100000:
                #  Take current occupancy_list and redistribute occupants
                #  manually until valid distribution is found
                occupancy_list = redistribute_occ(occ_list=occupancy_list)

                #  Exit while loop
                break

            count += 1

        print('Current list of occupants per apartment: ', occupancy_list)
    else:
        msg = 'Number of occupants is None for current building!'
        warnings.warn(msg)

    # Define SLP profiles for residential building with multiple zone
    th_slp_type = 'HMF'
    el_slp_type = 'H0'

    # Create extended building object
    extended_building = \
        build_ex.BuildingExtended(environment,
                                  build_year=build_year,
                                  mod_year=mod_year,
                                  build_type=build_type,
                                  roof_usabl_pv_area=pv_use_area,
                                  net_floor_area=net_floor_area,
                                  height_of_floors=height_of_floors,
                                  nb_of_floors=nb_of_floors,
                                  neighbour_buildings=
                                  neighbour_buildings,
                                  residential_layout=
                                  residential_layout,
                                  attic=attic,
                                  cellar=cellar,
                                  construction_type=
                                  construction_type,
                                  dormer=dormer,
                                  with_ahu=curr_central_ahu)

    if annual_el_demand is not None:
        #  Distribute el. demand equally to apartments
        annual_el_demand_ap = annual_el_demand / nb_of_apartments
    else:
        annual_el_demand_ap = None

    # Loop over apartments
    #  #---------------------------------------------------------------------
    for i in range(nb_of_apartments):

        #  Dummy init of number of occupants
        curr_number_occupants = None

        #  Check number of occupants
        if total_number_occupants is not None:

            #  Get number of occupants
            curr_number_occupants = occupancy_list[i]

            #  Generate occupancy profiles for stochastic el. and/or dhw
            if el_gen_method == 2 or (dhw_method == 2 and use_dhw):

                #  Generate occupancy profile (necessary for stochastic, el. or
                #  dhw profile)
                occupancy_object = occup.Occupancy(environment,
                                                   number_occupants=
                                                   curr_number_occupants)

            else:  # Generate occupancy object without profile
                occupancy_object = occup.Occupancy(environment,
                                                   number_occupants=
                                                   curr_number_occupants,
                                                   do_profile=False)
        else:
            if el_gen_method == 2:
                warnings.warn('Stochastic el. profile cannot be generated ' +
                              'due to missing number of occupants. ' +
                              'SLP is used instead.')
                #  Set el_gen_method to 1 (SLP)
                el_gen_method = 1

            elif dhw_method == 2:
                raise AssertionError('DHW profile cannot be generated' +
                                     'for residential building without' +
                                     'occupants (stochastic mode).' +
                                     'Please check your input file ' +
                                     '(missing number of occupants) ' +
                                     'or disable dhw generation.')

        if (curr_number_occupants is None and dhw_method == 1 and
                    use_dhw == True):
            #  If dhw profile should be generated, but current number of
            #  occupants is None, number of occupants is samples from
            #  occupancy distribution for apartment
            curr_number_occupants = usunc.calc_sampling_occ_per_app(
                nb_samples=1)

        # Assumes equal area share for all apartments
        apartment_area = net_floor_area / nb_of_apartments

        #  Create space heating demand (for apartment)
        if th_gen_method == 1:
            #  Use SLP
            heat_power_curve = \
                SpaceHeating.SpaceHeating(environment,
                                          method=1,
                                          profile_type=th_slp_type,
                                          livingArea=apartment_area,
                                          specificDemand=spec_th_demand)

            if slp_manipulate:  # Do SLP manipulation

                timestep = environment.timer.timeDiscretization
                temp_array = environment.weather.tAmbient

                mod_curve = \
                    slpman.slp_th_manipulator(timestep,
                                              th_slp_curve=heat_power_curve.loadcurve,
                                              temp_array=temp_array)

                heat_power_curve.loadcurve = mod_curve

        elif th_gen_method == 2:
            #  Use Modelica result profile
            heat_power_curve = SpaceHeating.SpaceHeating(environment,
                                                         method=3,
                                                         livingArea=apartment_area,
                                                         specificDemand=spec_th_demand)

        # Calculate el. energy demand for apartment, if no el. energy
        #  demand is given for whole building to rescale
        if annual_el_demand_ap is None:
            #  Generate annual_el_demand_ap
            annual_el_demand_ap = calc_el_dem_ap(nb_occ=curr_number_occupants,
                                                 el_random=el_random,
                                                 type='mfh')

        # Create electrical power curve
        if el_gen_method == 2:

            if season_mod is not None:
                season_light_mod = True
            else:
                season_light_mod = False

            el_power_curve = ElectricalDemand.ElectricalDemand(environment,
                                                               method=2,
                                                               total_nb_occupants=curr_number_occupants,
                                                               randomizeAppliances=True,
                                                               lightConfiguration=0,
                                                               annualDemand=annual_el_demand_ap,
                                                               occupancy=occupancy_object.occupancy,
                                                               do_normalization=do_normalization,
                                                               prev_heat_dev=prev_heat_dev,
                                                               season_light_mod=season_light_mod,
                                                               light_mod_fac=season_mod)
        else:  # Use el. SLP
            el_power_curve = ElectricalDemand.ElectricalDemand(environment,
                                                               method=1,
                                                               annualDemand=annual_el_demand_ap,
                                                               profileType=el_slp_type)

        # Create domestic hot water demand
        if use_dhw:

            if dhw_volumen is None or dhw_random:
                dhw_kwh = calc_dhw_dem_ap(nb_occ=curr_number_occupants,
                                             dhw_random=dhw_random,
                                             type='mfh')

                #  Reconvert kWh/a to Liters per day
                dhw_vol_ap = dhw_kwh * 1000 * 3600 * 1000 / (
                955 * 4182 * 35 * 365)

                #  DHW volume per person and day
                dhw_volumen = dhw_vol_ap / curr_number_occupants

            if dhw_method == 1:  # Annex 42

                dhw_power_curve = DomesticHotWater.DomesticHotWater(
                    environment,
                    tFlow=60,
                    thermal=True,
                    method=1,
                    # Annex 42
                    dailyConsumption=dhw_volumen * curr_number_occupants,
                    supplyTemperature=25)

            else:  # Stochastic profile
                dhw_power_curve = DomesticHotWater.DomesticHotWater(
                    environment,
                    tFlow=60,
                    thermal=True,
                    method=2,
                    supplyTemperature=25,
                    occupancy=occupancy_object.occupancy)

                # Rescale to reference dhw volume (liters per person
                #  and day)

                curr_dhw_vol_flow = dhw_power_curve.water
                # Water volume flow in Liter/hour

                curr_volume_year = sum(curr_dhw_vol_flow) * \
                                   environment.timer.timeDiscretization / \
                                   3600
                curr_vol_day = curr_volume_year / 365
                curr_vol_day_and_person = curr_vol_day / \
                                          occupancy_object.number_occupants
                print('Curr. volume per person and day: ',
                      curr_vol_day_and_person)

                dhw_con_factor = dhw_volumen / curr_vol_day_and_person
                print('Conv. factor of hot water: ', dhw_con_factor)
                print('New volume per person and day: ',
                      curr_vol_day_and_person * dhw_con_factor)

                #  Normalize water flow and power load
                dhw_power_curve.water *= dhw_con_factor
                dhw_power_curve.loadcurve *= dhw_con_factor

        # Create apartment
        apartment = Apartment.Apartment(environment,
                                        occupancy=occupancy_object,
                                        net_floor_area=apartment_area)

        #  Add demands to apartment
        if th_gen_method == 1 or th_gen_method == 2:
            if use_dhw:
                apartment.addMultipleEntities([heat_power_curve,
                                               el_power_curve,
                                               dhw_power_curve])
            else:
                apartment.addMultipleEntities([heat_power_curve,
                                               el_power_curve])
        else:
            if use_dhw:
                apartment.addMultipleEntities([el_power_curve,
                                               dhw_power_curve])
            else:
                apartment.addEntity(el_power_curve)

        # Add apartment to extended building
        extended_building.addEntity(entity=apartment)

    return extended_building


def generate_nonres_building_single_zone(environment,
                                         net_floor_area, spec_th_demand,
                                         annual_el_demand, th_slp_type,
                                         el_slp_type=None,
                                         build_year=None, mod_year=None,
                                         build_type=None, pv_use_area=None,
                                         method_3_type=None,
                                         method_4_type=None,
                                         height_of_floors=None,
                                         nb_of_floors=None):
    """
    Function generates and returns extended nonresidential building object
    with single zone.

    Parameters
    ----------
    environment : object
        Environment object
    net_floor_area : float
        Net floor area of building in m2
    spec_th_demand : float
        Specific thermal energy demand in kWh/m2*a
    annual_el_demand : float
        Annual electrical energy demand in kWh/a
    th_slp_type : str
        Thermal SLP type (for non-residential buildings)
        - `GBA` : Bakeries
        - `GBD` : Other services
        - `GBH` : Accomodations
        - `GGA` : Restaurants
        - `GGB` : Gardening
        - `GHA` : Retailers
        - `GHD` : Summed load profile business, trade and services
        - `GKO` : Banks, insurances, public institutions
        - `GMF` : Household similar businesses
        - `GMK` : Automotive
        - `GPD` : Paper and printing
        - `GWA` : Laundries
    el_slp_type : str, optional (default: None)
        Electrical SLP type
        - H0 : Household
        - L0 : Farms
        - L1 : Farms with breeding / cattle
        - L2 : Farms without cattle
        - G0 : Business (general)
        - G1 : Business (workingdays 8:00 AM - 6:00 PM)
        - G2 : Business with high loads in the evening
        - G3 : Business (24 hours)
        - G4 : Shops / Barbers
        - G5 : Bakery
        - G6 : Weekend operation
    number_occupants : int, optional
        Number of occupants (default: None)
    build_year : int, optional
        Building year of construction (default: None)
    mod_year : int, optional
        Last year of modernization of building (default: None)
    build_type : int, optional
        Building type (default: None)
    pv_use_area : float, optional
        Usable pv area in m2 (default: None)
    method_3_type : str, optional
        Defines type of profile for method=3 (default: None)
        Options:
        - 'food_pro': Food production
        - 'metal': Metal company
        - 'rest': Restaurant (with large cooling load)
        - 'sports': Sports hall
        - 'repair': Repair / metal shop
    method_4_type : str, optional
        Defines type of profile for method=4 (default: None)
        - 'metal_1' : Metal company with smooth profile
        - 'metal_2' : Metal company with fluctuation in profile
        - 'warehouse' : Warehouse
    height_of_floors : float
        average height of the floors
    nb_of_floors : int
        Number of floors above the ground

    Returns
    -------
    extended_building : object
        BuildingExtended object
    """

    assert net_floor_area > 0
    assert spec_th_demand >= 0
    assert annual_el_demand >= 0
    assert th_slp_type != 'HEF', ('HEF thermal slp profile only valid for ' +
                                  'residential buildings.')
    assert th_slp_type != 'HMF', ('HMF thermal slp profile only valid for ' +
                                  'residential buildings.')
    assert el_slp_type != 'H0', ('H0 thermal slp profile only valid for ' +
                                 'residential buildings.')

    # Create space heating demand
    heat_power_curve = SpaceHeating.SpaceHeating(environment,
                                                 method=1,
                                                 profile_type=th_slp_type,
                                                 livingArea=net_floor_area,
                                                 specificDemand=spec_th_demand)

    if method_3_type is not None:
        el_power_curve = \
            ElectricalDemand.ElectricalDemand(environment,
                                              method=3,
                                              annualDemand=annual_el_demand,
                                              do_normalization=True,
                                              method_3_type=method_3_type)

    elif method_4_type is not None:
        el_power_curve = \
            ElectricalDemand.ElectricalDemand(environment,
                                              method=4,
                                              annualDemand=annual_el_demand,
                                              do_normalization=True,
                                              method_4_type=method_4_type)

    else:
        # Use el. SLP for el. power load generation
        assert el_slp_type is not None, 'el_slp_type is required!'

        el_power_curve = \
            ElectricalDemand.ElectricalDemand(environment,
                                              method=1,
                                              annualDemand=annual_el_demand,
                                              profileType=el_slp_type)

    # Create apartment
    apartment = Apartment.Apartment(environment)

    #  Add demands to apartment
    apartment.addMultipleEntities([heat_power_curve, el_power_curve])

    # Create extended building object
    extended_building = build_ex.BuildingExtended(environment,
                                                  net_floor_area=net_floor_area,
                                                  build_year=build_year,
                                                  mod_year=mod_year,
                                                  build_type=build_type,
                                                  roof_usabl_pv_area=pv_use_area,
                                                  height_of_floors=height_of_floors,
                                                  nb_of_floors=nb_of_floors,
                                                  )

    #  Add apartment to extended building
    extended_building.addEntity(entity=apartment)

    return extended_building


def get_district_data_from_txt(path, delimiter='\t'):
    """
    Load city district data from txt file (see annotations below for further
    information of required inputs).

    naN are going to be replaced with Python None.

    Parameters
    ----------
    path : str
        Path to txt file
    delimiter : str, optional
        Defines delimiter for txt file (default: '\t')

    Returns
    -------
    district_data : ndarray
        Numpy 2d-array with city district data (each column represents
        different parameter, see annotations)

    Annotations
    -----------
    File structure
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
    17: Neighbour Buildings (int, optional) (0 - free standing)
    (1 - double house) (2 - row house)
    18: Type of attic (int, optional, e.g. 0 for flat roof) (1 - regular roof;
    unheated) (2 - regular roof; partially heated) (3 - regular roof; fully
    heated)
    19: Type of cellar (int, optional, e.g. 1 for non heated cellar)
    (0 - no basement) (1 - non heated) (2 - partially heated) (3 - fully heated)
    20: Dormer (int, optional, 0: no dormer/ 1: dormer)
    21: Construction Type(heavy/light, optional) (0 - heavy; 1 - light)
    22: Method_3_nb (for usage of measured, weekly non-res. el. profile
    (optional)
    23: Method_4_nb (for usage of measured, annual non-res. el. profile
    (optional)
    """

    district_data = np.genfromtxt(path, delimiter=delimiter, skip_header=1)

    #  Replace nan with None values of Python
    district_data = np.where(np.isnan(district_data), None, district_data)

    return district_data


def calc_el_dem_ap(nb_occ, el_random, type):
    """
    Calculate electric energy demand per apartment per year
    in kWh/a (residential buildings, only)

    Parameters
    ----------
    nb_occ : int
        Number of occupants
    el_random : bool
        Defines, if random value should be chosen from statistics
        or if average value should be chosen. el_random == True means,
        use random value.
    type : str
        Define residential building type (single family or multi-
        family)
        Options:
        - 'sfh' : Single family house
        - 'mfh' : Multi family house

    Returns
    -------
    el_dem : float
        Electric energy demand per apartment in kWh/a
    """

    assert nb_occ > 0
    assert nb_occ <= 5, 'Number of occupants cannot exceed 5 per ap.'
    assert type in ['sfh', 'mfh']

    if el_random:
        #  Choose first entry of random sample list
        el_dem = usunc.calc_sampling_el_demand_per_apartment(
            nb_samples=1,
            nb_persons=nb_occ,
            type=type)[0]
    else:
        #  Choose average value depending on nb_occ
        #  Class D without hot water (Stromspiegel 2017)
        dict_sfh = {1: 2500,
                    2: 3200,
                    3: 3900,
                    4: 4200,
                    5: 5400}

        dict_mfh = {1: 1500,
                    2: 2200,
                    3: 2800,
                    4: 3200,
                    5: 4000}

        if type == 'sfh':
            el_dem = dict_sfh[nb_occ]
        elif type == 'mfh':
            el_dem = dict_mfh[nb_occ]

    return el_dem


def calc_dhw_dem_ap(nb_occ, dhw_random, type):
    """
    Calculate hot water energy demand per apartment per year
    in kWh/a (residential buildings, only)

    Parameters
    ----------
    nb_occ : int
        Number of occupants
    dhw_random : bool
        Defines, if random value should be chosen from statistics
        or if average value should be chosen. dhw_random == True means,
        use random value.
    type : str
        Define residential building type (single family or multi-
        family)
        Options:
        - 'sfh' : Single family house
        - 'mfh' : Multi family house

    Returns
    -------
    dhw_dem : float
        Electric energy demand per apartment in kWh/a
    """

    assert nb_occ > 0
    assert nb_occ <= 5, 'Number of occupants cannot exceed 5 per ap.'
    assert type in ['sfh', 'mfh']

    if dhw_random:
        #  Choose first entry of random sample list
        dhw_dem = usunc.calc_sampling_el_demand_per_apartment(
            nb_samples=1,
            nb_persons=nb_occ,
            type=type)[0]
    else:
        #  Choose average value depending on nb_occ
        #  Class D without hot water (Stromspiegel 2017)
        dict_sfh = {1: 500,
                    2: 800,
                    3: 1000,
                    4: 1300,
                    5: 1600}

        dict_mfh = {1: 500,
                    2: 900,
                    3: 1300,
                    4: 1400,
                    5: 2000}

        if type == 'sfh':
            dhw_dem = dict_sfh[nb_occ]
        elif type == 'mfh':
            dhw_dem = dict_mfh[nb_occ]

    return dhw_dem


def run_city_generator(generation_mode, timestep, year, location,
                       th_gen_method,
                       el_gen_method, district_data, use_dhw=False,
                       dhw_method=1, try_path=None,
                       pickle_city_filename=None, do_save=True,
                       path_save_city=None, eff_factor=0.85,
                       show_city=False, altitude=55, dhw_volumen=None,
                       do_normalization=True, slp_manipulate=True,
                       call_teaser=False, teaser_proj_name='pycity',
                       do_log=True, log_path=None,
                       project_name='teaser_project',
                       air_vent_mode=1, vent_factor=0.5,
                       t_set_heat=20,
                       t_set_cool=70,
                       t_night=16,
                       vdi_sh_manipulate=False, city_osm=None,
                       el_random=False, dhw_random=False, prev_heat_dev=True,
                       season_mod=None, merge_windows=False, new_try=False):
    """
    Function generates city district for user defined input. Generated
    buildings consist of only one single zone!

    Parameters
    ----------
    generation_mode : int
        Integer to define method to generate city district
        (so far, only csv/txt file import has been implemented)
        generation_mode = 0: Load data from csv/txt file (tab seperated)
    timestep : int
        Timestep in seconds
    year : int
        Chosen year
    location : Tuple
        (latitude, longitude) of the simulated system's position.
    th_gen_method : int
        Thermal load profile generation method
        1 - Use SLP
        2 - Load Modelica simulation output profile (only residential)
            Method 2 is only used for residential buildings. For non-res.
            buildings, SLPs are generated instead
        3 - Use TEASER VDI 6007 core to simulate thermal loads‚
    el_gen_method : int
        Electrical generation method
        1 - Use SLP
        2 - Generate stochastic load profile (only valid for residential
        building). Requires number of occupants.
    district_data : ndarray
        Numpy 2d-array with city district data (each column represents
        different parameter, see annotations)
    use_dhw : bool, optional
        Defines if domestic hot water profiles should be generated.
        (default: False)
    dhw_method : int, optional
        Defines method for dhw profile generation (default: 1)
        Only relevant if use_dhw=True. Options:
        - 1: Generate profiles via Annex 42
        - 2: Generate stochastic dhw profiles
    try_path : str, optional
        Path to TRY weather file (default: None)
        If set to None, uses default weather TRY file (2010, region 5)
    pickle_city_filename : str, optional
        Name for file, which should be pickled and saved, if no path is
        handed over to save object to(default: None)
    do_save : bool, optional
        Defines, if city object instance should be saved as pickle file
        (default: True)
    path_save_city : str, optional
        Path to save (pickle and dump) city object instance to (default: None)
        If None is used, saves file to .../output/...
    eff_factor : float, optional
         Efficiency factor of thermal boiler system (default: 0.85)
    show_city : bool, optional
        Boolean to define if city district should be printed by matplotlib
        after generation (default: False)
        True: Print results
        False: Do not print results
    altitude : float, optional
        Altitude of location in m (default: 55 - City of Bottrop)
    dhw_volumen : float, optional
        Volume of domestic hot water in liter per capita and day
        (default: None).
    do_normalization : bool, optional
        Defines, if stochastic profile (el_gen_method=2) should be
        normalized to given annualDemand value (default: True).
        If set to False, annual el. demand depends on stochastic el. load
        profile generation. If set to True, does normalization with
        annualDemand
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
        (Related to constraints for res. buildings in DIN V 18599)
    t_set_cool : float, optional
        Cooling set temperature in degree Celsius. If temperature rises above
        t_set_cool, model is going to be cooled down. (default: 70)
    t_night : float, optional
        Night set back temperature in degree Celsius (default: 16)
        (Related to constraints for res. buildings in DIN V 18599)
    project_name : str, optional
        TEASER project name (default: 'teaser_project')
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
	For residential: space heating, only!
	For non-residential: Space heating AND hot water! (SLP usage)
    9:  Annual electrical energy demand in kWh (float, optional)
    10: Usable pv roof area in m2 (float, optional)
    11: Number of apartments (int, optional)
    12: Total number of occupants (int, optional)
    13: Number of floors above the ground (int, optional)
    14: Average Height of floors (float, optional)
    15: If building has a central AHU or not (boolean, optional)
    16: Residential layout (int, optional, e.g. 0 for compact)
    17: Neighbour Buildings (int, optional); 0 - free standing; 1 - Double house; 2 - Row house;
    18: Type of attic (int, optional, e.g. 0 for flat roof); 1 - Roof, non heated; 2 - Roof, partially heated; 3- Roof, fully heated;
    19: Type of basement (int, optional, e.g. 1 for non heated basement 0 - No basement; 1 - basement, non heated; 2 - basement, partially heated; 3- basement, fully heated;
    20: Dormer (int, optional, 0: no dormer/ 1: dormer)
    21: Construction Type(heavy/light, optional) (0 - heavy; 1 - light)
    22: Method_3_nb (for usage of measured, weekly non-res. el. profile
    (optional) (0 to 4)
    23: Method_4_nb (for usage of measured, annual non-res. el. profile
    (optional) (0 - 2)

	method_3_type : str, optional
        Defines type of profile for method=3 (default: None)
        Options:
        0 - 'food_pro': Food production
        1 - 'metal': Metal company
        2 - 'rest': Restaurant (with large cooling load)
        3 - 'sports': Sports hall
        4 - 'repair': Repair / metal shop
    method_4_type : str, optional
        Defines type of profile for method=4 (default: None)
        0 - 'metal_1' : Metal company with smooth profile
        1 - 'metal_2' : Metal company with fluctuation in profile
        2 - 'warehouse' : Warehouse
    """

    assert eff_factor > 0, 'Efficiency factor has to be larger than zero.'
    assert eff_factor <= 1, 'Efficiency factor cannot increase value 1.'
    if dhw_volumen is not None:
        assert dhw_volumen >= 0, 'Hot water volume cannot be below zero.'

    if generation_mode == 1:
        assert city_osm is not None, 'Generation mode 1 requires city object!'

    if vdi_sh_manipulate is True and th_gen_method == 3:
        msg = 'Simulated profiles of VDI 6007 call (TEASER --> ' \
              'space heating) is going to be normalized with annual thermal' \
              ' space heating demand values given by user!'
        warnings.warn(msg)

    if do_log:
        #  Write log file
        #  ################################################################

        #  Log file path
        if log_path is None:
            #  If not existing, use default path
            this_path = os.path.dirname(os.path.abspath(__file__))
            log_path = os.path.join(this_path, 'output', 'city_gen_log.txt')

        log_file = open(log_path, mode='w')
        log_file.write('PyCity_Calc city_generator.py log file')

        log_file.write('\n############## Time and location ##############\n')
        log_file.write('Date: ' + str(datetime.datetime.now()) + '\n')
        log_file.write('generation_mode: ' + str(generation_mode) + '\n')
        log_file.write('timestep in seconds: ' + str(timestep) + '\n')
        log_file.write('Year: ' + str(year) + '\n')
        log_file.write('Location: ' + str(location) + '\n')
        log_file.write('altitude: ' + str(altitude) + '\n')
        if generation_mode == 0:
            log_file.write('Generation mode: csv/txt input, only.\n')
        elif generation_mode == 1:
            log_file.write('Generation mode: csv/txt plus city osm object.\n')

        log_file.write('\n############## Generation methods ##############\n')
        log_file.write('th_gen_method: ' + str(th_gen_method) + '\n')
        if th_gen_method == 1:
            log_file.write('Manipulate SLP: ' + str(slp_manipulate) + '\n')
        elif th_gen_method == 3:
            log_file.write('t_set_heat: ' + str(t_set_heat) + '\n')
            log_file.write('t_set_night: ' + str(t_night) + '\n')
            log_file.write('t_set_cool: ' + str(t_set_cool) + '\n')
            log_file.write('air_vent_mode: ' + str(air_vent_mode) + '\n')
            log_file.write('vent_factor: ' + str(vent_factor) + '\n')

        log_file.write('el_gen_method: ' + str(el_gen_method) + '\n')
        log_file.write(
            'Normalize el. profile: ' + str(do_normalization) + '\n')
        log_file.write(
            'Do random el. normalization: ' + str(el_random) + '\n')
        log_file.write(
            'Prevent el. heating devices for el load generation: '
            '' + str(prev_heat_dev) + '\n')
        log_file.write(
            'Rescaling factor lighting power curve to implement seasonal '
            'influence: ' + str(season_mod) + '\n')

        log_file.write('use_dhw: ' + str(use_dhw) + '\n')
        log_file.write('dhw_method: ' + str(dhw_method) + '\n')
        log_file.write('dhw_volumen: ' + str(dhw_volumen) + '\n')
        log_file.write(
            'Do random dhw. normalization: ' + str(dhw_random) + '\n')

        log_file.write('\n############## Others ##############\n')
        log_file.write('try_path: ' + str(try_path) + '\n')
        log_file.write('eff_factor: ' + str(eff_factor) + '\n')
        log_file.write('timestep in seconds: ' + str(timestep) + '\n')
        log_file.write('call_teaser: ' + str(call_teaser) + '\n')
        log_file.write('teaser_proj_name: ' + str(teaser_proj_name) + '\n')

        #  Log file is closed, after pickle filename has been generated
        #  (see code below)

    if generation_mode == 0 or generation_mode == 1:
        #  ##################################################################
        #  Load specific demand files

        #  Load specific thermal demand input data
        spec_th_dem_res_building = load_data_file_with_spec_demand_data(
            'RWI_res_building_spec_th_demand.txt')

        start_year_column = (spec_th_dem_res_building[:, [0]])
        #  Reverse
        start_year_column = start_year_column[::-1]
        """
        Columns:
        1. Start year (int)
        2. Final year (int)
        3. Spec. thermal energy demand in kWh/m2*a (float)
        """

        #  ##################################################################
        #  Load specific electrical demand input data
        spec_el_dem_res_building = load_data_file_with_spec_demand_data(
            'AGEB_res_building_spec_e_demand.txt')

        """
        Columns:
        1. Start year (int)
        2. Final year (int)
        3. Spec. thermal energy demand in kWh/m2*a (float)
        """

        #  ##################################################################
        #  Load specific electrical demand input data
        #  (depending on number of occupants)
        spec_el_dem_res_building_per_person = \
            load_data_file_with_spec_demand_data(
                'Stromspiegel2017_spec_el_energy_demand.txt')

        """
        Columns:
        1. Number of persons (int) ( 1 - 5 SFH and 1 - 5 MFH)
        2. Annual electrical demand in kWh/a (float)
        3. Specific electrical demand per person in kWh/person*a (float)
        """

        #  ###################################################################
        #  Load specific demand data and slp types for
        #  non residential buildings
        spec_dem_and_slp_non_res = load_data_file_with_spec_demand_data(
            'Spec_demands_non_res.txt')

        """
        Columns:
        1. type_id (int)
        2. type_name (string)  # Currently 'nan', due to expected float
        3. Spec. thermal energy demand in kWh/m2*a (float)
        4. Spec. electrical energy demand in kWh/m2*a (float)
        5. Thermal SLP type (int)
        6. Electrical SLP type (int)
        """

        #  ###################################################################
        #  Generate city district

        #  Generate extended environment of pycity_calc
        environment = generate_environment(timestep=timestep, year=year,
                                           location=location,
                                           try_path=try_path,
                                           altitude=altitude,
                                           new_try=new_try)

        print('Generated environment object.\n')

        if generation_mode == 0:
            #  Generate city object
            #  ############################################################
            city_object = city.City(environment=environment)
            print('Generated city object.\n')
        else:
            #  Overwrite city_osm environment
            print('Overwrite city_osm.environment with new environment')
            city_osm.environment = environment
            city_object = city_osm

        # Check if district_data only holds one entry for single building
        #  In this case, has to be processed differently
        if district_data.ndim > 1:
            multi_data = True
        else:  # Only one entry (single building)
            multi_data = False
            #  If multi_data is false, loop below is going to be exited with
            #  a break statement at the end.

        #  Generate dummy node id and thermal space heating demand dict
        dict_id_vdi_sh = {}

        #  Loop over district_data
        #  ############################################################
        for i in range(len(district_data)):
            if multi_data:
                #  Extract data out of input file
                curr_id = int(
                    district_data[i][0])  # id / primary key of building
                curr_x = district_data[i][1]  # x-coordinate in m
                curr_y = district_data[i][2]  # y-coordinate in m
                curr_build_type = int(
                    district_data[i][3])  # building type nb (int)
                curr_nfa = district_data[i][4]  # Net floor area in m2
                curr_build_year = district_data[i][5]  # Year of construction
                curr_mod_year = district_data[i][
                    6]  # optional (last year of modernization)
                curr_th_e_demand = district_data[i][
                    7]  # optional: Final thermal energy demand in kWh
                #  For residential buildings: Space heating only!
                #  For non-residential buildings: Space heating AND hot water! (SLP)
                curr_el_e_demand = district_data[i][
                    8]  # optional  (Annual el. energy demand in kWh)
                curr_pv_roof_area = district_data[i][
                    9]  # optional (Usable pv roof area in m2)
                curr_nb_of_apartments = district_data[i][
                    10]  # optional (Number of apartments)
                curr_nb_of_occupants = district_data[i][
                    11]  # optional (Total number of occupants)
                curr_nb_of_floors = district_data[i][
                    12]  # optional (Number of floors above the ground)
                curr_avg_height_of_floors = district_data[i][
                    13]  # optional (Average Height of floors)
                curr_central_ahu = district_data[i][
                    14]  # optional (If building has a central air handling unit (AHU) or not (boolean))
                curr_res_layout = district_data[i][
                    15]  # optional Residential layout (int, optional, e.g. 0 for compact)
                curr_nb_of_neighbour_bld = district_data[i][
                    16]  # optional Neighbour Buildings (int, optional)
                curr_type_attic = district_data[i][
                    17]  # optional Type of attic (int, optional, e.g. 0 for flat roof);
                # 1 - Roof, non heated; 2 - Roof, partially heated; 3- Roof, fully heated;
                curr_type_cellar = district_data[i][
                    18]  # optional Type of basement
                # (int, optional, e.g. 1 for non heated basement 0 - No basement; 1 - basement, non heated; 2 - basement, partially heated; 3- basement, fully heated;
                curr_dormer = district_data[i][
                    19]  # optional  Dormer (int, optional, 0: no dormer/ 1: dormer)
                curr_construction_type = district_data[i][
                    20]  # optional  Construction Type(heavy/light, optional) (0 - heavy; 1 - light)
                curr_method_3_nb = district_data[i][
                    21]  # optional  Method_3_nb (for usage of measured, weekly non-res. el. profile
                curr_method_4_nb = district_data[i][
                    22]  # optional  Method_4_nb (for usage of measured, annual non-res. el. profile
            else:  # Single entry
                #  Extract data out of input file
                curr_id = int(district_data[0])  # id / primary key of building
                curr_x = district_data[1]  # x-coordinate in m
                curr_y = district_data[2]  # y-coordinate in m
                curr_build_type = int(
                    district_data[3])  # building type nb (int)
                curr_nfa = district_data[4]  # Net floor area in m2
                curr_build_year = district_data[5]  # Year of construction
                curr_mod_year = district_data[
                    6]  # optional (last year of modernization)
                curr_th_e_demand = district_data[
                    7]  # optional: Final thermal energy demand in kWh
                #  For residential buildings: Space heating only!
                #  For non-residential buildings: Space heating AND hot water! (SLP)
                curr_el_e_demand = district_data[
                    8]  # optional  (Annual el. energy demand in kWh)
                curr_pv_roof_area = district_data[
                    9]  # optional (Usable pv roof area in m2)
                curr_nb_of_apartments = district_data[
                    10]  # optional (Number of apartments)
                curr_nb_of_occupants = district_data[
                    11]  # optional (Total number of occupants)
                curr_nb_of_floors = district_data[
                    12]  # optional (Number of floors above the ground)
                curr_avg_height_of_floors = district_data[
                    13]  # optional (Average Height of floors)
                curr_central_ahu = district_data[
                    14]  # optional (If building has a central air handling unit (AHU) or not (boolean))
                curr_res_layout = district_data[
                    15]  # optional Residential layout (int, optional, e.g. 0 for compact)
                curr_nb_of_neighbour_bld = district_data[
                    16]  # optional Neighbour Buildings (int, optional)
                curr_type_attic = district_data[
                    17]  # optional Type of attic (int, optional, e.g. 0 for flat roof);
                # 1 - Roof, non heated; 2 - Roof, partially heated; 3- Roof, fully heated;
                curr_type_cellar = district_data[
                    18]  # optional Type of basement
                # (int, optional, e.g. 1 for non heated basement 0 - No basement; 1 - basement, non heated; 2 - basement, partially heated; 3- basement, fully heated;
                curr_dormer = district_data[
                    19]  # optional  Dormer (int, optional, 0: no dormer/ 1: dormer)
                curr_construction_type = district_data[
                    20]  # optional  Construction Type(heavy/light, optional) (0 - heavy; 1 - light)
                curr_method_3_nb = district_data[
                    21]  # optional  Method_3_nb (for usage of measured, weekly non-res. el. profile
                curr_method_4_nb = district_data[
                    22]  # optional  Method_4_nb (for usage of measured, annual non-res. el. profile

            print('Process building', curr_id)
            print('########################################################')

            #  Assert functions
            #  ############################################################
            assert curr_build_type >= 0
            assert curr_nfa > 0

            for m in range(5, 9):
                if multi_data:
                    if district_data[i][m] is not None:
                        assert district_data[i][m] > 0
                else:
                    if district_data[m] is not None:
                        assert district_data[m] > 0

            if curr_nb_of_apartments is not None:
                assert curr_nb_of_apartments > 0
                #  Convert to int
                curr_nb_of_apartments = int(curr_nb_of_apartments)

            if curr_nb_of_occupants is not None:
                assert curr_nb_of_occupants > 0
                #  Convert curr_nb_of_occupants from float to int
                curr_nb_of_occupants = int(curr_nb_of_occupants)

            if (curr_nb_of_occupants is not None
                and curr_nb_of_apartments is not None):
                assert curr_nb_of_occupants / curr_nb_of_apartments <= 5, (
                    'Average share of occupants per apartment should ' +
                    'not exceed 5 persons! (Necessary for stochastic, el.' +
                    'profile generation.)')

            if curr_method_3_nb is not None:
                curr_method_3_nb >= 0
            if curr_method_4_nb is not None:
                curr_method_4_nb >= 0

            if curr_build_type == 0 and curr_nb_of_apartments is None:
                #  Define single apartment, if nb of apartments is unknown
                msg = 'Building ' + str(curr_id) + ' is residential, but' \
                                                   ' does not have a number' \
                                                   ' of apartments. Going' \
                                                   ' to set nb. to 1.'
                warnings.warn(msg)
                curr_nb_of_apartments = 1

            if (curr_build_type == 0 and curr_nb_of_occupants is None
                and use_dhw and dhw_method == 2):
                raise AssertionError('DHW profile cannot be generated' +
                                     'for residential building without' +
                                     'occupants (stochastic mode).' +
                                     'Please check your input file ' +
                                     '(missing number of occupants) ' +
                                     'or disable dhw generation.')

            # Check if TEASER inputs are defined
            if call_teaser or th_gen_method == 3:
                if curr_build_type == 0:  # Residential
                    assert curr_nb_of_floors is not None
                    assert curr_avg_height_of_floors is not None
                    assert curr_central_ahu is not None
                    assert curr_res_layout is not None
                    assert curr_nb_of_neighbour_bld is not None
                    assert curr_type_attic is not None
                    assert curr_type_cellar is not None
                    assert curr_dormer is not None
                    assert curr_construction_type is not None

            if curr_nb_of_floors is not None:
                assert curr_nb_of_floors > 0
            if curr_avg_height_of_floors is not None:
                assert curr_avg_height_of_floors > 0
            if curr_central_ahu is not None:
                assert 0 <= curr_central_ahu <= 1
            if curr_res_layout is not None:
                assert 0 <= curr_res_layout <= 1
            if curr_nb_of_neighbour_bld is not None:
                assert 0 <= curr_nb_of_neighbour_bld <= 2
            if curr_type_attic is not None:
                assert 0 <= curr_type_attic <= 3
            if curr_type_cellar is not None:
                assert 0 <= curr_type_cellar <= 3
            if curr_dormer is not None:
                assert 0 <= curr_dormer <= 1
            if curr_construction_type is not None:
                assert 0 <= curr_construction_type <= 1

            # Check building type (residential or non residential)
            #  #-------------------------------------------------------------
            if curr_build_type == 0:  # Is residential
                print('Residential building')

                #  Get spec. net therm. demand value according to last year
                #  of modernization or build_year
                #  If year of modernization is defined, use curr_mod_year
                if curr_mod_year is not None:
                    use_year = int(curr_mod_year)
                else:  # Use year of construction
                    use_year = int(curr_build_year)

                # Get specific, thermal energy demand (based on use_year)
                for j in range(len(start_year_column)):
                    if use_year >= start_year_column[j]:
                        curr_spec_th_demand = spec_th_dem_res_building[len(
                            spec_th_dem_res_building) - 1 - j][2]
                        break

                        # # Get spec. electr. demand
                        # if curr_nb_of_occupants is None:
                        #     #  USE AGEB values, if no number of occupants is given
                        #     #  Set specific demand value in kWh/m2*a
                        #     curr_spec_el_demand = spec_el_dem_res_building[1]
                        #     #  Only valid for array like [2012    38.7]

                        # else:
                        #     #  Use Stromspiegel 2017 values
                        #     #  Calculate specific electric demand values depending
                        #     #  on number of occupants
                        #
                        #     if curr_nb_of_apartments == 1:
                        #         btype = 'sfh'
                        #     elif curr_nb_of_apartments > 1:
                        #         btype = 'mfh'
                        #
                        #     #  Average occupancy number per apartment
                        #     curr_av_occ_per_app = \
                        #         curr_nb_of_occupants / curr_nb_of_apartments
                        #     print('Average number of occupants per apartment')
                        #     print(round(curr_av_occ_per_app, ndigits=2))
                        #
                        #     if curr_av_occ_per_app <= 5 and curr_av_occ_per_app > 0:
                        #         #  Correctur factor for non-int. av. number of
                        #         #  occupants (#19)
                        #
                        #         #  Divide annual el. energy demand with net floor area
                        #         if btype == 'sfh':
                        #             row_idx_low = math.ceil(curr_av_occ_per_app) - 1
                        #             row_idx_high = math.floor(curr_av_occ_per_app) - 1
                        #         elif btype == 'mfh':
                        #             row_idx_low = math.ceil(curr_av_occ_per_app) - 1 \
                        #                            + 5
                        #             row_idx_high = math.floor(curr_av_occ_per_app) - 1 \
                        #                           + 5
                        #
                        #         cur_spec_el_dem_per_occ_high = \
                        #             spec_el_dem_res_building_per_person[row_idx_high][2]
                        #         cur_spec_el_dem_per_occ_low = \
                        #             spec_el_dem_res_building_per_person[row_idx_low][2]
                        #
                        #         print('Chosen reference spec. el. demands per person '
                        #               'in kWh/a (high and low value):')
                        #         print(cur_spec_el_dem_per_occ_high)
                        #         print(cur_spec_el_dem_per_occ_low)
                        #
                        #         delta = round(curr_av_occ_per_app, 0) - \
                        #                 curr_av_occ_per_app
                        #
                        #         if delta < 0:
                        #             curr_spec_el_dem_occ = cur_spec_el_dem_per_occ_high + \
                        #                                (cur_spec_el_dem_per_occ_high -
                        #                                 cur_spec_el_dem_per_occ_low) * delta
                        #         elif delta > 0:
                        #             curr_spec_el_dem_occ = cur_spec_el_dem_per_occ_low + \
                        #                                (cur_spec_el_dem_per_occ_high -
                        #                                 cur_spec_el_dem_per_occ_low) * delta
                        #         else:
                        #             curr_spec_el_dem_occ = cur_spec_el_dem_per_occ_high
                        #
                        #         # print('Calculated spec. el. demand per person in '
                        #         #       'kWh/a:')
                        #         # print(round(curr_spec_el_dem_occ, ndigits=2))
                        #
                        #         #  Specific el. demand per person (dependend on av.
                        #         #  number of occupants in each apartment)
                        #         #  --> Multiplied with number of occupants
                        #         #  --> Total el. energy demand in kWh
                        #         #  --> Divided with net floor area
                        #         #  --> Spec. el. energy demand in kWh/a
                        #
                        #         curr_spec_el_demand = \
                        #             curr_spec_el_dem_occ * curr_nb_of_occupants \
                        #             / curr_nfa
                        #
                        #         # print('Spec. el. energy demand in kWh/m2:')
                        #         # print(curr_spec_el_demand)
                        #
                        #     else:
                        #         raise AssertionError('Invalid number of occupants')

                        # if el_random:
                        #     if curr_nb_of_occupants is None:
                        #         #  Randomize curr_spec_el_demand with normal distribution
                        #         #  with curr_spec_el_demand as mean and 10 % standard dev.
                        #         curr_spec_el_demand = \
                        #             np.random.normal(loc=curr_spec_el_demand,
                        #                              scale=0.10 * curr_spec_el_demand)

                        # else:
                        #     #  Randomize rounding up and down of curr_av_occ_per_ap
                        #     if round(curr_av_occ_per_app) > curr_av_occ_per_app:
                        #         #  Round up
                        #         delta = round(curr_av_occ_per_app) - \
                        #                 curr_av_occ_per_app
                        #         prob_r_up = 1 - delta
                        #         rnb = random.random()
                        #         if rnb < prob_r_up:
                        #             use_occ = math.ceil(curr_av_occ_per_app)
                        #         else:
                        #             use_occ = math.floor(curr_av_occ_per_app)
                        #
                        #     else:
                        #         #  Round down
                        #         delta = curr_av_occ_per_app - \
                        #                 round(curr_av_occ_per_app)
                        #         prob_r_down = 1 - delta
                        #         rnb = random.random()
                        #         if rnb < prob_r_down:
                        #             use_occ = math.floor(curr_av_occ_per_app)
                        #         else:
                        #             use_occ = math.ceil(curr_av_occ_per_app)
                        #
                        #     sample_el_per_app = \
                        #             usunc.calc_sampling_el_demand_per_apartment(nb_samples=1,
                        #                                                   nb_persons=use_occ,
                        #                                                   type=btype)[0]
                        #
                        #     #  Divide sampled el. demand per apartment through
                        #     #  number of persons of apartment (according to
                        #     #  Stromspiegel 2017) and multiply this value with
                        #     #  actual number of persons in building to get
                        #     #  new total el. energy demand. Divide this value with
                        #     #  net floor area to get specific el. energy demand
                        #     curr_spec_el_demand = \
                        #         (sample_el_per_app / curr_av_occ_per_app) * \
                        #         curr_nb_of_occupants / curr_nfa

                # conversion of the construction_type from int to str
                if curr_construction_type == 0:
                    new_curr_construction_type = 'heavy'
                elif curr_construction_type == 1:
                    new_curr_construction_type = 'light'
                else:
                    new_curr_construction_type = 'heavy'

            # #-------------------------------------------------------------
            else:  # Non-residential
                print('Non residential')

                #  Get spec. demands and slp types according to building_type
                curr_spec_th_demand = \
                    spec_dem_and_slp_non_res[curr_build_type - 1][2]
                curr_spec_el_demand = \
                    spec_dem_and_slp_non_res[curr_build_type - 1][3]
                curr_th_slp_type = \
                    spec_dem_and_slp_non_res[curr_build_type - 1][4]
                curr_el_slp_type = \
                    spec_dem_and_slp_non_res[curr_build_type - 1][5]

                #  Convert slp type integers into strings
                curr_th_slp_type = convert_th_slp_int_and_str(curr_th_slp_type)
                curr_el_slp_type = convert_el_slp_int_and_str(curr_el_slp_type)

            # #-------------------------------------------------------------
            #  If curr_th_e_demand is known, recalc spec e. demand
            if curr_th_e_demand is not None:
                #  Calc. spec. net thermal energy demand with efficiency factor
                curr_spec_th_demand = eff_factor * curr_th_e_demand / curr_nfa
            else:
                #  Spec. final energy demand is given, recalculate it to
                #  net thermal energy demand with efficiency factor
                curr_spec_th_demand *= eff_factor

            # # If curr_el_e_demand is not known, calculate it via spec. demand
            # if curr_el_e_demand is None:
            #     curr_el_e_demand = curr_spec_el_demand * curr_nfa

            if th_gen_method == 1 or th_gen_method == 2 or curr_build_type != 0:
                print('Used specific thermal demand value in kWh/m2*a:')
                print(curr_spec_th_demand)

            # print('Annual el. energy demand in kWh:')
            # print(curr_el_e_demand)
            # print()
            #
            # print('Used specific electric demand value in kWh/m2*a:')
            # print(curr_spec_el_demand)

            # if curr_nb_of_occupants is not None:
            #     print('Average spec. el. energy demand per person in kWh/a:')
            #     print(curr_el_e_demand / curr_nb_of_occupants)
            #     print()

            # #-------------------------------------------------------------
            #  Generate BuildingExtended object
            if curr_build_type == 0:  # Residential

                if curr_nb_of_apartments > 1:  # Multi-family house
                    building = generate_res_building_multi_zone(environment,
                                                                net_floor_area=curr_nfa,
                                                                spec_th_demand=curr_spec_th_demand,
                                                                annual_el_demand=curr_el_e_demand,
                                                                th_gen_method=th_gen_method,
                                                                el_gen_method=el_gen_method,
                                                                nb_of_apartments=curr_nb_of_apartments,
                                                                use_dhw=use_dhw,
                                                                dhw_method=dhw_method,
                                                                total_number_occupants=curr_nb_of_occupants,
                                                                build_year=curr_build_year,
                                                                mod_year=curr_mod_year,
                                                                build_type=curr_build_type,
                                                                pv_use_area=curr_pv_roof_area,
                                                                height_of_floors=curr_avg_height_of_floors,
                                                                nb_of_floors=curr_nb_of_floors,
                                                                neighbour_buildings=curr_nb_of_neighbour_bld,
                                                                residential_layout=curr_res_layout,
                                                                attic=curr_type_attic,
                                                                cellar=curr_type_cellar,
                                                                construction_type=new_curr_construction_type,
                                                                dormer=curr_dormer,
                                                                dhw_volumen=dhw_volumen,
                                                                do_normalization=do_normalization,
                                                                slp_manipulate=slp_manipulate,
                                                                curr_central_ahu=curr_central_ahu,
                                                                dhw_random=dhw_random,
                                                                prev_heat_dev=prev_heat_dev,
                                                                season_mod=season_mod)

                elif curr_nb_of_apartments == 1:  # Single-family house
                    building = generate_res_building_single_zone(environment,
                                                                 net_floor_area=curr_nfa,
                                                                 spec_th_demand=curr_spec_th_demand,
                                                                 annual_el_demand=curr_el_e_demand,
                                                                 th_gen_method=th_gen_method,
                                                                 el_gen_method=el_gen_method,
                                                                 use_dhw=use_dhw,
                                                                 dhw_method=dhw_method,
                                                                 number_occupants=curr_nb_of_occupants,
                                                                 build_year=curr_build_year,
                                                                 mod_year=curr_mod_year,
                                                                 build_type=curr_build_type,
                                                                 pv_use_area=curr_pv_roof_area,
                                                                 height_of_floors=curr_avg_height_of_floors,
                                                                 nb_of_floors=curr_nb_of_floors,
                                                                 neighbour_buildings=curr_nb_of_neighbour_bld,
                                                                 residential_layout=curr_res_layout,
                                                                 attic=curr_type_attic,
                                                                 cellar=curr_type_cellar,
                                                                 construction_type=new_curr_construction_type,
                                                                 dormer=curr_dormer,
                                                                 dhw_volumen=dhw_volumen,
                                                                 do_normalization=do_normalization,
                                                                 slp_manipulate=slp_manipulate,
                                                                 curr_central_ahu=curr_central_ahu,
                                                                 dhw_random=dhw_random,
                                                                 prev_heat_dev=prev_heat_dev,
                                                                 season_mod=season_mod)
                else:
                    raise AssertionError('Wrong number of apartments')
            else:  # Non-residential

                method_3_str = None
                method_4_str = None

                #  Convert curr_method numbers, if not None
                if curr_method_3_nb is not None:
                    method_3_str = \
                        convert_method_3_nb_into_str(int(curr_method_3_nb))

                if curr_method_4_nb is not None:
                    method_4_str = \
                        convert_method_4_nb_into_str(int(curr_method_4_nb))

                building = generate_nonres_building_single_zone(environment,
                                                                th_slp_type=curr_th_slp_type,
                                                                net_floor_area=curr_nfa,
                                                                spec_th_demand=curr_spec_th_demand,
                                                                annual_el_demand=curr_el_e_demand,
                                                                el_slp_type=curr_el_slp_type,
                                                                build_year=curr_build_year,
                                                                mod_year=curr_mod_year,
                                                                build_type=curr_build_type,
                                                                pv_use_area=curr_pv_roof_area,
                                                                method_3_type=method_3_str,
                                                                method_4_type=method_4_str,
                                                                height_of_floors=curr_avg_height_of_floors,
                                                                nb_of_floors=curr_nb_of_floors
                                                                )

            # Generate position shapely point
            position = point.Point(curr_x, curr_y)

            if generation_mode == 0:
                #  Add building to city object
                id = city_object.add_extended_building(
                    extended_building=building,
                    position=position, name=curr_id)

            elif generation_mode == 1:
                #  Add building as entity to corresponding building node

                #  Positions should be (nearly) equal
                assert position.x - city_object.node[int(curr_id)][
                    'position'].x <= 0.1
                assert position.y - city_object.node[int(curr_id)][
                    'position'].y <= 0.1
                city_object.node[int(curr_id)]['entity'] = building

                id = curr_id

            # Save annual thermal net heat energy demand for space heating
            #  to dict (used for normalization with VDI 6007 core)
            dict_id_vdi_sh[id] = curr_spec_th_demand * curr_nfa

            print('Finished processing of building', curr_id)
            print('#######################################################')
            print()

            #  If only single building should be processed, break loop
            if multi_data is False:
                break

        # #-------------------------------------------------------------
        print('Added all buildings with data to city object.')

        #  VDI 6007 simulation to generate space heating load curves
        #  Overwrites existing heat load curves (and annual heat demands)
        if th_gen_method == 3:

            print('Perform VDI 6007 space heating load simulation for every'
                  ' building')

            if el_gen_method == 1:
                #  Skip usage of occupancy and electrial load profiles
                #  as internal loads within VDI 6007 core
                requ_profiles = False
            else:
                requ_profiles = True

            tusage.calc_and_add_vdi_6007_loads_to_city(city=city_object,
                                                       air_vent_mode=air_vent_mode,
                                                       vent_factor=vent_factor,
                                                       t_set_heat=t_set_heat,
                                                       t_set_cool=t_set_cool,
                                                       t_night=t_night,
                                                       alpha_rad=None,
                                                       project_name=project_name,
                                                       requ_profiles=requ_profiles)

            #  Set call_teaser to False, as it is already included
            #  in calc_and_add_vdi_6007_loads_to_city
            call_teaser = False

            if vdi_sh_manipulate:
                #  Normalize VDI 6007 load curves to match given annual
                #  thermal space heating energy demand
                for n in city_object.nodes():
                    if 'node_type' in city_object.node[n]:
                        #  If node_type is building
                        if city_object.node[n]['node_type'] == 'building':
                            #  If entity is kind building
                            if city_object.node[n][
                                'entity']._kind == 'building':

                                #  Given value (user input)
                                ann_sh = dict_id_vdi_sh[n]

                                #  Building pointer
                                curr_b = city_object.node[n]['entity']

                                #  Current value on object
                                curr_sh = curr_b.get_annual_space_heat_demand()

                                norm_factor = ann_sh / curr_sh

                                #  Do normalization
                                #  Loop over apartments
                                for apart in curr_b.apartments:
                                    #  Normalize apartment space heating load
                                    apart.demandSpaceheating.loadcurve \
                                        *= norm_factor

        print('Generation results:')
        print('###########################################')
        for n in city_object.nodes():
            if 'node_type' in city_object.node[n]:
                if city_object.node[n]['node_type'] == 'building':
                    if 'entity' in city_object.node[n]:
                        if city_object.node[n]['entity']._kind == 'building':
                            print('Results of building: ', n)
                            print('################################')
                            print()

                            curr_b = city_object.node[n]['entity']
                            sh_demand = curr_b.get_annual_space_heat_demand()
                            el_demand = curr_b.get_annual_el_demand()
                            dhw_demand = curr_b.get_annual_dhw_demand()
                            nfa = curr_b.net_floor_area

                            print('Annual space heating demand in kWh:')
                            print(sh_demand)
                            if nfa is not None and nfa != 0:
                                print(
                                    'Specific space heating demand in kWh/m2:')
                                print(sh_demand / nfa)
                            print()

                            print('Annual electric demand in kWh:')
                            print(el_demand)
                            if nfa is not None and nfa != 0:
                                print('Specific electric demand in kWh/m2:')
                                print(el_demand / nfa)

                            nb_occ = curr_b.get_number_of_occupants()

                            if nb_occ is not None and nb_occ != 0:
                                print('Specific electric demand in kWh'
                                      ' per person and year:')
                                print(el_demand / nb_occ)

                            print()

                            print('Annual hot water demand in kWh:')
                            print(dhw_demand)
                            if nfa is not None and nfa != 0:
                                print('Specific hot water demand in kWh/m2:')
                                print(dhw_demand / nfa)

                            volume_year = dhw_demand * 1000 * 3600 / (
                                4200 * 35)
                            volume_day = volume_year / 365
                            if nb_occ is not None and nb_occ != 0:
                                v_person_day = \
                                    volume_day / nb_occ
                                print('Hot water volume per person and day:')
                                print(v_person_day)

                            print()

        # Create and add TEASER type_buildings to every building node
        if call_teaser:
            #  Create TEASER project
            project = tusage.create_teaser_project(name=teaser_proj_name,
                                                   merge_windows=merge_windows)

            #  Generate typeBuildings and add to city
            tusage.create_teaser_typecity(project=project,
                                          city=city_object,
                                          generate_Output=False)

        if do_save:

            if path_save_city is None:
                if pickle_city_filename is None:
                    msg = 'If path_save_city is None, pickle_city_filename' \
                          'cannot be None! Instead, filename has to be ' \
                          'defined to be able to save city object.'
                    raise AssertionError
                this_path = os.path.dirname(os.path.abspath(__file__))
                path_save_city = os.path.join(this_path, 'output',
                                              pickle_city_filename)

            try:
                #  Pickle and dump city objects
                pickle.dump(city_object, open(path_save_city, 'wb'))
                print('Pickled and dumped city object to: ')
                print(path_save_city)
            except:
                warnings.warn('Could not pickle and save city object')

        if do_log:

            if pickle_city_filename is not None:
                log_file.write('pickle_city_filename: ' +
                               str(pickle_city_filename)
                               + '\n')
            print('Wrote log file to: ' + str(log_path))
            #  Close log file
            log_file.close()

        # Visualize city
        if show_city:
            #  Plot city district
            try:
                citvis.plot_city_district(city=city_object,
                                          plot_street=False)
            except:
                warnings.warn('Could not plot city district.')

    return city_object


if __name__ == '__main__':
    this_path = os.path.dirname(os.path.abspath(__file__))

    #  User inputs  #########################################################

    #  Choose generation mode
    #  ######################################################
    #  0 - Use csv/txt input to generate city district
    #  1 - Use csv/txt input file to enrich existing city object, based on
    #  osm call (city object should hold nodes, but no entities. City
    #  generator is going to add building, apartment and load entities to
    #  building nodes
    generation_mode = 0

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
    #  electrical load generation (only relevant if el_gen_method == 2)
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
    dhw_random = False

    #  Input file names and pathes
    #  ######################################################
    #  Define input data filename

    filename = 'city_3_buildings.txt'
    # filename = 'city_clust_simple.txt'
    # filename = 'aachen_forsterlinde_mod_6.txt'
    # filename = 'aachen_frankenberg_mod_6.txt'
    # filename = 'aachen_huenefeld_mod_6.txt'
    # filename = 'aachen_kronenberg_mod_8.txt'
    # filename = 'aachen_preusweg_mod_8.txt'
    # filename = 'aachen_tuerme_mod_6.txt'

    #  Output filename
    pickle_city_filename = filename[:-4] + '.pkl'

    #  For generation_mode == 1:
    # city_osm_input = None
    # city_osm_input = 'aachen_forsterlinde_mod_7.pkl'
    city_osm_input = 'aachen_frankenberg_mod_7.pkl'
    # city_osm_input = 'aachen_huenefeld_mod_7.pkl'
    # city_osm_input = 'aachen_kronenberg_mod_7.pkl'
    # city_osm_input = 'aachen_preusweg_mod_7.pkl'
    # city_osm_input = 'aachen_tuerme_mod_7.pkl'

    #  Pickle and dump city object instance?
    do_save = True

    #  Path to save city object instance to
    path_save_city = None
    #  If None, uses .../output/...

    #  Efficiency factor of thermal energy systems
    #  Used to convert input values (final energy demand) to net energy demand
    eff_factor = 1

    #  For VDI 6007 simulation (th_gen_method == 3)
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

    vent_factor = 0.3  # Constant. ventilation rate
    #  (only used, if air_vent_mode is 0. Otherwise, estimate vent_factor
    #  based on last year of modernization)

    #  TEASER typebuilding generation
    #  ######################################################
    #  Use TEASER to generate typebuildings?

    call_teaser = False
    teaser_proj_name = filename[:-4]
    #  Requires additional attributes (such as nb_of_floors, net_floor_area..)

    merge_windows = False
    #  merge_windows : bool, optional
    #  Defines TEASER project setting for merge_windows_calc
    # (default: False). If set to False, merge_windows_calc is set to False.
    #  If True, Windows are merged into wall resistances.

    txt_path = os.path.join(this_path, 'input', filename)
    if generation_mode == 1:
        path_city_osm_in = os.path.join(this_path, 'input', city_osm_input)

    # Path for log file
    log_f_name = log_file_name = str('log_' + filename)
    log_f_path = os.path.join(this_path, 'output', log_file_name)

    #  End of user inputs  ################################################

    print('Run city generator for ', filename)

    assert generation_mode in [0, 1]

    if generation_mode == 1:
        assert city_osm_input is not None

    if air_vent_mode == 1 or air_vent_mode == 2:
        assert el_gen_method == 2, 'air_vent_mode 1 and 2 require occupancy' \
                                   ' profiles!'

    # Load district_data file
    district_data = get_district_data_from_txt(txt_path)

    if generation_mode == 1:

        #  Load city input file
        city_osm = pickle.load(open(path_city_osm_in, mode='rb'))

    else:
        #  Dummy value
        city_osm = None

    # Generate city district
    city = run_city_generator(generation_mode=generation_mode,
                              timestep=timestep,
                              year=year, location=location,
                              th_gen_method=th_gen_method,
                              el_gen_method=el_gen_method, use_dhw=use_dhw,
                              dhw_method=dhw_method,
                              district_data=district_data,
                              pickle_city_filename=pickle_city_filename,
                              eff_factor=eff_factor, show_city=True,
                              try_path=try_path, altitude=altitude,
                              dhw_volumen=dhw_volumen,
                              do_normalization=do_normalization,
                              slp_manipulate=slp_manipulate,
                              call_teaser=call_teaser,
                              teaser_proj_name=teaser_proj_name,
                              air_vent_mode=air_vent_mode,
                              vent_factor=vent_factor,
                              t_set_heat=t_set_heat,
                              t_set_cool=t_set_cool,
                              t_night=t_set_night,
                              vdi_sh_manipulate=vdi_sh_manipulate,
                              city_osm=city_osm, el_random=el_random,
                              dhw_random=dhw_random,
                              prev_heat_dev=prev_heat_dev,
                              log_path=log_f_path,
                              season_mod=season_mod,
                              merge_windows=merge_windows,
                              new_try=new_try,
                              path_save_city=path_save_city,
                              do_save=do_save)

    # if call_teaser:
    #     #  Search for residential building
    #     for n in city.nodes():
    #         if 'node_type' in city.node[n]:
    #             #  If node_type is building
    #             if city.node[n]['node_type'] == 'building':
    #                 #  If entity is of type pv
    #                 if city.node[n]['entity']._kind == 'building':
    #                     if city.node[n]['entity'].build_type == 0:
    #                         break
    #
    #     type_building = city.node[n]['type_building']
    #     print(type_building)

    # el_power = city.get_aggr_el_power_curve()
    #
    # import matplotlib.pyplot as plt
    #
    # plt.plot(el_power)
    # plt.show()
    # plt.close()
