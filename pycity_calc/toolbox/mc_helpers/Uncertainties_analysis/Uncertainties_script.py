#!/usr/bin/env python
# coding=utf-8

'''

Script to perform a Monte Carlo analysis of a city object.
Output are gas, electrical final demand, uncertain annuity and GHG emissions

Structure:
---------
1: Define parameter for the uncertainty analysis
    City generation method: - from a pickle file
                            - Generation with City_generator

    Uncertainties:  weather is always uncertain
                    energy systems parameters unknown: True or False (efficiency, maximum temperature...)
                    buildings parameters: True or False (infiltration rate, net_floor_area, modernisation year)

                    user parameters: True or False (user_ventilations_rate, Tset_heat, number of occupants)

    Analyse: Confident interval definition
             Reference for GHG specific calculation

    Results: Save the results in a text file: True or False
             Filename

2: Reference City generation and add energy systems

3: Dictionary for sampling

4: Simulation generation

5: Analyse of simulations

6: Write results of the analyse

7: Visualisation

'''

import os
import pickle
import copy
import pycity_calc.cities.scripts.overall_gen_and_dimensioning as City_gen
import pycity_calc.environments.germanmarket as Mark
import pycity_calc.simulation.energy_balance_optimization.energy_balance_building as EBB
import pycity_calc.economic.annuity_calculation as eco_calc
import pycity_calc.economic.calc_CO2_emission as GHG_calc
import pycity_calc.toolbox.mc_helpers.Uncertainties_analysis.MC_new_cities_evaluation as newcity
import pycity_calc.toolbox.mc_helpers.weather.gen_weather_set as genweather
import pycity_calc.toolbox.mc_helpers.Uncertainties_analysis.MC_esys_new_evaluation as esys_gen

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import random as rd
from xlwt import Workbook

def do_uncertainty_analysis(Nsamples=1000 , time=10, Is_k_esys_parameters = True, time_sp_force_retro = 40,
                            max_retro_year = 2014,  Is_k_user_parameters = True, interest_fix = 0.05,
                            MC_analyse_total = True , Confident_intervall_pourcentage = 90, save_result = True,
                            save_path_mc='D:\jsc-les\\test_lolo\Results',
                            results_name = 'mc_results.txt',city_pickle_name = 'aachen_kronenberg_3_mfh_ref_1.pkl',
                            results_excel_name = 'mesresultats',
                            Is_k_building_parameters = False, esys_filename = 'City_lolo_esys_ref.txt' ,
                            gen_e_net=False, network_filename = 'lolo_networks.txt'):

    # Define Uncertainty analysis parameters
    # #############################################################################################################
    # ## City generation mode
    load_city = True  # load a pickle City file
    # if set to False: generation of a City with city_generator
    city_pickle_name = city_pickle_name
    # Scaling of esys (initialization)
    size_esys=False
    # ## Uncertainty

    # energy systems parameters are unknown (efficiency, maximum temperature...)
    Is_k_esys_parameters = Is_k_esys_parameters
    # Set to false: energy systems are known: buildings characteristics uncertainties

    # buildings parameters are unknown (infiltration rate, net_floor_area, modernisation year)
    Is_k_building_parameters = Is_k_building_parameters
    # Set to False:  buildings parameters are known: building uncertainties (infiltration rate and net_floor_area)
    time_sp_force_retro = time_sp_force_retro
    max_retro_year = max_retro_year

    # user parameters are unknown (user_ventilation_rate, Tset_heat, number of occupants)
    Is_k_user_parameters = Is_k_user_parameters
    #Set to False: user parameters are fixed

    # ## Economic calculations:
    interest_fix = interest_fix

    # Time for economic calculation in years (default: 10)
    time = time  # Years


    MC_analyse_total = MC_analyse_total
    # if set to false: MC analyse without uncertainties for area, height of floors, energy systems and economy

    # ## Analyse
    Confident_intervall_pourcentage = Confident_intervall_pourcentage
    GHG_specific = 'user energy demand'

    # ## Save results
    save_result = save_result # if set to false: no generation of results txt file
    results_name = results_name
    results_excel_name = results_excel_name
    save_path_mc = save_path_mc

    print('***********************************************************************************************************')
    print('Initialisation: Reference City Generation')
    print('***********************************************************************************************************')
    # City Generation with reference district data values and default parameters

    # #----------------------------------------------------------------------
    # #----------------------------------------------------------------------
    # # Generation of City reference:
    # #   load_city = True : City is load from pickle file
    # #   load_city 0 False : City is generated with City_generator

    this_path = os.path.dirname(os.path.abspath(__file__))

    if load_city == True:
        # load pickle City

        load_path = os.path.join(this_path, 'City_generation', 'input', city_pickle_name)
        City = pickle.load(open(load_path, mode='rb'))

        print()
        print('load city from pickle file: {}'.format(city_pickle_name))
        print()

        #  Add energy systems to city
        gen_esys = True  # True - Generate energy systems
        gen_e_net = gen_e_net # True - Generate energy networks
        #dhw_dim_esys = True  # Use dhw profiles for esys dimensioning

        #  Path to energy system input file (csv/txt; tab separated)
        esys_filename = esys_filename
        esys_path = os.path.join(this_path, 'City_generation', 'input', 'input_esys_generator', esys_filename)

        # Generate energy systems for city district
        if gen_esys:
            #  Load energy networks planing data
            list_esys = esys_gen.load_enersys_input_data(esys_path)
            print ('Add energy systems')

            #  Generate energy systems
            esys_gen.gen_esys_for_city(city=City, list_data=list_esys, size_esys=size_esys)
        # else enter all the parameter your self


        #  Add energy networks to city
        if gen_e_net:  # True - Generate energy networks

            #  Path to energy network input file (csv/txt; tab separated)
            network_filename = network_filename

            network_path = os.path.join(this_path, 'City_generation', 'input', 'input_en_network_generator',
                                             network_filename)
            #  Load energy networks planing data
            dict_e_net_data = City_gen.enetgen.load_en_network_input_data(network_path)

            City_gen.enetgen.add_energy_networks_to_city(city=City, dict_data=dict_e_net_data)



    else:
        # Generate City with City_generator

        #  # Userinputs


        #  Generate environment
        #  ######################################################
        print('Parameters:')
        year = 2010
        print('year : {}'.format(year))
        timestep = 3600  # Timestep in seconds
        print('timestep : {}'.format(timestep))
        # location = (51.529086, 6.944689)  # (latitude, longitude) of Bottrop
        location = (50.775346, 6.083887)  # (latitude, longitude) of Aachen
        print('location : {}'.format(timestep))
        altitude = 266  # Altitude of location in m (Aachen)
        print('altitude : {}'.format(altitude))

        #  Weather path
        try_path = None
        #  If None, used default TRY (region 5, 2010)


        #  Space heating load generation
        #  ######################################################
        #  Thermal generation method
        #  1 - SLP (standardized load profile)
        #  2 - Load and rescale Modelica simulation profile
        #  (generated with TRY region 12, 2010)
        #  3 - VDI 6007 calculation (requires el_gen_method = 2)

        print('Thermal generation : VDI 6007 calculation')
        th_gen_method = 3
        #  For non-residential buildings, SLPs are generated automatically.

        #  Manipulate thermal slp to fit to space heating demand?
        slp_manipulate = False
        print('slp manipulation : {}'.format(slp_manipulate))

        #  True - Do manipulation
        #  False - Use original profile
        #  Only relevant, if th_gen_method == 1
        #  Sets thermal power to zero in time spaces, where average daily outdoor
        #  temperature is equal to or larger than 12 °C. Rescales profile to
        #  original demand value.

        #  Manipulate vdi space heating load to be normalized to given annual net
        #  space heating demand in kWh
        vdi_sh_manipulate = False
        print('vdi manipulation : {}'.format(vdi_sh_manipulate))

        #  Electrical load generation
        #  ######################################################
        #  Choose electric load profile generation method (1 - SLP; 2 - Stochastic)
        #  Stochastic profile is only generated for residential buildings,
        #  which have a defined number of occupants (otherwise, SLP is used)
        print('Electrical load generation : Stochastic method')

        el_gen_method = 2
        #  If user defines method_3_nb or method_4_nb within input file
        #  (only valid for non-residential buildings), SLP will not be used.
        #  Instead, corresponding profile will be loaded (based on measurement
        #  data, see ElectricalDemand.py within pycity)

        #  Do normalization of el. load profile
        #  (only relevant for el_gen_method=2).
        #  Rescales el. load profile to expected annual el. demand value in kWh
        do_normalization = False
        print('normalisation of el.load : {}'.format(do_normalization))

        #  Randomize electrical demand value (residential buildings, only)
        el_random = False
        print('randomization electrical demand value : {}'.format(el_random))

        #  Prevent usage of electrical heating and hot water devices in
        #  electrical load generation
        prev_heat_dev = True
        #  True: Prevent electrical heating device usage for profile generation
        #  False: Include electrical heating devices in electrical load generation
        print(' Prevent usage of electrical heating and hot water devices in electrical load generation : {}'.format(
            prev_heat_dev))

        #  Use cosine function to increase winter lighting usage and reduce
        #  summer lighting usage in richardson el. load profiles
        #  season_mod is factor, which is used to rescale cosine wave with
        #  lighting power reference (max. lighting power)
        season_mod = 0.3
        print('season mod : {}'.format(season_mod))
        #  If None, do not use cosine wave to estimate seasonal influence
        #  Else: Define float
        #  (only relevant if el_gen_method == 2)

        #  Hot water profile generation
        #  ######################################################
        #  Generate DHW profiles? (True/False)
        use_dhw = True  # Only relevant for residential buildings

        #  DHW generation method? (1 - Annex 42; 2 - Stochastic profiles)
        #  Choice of Annex 42 profiles NOT recommended for multiple builings,
        #  as profile stays the same and only changes scaling.
        #  Stochastic profiles require defined nb of occupants per residential
        #  building
        dhw_method = 2  # Only relevant for residential buildings
        print('DHW generation method : Stochastic method')

        #  Define dhw volume per person and day (use_dhw=True)
        dhw_volumen = 64  # Only relevant for residential buildings
        print('dhw volumen : {}'.format(dhw_method))

        #  Randomize choosen dhw_volume reference value by selecting new value
        #  from gaussian distribution with 20 % standard deviation
        dhw_random = False
        print('randomization dhw volume reference : {}'.format(dhw_random))

        #  Use dhw profiles for esys dimensioning
        dhw_dim_esys = True

        #  Plot city district with pycity_calc visualisation
        plot_pycity_calc = False

        #  Efficiency factor of thermal energy systems
        #  Used to convert input values (final energy demand) to net energy demand
        eff_factor = 1
        print('Efficiency factor of thermal energy systems : {}'.format(eff_factor))

        #  Define city district input data filename
        filename = 'aachen_kronenberg_3_mfh_ref_1.txt'
        txt_path = os.path.join(this_path, 'City_generation', 'input', filename)

        #  Define city district output file
        save_filename = 'test_lolo.p'
        save_path = os.path.join(this_path, 'City_generation', 'output', save_filename)

        #  #####################################
        t_set_heat = 20  # Heating set temperature in degree Celsius
        t_set_night = 16  # Night set back temperature in degree Celsius
        t_set_cool = 70  # Cooling set temperature in degree Celsius
        print('tset : ', t_set_heat, ' ;', t_set_cool, ' ;', t_set_night)

        #  Air exchange rate (required for th_gen_method = 3 (VDI 6007 sim.))
        air_vent_mode = 0
        print('air exchange rate calculation method : Use constant value')
        #  int; Define mode for air ventilation rate generation
        #  0 : Use constant value (vent_factor in 1/h)
        #  1 : Use deterministic, temperature-dependent profile
        #  2 : Use stochastic, user-dependent profile
        #  False: Use static ventilation rate value

        vent_factor = 0.5  # Constant. ventilation rate
        print('vent factor: {}'.format(vent_factor))
        #  (only used, if air_vent_mode = 0)
        #  #####################################

        #  Use TEASER to generate type buildings
        call_teaser = False
        teaser_proj_name = filename[:-4]

        #  Log file for city_generator
        do_log = True  # True, generate log file
        print('Generation of a log file with the inputs : {}'.format(do_log))
        log_path = os.path.join(this_path, 'City_generation', 'output', 'city_gen_test_lolo_log.txt')

        #  Generate street networks
        gen_str = False  # True - Generate street network

        #  Street node and edges input filenames
        str_node_filename = 'street_nodes_cluster_simple.csv'
        str_edge_filename = 'street_edges_cluster_simple.csv'

        #  Load street data from csv
        str_node_path = os.path.join(this_path, 'input', 'street_generator',
                                     str_node_filename)
        str_edge_path = os.path.join(this_path, 'input', 'street_generator',
                                     str_edge_filename)

        #  Add energy networks to city
        gen_e_net = False  # True - Generate energy networks

        #  Path to energy network input file (csv/txt; tab separated)
        network_filename = 'lolo_networks.txt'
        network_path = os.path.join(this_path, 'City_generation', 'input', 'input_en_network_generator',
                                    network_filename)

        #  Add energy systems to city
        gen_esys = True  # True - Generate energy networks

        #  Path to energy system input file (csv/txt; tab separated)
        esys_filename = 'lolo_esys.txt'
        esys_path = os.path.join(this_path, 'City_generation', 'input', 'input_esys_generator',
                                 esys_filename)

        #  Add energy networks to city
        gen_e_net = False  # True - Generate energy networks

        #  Path to energy network input file (csv/txt; tab separated)
        network_filename = 'lolo_networks.txt'
        network_path = os.path.join(this_path, 'City_generation', 'input', 'input_en_network_generator',
                                    network_filename)




        # # Load district_data file



        district_data = City_gen.citygen.get_district_data_from_txt(txt_path)
        print('district data : ', district_data)



        # # City Generation

        City = City_gen.run_overall_gen_and_dim(timestep=timestep,
                                                year=year,
                                                location=location,
                                                try_path=try_path, th_gen_method=th_gen_method,
                                                el_gen_method=el_gen_method,
                                                use_dhw=use_dhw,
                                                dhw_method=dhw_method,
                                                district_data=district_data,
                                                gen_str=gen_str,
                                                str_node_path=str_node_path,
                                                str_edge_path=str_edge_path,
                                                generation_mode=0,
                                                eff_factor=eff_factor,
                                                save_path=save_path,
                                                altitude=altitude,
                                                do_normalization=do_normalization,
                                                dhw_volumen=dhw_volumen,
                                                gen_e_net=gen_e_net,
                                                network_path=network_path,
                                                gen_esys=gen_esys,
                                                esys_path=esys_path,
                                                dhw_dim_esys=dhw_dim_esys,
                                                plot_pycity_calc=plot_pycity_calc,
                                                slp_manipulate=slp_manipulate,
                                                call_teaser=call_teaser,
                                                teaser_proj_name=teaser_proj_name,
                                                do_log=do_log, log_path=log_path,
                                                air_vent_mode=air_vent_mode,
                                                vent_factor=vent_factor,
                                                t_set_heat=t_set_heat,
                                                t_set_cool=t_set_cool,
                                                t_night=t_set_night,
                                                vdi_sh_manipulate=vdi_sh_manipulate,
                                                el_random=el_random,
                                                dhw_random=dhw_random,
                                                prev_heat_dev=prev_heat_dev,
                                                season_mod=season_mod)


    # #----------------------------------------------------------------------
    # #----------------------------------------------------------------------

    # # Energy balance calculations

    print("Energy balance calculations for city reference")
    Calculator = EBB.calculator(City)
    dict_bes_data = Calculator.assembler()

    for i in range(len(dict_bes_data)):
        City, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)

    # Gas and electrical demand
    el_dem_ref = 0
    gas_dem_ref = 0
    for n in City.nodes():
        if 'node_type' in City.node[n]:
            #  If node_type is building
            if City.node[n]['node_type'] == 'building':
                #  If entity is kind building
                if City.node[n]['entity']._kind == 'building':

                    if 'electrical demand' in City.node[n]:
                        el_dem_ref += sum(City.node[n]['electrical demand']) * \
                                          City.environment.timer.timeDiscretization / 1000 / 3600

                    if 'fuel demand' in City.node[n]:
                        gas_dem_ref += sum(City.node[n]['fuel demand']) * \
                                          City.environment.timer.timeDiscretization / 1000 / 3600

    # #----------------------------------------------------------------------
    # #----------------------------------------------------------------------

    # # Economic and GHG calculations

    interest = 0.05  # Interest rate
    Market_instance = Mark.GermanMarket()

    #  Generate economic calculator object
    print("Economic object generation")
    eco_inst = eco_calc.EconomicCalculation(time=time, interest=interest, germanmarket=Market_instance)

    # Annuity Calculation
    print("Annuity calculations")
    dem_rel_annuity = eco_inst.calc_dem_rel_annuity_city(City,)
    total_proc_annuity = eco_inst.calc_proc_annuity_multi_comp_city(City)
    cap_rel_ann, op_rel_ann = eco_inst.calc_cap_and_op_rel_annuity_city(City)

    total_annuity_ref = eco_inst.calc_total_annuity(ann_capital=cap_rel_ann,
                                                    ann_demand=dem_rel_annuity,
                                                    ann_op=op_rel_ann,
                                                    ann_proc=total_proc_annuity)

    print("Emission object generation")

    GHG = City.environment.co2emissions

    GHG_Emission_ref = GHG_calc.CO2_emission_calc(city_object=City, emission_object=GHG, CO2_zero_lowerbound=False,
                                                  eco_calc_instance=eco_inst)

    #print('GHG emissions reference City : kg/year')
    #print(GHG_Emission_ref)

    print('***********************************************************************************************************')
    print('Save the city')
    print('***********************************************************************************************************')
    # Save the reference city
    SaveCity = copy.deepcopy(City)

    print('Annual electricity demand : ', SaveCity.get_annual_el_demand(), 'kWh/year')
    print('Annual thermal demand : ', SaveCity.get_total_annual_th_demand(), 'kWh/year')
    print('Annual electricity demand reference City after EBB : ', el_dem_ref, 'kWh/year')
    print('Annual gas demand reference City after EBB: ', gas_dem_ref, 'kWh/year')
    print('total reference annuity:', round(total_annuity_ref, 2), ' Euro/year')
    print('total emission reference City :', GHG_Emission_ref, ' kg/year ')

    print('***********************************************************************************************************')
    print('Samples Dictionnary')
    print('***********************************************************************************************************')
    # ## Do the dictionary for Monte Carlo uncertainty analysis sampling

    dict_par_unc = {}
    dict_par_unc['Nsamples'] = Nsamples

    dict_par_unc['weather'] = genweather.gen_set_of_weathers(Nsamples)
    print('End of weather sampling')

    # ## Define which parameters are uncertain
    if Is_k_esys_parameters:
        # energy systems parameters are totally uncertain
        dict_par_unc['esys'] = True
    else:
        dict_par_unc['esys'] = False

    if Is_k_building_parameters:
        dict_par_unc['build_physic_unc'] = True
    else:
        dict_par_unc['build_physic_unc'] = False


    dict_par_unc['time_sp_force_retro'] = time_sp_force_retro
    dict_par_unc['max_retro_year'] = max_retro_year
    if Is_k_user_parameters:
        dict_par_unc['nb_occ_unc'] = True
        dict_par_unc['user'] = True
    else:
        dict_par_unc['nb_occ_unc'] =False
        dict_par_unc['user'] = False

    if MC_analyse_total:
        dict_par_unc['MC_analysis'] = True
    else:
        dict_par_unc['MC_analysis'] = False

    # # Interest sampling
    # low interest
    max =  0.05
    min = 0
    interest_list_low = []
    for i in range(Nsamples):
        temp = rd.uniform(min, max)
        interest_list_low.append(temp)

    # medium interest
    max =  0.1
    min = 0.05
    interest_list_medium = []
    for i in range(Nsamples):
        temp = rd.uniform(min, max)
        interest_list_medium.append(temp)

    # high interest
    max = 0.2
    min = 0.1
    interest_list_high = []
    for i in range(Nsamples):
        temp = rd.uniform(min, max)
        interest_list_high.append(temp)
    # interest fix
    interest_list_fix=[]
    for i in range (Nsamples):
        interest_list_fix.append(interest_fix)

    dict_par_unc['interest_fix'] = interest_list_fix
    dict_par_unc['interest_low'] = interest_list_low
    dict_par_unc['interest_medium'] = interest_list_medium
    dict_par_unc['interest_high'] = interest_list_high

    dict_par_unc['time'] = time

        # TODO rajouter le sample pour un equipement avec des proprietes vraiment incertaines et d'autres moins

    print('***********************************************************************************************************')
    print('Do the simulations')
    print('***********************************************************************************************************')

    Th_results, Gas_results, El_results, Annuity_results, GHG_results, \
    GHG_spe_results, el_results2, dict_city_pb, Nboiler_rescaled, NEH_rescaled, Lal_rescaled, Tes_rescaled, \
    Annuity_results_ec1, Annuity_results_ec2, Annuity_results_ec3, Annuity_results_ec4, \
    Annuity_results_f, Annuity_results_h, Annuity_results_m,= \
        newcity.new_city_evaluation_monte_carlo(City, dict_par_unc)

    print('***********************************************************************************************************')
    print('Do the Uncertainties analyse')
    print('***********************************************************************************************************')
    # ## Results analysis - Standard deviation, mean and 90 confident interval- interest fix - eco0

    print ()
    print ('Gas demand analysis')
    print ('-------------------')
    print ('unit: kWh/year')
    mean_gas_demand = sum(Gas_results)/ len(Gas_results)
    sigma_gas_demand = np.std(a=Gas_results)
    median_gas_demand = np.median(a=Gas_results)
    confident_inter_gas = stats.norm.interval(Confident_intervall_pourcentage/100, loc=mean_gas_demand, scale=sigma_gas_demand)
    first_quantil_gas = stats.scoreatpercentile(Gas_results, per=25 )
    second_quantil_gas = stats.scoreatpercentile(Gas_results, per=50)
    third_quantil_gas = stats.scoreatpercentile(Gas_results, per=75 )

    print('mean :', mean_gas_demand)
    print('sigma :', sigma_gas_demand)
    print('confident interval {}'.format(Confident_intervall_pourcentage), confident_inter_gas)
    print('{:0.2%} of the means are in confident interval'.format(((Gas_results >= confident_inter_gas[0]) & (Gas_results < confident_inter_gas[1])).sum() / float(Nsamples)))
    print ('median : ', median_gas_demand)
    print ('first quantil : ', first_quantil_gas)
    print ('second quantil :', second_quantil_gas)
    print ('third quantil : ', third_quantil_gas)
    print()

    # Electrical demand
    print('Electrical demand analysis')
    print('--------------------------')
    print('unit: kWh/year')

    mean_el_demand = sum (El_results)/len(El_results)
    sigma_el_demand = np.std(a=El_results)
    confident_inter_el = stats.norm.interval(Confident_intervall_pourcentage / 100, loc=mean_el_demand,
                                              scale=sigma_el_demand)
    median_el_demand = np.median(a=El_results)
    first_quantil_el = stats.scoreatpercentile(El_results, per=25)
    second_quantil_el = stats.scoreatpercentile(El_results, per=50)
    third_quantil_el = stats.scoreatpercentile(El_results, per=75)

    print('mean :', mean_el_demand)
    print('sigma :', sigma_el_demand)
    print('confident interval {}'.format(Confident_intervall_pourcentage), confident_inter_el)
    print('{:0.2%} of the means are in confident interval'.format(((El_results >= confident_inter_el[0]) & (El_results < confident_inter_el[1])).sum() / float(Nsamples)))
    print('median : ', median_el_demand)
    print('first quantil : ', first_quantil_el)
    print('second quantil :', second_quantil_el)
    print('third quantil : ', third_quantil_el)
    print()

    # Annuity, eco0, interest fixed
    print('Annuity analysis ref')
    print('----------------')
    print('unit: Euro/year')

    mean_annuity = sum(Annuity_results_f)/len(Annuity_results_f)
    sigma_annuity = np.std(a=Annuity_results_f)
    confident_inter_a = stats.norm.interval(Confident_intervall_pourcentage / 100, loc=mean_annuity, scale=sigma_annuity)

    median_a = np.median(a=Annuity_results_f)
    first_quantil_a = stats.scoreatpercentile(Annuity_results_f, per=25)
    second_quantil_a = stats.scoreatpercentile(Annuity_results_f, per=50)
    third_quantil_a = stats.scoreatpercentile(Annuity_results_f, per=75)

    print('mean :', mean_annuity)
    print('sigma :', sigma_annuity)
    print('confident interval {}'.format(Confident_intervall_pourcentage), confident_inter_a)
    print('{:0.2%} of the means are in confident interval'.format(((Annuity_results_f >= confident_inter_a[0]) & (Annuity_results_f < confident_inter_a[1])).sum() / float(Nsamples)))
    print('median : ', median_a)
    print('first quantil : ', first_quantil_a)
    print('second quantil :', second_quantil_a)
    print('third quantil : ', third_quantil_a)
    print()

    # Annuity, eco0, interest low
    print('Annuity analysis low')
    print('----------------')
    print('unit: Euro/year')

    mean_annuity_low= sum(Annuity_results) / len(Annuity_results)
    sigma_annuity_low = np.std(a=Annuity_results)
    confident_inter_a_low= stats.norm.interval(Confident_intervall_pourcentage / 100, loc=mean_annuity_low,
                                            scale=sigma_annuity_low)

    # Annuity, eco0, interest medium
    print('Annuity analysis medium')
    print('----------------')
    print('unit: Euro/year')

    mean_annuity_medium = sum(Annuity_results_m) / len(Annuity_results_m)
    sigma_annuity_medium = np.std(a=Annuity_results_m)
    confident_inter_a_medium = stats.norm.interval(Confident_intervall_pourcentage / 100, loc=mean_annuity_medium,
                                                scale=sigma_annuity_medium)

    # Annuity, eco0, interest high
    print('Annuity analysis medium')
    print('----------------')
    print('unit: Euro/year')

    mean_annuity_h = sum(Annuity_results_h) / len(Annuity_results_h)
    sigma_annuity_h = np.std(a=Annuity_results_h)
    confident_inter_a_h = stats.norm.interval(Confident_intervall_pourcentage / 100, loc=mean_annuity_h,
                                                   scale=sigma_annuity_h)

    # Annuity, eco1, interest fixed
    print('Annuity analysis eco1')
    print('----------------')
    print('unit: Euro/year')

    mean_annuity_ec1 = sum(Annuity_results_ec1) / len(Annuity_results_ec1)
    sigma_annuity_ec1 = np.std(a=Annuity_results_ec1)
    confident_inter_a_ec1 = stats.norm.interval(Confident_intervall_pourcentage / 100, loc=mean_annuity_ec1,
                                            scale=sigma_annuity_ec1)

    median_a_ec1 = np.median(a=Annuity_results_ec1)
    first_quantil_a_ec1 = stats.scoreatpercentile(Annuity_results_ec1, per=25)
    second_quantil_a_ec1 = stats.scoreatpercentile(Annuity_results_ec1, per=50)
    third_quantil_a_ec1 = stats.scoreatpercentile(Annuity_results_ec1, per=75)

    print('mean :', mean_annuity_ec1)
    print('sigma :', sigma_annuity_ec1)
    print('confident interval {}'.format(Confident_intervall_pourcentage), confident_inter_a_ec1)
    print('{:0.2%} of the means are in confident interval'.format(
        ((Annuity_results_ec1 >= confident_inter_a_ec1[0]) & (Annuity_results_ec1 < confident_inter_a_ec1[1])).sum() / float(
            Nsamples)))
    print('median : ', median_a_ec1)
    print('first quantil : ', first_quantil_a_ec1)
    print('second quantil :', second_quantil_a_ec1)
    print('third quantil : ', third_quantil_a_ec1)
    print()

    # Annuity, eco2, interest fixed
    print('Annuity analysis eco2')
    print('----------------')
    print('unit: Euro/year')

    mean_annuity_ec2 = sum(Annuity_results_ec2) / len(Annuity_results_ec2)
    sigma_annuity_ec2 = np.std(a=Annuity_results_ec2)
    confident_inter_a_ec2 = stats.norm.interval(Confident_intervall_pourcentage / 100, loc=mean_annuity_ec2,
                                            scale=sigma_annuity_ec2)

    median_a_ec2 = np.median(a=Annuity_results_ec2)
    first_quantil_a_ec2 = stats.scoreatpercentile(Annuity_results_ec2, per=25)
    second_quantil_a_ec2 = stats.scoreatpercentile(Annuity_results_ec2, per=50)
    third_quantil_a_ec2 = stats.scoreatpercentile(Annuity_results_ec2, per=75)

    print('mean :', mean_annuity_ec2)
    print('sigma :', sigma_annuity_ec2)
    print('confident interval {}'.format(Confident_intervall_pourcentage), confident_inter_a_ec2)
    print('{:0.2%} of the means are in confident interval'.format(
        ((Annuity_results_ec2 >= confident_inter_a_ec2[0]) & (Annuity_results_ec2 < confident_inter_a_ec2[1])).sum() / float(
            Nsamples)))
    print('median : ', median_a_ec2)
    print('first quantil : ', first_quantil_a_ec2)
    print('second quantil :', second_quantil_a_ec2)
    print('third quantil : ', third_quantil_a_ec2)
    print()

    # Annuity, eco3, interest fixed
    print('Annuity analysis eco3')
    print('----------------')
    print('unit: Euro/year')

    mean_annuity_ec3 = sum(Annuity_results_ec3) / len(Annuity_results_ec3)
    sigma_annuity_ec3 = np.std(a=Annuity_results_ec3)
    confident_inter_a_ec3 = stats.norm.interval(Confident_intervall_pourcentage / 100, loc=mean_annuity_ec3,
                                                scale=sigma_annuity_ec3)

    median_a_ec3 = np.median(a=Annuity_results_ec3)
    first_quantil_a_ec3 = stats.scoreatpercentile(Annuity_results_ec3, per=25)
    second_quantil_a_ec3 = stats.scoreatpercentile(Annuity_results_ec3, per=50)
    third_quantil_a_ec3 = stats.scoreatpercentile(Annuity_results_ec3, per=75)

    print('mean :', mean_annuity_ec3)
    print('sigma :', sigma_annuity_ec3)
    print('confident interval {}'.format(Confident_intervall_pourcentage), confident_inter_a_ec3)
    print('{:0.2%} of the means are in confident interval'.format(
        ((Annuity_results_ec3 >= confident_inter_a_ec3[0]) & (
        Annuity_results_ec3 < confident_inter_a_ec3[1])).sum() / float(
            Nsamples)))
    print('median : ', median_a_ec3)
    print('first quantil : ', first_quantil_a_ec3)
    print('second quantil :', second_quantil_a_ec3)
    print('third quantil : ', third_quantil_a_ec3)
    print()

    # Annuity, eco4, interest fixed
    print('Annuity analysis eco4')
    print('----------------')
    print('unit: Euro/year')

    mean_annuity_ec4 = sum(Annuity_results_ec4) / len(Annuity_results_ec4)
    sigma_annuity_ec4 = np.std(a=Annuity_results_ec4)
    confident_inter_a_ec4 = stats.norm.interval(Confident_intervall_pourcentage / 100, loc=mean_annuity_ec4,
                                                scale=sigma_annuity_ec4)

    median_a_ec4 = np.median(a=Annuity_results_ec4)
    first_quantil_a_ec4 = stats.scoreatpercentile(Annuity_results_ec4, per=25)
    second_quantil_a_ec4 = stats.scoreatpercentile(Annuity_results_ec4, per=50)
    third_quantil_a_ec4 = stats.scoreatpercentile(Annuity_results_ec4, per=75)

    print('mean :', mean_annuity_ec4)
    print('sigma :', sigma_annuity_ec4)
    print('confident interval {}'.format(Confident_intervall_pourcentage), confident_inter_a_ec4)
    print('{:0.2%} of the means are in confident interval'.format(
        ((Annuity_results_ec4 >= confident_inter_a_ec4[0]) & (
        Annuity_results_ec4 < confident_inter_a_ec4[1])).sum() / float(
            Nsamples)))
    print('median : ', median_a_ec4)
    print('first quantil : ', first_quantil_a_ec4)
    print('second quantil :', second_quantil_a_ec4)
    print('third quantil : ', third_quantil_a_ec4)
    print()

    # GHG
    print('GHG_analysis')
    print('------------')
    print('unit: kg/year')

    mean_GHG = sum(GHG_results)/len(GHG_results)
    sigma_GHG = np.std(GHG_results)
    confident_inter_GHG = stats.norm.interval(Confident_intervall_pourcentage / 100, loc=mean_GHG,
                                            scale=sigma_GHG)

    median_GHG = np.median(a=GHG_results)
    first_quantil_GHG = stats.scoreatpercentile(GHG_results, per=25)
    second_quantil_GHG = stats.scoreatpercentile(GHG_results, per=50)
    third_quantil_GHG = stats.scoreatpercentile(GHG_results, per=75)

    print('mean:', mean_GHG)
    print('sigma :', sigma_GHG)
    print('confident interval {}'.format(Confident_intervall_pourcentage), confident_inter_GHG)
    print('{:0.2%} of the means are in confident interval'.format(
        ((GHG_results >= confident_inter_GHG[0]) & (GHG_results < confident_inter_GHG[1])).sum() / float(Nsamples)))
    print('median : ', median_GHG)
    print('first quantil : ', first_quantil_GHG)
    print('second quantil :', second_quantil_GHG)
    print('third quantil : ', third_quantil_GHG)
    print()

    # Specific GHG
    print('Specific GHG_analysis')
    print('---------------------')
    print('unit: kg/kWh/year')
    print ('specific reference: ', GHG_specific)

    mean_spe_GHG = sum(GHG_spe_results) / len(GHG_spe_results)
    sigma_spe_GHG = np.std(a=GHG_spe_results)
    confident_inter_spe_GHG = stats.norm.interval(Confident_intervall_pourcentage / 100, loc=mean_GHG,
                                                  scale=sigma_spe_GHG)
    median_spe_GHG = np.median(a=GHG_spe_results)
    first_quantil_spe_GHG = stats.scoreatpercentile(GHG_spe_results, per=25)
    second_quantil_spe_GHG = stats.scoreatpercentile(GHG_spe_results, per=50)
    third_quantil_spe_GHG = stats.scoreatpercentile(GHG_spe_results, per=75)

    print('mean specific GHG :', mean_spe_GHG)
    print('sigma specific GHG :', sigma_spe_GHG)
    print('confident interval {}'.format(Confident_intervall_pourcentage), confident_inter_spe_GHG)
    print('{:0.2%} of the means are in confident interval'.format(
        ((GHG_spe_results >= confident_inter_spe_GHG[0]) & (GHG_spe_results < confident_inter_spe_GHG[1])).sum() / float(Nsamples)))
    print('median : ', median_spe_GHG)
    print('first quantil : ', first_quantil_spe_GHG)
    print('second quantil :', second_quantil_spe_GHG)
    print('third quantil : ', third_quantil_spe_GHG)
    print ()

    print ('Number of simulations with rescaled boiler : ', Nboiler_rescaled)
    print('Number of simulations with rescaled EH : ', NEH_rescaled)
    print ('Number of simulations with rescaled Boiler Lal : ', Lal_rescaled)
    print ('Number of Tes rescaled : ', Tes_rescaled)

    print('***********************************************************************************************************')
    print('Save results')
    print('***********************************************************************************************************')

    if save_result:
        #  Write results file

        #  Log file path
        #this_path = os.path.dirname(os.path.abspath(__file__))
        results_path = os.path.join(save_path_mc, results_name)
        write_results = open(results_path, mode='w')

        write_results.write(' ---------- Monte Carlo Analysis ---------- \n ')

        write_results.write(' Number of sampling :' + str(Nsamples)+ '\n')

        write_results.write('\n############## Uncertain parameters ##############\n')
        write_results.write('user behaviour: ' + str(Is_k_user_parameters)+ '\n')
        write_results.write('energy systems parameters: ' + str(Is_k_esys_parameters)+ '\n')
        write_results.write('buildings parameters: ' + str(Is_k_building_parameters)+ '\n')
        write_results.write('interest_fix: ' + str(interest_fix) + '\n')
        write_results.write('network: ' + str(gen_e_net) + '\n')

        write_results.write('\n############## City reference ##############\n')
        if load_city == True:
            generation_mode = 'load City from pickle file'
            write_results.write('Generation mode: ' + generation_mode+ '\n')
            write_results.write('pickle file path :  ' + str(load_path)+ '\n')
        else:
            generation_mode = 'generation of a city with City_generator'
            write_results.write('Generation mode: ' + generation_mode)
            write_results.write('*-*- City ref parameters: ')
            write_results.write('generation_mode: ' + str(generation_mode) + '\n')
            write_results.write('timestep in seconds: ' + str(timestep) + '\n')
            write_results.write('Year: ' + str(year) + '\n')
            write_results.write('Location: ' + str(location) + '\n')
            write_results.write('District data: ' + district_data + '\n')
            write_results.write('t_set_heat: ' + str(t_set_heat) + '\n')
            write_results.write('t_set_night: ' + str(t_set_night) + '\n')
            write_results.write('t_set_cool: ' + str(t_set_cool) + '\n')
            write_results.write('air_vent_mode: ' + str(air_vent_mode) + '\n')
            write_results.write('vent_factor: ' + str(vent_factor) + '\n')
            write_results.write('el_gen_method: ' + str(el_gen_method) + '\n')
            write_results.write(
                'Normalize el. profile: ' + str(do_normalization) + '\n')
            write_results.write(
                'Do random el. normalization: ' + str(el_random) + '\n')
            write_results.write(
                'Prevent el. heating devices for el load generation: '
                '' + str(prev_heat_dev) + '\n')
            write_results.write(
                'Rescaling factor lighting power curve to implement seasonal '
                'influence: ' + str(season_mod) + '\n')

            write_results.write('use_dhw: ' + str(use_dhw) + '\n')
            write_results.write('dhw_method: ' + str(dhw_method) + '\n')
            write_results.write('dhw_volumen: ' + str(dhw_volumen) + '\n')
            write_results.write(
                'Do random dhw. normalization: ' + str(dhw_random) + '\n')

        write_results.write('\n############################Esys #########################\n')

        write_results.write('+++++++++++++++++++ \n')
        write_results.write('energy systems type: ' + str(list_esys)+ '\n')
        write_results.write('+++++++++++++++++++ \n')

        write_results.write('\n############################Results #########################\n')
        write_results.write('\n gas demand\n')
        write_results.write('\n ----------\n')
        write_results.write('unit : kWh/year \n')
        write_results.write('median : '+ str(median_gas_demand)+ '\n' )
        write_results.write('first quantil : '+ str(first_quantil_gas) + '\n')
        write_results.write('second quantil :'+ str(second_quantil_gas)+ '\n')
        write_results.write('third quantil :'+ str(third_quantil_gas) + '\n')
        write_results.write('mean : '+ str(mean_gas_demand) + '\n')
        write_results.write('sigma : '+ str(sigma_gas_demand) + '\n')
        write_results.write('confident interval {}'.format(Confident_intervall_pourcentage)+ str(confident_inter_gas) + '\n')
        write_results.write('{:0.2%} of the means are in confident interval'.format(((Gas_results >= confident_inter_gas[0]) & (Gas_results < confident_inter_gas[1])).sum() / float(Nsamples))+ '\n')
        write_results.write('reference:' + str(gas_dem_ref) + '\n')

        write_results.write('\n electrical demand\n')
        write_results.write('\n -----------------\n')
        write_results.write('unit : kWh/year \n')
        write_results.write('median : '+ str(median_el_demand) + '\n')
        write_results.write('first quantil : '+ str(first_quantil_el) + '\n')
        write_results.write('second quantil :'+ str(second_quantil_el) + '\n')
        write_results.write('third quantil :'+ str(third_quantil_el) + '\n')
        write_results.write('mean : '+ str(mean_el_demand) + '\n')
        write_results.write('sigma : '+ str(sigma_el_demand) + '\n')
        write_results.write('confident interval {}'.format(Confident_intervall_pourcentage)+ str(confident_inter_el) + '\n')
        write_results.write('{:0.2%} of the means are in confident interval'.format(
            ((El_results >= confident_inter_el[0]) & (El_results < confident_inter_el[1])).sum() / float(
                Nsamples)) + '\n')
        write_results.write('reference:' + str(el_dem_ref) + '\n')

        write_results.write('\n Annuity ec0 \n')
        write_results.write('\n -------\n')
        write_results.write('unit : Euro/year \n')
        write_results.write('median : '+ str(median_a) + '\n')
        write_results.write('first quantil : '+ str(first_quantil_a) + '\n')
        write_results.write('second quantil :'+ str(second_quantil_a) + '\n')
        write_results.write('third quantil :'+ str(third_quantil_a) + '\n')
        write_results.write('mean : '+ str(mean_annuity) + '\n')
        write_results.write('sigma : '+ str(sigma_annuity) + '\n')
        write_results.write('confident interval {}'.format(Confident_intervall_pourcentage)+ str(confident_inter_a) + '\n')
        write_results.write('{:0.2%} of the means are in confident interval'.format(
            ((Annuity_results_f >= confident_inter_a[0]) & (Annuity_results_f < confident_inter_a[1])).sum() / float(
                Nsamples)) + '\n')
        write_results.write('reference:' + str(total_annuity_ref) + '\n')

        write_results.write('\n Annuity ec1 \n')
        write_results.write('\n -------\n')
        write_results.write('unit : Euro/year \n')
        write_results.write('median : ' + str(median_a_ec1) + '\n')
        write_results.write('first quantil : ' + str(first_quantil_a_ec1) + '\n')
        write_results.write('second quantil :' + str(second_quantil_a_ec1) + '\n')
        write_results.write('third quantil :' + str(third_quantil_a_ec1) + '\n')
        write_results.write('mean : ' + str(mean_annuity_ec1) + '\n')
        write_results.write('sigma : ' + str(sigma_annuity_ec1) + '\n')
        write_results.write('confident interval {}'.format(Confident_intervall_pourcentage) + str(confident_inter_a_ec1) + '\n')
        write_results.write('{:0.2%} of the means are in confident interval'.format(((Annuity_results_ec1 >= confident_inter_a_ec1[0]) & (Annuity_results_ec1 < confident_inter_a_ec1[1])).sum() / float(
                Nsamples)) + '\n')
        write_results.write('reference:' + str(total_annuity_ref) + '\n')

        write_results.write('\n Annuity ec2 \n')
        write_results.write('\n -------\n')
        write_results.write('unit : Euro/year \n')
        write_results.write('median : ' + str(median_a_ec2) + '\n')
        write_results.write('first quantil : ' + str(first_quantil_a_ec2) + '\n')
        write_results.write('second quantil :' + str(second_quantil_a_ec2) + '\n')
        write_results.write('third quantil :' + str(third_quantil_a_ec2) + '\n')
        write_results.write('mean : ' + str(mean_annuity_ec2) + '\n')
        write_results.write('sigma : ' + str(sigma_annuity_ec2) + '\n')
        write_results.write(
            'confident interval {}'.format(Confident_intervall_pourcentage) + str(confident_inter_a) + '\n')
        write_results.write('{:0.2%} of the means are in confident interval'.format(
            ((Annuity_results_ec2 >= confident_inter_a_ec2[0]) & (Annuity_results_ec2 < confident_inter_a_ec2[1])).sum() / float(
                Nsamples)) + '\n')
        write_results.write('reference:' + str(total_annuity_ref) + '\n')

        write_results.write('\n Annuity ec3 \n')
        write_results.write('\n -------\n')
        write_results.write('unit : Euro/year \n')
        write_results.write('median : ' + str(median_a_ec3) + '\n')
        write_results.write('first quantil : ' + str(first_quantil_a_ec3) + '\n')
        write_results.write('second quantil :' + str(second_quantil_a_ec3) + '\n')
        write_results.write('third quantil :' + str(third_quantil_a_ec3) + '\n')
        write_results.write('mean : ' + str(mean_annuity_ec3) + '\n')
        write_results.write('sigma : ' + str(sigma_annuity_ec3) + '\n')
        write_results.write(
            'confident interval {}'.format(Confident_intervall_pourcentage) + str(confident_inter_a_ec3) + '\n')
        write_results.write('{:0.2%} of the means are in confident interval'.format(
            ((Annuity_results_ec3 >= confident_inter_a_ec3[0]) & (Annuity_results_ec3 < confident_inter_a_ec3[1])).sum() / float(
                Nsamples)) + '\n')
        write_results.write('reference:' + str(total_annuity_ref) + '\n')

        write_results.write('\n Annuity ec4 \n')
        write_results.write('\n -------\n')
        write_results.write('unit : Euro/year \n')
        write_results.write('median : ' + str(median_a_ec4) + '\n')
        write_results.write('first quantil : ' + str(first_quantil_a_ec4) + '\n')
        write_results.write('second quantil :' + str(second_quantil_a_ec4) + '\n')
        write_results.write('third quantil :' + str(third_quantil_a_ec4) + '\n')
        write_results.write('mean : ' + str(mean_annuity_ec4) + '\n')
        write_results.write('sigma : ' + str(sigma_annuity_ec4) + '\n')
        write_results.write(
            'confident interval {}'.format(Confident_intervall_pourcentage) + str(confident_inter_a_ec4) + '\n')
        write_results.write('{:0.2%} of the means are in confident interval'.format(
            ((Annuity_results_ec4 >= confident_inter_a_ec4[0]) & (Annuity_results_ec4 < confident_inter_a_ec4[1])).sum() / float(
                Nsamples)) + '\n')
        write_results.write('reference:' + str(total_annuity_ref) + '\n')

        write_results.write('\n GHG Emissions\n')
        write_results.write('\n -------------\n')
        write_results.write('unit : kg/year \n')
        write_results.write('median : '+ str(median_GHG) + '\n')
        write_results.write('first quantil : '+ str(first_quantil_GHG) + '\n')
        write_results.write('second quantil :'+ str(second_quantil_GHG) + '\n')
        write_results.write('third quantil :'+ str(third_quantil_GHG) + '\n')
        write_results.write('mean : '+ str(mean_GHG) + '\n')
        write_results.write('sigma : '+ str(sigma_GHG) + '\n')
        write_results.write('confident interval {}'.format(Confident_intervall_pourcentage)+ str(confident_inter_GHG) + '\n')
        write_results.write('{:0.2%} of the means are in confident interval'.format(
            ((GHG_results >= confident_inter_GHG[0]) & (GHG_results < confident_inter_GHG[1])).sum() / float(
                Nsamples)) + '\n')

        write_results.write('\n Specific GHG Emissions\n')
        write_results.write('\n ----------------------\n')
        write_results.write('unit : kg/kWh/year \n')
        write_results.write('reference: ' + str(GHG_specific) +'\n')
        write_results.write('median : '+ str(median_spe_GHG) + '\n')
        write_results.write('first quantil : '+ str(first_quantil_spe_GHG) + '\n')
        write_results.write('second quantil :'+ str(second_quantil_spe_GHG) + '\n')
        write_results.write('third quantil :'+ str(third_quantil_spe_GHG) + '\n')
        write_results.write('mean : '+ str(mean_spe_GHG) + '\n')
        write_results.write('sigma : '+ str(sigma_spe_GHG) + '\n')
        write_results.write('confident interval {}'.format(Confident_intervall_pourcentage)+ str(confident_inter_spe_GHG) + '\n')
        write_results.write('{:0.2%} of the means are in confident interval'.format(
            ((GHG_spe_results >= confident_inter_spe_GHG[0]) & (GHG_spe_results < confident_inter_spe_GHG[1])).sum() / float(
                Nsamples)) + '\n')
        write_results.write('reference:' + str(GHG_Emission_ref) + '\n')


        write_results.write('\n Nboiler Lal rescaled: ' + str(Lal_rescaled))
        write_results.write('\n Nboiler rescaled' + str(Nboiler_rescaled))
        write_results.write('\n NEH rescaled' + str(NEH_rescaled))
        write_results.write('\n Tes rescaled' + str(Tes_rescaled))
        write_results.close()



        # Xecel
        # Creation
        book = Workbook()

        #creation feuille1
        feuill1 = book.add_sheet('i_low_ec0')
        feuill2 = book.add_sheet('i_fix_eco0')
        feuill3 = book.add_sheet('i_high_eco0')
        feuill4 = book.add_sheet('i_medium_eco0')
        feuill5 = book.add_sheet('i_fix_ eco1')
        feuill6 = book.add_sheet('i_fix_eco2')
        feuill7 = book.add_sheet('i_fix_eco3')
        feuill8 = book.add_sheet('i_fix_eco4')

        # ajout des en-tête
        feuill1.write(0,0,'el_demand')
        feuill1.write(0,1,'gas_demand')
        feuill1.write(0,2,'Annuity')
        feuill1.write(0,3,'GHG')
        feuill2.write(0, 0, 'Annuity')
        feuill3.write(0, 0, 'Annuity')

        feuill4.write(0, 0, 'Annuity')

        feuill5.write(0, 0, 'Annuity')

        feuill6.write(0, 0, 'Annuity')

        feuill7.write(0, 0, 'Annuity')

        feuill8.write(0, 0, 'Annuity')

        # write results
        feuill1.write(0, 10, 'mean')
        feuill1.write(1, 10, str(mean_annuity))
        feuill1.write(0, 11, 'sigma')
        feuill1.write(1, 11, str(sigma_annuity))

        feuill2.write(0, 10, 'mean')
        feuill2.write(1, 10, str(mean_annuity_low))
        feuill2.write(0, 11, 'sigma')
        feuill2.write(1, 11, str(sigma_annuity_low))

        feuill3.write(0, 10, 'mean')
        feuill3.write(1, 10, str(mean_annuity_h))
        feuill3.write(0, 11, 'sigma')
        feuill3.write(1, 11, str(sigma_annuity_h))

        feuill4.write(0, 10, 'mean')
        feuill4.write(1, 10, str(mean_annuity_medium))
        feuill4.write(0, 11, 'sigma')
        feuill4.write(1, 11, str(sigma_annuity_medium))

        feuill5.write(0,10, 'mean')
        feuill5.write(1,10, str(mean_annuity_ec1))
        feuill5.write(0, 11, 'sigma')
        feuill5.write(1, 11, str(sigma_annuity_ec1))

        feuill6.write(0, 10, 'mean')
        feuill6.write(1, 10, str(mean_annuity_ec2))
        feuill6.write(0, 11, 'sigma')
        feuill6.write(1, 11, str(sigma_annuity_ec2))

        feuill7.write(0, 10, 'mean')
        feuill7.write(1, 10, str(mean_annuity_ec3))
        feuill7.write(0, 11, 'sigma')
        feuill7.write(1, 11, str(sigma_annuity_ec3))

        feuill8.write(0, 10, 'mean')
        feuill8.write(1, 10, str(mean_annuity_ec4))
        feuill8.write(0, 11, 'sigma')
        feuill8.write(1, 11, str(sigma_annuity_ec4))

        #ajout des valeurs dans la ligne suivante
        #ligne1 = feuill1.row(1)
        #ligne2 = feuill1.row(2)
        #ligne3 = feuill1.row(3)
        #ligne4 = feuill1.row(4)

        for value in range(len(El_results)):
            feuill1.write(value+1,0,str(El_results[value]))
            feuill1.write(value+1,1, str(Gas_results[value]))
            feuill1.write(value+1,2, str(Annuity_results_f[value]))
            feuill1.write(value+1,3, str(GHG_results[value]))

        for value in range(len(El_results)):
            feuill2.write(value+1,0,str(Annuity_results[value]))

        for value in range(len(El_results)):
            feuill3.write(value+1,0,str(Annuity_results_h[value]))

        for value in range(len(El_results)):
            feuill4.write(value+1,0,str(Annuity_results_m[value]))

        for value in range(len(El_results)):
            feuill5.write(value+1,0,str(Annuity_results_ec1[value]))

        for value in range(len(El_results)):
            feuill6.write(value+1,0,str(Annuity_results_ec2[value]))

        for value in range(len(El_results)):
            feuill7.write(value+1,0,str(Annuity_results_ec3[value]))

        for value in range(len(El_results)):
            feuill8.write(value+1,0,str(Annuity_results_ec4[value]))


        # creation materielle du fichier
        book.save(os.path.join(save_path_mc,results_excel_name))

    print('***********************************************************************************************************')
    print('Visualisation')
    print('***********************************************************************************************************')
    print()

    # ## Visualisation
    # Histogram figure

    fig, ((ax1,ax2), (ax3,ax4)) = plt.subplots(2, 2, figsize=(17,9))

    ax1.hist(El_results,50, normed=1)
    ax1.set_title('Final electrical demand in kWh')

    ax2.hist(Gas_results,50 , normed=1)
    ax2.set_title('Gas demand in kWh')

    ax3.hist(Annuity_results_f, 50, normed=1)
    ax3.set_title('Annuity in  Euro/year')

    ax4.hist(GHG_spe_results, 50 , normed=1)
    ax4.set_title('GHG specific emission in kg/kWh/year')

    fig.suptitle('Histogram energy demand in kWh/year for {} simulations '.format(Nsamples))
    fig.savefig(os.path.join(save_path_mc, 'Mainoutput.pdf'))

    # Box plot:
    fig2, ((ax5,ax6),(ax7,ax8)) = plt.subplots(2,2, figsize=(17,9))

    ax5.boxplot(El_results, showmeans=True, whis=99)
    ax5.set_title('Electrical demand in kWh')
    ax5.grid(color='b', alpha=0.5, linestyle='dashed', linewidth=0.5)
    ax6.boxplot(Gas_results, showmeans=True, whis=99)
    ax6.set_title('Gas demand in kWh')
    ax6.grid(color='b', alpha=0.5, linestyle='dashed', linewidth=0.5)
    ax7.boxplot(Annuity_results_f, showmeans=True, whis=99)
    ax7.set_title('Annuity in  Euro/year')
    ax7.grid(color='b', alpha=0.5, linestyle='dashed', linewidth=0.5)
    ax8.boxplot(GHG_spe_results, showmeans=True, whis=99)
    ax8.set_title('GHG specific emission in kg/kWh/year')
    ax8.grid(color='b', alpha=0.5, linestyle='dashed', linewidth=0.5)
    fig2.savefig(os.path.join(save_path_mc,'boxplot.pdf'))

    fig3,((ax11,ax12), (ax13,ax14)) = plt.subplots(2, 2, figsize=(17,9))
    ax12.hist(Th_results, 50)
    ax12.set_title('Thermal demand')
    ax11.hist(El_results, 50)
    ax11.set_title('Electrical demand after EBB')
    ax13.hist(el_results2, 50)
    ax13.set_title('Electrical demand for EBB')
    ax14.hist(Gas_results, 50)
    ax14.set_title('Gas demand')
    fig3.savefig(os.path.join(save_path_mc,'Energy_demand.pdf'))

    fig4, ((ax21, ax22), (ax23, ax24)) = plt.subplots(2, 2, figsize=(17,9))
    ax22.hist(Annuity_results_f, 50)
    ax22.set_title('Annuity_results_f')
    ax21.hist(Annuity_results, 50)
    ax21.set_title('Annuity_results low interest')
    ax23.hist(Annuity_results_h, 50)
    ax23.set_title('Annuity_results_h')
    ax24.hist(Annuity_results_m, 50)
    ax24.set_title('Annuity_results_m')
    fig4.savefig(os.path.join(save_path_mc,'Annuity_interest.pdf'))

    fig5, ((ax31, ax32), (ax33, ax34)) = plt.subplots(2, 2, figsize=(17,9))
    ax32.hist(Annuity_results_ec1, 50)
    ax32.set_title('Annuity_results_ec1')
    ax31.hist(Annuity_results_ec2, 50)
    ax31.set_title('Annuity_results ec2')
    ax33.hist(Annuity_results_ec3, 50)
    ax33.set_title('Annuity_results_ec3')
    ax34.hist(Annuity_results_ec4, 50)
    ax34.set_title('Annuity_results_ec4')
    fig5.savefig(os.path.join(save_path_mc,'Annuity_scenario.pdf'))

    #plt.show()

    #fig = plt.figure()
    #plt.hist(El_results, 100)
    #plt.xlabel('Electrical demand after EBB in kWh')

    #plt.show()


if __name__ == '__main__':

    do_uncertainty_analysis(Nsamples=10, time=10, Is_k_esys_parameters=True, time_sp_force_retro=40,
                            max_retro_year=2014, Is_k_user_parameters=True, interest_fix=0.05,
                            MC_analyse_total=True, Confident_intervall_pourcentage=90, save_result=True,
                            save_path_mc='D:\jsc-les\\test_lolo\\Results',
                            results_name='mc_results.txt', results_excel_name='mesresultats',
                            Is_k_building_parameters=False, esys_filename='City_lolo_esys_7build_ref.txt',
                            gen_e_net=True, network_filename='lolo_networks_7.txt',
                            city_pickle_name='wm_res_east_7_richardsonpy.pkl')
