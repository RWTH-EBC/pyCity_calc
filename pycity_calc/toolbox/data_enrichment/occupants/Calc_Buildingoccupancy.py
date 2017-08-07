#!/usr/bin/env python
# coding=utf-8

"""
Script to enrich input txt data file with number of apartments and total
occupants per building, based on year of construction and available net
floor area
(Zensusdatenbank Zensus 2011 der Statistischen Ämter des Bundes und der Länder
Represented by
Bayerisches Landesamt für Statistik
St.-Martin-Straße 47, 81541 München
Tel. +49 89 2119-0.)

This function contains different methods to determine the number of apartments
of a building.
A number of occupants is then assigned to each Apartment by probabilities
depending
onf the net_floor_area calculated from statistic Data. (determine_occ())

Important function: np.random.choice(a,p) custom descrete randomfunction,
returns single items from given list with custom probability p for each item


Implemented 14.10.2016 by jsc-swi
"""
from __future__ import division
import os
import numpy as np
import csv
import pycity_calc.cities.scripts.city_generator.city_generator as citgen


# calculate occupancy probabilities
def calc_occ_probability(net_floor_class, list_occ_prob):
    """
    Calculate probabilities for number of occupants depending on net_floor
    area.

    Parameters
    ----------
    net_floor_class: int
        Net floor area categorie
        options
        0:A<40m^2, 1:40m^2<=A<60m^2, 2:60m^2<=A<80m^2,....,
        8:180m^2<=A<200m^2, 9:A>200m^2
    list_occ_prob: list
        List with
        occupancy probabilities:
        row: net_floor_class;
        columns: number
        of occupants, Database according to Zensus 2011
        ROWS AND COLUMNS HAVE TO BE OF THE EXACT FORMAT AS IN FILE
        'data/BuildingData/Personen_Wohnungsflaeche_commented.csv'

    Returns
    -------
    p: list
        List with probabilities for each number of occupants
    """
    # open .csv file with probabilities, row: net_floor_class;
    # columns: number of occupants

    # convert str list to float list
    liste_int = list(map(float, list_occ_prob[net_floor_class]))
    p = []

    # calculate probabilities from absolute values
    for i in liste_int:
        p.append(i / sum(liste_int))

    # return list of probabilities for each number of occupants
    return p


# calculate number of apartment probabilities
def calc_num_ap_probability(BuildingTypes, build_year_class, list_ap_prob,
                            custom_p=[0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
                                      0.1, 0.1]):
    """
    Calculate the probability of the number of apartments for one building
    It can be chosen between different methods (configurable
    by BuildingTypes) to determine this probability.

    Parameters
    ----------
    BuildingTypes: str
        Building type string, options:
        SFH: Single family house
        DFH: Double family house
        MFH: Multiple family house
        STAT: Statistic distribution of houses
        CUSTOM: customized probabilities, list of 10
        items required, sum(list)=1
    build_year_class:  int
        Building year class
        year of build, 0: before 1950, 1:
        1950 to 1969, 2: 1970 to 1989, 3: after 1990
    list_ap_prob: list
        qapartment probabilities:
        row: buildyearclass(see Annotations);
        columns: number
        of apartments, Database according to Zensus 2011
        ROWS AND COLUMNS HAVE TO BE OF THE EXACT FORMAT AS IN FILE
        'data/BuildingData/Personen_Wohnungsflaeche_commented.csv'
    custom_p: list, optional
        list of apartment number probabilities, list of 10
        items, sum(list)=1 (default: [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
                                      0.1, 0.1])

    Returns
    -------
    p: list
        List of probabilities for each number of apartments
    """

    assert BuildingTypes == 'SFH' or BuildingTypes == "DFH" or BuildingTypes == "MFH" or BuildingTypes == "STAT" or BuildingTypes == "CUSTOM", "Unknown BuildTypes: SFH, DFH, MFH, STAT, CUSTOM"

    if BuildingTypes == "STAT":
        assert build_year_class == 0 or build_year_class == 1 or build_year_class == 2 or build_year_class == 3, 'invalid buildyear class'
        #  TODO: calculate correct probabilities for apartnumbers 3 to 13,
        #  BuildingTypes=STAT is not ready yet!

        liste_int = list(map(float, list_ap_prob[build_year_class]))
        p = []

        for i in liste_int:
            p.append(i / sum(liste_int))

        return p

    elif BuildingTypes == "SFH":
        return [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    elif BuildingTypes == "DFH":
        return [0, 1, 0, 0, 0, 0, 0, 0, 0, 0]

    elif BuildingTypes == "MFH":
        return [0.2, 0.2, 0.2, 0.2, 0, 0, 0, 0, 0, 0]
        # TODO determine reasonable values

    elif BuildingTypes == "CUSTOM":
        assert len(custom_p), "len(custom_p) must be 10"
        p = custom_p
        return p


# determine and store occupancy of apartment
def determine_occ(ap_net_floor_area, list_occ_prob):
    """
    Determine occupancy of apartment. Number of occupants depends
    on net_floor area.

    Parameters
    ----------
    ap_net_floor_area: float
        Netto floor area of apartment
    list_occ_prob, 'list',  occupancy probabilities:
        row: net_floor_class; columns: number
        of occupants, Database according to Zensus 2011
        ROWS AND COLUMNS HAVE TO BE OF THE EXACT FORMAT AS IN FILE
        'data/BuildingData/Personen_Wohnungsflaeche_commented.csv'

    Returns:
    -------
    occupants: 'int', number of occupants of an apartment

    """
    if ap_net_floor_area < 40:  # net floor class 0
        occupants = np.random.choice([1, 2, 3, 4, 5], 1,
                                     p=calc_occ_probability(0,
                                                            list_occ_prob))  # determine apartments occupants
    elif 60 > ap_net_floor_area >= 40:  # net floor class 1
        occupants = np.random.choice([1, 2, 3, 4, 5], 1,
                                     p=calc_occ_probability(1,
                                                            list_occ_prob))  # determine apartments occupants
    elif 80 > ap_net_floor_area >= 60:  # net floor class 2
        occupants = np.random.choice([1, 2, 3, 4, 5], 1,
                                     p=calc_occ_probability(2,
                                                            list_occ_prob))  # determine apartments occupants
    elif 100 > ap_net_floor_area >= 80:  # net floor class 3
        occupants = np.random.choice([1, 2, 3, 4, 5], 1,
                                     p=calc_occ_probability(3,
                                                            list_occ_prob))  # determine apartments occupants
    elif 120 > ap_net_floor_area >= 100:  # net floor class 4
        occupants = np.random.choice([1, 2, 3, 4, 5], 1,
                                     p=calc_occ_probability(4,
                                                            list_occ_prob))  # determine apartments occupants
    elif 140 > ap_net_floor_area >= 120:  # net floor class 5
        occupants = np.random.choice([1, 2, 3, 4, 5], 1,
                                     p=calc_occ_probability(5,
                                                            list_occ_prob))  # determine apartments occupants
    elif 160 > ap_net_floor_area >= 140:  # net floor class 6
        occupants = np.random.choice([1, 2, 3, 4, 5], 1,
                                     p=calc_occ_probability(6,
                                                            list_occ_prob))  # determine apartments occupants
    elif 180 > ap_net_floor_area >= 160:  # net floor class 7
        occupants = np.random.choice([1, 2, 3, 4, 5], 1,
                                     p=calc_occ_probability(7,
                                                            list_occ_prob))  # determine apartments occupants
    elif 200 > ap_net_floor_area >= 180:  # net floor class 8
        occupants = np.random.choice([1, 2, 3, 4, 5], 1,
                                     p=calc_occ_probability(8,
                                                            list_occ_prob))  # determine apartments occupants
    elif ap_net_floor_area >= 200:  # net floor class 9
        occupants = np.random.choice([1, 2, 3, 4, 5], 1,
                                     p=calc_occ_probability(9,
                                                            list_occ_prob))  # determine apartments occupants

    return occupants


# determine number of apartments and occupancy from building
def determine_ap_num(district_data, BuildingTypes, custom_p, list_occ_prob,
                     list_ap_prob):
    """
    Determine number of apartments and occupancy of a building. BuildingTypes
    sets the method to
    to determine number of apartments.
    The apartment net floor area is calculated by dividing the buildings net
    floor area into equal parts depending on the number of apartments.

    Parameters
    ----------
    district_data: ndarray
        Numpy 2d-array with city district data (each
        column represents different parameter, see annotations)
    BuildingTypes:  str
        Building type
        Options:
        SFH: Single family house
        DFH: Double family house
        MFH: Multiple family house
        STAT: Statistic distribution of houses
        CUSTOM: customized probabilities, list of 10  items required,
        sum(list)=1
    custom_p: list
        list of apartment number probabilities, list of 10, items, sum(list)=1
    list_occ_prob: list
        occupancy probabilities:
        row: net_floor_class;
        columns: number
        of occupants, Database according to Zensus 2011
        ROWS AND COLUMNS HAVE TO BE OF THE EXACT FORMAT AS IN FILE
        'data/BuildingData/Personen_Wohnungsflaeche_commented.csv'
    list_ap_prob: list
        apartment probabilities:
        row: buildyearclass (see Annotations);
        columns: number
        of apartments, Database according to Zensus 2011
        ROWS AND COLUMNS HAVE TO BE OF THE EXACT FORMAT AS IN FILE
        'data/BuildingData/Personen_Wohnungsflaeche_commented.csv'

    Returns:
    -------
    district_data:
        ndarray, Numpy 2d-array with city district data (each
        column represents different parameter, see annotations)

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

    # Add all buildings from city to their construction year class
    nodelist_constr_year_to1950 = []
    nodelist_constr_year_1950to1969 = []
    nodelist_constr_year_1970to1989 = []
    nodelist_constr_year_1990older = []

    for i in range(len(district_data)):
        buildyear = district_data[i][5]
        build_type = district_data[i][3]

        assert buildyear is not None, ("No year of construction at node",
                                       district_data[i][0])

        if buildyear < 1950:
            if build_type == 0:
                nodelist_constr_year_to1950.append(i)
        elif 1969 >= buildyear >= 1950:
            if build_type == 0:
                nodelist_constr_year_1950to1969.append(i)
        elif 1989 >= buildyear >= 1970:
            if build_type == 0:
                nodelist_constr_year_1970to1989.append(i)
        elif buildyear >= 1990:
            if build_type == 0:
                nodelist_constr_year_1990older.append(i)

    # Generate dictionary with construction years (years as keys (as ints)
    dict_const_lists = {}

    dict_const_lists[1950] = nodelist_constr_year_to1950
    dict_const_lists[1969] = nodelist_constr_year_1950to1969
    dict_const_lists[1989] = nodelist_constr_year_1970to1989
    dict_const_lists[1990] = nodelist_constr_year_1990older

    for key in dict_const_lists:
        list_constr = dict_const_lists[key]
        if len(list_constr) != 0:
            for i in list_constr:

                if key == 1950:
                    b_y_class = 0
                elif key == 1969:
                    b_y_class = 1
                elif key == 1989:
                    b_y_class = 2
                elif key == 1990:
                    b_y_class = 3

                list_nb = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

                #  Get list of probabilities for each number of apartments
                prob = calc_num_ap_probability(BuildingTypes=BuildingTypes,
                                               build_year_class=b_y_class,
                                               list_ap_prob=list_ap_prob,
                                               custom_p=custom_p)

                #  Generate random sample from list_nb with probabilities prob
                num_apartments = np.random.choice(list_nb, 1, prob)
                #  determine number of apartments in a building

                occupants_total = 0

                #  Loop over apartments
                for n in range(int(num_apartments)):
                    ap_net_floor_area = district_data[i][4] / num_apartments
                    # calculate apartment net_floor_area

                    occupants = determine_occ(ap_net_floor_area,
                                              list_occ_prob)
                    # determine and store occupancy of apartment

                    occupants_total += occupants
                district_data[i][11] = occupants_total
                district_data[i][10] = num_apartments

    return district_data


def save_dist_data_to_file(dist_data, path):
    """
    Save district_data array to path. Replaces all None with np.nan

    Parameters
    ----------
    district_data : ndarray
        Numpy 2d-array with city district data (each column represents
        different parameter, see annotations)
    path : str,
        Path to save file to

    Annotations
    -----------
    district_data structure
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

    #  Define header
    header = 'id\tX\tY\tbuilding_type\ttab_ease_building_net_floor_area' \
             '\ttab_ease_building_build_year\ttab_ease_building_mod_year' \
             '\tAnnual thermal e demand in kWh' \
             '\tAnnual electr. E demand in kWh\tUsable pv roof area in m2' \
             '\tNumber of apartments\tTotal number of occupants' \
             '\tNumber of floors\tHeight of floors\twith ahu' \
             '\tresidential layout\tneighbour buildings\tattic\tcellar' \
             '\tdormer\tconstruction type\tmethod_3_type\tmethod_4_type'

    #  Replace all None with np.nan to prevent saving errors
    for i in range(len(dist_data)):
        for j in range(len(dist_data[0])):
            if district_data[i][j] is None:
                district_data[i][j] = np.nan

    # Save to path
    np.savetxt(path, dist_data, delimiter='\t', header=header, fmt='%1.0f')

    print('Saved district data to path ' + str(path))


def get_list_occ_prob_from_csv():
    """
    Load statistical occupancy probabilites from .csv file
    (file holds number of apartments with specific net floor area (rows) and
    number of persons (columns)

    Returns
    -------
    list_occ_prob: list
        List (of lists) for calculation of occupancy probabilities.
        row: net_floor_class(see Annotations);
        columns: number
        of occupants, Database according to Zensus 2011
        ROWS AND COLUMNS HAVE TO BE OF THE EXACT FORMAT AS IN FILE
        'data/BuildingData/Personen_Wohnungsflaeche_commented.csv'

    Annotations
    -----------
    net_floor_class: 'int',
        0:A<40m^2, 1:40m^2<=A<60m^2, 2:60m^2<=A<80m^2,....,
        8:180m^2<=A<200m^2, 9:A>200m^2
    """

    this_path = os.path.dirname(os.path.abspath(__file__))
    filename = 'Personen_Wohnungsflaeche.csv'
    src_path = os.path.dirname(os.path.dirname(os.path.dirname(this_path)))
    input_path = os.path.join(src_path, 'data', 'BuildingData', filename)
    with open(input_path) as csvfile:
        read = csv.reader(csvfile, delimiter=';')
        list_occ_prob = []
        for row in read:
            list_occ_prob.append(row)

    return list_occ_prob


def get_list_ap_prob_from_csv():
    """
    Load statistical apartment probabilites from .csv file
    (file holds number of buildings with year of construction (row) and
    number of apartments per bulding (column))

    Returns
    -------
    list_ap_prob: list
        apartment probabilities: row: buildyearclass (see Annotations);
        columns: number
        of apartments, Database according to Zensus 2011
        ROWS AND COLUMNS HAVE TO BE OF THE EXACT FORMAT AS IN FILE
        'data/BuildingData/Personen_Wohnungsflaeche_commented.csv'

    Annotation
    ----------
    build_year_class:  'int', year of build, 0: before 1950, 1:
        1950 to 1969, 2: 1970 to 1989, 3: after 1990
    """
    this_path = os.path.dirname(os.path.abspath(__file__))
    filename = 'Gebaeude_Wohnung_und_Baujahr.csv'
    src_path = os.path.dirname(os.path.dirname(os.path.dirname(this_path)))
    input_path = os.path.join(src_path, 'data', 'BuildingData', filename)

    with open(input_path) as csvfile:
        read = csv.reader(csvfile, delimiter=';')
        list_ap_prob = []
        for row in read:
            list_ap_prob.append(row)
    return list_ap_prob


if __name__ == '__main__':
    #  Input filename
    filename = 'test2.txt'

    #  Output filename
    file_out = 'test_enrich2.txt'

    #  Path definitions
    this_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(this_path, 'input', filename)
    out_path = os.path.join(this_path, 'output', file_out)

    #  Load city district data set
    district_data = citgen.get_district_data_from_txt(path=file_path)

    print('Total district data set:')
    print(district_data)
    print()

    print('Number of occupants per building before data enrichment:')
    print(district_data[:, [11]])
    print()

    # load occ csv. file to list
    list_occ_prob = get_list_occ_prob_from_csv()

    # load ap csv. file to list
    list_ap_prob = get_list_ap_prob_from_csv()

    #  Add occupants to district data

    #  Building types:
    #  #########################################
    # 'str', SFH: Single family house
    # DFH: Double family house
    # MFH: Multiple family house
    # STAT: Statistic distribution of houses
    # CUSTOM: customized probabilities, list of 10 items required, sum(list) = 1
    BuildingTypes = "CUSTOM"

    #  list of apartment number probabilities
    custom_p = [0.4, 0.2, 0.2, 0.2, 0, 0, 0, 0, 0, 0]

    district_data = determine_ap_num(district_data, BuildingTypes, custom_p,
                                     list_occ_prob, list_ap_prob)

    print('Number of occupants per building after data enrichment:')
    print(district_data[:, [11]])

    #  Save file to out_path
    save_dist_data_to_file(dist_data=district_data, path=out_path)
