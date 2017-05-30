#!/usr/bin/env python
# coding=utf-8

'''
Script to evaluate the output array for the Morris Analysis of a city object
Residential buildings only
Thermal space heating calculate with TEASER
Electrical load curve calculate with method 2: stochastic method
Generation of the Domestic Hot water profile with stochastic method

step 1: Load the district data
step 2: Generation of a city
step 3: energy balance

Return: Y: array of gas demand values after energy balance
        Z: array of electrical demand values after the energy balance

'''

import pycity_calc.cities.scripts.city_generator.city_generator as City_generator
import pycity_calc.simulation.energy_balance_optimization.energy_balance_building as EBB
import pycity_calc.economic.annuity_calculation as eco_calc
import pycity_calc.economic.economic_ann as economic_ann
import pycity_calc.environments.market as Mark
import pycity_calc.economic.calc_CO2_emission as GHG_calc
import numpy as np
import pycity_calc.toolbox.mc_helpers.weather.gen_weather_set as mc_weather
import copy
import pycity_calc.toolbox.teaser_usage.teaser_use as teaserusage
import pycity_calc.toolbox.mc_helpers.Morris_analysis.Building_evaluation_Morris as buildmod
import pycity_calc.toolbox.mc_helpers.Morris_analysis.Esystems_evaluation_Morris as esysmod


def evaluate(City, values):

    if type(values) != np.ndarray:
        raise TypeError("The argument `values` must be a numpy ndarray")

    # Save the City and building numbers

    City_ref = copy.deepcopy(City)
    list_building = City_ref.get_list_build_entity_node_ids()

    #  Generate environment
    #  ######################################################

    year = 2010
    timestep = City.environment.timer.timeDiscretization  # Timestep in seconds

    Y = np.zeros([values.shape[0]])
    Z = np.zeros([values.shape[0]])
    A = np.zeros([values.shape[0]])
    H = np.zeros([values.shape[0]])

    for loop, row in enumerate(values):

        print('_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-')
        print('row : ', loop)
        print('_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-')

        # --------------------------------------------------------------------------------------------------------
        City = copy.deepcopy(City_ref)


        ############################################

        # ## Generate an environment for the new City

        ############################################

        location = (row[0], row[1])  # (latitude, longitude)
        altitude = row[2]  # Altitude of location in m

        new_environment = City_generator.generate_environment(timestep=timestep, year=year,
                                           location=location,
                                           try_path=None,
                                           altitude=altitude)

        City.environment = new_environment

        # Weather generation for the new city
        weather_factor = row[3]

        # Generation of a 3 TRY weather (cold, warm, regular)
        dict_weather = mc_weather.get_warm_cold_regular_weather(year=year, timestep=timestep,
                                                                region_nb=5)
        # linear interpolation to define the new weather
        new_weather = mc_weather.calc_lin_ipl_weath(weath_dict=dict_weather, factor=weather_factor)

        City.environment.weather = new_weather

        '''# Save the weather file to further use in the city_generator
                    # TRY file start to read after lines 38
                    # qDirect = row [13]
                    # qDiffuse = row [14]
                    # tAmbient = row [8]
                    # first step: generation of an array with the weather data

                    new_weather_array = np.zeros((8798, 18))
                    new_weather_array[38:, 13] = new_weather.qDiffuse
                    new_weather_array[38:, 14] = new_weather.qDirect
                    new_weather_array[38:, 8] = new_weather.tAmbient

                    filname_weather = 'TRY_morris.dat'
                    Mypath = os.path.dirname(os.path.dirname(
                        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

                    save_weather_path = os.path.join(Mypath, 'pyCity', 'pycity', 'inputs', 'weather', filname_weather)

                    save_weather = open(save_weather_path, mode='w')

                    np.savetxt(save_weather_path, new_weather_array)

                    # close the file
                    save_weather.close()

                    # TRY path definition
                    try_path = None'''

        for n in list_building:
            if City.node[n]['entity']._kind == 'building':

                # function to recalculate building electrical_curve DHW and Space Heating Curve

                City.node[n]['entity'] = buildmod.new_evaluation_building(City.node[n]['entity'], parameters=row[4: 12])


        ############################################

        # ## Generate new space heating curve

        ############################################

        # ## Rescaling Space Heating generation

        vent_factor = row[12]
        Tset_heat = row[13]
        Tset_night = row[14]
        Tset_cool = 70

        print()
        teaserusage.calc_and_add_vdi_6007_loads_to_city(city=City,
                                                       air_vent_mode=0,
                                                       vent_factor=vent_factor,
                                                       t_set_heat=Tset_heat,
                                                       t_set_cool=Tset_cool,
                                                       t_night=Tset_night)
        print()


        ############################################

        # ## Generate new energy systems

        ############################################

        #  Generate energy systems

        City = esysmod.new_evaluation_esys(City, parameters=row[15: 40])



        ############################################

        # ## Get energy curves

        ############################################

        annual_el_dem = City.get_annual_el_demand()
        annual_th_dem = City.get_total_annual_th_demand()
        print()
        print('Annual electricity demand : ', annual_el_dem, 'kWh/year')
        print('Annual thermal demand : ', annual_th_dem, 'kWh/year')
        print()

        ############################################

        # ## Energy balance

        ############################################


        # Energy balance calculations
        print("Energy balance calculations")
        Calculator = EBB.calculator(City)
        dict_bes_data = Calculator.assembler()

        #print('Dict city data', dict_bes_data)
        for i in range(len(dict_bes_data)):
            City, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)

        #Gas and electrical demand
        for n in City.nodes():
            if 'node_type' in City.node[n]:
                #  If node_type is building
                if City.node[n]['node_type'] == 'building':
                    #  If entity is kind building
                    if City.node[n]['entity']._kind == 'building':

                        if 'electrical demand' in City.node[n]:
                            if type(City.node[n]['electrical demand']) != int:
                                el_dem = sum(City.node[n][
                                                 'electrical demand']) *\
                                         City.environment.timer.timeDiscretization / 1000 / 3600

                        if 'fuel demand' in City.node[n]:
                            if type(City.node[n]['fuel demand']) != int:
                                gas_dem = sum(City.node[n]['fuel demand']) *\
                                          City.environment.timer.timeDiscretization / 1000 / 3600

        print()
        print('Annual electricity demand : ', annual_el_dem, 'kWh/year')
        print('Annual thermal demand : ', annual_th_dem, 'kWh/year')
        print('Annual electricity demand after energy balance : ', el_dem, 'kWh/year')
        print('Annual gas demand after energy balance : ', gas_dem, 'kWh/year')
        print()

        Y[loop] = gas_dem
        Z[loop] = el_dem

        ############################################

        # ## Economic analysis

        ############################################

        time = 10  # Years
        interest = 0.05  # Interest rate

        price_ch_cap = row[40]
        price_ch_dem_gas = row[41]
        price_ch_dem_el = row[42]
        price_ch_op = row[43]
        price_ch_proc_chp = row[44]
        price_ch_proc_pv = row[45]
        price_ch_EEG_Umlage_tax_chp = row[46]
        price_ch_EEG_Umlage_tax_pv = row[47]
        price_EEX_baseload_price = row[48]
        price_ch_avoid_grid_usage = row[49]
        price_ch_sub_chp = row[50]
        price_ch_self_usage_chp = row[51]
        price_ch_gas_disc_chp = row[52]
        price_ch_sub_pv = row[53]
        life_factor = row[54]
        maintenance_factor = row[55]
        # market_factor_el = row [65]
        # market_factor_gas = row [66]


        #  Generate economic calculator object
        print("Economic object generation")
        eco_inst = eco_calc.EconomicCalculation(time=time, interest=interest, price_ch_cap=price_ch_cap,
                                                price_ch_dem_gas=price_ch_dem_gas, price_ch_dem_el=price_ch_dem_el,
                                                price_ch_op=price_ch_op, price_ch_proc_chp=price_ch_proc_chp,
                                                price_ch_proc_pv=price_ch_proc_pv,
                                                price_ch_EEG_Umlage_tax_chp=price_ch_EEG_Umlage_tax_chp,
                                                price_ch_EEG_Umlage_tax_pv=price_ch_EEG_Umlage_tax_pv,
                                                price_EEX_baseload_price=price_EEX_baseload_price,
                                                price_ch_avoid_grid_usage=price_ch_avoid_grid_usage,
                                                price_ch_sub_chp=price_ch_sub_chp,
                                                price_ch_self_usage_chp=price_ch_self_usage_chp,
                                                price_ch_gas_disc_chp=price_ch_gas_disc_chp,
                                                price_ch_sub_pv=price_ch_sub_pv)

        # Modification lifetime and maintenance
        for key1 in eco_inst.dict_lifetimes.keys():
            tempp = eco_inst.dict_lifetimes[key1] * life_factor
            eco_inst.dict_lifetimes[key1] = tempp

        for key2 in eco_inst.dict_maintenance.keys():
            tempp = eco_inst.dict_maintenance[key2] * maintenance_factor
            eco_inst.dict_maintenance[key2] = tempp

        ## Annuity Calculation
        print("Annuity calculation")
        Market_instance = Mark.Market()

        # Rescaling market object for the SA
        #Market_instance.el_price_data_res = Market_instance.el_price_data_res*market_factor_el
        #Market_instance.el_price_data_ind = Market_instance.el_price_data_ind*market_factor_el
        #Market_instance.gas_price_data_res = Market_instance.gas_price_data_res*market_factor_gas
        #Market_instance.gas_price_data_ind = Market_instance.gas_price_data_ind*market_factor_gas


        # Annuity
        dem_rel_annuity = economic_ann.calc_dem_rel_annuity_city(City, eco_inst, Market_instance)
        total_proc_annuity = economic_ann.calc_proc_annuity_multi_comp_city(City, eco_inst)
        cap_rel_ann, op_rel_ann = economic_ann.calc_cap_and_op_rel_annuity_city(City, eco_inst)

        total_annuity = eco_inst.calc_total_annuity(ann_capital=cap_rel_ann,
                                                         ann_demand=dem_rel_annuity,
                                                         ann_op=op_rel_ann,
                                                         ann_proc=total_proc_annuity)
        print('Total_annuity:', round(total_annuity, 2) , 'Euro/year')
        A[loop] = total_annuity

        print("Emission calculation")

        GHG = City.environment.co2emissions
        #print(New_City.environment.weather.qDirect)
        GHG_Emission = GHG_calc.CO2_emission_calc(city_object=City, emission_object=GHG , CO2_zero_lowerbound = False, eco_calc_instance= eco_inst )

        print(GHG_Emission, 'kg/year')
        H[loop]=GHG_Emission

    return(Y, Z, A, H)
