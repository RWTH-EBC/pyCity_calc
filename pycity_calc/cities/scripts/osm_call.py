#!/usr/bin/env python
# coding=utf-8
"""
Script to generate city object with building and street topology based on
openstreetmap (osm) file input

- Download file through http://www.overpass-api.de/api/xapi_meta?*[bbox=7.1450,50.6813,7.1614,50.6906]
--> change to the new coordinates
- Save in your input_osm as .../pycity_calc/cities/scripts/input_osm/name.osm

"""

import os
import pickle
import utm
import shapely.geometry.point as point

import uesgraphs.examples.example_osm as example_osm

import pycity.classes.demand.Apartment as apart

import pycity_calc.cities.scripts.city_generator.city_generator as citgen
import pycity_calc.cities.city as cit
import pycity_calc.visualization.city_visual as citvis
import pycity_calc.buildings.building as exbuild


def gen_osm_city_topology(osm_path, environment, name=None,
                          check_boundary=False,
                          show_graph_stats=False, min_area=None):
    """
    Initialize city object and generate building and street nodes (without
    building objects) based on openstreetmaps osm file.

    Important: Only generates topology and returns city object.
    Furthermore, point x, y positions are latitude and longitute!
    If you require meter positions in UTM coordinates, you have to convert
    the points!

    Parameters
    ----------
    osm_path : str
        Path to osm file
    environment : object
        Environment object of pycity_calc
    name : str, optional
        Name of city or district, which should be searched for in osm data file
        (default: None). If name is defined, script tries to extract all
        osm entities, which are within area 'name'
    check_boundary : bool, optional
        Defines, if only objects within boundaries of area 'name' should be
        extracted (default: False)
    show_graph_stats : bool, optional
        Define, if statistics of osm extracted data should be shown
        (default: False)
    min_area : float, optional
        Minimal required ground area of building (default: None).
        If set to None, not changes happen.
        If set to specific float value, all buildings with an area smaller
        than min_area are erased from city district

    Returns
    -------
    city : object
        City object of pycity_calc with building and network topology
    """

    #  Init city object
    city = cit.City(environment)

    #  Generate topology from osm data file
    city = city.from_osm(osm_path, name=name,
                         check_boundary=check_boundary, add_str_info=True)

    if min_area is not None:
        example_osm.remove_small_buildings(city, min_area=min_area)

    if show_graph_stats:
        example_osm.graph_stats(city)

    return city


def conv_city_long_lat_to_utm(city, zone_number=None):
    """
    Converts all point object coordinates within city from latitude,
    longitute to utm coordinates in meters

    Parameters
    ----------
    city : object
        City object with latitude, longitude coordinates
    zone_number : int, optional
        Zone number of utm as integer (default: None)
        If set to none, utm modul chooses zone automatically.

    Returns
    -------
    city_new : object
        City object in UTM
    """

    #  Loop over every node in city
    for n in city.nodes():
        #  Current node
        cur_pos = city.node[n]['position']

        #  Current x/y coordinates
        x_cor = cur_pos.x  # Longitude
        y_cor = cur_pos.y  # Latitude

        #  Convert lat, long to utm
        (x_new, y_new, zone_nb, zone_str) = utm.from_latlon(y_cor, x_cor,
                                                            zone_number)

        #  New shapely point
        cur_point = point.Point((x_new, y_new))

        #  Overwrite positional attributes
        city.node[n]['position'] = cur_point

    city.graph['zone_nb'] = zone_nb
    city.graph['zone_str'] = zone_str

    return city


def get_list_b_nodes_without_area(city):
    """
    Returns list of building node ids without area parameter.
    Requires osm call to generate city obejct, first!

    Parameters
    ----------
    city : object
        City object generated with osm call

    Returns
    -------
    list_missing_area : list (of ints)
        List with building node ids without area parameter
    """

    list_missing_area = []

    for n in city.nodes():
        if 'node_type' in city.node[n]:
            if city.node[n]['node_type'] == 'building':
                if 'area' not in city.node[n]:
                    list_missing_area.append(n)

    return list_missing_area


def add_build_entities(city, add_ap=False):
    """
    Add building entities with single apartment (without loads) to city object
    instance.

    Parameters
    ----------
    city : object
        City object instance of PyCity_Calc
    add_ap : bool, optional
        Adds (single) apartment to building entity (default: False)
    """

    for n in city.nodes():
        if 'node_type' in city.node[n]:
            if city.node[n]['node_type'] == 'building':

                #  Add building object instance
                build = exbuild.BuildingExtended(environment=city.environment)

                #  Add ground floor area
                build.ground_area = city.node[n]['area']

                if add_ap:
                    ap = apart.Apartment(environment=city.environment)

                    build.addEntity(ap)

                city.node[n]['entity'] = build

if __name__ == '__main__':

    #  osm filename
    filename = 'test.osm'

    #  Minimal required building area in m2
    min_area = 35

    #  Save generated city objecct as pickle file?
    save_city = True
    city_filename = 'test_osm.pkl'

    #  Convert lat/long to utm coordinates in meters?
    #  Only necessary, if no conversion is done within uesgraphs itself
    conv_utm = False
    zone_number = 32

    check_boundary = False
    name = None

    #  Add building entities?
    add_entities = True
    #  True: Add building object instances to building nodes
    #  False: Only use building nodes, do not generate building objects
    add_ap = True
    #  Add single apartment to every building (True/False)

    #  Parameters for environment
    timestep = 3600  # in seconds
    year = 2010
    location = (50.781743,6.083470)  #  Aachen
    #  location = (51.529086, 6.944689)  # Bottrop
    altitude = 55
    try_path = None

    #   End of user input  ###################################################

    this_path = os.path.dirname(os.path.abspath(__file__))
    osm_path = os.path.join(this_path, 'input_osm', filename)
    # osm_path = os.path.join(this_path, 'input_osm', 'Diss_Quartiere', filename)
    osm_out_path = os.path.join(this_path, 'output_osm', city_filename)
    # osm_out_path = os.path.join(this_path, 'input_osm',
    #                             'Diss_Quartiere', city_filename)

    #  Generate environment
    environment = citgen.generate_environment(timestep=timestep, year=year,
                                              try_path=try_path,
                                              location=location,
                                              altitude=altitude)

    #  Generate city topology based on osm data
    city = gen_osm_city_topology(osm_path=osm_path, environment=environment,
                                 name=name,
                                 check_boundary=check_boundary,
                                 min_area=min_area,
                                 show_graph_stats=True)

    if conv_utm:
        #  Convert latitude, longitude to utm
        city = conv_city_long_lat_to_utm(city, zone_number=zone_number)

    #  If building entities should be added
    if add_entities:
        add_build_entities(city=city, add_ap=add_ap)

    print()
    print('Nodelist_building:')
    print(city.nodelist_building)
    print()

    #  Plot city district
    citvis.plot_city_district(city=city, node_size=10, plot_build_labels=False)

    if 1001 in city.nodes():
        print('Area of building 1001: ', city.node[1001]['area'])
        print('OSM id of building 1001: ', city.node[1001]['osm_id'])
        print('x-coordinate of building 1001: ', city.node[1001]['position'].x)
        print('y-coordinate of building 1001: ', city.node[1001]['position'].y)

        if 'addr:street' in city.node[1001]:
            print('Street name at node 1001: ', city.node[1001]['addr:street'])
        if 'addr:street' in city.node[1001]:
            print('House number of node 1001: ',
                  city.node[1001]['addr:housenumber'])
        print()

    list_miss_area = get_list_b_nodes_without_area(city)
    print('List of building ids without area parameter: ', list_miss_area)

    #  Dump as pickle file
    if save_city:
        pickle.dump(city, open(osm_out_path, mode='wb'))
        print()
        print('Saved city object as pickle file to ', osm_out_path)
