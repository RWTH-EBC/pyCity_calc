#!/usr/bin/env python
# coding=utf-8
"""
Script with option to visualize cities
"""

import os
import warnings
import numpy as np
import shapely.geometry.point as point

import matplotlib.pyplot as plt
import networkx as nx
import itertools

try:
    from matplotlib2tikz import save as tikz_save
except:  # pragma: no cover
    msg = 'Could not import matplotlib2tikz. Install first (e.g. via pip)'
    warnings.warn(msg)


def gen_path(path):
    """
    Generates path, if not existent.

    Parameters
    ----------
    path : str
        Path
    """

    if not os.path.exists(path):  # pragma: no cover
        os.makedirs(path)


def get_ebc_color_list(intensity=3):
    """
    Returns ebc color list (7 colors; red, blue, orange, lila, brown,
    light lila, green)

    Parameters
    ----------
    intensity : int, optional
        Defines intensity (default: 3)
        Options: 1 - 3
        1: Low intensity (bar plots)
        3: High intensity (lines etc.)

    Returns
    -------
    list_color_ebc : list (of str)
        List with color RGB codes
    """

    if intensity == 1:
        list_color_ebc = ['#F4A29E', '#93B4DC', '#FBC09E', '#B79CB4',
                          '#D29C9A', '#E7A7CE', '#8CC9AC']

    elif intensity == 2:
        list_color_ebc = ['#EC635C', '#4B81C4', '#F49961', '#8768B4',
                          '#B45955', '#CB74F4', '#3FA574']

    elif intensity == 3:
        list_color_ebc = ['#E53027', '#1058B0', '#F47328', '#5F379B',
                          '#9B231E', '#BE4198', '#08746']

    return list_color_ebc


def get_grey_color_list():
    """
    Return list with black and grey colors (3 different ones, repeated two
    times)

    Returns
    -------
    list_bw_colors
    """

    list_bw_colors = ['#7e7e7e', '#000000', '#bdbdbd',
                      '#7e7e7e', '#000000', '#bdbdbd']

    return list_bw_colors


def get_grey_linestyles():
    """
    Returns list of linestyles ['-', '--', '-', '-.', '-', '-.']

    Returns
    -------
    list_lstyles : list (of str)
        List of linestyles
    """

    list_lstyles = ['-', '--', '-', '-.', '-', '-.']

    return list_lstyles


def get_marker_list():
    """
    Returns list of markerstyles ['o', 'v', 's', '^', '8', '*', 'h', '+']

    Returns
    -------
    list_markers : list (of str)
        List of markerstyles
    """

    list_markers = ['o', 'v', 's', '^', '8', '*', 'h', '+']

    return list_markers


def get_pos_for_plotting(city):
    """
    Returns dictionary with node ids as keys and position tuples (x, y) as
    values, which is necessary for plotting of city graph.

    Nodes must hold 'position' attribute (shapely Point)!

    Parameters
    ----------
    city : City object
        City object of pycity_calc (requires shapely Point as position attribute
        per building)

    Returns
    -------
    pos : dict
        Dictionary of node ids as keys with position tuples (x, y) as values
    """

    import pycity_calc.toolbox.networks.network_ops as netop

    #  Extract positions (shapely Points) for every node
    pos = nx.get_node_attributes(city, 'position')

    #  Convert pos points into tuples
    for key in pos:
        pos[key] = netop.convert_shapely_point_to_tuple(pos[key])

    return pos


def plot_city_district(city, city_list=None, plot_buildings=True,
                       plot_street=True,
                       plot_lhn=False, plot_deg=False, plot_esys=False,
                       offset=None,
                       plot_build_labels=True, plot_str_labels=False,
                       plot_heat_labels=False,
                       equal_axis=False, font_size=12, plt_title=None,
                       x_label='x-position in m',
                       y_label='y-position in m', show_plot=True,
                       fig_adjust=None,
                       plot_elec_labels=False, save_plot=False,
                       save_path=None, dpi=100, plot_color=True,
                       plot_engl=True,
                       auto_close=False, plot_str_dist=None, node_size=50):
    """
    Plots city object of pycity_calc

    Parameters
    ----------
    city : city object
        City object of pycity_calc
    city_list : list, optional
        List of city objects. If not None, plot results for all city objects
        within list (default: None)
    plot_buildings : bool, optional
        Plot buildings (default: True)
    plot_street : bool, optional
        Plot street (default: True)
    plot_lhn : bool, optional
        Plot local heating networks (default: False)
    plot_deg : bool, optional
        Plot decentralized, electrical grids (default: False)
    plot_esys : bool, optional
        Plot energy systems (default: False)
    offset : float, optional
        Offset between node position and label on y axis
        (default: None)
    plot_build_labels : bool, optional
        Plot building node labels (default: True)
    plot_str_labels : bool, optional
        Plot street node labels (default: False)
    plot_heat_labels : bool, optional
        Plot heating network node labels (default: False)
    equal_axis : bool, optional
        Equalize x- and y-axis (default: False)
    font_size : float, optional
        Font size of axis text and title (default: 12)
    plt_title : str, optional
        Title of plot (default: None)
    x_label : str, optional
        x-axis label (default: 'x-position in m')
    y_label : str, optional
        y-axis label (default: 'y-position in m')
	show_plot : bool, optional
		Defines, if plot should be displayed (default: True)
	fig_adjust : str, optional
        Defines figure size (default: None)
        If None, default rc parameters are used.
        Other options: 'a4', 'a4_half'
	plot_elec_labels : bool, optional
	    Defines, if electric labels should be plotted (default: False)
	save_plot : bool, optional
	    Defines, if plot should be saved (default: False)
	save_path : str, optional
	    Defines folder path to save plot to (default: None)
	    If set to None and save_plot == True, saves into __file__ directory
	    in eps and png format.
	dpi : int, optional
	    DPI size (default: 100)
	plot_color : bool, optional
	    Defines, if plot should be colored or in greyscale (default: True)
	    If true, color is used. If False, greyscale is used
	plot_engl : bool, optional
	    Defines language of energy system labels (default: True)
	    If True, uses English. If False, uses German.
	auto_close : bool, optional
	    Automatically closes current figure (default: False)
	plot_str_dist : float, optional
        Defines, if streets should only be plotted within a specific distance
        (default: None). If set to None, all street networks are plotted
        (requires plot_street == True)
    node_size : int, optional
        Node size for plotting (default: 50)
    """

    import pycity_calc.toolbox.networks.network_ops as netop

    plt.rc('text', usetex=False)
    # font = {'family': 'serif', 'size': font_size}
    # plt.rc('font', **font)
    plt.rc('font', family='Arial', size=font_size)

    if city_list is None:  # city
        assert city is not None
        city_list = [city]
    else:
        assert len(city_list) > 0
        assert city is None

    # Generate figure object
    if fig_adjust == 'a4':
        fig = plt.figure(figsize=(8, 8), dpi=dpi)
    elif fig_adjust == 'a4_half':
        fig = plt.figure(figsize=(4, 4), dpi=dpi)
    else:
        fig = plt.figure(dpi=dpi)

    for i in range(len(city_list)):

        #  Current city object
        city = city_list[i]

        #  Extract positions
        pos = get_pos_for_plotting(city)

        # Get node labels
        node_labels = nx.get_node_attributes(city, 'node_type')

        if plot_buildings:
            #  Plot building nodes
            nx.draw_networkx_nodes(city, pos=pos,
                                   nodelist=city.nodelist_building,
                                   node_color='k', node_shape='s', alpha=0.5,
                                   node_size=node_size)

        if plot_street:
            #  Plot street network
            if plot_str_dist is None:  # Plot total street network

                #  Plot street network
                nx.draw_networkx_nodes(city, pos=pos,
                                       nodelist=city.nodelist_street,
                                       node_color='k', node_shape='o',
                                       alpha=0.5, with_labels=False,
                                       node_size=node_size,
                                       width=2)

                edgelist_street = []
                for u, v in city.edges():
                    if 'network_type' in city.edges[u, v]:
                        if city.edges[u, v]['network_type'] == 'street':
                            edgelist_street.append((u, v))
                nx.draw_networkx_edges(city, pos=pos, edgelist=edgelist_street,
                                       width=1, edge_color='k')

            else:  # Only plot street network in specific position

                list_str_close = []

                for s in city.nodelist_street:
                    for b in city.nodelist_building:
                        dist = netop.calc_node_distance(city, s, b)
                        if dist <= plot_str_dist:
                            if s not in list_str_close:
                                #  Add street node s to list
                                list_str_close.append(s)
                                break

                nx.draw_networkx_nodes(city, pos=pos,
                                       nodelist=list_str_close,
                                       node_color='k', node_shape='o',
                                       alpha=0.5, with_labels=False,
                                       node_size=node_size,
                                       width=2)
                edgelist_street = []

                for s1 in list_str_close:
                    for s2 in list_str_close:
                        if (s1, s2) in city.edges():
                            if 'network_type' in city.edges[s1, s2]:
                                if city.edges[s1, s2][
                                    'network_type'] == 'street':
                                    edgelist_street.append((s1, s2))

                nx.draw_networkx_edges(city, pos=pos, edgelist=edgelist_street,
                                       width=1, edge_color='k')

        if plot_lhn:
            #  Plot local heating networks
            #  TODO: Label plotten

            if plot_color:
                node_color = 'r'
                edge_color = 'r'
            else:
                node_color = get_grey_color_list()[0]
                edge_color = get_grey_color_list()[0]
            edge_style = '--'

            for network_id in city.nodelists_heating:
                nx.draw_networkx_nodes(city, pos=pos,
                                       nodelist=city.nodelists_heating[
                                           network_id],
                                       node_size=node_size, width=2,
                                       node_color=node_color)
            edgelist_heating = []
            for u, v in city.edges():
                if 'network_type' in city.edges[u, v]:
                    if city.edges[u, v]['network_type'] == 'heating':
                        edgelist_heating.append((u, v))
            nx.draw_networkx_edges(city, pos=pos, edgelist=edgelist_heating,
                                   width=3, edge_color=edge_color,
                                   style=edge_style)

        if plot_deg:

            if plot_color:
                node_color = 'y'
                edge_color = 'y'
            else:
                node_color = get_grey_color_list()[1]
                edge_color = get_grey_color_list()[1]
            edge_style = '-.'

            #  Plot decentralized electrical grids
            #  TODO: label plotten
            for network_id in city.nodelists_electricity:
                nx.draw_networkx_nodes(city, pos=pos,
                                       nodelist=city.nodelists_electricity[
                                           network_id],
                                       node_size=node_size, width=2,
                                       node_color=node_color)
            edgelist_el = []
            for u, v in city.edges():
                if 'network_type' in city.edges[u, v]:
                    if city.edges[u, v]['network_type'] == 'electricity':
                        edgelist_el.append((u, v))
            nx.draw_networkx_edges(city, pos=pos, edgelist=edgelist_el,
                                   width=3, edge_color=edge_color,
                                   style=edge_style)

            #   add transformers
            edgelist_transformer = []
            for u, v in city.edges():
                if 'network_type' in city.edges[u, v]:
                    if (city.edges[u, v]['network_type'] == 'transformer'):
                        edgelist_transformer.append((u, v))
            nx.draw_networkx_edges(city, pos=pos,
                                   edgelist=edgelist_transformer,
                                   style='dotted', width=3,
                                   edge_color=edge_color)

        if plot_lhn or plot_deg:

            if plot_color:
                edge_color = 'g'
                edge_style = '-.'
            else:
                edge_color = get_grey_color_list()[2]
                edge_style = 'dotted'

            edgelist_el = []
            for u, v in city.edges():
                if 'network_type' in city.edges[u, v]:
                    if city.edges[u, v]['network_type'] == 'heating_and_deg':
                        edgelist_el.append((u, v))
            nx.draw_networkx_edges(city, pos=pos, edgelist=edgelist_el,
                                   width=2, edge_color=edge_color,
                                   style=edge_style)

        # Generate labeling
        pos_labels = {}
        keys = list(pos.keys())
        for key in keys:
            x, y = pos[key]

            #  With offset
            if offset is not None:
                pos_labels[key] = (x, y + offset)

            # Without offset
            else:
                pos_labels[key] = (x, y)

        if plot_build_labels:
            #  Plot building node ids
            labels = {}
            for node in city.nodes():
                if node in city.nodelist_building:
                    labels[node] = node
            nx.draw_networkx_labels(city, pos=pos_labels, labels=labels)

        if plot_elec_labels:
            #   Plot electricity node ids
            labels = {}
            for node in city.nodes():
                for network_id in city.nodelists_electricity:
                    if node in city.nodelists_electricity[network_id]:
                        labels[node] = node
            nx.draw_networkx_labels(city, font_size=10, pos=pos_labels,
                                    labels=labels)

        #  Fixme: Heating plotting should work with uesgraphs lists, too!
        if plot_heat_labels:
            #  Plot building node ids
            labels = {}
            for n in city.nodes():
                if 'node_type' in city.nodes[n]:
                    if (city.nodes[n]['node_type'] == 'heating' or
                                city.nodes[n][
                                    'node_type'] == 'heating_and_deg'):
                        labels[n] = n
            nx.draw_networkx_labels(city, pos=pos_labels, labels=labels)

        # TODO: Plot cooling', 'gas', 'others'

        if plot_esys:
            ax = fig.add_subplot(111)
            #  Plot energy systems by name
            for n in city.nodelist_building:
                if city.nodes[n]['entity']._kind == 'building':
                    #  Look if building has bes
                    if city.nodes[n]['entity'].hasBes:
                        #  Extract types of energy systems
                        esys_tuple = city.nodes[n]['entity'].bes.getHasDevices()
                        # esys_tuple = (self.hasBattery,
                        #               self.hasBoiler,
                        #               self.hasChp,
                        #               self.hasElectricalHeater,
                        #               self.hasHeatpump,
                        #               self.hasInverterAcdc,
                        #               self.hasInverterDcac,
                        #               self.hasPv,
                        #               self.hasTes)
                        found_esys = False
                        esys_str_list = []
                        esys_str = ''

                        if esys_tuple[2]:  # Has CHP
                            found_esys = True
                            if plot_engl:
                                esys_str_list.append('CHP')
                            else:
                                esys_str_list.append('KWK')

                        if esys_tuple[1]:  # Has Boiler
                            found_esys = True
                            if plot_engl:
                                esys_str_list.append('BOI')
                            else:
                                esys_str_list.append('K')

                        if esys_tuple[4]:  # Has HP
                            found_esys = True
                            if plot_engl:
                                esys_str_list.append('HP')
                            else:
                                esys_str_list.append('WP')

                        if esys_tuple[3]:  # Has el. heater
                            found_esys = True
                            esys_str_list.append('EH')

                        if esys_tuple[8]:  # Has TES
                            found_esys = True
                            if plot_engl:
                                esys_str_list.append('TES')
                            else:
                                esys_str_list.append('TS')

                        if esys_tuple[7]:  # Has PV
                            found_esys = True
                            esys_str_list.append('PV')

                        if esys_tuple[0]:  # Has battery
                            found_esys = True
                            esys_str_list.append('BAT')

                        if found_esys:
                            #  Construct string
                            for i in range(len(esys_str_list)):
                                if i == 0:
                                    esys_str = str(esys_str_list[i])
                                else:  # All other positions
                                    esys_str += ', ' + str(esys_str_list[i])

                            # Define position next to building node
                            x_p = city.nodes[n]['position'].x + 6
                            y_p = city.nodes[n]['position'].y

                            #  Plot textbox
                            ax.text(x_p, y_p, esys_str,
                                    bbox={'facecolor': 'white', 'alpha': 0.5,
                                          'pad': 5}, fontsize=font_size)

        if plot_str_labels:
            #  Plot street node ids
            labels = {}
            for node in city.nodes():
                if node in city.nodelist_street:
                    labels[node] = node
            nx.draw_networkx_labels(city, pos=pos_labels, labels=labels)

    # #  Add to city_visual.py as workaround to rescale figure size
    # #  to prevent overlapping of large esys labels with axes
    # plt.plot([335], [220], color='white')

    if plt_title:
        plt.title(str(plt_title))
    if x_label:
        plt.xlabel(str(x_label))
    if y_label:
        plt.ylabel(str(y_label))

    # TODO: Add function to normalizes axes to start with 0

    # plt.plot([335], [220], color='white')

    if equal_axis:
        plt.gca().set_aspect('equal', adjustable='box')

    fig.autofmt_xdate()
    plt.tight_layout()

    if save_plot:
        #  Save plots

        if save_path is None:

            save_path = os.path.dirname(os.path.abspath(__file__))

            #  Save as eps and png to __file__ directory
            save_eps = str(os.path.join(save_path, 'city_district.eps'))
            save_png = str(os.path.join(save_path, 'city_district.png'))
            save_svg = str(os.path.join(save_path, 'city_district.svg'))

            plt.savefig(save_eps, format='eps', dpi=dpi)
            plt.savefig(save_png, format='png', dpi=dpi)
            plt.savefig(save_svg, format='svg', dpi=dpi)

            try:
                path_tikz = os.path.join(save_path, 'city_district.tikz')

                tikz_save(path_tikz, figureheight='\\figureheight',
                          figurewidth='\\figurewidth')
            except:
                warnings.warn('Could not save figure as tikz')

        else:  # save path is not none

            #  Check if save_path points on folder or file
            if os.path.isdir(save_path):

                #  Save as eps and png to __file__ directory
                save_eps = str(os.path.join(save_path, 'city_district.eps'))
                save_png = str(os.path.join(save_path, 'city_district.png'))
                save_svg = str(os.path.join(save_path, 'city_district.svg'))

                plt.savefig(save_eps, format='eps', dpi=dpi)
                plt.savefig(save_png, format='png', dpi=dpi)
                plt.savefig(save_svg, format='svg', dpi=dpi)

                try:
                    path_tikz = os.path.join(save_path, 'city_district.tikz')

                    tikz_save(path_tikz, figureheight='\\figureheight',
                              figurewidth='\\figurewidth')
                except:
                    warnings.warn('Could not save figure as tikz')

            else:
                plt.savefig(save_path, dpi=dpi)

        print()
        print('###############################################')
        print('Saved city_district figures to %s' % (save_path))
        print('###############################################')
        print()

    if show_plot:
        plt.show()

    if auto_close:
        plt.close()

    return fig


def plot_multi_city_district(city, main_save_path,
                             city_list=None,
                             plot_buildings=True,
                             plot_street=True, plot_lhn=True,
                             plot_deg=True, plot_esys=True,
                             offset=10,
                             plot_build_labels=False, plot_str_labels=False,
                             equal_axis=True, font_size=16, plt_title=None,
                             show_plot=False,
                             fig_adjust=None,
                             plot_elec_labels=False, save_plot=True, dpi=100,
                             auto_close=True, plot_str_dist=None):
    """
    Plots city object of pycity_calc with different colors and different
    languages (English and German) to specific folder

    Parameters
    ----------
    city : city object
        City object of pycity_calc
    main_save_path : str
	    Defines folder path to save all plot to
    city_list : list, optional
        List of city objects. If not None, plot results for all city objects
        within list (default: None)
    plot_buildings : bool, optional
        Plot buildings (default: True)
    plot_street : bool, optional
        Plot street (default: True)
    plot_lhn : bool, optional
        Plot local heating networks (default: True)
    plot_deg : bool, optional
        Plot decentralized, electrical grids (default: True)
    plot_esys : bool, optional
        Plot energy systems (default: True)
    offset : float, optional
        Offset between node position and label on y axis
        (default: 10)
    plot_build_labels : bool, optional
        Plot building node labels (default: False)
    plot_str_labels : bool, optional
        Plot street node labels (default: False)
    equal_axis : bool, optional
        Equalize x- and y-axis (default: True)
    font_size : float, optional
        Font size of axis text and title (default: 16)
    plt_title : str, optional
        Title of plot (default: None)
	show_plot : bool, optional
		Defines, if plot should be displayed (default: False)
	fig_adjust : str, optional
        Defines figure size (default: None)
        If None, default rc parameters are used.
        Other options: 'a4', 'a4_half'
	plot_elec_labels : bool, optional
	    Defines, if electric labels should be plotted (default: False)
	save_plot : bool, optional
	    Defines, if plot should be saved (default: True)
	dpi : int, optional
	    DPI size (default: 100)
	auto_close : bool, optional
	    Automatically closes current figure (default: True)
	plot_str_dist : float, optional
        Defines, if streets should only be plotted within a specific distance
        (default: None). If set to None, all street networks are plotted
        (requires plot_street == True)
    """

    list_language = ['engl', 'ger']
    list_color = ['color', 'grey']

    for lan in list_language:

        if lan == 'engl':
            x_label = u'x-coordinate in m'
            y_label = u'y-coordinate in m'
            plot_engl = True

        elif lan == 'ger':
            x_label = u'x-Koordinate in m'
            y_label = u'y-Koordinate in m'
            plot_engl = False

        for clr in list_color:

            if clr == 'color':
                plot_color = True

            elif clr == 'grey':
                plot_color = False

            curr_path = os.path.join(main_save_path, lan, clr)

            #  Generate path, if not existent
            gen_path(curr_path)

            plot_city_district(city=city, city_list=city_list,
                               plot_buildings=plot_buildings,
                               plot_street=plot_street,
                               plot_lhn=plot_lhn,
                               plot_deg=plot_deg,
                               plot_esys=plot_esys,
                               offset=offset,
                               plot_build_labels=plot_build_labels,
                               plot_str_labels=plot_str_labels,
                               equal_axis=equal_axis,
                               font_size=font_size, plt_title=plt_title,
                               x_label=x_label, y_label=y_label,
                               show_plot=show_plot, fig_adjust=fig_adjust,
                               plot_elec_labels=plot_elec_labels,
                               save_plot=save_plot,
                               save_path=curr_path, dpi=dpi,
                               plot_color=plot_color,
                               plot_engl=plot_engl,
                               auto_close=auto_close,
                               plot_str_dist=plot_str_dist)


def plot_cluster_results(city, cluster_dict, plot_street=True,
                         plot_build_labels=False, plot_clust_keys=True,
                         use_bw=False, offset=None,
                         save_plot=False, show_plot=True,
                         save_path='clust_res.png', plot_str_dist=None,
                         font_size=16, plt_title=None,
                         x_label=None, y_label=None):
    """
    Plot results of clustering

    Parameters
    ----------
    city : city object
        City object of pycity_calc
    cluster_dict : dict
        Dictionary with cluster numbers (int) as keys and node ids (int)
        as values
    plot_street : bool, optional
        Plot street (default: True)
    plot_build_labels : bool, optional
        Defines if building node numbers should be plotted (default: False)
    plot_clust_keys : bool, optional
        Defines if cluster labels should be plotted (default: True)
    use_bw : bool, optional
        Defines, if black and white colors should be used (default: False)
        True - Use black, white (and grey) exclusively
        False - Use different colors
    offset : float, optional
        Defines y-axis offset of building labels (default: None)
    save_plot : bool, optional
        Save plot (default: False)
    show_plot : bool, optional
        Show plot (default: True)
    save_path : str, optional
        Path to save picture to (default: 'clust_res.png')
    plot_str_dist : float, optional
        Defines, if streets should only be plotted within a specific distance
        (default: None). If set to None, all street networks are plotted
        (requires plot_street == True)
    """

    import pycity_calc.toolbox.networks.network_ops as netop

    #  Get node positions
    pos = get_pos_for_plotting(city)

    # Get node labels
    node_labels = nx.get_node_attributes(city, 'node_type')

    #  Create figure
    fig1 = plt.figure()

    markers = itertools.cycle(('s', 'o', '*', 'v', '+', 'x', '8', 'D'))

    #  Loop over cluster_dict
    for ke in cluster_dict:
        node_list = cluster_dict[ke]

        if use_bw:
            color = 'k'
        else:  # Use different colors
            color = np.random.rand(3)

        # Plot building nodes
        nx.draw_networkx_nodes(city, pos=pos, nodelist=node_list,
                               node_color=color, node_shape=next(markers),
                               alpha=0.5)

        #  Generate labeling
        pos_labels = {}
        keys = list(pos.keys())
        for key in keys:
            x, y = pos[key]

            #  With offset
            if offset is not None:
                pos_labels[key] = (x, y + offset)

            # Without offset
            else:
                pos_labels[key] = (x, y)

        if plot_build_labels:
            #  Plot building node ids
            labels = {}
            for node in city.nodes():
                if node in city.nodelist_building:
                    labels[node] = node

            nx.draw_networkx_labels(city, pos=pos_labels, labels=labels)

        if plot_clust_keys:
            #  # For plotting cluster keys to every building node
            #  Plot cluster keys
            # labels = {}
            # for node in city.nodes():
            #     if node in node_list:
            #         labels[node] = ke

            #  Find average point of all nodes within cluster
            (x, y) = netop.calc_center_pos(city, nodelist=node_list)

            pos_labels = {}
            pos_labels[node_list[0]] = (x, y)
            labels = {}
            labels[node_list[0]] = 'C' + str(ke)

            #  Plot cluster keys within cluster center
            nx.draw_networkx_labels(city, pos=pos_labels, labels=labels,
                                    font_size=16)

    if plot_street:

        if plot_str_dist is None:  # Plot total street network
            #  Plot street network
            nx.draw_networkx(city, pos=pos, nodelist=city.nodelist_street,
                             node_color='k',
                             node_shape='o', alpha=0.5, with_labels=False,
                             node_size=100, width=2)

        else:  # Only plot street network in specific position

            list_str_close = []

            for s in city.nodelist_street:
                for b in city.nodelist_building:
                    dist = netop.calc_node_distance(city, s, b)
                    if dist <= plot_str_dist:
                        if s not in list_str_close:
                            #  Add street node s to list
                            list_str_close.append(s)
                            break

            # nx.draw_networkx(city, pos=pos, nodelist=list_str_close,
            #                  node_color='k',
            #                  node_shape='o', alpha=0.5, with_labels=False,
            #                  node_size=100, width=2)

            #  Plot street network

            nx.draw_networkx_nodes(city, pos=pos,
                                   nodelist=list_str_close,
                                   node_color='k', node_shape='o',
                                   alpha=0.5, with_labels=False, node_size=100,
                                   width=2)
            edgelist_street = []

            for s1 in list_str_close:
                for s2 in list_str_close:
                    if (s1, s2) in city.edges():
                        if 'network_type' in city.edges[s1, s2]:
                            if city.edges[s1, s2]['network_type'] == 'street':
                                edgelist_street.append((s1, s2))

            nx.draw_networkx_edges(city, pos=pos, edgelist=edgelist_street,
                                   width=1, edge_color='k')

    plt.rc('text', usetex=True)
    # font = {'family': 'serif', 'size': font_size}
    # plt.rc('font', **font)
    plt.rc('font', family='Arial', size=font_size)

    if plt_title:
        plt.title(plt_title)
    if x_label:
        plt.xlabel(x_label)
    if y_label:
        plt.ylabel(y_label)

    plt.gca().set_aspect('equal', adjustable='box')
    plt.tight_layout()

    if save_plot:
        plt.savefig(save_path, bbox_inches='tight')

    if show_plot:
        plt.show()


if __name__ == '__main__':
    import pycity_base.classes.supply.BES as BES
    import pycity_base.classes.supply.Boiler as Boiler
    import pycity_base.classes.supply.CHP as CHP
    import pycity_base.classes.supply.Battery as Batt

    import pycity_calc.examples.example_city as excity

    #  Maximum distance from streetnode to cluster graph, which should be
    #  plotted (if None, plot complete street network)
    plot_str_dist = None

    #  Generate city object via example_city.py run
    city_object = excity.run_example()
    #  3 buildings (positions (0, 0), (10, 10) and (20, 20)

    #  Add street nodes
    node_1 = city_object.add_street_node(position=point.Point(0, -2))
    node_2 = city_object.add_street_node(position=point.Point(10, -2))
    node_3 = city_object.add_street_node(position=point.Point(22, -2))
    node_4 = city_object.add_street_node(position=point.Point(22, 10))

    #  Add street edges
    city_object.add_edge(node_1, node_2, network_type='street')
    city_object.add_edge(node_2, node_3, network_type='street')
    city_object.add_edge(node_3, node_4, network_type='street')

    #  Add lhn node
    node_lhn = city_object.add_network_node(network_type='heating',
                                            position=point.Point(5, 0))
    #  Add lhn edges
    city_object.add_edge(city_object.nodelist_building[0], node_lhn,
                         network_type='heating')
    city_object.add_edge(city_object.nodelist_building[1], node_lhn,
                         network_type='heating')

    #  Add deg node
    node_deg = city_object.add_network_node(network_type='electricity',
                                            position=point.Point(15, 0))
    #  Add lhn edges
    city_object.add_edge(city_object.nodelist_building[1], node_deg,
                         network_type='electricity')
    city_object.add_edge(city_object.nodelist_building[2], node_deg,
                         network_type='electricity')

    #  Instantiate BES
    bes = BES.BES(city_object.environment)

    #  Create Boiler
    boiler = Boiler.Boiler(city_object.environment, qNominal=10000, eta=0.95)

    #  Create CHP
    chp = CHP.CHP(city_object.environment, pNominal=2000, qNominal=3000,
                  omega=0.9)

    #  Create battery
    battery = Batt.Battery(city_object.environment, socInit=1, capacity=100000)

    #  Add boiler to BES
    bes.addMultipleDevices([boiler, chp, battery])

    #  Add bes to one building within city
    city_object.nodes[city_object.nodelist_building[0]]['entity']. \
        addEntity(entity=bes)

    #  Plot city
    plot_city_district(city=city_object,
                       plot_buildings=True,
                       plot_street=True,
                       plot_lhn=True,
                       plot_deg=True,
                       plot_esys=True,
                       offset=2,
                       plot_build_labels=True,
                       plot_str_labels=False,
                       equal_axis=False,
                       font_size=16,
                       save_plot=False,
                       plot_str_dist=plot_str_dist,
                       plot_color=True,
                       fig_adjust=None)

    #  Plot multi city district files
    #  ###########################################################
    #  #  uncomment, if necessary
    # this_path = os.path.dirname(os.path.abspath(__file__))
    #
    # main_save_path = os.path.join(this_path, 'output', 'multi')
    #
    # gen_path(main_save_path)
    #
    # plot_multi_city_district(city=city_object, main_save_path=main_save_path)
