#!/usr/bin/env python
# coding=utf-8
"""
Script to enrich input txt data file, for instance with number of occupants
per apartment

#  TODO
- Enrich given apartment nb with nb of occupants
- Enrich given buildings with nb. of apartments and nb. occupants
- Estimate last year of retrofit based on statistics
- Estimate last year of retrofit, when thermal consumption values is given
and VDI6007/TEASER model is used within a loop, until closest mod. year is
found

"""
from __future__ import division

import os
import random
import warnings
import numpy as np

import pycity_calc.cities.scripts.city_generator.city_generator as citgen


def est_nb_apartments(net_floor_area):
    """
    Estimates number of apartments based on net floor area, according to
    statistics of TABULA:
    [Institut für Wohnen und Umwelt - IWU 2009] INSTITUT FÜR WOHNEN UND
    UMWELT - IWU: TABULA Average Buildings: German residential building
    stock. http://s2.building-typology.eu/abpdf/DE_N_01_EPISCOPE_
    CaseStudy_TABULA_National.pdf. Version: 2009
    with around 74 m2 per apartment

    Parameters
    ----------
    net_floor_area : float
        Net floor area of building in m2

    Returns
    -------
    nb_app : int
        Number of apartments
    """

    assert net_floor_area > 0, 'Net floor area has to be larger than zero!'

    nb_app = int(round(net_floor_area/74, 0))

    #  Cover case, if nb_app is calculated to be zero
    if nb_app == 0:
        nb_app = 1

    return nb_app


def add_occ_to_given_app(district_data):
    """
    Add occupants to district data, where number of apartments is given

    Parameters
    ----------
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

    #  Loop over district_data
    for i in range(len(district_data)):
        curr_nb_of_apartments = district_data[i][10]
        curr_nb_of_occupants = district_data[i][11]

        #  Check if apartment number is set
        if curr_nb_of_apartments is None:
            msg = str('Nb. of apartments of building ' + str(i) + ' is None!'
                      ' Thus, could not add occupants!')
            warnings.warn(msg)

        else:  # Number of apartments is set
            curr_nb_of_apartments > 0, 'Number of apartments has to be > 0!'

            #  Number of occupants is already defined
            if curr_nb_of_occupants is not None:
                print('\nNb. of occupants for building ' + str(i) + ' is '
                      'already defined to ' + str(curr_nb_of_occupants))
                print('Thus, going to skip this building.\n')

            else:  # Number of occupants is None

                nb_occ = 0

                #  Loop over apartments
                for j in range(int(curr_nb_of_apartments)):
                    #  Execute adding of occupants (per apartment)
                    nb_occ += estimate_occ_per_ap()

                #  Add total number of occupants to building
                district_data[i][11] = int(nb_occ)


def estimate_occ_per_ap(prob_dist=[0.405, 0.345, 0.125, 0.092, 0.033]):
    """
    Randomly generates a number of occupants between 1 and 5

    Parameters
    ----------
    prob_dist : list (of floats), optional
        Defines probability distribution of occupants per apartment
        Default: [0.405, 0.345, 0.125, 0.092, 0.033]
        Based on data of Statistisches Bundesamt (2012)
        https://www.destatis.de/DE/ZahlenFakten/Indikatoren/LangeReihen/Bevoelkerung/lrbev05.html;jsessionid=4AACC10D2225591EC88C40EDEFB5EDAC.cae2

    Returns
    -------
    nb_occ : int
        Number of occupants within one apartment
    """

    #  Generate random float between 0 and 1 (0 and 1 included!)
    rand_val = random.randint(0, 100000) / 100000

    if rand_val < prob_dist[0]:
        nb_occ = 1
    elif rand_val < prob_dist[0] + prob_dist[1]:
        nb_occ = 2
    elif rand_val < prob_dist[0] + prob_dist[1] + prob_dist[2]:
        nb_occ = 3
    elif rand_val < prob_dist[0] + prob_dist[1] + prob_dist[2] + prob_dist[3]:
        nb_occ = 4
    else:
        nb_occ = 5

    return int(nb_occ)

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
            if dist_data[i][j] == None:
                dist_data[i][j] = np.nan

    #  Save to path
    np.savetxt(path, dist_data, delimiter='\t', header=header)

    print('Saved district data to path ' + str(path))


if __name__ == '__main__':

    filename = 'test.txt'
    file_out = 'test_enrich.txt'

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

    #  Add occupants to district data
    add_occ_to_given_app(district_data)

    print('Number of occupants per building after data enrichment:')
    print(district_data[:, [11]])

    #  Save file to out_path
    save_dist_data_to_file(dist_data=district_data, path=out_path)