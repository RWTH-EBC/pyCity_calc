#!/usr/bin/env python
# coding=utf-8
"""
Example for complex_city_generator. Creates a City with 32 buildings and
several streets. Also adds a LHN connecting to specific buildings.
"""

import os
import matplotlib.pyplot as plt

import pycity_calc.cities.scripts.city_generator.city_generator as citygen
import pycity_calc.visualization.city_visual as citvis
import \
    pycity_calc.cities.scripts.complex_city_generator as complex_city_generator
import pycity_calc.toolbox.dimensioning.dim_networks as dimnet


def run_example(printcitydata=False):
    #  # Userinputs
    #  #----------------------------------------------------------------------

    #  Year, timestep and location
    year = 2010
    timestep = 3600  # Timestep in seconds
    location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop
    altitude = 55  # Altitude of Bottrop

    #  Weather path
    try_path = None
    #  If None, used default TRY (region 5, 2010)

    #  Thermal generation method (1 - SLP; 2 - Load Modelica simulation profile)
    th_gen_method = 2
    #  th_gen_method = 2 is only valid for residential buildings and TRY
    #  for 2010, region 5. For non-residential buildings, SLPs are generated
    #  automatically.

    #  Manipulate thermal slp to fit to space heating demand?
    slp_manipulate = True
    #  True - Do manipulation
    #  False - Use original profile
    #  Only relevant, if th_gen_method == 1
    #  Sets thermal power to zero in time spaces, where average daily outdoor
    #  temperature is equal to or larger than 12 °C. Rescales profile to
    #  original demand value.

    #  Choose electric load profile generation method (1 - SLP; 2 - Stochastic)
    #  Stochastic profile is only generated for residential buildings,
    #  which have a defined number of occupants (otherwise, SLP is used)
    el_gen_method = 1
    #  If user defindes method_3_nb or method_4_nb within input file
    #  (only valid for non-residential buildings), SLP will not be used.
    #  Instead, corresponding profile will be loaded (based on measurement
    #  data, see ElectricalDemand.py within pycity)

    #  Do normalization of el. load profile
    #  (only relevant for el_gen_method=2).
    #  Rescales el. load profile to expected annual el. demand value in kWh
    do_normalization = True

    #  Generate DHW profiles? (True/False)
    use_dhw = True  # Only relevant for residential buildings

    #  DHW generation method? (1 - Annex 42; 2 - Stochastic profiles)
    #  Stochastic profiles require defined nb of occupants per residential
    #  building
    dhw_method = 1  # Only relevant for residential buildings

    #  Define dhw volume per capita and day (dhw_method = 1 and use_dhw=True)
    dhw_volumen = 64  # Only relevant for residential buildings

    #  Efficiency factor of thermal energy systems
    #  Used to convert input values (final energy demand) to net energy demand
    eff_factor = 0.85

    #  Define city district input data filename
    filename = 'city_example_complex_city_generator.txt'

    #  Define ouput data filename (pickled city object)
    save_city = 'city_example_complex_city_generator.p'

    #  Use TEASER to generate typebuildings?
    call_teaser = False
    teaser_proj_name = filename[:-4]

    str_node_filename = 'street_nodes_example_complex_city_generator.csv'
    str_edge_filename = 'street_edges_example_complex_city_generator.csv'

    #  Load street data from csv
    this_path = os.path.dirname(os.path.abspath(__file__))

    txt_path = os.path.join(this_path, 'inputs', filename)

    str_node_path = os.path.join(this_path, 'inputs', str_node_filename)
    str_edge_path = os.path.join(this_path, 'inputs', str_edge_filename)

    #  #----------------------------------------------------------------------

    #  Load district_data file
    district_data = citygen.get_district_data_from_txt(txt_path)

    city_object = \
        complex_city_generator.gen_city_with_street_network_from_csvfile(
            timestep=timestep,
            year=year,
            location=location,
            try_path=try_path,
            th_gen_method=th_gen_method,
            el_gen_method=el_gen_method,
            use_dhw=use_dhw,
            dhw_method=dhw_method,
            district_data=district_data,
            str_node_path=str_node_path,
            str_edge_path=str_edge_path,
            generation_mode=0,
            eff_factor=eff_factor,
            do_save=False,
            altitude=altitude,
            do_normalization=do_normalization,
            dhw_volumen=dhw_volumen,
            slp_manipulate=slp_manipulate,
            call_teaser=call_teaser,
            teaser_proj_name=
            teaser_proj_name)

    #  Add a local heating network to the city
    #  Add LHN to all buildings, except [1029, 1030, 1031, 1032]
    buildingnodes = []
    list_exclude = [1029, 1030, 1031, 1032]
    for i in city_object.node:
        if 'entity' in city_object.node[i]:
            if city_object.node[i]['entity']._kind == 'building':
                if i not in list_exclude:
                    buildingnodes.append(i)
    print('Buildnode for LHN:', buildingnodes)

    dimnet.add_lhn_to_city(city_object, buildingnodes, temp_vl=90,
                           temp_rl=50, c_p=4186, rho=1000,
                           use_street_network=True, network_type='heating',
                           plot_stepwise=False)

    # Plot the City
    if printcitydata:
        citvis.plot_city_district(city=city_object, plot_street=True,
                                  plot_lhn=True, offset=None,
                                  plot_build_labels=True,
                                  equal_axis=True, font_size=16,
                                  plt_title=None,
                                  x_label='x-Position in m',
                                  y_label='y-Position in m',
                                  show_plot=True)

        aggr_sp_heat = city_object.get_aggr_space_h_power_curve()
        aggr_dhw = city_object.get_aggr_dhw_power_curve()

        aggr_th_load_curve = aggr_sp_heat + aggr_dhw

        print(aggr_th_load_curve)

        #  Sort descending
        aggr_th_load_curve.sort()
        annual_power_curve = aggr_th_load_curve[::-1]

        plt.plot(annual_power_curve / 1000)

        plt.rc('text', usetex=True)
        font = {'family': 'serif', 'size': 24}
        plt.rc('font', **font)

        plt.xlabel('Time in hours')
        plt.ylabel('Thermal load in kW')
        plt.grid()
        plt.tight_layout()
        plt.show()


if __name__ == '__main__':
    run_example(True)
