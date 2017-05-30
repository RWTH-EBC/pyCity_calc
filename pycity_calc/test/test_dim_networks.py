#!/usr/bin/env python
# coding=utf-8
"""
Pytest script for network operation functions of toolbox
"""

import networkx as nx
import shapely.geometry.point as point
import shapely.geometry.linestring as lstr

import pycity_calc.toolbox.networks.intersection as intersec
import pycity_calc.toolbox.networks.network_ops as netop
import pycity_calc.cities.city as cit
import pycity_calc.toolbox.dimensioning.dim_networks as dimnet

from pycity_calc.test.pycity_calc_fixtures import fixture_building, \
    fixture_environment, fixture_city, fixture_apartment, fixture_th_demand, \
    fixture_el_demand

class Test_DimNetworks():

    def test_add_lhn_to_city_1(self, fixture_environment, fixture_building):

        #  Generate city object
        city_object = cit.City(environment=fixture_environment)

        node_1 = city_object.add_extended_building(
            extended_building=fixture_building,
            position=point.Point(0, 0))
        node_2 = city_object.add_extended_building(
            extended_building=fixture_building,
            position=point.Point(0, 10))
        node_3 = city_object.add_extended_building(
            extended_building=fixture_building,
            position=point.Point(10, 0))
        node_4 = city_object.add_extended_building(
            extended_building=fixture_building,
            position=point.Point(10, 10))

        list_con = [node_1, node_2, node_3]

        dimnet.add_lhn_to_city(city=city_object, list_build_node_nb=list_con,
                               use_street_network=False,
                               network_type='heating')

        assert len(city_object.nodes()) == 4

        assert city_object.edge[node_1][node_2]['network_type'] == 'heating'
        assert city_object.edge[node_1][node_3]['network_type'] == 'heating'

    def test_add_lhn_to_city_2(self, fixture_environment, fixture_building):

        #  Generate city object
        city_object = cit.City(environment=fixture_environment)

        node_1 = city_object.add_extended_building(
            extended_building=fixture_building,
            position=point.Point(0, 0))
        node_2 = city_object.add_extended_building(
            extended_building=fixture_building,
            position=point.Point(10, 20))
        node_3 = city_object.add_extended_building(
            extended_building=fixture_building,
            position=point.Point(15, 0))
        node_4 = city_object.add_extended_building(
            extended_building=fixture_building,
            position=point.Point(12, 0))

        node_str_1 = city_object.add_street_node(position=point.Point(-5, 10))
        node_str_2 = city_object.add_street_node(position=point.Point(20, 10))

        city_object.add_edge(node_str_1, node_str_2, network_type='street')

        list_con = [node_1, node_2, node_3]

        dimnet.add_lhn_to_city(city=city_object, list_build_node_nb=list_con,
                               use_street_network=True,
                               network_type='heating')

        assert len(city_object.nodes()) == 9

        list_build = \
            netop.get_list_with_energy_net_con_node_ids(city=city_object,
                                                        build_node_only=True)

        for sublist in list_build:
            sublist.sort()
        assert list_build == [[node_1, node_2, node_3]]

        list_lhn = \
            netop.get_list_with_energy_net_con_node_ids(city=city_object,
                                                        build_node_only=False)

        for sublist in list_lhn:
            sublist.sort()

        list_lhn_all = sorted(list_lhn)
        assert list_lhn_all == [[node_1, node_2, node_3, 1008, 1009, 1010]]

        assert len(city_object.nodes()) == 9

    def test_add_lhn_to_city_3(self, fixture_environment, fixture_building):

        #  Generate city object
        city_object = cit.City(environment=fixture_environment)

        node_1 = city_object.add_extended_building(
            extended_building=fixture_building,
            position=point.Point(0, 0))
        node_2 = city_object.add_extended_building(
            extended_building=fixture_building,
            position=point.Point(10, 20))
        node_3 = city_object.add_extended_building(
            extended_building=fixture_building,
            position=point.Point(15, 0))
        node_4 = city_object.add_extended_building(
            extended_building=fixture_building,
            position=point.Point(20, 20))

        node_str_1 = city_object.add_street_node(position=point.Point(-5, 10))
        node_str_2 = city_object.add_street_node(position=point.Point(30, 10))

        city_object.add_edge(node_str_1, node_str_2, network_type='street')

        list_con = [node_1, node_2]

        dimnet.add_lhn_to_city(city=city_object, list_build_node_nb=list_con,
                               use_street_network=True,
                               network_type='heating')

        list_con_2 = [node_3, node_4]

        dimnet.add_lhn_to_city(city=city_object, list_build_node_nb=list_con_2,
                               use_street_network=True,
                               network_type='heating')

        assert len(city_object.nodes()) == 10

        list_build = \
            netop.get_list_with_energy_net_con_node_ids(city=city_object,
                                                        build_node_only=True)

        list_build.sort()
        for sublist in list_build:
            sublist.sort()
        assert list_build == [[node_1, node_2], [node_3, node_4]]

        list_lhn = \
            netop.get_list_with_energy_net_con_node_ids(city=city_object,
                                                        build_node_only=False)

        list_lhn.sort()
        for sublist in list_lhn:
            sublist.sort()

        assert list_lhn == [[node_1, node_2, 1008, 1009],
                            [node_3, node_4, 1010, 1011]]

        assert len(city_object.nodes()) == 10