#!/usr/bin/env python
# coding=utf-8

import copy
import random as rd
import os
import pickle
import pycity_calc.cities.scripts.overall_gen_and_dimensioning as City_gen
import pycity_calc.toolbox.dimensioning.dim_functions as dimfunc
import numpy as np


def MC_rescale_esys(City, esys_unknown=True, recent_systems=False):

    '''
    Performs uncertainty rescaling for energy systems.

    Parameters
    ----------
    City :  object
            City object from pycity_calc
    esys_unknown: Boolean
        True:   energy systems characteristics are unknown. Generate a aleatory energy systems among possible
                market products and then rescale it to take into account uncertainties due to real conditions of use.
        False : energy systems are known. Rescale energy systems characteristics to simulate
                uncertainties due to real conditions of use
    recent_systems: Boolean
        True: energy systems generated with quite good performance
        False: energy generated with no performance preferences

    Returns
    -------
    City :  object
            City object modified for Monte Carlo analysis
    dict_city_esys_sampl : dict (of list)
            Dictionary of dictionnaries of samples for each building
            Keys: first keys are building identities then each building dictionary contains:
            'battery' : Holding modification of battery characteristics
            'CHP' : Holding modification of CHP characteristics
            'HP' : Holding modification of HP characteristics
            'EH' : Holding modification of EH characteristics
            'Boiler' : Holding modification of Boiler characteristics
            'PV' : Holding modification of PV characteristics

    '''

    #TODO rajouter dictionnaire pour choisir quelle energie systeme va etre utilise ou pas dans le MC
    # Initialisation dictionnary sampling
    dict_city_esys_sampl = {}

    # Get list of building
    list_of_building = City.get_list_build_entity_node_ids()

    #Loop over building
    for id_building in list_of_building:

        # Pointer on current building
        building = City.node[id_building]['entity']

        if esys_unknown:  # generate aleatory energy systems
            building = gen_esys_unknown(building, recent_systems=recent_systems)

        building, dict_build_esys_sampl = MC_new_esys_evaluation(building)
        # rescale it to take into account real conditions of use

        dict_city_esys_sampl[str(id_building)]=dict_build_esys_sampl

    return City, dict_city_esys_sampl

def gen_esys_unknown (building, recent_systems=True):

    '''
        Generates aleatory energy systems characteristics among all possible market products.

        Parameters
        ----------
        Building :  object
                    BuildingExtended Object from pycity_calc

        recent_systems: boolean
                        True: energy systems are recent
                        False: no information about the age of energy systems (energy systems can be old)
        Returns
        -------
        Building:  object
                Building Extended object modified for Monte Carlo analysis
    '''

    # Save copy
    ex_building = copy.deepcopy(building)

    # Battery
    if ex_building.bes.hasBattery == True:
        if recent_systems:
            building.bes.battery.eta_charge = rd.uniform(0.8,0.9)
            building.bes.battery.eta_discharge = rd.uniform(0.8,0.9)
            building.bes.battery.self_discharge = rd.uniform(0.8,0.9)
        else:
            building.bes.battery.eta_charge = rd.uniform(0.8, 0.9)
            building.bes.battery.eta_discharge = rd.uniform(0.8, 0.9)
            building.bes.battery.self_discharge = rd.uniform(0.8, 0.9)

    # Thermal storage
    if ex_building.bes.hasTes == True:
        if recent_systems:
            building.bes.tes.t_max = rd.uniform(50,75)
            #print (building.bes.tes.t_max)
            building.bes.tes.t_min = rd.uniform(15,20)
            print(building.bes.tes.t_min)
            #print (building.bes.tes.t_min )
            #building.bes.tes.t_surroundings = rd.uniform(20,25)
            building.bes.tes.k_loss = rd.uniform(0.25,0.5)
            #building.bes.tes.t_init = rd.uniform(20,50)
            #building.bes.tes.array_temp_storage = np.zeros(building.environment.timer.timeDiscretization)
            #building.bes.tes.array_q_charge = np.zeros(building.environment.timer.timeDiscretization)
            #building.bes.tes.array_q_discharge = np.zeros(building.environment.timer.timeDiscretization)
            building.bes.tes.t_init = building.bes.tes.t_min
            building.bes.tes.t_current = building.bes.tes.t_init
            #building.bes.tes.t_current = building.bes.tes.t_init
            #building.bes.tes.totalTSto = np.zeros(building.environment.timer.timestepsTotal)
            #building.bes.tes.currentTSto = np.zeros(building.environment.timer.timeDiscretization)
            #building.bes.tes.capacity = 100000


        else:

            building.bes.tes.t_max = rd.uniform(50, 75)
            building.bes.tes.t_min = rd.uniform(15, 20)
            #building.bes.tes.t_surroundings = rd.uniform(20, 25)
            building.bes.tes.k_loss = rd.uniform(0.25, 0.5)
            building.bes.tes.array_temp_storage = np.zeros(8760)
            building.bes.tes.array_q_charge = np.zeros(8760)
            building.bes.tes.array_q_discharge = np.zeros(8760)
            building.bes.tes.t_init = building.bes.tes.t_min
            building.bes.tes.t_current = building.bes.tes.t_init
            #building.bes.tes.capacity = building.bes.tes.capacity*1.1

    # Boiler
    if building.bes.hasBoiler == True:
        if recent_systems:
            building.bes.boiler.eta = rd.uniform(0.6,0.9)
            #City.node[build]['entity'].bes.boiler.lower_activation_limit = rd.uniform(0.1,0.3)
            #City.node[build]['entity'].bes.boiler.t_max = rd.uniform(80,100)
        else:
            building.bes.boiler.eta = rd.uniform(0.6, 0.9)
            # City.node[build]['entity'].bes.boiler.lower_activation_limit = rd.uniform(0.1,0.3)
            # City.node[build]['entity'].bes.boiler.t_max = rd.uniform(80,100)

    # Combined heat pump
    if building.bes.hasChp == True:
        if recent_systems:
            building.bes.chp.eta = rd.uniform(0.8,0.9)
            #building.bes.chp.t_max = rd.uniform(80,100)
            #building.bes.chp.lower_activation_limit = rd.uniform(0.1,0.3)
        else:
            building.bes.chp.eta = rd.uniform(0.8,0.9)
            #building.bes.chp.t_max = rd.uniform(80,100)
            #building.bes.chp.lower_activation_limit = rd.uniform(0.1,0.3)

    # Electrical heater
    if ex_building.bes.hasElectricalHeater == True:
        if recent_systems:
            building.bes.electricalHeater.eta = rd.uniform(0.8,0.95)
            #building.bes.electricalHeater.t_max = rd.uniform(80,100)
        else:
            building.bes.electricalHeater.eta = rd.uniform(0.8, 0.95)
            #building.bes.electricalHeater.t_max = rd.uniform(80, 100)

    # Heat pump
    if ex_building.bes.hasHeatpump == True:
        if recent_systems:
            #building.bes.heatpump.lower_activation_limit = rd.uniform(0.1,0.3)
            building.bes.heatpump.t_max = rd.uniform(80,100)
            building.bes.heatpump.t_sink = rd.uniform(20,25)
        else:
            #building.bes.heatpump.lower_activation_limit = rd.uniform(0.1, 0.3)
            building.bes.heatpump.t_max = rd.uniform(80, 100)
            building.bes.heatpump.t_sink = rd.uniform(20, 25)

    # photovoltaic
    if ex_building.bes.hasPv == True:
        if recent_systems:
            building.bes.pv.eta = rd.uniform(0.8,0.9)
            building.bes.pv.temperature_nominal = rd.uniform(18,25)
            building.bes.pv.alpha = rd.uniform(0.8,0.9)
            building.bes.pv.beta = rd.uniform(0.8,0.9)
            building.bes.pv.gamma = rd.uniform(0.8,0.9)
            building.bes.pv.tau_alpha = rd.uniform(0.8,0.9)
        else:
            building.bes.pv.eta = rd.uniform(0.8, 0.9)
            building.bes.pv.temperature_nominal = rd.uniform(18, 25)
            building.bes.pv.alpha = rd.uniform(0.8, 0.9)
            building.bes.pv.beta = rd.uniform(0.8, 0.9)
            building.bes.pv.gamma = rd.uniform(0.8, 0.9)
            building.bes.pv.tau_alpha = rd.uniform(0.8, 0.9)

    return building

def MC_new_esys_evaluation (building):
    '''
            Rescales energy systems characteristics to simulate characteristics for real conditions of use.

            Parameters
            ----------
            Building :  object
                    BuildingExtended Object from pycity_calc
            Returns
            -------
            Building:  object
                    Building Extended object modified for Monte Carlo analysis
            dict_build_esys_sampl : dict (of list)
            Dictionary of samples
            Keys:
            'battery' : Holding modification of battery characteristics
            'CHP' : Holding modification of CHP characteristics
            'HP' : Holding modification of HP characteristics
            'EH' : Holding modification of EH characteristics
            'Boiler' : Holding modification of Boiler characteristics
            'PV' : Holding modification of PV characteristics
        '''

    #TODO edimenssionner les fonctions dechantillonnnage
    # Dictionary to get samples track
    dict_build_esys_sampl = {}

    # Save copy
    ex_building = copy.deepcopy(building)

    if ex_building.bes.hasBattery == True:
        building.bes.battery.eta_charge = rd.normalvariate(mu= ex_building.bes.battery.eta_charge,
                                                                                  sigma = 0.1)
        building.bes.battery.eta_discharge = rd.normalvariate(mu= ex_building.bes.battery.eta_discharge,
                                                                                  sigma = 0.1)
        building.bes.battery.self_discharge = rd.normalvariate(mu= ex_building.bes.battery.self_discharge,
                                                                                  sigma = 0.1)

        dict_build_esys_sampl['battery']['eta_charge']= building.bes.battery.eta_charge
        dict_build_esys_sampl['battery']['eta_discharge']=building.bes.battery.eta_discharge
        dict_build_esys_sampl['battery']['self_discharge']=building.bes.battery.self_discharge

    #if ex_building.bes.hasTes == True:
        #building.bes.tes.t_max = rd.normalvariate(mu= ex_building.bes.tes.t_max,sigma = 0.1)
        #building.bes.tes.t_min = rd.normalvariate(mu= ex_building.bes.tes.t_min,sigma = 0.1)
        #building.bes.tes.t_surroundings = rd.normalvariate(mu= ex_building.bes.tes.t_surroundings ,sigma = 0.1)
        #building.bes.tes.k_loss = rd.normalvariate(mu= ex_building.bes.tes.k_loss,sigma = 0.1)
        #building.bes.tes.t_init = rd.normalvariate(mu= ex_building.bes.tes.t_init,sigma = 0.1)

    if ex_building.bes.hasBoiler == True:
        building.bes.boiler.eta = rd.normalvariate(mu= ex_building.bes.boiler.eta,
                                                                        sigma = 0.1)
        dict_build_esys_sampl['boiler']={}
        dict_build_esys_sampl['boiler']['eta'] = building.bes.boiler.eta

    if ex_building.bes.hasChp == True:
        building.bes.chp.eta = rd.normalvariate(mu= ex_building.bes.chp.eta,
                                                                        sigma = 0.1)
        #building.bes.chp.tMax = rd.normalvariate(mu= ex_building.bes.chp.tMax,sigma = 0.1)
        #building.bes.chp.lowerActivationLimit = rd.normalvariate(mu= ex_building.bes.chp.lowerActivationLimit,
                                                                 #sigma = 0.1)
        dict_build_esys_sampl['CHP']={}
        dict_build_esys_sampl['CHP']['eta'] = building.bes.chp.eta

    if ex_building.bes.hasElectricalHeater == True:
        building.bes.electricalHeater.eta = rd.normalvariate(mu= ex_building.bes.electricalHeater.eta,
                                                                        sigma = 0.1)
        #building.bes.electricalHeater.t_max = rd.normalvariate(mu= ex_building.bes.electricalHeater.t_max,
                                                                        #sigma = 0.1)
        dict_build_esys_sampl['EH']={}
        dict_build_esys_sampl['EH']['eta'] = building.bes.electricalHeater.eta

    if ex_building.bes.hasHeatpump == True:
        #building.bes.heatpump.lower_activation_limit = rd.normalvariate(mu= ex_building.bes.heatpump.lower_activation_limit,
                                                                        #sigma = 0.1)
        building.bes.heatpump.t_max = rd.normalvariate(mu= ex_building.bes.heatpump.t_max,
                                                                        sigma = 0.1)
        building.bes.heatpump.t_sink = rd.normalvariate(mu= ex_building.bes.heatpump.t_sink,
                                                                        sigma = 0.1)
        dict_build_esys_sampl['HP']={}
        dict_build_esys_sampl['HP']['tmax'] = building.bes.heatpump.t_max
        dict_build_esys_sampl['HP']['tsink'] = building.bes.heatpump.t_sink


    if ex_building.bes.hasPv == True:
        building.bes.pv.eta = rd.normalvariate(mu= ex_building.bes.pv.eta,
                                                                        sigma = 0.1)
        building.bes.pv.temperature_nominal = rd.normalvariate(mu= ex_building.bes.pv.temperature_nominal,
                                                                        sigma = 0.1)
        building.bes.pv.alpha = rd.normalvariate(mu= ex_building.bes.pv.alpha,
                                                                        sigma = 0.1)
        building.bes.pv.beta = rd.normalvariate(mu= ex_building.bes.pv.beta,
                                                                        sigma = 0.1)
        building.bes.pv.gamma = rd.normalvariate(mu= ex_building.bes.pv.gamma,
                                                                        sigma = 0.1)
        building.bes.pv.tau_alpha =rd.normalvariate(mu= ex_building.bes.pv.tau_alpha,
                                                                        sigma = 0.1)

        dict_build_esys_sampl['PV']={}
        dict_build_esys_sampl['PV']['eta'] =  building.bes.pv.eta
        dict_build_esys_sampl['PV']['tnominal'] = building.bes.pv.temperature_nominal
        dict_build_esys_sampl['PV']['beta'] = building.bes.pv.beta
        dict_build_esys_sampl['PV']['gamma'] = building.bes.pv.gamma
        dict_build_esys_sampl['PV']['alpha'] = building.bes.pv.tau_alpha
        dict_build_esys_sampl['PV']['alphPV'] = building.bes.pv.alphPV

    return building,dict_build_esys_sampl


if __name__ == '__main__':

    import matplotlib.pyplot as plt

    Nsamples = 100000
    city_pickle_name = 'aachen_kronenberg_3_mfh_ref_1.pkl'

    this_path = os.path.dirname(os.path.abspath(__file__))
    load_path = os.path.join(this_path, 'City_generation', 'output', city_pickle_name)
    City = pickle.load(open(load_path, mode='rb'))

    print()
    print('load city from pickle file: {}'.format(city_pickle_name))
    print()

    #  Add energy systems to city
    gen_esys = True  # True - Generate energy networks
    dhw_dim_esys = True  # Use dhw profiles for esys dimensioning

    #  Path to energy system input file (csv/txt; tab separated)
    esys_filename = 'lolo_esys.txt'
    esys_path = os.path.join(this_path, 'City_generation', 'input', 'input_esys_generator', esys_filename)

    #initialisation list boiler sampling
    list_boiler_sampling = []



    # Generate energy systems for city district
    if gen_esys:
        #  Load energy networks planing data
        list_esys = City_gen.esysgen.load_enersys_input_data(esys_path)
        print('Add energy systems')

        #  Generate energy systems
        City_gen.esysgen.gen_esys_for_city(city=City, list_data=list_esys,dhw_scale=dhw_dim_esys)

    ref_city = copy.deepcopy(City)

    for i in range(Nsamples):
        print(i)
        City, dict_city_sample = MC_rescale_esys(ref_city)
        list_boiler_sampling.append(City.node[1001]['entity'].bes.boiler.eta)

    plt.hist(list_boiler_sampling, 100, normed=1)
    plt.show()
