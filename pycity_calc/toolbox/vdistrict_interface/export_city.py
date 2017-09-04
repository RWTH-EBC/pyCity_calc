#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script exports buildings of city object into vDistrict

"""
from __future__ import division

import os
import pickle

try:
    import vdistrict as vd
except:
    msg = 'Could not import vDistrict, which can be found at: ' \
          'https://git.rwth-aachen.de/EBC/Team_UES/living-roadmap/vDistrict '
    raise ImportError(msg)

def export_city_to_vdistrict(city):

    #  Get building entity list
    list_build_ids = city.get_list_build_entity_node_ids()

    #  Loop over buildings
    for n in list_build_ids:
        #  Building pointer
        build = city.node[n]['entity']

        #  Generate new vDistrict building
        vbuild = vdistrict.modules.bldg.building



if __name__ == '__main__':

    this_path = os.path.dirname(os.path.abspath(__file__))

    city_f_name = 'city_3_buildings.pkl'

    city_path = os.path.join(this_path, 'input', city_f_name)

    city = pickle.load(open(city_path, mode='rb'))

