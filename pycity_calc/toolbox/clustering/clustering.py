#!/usr/bin/env python
# coding=utf-8
"""
Cluster class of pycity_calc.

Requires complex city object (with buildings and street network) as input
"""

import os
import copy
import datetime
import random
import math
import networkx as nx
import pickle

# from sympy.geometry import Point, Segment
import shapely.geometry.point as point

from sklearn.cluster import MeanShift, estimate_bandwidth

import pycity_calc.cities.scripts.complex_city_generator as comcity
import pycity_calc.toolbox.networks.intersection as intersec
import pycity_calc.toolbox.networks.network_ops as netop
import pycity_calc.visualization.city_visual as cityvis
import pycity_calc.toolbox.clustering.experiments.kmeans_city_clustering\
    as kmean
import pycity_calc.toolbox.clustering.experiments.cluster_experiment as cex



def gen_cl_log(log_path, method, max_nb_build=None, max_b_str=None,
               max_b_b=None, use_dist_one_b=None, use_act_cluster=None,
               nb_clusters=None, kmeans_method=None, search_range=None,
               use_active_node=None, filename=None, c_dict_name=None,
               path_save_clust=None):
    """
    Generate log file of input paramters for clustering

    Parameters
    ----------
    log_path
    method
    max_nb_build
    max_b_str
    max_b_b
    use_dist_one_b
    use_act_cluster
    nb_clusters
    kmeans_method
    search_range
    use_active_node
    filename
    c_dict_name
    path_save_clust
    """

    #  Open log file
    log_file = open(log_path, mode='w')
    log_file.write('Date: ' + str(datetime.datetime.now()) + '\n')
    log_file.write('Clustering method: ' + str(method) + '\n')

    log_file.write('City pickle object filename: ' + str(filename) + '\n')
    log_file.write('City pickle filepath: ' + str(file_path) + '\n')
    log_file.write('Cluster dict name: ' + str(c_dict_name) + '\n')
    log_file.write('Path to cluster pickle file: ' + str(path_save_clust)
                   + '\n')

    if method == 0:
        log_file.write('Clustering method is street clustering')
        log_file.write('Max. number of buildings per cluster: '
                       + str(max_nb_build) + '\n')
        log_file.write('max_b_str: ' + str(max_b_str) + '\n')
        log_file.write('max_b_b: ' + str(max_b_b) + '\n')
        log_file.write('use_dist_one_b: ' + str(use_dist_one_b) + '\n')
        log_file.write('use_act_cluster: ' + str(use_act_cluster) + '\n')
    elif method == 1:
        log_file.write('Clustering method is kmeans')
        log_file.write('Max. number of buildings per cluster: '
                       + str(max_nb_build) + '\n')
        log_file.write('Number of desired clusters: ' + str(nb_clusters)
                       + '\n')
        log_file.write('kmeans_method: ' + str(kmeans_method) + '\n')
    elif method == 2:
        log_file.write('Clustering method is meanshift')
    elif method == 3:
        log_file.write('Clustering method is positional clustering')
        log_file.write('Max. number of buildings per cluster: '
                       + str(max_nb_build) + '\n')
        log_file.write('Search range: ' + str(search_range) + '\n')
        log_file.write('use_active_node: ' + str(use_active_node) + '\n')

    log_file.close()


def check_if_cluster_is_oversized(cluster_dict, max_nb_build):
    """
    Checks if (at least) one cluster exceeds maximum allowed number of
    buildings nodes.

    Parameters
    ----------
    cluster_dict : dict
        Dictionary with key as cluster number and subgraph (object) as
        value
    max_nb_build : int
        Maximum allowed number of buildings per cluster

    Returns
    -------
    c_size_okay : bool
        True, if cluster sizes are okay. False, if (at least) one cluster
        is too large
    """

    c_size_okay = True  # Assume all sizes are within boundaries
    #  Check cluster_dict for size of every cluster
    for key in cluster_dict:
        if len(cluster_dict[key]) > max_nb_build:
            #  If one cluster is larger than max. value
            #  Set c_size_okay to False
            c_size_okay = False

    return c_size_okay

def get_id_min_x_pos(city):
    """
    Returns id of node with smallest x position value.

    Parameters
    ----------
    city : object
        City object of pycity_calc. Should hold building object with position.

    Returns
    -------
    min_id : int
        Id of node with minimum distance
    """

    min_x = None

    #  Find start node at outer area (min. x pos. of uesgraph)
    for n in city.nodelist_building:
        x_pos = city.nodes[n]['position'].x

        if min_x is None:
            min_x = x_pos
            min_id = n
        else:
            if x_pos < min_x:
                min_x = x_pos
                min_id = n

    return min_id

def get_min_dist_and_id(city, nodelist, search_id):
    """
    Returns minimum distance and node id of node, which is closest to
    search_id node.

    Parameters
    ----------
    city : object
        City object of pycity_calc
    nodelist : list
        List of node ids, which should be searched for nearest neighbor
        of search_id node
    search_id : int
        Id of start node for distance calculation

    Returns
    -------
    result_tuple : tuple
        Tuple holding minimum distance value and node id (min_dist, min_id)
    """

    min_dist = None

    #  Loop over all building node ids in remain_build_list
    #  and find nearest neighbor (by closest distance)
    for n in nodelist:
        distance = netop.calc_node_distance(city, node_1=search_id,
                                            node_2=n)
        if min_dist is None:
            min_dist = distance
            min_id = n

        else:
            if distance < min_dist:
                min_dist = distance
                min_id = n

    result_tuple = (min_dist, min_id)

    return result_tuple

def run_kmeans(city, nb_clusters):
    """
    Runs kmeans algorithm.

    Parameters
    ----------
    city : object
        City object of pycity_calc (should include building objects)
    nb_clusters : int
        Number of desired clusters for kmeans

    Returns
    -------
    cluster_dict : dict
        Dictionary with cluster number as key and lists of node id as values
    """

    #  Calculate clusters dictionary (with array positions)
    cluster_dict = kmean.kmeans_clustering(city,
                                           nb_clusters=nb_clusters,
                                           show_kmeans=False)

    #  Convert clusters array entries to Point objects
    cluster_dict = kmean.conv_cluster_array_to_point(cluster_dict)

    cluster_dict = kmean.conv_point_to_node_ids(city, cluster_dict)

    return cluster_dict

def run_kmeans_clustering(city, kmeans_method, nb_clusters=None):
    """
    Performs kmeans clustering

    Parameters
    ----------
    city : object
        City object of pycity_calc (should include building objects)
    kmeans_method : int, optional
        Method to perform kmeans clustering
        (default: 0)
        0 - Single run of kmeans (neglect max_nb_build constraint)
        1 - Loop over kmeans with ascending number of clusters until
            max_nb_build is kept for every cluster (very slow method!)
        2 - Runs kmeans on every oversized cluster until cluster size is
            within range.
    nb_clusters : int, optional
        Desired number of clusters for kmeans (default: None)
        Only relevant for kmeans_method = 0!

    Returns
    -------
    cluster_dict : dict
        Dictionary with cluster number as key and lists of node id as values
    """

    if kmeans_method == 0:  # Single kmeans run

        assert nb_clusters is not None, ('User has to define desired number ' +
                                         'of clusters (nb_clusters). ' +
                                         'Currently, value is set to default' +
                                         ' None.')
        assert nb_clusters > 0

        cluster_dict = run_kmeans(city, nb_clusters)

    elif kmeans_method == 1:  # Loop until all clusters are within range

        print('Loop over kmeans until every cluster is within' +
              ' max_nb_build')

        #  Calc. min. possible number of clusters
        nb_clusters = math.ceil(len(city.nodelist_building)/max_nb_build)

        c_size_okay = False
        #  Defines, if cluster sizes does not exceed max_nb_build

        #  While one cluster is not within max_nb_build limit
        while c_size_okay is False:

            print('Current desired number of clusters: ', nb_clusters)

            cluster_dict = run_kmeans(city, nb_clusters)

            c_size_okay = \
                check_if_cluster_is_oversized(cluster_dict, max_nb_build)

            if c_size_okay is False:
                print('Found oversized cluster. Call kmeans again.')

            #  Count cluster number up
            nb_clusters += 1

    elif kmeans_method == 2:  # Split oversized clusters via kmeans

        print('\nRun kmeans on every oversized cluster (method 2)\n')

        #  Calc. min. possible number of clusters
        nb_clusters = math.ceil(len(city.nodelist_building)/max_nb_build)

        #  Perform initial clustering with kmeans
        cluster_dict = run_kmeans(city, nb_clusters)

        #  Check if at least one cluster is oversized
        c_size_okay = \
            check_if_cluster_is_oversized(cluster_dict, max_nb_build)

        #  While cluster remains oversized
        while c_size_okay is False:

            list_oversized = []

            print('Found oversized clusters')
            print('Number of oversized clusters: '
                  + str(len(list_oversized)))

            #  Loop over cluster_dict and find oversized clusters
            for key in cluster_dict:
                #  If cluster is oversized, add key to list_oversized
                if len(cluster_dict[key]) > max_nb_build:
                    list_oversized.append(key)

            #  Loop over all oversized clusters
            for key in list_oversized:

                #  Get nodelist
                node_list = cluster_dict[key]

                #  Extract subcity
                subcity = \
                    netop.get_build_str_subgraph(city, nodelist=node_list)

                #  Estimate desired number of clusters
                nb_clust = \
                    math.ceil(len(subcity.nodelist_building)/max_nb_build)

                #  Perform kmeans on
                subcity_dict = \
                    run_kmeans(city=subcity, nb_clusters=nb_clust)

                #  Erase old cluster and add new clusters to cluster_dict
                del cluster_dict[key]

                #  Append cluster_dict with new clusters
                for k in subcity_dict:
                    kn = copy.deepcopy(k)
                    #  Search for available key (kn) in cluster_dict
                    while kn in cluster_dict:
                        kn += 1
                    #  Add subcity cluster dict lists
                    cluster_dict[kn] = subcity_dict[k]

            #  Check if at least one cluster is oversized
            c_size_okay = \
            check_if_cluster_is_oversized(cluster_dict, max_nb_build)
            if c_size_okay:
                print('\nAll clusters are within limit max_nb_build.\n')

    else:

        raise ValueError('Unknown method ' + str(kmeans_method) +
                         ' chosen by user (kmeans_method)!')

    return cluster_dict

def run_clust_method_3(city, max_nb_build, search_range,
                       use_active_node=False):
    """
    Performs clustering method 3 (search for closest building nodes until
    cluster is full or no more building nodes exist within specific range)

    Parameters
    ----------
    city : object
        City object of pycity_calc
    max_nb_build : int
        Maximum number of building nodes per cluster
    search_range : float
        Max. distance between building nodes
    use_active_node : bool, optional
        Defines, if active node should (exclusively) be used as search node
        (default: False)
        True - Only search closest node from active search node
        False - Loop over all nodes within active cluster and look for closest
        node

    Returns
    -------
    cluster_dict : dict
        Dictionary with cluster number as key and lists of node id as values
    """

    assert max_nb_build >= 2
    assert search_range > 0

    print('\nStart building clustering by position (method 3)\n')

    cluster_dict = {}
    cluster_nb = 1

    #  Get start id
    start_id = get_id_min_x_pos(city)
    print('Start node id: ', start_id)

    #  Perform clustering
    #  #---------------------------------------------------------------------
    #  While remaining building list is not empty, go on with clustering
    if use_active_node:

        print('\n Use search method based on active node.\n')

        #  Init clustering
        #  #-----------------------------------------------------------------
        #  List holding all unprocessed building nodes (not added to cluster)
        remain_build_list = copy.deepcopy(city.nodelist_building)

        #  List holding all non-active buiding nodes (not used for search)
        remain_act_node_list = copy.deepcopy(city.nodelist_building)

        #  Remove start_id is first active id from list
        remain_act_node_list.remove(start_id)
        remain_build_list.remove(start_id)

        #  Init first cluster dict list
        cluster_list = [start_id]
        active_id = start_id

        #  Perform clustering
        #  #-----------------------------------------------------------------
        #  While remaining building list is not empty, go on with clustering
        while remain_build_list != []:

            #  Find nearest nodes of active_id node
            #  #-------------------------------------------------------------

            (min_dist, id_min) = \
                get_min_dist_and_id(city, nodelist=remain_build_list,
                                    search_id=active_id)

            print('Current closest node to active node ' + str(active_id) +
                  ' is node ' + str(id_min) + ' with distance ' +
                  str(round(min_dist, 2)))

            #  Check if minimum found distance is smaller than search_range
            #  If yes, id_min is possible cluster candidate
            if min_dist <= search_range:

                print('Distance is within search range.')

                #  Check if at least one place is left within active cluster
                if len(cluster_list) == max_nb_build:
                    #  If not, open new cluster and add building node

                    #  Add cluster_list to cluster_dict
                    cluster_dict[cluster_nb] = cluster_list
                    #  Count up cluster_nb
                    cluster_nb += 1
                    #  Initialize new cluster_list
                    cluster_list = []
                    print('Opened new cluster. Clustercount is '
                          + str(cluster_nb))

                    if id_min in remain_act_node_list:
                        #  If new cluster has been opened, set last node to new
                        #  active search node
                        active_id = id_min
                    else:
                        #  Find closest node to min_id node f
                        #  remain_act_node_list
                        for n in remain_act_node_list:
                            distance = netop.calc_node_distance(city,
                                                                node_1=id_min,
                                                            node_2=n)
                            if min_dist is None:
                                min_dist = distance
                                active_id = n
                            else:
                                if distance < min_dist:
                                    min_dist = distance
                                    #  Set new active_id
                                    active_id = n
                    #  Remove new active_id from active id list
                    remain_act_node_list.remove(active_id)

                #  Add id_min to cluster_list
                cluster_list.append(id_min)
                #  Erase id_min from remaining building list
                remain_build_list.remove(id_min)
                print('Added node ' + str(id_min) + ' to active cluster ' +
                      str(cluster_nb))

            else:  # No node left within search range next to active_id node
                #  Find new active search node
                #  If minimum found distance is not within range
                #  #---------------------------------------------------------

                print('Distance is NOT within search range.')
                print('Thus, find new active search node.')

                min_dist = None

                #  Find closest node to active node from remain_act_node_list
                for n in remain_act_node_list:
                    distance = netop.calc_node_distance(city, node_1=active_id,
                                                    node_2=n)
                    if min_dist is None:
                        min_dist = distance
                        id_min = n
                    else:
                        if distance < min_dist:
                            min_dist = distance
                            id_min = n

                #  Check closest search node is outside search_range
                if min_dist > search_range:
                    #  If outside search range, open new cluster
                    if cluster_list != []:
                        #  Add cluster_list to cluster_dict
                        cluster_dict[cluster_nb] = cluster_list
                        #  Count up cluster_nb
                        cluster_nb += 1
                        #  Initialize new cluster_list
                        cluster_list = []
                        print('Opened new cluster. Clustercount is '
                              + str(cluster_nb))

                #  Set id_min to new active search node id
                active_id = id_min
                print('New active search node id: ' + str(active_id))
                #  Remove new active_id node from remain_act_node_list
                remain_act_node_list.remove(active_id)


    else:

        print('\n Use search method based on whole cluster.\n')

        #  Init clustering
        #  #-----------------------------------------------------------------
        #  List holding all unprocessed building nodes (not added to cluster)
        remain_build_list = copy.deepcopy(city.nodelist_building)

        #  Remove start_id is first active id from list
        remain_build_list.remove(start_id)

        #  Init first cluster dict list
        cluster_list = [start_id]

        while remain_build_list != []:

            min_value = None

            #  Loop over all nodes in cluster_list
            for i in range(len(cluster_list)):
                curr_id = cluster_list[i]

                #  Get min distance
                (min_dist, min_id) = \
                    get_min_dist_and_id(city, nodelist=remain_build_list,
                                        search_id=curr_id)
                if min_value is None:
                    min_value = min_dist
                    closest_id = min_id
                if min_value > min_dist:
                    min_value = min_dist
                    closest_id = min_id

            print('Current closest node to active cluster is node '
                  + str(closest_id) + ' with distance ' +
                  str(round(min_value, 2)))

            #  Is min_value within search range?
            if min_value <= search_range:

                print('Value is within search range.')

                #  Is cluster already full?
                if len(cluster_list) == max_nb_build:
                    #  Open new cluster
                    #  Add cluster_list to cluster_dict
                    cluster_dict[cluster_nb] = cluster_list
                    #  Count up cluster_nb
                    cluster_nb += 1
                    #  Initialize new cluster_list
                    cluster_list = []
                    print('Opened new cluster. Clustercount is '
                          + str(cluster_nb))

                #  Add closest_id node to cluster
                cluster_list.append(closest_id)

                print('Add node ' + str(closest_id) + ' to cluster '
                      + str(cluster_nb))

                #  Remove closest_id from remain_build_list
                remain_build_list.remove(closest_id)

            else:  # min value is not within search range
                print('\nMin value is not within search range.' +
                      'Open new cluster.\n')
                #  Open new cluster
                #  Add cluster_list to cluster_dict
                cluster_dict[cluster_nb] = cluster_list
                #  Count up cluster_nb
                cluster_nb += 1
                #  Initialize new cluster_list
                cluster_list = []
                print('Opened new cluster. Clustercount is ' + str(cluster_nb))

                #  Add closest_id node to cluster
                cluster_list.append(closest_id)

                #  Remove closest_id from remain_build_list
                remain_build_list.remove(closest_id)

    #  If cluster_list is not empty, save it
    if cluster_list != []:
        cluster_dict[cluster_nb] = cluster_list

    print('\nFinished building position clustering (method 3).\n')
    print('\nCluster dictionary: ', cluster_dict)

    print('\nTotal number of clusters: ', cluster_nb)

    #  Check if all buildings have been processed
    nb_cluster_nodes = 0
    for key in cluster_dict:
        nb_cluster_nodes += len(cluster_dict[key])
    assert nb_cluster_nodes == len(city.nodelist_building), \
        ('Number of buildingnodes within cluster does not match building nb!')

    return cluster_dict


class StreetCluster(object):
    """
    PyCity_calc cluster class (clustering building object)

    Attributes
    ----------
    cluster_dict : dict
        Dictionary with key as cluster number and subgraph (object) as
        value
    __city : object
        City object of PyCity_calc
    """

    def __init__(self, max_nb_build, max_b_str, max_b_b):
        """
        Constructor of cluster object.

        Parameters
        ----------
        max_nb_build : int
            Maximum number of building nodes, which can be set per cluster
        max_b_str : float
            Maximum allowed distance between street and building
            (for adding building to cluster)
        max_b_b : float
            Maximum allowed distance between buildings
            (for adding building to cluster)
        """

        self.cluster_dict = {}  # Initialize empty results dict
        self.__city = None
        self.street = None

        #  Cluster parameters
        self._max_nb_build = max_nb_build
        self._max_b_str = max_b_str
        self._max_b_b = max_b_b

        #  Initialize last added and last processed building node id
        self.last_proc_build_id = None
        self.last_proc_str_id = None
        self.last_proc_build_id = None

        self.cluster_counter = 1
        #  Open cluster_dict
        self.cluster_dict = {}
        #  Open empty cluster  (list of buildings)
        self.cluster_list = []

    @property
    def city(self):
        return self.__city

    @city.setter
    def city(self, city):
        """
        Copies city_object to cluster object

        Parameters
        ----------
        city : object
            City object of pycity_calc
        """
        assert city._kind == 'citydistrict'
        self.__city = copy.deepcopy(city)

    def erase_str_nodes_without_connection(self):
        """
        Preprocessing method.
        Erases all street nodes, which have no connection to other nodes.

        Requires city object within cluster object.
        """
        if self.city is not None:
            for n in self.city.nodes():
                #  If node has attribute 'node_type'
                if 'node_type' in self.city.nodes[n]:
                    #  If node_type is 'street'
                    if self.city.nodes[n]['node_type'] == 'street':
                        #  If street_node has no edge connection
                        if nx.degree(self.city, n) == 0:
                            #  Erase node
                            self.city.remove_street_node(n)
                            print('Removed street node ', n)

    def gen_str_dicts(self):
        """
        Returns two dictionaries, holding information about building nodes
        close to each street node or edge.

        Returns
        -------
        str_node_dict : dict
            Dictionary with street_node_id (int) as key and list of building
            node ids as value
        str_edge_dict : dict
            Dictionary with street_edge_ids (tuple with node id 1 and 2)
            as key and list of building node ids as value.
            First entry in key tuple is always the smaller node id, e.g.
            (1001, 1003)
        """

        #  Initial dicts
        str_node_dict = {}
        str_edge_dict = {}

        #  Loop over all building nodes
        for i in range(len(self.city.nodelist_building)):
            node_id = self.city.nodelist_building[i]
            #  Check if entity is also of type building (otherwise, could
            #  be PV- or windfarm
            if self.city.nodes[node_id]['entity']._kind == 'building':
                if 'position' in self.city.nodes[node_id]:
                    build_pos = self.city.nodes[node_id]['position']
                    #  Find str node or edge closest to building node
                    closest_point, seg_point_1, seg_point_2 = \
                        netop.calc_graph_pos_closest_to(graph=self.street,
                                                        target_point=build_pos)

                    #  If closest point and segment end point are identical
                    #  Add only closest point
                    if (closest_point == seg_point_1
                        or closest_point == seg_point_2):

                        #  Find str_node_id corresponding to closest_point
                        str_node_id = \
                            netop.get_node_id_by_position(self.street,
                                                          position=closest_point)

                        #  Append list of nodes in node dict
                        str_node_dict.setdefault(str_node_id, []).append(
                                node_id)

                    else:  # Add segment/edge id

                        #  Find str_node_id corresponding to segment points
                        str_id_1 = \
                            netop.get_node_id_by_position(self.street,
                                                          position=seg_point_1)
                        str_id_2 = \
                            netop.get_node_id_by_position(self.street,
                                                          position=seg_point_2)

                        #  Generate edge key (tuple); smallest value first
                        if str_id_1 < str_id_2:
                            str_edge_id = (str_id_1, str_id_2)
                        elif str_id_1 > str_id_2:
                            str_edge_id = (str_id_2, str_id_1)
                        else:
                            raise AssertionError('Street node ids of street' +
                                                 ' edge cannot be idential!')

                        # Append list of nodes in edge dict
                        str_edge_dict.setdefault(str_edge_id, []).append(
                                node_id)

        return str_node_dict, str_edge_dict

    def preprocessing(self):
        """
        Preprocessing function:
        - Erase unnecessary street nodes (without street connection)
        - Generate street-building dictionaries (Closest position of
        building nodes to street positions)

        Returns
        -------
        str_node_dict : dict
            Dictionary with street_node_id (int) as key and list of building
            node ids as value
        str_edge_dict : dict
            Dictionary with street_edge_ids (tuple with node id 1 and 2)
            as key and list of building node ids as value.
            First entry in key tuple is always the smaller node id, e.g.
            (1001, 1003)
        """

        #  Execute preprocessing
        #  #-----------------------------------------------------------------
        #  Erase unnecessary street nodes (without edge connection)
        self.erase_str_nodes_without_connection()

        #  Extract street network as graph from city
        self.street = netop.get_street_subgraph(self.city)

        #  TODO: Add function to erase street edges, which are not close to any building

        # Generate str_seg_dict and str_node_dict
        str_node_dict, str_edge_dict = self.gen_str_dicts()

        return str_node_dict, str_edge_dict

    def init_clustering(self):
        """
        Method to initialize clustering by:
        -  Searching for start node
        -  Getting copy of remaining building and street node lists

        Returns
        -------
        str_start_node : int
            ID of start street node
        remain_build_list : list (of ints)
            List with building node ids
        remain_str_list : list (of ints)
            List with street node ids
        """
        #  TODO: Imp. function to find start node at edge position in graph

        #  Define start point
        str_start_node = self.set_str_start_point()
        st_point = self.street.nodes[str_start_node]['position']

        print('Start node:')
        print('Node id:', str_start_node)
        print('Coordinates:', st_point.x, st_point.y)

        #  Initialize list with remaining building node ids
        remain_build_list = copy.deepcopy(self.city.nodelist_building)

        #  Erase all node ids, which do not belong to building entity
        to_erase_list = []
        for node in remain_build_list:
            if self.city.nodes[node]['entity']._kind != 'building':
                to_erase_list.append(node)
        for node in to_erase_list:
            if node in remain_build_list:
                remain_build_list.remove(node)

        print('Remaining building node id list:')
        print(remain_build_list)
        print('Number of buildings')
        print(len(remain_build_list))

        #  Initialize list with remaining street node ids
        remain_str_list = copy.deepcopy(self.street.nodelist_street)

        return str_start_node, remain_build_list, remain_str_list

    def set_str_start_point(self):
        """
        Returns shapely Position of street node, which is used as starting
        point for cluster algorithm.

        Returns
        -------
        str_start_point : shapely Point
            shapely Point object (street node position)
        """

        str_start_point = None
        degree = 1

        while str_start_point == None:

            for node in self.street:
                if self.street.degree(node) == degree:
                    #  Set first found node as initial start point
                    str_start_point = node
                    break
                    #  TODO: Check if node is at 'outside' of graph

            #  Count degree up
            degree += 1

        return str_start_point

    def sort_nodes_at_str_edge(self, graph, str_start_node, curr_str_tuple,
                               b_node_list):
        """
        Method sorts building node numbers along street node.

        Parameters
        ----------
        graph : nx.Graph
            Networkx graph
        str_start_node : int
            Street start node id
        curr_str_tuple : tuple (of ints)
            Tuple holding node ids of street start and stop node

        b_node_list : list (of ints)
            List of building node ids closest to street edge

        Returns
        -------
        sort_b_node_list : list (of ints)
            List of building node ids closest to street edge (sorted along
            street)
        """

        #  Convert curr_str_tuple to list of segments
        str_start_x = graph.nodes[curr_str_tuple[0]]['position'].x
        str_start_y = graph.nodes[curr_str_tuple[0]]['position'].y
        str_stop_x = graph.nodes[curr_str_tuple[1]]['position'].x
        str_stop_y = graph.nodes[curr_str_tuple[1]]['position'].y
        list_seg = [Segment(Point(str_start_x, str_start_y),
                            Point(str_stop_x, str_stop_y))]

        int_point_list = []

        #  Calculate cutting point for every building node with street edge
        #  (perpendicular to street)
        for i in range(len(b_node_list)):
            node_pos = self.city.nodes[b_node_list[i]]['position']

            #  Calculate intersection point
            inter_point, seg_min_dist = \
                intersec.calc_segment_point_with_min_dist_to_point(list_seg,
                                                                   node_pos)
            int_point_list.append(inter_point)

        # Calculate distance between intersection point and str_start_point
        n_sec_dist_list = []
        for i in range(len(int_point_list)):
            str_pos = self.street.nodes[str_start_node]['position']
            intersec_pos = int_point_list[i]
            dist = netop.calc_point_distance(str_pos, intersec_pos)
            n_sec_dist_list.append(dist)

        # print('Building node list (before sorting)')
        # print(b_node_list)
        # print('Distance list')
        # print(n_sec_dist_list)

        #  Sort b_node_list by n_sec_dist_list
        n_sec_dist_list, sort_b_node_list = zip(*sorted(zip(n_sec_dist_list,
                                                            b_node_list)))

        #  Convert tuples into list
        sort_b_node_list = list(sort_b_node_list)

        # print('Building node list (after sorting)')
        # print(sort_b_node_list)
        # print('Distance list')
        # print(n_sec_dist_list)

        return sort_b_node_list

    def calc_dist_point_seg(self, graph, node_id, str_tuple):
        """
        Returns distance between point (node) and str segment (edge).
        Requires position parameter (shapely Point) for nodes.

        Parameters
        ----------
        graph : nx.Graph
            Networkx Graph object
        node_id : int
            ID of node
        str_tuple : tuple (of ints)
            2D tuple with node ids of street edge

        Returns
        -------
        distance : float
            Distance between node and edge/segment
        """

        target_point = graph.nodes[node_id]['position']
        seg_point_1 = graph.nodes[str_tuple[0]]['position']
        seg_point_2 = graph.nodes[str_tuple[1]]['position']
        list_seg = [Segment(seg_point_1, seg_point_2)]

        intersec_point, seg_min_dist = \
            intersec.calc_segment_point_with_min_dist_to_point(list_seg,
                                                               target_point)
        node_2_x = intersec_point.x
        node_2_y = intersec_point.y

        distance = math.sqrt((target_point.x - node_2_x) ** 2 +
                             (target_point.y - node_2_y) ** 2)

        return distance

    def proc_street_node(self, str_start_node, str_node_dict,
                         remain_build_list, use_dist_one_b,
                         use_act_cluster=False):
        """
        Process street node. Tries to add building nodes close to street node
        to open cluster.

        Parameters
        ----------
        str_start_node : int
            Street start node id
        str_node_dict : dict
            Dictionary with street_node_id (int) as key and list of building
            node ids as value
        remain_build_list : list (of ints)
            List with node ids of remaining/unprocessed buildings
        use_dist_one_b : bool
            Defines, if single building distance should be checked or
            distance to all existing building nodes in cluster
        use_act_cluster : bool, optional
            Defines if new building node should be added to active cluster or
            if every existing cluster should be tested, if its suitable for
            adding building
            (default: False)
            (False - Search every existing cluster and try to add)
            (True - Automatically add to active cluster)
        """

        print('Found str_node ' + str(str_start_node) +
              ' in str_node_dict')
        #  Get list of remaining building nodes (closest to str node)
        rem_node_list = copy.deepcopy(str_node_dict[str_start_node])

        #  Sort rem_node_list (of buildings) by distance to str_node
        sort_node_tuple = \
            netop.sort_node_list_by_distance(self.city, str_start_node,
                                             rem_node_list)
        #  Convert to list
        sort_node_list = list(sort_node_tuple)

        #  Loop over sorted building node list
        #  #---------------------------------------------------------------
        for n in sort_node_list:
            #  If distance between building and str is within range
            print('Current building node id ' + str(n) +
                  ' close to street node ' + str(str_start_node))

            #  Check that n does not have been processed
            #  #-----------------------------------------------------------
            #  FIXME: Search cluster_dict (instead of self.cluster_list)
            if n not in self.cluster_list and n in remain_build_list:
                #  If open cluster_list is empty, directly add node
                #  #-------------------------------------------------------
                #  FIXME: Only add if criteria are fulfilled
                if not self.cluster_list:
                    self.cluster_list.append(n)
                    # if use_act_cluster:
                    #     #  Directly add to open cluster
                    #     self.cluster_list.append(n)
                    # else:  # Try adding to existing clusters
                    #     #  TODO: Continue over here

                #  #-------------------------------------------------------
                else:  # Active cluster already hold building node ids
                    #  Try adding building node to open cluster
                    curr_dist = netop.calc_node_distance(self.city,
                                                         str_start_node, n)
                    #  #---------------------------------------------------
                    if use_dist_one_b:  # Only find single building in range
                        use_new_cluster = True
                        for clust_node in self.cluster_list:
                            next_b_dist = netop.calc_node_distance(self.city,
                                                                   n,
                                                                   clust_node)
                            #  If one building within cluster has allowed
                            #  distance to current processed building
                            #  Add building to cluster
                            if next_b_dist <= self._max_b_b:
                                use_new_cluster = False
                                break

                    # #---------------------------------------------------
                    else:  # All cluster buildings must be in range max_b_b
                        use_new_cluster = False
                        #  New candidate should not exceed max. distance
                        #  to all buildings within cluster
                        for clust_node in self.cluster_list:
                            next_b_dist = netop.calc_node_distance(self.city,
                                                                   n,
                                                                   clust_node)
                            #  If any connection exceeds max value
                            if next_b_dist > self._max_b_b:
                                use_new_cluster = True
                                break

                    # #---------------------------------------------------
                    # Current distance (building - street) within range?
                    if curr_dist > self._max_b_str:
                        #  If not in range, start new cluster
                        use_new_cluster = True

                    # If new cluster should be used
                    #  #---------------------------------------------------
                    if use_new_cluster:

                        #  If all clusters should be searched if they are
                        #  suitable for adding building node
                        #  #-----------------------------------------------
                        if use_act_cluster is False:
                            #  try adding node to existing cluster

                            #  Loop over existing clusters
                            for key in self.cluster_dict:
                                curr_cluster = self.cluster_dict[key]

                                #  Is cluster suitable for adding building n?
                                cluster_suitable = False  # Init value

                                #  Only analyze cluster when max cluster size
                                #  has not been reached
                                if len(curr_cluster) < max_nb_build:

                                    #  #-------------------------------------
                                    if use_dist_one_b:
                                        #  Criteria: Cluster must have at
                                        #  least single building close enough
                                        #  to building n

                                        #  Is cluster suitable for adding building n?
                                        cluster_suitable = False

                                        for c_node in curr_cluster:
                                            curr_dist = \
                                                netop.calc_node_distance(
                                                        self.city,
                                                        c_node, n)

                                            #  If one building within cluster
                                            #  has suitable distance to curr.
                                            #  building node --> suitable
                                            if curr_dist <= self._max_b_b:
                                                cluster_suitable = True
                                                break

                                    # #-------------------------------------
                                    else:  # All buildings must have max.
                                        #  distance to building node n
                                        cluster_suitable = True

                                        for c_node in curr_cluster:
                                            curr_dist = \
                                                netop.calc_node_distance(
                                                        self.city,
                                                        c_node, n)

                                            #  If one building within cluster
                                            #  has to high distance to curr.
                                            #  building --> Not suitable
                                            if curr_dist > self._max_b_b:
                                                cluster_suitable = False
                                                break

                                if cluster_suitable:
                                    curr_key = key
                                    break

                        # Directly add to new cluster
                        #  #-------------------------------------------------
                        else:  # Add to new cluster by setting
                            #  cluster_suitable to False --> open new cluster
                            # cluster_suitable = False
                            pass

                        # #-------------------------------------------------
                        if cluster_suitable:
                            #  Add building node n to cluster with curr_key
                            self.cluster_dict.setdefault(curr_key, []).append(
                                    n)
                        # #-------------------------------------------------
                        else:
                            #  If no existing cluster is close enough to build
                            #  node. Open new cluster and add value
                            self.open_new_cluster()
                            self.cluster_list.append(n)

                            # self.open_new_cluster()
                            # self.cluster_list.append(n)

                    # If all criteria are fulfilled, directly add node
                    #  to active cluster
                    #  #-----------------------------------------------------
                    else:  # Save to existing cluster
                        self.cluster_list.append(n)
                        #  Check if new cluster should be opened (max size)
                        if len(self.cluster_list) >= self._max_nb_build:
                            #  Open new cluster
                            self.open_new_cluster()

                remain_build_list.remove(n)
                print('Added building node ' + str(n) + ' to ' +
                      'cluster ' + str(self.cluster_counter) + '\n')

    def proc_street_edge(self, str_start_node, str_edge_dict,
                         remain_build_list, proc_str_list, use_dist_one_b):
        """
        Method processes street edge

        Parameters
        ----------
        str_start_node : int
            Street start node id
        str_edge_dict : dict
            Dictionary with street edge tuples as key and list of building
            node ids as value
        emain_build_list : list (of ints)
            List with node ids of remaining/unprocessed buildings
        proc_str_list : list (of ints)
            List of already processed street node ids
        use_dist_one_b : bool, optional
            Defines, if single building distance should be checked or
            distance to all existing building nodes in cluster
            (default: False - Only try to find single building in range
            to building)
        use_act_cluster : bool, optional
            Defines if new building node should be added to active cluster or
            if every existing cluster should be tested, if its suitable for
            adding building
            (default: False)
            (False - Search every existing cluster and try to add)
            (True - Automatically add to active cluster)
        """

        #  Get all neighbor street nodes of street start node
        list_of_neigh_nodes = self.street.neighbors(str_start_node)

        #  Generate edge tuples
        str_tuple_list = []
        #  While segments (of start node are left)
        #  Loop over neighbor nodes --> Generate street tuples
        #  #----------------------------------------------------------------
        for i in range(len(list_of_neigh_nodes)):
            curr_neighbor = list_of_neigh_nodes[i]
            # Check if segment has already been processed (start/stop street
            #  node has already been used)
            if curr_neighbor not in proc_str_list:
                #  Generate and add tuple (with node ids in ascending order)
                if curr_neighbor < str_start_node:
                    str_tuple = (curr_neighbor, str_start_node)
                else:
                    str_tuple = (str_start_node, curr_neighbor)
                str_tuple_list.append(str_tuple)

        print('str_tupel_list ' + str(str_tuple_list) + 'of str node ' +
              str(str_start_node))

        #  Process adjacent street edges
        #  #----------------------------------------------------------------
        #  Loop over all edges with str_start_node
        for i in range(len(str_tuple_list)):
            curr_str_tuple = str_tuple_list[i]
            if curr_str_tuple in str_edge_dict:

                print('Found str_edge ' + str(curr_str_tuple) +
                      ' in str_edge_dict')

                #  Get list of remaining building nodes (closest to str node)
                rem_node_list = copy.deepcopy(str_edge_dict[curr_str_tuple])

                print('Remaining building nodes close to edge:',
                      rem_node_list)

                #  Sort building node list (sort buildings along street axis
                rem_node_list = \
                    self.sort_nodes_at_str_edge(self.city, str_start_node,
                                                curr_str_tuple,
                                                rem_node_list)

                #  Loop over sorted building node list
                #  #---------------------------------------------------------
                for n in rem_node_list:
                    #  If distance between building and str is within range

                    print('Current building node id ' + str(n) +
                          ' close to street edge ' + str(curr_str_tuple))

                    #  Check that n does not have been processed
                    #  #-----------------------------------------------------
                    #  FIXME: Look in whole cluster_dict
                    if n not in self.cluster_list and n in remain_build_list:

                        #  If open cluster_list is empty, directly add node
                        #  #-------------------------------------------------
                        if not self.cluster_list:
                            self.cluster_list.append(n)

                        # #-------------------------------------------------
                        else:
                            curr_dist = \
                                self.calc_dist_point_seg(self.city, n,
                                                         curr_str_tuple)

                            #  #---------------------------------------------
                            if use_dist_one_b:  # Only find single building
                                #  in range
                                use_new_cluster = True
                                for clust_node in self.cluster_list:
                                    next_b_dist = \
                                        netop.calc_node_distance(self.city,
                                                                 n, clust_node)
                                    #  If one building within cluster has
                                    #  allowed  distance to current processed
                                    #  building. Add building to cluster
                                    if next_b_dist <= self._max_b_b:
                                        use_new_cluster = False
                                        break

                            # #----------------------------------------------
                            else:
                                use_new_cluster = False
                                #  New candidate should not exceed max. distance
                                #  to all buildings within cluster
                                for clust_node in self.cluster_list:
                                    next_b_dist = \
                                        netop.calc_node_distance(self.city, n,
                                                                 clust_node)
                                    #  If any connection exceeds max value
                                    if next_b_dist > self._max_b_b:
                                        use_new_cluster = True
                                        break

                            # #---------------------------------------------
                            if curr_dist > self._max_b_str:
                                #  If not in range, start new cluster
                                use_new_cluster = True

                            # If new cluster should be used
                            if use_new_cluster:
                                self.open_new_cluster()
                                self.cluster_list.append(n)
                            else:  # Save to existing cluster
                                self.cluster_list.append(n)
                                #  Check if new cluster should be opened
                                #  (max size)
                                if len(
                                        self.cluster_list) >= self._max_nb_build:
                                    #  Open new cluster
                                    self.open_new_cluster()

                        remain_build_list.remove(n)
                        print('Added building node ' + str(n) + ' to ' +
                              'cluster ' + str(self.cluster_counter) + '\n')

    def go_to_next_str_node(self, remain_str_list, str_start_node,
                            proc_str_list):
        """
        Method searches for new street node, that should be processed.

        Parameters
        ----------
        remain_str_list : list (of ints)
            List of remaining street node ids (unprocessed)
        str_start_node : int
            Current street node id (last processed node)
        proc_str_list : list (of ints)
            List of processed street node ids

        Returns
        -------
        new_str_node : int
            Chosen street node id (going to be processed next)
        """
        if len(remain_str_list) == 1:
            new_str_node = remain_str_list[0]
        elif len(remain_str_list) > 1:
            #  Search neigbors
            next_str_nodes = self.street.neighbors(str_start_node)
            found_new_start = False
            if len(next_str_nodes) > 0:
                for n in next_str_nodes:
                    #  If neighbor str node is in remaining str node list
                    if n in remain_str_list:
                        #  Set new street start node
                        new_str_node = n
                        found_new_start = True
                        print('Found new start node (neighbor)' +
                              ' of last str_start_node' + str(n))
                        break
            # If no new street start node has been found, continue search
            if found_new_start is not True:
                #  Search for neigbors of already processed nodes
                for n in proc_str_list:
                    next_str_nodes = self.street.neighbors(n)
                    if len(next_str_nodes) > 0:
                        for next in next_str_nodes:
                            if next in remain_str_list:
                                #  Set new street start node
                                new_str_node = next
                                found_new_start = True
                                print('Found new start node (neighbor' +
                                      ' of processed nodes ' + str(next))
                                break
                    if found_new_start:
                        break
            # If processed nodes do not have any unprocessed neighbors,
            #  select a random node within remain_str_list
            if found_new_start is not True:
                new_str_node = remain_str_list[random.
                    randint(0, len(remain_str_list) - 1)]
                print('Found new start node (random)'
                      + str(new_str_node))
        else:  # No street node left
            new_str_node = None

        return new_str_node

    def open_new_cluster(self):
        """
        Opens new cluster and saves old cluster to cluster_dict.
        """

        #  Add cluster list to cluster dict
        self.cluster_dict[self.cluster_counter] = self.cluster_list
        print('Cluster dict', self.cluster_dict)

        print('Cluster counter', self.cluster_counter)
        #  Count up cluster counter
        self.cluster_counter += 1
        print('Cluster counter', self.cluster_counter)

        #  Open new cluster (as empty list)
        self.cluster_list = []
        print('Open new cluster nb: ', self.cluster_counter)

    def main_perform_clustering(self, use_dist_one_b=False,
                                use_act_cluster=False):
        """
        Main function. Performs clustering.

        Parameters
        ----------
        use_dist_one_b : bool, optional
            Defines, if single building distance should be checked or
            distance to all existing building nodes in cluster
            (default: False - Only try to find single building in range
            to building)
        use_act_cluster : bool, optional
            Defines if new building node should be added to active cluster or
            if every existing cluster should be tested, if its suitable for
            adding building
            (default: False)
            (False - Search every existing cluster and try to add)
            (True - Automatically add to active cluster)

        Returns
        -------
        cluster_dict : dict
            Dictionary with cluster numbers (int) as keys and node ids (int)
            as values
        """

        #  Check if city object has been added (assert)
        assert self.city is not None

        proc_str_list = []

        # Execute preprocessing
        #  #-----------------------------------------------------------------
        #  Generate str_seg_dict and str_node_dict and erase unnecessary
        #  street nodes (without connection)
        print('\nExecute preprocessing\n')

        print('Search for closest street nodes and edges of every building.')
        print('Generate dictionaries (key: str; value: building node ids)')
        str_node_dict, str_edge_dict = self.preprocessing()

        print('Str node dict')
        print(str_node_dict)
        print('Str edge dict')
        print(str_edge_dict)

        print('\nFinished preprocessing\n')

        #  Initialize clustering
        #  #-----------------------------------------------------------------
        print('\nInitialize clustering\n')

        str_start_node, remain_build_list, remain_str_list = \
            self.init_clustering()

        #  Used for later plausibility check
        init_nb_buildings = len(remain_build_list)

        print('\nFinished initialization for clustering\n')

        print('Remain build list')
        print(remain_build_list)
        print('Remain str list')
        print(remain_str_list)

        print('\nStart clustering\n')

        #  Start clustering
        #  #-----------------------------------------------------------------
        #  While str nodes are unprocessed (remain_str_list is not empty)
        while len(remain_str_list) > 0:

            #  Search for str_start_node in str_node_dict
            #  #--------------------------------------------------------------
            print('\nProcess street node\n')

            if str_start_node in str_node_dict:
                #  Process building nodes close to street node

                self.proc_street_node(str_start_node, str_node_dict,
                                      remain_build_list, use_dist_one_b,
                                      use_act_cluster)

            print('self.cluster_dict', self.cluster_dict)
            print('self.cluster_list', self.cluster_list)

            # Loop over edges/segments of start_str_node
            #  #--------------------------------------------------------------
            print('\nProcess street node adjacent edge\n')

            self.proc_street_edge(str_start_node, str_edge_dict,
                                  remain_build_list, proc_str_list,
                                  use_dist_one_b)

            print('self.cluster_dict', self.cluster_dict)
            print('self.cluster_list', self.cluster_list)

            #  When start_str_node and all adjacent str edges have been
            #  processed, go to next node
            #  ---------------------------------------------------------------

            #  TODO: Add function to prefer next str node with low degree

            #  Save last processed str_node
            self.last_proc_str_id = str_start_node
            #  Erase str_start_node in remain_str_list
            print('Last processed street node: ', str_start_node)
            remain_str_list.remove(str_start_node)
            proc_str_list.append(str_start_node)
            print('Finished processing street node and edges of node ' +
                  str(str_start_node))
            print('remain_str_list', remain_str_list)

            print('\nGoing to next street node\n')

            str_start_node = self.go_to_next_str_node(remain_str_list,
                                                      str_start_node,
                                                      proc_str_list)

            #  When all building nodes are processed and nodes are left
            #  within cluster list, save clusterlist
            if len(remain_str_list) == 0 and len(self.cluster_list) > 0:
                self.open_new_cluster()

            print('self.cluster_dict', self.cluster_dict)
            print('self.cluster_list', self.cluster_list)

        print('\n')
        print('Cluster dictionary before postprocessing')
        print(self.cluster_dict)
        print('Number of clusters')
        print(len(self.cluster_dict))
        print('Remaining buildings')
        print(remain_build_list)

        #  Plausibility check
        sum_buildings = 0
        for key in self.cluster_dict:
            sum_buildings += len(self.cluster_dict[key])
        sum_buildings += len(remain_build_list)

        print('Number of buildings:')
        print(sum_buildings)
        print('\n')

        assert sum_buildings == init_nb_buildings

        return self.cluster_dict

def run_clustering(city, method, max_nb_build=7, max_b_str=10, max_b_b=20,
                   use_dist_one_b=True, use_act_cluster=False, nb_clusters=6,
                   search_range=25, use_active_node=False,
                   kmeans_method=0):
    """
    Runs clustering

    Parameters
    ----------
    city : object
        Pycity_calc city object
    method : int
        Cluster method
        0 - street clustering
        1 - k-means
        2 - meanshift
    max_nb_build : int, optional
        Maximum number of buildings per cluster (default: 7).
        Only relevant for method == 0 (street clustering) or method == 3
    max_b_str : float, optional
        Max. distance between street and building (per cluster)
        (default: 10)
        Only relevant for method == 0 (street clustering)
    max_b_b : float, optional
        Max. distance between buildings within cluster
        (default: 20)
        Only relevant for method == 0 (street clustering)
    use_dist_one_b : bool, optional
        Defines if inter building distance has only to be kept between two
        buildings or between all buildings (default: True)
        True - Only requires kept distance between two buildings
        False - Requires to keep max. distance between all buildings in cluster
        Only relevant for method == 0 (street clustering)
    use_act_cluster : bool, optional
        Defines, if current building should be added to active cluster or not
        (default: False)
        Only relevant for method == 0 (street clustering)
    nb_clusters : int, optional
        Total number of clusters
        (default: 6)
        Only relevant for method == 1 (kmeans)
    search_range : float, optional
        Search range for position clustering
        (default: 25)
        Only relevant for method == 3 (position clustering)
    use_active_node : bool, optional
        Defines, if active node should (exclusively) be used as search node
        (default: False)
        True - Only search closest node from active search node
        False - Loop over all nodes within active cluster and look for closest
        node
        Only relevant for method == 3 (position clustering)
    kmeans_method : int, optional
        Method to perform kmeans clustering
        (default: 0)
        0 - Single run of kmeans (neglect max_nb_build constraint)
        1 - Loop over kmeans with ascending number of clusters until
            max_nb_build is kept for every cluster (very slow method!)
        2 - Runs kmeans on every oversized cluster until cluster size is
            within range.

    Returns
    -------
    cluster_dict : dict
        Dictionary with cluster number as key and lists of node id as values
    """

    #  Start clustering
    if method == 0:  # Use street clustering

        #  Initialize cluster object
        cluster = StreetCluster(max_nb_build=max_nb_build, max_b_str=max_b_str,
                          max_b_b=max_b_b)

        #  Add copy of city to cluster object
        cluster.city = city

        cluster_dict = cluster.main_perform_clustering(use_dist_one_b=
                                                       use_dist_one_b,
                                                       use_act_cluster=
                                                       use_act_cluster)

    elif method == 1:  # Use kmeans

        cluster_dict = \
            run_kmeans_clustering(city, kmeans_method, nb_clusters=None)

    elif method == 2:  # Meanshift (http://scikit-learn.org/stable/index.html)
        cluster_dict = cex.meanshift_cluster(city, plot_results=False)

    elif method == 3:  # Positional clustering. Fill cluster with buildings in
        #  specific range until max. clustersize is reached
        cluster_dict = run_clust_method_3(city=city,
                                          max_nb_build=max_nb_build,
                                          search_range=search_range,
                                          use_active_node=use_active_node)

    else:
        raise ValueError('Unknown method ' + str(method) +'. Please ' +
                         'select method 0 (str), 1 (kmeans), 2 (meanshift)' +
                         ' or 3 (building position) for clustering!')

    return cluster_dict


def postprocess_results(city, cluster_dict, plot_city=False,
                        plot_clustering=True,
                        save_dict=True, path_to_save='cluster_dict.p'):
    """
    Perform postprocessing on clustering results (e.g. return cluster sizes,
    plot clusters)

    Parameters
    ----------
    city : object
        City object of pycity_calc
    cluster_dict : dict
        Dictionary with cluster number as key and lists of node id as values
    plot_city : bool, optional
        Defines, if city district should be plotted (default: False)
    plot_clustering : bool, optional
        Defines, if clusters should be plotted (default: True)
    save_dict : bool, optional
        Defines, if results dictionary should be saved (default: True)
    path_to_save : str, optional
        Path to save results dictionary to (default: 'cluster_dict.p')
    """

    print('##################### Results ###################################')
    print('\nClusters dictionary:')
    print(cluster_dict)

    print('\nTotal number of clusters: ', len(cluster_dict))

    #  Check if all buildings have been processed
    nb_cluster_nodes = 0
    for key in cluster_dict:
        nb_cluster_nodes += len(cluster_dict[key])
    assert nb_cluster_nodes == len(city.nodelist_building), \
        (
        'Number of buildingnodes within cluster does not match building nb!')

    max_size = 0
    #  Find largest cluster size
    for key in cluster_dict:
        if len(cluster_dict[key]) > max_size:
            max_size = len(cluster_dict[key])

    min_size = max_size + 1
    #  Find smallest cluster size
    for key in cluster_dict:
        if len(cluster_dict[key]) < min_size:
            min_size = len(cluster_dict[key])

    list_size = []
    for key in cluster_dict:
        list_size.append(len(cluster_dict[key]))


    def nb_clustersize(list_size, max_size):
        print()
        for i in range(1, max_size + 1):
            print('Number of clusters with size ' + str(i) + ': '
                  + str(list_size.count(i)))


    print('Minimum cluster size: ' + str(min_size) + ' building nodes.')
    print('Maximum cluster size: ' + str(max_size) + ' building nodes.')

    nb_clustersize(list_size, max_size)

    #  Save cluster_dict
    if save_dict:
        #  Save as pickle file
        pickle.dump(cluster_dict, open(path_to_save, mode='wb'))
        # #  Save as txt
        # text_file = open(txt_path, "w")
        # text_file.write("Cluster dictionary: %s" % str(cluster_dict))
        # text_file.close()


if __name__ == '__main__':

    this_path = os.path.dirname(os.path.abspath(__file__))

    #  User inputs
    #  #---------------------------------------------------------------------

    #  Select clustering method
    #  #-----------------------
    method = 3
    #  method = 0 - Use street clustering
    #  method = 1 - Use kmeans clustering
    #  method = 2 - Use meanshift clustering
    #  method = 3 - Positional clustering (distance only, until max. size)

    #  General input
    #  #-----------------------
    max_nb_build = 8  # Max. number of buildings per cluster
    #  Relevant for method 0 and 3 (as well as 1, if loop is active)

    #  Following values are only relevant for method 0
    #  #-----------------------
    max_b_str = 25  # Max. distance between street and building (per cluster)
    max_b_b = 25  # Max. distance between building within cluster
    use_dist_one_b = True  # True - Single building max
    use_act_cluster = False  # True - Add building to active cluster
    #  False - Search every existing cluster

    #  Following values are only relevant for method 1 (kmeans)
    #  #-----------------------
    #  Number of clusters
    nb_clusters = 25
    #  Run kmeans in loop, if cluster sizes are too big
    kmeans_method = 2
    #  0 - Single run of kmeans (neglect max_nb_build constraint)
    #  1 - Loop over kmeans with ascending number of clusters until
    #      max_nb_build is kept for every cluster (very slow method!)
    #  2 - Run kmeans once. If oversized clusters exist, rerun kmeans on them.

    #  Following vlaues are only relevant for method 3
    #  #-----------------------
    #  (building position clustering)
    #  Search range
    search_range = 50
    use_active_node = False
    # use_active_node : bool, optional
    #     Defines, if active node should (exclusively) be used as search node
    #     (default: False)
    #     True - Only search closest node from active search node
    #     False - Loop over all nodes within active cluster and look for
    #     closest node

    #  Further inputs
    #  #-----------------------
    #  Plot results:
    plot_city = False
    plot_clustering = True

    #  City pickle object filename
    #  (city object should include street graph)
    filename = 'test_city.p'
    #  Load pickle city file
    file_path = os.path.join(this_path, 'test_city_object', filename)

    #  Save cluster dict?
    save_dict = True

    #  Name of cluster dict pickle file
    c_dict_name = 'cluster_dict.p'
    # c_dict_txt = 'cluster_dict.txt'
    path_save_clust = os.path.join(this_path, 'output', c_dict_name)
    # txt_path = os.path.join(this_path, 'output', c_dict_txt)

    #  Name and path of log file
    log_name = 'input_log_clustering.txt'
    log_path = os.path.join(this_path, 'output', log_name)

    #  End of user input
    #  #---------------------------------------------------------------------

    #  Generate input parameter log file
    gen_cl_log(log_path=log_path, method=method, max_nb_build=max_nb_build,
               max_b_str=max_b_str, max_b_b=max_b_b,
               use_dist_one_b=use_dist_one_b, use_act_cluster=use_act_cluster,
               nb_clusters=nb_clusters, kmeans_method=kmeans_method,
               search_range=search_range, use_active_node=use_active_node,
               filename=filename, c_dict_name=c_dict_name,
               path_save_clust=path_save_clust)

    #  Load city object
    city = comcity.load_pickled_city_file(file_path)

    # #  Start clustering
    cluster_dict = run_clustering(city=city, method=method,
                                  max_nb_build=max_nb_build,
                                  max_b_str=max_b_str,
                                  max_b_b=max_b_b,
                                  use_dist_one_b=use_dist_one_b,
                                  use_act_cluster=use_act_cluster,
                                  nb_clusters=nb_clusters,
                                  search_range=search_range,
                                  use_active_node=use_active_node,
                                  kmeans_method=kmeans_method)

    #  Do postprocessing
    postprocess_results(city=city, cluster_dict=cluster_dict,
                        plot_city=plot_city,
                        plot_clustering=plot_clustering,
                        save_dict=save_dict,
                        path_to_save=path_save_clust)

    if plot_city:
        #  Plot city
        cityvis.plot_city_district(city, offset=10, plot_build_labels=True,
                                       equal_axis=True, plot_street=True,
                                       plot_str_labels=False)

    if plot_clustering:
        #  Plot clustering results
        cityvis.plot_cluster_results(city=city, cluster_dict=cluster_dict,
                                     plot_build_labels=False, use_bw=False,
                                     offset=6)
