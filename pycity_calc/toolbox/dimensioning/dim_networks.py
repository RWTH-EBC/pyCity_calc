#!/usr/bin/env python
# coding=utf-8
"""
Script with functions to dimension local heating and decentralized electrical
networks.

Currently, no support for separate heating_and_deg network dimensioning
(first lhn, then deg dimensioning; plus overlapping),
if street routing is used!
If you want to have a heating_and_deg network via street routing, use
add_lhn_to_city with street routing and heating_and_deg as network type.
"""

import os
import math
import pickle

import pycity_base.functions.process_city as prcity

import pycity_calc.visualization.city_visual as cityvis
import pycity_calc.toolbox.dimensioning.dim_functions as dimfunc
import pycity_calc.toolbox.networks.network_ops as netop


def estimate_u_value(d_i):
    """
    Estimate U-value (in W/mK) depending on inner pipe diameter d_i.
    Estimation based on values by: U-values: C. Beier, S. Bargel,
    C. Doetsch, LowEx in der Nah- und Fernwaerme. Abschlussbericht, 2010.

    Parameters
    ----------
    d_i : float
        Inner diameter of pipe in m

    Returns
    -------
    u_pipe : float
        U-value of pipe in W/m
    """

    u_pipe = 0.9264 * d_i ** 0.501

    return u_pipe


def calc_pipe_power_loss(length, u_pipe, temp_vl, temp_rl, temp_environment):
    """
    Calculate thermal loss power of heating pipe in Watt

    Parameters
    ----------
    length : float
        Total length of lhn grid in m
    u_pipe : float
        U-value of pipe in W/m
    temp_vl : float
        Inlet temperature of LHN in degree Celsius
    temp_rl : float
        Flowback temperature of LHN in degree Celsius
    temp_environment : float
        Environmental temperature in degree Celsius

    Returns
    -------
    q_dot_loss : float
        Thermal power loss of pipelines in Watt
    """

    #  Estimation of max lhn heat loss value in W
    q_dot_loss = u_pipe * length * (temp_vl + temp_rl - 2 * temp_environment)

    return q_dot_loss


def calc_diameter_of_lhn_network(max_th_power, length, temp_vl, temp_rl,
                                 temp_environment, c_p=4190, rho=1000, v_max=2,
                                 round_up=True):
    """
    Iterative function to estimate necessary inner pipe diameter of lhn pipes
    within network.

    Parameters
    ----------
    max_th_power : float
        Maximal thermal power in W (maximal power taken by final user from lhn
        grid)
    length : float
        Total length of lhn grid in m
    temp_vl : float
        Inlet temperature of LHN in degree Celsius
    temp_rl : float
        Flowback temperature of LHN in degree Celsius
    temp_environment : float
        Environmental temperature in degree Celsius
    c_p : float, optional
        Specific heat capacity of medium in J / (kg*K)
        (default: 4190 for water)
    rho : float, optional
        Density of medium in kg/m^3 (default: 1000 for water)
    v_max : float, optional
        Maximal allowed velocity within lhn system (in m/s)
        (default: 2)
    round_up : bool, optional
        Round up to next full cm value
        (default: True)
        False - Do not round up

    Returns
    -------
    d_i : float
        Inner pipe diameter for system dimensioning in meters
    """

    #  Assert functions
    assert temp_vl > temp_rl
    assert_list = [max_th_power, c_p, rho, length]
    for i in assert_list:
        assert i > 0, ('Input parameters of calc_diameter_of_lhn_network' +
                       ' [max_th_power, c_p, rho, length] must be larger' +
                       ' than zero!')

    # Iterative function to estimate inner diameter, depending on required
    #  thermal power (user + pipe losses)
    #  Start value for mass_flow
    m_point = max_th_power * 1.3 / ((temp_vl - temp_rl) * c_p)
    #  1.03 is used to account for lhn heating losses
    delta_e = 100  # Distance value in %

    #  Iterate while distance value is larger than 0.1 %
    while delta_e >= 0.001:
        m_point_1 = m_point

        #  Calculation of inner diameter (in m)
        d_i = round(2 * math.sqrt(m_point_1 / (math.pi * v_max * rho)), 5)

        #  Estimate u-value of pipe
        u_pipe = estimate_u_value(d_i)

        #  Estimation of max lhn heat loss value in W
        q_dot_loss = calc_pipe_power_loss(length=length, u_pipe=u_pipe,
                                          temp_vl=temp_vl, temp_rl=temp_rl,
                                          temp_environment=temp_environment)

        m_point = (max_th_power + q_dot_loss) / ((temp_vl - temp_rl) * c_p)

        #  Distance value between actual massflow and massflow
        #  (one timestep earlier)
        delta_e = (abs(m_point_1 - m_point)) / m_point_1

    #  Round up inner diameter value to
    if round_up:
        d_i = math.ceil(d_i * 100) / 100

    return d_i


def add_lhn_to_city(city, list_build_node_nb, temp_vl=90,
                    temp_rl=50, c_p=4186, rho=1000,
                    use_street_network=False, network_type='heating',
                    plot_stepwise=False):
    """
    Function adds local heating network (LHN) to city district.
    LHN can either be installed along minimum spanning tree
    (use_street_network = False)
    or along street network (use_street_network = True).

    Raise assertion error if one node within list_build_node_nb does not have
    a building entity or if one node is already connected to lhn and/or deg.

    Parameters
    ----------
    city : object
        City object of pycity_calc
    list_build_node_nb : list
        List of building nodes, which should be connected to LHN network
    temp_vl : float, optional
        Inlet flow temperature in degree Celsius
        (default: 90)
    temp_rl : float, optional
        Return flow temperature in degree Celsius
        (default: 50)
    c_p : float, optional
        Specific heat capacity of medium within lhn system in J/kgK
        (default: 4186 - for water)
    rho : float, optional
        Density of medium within lhn system in kg/m^3
        (default: 1000 - for water)
    use_street_network : bool, optional
        Defines if street network should be used to generate lhn system
        (default: False)
        False - Use minimum spanning tree to generate lhn system
        True - Only allow routing along street network
        If no street network exists within city object, minimium spanning tree
        is used
    network_type : str, optional
        Desired network (Default: 'heating')
        Options: 'heating' or 'heating_and_deg' (deg: decentralized, el. grid)
    plot_stepwise : bool, optional
        Plot stepwise graph search and lhn generation (default: False)
    """

    #  Assert functions
    assert temp_vl > temp_rl
    assert c_p > 0, 'c_p must be larger than zero!'
    assert rho > 0, 'rho must be larger than zero!'
    assert network_type in ['heating', 'heating_and_deg']

    #  Check if all node ids within list_build_node_nb belong to buildings
    for n in list_build_node_nb:
        assert n in city.get_list_build_entity_node_ids(), ('Node ' + str(n) +
                                                            ' does not have' +
                                                            ' a building ' +
                                                            'entity.')

    # Check if one building is already connected to lhn
    #  If existing heating connection is found, ValueError is raised
    for u in list_build_node_nb:
        for v in city.nodes():
            if city.has_edge(u, v):
                if 'network_type' in city.edge[u][v]:
                    if (city.edge[u][v]['network_type'] == 'heating' or
                                city.edge[u][v][
                                    'network_type'] == 'heating_and_deg'):
                        print('u', u)
                        print('v', v)
                        raise ValueError('Building within building list ' +
                                         'already holds lhn network!')

    print('Start process to add LHN to city\n')
    #  # Start with lhn processing
    #  #------------------------------------------------------------------

    #  Use street networks
    #  #------------------------------------------------------------------
    if use_street_network:  # Route along street networks

        #  Get minimum network spanning tree, based on street network
        (min_span_graph, list_new_nodes) = \
            netop.gen_min_span_tree_along_street(city=city,
                                                 nodelist=list_build_node_nb,
                                                 plot_graphs=plot_stepwise)

    # Use building minimum spanning tree
    #  #------------------------------------------------------------------
    else:  # Use minimum spanning tree between building nodes

        #  Generate subgraph with building of list, exclusively
        subcity = prcity.get_subcity(city=city, nodelist=list_build_node_nb)

        print('Subcity node ids:')
        print(subcity.nodes(data=False))
        print()

        print('Calculate minimum spanning tree.')
        #  Generate minimum spanning tree (with copy of subcity)
        min_span_graph = \
            netop.get_min_span_tree_for_x_y_positions(city=subcity,
                                                      nodelist=
                                                      list_build_node_nb)

    print('Minimum spanning tree edges:')
    print(min_span_graph.edges(data=False))
    print()

    #  Sum up weight to total length of network
    length = netop.sum_up_weights_of_edges(min_span_graph)

    print('Total network length in m:', math.ceil(length))
    print()

    #  Extract ground temperature of environment
    temp_ground = city.environment.temp_ground

    #  Get max thermal power of all buildings within list
    max_th_power = dimfunc.get_max_p_of_city(city_object=city,
                                             get_thermal=True,
                                             with_dhw=False,
                                             nodelist=list_build_node_nb)

    print('Max. thermal power in kW:', round(max_th_power / 1000, 1))
    print()

    d_i = calc_diameter_of_lhn_network(max_th_power=max_th_power,
                                       temp_vl=temp_vl,
                                       temp_rl=temp_rl,
                                       temp_environment=temp_ground,
                                       c_p=c_p, rho=rho,
                                       length=length,
                                       round_up=True)
    print('Chosen inner diameter of LHN pipes in m:', d_i)
    print()

    u_val = estimate_u_value(d_i=d_i)
    print('Estimated u-value of LHN pipe in W/m: ')
    print(round(u_val, 2))
    print()

    #  Use street networks
    #  #------------------------------------------------------------------
    if use_street_network:
        # create a list which saves information about created LHN nodes
        # hold created LHN nodes and the min_span_tree_node from which
        # it was created. This prevents multiple LHN node creation
        list_lhn_node=[[],[]]
        #  Loop over all edges of minimum spanning graph
        for u, v in min_span_graph.edges():
            # check if u and v are buildingnodes or if they have already been used to create an LHN node

            if u not in list_build_node_nb:
                #u is not a buildingnode
                if u not in list_lhn_node[0]:
                    # u was not set already as a LHN node
                    #  Get current position
                    pos_curr = min_span_graph.node[u]['position']
                    #  Generate new id
                    id1 = city.new_node_number()
                    list_lhn_node[0].append(u) # save the min_span_tree_node
                    list_lhn_node[1].append(id1) # save the new_lhn_node
                    #  Add new network node to city
                    city.add_node(id1, position=pos_curr,
                                  node_type=network_type)
                else:
                    # u was set already as a LHN node
                    # look up which id the LHN node has
                    for i in range(len(list_lhn_node[0])):
                        if list_lhn_node[0][i] == u:
                            index = i
                    id1 = list_lhn_node[1][index]
            else:
                # u is a buildingnode
                id1=u


            if v not in list_build_node_nb:
                # v is not a buildingnode
                if v not in list_lhn_node[0]:
                    # v was not set already as a LHN node
                    #  Get current position
                    pos_curr = min_span_graph.node[v]['position']
                    #  Generate new id
                    id2 = city.new_node_number()
                    list_lhn_node[0].append(v) # save the min_span_tree_node
                    list_lhn_node[1].append(id2) # save the new_lhn_node
                    #  Add new network node to city
                    city.add_node(id2, position=pos_curr,
                                  node_type=network_type)
                else:
                    # v was set already as a LHN node
                    # look up which id the LHN node has
                    for i in range(len(list_lhn_node[0])):
                        if list_lhn_node[0][i] == v:
                            index = i
                    id2 = list_lhn_node[1][index]
            else:
                # v is a buildingnode
                id2 = v

            city.add_edge(id1, id2, network_type=network_type,
                          temp_vl=temp_vl,
                          temp_rl=temp_rl, c_p=c_p, rho=rho, d_i=d_i)


    # Use building minimum spanning tree
    #  #------------------------------------------------------------------
    else:  # Use minimum spanning tree between building nodes

        #  Loop over minium spanning tree edges and add lhn to city
        for u, v, data in min_span_graph.edges(data=True):

            set_heat_deg = False

            #  If deg network already exists, replace it with heating_and_deg
            if city.has_edge(u, v):
                if 'network_type' in city.edge[u][v]:
                    if city.edge[u][v]['network_type'] == 'electricity':
                        print('Found existing el. network between node ' +
                              str(u) + ' and node ' + str(v) + '. Going '
                                                               'to replace is with type heating_and_deg.')
                        #  Add heating_and_deg edge to city
                        city.add_edge(u, v, network_type='heating_and_deg',
                                      temp_vl=temp_vl,
                                      temp_rl=temp_rl, c_p=c_p, rho=rho,
                                      d_i=d_i)
                        set_heat_deg = True

            # If there has not been a deg connection, add regular network edge
            if set_heat_deg is False:
                #  Add network edge to city
                city.add_edge(u, v, network_type=network_type, temp_vl=temp_vl,
                              temp_rl=temp_rl, c_p=c_p, rho=rho, d_i=d_i)


def add_deg_to_city(city, list_build_node_nb, use_street_network=False):
    """
    Function adds decentralized electrical grig to city district.
    DEG can either be installed along minimum spanning tree
    (use_street_network = False)
    or along street network (use_street_network = True).

    Raise assertion error if one node within list_build_node_nb does not have
    a building entity or if one node is already connected to deg and/or deg.

    Parameters
    ----------
    city : object
        City object of pycity_calc
    list_build_node_nb : list
        List of building nodes, which should be connected to DEG network
    use_street_network : bool, optional
        Defines if street network should be used to generate deg system
        (default: False)
        False - Use minimum spanning tree to generate deg system
        True - Only allow routing along street network
        If no street network exists within city object, minimium spanning tree
        is used
    """

    #  Check if all node ids within list_build_node_nb belong to buildings
    for n in list_build_node_nb:
        assert n in city.get_list_build_entity_node_ids(), ('Node ' + str(n) +
                                                            ' does not have' +
                                                            ' a building ' +
                                                            'entity.')

    print('Start process to add DEG to city\n')

    #  Use street networks
    #  #------------------------------------------------------------------
    if use_street_network:  # Route along street networks

        #  Get minimum network spanning tree, based on street network
        (min_span_graph, list_new_nodes) = \
            netop.gen_min_span_tree_along_street(city=city,
                                                 nodelist=list_build_node_nb,
                                                 plot_graphs=False)

    # Use building minimum spanning tree
    #  #------------------------------------------------------------------
    else:  # Use minimum spanning tree

        #  Generate subgraph with building of list, exclusively
        subcity = prcity.get_subcity(city=city, nodelist=list_build_node_nb)

        print('Subcity node ids:')
        print(subcity.nodes(data=False))
        print()

        print('Calculate minimum spanning tree.')
        #  Generate minimum spanning tree (with copy of subcity)
        min_span_graph = \
            netop.get_min_span_tree_for_x_y_positions(city=subcity,
                                                      nodelist=
                                                      list_build_node_nb)

    print('Minimum spanning tree edges:')
    print(min_span_graph.edges(data=False))
    print()

    #  Sum up weight to total length of network
    length = netop.sum_up_weights_of_edges(min_span_graph)

    print('Total network length in m:', math.ceil(length))
    print()

    #  Use street networks
    #  #------------------------------------------------------------------
    if use_street_network:
        # create a list which saves information about created DEG nodes
        # hold created DEG nodes and the min_span_tree_node from which
        # it was created. This prevents multiple DEG node creation
        list_deg_node = [[], []]
        #  Loop over all edges of minimum spanning graph
        for u, v in min_span_graph.edges():
            # check if u and v are buildingnodes or if they have already been used to create an deg node

            if u not in list_build_node_nb:
                # u is not a buildingnode
                if u not in list_deg_node[0]:
                    # u was not set already as a deg node
                    #  Get current position
                    pos_curr = min_span_graph.node[u]['position']
                    #  Generate new id
                    id1 = city.new_node_number()
                    list_deg_node[0].append(u)  # save the min_span_tree_node
                    list_deg_node[1].append(id1)  # save the new_deg_node
                    #  Add new network node to city
                    city.add_node(id1, position=pos_curr,
                                  node_type='electricity')
                else:
                    # u was set already as a deg node
                    # look up which id the deg node has
                    for i in range(len(list_deg_node[0])):
                        if list_deg_node[0][i] == u:
                            index = i
                    id1 = list_deg_node[1][index]
            else:
                # u is a buildingnode
                id1 = u

            if v not in list_build_node_nb:
                # v is not a buildingnode
                if v not in list_deg_node[0]:
                    # v was not set already as a deg node
                    #  Get current position
                    pos_curr = min_span_graph.node[v]['position']
                    #  Generate new id
                    id2 = city.new_node_number()
                    list_deg_node[0].append(v)  # save the min_span_tree_node
                    list_deg_node[1].append(id2)  # save the new_deg_node
                    #  Add new network node to city
                    city.add_node(id2, position=pos_curr,
                                  node_type='electricity')
                else:
                    # v was set already as a deg node
                    # look up which id the deg node has
                    for i in range(len(list_deg_node[0])):
                        if list_deg_node[0][i] == v:
                            index = i
                    id2 = list_deg_node[1][index]
            else:
                # v is a buildingnode
                id2 = v

            city.add_edge(id1, id2, network_type='electricity')

    # Use building minimum spanning tree
    #  #------------------------------------------------------------------
    else:
        #  Loop over minium spanning tree edges and add lhn to city
        for u, v in min_span_graph.edges():

            found_network = False

            if city.has_edge(u, v):

                if 'network_type' in city.edge[u][v]:

                    if city.edge[u][v]['network_type'] == 'heating':
                        print('Found existing heating network between node ' +
                              str(u) + ' and node ' + str(v) + '. Going '
                                                               'to replace is with type heating_and_deg.')
                        #  Add heating_and_deg edge to city
                        city.add_edge(u, v, network_type='heating_and_deg')
                        found_network = True

                    elif city.edge[u][v]['network_type'] == 'heating_and_deg':
                        print(
                            'Found existing heating_and_deg network between node'
                            + str(u) + ' and node ' + str(v) + '. Do nothing.')
                        found_network = True

            if found_network is False:
                #  Add lhn edge to city
                city.add_edge(u, v, network_type='electricity')


# TODO: Add function to erase complete network


if __name__ == '__main__':

    #  Path to pickle city file
    city_filename = 'city_clust_simple.p'
    this_path = os.path.dirname(os.path.abspath(__file__))
    pycity_calc_path = os.path.dirname(os.path.dirname(this_path))
    load_path = os.path.join(pycity_calc_path, 'toolbox', 'analyze',
                             'input', city_filename)

    use_street_network = True

    #  Load pickle city file
    city = pickle.load(open(load_path, mode='rb'))

    #  Extract list of all building nodes (should be connected to lhn)
    nodelist = city.nodelist_building

    #  Add heating network to city district
    add_lhn_to_city(city, list_build_node_nb=nodelist, temp_vl=90,
                    temp_rl=50, c_p=4186, rho=1000,
                    use_street_network=use_street_network,
                    network_type='heating',
                    plot_stepwise=False)

    #  Get infos about city graph
    print('City edge info:')
    print(city.edges(data=True))
    print('Edges without data:')
    print(city.edges(data=False))

    #  Plot city district
    cityvis.plot_city_district(city=city, plot_lhn=True, plot_deg=True)

    #  Add deg to city (on existing heating network)
    #  Results in heating_and_deg edge
    add_deg_to_city(city=city, list_build_node_nb=[1001, 1002],
                    use_street_network=use_street_network)

    #  Get infos about city graph
    print('City edge info:')
    print(city.edges(data=True))
    print('Edges without data:')
    print(city.edges(data=False))

    list_lhn = \
        netop.get_list_with_energy_net_con_node_ids(city=city,
                                                    network_type='heating',
                                                    build_node_only=False)

    print()
    print('LHN list: ', list_lhn)

    print('Length lhn list: ', len(list_lhn[0]))

    list_lhn = \
        netop.get_list_with_energy_net_con_node_ids(city=city,
                                                    network_type='heating',
                                                    build_node_only=True)

    print()
    print('LHN list (building nodes, only): ', list_lhn)
    #  Plot city district
    cityvis.plot_city_district(city=city, plot_lhn=True, plot_deg=True,
                               plot_build_labels=True, plot_heat_labels=True)

    # #  Plot multi city district
    # cityvis.plot_multi_city_district(city=city, main_save_path=this_path,
    #                                  equal_axis=False, fig_adjust='a4_half',
    #                                  dpi=300)

    list_heat_nodes = []
    for n in city.nodes():
        if 'node_type' in city.node[n]:
            if (city.node[n]['node_type'] == 'heating' or
                city.node[n]['node_type'] == 'heating_and_deg'):
                list_heat_nodes.append(n)

    print()
    print('List heating network nodes: ', list_heat_nodes)
    print('Number of heating nodes: ', len(list_heat_nodes))
