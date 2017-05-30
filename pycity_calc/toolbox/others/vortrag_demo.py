#!/usr/bin/env python
# coding=utf-8
"""
It is time for a Freitagsvortrags-Demo :-)
"""

import os
import pickle
import copy
import warnings
import numpy as np
import matplotlib.pyplot as plt

import pycity_calc.visualization.city_visual as citvis
import pycity_calc.toolbox.networks.network_ops as netop
import pycity_calc.toolbox.teaser_usage.teaser_use as teasuse
import pycity_calc.toolbox.dimensioning.dim_networks as dimnet
import pycity.functions.changeResolution as chres

import pycity_opt.demand_cluster_tool as ddtool
import pycity_opt.ESOpt as esopt
import pycity_opt.examples.example_run_ddc_and_opt_with_city_object as optex
import pycity_calc.toolbox.analyze.analyze_city_pickle_file as anpi
import pycity_calc.cities.scripts.street_generator.street_generator as strgen


def run_demo():
    """
    Execute demo
    """

    warnings.filterwarnings("ignore")

    print('pyCity Demonstration')
    print('####################################################')
    print()

    this_path = os.path.dirname(os.path.abspath(__file__))

    filename = 'city.p'

    load_path = os.path.join(this_path, 'demo', filename)

    print('Let us generate a city object instance, first.')
    print('####################################################')
    print()
    city = pickle.load(open(load_path, mode='rb'))

    citvis.plot_city_district(city=city, plot_build_labels=True,
                              equal_axis=True)


    print('Show example for occupancy dependent el. load and hot water profiles')
    print('####################################################')
    print()

    # import pycity.classes.demand.ElectricalDemand as eldem
    # import pycity.classes.Timer as time
    # import pycity.classes.Weather as weath
    # import pycity.classes.Environment as env
    # import pycity.classes.Prices as price
    # import pycity.classes.demand.Occupancy as occ
    #
    # timer = time.Timer(timeDiscretization=900)
    # weather = weath.Weather(timer)  # , useTRY=True)
    # prices = price.Prices()
    #
    # environment = env.Environment(timer, weather, prices)
    # occupancy_obj = occ.Occupancy(environment=environment, number_occupants=3)
    #
    # el_obj = eldem.ElectricalDemand(environment,
    #                                 method=2,
    #                                 total_nb_occupants=3,
    #                                 randomizeAppliances=True,
    #                                 occupancy=occupancy_obj.occupancy)
    #
    # import pycity.classes.demand.DomesticHotWater as DomesticHotWater
    #
    # dhw_obj = \
    #     DomesticHotWater.DomesticHotWater(environment,
    #                                       tFlow=60,
    #                                       thermal=True,
    #                                       method=2,
    #                                       supplyTemperature=20,
    #                                       occupancy=occupancy_obj.occupancy)
    #
    #
    #
    # save_path = os.path.join(this_path, 'demo', 'profiles.p')
    #
    # pickle.dump((occupancy_obj, el_obj, dhw_obj), open(save_path, mode='wb'))


    profile_path = os.path.join(this_path, 'demo', 'profiles.p')

    (occupancy_obj, el_obj, dhw_obj) = \
        pickle.load(open(profile_path, mode='rb'))

    occ_tr = 365 * 24 * 3600 / len(occupancy_obj.occupancy)
    el_tr = 365 * 24 * 3600 / len(el_obj.loadcurve)
    dhw_tr = 365 * 24 * 3600 / len(dhw_obj.loadcurve)

    occupancy_obj.occupancy = \
        chres.changeResolution(occupancy_obj.occupancy,
                               oldResolution=occ_tr, newResolution=600)
    el_obj.loadcurve = \
        chres.changeResolution(el_obj.loadcurve,
                               oldResolution=el_tr, newResolution=600)
    dhw_obj.loadcurve = \
        chres.changeResolution(dhw_obj.loadcurve,
                               oldResolution=dhw_tr, newResolution=600)

    time_array = np.arange(0, 365 * 24 * 3600, 600)/3600

    fig = plt.figure()
    fig.add_subplot(311)
    plt.plot(time_array[1008:1440], occupancy_obj.occupancy[1008:1440],
             label='Occupancy',
             color='#E53027')
    plt.ylabel('Occupancy')

    fig.add_subplot(312)
    plt.plot(time_array[1008:1440], el_obj.loadcurve[1008:1440] / 1000,
             label='El. power',
             color='#E53027')
    plt.ylabel('El. load\n in kW')

    fig.add_subplot(313)
    plt.plot(time_array[1008:1440], dhw_obj.loadcurve[1008:1440] / 1000,
             label='Hot water',
             color='#E53027')
    plt.ylabel('Hot water\n load in kW')
    plt.xlabel('Time in hours')
    plt.show()
    plt.close()

    print()


    # #  Add streets (only required, once)
    # path_nodes = os.path.join(this_path, 'demo', 'street_nodes_puetzhof.csv')
    # path_edges = os.path.join(this_path, 'demo', 'street_edges_puetzhof.csv')
    #
    # name_list, pos_list, edge_list = \
    #     strgen.load_street_data_from_csv(path_str_nodes=path_nodes,
    #                                      path_str_edges=path_edges)
    #
    # strgen.add_street_network_to_city(city_object=city, name_list=name_list,
    #                                   pos_list=pos_list, edge_list=edge_list)
    #
    # save_path = os.path.join(this_path, 'demo', 'pycity_puetzhof_kfw_str.p')
    #
    # pickle.dump(city, open(save_path, mode='wb'))
    #
    # input()

    print('Give me some information about the city district:')
    print('####################################################')

    nb_buildings = 0
    for n in city.nodelist_building:
        if 'entity' in city.node[n]:
            if city.node[n]['entity']._kind == 'building':
                nb_buildings += 1

    print('Number of buildings: ', nb_buildings)
    print()

    ann_space_heat = round(city.get_annual_space_heating_demand(), 2)
    ann_el_dem = round(city.get_annual_el_demand(), 2)
    ann_dhw_dem = round(city.get_annual_dhw_demand(), 2)

    print('Annual net thermal space heating demand in kWh: ')
    print(ann_space_heat)
    print()

    print('Annual electrical demand in kWh: ')
    print(ann_el_dem)
    print()

    print('Annual hot water energy demand in kWh: ')
    print(ann_dhw_dem)
    print()

    print('Percentage of space heat demand on total thermal demand in %:')
    print((100 * ann_space_heat) / (ann_space_heat + ann_dhw_dem))
    print('Percentage of hot water demand on total thermal demand in %:')
    print((100 * ann_dhw_dem) / (ann_space_heat + ann_dhw_dem))

    sh_power_curve = city.get_aggr_space_h_power_curve()
    el_power_curve = city.get_aggr_el_power_curve()
    dhw_power_curve = city.get_aggr_dhw_power_curve()

    timestep = city.environment.timer.timeDiscretization

    time_array = np.arange(0, 365 * 24 * 3600 / timestep, timestep / 3600)

    plt.plot(time_array, sh_power_curve/1000, label='Space heat',
             color='#E53027')
    plt.plot(time_array, el_power_curve/1000, label='El. power',
             color='#1058B0')
    plt.plot(time_array, dhw_power_curve/1000, label='Hot water',
             color='#F47328')
    plt.xlabel('Time in hours')
    plt.ylabel('Power in kW')
    plt.legend()
    plt.show()
    plt.close()

    print()

    # fig = plt.figure()
    # fig.add_subplot(311)
    # plt.plot(time_array, sh_power_curve / 1000, label='Space heat',
    #          color='#E53027')
    # plt.ylabel('Space heat\npower in kW')
    #
    # fig.add_subplot(312)
    # plt.plot(time_array, el_power_curve / 1000, label='El. power',
    #          color='#E53027')
    # plt.ylabel('El. power\nin kW')
    #
    # fig.add_subplot(313)
    # plt.plot(time_array, dhw_power_curve / 1000, label='Hot water',
    #          color='#E53027')
    # plt.ylabel('Hot water power\nin kW')
    #
    # plt.xlabel('Time in hours')
    # plt.ylabel('Power in kW')
    # plt.show()
    # plt.close()



    print('Give me some information about building 1001:')
    print('####################################################')

    b_1140 = city.node[1001]['entity']

    print('Type of building: ')
    if b_1140.build_type == 0:
        print('Residential building')
    print('Estimated net floor area in m2: ', b_1140.net_floor_area)
    print('Number of floors: ', int(b_1140.nb_of_floors))
    print('Number of apartments: ', int(b_1140.get_number_of_apartments()))
    print('Number of occupants: ', int(b_1140.get_number_of_occupants()))
    print()

    input()

    # print('Now, call TEASER VDI 6007 core and simulate thermal demand:')
    # print('####################################################')
    # print()

    #  TODO: Substitute with TEASER tpyebuilding call via node
    #  TODO: Or simulate with EnEV 2014 standard and compare with
    #  current thermal load


    # (temp_in, q_heat_cool, q_in_wall, q_out_wall) = \
    #     teasuse.calc_th_load_build_vdi6007_ex_build(exbuild=b_1140)
    #
    # #  #  Results
    # #  #####################################################################
    #
    # q_heat = np.zeros(len(q_heat_cool))
    # q_cool = np.zeros(len(q_heat_cool))
    # for i in range(len(q_heat_cool)):
    #     if q_heat_cool[i] > 0:
    #         q_heat[i] = q_heat_cool[i]
    #     elif q_heat_cool[i] < 0:
    #         q_cool[i] = q_heat_cool[i]
    #
    # print('Sum of net heating energy demand in kWh:')
    # print(sum(q_heat) / 1000)
    #
    # ebc_red = '#E53027'
    #
    # fig = plt.figure()
    # fig.add_subplot(311)
    # plt.plot(city.environment.weather.tAmbient, color=ebc_red)
    # plt.ylabel('Outdoor air\ntemperature in\ndegree Celsius')
    # fig.add_subplot(312)
    # plt.plot(temp_in, color=ebc_red)
    # plt.ylabel('Indoor air\ntemperature in\ndegree Celsius')
    # fig.add_subplot(313)
    # plt.plot(q_heat_cool / 1000, color=ebc_red)
    # plt.ylabel('Heating/cooling\npower (+/-)\nin kW')
    # plt.xlabel('Time in hours')
    # plt.show()
    # plt.close()

    city_copy = copy.deepcopy(city)

    print('Add local heating network to city. ')
    print('####################################################')
    dimnet.add_lhn_to_city(city=city_copy,
                           list_build_node_nb=city_copy.nodelist_building,
                           use_street_network=True)

    citvis.plot_city_district(city=city_copy, plot_build_labels=True,
                            offset=7, plot_lhn=True)


    build_list = [1001, 1002]
    print('Let us extract 2 buildings: ' + str(build_list))
    print('####################################################')
    print()

    #  Extract subcity
    subcity = netop.get_build_str_subgraph(city=city, nodelist=build_list)

    citvis.plot_city_district(city=subcity, plot_build_labels=True,
                              plot_str_dist=200, offset=7)

    print('Finally, perform energy system placement optimization:')
    print('####################################################')

    dem_profiles = optex.run_dem_day_clustering(city_object=subcity)
    #  Begin of user input
    #  #----------------------------------------------------------------------
    #  #----------------------------------------------------------------------

    ref_sys = False  # True : Reference energy system,
    # False : Optimized enery system
    with_mst = True  # True : minimum spanning tree,
    # False : unlimited heat network
    use_streetnetwork = True  # True : streetnetwork with nodes,
    # False : shortest direction

    with_LHN = True  # with LHN, if True (not allowed in reference system)
    with_BAT = False  # with Battery, if True (not allowed in reference system)
    with_PV = False  # with PV, if True (not allowed in reference system)
    with_BW_HP = False  # with HP, if True (not allowed in reference system)
    with_AW_HP = False  # with HP, if True (not allowed in reference system)
    with_CHP = True  # with CHP, if True (not allowed in reference system)
    with_BOI = True  # with Boiler, if True
    with_STO = True  # with Storage, if True

    with_DEG = 0  # 0: no decentralized electrical grid, 1: decentralized electrical grid possible,
    # 2: decentralized electrical grid fixed with mst (not allowed in reference system)

    CHP_start_limit = False  # True: CHP switch on once a day
    Grid_Constraint = False  # True: Apply Grid constraints
    v3 = 1  # Choose objective function: CO2-em. -> v3=0,
    # total annual costs -> v3=1
    v4 = 0  # consider costs for pump energy -> v4=1, do not consider -> v4=0

    #  epsilon-Constraints (used for pareto-optimal solution)
    #  Cost constraint (max. total cost per year in €/a
    epsilon_Cost = None  # not active for epsilon == None
    #  CO2 constraint (max. total co2 emission per year in kg CO2 eq / a
    epsilon_CO2 = 70000  # not active for epsilon == None
    #  Maximum share of exported electrical energy in percent
    epsilon_grid = None  # not active for epsilon == None
    #  Limits amount of exported electrical energy
    #  Maximum residual energy in kWh
    epsilon_ce = None  #not active for epsilon == None

    #  Gurobi solver parameters
    Opt_GAP = 0.05
    Opt_Heuristics = None
    Opt_Focus = None
    Opt_Cut = None
    Opt_Threads = None
    Opt_Nodefile = None
    opt_nodefiledir = None
    opt_timelimit = 3600

    #  Static or dynamic CO2 factors?
    static_co2 = False

    #  Path and name of callback file
    callback_name = 'callback_ESOpt.log'
    callback_path = os.path.join(this_path, callback_name)

    #  Run optimization
    (esopt_res, result, indices) = esopt.run_e_sys_opt_with_pycity(
        city_object=subcity,
        ref_sys=ref_sys,
        with_mst=with_mst,
        use_streetnetwork=
        use_streetnetwork,
        with_LHN=with_LHN,
        with_BAT=with_BAT,
        with_PV=with_PV,
        with_BW_HP=with_BW_HP,
        with_AW_HP=with_AW_HP,
        with_CHP=with_CHP,
        with_BOI=with_BOI, with_STO=with_STO,
        with_DEG=with_DEG,
        CHP_start_limit=CHP_start_limit,
        Grid_Constraint=Grid_Constraint,
        v3=v3,
        v4=v4, epsilon_Cost=epsilon_Cost,
        epsilon_CO2=epsilon_CO2,
        epsilon_grid=epsilon_grid,
        dem_profiles=dem_profiles,
        esopt_object=None,
        Opt_GAP=Opt_GAP,
        Opt_Heuristics=Opt_Heuristics,
        Opt_Focus=Opt_Focus,
        Opt_Cut=Opt_Cut,
        Opt_Threads=Opt_Threads,
        Opt_Nodefile=Opt_Nodefile,
        opt_nodefiledir=opt_nodefiledir,
        opt_timelimit=opt_timelimit,
        callback_path=callback_path,
        allow_standalone_EH=True,
        static_co2=static_co2)

    citvis.plot_city_district(city=esopt_res, #city_list=[city, esopt_res],
                              plot_lhn=True,
                              plot_esys=True, offset=7, plot_str_dist=200)

if __name__ == '__main__':

    run_demo()