#!/usr/bin/env python
# coding=utf-8

"""
Script to perform Morris sensitivity analysis using SaLib Library

Returns standard deviation and mean of the elementary effects absolute value for each parameter


Structure:
1: Define parameter for Morris analysis
    City generation method: - from a pickle file
                            - Generation with City_generator

    Morris_name:  text file with uncertain inputs for city model and associated boundaries

    Number of Samples


    Results: Save the results in a text file: True or False
             Filename

    Economic:   time (years)

2: Reference City generation and add energy systems

3: Sampling with Salib library

4: City simulations

5: Analyse of simulations

6: Save of analysis results

7: Visualisation

"""

import os
import matplotlib.pyplot as plt
import pycity_calc.cities.scripts.overall_gen_and_dimensioning as City_gen
import copy
import pycity_calc.environments.germanmarket as Mark
import pycity_calc.toolbox.mc_helpers.Morris_analysis.SA_evaluation_function as model_evaluation
from SALib.analyze import morris
from SALib.sample.morris import sample
from SALib.util import read_param_file
from SALib.plotting.morris import horizontal_bar_plot, covariance_plot, sample_histograms
import pycity_calc.economic.annuity_calculation as eco_calc
import pycity_calc.simulation.energy_balance_optimization.energy_balance_building as EBB
import pycity_calc.economic.calc_CO2_emission as GHG_calc
import pickle
import numpy as np


def run_Morris():

    # Define the Morris parameters
    # #############################################################################################################

    # number of samples
    Nsample = 5
    print(Nsample)
    Morris_name = 'Morris_values.txt' # filename of the parameters definition variation space for the Morris analysis
    Scenario = 1

    # City generation mode
    load_city = True  # load a pickle City file
    # if set to False: generation of a City with city_generator
    city_pickle_name = 'aachen_kronenberg_3_mfh_ref_1.pkl'

    # results
    save_result = True  # if set to false: no generation of results txt file
    results_name = 'Morris_results.txt'

    # Ecomomic
    time = 10  # Years

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
        gen_esys = True  # True - Generate energy networks
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
            City_gen.esysgen.gen_esys_for_city(city=City, list_data=list_esys, dhw_scale=dhw_dim_esys)

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
        save_filename = 'lolo.p'
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
    # Save reference city
    SaveCity = copy.deepcopy(City)
    ref_annual_electrical_demand_for_EBB = SaveCity.get_annual_el_demand()
    ref_annual_thermal_demand = SaveCity.get_total_annual_th_demand()

    # # Energy balance calculations

    print("Energy balance calculations")
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
                        el_dem_ref += sum(City.node[n]['electrical demand']) *City.environment.timer.timeDiscretization / 1000 / 3600

                    if 'fuel demand' in City.node[n]:
                        gas_dem_ref += sum(City.node[n]['fuel demand']) * City.environment.timer.timeDiscretization / 1000 / 3600
    # #----------------------------------------------------------------------
    # #----------------------------------------------------------------------

    # # Economic and GHG calculations
    Market_instance = Mark.GermanMarket()
    interest = 0.05  # Interest rate

    #  Generate economic calculator object
    print("Economic object generation")
    eco_inst = eco_calc.EconomicCalculation(time=time,germanmarket=Market_instance, interest=interest)

    # Annuity Calculation
    print("Annuity calculations")
    dem_rel_annuity = eco_inst.calc_dem_rel_annuity_city(City)
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

    #print('GHG emissions: kg/year')
    #print(GHG_Emission_ref)

    print('***********************************************************************************************************')
    print('Save the city')
    print('***********************************************************************************************************')

    print('Annual electricity demand : ', ref_annual_electrical_demand_for_EBB, 'kWh/year')
    print('Annual thermal demand : ', ref_annual_thermal_demand , 'kWh/year')
    print('Annual electricity demand reference City after EBB : ', el_dem_ref, 'kWh/year')
    print('Annual gas demand reference City after EBB: ', gas_dem_ref, 'kWh/year')
    print('total reference annuity:', round(total_annuity_ref, 2), ' Euro/year')
    print('total emission reference City :', GHG_Emission_ref, ' kg/year ')

    print('***********************************************************************************************************')
    print('Do the Morris samples')
    print('***********************************************************************************************************')

    # Read the parameter range file and generate samples

    this_path = os.path.dirname(os.path.abspath(__file__))
    load_path_pam = os.path.join(this_path, 'City_generation', Morris_name)

    problem = read_param_file(load_path_pam)

    Nparameters = len(problem['names'])

    # Generate samples for the SA of the electrical and gas demand
    param_values = sample(problem, N=Nsample, num_levels=5, grid_jump=1, optimal_trajectories=None)

    print('par :  ', param_values)

    print('***********************************************************************************************************')
    print('Do the Morris simulations')
    print('***********************************************************************************************************')
    # Run the "model" -- this will happen offline for external models
    (Gas_results, El_results, Emissions_results, Annuity_results, Spe_Emission_results, liste_max_dhw, liste_max_el,
     liste_max_sph, liste_shp_curve, liste_el_curve, liste_dhw_curve) =\
        model_evaluation.evaluate(City, param_values)

    print('***********************************************************************************************************')
    print('Do the Morris analyse')
    print('***********************************************************************************************************')
    print('Analysis regarding gas_dem')
    Si_gas = morris.analyze(problem, param_values, Gas_results, conf_level=0.95,
                    print_to_console=True,
                    num_levels=5, grid_jump=1, num_resamples=100)

    print('Analysis regarding el_dem')
    Si_el = morris.analyze(problem, param_values, El_results, conf_level=0.95,
                            print_to_console=True,
                            num_levels=5, grid_jump=1, num_resamples=100)

    print('Analysis regarding GHG')
    Si_ghg = morris.analyze(problem, param_values, Emissions_results, conf_level=0.95,
                           print_to_console=True,
                           num_levels=5, grid_jump=1, num_resamples=100)

    Si_ghg_spe = morris.analyze(problem, param_values, Spe_Emission_results, conf_level=0.95,
                            print_to_console=True,
                            num_levels=5, grid_jump=1, num_resamples=100)

    print('Analysis regarding Annuity')
    Si_a = morris.analyze(problem, param_values,Annuity_results, conf_level=0.95,
                            print_to_console=True,
                            num_levels=5, grid_jump=1, num_resamples=100)


    # Returns a dictionary with keys 'mu', 'mu_star', 'sigma', and 'mu_star_conf'
    # e.g. Si['mu_star'] contains the mu* value for each parameter, in the
    # same order as the parameter file

    print('***********************************************************************************************************')
    print('Save results')
    print('***********************************************************************************************************')

    if save_result:
        #  Write results file

        #  Log file path
        this_path = os.path.dirname(os.path.abspath(__file__))
        results_path = os.path.join(this_path, 'output', results_name)

        write_results = open(results_path, mode='w')
        write_results.write(' Morris analysis -Test Modernisation year 1970-2015 \n ')

        write_results.write(' Number of sampling :' + str(Nsample))

        write_results.write('\n##############Parameters for the sensibility##############\n')
        for j in list(range(len(problem['names']))):
            write_results.write(" {} {} \n".format(problem['names'][j],problem['bounds'][j]))

        write_results.write('\n############## City reference ##############\n')
        if load_city == True:
            generation_mode = 'load City from pickle file'
            write_results.write('Generation mode: ' + generation_mode)
            write_results.write('pickle file path :  ' + str(load_path))
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

        write_results.write('\n Annual electricity demand : ' + str(ref_annual_electrical_demand_for_EBB) + 'kWh/year')
        write_results.write('\n Annual thermal demand : ' + str(ref_annual_thermal_demand) + 'kWh/year')
        write_results.write('\n Annual electricity demand reference City after EBB : ' + str(el_dem_ref) + 'kWh/year')
        write_results.write('\n Annual gas demand reference City after EBB: ' + str(gas_dem_ref) + 'kWh/year')
        write_results.write('\n total reference annuity:' + str(round(total_annuity_ref, 2))+ ' Euro/year')
        write_results.write('\n total emission reference City :' + str(GHG_Emission_ref) + ' kg/year \n')

        write_results.write('\n############################Results #########################\n')
        write_results.write('\n gas demand\n')
        write_results.write("\n {0:<30} {1:>10} {2:>10} {3:>15} {4:>10} \n".format("Parameter", "Mu_Star",
                                                                             "Mu", "Mu_Star_Conf", "Sigma"))
        for j in list(range(len(Si_gas['names']))):
            write_results.write(" {0:30} {1:10.3f} {2:10.3f} {3:15.3f} {4:10.3f} \n".format(Si_gas['names'][j],
                                                                                        Si_gas['mu_star'][j],
                                                                                        Si_gas['mu'][j],
                                                                                        Si_gas['mu_star_conf'][j],
                                                                                        Si_gas['sigma'][j]))
        write_results.write('\n------------------------------------------------------------------\n')
        write_results.write('\nelectrical demand\n')
        write_results.write("\n {0:<30} {1:>10} {2:>10} {3:>15} {4:>10}\n".format("Parameter", "Mu_Star",
                                                                             "Mu", "Mu_Star_Conf", "Sigma"))
        for j in list(range(len(Si_el['names']))):
            write_results.write(" {0:30} {1:10.3f} {2:10.3f} {3:15.3f} {4:10.3f} \n".format(Si_el['names'][j],
                                                                                        Si_el['mu_star'][j],
                                                                                        Si_el['mu'][j],
                                                                                        Si_el['mu_star_conf'][j],
                                                                                        Si_el['sigma'][j]))

        write_results.write('\n------------------------------------------------------------------\n')
        write_results.write('annuity')
        write_results.write(" {0:<30} {1:>10} {2:>10} {3:>15} {4:>10} \n".format("Parameter", "Mu_Star",
                                                                             "Mu", "Mu_Star_Conf", "Sigma"))
        for j in list(range(len(Si_a['names']))):
            write_results.write(" {0:30} {1:10.3f} {2:10.3f} {3:15.3f} {4:10.3f} \n".format(Si_a['names'][j],
                                                                                        Si_a['mu_star'][j],
                                                                                        Si_a['mu'][j],
                                                                                        Si_a['mu_star_conf'][j],
                                                                                        Si_a['sigma'][j]))
        write_results.write('\n------------------------------------------------------------------\n')
        write_results.write('\n Ghg\n')
        write_results.write(" {0:<30} {1:>10} {2:>10} {3:>15} {4:>10} \n".format("Parameter", "Mu_Star",
                                                                             "Mu", "Mu_Star_Conf", "Sigma"))
        for j in list(range(len(Si_ghg['names']))):
            write_results.write(" {0:30} {1:10.3f} {2:10.3f} {3:15.3f} {4:10.3f}\n".format(Si_ghg['names'][j],
                                                                                        Si_ghg['mu_star'][j],
                                                                                        Si_ghg['mu'][j],
                                                                                        Si_ghg['mu_star_conf'][j],
                                                                                        Si_ghg['sigma'][j]))
        write_results.write('\n------------------------------------------------------------------\n')
        write_results.write('\n  Number of City generated {}\n'.format(Nsample*(Nparameters+1)))
        write_results.close()

    print('***********************************************************************************************************')
    print('Visualisation')
    print('***********************************************************************************************************')
    print ()
    print ('Number of samples: {} '.format(Nsample))
    print ('Number of City generated {}'.format(Nsample*(Nparameters+1)))

    fig, (ax1, ax2) = plt.subplots(1, 2)
    horizontal_bar_plot(ax1, Si_gas,{}, sortby='mu_star', unit=r"gas_dem[kWh]/year")
    covariance_plot(ax2, Si_gas, {}, unit=r"gas_dem[kWh]/year")
    fig.suptitle('Gas demand analysis for {} samples, Sc n°{}'.format(Nsample, Scenario))

    fig2, (ax3, ax4) = plt.subplots(1, 2)
    horizontal_bar_plot(ax3, Si_el, {}, sortby='mu_star', unit=r"el_dem[kWh]/year")
    covariance_plot(ax4, Si_el, {}, unit=r"el_dem[kWh]/year")
    fig2.suptitle('Electrical demand analysis for {} samples, Sc n°{}'.format(Nsample, Scenario))

    fig3, (ax5, ax6) = plt.subplots(1, 2)
    horizontal_bar_plot(ax5, Si_ghg, {}, sortby='mu_star', unit=r"GHG[kg]/year")
    covariance_plot(ax6, Si_ghg, {}, unit=r"GHG [kg]/year")
    fig3.suptitle ('GHG analysis for {} samples, Sc n°{}'.format(Nsample,Scenario))

    fig6, (ax9, ax10) = plt.subplots(1, 2)
    horizontal_bar_plot(ax9, Si_ghg_spe, {}, sortby='mu_star', unit=r"GHG[kg]/kWh*year")
    covariance_plot(ax10, Si_ghg_spe, {}, unit=r"GHG [kg]/kWh*year")
    fig6.suptitle('Specific GHG analysis for {} samples, Sc n°{}, '.format(Nsample, Scenario))

    fig4, (ax7, ax8) = plt.subplots(1, 2)
    horizontal_bar_plot(ax7, Si_a, {}, sortby='mu_star', unit=r"Annuity[Euro]/year")
    covariance_plot(ax8, Si_a, {}, unit=r"Annuity[Euro]/year")

    fig4.suptitle('Annuity analysis for {} samples, Sc n°{}'.format(Nsample, Scenario))

    '''# visualisation demand curves
    fig5, axarr = plt.subplots(2, 2)

    for curve in liste_shp_curve:
        axarr[0, 0].plot(curve/1000, alpha=0.5)

    axarr[0, 0].plot(SaveCity.get_aggr_space_h_power_curve()/1000, 'blue', label='City_ref', linewidth=3, )
    axarr[0, 0].set_title('Space heating demand in kW')

    for curve in liste_dhw_curve:
        axarr[0, 1].plot(curve/1000)
    axarr[0, 1].plot(SaveCity.get_aggr_dhw_power_curve() / 1000, 'blue', label='City_ref', linewidth=2)
    axarr[0, 1].set_title('Domestic Hot water demand in kW')

    for curve in liste_el_curve:
        axarr[1, 0].plot(curve/1000)
    axarr[1, 0].plot(SaveCity.get_aggr_el_power_curve()/1000,'blue', label='City_ref', linewidth=1)
    axarr[1, 0].set_title('Electrical demand in kW')

    axarr[1, 1].plot = plt.hist(liste_max_sph, 50, normed=1)
    axarr[1, 1].set_title('Maximal thermal demand in kWh, City_ref: {} kWh'.format(round(SaveCity.get_total_annual_th_demand(), 2)))

    fig5.suptitle('Energy demand curves in kW ')'''
    plt.show()


if __name__ == '__main__':
    run_Morris()
