#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example file how to extract osm data into city object

Here you can find an example instruction how to download an osm file:
- Download file, e.g. through
http://www.overpass-api.de/api/xapi_meta?*[bbox=7.1450,50.6813,7.1614,50.6906]
- Save in your input_osm as .../pycity_calc/cities/scripts/input_osm/name.osm

Coordinates are directly changed within uesgraphs form lat/long to pseudo
mercator coordinates in m
"""
from __future__ import division
import os
import pycity_calc.cities.scripts.osm_call as osm_call
import pycity_calc.cities.scripts.city_generator.city_generator as citgen
import pycity_calc.visualization.city_visual as citvis


def run_osm_example(plot_res=False):

    this_path = os.path.dirname(os.path.abspath(__file__))

    #  Beginn of user input

    filename = 'test.osm'

    file_path = os.path.join(this_path, 'inputs', filename)

    min_allowed_ground_area = 70  # m2

    #  Save generated city objecct as pickle file?
    save_city = True
    city_filename = 'test_osm.pkl'

    #  Add building entities?
    add_entities = True
    #  True: Add building object instances to building nodes
    #  False: Only use building nodes, do not generate building objects
    add_ap = True
    #  Add single apartment to every building (True/False)

    #  Parameters for environment
    timestep = 3600  # in seconds
    year = 2010
    location = (50.781743, 6.083470)  # Aachen
    #  location = (51.529086, 6.944689)  # Bottrop
    altitude = 55
    try_path = None
    show_stats = True

    #   End of user input  ###################################################

    #  Generate environment
    environment = citgen.generate_environment(timestep=timestep, year=year,
                                              try_path=try_path,
                                              location=location,
                                              altitude=altitude)

    #  Generate city topology based on osm data
    city = osm_call.gen_osm_city_topology(osm_path=file_path,
                                          environment=environment,
                                          min_area=min_allowed_ground_area,
                                          show_graph_stats=show_stats)

    #  If building entities should be added
    if add_entities:
        osm_call.add_build_entities(city=city, add_ap=add_ap)

    if plot_res:
        #  Plot city district
        citvis.plot_city_district(city=city, node_size=10,
                                  plot_build_labels=False)


if __name__ == '__main__':
    run_osm_example(plot_res=True)