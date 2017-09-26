#!/usr/bin/env python
# coding=utf-8

'''

Script to do Monte Carlo simulations

'''

import copy
import pycity_calc.toolbox.mc_helpers.Uncertainties_analysis.MC_new_building as newB
import pycity_calc.cities.scripts.overall_gen_and_dimensioning as City_gen
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
            interest_low:   list
                        Holding interest rate for economic calculation low
            interest_medium:   list
                            Holding interest rate for economic calculation medium
            interest_high:   list
                        Holding interest rate for economic calculation high
            time:   int
                    Time for economic calculation in years (default: 10)
        Returns
        -------
        res_tuple : tuple (of Array)
            Results tuple (Th_results, el_results_net, Gas_results, El_results, Annuity_results,\
           Annuity_results_high, Annuity_results_low,  Annuity_results_ec1, Annuity_results_ec2, Annuity_results_ec3,\
           GHG_results, GHG_spe_results, Nb_Lal_rescaled, Nb_boiler_medium_rescaled, Nb_boiler_high_rescaled,\
           Nb_Tes_rescale, Nb_EH_small_rescaled, Nb_EH_medium_rescaled, Nb_EH_high_rescaled)

            1. Array holding net space heating demands in kWh as float
            2. Array holding electrical demand for EBB in kWh as float (sum of buildings demand)
            3. Array holding Gas demands after EBB in kWh as float
            4. Array holding Electrical demands after EBB in kWh as float
            5. Array holding Annuity in Euro as float, interest medium (current value to 0.05)
            6. Array holding specific annuity in Euro/kwh as float, interest medium (current value to 0.05)
            7 Annuity_results_high: Array holding Annuity in Euro as float, interest high(current value to 0.07)
            8. Annuity_results_m: Array holding Annuity in Euro as float, interest low (current value to 0.03)
            9. Annuity_results_ec1: Array holding Annuity in Euro as float, interest medium , ec1 (economic setting 1)
            10. Annuity_results_ec2: Array holding Annuity in Euro as float, interest medium , ec2 (economic setting 2)
            11. Annuity_results_ec3: Array holding Annuity in Euro as float, interest medium , ec3 (economic setting 3)
            12. Array holding GHG emissions in kg as float
            13. Array holding specific GHG emissions in kg as float
            14 Lal_rescaled : Boolean, True: Lower Activation limit of boiler is set to 0 and boiler is rescaled of 10%
            15. rescale_boiler_second_time: Boolean, City with rescaled boilers to cover all city energy demands: 20%
            16. rescale_boiler_third_time: Boolean, City with rescaled boilers to cover all city energy demands: 50%
            17. Rescale_tes: Boolean, Tes has been rescaled to avoid error in energy balance:
                Big rescale: capacity = 10000000 kg and boiler rescale of *1000% and Electric heater rescaled of 10000%
            18. Rescale_eh_first_time: Boolean, City with rescaled EH to cover all city energy demands
                (small: 10% rescaling)
            19. rescale_eh_second_time : Boolean, City with rescaled EH to cover all city energy demands
                (medium: 20% rescaling)
            20. Rescal_eh_third_time:  Boolean, City with rescaled EH to cover all city energy demands
                (high: 50% rescaling)

        """

    # Save the City
    City = copy.deepcopy(ref_City)

    Nloop = dict_sample['Nsamples']

    Gas_results = np.zeros(Nloop)   # array of annual gas demand
    El_results = np.zeros(Nloop)    # array of annual electrical demand after energy balance
    Th_results = np.zeros(Nloop)    # array of annual thermal demand of the city before EBB
                                    #  (sum of DHW and Space heating demand)
    el_results_net = np.zeros(Nloop) # Array for electricity need of the city before EBB

    PV_el_sold = np.zeros(Nloop)  #array of annual electricity sold by PV
    PV_el_self_used = np.zeros(Nloop)  #array of annual electricity self used by PV
    CHP_el_sold = np.zeros(Nloop)  # array of annual electricity sold by CHP
    CHP_el_self_used = np.zeros(Nloop)  # array of annual electricity self used by CHP

    Nb_Lal_rescaled = 0 # Number of city with rescaled boiler lal (10%)
    Nb_boiler_medium_rescaled = 0  # number of boiler 20 % rescaled (thermal demand to high)
    Nb_boiler_high_rescaled = 0  # number of boiler 50 % rescaled (thermal demand to high)

    Nb_Tes_rescale = 0 # Number of City with rescaled thermal storage

    Nb_EH_small_rescaled = 0 #Number of City with rescaled Electrical heater small: 10%
    Nb_EH_medium_rescaled = 0  # number of electrical heater 20 % rescaled (thermal demand to high)
    Nb_EH_high_rescaled = 0 #Number of City with rescaled electrcial heater total: 50%


    # Initialisation of arrays
    Annuity_results = np.zeros(Nloop)  # Array of total annuity for the medium interest: current value: 0.05
    Annuity_spe_results = np.zeros(Nloop)  # Array of specific annuity for the medium interest: current value: 0.05
    GHG_results = np.zeros(Nloop)  # Array for GHG emission
    GHG_spe_results = np.zeros(Nloop)  # Array for GHG emissions specific

    Annuity_results_high = np.zeros(Nloop)  # Array of total annuity for high interest: current value: 0.07
    Annuity_results_low = np.zeros(Nloop)  # Array of total annuity for low interest: current value: 0.03

    # other economic scenario uncertainties (other settings of the price change factors)
    Annuity_results_ec1 = np.zeros(Nloop)  # Array of total annuity for ec1
    Annuity_results_ec2 = np.zeros(Nloop)  # Array of total annuity for ec2
    Annuity_results_ec3 = np.zeros(Nloop)  # Array of total annuity for ec3

    # Initialisation of variables
    list_weather = dict_sample['weather']
    MC_analysis = dict_sample['MC_analysis']
    nb_occ_unc = dict_sample ['nb_occ_unc']
    build_physic_unc = dict_sample['build_physic_unc']
    time_sp_force_retro = dict_sample['time_sp_force_retro']
    max_retro_year = dict_sample['max_retro_year']
    interest_low = dict_sample['interest_low']
    interest_medium = dict_sample['interest_medium']
    interest_high = dict_sample['interest_high']
    time = dict_sample['time']

    # primary energy factor related to the the thermal demand energy of the city:
    # so assuming conventianal energy systems: gas boiler, with the default value define in pyCity: efficiency 0.85
    pheat_factor_ref = ref_City.environment.co2emissions.pe_gas * 1/0.85

    # Initialisation dictionary to keep track of samples list
    # Not used later but it was useful to check eventual problems
    dict_city_pb = {}
    th_pow_ref = {}
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

       # get dictionnary of max thermal power for lhn cost calculation
        th_pow_ref[str(buildnb)] = max(City.node[buildnb]['entity'].get_space_heating_power_curve())

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
            dict_city_pb[buildingnb]['year'].append(dict_build_pb[buildingnb]['year'])
            dict_city_pb[buildingnb]['infiltration'].append(dict_build_pb[buildingnb]['infiltration'])
            dict_city_pb[buildingnb]['cellar'].append(dict_build_pb[buildingnb]['cellar'])
            dict_city_pb[buildingnb]['attic'].append(dict_build_pb[buildingnb]['attic'])
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
        #sph_curve = City.get_aggr_space_h_power_curve()
        #dhw_curve = City.get_aggr_dhw_power_curve()
        #el_curve = City.get_aggr_el_power_curve()
        #max_sph = dimfunc.get_max_p_of_power_curve(sph_curve)
        #max_el = dimfunc.get_max_p_of_power_curve(el_curve)
        #max_dhw = dimfunc.get_max_p_of_power_curve(dhw_curve)

        ############################################

        # ## Energy balance

        ############################################

        # Energy balance calculations
        el_dem, gas_dem, Lal_rescaled, rescale_boiler_second_time, rescale_boiler_third_time, Rescaled_tes, \
        Rescale_eh_first_time, rescale_eh_second_time, Rescal_eh_third_time, pv_sold,\
        pv_used_self, chp_sold, chp_self_used = MC_EBB_calc(City)

        # Counter of rescaled energy systems during EBB
        if Lal_rescaled:
            Nb_Lal_rescaled += 1
        if rescale_boiler_second_time:
            Nb_boiler_medium_rescaled+= 1
        if rescale_boiler_third_time:
            Nb_boiler_high_rescaled +=1

        if Rescaled_tes:
            Nb_Tes_rescale +=1

        if Rescale_eh_first_time:
            Nb_EH_small_rescaled +=1
        if rescale_eh_second_time:
            Nb_EH_medium_rescaled += 1
        if Rescal_eh_third_time:
            Nb_EH_high_rescaled +=1


        print()
        print('loop n°:  ', loop)
        print('boiler rescaling =', Lal_rescaled, rescale_boiler_second_time, rescale_boiler_third_time)
        print('EH_rescaled =', Rescale_eh_first_time, rescale_eh_second_time, Rescal_eh_third_time)
        print('Tes_big_rescaling = ', Rescaled_tes)
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

        # Do the simulation for the different interest
        City, GHG_Emission_l, total_annuity_low, dict_eco_Sample_low = \
            MC_new_economic_evaluation(City, time=time, interest=interest_low, th_pow_ref= th_pow_ref)
        print ('End eco analysis i low')
        City, GHG_Emission_m, total_annuity_medium, dict_eco_Sample_m = \
            MC_new_economic_evaluation(City, time=time, interest=interest_medium,  th_pow_ref= th_pow_ref)
        print('End eco analysis i medium')
        City, GHG_Emission_h, total_annuity_high, dict_eco_Sample_h = \
            MC_new_economic_evaluation(City, time=time, interest=interest_high,  th_pow_ref= th_pow_ref)
        print('End eco analysis i high')

        # Do other economic calculations for specific economic scenario, other settings of the price change factors

        City, GHG_Emission, total_annuity_ec1, dict_eco = MC_new_economic_evaluation(City, time=time,
                                                                                        interest=interest_medium,
                                                                                        th_pow_ref=th_pow_ref,
                                                                                     scenario='scenario_eco1')
        print('End eco analysis ec1')
        City, GHG_Emission_m, total_annuity_ec2, dict_eco = MC_new_economic_evaluation(City, time=time,
                                                                                              interest=interest_medium,
                                                                                              th_pow_ref=th_pow_ref,
                                                                                       scenario='scenario_eco2')
        print('End eco analysis ec2')
        City, GHG_Emission_h, total_annuity_ec3, dict_eco = MC_new_economic_evaluation(City, time=time,
                                                                                              interest=interest_medium,
                                                                                              th_pow_ref=th_pow_ref,
                                                                                       scenario='scenario_eco3')
        print('End eco analysis ec3')

        # Add results to result_arrays
        Gas_results[loop] = round(gas_dem,4)
        El_results[loop] = round(el_dem,4)
        Th_results[loop] = round(annual_th_dem, 4)
        # Keep track of electrical demand for EBB
        el_results_net[loop] = round(sum(el_city_list), 2)

        PV_el_sold [loop] = pv_sold  # array of annual electricity sold by CHP
        PV_el_self_used [loop] = pv_used_self  # array of annual electricity self used by CHP
        CHP_el_sold [loop] = chp_sold # array of annual electricity sold by CHP
        CHP_el_self_used [loop] = chp_self_used # array of annual electricity self used by CHP

        # If tes rescaled don't take Annuity and GHG in account (crazy values)
        if Rescaled_tes:
            Annuity_results[loop] = Annuity_results[loop-1]
            Annuity_spe_results[loop] = Annuity_spe_results[loop - 1]
            Annuity_results_high[loop] = Annuity_results_high[loop - 1]
            Annuity_results_low[loop] = Annuity_results_low[loop - 1]
            GHG_results[loop] = GHG_results[loop -1]
            GHG_spe_results[loop] = GHG_spe_results[loop -1]


            Annuity_results_ec1[loop] = Annuity_results_ec1[loop - 1]
            Annuity_results_ec2[loop] = Annuity_results_ec2[loop - 1]
            Annuity_results_ec3[loop] = Annuity_results_ec3[loop - 1]

        else:
            Annuity_results[loop] = round(total_annuity_medium, 4)
            Annuity_spe_results [loop] = round(total_annuity_medium/
                                               ((annual_sph_dem + annual_dhw_dem)*pheat_factor_ref +
                                                annual_el_dem*ref_City.environment.co2emissions.pe_total_el_mix) ,4)

            Annuity_results_high[loop] = round(total_annuity_high, 4)
            Annuity_results_low[loop] = round(total_annuity_low, 4)

            Annuity_results_ec1[loop] = round(total_annuity_ec1, 4)
            Annuity_results_ec2[loop] = round(total_annuity_ec2, 4)
            Annuity_results_ec3[loop] = round(total_annuity_ec3, 4)

            # Add GHG  to array results
            GHG_results[loop] = round(GHG_Emission, 4)
            GHG_spe_results[loop] = round(GHG_Emission /
                                          ((annual_sph_dem + annual_dhw_dem)*pheat_factor_ref +
                                           annual_el_dem*ref_City.environment.co2emissions.pe_total_el_mix),4)


        # Dictionary to keep track of samples list
        # Not used later but it was useful to check eventual problems
        for buildingnb in dict_build_pb:
            dict_city_pb[buildingnb]['inflation'].append(dict_eco_Sample_low['inflation'])
            dict_city_pb[buildingnb]['eeg'].append(dict_eco_Sample_low['eeg'])
            dict_city_pb[buildingnb]['eex'].append(dict_eco_Sample_low['eex'])
            dict_city_pb[buildingnb]['el_ch'].append(dict_eco_Sample_low['el_ch'])
            dict_city_pb[buildingnb]['gas_ch'].append(dict_eco_Sample_low['gas_ch'])

    return Th_results, el_results_net, Gas_results, El_results, Annuity_results, Annuity_spe_results,\
           Annuity_results_high, Annuity_results_low,  Annuity_results_ec1, Annuity_results_ec2, Annuity_results_ec3,\
           GHG_results, GHG_spe_results, Nb_Lal_rescaled, Nb_boiler_medium_rescaled, Nb_boiler_high_rescaled,\
           Nb_Tes_rescale, Nb_EH_small_rescaled, Nb_EH_medium_rescaled, Nb_EH_high_rescaled, PV_el_self_used, PV_el_sold



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
    print('*****************************************************************************************************')
    print()

    return City, sph_city_list, el_city_list, dhw_city_list, dict_build_pb

def MC_new_economic_evaluation(City, time=10, interest=0.05, scenario='scenario_eco0', th_pow_ref = None):
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
    th_pow_ref: dict
        If different from None: Take this maximum thermal power to calculate lhn specific costs

    Returns
    -------

    City:       Object
                City object from pycity_calc
    GHG_Emission:    float
                GHG emissions per year in kg
    total_annuity:     float
                annuity per year in Euro

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

    ## Annuity Calculation
    # Get Market object
    Market_instance = Mark.GermanMarket()

    print("Start Economic evaluation /n")

    if scenario=='scenario_eco0':
        # New_price change factor
        inflation = rd.uniform(0.99, 1.04)

        eeg_change = rd.uniform(0.93, 1.05)
        eex_change = rd.uniform(0.95, 1.05)
        #eex_change = 1 - eeg_change
        # electricity +/-5%
        el_change = rd.uniform(0.95, 1.05)
        # gas +/-5%
        gas_change = rd.uniform(0.95, 1.05)


    elif scenario=='scenario_eco1':
        # New_price change factor
        inflation = rd.uniform(0.99, 1.01)
        # -5% each year
        eeg_change = rd.uniform(0.945, 0.955)
        eex_change = 1-eeg_change
        # energy price increasing +5%
        el_change = rd.uniform(1.045, 1.055)
        gas_change = rd.uniform(1.045, 1.055)

    elif scenario=='scenario_eco2':
        # New_price change factor
        inflation = rd.uniform(0.99, 1.01)
        # fix energy taxes/subsidies
        eeg_change = 1
        eex_change = 1
        # electricity stay constant +/-0.5%
        el_change = rd.uniform(0.995, 1.005)
        # gas stay constant +/-0.5%
        gas_change = rd.uniform(0.995, 1.005)

    elif scenario=='scenario_eco3':
        # New_price change factor
        inflation = rd.uniform(0.99, 1.01)
        # +5% each year
        eeg_change = rd.uniform(1.045, 1.055)
        eex_change = 1-eeg_change
        # -5% each year
        el_change = rd.uniform(0.945, 0.955)
        gas_change = rd.uniform(0.945, 0.955)

    else : # scenario 4
        # New_price change factor
        inflation = rd.uniform(0.99, 1.01)
        # decrease of 7%
        eeg_change = rd.uniform(0.925, 0.935)
        # increase of 4%
        eex_change = rd.uniform(1.035, 1.045)
        # electrcity price decreasing -3%
        el_change = rd.uniform(0.965, 0.975)
        # gas price increase of 3%
        gas_change = rd.uniform(1.025, 1.035)

    dict_eco_samples['inflation']= inflation
    dict_eco_samples['eeg']= eeg_change
    dict_eco_samples['eex']= eex_change
    dict_eco_samples['el_ch']= el_change
    dict_eco_samples['gas_ch']= gas_change

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

    # fixed change factor
    price_ch_avoid_grid_usage = 1
    price_ch_sub_chp = 1
    price_ch_self_usage_chp = 1
    price_ch_gas_disc_chp = 1
    price_ch_sub_pv = 1

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
        life_factor = rd.normalvariate(mu=1, sigma=0.1)
        if life_factor < 0.5:
            life_factor = 1
        elif life_factor > 1.5:
            life_factor= 1

        #reevaluation
        tempp = eco_inst.dict_lifetimes[key1] * life_factor
        eco_inst.dict_lifetimes[key1] = tempp

    for key2 in eco_inst.dict_maintenance.keys():
        # Generation of a maintenance_factor:
        maintenance_factor = rd.normalvariate(mu=1, sigma=0.1)

        if  maintenance_factor < 0.5:
            maintenance_factor = 1
        elif  maintenance_factor > 1.5:
            maintenance_factor = 1
        tempp = eco_inst.dict_maintenance[key2] * maintenance_factor

        eco_inst.dict_maintenance[key2] = tempp

    # Annuity
    dem_rel_annuity = eco_inst.calc_dem_rel_annuity_city(City)
    total_proc_annuity = eco_inst.calc_proc_annuity_multi_comp_city(City)
    cap_rel_ann, op_rel_ann = eco_inst.calc_cap_and_op_rel_annuity_city(City, cost_spe=True, tes_pow_ref=th_pow_ref)

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
        Lal_rescaled : Boolean
                        True: Lower Activation limit of boiler is set to 0 and boiler is rescaled of 10%
        rescale_boiler_second_time: Boolean
                        True: City with rescaled boilers to cover all city energy demands: 20%
        rescale_boiler_third_time: Boolean
                            True: City with rescaled boilers to cover all city energy demands: 50%

        Rescale_tes: Boolean
                        True: Tes has been rescaled to avoid error in energy balance: Big rescale: capacity = 10000000 kg
                        and boiler rescale of *1000% and Electric heater rescaled of 10000%
        Rescale_eh_first_time: Boolean
            True: City with rescaled EH to cover all city energy demands (small: 10% rescaling)
        rescale_eh_second_time : Boolean
            True: City with rescaled EH to cover all city energy demands (medium: 20% rescaling)
        Rescal_eh_third_time:  Boolean
            True: City with rescaled EH to cover all city energy demands (high: 50% rescaling)
        pv_sold: float
                Electricity from pv sold on the public market in kWh
        pv_used_self: float
                Electricity from pv used for the city supply in kWh
        chp_sold: float
                Electricity from chp sold on the public market in kWh
        chp_self_used: float
                Electricity from chp used for the city supply in kWh

    """
    # Get special invalidind error of EBB
    invalidind = EBB.invalidind
    invalidind2 = EB.invalidind2

    print("Start energy balance")
    print()

    # Get dictionary of energy systems
    Calculator = EBB.calculator(City)
    dict_bes_data = Calculator.assembler()

    # Initialization of Boolean to keep track of rescaled energy systems

    Lal_rescaled= False
    rescale_boiler_second_time= False
    rescale_boiler_third_time = False
    Rescaled_tes= False
    Rescale_eh_first_time = False
    rescale_eh_second_time = False
    Rescal_eh_third_time = False

    # Loop over energy systems
    try:
        for i in range(len(dict_bes_data)):
            City, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)


    except invalidind:
        # ## Rescale LAL boiler or EH
        # Get list of building and rescale boiler or EH
        list_of_building = City.get_list_build_entity_node_ids()
        for build in list_of_building:
            # Start try to rescale boiler or EH
            if City.node[build]['entity'].bes.hasBoiler == True:
                City.node[build]['entity'].bes.boiler.lowerActivationLimit = 0
                Lal_rescaled = True

                print()
                print('Rescale LAl boiler')
                print('new boiler Lal kW: ', City.node[build]['entity'].bes.boiler.lowerActivationLimit)
                print()

            if City.node[build]['entity'].bes.hasBoiler == True:
                City.node[build]['entity'].bes.boiler.qNominal = \
                City.node[build]['entity'].bes.boiler.qNominal * 1.1 / City.node[build]['entity'].bes.boiler.eta

                # rescale_boiler_small = True

                print()
                print('Rescale boiler first round 10%')
                print('new boiler capacity kW: ', City.node[build]['entity'].bes.boiler.qNominal / 1000)
                print()

            if City.node[build]['entity'].bes.hasElectricalHeater == True:
                City.node[build]['entity'].bes.electricalHeater.qNominal = \
                    City.node[build]['entity'].bes.electricalHeater.qNominal * 1.1 \
                    / City.node[build]['entity'].bes.electricalHeater.eta

                Rescale_eh_first_time = True

                print()
                print('Rescale EH first round 10%')
                print('new EH capacity kW: ', City.node[build]['entity'].bes.electricalHeater.qNominal / 1000)
                print()

        # Do another time EBB
        for i in range(len(dict_bes_data)):
            try:
                City, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)

            except invalidind:
                ## Rescale boiler or resyze EH

                # Get list of building and rescale boiler or EH
                list_of_building = City.get_list_build_entity_node_ids()
                for build in list_of_building:
                    # Rescal Boiler capacity
                    if City.node[build]['entity'].bes.hasBoiler == True:
                        City.node[build]['entity'].bes.boiler.qNominal = \
                            City.node[build]['entity'].bes.boiler.qNominal * 1.2

                        rescale_boiler_second_time = True

                        print()
                        print('Rescale boiler second round ')
                        print('new boiler capacity kW: ', City.node[build]['entity'].bes.boiler.qNominal / 1000)
                        print()

                    # Rescal TES capacity
                    if City.node[build]['entity'].bes.hasTes == True:
                        City.node[build]['entity'].bes.tes.capacity = City.node[build]['entity'].bes.tes.capacity * 1.1

                        print()
                        print('Rescale Tes first round 10%')
                        print('new Tes capacity kg: ', City.node[build]['entity'].bes.tes.capacity)
                        print()

                    if City.node[build]['entity'].bes.hasElectricalHeater == True:
                        City.node[build]['entity'].bes.electricalHeater.qNominal = \
                            City.node[build]['entity'].bes.electricalHeater.qNominal * 1.2

                        rescale_eh_second_time = True

                        print()
                        print('Rescale EH for the second time 20%')
                        print('new EH capacity kW: ', City.node[build]['entity'].bes.electricalHeater.qNominal / 1000)
                        print()

                # Do another time EBB
                for i in range(len(dict_bes_data)):
                    try:
                        City, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)

                    except invalidind:
                        # Resize boiler totally

                        # Get list of building and rescale boiler or EH
                        list_of_building = City.get_list_build_entity_node_ids()
                        for build in list_of_building:
                            # Rescal Boiler capacity
                            if City.node[build]['entity'].bes.hasBoiler == True:
                                City.node[build]['entity'].bes.boiler.qNominal = City.node[build][
                                                                                 'entity'].bes.boiler.qNominal * 1.5

                                rescale_boiler_third_time = True
                                print()
                                print('Rescale boiler third time: 50%')
                                print('new boiler capacity kW: ', City.node[build]['entity'].bes.boiler.qNominal / 1000)
                                print()

                            if City.node[build]['entity'].bes.hasElectricalHeater == True:
                                City.node[build]['entity'].bes.electricalHeater.qNominal = \
                                    City.node[build]['entity'].bes.electricalHeater.qNominal * 1.5

                                Rescal_eh_third_time = True

                                print()
                                print('Rescale EH for the third time 50%')
                                print('new EH capacity kW: ',
                                      City.node[build]['entity'].bes.electricalHeater.qNominal / 1000)
                                print()

                        # Do another time EBB
                        for i in range(len(dict_bes_data)):
                            try:
                                City, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)

                            except invalidind:
                                ## Resvale TES
                                # Get list of building
                                list_of_building = City.get_list_build_entity_node_ids()

                                for build in list_of_building:

                                    # Rescal TES capacity
                                    if City.node[build]['entity'].bes.hasTes == True:
                                        City.node[build]['entity'].bes.tes.capacity = City.node[build][
                                                                                          'entity'].bes.tes.capacity * 100000

                                        print()
                                        print('Rescale Tes totally')
                                        print('new Tes capacity kg: ', City.node[build]['entity'].bes.tes.capacity)
                                        print()

                                        Rescaled_tes = True

                                    # Rescal Boiler capacity
                                    if City.node[build]['entity'].bes.hasBoiler == True:
                                        City.node[build]['entity'].bes.boiler.qNominal = \
                                            City.node[build]['entity'].bes.boiler.qNominal * 10

                                    if City.node[build]['entity'].bes.hasElectricalHeater == True:
                                        City.node[build]['entity'].bes.electricalHeater.qNominal = \
                                            City.node[build]['entity'].bes.electricalHeater.qNominal * 10

                                        print()
                                        print('Rescale EH totally')
                                        print('new EH capacity kW: ',City.node[build]['entity'].bes.electricalHeater.qNominal / 1000)
                                        print()

                                # Do another time EBB
                                for i in range(len(dict_bes_data)):
                                    City, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)

                                    # If here there is an error: Stop Monte Carlo simulations and crash: it's not normal


    except invalidind2:
        # ## Rescale LAL boiler or EH
        # Get list of building and rescale boiler or EH
        list_of_building = City.get_list_build_entity_node_ids()
        for build in list_of_building:
            # Start try to rescale boiler or EH
            if City.node[build]['entity'].bes.hasBoiler == True:
                City.node[build]['entity'].bes.boiler.lowerActivationLimit = 0
                Lal_rescaled = True

                print()
                print('Rescale LAl boiler')
                print('new boiler Lal kW: ', City.node[build]['entity'].bes.boiler.lowerActivationLimit )
                print()


            if City.node[build]['entity'].bes.hasBoiler == True:
                City.node[build]['entity'].bes.boiler.qNominal = \
                    City.node[build]['entity'].bes.boiler.qNominal * 1.1/City.node[build]['entity'].bes.boiler.eta

                #rescale_boiler_small = True

                print()
                print('Rescale boiler first round 10%')
                print('new boiler capacity kW: ', City.node[build]['entity'].bes.boiler.qNominal / 1000)
                print()

            if City.node[build]['entity'].bes.hasElectricalHeater == True:
                City.node[build]['entity'].bes.electricalHeater.qNominal =\
                    City.node[build]['entity'].bes.electricalHeater.qNominal*1.1\
                    /City.node[build]['entity'].bes.electricalHeater.eta

                Rescal_eh_third_time = True

                print()
                print('Rescale EH first round 10%')
                print('new EH capacity kW: ', City.node[build]['entity'].bes.electricalHeater.qNominal / 1000)
                print()

        # Do another time EBB
        for i in range(len(dict_bes_data)):
            try:
                City, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)

            except invalidind2:
                ## Rescale boiler or resyze EH

                # Get list of building and rescale boiler or EH
                list_of_building = City.get_list_build_entity_node_ids()
                for build in list_of_building:
                    # Rescal Boiler capacity
                    if City.node[build]['entity'].bes.hasBoiler == True:
                        City.node[build]['entity'].bes.boiler.qNominal = \
                            City.node[build]['entity'].bes.boiler.qNominal*1.2

                        rescale_boiler_second_time = True

                        print()
                        print('Rescale boiler second round ')
                        print('new boiler capacity kW: ', City.node[build]['entity'].bes.boiler.qNominal / 1000)
                        print()

                    # Rescal TES capacity
                    if City.node[build]['entity'].bes.hasTes == True:
                        City.node[build]['entity'].bes.tes.capacity = City.node[build]['entity'].bes.tes.capacity * 1.1

                        print()
                        print('Rescale Tes first round 10%')
                        print('new Tes capacity kg: ', City.node[build]['entity'].bes.tes.capacity)
                        print()


                    if City.node[build]['entity'].bes.hasElectricalHeater == True:
                        City.node[build]['entity'].bes.electricalHeater.qNominal = \
                            City.node[build]['entity'].bes.electricalHeater.qNominal * 1.2

                        rescale_eh_second_time = True

                        print()
                        print('Rescale EH for the second time 20%')
                        print('new EH capacity kW: ', City.node[build]['entity'].bes.electricalHeater.qNominal / 1000)
                        print()

                # Do another time EBB
                for i in range(len(dict_bes_data)):
                    try:
                        City, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)

                    except invalidind2:
                        # Resize boiler totally

                        # Get list of building and rescale boiler or EH
                        list_of_building = City.get_list_build_entity_node_ids()
                        for build in list_of_building:
                            # Rescal Boiler capacity
                            if City.node[build]['entity'].bes.hasBoiler == True:
                                City.node[build]['entity'].bes.boiler.qNominal = City.node[build]['entity'].bes.boiler.qNominal*1.5

                                rescale_boiler_third_time = True
                                print()
                                print('Rescale boiler third time: 50%')
                                print('new boiler capacity kW: ', City.node[build]['entity'].bes.boiler.qNominal / 1000)
                                print()

                            if City.node[build]['entity'].bes.hasElectricalHeater == True:
                                City.node[build]['entity'].bes.electricalHeater.qNominal = \
                                    City.node[build]['entity'].bes.electricalHeater.qNominal * 1.5

                                rescale_boiler_third_time = True

                                print()
                                print('Rescale EH for the third time 50%')
                                print('new EH capacity kW: ',
                                      City.node[build]['entity'].bes.electricalHeater.qNominal / 1000)
                                print()

                        # Do another time EBB
                        for i in range(len(dict_bes_data)):
                            try:
                                City, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)

                            except invalidind2:
                                ## Resvale TES
                                # Get list of building
                                list_of_building = City.get_list_build_entity_node_ids()

                                for build in list_of_building:

                                    # Rescal TES capacity
                                    if City.node[build]['entity'].bes.hasTes == True:
                                        City.node[build]['entity'].bes.tes.capacity = City.node[build][
                                                                                          'entity'].bes.tes.capacity * 100000

                                        print()
                                        print('Rescale Tes totally')
                                        print('new Tes capacity kg: ',City.node[build]['entity'].bes.tes.capacity)
                                        print()

                                        Rescaled_tes = True

                                    # Rescal Boiler capacity
                                    if City.node[build]['entity'].bes.hasBoiler == True:
                                        City.node[build]['entity'].bes.boiler.qNominal = \
                                            City.node[build]['entity'].bes.boiler.qNominal * 10

                                    if City.node[build]['entity'].bes.hasElectricalHeater == True:
                                        City.node[build]['entity'].bes.electricalHeater.qNominal = \
                                            City.node[build]['entity'].bes.electricalHeater.qNominal * 10


                                        print()
                                        print('Rescale EH totally')
                                        print('new EH capacity kW: ',
                                              City.node[build]['entity'].bes.electricalHeater.qNominal / 1000)
                                        print()

                                # Do another time EBB
                                for i in range(len(dict_bes_data)):
                                    City, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)

                                    # If here there is still an error: Stop Monte Carlo simulations and crash: it's not normal

    # ## Gas and electrical demand
    el_dem = 0
    gas_dem = 0
    pv_used_self=0
    pv_sold=0
    chp_self_used = 0
    chp_sold = 0

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


                    if 'pv_used_self' in City.node[n]:
                        pv_used_self += sum(City.node[n]['pv_used_self']) * \
                                   City.environment.timer.timeDiscretization / 1000 / 3600


                    if 'pv_sold' in City.node[n]:
                        pv_sold += sum(City.node[n]['pv_sold']) * \
                                   City.environment.timer.timeDiscretization / 1000 / 3600

                    if 'chp_used_self' in City.node[n]:
                        chp_self_used += sum(City.node[n]['pv_used_self']) * \
                                   City.environment.timer.timeDiscretization / 1000 / 3600


                    if 'chp_sold' in City.node[n]:
                        chp_sold += sum(City.node[n]['pv_sold']) * \
                                   City.environment.timer.timeDiscretization / 1000 / 3600

    return el_dem, gas_dem, Lal_rescaled, rescale_boiler_second_time, rescale_boiler_third_time, Rescaled_tes, \
        Rescale_eh_first_time, rescale_eh_second_time, Rescal_eh_third_time, pv_sold, pv_used_self, \
           chp_sold, chp_self_used

if __name__ == '__main__':

    #  User Inputs
    #  ##############################
    nb_samples = 1000
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
    dict_pam['interest_low']=0.03
    dict_pam['interest_medium']=0.05
    dict_pam['interest_high']=0.07
    dict_pam['weather'] = wea.gen_set_of_weathers(nb_samples)
    dict_pam['time']=time

    #  Perform MC analysis for whole city
    ( Th_results, el_results_net, Gas_results, El_results, Annuity_results,\
           Annuity_results_high, Annuity_results_low,  Annuity_results_ec1, Annuity_results_ec2, Annuity_results_ec3,\
           GHG_results, GHG_spe_results, Nb_Lal_rescaled, Nb_boiler_medium_rescaled, Nb_boiler_high_rescaled,\
           Nb_Tes_rescale, Nb_EH_small_rescaled, Nb_EH_medium_rescaled, Nb_EH_high_rescaled) = \
        new_city_evaluation_monte_carlo(ref_City=city, dict_sample=dict_pam)

    #  Results
    #  ##################################################################
    print ('Number of boiler rescaled 10%', Nb_Lal_rescaled)
    print('Number of EH rescaled 10%: ', Nb_EH_small_rescaled)
    print ('Number of tes rescaled: ',Nb_Tes_rescale)

    fig = plt.figure()
    # the histogram of the data
    plt.hist(Th_results, 100)
    plt.xlabel('Thermal energy demand in kWh')
    plt.ylabel('Number of values')
    plt.show()

    fig4, ((ax21, ax22), (ax23, ax24)) = plt.subplots(2, 2)
    ax22.hist(Annuity_results, 50)
    ax22.set_title('Annuity_results 5%')
    ax21.hist(Annuity_results_low, 50)
    ax21.set_title('Annuity_results low interest 3%')
    ax23.hist(Annuity_results_high, 50)
    ax23.set_title('Annuity_results high interest 7%')

    #plt.show()
    #plt.close()

