#!/usr/bin/env python
# coding=utf-8
"""
Pytest script for clustering
"""
from __future__ import division
import shapely.geometry.point as point

import pycity_calc.toolbox.clustering.clustering as clust
import pycity_calc.cities.city as cit

import pycity_calc.toolbox.networks.network_ops as netop

from pycity_calc.test.pycity_calc_fixtures import fixture_building, \
    fixture_environment, fixture_city, fixture_apartment, fixture_th_demand, \
    fixture_el_demand


class TestClustering(object):

    def test_init_cluster(self):

        max_nb_build = 7
        max_b_str = 12
        max_b_b = 50

        cluster = clust.StreetCluster(max_nb_build=max_nb_build, max_b_str=max_b_str,
                      max_b_b=max_b_b)

    def test_erase_str_nodes_without_connection(self, fixture_environment):

        max_nb_build = 7
        max_b_str = 12
        max_b_b = 50

        cluster = clust.StreetCluster(max_nb_build=max_nb_build, max_b_str=max_b_str,
                      max_b_b=max_b_b)

        #  Init street graph
        city = cit.City(environment=fixture_environment)

        #  Add str nodes
        node_1 = city.add_street_node(position=point.Point(0, 0))
        node_2 = city.add_street_node(position=point.Point(0, 5))
        node_3 = city.add_street_node(position=point.Point(0, 10))
        node_4 = city.add_street_node(position=point.Point(0, 15))

        #  Add edge
        city.add_edge(node_1, node_2, networktype='street')

        assert sorted(list(city.nodes())) == [node_1, node_2, node_3, node_4]

        #  Remove unnecessary nodes
        cluster.city = city
        cluster.erase_str_nodes_without_connection()

        assert cluster.city.nodes() == [node_1, node_2]

    def test_get_street_subgraph(self, fixture_environment, fixture_building):

        max_nb_build = 7
        max_b_str = 12
        max_b_b = 50

        cluster = clust.StreetCluster(max_nb_build=max_nb_build, max_b_str=max_b_str,
                      max_b_b=max_b_b)

        #  Init street graph
        city = cit.City(environment=fixture_environment)

        #  Add str nodes
        node_1 = city.add_street_node(position=point.Point(0, 0))
        node_2 = city.add_street_node(position=point.Point(0, 5))
        node_3 = city.add_street_node(position=point.Point(0, 10))

        #  Add edges
        city.add_edge(node_1, node_2, networktype='street')
        city.add_edge(node_2, node_3, networktype='street')

        #  Add building entities
        city.addEntity(entity=fixture_building, position=point.Point(-1, -1))
        city.addEntity(entity=fixture_building, position=point.Point(1, -1))

        #  Extract street graph
        cluster.city = city
        street = netop.get_street_subgraph(city)

        assert sorted(list(street.nodes())) == [node_1, node_2, node_3]

    # def test_gen_str_dicts(self, fixture_environment, fixture_building):
    #
    #     max_nb_build = 7
    #     max_b_str = 12
    #     max_b_b = 50
    #
    #     cluster = clust.StreetCluster(max_nb_build=max_nb_build, max_b_str=max_b_str,
    #                   max_b_b=max_b_b)
    #
    #     #  Init street graph
    #     city = cit.City(environment=fixture_environment)
    #
    #     #  Add str nodes
    #     node_1 = city.add_street_node(position=Point(0, 0))
    #     node_2 = city.add_street_node(position=Point(0, 5))
    #     node_3 = city.add_street_node(position=Point(0, 10))
    #
    #      #  Add edges
    #     city.add_edge(node_1, node_2, networktype='street')
    #     city.add_edge(node_2, node_3, networktype='street')
    #
    #      #  Add building entities
    #     city.addEntity(entity=fixture_building, position=Point(-1, 0))
    #     city.addEntity(entity=fixture_building, position=Point(1, 1))
    #     city.addEntity(entity=fixture_building, position=Point(1, 2))
    #
    #     cluster.city = city
    #
    #     str_node_dict, str_edge_dict = cluster.gen_str_dicts()
    #
    #     assert str_node_dict == {}
    #     assert str_edge_dict == {}
