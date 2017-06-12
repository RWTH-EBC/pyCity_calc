"""
1. If __name__ == ‚__main__‘: Durchlauf des Programms
2. Beispielstadt laden
3. Passende Szenarien anhand der Randbedingungen auswählen und in qual_scenarios speichern: select_szenarios()
4. Alle qual_scenarios durchlaufen und abhängig ob zentral/dezentral dimensionieren:
        dim_centralized(city, scenario)
        dim_decentralized(city, scenario) 
5. Für jedes Szenario in dim_de/centralized():
        Dimensionierung der Anlagen in allen möglichen Szenarien nach gesetzlichen Bedingungen.
        Für centralized: Alle Lastgänge addieren -> daraus maximale Last errechnen
        Für decentralized: Einzelne Lastgänge nutzen

5.	Ausgabe aller Szenarien in Variablen/Dictionary/Datei



"""

import pickle
import matplotlib.pyplot as plt

import pycity.classes.supply.BES as BES
import pycity_calc.energysystems.boiler as Boiler


scen1 = {'supply':'centralized','base':['boiler'],'peak':[]}
scen2 = {'supply':'decentralized','base':['heatPump','PV','geo_flat'],'peak':['boiler']}

all_scenarios = [scen1, scen2]

def run_approach(city):

    # select qualified scenarios for this district and environment
    print('Selection of scenarios...')
    qual_scenarios = select_scenarios(city)


    # dimensioning of centralized and decentralized scenarios
    final_scen = []

    for scenario in qual_scenarios:

        if scenario['supply'] == 'centralized':
            print('\nDimensioning of scenarios with centralized supply...')
            # final_scen wird das dimensionierte scenario angefügt
            final_scen.append(dim_centralized(city, scenario))

        elif scenario['supply'] == 'decentralized':
            # die einzelnen Häuser müssen individuell ausgelegt werden. Wie kann das in dieser Struktur realisiert werden?
            # -> Abhängig von genereller Endstruktur der Anlagendaten (liste mit dictionaries o.ä.)
            print('\nDimensioning of scenarios with decentralized supply...')
            dim_decentralized(city, scenario)

    return final_scen




def dim_centralized(city, scenario):
    # Lastgänge aller Häuser addieren (Gesamtnachfrage wird betrachtet)
    # return scenario with sizes of units - in welcher form? city_object
    #[electr_curve heating_curve] = city.get_power_curves() #aus pycity.classes.CityDistrict
    #for unit in scenario['base']:

    [el_curve, th_curve] = city.get_power_curves(current_values=False)

    print('Aggregated electrical Demand: ', el_curve)
    print('Aggregated thermal Demand: ', th_curve)
    print('Buildings in District: ', city.get_list_build_entity_node_ids())

    # Bestimmung eines Gebäudes als Wärmezentrale - evtl. neues Gebäude erstellen, das Zentrale beinhaltet
    h_central = city.node[1001]['entity']

    # Add BES if necessary
    if not h_central.hasBes:
        bes = BES.BES(city.environment)
        h_central.addEntity(bes)
        print('* Added BES')

    for tech in scenario['base']:

        # Add Boiler
        if tech == 'boiler':
            lower_activation_limit = 0  # bei welchem Bedarf wird der Boiler angeschmissen?
            q_nominal = max(th_curve)  # Höchster Wert des thermischen Bedarfs
            t_max = 90   # prüfen, wieso 90°C?
            eta = 0.9    # kann so bleiben
            boiler = Boiler.BoilerExtended(city.environment, q_nominal, eta, t_max, lower_activation_limit)
            h_central.bes.addDevice(boiler)
            # Boiler übernimmt komplette Wärmeversorgung
            boiler._setQOutput(th_curve)
            results_boiler = boiler._getQOutput() #currentValues True/False?

        print('* Added', tech)

        plt.plot(results_boiler)
        plt.show()

    return None

def dim_decentralized(city, scenario):
    # Lastgänge jedes Hauses wird betrachtet und muss gedeckt werden
    # returns scenario with sizes of units - in welcher form?
    print('-- Dimensioning of decentralized supply deactivated --')
    return None



def select_scenarios(city):
    """
    Select qualified scenarios bc of

    :param city: city district which should be served
    :return: list of qualified scenarios
    """

    qual_scenarios = all_scenarios[:]

    for scenario in all_scenarios:
        # Randbedingungen auflisten, nach denen sortiert wird
        # Emissionen?
        # Anteil EE
        # Verfügbarkeit Pellets/Hackschnitzel
        # Höhe Sonneneinstrahlung
        # Verfügbarkeit Erdwärme

        if scenario['base'] != ['boiler']:
            #qual_scenarios.remove(scenario)
            print('Removed: ', scenario, ' (base is not boiler)')

    return qual_scenarios








if __name__ == '__main__':
    #  Run program
    city = pickle.load(open('D:/jsc-jun/Beispielquartier/3_mfh_kronenberg/aachen_kronenberg_3_mfh_ref_1.pkl', mode='rb'))
    #city = pickle.load(open('/Users/jules/PycharmProjects/Masterarbeit/Beispielquartier/aachen_kronenberg_3_mfh_ref_1.pkl', mode='rb'))
    print('District: Aachen Kronenberg')

    run_approach(city)






