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
import pycity_calc.cities.city as City
from prettytable import PrettyTable

sc0 = {'type':['centralized','decentralized'],'base':['hp_geo'],'peak':['boiler']}
sc1 = {'type':['centralized','decentralized'],'base':['hp_air'],'peak':['boiler']}
sc2 = {'type':['centralized','decentralized'],'base':[],'peak':['boiler']}
sc3 = {'type':['centralized','decentralized'],'base':['chp'],'peak':['boiler']}
sc4 = {'type':['centralized','decentralized'],'base':['solar'],'peak':['boiler']}
sc5 = {'type':['centralized','decentralized'],'base':['hp_geo'],'peak':[]}


all_scenarios = [sc0, sc1, sc2, sc3, sc4, sc5]



def run_approach(city):

    solutions = [] #Liste aller möglichen dimensionierten Szenarien (inklusive Kosten und Emissionen)

    building_age = get_building_age(city)
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
                    solutions.append(dim_centralized(city,scenario))
        print('\n##### Centralized #####')
        t = PrettyTable(['Scenario', 'base', 'peak'])
        for idx, val in enumerate(solutions):
            t.add_row(['Scenario ' + str(idx), val[0], val[1]])
        print(t)

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

def get_building_age(city):
    for house in city.node.values():
        if house['entity'].build_year >= 2009: # abhängig von Inkrafttreten des EEWärmeG (01.01.2009)
            print('New buildings')
            return 'new'
    print('No new buildings')
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


def dim_centralized(city, scenario):
    '''
    Set sizes of devices in scenario
    :param scenario:
    :return: scenario with sizes of devices - in welcher form? city_object
    '''

    base = []
    peak = []
    # get thermal and electrical demand curves (only available for sanitation)
    [el_curve, th_curve] = city.get_power_curves(current_values=False)

    # Load duration curve (Jahresdauerlinie)
    th_LDC = get_LDC(th_curve)

    q_base_max = []

    for device in scenario['base']:
        if device == 'chp':
            # Dimensionierungspremissen:
            # BHKW zwischen 5000 und 7000 h/a Volllast und
            # BHKW immer mit Speicher

            # Dimensionierungsstrategie: 1.Anlage bei 5500h/a mit 1/2 mehr installierter Leistung als nötig für Speicher
            q_base_max.append(3/2*th_LDC[5500])
            base.append('CHP: ' + str(round(q_base_max[-1]/1000)) +'kW (' + str(round(q_base_max[-1]/max(th_curve)*100)) + '%)')

            # Dimensionierung nach Krimmling "Energieeffiziente Nahwärmesysteme", S.127 - Faustformel: BHKW-Leistung zwischen 10% und 20% der Maximallast
            # q_borders = [min(th_LDC, key=lambda x:abs(x-0.1*max(th_LDC))), min(th_LDC, key=lambda x:abs(x-0.2*max(th_LDC)))] #gibt die Leistungsgrenzen nach Faustformel aus
            # t_borders = [th_LDC.index(q_borders[0]), th_LDC.index(q_borders[1])] #gibt die Volllaststunden für die errechneten Leistungen aus
            # print('BHKW mit Leistung zwischen ', q_borders)
            # print('Betriebszeiten zwischen ', t_borders)



        elif device == 'solar': # Regeln für Dimensionierung einführen!
            pv_area = 0
            for building in city.node.values():
                pv_area += building['entity'].roof_usabl_pv_area
            base.append('Solarth.: ' + str(round(pv_area)) + 'm²')

        elif device == 'hp_geo':
            base.append('HP_geo: ***')

        elif device == 'hp_air':
            base.append('HP air: ***')

    q_peak_max = []
    for device in scenario['peak']:
        if device == 'boiler':
            q_peak_max.append(max(th_LDC) - sum(q_base_max))
            peak.append('Boiler: ' + str(round(q_peak_max[-1]/1000)) + 'kW (' + str(round(q_peak_max[-1]/max(th_curve)*100)) + '%)')
    return [base, peak]



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