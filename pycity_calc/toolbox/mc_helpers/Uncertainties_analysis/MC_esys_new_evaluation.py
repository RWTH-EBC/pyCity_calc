#!/usr/bin/env python
# coding=utf-8

import copy
import random as rd
import os
import pickle
import pycity_calc.cities.scripts.overall_gen_and_dimensioning as City_gen
import csv
import pycity_base.classes.supply.BES as BES
import pycity_base.classes.supply.PV as PV
import pycity_calc.toolbox.dimensioning.dim_functions as dimfunc
import pycity_calc.energysystems.boiler as boil
import pycity_calc.energysystems.chp as chpsys
import pycity_calc.energysystems.thermalEnergyStorage as tes
import pycity_calc.energysystems.heatPumpSimple as hpsys
import pycity_calc.energysystems.electricalHeater as ehsys
import pycity_calc.energysystems.battery as batt

def MC_rescale_esys(City, esys_unknown=True, recent_systems=True):

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


    # Initialisation dictionnary sampling
    dict_city_esys_sampl = {}

    # Get list of building
    list_of_building = City.get_list_build_entity_node_ids()

    #Loop over building
    for id_building in list_of_building:

        # Pointer on current building
        building = City.nodes[id_building]['entity']

        # change building environment
        building.environment = City.environment

        if esys_unknown:  # generate aleatory energy systems
            building = gen_esys_unknown(building, recent_systems=recent_systems)

        else:
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
            building.bes.battery.eta_charge = rd.uniform(0.9,0.96)
            building.bes.battery.eta_discharge = rd.uniform(0.9,0.96)
            building.bes.battery.self_discharge = rd.uniform(0.01,0.03)
        else:
            building.bes.battery.eta_charge = rd.uniform(0.85, 0.96)
            building.bes.battery.eta_discharge = rd.uniform(0.85, 0.96)
            building.bes.battery.self_discharge = rd.uniform(0.01, 0.05)

    ''' Removed because of some bugs'''
    # Thermal storage
    #if ex_building.bes.hasTes == True:
        #if recent_systems:
            #building.bes.tes.t_max = rd.uniform(50,75)
            #print (building.bes.tes.t_max)
            #building.bes.tes.t_min = rd.uniform(15,20)
            #print(building.bes.tes.t_min)
            #print (building.bes.tes.t_min )
            #building.bes.tes.t_surroundings = rd.uniform(20,25)
            #building.bes.tes.k_loss = rd.uniform(0.25,0.5)
            #building.bes.tes.t_init = rd.uniform(20,50)
            #building.bes.tes.array_temp_storage = np.zeros(building.environment.timer.timeDiscretization)
            #building.bes.tes.array_q_charge = np.zeros(building.environment.timer.timeDiscretization)
            #building.bes.tes.array_q_discharge = np.zeros(building.environment.timer.timeDiscretization)
            #building.bes.tes.t_init = building.bes.tes.t_min
            #building.bes.tes.t_current = building.bes.tes.t_init
            #building.bes.tes.t_current = building.bes.tes.t_init
            #building.bes.tes.totalTSto = np.zeros(building.environment.timer.timestepsTotal)
            #building.bes.tes.currentTSto = np.zeros(building.environment.timer.timeDiscretization)
            #building.bes.tes.capacity = 100000


        #else:

            #building.bes.tes.t_max = rd.uniform(50, 75)
            #building.bes.tes.t_min = rd.uniform(15, 20)
            #building.bes.tes.t_surroundings = rd.uniform(20, 25)
            #building.bes.tes.k_loss = rd.uniform(0.25, 0.5)
            #building.bes.tes.array_temp_storage = np.zeros(8760)
            #building.bes.tes.array_q_charge = np.zeros(8760)
            #building.bes.tes.array_q_discharge = np.zeros(8760)
            #building.bes.tes.t_init = building.bes.tes.t_min
            #building.bes.tes.t_current = building.bes.tes.t_init
            #building.bes.tes.capacity = building.bes.tes.capacity*1.1

    # Boiler
    if building.bes.hasBoiler == True:
        if recent_systems:
            building.bes.boiler.eta = rd.uniform(0.85,0.95)

        else:
            building.bes.boiler.eta = rd.uniform(0.80, 0.95)


    # Combined heat pump
    if building.bes.hasChp == True:
        if recent_systems:
            building.bes.chp.omega = rd.uniform(0.88,0.93)

        else:
            building.bes.chp.omega = rd.uniform(0.80,0.93)

    # Electrical heater
    if ex_building.bes.hasElectricalHeater == True:
        if recent_systems:
            building.bes.electricalHeater.eta = rd.uniform(0.98,1)

        else:
            building.bes.electricalHeater.eta = rd.uniform(0.95, 0.99)

    # Heat pump
    if ex_building.bes.hasHeatpump == True:

        #building.bes.heatpump.lower_activation_limit = rd.uniform(0.1,0.3)
        building.bes.heatpump.t_sink = rd.uniform(35,55)
        building.bes.heatpump.quality_grade = \
            (1-rd.normalvariate(mu = 0, sigma = 0.3 ))* ex_building.bes.heatpump.quality_grade

    # photovoltaic
    if ex_building.bes.hasPv == True:

        # rescale pv timer
        building.bes.pv.environment.weather.timer = building.environment.timer

        if recent_systems:

            building.bes.pv.eta = rd.uniform(0.15,0.21)
            #building.bes.pv.temperature_nominal = rd.uniform(18,25)

        else:

            building.bes.pv.eta = rd.uniform(0.10,0.2 )

        #building.bes.pv.alpha = rd.uniform(0.8, 0.9)
        building.bes.pv.beta = rd.uniform(0, 45)
        building.bes.pv.gamma = rd.uniform(-45,45 )

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

    # Dictionary to get samples track
    dict_build_esys_sampl = {}

    # Save copy
    ex_building = copy.deepcopy(building)

    if ex_building.bes.hasBattery == True:
        building.bes.battery.eta_charge = rd.normalvariate(mu= ex_building.bes.battery.eta_charge,sigma = 0.01)
        building.bes.battery.eta_discharge = rd.normalvariate(mu= ex_building.bes.battery.eta_discharge,sigma = 0.01)
        building.bes.battery.self_discharge = rd.normalvariate(mu= ex_building.bes.battery.self_discharge,sigma = 0.01)
        dict_build_esys_sampl['battery']={}
        dict_build_esys_sampl['battery']['Battery_eta_charge']= building.bes.battery.eta_charge
        dict_build_esys_sampl['battery']['Battery_eta_discharge']=building.bes.battery.eta_discharge
        dict_build_esys_sampl['battery']['Battery_self_discharge']=building.bes.battery.self_discharge

    #if ex_building.bes.hasTes == True:
        #building.bes.tes.tMax = rd.normalvariate(mu= ex_building.bes.tes.t_max,sigma = 0.1)
        #building.bes.tes.t_min = rd.normalvariate(mu= ex_building.bes.tes.t_min,sigma = 0.1)
        #building.bes.tes.t_surroundings = rd.normalvariate(mu= ex_building.bes.tes.t_surroundings ,sigma = 0.1)
        #building.bes.tes.k_loss = rd.normalvariate(mu= ex_building.bes.tes.k_loss,sigma = 0.1)
        #building.bes.tes.t_init = rd.normalvariate(mu= ex_building.bes.tes.t_init,sigma = 0.1)
        #dict_build_esys_sampl['TES'] = {}
        #dict_build_esys_sampl['TES']['TES_kloss'] = building.bes.tes.k_loss
        #dict_build_esys_sampl['TES']['TES_Tmax'] = building.bes.tes.t_min
        #dict_build_esys_sampl['TES']['TES_Tmin'] = building.bes.tes.t_max

    if ex_building.bes.hasBoiler == True:
        #print('Rescale Boiler 2')
        building.bes.boiler.eta = rd.normalvariate(mu= ex_building.bes.boiler.eta,sigma = 0.01)

        # Assert that their is no extrem values
        if building.bes.boiler.eta < 0.70:
            building.bes.boiler.eta = 0.85

        elif building.bes.boiler.eta > 0.96:
            building.bes.boiler.eta = 0.9

        print('Rescaleboiler',building.bes.boiler.eta )
        dict_build_esys_sampl['boiler']={}
        dict_build_esys_sampl['boiler']['eta'] = building.bes.boiler.eta

    if ex_building.bes.hasChp == True:
        building.bes.chp.omega = rd.normalvariate(mu= ex_building.bes.chp.omega,sigma = 0.01)

        # Assert that their is no extrem values
        if building.bes.chp.omega > 1:
            building.bes.chp.omega = 0.9

        elif  building.bes.chp.omega<0.8:
            building.bes.chp.omega = 0.9

        dict_build_esys_sampl['CHP']={}
        dict_build_esys_sampl['CHP']['CHP_omega'] = building.bes.chp.omega

    if ex_building.bes.hasElectricalHeater == True:
        building.bes.electricalHeater.eta = rd.normalvariate(mu= ex_building.bes.electricalHeater.eta,sigma = 0.01)
        # Assert that their is no extrem values
        if building.bes.electricalHeater.eta < 0.95 :
            building.bes.electricalHeater.eta = 0.99
        elif building.bes.electricalHeater.eta > 1:
            building.bes.electricalHeater.eta = 0.99

        #building.bes.electricalHeater.t_max = rd.normalvariate(mu= ex_building.bes.electricalHeater.t_max,
                                                                        #sigma = 0.1)
        #dict_build_esys_sampl['EH']={}
        #dict_build_esys_sampl['EH']['EH_eta'] = building.bes.electricalHeater.eta

    if ex_building.bes.hasHeatpump == True:
        building.bes.heatpump.quality_grade = rd.normalvariate(mu=ex_building.bes.heatpump.quality_grade, sigma=0.01)
        building.bes.heatpump.t_sink = rd.normalvariate(mu= ex_building.bes.heatpump.t_sink, sigma = 1)
        #dict_build_esys_sampl['HP']={}
        #dict_build_esys_sampl['HP']['HP_lal'] = building.bes.heatpump.lower_activation_limit
        #dict_build_esys_sampl['HP']['HP_tsink'] = building.bes.heatpump.t_sink


    if ex_building.bes.hasPv == True:

        # rescale pv timer
        building.bes.pv.environment.weather.timer = building.environment.timer


        building.bes.pv.eta = rd.normalvariate(mu= ex_building.bes.pv.eta,sigma = 0.01)
        print('pv eta',building.bes.pv.eta )

        # Assert that their is no extrem values
        if building.bes.pv.eta < 10 or building.bes.pv.eta > 25:
            building.bes.pv.eta = 0.16

        building.bes.pv.beta = rd.normalvariate(mu= ex_building.bes.pv.beta, sigma = 1)

        building.bes.pv.gamma = rd.normalvariate(mu= ex_building.bes.pv.gamma, sigma = 1)


        dict_build_esys_sampl['PV']={}
        dict_build_esys_sampl['PV']['eta'] =  building.bes.pv.eta
        dict_build_esys_sampl['PV']['beta'] = building.bes.pv.beta
        dict_build_esys_sampl['PV']['gamma'] = building.bes.pv.gamma

    return building,dict_build_esys_sampl

def load_enersys_input_data(esys_path):
    """
    Load energy system input data from path (should point on
    txt file, which is tab separated and holds information about
    planed energy systems

    Parameters
    ----------
    esys_path : str
        Path to input file

    Returns
    -------
    list_data : list
        List (of tuples). Each tuple holds eneryg system data
    """

    #  Generate empty data list
    list_data = []

    with open(esys_path, 'r') as file:
        next(file)  # Skip header

        reader = csv.reader(file, delimiter='\t')
        for node_id , type_sys, pam1, pam2 in reader:

            #  Generate data tuple
            tup_data = (int(node_id), int(type_sys), float(pam1), float(pam2))

            #  Add tuple to data list
            list_data.append(tup_data)

    return list_data


def gen_esys_for_city(city, list_data, size_esys = False, boiler_buffer_factor=1.15):
    """
    Generate  energy systems within city district, based on
    user defined energy system from txt file.

    Parameters
    ----------
    city : object
        City object of pycity_calc
    list_data : list
        List (of tuples). Each tuple holds eneryg system data with following
        information: (node_id, type, method)
    dhw_scale : bool, optional
        Defines, if hot water thermal energy demand should be taken into
        account. (default: False)
        If True, only space heating power demand is taken into account.
    tes_default : float, optional
        Default value for smallest thermal storage size in kg
        (default: 100)
    boiler_buffer_factor : float, optional
        Factor for boiler oversizing (default: 1.15)
    """

    #  Check if all node ids exist within city object
    for tup in list_data:
        assert tup[0] in city.nodelist_building, ('Node ' + str(tup[0]) +
                                                  ' is not within city')

    # Generate energy systems
    #  #---------------------------------------------------------------------
    for tup in list_data:

        node_id = tup[0]  # Id of node
        type = tup[1]  # Type of energy system
        pam = tup[2]  # Parametre esys
        chp_pan = tup[3]

        print('Process node with id ', node_id)

        #  Check if building at node_id does not have BES, already
        if city.nodes[node_id]['entity'].hasBes is False:
            #  Generate BES, if not existent
            bes = BES.BES(environment=city.environment)
        else:
            bes = city.nodes[node_id]['entity'].bes

        # Pointer to building
        build = city.nodes[node_id]['entity']

        # #-------------------------------------------------------------
        if type == 1:  # Boiler
        #  #-------------------------------------------------------------

            #  Size boiler with max. building th. power load
            if size_esys:

                boiler_th_power = dimfunc.get_max_power_of_building(build, with_dhw=True)

                # Add boiler buffer factor
                boiler_th_power *= boiler_buffer_factor

                # Round results
                boiler_th_power = dimfunc.round_esys_size(boiler_th_power, round_up=True)

                print('Chosen boiler size in kW:')
                print(boiler_th_power / 1000)

            else:
                boiler_th_power = pam*1000
                print('Boiler size in kW:')
                print(boiler_th_power / 1000)


            boiler = boil.BoilerExtended(environment=city.environment,q_nominal=boiler_th_power,eta=0.85,
                                         lower_activation_limit=0)

            bes.addDevice(boiler)

        # #-------------------------------------------------------------
        elif type == 2:  #TES
            #  #-------------------------------------------------------------

            if size_esys:

                build_single = city.nodes[node_id]['entity']

                th_curve = dimfunc.get_max_power_of_building(build, with_dhw=False)

                #  Account for hot water by upscaling factor
                #  Upscale to account for dhw demand
                ann_dhw_demand = build_single.get_annual_dhw_demand()
                ann_th_heat_demand = build_single.get_annual_space_heat_demand()

                factor_rescale = (ann_dhw_demand + ann_th_heat_demand) / ann_th_heat_demand

                #  Rescale th_dur_curve
                th_curve *= factor_rescale

                # TES dimensioning
                #  #------------------------------------
                #  Use thermal load curve to dimension CHP with spec. method
                chp_th_power = th_curve
                chp_th_power = dimfunc.round_esys_size(power=chp_th_power) * 1.1

                #  TES sizing
                #  Storage should be capable of provide thermal need
                #  power for 6 hours (T_spread = 60 Kelvin)
                mass_tes = chp_th_power * 6 * 3600 / (4180 * 60)

                #  Round to realistic storage size
                mass_tes = dimfunc.storage_rounding(mass_tes)

                print('Chosen storage size in liters:')
                print(mass_tes)
                print()

            else:
                mass_tes = pam
                print('Storage size in liters:')
                print(mass_tes)
                print()

            storage = tes.thermalEnergyStorageExtended(environment=city.environment,t_init=30, capacity=mass_tes)

            # Add devices to bes
            bes.addDevice(storage)

        # #-------------------------------------------------------------
        elif type == 3:  # CHP
        #  #-------------------------------------------------------------

            # CHP
            #  #------------------------------------
            # Pointer to building
            build = city.nodes[node_id]['entity']

            if size_esys:
                chp_th_power = dimfunc.get_max_power_of_building(build, with_dhw=False)

                #  Size el. heater according to max. dhw power of building
                dhw_power_curve = build.get_dhw_power_curve()
                max_dhw_power = dimfunc.get_max_p_of_power_curve(dhw_power_curve)

                chp_th_power += max_dhw_power

                chp_el_th_ratio = dimfunc.calc_asue_el_th_ratio(chp_th_power)
                chp_el_power = chp_el_th_ratio * chp_th_power

                #  Round results
                chp_th_power = dimfunc.round_esys_size(power=chp_th_power)

                print('Chosen chp thermal power in kW:')
                print(chp_th_power / 1000)

                print('Chosen chp electrical power in kW:')
                print(chp_el_power / 1000)

            else:
                chp_th_power = pam*1000
                chp_el_power = chp_pan*1000

                print('Chp thermal power in W:')
                print(chp_th_power)

                print('Chp electrical power in W:')
                print(chp_el_power)

            chp = chpsys.ChpExtended(environment=city.environment, q_nominal=chp_th_power,p_nominal=chp_el_power)

            # Add pv to bes
            bes.addDevice(chp)

        # #-------------------------------------------------------------
        elif type == 4:  # PV
            #  #-------------------------------------------------------------
            # pam --> Defines area of PV as float value

            pv = PV.PV(environment=city.environment, area=pam, eta=0.16)

            print('Add PV system with area in m2: ', pam)

            # Add pv to bes
            bes.addDevice(pv)

        # #-------------------------------------------------------------
        elif type == 5:  # Heat pump
            #  #-------------------------------------------------------------
            #  pam --> Defines HP nominal power as float value (kW)

            # Pointer to building
            build = city.nodes[node_id]['entity']

            if size_esys:
                hp_th_power = dimfunc.get_max_power_of_building(build, with_dhw=False)

                #  Size el. heater according to max. dhw power of building
                dhw_power_curve = build.get_dhw_power_curve()
                max_dhw_power = dimfunc.get_max_p_of_power_curve(dhw_power_curve)

                hp_th_power += max_dhw_power

                # Round values
                hp_th_power = dimfunc.round_esys_size(hp_th_power, round_up=True)
                print('Chosen heat pump nominal th. power in kW:')
                print(hp_th_power / 1000)

            else:
                hp_th_power = pam * 1000
                print('Heat pump nominal th. power in kW:')
                print(hp_th_power / 1000)

            hp_heater = hpsys.heatPumpSimple(environment=city.environment,q_nominal=hp_th_power)

            # Add devices to bes
            bes.addDevice(hp_heater)

        # #-------------------------------------------------------------
        elif type == 6:  # Electrical heater
            #  #-------------------------------------------------------------
            #  pam --> Defines EH nominal power as float value (kW)

            # Pointer to building
            build = city.nodes[node_id]['entity']

            if size_esys:
                eh_th_power = dimfunc.get_max_power_of_building(build, with_dhw=False)

                #  Size el. heater according to max. dhw power of building
                dhw_power_curve = build.get_dhw_power_curve()
                max_dhw_power = dimfunc.get_max_p_of_power_curve(dhw_power_curve)

                eh_th_power+= max_dhw_power

                # Round values
                eh_th_power = dimfunc.round_esys_size(eh_th_power,round_up=True)
                print('Chosen el. heater nominal th. power in kW:')
                print(eh_th_power / 1000)

            else:
                eh_th_power = pam*1000
                print('El. heater nominal th. power in kW:')
                print(eh_th_power / 1000)

            el_heater = ehsys.ElectricalHeaterExtended(environment=city.environment,
                                         q_nominal=eh_th_power)


            # Add devices to bes
            bes.addDevice(el_heater)

        # #-------------------------------------------------------------
        elif type == 7:  # Battery
            #  #-------------------------------------------------------------
            #  pam --> Defines capacity of battery as float value (kWh)

            battery = batt. BatteryExtended(environment=city.environment,soc_init_ratio=0, capacity_kwh=pam)

            print('Add el. battery with capacity in kWh: ', pam)

            # Add battery to bes
            bes.addDevice(battery)

        # #-------------------------------------------------------------
        else:
            raise ValueError('Type is unknown. Check list_data input!')

        # Add bes to building
        city.nodes[node_id]['entity'].addEntity(bes)
        print()

if __name__ == '__main__':

    import matplotlib.pyplot as plt

    Nsamples = 10
    city_pickle_name = 'aachen_kronenberg_3_mfh_ref_1.pkl'

    this_path = os.path.dirname(os.path.abspath(__file__))
    load_path = os.path.join(this_path, 'City_generation', 'input', city_pickle_name)
    City = pickle.load(open(load_path, mode='rb'))

    print()
    print('load city from pickle file: {}'.format(city_pickle_name))
    print()

    #  Add energy systems to city
    gen_esys = True  # True - Generate energy networks
    dhw_dim_esys = True  # Use dhw profiles for esys dimensioning

    #  Path to energy system input file (csv/txt; tab separated)
    esys_filename = 'City_lolo_esys.txt'
    esys_path = os.path.join(this_path, 'City_generation', 'input', 'input_esys_generator', esys_filename)

    #initialisation list boiler sampling
    list_boiler_sampling = []

    # Generate energy systems for city district
    if gen_esys:

        #  Load energy networks planing data
        list_esys = load_enersys_input_data(esys_path)
        print ('Add energy systems')

        #  Generate energy systems
        gen_esys_for_city(city=City, list_data=list_esys, size_esys=False)

    ref_city = copy.deepcopy(City)

    for i in range(Nsamples):
        print(i)
        City, dict_city_sample = MC_rescale_esys(ref_city)
        list_boiler_sampling.append(City.nodes[1001]['entity'].bes.boiler.eta)

    plt.hist(list_boiler_sampling, 100, normed=1)
    plt.show()
