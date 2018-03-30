#!/usr/bin/env python
# coding=utf-8
"""
Estimate thermo-electric flexibility for given city districts (solutions)
with energy systems
"""
from __future__ import division

import os
import pickle
import warnings
import numpy as np

try:
    import ebc_ues_plot.bar_plots as bar_plots
except:
    msg = 'Could not import ebc simple plot library! ' \
          'Set do_plot to False to prevent errors!'
    warnings.warn(msg)

import pycity_calc.toolbox.flex_quantification.flexibility_quant as flexquant


def main():
    use_eh = False  # Use flexibility of (inefficient) EH? (recommend: False)
    mod_boi = True  # Upscale boiler to prevent assertion error for ref.
    #  el. load generation of EHG? (recommend: True)

    do_plot = True

    this_path = os.path.dirname(os.path.abspath(__file__))

    name_folder_in = '4b_eco_mc_run_dyn_co2'

    path_folder_in = os.path.join(this_path, 'input', name_folder_in)

    city_front_name = 'city_with_esys'

    list_pathes_cities = []
    #  Search for mc_run_results_dict.pkl results dict in each subdirectory
    for root, dirs, files in os.walk(path_folder_in):
        for file in files:
            if file.startswith(city_front_name):
                list_pathes_cities.append(str(os.path.join(root, file)))

    for dir in list_pathes_cities:
        print(dir)

    dict_cities = {}
    list_ids = []

    for dir in list_pathes_cities:
        #  Extract ind number
        dirpath = os.path.dirname(dir)
        ind_nb = dirpath.split('_')[len(dirpath.split('_')) - 1]
        print('Extracted solution nb:')
        print(ind_nb)
        print()

        city = pickle.load(open(dir, mode='rb'))
        dict_cities[int(ind_nb)] = city
        list_ids.append(int(ind_nb))

    #  Sort keys in list_ids
    list_ids.sort()

    print('Start flexibility quantification for each city object')
    print('#####################################################')
    print()

    dict_beta_el_pos = {}
    dict_beta_el_neg = {}

    for i in range(len(list_ids)):
        id = list_ids[i]
        print('ID: ', id)

        city = dict_cities[id]

        (beta_el_pos, beta_el_neg) = \
            flexquant.calc_beta_el_city(city=city,
                                        use_eh=use_eh,
                                        mod_boi=mod_boi)

        dict_beta_el_pos[id] = beta_el_pos
        dict_beta_el_neg[id] = beta_el_neg

        print('beta_el_pos ', beta_el_pos)
        print('beta_el_neg ', beta_el_neg)
        print()

    if do_plot:
        #  Do plotting with ebc simple plot library

        #  Define output path
        path_output = os.path.join(this_path, 'output', 'flex_quant')
        file_out = 'flex_quant'

        #  English infos
        title_engl = None  # Add 'u' in front of string to define it as unicode
        # (e.g. when using non-ascii characters)
        xlab_engl = None
        ylab_engl = 'Relative energy flexibility'
        #  ylab only used if plot_sub == False

        #  Labels for x-axis columns in English
        label_1_engl = 'Positive'
        label_2_engl = 'Negative'
        label_3_engl = ''
        label_4_engl = ''
        label_5_engl = ''
        label_6_engl = ''
        label_7_engl = ''
        label_8_engl = ''
        #  If  plot_sub == True, define ylabs as labels!

        #  Labels for legend in English
        label_1_leg_engl = 'Ref.'
        label_2_leg_engl = 'Sol. 1'
        label_3_leg_engl = 'Sol. 33'
        label_4_leg_engl = 'Sol. 90'
        label_5_leg_engl = 'Sol. 101'
        label_6_leg_engl = 'Sol. 161'
        label_7_leg_engl = 'Sol. 265'
        label_8_leg_engl = ''

        #  German infos
        title_dt = None  # Add 'u' in front of string to define it as unicode
        # (e.g. when using non-ascii characters)
        xlab_dt = None
        ylab_dt = u'Relative Energieflexibilität'
        #  ylab only used if plot_sub == False

        #  Labels for x-axis columns in German
        label_1_dt = 'Positiv'
        label_2_dt = 'Negativ'
        label_3_dt = ''
        label_4_dt = ''
        label_5_dt = ''
        label_6_dt = ''
        label_7_dt = ''
        label_8_dt = ''
        #  If  plot_sub == True, define ylabs as labels!

        #  Labels for legend in German
        label_1_leg_dt = 'Ref.'
        label_2_leg_dt = 'Sol. 1'
        label_3_leg_dt = 'Sol. 33'
        label_4_leg_dt = 'Sol. 90'
        label_5_leg_dt = 'Sol. 101'
        label_6_leg_dt = 'Sol. 161'
        label_7_leg_dt = 'Sol. 265'
        label_8_leg_dt = ''

        #  Fontsize
        fontsize = 11
        #  dpi size
        dpi = 100

        #  Plot figures?
        show_plot = False

        #  Use tight layout?
        use_tight = True

        #  Define position of legend
        legend_pos = 'inside'
        #  legend_pos = 'inside'  # Generate legend within box
        #  legend_pos = 'outside'  # Generate legend below box

        #  Adjust figure size to default (None), 'a4' or 'a4_half', 'a5'
        fig_adjust = 'a4'  # 'a4_half', 'a5'
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

        #  Copy input file into output folder?
        copy_input = False

        #  Additionally save as tikz for latex?
        save_tikz = True

        #  Save data array as pickle file?
        save_data_array = True

        #  Set additional values next to each bar
        use_autolabel = False

        #  Rotate x labels?
        rotate_x_labels = False

        #  Define relative bar width (0 < bar_width <= 1)
        bar_width = None

        #  Set ylimits
        set_ylimit = False
        ymin = 0
        ymax = 100

        #  #------------------------------------------------------------

        list_labels_engl = [label_1_engl, label_2_engl, label_3_engl,
                            label_4_engl, label_5_engl, label_6_engl,
                            label_7_engl,
                            label_8_engl]
        list_labels_dt = [label_1_dt, label_2_dt, label_3_dt,
                          label_4_dt, label_5_dt, label_6_dt, label_7_dt,
                          label_8_dt]

        list_labels_leg_engl = [label_1_leg_engl, label_2_leg_engl,
                                label_3_leg_engl, label_4_leg_engl,
                                label_5_leg_engl, label_6_leg_engl,
                                label_7_leg_engl, label_8_leg_engl]
        list_labels_leg_dt = [label_1_leg_dt, label_2_leg_dt, label_3_leg_dt,
                              label_4_leg_dt, label_5_leg_dt, label_6_leg_dt,
                              label_7_leg_dt, label_8_leg_dt]

        #  Make dir, if not existent
        if not os.path.isdir(path_output):
            os.makedirs(path_output)

        #  Prepare dataset
        array_data = np.zeros((len(list_ids), 2))

        #  Save results to array_data
        for m in range(len(array_data)):
            id = list_ids[m]
            array_data[m][0] = dict_beta_el_pos[id]
            array_data[m][1] = dict_beta_el_neg[id]

        array_data= np.transpose(array_data)

        if bar_width is None:
            #  bar_width estimation:
            if array_data.ndim == 1:
                bar_width = 0.6
            elif array_data.ndim == 2:
                bar_width = 0.7
            elif array_data.ndim >= 2:
                bar_width = 0.8

        print('Chosen bar_width: ', bar_width)

        bar_plots.plot_multi_language_multi_color_bar(
            dataset=array_data,
            output_path=path_output,
            output_filename=file_out,
            show_plot=show_plot,
            use_tight=use_tight,
            title_engl=title_engl,
            xlab_engl=xlab_engl,
            ylab_engl=ylab_engl,
            list_labels_engl=list_labels_engl,
            title_dt=title_dt, xlab_dt=xlab_dt,
            ylab_dt=ylab_dt,
            list_labels_dt=list_labels_dt,
            fontsize=fontsize,
            fig_adjust=fig_adjust,
            input_path=None,
            dpi=dpi, copy_py=copy_py,
            copy_input=copy_input,
            save_data_array=save_data_array,
            save_tikz=save_tikz,
            list_labels_leg_engl=
            list_labels_leg_engl,
            list_labels_leg_dt=
            list_labels_leg_dt,
            set_ylimit=set_ylimit,
            ymin=ymin, ymax=ymax,
            use_autolabel=use_autolabel,
            bar_width=bar_width,
            rotate_x_labels=rotate_x_labels,
            use_font=use_font,
            legend_pos=legend_pos)

if __name__ == '__main__':
    main()