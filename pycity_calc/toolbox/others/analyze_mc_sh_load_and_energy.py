#!/usr/bin/env python
# coding=utf-8
"""
Script to analyze results of Monte-Carlo space heating demand uncertainty
analysis for single buiding and cities
"""

import os
import math
import copy
import pickle
import numpy as np
import scipy
import scipy.stats
import warnings
import shutil
import matplotlib.pyplot as plt

import ebc_ues_plot.hist_plot as ebchist
import ebc_ues_plot.line_plots as ebcline

import pycity_calc.toolbox.dimensioning.dim_functions as dimfunc

try:
    from matplotlib2tikz import save as tikz_save
except:
    msg = 'Could not import matplotlib2tikz'
    warnings.warn(msg)


class McCityRes(object):
    def __init__(self):
        """
        Constructor of results class of Monte-Carlo analysis of city districts

        Attributes
        ----------
        dict_res : dict
            Dictionary holding lists of mc results
            (list_sh, list_el, list_dhw, list_sh_curves)
            1. Entry: list holding net space heating demands in kWh as float
            2. Entry: list holding space heating power curves in W as arrays
            3. Entry: list holding net electric energy demands in kWh
            4. Entry: list holding hot water net energy demands in kWh
        dict_cities : dict
            Dictionary holding city objects (with name as key)
        """

        self.dict_res_mc_city = {}
        self.dict_res_mc_build = {}
        self.dict_cities = {}
        self.dict_build_ids = {}

    def add_res_list_mc_city(self, list_res, key):
        """
        Add results list

        Parameters
        ----------
        list_res : list
            List holding sample result lists
        key : str
            Key/name to add list to dictionary
        """

        self.dict_res_mc_city[key] = list_res

    def add_res_list_mc_build(self, list_res, key):
        """
        Add results list

        Parameters
        ----------
        list_res : list
            List holding sample result lists
        key : str
            Key/name to add list to dictionary
        """

        self.dict_res_mc_build[key] = list_res

    def add_res_mc_city_from_path(self, path, key):
        """
        Add result lists (mc city analysis)
        from path, where pickle file is stored

        Parameters
        ----------
        path : str
            Path to pickle file
        key : str
            Key/name to add list to dictionary
        """

        list_res = load_results_from_path(path=path)

        self.add_res_list_mc_city(list_res=list_res, key=key)

    def add_res_mc_build_from_path(self, path, key):
        """
        Add result lists (building mc analysis)
        from path, where pickle file is stored

        Parameters
        ----------
        path : str
            Path to pickle file
        key : str
            Key/name to add list to dictionary
        """

        list_res = load_results_from_path(path=path)

        self.add_res_list_mc_build(list_res=list_res, key=key)

    def add_city(self, key, city):
        """
        Add city object to results object

        Parameters
        ----------
        key : str
            Name of city
        city : object
            City object of pycity_calc
        """

        self.dict_cities[key] = city

    def get_results_mc_city(self, key):
        """
        Return results list (of mc analysis of city)

        Parameters
        ----------
        key : str
            Key/name to add list to dictionary

        Returns
        -------
        list_res : list
            List of result lists
            (list_sh, list_el, list_dhw, list_sh_curves)
            1. Entry: list holding net space heating demands in kWh as float
            2. Entry: list holding space heating power curves in W as arrays
            3. Entry: list holding net electric energy demands in kWh
            4. Entry: list holding hot water net energy demands in kWh
        """

        return self.dict_res_mc_city[key]

    def get_results_mc_build(self, key):
        """
        Return results list (of mc analysis of building)

        Parameters
        ----------
        key : str
            Key/name to add list to dictionary

        Returns
        -------
        list_res : list
            List of result lists
            (list_sh, list_el, list_dhw, list_sh_curves)
            1. Entry: list holding net space heating demands in kWh as float
            2. Entry: list holding space heating power curves in W as arrays
            3. Entry: list holding net electric energy demands in kWh
            4. Entry: list holding hot water net energy demands in kWh
        """

        return self.dict_res_mc_build[key]

    def get_city(self, key):
        """
        Return city with corresponding key

        Parameters
        ----------
        key : str
            Name of city (as key for dict)

        Returns
        -------
        city : object
            City object of pycity_calc
        """

        return self.dict_cities[key]


def gen_path(path):
    """
    Generates path, if not existent.

    Parameters
    ----------
    path : str
        Path
    """

    if not os.path.exists(path):
        os.makedirs(path)


def load_results_from_path(path):
    """
    Load results from path

    Parameters
    ----------
    path : str
        Path to results pickle file

    Returns
    -------
    list_res : list (of lists)
        List holding result lists.
        (list_sh, list_el, list_dhw, list_sh_curves)
        1. Entry: list holding net space heating demands in kWh as float
        2. Entry: list holding space heating power curves in W as arrays
        3. Entry: list holding net electric energy demands in kWh
        4. Entry: list holding hot water net energy demands in kWh
    """

    list_res = pickle.load(open(path, mode='rb'))

    return list_res


def calc_riqr(list_samples):
    """
    Calculate relative interquartile range (RIQR) of list of samples

    Parameters
    ----------
    list_samples : list (of floats)
        List with samples

    Returns
    -------
    riqr : float
        Relative interquartile range (RIQR)
    """

    median = np.median(list_samples)

    iqr = scipy.stats.iqr(list_samples)

    riqr = iqr / median

    return riqr


def calc_min_max_av_sh_load_curves(list_sh_curves):
    """
    Calculate minimum, maximum and average space heating load curves, based
    on list of space heating curves

    Parameters
    ----------
    list_sh_curves

    Returns
    -------
    tup_res : tuple (of arrays)
        Results tuple (min_array, max_array, av_array)
        1. Entry: Array with minimum space heating load per timestep in W
        2. Entry: Array with maximum space heating load per timestep in W
        3. Entry: Array with average space heating load per timestep in W
    """

    min_array = np.zeros(len(list_sh_curves[0])) + 100000000000000000000000000
    max_array = np.zeros(len(list_sh_curves[0]))
    av_array = np.zeros(len(list_sh_curves[0]))

    for i in range(len(list_sh_curves)):

        sh_array = list_sh_curves[i]

        for t in range(len(sh_array)):

            curr_sh_value = sh_array[t]

            if curr_sh_value < min_array[t]:
                min_array[t] = curr_sh_value
            elif curr_sh_value > max_array[t]:
                max_array[t] = curr_sh_value

    for t in range(len(av_array)):
        av_array[t] = (max_array[t] + min_array[t]) / 2

    return (min_array, max_array, av_array)


def calc_sh_power_to_cov_spec_share_runs(mc_res, share, key, build=True):
    """
    Calculate share of covered demand values

    Parameters
    ----------
    mc_res : object
        Mc analysis results object
    share : float
        Share of runs, that should be covered (e.g. 0.95 --> 95 % of runs)
    key : str
        key of city district
    build : bool, optional
        Use building instead of whole city (default: True)
        True: Use building
        False: Use city

    Returns
    -------
    sh_power : float
        Space heating power value in W
    """

    #  Extract space heating power arrays
    if build:
        list_sh_arrays = mc_res.get_results_mc_build(key=key)[1]
    else:
        list_sh_arrays = mc_res.get_results_mc_city(key=key)[1]

    #  Extract maximum power values in Watt
    list_sh_power = []
    for power in list_sh_arrays:
        list_sh_power.append(max(power))

    #  Sort list in ascending order
    list_sh_power.sort()

    total_nb = len(list_sh_power)

    idx = math.ceil(share * total_nb) - 1

    #  Extract thermal power values, which is required to cover share of runs
    cov_power = list_sh_power[idx]

    print('Required thermal space heating power to cover share of ' +
          str(share * 100) + ' % of area ' + str(key) + ' in kW:')
    print(cov_power / 1000)
    print()

    return cov_power


def calc_sh_coverage_cities(mc_res, list_shares=[0.9, 0.95, 0.98, 0.99, 1],
                            build=True):
    """
    Calculate all necessary power values to cover specific shares of runs
    given in list_shares for all city districts in mc_res.

    Parameters
    ----------
    mc_res : object
        Results object
    list_shares : list, optional
        List with desired share to be covered
        (default: [0.9, 0.95, 0.98, 0.99, 1])
        (e.g. single share 0.95 --> 95 % of runs)
    build : bool, optional
        Use building instead of whole city (default: True)
        True: Use building
        False: Use city

    Returns
    -------
    dict_cov_power_lists : dict (of lists)
        Dictionary holding coverage power values as floats (dict values)
        and city names as keys
    """

    dict_cov_power_lists = {}

    #  Loop over all districts
    for key in mc_res.dict_cities.keys():

        print()
        print('Key: ', key)

        list_cov_power = []

        for share in list_shares:

            print('Share: ', share)
            cov_power = \
                calc_sh_power_to_cov_spec_share_runs(mc_res=mc_res,
                                                     share=share,
                                                     key=key, build=build)

            list_cov_power.append(cov_power)

        dict_cov_power_lists[key] = list_cov_power

    return dict_cov_power_lists


def get_ref_sh_nom_powers(mc_res, build=True):
    """
    Extract reference space heating nomimal power values and mean power values

    Parameters
    ----------
    mc_res : object
        MC results object
    build : bool, optional
        Use building instead of whole city (default: True)
        True: Use building
        False: Use city

    Returns
    -------
    res_tuple : tuple (of dicts)
        Results tuple with (dict_ref_sh, dict_mean_sh)
        First dict holding reference space heating power values per district.
        Second dict holding mean space heating power values per district.
    """

    dict_ref_sh = {}
    dict_mean_sh = {}

    for key in mc_res.dict_cities.keys():

        print('Key: ', key)

        # Extract reference space heating power
        #  ##################################################################
        city = mc_res.get_city(key=key)

        if build:
            node_id = mc_res.dict_build_ids[key]

            curr_build = city.nodes[node_id]['entity']

            #  Get reference space heating nominal power
            q_sh_ref = dimfunc.get_max_power_of_building(building=curr_build,
                                                         get_therm=True,
                                                         with_dhw=False)
        else:
            q_sh_ref = dimfunc.get_max_p_of_city(city_object=city,
                                                 get_thermal=True,
                                                 with_dhw=False)

        print('Ref. space heating power in W: ')
        print(q_sh_ref)

        dict_ref_sh[key] = q_sh_ref

        #  Extract list of space heating power arrays
        if build:
            list_powers = mc_res.get_results_mc_build(key=key)[1]
        else:
            list_powers = mc_res.get_results_mc_city(key=key)[1]

        list_max_sh_p = []
        for power in list_powers:
            list_max_sh_p.append(max(power))

        mean = np.mean(list_max_sh_p)

        print('Mean power value in W:')
        print(mean)
        print('Median power value in W:')
        print(np.median(list_max_sh_p))

        list_max_sh_p.sort()

        count_cov_val = 0
        for pow in list_max_sh_p:
            if pow <= q_sh_ref:
                count_cov_val += 1
            else:
                break

        print('Share of covered power values based on reference space heating'
              ' power value: ')
        print(count_cov_val/len(list_max_sh_p))
        print()

        dict_mean_sh[key] = mean

    return (dict_ref_sh, dict_mean_sh)


def do_sh_load_analysis(mc_res, key, output_path, output_filename, dpi=300,
                        mc_city=True, fontsize=12):
    """

    Parameters
    ----------
    mc_res
    key
    output_path
    output_filename
    dpi
    mc_city : bool, optional

    Returns
    -------

    """

    if mc_city:
        #  Extract list with space heating arrays
        list_sh_curves = mc_res.get_results_mc_city(key=key)[1]
    else:
        list_sh_curves = mc_res.get_results_mc_build(key=key)[1]

    #  Sort list by sum of arrays
    list_sh_curves.sort(key=sum, reverse=True)

    (min_array, max_array, av_array) = \
        calc_min_max_av_sh_load_curves(list_sh_curves=list_sh_curves)

    plt.rc('font', family='Arial', size=fontsize)

    fig = plt.figure(figsize=(5, 3), dpi=dpi)

    ax = fig.gca()

    for sh_curve in list_sh_curves:
        plt.plot(sh_curve / 1000, alpha=1, linewidth=1)

    # plt.plot(min_array/1000, color='black', linewidth=0.5)
    # plt.plot(max_array/1000, color='black', linewidth=0.5)
    # plt.plot(av_array/1000, color='black', linewidth=0.5)

    ax.set_xlim([0, 8760])
    # ax.set_ylim([0, 800])

    plt.xlabel('Time in hours')
    plt.ylabel('Thermal power in kW')

    plt.tight_layout()

    gen_path(output_path)

    #  Generate file names for different formats
    file_pdf = output_filename + '.pdf'
    file_eps = output_filename + '.eps'
    file_png = output_filename + '.png'
    file_tiff = output_filename + '.tiff'
    file_tikz = output_filename + '.tikz'

    #  Generate saving pathes
    path_pdf = os.path.join(output_path, file_pdf)
    path_eps = os.path.join(output_path, file_eps)
    path_png = os.path.join(output_path, file_png)
    path_tiff = os.path.join(output_path, file_tiff)
    path_tikz = os.path.join(output_path, file_tikz)

    #  Save figure in different formats
    plt.savefig(path_pdf, format='pdf', dpi=dpi)
    plt.savefig(path_eps, format='eps', dpi=dpi)
    plt.savefig(path_png, format='png', dpi=dpi)
    # plt.savefig(path_tiff, format='tiff', dpi=dpi)
    tikz_save(path_tikz, figureheight='\\figureheight',
              figurewidth='\\figurewidth')

    # plt.show()
    plt.close()

    fig = plt.figure(figsize=(5, 3), dpi=dpi)

    ax = fig.gca()

    plt.plot(max_array / 1000, color='#E53027', linewidth=1, label='Maximum')
    plt.plot(min_array / 1000, color='#1058B0', linewidth=1, label='Minimum')

    ax.set_xlim([0, 8760])
    ax.set_ylim([0, 800])

    plt.xlabel('Time in hours')
    plt.ylabel('Thermal power in kW')
    plt.legend(loc='best')

    plt.tight_layout()

    gen_path(output_path)

    output_filename = output_filename + '_min_max'

    #  Generate file names for different formats
    file_pdf = output_filename + '.pdf'
    file_eps = output_filename + '.eps'
    file_png = output_filename + '.png'
    file_tiff = output_filename + '.tiff'
    file_tikz = output_filename + '.tikz'

    #  Generate saving pathes
    path_pdf = os.path.join(output_path, file_pdf)
    path_eps = os.path.join(output_path, file_eps)
    path_png = os.path.join(output_path, file_png)
    path_tiff = os.path.join(output_path, file_tiff)
    path_tikz = os.path.join(output_path, file_tikz)

    #  Save figure in different formats
    plt.savefig(path_pdf, format='pdf', dpi=dpi)
    plt.savefig(path_eps, format='eps', dpi=dpi)
    plt.savefig(path_png, format='png', dpi=dpi)
    # plt.savefig(path_tiff, format='tiff', dpi=dpi)
    tikz_save(path_tikz, figureheight='\\figureheight',
              figurewidth='\\figurewidth')

    # plt.show()
    plt.close()


def analyze_demands_hist(mc_res, key, mode, output_path, dpi=1000,
                        mc_city=True, fontsize=12):
    """

    Parameters
    ----------
    mc_res
    key
    mode : str
        Mode for histogram analysis. Options:
        - 'sh' : space heating
        - 'el' : electric demand
        - 'dhw' : Hot water
    output_path
    dpi
    mc_city
    fontsize

    Returns
    -------

    """

    assert mode in ['sh', 'el', 'dhw']

    if mode == 'sh':
        midx = 0
    elif mode == 'el':
        midx = 2
    elif mode == 'dhw':
        midx = 3

    if mc_city:
        #  Extract list with sampling demand values in kWh
        list_dem = mc_res.get_results_mc_city(key=key)[midx]
    else:
        list_dem = mc_res.get_results_mc_build(key=key)[midx]

    #  Extract reference demand
    #  ##################################################################

    #  Extract city
    city = mc_res.get_city(key=key)

    if mc_city:
        #  Get reference  demand in kWh (per building)
        if mode == 'sh':
            ref_dem = city.get_annual_space_heating_demand()
        elif mode == 'el':
            ref_dem = city.get_annual_el_demand()
        elif mode == 'dhw':
            ref_dem = city.get_annual_dhw_demand()

    else:
        node_id = mc_res.dict_build_ids[key]

        curr_build = city.nodes[node_id]['entity']

        #  Get reference  demand in kWh (per building)
        if mode == 'sh':
            ref_dem = curr_build.get_annual_space_heat_demand()
        elif mode == 'el':
            ref_dem = curr_build.get_annual_el_demand()
        elif mode == 'dhw':
            ref_dem = curr_build.get_annual_dhw_demand()


    dict_v_lines = {}
    dict_v_lines['Reference'] = ref_dem

    #  Get reference  demand in kWh (per building)
    if mode == 'sh':
        e_name = 'net space heating energy'
    elif mode == 'el':
        e_name = 'el. energy demand'
    elif mode == 'dhw':
        e_name = 'hot water energy demand'

    print()
    print('Mean ' + str(e_name) + ' value in kWh:')
    mean = np.mean(list_dem)
    print(mean)
    print()

    print('Standard deviation of ' + str(e_name) + ' value in kWh:')
    stdev = np.std(a=list_dem)
    print()

    print('Median  ' + str(e_name) + '  value in kWh:')
    median = np.median(a=list_dem)
    print(median)
    print()

    print('Interquartile range (IQR):')
    iqr = scipy.stats.iqr(x=list_dem)
    print(iqr)
    print()

    print('Relative interquartile range (RIQR):')
    riqr = iqr / median
    print(riqr)
    print()

    print('95 % confidence interval for single draw:')
    conf_int = scipy.stats.norm.interval(0.95, loc=mean, scale=stdev)
    print(conf_int)
    print()

    #  EBC hist plot
    #  English infos
    title_engl = None  # Add 'u' in front of string to define it as unicode
    # (e.g. when using non-ascii characters)
    #  Get reference  demand in kWh (per building)
    if mode == 'sh':
        xlab_engl = 'Space heating demand in kWh'
        ylab_engl = 'Number of demand values'
    elif mode == 'el':
        xlab_engl = 'Electric energy demand in kWh'
        ylab_engl = 'Number of demand values'
    elif mode == 'dhw':
        xlab_engl = 'Hot water energy demand in kWh'
        ylab_engl = 'Number of demand values'

    #  German infos
    title_dt = None  # Add 'u' in front of string to define it as unicode
    # (e.g. when using non-ascii characters)
    if mode == 'sh':
        xlab_dt = 'Raumwärmebedarf in kWh'
        ylab_dt = 'Anzahl Energiebedarfswerte'
    elif mode == 'el':
        xlab_dt = 'Elektrischer Energiebedarf in kWh'
        ylab_dt = 'Anzahl Energiebedarfswerte'
    elif mode == 'dhw':
        xlab_dt = 'Warmwasserenergiebedarf in kWh'
        ylab_dt = 'Anzahl Energiebedarfswerte'
    #  ylab only used if plot_sub == False

    #  Plot figures?
    show_plot = False

    #  Use tight layout?
    use_tight = True

    #  Adjust figure size to default (None), 'a4' or 'a4_half', 'a5'
    fig_adjust = 'a5'  # 'a4_half', 'a5'
    #  fig_adjust = None  # default

    #  Font type
    # use_font = 'tex'  # Latex font
    use_font = 'arial'  # Arial font
    #  Pre-defines used font in matplotlib rc parameters
    #  Options:
    #  - 'tex' : Use Latex fonts in plots
    #  - 'arial' : Use arial fonts

    #  Copy Python code into output folder?
    copy_py = True

    #  Additionally save as tikz for latex?
    save_tikz = True

    #  Save data array as pickle file?
    save_data_array = True

    #  Rotate x labels?
    rotate_x_labels = False

    plot_edgecolor = True

    plot_mean = True

    plot_std = True

    if mc_city:
        addname = '_city'
    else:
        addname = '_build_id_' + str(node_id)

    #  Get reference  demand in kWh (per building)
    if mode == 'sh':
        output_filename = key + '_sh_demand' + addname
    elif mode == 'el':
        output_filename = key + '_el_demand' + addname
    elif mode == 'dhw':
        output_filename = key + '_dhw_demand' + addname

    #  #--------------------------------------------------------------

    ebchist.plot_multi_lang_multi_color_hist(list_data=list_dem,
                                             output_path=output_path,
                                             output_filename=output_filename,
                                             show_plot=show_plot,
                                             use_tight=use_tight,
                                             title_engl=title_engl,
                                             xlab_engl=xlab_engl,
                                             ylab_engl=ylab_engl,
                                             title_dt=title_dt,
                                             xlab_dt=xlab_dt,
                                             ylab_dt=ylab_dt,
                                             fontsize=fontsize,
                                             fig_adjust=fig_adjust,
                                             dpi=dpi, copy_py=copy_py,
                                             save_data_array=save_data_array,
                                             save_tikz=save_tikz,
                                             rotate_x_labels=rotate_x_labels,
                                             use_font=use_font,
                                             plot_edgecolor=plot_edgecolor,
                                             plot_mean=plot_mean,
                                             plot_std=plot_std,
                                             dict_v_lines=dict_v_lines
                                             )


def analyze_sh_powers_hist(mc_res, key, output_path):
    """

    Parameters
    ----------
    mc_res
    key
    output_path

    Returns
    -------

    """

    #  Extract space heating load curves
    #  ##################################################################
    list_sh_curves = mc_res.get_results(key=key)[1]

    list_sh_power = []
    for power in list_sh_curves:
        list_sh_power.append(max(power) / 1000)

    # Extract reference space heating power
    #  ##################################################################
    city = mc_res.get_city(key=key)
    node_id = mc_res.dict_build_ids[key]

    curr_build = city.nodes[node_id]['entity']

    #  Get reference space heating nominal power
    q_sh_ref = dimfunc.get_max_power_of_building(building=curr_build,
                                                 get_therm=True,
                                                 with_dhw=False) / 1000
    dict_v_lines = {}
    dict_v_lines['Reference'] = q_sh_ref

    print()
    print('Mean max. space heating power in kW:')
    mean = np.mean(list_sh_power)
    print(mean)
    print()

    print('Standard deviation of max. space heating power in kW:')
    stdev = np.std(a=list_sh_power)
    print()

    print('Median max. space heating power in kW:')
    median = np.median(a=list_sh_power)
    print(median)
    print()

    print('Interquartile range (IQR):')
    iqr = scipy.stats.iqr(x=list_sh_power)
    print(iqr)
    print()

    print('Relative interquartile range (RIQR):')
    riqr = iqr / median
    print(riqr)
    print()

    print('95 % confidence interval for single draw:')
    conf_int = scipy.stats.norm.interval(0.95, loc=mean, scale=stdev)
    print(conf_int)
    print()

    #  EBC hist plot
    #  English infos
    title_engl = None  # Add 'u' in front of string to define it as unicode
    # (e.g. when using non-ascii characters)
    xlab_engl = 'Maximum space heating power in kW'
    ylab_engl = 'Number of power values'

    #  German infos
    title_dt = None  # Add 'u' in front of string to define it as unicode
    # (e.g. when using non-ascii characters)
    xlab_dt = 'Spitzenheizleistung in kW'
    ylab_dt = 'Anzahl Leistungswerte'
    #  ylab only used if plot_sub == False

    #  Fontsize
    fontsize = 12
    #  dpi size
    dpi = 1000
    #  Linewidth
    linewidth = 1

    #  Plot figures?
    show_plot = False

    #  Use tight layout?
    use_tight = True

    #  Adjust figure size to default (None), 'a4' or 'a4_half', 'a5'
    fig_adjust = 'a5'  # 'a4_half', 'a5'
    #  fig_adjust = None  # default

    #  Font type
    # use_font = 'tex'  # Latex font
    use_font = 'arial'  # Arial font
    #  Pre-defines used font in matplotlib rc parameters
    #  Options:
    #  - 'tex' : Use Latex fonts in plots
    #  - 'arial' : Use arial fonts

    #  Copy Python code into output folder?
    copy_py = True

    #  Additionally save as tikz for latex?
    save_tikz = True

    #  Save data array as pickle file?
    save_data_array = True

    #  Rotate x labels?
    rotate_x_labels = False

    plot_edgecolor = True

    plot_mean = True

    plot_std = True

    output_filename = key + '_sh_power'

    #  #--------------------------------------------------------------

    ebchist.plot_multi_lang_multi_color_hist(list_data=list_sh_power,
                                             output_path=output_path,
                                             output_filename=output_filename,
                                             show_plot=show_plot,
                                             use_tight=use_tight,
                                             title_engl=title_engl,
                                             xlab_engl=xlab_engl,
                                             ylab_engl=ylab_engl,
                                             title_dt=title_dt,
                                             xlab_dt=xlab_dt,
                                             ylab_dt=ylab_dt,
                                             fontsize=fontsize,
                                             fig_adjust=fig_adjust,
                                             dpi=dpi, copy_py=copy_py,
                                             save_data_array=save_data_array,
                                             save_tikz=save_tikz,
                                             rotate_x_labels=rotate_x_labels,
                                             use_font=use_font,
                                             plot_edgecolor=plot_edgecolor,
                                             plot_mean=plot_mean,
                                             plot_std=plot_std,
                                             dict_v_lines=dict_v_lines)


# def box_plot_analysis(mc_res, output_path, output_filename, with_outliners,
#                       list_order,
#                       dpi=100):
#     """
#
#     Parameters
#     ----------
#     mc_res
#     output_path
#     output_filename
#     with_outliners
#     list_order
#     dpi
#
#     Returns
#     -------
#
#     """
#
#     gen_path(output_path)
#
#     data_coll = []
#     list_xticks = []
#     list_riqr = []
#
#     for key in list_order:
#
#         list_sh_en = copy.deepcopy(mc_res.get_results(key=key)[0])
#
#         #  Convert kWh to MWh
#         for i in range(len(list_sh_en)):
#             list_sh_en[i] /= 1000
#
#         # Add space heating lists
#         data_coll.append(list_sh_en)
#
#         list_xticks.append(key)
#
#         #  Calc RIQR
#         riqr = calc_riqr(list_sh_en)
#         print('riqr')
#         print(riqr)
#         print('for key: ', key)
#         print()
#         list_riqr.append(riqr)
#
#     # for key in mc_res.dict_res.keys():
#     #
#     #     list_sh_en = copy.deepcopy(mc_res.get_results(key=key)[0])
#     #
#     #     #  Convert kWh to MWh
#     #     for i in range(len(list_sh_en)):
#     #         list_sh_en[i] /= 1000
#     #
#     #     # Add space heating lists
#     #     data_coll.append(list_sh_en)
#     #
#     #     list_xticks.append(key)
#     #
#     #     #  Calc RIQR
#     #     riqr = calc_riqr(list_sh_en)
#     #     print('riqr')
#     #     print(riqr)
#     #     print('for key: ', key)
#     #     print()
#     #     list_riqr.append(riqr)
#
#     # # Sort by space heating demands
#     # data_coll, list_xticks, list_riqr = zip(
#     #     *sorted(zip(data_coll, list_xticks, list_riqr)))
#
#     plt.rc('font', family='Arial', size=12)
#
#     fig = plt.figure(figsize=(5, 3), dpi=dpi)
#
#     ax = fig.gca()
#
#     pb = ax.boxplot(data_coll, showfliers=with_outliners)
#
#     ax.set_xticklabels(list_xticks)
#
#     for median in pb['medians']:
#         median.set(color='#E53027')
#
#     for flier in pb['fliers']:
#         flier.set(marker='*', markersize=0.5)
#
#     fig.autofmt_xdate()
#     plt.tight_layout()
#     plt.ylabel('Net space heating\ndemand in MWh')
#
#     #  Generate file names for different formats
#     file_pdf = output_filename + '.pdf'
#     file_eps = output_filename + '.eps'
#     file_png = output_filename + '.png'
#     file_tiff = output_filename + '.tiff'
#     file_tikz = output_filename + '.tikz'
#
#     #  Generate saving pathes
#     path_pdf = os.path.join(output_path, file_pdf)
#     path_eps = os.path.join(output_path, file_eps)
#     path_png = os.path.join(output_path, file_png)
#     path_tiff = os.path.join(output_path, file_tiff)
#     path_tikz = os.path.join(output_path, file_tikz)
#
#     #  Save figure in different formats
#     plt.savefig(path_pdf, format='pdf', dpi=dpi)
#     plt.savefig(path_eps, format='eps', dpi=dpi)
#     plt.savefig(path_png, format='png', dpi=dpi)
#     # plt.savefig(path_tiff, format='tiff', dpi=dpi)
#     tikz_save(path_tikz, figureheight='\\figureheight',
#               figurewidth='\\figurewidth')
#
#     # plt.show()
#     plt.close()
#
#
# def box_plot_analysis_double_plot(mc_res, output_path, output_filename,
#                                   list_order,
#                                   dpi=100, with_outliners=True):
#     """
#
#     Parameters
#     ----------
#     mc_res
#     output_path
#     output_filename
#     list_order
#     dpi
#     with_outliners
#
#     Returns
#     -------
#
#     """
#
#     gen_path(output_path)
#
#     data_coll = []
#     list_xticks = []
#     list_riqr = []
#
#     for key in list_order:
#
#         list_sh_en = copy.deepcopy(mc_res.get_results(key=key)[0])
#
#         #  Convert kWh to MWh
#         for i in range(len(list_sh_en)):
#             list_sh_en[i] /= 1000
#
#         # Add space heating lists
#         data_coll.append(list_sh_en)
#
#         list_xticks.append(key)
#
#         #  Calc RIQR
#         riqr = calc_riqr(list_sh_en)
#         print('riqr')
#         print(riqr)
#         print('for key: ', key)
#         print()
#         list_riqr.append(riqr)
#
#
#     # for key in mc_res.dict_res.keys():
#     #
#     #     list_sh_en = copy.deepcopy(mc_res.get_results(key=key)[0])
#     #
#     #     #  Convert kWh to MWh
#     #     for i in range(len(list_sh_en)):
#     #         list_sh_en[i] /= 1000
#     #
#     #     # Add space heating lists
#     #     data_coll.append(list_sh_en)
#     #
#     #     list_xticks.append(key)
#     #
#     #     #  Calc RIQR
#     #     riqr = calc_riqr(list_sh_en)
#     #     print('riqr')
#     #     print(riqr)
#     #     print('for key: ', key)
#     #     print()
#     #     list_riqr.append(riqr)
#     #
#     # # Sort by space heating demands
#     # data_coll, list_xticks, list_riqr = zip(
#     #     *sorted(zip(data_coll, list_xticks, list_riqr)))
#
#     plt.rc('font', family='Arial', size=12)
#
#     fig = plt.figure(figsize=(5, 3), dpi=dpi)
#
#     fig.add_subplot(121)
#
#     ax = fig.gca()
#
#     pb = ax.boxplot(data_coll[0:4], showfliers=with_outliners)
#     plt.ylabel('Net space heating\ndemand in MWh')
#     ax.set_xticklabels(list_xticks[0:4])
#
#     for median in pb['medians']:
#         median.set(color='#E53027')
#
#     for flier in pb['fliers']:
#         flier.set(marker='*', markersize=0.5)
#
#     fig.add_subplot(122)
#
#     ax = fig.gca()
#
#     pb = ax.boxplot(data_coll[4:6], showfliers=with_outliners)
#     plt.ylabel('Net space heating\ndemand in MWh')
#     ax.set_xticklabels(list_xticks[4:6])
#
#     for median in pb['medians']:
#         median.set(color='#E53027')
#
#     for flier in pb['fliers']:
#         flier.set(marker='*', markersize=0.5)
#
#     fig.autofmt_xdate()
#     plt.tight_layout()
#
#     gen_path(output_path)
#
#     #  Generate file names for different formats
#     file_pdf = output_filename + '.pdf'
#     file_eps = output_filename + '.eps'
#     file_png = output_filename + '.png'
#     file_tiff = output_filename + '.tiff'
#     file_tikz = output_filename + '.tikz'
#
#     #  Generate saving pathes
#     path_pdf = os.path.join(output_path, file_pdf)
#     path_eps = os.path.join(output_path, file_eps)
#     path_png = os.path.join(output_path, file_png)
#     path_tiff = os.path.join(output_path, file_tiff)
#     path_tikz = os.path.join(output_path, file_tikz)
#
#     #  Save figure in different formats
#     plt.savefig(path_pdf, format='pdf', dpi=dpi)
#     plt.savefig(path_eps, format='eps', dpi=dpi)
#     plt.savefig(path_png, format='png', dpi=dpi)
#     # plt.savefig(path_tiff, format='tiff', dpi=dpi)
#     tikz_save(path_tikz, figureheight='\\figureheight',
#               figurewidth='\\figurewidth')
#
#     # plt.show()
#     plt.close()


def box_plot_analysis_triple_plot(mc_res, output_path, output_filename,
                                  list_order, mode, mc_city=True,
                                  dpi=1000, with_outliners=True):
    """

    Parameters
    ----------
    mc_res
    output_path
    output_filename
    list_order
    mode : str
        Mode for histogram analysis. Options:
        - 'sh' : space heating
        - 'el' : electric demand
        - 'dhw' : Hot water
    mc_city : bool, optional
    dpi
    with_outliners

    Returns
    -------

    """

    assert mode in ['sh', 'el', 'dhw']

    #  Get reference  demand in kWh (per building)
    if mode == 'sh':
        e_name = 'net space heating energy'
    elif mode == 'el':
        e_name = 'el. energy demand'
    elif mode == 'dhw':
        e_name = 'hot water energy demand'

    gen_path(output_path)

    data_coll = []
    list_xticks = []
    list_riqr = []
    list_ref_values = []

    for key in list_order:

        print('Key: ', key)

        if mc_city:
            if mode == 'sh':
                list_energy = \
                    copy.deepcopy(mc_res.get_results_mc_city(key=key)[0])
            elif mode == 'el':
                list_energy = \
                    copy.deepcopy(mc_res.get_results_mc_city(key=key)[2])
            elif mode == 'dhw':
                list_energy = \
                    copy.deepcopy(mc_res.get_results_mc_city(key=key)[3])
        else:
            if mode == 'sh':
                list_energy = \
                    copy.deepcopy(mc_res.get_results_mc_build(key=key)[0])
            elif mode == 'el':
                list_energy = \
                    copy.deepcopy(mc_res.get_results_mc_build(key=key)[2])
            elif mode == 'dhw':
                list_energy = \
                    copy.deepcopy(mc_res.get_results_mc_build(key=key)[3])

        #  Convert kWh to MWh
        for i in range(len(list_energy)):
            list_energy[i] /= 1000

        # Add energy lists
        data_coll.append(list_energy)

        list_xticks.append(key)

        #  Get reference demand
        curr_city = mc_res.dict_cities[key]

        if mc_city:
            if mode == 'sh':
                ref_dem = \
                    curr_city.get_annual_space_heating_demand() / 1000
                    # in MWh
            elif mode == 'el':
                ref_dem = \
                    curr_city.get_annual_el_demand() / 1000
                # in MWh
            elif mode == 'dhw':
                ref_dem = \
                    curr_city.get_annual_dhw_demand() / 1000
        else:
            curr_id = mc_res.dict_build_ids[key]
            curr_build = curr_city.nodes[curr_id]['entity']
            if mode == 'sh':
                ref_dem = \
                    curr_build.get_annual_space_heat_demand() / 1000
                    # in MWh
            elif mode == 'el':
                ref_dem = \
                    curr_build.get_annual_el_demand() / 1000
                # in MWh
            elif mode == 'dhw':
                ref_dem = \
                    curr_build.get_annual_dhw_demand() / 1000

        list_ref_values.append(ref_dem)

        print('Reference ' + str(e_name) +' in MWh:')
        print(ref_dem)

        #  Calc RIQR
        riqr = calc_riqr(list_energy)
        print('riqr')
        print(riqr)
        print('for key: ', key)
        print()
        list_riqr.append(riqr)


    # for key in mc_res.dict_res.keys():
    #
    #     list_sh_en = copy.deepcopy(mc_res.get_results(key=key)[0])
    #
    #     #  Convert kWh to MWh
    #     for i in range(len(list_sh_en)):
    #         list_sh_en[i] /= 1000
    #
    #     # Add space heating lists
    #     data_coll.append(list_sh_en)
    #
    #     list_xticks.append(key)
    #
    #     #  Calc RIQR
    #     riqr = calc_riqr(list_sh_en)
    #     print('riqr')
    #     print(riqr)
    #     print('for key: ', key)
    #     print()
    #     list_riqr.append(riqr)
    #
    # # Sort by space heating demands
    # data_coll, list_xticks, list_riqr = zip(
    #     *sorted(zip(data_coll, list_xticks, list_riqr)))



    plt.rc('font', family='Arial', size=fontsize)

    fig = plt.figure(figsize=(5, 3), dpi=dpi)

    #  Subplot 1
    #  #################################################################
    fig.add_subplot(131)

    ax = fig.gca()

    pb = ax.boxplot(data_coll[0:2], showfliers=with_outliners,
                    widths=(0.8, 0.8))
    if mode == 'sh':
        plt.ylabel('Net space heating\ndemand in MWh')
    elif mode == 'el':
        plt.ylabel('Electric energy\ndemand in MWh')
    elif mode == 'dhw':
        plt.ylabel('Hot water\ndemand in MWh')

    ax.set_xticklabels(list_xticks[0:2])

    ax.plot([0.6, 1.4], [list_ref_values[0], list_ref_values[0]],
            label='Reference', color='#1058B0',
            linewidth=1)
    ax.plot([1.6, 2.4], [list_ref_values[1], list_ref_values[1]],
            label='Reference', color='#1058B0',
            linewidth=1)

    def get_start_stop_step(ax):

        start, end = ax.get_ylim()
        print(start)
        print(end)
        # start = round(start / 100, ndigits=0) * 100
        start = 0
        if end < 50:
            end = round(end / 10, ndigits=0) * 10
            stepsize = 5
        elif end < 150:
            end = round(end / 10, ndigits=0) * 10
            stepsize = 10
        elif end < 240:
            end = round(end / 10, ndigits=0) * 10
            stepsize = 20
        elif end < 500:
            end = round(end / 100, ndigits=0) * 100
            stepsize = 50
        elif end < 1500:
            end = round(end / 100, ndigits=0) * 100
            stepsize = 100
        elif end < 2400:
            end = round(end / 100, ndigits=0) * 100
            stepsize = 200
        elif end < 5000:
            end = round(end / 1000, ndigits=0) * 1000
            stepsize = 500
        else:
            end = round(end / 1000, ndigits=0) * 1000
            stepsize = 1000

        return (start, end, stepsize)

    (start, end, stepsize) = get_start_stop_step(ax)

    ax.yaxis.set_ticks(np.arange(start, end, stepsize))

    for median in pb['medians']:
        median.set(color='#E53027')

    for flier in pb['fliers']:
        flier.set(marker='.', markersize=1)

    #  Subplot 2
    #  #################################################################
    fig.add_subplot(132)

    ax = fig.gca()

    pb = ax.boxplot(data_coll[2:4], showfliers=with_outliners,
                    widths=(0.8, 0.8))
    ax.set_xticklabels(list_xticks[2:4])

    ax.plot([0.6, 1.4], [list_ref_values[2], list_ref_values[2]],
            label='Reference', color='#1058B0',
            linewidth=1)
    ax.plot([1.6, 2.4], [list_ref_values[3], list_ref_values[3]],
            label='Reference', color='#1058B0',
            linewidth=1)

    (start, end, stepsize) = get_start_stop_step(ax)

    ax.yaxis.set_ticks(np.arange(start, end, stepsize))

    for median in pb['medians']:
        median.set(color='#E53027')

    for flier in pb['fliers']:
        flier.set(marker='.', markersize=1)

    #  Subplot 3
    #  #################################################################
    fig.add_subplot(133)

    ax = fig.gca()

    pb = ax.boxplot(data_coll[4:6], showfliers=with_outliners,
                    widths=(0.8, 0.8))
    ax.set_xticklabels(list_xticks[4:6])

    ax.plot([0.6, 1.4], [list_ref_values[4], list_ref_values[4]],
            label='Reference', color='#1058B0',
            linewidth=1)
    ax.plot([1.6, 2.4], [list_ref_values[5], list_ref_values[5]],
            label='Reference', color='#1058B0',
            linewidth=1)

    (start, end, stepsize) = get_start_stop_step(ax)

    ax.yaxis.set_ticks(np.arange(start, end, stepsize))

    for median in pb['medians']:
        median.set(color='#E53027')

    for flier in pb['fliers']:
        flier.set(marker='.', markersize=1)

    fig.autofmt_xdate()

    plt.tight_layout()



    #  Generate legend
    import matplotlib.lines as mlines
    #  Generate proxy arist for legend
    median_proxy = mlines.Line2D([], [], color='#E53027', label='Median')
    ref_proxy = mlines.Line2D([], [], color='#1058B0', label='Reference')

    box_factor = 0.1
    for ax in fig.axes:
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * box_factor,
                         box.width, box.height * (1 - box_factor)])

    #  Put a legend below current axis
    lgd = ax.legend(handles=[median_proxy, ref_proxy],
                    loc='upper center', bbox_to_anchor=(-1.8, -0.4), ncol=2)

    # plt.legend(handles=[median_proxy, ref_proxy], loc='best')



    gen_path(output_path)

    #  Generate file names for different formats
    file_pdf = output_filename + '.pdf'
    file_eps = output_filename + '.eps'
    file_png = output_filename + '.png'
    file_tiff = output_filename + '.tiff'
    file_tikz = output_filename + '.tikz'

    #  Generate saving pathes
    path_pdf = os.path.join(output_path, file_pdf)
    path_eps = os.path.join(output_path, file_eps)
    path_png = os.path.join(output_path, file_png)
    path_tiff = os.path.join(output_path, file_tiff)
    path_tikz = os.path.join(output_path, file_tikz)

    #  Save figure in different formats
    plt.savefig(path_pdf, format='pdf')
    plt.savefig(path_eps, format='eps')
    plt.savefig(path_png, format='png')
    # plt.savefig(path_tiff, format='tiff', dpi=dpi)
    tikz_save(path_tikz, figureheight='\\figureheight',
              figurewidth='\\figurewidth')

    # plt.show()
    plt.close()


# def box_plot_analysis_el_dem(mc_res, output_path, output_filename,
#                              with_outliners, list_order, dpi=100):
#     """
#     Perform box plot analysis for electrical demand
#
#     Parameters
#     ----------
#     mc_res
#     output_path
#     output_filename
#     with_outliners
#     list_order
#     dpi
#
#     Returns
#     -------
#
#     """
#
#     gen_path(output_path)
#
#     data_coll = []
#     list_xticks = []
#     list_riqr = []
#
#     for key in list_order:
#
#         list_el_en = copy.deepcopy(mc_res.get_results(key=key)[2])
#
#         #  Convert kWh to MWh
#         for i in range(len(list_el_en)):
#             list_el_en[i] /= 1000
#
#         # Add space heating lists
#         data_coll.append(list_el_en)
#
#         list_xticks.append(key)
#
#         #  Calc RIQR
#         riqr = calc_riqr(list_el_en)
#         print('riqr')
#         print(riqr)
#         print('for key: ', key)
#         print()
#         list_riqr.append(riqr)
#
#     # for key in mc_res.dict_res.keys():
#     #
#     #     list_el_en = copy.deepcopy(mc_res.get_results(key=key)[2])
#     #
#     #     #  Convert kWh to MWh
#     #     for i in range(len(list_el_en)):
#     #         list_el_en[i] /= 1000
#     #
#     #     # Add space heating lists
#     #     data_coll.append(list_el_en)
#     #
#     #     list_xticks.append(key)
#     #
#     #     #  Calc RIQR
#     #     riqr = calc_riqr(list_el_en)
#     #     print('riqr')
#     #     print(riqr)
#     #     print('for key: ', key)
#     #     print()
#     #     list_riqr.append(riqr)
#     #
#     # # Sort by space heating demands
#     # data_coll, list_xticks, list_riqr = zip(
#     #     *sorted(zip(data_coll, list_xticks, list_riqr)))
#
#     plt.rc('font', family='Arial', size=12)
#
#     fig = plt.figure(figsize=(5, 3), dpi=dpi)
#
#     ax = fig.gca()
#
#     pb = ax.boxplot(data_coll, showfliers=with_outliners)
#
#     ax.set_xticklabels(list_xticks)
#
#     for median in pb['medians']:
#         median.set(color='#E53027')
#
#     for flier in pb['fliers']:
#         flier.set(marker='*', markersize=0.5)
#
#     fig.autofmt_xdate()
#     plt.tight_layout()
#     plt.ylabel('Electric demand in MWh')
#
#     #  Generate file names for different formats
#     file_pdf = output_filename + '.pdf'
#     file_eps = output_filename + '.eps'
#     file_png = output_filename + '.png'
#     file_tiff = output_filename + '.tiff'
#     file_tikz = output_filename + '.tikz'
#
#     #  Generate saving pathes
#     path_pdf = os.path.join(output_path, file_pdf)
#     path_eps = os.path.join(output_path, file_eps)
#     path_png = os.path.join(output_path, file_png)
#     path_tiff = os.path.join(output_path, file_tiff)
#     path_tikz = os.path.join(output_path, file_tikz)
#
#     #  Save figure in different formats
#     plt.savefig(path_pdf, format='pdf', dpi=dpi)
#     plt.savefig(path_eps, format='eps', dpi=dpi)
#     plt.savefig(path_png, format='png', dpi=dpi)
#     # plt.savefig(path_tiff, format='tiff', dpi=dpi)
#     tikz_save(path_tikz, figureheight='\\figureheight',
#               figurewidth='\\figurewidth')
#
#     # plt.show()
#     plt.close()
#
#
# def box_plot_analysis_double_plot_el_dem(mc_res, output_path,
#                                          output_filename, list_order,
#                                          dpi=100, with_outliners=True):
#     """
#
#     Parameters
#     ----------
#     mc_res
#     output_path
#     output_filename
#     list_order
#     dpi
#     with_outliners
#
#     Returns
#     -------
#
#     """
#
#     gen_path(output_path)
#
#     data_coll = []
#     list_xticks = []
#     list_riqr = []
#
#     for key in list_order:
#
#         list_el_en = copy.deepcopy(mc_res.get_results(key=key)[2])
#
#         #  Convert kWh to MWh
#         for i in range(len(list_el_en)):
#             list_el_en[i] /= 1000
#
#         # Add space heating lists
#         data_coll.append(list_el_en)
#
#         list_xticks.append(key)
#
#         #  Calc RIQR
#         riqr = calc_riqr(list_el_en)
#         print('riqr')
#         print(riqr)
#         print('for key: ', key)
#         print()
#         list_riqr.append(riqr)
#
#     # for key in mc_res.dict_res.keys():
#     #
#     #     list_el_en = copy.deepcopy(mc_res.get_results(key=key)[2])
#     #
#     #     #  Convert kWh to MWh
#     #     for i in range(len(list_el_en)):
#     #         list_el_en[i] /= 1000
#     #
#     #     # Add space heating lists
#     #     data_coll.append(list_el_en)
#     #
#     #     list_xticks.append(key)
#     #
#     #     #  Calc RIQR
#     #     riqr = calc_riqr(list_el_en)
#     #     print('riqr')
#     #     print(riqr)
#     #     print('for key: ', key)
#     #     print()
#     #     list_riqr.append(riqr)
#     #
#     # # Sort by space heating demands
#     # data_coll, list_xticks, list_riqr = zip(
#     #     *sorted(zip(data_coll, list_xticks, list_riqr)))
#
#     plt.rc('font', family='Arial', size=12)
#
#     fig = plt.figure(figsize=(5, 3), dpi=dpi)
#
#     fig.add_subplot(121)
#
#     ax = fig.gca()
#
#     pb = ax.boxplot(data_coll[0:4], showfliers=with_outliners)
#     plt.ylabel('Electric demand in MWh')
#     ax.set_xticklabels(list_xticks[0:4])
#
#     for median in pb['medians']:
#         median.set(color='#E53027')
#
#     for flier in pb['fliers']:
#         flier.set(marker='*', markersize=0.5)
#
#     fig.add_subplot(122)
#
#     ax = fig.gca()
#
#     pb = ax.boxplot(data_coll[4:6], showfliers=with_outliners)
#     plt.ylabel('Electric demand in MWh')
#     ax.set_xticklabels(list_xticks[4:6])
#
#     for median in pb['medians']:
#         median.set(color='#E53027')
#
#     for flier in pb['fliers']:
#         flier.set(marker='*', markersize=0.5)
#
#     fig.autofmt_xdate()
#     plt.tight_layout()
#
#     gen_path(output_path)
#
#     #  Generate file names for different formats
#     file_pdf = output_filename + '.pdf'
#     file_eps = output_filename + '.eps'
#     file_png = output_filename + '.png'
#     file_tiff = output_filename + '.tiff'
#     file_tikz = output_filename + '.tikz'
#
#     #  Generate saving pathes
#     path_pdf = os.path.join(output_path, file_pdf)
#     path_eps = os.path.join(output_path, file_eps)
#     path_png = os.path.join(output_path, file_png)
#     path_tiff = os.path.join(output_path, file_tiff)
#     path_tikz = os.path.join(output_path, file_tikz)
#
#     #  Save figure in different formats
#     plt.savefig(path_pdf, format='pdf', dpi=dpi)
#     plt.savefig(path_eps, format='eps', dpi=dpi)
#     plt.savefig(path_png, format='png', dpi=dpi)
#     # plt.savefig(path_tiff, format='tiff', dpi=dpi)
#     tikz_save(path_tikz, figureheight='\\figureheight',
#               figurewidth='\\figurewidth')
#
#     # plt.show()
#     plt.close()
#
#
# def box_plot_analysis_dhw_dem(mc_res, output_path, output_filename,
#                              with_outliners, list_order, dpi=100):
#     """
#     Perform box plot analysis for electrical demand
#
#     Parameters
#     ----------
#     mc_res
#     output_path
#     output_filename
#     with_outliners
#     list_order
#     dpi
#
#     Returns
#     -------
#
#     """
#
#     gen_path(output_path)
#
#     data_coll = []
#     list_xticks = []
#     list_riqr = []
#
#     for key in list_order:
#
#         list_dhw_en = copy.deepcopy(mc_res.get_results(key=key)[3])
#
#         #  Convert kWh to MWh
#         for i in range(len(list_dhw_en)):
#             list_dhw_en[i] /= 1000
#
#         # Add space heating lists
#         data_coll.append(list_dhw_en)
#
#         list_xticks.append(key)
#
#         #  Calc RIQR
#         riqr = calc_riqr(list_dhw_en)
#         print('riqr')
#         print(riqr)
#         print('for key: ', key)
#         print()
#         list_riqr.append(riqr)
#
#     # for key in mc_res.dict_res.keys():
#     #
#     #     list_dhw_en = copy.deepcopy(mc_res.get_results(key=key)[2])
#     #
#     #     #  Convert kWh to MWh
#     #     for i in range(len(list_dhw_en)):
#     #         list_dhw_en[i] /= 1000
#     #
#     #     # Add space heating lists
#     #     data_coll.append(list_dhw_en)
#     #
#     #     list_xticks.append(key)
#     #
#     #     #  Calc RIQR
#     #     riqr = calc_riqr(list_dhw_en)
#     #     print('riqr')
#     #     print(riqr)
#     #     print('for key: ', key)
#     #     print()
#     #     list_riqr.append(riqr)
#     #
#     # # Sort by space heating demands
#     # data_coll, list_xticks, list_riqr = zip(
#     #     *sorted(zip(data_coll, list_xticks, list_riqr)))
#
#     plt.rc('font', family='Arial', size=12)
#
#     fig = plt.figure(figsize=(5, 3), dpi=dpi)
#
#     ax = fig.gca()
#
#     pb = ax.boxplot(data_coll, showfliers=with_outliners)
#
#     ax.set_xticklabels(list_xticks)
#
#     for median in pb['medians']:
#         median.set(color='#E53027')
#
#     for flier in pb['fliers']:
#         flier.set(marker='*', markersize=0.5)
#
#     fig.autofmt_xdate()
#     plt.tight_layout()
#     plt.ylabel('Hot water demand in MWh')
#
#     #  Generate file names for different formats
#     file_pdf = output_filename + '.pdf'
#     file_eps = output_filename + '.eps'
#     file_png = output_filename + '.png'
#     file_tiff = output_filename + '.tiff'
#     file_tikz = output_filename + '.tikz'
#
#     #  Generate saving pathes
#     path_pdf = os.path.join(output_path, file_pdf)
#     path_eps = os.path.join(output_path, file_eps)
#     path_png = os.path.join(output_path, file_png)
#     path_tiff = os.path.join(output_path, file_tiff)
#     path_tikz = os.path.join(output_path, file_tikz)
#
#     #  Save figure in different formats
#     plt.savefig(path_pdf, format='pdf', dpi=dpi)
#     plt.savefig(path_eps, format='eps', dpi=dpi)
#     plt.savefig(path_png, format='png', dpi=dpi)
#     # plt.savefig(path_tiff, format='tiff', dpi=dpi)
#     tikz_save(path_tikz, figureheight='\\figureheight',
#               figurewidth='\\figurewidth')
#
#     # plt.show()
#     plt.close()
#
#
# def box_plot_analysis_double_plot_dhw_dem(mc_res, output_path,
#                                          output_filename, list_order,
#                                          dpi=100, with_outliners=True):
#     """
#
#     Parameters
#     ----------
#     mc_res
#     output_path
#     output_filename
#     list_order
#     dpi
#     with_outliners
#
#     Returns
#     -------
#
#     """
#
#     gen_path(output_path)
#
#     data_coll = []
#     list_xticks = []
#     list_riqr = []
#
#     for key in list_order:
#
#         list_dhw_en = copy.deepcopy(mc_res.get_results(key=key)[3])
#
#         #  Convert kWh to MWh
#         for i in range(len(list_dhw_en)):
#             list_dhw_en[i] /= 1000
#
#         # Add space heating lists
#         data_coll.append(list_dhw_en)
#
#         list_xticks.append(key)
#
#         #  Calc RIQR
#         riqr = calc_riqr(list_dhw_en)
#         print('riqr')
#         print(riqr)
#         print('for key: ', key)
#         print()
#         list_riqr.append(riqr)
#
#     # for key in mc_res.dict_res.keys():
#     #
#     #     list_dhw_en = copy.deepcopy(mc_res.get_results(key=key)[2])
#     #
#     #     #  Convert kWh to MWh
#     #     for i in range(len(list_dhw_en)):
#     #         list_dhw_en[i] /= 1000
#     #
#     #     # Add space heating lists
#     #     data_coll.append(list_dhw_en)
#     #
#     #     list_xticks.append(key)
#     #
#     #     #  Calc RIQR
#     #     riqr = calc_riqr(list_dhw_en)
#     #     print('riqr')
#     #     print(riqr)
#     #     print('for key: ', key)
#     #     print()
#     #     list_riqr.append(riqr)
#     #
#     # # Sort by space heating demands
#     # data_coll, list_xticks, list_riqr = zip(
#     #     *sorted(zip(data_coll, list_xticks, list_riqr)))
#
#     plt.rc('font', family='Arial', size=12)
#
#     fig = plt.figure(figsize=(5, 3), dpi=dpi)
#
#     fig.add_subplot(121)
#
#     ax = fig.gca()
#
#     pb = ax.boxplot(data_coll[0:4], showfliers=with_outliners)
#     plt.ylabel('Hot water demand in MWh')
#     ax.set_xticklabels(list_xticks[0:4])
#
#     for median in pb['medians']:
#         median.set(color='#E53027')
#
#     for flier in pb['fliers']:
#         flier.set(marker='*', markersize=0.5)
#
#     fig.add_subplot(122)
#
#     ax = fig.gca()
#
#     pb = ax.boxplot(data_coll[4:6], showfliers=with_outliners)
#     plt.ylabel('Hot water demand in MWh')
#     ax.set_xticklabels(list_xticks[4:6])
#
#     for median in pb['medians']:
#         median.set(color='#E53027')
#
#     for flier in pb['fliers']:
#         flier.set(marker='*', markersize=0.5)
#
#     fig.autofmt_xdate()
#     plt.tight_layout()
#
#     gen_path(output_path)
#
#     #  Generate file names for different formats
#     file_pdf = output_filename + '.pdf'
#     file_eps = output_filename + '.eps'
#     file_png = output_filename + '.png'
#     file_tiff = output_filename + '.tiff'
#     file_tikz = output_filename + '.tikz'
#
#     #  Generate saving pathes
#     path_pdf = os.path.join(output_path, file_pdf)
#     path_eps = os.path.join(output_path, file_eps)
#     path_png = os.path.join(output_path, file_png)
#     path_tiff = os.path.join(output_path, file_tiff)
#     path_tikz = os.path.join(output_path, file_tikz)
#
#     #  Save figure in different formats
#     plt.savefig(path_pdf, format='pdf', dpi=dpi)
#     plt.savefig(path_eps, format='eps', dpi=dpi)
#     plt.savefig(path_png, format='png', dpi=dpi)
#     # plt.savefig(path_tiff, format='tiff', dpi=dpi)
#     tikz_save(path_tikz, figureheight='\\figureheight',
#               figurewidth='\\figurewidth')
#
#     # plt.show()
#     plt.close()


if __name__ == '__main__':

    this_path = os.path.dirname(os.path.abspath(__file__))

    #  Generate results object
    mc_res = McCityRes()

    dict_files_city = {}
    dict_files_build = {}

    #  Add results of mc analyses
    #  ####################################################################

    filename_city = 'aachen_forsterlinde_mod_7_mc_city_samples_10000.pkl'
    filename_b = 'aachen_forsterlinde_mod_7_single_b_100001011.pkl'
    output_city = filename_city[:-4]
    output_b = filename_b[:-4]
    key = 'Forsterlinde'

    dict_files_city[key] = filename_city
    dict_files_build[key] = filename_b

    filename_city = 'aachen_frankenberg_mod_6_mc_city_samples_10000.pkl'
    filename_b = 'aachen_frankenberg_mod_6_single_b_100001020.pkl'
    output_city = filename_city[:-4]
    output_b = filename_b[:-4]
    key = 'Frankenberg'

    dict_files_city[key] = filename_city
    dict_files_build[key] = filename_b

    filename_city = 'aachen_kronenberg_mod_6_mc_city_samples_10000.pkl'
    filename_b = 'aachen_kronenberg_mod_6_single_b_100001002.pkl'
    output_city = filename_city[:-4]
    output_b = filename_b[:-4]
    key = 'Kronenberg'

    dict_files_city[key] = filename_city
    dict_files_build[key] = filename_b

    filename_city = 'aachen_preusweg_mod_6_mc_city_samples_10000.pkl'
    filename_b = 'aachen_preusweg_mod_6_single_b_100001092.pkl'
    output_city = filename_city[:-4]
    output_b = filename_b[:-4]
    key = 'Preusweg'

    dict_files_city[key] = filename_city
    dict_files_build[key] = filename_b

    #filename_city = 'aachen_tuerme_mod_7_mc_city_samples_10000.pkl'
    filename_city = 'aachen_tuerme_mod_7_mc_city_samples_10000_with_retro_person_data.pkl'
    #filename_b = 'aachen_tuerme_mod_6_single_b_100001010.pkl'
    filename_b = 'aachen_tuerme_mod_7_single_b_10000_fix_year_occ_1010.pkl'
    output_city = filename_city[:-4]
    output_b = filename_b[:-4]
    key = u'Türme'

    dict_files_city[key] = filename_city
    dict_files_build[key] = filename_b

    filename_city = 'aachen_huenefeld_mod_6_mc_city_samples_10000.pkl'
    filename_b = 'aachen_huenefeld_mod_6_single_b_100001003.pkl'
    output_city = filename_city[:-4]
    output_b = filename_b[:-4]
    key = u'Hünefeld'

    dict_files_city[key] = filename_city
    dict_files_build[key] = filename_b

    for key in dict_files_city.keys():
        file_city = dict_files_city[key]
        file_build = dict_files_build[key]

        load_path_city = os.path.join(this_path, 'input', 'mc_cities',
                                      '4_with_10000_samples',
                                      file_city)
        load_path_build = os.path.join(this_path, 'input', 'mc_buildings',
                                       file_build)

        #  Load results and add them to results object
        mc_res.add_res_mc_city_from_path(path=load_path_city, key=key)
        mc_res.add_res_mc_build_from_path(path=load_path_build, key=key)


    # Add cities
    #  ######################################################################
    dict_city_f_names = {}
    dict_b_node_nb = {}

    #  City object pickle file, which should be loaded
    city_f_name = 'aachen_forsterlinde_mod_7.pkl'
    key = 'Forsterlinde'
    build_node_nb = 1011  # Forsterlinde
    dict_city_f_names[key] = city_f_name
    dict_b_node_nb[key] = build_node_nb

    city_f_name = 'aachen_frankenberg_mod_8_el_resc.pkl'
    key = 'Frankenberg'
    build_node_nb = 1020  # Frankenberg
    dict_city_f_names[key] = city_f_name
    dict_b_node_nb[key] = build_node_nb

    city_f_name = 'aachen_kronenberg_mod_8.pkl'
    key = 'Kronenberg'
    build_node_nb = 1002  # Kronenberg
    dict_city_f_names[key] = city_f_name
    dict_b_node_nb[key] = build_node_nb

    city_f_name = 'aachen_preusweg_mod_9.pkl'
    key = 'Preusweg'
    build_node_nb = 1092  # Preusweg
    dict_city_f_names[key] = city_f_name
    dict_b_node_nb[key] = build_node_nb

    city_f_name = 'aachen_tuerme_mod_7_el_resc_2.pkl'
    key = u'Türme'
    build_node_nb = 1010  # Tuerme
    dict_city_f_names[key] = city_f_name
    dict_b_node_nb[key] = build_node_nb

    city_f_name = 'aachen_huenefeld_mod_7.pkl'
    key = u'Hünefeld'
    build_node_nb = 1003  # Huenefeld
    dict_city_f_names[key] = city_f_name
    dict_b_node_nb[key] = build_node_nb

    for key in dict_city_f_names.keys():
        city_f_name = dict_city_f_names[key]
        load_path = os.path.join(this_path, 'input', 'ref_cities', city_f_name)

        city = pickle.load(open(load_path, mode='rb'))

        #  Load results and add them to results object
        mc_res.add_city(key=key, city=city)

    mc_res.dict_build_ids = dict_b_node_nb

    #  User input
    #  ###############################################

    mc_city = False
    all_cities = True  # all cities / all buildings or only specific key

    with_outliners = True
    dpi = 1000
    fontsize = 12


    if mc_city:
        output_filename = 'mc_city'
    else:
        output_filename = 'mc_single_build'

    list_order = ['Preusweg', 'Forsterlinde', 'Kronenberg', 'Frankenberg',
                  'Hünefeld', 'Türme']

    #############################
    if all_cities:
        if mc_city:
            output_folder_n = 'cities_mc'
        else:
            output_folder_n = 'buildings_mc'

    else:
        #  For single analysis (only one district)
        key = u'Preusweg'
        if mc_city:
            #  For single district
            name_an = '_s_city'
            output_folder_n = key + name_an
        else:
            #  For single building
            name_an = '_s_build'
            output_folder_n = key + name_an

    output_path = os.path.join(this_path, 'output', output_folder_n)

    gen_path(output_path)
    #############################

    # # calc_sh_coverage_cities(mc_res=mc_res, build=not mc_city)
    # get_ref_sh_nom_powers(mc_res=mc_res, build=not mc_city)

    if all_cities is False:

        print('Single district analysis for: ', key)

        #  Perform space heating load analysis for single district
        #  Plot all space heating load curves
        #  #####################################################################
        # do_sh_load_analysis(mc_res=mc_res, key=key, output_path=output_path,
        #                     output_filename=key, dpi=300,
        #                     mc_city=True, fontsize=fontsize)

        # #  Perform space heating demand analysis for single district
        # #  #####################################################################
        # analyze_demands_hist(mc_res=mc_res, key=key, mode='sh',
        #                      output_path=output_path, dpi=dpi,
        #                      mc_city=mc_city, fontsize=fontsize)
        #
        # # #  Perform space heating power analysis for single district
        # # #  #####################################################################
        # # analyze_sh_powers_hist(mc_res=mc_res, key=key, output_path=output_path)
        #
        # #  Perform electric energy analysis for single district
        # #  #####################################################################
        # analyze_demands_hist(mc_res=mc_res, key=key, mode='el',
        #                      output_path=output_path, dpi=dpi,
        #                      mc_city=mc_city, fontsize=fontsize)
        #
        # #  Perform hot water energy analysis for single district
        # #  #####################################################################
        # analyze_demands_hist(mc_res=mc_res, key=key, mode='dhw',
        #                      output_path=output_path, dpi=dpi,
        #                      mc_city=mc_city, fontsize=fontsize)


    elif all_cities is True:

        print('Analysis for all districts')

        # # #  Perform space heating box plot analysis for all districts
        # # #  Plot boxplots with three axes
        # # #  #####################################################################
        # output_path_curr = os.path.join(output_path, 'th_dem_three_axes')
        # box_plot_analysis_triple_plot(mc_res=mc_res, output_path=output_path_curr,
        #                               output_filename=output_filename, dpi=dpi,
        #                               with_outliners=with_outliners,
        #                               list_order=list_order, mode='sh',
        #                               mc_city=mc_city)
        #
        # # #  Perform electric energy box plot analysis for all districts
        # # #  Plot boxplots with three axes
        # # #  #####################################################################
        # output_path_curr = os.path.join(output_path, 'el_dem_three_axes')
        # box_plot_analysis_triple_plot(mc_res=mc_res, output_path=output_path_curr,
        #                               output_filename=output_filename, dpi=dpi,
        #                               with_outliners=with_outliners,
        #                               list_order=list_order, mode='el',
        #                               mc_city=mc_city)
        #
        # # #  Perform hot water energy box plot analysis for all districts
        # # #  Plot boxplots with three axes
        # # #  #####################################################################
        # output_path_curr = os.path.join(output_path, 'dhw_dem_three_axes')
        # box_plot_analysis_triple_plot(mc_res=mc_res, output_path=output_path_curr,
        #                               output_filename=output_filename, dpi=dpi,
        #                               with_outliners=with_outliners,
        #                               list_order=list_order, mode='dhw',
        #                               mc_city=mc_city)

    print('Saved results to ' + str(output_path))
