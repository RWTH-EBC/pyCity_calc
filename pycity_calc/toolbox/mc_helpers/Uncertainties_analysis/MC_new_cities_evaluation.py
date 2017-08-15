#!/usr/bin/env python
# coding=utf-8

'''

Script to do Monte Carlo simulations

'''

import copy
import pycity_calc.toolbox.mc_helpers.Uncertainties_analysis.MC_new_building as newB
import pycity_calc.cities.scripts.overall_gen_and_dimensioning as City_gen
import pycity_calc.toolbox.dimensioning.dim_functions as dimfunc
import numpy as np
import pycity_calc.simulation.energy_balance_optimization.energy_balance_building as EBB
import pycity_calc.economic.annuity_calculation as eco_calc
import pycity_calc.environments.germanmarket as Mark
import pycity_calc.economic.calc_CO2_emission as GHG_calc
import pycity_calc.toolbox.mc_helpers.Uncertainties_analysis.MC_esys_new_evaluation as mc_esys
import pycity_calc.toolbox.mc_helpers.weather.gen_weather_set as wea
import os
import pickle
import matplotlib.pyplot as plt
import pycity_calc.cities.scripts.street_generator.street_generator as street_gen
import random as rd
import pycity_calc.simulation.energy_balance_optimization.Energy_balance_lhn as EB

def new_city_evaluation_monte_carlo(ref_City, dict_sample):
    """
        Does simulations for Monte Carlo Analyse.
        Evaluates new City and calculates gas and electrical demand, annuity and GHG emissions.

        Parameters
        ----------
        City : object
            City object from pycity_calc
        dict_sample : dict
            Dictionary holding uncertain parameters
            Keys:
            Nsamples :  int
                        Number of samples
            nb_occ_unc : bool
                        Defines, if number of occupants per apartment is unknown
            MC_analysis: boolean
                        Defines extra modifications for monte carlo analysis
                        (dormer,attic,cellar, net_floor_area)
            buil_physic_unc: bool
                        Defines,if building physics unknown or not (default: True)
            weather : Holding weather sample lists
            interest:   list
                        Holding interest rate sampling for economic calculation
            time:   int
                    Time for economic calculation in years (default: 10)
        Returns
        -------
        res_tuple : tuple (of Array)
            Results tuple (Th_results, Gas_results, El_results, Annuity_results, GHG_results, GHG_spe_results,
                            el_results2, Th_results2, dict_city_pb, Nboiler_rescaled, NEH_rescaled)
            1. Array holding net space heating demands in kWh as float
            2. Array holding Gas demands in kWh as float
            3. Array holding Electrical demands in kWh as float
            4. Array holding Annuity in Euro as float
            5. Array holding GHG emissions in kg as float
            6. Array holding specific GHG emissions in kg as float
            7. Array holding electrical demand in kWh as float (sum of buildings demand)
            8. Dict holding samples list for each building
            9. Nboiler_rescaled Number of city with rescaled boiler
            10: NEH_rescaled Number of city with rescaled EH
            11: Lal_rescaled Number of city with rescaled boiler lal
        """

    # Save the City
    City = copy.deepcopy(ref_City)

    Nloop = dict_sample['Nsamples']

    Nboiler_rescaled = 0# number of boiler rescaled (thermal demand to high)
    NEH_rescaled = 0 # number of electrical heater rescaled (thermal demand to high)
    Lal_rescaled = 0 # Number of city with rescaled boiler lal
    Tes_rescale = 0
    Gas_results = np.zeros(Nloop)  # array of annual gas demand
    El_results = np.zeros(Nloop)  # array of annual electrical demand after energy balance
    Th_results = np.zeros(Nloop) #array of annual space heating demand
    Annuity_results = np.zeros(Nloop)
    GHG_results = np.zeros(Nloop)
    GHG_spe_results = np.zeros(Nloop)
    el_results2 = np.zeros(Nloop)

    list_weather = dict_sample['weather']
    MC_analysis = dict_sample['MC_analysis']
    nb_occ_unc = dict_sample ['nb_occ_unc']
    build_physic_unc = dict_sample['build_physic_unc']
    time_sp_force_retro = dict_sample['time_sp_force_retro']
    max_retro_year = dict_sample['max_retro_year']
    interest = dict_sample['interest']
    time = dict_sample['time']

    # Initialisation dictionary to keep samples list
    dict_city_pb = {}
    for buildnb in City.get_list_build_entity_node_ids():
        dict_city_pb[str(buildnb)] = {}
        dict_city_pb[str(buildnb)]['year']=[]
        dict_city_pb[str(buildnb)]['infiltration']=[]
        dict_city_pb[str(buildnb)]['cellar']=[]
        dict_city_pb[str(buildnb)]['attic']=[]
        dict_city_pb[str(buildnb)]['user_air']=[]
        dict_city_pb[str(buildnb)]['inflation'] =[]
        dict_city_pb[str(buildnb)]['eeg'] = []
        dict_city_pb[str(buildnb)]['eex'] = []
        dict_city_pb[str(buildnb)]['el_ch'] = []
        dict_city_pb[str(buildnb)]['gas_ch'] = []
        dict_city_pb[str(buildnb)]['t_set'] = []
        dict_city_pb[str(buildnb)]['nb_occ'] = []

    for loop in range (Nloop):

        print('_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-')
        print('simulations n° : ', loop)
        print('_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-')
        print()

        # Save the City
        City = copy.deepcopy(ref_City)

        ############################################

        # ## Generate new City

        ############################################

        new_weather = list_weather[loop]

        City, sph_city_list, el_city_list, dhw_city_list, dict_build_pb = \
            MC_new_city_generation(City, new_weather, max_retro_year=max_retro_year,
                                   time_sp_force_retro=time_sp_force_retro,build_physic_unc=build_physic_unc,
                                   MC_analysis= MC_analysis, nb_occ_unc=nb_occ_unc)


        # Dictionary to keep track of sampling
        for buildingnb in dict_build_pb:
            #dict_city_pb[buildingnb]['year'].append(dict_build_pb[buildingnb]['year'])
            dict_city_pb[buildingnb]['infiltration'].append(dict_build_pb[buildingnb]['infiltration'])
            #dict_city_pb[buildingnb]['cellar'].append(dict_build_pb[buildingnb]['cellar'])
            #dict_city_pb[buildingnb]['attic'].append(dict_build_pb[buildingnb]['attic'])
            dict_city_pb[buildingnb]['user_air'].append(dict_build_pb[buildingnb]['user_air'])
            dict_city_pb[buildingnb]['t_set'].append(dict_build_pb[buildingnb]['tset_heat'])
            dict_city_pb[buildingnb]['nb_occ'].append(dict_build_pb[buildingnb]['nb_ocupants'])

        ############################################

        # ## Generate new energy systems

        ############################################

        #  Generate new energy systems

        City, dict_city_esys_samples = mc_esys.MC_rescale_esys(City, esys_unknown=dict_sample['esys'])

        ############################################

        # ## Get energy curves

        ############################################

        annual_el_dem = City.get_annual_el_demand()
        annual_th_dem = City.get_total_annual_th_demand()
        annual_dhw_dem = City.get_annual_dhw_demand()
        annual_sph_dem = City.get_annual_space_heating_demand()
        sph_curve = City.get_aggr_space_h_power_curve()
        dhw_curve = City.get_aggr_dhw_power_curve()
        el_curve = City.get_aggr_el_power_curve()
        max_sph = dimfunc.get_max_p_of_power_curve(sph_curve)
        max_el = dimfunc.get_max_p_of_power_curve(el_curve)
        max_dhw = dimfunc.get_max_p_of_power_curve(dhw_curve)

        ############################################

        # ## Energy balance

        ############################################

        # Energy balance calculations
        el_dem, gas_dem, rescale_boiler, rescale_EH, Lal_recaled, Rescale_tes = MC_EBB_calc(City)

        if rescale_boiler:
            Nboiler_rescaled += 1
        if rescale_EH:
            NEH_rescaled += 1
        if Lal_recaled:
            Lal_rescaled += 1
        if Tes_rescale:
            Tes_rescale +=1

        print()
        print('loop n°:  ', loop)
        print('boiler_rescaled =', rescale_boiler)
        print('EH_rescaled =', rescale_EH)
        print('Lal_rescaled=', Lal_recaled)
        print('Tes_rescaled = ', Rescale_tes)
        print()
        print('Annual electricity demand : ', annual_el_dem, 'kWh/year')
        print('Annual thermal demand : ', annual_th_dem, 'kWh/year')
        print('Annual Space Heating demand: ', annual_sph_dem, 'kWh/year')
        print('Annual domestic hot water demand: ', annual_dhw_dem, 'kWh/year')
        print()
        print('Annual reference electricity demand : ', ref_City.get_annual_el_demand(), 'kWh/year')
        print('Annual reference thermal demand : ', ref_City.get_total_annual_th_demand(), 'kWh/year')
        print ()
        print('Annual electricity demand after energy balance : ', el_dem, 'kWh/year')
        print('Annual gas demand after energy balance : ', gas_dem, 'kWh/year')
        print()

        ############################################

        # ## Economic analysis

        ############################################

        City, GHG_Emission, total_annuity, dict_eco_Sample = MC_new_economic_evaluation(City, time=time, interest=interest[loop])

        # Add results to result_arrays
        Gas_results[loop] = round(gas_dem,4)
        El_results[loop] = round(el_dem,4)
        Th_results[loop] = round(annual_th_dem, 4)

        # If tes rescaled don't take in account Annuity
        if Rescale_tes:
            Annuity_results[loop] = Annuity_results[loop-1]
        else:
            Annuity_results[loop] = round(total_annuity, 4)

        print (Rescale_tes)
        print ('annuity {}'.format(loop), Annuity_results[loop] )
        GHG_results[loop] = round(GHG_Emission,4)
        GHG_spe_results[loop] = round(GHG_Emission / (annual_sph_dem + annual_dhw_dem + annual_el_dem),4)

        # Keep track of electrical demand for EBB

        el_results2[loop] = round(sum(el_city_list),2)

        #  Dictionary to keep track of sampling
        for buildingnb in dict_build_pb:
            dict_city_pb[buildingnb]['inflation'].append(dict_eco_Sample['inflation'])
            dict_city_pb[buildingnb]['eeg'].append(dict_eco_Sample['eeg'])
            dict_city_pb[buildingnb]['eex'].append(dict_eco_Sample['eex'])
            dict_city_pb[buildingnb]['el_ch'].append(dict_eco_Sample['el_ch'])
            dict_city_pb[buildingnb]['gas_ch'].append(dict_eco_Sample['gas_ch'])

    return Th_results, Gas_results, El_results, Annuity_results, GHG_results, \
           GHG_spe_results, el_results2, dict_city_pb, Nboiler_rescaled, NEH_rescaled, Lal_rescaled, Tes_rescale


def MC_new_city_generation (City, new_weather, max_retro_year=2014, time_sp_force_retro=40,
                           build_physic_unc=True, MC_analysis=True, nb_occ_unc=True):
    """
       Performs city reevalution for Monte Carlo analysis

       Parameters
       ----------
       City : object
           City object of pycity_calc
       new_weather : object
           Weather object of pycity
       time_sp_force_retro : int, optional
           Timespan, in which a retrofit action is forced to the system.
           (default: 40).
       max_retro_year : int, optional
           Maximal / youngest possible retrofit year for sampling (default: 2014)
       nb_occ_unc : bool, optional
           Defines, if number of occupants per apartment is unknown
           (default: True).
           If set to True, number of occupants is unknown
           If set to False, uses number of occupants on occupancy objects
           as known values.
       MC_analysis: boolean, optional
               Defines extra modifications for monte carlo analysis
               (dormer,attic,cellar, net_floor_area)
       buil_physic_unc: bool, optional
           Defines,if building physics unknown or not (default: True)
           True - Building physics is unknown
           False - Building physics is known (year of modernisation, dormer, cellar
                   and attic are fixed, net floor area variation is smaller)

       Returns
       -------
       City :   object
                City object of pycity_calc modified for Monte Carlo analysis
        sph_city_list: list holding net space heating demands for each building in kWh as float
        el_city_list: list holding net electric energy demands for each building in kWh as float in kWh
        dhw_city_list: list holding hot water net energy demands for each building in kWh as float in kWh
        dict_build_problem : dict (of dictionaries)
        Dictionary of dictionaries holding parameters for each building
        Keys: 'build_id' : example: '1001'

       """

    # ## Initialisation
    sph_city_list = []
    el_city_list = []
    dhw_city_list = []
    dict_build_pb = {}

    # generation of a new weather
    new_weather = new_weather
    City.environment.weather = new_weather
    new_weather_list = []
    new_weather_list.append(new_weather)

    list_building = City.get_list_build_entity_node_ids()

    # ## Loop over building
    # #######################################################################

    for build in list_building:
        City.node[build]['entity'], dict_problem, el_demand, dhw_energy, sum_heat = \
            newB.new_building_evaluation_mc(City.node[build]['entity'], new_weather=new_weather_list,
                                                max_retro_year=max_retro_year, time_sp_force_retro=time_sp_force_retro,
                                                build_physic_unc=build_physic_unc, MC_analysis=MC_analysis,
                                                nb_occ_unc=nb_occ_unc)

        # List of energy demand for each building
        sph_city_list.append(sum_heat)
        el_city_list.append(el_demand)
        dhw_city_list.append (dhw_energy)

        # Get the sampling in a dictionary
        dict_build_pb[str(build)] = dict_problem


    print()
    print('*****************************************************************************************************')
    print('For EBB: Intermediate results for city')
    print('Space heating demand: ', sum(sph_city_list))
    print('Electrical demand : ', sum(el_city_list))
    print('DHW demand: ', sum(dhw_city_list))
    print('Thermal demand: ', sum(dhw_city_list)+sum(sph_city_list))
    print('*****************************************************************************************************')
    #print ('Comparaison with get annual demand:')
    #print('*****************************************************************************************************')
    #print('Annual electricity demand : ', City.get_annual_el_demand(), 'kWh/year')
    #print('Annual thermal demand : ', City.get_total_annual_th_demand(), 'kWh/year')
    #print('Annual space heating demand: ',City.get_annual_space_heating_demand(), 'kWh/year')
    #print('Annual dhw demand : ', City.get_annual_dhw_demand(), 'kWh/year')
    print('*****************************************************************************************************')
    print()

    return City, sph_city_list, el_city_list, dhw_city_list, dict_build_pb

def MC_new_economic_evaluation(City, time=10, interest=0.05):
    """
    Performs economic calculation for Monte Carlo analysis

    Parameters
    ----------
    City:   Object
            City object from pycity_calc
    time:   int
            Period in years for economic evaluation
    interest:   float
                Interest for economic calculation

    Returns
    -------
    City:       Object
                City object from pycity_calc
    gas_dem:    float
                Gas demand per year in kWh
    el_dem:     float
                El demand per year in kWh

    dict_eco_samples: Dictionary
    Dictionary with samples
    key: inflation sample
        eeg_change sample
        eex_change sample
        el_change sample
        gas_change sample

    """
    # Initialisation samples dictionary
    dict_eco_samples = {}

    #  Generate economic calculator object
    #print("Start Economic evaluation /n")
    #eco_inst = eco_calc.EconomicCalculation(time=time, interest=interest)

    ## Annuity Calculation
    # Get Market object
    Market_instance = Mark.GermanMarket()

    print("Start Economic evaluation /n")

    # New_price change factor
    inflation = rd.uniform(0.99, 1.01)
    eeg_change = rd.uniform(0.9, 1.1)
    eex_change = -eeg_change
    el_change = rd.uniform(0.99, 1.01)
    gas_change = rd.uniform(0.98, 1.02)

    dict_eco_samples['inflation']=inflation
    dict_eco_samples['eeg']=eeg_change
    dict_eco_samples['eex']=eex_change
    dict_eco_samples['el_ch']=el_change
    dict_eco_samples['gas_ch']=gas_change

    # Change factor follow inflation
    price_ch_cap = inflation
    price_ch_op = inflation

    # Change facrtor follow energy market trend
    price_ch_dem_gas = gas_change
    price_ch_dem_el = el_change
    price_ch_dem_el_hp = el_change

    # change factor follow eeg trend
    price_ch_proc_chp = eeg_change
    price_ch_proc_pv = eeg_change
    price_ch_EEG_Umlage_tax_chp = eeg_change
    price_ch_EEG_Umlage_tax_pv = eeg_change
    price_ch_avoid_grid_usage = eeg_change
    price_ch_sub_chp = eeg_change
    price_ch_self_usage_chp = eeg_change
    price_ch_gas_disc_chp = eeg_change
    price_ch_sub_pv =eeg_change

    # change factor follow eex market trend
    price_EEX_baseload_price = eex_change


    #  Generate economic calculator object
    eco_inst = eco_calc.EconomicCalculation(germanmarket=Market_instance, time=time, interest=interest,
                                                price_ch_cap=price_ch_cap,
                                                price_ch_dem_gas=price_ch_dem_gas, price_ch_dem_el=price_ch_dem_el,
                                                price_ch_op=price_ch_op, price_ch_proc_chp=price_ch_proc_chp,
                                                price_ch_proc_pv=price_ch_proc_pv,
                                                price_ch_eeg_chp=price_ch_EEG_Umlage_tax_chp,
                                                price_ch_eeg_pv=price_ch_EEG_Umlage_tax_pv,
                                                price_ch_eex=price_EEX_baseload_price,
                                                price_ch_grid_use=price_ch_avoid_grid_usage,
                                                price_ch_chp_sub=price_ch_sub_chp,
                                                price_ch_chp_self=price_ch_self_usage_chp,
                                                price_ch_chp_tax_return=price_ch_gas_disc_chp,
                                                price_ch_pv_sub=price_ch_sub_pv, price_ch_dem_el_hp=price_ch_dem_el_hp)

    # New lifetime and maintenance of energy systems
    for key1 in eco_inst.dict_lifetimes.keys():
        #Generation of a life_factor:
        life_factor = rd.uniform(0.8, 1.2)
        #reevaluation
        tempp = eco_inst.dict_lifetimes[key1] * life_factor
        eco_inst.dict_lifetimes[key1] = tempp

    for key2 in eco_inst.dict_maintenance.keys():
        # Generation of a maintenance_factor:
        maintenance_factor = rd.uniform(0.8, 1.2)
        tempp = eco_inst.dict_maintenance[key2] * maintenance_factor
        eco_inst.dict_maintenance[key2] = tempp

    # Annuity
    dem_rel_annuity = eco_inst.calc_dem_rel_annuity_city(City)
    total_proc_annuity = eco_inst.calc_proc_annuity_multi_comp_city(City)
    cap_rel_ann, op_rel_ann = eco_inst.calc_cap_and_op_rel_annuity_city(City)

    # Get total annuity
    total_annuity = eco_inst.calc_total_annuity(ann_capital=cap_rel_ann,
                                                ann_demand=dem_rel_annuity,
                                                ann_op=op_rel_ann,
                                                ann_proc=total_proc_annuity)

    print('Total_annuity:', round(total_annuity, 2), 'Euro/year')
    print()
    print("Start Emissions calculation /n")

    # CO2 object generation
    GHG = City.environment.co2emissions

    # Emissions calculation
    GHG_Emission = GHG_calc.CO2_emission_calc(city_object=City, emission_object=GHG, CO2_zero_lowerbound=False)

    print('Emissions: ', GHG_Emission, 'kg/year')

    return City, GHG_Emission, total_annuity , dict_eco_samples


def MC_EBB_calc (City):
    """
       Performs city energy balance for Monte Carlo analysis

       Parameters
       ----------
        City : object
           City object of pycity_calc

       Returns
       -------
        City :  object
            City object of pycity_calc modified
        Gas_dem:    float
                Gas demand per year in kWh
        el_dem:     float
                Electrical demand per year in kWh
        rescale_boiler: Boolean
                        True: City with rescaled boilers to cover all city energy demands
        rescale_EH : Boolean
                        True: City with rescaled EH to cover all city energy demands
        LaL_boiler_rescaled : Boolean
                        True: Lower Activation limit of boiler is set to 0
        Rescale_tes: Boolean
                        True: Tes has been rescaled to avoid error in energy balance

    """
    invalidind = EBB.invalidind
    rescale_boiler = False
    invalidind2 = EB.invalidind2
    print("Start energy balance")
    print()

    # Get dictionary of energy systems
    Calculator = EBB.calculator(City)
    dict_bes_data = Calculator.assembler()

    rescale_boiler=False
    rescale_EH=False
    LaL_boiler_rescaled = False
    Rescale_tes = False

    # Loop over energy systems
    try:
        for i in range(len(dict_bes_data)):
            City, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)

    except invalidind:
        # Get list of building and rescale boiler or EH
        list_of_building = City.get_list_build_entity_node_ids()
        for build in list_of_building:
            # Get max demand building
            demand_building = dimfunc.get_max_power_of_building(City.node[build]['entity'], with_dhw=True)
            # Start try to rescale just LAl boiler or EH
            if City.node[build]['entity'].bes.hasBoiler == True:
                City.node[build]['entity'].bes.boiler.lowerActivationLimit = 0
                LaL_boiler_rescaled = True

                print()
                print('Rescale LAl boiler')
                print('new boiler Lal kW: ', City.node[build]['entity'].bes.boiler.lowerActivationLimit )
                print()

            if City.node[build]['entity'].bes.hasElectricalHeater == True:
                City.node[build]['entity'].bes.electricalHeater.qNominal = \
                    dimfunc.round_esys_size(demand_building /City.node[build]['entity'].bes.electricalHeater.eta,
                                            round_up=True)
                rescale_EH = True

                print()
                print('Rescale EH')
                print('new EH capacity kW: ', City.node[build]['entity'].bes.electricalHeater.qNominal / 1000)
                print()

        # Do another time EBB
        for i in range(len(dict_bes_data)):
            try:
                City, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)

            except invalidind:
                # Get list of building and rescale boiler or EH
                list_of_building = City.get_list_build_entity_node_ids()
                for build in list_of_building:
                    # get max building demand
                    demand_building = dimfunc.get_max_power_of_building(City.node[build]['entity'], with_dhw=True)
                    # Rescal Boiler capacity
                    if City.node[build]['entity'].bes.hasBoiler == True:
                        City.node[build]['entity'].bes.boiler.qNominal = \
                            dimfunc.round_esys_size(demand_building * 1.00 / City.node[build]['entity'].bes.boiler.eta,
                                                    round_up=True)
                        rescale_boiler = True

                        print()
                        print('Rescale boiler')
                        print('new boiler capacity kW: ', City.node[build]['entity'].bes.boiler.qNominal / 1000)
                        print()

                    if City.node[build]['entity'].bes.hasElectricalHeater == True:
                        City.node[build]['entity'].bes.electricalHeater.qNominal = \
                            dimfunc.round_esys_size(
                                demand_building * 1.1 / City.node[build]['entity'].bes.electricalHeater.eta,
                                round_up=True)
                        rescale_EH = True

                        print()
                        print('Rescale EH for the second time')
                        print('new EH capacity kW: ', City.node[build]['entity'].bes.electricalHeater.qNominal / 1000)
                        print()





                # Do another time EBB
                for i in range(len(dict_bes_data)):
                    try:
                        City, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)

                    except invalidind:
                        # Get list of building and rescale boiler or EH
                        list_of_building = City.get_list_build_entity_node_ids()
                        for build in list_of_building:
                            # get max building demand
                            demand_building = dimfunc.get_max_power_of_building(City.node[build]['entity'], with_dhw=True)
                            # Rescal Boiler capacity
                            if City.node[build]['entity'].bes.hasTes == True:
                                City.node[build]['entity'].bes.tes.capacity = City.node[build]['entity'].bes.tes.capacity*100000

                            print()
                            print('Rescale Tes')
                            print('new Tes capacity kW: ', City.node[build]['entity'].bes.boiler.qNominal / 1000)
                            print()

                        Rescale_tes = True

                        # Do another time EBB
                        for i in range(len(dict_bes_data)):
                            City, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)


    except invalidind2:
        # Get list of building and rescale boiler
        list_of_building = City.get_list_build_entity_node_ids()
        for build in list_of_building:
            # Get max demand building
            demand_building = dimfunc.get_max_power_of_building(City.node[build]['entity'], with_dhw=True)
            # Rescaled boiler
            if City.node[build]['entity'].bes.hasBoiler == True:
                City.node[build]['entity'].bes.boiler.qNominal = \
                    dimfunc.round_esys_size(demand_building * 1.05 / City.node[build]['entity'].bes.boiler.eta,
                                            round_up=True)
                rescale_boiler = True

                print()
                print('Rescale boiler')
                print('new boiler capacity kW: ', City.node[build]['entity'].bes.boiler.qNominal / 1000)
                print()

            if City.node[build]['entity'].bes.hasElectricalHeater == True:
                City.node[build]['entity'].bes.electricalHeater.qNominal =\
                    dimfunc.round_esys_size(demand_building*1.05/City.node[build]['entity'].bes.electricalHeater.eta,
                                            round_up=True)

                rescale_EH = True

                print()
                print('Rescale EH')
                print('new EH capacity kW: ', City.node[build]['entity'].bes.electricalHeater.qNominal / 1000)
                print()

            # Do another time EBB
            for i in range(len(dict_bes_data)):

                City, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)

    # ## Gas and electrical demand
    el_dem = 0
    gas_dem = 0

    for n in City.nodes():
        if 'node_type' in City.node[n]:
            #  If node_type is building
            if City.node[n]['node_type'] == 'building':
                #  If entity is kind building
                if City.node[n]['entity']._kind == 'building':
                    if 'electrical demand' in City.node[n]:
                        el_dem += sum(City.node[n]['electrical demand']) *\
                                  City.environment.timer.timeDiscretization / 1000 / 3600

                    if 'fuel demand' in City.node[n]:
                        gas_dem += sum(City.node[n]['fuel demand']) * \
                                   City.environment.timer.timeDiscretization / 1000 / 3600

    return el_dem, gas_dem, rescale_boiler, rescale_EH, LaL_boiler_rescaled, Rescale_tes

if __name__ == '__main__':

    #  User Inputs
    #  ##############################
    nb_samples = 100
    time_sp_force_retro = 50
    max_retro_year = 2014
    nb_occ_unc = True
    MC_analysis = True
    build_physic_unc = True
    esys_unc = True
    Interest = 0.05
    esys_filename = 'City_lolo_esys.txt'
    city_f_name = 'aachen_kronenberg_3_mfh_ref_1.pkl'
    time = 10 #years

    #  End of user Inputs
    #  ##############################

    this_path = os.path.dirname(os.path.abspath(__file__))

    city_path = os.path.join(this_path,'City_generation', 'output', city_f_name)

    city = pickle.load(open(city_path, mode='rb'))

    #  Add energy systems to city
    gen_esys = True  # True - Generate energy networks
    gen_e_net = False # True - Generate energy networks
    dhw_dim_esys = True  # Use dhw profiles for esys dimensioning

    #  Path to energy system input file (csv/txt; tab separated)
    #esys_filename = 'lolo_esys.txt'
    esys_path = os.path.join(this_path, 'City_generation', 'input', 'input_esys_generator', esys_filename)

    # Generate energy systems for city district
    if gen_esys:
        #  Load energy networks planing data
        list_esys = mc_esys.load_enersys_input_data(esys_path)
        print('Add energy systems')

        #  Generate energy systems
        mc_esys.gen_esys_for_city(city=city, list_data=list_esys)


    # Add energy networks to city
    if gen_e_net:  # True - Generate energy networks

        #  Path to energy network input file (csv/txt; tab separated)
        network_filename = 'lolo_networks.txt'

        network_path = os.path.join(this_path, 'City_generation', 'input', 'input_en_network_generator',
                                        network_filename)
        #  Load energy networks planing data
        dict_e_net_data = City_gen.enetgen.load_en_network_input_data(network_path)

        City_gen.enetgen.add_energy_networks_to_city(city=city, dict_data=dict_e_net_data)

    # Add street generator:
    #street_g = True
    #path_street = os.path.join(this_path, 'City_generation', 'input', 'street_generator', 'street_edges_cluster_simple.csv')
    #path_edges = os.path.join(this_path, 'City_generation', 'input', 'street_generator', 'street_nodes_cluster_simple.csv')
    #if street_g:
        #name_list, pos_list, edge_list = street_gen.load_street_data_from_csv( path_str_nodes=path_edges ,path_str_edges=path_street)


        #street_gen.add_street_network_to_city(city_object=city, name_list=name_list, pos_list=pos_list, edge_list=edge_list)

    #print (name_list )
    #print (pos_list)
    #print (edge_list)

    #for key in city.node:
        #for key2 in city.node[key]:
            #print(key2, '--', city.node[key][key2])

    #for key in city.edge:
        #for key2 in city.edge[key]:
            #print(key2, '--', city.edge[key][key2])

    dict_pam = {}
    dict_pam['Nsamples'] = nb_samples
    dict_pam['MC_analysis'] = MC_analysis
    dict_pam['build_physic_unc'] = build_physic_unc
    dict_pam['nb_occ_unc'] = nb_occ_unc
    dict_pam['esys'] = esys_unc
    dict_pam['time_sp_force_retro'] = time_sp_force_retro
    dict_pam['max_retro_year'] = max_retro_year
    dict_pam['interest']=[]
    for i in range (nb_samples):
        dict_pam['interest'].append(Interest)

    dict_pam['weather'] = wea.gen_set_of_weathers(nb_samples)
    dict_pam['time']=time
    #  Perform MC analysis for whole city
    (Th_results, Gas_results, El_results, Annuity_results, GHG_results, \
           GHG_spe_results, el_results2, dict_city_pb, Nboiler_rescaled, NEH_rescaled, Lal_rescaled, Tes_rescaled) = \
        new_city_evaluation_monte_carlo(ref_City=city, dict_sample=dict_pam)

    #  Results
    #  ##################################################################
    print ('Nboiler rescaled : ', Nboiler_rescaled)
    print('NEH rescaled : ', NEH_rescaled)
    print ('Lal rescaled : ', Lal_rescaled)

    fig = plt.figure()
    # the histogram of the data
    plt.hist(Th_results, 100)
    plt.xlabel('Thermal energy demand in kWh')
    plt.ylabel('Number of values')
    plt.show()
    plt.close()

    plt.close()

