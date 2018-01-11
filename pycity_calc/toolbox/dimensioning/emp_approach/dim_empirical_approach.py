"""
Tool for the dimensioning of heating devices and district heating networks in city districts, based on approaches
as being common in the industry.
Every dimensioned district complies with current legal requirements.

"""

import os
import pickle
import numpy as np
from copy import deepcopy
import networkx as nx

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
import pycity_calc.toolbox.dimensioning.emp_approach.dim_devices as dim_devices



def run_approach(city,scenarios):
    """
    Main method to coordinate planning process

    Parameters
    ----------
    city:           standard city_object from pyCity_base
    scenarios:      list of dictionaries with common configurations of devices and suitability for (de)centralized usage

    Returns
    -------
    solutions:      list of city_objects with installed building energy systems, depending on scenarios
    """

    solutions = []

    # Change SpaceHeatingDemand of apartments to method 1 (SLP)
    slp_city = deepcopy(city)

    for n in slp_city.nodelist_building:
        b = slp_city.node[n]['entity']
        spec_th_dem = b.get_annual_space_heat_demand() / b.get_net_floor_area_of_building()

        for ap in b.apartments:
            if ap.demandSpaceheating.method != 1:
                ap.demandSpaceheating = SpaceHeating.SpaceHeating(environment=city.environment,
                                                                  method=1,  # Standard load profile
                                                                  livingArea=ap.net_floor_area,
                                                                  specificDemand=spec_th_dem)

    # --------------------------- Dimensioning of devices -----------------------------

    # Check Eligibility for District Heating Network
    dhn_elig, district_type = get_eligibility_dhn(city, method=1)

    if dhn_elig > 4:
        # District Heating eligible (not necessary to plan decentralized supply systems)

        for scenario in scenarios:

            if 'centralized' in scenario['type']:
                print('')
                print('-' * 10 + ' Centralized ' + str(scenarios.index(scenario)) + ': '
                      + scenario['base'][0] + ' // ' + scenario['peak'][0] + ' ' + '-' * 10)

                solutions.append(dim_centralized(city=deepcopy(city),
                                                 slp_city=slp_city,
                                                 scenario=scenario,
                                                 district_type=district_type))

    elif dhn_elig < 2:
        # District Heating not eligible (Decentralized supply system should be implemented)

        for scenario in scenarios:
            if 'decentralized' in scenario['type']:
                print('')
                print('-' * 10 + ' Decentralized ' + str(scenarios.index(scenario)) + ': '
                      + scenario['base'][0] + ' // ' + scenario['peak'][0] + ' ' + '-' * 10)

                solutions.append(dim_decentralized(city=deepcopy(city),
                                                   slp_city=slp_city,
                                                   scenario=scenario))

    else:
        # District Heating solutions might be eligible - check decentralized and centralized scenarios

        for scenario in scenarios:
            if 'centralized' in scenario['type']:
                print('')
                print('-' * 10 + ' Centralized ' + str(scenarios.index(scenario)) + ': '
                      + scenario['base'][0] + ' // ' + scenario['peak'][0] + ' ' + '-' * 10)

                solutions.append(dim_centralized(city=deepcopy(city),
                                                 slp_city=slp_city,
                                                 scenario=scenario,
                                                 district_type=district_type))

            if 'decentralized' in scenario['type']:
                print('')
                print('-' * 10 + ' Decentralized ' + str(scenarios.index(scenario)) + ': '
                      + scenario['base'][0] + ' // ' + scenario['peak'][0] + ' ' + '-' * 10)

                solutions.append(dim_decentralized(city=deepcopy(city),
                                                   slp_city=slp_city,
                                                   scenario=scenario))

    return solutions


def get_building_age(city):
    """
    Evaluates the age of a building in regards to the EEWärmeG. If one building in district is built in or after 2009,
    EEWärmeG must be complied by whole district.

    Parameters
    ----------
    city:      pyCity_Calc city object

    Returns
    -------
    building_age:   'old' or 'new' (string)
    """

    for building_node in city.nodelist_building:

        # check year of renovation and construction
        mod = city.node[building_node]['entity'].mod_year
        built = city.node[building_node]['entity'].build_year

        if mod is not None:
            if mod >= 2009:
                return 'new'

        elif built >= 2009:
            return 'new'

    return 'old'


def get_net_len(city):
    """
    Return length of heating network

    Parameters
    ----------
    city:   pyCity_Calc city object

    Returns
    -------
    net_len:    float
    """

    b_graph = nx.Graph()

    for bn in city.nodelist_building:
        b_graph.add_node(bn, position=city.node[bn]['position'])

    # get minimum spanning tree
    min_st = net_ops.get_min_span_tree(graph=b_graph, node_id_list=city.nodelist_building)

    # get total net length
    net_len = net_ops.sum_up_weights_of_edges(graph=min_st, network_type=None)  # in meter

    return net_len


def get_district_type(city, net_len=None):
    """
    Calculate type of city according to Fraunhofer UMSICHT - Leitfaden Nahwaerme (Tabelle 4.1)

    Parameters
    ----------
    city : pyCity_Calc city object
    net_len : length of heating network

    Returns
    -------
    district_type : string
        'big'
        'medium'
        'small'
    """

    # get total net length
    if net_len is None:
        net_len = get_net_len(city)

    num_apartments = 0

    # get total number of apartments
    for building_node in city.nodelist_building:
        num_apartments += len(city.node[building_node]['entity'].apartments)

    # calculate specific length
    spec_len = net_len / num_apartments

    # define district type by specific length
    if spec_len < 6:
        district_type = 'big'

    elif spec_len < 14:
        district_type = 'medium'

    else:
        district_type = 'small'

    return district_type


def get_eligibility_dhn(city, method=1):
    """
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
    """

    # calculate sum of total space heating and domestic hot water demand per year
    th_total_elig = city.get_annual_space_heating_demand() + city.get_annual_dhw_demand()  # in kWh/a

    # get total net length
    net_len = get_net_len(city)  # in meter

    # get combined thermal demand curve (sh and dhw)
    th_curve = ((city.get_aggr_dhw_power_curve(current_values=False) +
                 city.get_aggr_space_h_power_curve(current_values=False)) / 0.8) / 1000  # in kW

    # -------- Calculate "Wärmeliniendichten" ---------
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

            # Calculate aggregated floor area of all buildings
            area_total += city.node[n]['entity'].get_net_floor_area_of_building()  # sum area of buildings

            # Check if lhn already existent
            if city.edge[n] != {}:
                edge_count += 1

        # Calculate energy coefficient ("Energiekennwert")
        ekw = th_total_elig / area_total  # in kWh/(m2*a)

        # --------- Check for existing LHN and building connections -------

        if edge_count / len(city.nodelist_building) > 0.5:
            heating_net = True
            building_con = True

        else:
            heating_net = False
            building_con = False

        # --------- Get Energy demand factor ----------

        # get district type
        district_type = get_district_type(city, net_len)

        # Calculate eligibility from Matrix of Wolff & Jagnow 2011
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


def get_eta_transmission(district_type):
    """
    Returns efficency of lhn based on Fraunhofer Umsicht: Leitfaden Nahwärme (p.51)

    Parameters
    ----------
    district_type : string
        type of district (big, medium, small)

    Returns
    -------
    eta_transmission : float
        efficiency factor for transmission
    """

    if district_type is 'big':
        eta_transmission = 0.93

    elif district_type is 'small':
        eta_transmission = 0.85

    else:   # medium
        eta_transmission = 0.9

    return eta_transmission


def dim_centralized(city, slp_city, scenario, district_type):
    """
    Set sizes of devices in centralized supply system

    Parameters
    ----------
    city : pyCity_Calc city object
    slp_city : city_object with SLP for space heating demand
    scenario : dictionary with common configuration of devices and suitability for centralized usage
    district_type : string
        'big', 'medium', 'small'

    Returns
    -------
    city: city object
        city object including energysystem - BES only in first building
    """

    # get transmission efficiency
    eta_transmission = get_eta_transmission(district_type)

    # calculate combined th. demand curve (SLP type)
    th_curve_slp = (slp_city.get_aggr_dhw_power_curve(current_values=False) +
                    slp_city.get_aggr_space_h_power_curve(current_values=False)) / eta_transmission

    # calculate combined th. demand curve (standard)
    th_curve_orig = (city.get_aggr_dhw_power_curve(current_values=False) +
                     city.get_aggr_space_h_power_curve(current_values=False)) / eta_transmission

    # get load demand curve and total demand for SLP
    th_LDC_slp = dim_devices.get_LDC(th_curve_slp)
    q_total_slp = sum(th_curve_slp)

    # get load demand curve and total demand for standard curve
    th_LDC_orig = dim_devices.get_LDC(th_curve_orig)
    q_total_orig = sum(th_curve_orig)

    people_total = 0
    area_total = 0

    # Calculate total area and total number of inhabitants
    for b_node in city.nodelist_building:

        building = city.node[b_node]['entity']
        area_total += building.net_floor_area

        for ap in building.apartments:
            people_total += ap.occupancy.number_occupants

    bes = BES.BES(city.environment)

    # ------------- install local heating network -------------

    dimnet.add_lhn_to_city(city=city,
                           list_build_node_nb=city.nodelist_building,
                           temp_vl=90,
                           temp_rl=50,
                           c_p=4186,
                           rho=1000,
                           use_street_network=False,
                           network_type='heating',
                           plot_stepwise=False)

    net_ops.add_weights_to_edges(city)

    # ------------- dimensioning of devices --------------

    bafa_chp_tes = False
    bafa_lhn = False
    q_gas = []
    w_el = []
    chp_el_prod = 0

    # ---- CHP -----
    if 'chp' in scenario['base']:

        # Calculate size of CHP
        chp_sol = dim_devices.dim_central_chp(th_LDC=th_LDC_slp,
                                              q_total=q_total_slp,
                                              method=0)

        if chp_sol is None:
            raise Warning('CHP not suitable for lhn.')

        # Extract CHP data
        eta_el, eta_th, p_nom, q_nom, t_x, t_ann_op = chp_sol

        # Calculate estimated ratio of annual CHP heat
        chp_ee_ratio = q_nom * t_ann_op / q_total_slp

        # Add CHP
        chp = CHP.ChpExtended(environment=city.environment,
                              q_nominal=q_nom,
                              p_nominal=p_nom,
                              eta_total=eta_el + eta_th)
        bes.addDevice(chp)

        print('CHP: Q_nom = ' + str(q_nom / 1000) + ' kW (' + str(round(q_nom * 100 / max(th_curve_slp), 2)) +
              '% of Q_max, ' + str(np.round(q_nom * t_ann_op * 100 / q_total_slp,2)) + '% of ann. production) ->',
              t_x, 'full-load hours.')

        # Check if CHP is according to EEWärmeG
        if not check_eewaermeg(city=city,
                               device=chp,
                               ee_ratio=chp_ee_ratio):
            raise Warning('Energysystem with CHP not according to EEWaermeG!')

        # Calculate gas demand for chp in kWh/yr
        q_gas.append((q_nom * t_ann_op / eta_th) / 1000)

        # Calculate produced electricity in kWh/yr
        chp_el_prod = q_nom*t_ann_op / eta_th * eta_el / 1000

        # Check if BAFA/KWKG subsidy for lhn is available
        if t_ann_op * q_nom / q_total_slp > 0.75:
            bafa_lhn = True

        # Calculate TES volume
        v_tes = q_nom/1000*60   # BAFA-subsidy for mini-chp if tes_volume >= 60 l/kW_th

        if v_tes > 1600:        # 1600 liter are sufficient for BAFA-subsidy
            v_tes = 1600 + (q_nom/1000*60-1600)*0.3     # slow vol-increase over 1600 liter

        # Add TES
        tes = TES.thermalEnergyStorageExtended(environment=city.environment,
                                               t_init=50,        # TODO: tInit stellt sich automtisch wieder auf 68°C
                                               capacity=v_tes)
        bes.addDevice(tes)

        print('Added Thermal Energy Storage:', v_tes, 'liter ')

        # Check if KWKG subsidy for TES in combination with CHP is applicable
        if q_nom * t_ann_op * 100 / q_total_slp >= 50:
            bafa_chp_tes = True

        # Add Boiler for peak supply
        if 'boiler' in scenario['peak']:

            # Calculate th.power for boiler
            q_boiler = (max(th_LDC_orig) - q_nom)

            # Add Boiler
            boiler = Boiler.BoilerExtended(environment=city.environment,
                                           q_nominal=q_boiler,
                                           eta=0.95,
                                           t_max=85,
                                           lower_activation_limit=0)
            bes.addDevice(boiler)

            print('Added Boiler: Q_nom = '+str(round(q_boiler/1000, 2))+' kW')

            # Calculate gas demand for boiler in kWh/yr
            q_gas.append(((q_total_slp - q_nom * t_ann_op)/boiler.eta)/1000)

            # Check if Boiler according to EnEV
            check_enev(area_total)

            if 4000 <= q_boiler < 400000:
                print('Boiler requires CE Label. (according to 92/42/EWG)')

    # ----- Boiler as baseload supply -----

    elif 'boiler' in scenario['base']:

        q_boiler = max(th_curve_orig)

        # Add Boiler
        boiler = Boiler.BoilerExtended(environment=city.environment,
                                       q_nominal=q_boiler,
                                       eta=0.95,
                                       t_max=85,
                                       lower_activation_limit=0)
        bes.addDevice(boiler)

        print('Added Boiler: Q_nom = ' + str(round(q_boiler / 1000, 2)) + ' kW')

        # Check EnEV
        check_enev(area_total)

        # Check if CHP is according to EEWärmeG
        if not check_eewaermeg(city=city,
                               device=boiler,
                               ee_ratio=0):
            raise Warning('Energy system with only Boiler not according to EEWaermeG!')


        # Calculate gas demand for boiler in kWh/yr
        q_gas.append((q_total_orig/boiler.eta) / 1000) # gas demand for supply in kWh/yr

    # Add BES
    assert not city.node[city.nodelist_building[0]]['entity'].hasBes, 'Building 0 has already BES. Mistakes may occur!'
    city.node[city.nodelist_building[0]]['entity'].addEntity(bes)

    # Get total electricity demand in kWh/yr
    w_el.append(city.get_annual_el_demand()/1000)

    # Calculate costs and emissions
    calc_costs(city=city,
               q_gas=q_gas,
               w_el_in=w_el,
               w_el_out=chp_el_prod,
               bafa_lhn=bafa_lhn,
               bafa_chp_tes=bafa_chp_tes)

    calc_emissions(q_gas, w_el)

    return city


def dim_decentralized(city, slp_city, scenario):
    """
    Set sizes of devices in decentralized supply system

    Parameters
    ----------
    city : pyCity_Calc city object
    slp_city : city_object with SLP for space heating demand
    scenario : dictionary with common configuration of devices and suitability for decentralized usage

    Returns
    -------

    """

    for b_node in city.nodelist_building:
        print('')
        print('-'*5 + ' Building ' + str(b_node) + ' ' + 5*'-')

        building = city.node[b_node]['entity']
        building_slp = slp_city.node[b_node]['entity']

        # Get power curves
        sh_curve_slp = building_slp.get_space_heating_power_curve()
        sh_total_slp = np.sum(sh_curve_slp)
        dhw_curve_slp = building_slp.get_dhw_power_curve()
        dhw_total_slp = np.sum(dhw_curve_slp)
        q_total_slp = sh_total_slp + dhw_total_slp

        sh_curve_orig = building.get_space_heating_power_curve()
        sh_total_orig = np.sum(sh_curve_orig)
        dhw_curve_orig = building.get_dhw_power_curve()
        dhw_total_orig = np.sum(dhw_curve_orig)
        th_curve_orig = building.get_space_heating_power_curve() + building.get_dhw_power_curve()
        q_total_orig = np.sum(th_curve_orig)

        # Calculate total number of inhabitants
        people_total = 0
        for ap in building.apartments:
            people_total += ap.occupancy.number_occupants

        bes = BES.BES(city.environment)

        bafa_chp_tes = False
        q_gas = []
        w_el = []
        chp_el_prod = 0

        for device in scenario['base']:

            # --------------- CHP ---------------
            if device == 'chp':

                # get load demand curve
                th_LDC_slp = dim_devices.get_LDC(sh_curve_slp + dhw_curve_slp)

                # get most suitable CHP
                chp_sol = dim_devices.dim_decentral_chp(th_LDC_slp, q_total_slp, method=0)

                if chp_sol is None:
                    raise Warning('CHP not suitable for lhn.')

                # extract CHP data
                eta_el, eta_th, p_nom, q_nom, t_x, t_ann_op = chp_sol

                # Calculate estimated ratio of annual CHP heat
                chp_ee_ratio = q_nom * t_ann_op / q_total_slp

                # Add CHP
                chp = CHP.ChpExtended(city.environment,
                                      p_nominal=p_nom,
                                      q_nominal=q_nom,
                                      eta_total=eta_el + eta_th)
                bes.addDevice(chp)

                print('CHP: Q_nom = ' + str(q_nom / 1000) + ' kW (' + str(round(q_nom * 100 / max(th_LDC_slp), 2)) +
                      '% of Q_max) ->', t_x, 'full-load hours.')

                # Check if CHP is according to EEWärmeG
                if not check_eewaermeg(city=city,
                                       device=chp,
                                       ee_ratio=chp_ee_ratio):
                    raise Warning('Energysystem with CHP not according to EEWaermeG!')

                # Calculate gas demand for chp in kWh/yr
                q_gas.append(((t_ann_op * q_nom)/eta_th) / 1000)

                # Calculate produced electricity in kWh/yr
                chp_el_prod = q_nom * t_ann_op / eta_th * eta_el / 1000

                # Calculate TES volume
                v_tes = q_nom / 1000 * 60  # BAFA-subsidy for Mini-CHP if volume >= 60 l/kW_th

                if v_tes > 1600:  # 1600 liter sufficient for subsidy
                    v_tes = 1600 + (q_nom / 1000 * 60 - 1600) * 0.3  # increasing volume over 1600 liter

                # Add TES
                tes = TES.thermalEnergyStorageExtended(environment=city.environment,
                                                       t_init=68,
                                                       capacity=v_tes)
                bes.addDevice(tes)

                print('Added Thermal Energy Storage:', v_tes, 'liter ')

                # Check if bafa subsidy for mini-chp applies
                if q_nom * t_ann_op * 100 / q_total_slp >= 50:
                    bafa_chp_tes = True

                # Add Boiler as peak supply
                if 'boiler' in scenario['peak']:

                    # Calculate th.power of boiler
                    q_boiler = (max(th_curve_orig) - q_nom)

                    # Add boiler
                    boiler = Boiler.BoilerExtended(city.environment,
                                                   q_nominal=q_boiler,
                                                   eta=0.95,
                                                   t_max=85,
                                                   lower_activation_limit=0)
                    bes.addDevice(boiler)

                    print('Added Boiler: Q_nom = ' + str(round(q_boiler / 1000, 2)) + ' kW')

                    # Calculate gas demand for peak supply in kWh/yr
                    q_gas.append(((q_total_slp - q_nom * t_ann_op)/boiler.eta) / 1000)

                    # Check if Boiler according to EnEV
                    if 4000 <= q_boiler < 400000:
                        print('Boiler requires CE Label. (according to 92/42/EWG)')
                    check_enev(building.net_floor_area)

            # --------------- Air/Water Heat Pump ---------------

            elif device == 'hp_air':

                # Set bivalence point depending on peak supply
                if 'boiler' in scenario['peak']:
                    t_biv = 4
                else:
                    t_biv = -2

                # Calculate most suitable heat pump
                q_nom, cop_list, tMax, lowerActivationLimit, tSink, t_dem_ldc, biv_ind, hp_ee_ratio = \
                    dim_devices.dim_decentral_hp(city.environment, sh_curve_orig, t_biv=t_biv)

                # Add heat pump
                heatPump = HP.heatPumpSimple(environment=city.environment,
                                             q_nominal=q_nom,
                                             t_max=tMax,
                                             lower_activation_limit=lowerActivationLimit,
                                             hp_type='aw',
                                             t_sink=tSink)
                bes.addDevice(heatPump)

                print('Added HP: Q_nom = ' + str(q_nom / 1000) + ' kW')

                # Calculate el. demand for heat pump
                w_el_hp = 0

                for t in range(len(sh_curve_orig)):
                    w_el_hp += heatPump.calc_hp_el_power_input(sh_curve_orig[t], city.environment.weather.tAmbient[t])

                w_el.append(w_el_hp/1000)   # el. power demand in kWh/yr

                # Calculate seasonal performance factor (SPF)
                spf = calc_hp_spf(heatPump=heatPump,
                                  environment=city.environment,
                                  sh_curve=sh_curve_orig,
                                  cop=cop_list)

                # Check if energysystem with heat pump is according to EEWärmeG
                if not check_eewaermeg(city=city,
                                       device=heatPump,
                                       ee_ratio=hp_ee_ratio,
                                       spf=spf):
                    raise Warning('Energysystem not according to EEWaermeG!')

                # Add peak supply
                if 'elHeater' in scenario['peak']:

                    # Calculate elHeater
                    safety_factor = 1.5    # over dimensioning to guarantee simulation success
                    q_elHeater = (max(dhw_curve_orig) + max(sh_curve_orig) - q_nom)*safety_factor

                    if q_elHeater > 0:

                        # Add elHeater
                        elHeater = ElectricalHeater.ElectricalHeaterExtended(environment=city.environment,
                                                                             q_nominal=q_elHeater,
                                                                             eta=1,
                                                                             t_max=85,
                                                                             lower_activation_limit=0)
                        bes.addDevice(elHeater)
                        print('Added elHeater: Q_nom = ' + str(round(q_elHeater / 1000, 2)) + ' kW')

                        # Calculate el. demand for elHeater (sh peak supply and dhw) in kWh/yr
                        w_el.append((((1-hp_ee_ratio)*np.sum(sh_curve_orig) + np.sum(dhw_curve_orig))/elHeater.eta)/1000)

                    else:
                        print('No elHeater installed.')

                elif 'boiler' in scenario['peak']:

                    # Dimensioning of Boiler - may also be covering hot water
                    safety_factor = 1.2  # over dimensioning to guarantee simulation success

                    # hot water with boiler
                    #q_boiler = (max(dhw_curve) + max(sh_curve) - q_nom) * safety_factor

                    # hot water with elHeater
                    q_boiler = (max(sh_curve_orig) - q_nom) * safety_factor
                    q_elHeater = max(dhw_curve_orig)

                    if q_boiler > 0:
                        # Add Boiler
                        boiler = Boiler.BoilerExtended(environment=city.environment,
                                                       q_nominal=q_boiler,
                                                       eta=0.95,
                                                       t_max=85,
                                                       lower_activation_limit=0)
                        bes.addDevice(boiler)

                        print('Added Boiler: Q_nom = ' + str(round(q_boiler / 1000, 2)) + ' kW')

                        check_enev(building.net_floor_area)

                    if q_elHeater > 0:
                        # Add elHeater for dhw supply
                        elHeater = ElectricalHeater.ElectricalHeaterExtended(environment=city.environment,
                                                                             q_nominal=q_elHeater,
                                                                             eta=1,
                                                                             t_max=85,
                                                                             lower_activation_limit=0)
                        bes.addDevice(elHeater)

                        print('Added elHeater: Q_nom = ' + str(round(q_elHeater / 1000, 2)) + ' kW')

                # Add TES
                # DIN EN 15450: volume between 12 - 35 l/kW
                # VDI4645: 20 l/kW (for q_hp < 50 kW, monovalent)
                v_tes = 35*q_nom/1000   # in liter

                tes = TES.thermalEnergyStorageExtended(environment=city.environment,
                                                       t_init=68,
                                                       capacity=v_tes)

                bes.addDevice(tes)

                print('Added Thermal Energy Storage:', round(v_tes,2), 'liter ')

            # --------------- Brine/Water Heat Pump ---------------

            elif device == 'hp_geo':
                evu_block = 4

                # Add heat pump
                q_nom, cop, tMax, lowerActivationLimit, tSink = \
                    dim_devices.dim_decentral_hp(environment=city.environment,
                                                 sh_curve=sh_curve_orig,
                                                 hp_type='ww',
                                                 t_blocked=evu_block)

                heatPump = HP.heatPumpSimple(environment=city.environment,
                                             q_nominal=q_nom,
                                             t_max=tMax,
                                             lower_activation_limit=lowerActivationLimit,
                                             hp_type='ww',
                                             t_sink=tSink)
                bes.addDevice(heatPump)

                print('Added S/W-HP: Q_nom = ' + str(q_nom / 1000) + ' kW')

                # Calculate el. demand for heat pump
                w_el_hp = 0
                for sh in sh_curve_orig:
                    w_el_hp += heatPump.calc_hp_el_power_input(sh, city.environment.temp_ground)
                w_el.append(w_el_hp / 1000)  # el. power demand in kWh/yr

                # Calculate seasonal performance factor (SPF)
                spf = calc_hp_spf(heatPump=heatPump,
                                  environment=city.environment,
                                  sh_curve=sh_curve_orig,
                                  cop=cop)

                # Check if according to EEWärmeG
                ee_ratio = 1
                if not check_eewaermeg(city=city,
                                       device=heatPump,
                                       ee_ratio=ee_ratio,
                                       spf=spf):
                    raise Warning('Energysystem not according to EEWaermeG!')

                # Add elHeater (DHW supply)
                q_elHeater = max(dhw_curve_orig)
                elHeater = ElectricalHeater.ElectricalHeaterExtended(environment=city.environment,
                                                                     q_nominal=q_elHeater,
                                                                     eta=1,
                                                                     t_max=85,
                                                                     lower_activation_limit=0)

                bes.addDevice(elHeater)
                print('Added elHeater: Q_nom = ' + str(round(q_elHeater / 1000, 2)) + ' kW')

                # Calculate el. demand for elHeater (only dhw supply) in kWh
                w_el.append((dhw_total_orig/elHeater.eta)/1000)

                # Add TES
                # DIN EN 15450: volume between 12 - 35 l/kW
                # VDI4645:  l/kW (for q_hp < 50 kW, monovalent)
                v_tes = 40 * (evu_block + q_nom / 1000)  # in liter

                tes = TES.thermalEnergyStorageExtended(environment=city.environment,
                                                       t_max=90,
                                                       t_init=55,
                                                       capacity=v_tes)

                bes.addDevice(tes)
                print('Added Thermal Energy Storage:', round(v_tes, 2), 'liter ')

            # --------------- Boiler ---------------

            elif device == 'boiler':

                # Add Boiler
                q_boiler = max(sh_curve_orig+dhw_curve_orig)
                boiler = Boiler.BoilerExtended(environment=city.environment,
                                               q_nominal=q_boiler,
                                               eta=0.95,
                                               t_max=85,
                                               lower_activation_limit=0)

                bes.addDevice(boiler)
                print('Added Boiler: Q_nom = ' + str(round(q_boiler / 1000, 2)) + ' kW')

                # Calculate gas demand for boiler
                q_gas.append((q_total_orig / boiler.eta) / 1000)  # gas demand for supply in kWh/yr

                # Check if Boiler according to EnEV
                check_enev(building.net_floor_area)

                # Check if CHP is according to EEWärmeG
                if not check_eewaermeg(city=city,
                                       device=boiler,
                                       ee_ratio=0):
                    raise Warning('Energysystem with CHP not according to EEWaermeG!')

        # --------------- Add BES ---------------
        assert not city.node[b_node]['entity'].hasBes, ('Building ', b_node, ' has already BES. Mistakes may occur!')
        city.node[b_node]['entity'].addEntity(bes)

        # Get total electricity demand in kWh/yr
        w_el.append(city.get_annual_el_demand() / 1000)

        # Calculate costs and emissions
        calc_costs(city=city,
                   q_gas=q_gas,
                   w_el_in=w_el,
                   w_el_out=chp_el_prod,
                   bafa_chp_tes=bafa_chp_tes)

        calc_emissions(q_gas, w_el)

    return city


def calc_hp_spf(heatPump, environment, sh_curve, cop=(2.9, 3.7, 4.4), method=0):
    """
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
    spf : Seasonal performance factor
    """

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

        f_theta_dict = {-3: 1.26, -2: 1.142, -1: 1.159, 0: 1.177, 1: 1.95, 2: 1.214, 3: 1.234, 4: 1.253, 5: 1.273}
        f_theta = f_theta_dict[t_ground]
        f_P = 1.075     # correction factor for pump

        hp_spf = cop[0] * f_d_theta * f_theta / f_P

        return hp_spf

    else:
        raise Warning('Unknown heatPump type!')


def check_enev(area_total):
    """
    Check if commissioning of boiler is according to EnEV.
    It is presumed that only condensing boilers are used (outside of thermal envelope; temperatures 70/55)
    "Energieaufwandszahl" (e_g) taken from table C.3-4b of DIN V 4701-10:2003-08

    Parameters
    ----------
    area_total : float
        Total area of building
    """

    # e_g for boiler from DIN V 4701-10, table C.3-4b, ff.
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
    """
    Checks for compliance with EEWaermeG.
    Works only for districts where all buildings have same building age (see get_building_age())

    Parameters
    ----------
    city : pyCity_calc city object
    device : pyCity_calc class : HeatpumpExtended, ChpExtended, BoilerExtended
    ee_ratio : float : ratio of renewable
    spf : float : seasonal performance factor

    Returns
    -------
    Compliance with EEWaermeG : bool
    """

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

        # -------------- Boiler (base supply) --------------
        elif device.kind == 'boiler':
            return False
    else:
        print('EEWaermeG is not obligatory due to building age.')
        return True


def calc_emissions(q_gas, w_el):
    """
    Calculate estimated emissions.

    Parameters
    ----------
    q_gas : list : total amount of gas used during one year in kWh/yr
    w_el : list : total amount of electricity from the grid used during one year in kWh/yr

    Returns
    -------

    """
    emission = co2.Emissions()
    emf_el = emission.get_co2_emission_factors(type='el_mix')  # kg/kWh
    emf_gas = emission.get_co2_emission_factors(type='gas')    # kg/kWh

    co2_gas = sum(q_gas) * emf_gas
    co2_el = sum(w_el) * emf_el
    co2_total = co2_el + co2_gas

    print('** CO2 per year: ' + str(round(co2_total,2)) + ' kgCO2/a **')


def calc_costs(city, q_gas, w_el_in, w_el_out, i=0.08, price_gas=0.0661, price_el=0.29, el_feedin_epex=0.02978, bafa_lhn=False, bafa_chp_tes=False):
    """
    Calculate estimated costs (in EUR/yr):
    - Capital related costs
    - Demand related costs
    - Operational costs (for inspection, maintenance and service)
    - Revenue for produced electricity
    - Subsidies

    Parameters
    ----------
    city:           pyCity city-object
    q_gas:          amount of gas needed
    w_el_in:        amount of el. energy needed
    w_el_out:       amount of el. energy produced
    i:              interest rate
    price_gas:      price of gas EUR/kWh
    price_el:       price of electricity for heatpump in EUR/kWh
    el_feedin_epex: average price for baseload power at EPEX Spot for Q2 2017 in Euro/kWh
    bafa_lhn:       indicates if BAFA funding for lhn is applicable
    bafa_chp_tes:   indicates if BAFA funding for TES with CHP is applicable

    Returns
    -------
    costs:          tuple of total capital and total operational costs in Euro
    """

    # Data for maintenance and service (from VDI2067)

    # service fee in Euro/h
    service_fee = 40

    # [maintenance in %, service in %, service hours in h]
    insp_vdi2067 = {'boiler': [0.01, 0.015, 20], 'chp': [0.06, 0.02, 100], 'hp': [0.01, 0.015, 5],
                    'elHeater': [0.01, 0.01, 0], 'tes': [0.01, 0.01, 0], 'lhn_station': [0.02, 0.01, 0],
                    'lhn_pipes': [0.5, 0, 0]}

    # Investment costs for pipes dependant on diameter {diameter in m : costs in EUR}
    cost_pipes_dm = {0.0161: 284, 0.0217: 284.25, 0.0273: 284.50, 0.0372: 284.75, 0.0431: 285, 0.0545: 301,
                     0.0703: 324.5, 0.0825: 348.5, 0.1071: 397, 0.1325: 443, 0.1603: 485}

    #################################
    #   Economic results for devices
    #################################

    for bn in city.nodelist_building:

        if city.node[bn]['entity'].hasBes:
            bes = city.node[bn]['entity'].bes

            p_chp_nom = 0

            cost_invest = []    # invest costs
            cost_cap = []       # capital costs
            cost_insp = []      # inspection, maintenance and service costs (VDI 2067)
            rev = []            # revenue for electricity feed-in and kwkg

            if bes.hasHeatpump:
                t = 20  # VDI 2067
                q_hp_nom = bes.heatpump.qNominal/1000   # in kW

                if bes.heatpump.hp_type == 'aw':

                    # Calculate seasonal performance factor
                    spf = calc_hp_spf(heatPump=bes.heatpump,
                                      environment=city.environment,
                                      sh_curve=city.node[bn]['entity'].get_space_heating_power_curve())

                    # Calculate invest costs for hp
                    hp_invest = hp_cost.calc_spec_cost_hp(q_hp_nom, method='wolf', hp_type='aw') * q_hp_nom
                    a = i * (1 + i) ** t / ((1 + i) ** t - 1)

                    cost_invest.append(hp_invest)
                    cost_cap.append(hp_invest * a)
                    cost_insp.append(hp_invest * (sum(insp_vdi2067['hp'][0:2])) + insp_vdi2067['hp'][2] * service_fee)

                elif bes.heatpump.hp_type == 'ww':

                    # Calculate seasonal performance factor
                    spf = calc_hp_spf(heatPump=bes.heatpump,
                                      environment=city.environment,
                                      sh_curve=city.node[bn]['entity'].get_space_heating_power_curve(),
                                      cop=[4.8])

                    hp_invest = hp_cost.calc_spec_cost_hp(q_hp_nom, method='wolf', hp_type='ww') * q_hp_nom
                    a = i * (1 + i) ** t / ((1 + i) ** t - 1)

                    cost_invest.append(hp_invest)
                    cost_cap.append(hp_invest * a)
                    cost_insp.append(hp_invest * (sum(insp_vdi2067['hp'][0:2])) + insp_vdi2067['hp'][2] * service_fee)

                if bes.hasBoiler:
                    t = 20  # VDI 2067
                    q_boi_nom = bes.boiler.qNominal/1000    # in kW

                    boiler_invest = boiler_cost.calc_spec_cost_boiler(q_boi_nom, method='viess2013') * q_boi_nom
                    a = i * (1 + i) ** t / ((1 + i) ** t - 1)

                    cost_invest.append(boiler_invest)
                    cost_cap.append(boiler_invest * a)
                    cost_insp.append(
                        boiler_invest * (sum(insp_vdi2067['boiler'][0:2])) + insp_vdi2067['boiler'][2] * service_fee)
    
                elif bes.hasElectricalHeater:
                    t = 18 # VDI 2067
                    q_elHeater_nom = bes.electricalHeater.qNominal/1000 # in kW

                    elHeater_invest = eh_cost.calc_spec_cost_eh(q_elHeater_nom, method='spieker') * q_elHeater_nom
                    a = i * (1 + i) ** t / ((1 + i) ** t - 1)

                    cost_invest.append(elHeater_invest)
                    cost_cap.append(elHeater_invest * a)
                    cost_insp.append(elHeater_invest*(sum(insp_vdi2067['elHeater'][0:2])) + insp_vdi2067['elHeater'][2] * service_fee)

            # CHP as base supply
            elif bes.hasChp:
                t = 15  # VDI 2067
                p_chp_nom = bes.chp.pNominal/1000   # in kW
                q_chp_nom = bes.chp.qNominal/1000   # in kW
                eta_th = bes.chp.omega / (1 + bes.chp.sigma)

                a = i * (1 + i) ** t / ((1 + i) ** t - 1)
                chp_invest = p_chp_nom * chp_cost.calc_spec_cost_chp(p_chp_nom,
                                                                     method='asue2015',
                                                                     with_inst=True,
                                                                     use_el_input=True,
                                                                     q_th_nom=None)

                if bes.hasTes:
                    v_tes = bes.tes.capacity*1000/bes.tes.rho   # in liter
                    bafa_subs_chp = dim_devices.get_subs_minichp(p_chp_nom, q_chp_nom, v_tes)   # in Euro
                else:
                    bafa_subs_chp = 0

                el_feedin_chp = dim_devices.get_el_feedin_tariff_chp(p_chp_nom,el_feedin_epex)

                cost_invest.append(chp_invest - bafa_subs_chp)
                cost_cap.append((chp_invest - bafa_subs_chp)*a)
                cost_insp.append(chp_invest * (sum(insp_vdi2067['chp'][0:2])) + insp_vdi2067['chp'][2] * service_fee)
                rev.append(w_el_out * bes.chp.sigma * el_feedin_chp)

                if bes.hasBoiler:
                    t = 20  # VDI 2067
                    q_boi_nom = bes.boiler.qNominal/1000

                    boiler_invest = boiler_cost.calc_spec_cost_boiler(q_boi_nom, method='viess2013') * q_boi_nom
                    a = i * (1 + i) ** t / ((1 + i) ** t - 1)

                    cost_invest.append(boiler_invest)
                    cost_cap.append(boiler_invest * a)
                    cost_insp.append(boiler_invest * (sum(insp_vdi2067['boiler'][0:2])) + insp_vdi2067['boiler'][2] * service_fee)

            # Boiler as base supply
            elif bes.hasBoiler:
                t = 20  # VDI 2067
                q_boi_nom = bes.boiler.qNominal / 1000

                boiler_invest = boiler_cost.calc_spec_cost_boiler(q_boi_nom, method='viess2013') * q_boi_nom
                a = i * (1 + i) ** t / ((1 + i) ** t - 1)

                cost_invest.append(boiler_invest)
                cost_cap.append(boiler_invest * a)
                cost_insp.append(
                    boiler_invest * (sum(insp_vdi2067['boiler'][0:2])) + insp_vdi2067['boiler'][2] * service_fee)

            # Invest and subsidies for TES
            if bes.hasTes:
                t = 20 # VDI 2067
                volume = bes.tes.capacity/bes.tes.rho # in m3
                tes_invest = tes_cost.calc_invest_cost_tes(volume, method='spieker')
                a = i * (1 + i) ** t / ((1 + i) ** t - 1)

                # BAFA subsidy for TES
                if bafa_chp_tes:    # if True -> chp_ratio >= 0.5
                    bafa_subs_tes = dim_devices.get_subs_tes_chp(chp_ratio=0.55,
                                                                 v_tes=volume,
                                                                 tes_invest=tes_invest,
                                                                 p_nom=p_chp_nom)

                    print('BAFA subsidy for TES possible:', bafa_subs_tes, ' Euro')
                else:
                    bafa_subs_tes = 0

                cost_invest.append(tes_invest-bafa_subs_tes)
                cost_cap.append((tes_invest-bafa_subs_tes)*a)
                cost_insp.append(tes_invest*(sum(insp_vdi2067['tes'][0:2])) + insp_vdi2067['tes'][2] * service_fee)
            break
    else:
        raise Exception('No BES installed!')

    #########################
    #   Economic data for LHN
    #########################

    for v in city.edge.values():

        if bool(v):

            lhn_station_invest = []

            # LHN station for every building
            for b in city.nodelist_building:
                building = city.node[b]['entity']
                q_max = max(building.get_space_heating_power_curve()/1000 + building.get_dhw_power_curve()/1000)
                lhn_station_invest.append(lhn_cost.calc_invest_single_lhn_station(q_max))

            t = 20  # VDI 2067 (indirect connection)
            a_station = i * (1 + i) ** t / ((1 + i) ** t - 1)

            cost_invest.append(sum(lhn_station_invest))
            cost_cap.append(sum(lhn_station_invest) * a_station)
            cost_insp.append(sum(lhn_station_invest) * (sum(insp_vdi2067['lhn_station'][0:2])) +
                             insp_vdi2067['lhn_station'][2] * service_fee)

            # Pipe costs
            lhn_length = round(net_ops.sum_up_weights_of_edges(city),2)

            for d in city.edge[city.nodelist_building[0]].values():
                pipe_dm = d['d_i']  # get pipe_diameter
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
                    cost_insp.append(pipes_invest*(sum(insp_vdi2067['lhn_pipes'][0:2])) + insp_vdi2067['lhn_pipes'][2] * service_fee)
                    break
            else:
                raise Exception('Pipe diameter too big!')

            # BAFA subsidy for LHN
            if bafa_lhn:
                if dm <= 0.1:
                    lhn_subs_pre = 100 * lhn_length  # 100 Euro/m if dn <= 100
                    if lhn_subs_pre > 0.4 * sum(cost_invest):  # subsidy must not be higher than 40% of total invest
                        lhn_subs = 0.4 * sum(cost_invest)
                    else:
                        lhn_subs = lhn_subs_pre
                else:
                    lhn_subs = 0.3 * sum(cost_invest)   # 30% of invest if dn > 100
                if lhn_subs > 20000000:  # max. subsidy is 20.000.000
                    lhn_subs = 20000000
                lhn_subs_fee = 0.002 * lhn_subs  # fee is 0.2% of subsidy
                if lhn_subs_fee < 100:  # min. fee is 100 Euro
                    lhn_subs_fee = 100
                lhn_subs = lhn_subs - lhn_subs_fee
                cost_invest.append(-lhn_subs)
                cost_cap.append(-lhn_subs*a_pipes)
                print('BAFA LHN subsidy applies: ' + str(lhn_subs) + 'Euro off of total invest')
            break

    # Calculate demand related costs
    cost_dem = sum(q_gas) * price_gas + sum(w_el_in) * price_el

    #################
    #   Print Costs
    #################

    cost_cap_total = round(sum(cost_cap), 2)
    cost_dem_total = round(cost_dem, 2)
    cost_insp_total = round(sum(cost_insp), 2)
    rev_total = round(sum(rev), 2)

    print('Capital Cost:', cost_cap_total)
    print('Demand related Cost:', cost_dem_total)
    print('Costs for inspection, maintenance and service:', cost_insp_total)
    print('Revenue for el feed-in:', rev_total)
    print('\n** Costs per year:', cost_cap_total+cost_dem_total+cost_insp_total-rev_total, 'Euro/a **')

    return cost_cap_total, cost_dem_total


if __name__ == '__main__':

    scenarios = []

    scenarios.append({'type': ['centralized'], 'base': ['boiler'], 'peak': ['']})
    scenarios.append({'type': ['decentralized'], 'base': ['boiler'], 'peak': ['']})

    scenarios.append({'type': ['centralized'], 'base': ['chp'], 'peak': ['boiler']})
    scenarios.append({'type': ['decentralized'], 'base': ['chp'], 'peak': ['boiler']})

    scenarios.append({'type': ['decentralized'], 'base': ['hp_air'], 'peak': ['boiler']})
    scenarios.append({'type': ['decentralized'], 'base': ['hp_air'], 'peak': ['elHeater']})
    scenarios.append({'type': ['decentralized'], 'base': ['hp_geo'], 'peak': ['']})

    this_path = os.path.dirname(os.path.abspath(__file__))

    city_f_name = 'city_2_buildings_w_street.pkl'

    city_path = os.path.join(this_path, 'input', city_f_name)
    city = pickle.load(open(city_path, mode='rb'))

    print('District ' + city_f_name[:-4] + ' loaded')
    list_city_object = run_approach(city, scenarios)

    # ---- Output in pickle files -----
    '''
    import pycity_calc.visualization.city_visual as citvis

    for i in range(len(list_city_object)):
        cit = list_city_object[i]
        city_name = 'output_(' + str(i) + ')_' + city_f_name

        path_output = os.path.join(this_path, 'output', city_name)
        pickle.dump(cit, open(path_output, mode='wb'))
        citvis.plot_city_district(city=cit, plot_lhn=True, plot_deg=True,
                                  plot_esys=True)
    '''
