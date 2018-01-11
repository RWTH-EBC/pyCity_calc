#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to increase energy system base load size of city
"""
from __future__ import division

import os
import pickle
import warnings

import pycity_calc.cities.scripts.energy_sys_generator as esysgen


def incr_esys_size_build(building, base_factor=3, w_tes=True, tes_factor=2,
                         id=None):
    """
    Increase size of energy systems of building.

    Parameters
    ----------
    building : object
        Building object of pyCity_calc
    base_factor : float, optional
        Rescaling factor for base load devices, such as boiler or electric
        heater (default: 3). E.g. 3 means that current nominal thermal power
        is increased by factor 3
    w_tes : bool, optional
        Defines, if TES should be rescaled (default: True)
    tes_factor : float, optional
        Rescaling factor for thermal storages (default: 2). E.g. 2 means that
        current tes volume is increased by factor 2
    id : int, optional
        Building id (default: None)
    """

    assert base_factor >= 0
    if w_tes:
        assert tes_factor >= 0

    if building.hasBes:

        #  bes pointer
        bes = building.bes

        if bes.hasBoiler:
            bes.boiler.qNominal *= base_factor

        if bes.hasElectricalHeater:
            bes.electricalHeater.qNominal *= base_factor

        if w_tes:
            if bes.hasTes:
                bes.tes.capacity *= tes_factor

    else:
        if id is not None:
            msg = 'Building with id %d does not have energy system!' % (id)
        else:
            msg = 'Building has no energy system!'
        warnings.warn(msg)


def incr_esys_size_city(city, base_factor=3, w_tes=True, tes_factor=2):
    """
    Increase size of energy systems within city.

    Parameters
    ----------
    city : object
        City object of pyCity_calc
    base_factor : float, optional
        Rescaling factor for base load devices, such as boiler or electric
        heater (default: 3). E.g. 3 means that current nominal thermal power
        is increased by factor 3
    w_tes : bool, optional
        Defines, if TES should be rescaled (default: True)
    tes_factor : float, optional
        Rescaling factor for thermal storages (default: 2). E.g. 2 means that
        current tes volume is increased by factor 2
    """

    list_build_ids = city.get_list_build_entity_node_ids()

    for n in list_build_ids:
        build = city.nodes[n]['entity']

        incr_esys_size_build(building=build, base_factor=base_factor,
                             w_tes=w_tes, tes_factor=tes_factor, id=n)


if __name__ == '__main__':
    this_path = os.path.dirname(os.path.abspath(__file__))

    city_name = 'city_3_buildings.pkl'
    city_path = os.path.join(this_path, 'input', city_name)

    #  Path to energy system input file (csv/txt; tab separated)
    esys_filename = 'city_3_buildings_enersys.txt'
    esys_path = os.path.join(this_path, 'input',
                             esys_filename)

    city = pickle.load(open(city_path, mode='rb'))

    #  Load energy networks planing data
    list_data = esysgen.load_enersys_input_data(esys_path)

    esysgen.gen_esys_for_city(city=city, list_data=list_data, dhw_scale=True)

    q_nom = city.nodes[1001]['entity'].bes.boiler.qNominal
    print('Nominal thermal power of boiler before rescaling in kW:')
    print(round(q_nom / 1000, 3))

    incr_esys_size_city(city=city)

    q_nom = city.nodes[1001]['entity'].bes.boiler.qNominal
    print('Nominal thermal power of boiler after rescaling in kW:')
    print(round(q_nom / 1000, 3))
