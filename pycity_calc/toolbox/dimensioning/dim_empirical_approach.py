"""
1. If __name__ == ‚__main__‘: Durchlauf des Programms
2. Beispielstadt laden
3.


Passende Szenarien anhand der Randbedingungen auswählen und in qual_scenarios speichern: select_szenarios()
4. Alle qual_scenarios durchlaufen und abhängig ob zentral/dezentral dimensionieren:
        dim_centralized(city, scenario)
        dim_decentralized(city, scenario) 
5. Für jedes Szenario in dim_de/centralized():
        Dimensionierung der Anlagen in allen möglichen Szenarien nach gesetzlichen Bedingungen.
        Für centralized: Alle Lastgänge addieren -> daraus maximale Last errechnen
        Für decentralized: Einzelne Lastgänge nutzen

"""

import os
import pickle
import numpy as np
from copy import deepcopy
import xlrd
import math

import matplotlib.pyplot as plt
import pycity_calc.cities.city as City
from prettytable import PrettyTable

import pycity.classes.supply.BES as BES
import pycity.classes.supply.Boiler as Boiler
import pycity.classes.supply.CHP as CHP
import pycity.classes.supply.HeatPump as HP
import pycity.classes.supply.ElectricalHeater as ElectricalHeater
import pycity.classes.supply.Inverter as Inverter
import pycity.classes.supply.PV as PV
import pycity_calc.energysystems.thermalEnergyStorage as TES
import pycity.classes.demand.SpaceHeating as SpaceHeating


#sc0 = {'type':['centralized','decentralized'],'base':['hp_geo'],'peak':['boiler']}
#sc1 = {'type':['centralized','decentralized'],'base':['hp_air'],'peak':['boiler']}
#sc2 = {'type':['centralized','decentralized'],'base':[],'peak':['boiler']}
#sc3 = {'type':['centralized','decentralized'],'base':['chp'],'peak':['boiler']}
#sc4 = {'type':['centralized','decentralized'],'base':['hp_geo'],'peak':[]}
# sc5 = {'type':['decentralized'],'base':['hp_air'],'peak':['elHeater']} # elHeater = Heizstab

#all_scenarios = [sc0, sc1, sc2, sc3, sc4]

sc3 = {'type':['centralized','decentralized'],'base':['chp'],'peak':['boiler']}
all_scenarios = [sc3]


def run_approach(city):

    solutions = [] #Liste aller möglichen dimensionierten Szenarien (inklusive Kosten und Emissionen)

    building_con = True
    heating_net = True
    geothermal = True

    # building_con, heating_net, geothermal = additional_information()

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
        for scenario in all_scenarios:
            if 'centralized' in scenario['type']:
                if approve_scenario(city, scenario, geothermal):
                    result = dim_centralized(deepcopy(city),scenario)
                    solutions.append(result)


    elif dhn_elig < 3:
        print('District Heating not eligible!')
    #     for scenario in all_scenarios:
    #         if 'decentralized' in scenario['type']:
    #             if approve_scenario(city, scenario, geothermal):
    #                 solutions.append(dim_decentralized(deepcopy(city),scenario))
    #
    # else:
    #     print('District Heating solutions might be eligible...')
    #     for scenario in all_scenarios:
    #         if approve_scenario(city, scenario, geothermal):
    #             if 'centralized' in scenario['type']:
    #                 solutions.append(dim_centralized(deepcopy(city),scenario))
    #             if 'decentralized' in scenario['type']:
    #                 solutions.append(dim_decentralized(deepcopy(city),scenario))

    return solutions



def get_building_age(city): #alternativ immer exaktes Alter abfragen. Wie sähe ein Neubau aus? build_year = 2017?
    for building_node in city.nodelist_building:
        if city.node[building_node]['entity'].build_year >= 2009: # abhängig von Inkrafttreten des EEWärmeG (01.01.2009)
            return 'new'
    return 'old'


def get_city_type(city):
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

    return building_age, building_con, heating_net, geothermal


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
            if abs(q_nom*eta_th-q_ideal) < abs(specs[3]*eta_th-q_ideal):       # q_nom * eta?!
                specs = dev[:]
    elif dev_type == 'hp':
        # TODO: Methode schreiben die heatpumps mit charakteristica in dict speichert
        hp_dict = [{'tAmbient':0,'qNominal':0,'pNominal':0,'cop':0,'tMax':0,'l_a_l':0},{'tAmbient':0,'qNominal':0,'pNominal':0,'cop':0,'tMax':0,'l_a_l':0}]

    return specs


def get_chp_ann_op_time(eta_th, q_nom, th_LDC):

    # CHP-Jahreslaufzeitberechnung (annual operation time) nach Krimmling(2011)
    for q_m in th_LDC:
        if q_m <= q_nom * eta_th:
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
    # TODO: Netzverluste korrekt integrieren (-> Wolff & Jagnow S.20)
    # Abstand zwischen Häusern und Wärmezentrale herausfinden
    #


    eta_transmission = 0.9  # richtigen Faktor suchen
    [el_curve, th_c] = city.get_power_curves(current_values=False)
    th_curve = th_c/eta_transmission
    th_LDC = get_LDC(th_curve)
    q_total = np.sum(th_curve)

    bes = BES.BES(city.environment)


    for device in scenario['base']:
        # TODO: Devices sollten in eigene Methode ausgegliedert werden, die bei (de)zentraler Dimensionierung aufgerufen werden (quasi gleiches Vorgehen bei Dimensionierung)
        if device == 'chp':
            # Dimensionierungspremissen:
            # BHKW zwischen 5000 und 7000 h/a Volllast und
            # BHKW immer mit Speicher

            # Dimensionierungsstrategie: 1.Anlage mit 1/2 mehr installierter Leistung als nötig für Speicher

            chp_flh = 7000 #best possible full-load-hours
            q_chp = th_LDC[chp_flh]
            [eta_el, eta_th, p_nom, q_nom] = choose_device('chp', q_chp)
            (t_ann_op, t_x) = get_chp_ann_op_time(eta_th, q_nom, th_LDC)  # (Jahreslaufzeit, Volllaststunden)

            bafa = False
            while not bafa:
                # Auslegung auf BAFA Förderung (60% Deckungsanteil aus KWK)
                if t_ann_op >= 6000 and t_x >= 5000 and q_nom*eta_th*t_ann_op/q_total > 0.6: # Auslegung nur gültig, falls Bedingungen für aot und flh erfüllt sind
                    print('CHP: BAFA Förderung möglich! Gesamtdeckungsanteil: '+str(round(q_nom*eta_th*t_ann_op*100/q_total,2))+'%')
                    bafa = True
                else:
                    chp_flh -= 20
                    if chp_flh >= 5000:
                        q_chp = th_LDC[chp_flh]
                        [eta_el, eta_th, p_nom, q_nom] = choose_device('chp', q_chp)
                        (t_ann_op, t_x) = get_chp_ann_op_time(eta_th, q_nom,
                                                              th_LDC)  # (Jahreslaufzeit, Volllaststunden)
                    else:
                        print('CHP: BAFA Förderung nicht möglich!')
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
                    (t_ann_op, t_x) = get_chp_ann_op_time(eta_th, q_nom, th_LDC)  # (Jahreslaufzeit, Volllaststunden)
                    if chp_flh > 7500:
                        print('CHP: Fehler bei alternativer Auslegung')
                        break
                if q_nom*eta_th/max(th_LDC) < 0.1:
                    print('CHP ungeeignet für Szenario.')
                    [eta_el, eta_th, p_nom, q_nom] = [0,0,0,0]
                else:
                    print('CHP: BAFA Förderung nicht möglich! Gesamtdeckungsanteil: '+str(q_nom * eta_th * t_ann_op * 100 / q_total)+'%')


            # Check ob EEWärmeG erfüllt wird. Ansonsten gesetzeskonforme Dimensionierung.
            if get_building_age(city) == 'new':
                print('EEWärmeG beachten!')
                eewg = False
                count = 0
                while not eewg:
                    ee_ratio = q_nom*eta_th*t_ann_op/q_total
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
                    (t_ann_op, t_x) = get_chp_ann_op_time(eta_th, q_nom, th_LDC)  # (Jahreslaufzeit, Volllaststunden)
                    count += 1
            else:
                print('EEWärmeG muss aufgrund des Gebäudealters nicht beachtet werden.')
                eewg = True

            enev = False
            # TODO: EnEV hinzufügen



            chp = CHP.CHP(city.environment, p_nom, q_nom, eta_el+eta_th)
            bes.addDevice(chp)
            print('Added CHP: Q_nom = ' + str(q_nom/1000) + ' kW (' + str(
                round(q_nom * eta_th * 100 / max(th_curve), 2)) + '% of Q_max) ->', t_x, 'full-load hours.')


            # Pufferspeicher hinzufügen falls Leistung über 20% von Maximalverbrauch
            if q_nom*eta_th/max(th_LDC) > 0.2:
                v_tes = q_nom/1000*60 # Förderung von Speichern für Mini-BHKW durch BAFA bei Speichergrößen über 60 l/kW_th
                if v_tes > 1600: # 1600 liter genügen für Förderung
                    v_tes = 1600 + (q_nom/1000*60-1600)*0.2 # Schätzung um auch Anlagen >30kW mit Speicher zu versorgen
                    # TODO: Wie sieht die Dimensionierung für KWK-Anlagen über 30 kW aus? Sind die 20% realistisch?
                tes = TES.thermalEnergyStorageExtended(environment=city.environment,t_init=50,capacity=v_tes)
                bes.addDevice(tes)
                print('Added Thermal Energy Storage:', v_tes,'liter ')


            # Wärmeerzeuger für Spitzenlast hinzufügen
            if 'boiler' in scenario['peak']:
                q_boiler = max(th_LDC) - q_nom*eta_th
                boiler = Boiler.Boiler(city.environment, q_boiler, 0.8)
                bes.addDevice(boiler)
                print('Added Boiler: Q_nom = '+str(round(q_boiler/1000,2))+' kW')

            if 'elHeater' in scenario['peak']:
                q_elHeater = max(th_LDC) - q_nom*eta_th
                # TODO: Werte überprüfen
                elHeater = ElectricalHeater.ElectricalHeater(city.environment, q_elHeater, 0.95, 100, 0.2)
                bes.addDevice(elHeater)
                print('Added elHeater: Q_nom = ' + str(round(q_elHeater / 1000, 2)) + ' kW')



        elif device == 'solar': # Regeln für Dimensionierung einführen!
            pv_area = 0
            for building in city.node.values():
                pv_area += building['entity'].roof_usabl_pv_area
            print('Solarthermie auf ', pv_area, ' qm')
            #result['solar'] = pv_area # in m2

        elif device == 'hp_geo':
            print(' hp geothermie')
            # result['hp_geo'] = 1 # dummy



        elif device == 'hp_air':

            # TODO: sind Vor- und Rücklauftemperaturen in city_object gegeben? Sonst über Diagramm aus KVS-Klimatechnik bestimmen (Bild 1.1a, S.11)


            if max(th_curve) < 60000:
                print('Katalogauswahl Wärmepumpe!')

            else:
                if 'elHeater' in scenario['peak']:
                    print('Dimplex LA60TU auswählen + Restleistung elHeater.')
                elif scenario['peak'] is []:
                    print('Heat pumps in monovalent operation mode are not suitable for heat demand > 60 kW_th!')
                    return None
                elif 'boiler' in scenario['peak']:
                    t_demand_list = get_t_demand_list(city.environment.weather.tAmbient, th_curve)
                    cop = {-20:1.54,-15:1.73,-7:2.22,2:2.56,7:2.8,10:3.08,12:3.15,20:3.61}
























            # TODO: Speicherdimensionierung für Wärmepumpe



            # erster Teil aus py_city -> examples übernommen (Daten für Dimplex_LA60TU angepasst)

            #  Heatpump data path
            this_path = os.path.dirname(os.path.abspath(__file__))
            hp_data_path = os.path.join(this_path, 'input', 'heat_pumps.xlsx')
            heatpumpData = xlrd.open_workbook(hp_data_path)
            dimplex_LA60TU = heatpumpData.sheet_by_name("Dimplex_LA60TU")

            # Size of the worksheet
            number_rows = dimplex_LA60TU._dimnrows
            number_columns = dimplex_LA60TU._dimncols
            # Flow, ambient and max. temperatures
            tFlow = np.zeros(number_columns - 2)
            tAmbient = np.zeros(int((number_rows - 7) / 2))
            tMax = dimplex_LA60TU.cell_value(0, 1)

            firstRowCOP = number_rows - len(tAmbient)

            qNominal = np.empty((len(tAmbient), len(tFlow)))
            cop = np.empty((len(tAmbient), len(tFlow)))

            for i in range(number_columns - 2):
                tFlow[i] = dimplex_LA60TU.cell_value(3, 2 + i)

            for col in range(len(tFlow)):
                for row in range(len(tAmbient)):
                    qNominal[row, col] = dimplex_LA60TU.cell_value(int(4 + row),
                                                                   int(2 + col))
                    cop[row, col] = dimplex_LA60TU.cell_value(int(firstRowCOP + row),
                                                              int(2 + col))

            pNominal = qNominal / cop

            # Create HP
            lower_activation_limit = 0.5

            hp_air = HP.Heatpump(city.environment, tAmbient, tFlow, qNominal, pNominal, cop,
                                 tMax, lower_activation_limit)

            bes.addDevice(hp_air)

            # Details HeatPump
            t1_hp = -15  # °C
            t2_hp = 20  # °C
            q1_hp = hp_air.heat[1][2]  # W
            q2_hp = hp_air.heat[7][2]  # W

            # Leistung von HP bei niedrigster Temperatur (Annahme Wärmebedarf dort am größten)
            q_hp = (q2_hp - q1_hp) / (t2_hp - t1_hp) * (min(city.environment.weather.tAmbient) - t1_hp) + q1_hp

            if 'boiler' in scenario['peak']:
                q_boiler = max(city.get_aggr_space_h_power_curve(current_values=False)) - q_hp
                boiler = Boiler.Boiler(city.environment, q_boiler, 0.8)
                bes.addDevice(boiler)


            '''
            # Vorlauftemperaturen für Heizkörper? Fußbodenheizung?
            # check if tFlow = 60°C.
            tmax_dhw = 0
            for building in city.node.values():
                for apartment in building['entity'].apartments:
                    dhw_t = apartment.demandDomesticHotWater.tFlow
                    if dhw_t > tmax_dhw:
                        tmax_dhw = dhw_t
                        print('tMax for dhw set to ', dhw_t)

            t_min_env = min(city.environment.weather.tAmbient)
            q_max_distr = max(city.get_aggr_space_h_power_curve(current_values=False)) # W

            if tmax_dhw <= 55:
                print('LT HeatPump')

            elif tmax_dhw > 55 and dhw_t <= 65:

                # Details HeatPump
                t1_hp = -15 #°C
                t2_hp = 20 #°C
                q1_hp = 26700 #W
                q2_hp = 72000 #W
                cop1 = 1.73
                cop2 = 3.6

                result['hp_air'] = 'MT HeatPump (Dimplex LA 60TU)'


            elif tmax_dhw > 65:
                print('HT HeatPump')

            # -------- Heatpump und Heat demand plotten ---------
            # plt.plot([t_min_env, 20],
            #          [q_max_distr, 0], 'b', [t2_hp, t1_hp], [q2_hp, q1_hp], 'r')
            # plt.text(t1_hp + 2, q1_hp, 'HeatPump')
            # plt.text(t_min_env + 2, q_max_distr, 'aggregated heat demand of district')
            # plt.xlabel('Outside Temp. / °C')
            # plt.ylabel('Thermal Power / kW')
            # plt.title('Bivalenzpunkt')
            # plt.show()
            # ----------------------------------------------------

            # Geradengleichung HeatPump bei minimaler Umgebungstemperatur
            p_hp = (q2_hp - q1_hp) / (t2_hp - t1_hp) * (t_min_env - t1_hp) + q1_hp

            # Geragengleichung Wärmebedarf
            p_distr = q_max_distr

            if 'boiler' in scenario['peak']:
                result['boiler'] = p_distr - p_hp

    if scenario['base'] == [] and scenario['peak'] == ['boiler']:
        result['boiler'] = max(th_LDC)
    '''


    # Im ersten Gebäude wird das BES installiert (-> besser in kürzester Distanz aller Gebäude)
    assert not city.node[city.nodelist_building[0]]['entity'].hasBes, ('Building 0 has already BES. Mistakes may occur!')
    city.node[city.nodelist_building[0]]['entity'].addEntity(bes)


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
                # Dimensionierungspremissen:
                # BHKW zwischen 5000 und 7000 h/a Volllast und
                # BHKW immer mit Speicher

                # Dimensionierungsstrategie: 1.Anlage bei 7000h/a mit 1/2 mehr installierter Leistung als nötig für Speicher

                chp_flh = 7000  # best possible full-load-hours
                q_chp = th_LDC[chp_flh]

                [eta_el, eta_th, p_nom, q_nom] = choose_device('chp', q_chp)

                while q_nom * eta_th / max(th_curve) < 0.1:  # falls leistungsanteil kleiner als 10%
                    chp_flh -= 50
                    q_chp = th_LDC[chp_flh]
                    [eta_el, eta_th, p_nom, q_nom] = choose_device('chp', q_chp)

                if building.build_year >= 2009:
                    print('EEWärmeG beachten!')
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
                                    print('EEWärmeG erfüllt. (>=1MW)')
                                    eewg = True
                                    break
                            else:
                                if pee > 0:
                                    print('EEWärmeG erfüllt. (<1MW)')
                                    eewg = True
                                    break
                            if q_chp / q_total > 0.9:
                                print('EEWärmeG nicht erfüllt: Unrealistische Werte! (Q_chp > 90% von Q_total)')
                                break
                        q_chp = math.ceil(
                            0.5 * q_total + count * q_total / 100)  # Mindestwert 50% Deckung + 1% der Gesamtleistung je Durchlauf
                        [eta_el, eta_th, p_nom, q_nom] = choose_device('chp', q_chp)
                        count += 1
                else:
                    print('EEWärmeG muss aufgrund des Gebäudealters nicht beachtet werden.')
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

        assert not city.node[b_node]['entity'].hasBes, ('Building ', b_node ,' has already BES. Mistakes may occur!')
        city.node[b_node]['entity'].addEntity(bes)

    return city




def calc_annuity(city):
    """

    - Kosten/Annuität
        - KWK Vergünstigungen
        - Einspeisevergütung durch EEG
        - Strom- und Brennstoffkosten
        - Investitionskosten
        - sonstige Förderungen (Recherche!)
    
    :param city: 
    :return: 
    """
    print('Annuity check not implemented')



if __name__ == '__main__':

    #Choose example city_object
    ex_city = 2

    this_path = os.path.dirname(os.path.abspath(__file__))
    #  Run program
    if ex_city == 1:
        city_f_name = 'aachen_kronenberg_3_mfh_ref_1.pkl'
        city_path = os.path.join(this_path, 'input', city_f_name)
        city = pickle.load(open(city_path, mode='rb'))
        #city = pickle.load(open('/Users/jules/PycharmProjects/Masterarbeit/Beispielquartier/aachen_kronenberg_3_mfh_ref_1.pkl', mode='rb'))
        print('District: Aachen Kronenberg')
    elif ex_city == 2:
        city_f_name = 'wm_res_east_7_th_mod_el_stoch_dhw_stoch.p'
        city_path = os.path.join(this_path, 'input', city_f_name)
        city = pickle.load(open(city_path, mode='rb'))
        print("District: 7 MFH, Bottrop")

    run_approach(city)