#!/usr/bin/env python
# coding=utf-8
"""
Pytest script for city generators
"""
from __future__ import division

import os

import pycity_calc.cities.scripts.city_generator.city_generator as citygen
import pycity_calc.cities.scripts.street_generator.street_generator as strgen
import pycity_calc.cities.scripts.energy_network_generator as enetgen
import pycity_calc.cities.scripts.energy_sys_generator as esysgen

from pycity_calc.test.pycity_calc_fixtures import fixture_building, \
    fixture_environment, fixture_city, fixture_apartment, fixture_th_demand, \
    fixture_el_demand


class Test_City_Generators():

    def test_city_generator(self, fixture_environment):

        this_path = os.path.dirname(os.path.abspath(__file__))

        th_gen_method = 1
        el_gen_method = 1
        do_normalization = True
        use_dhw = False
        dhw_method = 1
        dhw_volumen = 64
        eff_factor = 1
        filename = 'city_clust_simple.txt'
        filepath = os.path.join(this_path, 'input_generator', filename)

        str_node_filename = 'street_nodes_cluster_simple.csv'
        str_edge_filename = 'street_edges_cluster_simple.csv'
        str_node_path = os.path.join(this_path, 'input_generator',
                                     str_node_filename)
        str_edge_path = os.path.join(this_path, 'input_generator',
                                     str_edge_filename)

        #  Path to energy network input file (csv/txt; tab separated)
        network_filename = 'city_clust_simple_networks.txt'
        network_path = os.path.join(this_path, 'input_generator',
                                     network_filename)

        #  Path to energy system input file (csv/txt; tab separated)
        esys_filename = 'city_clust_simple_enersys.txt'
        esys_path = os.path.join(this_path, 'input_generator',
                                 esys_filename)

        timestep = fixture_environment.timer.timeDiscretization
        year = fixture_environment.timer.year
        location = fixture_environment.location
        altitude = fixture_environment.weather.altitude

        #  Load district_data file
        district_data = citygen.get_district_data_from_txt(filepath)

        city = citygen.run_city_generator(generation_mode=0,
                                          timestep=timestep,
                                          year_timer=year,
                                          year_co2=year,
                                          location=location,
                                          th_gen_method=th_gen_method,
                                          el_gen_method=el_gen_method,
                                          use_dhw=use_dhw,
                                          dhw_method=dhw_method,
                                          district_data=district_data,
                                          pickle_city_filename=None,
                                          eff_factor=eff_factor,
                                          show_city=False,
                                          try_path=None, altitude=altitude,
                                          dhw_volumen=dhw_volumen,
                                          do_normalization=do_normalization,
                                          do_save=False)

        assert city.get_nb_of_building_entities() == 12
        assert len(city.nodes()) == 12

        assert city.nodes[1004]['position'].x == 10
        assert city.nodes[1004]['position'].y == 70

        build_4 = city.nodes[1004]['entity']

        assert build_4._kind == 'building'
        assert build_4.get_number_of_apartments() == 1
        assert build_4.get_number_of_occupants() == 2
        assert build_4.get_annual_space_heat_demand() - 15000 < 0.001 * 15000
        assert build_4.get_annual_el_demand() - 1700 < 0.001 * 1700
        assert build_4.build_year == 1980
        assert build_4.mod_year == None
        assert build_4.net_floor_area == 100
        assert build_4.ground_area == None
        assert build_4.roof_usabl_pv_area == 30
        assert build_4.dormer == None

        #  Get street network data
        name_list, pos_list, edge_list = \
            strgen.load_street_data_from_csv(path_str_nodes=str_node_path,
                                             path_str_edges=str_edge_path)

        #  Add street network to city_object
        strgen.add_street_network_to_city(city, name_list, pos_list,
                                          edge_list)

        assert city.get_nb_of_building_entities() == 12
        assert len(city.nodes()) == 12 + 6

        assert city.nodes[1018]['position'].x == 40
        assert city.nodes[1018]['position'].y == 0

        assert city.edges[1017, 1018]['network_type'] == 'street'

        #  Load energy networks planing data
        dict_e_net_data = enetgen.load_en_network_input_data(network_path)

        #  Add energy networks to city
        enetgen.add_energy_networks_to_city(city=city,
                                            dict_data=dict_e_net_data)

        #  Node number should remain the same, because no energy network
        #  nodes have been generated (only connections between building nodes)
        assert city.get_nb_of_building_entities() == 12
        assert len(city.nodes()) == 12 + 6

        assert city.edges[1002, 1003]['network_type'] == 'heating'
        assert city.edges[1010, 1011]['network_type'] == 'heating_and_deg'
        assert city.edges[1006, 1007]['network_type'] == 'electricity'

        #  Load energy networks planing data
        list_esys = esysgen.load_enersys_input_data(esys_path)

        #  Generate energy systems
        esysgen.gen_esys_for_city(city=city, list_data=list_esys,
                                  dhw_scale=False)

        assert city.get_nb_of_building_entities() == 12
        assert len(city.nodes()) == 12 + 6

        build_1001 = city.nodes[1001]['entity']
        build_1006 = city.nodes[1006]['entity']
        build_1007 = city.nodes[1007]['entity']
        build_1008 = city.nodes[1008]['entity']
        build_1012 = city.nodes[1012]['entity']

        assert build_1001.bes.hasChp == True
        assert build_1001.bes.hasBoiler == True
        assert build_1001.bes.hasTes == True
        assert build_1001.bes.hasBattery == False
        assert build_1001.bes.hasPv == False
        assert build_1001.bes.hasHeatpump == False

        assert build_1006.bes.hasBattery == True
        assert build_1006.bes.hasBoiler == True
        assert build_1006.bes.hasPv == True
        assert build_1006.bes.hasTes == True
        assert build_1006.bes.hasHeatpump == False
        assert build_1006.bes.hasChp == False

        assert build_1007.bes.hasBoiler == True
        assert build_1007.bes.hasChp == False
        assert build_1007.bes.hasTes == False
        assert build_1007.bes.hasPv == False
        assert build_1007.bes.hasHeatpump == False

        assert build_1008.bes.hasHeatpump == True
        assert build_1008.bes.hasElectricalHeater == True
        assert build_1008.bes.hasTes == True
        assert build_1008.bes.hasPv == True
        assert build_1008.bes.hasChp == False
        assert build_1008.bes.hasBoiler == False

        assert build_1012.bes.hasChp == True
        assert build_1012.bes.hasBoiler == True
        assert build_1012.bes.hasTes == True
        assert build_1012.bes.hasBattery == False
        assert build_1012.bes.hasPv == False
        assert build_1012.bes.hasHeatpump == False

    def test_city_gen_2(self, fixture_environment):

        this_path = os.path.dirname(os.path.abspath(__file__))

        th_gen_method = 2
        el_gen_method = 1
        do_normalization = True
        use_dhw = True
        dhw_method = 1
        dhw_volumen = 64
        eff_factor = 1
        filename = 'city_clust_simple.txt'
        filepath = os.path.join(this_path, 'input_generator', filename)

        timestep = fixture_environment.timer.timeDiscretization
        year = fixture_environment.timer.year
        location = fixture_environment.location
        altitude = fixture_environment.weather.altitude

        #  Load district_data file
        district_data = citygen.get_district_data_from_txt(filepath)

        city = citygen.run_city_generator(generation_mode=0,
                                          timestep=timestep,
                                          year_timer=year,
                                          year_co2=year,
                                          location=location,
                                          th_gen_method=th_gen_method,
                                          el_gen_method=el_gen_method,
                                          use_dhw=use_dhw,
                                          dhw_method=dhw_method,
                                          district_data=district_data,
                                          pickle_city_filename=None,
                                          eff_factor=eff_factor,
                                          show_city=False,
                                          try_path=None, altitude=altitude,
                                          dhw_volumen=dhw_volumen,
                                          do_normalization=do_normalization,
                                          do_save=False)

        assert city.get_nb_of_building_entities() == 12
        assert len(city.nodes()) == 12

        assert city.nodes[1004]['position'].x == 10
        assert city.nodes[1004]['position'].y == 70

        build_1 = city.nodes[1001]['entity']
        build_4 = city.nodes[1004]['entity']

        assert build_4._kind == 'building'
        assert build_4.get_number_of_apartments() == 1
        assert build_4.get_number_of_occupants() == 2
        assert build_4.get_annual_space_heat_demand() - 15000 < 0.001 * 15000
        assert build_4.get_annual_el_demand() - 1700 < 0.001 * 1700
        assert build_4.build_year == 1980
        assert build_4.mod_year == None
        assert build_4.net_floor_area == 100
        assert build_4.ground_area == None
        assert build_4.roof_usabl_pv_area == 30
        assert build_4.dormer == None

        assert build_1.get_annual_space_heat_demand() > 0

    def test_city_generator3(self, fixture_environment):

        this_path = os.path.dirname(os.path.abspath(__file__))

        th_gen_method = 3
        el_gen_method = 2
        do_normalization = True
        use_dhw = True
        dhw_method = 2
        dhw_volumen = None
        eff_factor = 0.85
        filename = 'city_1_building.txt'
        filepath = os.path.join(this_path, 'input_generator', filename)

        timestep = fixture_environment.timer.timeDiscretization
        year = fixture_environment.timer.year
        location = fixture_environment.location
        altitude = fixture_environment.weather.altitude

        #  Load district_data file
        district_data = citygen.get_district_data_from_txt(filepath)

        city = citygen.run_city_generator(generation_mode=0,
                                          timestep=timestep,
                                          year_timer=year,
                                          year_co2=year,
                                          location=location,
                                          th_gen_method=th_gen_method,
                                          el_gen_method=el_gen_method,
                                          use_dhw=use_dhw,
                                          dhw_method=dhw_method,
                                          district_data=district_data,
                                          pickle_city_filename=None,
                                          eff_factor=eff_factor,
                                          show_city=False,
                                          try_path=None, altitude=altitude,
                                          dhw_volumen=dhw_volumen,
                                          do_normalization=do_normalization,
                                          do_save=False,
                                          call_teaser=True)

    def test_city_gen_4(self, fixture_environment):

        this_path = os.path.dirname(os.path.abspath(__file__))

        th_gen_method = 2
        el_gen_method = 1
        do_normalization = True
        use_dhw = True
        dhw_method = 1
        dhw_volumen = 64
        eff_factor = 1
        filename = 'city_clust_mixed.txt'
        filepath = os.path.join(this_path, 'input_generator', filename)

        timestep = fixture_environment.timer.timeDiscretization
        year = fixture_environment.timer.year
        location = fixture_environment.location
        altitude = fixture_environment.weather.altitude

        #  Load district_data file
        district_data = citygen.get_district_data_from_txt(filepath)

        city = citygen.run_city_generator(generation_mode=0,
                                          timestep=timestep,
                                          year_timer=year,
                                          year_co2=year,
                                          location=location,
                                          th_gen_method=th_gen_method,
                                          el_gen_method=el_gen_method,
                                          use_dhw=use_dhw,
                                          dhw_method=dhw_method,
                                          district_data=district_data,
                                          pickle_city_filename=None,
                                          eff_factor=eff_factor,
                                          show_city=False,
                                          try_path=None, altitude=altitude,
                                          dhw_volumen=dhw_volumen,
                                          do_normalization=do_normalization,
                                          do_save=False)

    def test_convert_th_slp_int_and_str(self):

        assert citygen.convert_th_slp_int_and_str(0) == 'HEF'
        assert citygen.convert_th_slp_int_and_str(7) == 'GKO'

    def test_convert_el_slp_int_and_str(self):

        assert citygen.convert_el_slp_int_and_str(0) == 'H0'
        assert citygen.convert_el_slp_int_and_str(1) == 'G0'

    def test_convert_method_3_nb_into_str(self):

        assert citygen.convert_method_3_nb_into_str(1) == 'metal'

    def test_convert_method_4_nb_into_str(self):

        assert citygen.convert_method_4_nb_into_str(2) == 'warehouse'

    def test_conv_build_type_nb_to_name(self):

        assert citygen.conv_build_type_nb_to_name(0) == 'Residential'
        assert citygen.conv_build_type_nb_to_name(23) == 'Restaurant'

    def test_redistribute_occ(self):

        list_person_per_ap = [5, 6, 7, 1, 1, 2, 3, 2, 1, 0, 0]

        list_new = citygen.redistribute_occ(list_person_per_ap)

        assert max(list_new) <= 5
        assert min(list_new) >= 1

        list_person_per_ap = [5, 4, 3, 2, 1]

        list_new = citygen.redistribute_occ(list_person_per_ap)

        assert list_new == list_person_per_ap

    def test_gen_non_res(self, fixture_environment):

        citygen.generate_nonres_building_single_zone(environment=fixture_environment,
                                                     net_floor_area=500,
                                                     spec_th_demand=250,
                                                     annual_el_demand=40000,
                                                     th_slp_type='GGA',
                                                     el_slp_type='G0')

    def test_calc_el_dem_ap(self):

        nb_occ = 1
        el_random = True
        type = 'sfh'

        el_dem = citygen.calc_el_dem_ap(nb_occ=nb_occ, el_random=el_random,
                                        type=type)

        assert el_dem >= 0

        nb_occ = 2
        el_random = True
        type = 'mfh'

        el_dem = citygen.calc_el_dem_ap(nb_occ=nb_occ, el_random=el_random,
                                        type=type)

        assert el_dem >= 0

        nb_occ = 1
        el_random = False
        type = 'sfh'

        el_dem = citygen.calc_el_dem_ap(nb_occ=nb_occ, el_random=el_random,
                                        type=type)

        assert el_dem == 2500

        nb_occ = 2
        el_random = False
        type = 'mfh'

        el_dem = citygen.calc_el_dem_ap(nb_occ=nb_occ, el_random=el_random,
                                        type=type)

        assert el_dem == 2200

    def test_calc_dhw_dem_ap(self):

        nb_occ = 1
        dhw_random = True
        type = 'sfh'

        dhw_dem = citygen.calc_dhw_dem_ap(nb_occ, dhw_random, type, delta_t=35,
                                          c_p_water=4182,
                                          rho_water=995)

        assert dhw_dem >= 200 - 20
        assert dhw_dem <= 1000 + 20

        nb_occ = 3
        dhw_random = True
        type = 'mfh'

        dhw_dem = citygen.calc_dhw_dem_ap(nb_occ, dhw_random, type, delta_t=35,
                                          c_p_water=4182,
                                          rho_water=995)

        assert dhw_dem >= 900 - 20
        assert dhw_dem <= 1700 + 20

        nb_occ = 1
        dhw_random = False
        type = 'sfh'

        dhw_dem = citygen.calc_dhw_dem_ap(nb_occ, dhw_random, type, delta_t=35,
                                          c_p_water=4182,
                                          rho_water=995)

        assert dhw_dem == 500


        nb_occ = 3
        dhw_random = False
        type = 'mfh'

        dhw_dem = citygen.calc_dhw_dem_ap(nb_occ, dhw_random, type, delta_t=35,
                                          c_p_water=4182,
                                          rho_water=995)

        assert dhw_dem == 1300
