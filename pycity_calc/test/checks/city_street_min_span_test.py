# coding=utf-8
"""
Script to check gen_min_span_tree_along_street function
"""

import matplotlib.pyplot as plt
import networkx as nx
import shapely.geometry.point as point

import pycity_base.classes.Weather as Weather

import pycity_calc.buildings.building as build_ex
import pycity_calc.cities.city as cit
import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.environment as env
import pycity_calc.environments.market as mark
import pycity_calc.environments.timer as time
import pycity_calc.toolbox.networks.network_ops as netop

import pycity_calc.visualization.city_visual as citvis


def run_example():
    """
    Run example to create city object of pycity with 3 buildings and
    street network
    """

    #  Create extended environment of pycity_calc
    year = 2010
    timestep = 3600  # Timestep in seconds
    location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop
    altitude = 55  # Altitude of Bottrop

    #  Generate timer object
    timer = time.TimerExtended(timestep=timestep, year=year)

    #  Generate weather object
    weather = Weather.Weather(timer, useTRY=True, location=location,
                              altitude=altitude)

    #  Generate market object
    market = mark.Market()

    #  Generate co2 emissions object
    co2em = co2.Emissions(year=year)

    #  Generate environment
    environment = env.EnvironmentExtended(timer, weather, prices=market,
                                          location=location, co2em=co2em)

    #  Generate city object
    city_object = cit.City(environment=environment)

    #  Create extended building object
    extended_building = build_ex.BuildingExtended(environment,
                                                  build_year=1962,
                                                  mod_year=2003,
                                                  build_type=0)

    #  Add 3 extended buildings to city object
    #  Add building entities
    node_1 = city_object.add_extended_building(
        extended_building=extended_building,
        position=point.Point(0, 0))
    node_2 = city_object.add_extended_building(
        extended_building=extended_building,
        position=point.Point(2, 2))
    node_3 = city_object.add_extended_building(
        extended_building=extended_building,
        position=point.Point(0.5, 4))

    node_4 = city_object.add_extended_building(
        extended_building=extended_building,
        position=point.Point(8, 10))

    list_to_be_conn = [node_1, node_2, node_3]

    #  Add additional, arbitrary buildings
    node_str_1 = city_object.add_street_node(position=point.Point(-1, 1))
    node_str_2 = city_object.add_street_node(position=point.Point(10, 1))

    #  Add street edge
    city_object.add_edge(node_str_1, node_str_2, network_type='street')

    pos_dict = citvis.get_pos_for_plotting(city=city_object)

    nx.draw_networkx_nodes(G=city_object, pos=pos_dict,
                           node_color='k', node_shape='s', alpha=0.5)
    nx.draw_networkx_edges(G=city_object, pos=pos_dict)
    plt.title('4 Buildings with 1 street')
    plt.show()
    plt.close()

    (min_span_graph, list_new_nodes) = \
        netop.gen_min_span_tree_along_street(city=city_object,
                                             nodelist=list_to_be_conn)

    pos_dict = citvis.get_pos_for_plotting(city=min_span_graph)

    nx.draw_networkx_nodes(G=min_span_graph, pos=pos_dict,
                           node_color='k', node_shape='s', alpha=0.5)
    nx.draw_networkx_edges(G=min_span_graph, pos=pos_dict)
    plt.title('Minimum spanning (3 buildings) tree along street')
    plt.show()

    print('New nodes: ', list_new_nodes)

if __name__ == '__main__':
    #  Execute example
    run_example()
