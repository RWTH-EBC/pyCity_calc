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

import pickle
import pycity_calc.cities.city as City

#centralized
sc1 = {'type':['centralized','decentralized'],'base':['chp'],'peak':['boiler']} #kann zentral/semizentral/dezentral genutzt werden
sc2 = {'type':['centralized','decentralized'],'base':['chp', 'solar'],'peak':['boiler']}
#sc3 = {'type':['centralized'],'base':['boiler_bio'],'peak':['boiler']}
#sc4 = {'type':['centralized'],'base':['boiler_bio','chp'],'peak':['boiler']}

#decentralized
sc5 = {'type':['decentralized'],'base':[],'peak':['boiler']}
sc6 = {'type':['decentralized'],'base':['heatPump'],'peak':['boiler']}
sc7 = {'type':['decentralized'],'base':['heatPump','PV'],'peak':['boiler']}

all_scenarios = [sc1, sc2, sc5, sc6, sc7]



def run_approach(city):

    solutions = [] #Liste aller möglichen dimensionierten Szenarien (inklusive Kosten und Emissionen)

#----------------------- Abschätzung ob zentral/dezentral versorgt werden sollte ----------------------------------

    # Energiekennwert des Quartiers (Keine Unterscheidung der Gebäude - nur Betrachtung als Gesamtes zur Abschätzung)
    th_total = city.get_annual_space_heating_demand() + city.get_annual_dhw_demand()
    area_total = 0
    for house in city.node.values():
        area_total += house['entity'].get_net_floor_area_of_building()
    ekw = th_total/area_total #in kWh/(m2*a)

    # Art des Quartiers bestimmen (großes/mittleres/kleines Versorgungsgebiet)
    # Anzahl Personen in Gebiet? Höhe Gesamtverbrauch?
    # Aufteilung nach BBSR - Handlungsleitfaden zur energetischen Stadterneuerung (Infos über Grundstücksfläche benötigt um GFZ berechnen zu können)
    district_type = 'small' # -> kleines Versorgungsgebiet (Siedlung/Dorf mit überwiegend 1-/2-Familienhäusern)

    # Check ob Nahwärmenetz vorhanden oder Bau notwendig - gibt es die Info in city_object?
    heating_net = True
    # Falls vorhanden Check ob Anschluss an Gebäude vorhanden - gibt es die Info in city_object?
    building_con = True

    dhn_elig = get_eligibility_dhn(district_type, ekw, heating_net, building_con)

    print('Eligibility: ', dhn_elig)
    print('Ekw = ', ekw)

#------------------------------------ Dimensionierung der Anlagen -------------------------------------------------

    if dhn_elig > 3:
        print('District Heating eligible!')
        for scenario in all_scenarios:
            if 'centralized' in scenario['type']:
                print('dim_centralized mit', scenario)
                solutions.append(dim_centralized(city,scenario))

    elif dhn_elig < 3:
        print('District Heating not eligible!')
        for scenario in all_scenarios:
            if 'decentralized' in scenario['type']:
                print('dim_decentralized mit', scenario)
                solutions.append(dim_decentralized(city,scenario))

    else:
        print('District Heating solutions might be eligible...')
        for scenario in all_scenarios:
            if approve_scenario(city, scenario):
                if 'centralized' in scenario['type']:
                    print('dim_centralized mit', scenario)
                    solutions.append(dim_centralized(city,scenario))
#               if 'decentralized' in scenario['type']:
#                   solutions.append(dim_decentralized(city,scenario))
            else:
                print('Scenario not suitable: ', scenario)







def approve_scenario(city, scenario):
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

    if 'geothermal' in scenario['base']:
        print('Geothermal usage required. Not implemented yet.')
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

    result = {}
    # get thermal and electrical demand curves (only available for sanitation)
    [el_curve, th_curve] = city.get_power_curves(current_values=False)

    # Load duration curve (Jahresdauerlinie)
    th_LDC = get_LDC(th_curve)

    q_base_max = []
    for device in scenario['base']:
        if device == 'chp':
            # Dimensionierungspremissen:
            # möglichst unter 50kW pro BHKW, da Förderung dann höher?! - überprüfen
            # Möglichkeiten mit mehreren BHKWs überprüfen - Wie wird da in der Praxis entschieden
            # Kleinstes BHKW mindestens 6000 h/a Volllast
            # BHKW immer mit Speicher

            # Dimensionierungsstrategie: 1.Anlage bei 5000h/a mit 1/2 mehr installierter Leistung als nötig für Speicher
            q_base_max.append(3/2*th_LDC[5000])
            print('* Add CHP:', round(q_base_max[-1]/1000), 'kW')

            #Dimensionierung nach Krimmling "Energieeffiziente Nahwärmesysteme", S.127 - Faustformel: BHKW-Leistung zwischen 10% und 20% der Maximallast
            # q_borders = [min(th_LDC, key=lambda x:abs(x-0.1*max(th_LDC))), min(th_LDC, key=lambda x:abs(x-0.2*max(th_LDC)))] #gibt die Leistungsgrenzen nach Faustformel aus
            # t_borders = [th_LDC.index(q_borders[0]), th_LDC.index(q_borders[1])] #gibt die Volllaststunden für die errechneten Leistungen aus
            # print('BHKW mit Leistung zwischen ', q_borders)
            # print('Betriebszeiten zwischen ', t_borders)

        elif device == 'solar': # Regeln für Dimensionierung einführen!
            pv_area = 0
            for building in city.node.values():
                pv_area += building['entity'].roof_usabl_pv_area
            print('* Add Solarthermal device:', round(pv_area), 'm²')




    q_peak_max = []
    for device in scenario['peak']:
        if device == 'boiler':
            q_peak_max.append(max(th_LDC) - sum(q_base_max))
            print('* Add Boiler:', round(q_peak_max[-1]/1000), 'kW')







if __name__ == '__main__':
    #  Run program
    city = pickle.load(open('D:/jsc-jun/Beispielquartier/3_mfh_kronenberg/aachen_kronenberg_3_mfh_ref_1.pkl', mode='rb'))
    #city = pickle.load(open('/Users/jules/PycharmProjects/Masterarbeit/Beispielquartier/aachen_kronenberg_3_mfh_ref_1.pkl', mode='rb'))
    print('District: Aachen Kronenberg')

    run_approach(city)





#---------------------------------------- Alt -------------------------------------------------------

"""
    # select qualified scenarios for this district and environment
    print('Selection of scenarios...')
    qual_scenarios = select_scenarios(city)

    # dimensioning of centralized and decentralized scenarios
    final_scen = []



    for scenario in qual_scenarios:
        print('\nDimensioning of scenario: ', scenario)
        if scenario['supply'] == 'centralized':
            # final_scen wird das dimensionierte scenario angefügt
            final_scen.append(dim_centralized(city, scenario))

        elif scenario['supply'] == 'decentralized':
            # die einzelnen Häuser müssen individuell ausgelegt werden. Wie kann das in dieser Struktur realisiert werden?
            # -> Abhängig von genereller Endstruktur der Anlagendaten (liste mit dictionaries o.ä.)
            dim_decentralized(city, scenario)

    return final_scen







def dim_decentralized(city, scenario):
    # Lastgänge jedes Hauses wird betrachtet und muss gedeckt werden
    # returns scenario with sizes of units - in welcher form?
    print('-- Dimensioning of decentralized supply deactivated --')
    return None



def select_scenarios(city):
    '''
    Select qualified scenarios bc of

    :param city: city district which should be served
    :return: list of qualified scenarios
    '''

    qual_scenarios = all_scenarios[:]

    for scenario in all_scenarios:
        # Randbedingungen auflisten, nach denen sortiert wird
        # Emissionen?
        # Anteil EE
        # Verfügbarkeit Pellets/Hackschnitzel
        # Höhe Sonneneinstrahlung
        # Verfügbarkeit Erdwärme

        if scenario['base'] == ['boiler']:
            qual_scenarios.remove(scenario)
            print('Removed: ', scenario, ' (base is boiler)')



    return qual_scenarios


"""









