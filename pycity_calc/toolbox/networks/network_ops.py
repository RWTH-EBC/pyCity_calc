#!/usr/bin/env python
# coding=utf-8
"""
Network operation toolbox of pycity_calc
"""

import os
import math
import copy
import pickle
import warnings
import matplotlib.pyplot as plt
import shapely.geometry.point as point
import shapely.geometry.linestring as lstr

import networkx as nx

import pycity_calc.toolbox.networks.intersection as intersec
import pycity_calc.cities.city as cit


def set_new_next_node_number(city):
    """
    Calculates and sets next node number attribute for city graph,
    if next_node_number attribute is None.

    Parameters
    ----------
    city : object
        City object
    """

    if 'next_node_number' not in city:

        #  Get node number
        curr_nb_nodes = len(city.nodes())

        #  Set next node number value
        city.next_node_number = 1001 + int(curr_nb_nodes)


def get_min_span_tree(graph, node_id_list):
    """
    Returns weighted graph with minimum spanning tree for given list of
    building nodes. Requires pos attribute within, node_id_list,
    e.g. pos = (10, 20)

    Parameter
    ---------
    graph : nx.Graph
        Graph of networkx module (must hold nodes with position parameters
        (position as shapely.geometry.point.Point, e.g. (10.5, 24.8))
    node_id_list: list
        List containing node ids (for nodes with position attribute),
        which should be used to find min span tree

    Returns
    ---------
    min_span_tree : nx.Graph
        Graph with minimum spanning tree edges (with weight parameter)
    """

    #  Check if nodes are within graph
    for i in node_id_list:
        assert graph.has_node(i)

    # Create empty graph
    temp_graph = nx.Graph()
    #  Iterate over all building node combinations
    for i in node_id_list:
        for j in node_id_list:
            if i != j:
                #  Calculate distance via sqr( (x1-x2)^2 + (y1-y2)^2)
                distance = calc_node_distance(graph, i, j)
                #  Create empty graph with original nodes and distances
                #  as attribute
                temp_graph.add_edge(i, j, weight=distance)
    # Minimum spanning tree function (with length as weight parameter)
    min_span_tree = nx.minimum_spanning_tree(temp_graph, weight='weight')
    return min_span_tree


def calc_node_distance(graph, node_1, node_2):
    """
    Calculates distance between two nodes of graph,
    Requires node attribute 'position' as shapely Point, e.g. Point(10, 15.2)

    Parameters
    -----------
    graph : nx.graph
        Graph object of networkx
    node_1 : int
        Node id of node 1
    node_2 : int
        Node id of node 2

    Returns
    --------
    distance : float
        Distance between nodes
    """
    assert graph.has_node(node_1)
    assert graph.has_node(node_2)
    node_1_x = graph.node[node_1]['position'].x
    node_1_y = graph.node[node_1]['position'].y
    node_2_x = graph.node[node_2]['position'].x
    node_2_y = graph.node[node_2]['position'].y

    distance = math.sqrt((node_1_x - node_2_x) ** 2 +
                         (node_1_y - node_2_y) ** 2)
    return distance


def calc_point_distance(point_1, point_2):
    """
    Calculates distance between two shapely Points

    Parameters
    -----------
    point_1 : Point
        shapely point object
    point_2 : Point
        shapely point object

    Returns
    --------
    distance : float
        Distance between points
    """

    distance = math.sqrt((point_1.x - point_2.x) ** 2 +
                         (point_1.y - point_2.y) ** 2)
    return distance


def check_node_on_pos(graph, position, resolution=1e-4):
    """
    Function checks, if at least one node of graph has position 'position'
    Returns boolean value. 'position' attribute must be shapely Point object.

    Parameters
    ----------
    graph : nx.Graph
        networkx graph object (nodes should have attribute 'position')
    position : shapely Point
        shapely Point object, e.g. Point(10.8, 24.5)
    resolution : float, optional
        Minimum distance between two points in m. If  position is closer
        than resolution to another existing node, the existing node will be
        returned.
        (default: 1e-4)

    Returns
    -------
    node_on_pos : bool
        boolean, which defines, if node does exist on position pos
        node_on_pos = True: At least one node exists with position pos
        node_on_pos = False: No node on position pos
    """

    node_on_pos = False  # Initial value

    for n in graph.nodes():
        if 'position' in graph.node[n]:
            #  If positions are identical, save name and node_id to dict
            if graph.node[n]['position'].distance(position) < resolution:
                node_on_pos = True
                break

    return node_on_pos


def convert_shapely_point_to_tuple(point):
    """
    Function converts shapely Point object into tuple (x, y)

    Parameters
    ----------
    point : shapely Point
        shapely Point object

    Returns
    -------
    pos_tuple : tuple
        2d tuple holding x- and y-coordinates of point
    """
    pos_tuple = (point.x, point.y)
    return pos_tuple

  #TODO: Implement function into pycity

def gen_pos_tuple_dict(city):
    """
    Generates dictionary of position tuples with node ids as keys.
    Requires shapely point positions as attributes on city nodes

    Parameters
    ----------
    city : object
        Object of pycity_calc

    Returns
    -------
    pos_dict : dict (of tuples)
        Dictionary with node ids as keys and position tuples as values
    """

    pos_dict = {}

    for n in city.nodes():
        #  Get current point position (shapely point object)
        curr_point = city.node[n]['position']

        #  Convert to tuple
        pos_tuple = convert_shapely_point_to_tuple(curr_point)

        #  Add to dictionary
        pos_dict[n] = pos_tuple

    return pos_dict


def add_weights_to_edges(graph):
    """
    Function calculates weights for edges in graph.
    Requires attribute 'position' as shapely Point object for nodes,
    e.g. position = Point(10.8, 20.5)

    Parameters
    ----------
    graph : networkx.Graph object
        Graph of networkx module (with position attributes)
    """

    for e in graph.edges():
        node_1 = e[0]
        node_2 = e[1]
        curr_distance = calc_node_distance(graph, node_1, node_2)
        #  Add distance as weight to edge
        graph.add_edge(node_1, node_2, weight=curr_distance)


def sum_up_weights_of_edges(graph, network_type=None):
    """

    Parameters
    ----------
    graph : Graph
        nx.graph object. Edges should hold attribute 'weight'

    Returns
    -------
    length : float
        Total network length
    network_type : str, optional
        Define network type (default: None).
        Options:
        - None. Sum up all edges
        - 'heating': Sum up weights of heating and heating_and_deg edges
        - 'heating_and_deg': Sum up weights of heating_and_deg edges
        - 'electricity': Sum up weights of electricity and heating_and_deg
           edges
    """

    length = 0

    if network_type is None:
        #  Sum up weight to total length of network
        for n, nbrsdict in graph.adjacency_iter():
            for nbr, eattr in nbrsdict.items():
                if 'weight' in eattr:
                    length += eattr['weight']
    else:
        #  Only sum up edge weight of specific network_type
        if network_type == 'heating':
            list_network_type = ['heating', 'heating_and_deg']
        elif network_type == 'electricity':
            list_network_type = ['electricity', 'heating_and_deg']
        elif network_type == 'heating_and_deg':
            list_network_type = ['heating_and_deg']

        for n, nbrsdict in graph.adjacency_iter():
            for nbr, eattr in nbrsdict.items():
                if 'weight' in eattr:
                    if 'network_type' in eattr:
                        if eattr['network_type'] in list_network_type:
                            length += eattr['weight']

    #  Due to double counting, divide by two
    length /= 2

    return length

# def calc_length_of_grids(graph, all_nodes):
#     """
#
#     Parameters
#     ----------
#     graph
#     all_nodes
#
#     Returns
#     -------
#
#     """
#     #  TODO: Missing explanations (org. inserted by D. Orth)
#
#     # for n in all_nodes:
#     #     assert n in graph, 'Node is not in graph!'
#
#     all_weight = []
#     for i in range(len(all_nodes)):
#         weight = []
#         for e in graph.edges():
#             node_1 = e[0]
#             node_2 = e[1]
#             if node_1 in all_nodes[i] and node_2 in all_nodes[i]:
#                 curr_distance = calc_node_distance(graph, node_1, node_2)
#                 weight.append(curr_distance)
#                 graph.add_edge(node_1, node_2, weight=curr_distance)
#
#         all_weight.append(sum(weight))
#
#     return all_weight


def is_street(node):
    """
    Checks if a given node object is a street.

    Parameters
    ----------
    node : graph.node[id] object

    Returns
    -------
    is_street : bool
        True, if node is of node_type street
    """
    if 'node_type' in node:
        if node['node_type'] == 'street':
            return True
    else:
        return False


def get_street_linestrings(graph, check_street=True):
    """
    Create a list of shapely LineStrings of the edges of an graph that are
    streets (have the 'node_type'=street)

    Parameters
    ----------
    graph : nx.Graph
        Networkx graph object (should hold nodes with 'position' attributes as
        shapely Points)
    check_street : bool, optional
        Checks, if graph edge is of network_type street (default: True)

    Returns
    -------
    list_lstr : list of shapely LineStrings
        List of shapely LineStrings, which represent street network
    """

    edge_list = graph.edges()

    #  Generate shapely geometry segment list
    list_lstr = []

    for e1, e2 in edge_list:  # Loop over all edges in street graph
        node1 = graph.node[e1]
        node2 = graph.node[e2]

        if check_street:
            # check if both nodes are streets
            if not (is_street(node1) and is_street(node2)):
                continue

        point1 = node1['position']
        point2 = node2['position']

        curr_seg = lstr.LineString([(point1.x, point1.y), (point2.x, point2.y)])

        # curr_seg = Segment(point1, point2)
        # curr_seg.edge = (e1, e2)
        list_lstr.append(curr_seg)

    return list_lstr


def get_str_linstr_pos(city, pnt, resolution=1e-4, check_street=True):
    """
    Returns tuple of street linestring start and stop point coordinates
    for linestring, where pnt is placed on.

    Returns None, if no street linestring exists, where pnt is placed on.

    Parameters
    ----------
    city : object
        City object
    pnt : object
        Shapely point object
    resolution : float, optional
        Resolution, in which pnt position is accepted on linestring
        (default: 1e-4)
    check_street : bool, optional
        Checks, if graph edge is of network_type street (default: True)

    Returns
    -------
    tup_pos : tuple (of tuples)
        Tuple of street linestring start and end point coordinates
    """

    #  Get list of linestrings of type street
    list_lstr = get_street_linestrings(city, check_street=check_street)

    #  Dummy value for min distance
    min_dist = intersec.calc_dist_point_to_linestr(pnt,
                                                   list_lstr[0]) + 10000000000
    final_lstr = None

    for i in range(len(list_lstr)):

        lstr = list_lstr[i]

        dist = intersec.calc_dist_point_to_linestr(pnt, lstr)

        if dist < min_dist:
            min_dist = dist
            final_lstr = lstr

    if final_lstr is None:
        if min_dist > resolution:
            tup_pos = None
    else:
        tup_pos = (final_lstr.coords[0], final_lstr.coords[1])

    return tup_pos



def calc_graph_pos_closest_to(graph, target_point, show_process=False):
    """
    Calculates point on graph, which is closest to target point.
    Point can be on a graph node or edge.
    Points must be shapely Point objects!

    Parameters
    ----------
    graph : nx.Graph
        Networkx graph object (should hold nodes with 'position' attributes as
        shapely Points)
    target_point : shapely Point
        shapely Point object (e.g. Point(10.5, 25.8))
    show_process : bool, optional
        Defines if steps of ongoing process should be plotted (default: False)

    Returns
    -------
    closest_point : shapely Point
        shapely Point with x- and y-coordinates of point on graph, which is
        closest to target point
    segment_start_point : shapely Point
        shapely Point with x- and y-coordinates of start point of segment,
        where closest point is placed on
    segment_stop_point : shapely Point
        shapely Point with x- and y-coordinates of stop point of segment,
        where closest point is placed on
    """

    if show_process:
        print('Start calculation of closest point position of graph to ' +
              'given target point: ', target_point)

    #  Get list of street network linestrings
    list_seg = get_street_linestrings(graph)

    if len(list_seg) == 0:
        raise AssertionError('Segment list is empty! '
                             'Check get_street_linestrings function call!'
                             'Did you generate and hand over edges of'
                             'network_type street!')

    # Calculate shapely geometry point, which is closest to target_point
    #  position. Returns point as well as segment, where point is placed on
    closest_point = \
        intersec.calc_closest_point_w_list_linestr(target_point, list_seg)

    #  Get coordinates of start and stop points of street segment
    tup_pos = get_str_linstr_pos(graph, pnt=closest_point, check_street=True)

    # #  Get coordinates of start and stop points of street segment
    # tup_pos = intersec.get_lstr_points_list(closest_point, list_seg)

    if tup_pos is None:
        msg = 'Have not found linestring, where point is placed on.'
        raise AssertionError(msg)

    else:
        #  Generate point objects
        segment_start_point = point.Point(tup_pos[0])
        segment_stop_point = point.Point(tup_pos[1])

    if show_process:
        print('Closest point position is:', closest_point)

    return closest_point, segment_start_point, segment_stop_point


def get_node_id_by_position(graph, position, resolution=1e-4):
    """
    Returns node id for given position (if node exists).
    Nodes must have position attribute as shapely Point!

    Parameters
    ----------
    graph : nx.Graph
        Networkx Graph
    positions : dict
        In general, positions in uesgraphs are defined by
        `shapely.geometry.point` objects. This attribute converts the
        positions into a dict of numpy arrays only for use in
        uesgraphs.visuals, as the networkx drawing functions need this
        format.
    resolution : float, optional
        Minimum distance between two points in m. If  position is closer
        than resolution to another existing node, the existing node will be
        returned.
        (default: 1e-4)

    Returns
    -------
    node_id : int
        Node id
    """
    node_id = None

    for node in graph:
        if 'position' in graph.node[node]:

            #  Get node position (shapely point object)
            point_1 = graph.node[node]['position']

            #  If positions are identical, save name and node_id to dict
            if calc_point_distance(point_1, position) < resolution:
                node_id = node

    return node_id


def calc_center_pos(city, nodelist):
    """
    Calculates center position for nodes in nodelist

    Parameters
    ----------
    city : object
        city object of pycity_calc
    nodelist : list (of ints)
        List of node ids

    Returns
    -------
    pos : tuple
        Position tuple (x, y)
    """

    for node in nodelist:
        assert node in city, ('Node ' + str(node) + 'is not in city!')

    x_sum = 0
    y_sum = 0
    nb_nodes = len(nodelist)

    for id in nodelist:
        node_x = city.node[id]['position'].x
        node_y = city.node[id]['position'].y

        x_sum += node_x
        y_sum += node_y

    x = x_sum / nb_nodes
    y = y_sum / nb_nodes

    pos = (x, y)

    return pos


def find_closest_node(graph, target_node, node_list=None):
    """
    Returns node if of closest node to target node.
    If node_list is set, only searches for nodes in node_list, else
    searches whole graph.
    Requires position argument for nodes (as shapely Point).

    Parameters
    ----------
    graph : nx.Graph
        Networkx Graph
    target_node : int
        Node id of target node
    node_list : list, optional
        List of node ids, which should be used for searching closest node
        (default: None)

    Returns
    -------
    close_node_id : int
        Node id of node, which is closest to target node
    """

    #  Check if nodes are within graph
    if node_list is not None:
        for node in node_list:
            assert node in graph

    if node_list is None:  # Search complete graph
        search_list = graph.nodes()
    else:  # Only search within node_list
        search_list = node_list

    if target_node in search_list:
        #  Erase target_node_id from search_list
        search_list.remove(target_node)

    # Select start node
    close_node_id = search_list[0]
    #  Calculate initial distance
    short_dist = calc_node_distance(graph, target_node, close_node_id)

    for id in search_list:
        dist = calc_node_distance(graph, target_node, id)
        #  If new distance is smaller than current shortest distance
        if dist < short_dist:
            #  Set new distance
            short_dist = dist
            close_node_id = id

    return close_node_id


def sort_node_list_by_distance(graph, target_node, node_list):
    """
    Returns sorted list of nodes (sorted by distance to target node;
    ascending order)

    Parameters
    ----------
    graph : nx.Graph
        Networkx Graph
    target_node : int
        Node id of target node
    node_list : list
        List of node ids, which should be used for sorting

    Returns
    -------
    sorted : tuple
        Sorted tuple of node ids (sorted by distance to target node)
    """
    if node_list is not None:
        for node in node_list:
            assert node in graph

    dist_list = []
    #  Generate distance list
    for i in range(len(node_list)):
        dist = calc_node_distance(graph, target_node, node_list[i])
        dist_list.append(dist)

    # Sort dist_list and node_list by dist_list distance values
    dist_list, node_list = zip(*sorted(zip(dist_list, node_list)))
    return node_list


def delete_nodes_build(graph, nodelist):
    """
    Deletes all building/network nodes with ids within nodelist

    Parameters
    ----------
    graph : nx.Graph
        Graph, where nodes should be deleted
    nodelist : list
        List with node ids
    """

    nodelist_copy = copy.deepcopy(nodelist)
    for n in nodelist_copy:
        if 'node_type' in graph.node[n]:
            if graph.node[n]['node_type'] == 'building':
                graph.remove_building(n)
            else:
                warnings.warn('Unknown node type. Node ' + str(n) +
                              ' has not been erased.')
        else:
            warnings.warn('Unknown node type. Node ' + str(n) +
                          ' has not been erased.')


def get_street_subgraph(city, nodelist_str=None):
    """
    Returns networkx (copied) subgraph of street network within city object

    Parameters
    ----------
    city : city object
        City object of pycity_calc
    nodelist_str : list (of ints), optional
        List holding street node ids. (default: None)
        If set to None, extract all street nodes

    Returns
    -------
    street_graph : nx.Graph
        networkx Graph of street network within city object
    """

    #  If set to None, search over all nodes
    if nodelist_str is None:
        nodelist_str = city.nodes()
    else:
        for n in nodelist_str:
            assert n in city.nodes()

    #  Set up new city (empty)
    street_graph = cit.City(environment=city.environment)

    list_n_str = []
    #  Add building nodes of nodelist to street_graph
    for n in nodelist_str:
        if 'node_type' in city.node[n]:
            if city.node[n]['node_type'] == 'street':
                curr_pos = city.node[n]['position']
                #  Add nodes to city_copy
                street_graph.add_node(n, position=curr_pos, node_type='street')
                list_n_str.append(n)

    #  Add all edges of type street
    for u, v in city.edges():
        if 'network_type' in city.edge[u][v]:
            if city.edge[u][v]['network_type'] == 'street':
                #  Add street edge to street_graph
                street_graph.add_edge(u, v, network_type='street')

    #  Add nodelist street
    street_graph.nodelist_street = list_n_str

    return street_graph

def get_lhn_subgraph(city, search_node):
    """
    Returns networkx (copied) subgraph of street network within city object

    Parameters
    ----------
    city : city object
        City object of pycity_calc
     search_node : int,
        Id of a node which is in the lhn subgraph

    Returns
    -------
    street_graph : nx.Graph
        networkx Graph of street network within city object
    """
    #create empty graph
    lhn_graph = cit.City(environment=city.environment)
    #get list of lhn connected nodes
    lhn_con_nodes = get_list_with_energy_net_con_node_ids(city,search_node=search_node, network_type='heating')


    list_n_lhn = []
    #  Add building nodes of nodelist to lhn_graph
    for n in lhn_con_nodes:
        if 'node_type' in city.node[n]:
            if city.node[n]['node_type'] == 'heating' or city.node[n]['node_type'] == 'building':
                curr_pos = city.node[n]['position']
                #  Add nodes to city_copy
                lhn_graph.add_node(n, position=curr_pos, node_type='heating')
                list_n_lhn.append(n)

    #  Add all edges of type heating to lhn_graph
    for u, v in city.edges():
        if u in lhn_con_nodes and v in lhn_con_nodes:
            if 'network_type' in city.edge[u][v]:
                if city.edge[u][v]['network_type'] == 'heating':
                    #  Add street edge to street_graph
                    lhn_graph.add_edge(u, v, network_type='heating')

    #Add nodelist street
    lhn_graph.nodelist_street = list_n_lhn

    return lhn_graph

def get_build_str_subgraph(city, nodelist=None):
    """
    Returns subcity of city object, which only holds street network and all
    building nodes of nodelist.

    Parameters
    ----------
    city : object
        City object of pycity_calc
    nodelist : list (of ints), optional
        List with building node ids, which should be returned
        (default: None). If nodelist is None, all building nodes are returned
        within subcity graph. Parameter nodelist does not influence returned
        street graph nodes.

    Returns
    -------
    subcity : object
        City object of pycity_calc
    """

    #  Check if all nodes of nodelist are within nodelist_building of city
    if nodelist is not None:
        for id in nodelist:
            assert id in city.nodelist_building, ('ID ' + str(id) + 'is not ' +
                                                  'within city object.')
        for id in nodelist:
            if 'node_type' in city.node[id]:
                #  If node_type is building
                if city.node[id]['node_type'] == 'building':
                    #  Check if entity is kind building (and not pv or wind)
                    assert city.node[id]['entity']._kind == 'building'

    # Initialize street_graph as deepcopy of self.city
    city_copy = copy.deepcopy(city)

    #  Get subgraph (only holding nodes within nodelist)
    subcity = city_copy.subgraph(nodelist)

    #  Read environment pointer
    subcity.environment = city.environment

    #  Add street graph
    street = get_street_subgraph(city)

    #  Add street graph to subcity
    subcity.add_nodes_from(street)

    #  Add attribute node_type = street to every node
    for n in street.nodelist_street:
        subcity.node[n]['node_type'] = 'street'
        #  Extract original position
        curr_pos = street.node[n]['position']
        #  Add position to subcity street
        subcity.node[n]['position'] = curr_pos

    # Add all edges of type street
    for u, v in street.edges():
        if 'network_type' in street.edge[u][v]:
            if street.edge[u][v]['network_type'] == 'street':
                #  Add street edge to street_graph
                subcity.add_edge(u, v, network_type='street')

    if nodelist is None:
        subcity.nodelist_building = city_copy.nodelist_building
    else:
        subcity.nodelist_building = nodelist

    # Add nodelist_street
    subcity.nodelist_street = city_copy.nodelist_street

    #  Set next node number value
    set_new_next_node_number(city)

    return subcity


#  TODO: Add function to extract subgraph with all possible uesgpraph edges

def get_min_span_tree_for_x_y_positions(city, nodelist):
    """

    Returns weighted graph with minimum spanning tree for given list of
    building nodes. Requires pos attribute as shapely.geometry Point object.

    Parameter
    ---------
    city : object
        city object of pycity
    nodelist : list (of ints)
        List holding node ids

    Returns
    ---------
    min_span_tree : nx.Graph
        Graph with minimum spanning tree edges (with weight parameter)
    """

    #  Check if nodes are within graph
    for i in nodelist:
        assert city.has_node(i)

    # Create empty graph
    temp_graph = copy.deepcopy(city)

    #  Erase all existing edges
    if len(temp_graph.edges()) > 0:
        temp_graph.remove_edges_from(temp_graph)

    #  Iterate over all building node combinations
    for i in nodelist:
        for j in nodelist:
            if i != j:
                #  Calculate distance
                p_1 = city.node[i]['position']
                p_2 = city.node[j]['position']
                distance = calc_point_distance(point_1=p_1, point_2=p_2)
                #  Create empty graph with original nodes and distances
                #  as attribute
                temp_graph.add_edge(i, j, weight=distance)

    # Minimum spanning tree function (with length as weight parameter)
    min_span_tree = nx.minimum_spanning_tree(temp_graph, weight='weight')

    #  Erase all non connected nodes
    list_remove = []
    for n in min_span_tree.nodes():
        if nx.degree(G=min_span_tree, nbunch=n) == 0:
            list_remove.append(n)
    for n in list_remove:
        min_span_tree.remove_node(n)

    return min_span_tree


def process_neighbors(city, node, etype, list_conn_nodes, list_curr_nodes,
                      processed_nodes):
    """
    Function searches for all nodes, which are interconnected with edges of
    specific type.
    ONLY valid for lhn or mg types! (uses 'lhn_and_mg' types within code)

    Parameters
    ----------
    city : object
        city object of pycity_calc
    node : int
        Node label/id
    etype : str
        Type of search edge (e.g. 'lhn' or 'mg')
    list_conn_nodes : list (of lists)
        List holding sublists. All sublists are hold sets of nodes, which
        are interconnected with etype edges
    list_curr_node : list (of integers)
        List holding actual set of interconnected nodes
    processed_nodes : list (of integers)
        List holding all node labels/ids (of processed nodes)

    Returns
    -------
    list_curr_nodes : list (with integers)
        List of building node ids, which are interconnected with edges of
        type 'etype' (e.g. lhn or mg)
        e.g. [0, 2, 3, 5] --> Buildings 0, 2, 3, 5 are interconnected
    """

    if node not in processed_nodes:
        #  Get list of neighbors of node
        list_of_neighbors = city.neighbors(node)
        #  Add node to list of processed nodes
        processed_nodes.append(node)
        #  If node has neighbors nb, continue to analyse neighbors
        if list_of_neighbors:
            #  Preprocess list_of_neighbors (erase neighbors for non-etype
            #  connections)
            for nb in list_of_neighbors:
                if 'network_type' in city.edge[node][nb]:
                    if city.edge[node][nb]['network_type'] != etype and \
                            city.edge[node][nb]['network_type'] != 'heating_and_deg':
                        list_of_neighbors.remove(nb)
            # Iter over neighbor list
            for nb in list_of_neighbors:
                #  If neighbor is connected with edge type etype or
                #  lhn_and_mg, add to temp_list and conn_list
                if 'network_type' in city.edge[node][nb]:
                    if city.edge[node][nb]['network_type'] == etype or \
                            city.edge[node][nb]['network_type'] == 'heating_and_deg':
                        #  If not within list_curr_nodes (list of lhn connected
                        #  nodes), add node to list
                        if node not in list_curr_nodes:
                            list_curr_nodes.append(node)
                        # If neighbor not within list_curr_nodes, add neighbor
                        #  to list
                        if nb not in list_curr_nodes:
                            list_curr_nodes.append(nb)
            # After processing all neighbors, process neighbors of neighbors
            for nb in list_of_neighbors:
                #  If not all neighbors have been processed, call recursive
                #  function with neighbor as new node
                if nb not in processed_nodes:
                    process_neighbors(city=city, node=nb, etype=etype,
                                      list_conn_nodes=list_conn_nodes,
                                      list_curr_nodes=list_curr_nodes,
                                      processed_nodes=processed_nodes)
                    #  If all neighbors have been processed (all end nodes
                    #  are reached within lhn network),
    return list_curr_nodes


def get_list_with_energy_net_con_node_ids(city, network_type='heating',
                                          search_node=None,
                                          build_node_only=False):
    """
    Function returns list of energy network connected subgraphs.
    Also accounts for 'heating_and_deg' networks.

    Parameters
    ----------
    city : object
        city object of pycity_calc
    network_type : str, optional
        Chosen network type (default: 'heating')
        Options: 'heating' or 'electricity'
    search_node : int, optional
        Id of node, which should be used for search (default: None)
        If search_node == None, all lhn networks are searched.
    build_node_only : bool, optional
        Defines, if all node types or only nodes of node_type 'building'
        (according to uesgraph) should be extracted (default: False).
        If True: Only extract nodes with node_type 'building'
        If False: Extract all nodes connected to specific network

    Returns
    -------
    list_conn_nodes : list (of lists or of integers)
        List holding lists of lhn connected nodes, e.g.
        [[0,2,3], [4,7]] --> Buildings 0, 2 and 3 are interconnected.
        Building 4 and 7 are interconnected.
        If search_node is set, list of integers is returned,
        e.g. [0, 2, 7]
    """

    assert network_type in ['heating', 'electricity']

    list_conn_nodes = []
    list_curr_nodes = []
    processed_nodes = []

    if search_node is None:
        # Loop over all nodes of graph
        for node in city.nodes():
            # Execute function process_neighbors
            list_curr_nodes = \
                process_neighbors(city=city, node=node, etype=network_type,
                                  list_conn_nodes=list_conn_nodes,
                                  list_curr_nodes=list_curr_nodes,
                                  processed_nodes=processed_nodes)

            # If current list is not empty, add list to list_lhn_conn_nodes
            if list_curr_nodes:
                list_conn_nodes.append(list_curr_nodes)
            list_curr_nodes = []

        if build_node_only:
            #  Erase all nodes within list, if they are not of node_type
            #  'building'

            list_nodes_clean = []

            for sublist in list_conn_nodes:

                sublist_clean = []

                for n in sublist:
                    if 'node_type' in city.node[n]:
                        if city.node[n]['node_type'] == 'building':
                            sublist_clean.append(n)
                if sublist_clean != []:
                    list_nodes_clean.append(sublist_clean)

            #  Overwrite list_conn_nodes with cleaned up list
            #  Building nodes, only
            list_conn_nodes = list_nodes_clean

    else:  # Use search node (only get network connected to search node)

        assert search_node in city.nodes(), 'Search node is not within city!'

        # Execute function process_neighbors
        list_conn_nodes = \
            process_neighbors(city=city, node=search_node, etype=network_type,
                              list_conn_nodes=list_conn_nodes,
                              list_curr_nodes=list_curr_nodes,
                              processed_nodes=processed_nodes)

        if build_node_only:
            #  Erase all nodes within list, if they are not of node_type
            #  'building'

            list_nodes_clean = []

            for n in list_conn_nodes:
                if 'node_type' in city.node[n]:
                    if city.node[n]['node_type'] == 'building':
                        list_nodes_clean.append(n)

            #  Overwrite list_conn_nodes with cleaned up list
            #  Building nodes, only
            list_conn_nodes = list_nodes_clean

    return list_conn_nodes


def get_list_build_without_energy_network(city):
    """
    Returns list of building entity nodes, which are neither connected to a
    heating nor to an decentralized electrical network.

    Parameters
    ----------
    city : object
        City object of pyCity_calc

    Returns
    -------
    list_single_build : list
        List holding building entity node ids (int) of buildings, which are
        neither connected to a heating nor to an decentralized electrical
        network
    """

    #  Get list of all building entities
    list_b_entities = city.get_list_build_entity_node_ids()

    #  Identify all single buildings (in city, but not LHN or DEG
    #  connected
    list_single_build = []

    for n in list_b_entities:
        #  Add all buildings without graph neighbours
        if len(city.neighbors(n)) == 0:
            list_single_build.append(n)
        # If buildings are connected to graph, check network_type
        else:
            valid_net = True
            for k in city.neighbors(n):
                if 'network_type' in city.edge[k][n]:
                    net_type = city.edge[k][n]['network_type']
                    if (net_type == 'heating' or
                                net_type == 'heating_and_deg' or
                                net_type == 'electricity'):
                        valid_net = False
                        break
                if 'network_type' in city.edge[n][k]:
                    net_type = city.edge[n][k]['network_type']
                    if (net_type == 'heating' or
                                net_type == 'heating_and_deg' or
                                net_type == 'electricity'):
                        valid_net = False
                        break

            if valid_net:
                list_single_build.append(n)


def remove_str_nodes_degree_one(city, nodelist):
    """
    Remove all nodes of degree 1, which are not part of nodelist.
    E.g. necessary for removing street nodes with only single edge inter-
    connection

    Parameters
    ----------
    city : city object
        City object of pycity_calc
    nodelist : list (of ints)
        List of node ids, which should not be removed (e.g. can be of degree
        1, such as building nodes in minimum spann. network)
    """

    #  Identify all nodes of degree 1, which are not in nodelist
    #  These should be street nodes with only single edge --> Remove them
    list_remove = []
    for n in city.nodes():
        if n not in nodelist:
            if nx.degree(city, nbunch=n) == 1:
                list_remove.append(n)
    # Erase nodes
    for n in list_remove:
        city.remove_node(n)


def gen_min_span_tree_along_street(city, nodelist, plot_graphs=False):
    """
    Generates minimum spanning tree of specific network type along street n
    etwork within city object. Requires street network.
    Connects all building node ids within nodelist.

    Parameters
    ----------
    city : object
        City object of pycity_calc
    nodelist : list
        List of building nodes, which should be connected with network
    plot_graphs : bool, optional
        Defines, if graph results should be plotted (default: False)

    Returns
    -------
    res_tuple : tuple (with object and list)
        Results tuple of type (min_span_graph, list_new_nodes), holding:
        min_span_graph : object
            City object of pycity_calc with minimum spanning tree edges
        list_new_nodes : list
            List with new node ids (within min. spann tree, compared to city)
    """

    for n in nodelist:
        assert n in city.nodes()

    list_new_nodes = []

    if plot_graphs:
        pos = gen_pos_tuple_dict(city)
        #  Draw
        nx.draw_networkx(city, pos)
        plt.title('Original city structure')
        plt.show()

    #  Copy street network and nodes from nodelist
    graph_temp = get_build_str_subgraph(city, nodelist=nodelist)

    if plot_graphs:
        pos = gen_pos_tuple_dict(graph_temp)
        #  Draw
        nx.draw_networkx(graph_temp, pos)
        plt.title('Mod. city structure (only relevant buildings)')
        plt.show()

    #  New node number init (necessary to prevent handing over ids, which
    #  already exist within original city object
    id_new = city.new_node_number()

    #  Loop over all building nodes and add intersect points and new segments
    for n in nodelist:

        #  Get current point position
        curr_pos = graph_temp.node[n]['position']

        #  Extract closest point as well as start and stop points of closest
        #  segment
        closest_point_pos, segment_start_position, segment_stop_position = \
            calc_graph_pos_closest_to(graph=graph_temp, target_point=curr_pos)

        #  If node on position already exists and if it is building node
        if check_node_on_pos(graph_temp, closest_point_pos):

            #  Get id of existing node
            id_exist = get_node_id_by_position(graph_temp, closest_point_pos)

            #  Connect node n to existing node with network edge
            graph_temp.add_edge(n, id_exist)

        else:  # Add new node and connect it to street segment nodes
            #  Add node as network node to graph_temp
            graph_temp.add_node(id_new, position=closest_point_pos, node_type='street')
            list_new_nodes.append(id_new)

            #  Add network edge (node to street connection)
            graph_temp.add_edge(n, id_new)

            #  Connect new node with street segment start and stop points
            id_start = get_node_id_by_position(graph_temp,
                                               position=segment_start_position)
            #  Add network edge
            graph_temp.add_edge(id_start, id_new)

            id_stop = get_node_id_by_position(graph_temp,
                                              position=segment_stop_position)
            #  Add network edge
            graph_temp.add_edge(id_stop, id_new)

            #  Remove redundant edge, on which new node has been placed
            graph_temp.remove_edge(id_start, id_stop)

            id_new += 1

        if plot_graphs:
            pos = gen_pos_tuple_dict(graph_temp)
            #  Draw
            nx.draw_networkx(graph_temp, pos)
            plt.title('Mod. city (intermediate)')
            plt.show()

    if plot_graphs:
        pos = gen_pos_tuple_dict(graph_temp)
        #  Draw
        nx.draw_networkx(graph_temp, pos)
        plt.title('Mod. city (with build-str interconnections)')
        plt.show()

    # Identify all nodes of degree 1, which are not in nodelist
    remove_str_nodes_degree_one(graph_temp, nodelist)

    # Add weight to edges
    add_weights_to_edges(graph_temp)

    #  Generate minimum spanning tree
    min_span_graph = nx.minimum_spanning_tree(graph_temp, weight='weight')

    #  Identify all nodes of degree 1, which are not in nodelist
    #  These should be street nodes with only single edge --> Remove them
    to_remove = True

    while to_remove:

        #  Remove street nodes of degree 1
        remove_str_nodes_degree_one(min_span_graph, nodelist)

        for n in min_span_graph.nodes():
            if n not in nodelist:
                if nx.degree(min_span_graph, nbunch=n) == 1:
                    to_remove = True
                    break
                else:
                    to_remove = False

    if plot_graphs:
        pos = gen_pos_tuple_dict(min_span_graph)
        #  Draw
        nx.draw_networkx(min_span_graph, pos)
        plt.title('Min. span tree (energy network)')
        plt.show()

    return (min_span_graph, list_new_nodes)


if __name__ == '__main__':

    def plot_city(city):
        """
        Plot city function. Prevents import error (mutual top-level import
        of city_visual and netops)

        Parameters
        ----------
        city : object
            City object of pycity_calc
        """

        import pycity_calc.visualization.city_visual as cityvis
        #  Plot city district
        cityvis.plot_city_district(city, plot_lhn=True, plot_deg=True,
                                   plot_esys=True)

    #  Example for minimum spanning tree network generation within city
    #  based on street networks

    #  User inputs
    #  #-------------------------------------------------------------------
    city_file_name = 'city_clust_simple.p'

    #  Nodes, which should be connected with network
    nodelist = [1001, 1002, 1003, 1005, 1009, 1010]

    #  Network type ('heating', 'electrical' or 'heating_and_deg')
    ntype = 'heating'

    #  Plot stepwise results with matplotlib
    plot_stepwise = True

    #  End of user inputs
    #  #-------------------------------------------------------------------

    this_path = os.path.dirname(os.path.abspath(__file__))
    pycity_calc_path = os.path.dirname(os.path.dirname(this_path))

    city_path = os.path.join(pycity_calc_path, 'toolbox', 'analyze',
                             'input', city_file_name)

    #  Load city object
    city = pickle.load(open(city_path, mode='rb'))

    #  Generate heating network within city
    (min_span_graph, list_new_nodes) = \
        gen_min_span_tree_along_street(city, nodelist=nodelist,
                                       plot_graphs=plot_stepwise)

    print('Nodes of min. spann. tree:')
    print(min_span_graph.nodes())

    nx.draw_networkx(G=min_span_graph)
    plt.show()
    plt.close()
