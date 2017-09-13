"""
Tool for the dimensioning of heating devices and district heating networks in city districts, based on approaches
as being common in the industry.
Every dimensioned district complies with current legal requirements.

"""
#  Todo: English comments

import os
import pickle
import numpy as np
from copy import deepcopy
import xlrd
import math

#import pycity_calc.cities.city as City
import networkx as nx

import pycity_base.classes.supply.BES as BES
import pycity_base.classes.supply.Boiler as Boiler
import pycity_base.classes.supply.CHP as CHP
import pycity_base.classes.supply.HeatPump as HP
# import pycity_calc.energysystems.heatPumpSimple as HP
#  TOdo: use heatpumpsimple of pycity_calc

import pycity_base.classes.supply.ElectricalHeater as ElectricalHeater
import pycity_base.classes.supply.Inverter as Inverter
import pycity_base.classes.supply.PV as PV
import pycity_calc.energysystems.thermalEnergyStorage as TES
import pycity_base.classes.demand.SpaceHeating as SpaceHeating
import pycity_calc.toolbox.networks.network_ops as NW
import pycity_calc.toolbox.dimensioning.dim_networks as dimnet

import pycity_calc.economic.energy_sys_cost.boiler_cost as boiler_cost
import pycity_calc.economic.energy_sys_cost.chp_cost as chp_cost
import pycity_calc.economic.energy_sys_cost.eh_cost as eh_cost
import pycity_calc.economic.energy_sys_cost.hp_cost as hp_cost
import pycity_calc.economic.energy_sys_cost.lhn_cost as lhn_cost
import pycity_calc.economic.energy_sys_cost.tes_cost as tes_cost



def run_approach(city,scenarios,building_con=True,heating_net=True, geothermal=True):
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

    # Change SpaceHeatingDemand of apartments to method 1 (SLP)
    for n in city.nodelist_building:
        b = city.node[n]['entity']
        spec_th_dem = b.get_annual_space_heat_demand()/b.get_net_floor_area_of_building()
        for ap in b.apartments:
            if ap.demandSpaceheating.method != 1:
                ap.demandSpaceheating = SpaceHeating.SpaceHeating(city.environment,
                                           method=1,  # Standard load profile
                                           livingArea=ap.net_floor_area,
                                           specificDemand=spec_th_dem)


#----------------------- Check Eligibility for District Heating Network ----------------------------------

    # Energiekennwert des Quartiers (Keine Unterscheidung der Gebäude - nur Betrachtung als Gesamtes zur Abschätzung)
    th_total = city.get_annual_space_heating_demand() + city.get_annual_dhw_demand()

    area_total = 0
    for n in city.nodelist_building:
        area_total += city.node[n]['entity'].get_net_floor_area_of_building() #sum area of buildings
    ekw = th_total/area_total #in kWh/(m2*a)


    district_type = get_city_type(city)

    dhn_elig = get_eligibility_dhn(district_type, ekw, heating_net, building_con)

#------------------------------------ Dimensionierung der Anlagen -------------------------------------------------

    if dhn_elig >= 3:
        print('District Heating eligible!')
        for scenario in scenarios:
            print('\n---------- Scenario Centralized '+ str(scenarios.index(scenario)),'-----------')
            if 'centralized' in scenario['type']:
                if approve_scenario(city, scenario, geothermal):
                    result = dim_centralized(deepcopy(city),scenario)
                    solutions.append(result)


    elif dhn_elig < 3:
        print('District Heating not eligible!')
    #     for scenario in scenarios:
    #         if 'decentralized' in scenario['type']:
    #             if approve_scenario(city, scenario, geothermal):
    #                 solutions.append(dim_decentralized(deepcopy(city),scenario))
    #
    # else:
    #     print('District Heating solutions might be eligible...')
    #     for scenario in scenarios:
    #         if approve_scenario(city, scenario, geothermal):
    #             if 'centralized' in scenario['type']:
    #                 solutions.append(dim_centralized(deepcopy(city),scenario))
    #             if 'decentralized' in scenario['type']:
    #                 solutions.append(dim_decentralized(deepcopy(city),scenario))

    return solutions



def get_building_age(city): #alternativ immer exaktes Alter abfragen. Wie sähe ein Neubau aus? build_year = 2017?
    """
    Evaluates the age of a building in regards to the EEWärmeG
    :param city: standard city_object
    :return: string 'new' or 'old'
    """
    for building_node in city.nodelist_building:
        if city.node[building_node]['entity'].build_year >= 2009: # abhängig von Inkrafttreten des EEWärmeG (01.01.2009)
            return 'new'
    return 'old'


def get_city_type(city):
    """

    :param city:
    :return:
    """
    #  Todo: building.net_floor_area --> Relate to energy
    #  n1 and n2 --> calc_node_distance(graph, node_1, node_2)
    #  get_min_span_tree_for_x_y_positions(city, nodelist)
    #  --> Relate to energy demand

    # dimnet.add_lhn_to_city(city, city.nodelist_building, temp_vl=90,
    #                        temp_rl=50, c_p=4186, rho=1000,
    #                        use_street_network=True, network_type='heating',
    #                        plot_stepwise=False)

    b_graph = nx.Graph()
    for bn in city.nodelist_building:
        b_graph.add_node(bn, position=city.node[bn]['position'])
    min_st = NW.get_min_span_tree(b_graph,city.nodelist_building)
    print(min_st)


    num_buildings = len(city.nodelist_building)
    num_apartments = 0
    for building_node in city.nodelist_building:
        num_apartments += len(city.node[building_node]['entity'].apartments)
    density_index = num_apartments/num_buildings

    if num_buildings < 5:
        if density_index < 5:
            print('Small District')
            return 'small'
        else:
            print('Medium Sized District')
            return 'medium'
    elif num_buildings >= 5 and num_buildings < 15:
        if density_index < 3:
            print('Small District')
            return 'small'
        elif density_index >= 3 and density_index <= 7:
            print('Medium Sized District')
            return 'medium'
        elif density_index > 7:
            print('Big (city) District')
            return 'big'
    else:
        if density_index < 5:
            print('Medium Sized District')
            return 'medium'
        else:
            print('Big (city) District')
            return 'big'


# User input for more specifications
def additional_information():

    print('Please clarify some facts about the district...')

     # Geothermienutzung möglich?
    user_input = input('Is use of geothermal probes for heat pumps possible? (y/n): ')
    while user_input not in {'y', 'n', 'yes', 'no'}:
        user_input = input('Wrong input! Try again... (y/n): ')
    if user_input in {'y', 'yes'}:
        geothermal = True
    else:
        geothermal = False

    # Check ob Nahwärmenetz vorhanden oder Bau notwendig - gibt es die Info in city_object?
    user_input = input('Local heating network already available? (y/n): ')
    while user_input not in {'y','n','yes','no'}:
        user_input = input('Wrong input! Try again... (y/n): ')
    if user_input in {'y','yes'}:
        heating_net = True
    else:
        heating_net = False

    # Falls vorhanden Check ob Anschluss an Gebäude vorhanden - gibt es die Info in city_object?
    user_input = input('Buildings already connected to local heating network? (y/n): ')
    while user_input not in {'y', 'n', 'yes', 'no'}:
        user_input = input('Wrong input! Try again... (y/n): ')
    if user_input in {'y', 'yes'}:
        building_con = True
    else:
        building_con = False

    return building_con, heating_net, geothermal


def approve_scenario(city, scenario, geothermal):
    '''
    Check if scenario is suitable for city
    :param city: standard city_object
    :param scenario:
    :return: True/False
    '''

    if 'hp_geo' in scenario['base'] and not geothermal:
        return False
    return True


def get_eligibility_dhn(district_type, ekw, heating_net=False, building_con=False):
    '''

    :param district_type: big/medium/small
    :param ekw: Energiekennwert in kWh/m²a
    :param heating_net: District heating network already in place (True/False)
    :param building_con: Building connection to dhn already installed (True/False)
    :return: elig_val = value of eligibility for usage of district heating: 1(very bad) - 5(very good)
    '''
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


def get_t_demand_list(temp_curve, th_curve):
    '''
    Sorts thermal energy demand based on values of ambient temperatures.

    :param temp_curve: curve of ambient temperatures
    :param th_curve: curve of thermal energy demand
    :return: thermal energy curve sorted based on ambient temperature values
    '''
    return [th_demand for _, th_demand in sorted(zip(temp_curve, th_curve))]


def choose_device(dev_type, q_ideal):
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
            if abs(q_nom*eta_th-q_ideal) < abs(specs[3]*eta_th-q_ideal):    # muss hier eta nicht raus?!
                specs = dev[:]
    elif dev_type == 'hp':
        this_path = os.path.dirname(os.path.abspath(__file__))
        hp_data_path = os.path.join(this_path, 'input', 'heat_pumps.xlsx')
        heatpumpData = xlrd.open_workbook(hp_data_path)

        lower_activation_limit = 0.5

        # TODO: Auswahl der Wärmepumpen anpassen (Gespräch mit Markus - Wirtschaftlichkeitsbetrachtung)
        # bis zu 50% des maximalen Wärmebedarfs, ca. 60% der aufzubringenden Jahreswärmemenge (Quelle: Springer - Wärme&Kälteversorgungsanlagen, S.68)

        # TODO: (Gas-)Motorwärmepumpen statt Strom!

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


def dim_centralized(city, scenario):
    '''
    Set sizes of devices in scenario
    :param scenario:
    :return: scenario with sizes of devices - in welcher form? city_object
    '''
    # Abstand zwischen Häusern und Wärmezentrale herausfinden
    #

    # TODO: Netzverluste korrekt integrieren (-> Wolff & Jagnow S.20)
    eta_transmission = 0.9  # richtigen Faktor suchen
    [el_curve, th_c] = city.get_power_curves(current_values=False)
    th_curve = th_c/eta_transmission
    th_LDC = get_LDC(th_curve)
    q_total = np.sum(th_curve)
    people_total = 0
    area_total = 0
    for b_node in city.nodelist_building:
        building = city.node[b_node]['entity']
        area_total += building.net_floor_area
        for ap in building.apartments:
            people_total += ap.occupancy.number_occupants

    # Aufwandszahlen und PEF nach DIN V 4701-10, Tabelle C.3-4b, ff.
    eg_enev = {'boiler': {100: 1.08, 150: 1.07, 200: 1.07, 300: 1.06, 500: 1.05, 750: 1.05, 1000: 1.05, 1500: 1.04,
                    2500: 1.04, 5000: 1.03, 10000: 1.03}, 'hp_air': 0.37, 'hp_geo': 0.27, 'elHeater': 1}
    heg_enev = {'distribution': {100: 3.52, 150: 2.4, 200: 1.88, 300: 1.39, 500: 1.01, 750: 0.83, 1000: 0.74, 1500: 0.65,
                    2500: 0.58, 5000: 0.53, 10000: 0.5}, # Werte für geregelte Pumpen, integrierte Heizflächen
                'storage': {100: 0.63, 150: 0.43, 200: 0.34, 300: 0.24, 500: 0.16, 750: 0.12, 1000: 0.1, 1500: 0.08,
                    2500: 0.07, 5000: 0.06, 10000: 0.05},
                'boiler': {100: 0.79, 150: 0.66, 200: 0.58, 300: 0.48, 500: 0.38, 750: 0.31, 1000: 0.27, 1500: 0.23,
                    2500: 0.18, 5000: 0.13, 10000: 0.09}, 'hp_geo': 1.9 / (area_total ** 0.1)}
    pef_enev = {'gas': 1.1, 'el_chp_out': 2.7, 'el_in': 1.8}  # el_chp_out = Verdrängungsstrommix für KWK
    area_enev = 0
    for a in eg_enev['boiler'].keys():
        if a > area_total:
            area_enev = a
            break
    else:
        area_enev = 10000

    heg = []
    qPEF = []

    bes = BES.BES(city.environment)


    for device in scenario['base']:
        if device == 'chp':
            chp_flh = 7000 # best possible full-load-hours (not actual flh - just for dimensioning)
            q_chp = th_LDC[chp_flh]
            [eta_el, eta_th, p_nom, q_nom] = choose_device('chp', q_chp)
            (t_ann_op, t_x) = get_chp_ann_op_time(q_nom, th_LDC)  # (annual operation time, full load hours)

            bafa = False
            while not bafa:
                # Auslegung auf BAFA Förderung (60% Deckungsanteil aus KWK)
                if t_ann_op >= 6000 and t_x >= 5000 and q_nom*t_ann_op/q_total > 0.6: # Auslegung nur gültig, falls Bedingungen für aot und flh erfüllt sind
                    print('CHP: BAFA Förderung möglich! Gesamtdeckungsanteil: '+ str(round(q_nom*t_ann_op*100/q_total,2)) + '%')
                    bafa = True
                else:
                    chp_flh -= 20
                    if chp_flh >= 5000:
                        q_chp = th_LDC[chp_flh]
                        [eta_el, eta_th, p_nom, q_nom] = choose_device('chp', q_chp)
                        (t_ann_op, t_x) = get_chp_ann_op_time(q_nom,
                                                              th_LDC)  # (Jahreslaufzeit, Volllaststunden)
                    else:
                        bafa = False
                        break

            # Alternative Auslegung falls BAFA-Förderung nicht möglich
            if not bafa:
                chp_flh = 5000
                t_x = 0
                t_ann_op = 0
                while t_ann_op < 6000 or t_x < 5000:
                    chp_flh += 20
                    q_chp = th_LDC[chp_flh]
                    [eta_el, eta_th, p_nom, q_nom] = choose_device('chp', q_chp)
                    (t_ann_op, t_x) = get_chp_ann_op_time(q_nom, th_LDC)  # (Jahreslaufzeit, Volllaststunden)
                    if chp_flh > 7500:
                        print('CHP: Fehler bei alternativer Auslegung')
                        break
                if q_nom/max(th_LDC) < 0.1:
                    print('CHP ungeeignet für Szenario.')
                    [eta_el, eta_th, p_nom, q_nom] = [0,0,0,0]
                else:
                    print('CHP: BAFA Förderung nicht möglich! Gesamtdeckungsanteil: '+str(q_nom * t_ann_op * 100 / q_total)+'%')


            # Check ob EEWärmeG erfüllt wird. Ansonsten gesetzeskonforme Dimensionierung.
            if get_building_age(city) == 'new':
                print('EEWärmeG beachten!')
                eewg = False
                count = 0
                while not eewg:
                    ee_ratio = q_nom*t_ann_op/q_total
                    if ee_ratio > 0.5:
                        #PEE berechnen
                        refeta_th = 0.85  # th. Referenzwirkungsgrad für Anlagen vor 2016, Dampf, Erdgas
                        refeta_el = 0.525  # el. Referenzwirkungsgrad für Anlagen zwischen 2012 und 2015, Erdgas
                        # Primärenergieeinsparung (PEE) in % nach Richtlinie 2012/27/EU
                        pee = (1 - 1 / ((eta_th / refeta_th) + (eta_el / refeta_el))) * 100
                        if p_nom >= 1000000:
                            if pee >= 10:
                                print('Anlage (>=1MW) ist hocheffizient -> EEWärmeG erfüllt.')
                                eewg = True
                                break
                        else:
                            if pee > 0:
                                print('Anlage (<1MW) ist hocheffizient -> EEWärmeG erfüllt.')
                                eewg = True
                                break
                        if ee_ratio >= 1:
                            print('EEWärmeG nicht erfüllt: Unrealistische Werte! (Q_chp >= Q_total)')
                            break

                    q_chp = 0.5*q_total/8760+count*q_total/(8760*100) #Mindestwert 50% Deckung + 1% der Gesamtleistung je Durchlauf
                    [eta_el, eta_th, p_nom, q_nom] = choose_device('chp', q_chp)
                    (t_ann_op, t_x) = get_chp_ann_op_time(q_nom, th_LDC)  # (Jahreslaufzeit, Volllaststunden)
                    count += 1
            else:
                print('EEWärmeG muss aufgrund des Gebäudealters nicht beachtet werden.')
                eewg = True

            chp = CHP.CHP(city.environment, p_nom, q_nom, eta_el+eta_th)
            bes.addDevice(chp)
            print('Added CHP: Q_nom = ' + str(q_nom / 1000) + ' kW (' + str(
                round(q_nom * 100 / max(th_curve), 2)) + '% of Q_max) ->', t_x, 'full-load hours.')

            # PEF und qPEF für EnEV berechnen
            q_chp_ann = t_ann_op*q_nom/eta_th # Endenergiemenge des Brennstoffs vor der Verbrennung in KWK-Anlage
            w_el_chp_out = q_chp_ann * eta_el # Mit KWK-Anlage produzierte, ausgespeiste Strommenge
            qPEF.append(pef_enev['gas'] * q_chp_ann - pef_enev['el_chp_out'] * w_el_chp_out) # KWK-Anlage mit Erdgas betrieben?!

            # Pufferspeicher hinzufügen falls Leistung über 20% von Maximalverbrauch
            if q_nom/max(th_LDC) > 0.2:
                v_tes = q_nom/1000*60 # Förderung von Speichern für Mini-BHKW durch BAFA bei Speichergrößen über 60 l/kW_th
                if v_tes > 1600: # 1600 liter genügen für Förderung
                    v_tes = 1600 + (q_nom/1000*60-1600)*0.2 # Schätzung um auch Anlagen >30kW mit Speicher zu versorgen
                    # TODO: Wie sieht die Dimensionierung für KWK-Anlagen über 30 kW aus? Sind die 20% realistisch?
                tes = TES.thermalEnergyStorageExtended(environment=city.environment,t_init=50,capacity=v_tes)
                bes.addDevice(tes)
                print('Added Thermal Energy Storage:', v_tes,'liter ')
                heg.append(heg_enev['storage'][area_enev]*area_total)

            # Wärmeerzeuger für Spitzenlast hinzufügen
            if 'boiler' in scenario['peak']:
                q_boiler = max(th_LDC) - q_nom
                boiler = Boiler.Boiler(city.environment, q_boiler, 0.8)
                bes.addDevice(boiler)
                print('Added Boiler: Q_nom = '+str(round(q_boiler/1000,2))+' kW')
                if q_boiler >= 4000 and q_boiler < 400000:
                    print('Boiler requires CE Label. (according to 92/42/EWG)')
                qPEF.append(pef_enev['gas']*(q_total - q_nom * t_ann_op))  # EnEV für Boiler. Anteil an Wärme*PEF (eta_th mit rein?)
                heg.append(heg_enev['boiler'][area_enev]*area_total)


            if 'elHeater' in scenario['peak']:
                q_elHeater = max(th_LDC) - q_nom
                # TODO: Werte überprüfen
                elHeater = ElectricalHeater.ElectricalHeater(city.environment, q_elHeater, 0.95, 100, 0.2)
                bes.addDevice(elHeater)
                print('Added elHeater: Q_nom = ' + str(round(q_elHeater / 1000, 2)) + ' kW')
                qPEF.append(pef_enev['el'] * (q_total - q_nom * t_ann_op))

            ann_q_base = t_ann_op*q_nom/1000 # Annual produced heat with base supply in kWh
            ann_q_peak = (q_total - q_nom * t_ann_op)/1000 # Annual produced heat with peak supply in kWh


        elif device == 'hp_geo':
            print(' hp geothermie')
            # result['hp_geo'] = 1 # dummy



        elif device == 'hp_air':
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
                boiler = Boiler.Boiler(city.environment, q_boiler, 0.8)
                bes.addDevice(boiler)
                print('Added Boiler: Q_nom = ' + str(round(q_boiler / 1000, 2)) + ' kW')
                if q_boiler >= 4000 and q_boiler < 400000:
                    print('Kessel muss CE Kennzeichnung vorweisen können. (gemäß 92/42/EWG)')

                # HP- and Boiler-Data for EnEV
                cop_durchschnitt = 3 # TODO: Welcher COP wird hier verwendet? Durchschnitt?
                # TODO: Anwendung der Aufwandszahlen eg überprüfen - in dieser Weise korrekt?
                w_hp_ann = 0.83*0.37*q_total/cop_durchschnitt # Anteil HP/Boiler nach DIN V 4701-10, Tabelle C.3-4a.
                qPEF.append(pef_enev['el_in'] * w_hp_ann)
                qPEF.append(pef_enev['gas']*0.17*eg_enev['boiler'][a]*q_total/boiler.eta)
                heg.append(heg_enev['boiler'][area_enev]*area_total)
            else:
                cop_durchschnitt = 3 # TODO: Welcher COP wird hier verwendet? Durchschnitt?
                # TODO: Anwendung der Aufwandszahlen eg überprüfen - in dieser Weise korrekt?
                w_hp_ann = q_total/cop_durchschnitt # Anteil HP/Boiler nach DIN V 4701-10, Tabelle C.3-4a.
                qPEF.append(pef_enev['el_in'] * w_hp_ann)



    # Check EnEV (Produkt Erzeugeraufwandszahl und PEF <= 1,3)
    eg_nahwaerme = 1.01 # Zentralisierte Versorgung!
    pef_nahwaerme = (sum(qPEF)+sum(heg)*pef_enev['el_in'])/sum(th_curve*eta_transmission)
    if eg_nahwaerme*pef_nahwaerme <= 1.3:
        print('Energysytem according to EnEV! Factor:', round(eg_nahwaerme*pef_nahwaerme,2))
    else:
        print('Energysystem not according to EnEV! Factor:', round(eg_nahwaerme*pef_nahwaerme,2))


    # Im ersten Gebäude wird das BES installiert (-> besser in kürzester Distanz aller Gebäude)
    assert not city.node[city.nodelist_building[0]]['entity'].hasBes, ('Building 0 has already BES. Mistakes may occur!')
    city.node[city.nodelist_building[0]]['entity'].addEntity(bes)

    calc_costs(city,ann_q_base, ann_q_peak)

    return city



def dim_decentralized(city, scenario):
    '''
    Set sizes of devices in scenario
    :param scenario:
    :return: scenario with sizes of devices - in welcher form? city_object
    '''
    # TODO: Netzverluste korrigieren (siehe dim_centralized)
    eta_transmission = 0.9  # richtigen Faktor suchen

    for b_node in city.nodelist_building:
        building = city.node[b_node]['entity']
        th_curve = building.get_space_heating_power_curve() + building.get_dhw_power_curve()
        th_LDC = get_LDC(th_curve / eta_transmission)
        q_total = sum(th_curve)

        bes = BES.BES(city.environment)

        for device in scenario['base']:
            if device == 'chp':

                chp_flh = 7000  # best possible full-load-hours
                q_chp = th_LDC[chp_flh]

                [eta_el, eta_th, p_nom, q_nom] = choose_device('chp', q_chp)

                while q_nom * eta_th / max(th_curve) < 0.1:  # falls leistungsanteil kleiner als 10%
                    chp_flh -= 50
                    q_chp = th_LDC[chp_flh]
                    [eta_el, eta_th, p_nom, q_nom] = choose_device('chp', q_chp)

                if building.build_year >= 2009:
                    print('Energysystem must comply with EEWärmeG!')
                    eewg = False
                    count = 0
                    while not eewg:
                        ee_ratio = q_chp / q_total
                        if ee_ratio > 0.5:
                            # PEE berechnen
                            refeta_th = 0.85  # th. Referenzwirkungsgrad für Anlagen vor 2016, Dampf, Erdgas
                            refeta_el = 0.525  # el. Referenzwirkungsgrad für Anlagen zwischen 2012 und 2015, Erdgas
                            # Primärenergieeinsparung (PEE) in % nach Richtlinie 2012/27/EU
                            pee = (1 - 1 / ((eta_th / refeta_th) + (eta_el / refeta_el))) * 100
                            if p_nom >= 1000000:
                                if pee >= 10:
                                    print('EEWärmeG obeyed. (>=1MW)')
                                    eewg = True
                                    break
                            else:
                                if pee > 0:
                                    print('EEWärmeG obeyed. (<1MW)')
                                    eewg = True
                                    break
                            if q_chp / q_total > 0.9:
                                print('EEWärmeG not obeyed: Unrealistic values! (Q_chp > 90% of Q_total)')
                                break
                        q_chp = math.ceil(
                            0.5 * q_total + count * q_total / 100)  # Mindestwert 50% Deckung + 1% der Gesamtleistung je Durchlauf
                        [eta_el, eta_th, p_nom, q_nom] = choose_device('chp', q_chp)
                        count += 1
                else:
                    print('Due to building age, the EEWärmeG does not need to be considered.')
                    eewg = True

                enev = False

                chp = CHP.CHP(city.environment, p_nom, q_nom, eta_el + eta_th)
                bes.addDevice(chp)
                print('CHP with Q_nom =', q_nom, ' W (', round(q_nom * 100 / max(th_curve),2), '%) ->', chp_flh, 'full-load hours.' )

                if 'boiler' in scenario['peak']:
                    q_boiler = max(th_LDC) - q_nom
                    boiler = Boiler.Boiler(city.environment, q_boiler, 0.8)
                    bes.addDevice(boiler)

        # TODO: Wärmepumpe und andere Anlagen implementieren!

            if device == 'hp_air':
                #Monovalenter Betrieb von Luft/Wasser-Wärmepumpen nach Dimplex Anleitung (Planungshandbuch S.16)
                # Deckung durch WP bis -5°C Außentemperatur. Danach elHeater.
                # -> Deckung von 2% durch 2.Wärmeerzeuger (elHeater) nach DIN 4701:10 (siehe Dimplex PHB)
                print('dezentral wp')

        assert not city.node[b_node]['entity'].hasBes, ('Building ', b_node ,' has already BES. Mistakes may occur!')
        city.node[b_node]['entity'].addEntity(bes)

    return city




def calc_costs(city, q_base, q_peak, i=0.03, price_gas=0.0661):
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

    :param city: pycity_calc city_object
    :param q_base: amount of thermal energy provided by base supply in kWh
    :param q_peak: amount of thermal energy provided by peak supply in kWh
    :param i: interest rate
    :param price_gas: price of gas
    :return: tuple of total capital and total operational costs in Euro
    """

    # Kostenfunktion in Wolff 2011, Kapitel 6.3.6
    # Betriebs- und Energiekosten in Kapitel 6.3.7
    # Bewertungskriterien, Masterarbeit Hendrik Kapitel 2.3
    b_with_bes = []
    for bn in city.nodelist_building:
        if city.node[bn]['entity'].hasBes:
            b_with_bes.append(city.node[bn]['entity'])
    if len(b_with_bes) == 1:
        d_type = 'c'

        print('Costs for lhn missing (not implemented)')
    elif len(b_with_bes) > 1:
        d_type = 'd'
    else:
        raise Exception('No BES installed!')

    # ------- Calculate Costs --------
    cost_cap = [] # capital costs
    cost_op = [] # operational costs

    for b in b_with_bes:
        bes = b.bes
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
            t = 15  # nach VDI 2067
            i_0 = chp_cost.calc_spec_cost_chp(bes.chp.pNominal, method='asue2015', with_inst=True,
                                              use_el_input=True, q_th_nom=None)
            a = i * (1 + i) ** t / ((1 + i) ** t - 1)
            cost_cap.append(i_0 * a)

            eta_th = bes.chp.omega/(1+bes.chp.sigma)
            cost_op.append(q_base/eta_th*price_gas)

            if bes.hasBoiler:
                t = 18  # nach VDI 2067
                i_0 = boiler_cost.calc_spec_cost_boiler(bes.boiler.qNominal,
                                                        method='viess2013') * bes.boiler.qNominal
                a = i * (1 + i) ** t / ((1 + i) ** t - 1)
                cost_cap.append(i_0 * a)
                cost_op.append(q_peak/bes.boiler.eta*price_gas)


        if bes.hasTes:
            t = 20 # nach VDI 2067
            volume = bes.tes.capacity/bes.tes.rho
            i_0 = tes_cost.calc_spec_cost_tes(volume, method='spieker') * volume
            a = i * (1 + i)** t / ((1 + i)**t - 1)
            cost_cap.append(i_0*a)

    cost_cap_total = round(sum(cost_cap),2)
    cost_op_total = round(sum(cost_op),2)

    print('Capital Cost:', cost_cap_total)
    print('Operational Cost:', cost_op_total)

    return (cost_cap_total, cost_op_total)



if __name__ == '__main__':

    scenarios = []
    #scenarios.append({'type': ['centralized', 'decentralized'], 'base': [], 'peak': ['boiler']})
    #scenarios.append({'type': ['decentralized'], 'base': ['hp_air'], 'peak': []})
    #scenarios.append({'type': ['centralized', 'decentralized'], 'base': ['hp_air'], 'peak': ['boiler']})
    #scenarios.append({'type': ['centralized', 'decentralized'], 'base': ['hp_air'], 'peak': ['elHeater']})
    scenarios.append({'type': ['centralized', 'decentralized'], 'base': ['chp'], 'peak': ['boiler']})
    #scenarios.append({'type': ['centralized', 'decentralized'], 'base': ['hp_geo'], 'peak': ['boiler']})
    # scenarios.append({'type': ['centralized', 'decentralized'], 'base': ['hp_geo'], 'peak': ['elHeater']})

    #Choose example city_object
    ex_city = 1

    this_path = os.path.dirname(os.path.abspath(__file__))
    #  Run program
    if ex_city == 1:
        city_f_name = 'aachen_kronenberg_3_mfh_ref_1.pkl'
        city_path = os.path.join(this_path, 'input', city_f_name)
        city = pickle.load(open(city_path, mode='rb'))
        #city = pickle.load(open('/Users/jules/PycharmProjects/Masterarbeit/Beispielquartier/aachen_kronenberg_3_mfh_ref_1.pkl', mode='rb'))
        print('District: Aachen Kronenberg')

    elif ex_city == 2:
        city_f_name = 'wm_res_east_7_richardsonpy.pkl'
        city_path = os.path.join(this_path, 'input', city_f_name)
        city = pickle.load(open(city_path, mode='rb'))
        print("District: 7 MFH, Bottrop")

    list_city_object = run_approach(city,scenarios)

    '''
    # ---- Output in pickle files -----
    
    import pycity_calc.visualization.city_visual as citvis

    for i in range(len(list_city_object)):
        cit = list_city_object[i]
        city_name = 'city_out_' + str(i+1) + '.pkl'
        path_output = os.path.join(this_path, 'output', city_name)
        pickle.dump(cit, open(path_output, mode='wb'))
        citvis.plot_city_district(city=cit, plot_lhn=True, plot_deg=True,
                                  plot_esys=True)
    '''