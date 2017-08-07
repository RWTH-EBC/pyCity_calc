#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Code extracts and saves load profiles of all buildings of city object
"""

import os
import pickle

import pycity_calc.visualization.city_visual as citvis
import pycity_calc.cities.scripts.city_generator.city_generator as citgen


def gen_path_if_not_existent(dir):
    """
    Generate directory, if not existent

    Parameters
    ----------
    dir : str
        Directory path
    """
    if not os.path.exists(dir):
        os.makedirs(dir)


def extract_build_base_data(city, id, file_path):
    """
    Extract and save building base data to txt file

    Parameters
    ----------
    city : object
        City object
    id : int
        Building node id
    file_path : str
        Path to save file to (e.g. ...\building_data.txt)
    """
    #  Building pointer
    build = city.node[id]['entity']

    with open(file_path, mode='w') as f:
        f.write('Building node id: ' + str(id) + '\n')

        x_coord = city.node[id]['position'].x
        y_coord = city.node[id]['position'].y
        f.write('X-coordinate in m: ' + str(int(x_coord)) + '\n')
        f.write('Y-coordinate in m: ' + str(int(y_coord)) + '\n')

        f.write(
            'Year of construction: ' + str(int(build.build_year)) + '\n')
        f.write('Last year of modernization: ' + str(
            int(build.mod_year)) + '\n')
        f.write('Building type number: ' + str(build.build_type) + '\n')

        build_name = citgen.conv_build_type_nb_to_name(build.build_type)

        f.write('Building type explanation: ' + str(build_name) + '\n')

        #  Write building data to file
        f.write('Nb. of zones/apartments: ' + str(
            len(build.apartments)) + '\n')

        f.write('Usable PV roof area in m2: ' +
                str(build.roof_usabl_pv_area) + '\n')
        f.write('Net floor area (NFA) in m2: ' +
                str(build.net_floor_area) + '\n')
        f.write('Ground area in m2: ' + str(build.ground_area) + '\n')
        f.write('Height of single floor in m: ' +
                str(build.height_of_floors) + '\n')
        f.write('Ground area in m2: ' + str(build.nb_of_floors) + '\n')

        ann_th_sh_demand = build.get_annual_space_heat_demand()
        ann_el_demand = build.get_annual_el_demand()
        ann_dhw_demand = build.get_annual_dhw_demand()

        f.write('Annual net space heating energy demand in kWh/a: '
                + str(int(ann_th_sh_demand)) + '\n')
        f.write('Annual electric energy demand in kWh/a: '
                + str(int(ann_el_demand)) + '\n')
        f.write('Annual net hot water energy demand in kWh/a: '
                + str(int(ann_dhw_demand)) + '\n')
        f.write('\n')

        if 'osm_id' in city.node[id]:
            f.write(
                'openstreetmap id: ' + str(city.node[id]['osm_id']) + '\n')
        if 'name' in city.node[id]:
            f.write('OSM name: ' + str(city.node[id]['name']) + '\n')
        if 'addr_street' in city.node[id]:
            f.write('Street: ' + str(city.node[id]['addr_street']) + '\n')
        if 'addr_housenumber' in city.node[id]:
            f.write('Street nb.: ' +
                    str(city.node[id]['addr_housenumber']) + '\n')
        if 'comment' in city.node[id]:
            f.write('OSM comment: ' +
                    str(city.node[id]['comment']) + '\n')

        # print(vars(build))

        f.close()


def save_city_load_profiles(city, out_path):
    #  Get all building nodes
    list_ids = city.get_list_build_entity_node_ids()

    for n in list_ids:
        #  Generate folder with node id name
        curr_path = os.path.join(out_path, str(n))

        gen_path_if_not_existent(curr_path)

        #  Open txt file and add
        data_f_name = str(n) + '_data.txt'
        data_f_path = os.path.join(curr_path, data_f_name)

        #  Extract building base data and save them to file
        extract_build_base_data(city=city, id=n, file_path=data_f_path)


if __name__ == '__main__':
    this_path = os.path.dirname(os.path.abspath(__file__))

    city_f_name = 'aachen_tuerme_mod_7_el_resc_2.pkl'

    input_path = os.path.join(this_path, 'input', city_f_name)

    out_name = city_f_name[:-4]

    out_path = os.path.join(this_path, 'output', 'extracted', out_name)

    #  Make out_path, if not existent
    gen_path_if_not_existent(out_path)

    city = pickle.load(open(input_path, mode='rb'))

    save_city_load_profiles(city=city, out_path=out_path)

    citvis.plot_city_district(city=city)
