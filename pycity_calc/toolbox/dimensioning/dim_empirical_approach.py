"""
Tool for the dimensioning of heating devices and district heating networks in city districts, based on approaches
as being common in the industry.
Every dimensioned district complies with current legal requirements.

"""

import os
import pickle
import numpy as np
from copy import deepcopy
import xlrd
import math

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



def run_approach(city,scenarios,geothermal=True):
    """
    Main method to coordinate the planning process.

    Parameters
    ----------
    city:           standard city_object from pyCity_base
    scenarios:      list of dictionaries with common configurations of devices and suitability for (de)centralized usage
    building_con:   Connection building -> district heating network already installed
    heating_net:    district heating network already installed
    geothermal:     usage of geothermal energy possible

    Returns
    -------
    solutions:      list of city_objects with installed building energy systems, depending on scenarios
    """
    #  Todo: Add explanations to docstring

    solutions = [] #Liste aller möglichen dimensionierten Szenarien (inklusive Kosten und Emissionen)


    # Check Eligibility for District Heating Network
    dhn_elig = get_eligibility_dhn(city, method=1)


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
                if approve_scenario(city, scenario, geothermal):
                    print('\n---------- Scenario Centralized ' + str(scenarios.index(scenario)), '-----------')
                    result = dim_centralized(deepcopy(city),scenario, district_type)
                    solutions.append(result)


    elif dhn_elig < 2:
        print('District Heating not eligible!')
        for scenario in scenarios:
            if 'decentralized' in scenario['type']:
                if approve_scenario(city, scenario, geothermal):
                    print('\n---------- Scenario Decentralized ' + str(scenarios.index(scenario)), '-----------')
                    solutions.append(dim_decentralized(deepcopy(city),scenario))

    else:
        print('District Heating solutions might be eligible...')
        for scenario in scenarios:
            if approve_scenario(city, scenario, geothermal):
                if 'centralized' in scenario['type']:
                    print('\n---------- Scenario Centralized ' + str(scenarios.index(scenario)), '-----------')
                    solutions.append(dim_centralized(deepcopy(city),scenario,district_type))
                if 'decentralized' in scenario['type']:
                    print('\n---------- Scenario Decentralized ' + str(scenarios.index(scenario)), '-----------')
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



def approve_scenario(city, scenario, geothermal):
    # TODO: Wird diese Funktion gebraucht? Kann ggf. in Geothermiedimensionierung rein!!
    '''
    Check if scenario is suitable for city
    :param city: standard city_object
    :param scenario:
    :return: True/False
    '''
    if 'hp_geo' in scenario['base'] and not geothermal:
        return False
    return True


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

        num_buildings = len(city.nodelist_building)
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

        elif district_type == 'small':
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

        return elig_val


def get_LDC(curve):
    '''
    returns Load duration curve (Jahresdauerlinie)
    :param curve: thermal or electrical curve
    :return: load duration curve
    '''
    return sorted(curve, reverse=True)


def choose_device(dev_type, q_ideal):
    # TODO: Mehr BHKW Daten eintragen
    # Source: BHKW-Kenndaten 2014, S.26 - [eta_el, eta_th, p_nom, q_nom]
    chp_list = {'vai1':[0.263, 0.658, 1000, 2500], 'vai2':[0.25, 0.667, 3000, 8000], 'vai3':[0.247,0.658,4700,12500],
                'vie':[0.27, 0.671, 6000, 14900], 'rmb7.2':[0.263, 0.657, 7200, 18000],'oet8':[0.268,0.633,8000,19000],
                'xrgi9':[0.289,0.641,9000,20000],'rmb11.0':[0.289,0.632,11000,24000],'xrgi15':[0.307,0.613,15000,30000],
                'asv1534':[0.306,0.694,15000,34000],'sb16':[0.314,0.72,16000,36700],'xrgi20':[0.32,0.64,20000,40000]}

    if dev_type == 'chp':
        specs = [0, 0, 0, 0]
        for dev in chp_list.values():
            eta_th = dev[1]
            q_nom = dev[3]
            if abs(q_nom-q_ideal) < abs(specs[3]-q_ideal):
                specs = dev[:]
    elif dev_type == 'hp':
        this_path = os.path.dirname(os.path.abspath(__file__))
        hp_data_path = os.path.join(this_path, 'input', 'heat_pumps.xlsx')
        heatpumpData = xlrd.open_workbook(hp_data_path)

        lower_activation_limit = 0.5

        if q_ideal >= 50000:
            hp_sheet = heatpumpData.sheet_by_name("Dimplex_LA60TU")
            print('Added HP: Dimplex LA60TU')
        elif q_ideal >= 30000 and q_ideal < 50000:
            hp_sheet = heatpumpData.sheet_by_name("Dimplex_LA40TU")
            print('Added HP: Dimplex LA40TU')
        elif q_ideal >= 20000 and q_ideal < 30000:
            hp_sheet = heatpumpData.sheet_by_name("Dimplex_LA25TU")
            print('Added HP: Dimplex LA25TU')
        elif q_ideal >= 10000 and q_ideal < 20000:
            hp_sheet = heatpumpData.sheet_by_name("Dimplex_LA18STU")
            print('Added HP: Dimplex LA18STU')
        elif q_ideal < 10000:
            hp_sheet = heatpumpData.sheet_by_name("Dimplex_LA9STU")
            print('Added HP: Dimplex LA9STU')

        # Size of the worksheet
        number_rows = hp_sheet._dimnrows
        number_columns = hp_sheet._dimncols
        # Flow, ambient and max. temperatures
        tFlow = np.zeros(number_columns - 2)
        tAmbient = np.zeros(int((number_rows - 7) / 2))
        tMax = hp_sheet.cell_value(0, 1)

        firstRowCOP = number_rows - len(tAmbient)

        qNominal = np.empty((len(tAmbient), len(tFlow)))
        cop = np.empty((len(tAmbient), len(tFlow)))

        for i in range(number_columns - 2):
            tFlow[i] = hp_sheet.cell_value(3, 2 + i)

        for col in range(len(tFlow)):
            for row in range(len(tAmbient)):
                qNominal[row, col] = hp_sheet.cell_value(int(4 + row),
                                                               int(2 + col))
                cop[row, col] = hp_sheet.cell_value(int(firstRowCOP + row),
                                                          int(2 + col))

        pNominal = qNominal / cop

        specs = [tAmbient, tFlow, qNominal, pNominal, cop, tMax, lower_activation_limit]

    return specs


def get_chp_ann_op_time(q_nom, th_LDC):

    # CHP-Jahreslaufzeitberechnung (annual operation time) nach Krimmling(2011)
    for q_m in th_LDC:
        if q_m <= q_nom:
            t_x = th_LDC.index(q_m)  # find crossing point on LDC (Volllaststunden)
            break
    delta_a = 8760 * th_LDC[0]
    for t in range(t_x, 8760):  # Punkt suchen an dem Dreicke gleichgroß (siehe Krimmling S.131, Abb.4-15)
        a1 = q_m * (t - t_x) - sum(th_LDC[t_x:t])
        a2 = sum(th_LDC[t:8760])
        if delta_a <= abs(a2 - a1):
            t_ann_operation = t - 1
            return t_ann_operation, t_x
        else:
            delta_a = a2 - a1


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
    th_LDC = get_LDC(th_curve)
    q_total = np.sum(th_curve)
    people_total = 0
    area_total = 0
    for b_node in city.nodelist_building:
        building = city.node[b_node]['entity']
        area_total += building.net_floor_area
        for ap in building.apartments:
            people_total += ap.occupancy.number_occupants

    heg = []
    qPEF = []

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


    if 'chp' in scenario['base']:

        # select method (method=0 is standard)
        chp_sol = dim_devices.dim_central_chp(th_LDC, q_total, district_type, method=0)

        if chp_sol is None:
            raise Warning('CHP not suitable for lhn.')

        else:
            eta_el, eta_th, p_nom, q_nom, t_x, t_ann_op = chp_sol

            if not check_eewaermeg(city, 'chp', t_ann_op, q_total):
                raise Warning('Energysystem with CHP not according to EEWaermeG!')

            chp = CHP.ChpExtended(city.environment,q_nom,p_nom, eta_el + eta_th)
            bes.addDevice(chp)
            print('CHP: Q_nom = ' + str(q_nom / 1000) + ' kW (' + str(round(q_nom * 100 / max(th_curve), 2)) +
                  '% of Q_max) ->', t_x, 'full-load hours.')

            # Check if BAFA/KWKG subsidy for lhn is available
            if t_ann_op*q_nom/q_total > 0.75:
                bafa_lhn = True
            else:
                bafa_lhn = False

            # PEF und qPEF für EnEV berechnen
            q_chp_ann = t_ann_op*q_nom/eta_th # Endenergiemenge des Brennstoffs vor der Verbrennung in KWK-Anlage
            w_el_chp_out = q_chp_ann * eta_el # Mit KWK-Anlage produzierte, ausgespeiste Strommenge
            qPEF.append(get_factor_enev('pef','gas',area_total) * q_chp_ann - get_factor_enev('pef','el_chp_out',area_total) * w_el_chp_out) # KWK-Anlage mit Erdgas betrieben?!

            # Pufferspeicher hinzufügen falls Leistung über 20% von Maximalverbrauch
            if True:    #q_nom/max(th_LDC) > 0.2:
                v_tes = q_nom/1000*60 # Förderung von Speichern für Mini-BHKW durch BAFA bei Speichergrößen über 60 l/kW_th
                if v_tes > 1600: # 1600 liter genügen für Förderung
                    v_tes = 1600 + (q_nom/1000*60-1600)*0.2 # Schätzung um auch Anlagen >30kW mit Speicher zu versorgen
                    # TODO: Wie sieht die Dimensionierung für KWK-Anlagen über 30 kW aus? Sind die 20% realistisch?
                # v_tes = 104 + 10 * q_nom    # Dimensionierung nach Wolff & Jagnow 2011, S. 60, evtl. nur für konkretes beispiel
                tes = TES.thermalEnergyStorageExtended(environment=city.environment,t_init=50,capacity=v_tes)
                bes.addDevice(tes)
                print('Added Thermal Energy Storage:', v_tes,'liter ')
                heg.append(get_factor_enev('heg','storage',area_total)*area_total)
                if q_nom * t_ann_op * 100 / q_total >= 50:
                    bafa_chp_tes = True

            # Wärmeerzeuger für Spitzenlast hinzufügen
            if 'boiler' in scenario['peak']:
                q_boiler = (max(th_LDC) - q_nom) * 1.1  # 10% safety
                boiler = Boiler.BoilerExtended(city.environment, q_boiler, 0.8)
                bes.addDevice(boiler)
                print('Added Boiler: Q_nom = '+str(round(q_boiler/1000,2))+' kW')
                if q_boiler >= 4000 and q_boiler < 400000:
                    print('Boiler requires CE Label. (according to 92/42/EWG)')
                qPEF.append(get_factor_enev('pef','gas',area_total)*(q_total - q_nom * t_ann_op))  # EnEV für Boiler. Anteil an Wärme*PEF (eta_th mit rein?)
                heg.append(get_factor_enev('heg','boiler',area_total)*area_total)

            ann_q_base = t_ann_op*q_nom/1000 # Annual produced heat with base supply in kWh
            ann_q_peak = (q_total - q_nom * t_ann_op)/1000 # Annual produced heat with peak supply in kWh


    elif 'hp_geo' in scenario['base']:
        # TODO: GEothermie Wärmepumpe einbinden?
        print(' hp geothermie')
        # result['hp_geo'] = 1 # dummy

    elif 'boiler' in scenario['base']:
        q_boiler = max(th_curve)
        boiler = Boiler.BoilerExtended(city.environment, q_boiler, 0.8)
        bes.addDevice(boiler)
        print('Added Boiler: Q_nom = ' + str(round(q_boiler / 1000, 2)) + ' kW')

        qPEF.append(get_factor_enev('pef', 'gas', area_total) * get_factor_enev('eg', 'boiler', area_total) * q_total / boiler.eta)
        heg.append(get_factor_enev('heg', 'boiler', area_total) * area_total)

        ann_q_base = np.sum(th_curve) / 1000  # Annual produced heat with base supply in kWh
        ann_q_peak = 0


    elif 'hp_air' in scenario['base']:
        # evtl. Vor/Rücklauftemperaturen mit Diagramm aus KVS-Klimatechnik bestimmen (Bild 1.1a, S.11)

        # TODO: Wärmepumpen doch nur für Heizung -> Warmwasser über andere Anlage?

        [tAmbient, tFlow, qNominal, pNominal, cop, tMax, lower_activation_limit] = choose_device('hp', max(th_curve))
        hp_air = HP.Heatpump(city.environment, tAmbient, tFlow, qNominal, pNominal, cop,
                             tMax, lower_activation_limit)
        bes.addDevice(hp_air)

        # Warmwasserspeicher hinzufügen
        t_soll = 50 # Speichersolltemperatur
        t_cw = 10 # Kaltwassertemperatur
        v_tes = people_total*25*(60-t_cw)/(t_soll-t_cw) # Speichervolumen nach Dimplex PHB (Kap.6.1.3)
        tes = TES.thermalEnergyStorageExtended(environment=city.environment, t_init=t_soll, capacity=v_tes)
        bes.addDevice(tes)
        print('Added Thermal Energy Storage:', v_tes, 'liter ')

        if 'boiler' in scenario['peak']:
            '''Ansatz nach Edraw
            t_demand_list = get_t_demand_list(city.environment.weather.tAmbient, th_curve)
            cop = {-20:1.54,-15:1.73,-7:2.22,2:2.56,7:2.8,10:3.08,12:3.15,20:3.61}
            '''

            # Alter Ansatz (nach PHB Dimplex)
            # Details HeatPump
            t1_hp = -15  # °C
            t2_hp = 20  # °C
            q1_hp = hp_air.heat[1][2]  # W
            q2_hp = hp_air.heat[7][2]  # W

            # Leistung von HP bei niedrigster Temperatur (Annahme Wärmebedarf dort am größten)
            q_hp = (q2_hp - q1_hp) / (t2_hp - t1_hp) * (min(city.environment.weather.tAmbient) - t1_hp) + q1_hp

            # Add Boiler
            q_boiler = max(th_curve) - q_hp
            boiler = Boiler.BoilerExtended(city.environment, q_boiler, 0.8)
            bes.addDevice(boiler)
            print('Added Boiler: Q_nom = ' + str(round(q_boiler / 1000, 2)) + ' kW')
            if q_boiler >= 4000 and q_boiler < 400000:
                print('Kessel muss CE Kennzeichnung vorweisen können. (gemäß 92/42/EWG)')

            # HP- and Boiler-Data for EnEV
            cop_durchschnitt = 3 # TODO: Welcher COP wird hier verwendet? Durchschnitt?
            # TODO: Anwendung der Aufwandszahlen eg überprüfen - in dieser Weise korrekt?
            w_hp_ann = 0.83*0.37*q_total/cop_durchschnitt # Anteil HP/Boiler nach DIN V 4701-10, Tabelle C.3-4a.
            qPEF.append(get_factor_enev('pef','el_in',area_total) * w_hp_ann)
            qPEF.append(get_factor_enev('pef','gas',area_total)*0.17*get_factor_enev('eg','boiler',area_total)*q_total/boiler.eta)
            heg.append(get_factor_enev('heg','boiler',area_total)*area_total)
        else:
            cop_durchschnitt = 3 # TODO: Welcher COP wird hier verwendet? Durchschnitt?
            # TODO: Anwendung der Aufwandszahlen eg überprüfen - in dieser Weise korrekt?
            w_hp_ann = q_total/cop_durchschnitt # Anteil HP/Boiler nach DIN V 4701-10, Tabelle C.3-4a.
            qPEF.append(get_factor_enev('pef','el_in',area_total) * w_hp_ann)



    # Check EnEV (Produkt Erzeugeraufwandszahl und PEF <= 1,3)
    eg_nahwaerme = 1.01 # Zentralisierte Versorgung!
    pef_nahwaerme = (sum(qPEF)+sum(heg)*get_factor_enev('pef','el_in',area_total))/sum(th_curve*eta_transmission)
    if eg_nahwaerme*pef_nahwaerme <= 1.3:
        print('Energysytem according to EnEV! Factor:', round(eg_nahwaerme*pef_nahwaerme,2))
    else:
        print('Energysystem not according to EnEV! Factor:', round(eg_nahwaerme*pef_nahwaerme,2))


    # Im ersten Gebäude wird das BES installiert (-> besser in kürzester Distanz aller Gebäude)
    # TODO: Optimales Gebäude/Standort auswählen
    assert not city.node[city.nodelist_building[0]]['entity'].hasBes, ('Building 0 has already BES. Mistakes may occur!')
    city.node[city.nodelist_building[0]]['entity'].addEntity(bes)

    calc_costs_centralized(city,ann_q_base, ann_q_peak, bafa_lhn=bafa_lhn, bafa_chp_tes=bafa_chp_tes)

    return city




def dim_decentralized(city, scenario):
    '''
    Set sizes of devices in scenario
    :param scenario:
    :return: scenario with sizes of devices - in welcher form? city_object
    '''

    # TODO: EnEV für dezentrale Fälle berechnen, kontrollieren
    # TODO: EEWärmeG für dezentrale Fälle kontrollieren

    for b_node in city.nodelist_building:
        building = city.node[b_node]['entity']

        sh_curve = building.get_space_heating_power_curve()
        dhw_curve = building.get_dhw_power_curve()
        q_total = np.sum(sh_curve + dhw_curve)

        area_total = building.net_floor_area

        people_total = 0
        for ap in building.apartments:
            people_total += ap.occupancy.number_occupants

        heg = []
        qPEF = []

        bes = BES.BES(city.environment)

        for device in scenario['base']:
            if device == 'chp':

                th_LDC = dim_devices.get_LDC(sh_curve + dhw_curve)
                chp_sol = dim_devices.dim_decentral_chp(th_LDC, q_total, method=0)

                if chp_sol is None:
                    raise Warning('CHP not suitable for lhn.')
                else:
                    eta_el, eta_th, p_nom, q_nom, t_x, t_ann_op = chp_sol

                chp = CHP.ChpExtended(city.environment, p_nom, q_nom, eta_el + eta_th)
                bes.addDevice(chp)
                print('CHP: Q_nom = ' + str(q_nom / 1000) + ' kW (' + str(round(q_nom * 100 / max(th_LDC), 2)) +
                      '% of Q_max) ->', t_x, 'full-load hours.')

                # PEF und qPEF für EnEV berechnen
                q_chp_ann = t_ann_op * q_nom / eta_th  # Endenergiemenge des Brennstoffs vor der Verbrennung in KWK-Anlage
                w_el_chp_out = q_chp_ann * eta_el  # Mit KWK-Anlage produzierte, ausgespeiste Strommenge
                qPEF.append(get_factor_enev('pef', 'gas', area_total) * q_chp_ann - get_factor_enev('pef', 'el_chp_out',
                                                                                                   area_total) * w_el_chp_out)  # KWK-Anlage mit Erdgas betrieben?!

                # Pufferspeicher hinzufügen falls Leistung über 20% von Maximalverbrauch
                if True:    #q_nom / max(th_LDC) > 0.2:
                    v_tes = q_nom / 1000 * 60  # Förderung von Speichern für Mini-BHKW durch BAFA bei Speichergrößen über 60 l/kW_th
                    if v_tes > 1600:  # 1600 liter genügen für Förderung
                        v_tes = 1600 + (q_nom / 1000 * 60 - 1600) * 0.2  # Schätzung um auch Anlagen >30kW mit Speicher zu versorgen
                    tes = TES.thermalEnergyStorageExtended(environment=city.environment, t_init=50, capacity=v_tes)
                    bes.addDevice(tes)
                    print('Added Thermal Energy Storage:', v_tes, 'liter ')
                    heg.append(get_factor_enev('heg', 'storage', area_total) * area_total)
                    if q_nom * t_ann_op * 100 / q_total >= 50:
                        bafa_chp_tes = True

                # Wärmeerzeuger für Spitzenlast hinzufügen
                if 'boiler' in scenario['peak']:
                    q_boiler = (max(th_LDC) - q_nom)*1.5
                    boiler = Boiler.BoilerExtended(city.environment, q_boiler, 0.8)
                    bes.addDevice(boiler)
                    print('Added Boiler: Q_nom = ' + str(round(q_boiler / 1000, 2)) + ' kW')
                    if q_boiler >= 4000 and q_boiler < 400000:
                        print('Boiler requires CE Label. (according to 92/42/EWG)')
                    qPEF.append(get_factor_enev('pef', 'gas', area_total) * (
                    q_total - q_nom * t_ann_op))  # EnEV für Boiler. Anteil an Wärme*PEF (eta_th mit rein?)
                    heg.append(get_factor_enev('heg', 'boiler', area_total) * area_total)


                # TODO: Welche Förderungen im dezentralen Fall?


            elif device == 'hp_air':

                # Hier deckt Wärmepumpe mit integriertem elHeater/Brennwertkessel den Bedarf von Raumwärme und WW

                # TODO: Dimensionierung integrieren
                # Dimensionierung nach:
                #   - Kurvenverschiebung wie in zentralisiert (ggf. in Buch nachgucken)
                #   - nur mit elHeater für peak-Deckung

                # nach VDI 4645!

                #sh_curve = building.get_space_heating_power_curve()

                q_nom, tMax, lowerActivationLimit, tSink, t_dem_ldc, biv_ind = dim_devices.dim_decentral_hp(city.environment, sh_curve)

                heatPump = HP.heatPumpSimple(city.environment,
                                             q_nominal=q_nom,
                                             t_max=tMax,
                                             lower_activation_limit=lowerActivationLimit,
                                             hp_type='aw',
                                             t_sink=tSink)
                bes.addDevice(heatPump)
                print('Added HP: Q_nom = ' + str(q_nom / 1000) + ' kW')

                if 'elHeater' in scenario['peak']:
                    safety_factor = 1.8    # over dimensioning to guarantee simulation success
                    q_elHeater = (max(dhw_curve) + max(sh_curve) - q_nom)*safety_factor
                    if q_elHeater > 0:
                        elHeater = ElectricalHeater.ElectricalHeaterExtended(city.environment, q_elHeater, 0.95, 100, 0.2)
                        bes.addDevice(elHeater)
                        print('Added elHeater: Q_nom = ' + str(round(q_elHeater / 1000, 2)) + ' kW')
                    else:
                        print('No elHeater installed.')


                elif 'boiler' in scenario['peak']:
                    safety_factor = 1.2  # over dimensioning to guarantee simulation success
                    q_boiler = (max(dhw_curve) + max(t_dem_ldc[0:biv_ind]) - q_nom) * safety_factor
                    if q_boiler > 0:
                        boiler = Boiler.BoilerExtended(city.environment, q_boiler, 0.8)
                        bes.addDevice(boiler)

                        # elHeater muss installiert werden zur TWW Deckung. Eigentlich sinnlos! Boiler kann das auch!!
                        # elHeater = ElectricalHeater.ElectricalHeaterExtended(city.environment,max(dhw_curve) , 0.95, 100, 0.2)
                        # bes.addDevice(elHeater)
                        print('Added Boiler: Q_nom = ' + str(round(q_boiler / 1000, 2)) + ' kW')
                    else:
                        print('No boiler installed.')

                v_tes = 30*q_nom/1000   # in liter (DIN EN 15450: volume between 12 - 35 l/kW)

                # Warmwasserspeicher hinzufügen
                # t_soll = 65  # Speichersolltemperatur
                # t_cw = 10  # Kaltwassertemperatur
                #TODO: Dimensionierung Speicher verbessern - das ist nur TWW Speicher
                # v_tes = people_total * 25 * (60 - t_cw) / (
                #     t_soll - t_cw)  # Speichervolumen nach Dimplex PHB (Kap.6.1.3)
                tes = TES.thermalEnergyStorageExtended(environment=city.environment, t_init=50,
                                                       capacity=v_tes)
                bes.addDevice(tes)
                print('Added Thermal Energy Storage:', round(v_tes,2), 'liter ')

                # TODO: Förderungen für Wärmepumpe einfügen

            #elif 'hp_geo' in scenario['base']:



            elif 'boiler' in scenario['base']:
                q_boiler = max(sh_curve+dhw_curve)
                boiler = Boiler.BoilerExtended(city.environment, q_boiler, 0.8)
                bes.addDevice(boiler)
                print('Added Boiler: Q_nom = ' + str(round(q_boiler / 1000, 2)) + ' kW')

                qPEF.append(get_factor_enev('pef', 'gas', area_total) * get_factor_enev('eg', 'boiler',
                                                                                        area_total) * q_total / boiler.eta)
                heg.append(get_factor_enev('heg', 'boiler', area_total) * area_total)



                '''
            # TODO: Wärmepumpe und andere Anlagen implementieren!

            if device == 'hp_air':
                #Monovalenter Betrieb von Luft/Wasser-Wärmepumpen nach Dimplex Anleitung (Planungshandbuch S.16)
                # Deckung durch WP bis -5°C Außentemperatur. Danach elHeater.
                # -> Deckung von 2% durch 2.Wärmeerzeuger (elHeater) nach DIN 4701:10 (siehe Dimplex PHB)
                print('dezentral wp')
                '''

        assert not city.node[b_node]['entity'].hasBes, ('Building ', b_node ,' has already BES. Mistakes may occur!')
        city.node[b_node]['entity'].addEntity(bes)

    return city


def get_factor_enev(factor_type, device, area_total):
    # Aufwandszahlen und PEF nach DIN V 4701-10, Tabelle C.3-4b, ff.
    eg_enev = {'boiler': {100: 1.08, 150: 1.07, 200: 1.07, 300: 1.06, 500: 1.05, 750: 1.05, 1000: 1.05, 1500: 1.04,
                          2500: 1.04, 5000: 1.03, 10000: 1.03}, 'hp_air': 0.37, 'hp_geo': 0.27, 'elHeater': 1}
    heg_enev = {
        'distribution': {100: 3.52, 150: 2.4, 200: 1.88, 300: 1.39, 500: 1.01, 750: 0.83, 1000: 0.74, 1500: 0.65,
                         2500: 0.58, 5000: 0.53, 10000: 0.5},  # Werte für geregelte Pumpen, integrierte Heizflächen
        'storage': {100: 0.63, 150: 0.43, 200: 0.34, 300: 0.24, 500: 0.16, 750: 0.12, 1000: 0.1, 1500: 0.08,
                    2500: 0.07, 5000: 0.06, 10000: 0.05},
        'boiler': {100: 0.79, 150: 0.66, 200: 0.58, 300: 0.48, 500: 0.38, 750: 0.31, 1000: 0.27, 1500: 0.23,
                   2500: 0.18, 5000: 0.13, 10000: 0.09}, 'hp_geo': 1.9 / (area_total ** 0.1)}
    pef_enev = {'gas': 1.1, 'el_chp_out': 2.7, 'el_in': 1.8}  # el_chp_out = Verdrängungsstrommix für KWK

    for a in eg_enev['boiler'].keys():
        if a > area_total:
            area_enev = a
            break
    else:
        area_enev = 10000

    if factor_type == 'eg':
        if device == 'boiler':
            return eg_enev[device][area_enev]
        else:
            return eg_enev[device]

    elif factor_type == 'heg':

        if device == 'hp_geo':
            return heg_enev[device]
        else:
            return heg_enev[device][area_enev]

    elif factor_type == 'pef':

        return pef_enev[device]

    else:
        raise Exception('Could not return factor for EnEV calculation.')


def check_eewaermeg(city, device, t_ann_op, q_total):

    if get_building_age(city) == 'new':
        print('EEWaermeG is obligatory!')

        # ----------- CHP -----------
        if device.kind == 'chp':
            p_nom = device.pNominal
            q_nom = device.qNominal
            eta_el = device.omega*device.sigma
            eta_th = device.omega-eta_el

            ee_ratio = q_nom * t_ann_op / q_total

            if ee_ratio > 0.5:
                # calculate primary energy
                refeta_th = 0.85  # th. reference efficiency rate for devices older than 2016 (natural gas)
                refeta_el = 0.525  # el. reference efficiency rate for devices built between 2012 and 2015 (natural gas)

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
        if device.kind == 'hp':
            # TODO: Implementieren!!
            return True

        # ------------ Boiler ------------
        elif device.kind == 'boiler':
            # Must be changed according to EEWaermeG if boiler can be operated with biofuel
            return False

    else:
        print('EEWaermeG is not obligatory due to building age.')
        return True

# -------------------------------- Economic Calculations ----------------------------------------------------


def calc_costs_centralized(city, q_base, q_peak, i=0.08, price_gas=0.0661, el_feedin_epex=0.02978, bafa_lhn=False, bafa_chp_tes=False):
    """
    - Kosten
        - Kapitalkosten (Investitionskosten über Annuitätenfaktor in jährliche Zahlung umrechnen)
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
    price_gas:      price of gas
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
    print('')

    insp_vdi2067 = {'boiler':[0.01,0.02,20],'chp':[0.06,0.02,100],'hp':[0.01,0.015,5]} # [maintenance, service, service hours]
    service_fee = 40 # service fee in Euro/h

    for bn in city.nodelist_building:
        if city.node[bn]['entity'].hasBes:
            bes = city.node[bn]['entity'].bes

            cost_invest = []
            cost_cap = [] # capital costs
            cost_op = [] # operational costs
            cost_insp = [] # inspection, maintenance and service costs (VDI 2067)
            rev = [] # revenue for electricity feed-in and kwkg


            # TODO: Heatpump integrieren (vorher auf Heatpump simple umstellen)
            '''
            if bes.hasHeatpump:
                t = 20  # nach VDI 2067
                i_0 = hp_cost.calc_spec_cost_hp(bes.heatpump.qNominal, method='wolf', hp_type='aw') * bes.heatpump.qNominal
                a = i * (1 + i) ** t / ((1 + i) ** t - 1)
                c_cap.append(i_0 * a)
                
                if bes.hasBoiler:
                    t = 18  # nach VDI 2067
                    i_0 = boiler_cost.calc_spec_cost_boiler(bes.boiler.qNominal,
                                                            method='viess2013') * bes.boiler.qNominal
                    a = i * (1 + i) ** t / ((1 + i) ** t - 1)
                    c_cap.append(i_0 * a)
    
                elif bes.hasElectricalHeater:
                    t = 20 # nach VDI 2067
                    i_0 = eh_cost.calc_spec_cost_eh(bes.electricalHeater.qNominal, method='spieker') * bes.electricalHeater.qNominal
                    a = i * (1 + i)** t / ((1 + i)**t - 1)
                    c_cap.append(i_0*a)
    
            '''
            if bes.hasChp:
                eta_th = bes.chp.omega/(1+bes.chp.sigma)
                t = 15  # nach VDI 2067
                a = i * (1 + i) ** t / ((1 + i) ** t - 1)
                chp_invest = chp_cost.calc_invest_cost_chp(bes.chp.pNominal/1000, method='asue2015', with_inst=True,
                                                                                use_el_input=True, q_th_nom=None)
                print('Investcost CHP', round(chp_invest,2), 'Euro')

                if bes.hasTes:
                    bafa_subs_chp = dim_devices.get_subs_minichp(bes.chp.pNominal, bes.tes.capacity/1000)
                else:
                    bafa_subs_chp = 0

                el_feedin_chp = dim_devices.get_el_feedin_tariff_chp(bes.chp.pNominal,el_feedin_epex)

                cost_invest.append(chp_invest - bafa_subs_chp)
                cost_cap.append((chp_invest - bafa_subs_chp)*a)
                cost_op.append(q_base/eta_th*price_gas)
                cost_insp.append(chp_invest *(sum(insp_vdi2067['chp'][0:2]))+insp_vdi2067['chp'][2]*service_fee)
                rev.append(q_base*bes.chp.sigma*el_feedin_chp)

                if bes.hasBoiler:
                    t = 18  # nach VDI 2067
                    boiler_invest = boiler_cost.calc_abs_boiler_cost(bes.boiler.qNominal/1000, method='viess2013')
                    a = i * (1 + i) ** t / ((1 + i) ** t - 1)
                    cost_invest.append(boiler_invest)
                    cost_cap.append(boiler_invest * a)
                    cost_op.append(q_peak/bes.boiler.eta*price_gas)
                    cost_insp.append(boiler_invest * (sum(insp_vdi2067['boiler'][0:2])) + insp_vdi2067['boiler'][2] * service_fee)

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
            t = 40 # Daumenwert (Quelle: nahwaerme.at)
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

    cost_cap_total = round(sum(cost_cap),2)
    cost_op_total = round(sum(cost_op),2)
    cost_insp_total = round(sum(cost_insp),2)
    rev_total = round(sum(rev),2)

    print('Capital Cost:', cost_cap_total)
    print('Operational Cost:', cost_op_total)
    print('Costs for inspection, maintenance and service:', cost_insp_total)
    print('Revenue for el feed-in:', rev_total)
    print('\n** Costs per year:', cost_cap_total+cost_op_total+cost_insp_total-rev_total, 'Euro/a **')
    return (cost_cap_total, cost_op_total)

# def calc_cost_decentralized():
#     """
#     Calculation for decentralized energy supply
#     :return:
#     """



if __name__ == '__main__':

    scenarios = []
    # scenarios.append({'type': ['decentralized'], 'base': ['hp_air'], 'peak': ['boiler']})
    scenarios.append({'type': ['decentralized'], 'base': ['hp_air'], 'peak': ['elHeater']})
    scenarios.append({'type': ['centralized'], 'base': ['chp'], 'peak': ['boiler']})
    # scenarios.append({'type': ['centralized', 'decentralized'], 'base': ['boiler'], 'peak': []})

    #scenarios.append({'type': ['decentralized'], 'base': ['chp'], 'peak': ['boiler']})


    #scenarios.append({'type': ['centralized', 'decentralized'], 'base': ['hp_geo'], 'peak': ['boiler']})
    # scenarios.append({'type': ['centralized', 'decentralized'], 'base': ['hp_geo'], 'peak': ['elHeater']})

    #Choose example city_object
    ex_city = 1

    this_path = os.path.dirname(os.path.abspath(__file__))
    #  Run program

    #city_f_name = 'aachen_kronenberg_3_mfh_ref_1.pkl'
    city_f_name = 'ex_city_7_geb_mixed.pkl'
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
        city_name = 'output_(' + str(i+1) + ')_' + city_f_name
        path_output = os.path.join(this_path, 'output', city_name)
        pickle.dump(cit, open(path_output, mode='wb'))
        citvis.plot_city_district(city=cit, plot_lhn=True, plot_deg=True,
                                  plot_esys=True)
    '''