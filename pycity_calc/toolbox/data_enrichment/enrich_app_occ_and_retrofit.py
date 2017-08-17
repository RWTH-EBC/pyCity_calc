#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script loads basic city input txt file and:
- Checks it for missing inputs (if required input is missing, raises Assertion
Error)
- Enrichs buildings with number of apartments (if no number of apartments is
given)
- Enrichs residential buildings with total number of occupants per building
(if no total number of occupants is given)
- Estimates last year of retrofit for buildings with given thermal space
heating energy demand
- Saves enriched dataset as new txt file (which can be used as input file
for city generator)
"""
from __future__ import division

import os

import pycity_calc.cities.scripts.city_generator.city_generator as citgen
import pycity_calc.toolbox.data_enrichment.occupants.enrich_input_file as oen

def check_district_data_set(district_data, check_sim_data=True):
    """
    Checks consistency of district_data file

    Parameters
    ----------
    district_data : ndarray
        Numpy 2d-array with city district data (each column represents
        different parameter, see annotations)
    check_sim_data : bool, optional
        Checks all requires simulation data for VDI 6007 simulation with
        TEASER (space heating load generation)
        (default: True)

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

    print('Start city district input data checker')

    # Check if district_data only holds one entry for single building
    #  In this case, has to be processed differently
    if district_data.ndim > 1:
        multi_data = True
    else:  # Only one entry (single building)
        multi_data = False
        #  If multi_data is false, loop below is going to be exited with
        #  a break statement at the end.

    #  Extract data
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

        print('Check building with id: ', curr_id)

        assert curr_id is not None
        assert curr_x is not None
        assert curr_y is not None
        assert curr_build_type >= 0, 'Unknown building type'
        assert curr_nfa > 0
        assert curr_build_year is not None

        if (curr_nb_of_occupants is not None
            and curr_nb_of_apartments is not None):
            assert curr_nb_of_occupants / curr_nb_of_apartments <= 5, (
                'Average share of occupants per apartment should ' +
                'not exceed 5 persons! (Necessary for stochastic, el.' +
                'profile generation.)')

        if curr_mod_year is not None:
            curr_mod_year >= 1900
        if curr_th_e_demand is not None:
            curr_th_e_demand > 0
        if curr_el_e_demand is not None:
            curr_el_e_demand > 0
        if curr_pv_roof_area is not None:
            curr_pv_roof_area >= 0
        if curr_nb_of_apartments is not None:
            curr_nb_of_apartments >= 1
        if curr_nb_of_occupants is not None:
            curr_nb_of_occupants >= 1
        if curr_nb_of_floors is not None:
            curr_nb_of_floors >= 1
        if curr_avg_height_of_floors is not None:
            curr_avg_height_of_floors > 0
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

        if check_sim_data:
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

        if curr_method_3_nb is not None:
            curr_method_3_nb >= 0
        if curr_method_4_nb is not None:
            curr_method_4_nb >= 0

    print('Passed all checks!')
    print()


def enrich_apartments(district_data):
    """
    Enrich district_data set with number of apartments (for buildings,
    where no number of apartments is given). Automatically sets single
    apartment/zone for non-residential buildings, if no number of buildings is
    defined.
    Modifies district_data input parameter.

    Estimates nb. of apartments based on net floor area, according to
    statistics of TABULA:
    [Institut für Wohnen und Umwelt - IWU 2009] INSTITUT FÜR WOHNEN UND
    UMWELT - IWU: TABULA Average Buildings: German residential building
    stock. http://s2.building-typology.eu/abpdf/DE_N_01_EPISCOPE_
    CaseStudy_TABULA_National.pdf. Version: 2009
    with around 74 m2 per apartment

    Parameters
    ----------
    district_data : ndarray
        Numpy 2d-array with city district data (each column represents
        different parameter, see annotations)
    """

    print('Start apartment enrichment')

    # Check if district_data only holds one entry for single building
    #  In this case, has to be processed differently
    if district_data.ndim > 1:
        multi_data = True
    else:  # Only one entry (single building)
        multi_data = False
        #  If multi_data is false, loop below is going to be exited with
        #  a break statement at the end.

    #  Extract data
    #  Loop over district_data
    #  ############################################################
    for i in range(len(district_data)):

        if multi_data:
            #  Extract data out of input file
            curr_id = int(
                district_data[i][0])  # id / primary key of building
            curr_build_type = int(
                district_data[i][3])  # building type nb (int)
            curr_nfa = district_data[i][4]  # Net floor area in m2
            curr_nb_of_apartments = district_data[i][
                10]  # optional (Number of apartments)
        else:  # Single entry
            #  Extract data out of input file
            curr_id = int(district_data[0])  # id / primary key of building
            curr_build_type = int(
                district_data[3])  # building type nb (int)
            curr_nfa = district_data[4]  # Net floor area in m2
            curr_nb_of_apartments = district_data[
                10]  # optional (Number of apartments)

        if curr_nb_of_apartments is None:

            print('Building ' + str(curr_id) + ' has no number of apartments'
                                               '. Going to enrich it.')

            #  Check building type:
            if curr_build_type == 0:
                #  Estimate number of apartments
                nb_app = oen.est_nb_apartments(net_floor_area=curr_nfa)
                #  Set number of apartments
                district_data[i][10] = nb_app
                print('Added ' + str(nb_app) + ' apartments.')

            else:  # Non-residential type
                #  Set number of apartments/zones to 1
                district_data[i][10] = 1
                print('Added single apartment/zone to non-res. building.')

    print('All buildings hold number of apartments, now.')
    print()


if __name__ == '__main__':
    this_path = os.path.dirname(os.path.abspath(__file__))

    #  User input
    #  ####################################################################

    #  Input and output filename
    filename = 'city_3_buildings.txt'
    file_out = filename[:-4] + '_enrich.txt'

    #  Input and output filepath
    file_path = os.path.join(this_path, 'input', filename)
    out_path = os.path.join(this_path, 'output', file_out)

    #  Check input data consistency?
    check_input = True
    #  If True, runs input data checker
    #  If False, skips input data checker

    #  Enrich buildings with number of apartments, if no number of apartments
    #  is given
    enrich_apps = True

    #  Enrich buildings with number of occupants, if no number of occupants
    #  is given
    enrich_occ = True

    #  End of user input
    #  ####################################################################

    #  Load basic city input txt file
    #  Load city district data set
    district_data = citgen.get_district_data_from_txt(path=file_path)

    print('Total district data set:')
    print(district_data)
    print()

    if check_input:
        #  Run district data input checker
        check_district_data_set(district_data=district_data)

    if enrich_apps:
        #  Run apartment enrichment
        enrich_apartments(district_data=district_data)

    if enrich_occ:
        #  Run occupancy enrichment
        pass