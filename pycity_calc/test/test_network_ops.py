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

from pycity_calc.test.pycity_calc_fixtures import fixture_building, \
    fixture_environment, fixture_city, fixture_apartment, fixture_th_demand, \
    fixture_el_demand


class Test_NetworkOperations(object):
    """
    Pytest class for network operations and segment script of toolbox of
    pycity_calc package.
    """

    def test_calc_distance(self):
        graph = nx.Graph()
        graph.add_node(0, position=point.Point(0, 0))
        graph.add_node(1, position=point.Point(0, 5))
        graph.add_node(2, position=point.Point(5, 5))
        graph.add_edges_from([(0, 1), (1, 2), (0, 2)])

        #  Should return 5 als distance between node 0 and 1
        assert (netop.calc_node_distance(graph, 0, 1) - 5) <= 0.0001

    def test_get_min_span_tree(self):
        graph = nx.Graph()
        graph.add_node(0, position=point.Point(0, 0))
        graph.add_node(1, position=point.Point(0, 5))
        graph.add_node(2, position=point.Point(5, 5))
        graph.add_edges_from([(0, 1), (1, 2), (0, 2)])

        assert ((netop.get_min_span_tree(graph,
                                         [0, 1, 2])).edges() == [(0, 1),
                                                                 (1, 2)])
        #  Check for assertionError when node id is not within graph
        try:
            netop.get_min_span_tree(graph, [3])
        except:
            assert True
        # Check for assertionError when graph is empty
        try:
            testgraph = nx.Graph()
            netop.get_min_span_tree(testgraph, [0])
        except:
            assert True

    def test_check_if_node_exist_on_position(self):
        graph = nx.Graph()
        graph.add_node(0, position=point.Point(0, 0))
        graph.add_node(1, position=point.Point(0, 5))
        graph.add_node(2, position=point.Point(5, 5))
        graph.add_edges_from([(0, 1), (1, 2), (0, 2)])

        assert netop.check_node_on_pos(graph, point.Point(0, 0)) == True
        assert netop.check_node_on_pos(graph, point.Point(1, 0)) == False

    def test_add_weights_to_edges(self):
        graph = nx.Graph()
        graph.add_node(0, position=point.Point(0, 0))
        graph.add_node(1, position=point.Point(0, 5))
        graph.add_edge(0, 1)

        netop.add_weights_to_edges(graph)
        assert graph.edges(data=True) == [(0, 1, {'weight': 5.0})]

    def test_calc_graph_pos_closest_to(self):
        graph = nx.Graph()
        graph.add_node(0, position=point.Point(0, 0), node_type='street')
        graph.add_node(1, position=point.Point(0, 5), node_type='street')
        graph.add_node(2, position=point.Point(5, 5), node_type='street')
        graph.add_edges_from([(0, 1), (1, 2), (0, 2)], network_type='street')

        target_node_pos = point.Point(0, 0)

        assert (netop.calc_graph_pos_closest_to(graph, target_node_pos)) == \
               (point.Point(0, 0), point.Point(0, 0), point.Point(0, 5))

        target_node_pos = point.Point(-2, -2)

        assert (netop.calc_graph_pos_closest_to(graph, target_node_pos)) == \
               (point.Point(0, 0), point.Point(0, 0), point.Point(0, 5))

        target_node_pos = point.Point(-2.5, 2.5)

        assert (netop.calc_graph_pos_closest_to(graph, target_node_pos)) == \
               (point.Point(0, 2.5), point.Point(0, 0), point.Point(0, 5))

    def test_calc_closest_node(self):
        graph = nx.Graph()
        graph.add_node(0, position=point.Point(0, 0))
        graph.add_node(1, position=point.Point(0, 5))
        graph.add_node(2, position=point.Point(5, 5))
        graph.add_node(3, position=point.Point(6, 5))

        close_node_id = netop.find_closest_node(graph, target_node=0,
                                                node_list=None)
        assert close_node_id == 1

        close_node_id = netop.find_closest_node(graph, target_node=0,
                                                node_list=[1, 3])
        assert close_node_id == 1

        close_node_id = netop.find_closest_node(graph, target_node=3,
                                                node_list=None)
        assert close_node_id == 2

    def test_sort_node_list_by_distance(self):
        graph = nx.Graph()
        graph.add_node(0, position=point.Point(0, 0))
        graph.add_node(1, position=point.Point(0, 4))
        graph.add_node(3, position=point.Point(0, 3))
        graph.add_node(2, position=point.Point(0, 2))
        graph.add_node(4, position=point.Point(0, 1))

        target_node = 0
        node_list = [1, 2, 3, 4]
        sort_list = netop.sort_node_list_by_distance(graph, target_node,
                                                     node_list)
        assert sort_list == (4, 2, 3, 1)

    def test_get_street_subgraph(self, fixture_building):

        #  Init street graph
        city = cit.City(environment=fixture_environment)

        #  Add str nodes
        node_1 = city.add_street_node(position=point.Point(0, 0))
        node_2 = city.add_street_node(position=point.Point(0, 5))
        node_3 = city.add_street_node(position=point.Point(0, 10))

        #  Add edges
        city.add_edge(node_1, node_2, network_type='street')
        city.add_edge(node_2, node_3, network_type='street')

        #  Add building entities
        city.addEntity(entity=fixture_building, position=point.Point(-1, -1))
        city.addEntity(entity=fixture_building, position=point.Point(1, -1))

        street = netop.get_street_subgraph(city)

        assert street.nodes() == [node_1, node_2, node_3]
        assert street.edges() == [(node_1, node_2), (node_2, node_3)]

    def test_get_build_str_subgraph(self, fixture_building):

        #  Init street graph
        city = cit.City(environment=fixture_environment)

        #  Add str nodes
        node_1 = city.add_street_node(position=point.Point(0, 0))
        node_2 = city.add_street_node(position=point.Point(0, 5))
        node_3 = city.add_street_node(position=point.Point(0, 10))

        #  Add edges
        city.add_edge(node_1, node_2, network_type='street')
        city.add_edge(node_2, node_3, network_type='street')

        #  Add building entities
        node_4 = city.addEntity(entity=fixture_building,
                                position=point.Point(-1, -1))
        node_5 = city.addEntity(entity=fixture_building,
                                position=point.Point(1, -1))

        subcity = netop.get_build_str_subgraph(city, nodelist=[node_4])

        assert sorted(subcity.nodes()) == [node_1, node_2, node_3, node_4]
        assert subcity.edges() == [(node_1, node_2), (node_2, node_3)]

    def test_get_list_with_energy_net_con_node_ids_1(self, fixture_building):

        #  Init city
        city = cit.City(environment=fixture_environment)

        #  Add building entities
        node_1 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(0, 0))
        node_2 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(5, 0))
        node_3 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(5, 5))
        node_4 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(5, 10))
        node_5 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(10, 0))
        node_6 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(10, 5))
        node_7 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(15, 10))

        #  Add heating network node
        node_heat = city.add_network_node(network_type='heating',
                                          position=point.Point(10, 10))

        #  Add heating networks (only)
        city.add_edges_from([(node_1, node_2), (node_2, node_5),
                             (node_3, node_4), (node_6, node_heat),
                             (node_heat, node_7)], network_type='heating')
        #  Add heating and deg network
        city.add_edge(node_2, node_3, network_type='heating_and_deg')

        #  Test function call
        list_lhn_conn = \
            netop.get_list_with_energy_net_con_node_ids(city=city,
                                                        network_type='heating')

        #  Sort lists in list_lhn_conn
        list_lhn_conn.sort()
        for l in list_lhn_conn:
            l.sort()

        assert list_lhn_conn == [[node_1, node_2, node_3, node_4, node_5],
                                 [node_6, node_7, node_heat]]

    def test_get_list_with_energy_net_con_node_ids_2(self, fixture_building):

        #  Init city
        city = cit.City(environment=fixture_environment)

        #  Add building entities
        node_1 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(0, 0))
        node_2 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(5, 0))
        node_3 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(5, 5))
        node_4 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(5, 10))
        node_5 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(10, 0))
        node_6 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(10, 5))
        node_7 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(15, 10))

        #  Add heating network node
        node_heat = city.add_network_node(network_type='electricity',
                                          position=point.Point(10, 10))

        #  Add heating networks (only)
        city.add_edges_from([(node_1, node_2), (node_2, node_5),
                             (node_3, node_4), (node_6, node_heat),
                             (node_heat, node_7)], network_type='electricity')
        #  Add heating and deg network
        city.add_edge(node_2, node_3, network_type='heating_and_deg')

        #  Test function call
        list_deg_conn = \
            netop.get_list_with_energy_net_con_node_ids(city=city,
                                                        network_type='electricity')

        #  Sort lists in list_lhn_conn
        list_deg_conn.sort()
        for l in list_deg_conn:
            l.sort()

        assert list_deg_conn == [[node_1, node_2, node_3, node_4, node_5],
                                 [node_6, node_7, node_heat]]

    def test_get_list_with_energy_net_con_node_ids_3(self, fixture_building):

        #  Init city
        city = cit.City(environment=fixture_environment)

        #  Add building entities
        node_1 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(0, 0))
        node_2 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(5, 0))
        node_3 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(5, 5))
        node_4 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(5, 10))
        node_5 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(10, 0))
        node_6 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(10, 5))
        node_7 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(15, 10))

        #  Add heating network node
        node_heat = city.add_network_node(network_type='electricity',
                                          position=point.Point(10, 10))

        #  Add heating networks (only)
        city.add_edges_from([(node_1, node_2), (node_2, node_5),
                             (node_3, node_4), (node_6, node_heat),
                             (node_heat, node_7)], network_type='electricity')
        #  Add heating and deg network
        city.add_edge(node_2, node_3, network_type='heating_and_deg')

        #  Test function call
        list_deg_conn = \
            netop.get_list_with_energy_net_con_node_ids(city=city,
                                                        network_type='electricity',
                                                        search_node=node_heat)

        #  Sort lists in list_lhn_conn
        list_deg_conn.sort()

        assert list_deg_conn == [node_6, node_7, node_heat]

    def test_get_list_with_energy_net_con_node_ids_4(self, fixture_building):

        #  Init city
        city = cit.City(environment=fixture_environment)

        #  Add building entities
        node_1 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(0, 0))

        #  Test function call
        list_deg_conn = \
            netop.get_list_with_energy_net_con_node_ids(city=city,
                                                        network_type='electricity',
                                                        search_node=node_1)

        #  Sort lists in list_lhn_conn
        list_deg_conn.sort()

        assert list_deg_conn == []

    def test_get_list_with_energy_net_con_node_ids_5(self, fixture_building):

        #  Init city
        city = cit.City(environment=fixture_environment)

        #  Add building entities
        node_1 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(0, 0))
        node_2 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(15, 0))
        node_3 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(0, 20))
        node_4 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(15, 20))

        #  Add heating network points
        node_5 = city.add_network_node(position=point.Point(5, 0),
                                       network_type='heating')
        node_6 = city.add_network_node(position=point.Point(10, 0),
                                       network_type='heating')
        node_7 = city.add_network_node(position=point.Point(5, 20),
                                       network_type='heating')
        node_8 = city.add_network_node(position=point.Point(10, 20),
                                       network_type='heating')

        #  Add buildings, which are not relevant for LHN
        node_9 = \
            city.add_extended_building(extended_building=fixture_building,
                                       position=point.Point(30, 30))
        node_10 = \
            city.add_extended_building(extended_building=fixture_building,
                                       position=point.Point(40, 40))
        city.add_extended_building(extended_building=fixture_building,
                                   position=point.Point(50, 50))

        #  Add heating networks (only)
        city.add_edges_from([(node_1, node_5), (node_5, node_6),
                             (node_6, node_2)], network_type='heating')
        city.add_edges_from([(node_3, node_7), (node_7, node_8),
                             (node_8, node_4)], network_type='heating')

        #  Add arbitrary edge
        city.add_edge(node_9, node_10)

        #  Test function call
        list_lhn_conn = \
            netop.get_list_with_energy_net_con_node_ids(city=city,
                                                        network_type='heating')

        #  Sort lists in list_lhn_conn
        list_lhn_conn.sort()
        for li in list_lhn_conn:
            li.sort()

        assert list_lhn_conn == [[node_1, node_2, node_5, node_6],
                                 [node_3, node_4, node_7, node_8]]

    def test_calc_dist_point_to_linestr(self):

        #  Init point
        testpoint = point.Point(10, 10)

        testlstr = lstr.LineString([(0, 0), (10, 0)])

        dist = intersec.calc_dist_point_to_linestr(testpoint, testlstr)

        assert dist - 10 < 0.0001

    def test_calc_closest_point_w_linestr(self):

        #  Init point
        testpoint = point.Point(8, 8)

        testlstr = lstr.LineString([(0, 0), (10, 0), (10, 10)])

        closest_point = \
            intersec.calc_closest_point_w_linestr(testpoint, testlstr)

        assert closest_point.x == 10
        assert closest_point.y == 8

        testpoint2 = point.Point(-2, 0)

        closest_point2 = \
            intersec.calc_closest_point_w_linestr(testpoint2, testlstr)

        assert closest_point2.x == 0
        assert closest_point2.y == 0

    def test_get_lstr_points(self):

        #  Init point
        testpoint = point.Point(10, 8)

        testlstr = lstr.LineString([(0, 0), (10, 0), (10, 10)])

        tup_coord = intersec.get_lstr_points(testpoint, testlstr)

        assert tup_coord[0] == (10, 10) or tup_coord[0] == (10, 0)
        assert tup_coord[1] == (10, 0) or tup_coord[1] == (10, 10)

    def test_get_lstr_points_list(self):

        #  Define points
        P1 = point.Point(10, 0)
        P2 = point.Point(10, 10)
        P3 = point.Point(20, 5)
        P4 = point.Point(20, 15)
        P5 = point.Point(0, 25)
        P6 = point.Point(20, 25)

        # Define segments
        S1 = lstr.LineString([(P1.x, P1.y), (P2.x, P2.y)])
        S2 = lstr.LineString([(P3.x, P3.y), (P4.x, P4.y)])
        S3 = lstr.LineString([(P5.x, P5.y), (P6.x, P6.y)])

        list_seg = [S1, S2, S3]  # Test case 1

        target_point = point.Point(20, 25)

        tup_coord = intersec.get_lstr_points_list(target_point, list_seg)

        assert tup_coord[0] == (0.0, 25.0) or tup_coord[0] == (20.0, 25.0)
        assert tup_coord[1] == (20.0, 25.0) or tup_coord[1] == (0.0, 25.0)

    def test_get_min_span_tree_for_x_y_positions(self, fixture_building):

        #  Init city
        city = cit.City(environment=fixture_environment)

        #  Add building entities
        node_1 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(0, 0))
        node_2 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(1, 1))
        node_3 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(2, 1))
        node_4 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(0, 3))

        list_to_be_conn = [node_1, node_2, node_3, node_4]

        #  Add additional, arbitrary buildings
        node_5 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(1, 0))
        node_6 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(15, 20))

        min_span_graph = \
            netop.get_min_span_tree_for_x_y_positions(city,
                                                      nodelist=list_to_be_conn)

        #  Should include all existing nodes
        assert len(min_span_graph.nodes()) == 4
        assert sorted(min_span_graph.nodes()) == [node_1, node_2, node_3, node_4]

        list_edges = sorted(min_span_graph.edges())
        #  Should only hold minimum spanning tree edges

        # assert list_edges == [(node_1, node_2), (node_2, node_3),
        #                       (node_2, node_4)]

        assert list_edges[0] == (node_1, node_2) or list_edges[0] == (
            node_2, node_1)
        assert list_edges[1] == (node_2, node_3) or list_edges[1] == (
            node_3, node_2)
        assert list_edges[2] == (node_2, node_4) or list_edges[2] == (
            node_4, node_2)

    def test_gen_min_span_tree_along_street(self, fixture_building):

        #  Init city
        city = cit.City(environment=fixture_environment)

        #  Add building entities
        node_1 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(0, 0))
        node_2 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(2, 2))
        node_3 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(0.5, 4))

        node_4 = city.add_extended_building(extended_building=fixture_building,
                                            position=point.Point(8, 10))

        list_to_be_conn = [node_1, node_2, node_3]

        #  Add additional, arbitrary buildings
        node_str_1 = city.add_street_node(position=point.Point(-1, 1))
        node_str_2 = city.add_street_node(position=point.Point(10, 1))

        #  Add street edge
        city.add_edge(node_str_1, node_str_2, network_type='street')

        (min_span_graph, list_new_nodes) = \
            netop.gen_min_span_tree_along_street(city=city,
                                                 nodelist=list_to_be_conn)

        #  Should include all existing nodes plus new nodes
        assert len(min_span_graph.nodes()) == 6
        assert len(list_new_nodes) == 3

        mst_nodes = sorted(min_span_graph.nodes())

        assert mst_nodes == [node_1, node_2, node_3, 1007, 1008, 1009]
        assert list_new_nodes == [1007, 1008, 1009]
