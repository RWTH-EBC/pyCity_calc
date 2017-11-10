"""
Tool for the dimensioning of heating devices and district heating networks in city districts, based on approaches
as being common in the industry.
Every dimensioned district complies with current legal requirements.

"""

import os
import pickle
import numpy as np
from copy import deepcopy

import matplotlib.pyplot as plt
import networkx as nx

import dim_devices

import pycity_base.classes.supply.BES as BES
import pycity_calc.energysystems.boiler as Boiler
import pycity_calc.energysystems.chp as CHP
import pycity_calc.energysystems.heatPumpSimple as HP
import pycity_calc.energysystems.electricalHeater as ElectricalHeater
import pycity_calc.energysystems.thermalEnergyStorage as TES

import pycity_base.classes.demand.SpaceHeating as SpaceHeating
import pycity_calc.toolbox.networks.network_ops as net_ops
import pycity_calc.toolbox.dimensioning.dim_networks as dimnet
import pycity_calc.visualization.city_visual as citvis

import pycity_calc.economic.energy_sys_cost.boiler_cost as boiler_cost
import pycity_calc.economic.energy_sys_cost.chp_cost as chp_cost
import pycity_calc.economic.energy_sys_cost.eh_cost as eh_cost
import pycity_calc.economic.energy_sys_cost.hp_cost as hp_cost
import pycity_calc.economic.energy_sys_cost.lhn_cost as lhn_cost
import pycity_calc.economic.energy_sys_cost.tes_cost as tes_cost

import pycity_calc.environments.co2emissions as co2


def run_approach(city,scenarios):
    """
    Main method to coordinate the planning process.

    Parameters
    ----------
    city:           standard city_object from pyCity_base
    scenarios:      list of dictionaries with common configurations of devices and suitability for (de)centralized usage
    building_con:   Connection building -> district heating network already installed
    heating_net:    district heating network already installed

    Returns
    -------
    solutions:      list of city_objects with installed building energy systems, depending on scenarios
    """
    #  Todo: Add explanations to docstring

    solutions = [] #Liste aller möglichen dimensionierten Szenarien (inklusive Kosten und Emissionen)


    # Check Eligibility for District Heating Network
    dhn_elig, district_type = get_eligibility_dhn(city, method=1)


    # Change SpaceHeatingDemand of apartments to method 1 (SLP)
    for n in city.nodelist_building:
        b = city.node[n]['entity']
        spec_th_dem = b.get_annual_space_heat_demand() / b.get_net_floor_area_of_building()
        for ap in b.apartments:
            if ap.demandSpaceheating.method != 1:
                ap.demandSpaceheating = SpaceHeating.SpaceHeating(city.environment,
                                                                  method=1,  # Standard load profile
                                                                  livingArea=ap.net_floor_area,
                                                                  specificDemand=spec_th_dem)

    # ------------------------------------ Dimensionierung der Anlagen -------------------------------------------------

    if dhn_elig > 4:
        print('District Heating eligible!')
        for scenario in scenarios:
            if 'centralized' in scenario['type']:
                print('')
                print(
                    '-' * 10 + ' Centralized ' + str(scenarios.index(scenario)) + ': ' + scenario['base'][0] + ' // ' +
                    scenario['peak'][0] + ' ' + '-' * 10)
                #print('\n---------- Scenario Centralized ' + str(scenarios.index(scenario)), '-----------')
                result = dim_centralized(deepcopy(city),scenario, district_type)
                solutions.append(result)


    elif dhn_elig < 2:
        print('District Heating not eligible!')
        for scenario in scenarios:
            if 'decentralized' in scenario['type']:
                print('')
                print('-' * 10 + ' Decentralized ' + str(scenarios.index(scenario)) + ': ' + scenario['base'][
                    0] + ' // ' + scenario['peak'][0] + ' ' + '-' * 10)
                #print('\n---------- Scenario Decentralized ' + str(scenarios.index(scenario)), '-----------')
                solutions.append(dim_decentralized(deepcopy(city),scenario))

    else:
        print('District Heating solutions might be eligible...')
        for scenario in scenarios:
            if 'centralized' in scenario['type']:
                print('')
                print(
                    '-' * 10 + ' Centralized ' + str(scenarios.index(scenario)) + ': ' + scenario['base'][0] + ' // ' +
                    scenario['peak'][0] + ' ' + '-' * 10)
                #print('\n---------- Scenario Centralized ' + str(scenarios.index(scenario)), '-----------')
                solutions.append(dim_centralized(deepcopy(city),scenario,district_type))
            if 'decentralized' in scenario['type']:
                print('')
                print('-' * 10 + ' Decentralized ' + str(scenarios.index(scenario)) + ': ' + scenario['base'][
                    0] + ' // ' + scenario['peak'][0] + ' ' + '-' * 10)
                #print('\n---------- Scenario Decentralized ' + str(scenarios.index(scenario)), '-----------')
                solutions.append(dim_decentralized(deepcopy(city),scenario))

    return solutions



def get_building_age(city):
    """
    Evaluates the age of a building in regards to the EEWärmeG. If one building in district is built in or after 2009,
    EEWärmeG must be complied by whole district.

    :param city: standard city_object
    :return: string 'new' or 'old'
    """
    for building_node in city.nodelist_building:
        if city.node[building_node]['entity'].build_year >= 2009: # EEWärmeG in place since 01.01.2009
            return 'new'
    return 'old'


def get_eligibility_dhn(city, method=1):
    '''
    Calculates the eligibility for using a district heating network (dhn)

    Parameters
    ----------
    city    :   city object
    method  :   int
        0 : Calculate Wärmeliniendichten (use only if spaceHeating in district was calculated with method 0)
        1 : Use Matrix from Wolff & Jagnow 2011

    Returns
    -------
    elig_val : int
        integer between 0 (bad) and 5 (good), which indicates the eligibility for lhn in district
    district_type : str
        describes type of district, defined by specific net length
    '''

    th_total_elig = city.get_annual_space_heating_demand() + city.get_annual_dhw_demand()  # in kWh/a

    b_graph = nx.Graph()
    for bn in city.nodelist_building:
        b_graph.add_node(bn, position=city.node[bn]['position'])
    min_st = net_ops.get_min_span_tree(b_graph, city.nodelist_building)

    net_len = net_ops.sum_up_weights_of_edges(min_st, network_type=None)  # in meter

    th_curve = ((city.get_aggr_dhw_power_curve(current_values=False) +
                 city.get_aggr_space_h_power_curve(current_values=False)) / 0.8) / 1000  # in kW

    # -------- Calculate Wärmeliniendichten ---------
    if method == 0:
        elig_val = 0

        # Wärmeleistungsliniendichte
        wlld = max(th_curve)/net_len    # in kW/m
        if wlld >= 1.5:
            elig_val += 2

        # Wärmeabnahmeliniendichte
        wald = th_total_elig/net_len     # in kWh/(m*a)
        if wald >= 1500:
            elig_val += 2

        return elig_val

    # -------- Get EKW ---------
    elif method == 1:

        area_total = 0
        edge_count = 0
        for n in city.nodelist_building:
            area_total += city.node[n]['entity'].get_net_floor_area_of_building()  # sum area of buildings
            if city.edge[n] != {}:
                edge_count += 1

        ekw = th_total_elig / area_total  # in kWh/(m2*a)

        # --------- Check for existing LHN and building connections -------

        if edge_count / len(city.nodelist_building) > 0.5:
            heating_net = True
            building_con = True
        else:
            heating_net = False
            building_con = False

        # Overwrite results from existing lhn check
        # heating_net = True
        # building_con = True

        # -------- Get district size -------

        num_apartments = 0
        for building_node in city.nodelist_building:
            num_apartments += len(city.node[building_node]['entity'].apartments)

        spec_len = net_len/num_apartments

        if spec_len < 6:
            district_type = 'big'
        elif spec_len < 14:
            district_type = 'medium'
        else:
            district_type = 'small'

        # --------- Get Energy demand factor ----------

        if district_type == 'big':
            if heating_net:
                if building_con:
                    if ekw > 120:
                        elig_val = 5
                    else:
                        elig_val = 4
                else:
                    if ekw > 120:
                        elig_val = 4
                    else:
                        elig_val = 3
            else:
                elig_val = 3

        elif district_type == 'medium':
            if heating_net:
                if building_con:
                    if ekw > 180:
                        elig_val = 5
                    elif ekw > 120:
                        elig_val = 4
                    else:
                        elig_val = 3
                else:
                    if ekw > 180:
                        elig_val = 4
                    elif ekw > 120:
                        elig_val = 3
                    else:
                        elig_val = 2
            else:
                if ekw > 180:
                    elig_val = 3
                elif ekw > 120:
                    elig_val = 2
                else:
                    elig_val = 1

        else:       # district_type == 'small':
            if heating_net:
                if building_con:
                    if ekw > 120:
                        elig_val = 4
                    elif ekw > 80:
                        elig_val = 3
                    else:
                        elig_val = 2
                else:
                    if ekw > 180:
                        elig_val = 3
                    elif ekw > 120:
                        elig_val = 2
                    else:
                        elig_val = 1
            else:
                if ekw > 120:
                    elig_val = 2
                else:
                    elig_val = 1

        return elig_val, district_type


def dim_centralized(city, scenario, district_type):
    '''
    Set sizes of devices in scenario
    :param scenario:
    :return: scenario with sizes of devices - in welcher form? city_object
    '''

    if district_type is 'big':    # Abschätzung aus Fraunhofer Umsicht - Leitfaden Nahwärme S.51
        eta_transmission = 0.93
    elif district_type is 'small':
        eta_transmission = 0.85
    else:
        eta_transmission = 0.9

    th_curve = (city.get_aggr_dhw_power_curve(current_values=False) +
                city.get_aggr_space_h_power_curve(current_values=False)) / eta_transmission

    th_LDC = dim_devices.get_LDC(th_curve)
    q_total = np.sum(th_curve)

    people_total = 0
    area_total = 0
    for b_node in city.nodelist_building:
        building = city.node[b_node]['entity']
        area_total += building.net_floor_area
        for ap in building.apartments:
            people_total += ap.occupancy.number_occupants

    bes = BES.BES(city.environment)

    # ------------- install local heating network -------------

    dimnet.add_lhn_to_city(city, city.nodelist_building, temp_vl=90,
                           temp_rl=50, c_p=4186, rho=1000,
                           use_street_network=False, network_type='heating',
                           plot_stepwise=False)
    net_ops.add_weights_to_edges(city)
    print("ready")
    '''
    citvis.plot_city_district(city=city, plot_street=False,
                              plot_lhn=True, offset=None,
                              plot_build_labels=True,
                              equal_axis=True, font_size=16,
                              plt_title=None,
                              x_label='x-Position in m',
                              y_label='y-Position in m',
                              show_plot=True)
    '''

    # ------------- dimensioning of devices --------------

    bafa_chp_tes = False
    bafa_lhn = False
    q_gas = []
    w_el = []

    # ---- CHP -----
    if 'chp' in scenario['base']:

        # select method (method=0 is standard)
        chp_sol = dim_devices.dim_central_chp(th_LDC, q_total, method=0)

        if chp_sol is None:
            raise Warning('CHP not suitable for lhn.')

        else:
            eta_el, eta_th, p_nom, q_nom, t_x, t_ann_op = chp_sol

            chp_ee_ratio = q_nom * t_ann_op / q_total

            if not check_eewaermeg(city, 'chp', chp_ee_ratio):
                raise Warning('Energysystem with CHP not according to EEWaermeG!')

            chp = CHP.ChpExtended(city.environment,q_nom,p_nom, eta_el + eta_th)
            bes.addDevice(chp)
            print('CHP: Q_nom = ' + str(q_nom / 1000) + ' kW (' + str(round(q_nom * 100 / max(th_curve), 2)) +
                  '% of Q_max, ' + str(np.round(q_nom * t_ann_op * 100 / q_total,2)) + '% of ann. production) ->', t_x, 'full-load hours.')

            q_gas.append((q_nom*t_ann_op/eta_th)/1000)   # gas demand for base supply in kWh/yr

            # Check if BAFA/KWKG subsidy for lhn is available
            if t_ann_op*q_nom/q_total > 0.75:
                bafa_lhn = True

            # Add TES
            v_tes = q_nom/1000*60   # BAFA-subsidy for mini-chp if tes_volume >= 60 l/kW_th
            if v_tes > 1600:        # 1600 liter are sufficient for BAFA-subsidy
                v_tes = 1600 + (q_nom/1000*60-1600)*0.2     # slow vol-increase over 1600 liter

            tes = TES.thermalEnergyStorageExtended(environment=city.environment,t_init=50,capacity=v_tes)
            bes.addDevice(tes)
            print('Added Thermal Energy Storage:', v_tes,'liter ')
            if q_nom * t_ann_op * 100 / q_total >= 50:
                bafa_chp_tes = True

            # Add peak supply
            if 'boiler' in scenario['peak']:
                q_boiler = (max(th_LDC) - q_nom) * 1.1  # 10% safety
                boiler = Boiler.BoilerExtended(city.environment, q_boiler, eta=0.85, t_max=0.90,
                                               lower_activation_limit=0.1)
                bes.addDevice(boiler)
                print('Added Boiler: Q_nom = '+str(round(q_boiler/1000,2))+' kW')

                q_gas.append(((q_total - q_nom * t_ann_op)/boiler.eta)/1000)    # gas demand for peak demand in kWh/yr

                check_enev(area_total)
                if q_boiler >= 4000 and q_boiler < 400000:
                    print('Boiler requires CE Label. (according to 92/42/EWG)')

            ann_q_base = t_ann_op*q_nom/1000 # Annual produced heat with base supply in kWh/yr
            ann_q_peak = (q_total - q_nom * t_ann_op)/1000 # Annual produced heat with peak supply in kWh/yr


    # ----- Boiler -----
    elif 'boiler' in scenario['base']:
        q_boiler = max(th_curve)
        boiler = Boiler.BoilerExtended(city.environment, q_boiler, eta=0.90,t_max=90, lower_activation_limit=0.2)
        bes.addDevice(boiler)
        print('Added Boiler: Q_nom = ' + str(round(q_boiler / 1000, 2)) + ' kW')
        check_enev(area_total)

        ann_q_base = q_total / 1000  # annual produced heat with base supply in kWh/yr
        ann_q_peak = 0
        q_gas = (q_total/boiler.eta) / 1000 # gas demand for supply in kWh/yr

    # ---- Add BES ----
    assert not city.node[city.nodelist_building[0]]['entity'].hasBes, 'Building 0 has already BES. Mistakes may occur!'
    city.node[city.nodelist_building[0]]['entity'].addEntity(bes)

    w_el.append(city.get_annual_el_demand()/1000) # electricity demand in kWh/yr

    #TODO: Anstatt q_base und q_peak die berechneten Gas und Stromverbräuche nehmen!!
    calc_costs(city,ann_q_base, ann_q_peak, w_total=w_el, bafa_lhn=bafa_lhn, bafa_chp_tes=bafa_chp_tes)
    calc_emissions(q_gas, w_el)

    return city


def dim_decentralized(city, scenario):
    '''
    Set sizes of devices in scenario
    :param scenario:
    :return: scenario with sizes of devices - in welcher form? city_object
    '''

    # TODO: EEWärmeG für dezentrale Fälle kontrollieren

    for b_node in city.nodelist_building:
        print('')
        print('-'*5 + ' Building ' + str(b_node) + ' ' + 5*'-')

        building = city.node[b_node]['entity']

        sh_curve = building.get_space_heating_power_curve()
        sh_total = np.sum(sh_curve)
        dhw_curve = building.get_dhw_power_curve()
        dhw_total = np.sum(dhw_curve)
        q_total = sh_total + dhw_total

        people_total = 0
        for ap in building.apartments:
            people_total += ap.occupancy.number_occupants

        bes = BES.BES(city.environment)

        bafa_chp_tes = False
        q_gas = []
        w_el = []

        for device in scenario['base']:
            if device == 'chp':

                th_LDC = dim_devices.get_LDC(sh_curve + dhw_curve)
                chp_sol = dim_devices.dim_decentral_chp(th_LDC, q_total, method=0)

                if chp_sol is None:
                    raise Warning('CHP not suitable for lhn.')

                eta_el, eta_th, p_nom, q_nom, t_x, t_ann_op = chp_sol

                chp = CHP.ChpExtended(city.environment, p_nom, q_nom, eta_el + eta_th)
                bes.addDevice(chp)
                print('CHP: Q_nom = ' + str(q_nom / 1000) + ' kW (' + str(round(q_nom * 100 / max(th_LDC), 2)) +
                      '% of Q_max) ->', t_x, 'full-load hours.')

                q_gas.append(((t_ann_op * q_nom)/eta_th) / 1000)    # gas demand for base supply in kWh/yr

                # Add TES
                v_tes = q_nom / 1000 * 60  # BAFA-subsidy for Mini-CHP if volume >= 60 l/kW_th
                if v_tes > 1600:  # 1600 liter sufficient for subsidy
                    v_tes = 1600 + (q_nom / 1000 * 60 - 1600) * 0.2  # increasing volume over 1600 liter
                tes = TES.thermalEnergyStorageExtended(environment=city.environment, t_init=50, capacity=v_tes)
                bes.addDevice(tes)
                print('Added Thermal Energy Storage:', v_tes, 'liter ')
                if q_nom * t_ann_op * 100 / q_total >= 50:
                    bafa_chp_tes = True

                # Add peak supply
                if 'boiler' in scenario['peak']:
                    q_boiler = (max(th_LDC) - q_nom)*1.5
                    boiler = Boiler.BoilerExtended(city.environment, q_boiler, eta=0.85, t_max=0.90,
                                                   lower_activation_limit=0.1)
                    bes.addDevice(boiler)
                    print('Added Boiler: Q_nom = ' + str(round(q_boiler / 1000, 2)) + ' kW')
                    q_gas.append(((q_total - q_nom * t_ann_op)/boiler.eta) / 1000)  # gas demand for peak supply in kWh/yr

                    if q_boiler >= 4000 and q_boiler < 400000:
                        print('Boiler requires CE Label. (according to 92/42/EWG)')
                    check_enev(building.net_floor_area)

                ann_q_base = t_ann_op * q_nom / 1000  # Annual produced heat with base supply in kWh
                ann_q_peak = (q_total - q_nom * t_ann_op) / 1000  # Annual produced heat with peak supply in kWh

            elif device == 'hp_air':

                if 'boiler' in scenario['peak']:
                    t_biv = 4
                else:
                    t_biv = -2

                # Add heat pump
                q_nom, cop_list, tMax, lowerActivationLimit, tSink, t_dem_ldc, biv_ind, hp_ee_ratio = \
                    dim_devices.dim_decentral_hp(city.environment, sh_curve, t_biv=t_biv)

                heatPump = HP.heatPumpSimple(city.environment,
                                             q_nominal=q_nom,
                                             t_max=tMax,
                                             lower_activation_limit=lowerActivationLimit,
                                             hp_type='aw',
                                             t_sink=tSink)
                bes.addDevice(heatPump)
                print('Added HP: Q_nom = ' + str(q_nom / 1000) + ' kW')

                # Calculate el. demand for heat pump
                w_el_hp = 0
                for t in range(len(sh_curve)):
                    w_el_hp += heatPump.calc_hp_el_power_input(sh_curve[t], city.environment.weather.tAmbient[t])
                w_el.append(w_el_hp/1000)   # el. power demand in kWh/yr

                # Calculate seasonal performance factor (SPF)
                spf = calc_hp_spf(heatPump=heatPump, environment=city.environment, sh_curve=sh_curve, cop=cop_list)
                print('SPF = ' + str(spf))

                if not check_eewaermeg(city,heatPump,hp_ee_ratio,spf=spf):
                    raise Warning('Energysystem not according to EEWaermeG!')

                if 'elHeater' in scenario['peak']:

                    # Dimensioning of elHeater
                    safety_factor = 2.2    # over dimensioning to guarantee simulation success
                    q_elHeater = (max(dhw_curve) + max(sh_curve) - q_nom)*safety_factor
                    if q_elHeater > 0:
                        elHeater = ElectricalHeater.ElectricalHeaterExtended(city.environment, q_elHeater, eta=0.95, t_max=95, lower_activation_limit=0.1)
                        bes.addDevice(elHeater)
                        print('Added elHeater: Q_nom = ' + str(round(q_elHeater / 1000, 2)) + ' kW')

                        # Calculate el. demand for elHeater (sh peak supply and dhw) in kWh/yr
                        w_el.append((((1-hp_ee_ratio)*np.sum(sh_curve) + np.sum(dhw_curve))/elHeater.eta)/1000)
                    else:
                        print('No elHeater installed.')
                '''
                elif 'boiler' in scenario['peak']:

                    # Dimensioning of Boiler - also covering hot water?

                    safety_factor = 1.2  # over dimensioning to guarantee simulation success
                    #q_boiler = (max(dhw_curve) + max(sh_curve) - q_nom) * safety_factor
                    q_boiler = (max(sh_curve) - q_nom) * safety_factor
                    if q_boiler > 0:
                        boiler = Boiler.BoilerExtended(city.environment, q_boiler, eta=0.85, t_max=0.90,lower_activation_limit=0.1)
                        bes.addDevice(boiler)
                        print('Added Boiler: Q_nom = ' + str(round(q_boiler / 1000, 2)) + ' kW')
                        check_enev(building.net_floor_area)
                        

                        # elHeater muss installiert werden zur TWW Deckung. Eigentlich sinnlos! Boiler kann das auch!!
                        q_elHeater = max(dhw_curve)
                        elHeater = ElectricalHeater.ElectricalHeaterExtended(city.environment,q_elHeater , eta=0.95, t_max=95, lower_activation_limit=0)
                        bes.addDevice(elHeater)
                        print('Added elHeater: Q_nom = ' + str(round(q_elHeater / 1000, 2)) + ' kW')
                    else:
                        print('No boiler installed.')
                '''

                # Add TES
                v_tes = 35*q_nom/1000   # in liter (DIN EN 15450: volume between 12 - 35 l/kW // VDI4645: 20 l/kW (for q_hp < 50 kW, monovalent))
                tes = TES.thermalEnergyStorageExtended(environment=city.environment, t_init=50,
                                                       capacity=v_tes)
                bes.addDevice(tes)
                print('Added Thermal Energy Storage:', round(v_tes,2), 'liter ')


                #Falsch TWW Bedarf dabei
                ann_q_base = hp_ee_ratio * sh_total / 1000  # in kWh
                ann_q_peak = q_total / 1000 - ann_q_base  # in kWh

            # TODO: Geothermie-WP
            elif device == 'hp_geo':

                q_nom, cop, tMax, lowerActivationLimit, tSink = \
                    dim_devices.dim_decentral_hp(city.environment, sh_curve, type='ww')

                heatPump = HP.heatPumpSimple(city.environment,
                                             q_nominal=q_nom,
                                             t_max=tMax,
                                             lower_activation_limit=lowerActivationLimit,
                                             hp_type='ww',
                                             t_sink=tSink)
                bes.addDevice(heatPump)
                print('Added S/W-HP: Q_nom = ' + str(q_nom / 1000) + ' kW')

                # Calculate el. demand for heat pump
                w_el_hp = 0
                for sh in sh_curve:
                    w_el_hp += heatPump.calc_hp_el_power_input(sh, city.environment.temp_ground)
                w_el.append(w_el_hp / 1000)  # el. power demand in kWh/yr

                # Calculate seasonal performance factor (SPF)
                spf = calc_hp_spf(heatPump=heatPump, environment=city.environment, sh_curve=sh_curve, cop=cop)
                print('SPF = ' + str(spf))

                ee_ratio = 1
                if not check_eewaermeg(city, heatPump, ee_ratio, spf=spf):
                    raise Warning('Energysystem not according to EEWaermeG!')

                ann_q_base = q_total / 1000  # in kWh
                ann_q_peak = 0  # in kWh

                if 'elHeater' in scenario['peak']:

                    # Add elHeater
                    q_elHeater = max(dhw_curve)
                    elHeater = ElectricalHeater.ElectricalHeaterExtended(city.environment, q_elHeater, eta=0.95,
                                                                         t_max=95, lower_activation_limit=0.1)
                    bes.addDevice(elHeater)
                    print('Added elHeater: Q_nom = ' + str(round(q_elHeater / 1000, 2)) + ' kW')

                    # Calculate el. demand for elHeater (only dhw supply) in kWh
                    w_el.append((dhw_total/elHeater.eta)/1000)

                v_tes = 20 * q_nom / 1000  # in liter (DIN EN 15450: volume between 12 - 35 l/kW // VDI4645: 20 l/kW (for q_hp < 50 kW, monovalent))
                tes = TES.thermalEnergyStorageExtended(environment=city.environment, t_init=50,
                                                       capacity=v_tes)
                bes.addDevice(tes)
                print('Added Thermal Energy Storage:', round(v_tes, 2), 'liter ')

            elif device == 'boiler':
                q_boiler = max(sh_curve+dhw_curve)
                boiler = Boiler.BoilerExtended(city.environment, q_boiler, eta=0.95, t_max=0.75, lower_activation_limit=0.2)
                bes.addDevice(boiler)
                print('Added Boiler: Q_nom = ' + str(round(q_boiler / 1000, 2)) + ' kW')

                q_gas = (q_total / boiler.eta) / 1000  # gas demand for supply in kWh/yr

                check_enev(building.net_floor_area)

                ann_q_base = q_total/1000
                ann_q_peak = 0

        w_el.append(city.get_annual_el_demand() / 1000)  # electricity demand in kWh/yr

        assert not city.node[b_node]['entity'].hasBes, ('Building ', b_node ,' has already BES. Mistakes may occur!')
        city.node[b_node]['entity'].addEntity(bes)

        calc_costs(city, ann_q_base, ann_q_peak, w_total=w_el, bafa_chp_tes=bafa_chp_tes)
        calc_emissions(q_gas, w_el)

    return city


def calc_hp_spf(heatPump, environment, sh_curve, cop=(2.9, 3.7, 4.4), method=0):
    '''
    Calculates seasonal performance factor (SPF = "Jahresarbeitszahl") for heat pump.
    Method 0 uses VDI 4650 to calculate SPF

    Method 1 uses regular calculation method
    If Space Heating curve is calculated with SLP, SPF is always = 4.56 (similar phenomenon as constant peak supply ratio per year)

    Parameters
    ----------
    heatPump : pyCity_calc heatPumpSimple class
    environment : environment class
    sh_curve : space heating curve
    cop : list of cops for heat pump [A-7/W35, A2/W35, A7/W35]
    method : choose method for calculation of spf

    Returns
    -------

    '''
    if heatPump.hp_type == 'aw':
        if method == 0:     # VDI 4650
            t_norm_outside = -12    # outside temperature for Aachen (DIN EN 12831)

            f_d_theta = 1.020   # temperature difference between test (5K) and operating conditions (7K)

            # Values for flow temperature = 35°C and norm_outside_temp = -12°C, taken from table 16 in VDI 4650
            f_theta1 = 0.058
            f_theta2 = 0.673
            f_theta3 = 0.208

            s_ab = 0.3  # correction for defrosting with reverse circulation ("Kreislaufumkehr")

            cop_n1 = cop[0]
            cop_n2 = cop[1] - s_ab
            cop_n3 = cop[2]

            hp_spf = f_d_theta/(f_theta1/cop_n1 + f_theta2/cop_n2 + f_theta3/cop_n3)


        elif method == 1:
            cop_array = np.zeros(8760)
            el_in_array = np.zeros(8760)
            q_out_array = np.zeros(8760)

            #  Get temperature array (source: outdoor air)
            array_temp = environment.weather.tAmbient

            for i in range(8760):
                curr_temp = array_temp[i]
                curr_q_dem = sh_curve[i]

                q_out_array[i] = heatPump.calc_hp_th_power_output(control_signal=curr_q_dem)
                cop_array[i] = heatPump.calc_hp_cop_with_quality_grade(temp_source=curr_temp)
                el_in_array[i] = heatPump.calc_hp_el_power_input(control_signal=q_out_array[i], t_source=curr_temp)

            hp_spf = np.round(np.sum(q_out_array) / np.sum(el_in_array),2)

        else:
            raise Warning('Unknown method!')

        return hp_spf

    elif heatPump.hp_type == 'ww':

        # method VDI4650 for t_ground = 0°C as recommended
        f_d_theta = 1.020  # temperature difference between test (5K) and operating conditions (7K)
        t_ground = 0

        f_theta_dict = {-3:1.26, -2:1.142, -1:1.159, 0:1.177, 1:1.95, 2:1.214, 3:1.234, 4:1.253, 5:1.273}
        f_theta = f_theta_dict[t_ground]
        f_P = 1.075 # correction factor for pump

        spf = cop[0] * f_d_theta * f_theta / f_P

        return spf

    else:
        raise Warning('Wrong heatPump type!')


def check_enev(area_total):
    '''
    Check if commissioning of boiler is according to EnEV.
    It is presumed that only condensing boilers are used (outside of thermal envelope; temperatures 70/55)
    "Energieaufwandszahl" (e_g) taken from table C.3-4b of DIN V 4701-10:2003-08

    Parameters
    ----------
    area_total : float
        Total area of building
    '''
    # e_g for boiler nach DIN V 4701-10, Tabelle C.3-4b, ff.
    eg_boiler = {100: 1.08, 150: 1.07, 200: 1.07, 300: 1.06, 500: 1.05, 750: 1.05, 1000: 1.05, 1500: 1.04,
                          2500: 1.04, 5000: 1.03, 10000: 1.03}

    for a in eg_boiler.keys():
        if a >= area_total:
            eg = eg_boiler[a]
            break
    else:
        eg = eg_boiler[10000]

    if eg * 1.1 < 1.3:
        print('Commissioning of condensing boiler according to EnEV (e_g * f_p < 1.3)')
    else:
        raise Warning('Commissioning of condensing boiler not according to EnEV!!')


def check_eewaermeg(city, device, ee_ratio, spf=None):

    if get_building_age(city) == 'new':
        print('EEWaermeG is obligatory!')

        # ----------- CHP -----------
        if device.kind == 'chp':
            p_nom = device.pNominal
            eta_el = device.omega*device.sigma
            eta_th = device.omega-eta_el

            if ee_ratio >= 0.5:
                # calculate primary energy
                refeta_th = 0.92  # th. reference efficiency rate for devices younger than 2016 (natural gas)
                refeta_el = 0.5355  # el. reference efficiency rate for devices younger than 2016 (natural gas)

                # Primary energy savings in % calculated according to EU directive 2012/27/EU
                pee = (1 - 1 / ((eta_th / refeta_th) + (eta_el / refeta_el))) * 100
                if p_nom >= 1000000:
                    if pee >= 10:
                        print('Device (>=1MW) is highly efficient -> EEWaermeG satisfied')
                        return True
                else:
                    if pee > 0:
                        print('Device (<1MW) is highly efficient -> EEWaermeG satisfied')
                        return True
            return False

        # -------------- HP --------------
        elif device.kind == 'hp':
            if device.hp_type == 'aw':
                if spf < 3.5:
                    print('SPF too low: ' + str(spf))
                    return False
            elif device.hp_type == 'ww':
                if spf < 4:
                    print('SPF too low: ' + str(spf))
                    return False

            if ee_ratio >= 0.5:
                return True

    else:
        print('EEWaermeG is not obligatory due to building age.')
        return True

# -------------------------------- Economic Calculations ----------------------------------------------------
# TODO: CO2 Überschlägige Berechnung reinbringen

def calc_emissions(q_gas, w_el):
    """

    Parameters
    ----------
    q_gas : list : total amount of gas used during one year in kWh/yr
    w_el : list : total amount of electricity from the grid used during one year in kWh/yr
    emf_gas : float : emission factor for gas
    emf_el : float : emission factor for electricity from grid

    Returns
    -------

    """
    emf_el = co2.Emissions.get_co2_emission_factors(type='el_mix')  # kg/kWh
    emf_gas = co2.Emissions.get_co2_emission_factors(type='gas')    # kg/kWh

    co2_gas = q_gas * emf_gas
    co2_el = w_el * emf_el
    co2_total = co2_el + co2_gas

    print('Total Emissions: ' + str(round(co2_total,2)) + ' kg CO2 / year')


def calc_costs(city, q_base, q_peak, w_total, i=0.08, price_gas=0.0661, price_el_hp=0.25, el_feedin_epex=0.02978, bafa_lhn=False, bafa_chp_tes=False):
    """
    - Kosten
        - Kapitalgebundene Kosten (Investitionskosten über Annuitätenfaktor in jährliche Zahlung umrechnen)
        - Bedarfsgebundene Kosten (Brennstoffkosten, Stromkosten)
        - Betriebsgebundene Kosten
        - sonstige Kosten und Erlöse (Förderungen, )

        - KWK Vergünstigungen
        - Einspeisevergütung durch EEG
        - Strom- und Brennstoffkosten
        - Investitionskosten
        - sonstige Förderungen (Recherche!)

    Parameters
    ----------
    city:           pyCity city-object
    q_base:         amount of thermal energy provided by base supply in kWh
    q_peak:         amount of thermal energy provided by peak supply in kWh
    i:              interest rate
    price_gas:      price of gas EUR/kWh
    price_el_hp:    price of electricity for heatpump in EUR/kWh
    el_feedin_epex: average price for baseload power at EPEX Spot for Q2 2017 in Euro/kWh
    bafa_lhn:       indicates if BAFA funding for lhn is applicable
    bafa_chp_tes:   indicates if BAFA funding for TES with CHP is applicable

    Returns
    -------
    costs:          tuple of total capital and total operational costs in Euro
    """

    # Kostenfunktion in Wolff 2011, Kapitel 6.3.6
    # Betriebs- und Energiekosten in Kapitel 6.3.7
    # Bewertungskriterien, Masterarbeit Hendrik Kapitel 2.3!

    # [maintenance in %, service in %, service hours in h]
    insp_vdi2067 = {'boiler':[0.01,0.02,20],'chp':[0.06,0.02,100],'hp':[0.01,0.015,5]}
    service_fee = 40    # service fee in Euro/h

    for bn in city.nodelist_building:
        if city.node[bn]['entity'].hasBes:
            bes = city.node[bn]['entity'].bes

            cost_invest = []    # invest costs
            cost_cap = []       # capital costs
            cost_op = []        # operational costs
            cost_insp = []      # inspection, maintenance and service costs (VDI 2067)
            rev = []            # revenue for electricity feed-in and kwkg

            if bes.hasHeatpump:
                t = 20  # nach VDI 2067
                q_hp_nom = bes.heatpump.qNominal/1000   # in kW

                if bes.heatpump.hp_type == 'aw':

                    spf = calc_hp_spf(bes.heatpump, city.environment, city.node[bn]['entity'].get_space_heating_power_curve())

                    hp_invest = hp_cost.calc_spec_cost_hp(q_hp_nom, method='wolf', hp_type='aw') * q_hp_nom
                    a = i * (1 + i) ** t / ((1 + i) ** t - 1)

                    cost_invest.append(hp_invest)
                    cost_cap.append(hp_invest * a)
                    cost_op.append(q_base / spf * price_el_hp)
                    cost_insp.append(hp_invest * (sum(insp_vdi2067['hp'][0:2])) + insp_vdi2067['hp'][2] * service_fee)

                elif bes.heatpump.hp_type == 'ww':
                    spf = calc_hp_spf(bes.heatpump, city.environment,
                                      city.node[bn]['entity'].get_space_heating_power_curve(), cop=4.8)

                    hp_invest = hp_cost.calc_spec_cost_hp(q_hp_nom, method='wolf', hp_type='ww') * q_hp_nom
                    a = i * (1 + i) ** t / ((1 + i) ** t - 1)

                    cost_invest.append(hp_invest)
                    cost_cap.append(hp_invest * a)
                    cost_op.append(q_base / spf * price_el_hp)
                    cost_insp.append(hp_invest * (sum(insp_vdi2067['hp'][0:2])) + insp_vdi2067['hp'][2] * service_fee)

                if bes.hasBoiler:
                    t = 20  # nach VDI 2067
                    q_boi_nom = bes.boiler.qNominal/1000    # in kW

                    boiler_invest = boiler_cost.calc_spec_cost_boiler(q_boi_nom, method='viess2013') * q_boi_nom
                    a = i * (1 + i) ** t / ((1 + i) ** t - 1)

                    cost_invest.append(boiler_invest)
                    cost_cap.append(boiler_invest * a)
                    cost_op.append(q_peak / bes.boiler.eta * price_gas)
                    cost_insp.append(
                        boiler_invest * (sum(insp_vdi2067['boiler'][0:2])) + insp_vdi2067['boiler'][2] * service_fee)
    
                elif bes.hasElectricalHeater:
                    t = 20 # nach VDI 2067
                    q_elHeater_nom = bes.electricalHeater.qNominal/1000 # in kW

                    elHeater_invest = eh_cost.calc_spec_cost_eh(q_elHeater_nom, method='spieker') * q_elHeater_nom
                    a = i * (1 + i) ** t / ((1 + i) ** t - 1)

                    cost_invest.append(elHeater_invest)
                    cost_cap.append(elHeater_invest * a)
                    cost_op.append(q_peak / bes.electricalHeater.eta * price_el_hp)

            elif bes.hasChp:
                t = 15  # nach VDI 2067
                p_chp_nom = bes.chp.pNominal/1000   # in kW
                q_chp_nom = bes.chp.qNominal/1000   # in kW
                eta_th = bes.chp.omega / (1 + bes.chp.sigma)

                a = i * (1 + i) ** t / ((1 + i) ** t - 1)
                chp_invest = chp_cost.calc_spec_cost_chp(p_chp_nom, method='asue2015', with_inst=True,
                       use_el_input=True, q_th_nom=None) * p_chp_nom    # in Euro

                print('Investcost CHP', round(chp_invest,2), 'Euro')

                if bes.hasTes:
                    v_tes = bes.tes.capacity*1000/bes.tes.rho   # in liter
                    bafa_subs_chp = dim_devices.get_subs_minichp(p_chp_nom, q_chp_nom, v_tes) # in Euro
                else:
                    bafa_subs_chp = 0

                el_feedin_chp = dim_devices.get_el_feedin_tariff_chp(p_chp_nom,el_feedin_epex)

                cost_invest.append(chp_invest - bafa_subs_chp)
                cost_cap.append((chp_invest - bafa_subs_chp)*a)
                cost_op.append(q_base/eta_th*price_gas)
                cost_insp.append(chp_invest *(sum(insp_vdi2067['chp'][0:2]))+insp_vdi2067['chp'][2]*service_fee)
                rev.append(q_base*bes.chp.sigma*el_feedin_chp)

                if bes.hasBoiler:
                    t = 20  # nach VDI 2067
                    q_boi_nom = bes.boiler.qNominal/1000

                    boiler_invest = boiler_cost.calc_spec_cost_boiler(q_boi_nom, method='viess2013') * q_boi_nom
                    a = i * (1 + i) ** t / ((1 + i) ** t - 1)

                    cost_invest.append(boiler_invest)
                    cost_cap.append(boiler_invest * a)
                    cost_op.append(q_peak/bes.boiler.eta*price_gas)
                    cost_insp.append(boiler_invest * (sum(insp_vdi2067['boiler'][0:2])) + insp_vdi2067['boiler'][2] * service_fee)

            elif bes.hasBoiler:
                t = 20  # nach VDI 2067
                q_boi_nom = bes.boiler.qNominal / 1000

                boiler_invest = boiler_cost.calc_spec_cost_boiler(q_boi_nom, method='viess2013') * q_boi_nom
                a = i * (1 + i) ** t / ((1 + i) ** t - 1)

                cost_invest.append(boiler_invest)
                cost_cap.append(boiler_invest * a)
                cost_op.append(q_base / bes.boiler.eta * price_gas)
                cost_insp.append(
                    boiler_invest * (sum(insp_vdi2067['boiler'][0:2])) + insp_vdi2067['boiler'][2] * service_fee)

            if bes.hasTes:
                t = 20 # nach VDI 2067
                volume = bes.tes.capacity/bes.tes.rho # in m3
                tes_invest = tes_cost.calc_invest_cost_tes(volume, method='spieker')
                a = i * (1 + i) ** t / ((1 + i) ** t - 1)

                # BAFA subsidy for TES according to KWKG
                if bafa_chp_tes:
                    bafa_subs_tes = volume*100
                    print('BAFA subsidy for TES possible:', bafa_subs_tes, ' Euro')
                else:
                    bafa_subs_tes = 0
                cost_invest.append(tes_invest-bafa_subs_tes)
                cost_cap.append((tes_invest-bafa_subs_tes)*a)
            break
    else:
        raise Exception('No BES installed!')

    for v in city.edge.values():
        if bool(v):
            # Only if edge exists
            # TODO: Kosten für Hausanschluss?! Bisher Kosten aus pyCity_calc Tabelle (Economic,LHN)
            cost_pipes_dm = {0.0161:284,0.0217:284.25,0.0273:284.50,0.0372:284.75,0.0431:285,0.0545:301,0.0703:324.5,0.0825:348.5,0.1071:397,0.1325:443,0.1603:485}
            lhn_length = round(net_ops.sum_up_weights_of_edges(city),2)

            for d in city.edge[city.nodelist_building[0]].values(): # gibts eine bessere Möglichkeit um an 'd_i' zu kommen?
                pipe_dm = d['d_i']
                break
            else:
                raise Exception('No pipe diameter found!')

            for dm in cost_pipes_dm.keys():
                if pipe_dm < dm:
                    t = 40  # approx. (source: nahwaerme.at)
                    a_pipes = i * (1 + i) ** t / ((1 + i) ** t - 1)
                    pipes_invest = cost_pipes_dm[dm]*lhn_length
                    print('Pipe costs:', pipes_invest)
                    cost_invest.append(pipes_invest)
                    cost_cap.append(pipes_invest*a_pipes)
                    break
            else:
                raise Exception('Pipe diameter too big!')

            if bafa_lhn:
                if dm <= 0.1:
                    lhn_subs_pre = 100 * lhn_length  # 100 Euro/m if dn <= 100
                    if lhn_subs_pre > 0.4 * sum(cost_invest):  # subsidy must not be higher than 40% of total invest
                        lhn_subs = 0.4 * sum(cost_invest)
                    else:
                        lhn_subs = lhn_subs_pre
                else:
                    lhn_subs = 0.3 * sum(cost_invest)   # 30% of invest if dn > 100
                if lhn_subs > 20000000: # max. subsidy is 20.000.000
                    lhn_subs = 20000000
                lhn_subs_fee = 0.002 * lhn_subs # fee is 0.2% of subsidy
                if lhn_subs_fee < 100:  # min. fee is 100 Euro
                    lhn_subs_fee = 100
                lhn_subs = lhn_subs - lhn_subs_fee
                cost_invest.append(-lhn_subs)
                cost_cap.append(-lhn_subs*a_pipes)
                print('BAFA LHN subsidy applies: ' + str(lhn_subs) + 'Euro off of total invest')
            break

    cost_cap_total = round(sum(cost_cap),2)
    cost_op_total = round(sum(cost_op),2)
    cost_insp_total = round(sum(cost_insp),2)
    rev_total = round(sum(rev),2)

    q_total = q_base + q_peak   # in kWh

    print('Capital Cost:', cost_cap_total)
    print('Operational Cost:', cost_op_total)
    print('Costs for inspection, maintenance and service:', cost_insp_total)
    print('Revenue for el feed-in:', rev_total)
    print('\n** Costs per year:', cost_cap_total+cost_op_total+cost_insp_total-rev_total, 'Euro/a **')
    print('** Heat production costs: '+ str((cost_cap_total+cost_op_total+cost_insp_total-rev_total)/q_total) +' EUR/kWh **')

    return (cost_cap_total, cost_op_total)



if __name__ == '__main__':

    scenarios = []

    #scenarios.append({'type': ['centralized'], 'base': ['chp'], 'peak': ['boiler']})
    #scenarios.append({'type': ['centralized'], 'base': ['boiler'], 'peak': ['']})

    #scenarios.append({'type': ['decentralized'], 'base': ['boiler'], 'peak': ['']})
    #scenarios.append({'type': ['decentralized'], 'base': ['hp_air'], 'peak': ['boiler']})
    #scenarios.append({'type': ['decentralized'], 'base': ['hp_air'], 'peak': ['elHeater']})
    #scenarios.append({'type': ['decentralized'], 'base': ['chp'], 'peak': ['boiler']})


    scenarios.append({'type': ['decentralized'], 'base': ['hp_geo'], 'peak': ['']})
    # scenarios.append({'type': ['centralized', 'decentralized'], 'base': ['hp_geo'], 'peak': ['elHeater']})

    #Choose example city_object
    ex_city = 1

    this_path = os.path.dirname(os.path.abspath(__file__))
    #  Run program

    city_f_name = 'aachen_kronenberg_3_mfh_ref_1.pkl'

    #city_f_name = 'ex_city_4mfh_3zfh.pkl'
    # city_f_name = 'ex_city_7_geb_mixed.pkl'
    #city_f_name = 'ex_city_7_geb_mixed_setDem.pkl'
    #city_f_name = 'example_2_buildings.pkl'
    city_path = os.path.join(this_path, 'input', 'city_objects', city_f_name)
    city = pickle.load(open(city_path, mode='rb'))

    print('District ' + city_f_name[:-4] + ' loaded')
    list_city_object = run_approach(city,scenarios)


    # ---- Output in pickle files -----
    '''
    import pycity_calc.visualization.city_visual as citvis

    for i in range(len(list_city_object)):
        cit = list_city_object[i]
        #city_name = 'output_(' + str(i+1) + ')_' + city_f_name
        city_name = 'output_(5)_' + city_f_name
        #city_name = 'output_test_boiler_2_' + city_f_name
        path_output = os.path.join(this_path, 'output', city_name)
        pickle.dump(cit, open(path_output, mode='wb'))
        citvis.plot_city_district(city=cit, plot_lhn=True, plot_deg=True,
                                  plot_esys=True)
    '''
