__author__ = 'jsc-tbe'
import math
import networkx as nx
import numpy as np
import warnings
# import sympy.geometry.point as point
import shapely.geometry.point as point

import sklearn.cluster as cl
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.colorbar
import sys
import pycity_calc.toolbox.networks.network_ops as netops
from scipy.spatial import distance, ConvexHull, Delaunay
#  Annotation: convex hull only works for clusters with more than 3 buildings
from operator import itemgetter
from copy import deepcopy

def centeroidnp(arr):
    length = arr.shape[0]
    sum_x = np.sum(arr[:, 0])
    sum_y = np.sum(arr[:, 1])

    return sum_x/length, sum_y/length

def distance_neighbor_ok(district, b10, b20, b15, b25, d_neighbor, mode):
    """
    Calculate distance between two building nodes (and nodes on street if mode='street') and check, if it's <d_neighbor.
    Parameters
    ----------
    district:   uesgraph
    b10:        building node of building 1
    b20:        building node of building 2
    b15:        node on street of building 1
    b25:        node on street of building 2
    d_neighbor: max. distance between building 1 und building 2
    mode:       'building' or 'street'

    Returns
    -------
    dst_ok:     boolean
    """

    dst_ok = False
    if mode == 'building':
        if (netops.calc_node_distance(district, b10, b20) < d_neighbor) and \
                (netops.calc_node_distance(district, b15, b25) < d_neighbor):
            dst_ok = True
    elif mode == 'street':
        if (netops.calc_node_distance(district, b15, b25) < d_neighbor):
            dst_ok = True

    return dst_ok

def grouping(district, buildings, d_neighbor, mode='street'):
    """
    Find groups of nodes (buildings) in district by looping over list of buildings and find neighbors.

    Parameters
    ----------
    district:   uesgraph
    buildings:  building_list
    d_neighbor: float

    Returns
    -------
    groups: list of groups containing list of buildings (building_list)
    """

    groups = []
    for b1 in range(len(buildings)):
        for b2 in range(b1 + 1, len(buildings)):
            # distance between building nodes and building nodes on street < d_neighbor
            # if (netops.calc_node_distance(quarter, buildings[b1][0], buildings[b2][0]) < d_neighbor) and \
            # if (netops.calc_node_distance(district, buildings[b1][5], buildings[b2][5]) < d_neighbor):

            if distance_neighbor_ok(district, buildings[b1][0], buildings[b2][0], buildings[b1][5], buildings[b2][5],
                                    d_neighbor, mode):

                # compare with existing groups
                new = True
                stop_b2 = False
                count_b1 = 0
                count_b2 = 0
                # both buildings are in one group or different groups-------------------------------------------------------
                for g in groups:
                    if buildings[b1] in g and buildings[b2] in g:   # both buildings are already in one group
                        stop_b2 = True
                        break
                    elif buildings[b1] in g:    # b1 is part of an existing group
                        count_b1 += 1
                        group1 = g
                    elif buildings[b2] in g:    # b2 is part of another existing group
                        count_b2 += 1
                        group2 = g
                if count_b1 == 1 and count_b2 == 1:     # both buildings are part of different groups
                    # connect the two groups
                    for i in group2:
                        group1.append(i)    # add buildings of group2 to group1
                    groups.remove(group2)   # delete old group2
                elif stop_b2:
                    continue    # go to next b2

                # one building is grouped or both buildings were not grouped------------------------------------------------
                else:
                    for g in groups:
                        if buildings[b1] in g:    # b1 already in group -> add b2
                            g.append(buildings[b2])
                            new = False
                            break
                        elif buildings[b2] in g:    # b2 already in group -> add b1
                            g.append(buildings[b1])
                            new = False
                            break

                    if new:     # both buildings were not grouped
                        groups.append([buildings[b1], buildings[b2]])   # add new neighbors

    # add residual buildings as single group
    for b in buildings:
        g = 0
        b_in_group = False
        while g != len(groups):
            if b in groups[g]:      # building in group
                b_in_group = True
                break
            else:       # building not in group
                b_in_group = False
            g += 1
        if not b_in_group:
            groups.append([b])  # add building as single group

    return groups

def show_demand_map(quarter, building_list, dem):
    # plot streetnetwork
    plt.rcParams['figure.figsize'] = 10, 10
    plt.axis('equal')
    # for building in quarter.nodelist_building:
    #     plt.text(quarter.node[building]['position'].x,
    #                              quarter.node[building]['position'].y + 0.1,
    #                              s=str(building),
    # #                             bbox=dict(facecolor='red', alpha=0.5),
    #                              horizontalalignment='center',
    #                              fontsize=8)
    for street in quarter.nodelist_street:
        draw = nx.draw_networkx_nodes(quarter,
                                      pos=quarter.positions,
                                      nodelist=[street],
                                      node_size=2 * 0.5,
                                      node_color='black',
                                      linewidths=None,
                                      alpha=0.2
                                      )
        if draw is not None:
            draw.set_edgecolor('black')
    for edge in quarter.edges():
        for node in edge:
            if 'street' in quarter.node[node]['node_type']:
                color = 'black'
                style = 'solid'
                alpha = 0.2
                break
        nx.draw_networkx_edges(quarter,
                                   pos=quarter.positions,
                                   edgelist=[edge],
                                   style=style,
                                   edge_color=[color],
                                   alpha=alpha)
    plt.tick_params(axis='both',
                            which='both',
                            bottom='on',
                            top='on',
                            labelbottom='on',
                            right='on',
                            left='on',
                            labelleft='on')
    plt.xlabel('x-Position [m]', horizontalalignment='center', labelpad=15)
    plt.ylabel('y-Position [m]', verticalalignment='center', labelpad=15)

    x = []
    y = []
    d = []
    for b in building_list:
        x.append(b[4].x)
        y.append(b[4].y)
        d.append(b[dem])

    # plot buildings, colour depending on thermal demand
    x = np.array(x)
    y = np.array(y)
    d = np.array(d)
    cmap = plt.cm.jet
    cmaplist = [cmap(i) for i in range(cmap.N)]
    cmap = cmap.from_list('Custom cmap', cmaplist, cmap.N)
    d_max = building_list[1][dem]
    d_min = building_list[len(building_list) - 1][dem]
    bounds = np.linspace(d_min, d_max, 11)
    norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
    plt.scatter(x, y, c=d, s=30, cmap='jet', norm=norm)
    ax2 = plt.axes([0.9, 0.1, 0.01, 0.8])
    #cbar.ax.set_xticklabels(['Low', 'Medium', 'High'])
    cb = mpl.colorbar.ColorbarBase(ax2, cmap=cmap, norm=norm, spacing='proportional', ticks=bounds, boundaries=bounds, format='%1i')
    cb.set_ticks(bounds)
    cb.set_ticklabels(['Low','','','','','','','','','', 'High'])
    ax2.set_ylabel('Annual Thermal Demand', size=12)
    plt.show()


# class BAclustering(object):
def get_clusters_street(district, street_type='real_simple', n_max=10, side_street_max=30, node_mode='building'):
    """
    Divides quarter into clusters focusing on streetnetwork. Each street forms own cluster, if the number
    of buildings is under n_building_max. Otherwise the street gets clustered by the k-means++-Algorithm.
    The resulting clusters are returned as uesgraphs.

    Step 1: Copy given CityDistrict as quarter and save building information in building_list.
            building_list:
                0. position: number of building node
                1. position: thermal annual demand
                2. posiiton: electrical annual demand
                3. position: total annual demand
                4. position: position of node (point object)
                5. position: number of building node on street
                6. position: edge belonging to building
                7. position: streetnumber belonging to building
    Step 2: Find complete streets: assign edges to street and form streetlist. Analyse intersections and possible
            short side streets.
            streetlist:
                0. position: number of street
                1. position: edge belonging to street
                2. position: nodes belonging to street
                3. position: position in building_list of building nodes belonging to street
    Step 3: For each building find nearest street and add nodes and edges to connect buildings among eachother.
            Information about nodes, and street are saved in building_list and streetlist.
    Step 4: Each street forms one cluster, if number of buildings in street < n_max. Else, run k-means++ to cluster
            the street. k is increased until all clusters are < n_max
    Step 5: Calculate convex hull for each cluster as border.

    Parameters
    ----------

    district : uesgraph
        Contains all nodes and edges of each type (e.g. 'street', 'building'...)
    street_type : str, optional
        'normal' : street = edge
        'real_simple' : simplified real streets, several edges form one street, interrupted by intersections with 4
                        or more edges
        (default: 'real_simple')
    n_max : int
        Max. number of buildings in one cluster
    side_street_max : float
        Defines the maximal length of a side street (to be added to
        main street). If too long, added as 'separate' street.
    node_mode : str
        'building' : use building nodes for k-means++
        'street' : use building nodes on street for k-menas++
                    (use projection of nodes on streets)

    Returns
    -------

    Clusters as dictionary: [clusternumber] = [nodelist of buildings in cluster]

    """
    # copy given CityDistrict
    quarter = deepcopy(district)

    # init lists
    clusterlist = []   # list of clusters
    node_number_list = quarter.nodelist_building   # list of building node numbers belonging to buildings in city
    building_list = []    # list of all building objects
    streetnodes = quarter.nodelist_street   # list of all street nodes in quarter
    street_graph = netops.get_street_subgraph(quarter)     # copy of street network of quarter
    streetedges = street_graph.edges()  # list of all street edges in quarter
    streetlist = []    # several streetedges form one street in streetlist
    streetnumber = 0

    netops.add_weights_to_edges(quarter)    # add distance to edges

    # commit building information
    for n in node_number_list:
        building_list.append([n,                                                            # node number
                              quarter.node[n]['entity'].get_annual_space_heat_demand(),     # annual th. demand
                              quarter.node[n]['entity'].get_annual_el_demand(),             # annual el. demand
                              quarter.node[n]['entity'].get_annual_space_heat_demand() \
                              + quarter.node[n]['entity'].get_annual_el_demand(),           # total demand (el./th.)
                              quarter.node[n]['position']])                                 # position of building

    if street_type == 'real_simple':
        #   #-----------------------------------------------------------------------------------------------------------
        print('Connect edges to real streets...\n')
        # add weights to egdes
        netops.add_weights_to_edges(quarter)

        # find intersectiondict
        intersectiondict = {}
        adj_dict = {}
        side_list = []
        side_edges = []
        start_list = []
        start_intersec = []
        start_intersec_edges = []
        triangle_intersec = []
        connect_dict = {}
        for n,nbrdict in quarter.adjacency_iter():  # search in adjacency_iter for intersections
            adj_dict[n] = nbrdict   # general adjacency dictionary {node: {neighbor: {}}}

            if len(nbrdict) > 3:    # more than 3 edges at one node
                intersectiondict[n] = nbrdict
                for n2 in nbrdict:
                    # add edge to start_intersec_edges, as edge to start or end a street
                    start_intersec.append(n)    # add node start/end street
                    if (n, n2) in streetedges:
                        start_intersec_edges.append((n, n2))     # add edge start/end street
                    else:
                        start_intersec_edges.append((n2, n))     # add edge start/end street

            elif len(nbrdict) == 3:   # 3 edges at one node
                intersectiondict[n] = nbrdict   # adjacency dictionary of intersection nodes
                triangle_intersec.append(n)    # list of intersection nodes (with 3 neighbors)

            elif len(nbrdict) == 2:     # 2 egdes at one node
                connect_dict[n] = nbrdict  # list of nodes that connect two edges

            elif len(nbrdict) == 1:    # start/end of street
                for n2 in nbrdict:
                    if netops.calc_node_distance(quarter, n, n2) <= side_street_max:
                        side_list.append(n2)
                        if (n, n2) in streetedges:
                            side_edges.append((n, n2))
                        else:
                            side_edges.append((n2, n))
                    else:
                        start_list.append(n)    # list of start nodes (with one neighbor)

        #   #-----------------------------------------------------------------------------------------------------------
        # search in triangle_intersec for edges that start/stop at triangle intersection and for connected edges
        for n in triangle_intersec:

            # set reference edge
            nd_one = n
            for i in adj_dict[nd_one]:
                nd_two = i
                break

            # reference edge as vector
            u = [quarter.node[nd_one]['position'].x - quarter.node[nd_two]['position'].x,
                 quarter.node[nd_one]['position'].y - quarter.node[nd_two]['position'].y]

            angles = {}
            sides = []
            for i in adj_dict[nd_one]:
                if i == nd_two:
                    pass
                else:
                    # edge at intersection as vector
                    v = [quarter.node[nd_one]['position'].x - quarter.node[i]['position'].x,
                         quarter.node[nd_one]['position'].y - quarter.node[i]['position'].y]
                    dot_prod = u[0] * v[0] + u[1] * v[1]    # dot product of u & v
                    lu = (u[0] ** 2 + u[1] ** 2) ** .5    # length of vector u
                    lv = (v[0] ** 2 + v[1] ** 2) ** .5    # length of vector v
                    angle = math.degrees(math.acos(dot_prod/lu/lv))   # angle between u & v

                    if 160 < angle < 200:   # edge possibly belongs to street
                        angles[angle] = i
                        no_match = False
                    else:
                        sides.append(i)
                        no_match = True

            if angles == {}:
                # check angle of other two edges
                u = [quarter.node[nd_one]['position'].x - quarter.node[sides[0]]['position'].x,
                     quarter.node[nd_one]['position'].y - quarter.node[sides[0]]['position'].y]
                v = [quarter.node[nd_one]['position'].x - quarter.node[sides[1]]['position'].x,
                     quarter.node[nd_one]['position'].y - quarter.node[sides[1]]['position'].y]
                dot_prod = u[0] * v[0] + u[1] * v[1]    # dot product of u & v
                lu = (u[0] ** 2 + u[1] ** 2) ** .5    # length of vector u
                lv = (v[0] ** 2 + v[1] ** 2) ** .5    # length of vector v
                angle = math.degrees(math.acos(dot_prod/lu/lv))   # angle between u & v

                if 160 < angle < 200:
                    # connection found
                    connect_dict[n] = {sides[0] : {}, sides[1] : {}}    # add node to connect_dict with nbrdict

                    if n in side_list:  # side street is listed
                        pass
                    else:   # search start_intersec_edge
                        for i in adj_dict[n]:
                            if i != sides[0] and i != sides[1]:
                                start_intersec.append(n)    # add node to start_intersec list
                                #add edge to start_intersec_edges
                                if (i, n) in streetedges:
                                    start_intersec_edges.append((i, n))
                                else:
                                    start_intersec_edges.append((n, i))
                else:
                    # no connection found
                    for i in sides:
                        if i in side_list:  # edge is small side street
                            pass
                        else:   # add edge to start_intersec_edges
                            start_intersec.append(n)  # edge starts/ends at intersection
                            if (n, i) in streetedges:
                                start_intersec_edges.append((n, i))
                            else:
                                start_intersec_edges.append((i, n))
            else:
                # one connection and one start-edge
                best_angle = min(angles, key=lambda x:abs (x-180))
                best_node = angles[best_angle]
                connect_dict[n] = {best_node : {}, nd_two : {}}    # add node to connect_dict with nbrdict
                start_intersec.append(n)   # add node to start_intersec, street strats or ends here
                # add edges to start_intersec_edges
                if (n, sides[0]) in streetedges:
                    start_intersec_edges.append((n, sides[0]))
                else:
                    start_intersec_edges.append((sides[0], n))

        # search in intersectiondict for small side streets
        for n in intersectiondict:
            if len(intersectiondict[n]) == 4:
                # check for side streets
                if sides.count(n) == 2:
                    # connect other edges
                    for n2 in intersectiondict[n]:
                        if ((n2, n) and (n, n2)) not in side_edges:
                            connect_dict[n] = {}
                            connect_dict[n][n2] = {}
                            if (n2, n) in start_intersec_edges:
                                start_intersec_edges.remove((n2, n))
                            else:
                                start_intersec_edges.remove((n, n2))
                            start_intersec.remove(n)

        #   #-----------------------------------------------------------------------------------------------------------
        # Find streets
        # TODO: fix problems with nodes in streetlist

        # first start node
        left_edges = deepcopy(streetedges)    # list with not used edges
        streetnumber = 0

        #streets starting & ending in start_intersec (one edge)
        temp_edges = []
        for e in set(start_intersec_edges):
            if start_intersec_edges.count(e) == 2:
                print('Started street ', streetnumber)
                streetlist.append([streetnumber, [e], [e[0], e[1]], []])    # add street to streetlist
                left_edges.remove(e)
                temp_edges.append(e)
                print(streetlist[streetnumber][2])
                print('Finished street ', streetnumber, '\n')
                streetnumber += 1
        # remove used edges and nodes
        for e in temp_edges:
            start_intersec_edges.remove(e)
            start_intersec.remove(e[0])
            start_intersec.remove(e[1])

        # street begins with node of start_list
        if len(start_list) > 0:
            current_node = start_list[0]
            start_list.remove(current_node)
            for e in streetedges:
                if current_node in e:
                    current_edge = e
            left_edges.remove(current_edge)
            streetlist.append([streetnumber, [current_edge], [current_node], []])   # add node and edge to new street
            print('Started street ', streetnumber)
            # update current node
            if current_edge[0] == current_node:
                current_node = current_edge[1]
            else:
                current_node = current_edge[0]

        # street begins with edge of list start_intersec_edges
        elif len(start_intersec_edges) > 0:
            current_edge = start_intersec_edges[0]
            start_intersec_edges.remove(current_edge)
            left_edges.remove(current_edge)
            if current_edge[0] in intersectiondict:
                current_node = current_edge[0]
            else:
                current_node = current_edge[1]
            streetlist.append([streetnumber, [current_edge], [current_node], []])   #add node and edge to new street
            print('Started street ', streetnumber)
            # update current node
            if current_edge[0] == start_list[0]:
                current_node = current_edge[1]
            else:
                current_node = current_edge[0]

        # no start node found
        else:
            warnings.warn('No start nodes found. Check street nodes!')

        while len(left_edges) > 0 or len(start_list) > 0 or len(start_intersec) > 0:

            #-----------------------------------------------------------------------------------------------------------
            # current_node belongs to side street
            if current_node in side_list:
                for e in side_edges:
                    if current_node in e:
                        streetlist[streetnumber][1].append(e)   # add edge of side street to current street
                        print('Added small side street.')
                        if e[0] == current_node:
                            streetlist[streetnumber][2].append(e[0])    # add node of side street to current street
                        else:
                            streetlist[streetnumber][2].append(e[1])    # add node of side street to current street
                        side_list.remove(current_node)
                        left_edges.remove(e)
                        break

            #-----------------------------------------------------------------------------------------------------------
            # street ends at current node (single end)
            elif len(start_list) > 0 and current_node in start_list:
                    streetlist[streetnumber][2].append(current_node)    # add last node to street
                    start_list.remove(current_node)
                    print(streetlist[streetnumber][2])
                    print('Finished street ', streetnumber, '\n')
                    streetnumber += 1   # next streetnumber

                    # new street begins with node of start_list
                    if len(start_list) > 0:
                        current_node = start_list[0]
                        for e in streetedges:
                            if current_node in e:
                                current_edge = e
                                break
                        left_edges.remove(current_edge)
                        streetlist.append([streetnumber, [current_edge], [current_node], []])
                        print('Started street ', streetnumber)
                        # update current node
                        if current_edge[0] == start_list[0]:
                            start_list.remove(current_node)
                            current_node = current_edge[1]
                        else:
                            start_list.remove(current_node)
                            current_node = current_edge[0]

                    # street begins with node of start_intersec
                    elif len(start_intersec) > 0:
                        current_node = start_intersec[0]
                        for e in start_intersec_edges:
                            if e[0] == current_node or e[1] == current_node:
                                current_edge = e
                                if e[0] in start_intersec:
                                    start_intersec.remove(current_node)
                                    streetlist.append([streetnumber, [e], [e[0], e[1]], []])
                                    current_node = e[1]
                                else:
                                    start_intersec.remove(current_node)
                                    streetlist.append([streetnumber, [e], [e[0], e[1]], []])
                                    current_node = e[0]
                                break
                        # for e in streetedges:
                        #     if current_node in e:
                        #         current_edge = e
                        #         break
                        left_edges.remove(current_edge)
                        # streetlist.append([streetnumber, [current_edge], [current_node], []])
                        print('Started street ', streetnumber)
                        # # update current node
                        # if current_edge[0] == start_list[0]:
                        #     current_node = current_edge[1]
                        # else:
                        #     current_node = current_edge[0]

                    # else:

            #-----------------------------------------------------------------------------------------------------------
            # street ends at current node (intersection)
            elif len(start_intersec) > 0 and current_node in start_intersec\
                    and len(start_intersec_edges) > 0 and current_edge in start_intersec_edges:
                streetlist[streetnumber][2].append(current_node)    # add last node to street
                start_intersec.remove(current_node)
                start_intersec_edges.remove(current_edge)
                print(streetlist[streetnumber][2])
                print('Finished street ', streetnumber, '\n')
                streetnumber += 1   # next streetnumber

                # new street begins with node of start_list
                if len(start_list) > 0:
                    current_node = start_list[0]
                    for e in streetedges:
                        if current_node in e:
                            current_edge = e
                            break
                    left_edges.remove(current_edge)
                    streetlist.append([streetnumber, [current_edge], [current_node], []])
                    print('Started street ', streetnumber)
                    # update current node
                    if current_edge[0] == start_list[0]:
                        start_list.remove(current_node)
                        current_node = current_edge[1]
                    else:
                        start_list.remove(current_node)
                        current_node = current_edge[0]

                # street begins with node of start_intersec
                elif len(start_intersec) > 0:
                    current_node = start_intersec[0]
                    start_intersec.remove(current_node)
                    for e in start_intersec_edges:
                        if e[0] == current_node or e[1] == current_node:
                            current_edge = e
                            if e[0] == current_node:
                                streetlist.append([streetnumber, [e], [e[0], e[1]], []])
                                current_node = e[1]
                            else:
                                streetlist.append([streetnumber, [e], [e[0], e[1]], []])
                                current_node = e[0]
                            break
                    left_edges.remove(current_edge)
                    print('Started street ', streetnumber)

            #-----------------------------------------------------------------------------------------------------------
            # street is not jet finished
            elif current_node in connect_dict:

                streetlist[streetnumber][2].append(current_node)
                for i in connect_dict[current_node]:
                    if i not in current_edge:
                        next_node = i   # next node of street
                        del connect_dict[current_node]  # remove used connection
                        if current_edge in start_intersec_edges:
                            start_intersec_edges.remove(current_edge)   # remove used edge
                        break

                no_edge = False
                for i in range(len(left_edges)):

                    if (current_node, next_node) == left_edges[i] or (next_node, current_node) == left_edges[i]:
                        current_edge = left_edges[i]    # next edge
                        streetlist[streetnumber][1].append(current_edge)    # add edge to street
                        streetlist[streetnumber][2].append(current_node)    # add node to street
                        current_node = next_node    # update current_node
                        left_edges.remove(current_edge)     # update left_edges
                        no_edge = False
                        break

                    else:
                        no_edge = True

                if no_edge:
                    streetlist[streetnumber][2].append(current_node)    # add last node to street
                    start_intersec.remove(current_node)     # remove used node
                    print(streetlist[streetnumber][2])
                    print('Finished street ', streetnumber, '\n')
                    streetnumber += 1   # next streetnumber

                    # new street begins with node of start_list
                    if len(start_list) > 0:
                        current_node = start_list[0]
                        start_list.remove(current_node)
                        for e in streetedges:
                            if current_node in e:
                                current_edge = e
                                break
                        left_edges.remove(current_edge)
                        streetlist.append([streetnumber, [current_edge], [current_node], []])
                        print('Started street ', streetnumber)
                        # update current node
                        if current_edge[0] == start_list[0]:
                            current_node = current_edge[1]
                        else:
                            current_node = current_edge[0]

                    # street begins with node of start_intersec
                    elif len(start_intersec) > 0:
                        for e in left_edges:
                            if e[0] in start_intersec or e[1] in start_intersec:
                                current_edge = e
                                if e[0] in start_intersec:
                                    streetlist.append([streetnumber, [e], [e[0], e[1]], []])
                                    current_node = e[1]
                                else:
                                    streetlist.append([streetnumber, [e], [e[0], e[1]], []])
                                    current_node = e[0]
                                break
                        for e in streetedges:
                            if current_node in e:
                                current_edge = e
                                break
                        left_edges.remove(current_edge)
                        streetlist.append([streetnumber, [current_edge], [current_node], []])
                        print('Started street ', streetnumber)
                        # update current node
                        if current_edge[0] == start_intersec[0]:
                            start_intersec.remove(current_node)
                            current_node = current_edge[1]
                        else:
                            start_intersec.remove(current_node)
                            current_node = current_edge[0]

    elif street_type == 'normal':
        #   #-------------------------------------------------------------------------------------------------------
        # find intersectiondict
        intersectiondict = {}
        adj_dict = {}
        start_list = []
        for n,nbrdict in quarter.adjacency_iter():  # search in adjacency_iter for intersections
            adj_dict[n] = nbrdict   # general adjacency dictionary {node: {neighbor: {}}}
            if len(nbrdict) >= 3:   # more than 3 edges at one node
                intersectiondict[n] = nbrdict   # adjacency dictionary of intersection nodes

        for i in streetedges:
            streetlist.append([streetnumber, [i], [i[0], i[1]], []])
            streetnumber += 1

    #   #-----------------------------------------------------------------------------------------------------------
    # Add building nodes on street
    print('------------------------------------\n')
    print('Find node on street for each building...')
    streets = []
    for i in range(len(streetedges)):  # every street gets a name
        streets.append(100 + i)  # name street with a letter

    x_start = {}
    y_start = {}
    x_end = {}
    y_end = {}
    a = 0
    for i in streets:
        x_start[i] = quarter.node[streetedges[a][0]]['position'].x     # get start x-position of node i
        y_start[i] = quarter.node[streetedges[a][0]]['position'].y     # get start y-position of node i
        x_end[i] = quarter.node[streetedges[a][1]]['position'].x       # get end x-position of node i
        y_end[i] = quarter.node[streetedges[a][1]]['position'].y       # get end y-position of node i
        a += 1

    # find minimal distance from building to street & add node on street
    xPos_min = {}
    yPos_min = {}
    dis = {}
    for i in range(len(building_list)):
        for n in streets:
            a = [x_start[n], y_start[n]]  # start point street
            u = [x_end[n] - x_start[n], y_end[n] - y_start[n]]  # direction vector street
            p = [building_list[i][4].x, building_list[i][4].y]  # position of building
            lam = (float((u[0] * (p[0] - a[0]) + u[1] * (p[1] - a[1])))
                   / float((u[0] ** 2 + u[1] ** 2)))
            if lam > 1:  # check boundary nodes, if optimum lays not in the range of street
                lam = 1  # set lam = 1 to check upper boundary nodes
            if lam < 0:
                lam = 0  # set lam = 0 to check lower boundary nodes
            xPos_min[n] = a[0] + lam * u[0]  # get x-position with minimum distance to building on street
            yPos_min[n] = a[1] + lam * u[1]  # get y-position with minimum distance to building on street
            dis[n] = math.sqrt(
                (xPos_min[n] - building_list[i][4].x) ** 2 +  # solve distance between street point and building
                (yPos_min[n] - building_list[i][4].y) ** 2)
        next_str = min(dis, key=dis.get)  # find street with minimum distance to building i
        nn = int(str(99)+str(i)+str(next_str))    # name for new node
        # TODO: implement type 'building_street' to streetnetwork/quarter
        quarter.add_node(nn, node_type='building_street',
                         position=point.Point(xPos_min[next_str], yPos_min[next_str]))   # add node on street
        building_list[i].append(nn)     # add node on street to building in building_list

        # save information in building_list and streetlist
        next_node1 = [x_start[next_str], y_start[next_str]]
        next_node2 = [x_end[next_str], y_end[next_str]]
        for no in streetnodes:  # search for nodes with positions of next_str
            if quarter.node[no]['position'] == point.Point(next_node1):
                nd_one = no
            elif quarter.node[no]['position'] == point.Point(next_node2):
                nd_two = no
        for ed in streetedges:  # search for edge with nodes of next_str
            if nd_one in ed and nd_two in ed:
                building_list[i].append(ed)  # add edge to building_list
                break
        for street in range(len(streetlist)):
            if street_type == 'real' or street_type == 'real_simple':
                if building_list[i][6] in streetlist[street][1]:
                    building_list[i].append(streetlist[street][0])   # add streetnumber to building in building_list
                    streetlist[street][3].append(i)    # add position in building_list to street in streetlist
            elif street_type == 'normal':
                if building_list[i][6] == streetlist[street][1][0]:
                    building_list[i].append(streetlist[street][0])   # add streetnumber to building in building_list
                    streetlist[street][3].append(i)    # add position in building_list to street in streetlist

        # add new edge between building node and building node on street
        quarter.add_edge(nn, building_list[i][0])

    # add edges between building nodes on street for buildings of one street
    for street in streetlist:
        if len(street[3]) > 0:
            x_start = {}
            y_start = {}
            x_end = {}
            y_end = {}
            for i in street[1]:
                x_start[i] = quarter.node[i[0]]['position'].x     # get start x-position of node i
                y_start[i] = quarter.node[i[0]]['position'].y     # get start y-position of node i
                x_end[i] = quarter.node[i[1]]['position'].x       # get end x-position of node i
                y_end[i] = quarter.node[i[1]]['position'].y       # get end y-position of node i

            # find distance from building node on street to start node of edge
            for e in street[1]:
                par = {}
                for n in street[3]:
                    a = [x_start[e], y_start[e]]  # start point edge
                    u = [x_end[e] - x_start[e], y_end[e] - y_start[e]]  # direction vector edge
                    p = [quarter.node[building_list[n][5]]['position'].x, quarter.node[building_list[n][5]]['position'].y]  # position of building node on street
                    lam1 = float((p[0] - a[0]) / u[0])
                    lam2 = float((p[1] - a[1]) / u[1])
                    if lam1 != lam2:    # node not on edge
                        continue
                    elif 0 <= lam1 <= 1:  # check, if node lays on edge
                        par[lam1] = building_list[n][5]  # parameter
                par_list = par.keys()
                par_list = sorted(par_list)   # sorted list of keys of par
                if len(par) == 1:
                    quarter.add_edge(e[0], par[min(par_list)])  # edge from start node to first building
                    quarter.add_edge(e[1], par[max(par_list)])  # edge from last building to end node
                elif len(par) > 1:
                    quarter.add_edge(e[0], par[min(par_list)])  # edge from start node to first building
                    for p in range(len(par_list) - 1):
                        quarter.add_edge(par[par_list[p]], par[par_list[p+1]])
                    quarter.add_edge(e[1], par[max(par_list)])  # edge from last building to end node

    print('Added all nodes.\n')

    #-------------------------------------------------------------------------------------------------------------------
    # Clustering via street
    print('------------------------------------\n')
    print('Clustering via street...\n')
    c = 0
    for street in streetlist:
        if len(street) >= 4:
            if len(street[3]) <= (n_max):  # number of buildings in street <= maximal number -> one cluster
                clusterlist.append([])  # new empty cluster
                for building in street[3]:  # every building in street
                    clusterlist[c].append(building_list[building])  # handover building to cluster
                c += 1
            else:   # number of buildings in street > maximal number -> several clusters
                print('k-means++ for street:' + str(street[0]))
                n_calc_min = int(round(float(len(street[3]) / n_max) + 0.5, 0))   # min number of clusters
                n_calc_max = int(round(float(len(street[3]) / (n_max / 3)) + 0.5, 0))   # max number of clusters
                #n_calc_max = len(street[3])
                print('with k in [', n_calc_min, ', ', n_calc_max, ']')
                # prepare data for k-means-clustering
                x = []
                for i in range(len(street[3])):
                    if node_mode == 'street':
                        x.append([quarter.node[building_list[street[3][i]][5]]['position'].x,
                                  quarter.node[building_list[street[3][i]][5]]['position'].y])
                    else:
                        x.append([building_list[street[3][i]][4].x,
                                  building_list[street[3][i]][4].y])
                x = np.array(x)

                checkdict = {}  # temporary clusterlists
                for n_cluster in range(n_calc_min, n_calc_max):
                    # k-means++-clustering
                    centers, labels, inertia = cl.k_means(x, n_clusters=n_cluster, init='k-means++',
                                                          precompute_distances='auto', n_init=10, max_iter=100)
                    store_result = []
                    for i in range(len(street[3])):     # store results/assign label (cluster) to edges of street
                        store_result.append([labels[i], street[3][i]])

                    # handover clusters/buildings to clusterlist
                    store_result = sorted(store_result, key=itemgetter(0))      # sort by label

                    ch = 0          # cluster counter
                    checkdict[n_cluster] = []
                    checkdict[n_cluster].append([])  # new empty cluster
                    checkdict[n_cluster][ch].append(building_list[store_result[0][1]])     # first building in cluster
                    old_label = store_result[0][0]  # save used label (cluster)
                    for i in range(1, len(street[3])):
                        if store_result[i][0] == old_label:   # check if cluster exist
                            checkdict[n_cluster][ch].append(building_list[store_result[i][1]])    # handover building to cluster
                        else:
                            ch += 1    # new cluster
                            checkdict[n_cluster].append([])  # new empty cluster
                            checkdict[n_cluster][ch].append(building_list[store_result[i][1]])    # handover building to cluster
                            old_label = store_result[i][0]    # save current label (cluster)
                # find best clustering with n_cluster_best clusters
                for n_cluster in checkdict:
                    for cluster in checkdict[n_cluster]:
                        if len(cluster) <= n_max:     # number of bildings < n_max
                            size_ok = True
                        else:
                            size_ok = False
                            break
                    if size_ok:
                        best_clusters = checkdict[n_cluster]
                        break
                try:
                    for cluster in best_clusters:
                        clusterlist.append([])
                        clusterlist[c] = cluster   # add cluster to clusterlist
                        c += 1
                except:
                    warnings.warn('Min. one cluster has more buildings than n_max!')

    #-------------------------------------------------------------------------------------------------------------------
    # convexhull defines borders of cluster
    print('\nCreate convex hulls...\n')

    plt.rcParams['figure.figsize'] = 10, 15
    for c in clusterlist:
        if len(c) > 1:
            bpoints = []
            points = []
            for b in c:
                bpoints.append([b[4].x, b[4].y])   # position of building node
                points.append([b[4].x, b[4].y])   # position of buildings
                points.append([quarter.node[b[5]]['position'].x, quarter.node[b[5]]['position'].y])
            bpoints = np.array(bpoints)
            points = np.array(points)
            hull = ConvexHull(points)   # calc convexhull of cluster
            vert = points[hull.vertices]
            vert = np.append(vert, [vert[0]], axis=0)

            plt.plot(vert[:, 0], vert[:, 1], 'r--', lw=2)
            plt.plot(bpoints[:,0], bpoints[:,1], 'o')
            plt.text(quarter.node[c[0][0]]['position'].x,
                                 quarter.node[c[0][0]]['position'].y + 0.8,
                                 s=str(clusterlist.index(c)),
                                 horizontalalignment='center',
                                 fontsize=12)
        else:
            bpoints = []
            points = []
            for b in c:
                bpoints.append([b[4].x, b[4].y])
            bpoints = np.array(bpoints)
            plt.plot(bpoints[:, 0], bpoints[:, 1], 'o')
            plt.plot(c[0][4].x, c[0][4].y, 's')
            plt.text(quarter.node[c[0][0]]['position'].x,
                                 quarter.node[c[0][0]]['position'].y + 0.8,
                                 s=str(clusterlist.index(c)),
                                 horizontalalignment='center',
                                 fontsize=12)

    # plot streetnetwork
    plt.axis('equal')
    for street in quarter.nodelist_street:
        draw = nx.draw_networkx_nodes(quarter,
                                      pos=quarter.positions,
                                      nodelist=[street],
                                      node_size=2 * 0.5,
                                      node_color='black',
                                      linewidths=None,
                                      alpha=0.2
                                      )
        if draw is not None:
            draw.set_edgecolor('black')
    for edge in quarter.edges():
        for node in edge:
            if 'street' in quarter.node[node]['node_type']:
                color = 'black'
                style = 'solid'
                alpha = 0.2
                break
        nx.draw_networkx_edges(quarter,
                                   pos=quarter.positions,
                                   edgelist=[edge],
                                   style=style,
                                   edge_color=[color],
                                   alpha=alpha)
    plt.tick_params(axis='both',
                            which='both',
                            bottom='on',
                            top='on',
                            labelbottom='on',
                            right='on',
                            left='on',
                            labelleft='on')

    plt.xlabel('x-Position [m]', horizontalalignment='center', labelpad=15)
    plt.ylabel('y-Position [m]', verticalalignment='center', labelpad=15)

    plt.show()

    #-------------------------------------------------------------------------------------------------------------------
    count = 0
    for c in clusterlist:
        print('Cluster ', clusterlist.index(c))
        for b in c:
            print(b[0])
            count += 1
    print('Number of clusters: ', len(clusterlist))
    print('Number of buildings: ', count)

    #-------------------------------------------------------------------------------------------------------------------
    # handover clusters
    clusters = {}
    for c in range(len(clusterlist)):
        buildings = []
        for b in range(len(clusterlist[c])):
            buildings.append(clusterlist[c][b][0])
        clusters[c] = buildings
    print('\nFinished clustering!')

    return clusters

def get_clusters_demand(district, n_max=10, demand_mode='thermal', dst_center_min=100, d_neighbor=10,
                        assignment='group', grouping_mode='street', recentering=True, show_demand=False):
    """
    Clusters the urban quarter by focusing on buildings with high demand.

    Step 1: Copy given CityDistrict as quarter and save building information in building_list.
            building_list:
                0. position: number of building node
                1. position: thermal annual demand
                2. posiiton: electrical annual demand
                3. position: total annual demand
                4. position: position of node (point object)
                5. position: number of building node on street
                6. position: edge belonging to building
                7. position: streetnumber belonging to building
    Step 2: For each building find nearest street and add nodes and edges to connect buildings among eachother.
            Information about nodes, and street are safed in building_list and streetlist.
            streetlist:
                0. position: number of street
                1. position: edge belonging to street
                2. position: nodes belonging to street
                3. position: building nodes belonging to street
    Step 2: Sort building_list by annual demand depending on demand_mode
    Step 3: Search groups of neighbors depending on
            grouping_mode:
                'street':   distance betweeen building nodes on street (independant of street side) must be <d_neighbor
                'building': distance between building nodes and also building nodes on street must be <d_neighbor
    Step 4: Find centers by taking buildings with high demand and min. distance (dst_center_min) among all centers.
            (Decrease dst_center_min, if not all centers are found)
    Step 5: Depending on chosen kind of assignment, assign each building/group to nearest clustercenter. If cluster is
            to big, it is split. Buildings/groups furthest from center are removed and build own cluster or buildings
            with lowest energetic factor (demand/distance_to_center) are removed.
            Before splitting clustercenter is updated, highest demand in cluster, if recentering=True.
    Step 6: Calculate convex hull for each cluster as border.

    Parameters
    ----------

    district : uesgraph
        Contains all nodes and edges of each type (e.g. 'street', 'building'...)
    demand_mode : str
        'thermal' : sorted by annual thermal demand
        'electrical' : sorted by annual electrical demand
        'total' : sorted by total annual demand (thermal + electrical)
    dst_center_min : float
        Minimal distance between clustercenters
    d_neighbor : float
        maximal distance between neighbor buildings of one group
        (preclustering)
    assignment : str
        Building assignment and correction (for clusters).
        If clustersize is too big, remove building/group from cluster
        'building' : buildings are assigned to nearest clustercenter
        'group' : groups are assigned to nearest clustercenter (dependign on main building in group/highest demand)
        'group_energetic' : like group, if cluster too big, buildings with low
                            energetic factor (f_En=demand/distance_to_center) are split off.
    grouping_mode : str, optional
        How to group nodes within preclustering
        'building' : use building nodes for k-means++
        'street' : use building nodes on street for k-menas++
                    (use projection of nodes on streets)
    recentering : bool, optional
        If new center should be chosen, defines which center is chosen:
        True - select building with highest demand (within cluster)
        False - Keep center, which has been selected, first.
        (default: True)
    show_demand : boolean
        show demand map of district, coloured building nodes depending on thermal demand

    Returns
    -------
    Clusters as dictionary: [clusternumber] = [nodelist of buildings in cluster]
    """

    # copy CityDistrict
    quarter = deepcopy(district)

    # init lists
    clusterlist = []   # list of clusters
    n_buildings = len(quarter.nodelist_building)    # number of buildings in city
    node_number_list = quarter.nodelist_building   # list of building node numbers belonging to buildings in city
    building_list = []    # list of all building-objects

    # create building_list with information about:
    # number, annual thermal demand, annual electrical demand, total annual demand, position
    for n in node_number_list:
        building_list.append([n, quarter.node[n]['entity'].get_annual_space_heat_demand(),
                              quarter.node[n]['entity'].get_annual_el_demand(),
                              quarter.node[n]['entity'].get_annual_space_heat_demand() \
                              + quarter.node[n]['entity'].get_annual_el_demand(), # total demand (el./th.)
                              quarter.node[n]['position']])   # position of building

    # combine quarter with streetnetwork
    streetnodes = quarter.nodelist_street  # list of all nodes in streetnetwork
    streetedges = quarter.edges()  # list of all edges in streetnetwork
    streetlist = []    # several streetedges form one street in streetlist
    streetnumber = 0

    for i in streetedges:
        streetlist.append([streetnumber, i, [i[0], i[1]], []])
        streetnumber += 1

    #   #---------------------------------------------------------------------------------------------------------------
    # Add building nodes on street (code by Stefan)
    # Find shortest connection from building to an edge and add nodes and edge to quarter
    streets = []
    for i in range(len(streetedges)):  # every street gets a name
        streets.append(100 + i)  # name street with a letter

    x_start = {}
    y_start = {}
    x_end = {}
    y_end = {}
    a = 0
    for i in streets:
        x_start[i] = quarter.node[streetedges[a][0]]['position'].x     # get start x-position of node i
        y_start[i] = quarter.node[streetedges[a][0]]['position'].y     # get start y-position of node i
        x_end[i] = quarter.node[streetedges[a][1]]['position'].x       # get end x-position of node i
        y_end[i] = quarter.node[streetedges[a][1]]['position'].y       # get end y-position of node i
        a += 1

    # find minimal distance from building to street
    xPos_min = {}
    yPos_min = {}
    dis = {}
    nodelist_building_street = []
    for i in range(len(building_list)):
        for n in streets:
            a = [x_start[n], y_start[n]]  # start point street
            u = [x_end[n] - x_start[n], y_end[n] - y_start[n]]  # direction vector street
            p = [building_list[i][4].x, building_list[i][4].y]  # position of building
            lam = (float((u[0] * (p[0] - a[0]) + u[1] * (p[1] - a[1])))
                   / float((u[0] ** 2 + u[1] ** 2)))
            if lam > 1:  # check boundary nodes, if optimum lays not in the range of street
                lam = 1  # set lam = 1 to check upper boundary nodes
            if lam < 0:
                lam = 0  # set lam = 0 to check lower boundary nodes
            xPos_min[n] = a[0] + lam * u[0]  # get x-position with minimum distance to building on street
            yPos_min[n] = a[1] + lam * u[1]  # get y-position with minimum distance to building on street
            dis[n] = math.sqrt(
                (xPos_min[n] - building_list[i][4].x) ** 2 +  # solve distance between street point and building
                (yPos_min[n] - building_list[i][4].y) ** 2)
        next_str = min(dis, key=dis.get)  # find street with minimum distance to building i
        nn = int(str(99)+str(i)+str(next_str))    # name for new node
        nodelist_building_street.append(nn)
        # TODO: implement type 'building_street' in quarter
        # add node on street
        quarter.add_node(nn, node_type='building_street',
                         position=point.Point(xPos_min[next_str], yPos_min[next_str]))

        # save information in building_list and streetlist
        building_list[i].append(nn)     # add building node on street to building in building_list
        next_node1 = [x_start[next_str], y_start[next_str]]
        next_node2 = [x_end[next_str], y_end[next_str]]
        for no in streetnodes:  # search for nodes with positions of next_str
            if quarter.node[no]['position'] == point.Point(next_node1):
                nd_one = no
            elif quarter.node[no]['position'] == point.Point(next_node2):
                nd_two = no
        for ed in streetedges:  # search for edge with nodes of next_str
            if nd_one in ed and nd_two in ed:
                building_list[i].append(ed)  # add edge to building_list
                break
        for street in range(len(streetlist)):
            if building_list[i][6] == streetlist[street][1]:
                building_list[i].append(streetlist[street][0])   # add streetnumber to building in building_list
                streetlist[street][3].append(i)    # add position in building_list to street in streetlist

        # add edges from building node on street to next nodes and to building node to quarter (later: shortest_path)
        quarter.add_edge(nn, nd_one)
        quarter.add_edge(nn, nd_two)
        quarter.add_edge(nn, building_list[i][0])

    # add edges between building nodes on street of each street
    for street in streetlist:
        for b1 in street[3]:
            for b2 in street[3]:
                if b1 == b2:
                    pass
                else:
                    quarter.add_edge(building_list[b1][5], building_list[b2][5])
    #   #---------------------------------------------------------------------------------------------------------------
    #   Clustering via demand

    # sort buildings by demand_mode
    if demand_mode == 'thermal':
        building_list = sorted(building_list, key=itemgetter(1), reverse=True)
        dem = 1
    elif demand_mode == 'electrical':
        building_list = sorted(building_list, key=itemgetter(2), reverse=True)
        dem = 2
    else:
        building_list = sorted(building_list, key=itemgetter(3), reverse=True)
        dem = 3

    centers = []  # save position of center-buildings in building_list
    centers.append([building_list[0][4].x, building_list[0][4].y])
    left_buildings = deepcopy(building_list)
    left_buildings.remove(building_list[0])     # list of not assigned

    if show_demand:
        show_demand_map(quarter, building_list, dem)

    #-------------------------------------------------------------------------------------------------------------------
    # search for groups
    print('\nSearch for groups of buildings...')

    if grouping_mode == 'street':
        # check nodes for n_max
        for b1 in building_list:
            count_nodes = 0
            pos = quarter.node[b1[5]]['position']
            for b2 in building_list:
                if quarter.node[b2[5]]['position'] == pos:
                    count_nodes += 1
            if count_nodes > n_max:
                warnings.warn('There are more than n_max nodes (' + str(count_nodes) + ') on same position on street! Try grouping_mode=building or set n_max to a higher value.')
                sys.exit(1)
    groups = grouping(quarter, building_list, d_neighbor, mode=grouping_mode)   # group direct neighbors

    count = 0
    for g in groups:
        count += 1
    print('Number of groups: ', count)

    # correct too big groups
    print('Correct size of groups...')
    all_groups_ok = False
    d_neighbor_new = d_neighbor * 0.9
    while not all_groups_ok:
        temp_groups = []
        for g in groups:
            if len(g) > n_max:  # group is too big
                temp_groups.append(g)   # collect too big groups
                d_neighbor_new = d_neighbor_new * 0.9   # set new max distance
                all_groups_ok = False
                break
            else:   # group is ok
                all_groups_ok = True
        if not all_groups_ok:
            for g in temp_groups:
                new_groups = grouping(quarter, g, d_neighbor_new)   # run grouping in g with reduced d_neighbor
                groups.remove(g)    # remove old too big groups
                for g in new_groups:
                    groups.append(g)    # add new corrected groups

    print('Found ', len(groups), ' groups.')
    print('------------------------------------\n')

    #-------------------------------------------------------------------------------------------------------------------
    # plot groups
    plt.rcParams['figure.figsize'] = 10, 15
    plt.axis('equal')
    for street in quarter.nodelist_street:
        draw = nx.draw_networkx_nodes(quarter,
                                      pos=quarter.positions,
                                      nodelist=[street],
                                      node_size=2 * 0.5,
                                      node_color='black',
                                      linewidths=None,
                                      alpha=0.2
                                      )
        if draw is not None:
            draw.set_edgecolor('black')
    for edge in quarter.edges():
        for node in edge:
            if 'street' in quarter.node[node]['node_type']:
                color = 'black'
                style = 'solid'
                alpha = 0.2
                break
        nx.draw_networkx_edges(quarter,
                                   pos=quarter.positions,
                                   edgelist=[edge],
                                   style=style,
                                   edge_color=[color],
                                   alpha=alpha)
    plt.tick_params(axis='both',
                            which='both',
                            bottom='on',
                            top='on',
                            labelbottom='on',
                            right='on',
                            left='on',
                            labelleft='on')

    plt.xlabel('x-Position [m]', horizontalalignment='center', labelpad=15)
    plt.ylabel('y-Position [m]', verticalalignment='center', labelpad=15)

    for g in groups:
        points = []
        for b in g:
            points.append([b[4].x, b[4].y])
        points = np.array(points)
        plt.plot(points[:,0], points[:,1], 's')
        plt.plot(points[:, 0], points[:, 1], 'r--', lw=2)
    plt.show()

    #-------------------------------------------------------------------------------------------------------------------
    # find cluster-centers in building_list
    print('Search for clustercenters...')
    b = 1   # counter building_list
    n_cluster = 1   # counter cluster
    n_cluster_set = round(float(n_buildings / n_max) + 0.5, 0)   # number of clusters (rounded up)
    clusterlist.append([])  # new empty cluster
    clusterlist[0].append(building_list[0])    # set first cluster-center

    while n_cluster < n_cluster_set:
        dst_ok = False
        # loop over all existing cluster-centers to check the distance between cluster-centers and actual building
        for i in range(len(clusterlist)):
            # distance between current building and cluster-centers
            dst_center = netops.calc_node_distance(quarter, clusterlist[i][0][0], building_list[b][0])
            if dst_center > dst_center_min:
                dst_ok = True
            else:
                dst_ok = False
                break
        if dst_ok:
            if assignment == 'building':
                clusterlist.append([])
                clusterlist[n_cluster].append(building_list[b])    # set next cluster-center
                centers.append([building_list[b][4].x, building_list[b][4].y])
                n_cluster += 1
                b += 1
            else:
                # ckeck group of building b for other clustercenters
                skip_building = False
                for g in groups:
                    if building_list[b] in g:   # b is in group g
                        for c in clusterlist:
                            if c[0] in g:   # group has another clustercenter
                                b += 1
                                skip_building = True
                                break
                    if skip_building:
                        break
                if not skip_building:
                    clusterlist.append([])
                    clusterlist[n_cluster].append(building_list[b])    # set next cluster-center
                    centers.append([building_list[b][4].x, building_list[b][4].y])
                    n_cluster += 1
                    b += 1
        else:
            b += 1
        # if n_cluster != n_cluster_set at end of building_list, decrease dst_center_min
        if b == (len(building_list)):
            clusterlist = []
            clusterlist.append([])  # new empty cluster
            clusterlist[0].append(building_list[0])    # set first cluster-center
            b = 1
            n_cluster = 1
            dst_center_min = dst_center_min * 0.9
            print('Calculate new min distance (d_center_min)!')

    print('\nClustercenters:')
    for c in clusterlist:
        print(c[0][0])
    print('------------------------------------\n')
    #-------------------------------------------------------------------------------------------------------------------

    #  add buildings to clusters
    print('Assign buildings or groups to centers...')
    if assignment == 'building':
        #---------------------------------------------------------------------------------------------------------------
        # list with street distance between buildings and clustercenters
        netops.add_weights_to_edges(quarter)    # add distance to edges
        paths = []

        # calculate for each building shortest path and length to each center
        for b in range(len(building_list)):
            paths.append([])
            for c in range(len(clusterlist)):
                # find shortest path from b to c
                path = nx.dijkstra_path(quarter, building_list[b][0], clusterlist[c][0][0])
                # calculate length of shortest path
                length = nx.dijkstra_path_length(quarter, building_list[b][0], clusterlist[c][0][0])
                paths[b].append([c, path, length])

        for b in range(len(building_list)):     # sort paths of each building
            paths[b] = sorted(paths[b], key=lambda x: x[2])

        for b in range(len(building_list)):
            skip = False
            for c in clusterlist:
                if building_list[b] in c:   # building already in cluster
                    skip = True
            if not skip:
                c = paths[b][0][0]  # nearest cluster
                clusterlist[c].append(building_list[b]) # add single building to cluster

        # split too big clusters
        if recentering:
            for c in range(len(clusterlist)):
                clusterlist[c] = sorted(clusterlist[c], key=itemgetter(dem), reverse=True)

        for c in clusterlist:
            if len(c) > n_max:
                print('Split cluster ', clusterlist.index(c))
                # split cluster
                n_too_much = len(c) - n_max     # number of surplus nodes
                print(n_too_much, ' buildings over n_max.')

                split_done = False
                while not split_done:
                    # # find centroid of cluster
                    # points = []
                    # for b in c:
                    #     points.append([b[4].x, b[4].y])     # list x-, y-position of nodes in cluster
                    # points = np.array(points)     # transform points to ndarray
                    # centroid = centeroidnp(points)  # find centroid of cluster
                    # centroid = point.Point(centroid)

                    # find building with greatest distance to centroid
                    dst = {}
                    for b in range(len(c)):
                        # dst[b] = netops.calc_point_distance(centroid, c[b][4])
                        dst[b] = nx.dijkstra_path_length(quarter, c[0][0], c[b][0])
                    last_building = c[max(dst, key=dst.get)]

                    # add single building to new cluster
                    clusterlist.append([])
                    clusterlist[n_cluster].append(last_building)    # add last building to new cluster
                    c.remove(last_building)     # remove building from old cluster
                    n_cluster += 1
                    print('Change building: ', last_building[0])
                    if n_too_much == 1:
                        split_done = True
                    else:
                        n_too_much -= 1

    elif assignment == 'group':
        #---------------------------------------------------------------------------------------------------------------
        # search center-building for each group
        for g in range(len(groups)):
            no_center = True
            for b in range(len(groups[g])):
                if [groups[g][b]] in clusterlist:
                    groups[g].insert(0, groups[g].pop(b))
                    no_center = False
            if no_center:
                # building with highest demand on position [0] (center of group)
                groups[g] = sorted(groups[g], key=itemgetter(1), reverse=True)

        # list with street distance between buildings and clustercenters
        netops.add_weights_to_edges(quarter)    # add distance to edges
        paths = []

        # calculate for each building shortest path and length to each center
        for g in range(len(groups)):
            paths.append([])
            for c in range(len(clusterlist)):
                # find shortest path from g to c
                path = nx.dijkstra_path(quarter, groups[g][0][0], clusterlist[c][0][0])
                # calculate length of shortest path
                length = nx.dijkstra_path_length(quarter, groups[g][0][0], clusterlist[c][0][0])
                paths[g].append([c, path, length])

        for g in range(len(groups)):     # sort paths of each building
            paths[g] = sorted(paths[g], key=itemgetter(2))

        for g in range(len(groups)):
            c = paths[g][0][0]  # nearest cluster
            for building in groups[g]:
                if building in clusterlist[c]:  # building already in cluster
                    continue
                else:
                    clusterlist[c].append(building)     # add building to cluster

        # split too big clusters
        if recentering:
            for c in range(len(clusterlist)):
                clusterlist[c] = sorted(clusterlist[c], key=itemgetter(dem), reverse=True)

        for c in clusterlist:
            if len(c) > n_max:
                print('Split cluster ', clusterlist.index(c))
                # split cluster
                n_too_much = len(c) - n_max     # number of surplus nodes
                print(n_too_much, ' buildings over n_max.')

                split_done = False
                while not split_done:
                    # # find centroid of cluster
                    # points = []
                    # for b in c:
                    #     points.append([b[4].x, b[4].y])     # list x-, y-position of nodes in cluster
                    # points = np.array(points)     # transform points to ndarray
                    # centroid = centeroidnp(points)  # find centroid of cluster
                    # centroid = point.Point(centroid)

                    # find building with greatest distance to center/centroid
                    dst = {}
                    for b in range(len(c)):
                        # dst[b] = netops.calc_point_distance(centroid, c[b][4])
                        dst[b] = nx.dijkstra_path_length(quarter, c[0][0], c[b][0])
                    last_building = c[max(dst, key=dst.get)]

                    # check if last_building is part of group
                    for g in groups:
                        if last_building in g and len(g) <= n_max:
                            # add group as new cluster
                            clusterlist.append(g)
                            clusterlist[n_cluster] = sorted(clusterlist[n_cluster], key=itemgetter(dem), reverse=True)
                            print('Found group to append new cluster')
                            for b in g:
                                print('Change building ', b[0])
                                c.remove(b)     # remove buildings from old cluster
                            n_cluster += 1
                            no_group = False
                            if len(g) >= n_too_much:
                                split_done = True
                            else:
                                n_too_much -= len(g)
                            break
                        else:
                            no_group = True

                    if no_group:
                        # add single building to new cluster
                        clusterlist.append([])
                        clusterlist[n_cluster].append(last_building)    # add last building to new cluster
                        c.remove(last_building)     # remove building from old cluster
                        n_cluster += 1
                        print('Change building: ', last_building[0])
                        if n_too_much == 1:
                            split_done = True
                        else:
                            n_too_much -= 1

    elif assignment == 'group_energetic':
        #---------------------------------------------------------------------------------------------------------------
        # search center-building for each group
        for g in range(len(groups)):
            no_center = True
            for b in range(len(groups[g])):
                if [groups[g][b]] in clusterlist:
                    groups[g].insert(0, groups[g].pop(b))
                    no_center = False
            if no_center:
                # building with highest demand on position [0] (center of group)
                groups[g] = sorted(groups[g], key=itemgetter(1), reverse=True)

        # list with street distance between buildings and clustercenters
        netops.add_weights_to_edges(quarter)    # add distance to edges
        paths = []

        # calculate for each building shortest path and length to each center
        for g in range(len(groups)):
            paths.append([])
            for c in range(len(clusterlist)):
                # find shortest path from g to c
                path = nx.dijkstra_path(quarter, groups[g][0][0], clusterlist[c][0][0])
                # calculate length of shortest path
                length = nx.dijkstra_path_length(quarter, groups[g][0][0], clusterlist[c][0][0])
                paths[g].append([c, path, length])

        for g in range(len(groups)):     # sort paths of each building
            paths[g] = sorted(paths[g], key=itemgetter(2))

        for g in range(len(groups)):
            c = paths[g][0][0]  # nearest cluster
            for building in groups[g]:
                if building in clusterlist[c]:  # building already in cluster
                    continue
                else:
                    clusterlist[c].append(building)     # add building to cluster

        # correct clustersize
        if recentering:
            for c in range(len(clusterlist)):
                clusterlist[c] = sorted(clusterlist[c], key=itemgetter(dem), reverse=True)

        for c in clusterlist:
            print('Cluster: ', clusterlist.index(c))
            for b in c:
                print(b[0])
        temp_clusterlist = []
        for c in clusterlist:
            if len(c) > n_max:
                print('Change cluster ', clusterlist.index(c), '. It comprises ', len(c), ' buildings.')
                f_En = []
                for b in range(len(c)):
                    if b == clusterlist[0]:
                        continue
                    else:
                        # calculate demand / distance
                        f_En.append([b, c[b][dem] / nx.dijkstra_path_length(quarter, c[b][0], c[0][0])])  # energetic factor

                f_En = sorted(f_En, key=itemgetter(1))  # sort by demand
                for n in range(len(c) - n_max):
                    temp_clusterlist.append(c[f_En[n][0]])  # store building as temporary cluster

        for tc in temp_clusterlist:
            for c in clusterlist:
                if tc in c:
                    c.remove(tc)    # remove building from old cluster
                    break
            clusterlist.append([tc])  # add temporary clusters to clusterlist
    print('\nAssignment completed.\n')
    print('------------------------------------\n')

    #-------------------------------------------------------------------------------------------------------------------
    count = 0
    for c in clusterlist:
        print('Cluster ', clusterlist.index(c))
        for b in c:
            print(b[0])
            count += 1
    print('Number of clusters: ', len(clusterlist))
    print('Number of buildings: ', count)
    #-------------------------------------------------------------------------------------------------------------------
    # plot streetnetwork
    plt.rcParams['figure.figsize'] = 10, 15
    plt.axis('equal')
    for street in quarter.nodelist_street:
        draw = nx.draw_networkx_nodes(quarter,
                                      pos=quarter.positions,
                                      nodelist=[street],
                                      node_size=2 * 0.5,
                                      node_color='black',
                                      linewidths=None,
                                      alpha=0.2
                                      )
        if draw is not None:
            draw.set_edgecolor('black')
    for edge in quarter.edges():
        for node in edge:
            if 'street' in quarter.node[node]['node_type']:
                color = 'black'
                style = 'solid'
                alpha = 0.2
                break
        nx.draw_networkx_edges(quarter,
                                   pos=quarter.positions,
                                   edgelist=[edge],
                                   style=style,
                                   edge_color=[color],
                                   alpha=alpha)
    plt.tick_params(axis='both',
                            which='both',
                            bottom='on',
                            top='on',
                            labelbottom='on',
                            right='on',
                            left='on',
                            labelleft='on')

    plt.xlabel('x-Position [m]', horizontalalignment='center', labelpad=15)
    plt.ylabel('y-Position [m]', verticalalignment='center', labelpad=15)

    # convexhull defines borders of cluster
    for c in clusterlist:
        if len(c) > 1:
            bpoints = []
            points = []
            for b in c:
                bpoints.append([b[4].x, b[4].y])   # position of building node
                points.append([b[4].x, b[4].y])   # position of building node
                points.append([quarter.node[b[5]]['position'].x, quarter.node[b[5]]['position'].y])
            bpoints = np.array(bpoints)
            points = np.array(points)
            hull = ConvexHull(points, 2)   # calc convexhull of cluster
            vert = points[hull.vertices]    # vertices of convex hull
            vert = np.append(vert, [vert[0]], axis=0)   # complete vertices with repetition of first point
            plt.plot(vert[:, 0], vert[:, 1], 'r--', lw=2)
            plt.plot(bpoints[:,0], bpoints[:,1], 'o')
            #plt.plot(points[hull.vertices[0],0], points[hull.vertices[0],1], 'ro')
            plt.plot(c[0][4].x, c[0][4].y, '*', markersize=12)
            plt.text(quarter.node[c[0][0]]['position'].x,
                                 quarter.node[c[0][0]]['position'].y + 0.8,
                                 s=str(clusterlist.index(c)),
                                 horizontalalignment='center',
                                 fontsize=12)
        else:
            bpoints = []
            points = []
            for b in c:
                bpoints.append([b[4].x, b[4].y])
            bpoints = np.array(bpoints)
            plt.plot(bpoints[:, 0], bpoints[:, 1], 'o')
            plt.plot(c[0][4].x, c[0][4].y, 's')
            plt.text(quarter.node[c[0][0]]['position'].x,
                                 quarter.node[c[0][0]]['position'].y + 0.8,
                                 s=str(clusterlist.index(c)),
                                 horizontalalignment='center',
                                 fontsize=12)
    plt.show()

    # handover clusters
    clusters = {}
    for c in range(len(clusterlist)):
        buildings = []
        for b in clusterlist[c]:
            buildings.append(b[0])
        clusters[c] = buildings
    print('Finished clustering!')

    return clusters