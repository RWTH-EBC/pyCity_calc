#!/usr/bin/env python
# coding=utf-8
"""
Script to analyze results of Monte-Carlo space heating demand uncertainty
analysis for single buiding and cities
"""

import os
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

        self.dict_res = {}
        self.dict_cities = {}
        self.dict_build_ids = {}

    def add_res_list(self, list_res, key):
        """
        Add results list with
        Parameters
        ----------
        list_res : list
            List holding sample result lists
        key : str
            Key/name to add list to dictionary
        """

        self.dict_res[key] = list_res

    def add_res_from_path(self, path, key):
        """
        Add result lists from path, where pickle file is stored

        Parameters
        ----------
        path : str
            Path to pickle file
        key : str
            Key/name to add list to dictionary
        """

        list_res = load_results_from_path(path=path)

        self.add_res_list(list_res=list_res, key=key)

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

    def get_results(self, key):
        """
        Return results list

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

        return self.dict_res[key]

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


def do_sh_load_analysis(mc_res, key, output_path, output_filename, dpi=300):
    """

    Parameters
    ----------
    mc_res
    key
    output_path
    output_filename
    dpi

    Returns
    -------

    """

    #  Extract list with space heating arrays
    list_sh_curves = mc_res.get_results(key=key)[1]

    #  Sort list by sum of arrays
    list_sh_curves.sort(key=sum, reverse=True)

    (min_array, max_array, av_array) = \
        calc_min_max_av_sh_load_curves(list_sh_curves=list_sh_curves)

    plt.rc('font', family='Arial', size=10)

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


def analyze_sh_demands_hist(mc_res, key, output_path):
    """

    Parameters
    ----------
    mc_res
    key
    output_path

    Returns
    -------

    """

    #  Extract space heating demands
    #  ##################################################################
    list_sh_dem = mc_res.get_results(key=key)[0]

    #  Extract reference space heating demand
    #  ##################################################################
    city = mc_res.get_city(key=key)
    node_id = mc_res.dict_build_ids[key]

    print(city.nodes())

    curr_build = city.node[node_id]['entity']

    #  Get reference space heating demand in kWh
    sh_dem_ref = curr_build.get_annual_space_heat_demand()

    dict_v_lines = {}
    dict_v_lines['Reference'] = sh_dem_ref

    print()
    print('Mean net space heating energy value in kWh:')
    mean = np.mean(list_sh_dem)
    print(mean)
    print()

    print('Standard deviation of net space heating energy value in kWh:')
    stdev = np.std(a=list_sh_dem)
    print()

    print('Median net space heating energy value in kWh:')
    median = np.median(a=list_sh_dem)
    print(median)
    print()

    print('Interquartile range (IQR):')
    iqr = scipy.stats.iqr(x=list_sh_dem)
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
    xlab_engl = 'Space heating demand in kWh'
    ylab_engl = 'Number of demand values'

    #  German infos
    title_dt = None  # Add 'u' in front of string to define it as unicode
    # (e.g. when using non-ascii characters)
    xlab_dt = 'Raumwärmebedarf in kWh'
    ylab_dt = 'Anzahl Energiebedarfswerte'
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

    output_filename = key + '_sh_demand'

    #  #--------------------------------------------------------------

    ebchist.plot_multi_lang_multi_color_hist(list_data=list_sh_dem,
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

    curr_build = city.node[node_id]['entity']

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

def analyze_el_demands_hist(mc_res, key, output_path):
    """

    Parameters
    ----------
    mc_res
    key
    output_path

    Returns
    -------

    """

    #  Extract electric energy demands
    #  ##################################################################
    list_el_dem = mc_res.get_results(key=key)[2]

    #  Extract reference electric energy demand
    #  ##################################################################
    city = mc_res.get_city(key=key)
    node_id = mc_res.dict_build_ids[key]

    curr_build = city.node[node_id]['entity']

    #  Get reference electric energy demand in kWh
    sh_dem_ref = curr_build.get_annual_el_demand()

    dict_v_lines = {}
    dict_v_lines['Reference'] = sh_dem_ref

    print()
    print('Mean electric energy demand value in kWh:')
    mean = np.mean(list_el_dem)
    print(mean)
    print()

    print('Standard deviation of electric energy demand value in kWh:')
    stdev = np.std(a=list_el_dem)
    print()

    print('Median net electric energy demand value in kWh:')
    median = np.median(a=list_el_dem)
    print(median)
    print()

    print('Interquartile range (IQR):')
    iqr = scipy.stats.iqr(x=list_el_dem)
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
    xlab_engl = 'Electric energy demand in kWh'
    ylab_engl = 'Number of demand values'

    #  German infos
    title_dt = None  # Add 'u' in front of string to define it as unicode
    # (e.g. when using non-ascii characters)
    xlab_dt = 'Elektrischer Energiebedarf in kWh'
    ylab_dt = 'Anzahl Energiebedarfswerte'
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

    output_filename = key + '_el_demand'

    #  #--------------------------------------------------------------

    ebchist.plot_multi_lang_multi_color_hist(list_data=list_el_dem,
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


def analyze_dhw_demands_hist(mc_res, key, output_path):
    """

    Parameters
    ----------
    mc_res
    key
    output_path

    Returns
    -------

    """

    #  Extract space heating demands
    #  ##################################################################
    list_dhw_en = mc_res.get_results(key=key)[3]

    #  Extract reference space heating demand
    #  ##################################################################
    city = mc_res.get_city(key=key)
    node_id = mc_res.dict_build_ids[key]

    curr_build = city.node[node_id]['entity']

    #  Get reference hot water energy demand in kWh
    sh_dem_ref = curr_build.get_annual_dhw_demand()

    dict_v_lines = {}
    dict_v_lines['Reference'] = sh_dem_ref

    print()
    print('Mean net hot water energy value in kWh:')
    mean = np.mean(list_dhw_en)
    print(mean)
    print()

    print('Standard deviation of hot water energy value in kWh:')
    stdev = np.std(a=list_dhw_en)
    print()

    print('Median hot water energy value in kWh:')
    median = np.median(a=list_dhw_en)
    print(median)
    print()

    print('Interquartile range (IQR):')
    iqr = scipy.stats.iqr(x=list_dhw_en)
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
    xlab_engl = 'Hot water energy demand in kWh'
    ylab_engl = 'Number of demand values'

    #  German infos
    title_dt = None  # Add 'u' in front of string to define it as unicode
    # (e.g. when using non-ascii characters)
    xlab_dt = 'Warmwasserenergiebedarf in kWh'
    ylab_dt = 'Anzahl Energiebedarfswerte'
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

    output_filename = key + '_dhw_demand'

    #  #--------------------------------------------------------------

    ebchist.plot_multi_lang_multi_color_hist(list_data=list_dhw_en,
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


def box_plot_analysis(mc_res, output_path, output_filename, with_outliners,
                      list_order,
                      dpi=100):
    """

    Parameters
    ----------
    mc_res
    output_path
    output_filename
    with_outliners
    list_order
    dpi

    Returns
    -------

    """

    gen_path(output_path)

    data_coll = []
    list_xticks = []
    list_riqr = []

    for key in list_order:

        list_sh_en = copy.deepcopy(mc_res.get_results(key=key)[0])

        #  Convert kWh to MWh
        for i in range(len(list_sh_en)):
            list_sh_en[i] /= 1000

        # Add space heating lists
        data_coll.append(list_sh_en)

        list_xticks.append(key)

        #  Calc RIQR
        riqr = calc_riqr(list_sh_en)
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

    # # Sort by space heating demands
    # data_coll, list_xticks, list_riqr = zip(
    #     *sorted(zip(data_coll, list_xticks, list_riqr)))

    plt.rc('font', family='Arial', size=12)

    fig = plt.figure(figsize=(5, 3), dpi=dpi)

    ax = fig.gca()

    pb = ax.boxplot(data_coll, showfliers=with_outliners)

    ax.set_xticklabels(list_xticks)

    for median in pb['medians']:
        median.set(color='#E53027')

    for flier in pb['fliers']:
        flier.set(marker='*', markersize=0.5)

    fig.autofmt_xdate()
    plt.tight_layout()
    plt.ylabel('Net space heating\ndemand in MWh')

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


def box_plot_analysis_double_plot(mc_res, output_path, output_filename,
                                  list_order,
                                  dpi=100, with_outliners=True):
    """

    Parameters
    ----------
    mc_res
    output_path
    output_filename
    list_order
    dpi
    with_outliners

    Returns
    -------

    """

    gen_path(output_path)

    data_coll = []
    list_xticks = []
    list_riqr = []

    for key in list_order:

        list_sh_en = copy.deepcopy(mc_res.get_results(key=key)[0])

        #  Convert kWh to MWh
        for i in range(len(list_sh_en)):
            list_sh_en[i] /= 1000

        # Add space heating lists
        data_coll.append(list_sh_en)

        list_xticks.append(key)

        #  Calc RIQR
        riqr = calc_riqr(list_sh_en)
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

    plt.rc('font', family='Arial', size=12)

    fig = plt.figure(figsize=(5, 3), dpi=dpi)

    fig.add_subplot(121)

    ax = fig.gca()

    pb = ax.boxplot(data_coll[0:4], showfliers=with_outliners)
    plt.ylabel('Net space heating\ndemand in MWh')
    ax.set_xticklabels(list_xticks[0:4])

    for median in pb['medians']:
        median.set(color='#E53027')

    for flier in pb['fliers']:
        flier.set(marker='*', markersize=0.5)

    fig.add_subplot(122)

    ax = fig.gca()

    pb = ax.boxplot(data_coll[4:6], showfliers=with_outliners)
    plt.ylabel('Net space heating\ndemand in MWh')
    ax.set_xticklabels(list_xticks[4:6])

    for median in pb['medians']:
        median.set(color='#E53027')

    for flier in pb['fliers']:
        flier.set(marker='*', markersize=0.5)

    fig.autofmt_xdate()
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


def box_plot_analysis_triple_plot(mc_res, output_path, output_filename,
                                  list_order,
                                  dpi=100, with_outliners=True):
    """

    Parameters
    ----------
    mc_res
    output_path
    output_filename
    list_order
    dpi
    with_outliners

    Returns
    -------

    """

    gen_path(output_path)

    data_coll = []
    list_xticks = []
    list_riqr = []

    for key in list_order:

        list_sh_en = copy.deepcopy(mc_res.get_results(key=key)[0])

        #  Convert kWh to MWh
        for i in range(len(list_sh_en)):
            list_sh_en[i] /= 1000

        # Add space heating lists
        data_coll.append(list_sh_en)

        list_xticks.append(key)

        #  Calc RIQR
        riqr = calc_riqr(list_sh_en)
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

    plt.rc('font', family='Arial', size=12)

    fig = plt.figure(figsize=(5, 3), dpi=dpi)

    fig.add_subplot(131)

    ax = fig.gca()

    pb = ax.boxplot(data_coll[0:2], showfliers=with_outliners, widths=(0.8, 0.8))
    plt.ylabel('Net space heating\ndemand in MWh')
    ax.set_xticklabels(list_xticks[0:2])

    start, end = ax.get_ylim()
    print(start)
    print(end)
    ax.yaxis.set_ticks(np.arange(round(start,-3), end, 100))

    for median in pb['medians']:
        median.set(color='#E53027')

    for flier in pb['fliers']:
        flier.set(marker='*', markersize=0.5)

    fig.add_subplot(132)

    ax = fig.gca()

    pb = ax.boxplot(data_coll[2:4], showfliers=with_outliners, widths=(0.8, 0.8))
    #plt.ylabel('Net space heating\ndemand in MWh')
    ax.set_xticklabels(list_xticks[2:4])

    start, end = ax.get_ylim()
    print(start)
    print(end)
    ax.yaxis.set_ticks(np.arange(round(start,-3), end, 250))

    for median in pb['medians']:
        median.set(color='#E53027')

    for flier in pb['fliers']:
        flier.set(marker='*', markersize=0.5)

    fig.add_subplot(133)

    ax = fig.gca()

    pb = ax.boxplot(data_coll[4:6], showfliers=with_outliners, widths=(0.8, 0.8))
    #plt.ylabel('Net space heating\ndemand in MWh')
    ax.set_xticklabels(list_xticks[4:6])

    start, end = ax.get_ylim()
    print(start)
    print(end)
    ax.yaxis.set_ticks(np.arange(round(start,-3), end, 500))

    for median in pb['medians']:
        median.set(color='#E53027')

    for flier in pb['fliers']:
        flier.set(marker='*', markersize=0.5)

    fig.autofmt_xdate()
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


def box_plot_analysis_el_dem(mc_res, output_path, output_filename,
                             with_outliners, list_order, dpi=100):
    """
    Perform box plot analysis for electrical demand

    Parameters
    ----------
    mc_res
    output_path
    output_filename
    with_outliners
    list_order
    dpi

    Returns
    -------

    """

    gen_path(output_path)

    data_coll = []
    list_xticks = []
    list_riqr = []

    for key in list_order:

        list_el_en = copy.deepcopy(mc_res.get_results(key=key)[2])

        #  Convert kWh to MWh
        for i in range(len(list_el_en)):
            list_el_en[i] /= 1000

        # Add space heating lists
        data_coll.append(list_el_en)

        list_xticks.append(key)

        #  Calc RIQR
        riqr = calc_riqr(list_el_en)
        print('riqr')
        print(riqr)
        print('for key: ', key)
        print()
        list_riqr.append(riqr)

    # for key in mc_res.dict_res.keys():
    #
    #     list_el_en = copy.deepcopy(mc_res.get_results(key=key)[2])
    #
    #     #  Convert kWh to MWh
    #     for i in range(len(list_el_en)):
    #         list_el_en[i] /= 1000
    #
    #     # Add space heating lists
    #     data_coll.append(list_el_en)
    #
    #     list_xticks.append(key)
    #
    #     #  Calc RIQR
    #     riqr = calc_riqr(list_el_en)
    #     print('riqr')
    #     print(riqr)
    #     print('for key: ', key)
    #     print()
    #     list_riqr.append(riqr)
    #
    # # Sort by space heating demands
    # data_coll, list_xticks, list_riqr = zip(
    #     *sorted(zip(data_coll, list_xticks, list_riqr)))

    plt.rc('font', family='Arial', size=12)

    fig = plt.figure(figsize=(5, 3), dpi=dpi)

    ax = fig.gca()

    pb = ax.boxplot(data_coll, showfliers=with_outliners)

    ax.set_xticklabels(list_xticks)

    for median in pb['medians']:
        median.set(color='#E53027')

    for flier in pb['fliers']:
        flier.set(marker='*', markersize=0.5)

    fig.autofmt_xdate()
    plt.tight_layout()
    plt.ylabel('Electric demand in MWh')

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


def box_plot_analysis_double_plot_el_dem(mc_res, output_path,
                                         output_filename, list_order,
                                         dpi=100, with_outliners=True):
    """

    Parameters
    ----------
    mc_res
    output_path
    output_filename
    list_order
    dpi
    with_outliners

    Returns
    -------

    """

    gen_path(output_path)

    data_coll = []
    list_xticks = []
    list_riqr = []

    for key in list_order:

        list_el_en = copy.deepcopy(mc_res.get_results(key=key)[2])

        #  Convert kWh to MWh
        for i in range(len(list_el_en)):
            list_el_en[i] /= 1000

        # Add space heating lists
        data_coll.append(list_el_en)

        list_xticks.append(key)

        #  Calc RIQR
        riqr = calc_riqr(list_el_en)
        print('riqr')
        print(riqr)
        print('for key: ', key)
        print()
        list_riqr.append(riqr)

    # for key in mc_res.dict_res.keys():
    #
    #     list_el_en = copy.deepcopy(mc_res.get_results(key=key)[2])
    #
    #     #  Convert kWh to MWh
    #     for i in range(len(list_el_en)):
    #         list_el_en[i] /= 1000
    #
    #     # Add space heating lists
    #     data_coll.append(list_el_en)
    #
    #     list_xticks.append(key)
    #
    #     #  Calc RIQR
    #     riqr = calc_riqr(list_el_en)
    #     print('riqr')
    #     print(riqr)
    #     print('for key: ', key)
    #     print()
    #     list_riqr.append(riqr)
    #
    # # Sort by space heating demands
    # data_coll, list_xticks, list_riqr = zip(
    #     *sorted(zip(data_coll, list_xticks, list_riqr)))

    plt.rc('font', family='Arial', size=12)

    fig = plt.figure(figsize=(5, 3), dpi=dpi)

    fig.add_subplot(121)

    ax = fig.gca()

    pb = ax.boxplot(data_coll[0:4], showfliers=with_outliners)
    plt.ylabel('Electric demand in MWh')
    ax.set_xticklabels(list_xticks[0:4])

    for median in pb['medians']:
        median.set(color='#E53027')

    for flier in pb['fliers']:
        flier.set(marker='*', markersize=0.5)

    fig.add_subplot(122)

    ax = fig.gca()

    pb = ax.boxplot(data_coll[4:6], showfliers=with_outliners)
    plt.ylabel('Electric demand in MWh')
    ax.set_xticklabels(list_xticks[4:6])

    for median in pb['medians']:
        median.set(color='#E53027')

    for flier in pb['fliers']:
        flier.set(marker='*', markersize=0.5)

    fig.autofmt_xdate()
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


def box_plot_analysis_dhw_dem(mc_res, output_path, output_filename,
                             with_outliners, list_order, dpi=100):
    """
    Perform box plot analysis for electrical demand

    Parameters
    ----------
    mc_res
    output_path
    output_filename
    with_outliners
    list_order
    dpi

    Returns
    -------

    """

    gen_path(output_path)

    data_coll = []
    list_xticks = []
    list_riqr = []

    for key in list_order:

        list_dhw_en = copy.deepcopy(mc_res.get_results(key=key)[3])

        #  Convert kWh to MWh
        for i in range(len(list_dhw_en)):
            list_dhw_en[i] /= 1000

        # Add space heating lists
        data_coll.append(list_dhw_en)

        list_xticks.append(key)

        #  Calc RIQR
        riqr = calc_riqr(list_dhw_en)
        print('riqr')
        print(riqr)
        print('for key: ', key)
        print()
        list_riqr.append(riqr)

    # for key in mc_res.dict_res.keys():
    #
    #     list_dhw_en = copy.deepcopy(mc_res.get_results(key=key)[2])
    #
    #     #  Convert kWh to MWh
    #     for i in range(len(list_dhw_en)):
    #         list_dhw_en[i] /= 1000
    #
    #     # Add space heating lists
    #     data_coll.append(list_dhw_en)
    #
    #     list_xticks.append(key)
    #
    #     #  Calc RIQR
    #     riqr = calc_riqr(list_dhw_en)
    #     print('riqr')
    #     print(riqr)
    #     print('for key: ', key)
    #     print()
    #     list_riqr.append(riqr)
    #
    # # Sort by space heating demands
    # data_coll, list_xticks, list_riqr = zip(
    #     *sorted(zip(data_coll, list_xticks, list_riqr)))

    plt.rc('font', family='Arial', size=12)

    fig = plt.figure(figsize=(5, 3), dpi=dpi)

    ax = fig.gca()

    pb = ax.boxplot(data_coll, showfliers=with_outliners)

    ax.set_xticklabels(list_xticks)

    for median in pb['medians']:
        median.set(color='#E53027')

    for flier in pb['fliers']:
        flier.set(marker='*', markersize=0.5)

    fig.autofmt_xdate()
    plt.tight_layout()
    plt.ylabel('Hot water demand in MWh')

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


def box_plot_analysis_double_plot_dhw_dem(mc_res, output_path,
                                         output_filename, list_order,
                                         dpi=100, with_outliners=True):
    """

    Parameters
    ----------
    mc_res
    output_path
    output_filename
    list_order
    dpi
    with_outliners

    Returns
    -------

    """

    gen_path(output_path)

    data_coll = []
    list_xticks = []
    list_riqr = []

    for key in list_order:

        list_dhw_en = copy.deepcopy(mc_res.get_results(key=key)[3])

        #  Convert kWh to MWh
        for i in range(len(list_dhw_en)):
            list_dhw_en[i] /= 1000

        # Add space heating lists
        data_coll.append(list_dhw_en)

        list_xticks.append(key)

        #  Calc RIQR
        riqr = calc_riqr(list_dhw_en)
        print('riqr')
        print(riqr)
        print('for key: ', key)
        print()
        list_riqr.append(riqr)

    # for key in mc_res.dict_res.keys():
    #
    #     list_dhw_en = copy.deepcopy(mc_res.get_results(key=key)[2])
    #
    #     #  Convert kWh to MWh
    #     for i in range(len(list_dhw_en)):
    #         list_dhw_en[i] /= 1000
    #
    #     # Add space heating lists
    #     data_coll.append(list_dhw_en)
    #
    #     list_xticks.append(key)
    #
    #     #  Calc RIQR
    #     riqr = calc_riqr(list_dhw_en)
    #     print('riqr')
    #     print(riqr)
    #     print('for key: ', key)
    #     print()
    #     list_riqr.append(riqr)
    #
    # # Sort by space heating demands
    # data_coll, list_xticks, list_riqr = zip(
    #     *sorted(zip(data_coll, list_xticks, list_riqr)))

    plt.rc('font', family='Arial', size=12)

    fig = plt.figure(figsize=(5, 3), dpi=dpi)

    fig.add_subplot(121)

    ax = fig.gca()

    pb = ax.boxplot(data_coll[0:4], showfliers=with_outliners)
    plt.ylabel('Hot water demand in MWh')
    ax.set_xticklabels(list_xticks[0:4])

    for median in pb['medians']:
        median.set(color='#E53027')

    for flier in pb['fliers']:
        flier.set(marker='*', markersize=0.5)

    fig.add_subplot(122)

    ax = fig.gca()

    pb = ax.boxplot(data_coll[4:6], showfliers=with_outliners)
    plt.ylabel('Hot water demand in MWh')
    ax.set_xticklabels(list_xticks[4:6])

    for median in pb['medians']:
        median.set(color='#E53027')

    for flier in pb['fliers']:
        flier.set(marker='*', markersize=0.5)

    fig.autofmt_xdate()
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


if __name__ == '__main__':
    this_path = os.path.dirname(os.path.abspath(__file__))

    #  Generate results object
    mc_res = McCityRes()

    dict_filenames = {}

    #  Add results
    #  ####################################################################

    filename1 = 'aachen_forsterlinde_5_mc_city_2000_new_dhw_2000.pkl'
    # filename1 = 'aachen_forsterlinde_5_single_b_new_dhw_1011.pkl'
    output_filename1 = filename1[:-4]
    key1 = 'Forsterlinde'

    dict_filenames[key1] = filename1

    filename2 = 'aachen_frankenberg_5_mc_city_2000_new_dhw_2000.pkl'
    # filename2 = 'aachen_frankenberg_5_single_b_new_dhw_1020.pkl'
    output_filename2 = filename2[:-4]
    key2 = 'Frankenberg'

    dict_filenames[key2] = filename2

    filename3 = 'aachen_kronenberg_5_mc_city_2000_new_dhw_2000.pkl'
    # filename3 = 'aachen_kronenberg_5_single_b_new_dhw_1002.pkl'
    output_filename3 = filename3[:-4]
    key3 = 'Kronenberg'

    dict_filenames[key3] = filename3

    filename4 = 'aachen_preusweg_5b_mc_city_2000_new_dhw_2000.pkl'
    # filename4 = 'aachen_preusweg_5b_single_b_new_dhw_1092.pkl'
    output_filename4 = filename4[:-4]
    key4 = 'Preusweg'

    dict_filenames[key4] = filename4

    filename5 = 'aachen_tuerme_osm_extr_enriched_mc_city_2000_new_dhw_2000.pkl'
    # filename5 = 'aachen_tuerme_osm_extr_enriched_single_b_new_dhw_1010.pkl'
    output_filename5 = filename5[:-4]
    key5 = u'Türme'

    dict_filenames[key5] = filename5

    filename6 = 'huenefeld_5_mc_city_2000_new_dhw_2000.pkl'
    # filename6 = 'huenefeld_5_single_b_new_dhw_1003.pkl'
    output_filename6 = filename6[:-4]
    key6 = u'Hünefeld'

    dict_filenames[key6] = filename6

    for key in dict_filenames.keys():
        filename = dict_filenames[key]
        load_path = os.path.join(this_path, 'input', 'mc_cities', filename)
        # load_path = os.path.join(this_path, 'input', 'mc_buildings', filename)

        #  Load results and add them to results object
        mc_res.add_res_from_path(path=load_path, key=key)

    # Add cities
    #  ######################################################################
    dict_city_f_names = {}
    dict_b_node_nb = {}

    #  City object pickle file, which should be loaded
    city_f_name = 'aachen_forsterlinde_mod_6.pkl'
    key = 'Forsterlinde'
    build_node_nb = 1011  # Forsterlinde
    dict_city_f_names[key] = city_f_name
    dict_b_node_nb[key] = build_node_nb

    city_f_name = 'aachen_frankenberg_mod_6.pkl'
    key = 'Frankenberg'
    build_node_nb = 1020  # Frankenberg
    dict_city_f_names[key] = city_f_name
    dict_b_node_nb[key] = build_node_nb

    city_f_name = 'aachen_kronenberg_mod_6.pkl'
    key = 'Kronenberg'
    build_node_nb = 1002  # Kronenberg
    dict_city_f_names[key] = city_f_name
    dict_b_node_nb[key] = build_node_nb

    city_f_name = 'aachen_preusweg_mod_6.pkl'
    key = 'Preusweg'
    build_node_nb = 1092  # Preusweg
    dict_city_f_names[key] = city_f_name
    dict_b_node_nb[key] = build_node_nb

    city_f_name = 'aachen_tuerme_mod_6.pkl'
    key = u'Türme'
    build_node_nb = 1010  # Tuerme
    dict_city_f_names[key] = city_f_name
    dict_b_node_nb[key] = build_node_nb

    city_f_name = 'aachen_tuerme_mod_6.pkl'
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

    output_filename = 'mc_single_building_2000'
    with_outliners = True
    dpi = 1000

    list_order = ['Preusweg', 'Forsterlinde', 'Kronenberg', 'Frankenberg',
                  'Hünefeld', 'Türme']

    #############################
    #  For single district
    # key = u'Hünefeld'
    # # #  analysis name
    # name_an = '_boxplots'
    # output_folder_n = key + name_an

    output_folder_n = 'cities_mc'

    output_path = os.path.join(this_path, 'output', output_folder_n)

    gen_path(output_path)
    #############################


    # #  Perform space heating load analysis for single district
    # #  Plot all space heating load curves
    # #  #####################################################################
    # do_sh_load_analysis(mc_res=mc_res, key=key, output_path=output_path,
    #                     output_filename=key)

    # #  Perform space heating demand analysis for single district
    # #  #####################################################################
    # analyze_sh_demands_hist(mc_res=mc_res, key=key, output_path=output_path)
    #
    # #  Perform space heating power analysis for single district
    # #  #####################################################################
    # analyze_sh_powers_hist(mc_res=mc_res, key=key, output_path=output_path)
    #
    # #  Perform electric energy analysis for single district
    # #  #####################################################################
    # analyze_el_demands_hist(mc_res=mc_res, key=key, output_path=output_path)
    #
    # #  Perform hot water energy analysis for single district
    # #  #####################################################################
    # analyze_dhw_demands_hist(mc_res=mc_res, key=key, output_path=output_path)

    # # #  Perform space heating box plot analysis for all districts
    # # #  Plot all boxplots in one figure
    # # #  #####################################################################
    # output_path_curr = os.path.join(output_path, 'th_dem_single_axes')
    # box_plot_analysis(mc_res=mc_res, output_path=output_path_curr,
    #                   output_filename=output_filename, dpi=dpi,
    #                   with_outliners=with_outliners,
    #                   list_order=list_order)
    #
    # # #  Perform space heating box plot analysis for all districts
    # # #  Plot boxplots in two figure
    # # #  #####################################################################
    # output_path_curr = os.path.join(output_path, 'th_dem_two_axes')
    # box_plot_analysis_double_plot(mc_res=mc_res, output_path=output_path_curr,
    #                               output_filename=output_filename, dpi=dpi,
    #                               with_outliners=with_outliners,
    #                               list_order=list_order)

    # #  Perform space heating box plot analysis for all districts
    # #  Plot boxplots in two figure
    # #  #####################################################################
    output_path_curr = os.path.join(output_path, 'th_dem_three_axes')
    box_plot_analysis_triple_plot(mc_res=mc_res, output_path=output_path_curr,
                                  output_filename=output_filename, dpi=dpi,
                                  with_outliners=with_outliners,
                                  list_order=list_order)

    # # #  Perform electric demand box plot analysis for all districts
    # # #  Plot all boxplots in one figure
    # # #  #####################################################################
    # output_path_curr = os.path.join(output_path, 'el_dem_single_axes')
    # box_plot_analysis_el_dem(mc_res=mc_res, output_path=output_path_curr,
    #                          output_filename=output_filename, dpi=dpi,
    #                          with_outliners=with_outliners,
    #                          list_order=list_order)
    #
    # # #  Perform electric demand box plot analysis for all districts
    # # #  Plot all boxplots in one figure
    # # #  #####################################################################
    # output_path_curr = os.path.join(output_path, 'el_dem_two_axes')
    # box_plot_analysis_double_plot_el_dem(mc_res=mc_res,
    #                                      output_path=output_path_curr,
    #                                      output_filename=output_filename,
    #                                      dpi=dpi,
    #                                      with_outliners=with_outliners,
    #                                      list_order=list_order)
    #
    # # #  Perform electric demand box plot analysis for all districts
    # # #  Plot all boxplots in one figure
    # # #  #####################################################################
    # output_path_curr = os.path.join(output_path, 'dhw_dem_single_axes')
    # box_plot_analysis_dhw_dem(mc_res=mc_res, output_path=output_path_curr,
    #                          output_filename=output_filename, dpi=dpi,
    #                          with_outliners=with_outliners,
    #                          list_order=list_order)
    #
    # # #  Perform electric demand box plot analysis for all districts
    # # #  Plot all boxplots in one figure
    # # #  #####################################################################
    # output_path_curr = os.path.join(output_path, 'dhw_dem_two_axes')
    # box_plot_analysis_double_plot_dhw_dem(mc_res=mc_res,
    #                                      output_path=output_path_curr,
    #                                      output_filename=output_filename,
    #                                      dpi=dpi,
    #                                      with_outliners=with_outliners,
    #                                      list_order=list_order)
