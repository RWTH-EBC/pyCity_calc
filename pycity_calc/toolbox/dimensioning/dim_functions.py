#!/usr/bin/env python
# coding=utf-8
"""
Script with dimensioning functions of pycity_calc
"""
from __future__ import division

import os
import pickle
import math
import warnings
import numpy as np
from bisect import bisect_left

import pycity_base.functions.process_city as prcity
import pycity_calc.energysystems.Input.chp_asue_2015 as asue


#  # General dimensioning functions
#  #------------------------------------------------------------------------

def get_max_p_of_power_curve(power_curve):
    """
    Returns maximal power of given power curve.

    Parameters
    ----------
    power_curve : numpy.array
        numpy array with power values per timestep (in W)

    Returns
    -------
    max_power : float
        Maximal power in W
    """

    max_power = np.amax(power_curve)
    return max_power


def max_rect_method(th_power_curve, force_min_runtime=False, timestep=None,
                    min_runtime=None):
    """
    Performs rectangular method on th_power_curve. Sorts th_power_curve in
    descending order. Then tries to find maximum rectangular area below curve
    and returns corresponding thermal power value.

    Parameters
    ----------
    th_power_curve : np.array
        Thermal power load curve
    force_min_runtime : bool, optional
        Defines, if min_runtime must be kept
        (default: False)
        False - Not necessary to keep min_runtime
        True - Necessary to keep min_runtime
    timestep : int, optional
        Timestep in seconds.
        (default: None)
    min_runtime : float, optional
        Minimum runtime CHP should have per year (in hours!).
        (default: None)

    Returns
    -------
    rec_power : float
        Thermal power value (for maximum rectangle area)
    """

    #  Sort power curve descending
    th_power_curve.sort()
    load_dur_curve = th_power_curve[::-1]

    #  Initial value
    max_rec_area = 0

    #  Look for max area as well as corresponding
    for i in range(len(load_dur_curve)):
        curr_power = load_dur_curve[i]
        curr_area = i * curr_power
        #  If new value is larger than curr. max value
        if curr_area > max_rec_area:
            #  Replace max value
            max_rec_area = curr_area
            rec_index = i  # Save search index of max. value
            rec_power = curr_power  # Save power value

    if force_min_runtime:  # Requires minimum runtime of device
        assert timestep >= 0
        assert min_runtime > 0, 'Min. runtime should be larger than zero.'
        assert min_runtime <= 8760 + 24,  ('Runtime size exceeds ' +
                                           'maximum hours per year.')

        #  Runtime for max rec method in seconds
        reached_runtime = rec_index * timestep

        #  If reached runtime is smaller than desired runtime
        if reached_runtime < min_runtime * 3600:  # Conversion to seconds
            print('Reached runtime ' + str(reached_runtime/3600) +
                  ' is smaller than required runtime of ' +
                  str(min_runtime) + ' hours.')
            print('Thus, min_runtime_method is called.')
            #  Call min_runtime_method and overwrite rec_power
            rec_power = min_runtime_method(th_power_curve, timestep,
                                           min_runtime)

    return rec_power


def min_runtime_method(th_power_curve, timestep, min_runtime):
    """
    Calculate nominal thermal power output for necessary, minimum runtime
    (in hours!!!)

    Parameters
    ----------
    th_power_curve : np.array
        Thermal power values per timestep
    timestep : int
        Timestep in seconds
    min_runtime : float
        Minimum runtime thermal device should have per year (in hours!).

    Returns
    -------
    nom_power : float
        Nominal thermal power
    """

    assert timestep >= 0
    assert min_runtime > 0, 'Min. runtime should be larger than zero.'
    assert min_runtime <= 8760 + 24,  ('Runtime size exceeds ' +
                                       'maximum hours per year.')

    #  Convert min_runtime from hours to seconds
    min_runtime_s = min_runtime * 3600

    #  Calculate index
    index = math.ceil(min_runtime_s/timestep)

    #  Sort power curve descending
    th_power_curve.sort()
    load_dur_curve = th_power_curve[::-1]

    nom_power = load_dur_curve[index]

    assert nom_power > 0, ('Nominal power cannot be zero. It seems like' +
                           ' the load duration curve does not allow ' +
                           'the desired, mimimum runtime. Consider '+
                           'reducing the minimum runtime!')

    return nom_power

def round_esys_size(power, round_up=False):
    """
    Round nominal power values. Rounding dependent on
    decimal size of power input value.

    Parameters
    ----------
    power : float
        Power value in W
    round_up : bool, optional
        Defines if all values should be rounded up
        (default: False)

    Returns
    -------
    power_round : int
        Rounded power value in W
    """

    assert power >= 0

    if round_up:

        if power > 10000:
            power_round = math.ceil(power/1000)*1000
        elif power > 1000:
            power_round = math.ceil(power/100)*100
        elif power > 100:
            power_round = math.ceil(power/10)*10
        else:
            power_round = math.ceil(power)

    else:  # Open direction for rounding

        if power > 10000:
            power_round = round(power/1000, 0)*1000
        elif power > 1000:
            power_round = round(power/100, 0)*100
        elif power > 100:
            power_round = round(power/10, 0)*10
        else:
            power_round = round(power, 0)

    return power_round


#  # Functions to process building objects
#  #------------------------------------------------------------------------

def get_load_dur_curve_building(building, get_therm=True, with_dhw=False):
    """
    Returns load duration power curve of building object.

    Parameters
    ----------
    building : object
        Building object of pycity (should have apartment with power curves)
    get_therm : bool, optional
        Defines if thermal or electrical load duration curve should be used
        (default: True)
        True - Return thermal power
        False - Return electrical power
    with_dhw : bool, optional
        Defines if domestic hot water (dhw) should be included (only relevant,
        if get_therm == True).
        (default: False)
        True - Return space heating power only
        False - Return space heating and hot water power

    Returns
    -------
    load_dur_curve : np.array
        Duration load curve array (power sorted in descending order)
    """

    if get_therm:  # Thermal power
        power_curve = building.get_space_heating_power_curve()
        if with_dhw:
            power_curve += building.get_dhw_power_curve()
    else:  # Electrical power
        power_curve = building.get_electric_power_curve()

    # Sort descending
    power_curve.sort()
    load_dur_curve = power_curve[::-1]
    return load_dur_curve


def get_max_power_of_building(building, get_therm=True, with_dhw=False):
    """
    Returns maximal power of building load curve.

    Parameters
    ----------
    building : object
        Building object of pycity (should have apartment with power curves)
    get_therm : bool, optional
        Defines if thermal or electrical load duration curve should be used
        (default: True)
        True - Return thermal power
        False - Return electrical power
    with_dhw : bool, optional
        Defines if domestic hot water (dhw) should be included (only relevant,
        if get_therm == True).
        (default: False)
        True - Return space heating power only
        False - Return space heating and hot water power

    Returns
    -------
    max_power : float
        Maximum power value
    """

    if get_therm:  # Thermal power
        power_curve = building.get_space_heating_power_curve()
        if with_dhw:
            power_curve += building.get_dhw_power_curve()
    else:  # Electrical power
        power_curve = building.get_electric_power_curve()

    max_power = np.amax(power_curve)
    return max_power


#  # Functions to process city objects
#  #------------------------------------------------------------------------

def get_ann_load_dur_curve(city_object, get_thermal=True, with_dhw=False,
                           nodelist=None):
    """
    Returns annual load duration curve of city_object

    Parameters
    ----------
    city_object : object
        City object of pycity_calc.
    get_thermal : bool, optional
        Defines if thermal curve should be returned
        (default: True)
        If set to False, electrical curve is returned
    with_dhw : bool, optional
        Defines, if dhw demand should be included within thermal power value.
        Only relevant, if get_thermal=True
        (default: False)
        False --> Only space heating max. power
        True --> Space heating + domestic hot water max power
    nodelist : list, optional
        List with building node ids, for which the annual load duration
        curve should be calculated (default: None)

    Returns
    -------
    ann_load_dur_curve : np.array
        Numpy array with power values per timestep
    """

    # if nodelist is not None:  # Get subgraph
    #     temp_city = prcity.get_subcity(city=city_object, nodelist=nodelist)
    # else:  # Use whole city district
    #     temp_city = city_object

    if nodelist is None:
        #  Use all nodes ids which hold building entity
        nodelist = city_object.get_list_build_entity_node_ids()

    #  TODO: Add function to check if nodelist only hold building entity nodes

    if get_thermal:  # Get th. power curve
        aggr_load_curve = np.zeros(city_object.environment.timer.timestepsTotal)
        #  for all ids in nodelist
        for n in nodelist:
            th_power_curve = city_object.node[n]['entity']. \
                                get_space_heating_power_curve\
                                    (current_values=False)
            aggr_load_curve += th_power_curve

        if with_dhw:
            #  for all ids in nodelist
            for n in nodelist:
                dhw_power_curve = city_object.node[n]['entity']. \
                                    get_dhw_power_curve\
                                        (current_values=False)
                aggr_load_curve += dhw_power_curve

    else:  # El. power curve
        aggr_load_curve = np.zeros(city_object.environment.timer.timestepsTotal)
        #  for all ids in nodelist
        for n in nodelist:
            el_power_curve = city_object.node[n]['entity']. \
                                get_aggr_el_power_curve\
                                    (current_values=False)
            aggr_load_curve += el_power_curve

    # Sort descending
    aggr_load_curve.sort()
    ann_load_dur_curve = aggr_load_curve[::-1]

    return ann_load_dur_curve


def get_max_p_of_city(city_object, get_thermal=True, with_dhw=False,
                      nodelist=None):
    """
    Returns maximal power value of chosen buildings in city object.

    Parameters
    ----------
    city_object : object
        City object of pycity_calc.
    get_thermal : bool, optional
        Defines if thermal curve should be returned
        (default: True)
        If set to False, electrical curve is returned
    with_dhw : bool, optional
        Defines, if dhw demand should be included within thermal power value.
        Only relevant, if get_thermal=True
        (default: False)
        False --> Only space heating max. power
        True --> Space heating + domestic hot water max power
    nodelist : list, optional
        List with building node ids, for which the annual load duration
        curve should be calculated (default: None)

    Returns
    -------
    max_power : float
        Maximal power in W
    """

    #  Get aggregated power curve
    aggr_power_curve = get_ann_load_dur_curve(city_object=city_object,
                                              get_thermal=get_thermal,
                                              with_dhw=with_dhw,
                                              nodelist=nodelist)

    #  Get max power
    max_power = get_max_p_of_power_curve(aggr_power_curve)
    return max_power


def get_id_max_th_power(city, with_dhw=False, current_values=False,
                        find_max=True, return_value=False):
    """
    Returns id of building with smallest max thermal power value
    within city.

    Parameters
    ----------
    city : object
        City object
    with_dhw : bool, optional
        Defines, if space heating plus dhw power value should be used
        (default: False)
        False - Only space heating
        True - Space heating plus domestic hot water
    current_values : bool, optional
        Defines, if only current horizon or all timesteps should be used.
        (default: False)
        False - Use complete number of timesteps
        True - Use horizon
    find_max : bool, optional
        Defines, if largest th. power values should be searched for
        (default: True)
        True - Search for largest max. th. power value
        False - Search for smallest max. th. power value
    return_value : bool, optional
        Defines if thermal power value should be returned additionally
        (Default: False)

    Returns
    -------
    id : int
        ID of building node with smallest thermal power value
    result_tuple : tuple (if return_value == True)
        Tuple with node id and thermal power value (id, th_p_max)
    """

    #  Initial values
    id = None
    th_p_max = None

    #  Loop over all nodes
    for n in city:
        #  If node holds attribute 'node_type'
        if 'node_type' in city.node[n]:
            #  If node_type is building
            if city.node[n]['node_type'] == 'building':
                #  If entity is kind building
                if city.node[n]['entity']._kind == 'building':

                    #  Get thermal power curve
                    th_power_curve = city.node[n]['entity']. \
                        get_space_heating_power_curve(
                        current_values=current_values)

                    #  Add dhw power, if necessary
                    if with_dhw:
                        dhw_power_curve = city.node[n]['entity']. \
                            get_dhw_power_curve(
                            current_values=current_values)
                        th_power_curve += dhw_power_curve

                    #  Get max. power value
                    curr_th_p_max = np.max(th_power_curve)

                    #  If smallest value is None
                    if th_p_max is None:
                        th_p_max = curr_th_p_max
                        id = n

                    #  Compare with current value
                    if find_max:  # Find largest max value
                        if curr_th_p_max > th_p_max:
                            th_p_max = curr_th_p_max
                            id = n
                    else:  # Find smallest max value
                        if curr_th_p_max < th_p_max:
                            th_p_max = curr_th_p_max
                            id = n
    if return_value:
        return (id, th_p_max)
    else:
        return id


#  # CHP size dimensioning
#  #-----------------------------------------------------------------------

def calc_chp_nom_th_power(th_power_curve, method=1, min_runtime=6000,
                          force_min_runtime=False, timestep=None):
    """
    Calculate nominal thermal power of CHP system (for given thermal power
    curve)

    Parameters
    ----------
    th_power_curve : np.array
        Thermal power values per timestep
    method : int, optional
        Method, which should be used for nominal power calculation
        (default: 1)
        Options:
        1 - Maximum rectangular
        2 - Minimum runtime per year
        3 - Maximum power
    min_runtime : float, optional
        Minimum runtime CHP should have per year (in hours!).
        Only relevant, if method == 2
        or force_min_runtime == True and method == 1
        (default: 6000)
    force_min_runtime : bool, optional
        Defines, if min_runtime must be kept (only relevant for method 1)
        (default: False)
        False - Not necessary to keep min_runtime
        True - Necessary to keep min_runtime
    timestep : int, optional
        Timestep in seconds. Only relevant for methods 2
        (default: None)

    Returns
    -------
    chp_nom_power : float
        CHP nominal thermal power
    """

    list_method = [1, 2, 3]
    assert method in list_method, 'Unknown chp sizing method.'

    if method == 1:  # Max. rectangle method

        #  Rectangular method
        chp_nom_power = max_rect_method(th_power_curve,
                                        force_min_runtime=force_min_runtime,
                                        timestep=timestep,
                                        min_runtime=min_runtime)

    elif method == 2:  # Min. runtime

        assert timestep is not None, 'Method 2 requires timestep'

        #  Use min. runtime method
        chp_nom_power = min_runtime_method(th_power_curve=th_power_curve,
                                           timestep=timestep,
                                           min_runtime=min_runtime)

    elif method == 3:  # Max. th. power

        chp_nom_power = np.amax(th_power_curve)

    return chp_nom_power


def calc_chp_nom_th_power_building(building, with_dhw=False,
                                   method=1, min_runtime=6000,
                                   force_min_runtime=False):
    """
    Calculate CHP nominal thermal power for building object.

    Parameters
    ----------
    building : object
        Building object of pycity
    with_dhw : bool, optional
        Defines, if hot water power should also be taken into account.
        (default: False)
        False - Only space heating demand for dimensioning
        True - Space heating and hot water power demand
    method : int, optional
        Method, which should be used for nominal power calculation
        (default: 1)
        Options:
        1 - Maximum rectangular
        2 - Minimum runtime per year
        3 - Maximum power
    min_runtime : float, optional
        Minimum runtime CHP should have per year (in hours!).
        Only relevant, if method == 2
        (default: 6000)
    force_min_runtime : bool, optional
        Defines, if min_runtime must be kept (only relevant for method 1)
        (default: False)
        False - Not necessary to keep min_runtime
        True - Necessary to keep min_runtime

    Returns
    -------
    chp_nom_power : float
            CHP nominal thermal power
    """

    #  Get space heating power curve of building
    th_power_curve = building.get_space_heating_power_curve()

    if with_dhw:
        #  Add hot water power curve
        th_power_curve += building.get_dhw_power_curve()

    #  Get timestep
    timestep = building.environment.timer.timeDiscretization

    #  Calculate nominal thermal chp power
    chp_nom_power = calc_chp_nom_th_power(th_power_curve=th_power_curve,
                                          method=method,
                                          min_runtime=min_runtime,
                                          timestep=timestep,
                                          force_min_runtime=force_min_runtime)
    return chp_nom_power

#  # Storage size dimensioning
#  #-----------------------------------------------------------------------

def storage_rounding(capacity):
    """
    Round thermal storage sized to next rounding step.
    Discrete sizes were chosen based on Buderus tables.

    Parameters
    ----------
    capacity : float
        Storage mass in kg (water)

    Returns
    -------
    capacity_sel : int
        Selected storage mass value in kg (water)
    """

    assert capacity > 0, 'Capacity should be larger than zero!'

    if capacity <= 100:
        capacity_sel = 100
    elif capacity <= 160:
        capacity_sel = 160
    elif capacity <= 200:
        capacity_sel = 200
    elif capacity <= 300:
        capacity_sel = 300
    elif capacity <= 400:
        capacity_sel = 400
    elif capacity <= 500:
        capacity_sel = 500
    elif capacity <= 750:
        capacity_sel = 750
    elif capacity <= 1000:
        capacity_sel = 1000
    elif capacity <= 1500:
        capacity_sel = 1500
    elif capacity <= 2000:
        capacity_sel = 2000
    elif capacity <= 2500:
        capacity_sel = 2500
    elif capacity <= 3000:
        capacity_sel = 3000
    else:
        capacity_sel = math.ceil(capacity/1000)*1000

    return capacity_sel


def take_closest(list_val, number):
    """
    Finds closest value in list_val to number

    Parameters
    ----------
    list_val : list (of floats)
        Search list
    number : float
        Search number

    Returns
    -------
    closest_val : float
        Value of list_val, which is closest to number input
    """

    list_val.sort()

    pos = bisect_left(list_val, number)
    if pos == 0:
        return list_val[0]
    if pos == len(list_val):
        return list_val[-1]
    before = list_val[pos - 1]
    after = list_val[pos]
    if after - number < number - before:
       return after
    else:
       return before

def calc_chp_el_sizes_for_opt(city, nb_sizes, mode, with_dhw=False):
    """
    Returns list of possible CHP sizes (el. nominal power in Watt) for
    pyCity_opt, based on city and single building thermal power curves

    Minimum possible size is defined with 1 kW el. power.

    Parameters
    ----------
    city : object
        City object of pyCity_calc
    nb_sizes : int
        Number of chp sizes
    mode : int
        Integer to select generation mode. Options:
        0 - For single buildings and city (equidistant space between
        th. power of smallest peak load building and whole city district th.
        power
        1 - For single buildings only
        2 - For force LHN / whole district, only
        3 - Fill up with discrete steps [1, 2, 3, 5, 10, 20, 30, 40, 50, 60,
        70, 80, 90, 100, 150, 200, 250, 300, 350, 400, 450, 500, 1000,
        1500, 2000],
        depending on city max. thermal power demand
    with_dhw : bool, optional
        Defines, if hot water demand should also be taken into account
        (default: False)

    Returns
    -------
    list_chp_size_el : list (of floats)
        List with different possible CHP nominal electric power sizes in
        Watt
    """

    assert mode in [0, 1, 2, 3], 'Unknown mode'
    assert nb_sizes > 0

    if nb_sizes <= 2:
        msg = 'Small number of CHPs chosen. Consider increasing nb_sizes.'
        warnings.warn(msg)

    list_chp_size_el = []

    #  Get id of max. th. power building
    id_max = get_id_max_th_power(city=city, with_dhw=with_dhw, find_max=True)
    #  Get id of building with min. max. thermal power
    id_min = get_id_max_th_power(city=city, with_dhw=with_dhw, find_max=False)

    #  Get max. th. power of building with largest thermal power
    q_dot_b_peak_max = \
        get_max_power_of_building(building=city.node[id_max]['entity'],
                                  with_dhw=with_dhw)
    #  Get max. th. power of building with smallest, max. power demand
    q_dot_b_peak_min = \
        get_max_power_of_building(building=city.node[id_min]['entity'],
                                  with_dhw=with_dhw)

    #  Get max. thermal power of city
    q_dot_city_peak = \
        get_max_p_of_city(city_object=city, with_dhw=with_dhw)

    if mode == 0:  # For city and single buildings (equidistant)
        array_chp_th = np.linspace(start=1/8 * q_dot_b_peak_min,
                                   stop=1/4 * q_dot_city_peak,
                                   num=nb_sizes)

        list_chp_th = array_chp_th.tolist()

    elif mode == 1:  # Sizing for single buildings, only
        array_chp_th = np.linspace(start=1/8 * q_dot_b_peak_min,
                                   stop=1/4 * q_dot_b_peak_max,
                                   num=nb_sizes)

        list_chp_th = array_chp_th.tolist()

    elif mode == 2: # For force LHN / whole district
        array_chp_th = np.linspace(start=1 / 10 * q_dot_city_peak,
                                   stop=1 / 2 * q_dot_city_peak,
                                   num=nb_sizes)

        list_chp_th = array_chp_th.tolist()

    elif mode == 3:

        #  Ref. electric energy demand in kW
        p_el_ref = 1/4 * q_dot_city_peak * \
                   asue.calc_asue_el_th_ratio(th_power=q_dot_city_peak) / 1000

        list_small = [1, 2, 3, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90]
        list_medium = np.arange(100, 500, 50).tolist()
        list_big = np.arange(500, 2500, 500).tolist()

        #  From 1 to 1000 kW el.
        list_choice = list_small + list_medium + list_big

        print(list_choice)

        #  Find closest value to p_el_ref in list_choice
        upper_val = take_closest(list_val=list_choice, number=p_el_ref)

        index_up = list_choice.index(upper_val)

        index_low = 0

        list_chp_size_el = []

        for i in range(nb_sizes):
            if i % 2 == 0:  # Even
                list_chp_size_el.append(list_choice[index_low])
                index_low += 1
            else:  # Odd
                list_chp_size_el.append(list_choice[index_up])
                index_up -= 1

        for i in range(len(list_chp_size_el)):
            list_chp_size_el[i] *= 1000  # Convert from kW to W

        list_chp_size_el.sort()

    if mode == 0 or mode == 1 or mode == 2:
        for i in range(len(list_chp_th)):

            th_power = list_chp_th[i]

            #  Get el./th. ratio (Stromkennzahl)
            el_th_ratio = asue.calc_asue_el_th_ratio(th_power=th_power)

            #  Convert to el. power
            el_power = round(th_power * el_th_ratio/1000, ndigits=0)*1000

            if el_power < 1000:
                el_power = 1000

            list_chp_size_el.append(el_power)

    return list_chp_size_el

if __name__ == '__main__':

    #  Estimate CHP sized
    this_path = os.path.dirname(os.path.abspath(__file__))

    city_file_name = 'city.pkl'

    city_path = os.path.join(this_path, 'input', city_file_name)

    city = pickle.load(open(city_path, mode='rb'))

    nb_sizes = 10
    chp_mode = 3
    with_dhw = False

    list_chp_size_el = calc_chp_el_sizes_for_opt(city=city,
                                                 nb_sizes=nb_sizes,
                                                 mode=chp_mode,
                                                 with_dhw=with_dhw)

    print('List of CHP nominal el. powers in Watt:')
    print(list_chp_size_el)