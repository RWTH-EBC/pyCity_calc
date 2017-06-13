#!/usr/bin/env python
# coding=utf-8

'''

Script to perform a Monte Cralo anlysis of a city object.
Output are uncertain gas and electrical final demand and uncertain annuity and GHG emissions

'''

import os
import pickle
import copy
import pycity_calc.cities.scripts.overall_gen_and_dimensioning as City_gen
import pycity_calc.environments.market as Mark
import pycity_calc.simulation.energy_balance_optimization.energy_balance_building as EBB
import pycity_calc.economic.economic_ann as economic_ann
import pycity_calc.economic.annuity_calculation as eco_calc
import pycity_calc.economic.calc_CO2_emission as GHG_calc
import pycity_calc.toolbox.mc_helpers.Uncertainties_analysis.MC_new_city as newcity
import pycity_calc.toolbox.mc_helpers.weather.gen_weather_set as genweather
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

def do_uncertainty_analysis(Nsample=100):

    # Define Uncertainty analysis parameters
    # #############################################################################################################
    # ## City generation mode
    load_city = True  # load a pickle City file
    # if set to False: generation of a City with city_generator
    city_pickle_name = 'aachen_kronenberg_3_mfh_ref_1.pkl'

    Confident_intervall_pourcentage = 90


    # ## Uncertainty

    # weather is uncertain
    Is_unc_weather = True

    # energy systems parameters are uncertain (efficiency, maximum temperature...)
    Is_unc_esys_parameters = True

    # buildings parameters are uncertain (infiltration rate, net_floor_area, modernisation year)
    Is_unc_building_parameters = True

    # user parameters are uncertain (user_ventilations_rate, Tset_heat, number of occupants)
    Is_unc_user_parameters = True

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
        esys_filename = 'test_lolo_esys.txt'
        esys_path = os.path.join(this_path, 'City_generation', 'input', 'input_esys_generator', esys_filename)

        # Generate energy systems for city district
        if gen_esys:
            #  Load energy networks planing data
            list_esys = City_gen.esysgen.load_enersys_input_data(esys_path)
            print ('Add energy systems')

            #  Generate energy systems
            City_gen.esysgen.gen_esys_for_city(city=City, list_data=list_esys,
                                               dhw_scale=dhw_dim_esys)

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
        network_filename = 'test_lolo_networks.txt'
        network_path = os.path.join(this_path, 'City_generation', 'input', 'input_en_network_generator',
                                    network_filename)

        #  Add energy systems to city
        gen_esys = True  # True - Generate energy networks

        #  Path to energy system input file (csv/txt; tab separated)
        esys_filename = 'test_lolo_esys.txt'
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
                        el_dem_ref += sum(City.node[n]['electrical demand']) * \
                                          City.environment.timer.timeDiscretization / 1000 / 3600

                    if 'fuel demand' in City.node[n]:
                        gas_dem_ref += sum(City.node[n]['fuel demand']) * \
                                          City.environment.timer.timeDiscretization / 1000 / 3600

    # #----------------------------------------------------------------------
    # #----------------------------------------------------------------------

    # # Economic and GHG calculations

    time = 10  # Years
    interest = 0.05  # Interest rate
    Market_instance = Mark.Market()

    #  Generate economic calculator object
    print("Economic object generation")
    eco_inst = eco_calc.EconomicCalculation(time=time, interest=interest)

    # Annuity Calculation
    print("Annuity calculations")
    dem_rel_annuity = economic_ann.calc_dem_rel_annuity_city(City, eco_inst, Market_instance)
    total_proc_annuity = economic_ann.calc_proc_annuity_multi_comp_city(City, eco_inst)
    cap_rel_ann, op_rel_ann = economic_ann.calc_cap_and_op_rel_annuity_city(City, eco_inst)

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
    print('Do the samples')
    print('***********************************************************************************************************')
    # ## Do the dictionary for Monte Carlo uncertainty analysis sampling

    dict_sample = {}
    dict_sample['Nsample'] = Nsample

    # ## Define which parameters are uncertain
    dict_sample['uncertain_inputs'] = []
    if Is_unc_weather:
        dict_sample['uncertain_inputs'].append('weather')
        dict_sample['weather'] = genweather.gen_set_of_weathers(Nsample)
    if Is_unc_esys_parameters:
        dict_sample['uncertain_inputs'].append('esys')
    if Is_unc_building_parameters:
        dict_sample['uncertain_inputs'].append('buildings_parameters')
    if Is_unc_user_parameters:
        dict_sample['uncertain_inputs'].append ('user')


    print('***********************************************************************************************************')
    print('Do the simulations')
    print('***********************************************************************************************************')

    Sph_results, Gas_results , El_results, Annuity_results, GHG_results, GHG_spe_results = \
        newcity.new_city_evaluation_monte_carlo(City, dict_sample)

    print('***********************************************************************************************************')
    print('Do the Uncertainties analyse')
    print('***********************************************************************************************************')

    #print (El_results, Gas_results)

    # ## Results analysis - Standard deviation, mean and 90 confident interval

    # Gas demand
    print ()
    print ('Gas demand analysis')
    mean_gas_demand = sum(Gas_results)/ len(Gas_results)
    sigma_gas_demand = np.std(a=Gas_results)
    confident_inter_gas = stats.norm.interval(Confident_intervall_pourcentage/100, loc=mean_gas_demand, scale=sigma_gas_demand)

    print ('mean :', mean_gas_demand)
    print ('sigma :', sigma_gas_demand)
    print ('confident interval {}'.format(Confident_intervall_pourcentage), confident_inter_gas)
    print('{:0.2%} of the means are in confident interval'.format(((Gas_results >= confident_inter_gas[0]) & (Gas_results < confident_inter_gas[1])).sum() / float(Nsample)))
    print ()

    # Electrical demand
    print ('Electrical demand analysis')
    mean_el_demand = sum (El_results)/len(El_results)
    sigma_el_demand = np.std(a=El_results)
    confident_inter_el = stats.norm.interval(Confident_intervall_pourcentage / 100, loc=mean_el_demand,
                                              scale=sigma_el_demand)
    print('mean :', mean_el_demand)
    print('sigma :', sigma_el_demand)
    print ('confident interval {}'.format(Confident_intervall_pourcentage), confident_inter_el)
    print('{:0.2%} of the means are in confident interval'.format(
        ((El_results >= confident_inter_el[0]) & (El_results < confident_inter_el[1])).sum() / float(Nsample)))
    print()

    # Annuity
    print('Annuity analysis')
    mean_annuity = sum(Annuity_results)/len(Annuity_results)
    sigma_annuity = np.std(a=Annuity_results)
    confident_inter_a = stats.norm.interval(Confident_intervall_pourcentage / 100, loc=mean_annuity,
                                             scale=sigma_annuity)
    print('mean :', mean_annuity)
    print('sigma :', sigma_annuity)
    print('confident interval {}'.format(Confident_intervall_pourcentage), confident_inter_a)
    int('{:0.2%} of the means are in confident interval'.format(
        ((Annuity_results >= confident_inter_a[0]) & (Annuity_results < confident_inter_a[1])).sum() / float(Nsample)))
    print()

    # GHG
    print('GHG_analysis')
    mean_GHG = sum(GHG_results)/len(GHG_results)
    sigma_GHG = np.std(GHG_results)
    mean_spe_GHG = sum(GHG_spe_results)/len(GHG_spe_results)
    sigma_spe_GHG = np.std(a=GHG_spe_results)
    print('mean:', mean_GHG)
    print('sigma :', sigma_GHG)
    print('mean specific GHG :', mean_spe_GHG)
    print('sigma specific GHG :', sigma_spe_GHG)
    print ()

    # ## Visualisation

    # Histogram figure
    fig, ((ax1,ax2), (ax3,ax4)) = plt.subplots(2, 2)

    ax1.hist(El_results,20, normed=1)
    ax1.set_title('Electrical demand in kWh')

    ax2.hist(Gas_results,20 , normed=1)
    ax2.set_title('Gas demand in kWh')

    #ax3.hist(Sph_results,100, normed=1)
    #ax3.set_title('Space heating demand in kWh')

    ax3.hist(Annuity_results, 20, normed=1)
    ax3.set_title('Annuity in  Euro/year')

    ax4.hist(GHG_spe_results, 20, normed=1)
    ax4.set_title('GHG specific emission in kg/kWh/year')

    fig.suptitle('Histogram energy demand in kWh/year for {} simulations '.format(Nsample))
    plt.show()

if __name__ == '__main__':
    do_uncertainty_analysis()