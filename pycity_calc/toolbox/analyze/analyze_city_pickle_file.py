#!/usr/bin/env python
# coding=utf-8
"""
Script to analyze pickle city file
"""
from __future__ import division
import os
import pickle
import warnings
import numpy as np
import matplotlib.pyplot as plt

import pycity_calc.toolbox.dimensioning.dim_functions as dimfunc
import pycity_calc.visualization.city_visual as citvis
import pycity_calc.toolbox.teaser_usage.teaser_use as tusage
import pycity_calc.toolbox.networks.network_ops as netop
import pycity_calc.cities.scripts.city_generator.city_generator as citgen



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


def get_nb_build_nodes_and_entities(city, print_out=False):
    """
    Returns number of building nodes and building entities in city

    Parameters
    ----------
    city : object
        City object of pycity_calc
    print_out : bool, optional
        Print out results (default: False)

    Returns
    -------
    res_tuple : tuple
        Results tuple with number of building nodes (int) and
        number of building entities
        (nb_b_nodes, nb_buildings)

    Annotations
    -----------
    building node might also be PV- or wind-farm (not only building entity)
    """

    nb_b_nodes = 0
    nb_buildings = 0

    for n in city.nodes():

        if 'node_type' in city.node[n]:
            if city.node[n]['node_type'] == 'building':

                if 'entity' in city.node[n]:

                    if city.node[n]['entity']._kind == 'building':
                        nb_buildings += 1

                    if (city.node[n]['entity']._kind == 'building' or
                                city.node[n][
                                    'entity']._kind == 'windenergyconverter' or
                                city.node[n]['entity']._kind == 'pv'):
                        nb_b_nodes += 1

    if print_out:  # pragma: no cover
        print('Number of building nodes (Buildings, Wind- and PV-Farms):')
        print(nb_b_nodes)
        print()

        print('Number of buildings: ', nb_buildings)
        print()

    return (nb_b_nodes, nb_buildings)


def get_ann_energy_demands(city, print_out=False):
    """
    Returns annual energy demands of city in kWh (space heating, electrical,
    hot water)

    Parameters
    ----------
    city : object
        City object of pycity_calc
    print_out : bool, optional
        Print out results (default: False)

    Returns
    -------
    res_tuple : Tuple (of floats)
        3d tuple with space heating, electrical and hot water energy demands
        in kWh
        (ann_space_heat, ann_el_dem, ann_dhw_dem)
    """

    ann_space_heat = round(city.get_annual_space_heating_demand(), 2)
    ann_el_dem = round(city.get_annual_el_demand(), 2)
    ann_dhw_dem = round(city.get_annual_dhw_demand(), 2)

    if print_out:  # pragma: no cover
        print('Annual net thermal space heating demand in kWh: ')
        print(ann_space_heat)
        print()

        print('Annual electrical demand in kWh: ')
        print(ann_el_dem)
        print()

        print('Annual hot water energy demand in kWh: ')
        print(ann_dhw_dem)
        print()

        print('Percentage of space heat demand on total thermal demand in %:')
        print((100 * ann_space_heat) / (ann_space_heat + ann_dhw_dem))
        print('Percentage of hot water demand on total thermal demand in %:')
        print((100 * ann_dhw_dem) / (ann_space_heat + ann_dhw_dem))

    return (ann_space_heat, ann_el_dem, ann_dhw_dem)


def get_power_curves(city, print_out=False):
    """
    Returns city power curves (space heating, electrical, hot water) in W

    Parameters
    ----------
    city : object
        City object of pycity_calc
    print_out : bool, optional
        Print out results (default: False)

    Returns
    -------
    res_tuple : Tuple (of numpy arrays)
        3d tuple with power curves in W
        (sh_power_curve, el_power_curve, dhw_power_curve)
    """

    sh_power_curve = city.get_aggr_space_h_power_curve()
    el_power_curve = city.get_aggr_el_power_curve()
    dhw_power_curve = city.get_aggr_dhw_power_curve()

    if print_out:  # pragma: no cover
        timestep = city.environment.timer.timeDiscretization

        time_array = np.arange(0, 365 * 24 * 3600 / timestep, timestep / 3600)

        ylab = str(timestep / 3600)

        plt.plot(time_array, sh_power_curve / 1000, label='Space heat')
        plt.plot(time_array, el_power_curve / 1000, label='El. power')
        plt.plot(time_array, dhw_power_curve / 1000, label='Hot water')
        plt.xlabel('Time with ' + ylab + ' hours timestep')
        plt.ylabel('Power in kW')
        plt.legend()
        plt.show()

    return (sh_power_curve, el_power_curve, dhw_power_curve)


def get_min_max_th_sh_powers(city, print_out=False):
    """
    Returns maximal thermal space heating power of whole city as well as
    smallest and largest single building space heating powers in W.

    Parameters
    ----------
    city : object
        City object of pycity_calc
    print_out : bool, optional
        Print out results (default: False)

    Returns
    -------
    res_tuple : tuple (of floats)
        3d tuple with maximal thermal space heating power of city,
        smallest and largest single buildig space heating power in W.
        (max_th_power_city, small_max_th_power_build, larg_max_th_power_build)
    """

    max_th_power_city = dimfunc.get_max_p_of_city(city_object=city) / 1000

    (id, larg_max_th_power_build) = dimfunc.get_id_max_th_power(city=city,
                                                                find_max=True,
                                                                return_value=True)

    (id, small_max_th_power_build) = dimfunc.get_id_max_th_power(city=city,
                                                                 find_max=False,
                                                                 return_value=True)

    if print_out:  # pragma: no cover
        print('Maximal thermal power of complete district (without dhw) '
              'in kW: ')
        print(round(max_th_power_city, 2))
        print()

        print('Largest max. thermal power within building ' + str(id) +
              '  with thermal power ' +
              str(round(larg_max_th_power_build / 1000, 2)) +
              ' kW.')
        print()

        print('Smallest max. thermal power within building ' + str(id) +
              '  with thermal power ' + str(
            round(small_max_th_power_build / 1000, 2)) +
              ' kW.')
        print()

    return (max_th_power_city, small_max_th_power_build,
            larg_max_th_power_build)


def get_mod_year_hist(city, plot_hist=True, facecolor='#EC635C',
                      xlabel='Last year of modernization', ylabel='Share'):
    """
    Generate histogram of last years of modification for all buildings in
    city

    Parameters
    ----------
    city : object
        city object of pycity_calc
    plot_hist : bool, optional
        Plot histogram (default: True)
    facecolor : str, optional
        Color of histogram bars (default: '#EC635C'; red)
    xlabel : str, optional
        xlabel (default: 'Years')
    ylabel : str, optional
        ylabel (default: 'Share')

    Returns
    -------
    list_mod_years : list (of ints)
        List of mod years, which are not None
    """

    list_mod_years = []

    for n in city.nodes():
        if 'node_type' in city.node[n]:
            if city.node[n]['node_type'] == 'building':
                if 'entity' in city.node[n]:
                    if city.node[n]['entity']._kind == 'building':

                        if city.node[n]['entity'].mod_year is not None:

                            mod_year = city.node[n]['entity'].mod_year

                            list_mod_years.append(mod_year)

    print(list_mod_years.sort())
    print(len(list_mod_years))

    if plot_hist:  # pragma: no cover

        # nb_bins = int((max(list_mod_years) - min(list_mod_years))/2)
        nb_bins = np.arange(min(list_mod_years), max(list_mod_years) +1)

        fig = plt.figure()

        #  Change rc paramters
        plt.rc('font', family='Arial', size=16)

        # the histogram of the data
        plt.hist(list_mod_years, nb_bins, normed=len(list_mod_years),
                 facecolor=facecolor,
                 alpha=1)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.tight_layout()
        plt.show()
        plt.close()

    return list_mod_years


def check_kwf_standard(exbuild, id=None, kfw=40, pe_gas=1.1, eff_boiler=0.9):
    """
    Checks, if building is able to keep kfw standard based on assumption of
    boiler usage with natural gas.

    Parameters
    ----------
    exbuild : object
        BuildingExtended object of pycity_calc
    id : int, optional
        Building id (default: None)
    kfw : int, optional
        KWF standard number (default: 40)
        Options: [40, 55, 70, 85, 100, 115]
    pe_gas : float, optional
        Primary energy (PE) factor gas (default: 1.1)
    eff_boiler : float, optional
        Boiler efficiency

    Returns
    -------
    pe_m2_value : float
        Specific primary energy demand per m2 and year of building
    """

    assert kfw in [40, 55, 70, 85, 100, 115]

    if exbuild.net_floor_area is None:
        msg = 'KFW check requires existence of net floor area on building!'
        raise AssertionError(msg)

    assert exbuild.net_floor_area > 0, 'Area must be larger than zero!'

    #  Get net thermal energy demand of space heating and hot water
    sum_th_e_demand = exbuild.get_annual_space_heat_demand() + \
                      exbuild.get_annual_dhw_demand()

    #  Convert to final energy gas usage
    gas_e_demand = sum_th_e_demand / eff_boiler

    #  Calculate primary energy demand
    pe_demand = gas_e_demand * pe_gas

    #  Calculate specific primary energy demand
    pe_m2_value = pe_demand / exbuild.net_floor_area

    return pe_m2_value


def check_kfw_standard_city(city, kfw=40, pe_gas=1.1, eff_boiler=0.9):
    """
    Checks, if buildings within city are able to keep kfw standard based on
    assumption of boiler usage with natural gas.

    Parameters
    ----------
    city : object
        City object of pycity_calc
    kfw : int, optional
        KWF standard number (default: 40)
        Options: [40, 55, 70, 85, 100, 115]
    pe_gas : float, optional
        Primary energy (PE) factor gas (default: 1.1)
    eff_boiler : float, optional
        Boiler efficiency

    Returns
    -------
    list_b_non_kfw : list
        List of building node ids, which were not able to keep standard
    """

    assert kfw in [40, 55, 70, 85, 100, 115]

    list_b_non_kfw = []

    for n in city.nodes():

        if 'node_type' in city.node[n]:
            if city.node[n]['node_type'] == 'building':

                if 'entity' in city.node[n]:

                    if city.node[n]['entity']._kind == 'building':

                        #  Define pointer to building
                        build = city.node[n]['entity']

                        #  Specific primary energy demand per building
                        #  in kWh/m2*a
                        pe_m2 = \
                            check_kwf_standard(exbuild=build, id=n, kfw=kfw,
                                               pe_gas=pe_gas,
                                               eff_boiler=eff_boiler)

                        if pe_m2 > kfw:
                            msg = 'Specific primary energy demand of ' \
                                  + str(pe_m2) + ' kWh/m2 is larger than ' \
                                                 'KFW ' + str(kfw) + ' value!'
                            warnings.warn(msg)
                            list_b_non_kfw.append(n)

    return list_b_non_kfw


def check_single_building_consistency(exbuild, id=None, check_sh=True,
                                      check_el=True,
                                      check_dhw=True, check_occ=True,
                                      check_base_par=True,
                                      check_bes=False):
    """
    Function checks if building object has been fully parameterized.
    If specific attribute is missing or its value seems to be wrong, prints
    out warnings.

    Assumes existence of apartment(s) within building object

    Parameters
    ----------
    exbuild : object
        BuildingExtended object of pycity_calc, which should be checked
    id : int, optional
        Building id / primary key (integer) (default: None)
    check_sh : bool, optional
        Defines, if space heating object should be checked (default: True)
    check_el : bool, optional
        Defines, if electrical object should be checked (default: True)
    check_dhw : bool, optional
        Defines, if hot water should be checked (default: True)
    check_occ : bool, optional
        Defines, if occupancy object should be checked (default: True)
    check_base_par : bool, optional
        Defines, if base parameters should be checked (default: True)
    check_bes : bool, optional
        Defines, if existing of BES should be checked (default: False)

    Returns
    -------
    b_is_correct : bool
        If no problem occurred, value is True.
        If problem occured, value is set to False
    """

    assert exbuild._kind == 'building', 'Input is not a building entity!'

    #  Assert, if every building holds apartment
    #  Each building entity should hold, at least, one apartment (or zone),
    #  which can hold load objects
    assert exbuild.hasApartments is True
    assert len(exbuild.apartments) > 0
    for ap in exbuild.apartments:
        assert ap._kind == 'apartment'

    b_is_correct = True  # Initial values, assuming consinstency of building

    timestep = exbuild.environment.timer.timeDiscretization

    print('Check building with id: ', id)
    print('Building type number: ', exbuild.build_type)

    build_name = citgen.conv_build_type_nb_to_name(exbuild.build_type)
    print('Building type explanation: ', build_name)

    if check_base_par:
        # Check existence of base parameters of
        #  ##############################################################
        if exbuild.build_year is None:
            msg = 'Building ' + str(id) + \
                  ' has no build_year (year of construction)!'
            warnings.warn(msg)
            b_is_correct = False

        if exbuild.build_type is None:
            msg = 'Building ' + str(id) + \
                  ' has no build_type (type of building)!'
            warnings.warn(msg)
            b_is_correct = False

        if exbuild.net_floor_area is None:
            msg = 'Building ' + str(id) + \
                  ' has no net floor area!'
            warnings.warn(msg)
            b_is_correct = False

        if exbuild.height_of_floors is None:
            msg = 'Building ' + str(id) + \
                  ' has no height_of_floors!'
            warnings.warn(msg)
            b_is_correct = False

        if exbuild.nb_of_floors is None:
            msg = 'Building ' + str(id) + \
                  ' has no nb_of_floors!'
            warnings.warn(msg)
            b_is_correct = False

        if exbuild.build_year is not None and exbuild.mod_year is not None:
            if exbuild.build_year > exbuild.mod_year:
                msg = 'Building ' + str(id) + 'has larger year of ' \
                                              'construction (' + str(
                    exbuild.build_year) + ')' \
                                          ' than year of modification (' + \
                      str(exbuild.mod_year) + ').'
                warnings.warn(msg)
                b_is_correct = False

    if check_sh:
        #  Checks existence of space heating object(s)
        #  ##############################################################
        for ap in exbuild.apartments:
            sh_curve = ap.get_space_heat_power_curve(current_values=False)
            sh_energy_kwh = sum(sh_curve) * timestep / (1000 * 3600)

            if sh_energy_kwh == 0:
                msg = 'Apartment of building ' + str(id) + \
                      ' has zero space heating demand!'
                warnings.warn(msg)
                b_is_correct = False

            elif sh_energy_kwh < 0:
                raise AssertionError('Apartment of building ' + str(id) +
                                     ' has negative space heating demand!')

        sh_building_kwh = exbuild.get_annual_space_heat_demand()
        if sh_building_kwh == 0:
            msg = 'Building ' + str(id) + \
                  ' has zero space heating demand!'
            warnings.warn(msg)
            b_is_correct = False

        if exbuild.build_type == 0:
            if sh_building_kwh < 3000:
                msg = 'Building ' + str(id) + ' has very low space heating ' \
                                              'energy demand of ' + str(
                    sh_building_kwh) + ' kWh'
                warnings.warn(msg)
                b_is_correct = False

            elif sh_building_kwh > 50000:
                msg = 'Building ' + str(id) + ' has very high space heating ' \
                                              'energy demand of ' + str(
                    sh_building_kwh) + ' kWh'
                warnings.warn(msg)
                b_is_correct = False

        if exbuild.net_floor_area is not None and exbuild.net_floor_area != 0:
            if sh_building_kwh/exbuild.net_floor_area < 50:
                msg = 'Building ' + str(id) + ' has very low specific space ' \
                                              'heating ' \
                                              'energy demand of ' + str(
                    sh_building_kwh / exbuild.net_floor_area) + ' kWh/m2a'
                warnings.warn(msg)
                b_is_correct = False

            elif sh_building_kwh/exbuild.net_floor_area > 300:
                msg = 'Building ' + str(id) + ' has very high specific space ' \
                                              'heating ' \
                                              'energy demand of ' + str(
                    sh_building_kwh / exbuild.net_floor_area)+ ' kWh/m2a'
                warnings.warn(msg)
                b_is_correct = False

    if check_el:
        #  Checks existence of electrical load object(s)
        #  ##############################################################
        for ap in exbuild.apartments:
            el_curve = ap.get_el_power_curve(current_values=False)
            el_energy_kwh = sum(el_curve) * timestep / (1000 * 3600)

            if el_energy_kwh == 0:
                msg = 'Apartment of building ' + str(id) + \
                      ' has zero electrical demand!'
                warnings.warn(msg)
                b_is_correct = False

            elif el_energy_kwh < 0:
                raise AssertionError('Apartment of building ' + str(id) +
                                     ' has negative electrical demand!')
                b_is_correct = False

        el_building_kwh = exbuild.get_annual_el_demand()
        if el_building_kwh == 0:
            msg = 'Building ' + str(id) + \
                  ' has zero electrical demand!'
            warnings.warn(msg)
            b_is_correct = False

        if exbuild.build_type == 0:
            if el_building_kwh < 1000 and exbuild.build_type == 0:
                msg = 'Building ' + str(id) + ' has very low electrical ' \
                                              'energy demand of ' + str(
                    el_building_kwh) + ' kWh'
                warnings.warn(msg)
                b_is_correct = False

            elif el_building_kwh > 40000 and exbuild.build_type == 0:
                msg = 'Building ' + str(id) + ' has very high electrical ' \
                                              'energy demand of ' + str(
                    el_building_kwh) + ' kWh'
                warnings.warn(msg)
                b_is_correct = False

        if exbuild.net_floor_area is not None and exbuild.net_floor_area != 0:
            if el_building_kwh/exbuild.net_floor_area < 10:
                msg = 'Building ' + str(id) + ' has very low specific ' \
                                              'electric ' \
                                              'energy demand of ' + str(
                    el_building_kwh / exbuild.net_floor_area) + ' kWh/m2a'
                warnings.warn(msg)
                b_is_correct = False

            elif el_building_kwh/exbuild.net_floor_area > 100:
                msg = 'Building ' + str(id) + ' has very high specific electric ' \
                                              'energy demand of ' + str(
                    el_building_kwh / exbuild.net_floor_area)+ ' kWh/m2a'
                warnings.warn(msg)
                b_is_correct = False

    if check_dhw:
        #  Checks existence of hot water object(s)
        #  ##############################################################
        if exbuild.build_type == 0:
            for ap in exbuild.apartments:
                dhw_curve = ap.get_dhw_power_curve(current_values=False)
                dhw_energy_kwh = sum(dhw_curve) * timestep / (1000 * 3600)

                if dhw_energy_kwh == 0:
                    msg = 'Apartment of building ' + str(id) + \
                          ' has zero hot water demand!'
                    warnings.warn(msg)
                    b_is_correct = False

                elif dhw_energy_kwh < 0:
                    raise AssertionError('Apartment of building ' + str(id) +
                                         ' has negative hot water!')

            dhw_building_kwh = exbuild.get_annual_dhw_demand()
            if dhw_building_kwh == 0:
                msg = 'Building ' + str(id) + \
                      ' has zero hot water!'
                warnings.warn(msg)
                b_is_correct = False

            water_mass = dhw_building_kwh * 3600 * 1000 / (4200 * 35)
            volume_per_day = water_mass / 365

            if exbuild.get_number_of_occupants() is not None:
                volume_per_person_and_day = \
                    volume_per_day / exbuild.get_number_of_occupants()

                if volume_per_person_and_day < 10:
                    msg = 'Building ' + str(id) + \
                          ' has low hot water volume per person and day of: ' \
                          '' + str(volume_per_person_and_day) + ' liters.'
                    warnings.warn(msg)
                    b_is_correct = False
                elif volume_per_person_and_day > 80:
                    msg = 'Building ' + str(id) + \
                          ' has high hot water volume per person and day of: ' \
                          '' + str(volume_per_person_and_day) + ' liters.'
                    warnings.warn(msg)
                    b_is_correct = False

    if check_occ and exbuild.build_type == 0:
        #  Checks existence of occupancy object(s) for residential buildings
        #  ##############################################################
        for ap in exbuild.apartments:
            occupancy = ap.occupancy

            if occupancy is None:
                msg = 'Apartment of building ' + str(id) + \
                      ' has zero no occupancy object!'
                warnings.warn(msg)
                b_is_correct = False

            else:
                if occupancy.occupancy is None:
                    msg = 'Apartment of building ' + str(id) + \
                          ' has occupancy object, but no occupancy profiles!'
                    warnings.warn(msg)
                    b_is_correct = False

                elif max(occupancy.occupancy) == 0:
                    msg = 'Apartment of building ' + str(id) + \
                          ' has occupancy object and profile, but profile' \
                          'is zero for every timestep!'
                    warnings.warn(msg)
                    b_is_correct = False

    if check_bes:
        #  Check existence of BES
        #  ##############################################################
        if exbuild.hasBes is False:
            msg = 'Building ' + str(id) + ' has no BES!'
            warnings.warn(msg)
            b_is_correct = False

    return b_is_correct


def check_city_consinstency(city, check_sh=True, check_el=True,
                            check_dhw=True, check_occ=True,
                            check_base_par=True, check_bes=False,
                            check_typebuilding=False):
    """
    Checks consistency of city district and prints warnings, if expected
    attributes are missing or seems to be wrong

    Parameters
    ----------
    city : object
        City object of pycity_calc
    check_sh : bool, optional
        Defines, if space heating object should be checked (default: True)
    check_el : bool, optional
        Defines, if electrical object should be checked (default: True)
    check_dhw : bool, optional
        Defines, if hot water should be checked (default: True)
    check_occ : bool, optional
        Defines, if occupancy object should be checked (default: True)
    check_base_par : bool, optional
        Defines, if base parameters should be checked (default: True)
    check_bes : bool, optional
        Defines, if existence of BES should be checked (default: False)
    check_typebuilding : bool, optional
        Defines, if existence of TEASER typebuilding should be checked
        (default: False)

    Returns
    -------
    list_incor_b_nodes : list (of ints)
        List of building node ids, which seems to miss specific parameters or
        hold values, which seems to be incorrect.
    """

    list_other_nodes = []
    list_incor_b_nodes = []

    for n in city.nodes():

        if 'node_type' in city.node[n]:
            if city.node[n]['node_type'] == 'building':

                if 'entity' in city.node[n]:

                    if city.node[n]['entity']._kind == 'building':

                        #  Define pointer to building
                        build = city.node[n]['entity']

                        #  Process building analysis
                        is_consistent = \
                            check_single_building_consistency(exbuild=build,
                                                              id=n,
                                                              check_sh=check_sh,
                                                              check_el=check_el,
                                                              check_dhw=check_dhw,
                                                              check_occ=check_occ,
                                                              check_base_par=check_base_par,
                                                              check_bes=check_bes)

                        if is_consistent is False:
                            list_incor_b_nodes.append(n)

                        if check_typebuilding:
                            found_t_build = False
                            if 'type_building' in city.node[n]:
                                if city.node[n]['node_type'] is not None:
                                    found_t_build = True
                            if found_t_build is False:
                                msg = 'Building node ' + str(n) + ' has no' \
                                                                  'TEASER typebuilding!'
                                warnings.warn(msg)

        else:
            list_other_nodes.append(n)

        if len(list_other_nodes) > 0:
            msg = 'Found nodes, which are not of known uesgraphs or pycity' \
                  ' types: ' + str(list_other_nodes)
            warnings.warn(msg)

    print('List of building nodes, which seems to be incorrect or which miss'
          ' specific attributes: ', list_incor_b_nodes)

    return list_incor_b_nodes


def run_c_file_an(city_object):
    """
    Perform analysis of city_object. Includes:
    - Number of buildings
    - Plot of city structure
    - Max. thermal peak loads in kW
    - Annual thermal and electrical demands in kWh

    Parameters
    ----------
    city_object : object
        City object of pycity_calc
    """

    print('Timestep of environment: ')
    print(city_object.environment.timer.timeDiscretization)
    print()

    #  Get building nodes and entities
    get_nb_build_nodes_and_entities(city=city_object, print_out=True)

    #  Plot city district
    citvis.plot_city_district(city=city_object, offset=7,
                              x_label='x-coordinate in m',
                              y_label='y-coordinate in m',
                              equal_axis=True,
                              plot_build_labels=True)

    #  Get infos about city and building space heating thermal power levels
    get_min_max_th_sh_powers(city_object, print_out=True)

    #  Get annual energy demands of city
    get_ann_energy_demands(city_object, print_out=True)

    #  Get annual power load curves of city
    get_power_curves(city_object, print_out=True)


if __name__ == '__main__':
    #  City pickle filename
    # city_file = 'city_clust_simple.p'
    # city_file = 'aachen_forsterlinde_osm.pkl'
    # city_file = 'aachen_frankenberg_osm.pkl'
    # city_file = 'aachen_huenefeld_osm.pkl'
    # city_file = 'aachen_kronenberg_osm.pkl'
    # city_file = 'aachen_preusweg_osm.pkl'
    # city_file = 'aachen_tuerme_osm.pkl'

    city_file = 'aachen_forsterlinde_mod_new_1.pkl'
    # city_file = 'aachen_frankenberg_mod_new_1.pkl'
    # city_file = 'aachen_huenefeld_mod_new_1.pkl'
    # city_file = 'aachen_kronenberg_mod_new_1.pkl'
    # city_file = 'aachen_preusweg_mod_new_1.pkl'
    # city_file = 'aachen_tuerme_mod_new_1.pkl'

    print('Analyse city file: ', city_file)

    #  Path to load file
    this_path = os.path.dirname(os.path.abspath(__file__))
    pycity_path = os.path.dirname(os.path.dirname(this_path))

    # file_path = os.path.join(this_path, 'input', 'aachen', city_file)
    file_path = os.path.join(pycity_path, 'cities', 'scripts',
                             'city_generator',
                             'output', city_file)

    #  Load city object from pickle file
    city = load_pickled_city_file(file_path)

    check_sh = True  # Check space heating
    check_el = True  # Check electrical demand object
    check_dhw = True  # Check hot water demand object
    check_occ = True  # Check occupancy object
    check_base_par = True  # Check existence of base parameters of building
    check_bes = False  # Check existence of BES on building
    check_typebuilding = False  # Check existence of TEASER typebuilding

    #  Check consistency of file
    check_city_consinstency(city=city, check_sh=check_sh, check_el=check_el,
                            check_dhw=check_dhw, check_occ=check_occ,
                            check_base_par=check_base_par, check_bes=check_bes,
                            check_typebuilding=check_typebuilding)

    #  Run analyzation script
    run_c_file_an(city_object=city)

    get_min_max_th_sh_powers(city, print_out=True)







    #  Uncomment following parts for further analysis, if required
    #  ###################################################################


    #  Plot and save in multipel formats
    #  ####################################################################

    # out_folder = os.path.splitext(city_file)[0]
    #
    # print(out_folder)
    #
    # main_save_path = os.path.join(this_path, 'output', out_folder)
    #
    # print(main_save_path)
    # input()
    #
    # citvis.plot_multi_city_district(city=city, main_save_path=main_save_path,
    #                                 city_list=None,
    #                                 plot_buildings=True,
    #                                 plot_street=True, plot_lhn=True,
    #                                 plot_deg=True, plot_esys=True,
    #                                 offset=10,
    #                                 plot_build_labels=False,
    #                                 plot_str_labels=False,
    #                                 equal_axis=False, font_size=16,
    #                                 plt_title=None,
    #                                 show_plot=False,
    #                                 fig_adjust=None,
    #                                 plot_elec_labels=False, save_plot=True,
    #                                 dpi=1000,
    #                                 auto_close=True, plot_str_dist=None)


    # #  Extract subcity
    # #  ####################################################################
    # list_sub = [1018, 1020, 1021, 1026, 1027, 1028, 1022]
    #
    # subcity = netop.get_build_str_subgraph(city=city, nodelist=list_sub)
    #
    # save_path = os.path.join(this_path, 'output', 'extr_alex.p')
    #
    # pickle.dump(subcity, open(save_path, mode='wb'))


    # #  Add KFW retrofit to buildings
    #  ###################################################################
    # tusage.add_kfw_retrofit_to_city(city=city, material=None, thickness=1)
    #
    # tusage.calc_and_add_vdi_6007_loads_to_city(city=city, air_vent_mode=0,
    #                                            vent_factor=0.05,
    #                                            use_exist_tbuild=True)
    #
    # list_non = check_kfw_standard_city(city=city)
    #
    # print('List of building ids, which do not stay within KFW limitations:')
    # print(list_non)
    #
    # #  Run analyzation script
    # run_c_file_an(city_object=city)
    #
    # out_fname = city_file[:-2] + '_kfw.p'
    # out_path = os.path.join(this_path, 'output', out_fname)
    #
    # pickle.dump(city, open(out_path, mode='wb'))




    #  Save load curves to file
    #  ###################################################################
    # build_1 = city.node[1001]['entity']
    #
    # space_h_load = build_1.get_space_heating_power_curve()
    # el_load = build_1.get_electric_power_curve()
    # dhw_load =build_1.get_dhw_power_curve()
    #
    # time_array = np.arange(0, 8760)
    #
    # dataset = np.transpose(np.vstack((time_array, space_h_load, el_load, dhw_load)))
    #
    # print(dataset)
    #
    # this_path = os.path.dirname(os.path.abspath(__file__))
    # filename = 'wm_res_east_single_profiles.txt'
    # save_path = os.path.join(this_path, filename)
    #
    # np.savetxt(save_path, dataset, delimiter='\t')
