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
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import random as rd

def do_uncertainty_analysis(Nsamples=10):

    # Define Uncertainty analysis parameters
    # #############################################################################################################
    # ## City generation mode
    load_city = True  # load a pickle City file
    # if set to False: generation of a City with city_generator
    city_pickle_name = 'aachen_kronenberg_3_mfh_ref_1.pkl'

    # ## Uncertainty

    # energy systems parameters are unknown (efficiency, maximum temperature...)
    Is_k_esys_parameters = True
    # Set to false: energy systems are known: buildings characteristics uncertainties

    # buildings parameters are unknown (infiltration rate, net_floor_area, modernisation year)
    Is_k_building_parameters = True
    # Set to False:  buildings parameters are known: building uncertainties (infiltration rate and net_floor_area)
    time_sp_force_retro = 40
    max_retro_year = 2014

    # user parameters are unknown (user_ventilation_rate, Tset_heat, number of occupants)
    Is_k_user_parameters = True
    #Set to False: user parameters are fixed

    # ## Economic calculations:
    # Interest rate is uncertain: Set to False: interest_rate is fixed
    interest_unc = True
    interest_rate_variation = 'low' #0-0.05
    #interest_rate_variation = 'medium' #0.05-0.1
    #interest_rate_variation = 'high' #0.1-0.2
    # if interest is fixed
    interest_fix = 0.05

    # Time for economic calculation in years (default: 10)
    time = 10  # Years

    MC_analyse_total = True

    # ## Analyse
    Confident_intervall_pourcentage = 90
    GHG_specific = 'user energy demand'

    # ## Save results
    save_result = True  # if set to false: no generation of results txt file
    results_name = 'mc_results.txt'

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

        load_path = os.path.join(this_path, 'City_generation', 'output', city_pickle_name)
        City = pickle.load(open(load_path, mode='rb'))

        print()
        print('load city from pickle file: {}'.format(city_pickle_name))
        print()

        #  Add energy systems to city
        gen_esys = True  # True - Generate energy systems
        gen_e_net = False# True - Generate energy networks
        dhw_dim_esys = True  # Use dhw profiles for esys dimensioning

        #  Path to energy system input file (csv/txt; tab separated)
        esys_filename = 'lolo_esys.txt'
        esys_path = os.path.join(this_path, 'City_generation', 'input', 'input_esys_generator', esys_filename)

        # Generate energy systems for city district
        if gen_esys:
            #  Load energy networks planing data
            list_esys = City_gen.esysgen.load_enersys_input_data(esys_path)
            print ('Add energy systems')

            #  Generate energy systems
            City_gen.esysgen.gen_esys_for_city(city=City, list_data=list_esys,
                                               dhw_scale=dhw_dim_esys)
        # else enter all the parameter your self


        #  Add energy networks to city
        if gen_e_net:  # True - Generate energy networks

            #  Path to energy network input file (csv/txt; tab separated)
            network_filename = 'lolo_networks.txt'

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

    if Is_k_building_parameters:
        dict_par_unc['build_physic_unc'] = True
    else:
        dict_par_unc['build_physic_unc'] = False
        # TODO rajouter le sample pour un equipement avec des proprietes totalement incertaines pour le batiments

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

    if interest_unc:
        if interest_rate_variation == 'low':
            max =  0.05
            min = 0
        elif interest_rate_variation== 'medium':
            max = 0.1
            min = 0.05
        elif interest_rate_variation=='high':
            max = 0.2
            min = 0.1
        else:
            print('Error: interest_rate_variation not valid: default value: low')
            max = 0.05
            min = 0

        interest_list = []
        for i in range(Nsamples):
            temp = rd.uniform(min, max)
            interest_list.append(temp)
    else:
        interest_list=[]
        for i in range (Nsamples):
            interest_list.append(interest_fix)
    dict_par_unc['interest'] = interest_list

    dict_par_unc['time'] = time

        # TODO rajouter le sample pour un equipement avec des proprietes vraiment incertaines et d'autres moins

    print('***********************************************************************************************************')
    print('Do the simulations')
    print('***********************************************************************************************************')


    Th_results, Gas_results, El_results, Annuity_results, GHG_results, \
    GHG_spe_results, el_results2, dict_city_pb, Nboiler_rescaled, NEH_rescaled, Lal_rescaled = \
        newcity.new_city_evaluation_monte_carlo(City, dict_par_unc)

    print('***********************************************************************************************************')
    print('Do the Uncertainties analyse')
    print('***********************************************************************************************************')
    # ## Results analysis - Standard deviation, mean and 90 confident interval

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

    # Annuity
    print('Annuity analysis')
    print('----------------')
    print('unit: Euro/year')

    mean_annuity = sum(Annuity_results)/len(Annuity_results)
    sigma_annuity = np.std(a=Annuity_results)
    confident_inter_a = stats.norm.interval(Confident_intervall_pourcentage / 100, loc=mean_annuity, scale=sigma_annuity)

    median_a = np.median(a=Annuity_results)
    first_quantil_a = stats.scoreatpercentile(Annuity_results, per=25)
    second_quantil_a = stats.scoreatpercentile(Annuity_results, per=50)
    third_quantil_a = stats.scoreatpercentile(Annuity_results, per=75)

    print('mean :', mean_annuity)
    print('sigma :', sigma_annuity)
    print('confident interval {}'.format(Confident_intervall_pourcentage), confident_inter_a)
    print('{:0.2%} of the means are in confident interval'.format(((Annuity_results >= confident_inter_a[0]) & (Annuity_results < confident_inter_a[1])).sum() / float(Nsamples)))
    print('median : ', median_a)
    print('first quantil : ', first_quantil_a)
    print('second quantil :', second_quantil_a)
    print('third quantil : ', third_quantil_a)
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

    print('***********************************************************************************************************')
    print('Save results')
    print('***********************************************************************************************************')

    if save_result:
        #  Write results file

        #  Log file path
        this_path = os.path.dirname(os.path.abspath(__file__))
        results_path = os.path.join(this_path, 'output', results_name)
        write_results = open(results_path, mode='w')

        write_results.write(' ---------- Monte Carlo Analysis ---------- \n ')

        write_results.write(' Number of sampling :' + str(Nsamples)+ '\n')

        write_results.write('\n############## Uncertain parameters ##############\n')
        write_results.write('user behaviour: ' + str(Is_k_user_parameters)+ '\n')
        write_results.write('energy systems parameters: ' + str(Is_k_esys_parameters)+ '\n')
        write_results.write('buildings parameters: ' + str(Is_k_building_parameters)+ '\n')
        write_results.write('interest_unc: ' + str(interest_unc) + '\n')
        write_results.write('interest_rate_variation: ' + str(interest_rate_variation) + '\n')
        write_results.write('interest_fix: ' + str(interest_fix) + '\n')

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

        write_results.write('\n Annuity\n')
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
            ((Annuity_results >= confident_inter_a[0]) & (Annuity_results < confident_inter_a[1])).sum() / float(
                Nsamples)) + '\n')

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


        write_results.write('\n Nboiler Lal rescaled: ' + str(Lal_rescaled))
        write_results.write('\n Nboiler rescaled' + str(Nboiler_rescaled))
        write_results.write('\n NEH rescaled' + str(NEH_rescaled))
        write_results.close()

    print('***********************************************************************************************************')
    print('Visualisation')
    print('***********************************************************************************************************')
    print()
    # ## Visualisation
    # Histogram figure

    fig, ((ax1,ax2), (ax3,ax4)) = plt.subplots(2, 2)

    ax1.hist(El_results,50, normed=1)
    ax2.set_title('Final electrical demand in kWh')

    ax2.hist(Gas_results,50 , normed=1)
    ax2.set_title('Gas demand in kWh')

    ax3.hist(Annuity_results, 50, normed=1)
    ax3.set_title('Annuity in  Euro/year')

    ax4.hist(GHG_spe_results, 50 , normed=1)
    ax4.set_title('GHG specific emission in kg/kWh/year')

    fig.suptitle('Histogram energy demand in kWh/year for {} simulations '.format(Nsamples))

    # Box plot:

    fig2, ((ax5,ax6),(ax7,ax8)) = plt.subplots(2,2)

    ax5.boxplot(El_results, showmeans=True, whis=99)
    ax5.set_title('Electrical demand in kWh')
    ax5.grid(color='b', alpha=0.5, linestyle='dashed', linewidth=0.5)
    ax6.boxplot(Gas_results, showmeans=True, whis=99)
    ax6.set_title('Gas demand in kWh')
    ax6.grid(color='b', alpha=0.5, linestyle='dashed', linewidth=0.5)
    ax7.boxplot(Annuity_results, showmeans=True, whis=99)
    ax7.set_title('Annuity in  Euro/year')
    ax7.grid(color='b', alpha=0.5, linestyle='dashed', linewidth=0.5)
    ax8.boxplot(GHG_spe_results, showmeans=True, whis=99)
    ax8.set_title('GHG specific emission in kg/kWh/year')
    ax8.grid(color='b', alpha=0.5, linestyle='dashed', linewidth=0.5)

    fig3,((ax11,ax12), (ax13,ax14)) = plt.subplots(2, 2)
    ax11.hist(Th_results, 50)
    ax11.set_title('Thermal demand')
    ax12.hist(el_results2, 50)
    ax12.set_title('Electrical demand for EBB')
    ax13.hist(El_results, 50)
    ax13.set_title('Electrical demand')
    ax14.hist(Gas_results, 50)
    ax14.set_title('Gas demand')
    plt.show()

    # Print samples
    for keys in dict_city_pb:
        print('Sampling building: {}'.format(keys))
        for keys2 in dict_city_pb[keys]:
            fig = plt.figure()
            print(keys2, dict_city_pb[keys][keys2])
            plt.hist(dict_city_pb[keys][keys2],50)
            plt.xlabel('Sampling for {}, {}'.format(keys, keys2))
            plt.ylabel('Number of values')
    plt.show()

if __name__ == '__main__':
    do_uncertainty_analysis()