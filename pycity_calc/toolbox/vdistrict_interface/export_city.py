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
    """

    Parameters
    ----------
    city

    Returns
    -------

    Annotations
    -----------
    CityGML parameter reference:
    http://en.wiki.quality.sig3d.org/index.php/Modeling_Guide_for_3D_Objects_-_Part_2:_Modeling_of_Buildings_(LoD1,_LoD2,_LoD3)#Building_.28bldg:Building.29
    """
    #  Get building entity list
    list_build_ids = city.get_list_build_entity_node_ids()

    #  Loop over buildings
    for n in list_build_ids:
        #  Building pointer
        build = city.node[n]['entity']

        #  Generate new vDistrict building
        vbuild = vd.modules.energy.buildingphysics.buildingenergy.BuildingEnergy()

        #  City id (foreign key)
        vbuild.id = None

        #  Building unique id
        vbuild.gml_id = n

        # #  Class
        # #  http://www.sig3d.org/codelists/Handbuch-SIG3D/building/2.0/CL-V1.0/_AbstractBuilding_class.xml
        # vbuild.class_field = 1000  # Wohngebaeude

        #  Year of construction
        if build.mod_year is not None:
            assert build.mod_year >= 1800
            vbuild.year_of_construction = build.mod_year
        else:
            vbuild.year_of_construction = build.build_year

        #  Measured_heigh
        if build.height_of_floors is not None and build.nb_of_floors is not None:
            vbuild.measured_height = build.height_of_floors * build.nb_of_floors

        if build.nb_of_floors is not None:
            vbuild.storeys_above_ground = build.nb_of_floors

        if build.height_of_floors is not None:
            vbuild.storey_heights_above_ground = build.height_of_floors

        if build.net_floor_area is not None:
            vbuild.floor_area = build.net_floor_area

        vbuild.save()

if __name__ == '__main__':
    this_path = os.path.dirname(os.path.abspath(__file__))

    city_f_name = 'city_3_buildings.pkl'

    city_path = os.path.join(this_path, 'input', city_f_name)

    city = pickle.load(open(city_path, mode='rb'))
