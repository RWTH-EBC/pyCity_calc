#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Code extracts and saves load profiles of all buildings of city object
"""
from __future__ import division

import os
import warnings
import pickle
import numpy as np
import matplotlib.pyplot as plt

import pycity_calc.visualization.city_visual as citvis
import pycity_calc.cities.scripts.city_generator.city_generator as citgen
import pycity_calc.toolbox.analyze.save_city_data as savcit


def gen_path_if_not_existent(dir):
    """
    Generate directory, if not existent

    Parameters
    ----------
    dir : str
        Directory path
    """
    if not os.path.exists(dir):
        os.makedirs(dir)


def extract_build_base_data(city, id, file_path, use_german=False):
    """
    Extract and save building base data to txt file

    Parameters
    ----------
    city : object
        City object
    id : int
        Building node id
    file_path : str
        Path to save file to (e.g. ...\building_data.txt)
    use_german : bool, optional
        Defines, if English or German language should be used
        (default: False). If False, uses English language.
    """
    #  Building pointer
    build = city.node[id]['entity']

    if use_german:

        with open(file_path, mode='w') as f:
            f.write(u'Gebäude-ID: ' + str(id) + '\n')

            x_coord = city.node[id]['position'].x
            y_coord = city.node[id]['position'].y
            f.write('X-Koordinate in m: ' + str(int(x_coord)) + '\n')
            f.write('Y-Koordinate in m: ' + str(int(y_coord)) + '\n')

            if build.build_year is not None:
                build_year = int(build.build_year)
            else:
                build_year = None
            f.write(
                'Baujahr: ' + str(build_year) + '\n')

            if build.mod_year is not None:
                mod_year = int(build.mod_year)
            else:
                mod_year = None
            f.write('Letztes Sanierungsjahr: ' + str(mod_year) + '\n')
            f.write(u'Nummer Gebäudetyp: ' + str(build.build_type) + '\n')

            build_name = citgen.conv_build_type_nb_to_name(build.build_type)

            f.write(
                u'(Engl.) Erläuterung Gebäudetyp: ' + str(build_name) + '\n')

            #  Write building data to file
            f.write('Anzahl Zonen/Apartments: ' + str(
                len(build.apartments)) + '\n')

            f.write(u'Nutzbare PV-Fläche in m2: ' +
                    str(build.roof_usabl_pv_area) + '\n')
            f.write(u'Nettogrundfläche in m2: ' +
                    str(build.net_floor_area) + '\n')
            f.write(
                u'Bebaute Grundfläche in m2: ' + str(build.ground_area) + '\n')
            f.write(u'Mittlere Geschosshöhe in m: ' +
                    str(build.height_of_floors) + '\n')
            f.write('Anzahl Geschosse: ' + str(build.nb_of_floors) + '\n')

            ann_th_sh_demand = build.get_annual_space_heat_demand()
            ann_el_demand = build.get_annual_el_demand()
            ann_dhw_demand = build.get_annual_dhw_demand()

            f.write(u'Jährlicher Nutzenergiebedarf für Raumwärme in kWh/a: '
                    + str(int(ann_th_sh_demand)) + '\n')
            f.write(u'Jährlicher, elektrischer Energiebedarf (ohne Warmwasser)'
                    ' in kWh/a: '
                    + str(int(ann_el_demand)) + '\n')
            f.write(u'Jährlicher Nutzenergiebedarf Warmwasser in kWh/a: '
                    + str(int(ann_dhw_demand)) + '\n')
            f.write('\n')

            if 'osm_id' in city.node[id]:
                f.write(
                    'openstreetmap id: ' + str(city.node[id]['osm_id']) + '\n')
            if 'name' in city.node[id]:
                f.write('OSM name: ' + str(city.node[id]['name']) + '\n')
            if 'addr_street' in city.node[id]:
                f.write('Street: ' + str(city.node[id]['addr_street']) + '\n')
            if 'addr_housenumber' in city.node[id]:
                f.write('Street nb.: ' +
                        str(city.node[id]['addr_housenumber']) + '\n')
            if 'comment' in city.node[id]:
                f.write('OSM comment: ' +
                        str(city.node[id]['comment']) + '\n')

            # print(vars(build))

            f.close()

    else:

        with open(file_path, mode='w') as f:
            f.write('Building node id: ' + str(id) + '\n')

            x_coord = city.node[id]['position'].x
            y_coord = city.node[id]['position'].y
            f.write('X-coordinate in m: ' + str(int(x_coord)) + '\n')
            f.write('Y-coordinate in m: ' + str(int(y_coord)) + '\n')

            if build.build_year is not None:
                build_year = int(build.build_year)
            else:
                build_year = None
            f.write(
                'Year of construction: ' + str(build_year) + '\n')

            if build.mod_year is not None:
                mod_year = int(build.mod_year)
            else:
                mod_year = None
            f.write('Last year of modernization: ' + str(mod_year) + '\n')

            f.write('Building type number: ' + str(build.build_type) + '\n')

            build_name = citgen.conv_build_type_nb_to_name(build.build_type)

            f.write('Building type explanation: ' + str(build_name) + '\n')

            #  Write building data to file
            f.write('Nb. of zones/apartments: ' + str(
                len(build.apartments)) + '\n')

            f.write('Usable PV roof area in m2: ' +
                    str(build.roof_usabl_pv_area) + '\n')
            f.write('Net floor area (NFA) in m2: ' +
                    str(build.net_floor_area) + '\n')
            f.write('Ground area in m2: ' + str(build.ground_area) + '\n')
            f.write('Height of single floor in m: ' +
                    str(build.height_of_floors) + '\n')
            f.write('Number of floors: ' + str(build.nb_of_floors) + '\n')

            ann_th_sh_demand = build.get_annual_space_heat_demand()
            ann_el_demand = build.get_annual_el_demand()
            ann_dhw_demand = build.get_annual_dhw_demand()

            f.write('Annual net space heating energy demand in kWh/a: '
                    + str(int(ann_th_sh_demand)) + '\n')
            f.write('Annual electric energy demand in kWh/a: '
                    + str(int(ann_el_demand)) + '\n')
            f.write('Annual net hot water energy demand in kWh/a: '
                    + str(int(ann_dhw_demand)) + '\n')
            f.write('\n')

            if 'osm_id' in city.node[id]:
                f.write(
                    'openstreetmap id: ' + str(city.node[id]['osm_id']) + '\n')
            if 'name' in city.node[id]:
                f.write('OSM name: ' + str(city.node[id]['name']) + '\n')
            if 'addr_street' in city.node[id]:
                f.write('Street: ' + str(city.node[id]['addr_street']) + '\n')
            if 'addr_housenumber' in city.node[id]:
                f.write('Street nb.: ' +
                        str(city.node[id]['addr_housenumber']) + '\n')
            if 'comment' in city.node[id]:
                f.write('OSM comment: ' +
                        str(city.node[id]['comment']) + '\n')

            # print(vars(build))

            f.close()


def extract_build_profiles(city, id, file_path, do_plot=False,
                           use_german=False, save_tikz=False):
    """
    Extract and save building profiles to file

    Parameters
    ----------
    city : object
        City object
    id : int
        Building node id
    file_path : str
        Path to save file to (e.g. ...\building_data.txt)
    do_plot : bool, optional
        Defines, if profiles should be plotted (default: False)
    use_german : bool, optional
        Defines, if English or German language should be used
        (default: False). If False, uses English language.
    save_tikz : bool, optional
        Define, if figure should be saved as tikz (default: False)
    """

    #  Building pointer
    build = city.node[id]['entity']

    #  Get power curves
    sh_profile = build.get_space_heating_power_curve()
    el_profile = build.get_electric_power_curve()
    dhw_profile = build.get_dhw_power_curve()

    #  Generate time array
    timestep = city.environment.timer.timeDiscretization
    year_in_seconds = 365 * 24 * 3600
    time_array = np.arange(0, year_in_seconds, timestep)

    #  Stack results together
    res_array = np.vstack((time_array, sh_profile))
    res_array = np.vstack((res_array, el_profile))
    res_array = np.vstack((res_array, dhw_profile))

    #  Transpose array
    res_array = np.transpose(res_array)

    #  Define header
    if use_german:
        #  Define header
        header = u'Zeit in Sekunden\tThermische Leistung Raumwärme in Watt\t' \
                 u'Elektrische Leistung in Watt' \
                 u'\tLeistung Warmwasser in Watt'
    else:
        header = 'Time in seconds\tNet space heating power in Watt\t' \
                 'Electric power in Watt\tNet hot water power in Watt'

    # Save numpy array to txt
    np.savetxt(fname=file_path, X=res_array, delimiter='\t', header=header)

    if do_plot:

        try:
            import ebc_ues_plot.line_plots as uesline
        except:
            msg = 'Cannot import ebc_ues_plot / simple_plot package.' \
                  'Thus, cannot perform plotting in EBC style!'
            raise AssertionError(msg)

        # Generate time array
        nb_timesteps = 365 * 24 * 3600 / timestep
        time_array = np.arange(0, nb_timesteps, timestep / 3600)

        plotdata = uesline.PlottingData()
        plotdata.add_data_entry(time_array, sh_profile / 1000)
        plotdata.add_data_entry(time_array, el_profile / 1000)
        plotdata.add_data_entry(time_array, dhw_profile / 1000)

        #  Perform plotting
        if use_german:
            output_path = os.path.join(os.path.dirname(file_path),
                                       'Lastgaenge')
        else:
            output_path = os.path.join(os.path.dirname(file_path),
                                       'power_curves_graphics')

        uesline.plot_multi_language_multi_color(plot_data=plotdata,
                                                plot_sub=True,
                                                output_path=output_path,
                                                output_filename=str(id),
                                                show_plot=False,
                                                use_tight=True,
                                                title_engl=None,
                                                xlab_engl='Time in hours',
                                                ylab_engl='Power in kW',
                                                list_labels_engl=[
                                                    'Space heating\npower in kW',
                                                    'Electric\npower in kW',
                                                    'Hot water\npower in kW'],
                                                title_dt=None,
                                                xlab_dt='Zeit in Stunden',
                                                ylab_dt='Leistung in kW',
                                                list_labels_dt=[
                                                    'Heizleistung\nin kW',
                                                    'Elektrische\nLeistung in kW',
                                                    'Warmwasser-\nleistung in kW'],
                                                fontsize=12,
                                                fig_adjust='a4',
                                                legend_pos_within=True,
                                                put_leg='below', dpi=500,
                                                # linewidth=1,
                                                set_zero_point=True,
                                                set_x_limits=True,
                                                xmin=0, xmax=8760,
                                                set_y_limits=False,
                                                # ymin=ymin, ymax=ymax,
                                                use_grid=False,
                                                # input_path=input_path,
                                                save_tikz=save_tikz,
                                                # rotate_x_labels=rotate_x_labels,
                                                copy_py=True,
                                                copy_input=False,
                                                save_data_array=True,
                                                use_font='arial')


def extract_city_base_data(city, out_file_path, do_plot=False,
                           use_german=False, save_tikz=False):
    """
    Extract and save basic city data

    Parameters
    ----------
    city : object
        City object of pyCity_calc
    out_file_path : str
        Path to save data to
    do_plot : bool, optional
        Defines, if profiles should be plotted (default: False)
    use_german : bool, optional
        Defines, if English or German language should be used
        (default: False). If False, uses English language.
    save_tikz : bool, optional
        Define, if figure should be saved as tikz (default: False)
    """

    #  Extract basic city data to path (.txt)
    if use_german:

        with open(out_file_path, mode='w') as f:
            f.write('Anzahl Knoten: ' + str(len(city.nodes())) + '\n')
            f.write(u'(Z.b. Gebäude, Straßen etc.)\n')

            nb_build_entities = city.get_nb_of_building_entities()
            f.write(u'Anzahl Gebäude: ' + str(nb_build_entities) + '\n')

            list_ent = city.get_list_build_entity_node_ids()
            f.write(u'Liste mit Gebäude-IDs: ' + str(list_ent) + '\n')

            location = city.environment.location
            f.write(
                u'Längen-/Breitengrad der Stadt: ' + (str(location)) + '\n')

            altitude = city.environment.weather.altitude
            f.write(u'Höhe über NN: ' + str(altitude) + '\n')

            nb_occ = city.get_nb_occupants()
            f.write('Anzahl Bewohner: ' + str(nb_occ) + '\n')

            ann_th_sh_demand = city.get_annual_space_heating_demand()
            ann_el_demand = city.get_annual_el_demand()
            ann_dhw_demand = city.get_annual_dhw_demand()

            f.write(u'Jährlicher Nutzenergiebedarf für Raumwärme in kWh/a: '
                    + str(int(ann_th_sh_demand)) + '\n')
            f.write(u'Jährlicher, elektrischer Energiebedarf (ohne Warmwasser)'
                    ' in kWh/a: '
                    + str(int(ann_el_demand)) + '\n')
            f.write(u'Jährlicher Nutzenergiebedarf Warmwasser in kWh/a: '
                    + str(int(ann_dhw_demand)) + '\n')
            f.write('\n')

            f.close()

            if do_plot:
                #  Plot energy demands as bar plots
                try:
                    import ebc_ues_plot.bar_plots as uesbar
                except:
                    msg = 'Could not import ebc_ues_plot module.'
                    raise AssertionError(msg)

                dataset = np.array([[ann_th_sh_demand], [ann_el_demand],
                                    [ann_dhw_demand]])

                output_path = os.path.join(os.path.dirname(out_file_path),
                                           'Stadt_Saulendiagramm_Energie')
                f_name = 'Stadt_Saulendiagramm_Energie'

                uesbar.plot_multi_language_multi_color_bar(dataset=dataset,
                                                           output_path=output_path,
                                                           output_filename=f_name,
                                                           show_plot=False,
                                                           use_tight=True,
                                                           title_engl=None,
                                                           xlab_engl=None,
                                                           ylab_engl='Energy demands in kWh/a',
                                                           list_labels_engl=[
                                                               'Space heating',
                                                               'Electric energy',
                                                               'Hot water energy'],
                                                           title_dt=None,
                                                           xlab_dt=None,
                                                           ylab_dt=u'Energiebedarf in kWh/a',
                                                           list_labels_dt=[
                                                               u'Raumwärme',
                                                               u'Elektr. Energie',
                                                               u'Warmwasser'],
                                                           fontsize=16,
                                                           fig_adjust=None,
                                                           dpi=300,
                                                           copy_py=True,
                                                           copy_input=False,
                                                           input_path=None,
                                                           save_data_array=True,
                                                           save_tikz=save_tikz,
                                                           list_labels_leg_engl=None,
                                                           list_labels_leg_dt=None,
                                                           use_autolabel=False,
                                                           bar_width=0.7,
                                                           set_ylimit=False,
                                                           ymin=None,
                                                           ymax=None,
                                                           rotate_x_labels=False,
                                                           use_font='arial',
                                                           legend_pos='inside')


    else:

        with open(out_file_path, mode='w') as f:
            f.write('Number of nodes: ' + str(len(city.nodes())) + '\n')

            nb_build_entities = city.get_nb_of_building_entities()
            f.write('Number of buildings: ' + str(nb_build_entities) + '\n')

            list_ent = city.get_list_build_entity_node_ids()
            f.write('List of building ids: ' + str(list_ent) + '\n')

            location = city.environment.location
            f.write('Location (lat/long): ' + (str(location)) + '\n')

            altitude = city.environment.weather.altitude
            f.write('Altitude in m above NN: ' + str(altitude) + '\n')

            nb_occ = city.get_nb_occupants()
            f.write('Total number of occupants: ' + str(nb_occ) + '\n')

            ann_th_sh_demand = city.get_annual_space_heating_demand()
            ann_el_demand = city.get_annual_el_demand()
            ann_dhw_demand = city.get_annual_dhw_demand()

            f.write('Annual net space heating energy demand in kWh/a: '
                    + str(int(ann_th_sh_demand)) + '\n')
            f.write('Annual electric energy demand in kWh/a: '
                    + str(int(ann_el_demand)) + '\n')
            f.write('Annual net hot water energy demand in kWh/a: '
                    + str(int(ann_dhw_demand)) + '\n')
            f.write('\n')

            f.close()

            if do_plot:
                #  Plot energy demands as bar plots
                try:
                    import ebc_ues_plot.bar_plots as uesbar
                except:
                    msg = 'Could not import ebc_ues_plot module.'
                    raise AssertionError(msg)

                dataset = np.array([[ann_th_sh_demand], [ann_el_demand],
                                    [ann_dhw_demand]])

                output_path = os.path.join(os.path.dirname(out_file_path),
                                           'city_energy_bars')
                f_name = 'city_bar_plot'

                uesbar.plot_multi_language_multi_color_bar(dataset=dataset,
                                                           output_path=output_path,
                                                           output_filename=f_name,
                                                           show_plot=False,
                                                           use_tight=True,
                                                           title_engl=None,
                                                           xlab_engl=None,
                                                           ylab_engl='Energy demands in kWh/a',
                                                           list_labels_engl=[
                                                               'Space heating',
                                                               'Electric energy',
                                                               'Hot water energy'],
                                                           title_dt=None,
                                                           xlab_dt=None,
                                                           ylab_dt='Energiebedarf in kWh/a',
                                                           list_labels_dt=[
                                                               u'Raumwärme',
                                                               'Elektr. Energie',
                                                               'Warmwasser'],
                                                           fontsize=16,
                                                           fig_adjust=None,
                                                           dpi=300,
                                                           copy_py=True,
                                                           copy_input=False,
                                                           input_path=None,
                                                           save_data_array=True,
                                                           save_tikz=save_tikz,
                                                           list_labels_leg_engl=None,
                                                           list_labels_leg_dt=None,
                                                           use_autolabel=False,
                                                           bar_width=0.7,
                                                           set_ylimit=False,
                                                           ymin=None,
                                                           ymax=None,
                                                           rotate_x_labels=False,
                                                           use_font='arial',
                                                           legend_pos='inside')


def extract_city_profiles(city, city_path, do_plot, use_german=False,
                          save_tikz=False):
    """

    Parameters
    ----------
    city : object
        City object of pyCity_calc
    city_path : str
        Path to folder, where profiles should be saved
    do_plot : bool, optional
        Defines, if profiles should be plotted (default: False)
    use_german : bool, optional
        Defines, if English or German language should be used
        (default: False). If False, uses English language
    save_tikz : bool, optional
        Define, if figure should be saved as tikz (default: False)
    """
    #  Get power curves
    sh_profile = city.get_aggr_space_h_power_curve()
    el_profile = city.get_aggr_el_power_curve()
    dhw_profile = city.get_aggr_dhw_power_curve()

    #  Generate time array
    timestep = city.environment.timer.timeDiscretization
    year_in_seconds = 365 * 24 * 3600
    time_array = np.arange(0, year_in_seconds, timestep)

    #  Stack results together
    res_array = np.vstack((time_array, sh_profile))
    res_array = np.vstack((res_array, el_profile))
    res_array = np.vstack((res_array, dhw_profile))

    #  Transpose array
    res_array = np.transpose(res_array)

    if use_german:
        #  Define header
        header = u'Zeit in Sekunden\tThermische Leistung Raumwärme in Watt\t' \
                 u'Elektrische Leistung in Watt' \
                 u'\tLeistung Warmwasser in Watt'

        data_f_name = 'Stadt_Profile.txt'

    else:
        #  Define header
        header = 'Time in seconds\tNet space heating power in Watt\t' \
                 'Electric power in Watt\tNet hot water power in Watt'

        data_f_name = 'city_profiles.txt'

    data_f_path = os.path.join(city_path, data_f_name)

    #  Save numpy array to txt
    np.savetxt(fname=data_f_path, X=res_array, delimiter='\t', header=header)

    if do_plot:
        #  Plot city profiles to path

        try:
            import ebc_ues_plot.line_plots as uesline
        except:
            msg = 'Cannot import ebc_ues_plot / simple_plot package.' \
                  'Thus, cannot perform plotting in EBC style!'
            raise AssertionError(msg)

        # Generate time array
        nb_timesteps = 365 * 24 * 3600 / timestep
        time_array = np.arange(0, nb_timesteps, timestep / 3600)

        plotdata = uesline.PlottingData()
        plotdata.add_data_entry(time_array, sh_profile / 1000)
        plotdata.add_data_entry(time_array, el_profile / 1000)
        plotdata.add_data_entry(time_array, dhw_profile / 1000)

        #  Perform plotting
        if use_german:
            output_path = os.path.join(city_path, 'Stadt_Lastgaenge')
            output_filename = 'Stadt_Lastgaenge'

        else:
            output_path = os.path.join(city_path, 'city_power_curves')
            output_filename = 'city_power_curves'

        uesline.plot_multi_language_multi_color(plot_data=plotdata,
                                                plot_sub=True,
                                                output_path=output_path,
                                                output_filename=output_filename,
                                                show_plot=False,
                                                use_tight=True,
                                                title_engl=None,
                                                xlab_engl='Time in hours',
                                                ylab_engl='Power in kW',
                                                list_labels_engl=[
                                                    'Space heating\npower in kW',
                                                    'Electric\npower in kW',
                                                    'Hot water\npower in kW'],
                                                title_dt=None,
                                                xlab_dt='Zeit in Stunden',
                                                ylab_dt='Leistung in kW',
                                                list_labels_dt=[
                                                    u'Heizleistung\nin kW',
                                                    u'Elektrische\nLeistung in kW',
                                                    u'Warmwasser-\nleistung in kW'],
                                                fontsize=12,
                                                fig_adjust='a4',
                                                legend_pos_within=True,
                                                put_leg='below', dpi=500,
                                                # linewidth=1,
                                                set_zero_point=True,
                                                set_x_limits=True,
                                                xmin=0, xmax=8760,
                                                set_y_limits=False,
                                                # ymin=ymin, ymax=ymax,
                                                use_grid=False,
                                                # input_path=input_path,
                                                save_tikz=save_tikz,
                                                # rotate_x_labels=rotate_x_labels,
                                                copy_py=True,
                                                copy_input=False,
                                                save_data_array=True,
                                                use_font='arial')


def extract_city_data(city, out_path, do_plot=False, use_german=False,
                      save_tikz=False):
    """
    Extract and save city data to file.

    Parameters
    ----------
    city : object
        City object of pyCity_calc
    out_path : str
        Path to save city data to
    do_plot: bool, optional
        Defines, if load profiles should be plotted
    use_german : bool, optional
        Defines, if English or German language should be used
        (default: False). If False, uses English language.
    save_tikz : bool, optional
        Define, if figure should be saved as tikz (default: False)
    """

    if use_german:

        city_path = os.path.join(out_path, 'Stadt')
        gen_path_if_not_existent(city_path)

        city_out = 'Stadt_Daten.txt'
        data_file = os.path.join(city_path, city_out)

    else:

        city_path = os.path.join(out_path, 'city')
        gen_path_if_not_existent(city_path)

        city_out = 'city_data.txt'
        data_file = os.path.join(city_path, city_out)

    # Extract city base data
    extract_city_base_data(city=city, out_file_path=data_file, do_plot=do_plot,
                           use_german=use_german, save_tikz=save_tikz)

    #  Extract data into single file
    if use_german:
        save_path = os.path.join(city_path, 'stadt_gebaeudedaten.txt')
        x_label = 'X-Koordinate in m'
        y_label = 'Y-Koordinate in m'

    else:
        save_path = os.path.join(city_path, 'city_data_buildings.txt')
        x_label = 'x-coordinate in m'
        y_label = 'y-coordinate in m'

    savcit.save_city_data_to_file(city=city, save_path=save_path,
                                  use_german=use_german)

    #  Generate plot with ids and save it to out_path
    citvis.plot_city_district(city=city,
                              city_list=None,
                              plot_buildings=True,
                              plot_street=True,
                              plot_lhn=False, plot_deg=False,
                              plot_esys=False,
                              offset=7,
                              plot_build_labels=True, plot_str_labels=False,
                              plot_heat_labels=False,
                              equal_axis=False, font_size=16, plt_title=None,
                              x_label=x_label,
                              y_label=y_label,
                              show_plot=False,
                              fig_adjust=None,
                              plot_elec_labels=False, save_plot=True,
                              save_path=city_path, dpi=300, plot_color=True,
                              plot_engl=not use_german,
                              auto_close=True, plot_str_dist=150,
                              node_size=50)

    #  Extract and save city profiles
    extract_city_profiles(city=city, city_path=city_path, do_plot=do_plot,
                          use_german=use_german, save_tikz=save_tikz)


def extract_city_n_build_data(city, out_path, use_german=False,
                              save_tikz=False):
    """

    Parameters
    ----------
    city : object
        City object of pyCity_calc
    out_path : str
        Path to save profiles to
    use_german : bool, optional
        Defines, if English or German language should be used
        (default: False). If False, uses English language.
    save_tikz : bool, optional
        Define, if figure should be saved as tikz (default: False)
    """
    #  Get all building nodes
    list_ids = city.get_list_build_entity_node_ids()

    #  Extract city data
    extract_city_data(city=city, out_path=out_path, do_plot=True,
                      use_german=use_german, save_tikz=save_tikz)

    #  Extract building data
    for n in list_ids:
        #  Generate folder with node id name
        if use_german:
            curr_path = os.path.join(out_path, 'Gebaeude', str(n))
        else:
            curr_path = os.path.join(out_path, 'buildings', str(n))

        gen_path_if_not_existent(curr_path)

        #  Open txt file and add
        if use_german:
            data_f_name = str(n) + '_Daten.txt'
        else:
            data_f_name = str(n) + '_data.txt'
        data_f_path = os.path.join(curr_path, data_f_name)

        #  Extract building base data and save them to file
        extract_build_base_data(city=city, id=n, file_path=data_f_path,
                                use_german=use_german)

        #  Open txt file and add
        if use_german:
            data_f_name = str(n) + '_Profile.txt'
        else:
            data_f_name = str(n) + '_profiles.txt'
        data_f_path = os.path.join(curr_path, data_f_name)

        extract_build_profiles(city=city, id=n, file_path=data_f_path,
                               do_plot=True, use_german=use_german,
                               save_tikz=save_tikz)


if __name__ == '__main__':
    this_path = os.path.dirname(os.path.abspath(__file__))

    city_f_name = 'city_3_buildings_mixed.pkl'
    input_path = os.path.join(this_path, 'input', city_f_name)

    out_name = city_f_name[:-4]
    out_path = os.path.join(this_path, 'output', 'extracted', out_name)

    use_german = False
    save_tikz = True

    #  Make out_path, if not existent
    gen_path_if_not_existent(out_path)

    city = pickle.load(open(input_path, mode='rb'))

    if use_german == True and save_tikz == True:
        msg = 'Choose use_german=True. Thus, save_tikz is set to False,' \
              ' due to possible utf-8 errors.'
        warnings.warn(msg)
        save_tikz = False

    extract_city_n_build_data(city=city, out_path=out_path,
                              use_german=use_german, save_tikz=save_tikz)
