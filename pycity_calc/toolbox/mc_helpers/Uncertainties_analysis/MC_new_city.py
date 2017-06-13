#!/usr/bin/env python
# coding=utf-8

'''

Script to do Monte Carlo simulations

Return :

'''

import copy
import pycity_calc.toolbox.mc_helpers.Uncertainties_analysis.MC_new_building as newB
import pycity_calc.toolbox.mc_helpers.demand_unc_single_build as dem_unc_b
import random
import pycity_calc.toolbox.dimensioning.dim_functions as dimfunc
import numpy as np
import pycity_calc.simulation.energy_balance_optimization.energy_balance_building as EBB
import pycity_calc.toolbox.user.user_air_exchange as user_air
import pycity_calc.economic.annuity_calculation as eco_calc
import pycity_calc.economic.economic_ann as economic_ann
import pycity_calc.environments.market as Mark
import pycity_calc.economic.calc_CO2_emission as GHG_calc




def new_city_evaluation_monte_carlo(City, dict_sample):

    # Save the City
    City_ref = copy.deepcopy(City)
    list_building = City_ref.get_list_build_entity_node_ids()

    Nloop = dict_sample['Nsample']


    Nboiler_rescaled = 0    # number of boiler rescaled (thermal demand to high)
    Gas_results = np.zeros(Nloop)  # array of annual gas demand
    El_results = np.zeros(Nloop)  # array of annual electrical demand after energy balance
    Sph_results = np.zeros(Nloop) #array of annual space heating demand
    Annuity_results = np.zeros(Nloop)
    GHG_results = np.zeros(Nloop)
    GHG_spe_results = np.zeros(Nloop)

    for loop in range (Nloop):

        print('_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-')
        print('simulations n° : ', loop)
        print('_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-')

        # ############################################

        # ## Environment for the new City

        # ###########################################

        year = City.environment.timer.year
        timestep = City.environment.timer.timeDiscretization

        # generation of a new weather if weather part of the uncertain inputs
        if 'weather' in dict_sample['uncertain_inputs']:

            new_weather = dict_sample['weather'][loop]
            City.environment.weather = new_weather

        ############################################

        # ## Generate new buildings

        ############################################

        # ## Loop over building

        for build in list_building:

            if City.node[build]['entity']._kind == 'building':

                # ## Get sample for new building generation
                dict_newvalues = dem_unc_b.building_unc_sampling(City.node[build]['entity'], 1)

                # ## Sort uncertain parameters
                if 'weather' in dict_sample['uncertain_inputs']:
                    dict_newvalues['weather'] = City.environment.weather
                else: dict_newvalues['weather'] = City_ref.environment.weather

                if 'buildings_parameters' in dict_sample['uncertain_inputs']:
                    dict_newvalues['net_floor_area'] = random.uniform(-0.05, 0.05)
                else:
                    dict_newvalues['mod_year'] = [City_ref.node[build]['entity'].mod_year]
                    dict_newvalues['inf'] = [user_air.get_inf_rate(City_ref.node[build]['entity'].mod_year)]

                if 'user' not in dict_sample['uncertain_inputs']:

                    # rescale Tset_heat
                    dict_newvalues['set_temp'] = []
                    for Nb_appart in range(len(City_ref.node[build]['entity'].appartments)):
                        dict_newvalues['set_temp'].append([20])

                    #rescale nb of accupants
                    dict_newvalues['occ'] = []
                    for appart in City_ref.node[build]['entity'].appartments:
                        temp = appart.get_max_nb_occupants()
                        dict_newvalues['occ'].append([temp])

                    #rescale user air ventilation rate
                    dict_newvalues['user'] = []
                    for appart in City_ref.node[build]['entity'].appartments:
                        temp = 0.2
                        dict_newvalues['user'].append([temp])

                    #rescale elctrical demand and domestical demand
                        dict_newvalues['el'] = []
                        dict_newvalues['dhw'] = []
                    for appart in City_ref.node[build]['entity'].appartments:
                        temp = sum(appart.get_total_el_power(currentValues=False)* timestep / (3600 * 1000))
                        temp2 = volume = sum(appart.demandDomesticHotWater.water) * timestep / 3600
                        dict_newvalues['el'].append([temp])
                        dict_newvalues['dhw'].append([temp2])



                    # ## function to rescale building with the new values
                City.node[build]['entity'] = newB.new_building_evaluation_mc(City.node[build]['entity'], dict_newvalues)

        ############################################

        # ## Generate new energy systems

        ############################################

        #  Generate new energy systems

        if 'esys' in dict_sample['uncertain_inputs']:
            City, rescale_boiler = new_evaluation_esys(City)

            if rescale_boiler == True:
                Nboiler_rescaled += 1

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

        #print()
        #print(loop, ' : ', 'Annual electricity demand : ', annual_el_dem, 'kWh/year')
        #print(loop, ' : ', 'Annual thermal demand : ', annual_sph_dem, 'kWh/year')
        #print(loop, ' : ', 'Annual domestic hot water : ', annual_dhw_dem, 'kWh/year')
        #print()

        ############################################

        # ## Energy balance

        ############################################


        # Energy balance calculations
        print("Energy balance calculations")
        Calculator = EBB.calculator(City)
        dict_bes_data = Calculator.assembler()

        for i in range(len(dict_bes_data)):
            City, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)

        # Gas and electrical demand
        el_dem = 0
        gas_dem = 0
        for n in City.nodes():
            if 'node_type' in City.node[n]:
                #  If node_type is building
                if City.node[n]['node_type'] == 'building':
                    #  If entity is kind building
                    if City.node[n]['entity']._kind == 'building':
                        if 'electrical demand' in City.node[n]:
                            el_dem += sum(City.node[n][
                                              'electrical demand']) * \
                                      City.environment.timer.timeDiscretization / 1000 / 3600

                        if 'fuel demand' in City.node[n]:
                            gas_dem += sum(City.node[n]['fuel demand']) * \
                                       City.environment.timer.timeDiscretization / 1000 / 3600


        print()
        print('loop n°:  ', loop)
        print('Annual electricity demand : ', annual_el_dem, 'kWh/year')
        print('Annual thermal demand : ', annual_th_dem, 'kWh/year')
        print('Annual reference electricity demand : ', City_ref.get_annual_el_demand(), 'kWh/year')
        print('Annual reference thermal demand : ', City_ref.get_total_annual_th_demand(), 'kWh/year')
        print ()
        print('Annual electricity demand after energy balance : ', el_dem, 'kWh/year')
        print('Annual gas demand after energy balance : ', gas_dem, 'kWh/year')
        print()


        ############################################

        # ## Economic analysis

        ############################################

        time = 10  # Years
        interest = 0.05  # Interest rate

        #  Generate economic calculator object
        print("Economic object generation")
        eco_inst = eco_calc.EconomicCalculation(time=time, interest=interest, )

        ## Annuity Calculation
        print("Annuity calculation")
        Market_instance = Mark.Market()

        # Annuity
        dem_rel_annuity = economic_ann.calc_dem_rel_annuity_city(City, eco_inst, Market_instance)
        total_proc_annuity = economic_ann.calc_proc_annuity_multi_comp_city(City, eco_inst)
        cap_rel_ann, op_rel_ann = economic_ann.calc_cap_and_op_rel_annuity_city(City, eco_inst)

        total_annuity = eco_inst.calc_total_annuity(ann_capital=cap_rel_ann,
                                                         ann_demand=dem_rel_annuity,
                                                         ann_op=op_rel_ann,
                                                         ann_proc=total_proc_annuity)

        print('Total_annuity:', round(total_annuity, 2) , 'Euro/year')

        print("Emission calculation")

        GHG = City.environment.co2emissions
        #print(New_City.environment.weather.qDirect)
        GHG_Emission = GHG_calc.CO2_emission_calc(city_object=City, emission_object=GHG , CO2_zero_lowerbound = False, eco_calc_instance= eco_inst )

        print(GHG_Emission, 'kg/year')

        Gas_results[loop] = gas_dem
        El_results[loop] = el_dem
        Sph_results [loop] = annual_sph_dem
        Annuity_results[loop] = total_annuity
        GHG_results[loop] = GHG_Emission
        GHG_spe_results[loop] = GHG_Emission / (annual_sph_dem + annual_dhw_dem + annual_el_dem)


    return Sph_results, Gas_results, El_results, Annuity_results, GHG_results, GHG_spe_results

def new_evaluation_esys (City):
    """
            Rescale energy systems of a city

            Parameters
            ----------
            City : object
                City object of pycity_calc

            Return :  City : City modified with the new energy systems
                      rescale_boiler : boolean : True if the boiler of the building was rescaled
            -------

    """
    print('New energy systems generation ')

    #  Save copy

    Cityref = copy.deepcopy(City)
    list_build = Cityref.get_list_build_entity_node_ids()

    # Rescale energy systems traits

    for build in list_build:

        if Cityref.node[build]['entity'].bes.hasBoiler == True:
            City.node[build]['entity'].bes.boiler.eta = random.uniform(0.8, 0.95)

        # Rescale boiler qNominal to cover all the thermal demand
        boiler_qNominal = City.node[build]['entity'].bes.boiler.qNominal

        demand_building = dimfunc.get_max_power_of_building(City.node[build]['entity'], with_dhw=True)

        rescale_boiler = False  # boolean to keep track of the number of rescaled boiler

        if Cityref.node[build]['entity'].bes.hasBoiler == True:

            if demand_building > boiler_qNominal:
                City.node[build]['entity'].bes.boiler.qNominal = \
                    dimfunc.round_esys_size(demand_building, round_up=True)
                rescale_boiler = True

                print()
                print('new boiler capacity kW: ', City.node[build]['entity'].bes.boiler.qNominal / 1000)
                print()

    return City, rescale_boiler


