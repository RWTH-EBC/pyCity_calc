#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
from __future__ import division

import os
import copy
import pickle

import pycity_base.classes.supply.BES as BES

def add_bes_to_all_build(city, makecopy=True):
    """
    Adds (empty) BES object to every building, which does not already hold
    bes object.

    Parameters
    ----------
    city : object
        City object instance of pyCity_calc
    makecopy : bool, optional
        Defines, if city should be copied or original city should be modified

    Returns
    -------
    city : object
        Modified city object instance (depending on makecopy; original or
        copied city)
    """

    if makecopy:
        #  Generate copy of city
        city = copy.deepcopy(city)

    #  Get list with building nodes with building entities
    list_build = city.get_list_build_entity_node_ids()

    for n in list_build:
        building = city.node[n]['entity']

        if building.hasBes is False:
            #  Generate empty bes object instance
            bes = BES.BES(environment=city.environment)

            building.addEntity(bes)

    return city

if __name__ == '__main__':

    this_path = os.path.dirname(os.path.abspath(__file__))

    city_f_name = 'city_3_buildings_mixed.pkl'

    file_path = os.path.join(this_path, 'input', city_f_name)

    city = pickle.load(open(file_path, mode='rb'))

    #  Add bes
    city_bes = add_bes_to_all_build(city)

    #  Get list with building nodes with building entities
    list_build = city_bes.get_list_build_entity_node_ids()

    for n in list_build:
        assert city_bes.node[n]['entity'].hasBes is True

    print('Added bes to all buildings without bes')
