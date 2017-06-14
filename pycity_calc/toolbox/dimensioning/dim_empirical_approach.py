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
import numpy as np

import pycity.classes.supply.BES as BES
import pycity_calc.energysystems.boiler as Boiler
import pycity_calc.energysystems.chp as CHP

scen1 = {'supply':'centralized','base':['boiler'],'peak':[]}
scen2 = {'supply':'centralized','base':['chp'],'peak':['boiler']}
#scen3 = {'supply':'decentralized','base':['heatPump','PV','geo_flat'],'peak':['boiler']}

all_scenarios = [scen1, scen2]

def run_approach(city):

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

    # correction factor for timesteps
    #timesteps_factor = 3600/city.environment.timer.timeDiscretization

    # get thermal and electrical demand curves
    [el_curve, th_curve] = city.get_power_curves(current_values=False)

    # Load duration curve (Jahresdauerlinie)
    th_LDC = get_LDC(th_curve)

    op_times = []

    # Bestimmung eines Gebäudes als Wärmezentrale - evtl. neues Gebäude erstellen, das Zentrale beinhaltet
    h_central = city.node[1001]['entity']

    # Add BES if necessary
    if not h_central.hasBes:
        bes = BES.BES(city.environment)
        h_central.addEntity(bes)
        print('* Added BES')

    for dev in scenario['base']:

        if dev == 'boiler':
            # Add Boiler

            lower_activation_limit = 0  # bei welchem Bedarf wird der Boiler angeschmissen?
            q_nominal = max(th_curve)  # Höchster Wert des thermischen Bedarfs
            t_max = 90   # prüfen, wieso 90°C?
            eta = 0.9    # kann so bleiben
            boiler = Boiler.BoilerExtended(city.environment, q_nominal, eta, t_max, lower_activation_limit)
            h_central.bes.addDevice(boiler)

            # Boiler übernimmt komplette Wärmeversorgung
            boiler._setQOutput(th_curve)

            # Macht es Sinn den Output in einer anderen Methode einzutragen?
            results_boiler = boiler._getQOutput() #currentValues True/False?
            op_times.append(results_boiler/q_nominal)

        elif dev == 'chp':
            # Auslegung nach Volllaststunden -> 5000h/a
            vlh = 5000 #Volllaststunden

            # Add CHP
            lower_activation_limit = 0.9
            #q_nominal = th_curve[vlh*timesteps_factor]
            q_nominal = th_curve[vlh]
            t_max = 90
            p_nominal = 0.4*q_nominal
            eta_total = 0.87
            chp = CHP.ChpExtended(environment=city.environment,
                                  p_nominal=p_nominal,
                                  q_nominal=q_nominal,
                                  eta_total=eta_total,
                                  t_max=t_max,
                                  lower_activation_limit=lower_activation_limit,
                                  thermal_operation_mode=True)
            h_central.bes.addDevice(chp)

            # wie lege ich den Output fest, zu jeder Zeit, zu der q_nominal überstiegen wird?
            #chp._setQOutput()


        print('* Added', dev)

    #plot operational times of all devices
    #for op in op_times: plt.plot(op)
    #plt.show()

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

        if scenario['base'] == ['boiler']:
            qual_scenarios.remove(scenario)
            print('Removed: ', scenario, ' (base is boiler)')



    return qual_scenarios








if __name__ == '__main__':
    #  Run program
    city = pickle.load(open('D:/jsc-jun/Beispielquartier/3_mfh_kronenberg/aachen_kronenberg_3_mfh_ref_1.pkl', mode='rb'))
    #city = pickle.load(open('/Users/jules/PycharmProjects/Masterarbeit/Beispielquartier/aachen_kronenberg_3_mfh_ref_1.pkl', mode='rb'))
    print('District: Aachen Kronenberg')

    run_approach(city)






