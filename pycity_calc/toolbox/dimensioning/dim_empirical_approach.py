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
import pycity.classes.supply.ThermalEnergyStorage as ThermalEnergyStorage

sc0 = {'type':['centralized','decentralized'],'base':['hp_geo'],'peak':['boiler']}
sc1 = {'type':['centralized','decentralized'],'base':['hp_air'],'peak':['boiler']}
sc2 = {'type':['centralized','decentralized'],'base':[],'peak':['boiler']}
sc3 = {'type':['centralized','decentralized'],'base':['chp'],'peak':['boiler']}
sc4 = {'type':['centralized','decentralized'],'base':['solar'],'peak':['boiler']}
sc5 = {'type':['centralized','decentralized'],'base':['hp_geo'],'peak':[]}


all_scenarios = [sc0, sc1, sc2, sc3, sc4, sc5]



def run_approach(city):

    solutions = [] #Liste aller möglichen dimensionierten Szenarien (inklusive Kosten und Emissionen)

    building_con = True
    heating_net = True
    geothermal = True

    # building_con, heating_net, geothermal = additional_information()

#----------------------- Abschätzung ob zentral/dezentral versorgt werden sollte ----------------------------------

    # Energiekennwert des Quartiers (Keine Unterscheidung der Gebäude - nur Betrachtung als Gesamtes zur Abschätzung)
    th_total = city.get_annual_space_heating_demand() + city.get_annual_dhw_demand()

    area_total = 0
    for house in city.node.values():
        area_total += house['entity'].get_net_floor_area_of_building() #sum area of buildings
    ekw = th_total/area_total #in kWh/(m2*a)


    district_type = get_city_type(city)

    dhn_elig = get_eligibility_dhn(district_type, ekw, heating_net, building_con)

    print('Eligibility: ', dhn_elig)
    print('Ekw = ', ekw)

#------------------------------------ Dimensionierung der Anlagen -------------------------------------------------

    if dhn_elig >= 3:
        print('District Heating eligible!')
        for scenario in all_scenarios:
            if 'centralized' in scenario['type']:
                if approve_scenario(city, scenario, geothermal):
                    solutions.append(dim_centralized(deepcopy(city),scenario))




    elif dhn_elig < 3:
        print('District Heating not eligible!')
        # for scenario in all_scenarios:
        #     if 'decentralized' in scenario['type']:
        #         if approve_scenario(city, scenario, geothermal):
        #             solutions.append(dim_decentralized(city,scenario))

    else:
        print('District Heating solutions might be eligible...')
        # for scenario in all_scenarios:
        #     if approve_scenario(city, scenario, geothermal):
        #         if 'centralized' in scenario['type']:
        #             print('dim_centralized mit', scenario)
        #             solutions.append(dim_centralized(city,scenario))
        #         if 'decentralized' in scenario['type']:
        #             print('dim_decentralized mit', scenario)
        #             solutions.append(dim_decentralized(city,scenario))





def get_building_age(city): #alternativ immer exaktes Alter abfragen. Wie sähe ein Neubau aus? build_year = 2017?
    for house in city.node.values():
        if house['entity'].build_year >= 2009: # abhängig von Inkrafttreten des EEWärmeG (01.01.2009)
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
            print('small district')
            return 'small'
        else:
            print('medium sized district')
            return 'medium'
    elif num_buildings >= 5 and num_buildings < 15:
        if density_index < 3:
            print('small district')
            return 'small'
        elif density_index >= 3 and density_index <= 7:
            print('medium sized district')
            return 'medium'
        elif density_index > 7:
            print('big (city) district')
            return 'big'
    else:
        if density_index < 5:
            print('medium sized district')
            return 'medium'
        else:
            print('considered a big (city) district')
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
    if 'solar' in scenario['base']:
        pv_area = 0
        for building in city.node.values():
            pv_area += building['entity'].roof_usabl_pv_area
        if pv_area == 0:
            print('No usable area for solar available.')
            return False

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


def choose_device(dev_type, q_ideal):
    # Source: BHKW-Kenndaten 2014, S.26
    chp_list = {'vai1':[0.263, 0.658, 1000, 2500], 'vai2':[0.25, 0.667, 3000, 8000], 'vai3':[0.247,0.658,4700,12500],
                'vie':[0.27, 0.671, 6000, 14900], 'rmb':[0.263, 0.657, 7200, 18000]} # [eta_el, eta_th, p_nom, q_nom]

    if dev_type == 'chp':
        specs = [0, 0, 0, 0]
        for dev in chp_list.values():
            eta_th = dev[1]
            q_nom = dev[3]
            if abs(q_nom*eta_th-q_ideal) < abs(specs[3]*eta_th-q_ideal):       # q_nom * eta?!
                specs = dev[:]
    return specs


def dim_centralized(city, scenario):
    '''
    Set sizes of devices in scenario
    :param scenario:
    :return: scenario with sizes of devices - in welcher form? city_object
    '''

    [el_curve, th_curve] = city.get_power_curves(current_values=False)
    th_LDC = get_LDC(th_curve)
    eta_transmission = 0.9  # richtigen Faktor suchen

    building_age = get_building_age(city)
    if building_age == 'new':
        print('Check if requirements of EEWärmeG are fulfilled!')

    bes = BES.BES(city.environment)

    q_base_max = []

    for device in scenario['base']:
        if device == 'chp':
            # Dimensionierungspremissen:
            # BHKW zwischen 5000 und 7000 h/a Volllast und
            # BHKW immer mit Speicher

            # Dimensionierungsstrategie: 1.Anlage bei 5500h/a mit 1/2 mehr installierter Leistung als nötig für Speicher


            q_chp = 3/2*th_LDC[5500]/eta_transmission

            [eta_el, eta_th, p_nom, q_nom] = choose_device('chp',q_chp)
            chp = CHP.CHP(city.environment, p_nom, q_nom, eta_el+eta_th)
            bes.addDevice(chp)

            # Dimensionierung nach Krimmling "Energieeffiziente Nahwärmesysteme", S.127 - Faustformel: BHKW-Leistung zwischen 10% und 20% der Maximallast
            # q_borders = [min(th_LDC, key=lambda x:abs(x-0.1*max(th_LDC))), min(th_LDC, key=lambda x:abs(x-0.2*max(th_LDC)))] #gibt die Leistungsgrenzen nach Faustformel aus
            # t_borders = [th_LDC.index(q_borders[0]), th_LDC.index(q_borders[1])] #gibt die Volllaststunden für die errechneten Leistungen aus
            # print('BHKW mit Leistung zwischen ', q_borders)
            # print('Betriebszeiten zwischen ', t_borders)

            if 'boiler' in scenario['peak']:
                q_boiler = max(th_LDC) - q_nom
                boiler = Boiler.Boiler(city.environment, q_boiler, 0.8)
                bes.addDevice(boiler)

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

    result = {}
    # get thermal and electrical demand curves (only available for sanitation)



    print('dim_decentralized clone of centralized... not working correctly')





if __name__ == '__main__':

    this_path = os.path.dirname(os.path.abspath(__file__))

    city_f_name = 'aachen_kronenberg_3_mfh_ref_1.pkl'

    city_path = os.path.join(this_path, 'input', city_f_name)

    #  Run program
    city = pickle.load(open(city_path, mode='rb'))
    #city = pickle.load(open('/Users/jules/PycharmProjects/Masterarbeit/Beispielquartier/aachen_kronenberg_3_mfh_ref_1.pkl', mode='rb'))
    print('District: Aachen Kronenberg')

    run_approach(city)