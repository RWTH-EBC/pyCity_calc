#!/usr/bin/env python
# coding=utf-8

"""
Script to perform Morris sensitivity analysis using SaLib Library

Returns standard deviation and mean of the absolute value of the elementary effects for each parameter
"""
import os
import matplotlib.pyplot as plt
from pycity_calc.toolbox.mc_helpers.Morris_analysis.SALib_master.SALib.plotting.morris import horizontal_bar_plot, covariance_plot, sample_histograms
import pycity_calc.cities.scripts.overall_gen_and_dimensioning as City_gen
import copy
import pycity_calc.environments.market as Mark
from pycity_calc.toolbox.mc_helpers.Morris_analysis.SALib_master.SALib.sample.morris import sample
from pycity_calc.toolbox.mc_helpers.Morris_analysis.SALib_master.SALib.util import read_param_file
import pycity_calc.toolbox.mc_helpers.Morris_analysis.SA_evaluation_function as model_evaluation
from pycity_calc.toolbox.mc_helpers.Morris_analysis.SALib_master.SALib.analyze import morris
import pycity_calc.economic.economic_ann as economic_ann
import pycity_calc.economic.annuity_calculation as eco_calc
import pycity_calc.simulation.energy_balance_optimization.energy_balance_building as EBB
import pycity_calc.economic.calc_CO2_emission as GHG_calc


def run_Morris():

    # City Generation with start district data values and default parameters
    print('***********************************************************************************************************')
    print('Initialisation: Reference City Generation')
    print('***********************************************************************************************************')

    this_path = os.path.dirname(os.path.abspath(__file__))

    #  # Userinputs
    #  #----------------------------------------------------------------------

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
    print(' Prevent usage of electrical heating and hot water devices in electrical load generation : {}'.format(prev_heat_dev))

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
    filename = 'test_lolo.txt'
    txt_path = os.path.join(this_path, 'City_generation', 'input', filename)

    #  Define city district output file
    save_filename = 'test_lolo.p'
    save_path = os.path.join(this_path, 'City_generation', 'output', save_filename)

    #  #####################################
    t_set_heat = 20  # Heating set temperature in degree Celsius
    t_set_night = 16  # Night set back temperature in degree Celsius
    t_set_cool = 70  # Cooling set temperature in degree Celsius
    print('tset : ',t_set_heat, ' ;', t_set_cool, ' ;', t_set_night)

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
    network_path = os.path.join(this_path,'City_generation', 'input', 'input_en_network_generator',
                                network_filename)

    #  Add energy systems to city
    gen_esys = True  # True - Generate energy networks

    #  Path to energy system input file (csv/txt; tab separated)
    esys_filename = 'test_lolo_esys.txt'
    esys_path = os.path.join(this_path, 'City_generation', 'input','input_esys_generator',
                             esys_filename)

    #  #----------------------------------------------------------------------

    #  Load district_data file
    district_data = City_gen.citygen.get_district_data_from_txt(txt_path)
    print('district data : ', district_data)

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

    #  #----------------------------------------------------------------------
    # Energy balance calculations
    print("energy balance calculations")
    Calculator = EBB.calculator(City)
    dict_bes_data = Calculator.assembler()

    for i in range(len(dict_bes_data)):
        City, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)

    # Gas and electrical demand
    for n in City.nodes():
        if 'node_type' in City.node[n]:
                #  If node_type is building
            if City.node[n]['node_type'] == 'building':
                    #  If entity is kind building
                if City.node[n]['entity']._kind == 'building':

                    if 'electrical demand' in City.node[n]:
                        if type(City.node[n]['electrical demand']) != int:
                            el_dem_ref = sum(City.node[n][
                                                 'electrical demand']) * \
                                        City.environment.timer.timeDiscretization / 1000 / 3600

                    if 'fuel demand' in City.node[n]:
                        if type(City.node[n]['fuel demand']) != int:
                            gas_dem_ref = sum(City.node[n]['fuel demand']) * \
                                        City.environment.timer.timeDiscretization / 1000 / 3600



    # #----------------------------------------------------------------------

    time = 10  # Years
    interest = 0.05  # Interest rate
    Market_instance = Mark.Market()

    #  Generate economic calculator object
    print("Economic object generation")
    eco_inst = eco_calc.EconomicCalculation(time=time, interest=interest)

    # Annuity Calculation
    print("annuity calculations")
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

    print(GHG_Emission_ref)

    #Save the city
    print('***********************************************************************************************************')
    print('Save the city')
    print('***********************************************************************************************************')
    SaveCity = copy.deepcopy(City)
    print('Annual electricity demand : ' , SaveCity.get_annual_el_demand(), 'kWh/year')
    print('Annual thermal demand : ', SaveCity.get_total_annual_th_demand(), 'kWh/year')
    print('Annual electricity demand reference City after EBB : ', el_dem_ref, 'kWh/year')
    print('Annual gas demand reference City after EBB: ', gas_dem_ref, 'kWh/year')
    print('total reference annuity:', round(total_annuity_ref, 2))
    print('total emission reference City :', GHG_Emission_ref)

    print('***********************************************************************************************************')
    print('Do the Morris sample')
    print('***********************************************************************************************************')

    # Read the parameter range file and generate samples

    this_path = os.path.dirname(os.path.abspath(__file__))
    load_path_pam = os.path.join(this_path, 'City_generation', 'Morris_values.txt')

    problem = read_param_file(load_path_pam)

    Nsample = 1
    print(Nsample)

    # Generate samples for the SA of the electrical and gas demand
    param_values = sample(problem, N=Nsample, num_levels=5, grid_jump=1, optimal_trajectories=None)

    # Generate samples for the SA of the annuity and GHG emission
    #param_values_el_gas = param_values[:40, :]
    #param_values_eco_ghg = param_values


    print('par :  ', param_values)

    print('***********************************************************************************************************')
    print('Do the Morris simulations')
    print('***********************************************************************************************************')
    # Run the "model" -- this will happen offline for external models
    (Y, Z, H, A) = model_evaluation.evaluate(City, param_values)

    #Y[0] = gas_dem_ref
    #Z[0] = el_dem_ref
    #H[0] = GHG_Emission_ref
    #A[0] = total_annuity_ref

    print('Y: gas_dem after energy balance', Y)
    print('Z: el_dem after energy balance', Z)
    print('H: GHG emissions', H)
    print('A : annuity ', A)


    print('***********************************************************************************************************')
    print('Do the Morris analyse')
    print('***********************************************************************************************************')
    print('Analysis regarding gas_dem')
    Si_gas = morris.analyze(problem, param_values, Y, conf_level=0.95,
                    print_to_console=True,
                    num_levels=5, grid_jump=1, num_resamples=100)
    print (Si_gas)
    print (Si_gas.keys())

    print('Analysis regarding el_dem')
    Si_el = morris.analyze(problem, param_values, Z, conf_level=0.95,
                            print_to_console=True,
                            num_levels=5, grid_jump=1, num_resamples=100)

    print('Analysis regarding GHG')
    Si_ghg = morris.analyze(problem, param_values, H, conf_level=0.95,
                           print_to_console=True,
                           num_levels=5, grid_jump=1, num_resamples=100)

    print('Analysis regarding Annuity')
    Si_a = morris.analyze(problem, param_values, A, conf_level=0.95,
                            print_to_console=True,
                            num_levels=5, grid_jump=1, num_resamples=100)





    # Returns a dictionary with keys 'mu', 'mu_star', 'sigma', and 'mu_star_conf'
    # e.g. Si['mu_star'] contains the mu* value for each parameter, in the
    # same order as the parameter file

    print('Savecity: Annual electricity demand : ', SaveCity.get_annual_el_demand(), 'kWh/year')

    print('Y', Y)

    print('Savecity: Annual thermal demand : ', SaveCity.get_total_annual_th_demand(), 'kWh/year')

    print('Z', Z)

    print('***********************************************************************************************************')
    print('Visualisation')
    print('***********************************************************************************************************')
    fig, (ax1, ax2) = plt.subplots(1, 2)
    horizontal_bar_plot(ax1, Si_gas,{}, sortby='mu_star', unit=r"gas_dem[kWh]/year")
    covariance_plot(ax2, Si_gas, {}, unit=r"gas_dem[kWh]/year")
    fig.suptitle('gas demand analysis')

    fig2, (ax3, ax4) = plt.subplots(1, 2)
    horizontal_bar_plot(ax3, Si_el, {}, sortby='mu_star', unit=r"el_dem[kWh]/year")
    covariance_plot(ax4, Si_el, {}, unit=r"el_dem[kWh]/year")
    fig2.suptitle('electrical demand analysis')

    fig3, (ax5, ax6) = plt.subplots(1, 2)
    horizontal_bar_plot(ax5, Si_ghg, {}, sortby='mu_star', unit=r"GHG[kg]/year")
    covariance_plot(ax6, Si_ghg, {}, unit=r"GHG [kg]/year")
    fig3.suptitle ('GHG analysis')

    fig4, (ax7, ax8) = plt.subplots(1, 2)
    horizontal_bar_plot(ax7, Si_a, {}, sortby='mu_star', unit=r"Annuity[Euro]/year")
    covariance_plot(ax8, Si_a, {}, unit=r"Annuity [Euro]/year")
    fig4.suptitle('annuity analysis')


    plt.show()


if __name__ == '__main__':

    run_Morris()