#!/usr/bin/env python
# coding=utf-8

'''
Script to evaluate  output arrays for the Morris Analysis of a city object
Residential buildings only
Thermal space heating calculate with TEASER
Electrical load curve calculate with method 2: stochastic method
Generation of the Domestic Hot water profile with stochastic method

step 1: Initialisation
step 2: Generation of a new city (energy curves recalculation)
step 3: energy balance
step 4: economic calculation
step 5: emissions calculation

Return: Y: array of gas demand values after energy balance
        Z: array of electrical demand values after the energy balance
        A : array of annuity
        H : array of ghg emission kg/year
        F : array of specific ghg emission kg/kwhyear
        Inter_el : list of intermediate annual electrical demand (for energy balance)
        Inter_dhw : list of intermediate annual domestic hot water demand (for energy balance)
        Inter_sph : list of intermediate annual space heating  demand (for energy balance)
        liste_shp_curve : list of intermediate electrical curve demand (for energy balance)
        liste_el_curve : list of intermediate space heating demand curve(for energy balance)
        liste_dhw_curve : list of intermediate domestic hot water demand curve(for energy balance)
        liste_max_sph : list of intermediate maximum space heating  demand (for energy balance)
        liste_max_el : list of intermediate maximum electrical demand (for energy balance)
        liste_max_dhw : list of intermediate maximum domestic hot water demand (for energy balance)

        Nboiler_rescaled : number of City with  rescaled boiler(space heating demand to high)

'''

import pycity_calc.cities.scripts.city_generator.city_generator as City_generator
import pycity_calc.simulation.energy_balance_optimization.energy_balance_building as EBB
import pycity_calc.economic.annuity_calculation as eco_calc
import pycity_calc.environments.germanmarket as Mark
import pycity_calc.economic.calc_CO2_emission as GHG_calc
import numpy as np
import pycity_calc.toolbox.mc_helpers.weather.gen_weather_set as mc_weather
import copy
import pycity_calc.toolbox.teaser_usage.teaser_use as teaserusage
import pycity_calc.toolbox.mc_helpers.Morris_analysis.Building_evaluation_Morris as buildmod
import pycity_calc.toolbox.mc_helpers.Morris_analysis.Esystems_evaluation_Morris as esysmod
import pycity_calc.toolbox.dimensioning.dim_functions as dimfunc
import pycity_calc.simulation.energy_balance_optimization.Energy_balance_lhn as EB

def evaluate(City, values):

    """
    Rescale City with new values for Morris analysis

    Parameters
    ----------
    City : object
        City object from pycity_calc
    values: Array with rescaling parameters
            Structure:
            Columns:
            0: longitude
            1: latitude
            2: Altitude
            3: weather
            4: net_floor_area
            5: average_height_of_floors
            6: year_of_modernization
            7: dormer
            8: attic
            9: cellar
            10: construction type
            11 total_number_occupants
            12: Annual_el_e_dem
            13: dhw_Tflow
            14: dhw_Tsupply
            15: vent_factor
            16: tset_heat
            17: tset_night
            18 - 42: energy systems parameters
            43-56: market parameters
            57: life_factor for energy systems
            58: maintenance_factor for energy systems
            59: interest

    Returns
    -------
        Y: array of gas demand values after energy balance
        Z: array of electrical demand values after the energy balance
        A : array of annuity
        H : array of ghg emission kg/year
        F : array of specific ghg emission kg/kwhyear
        Inter_el : list of intermediate annual electrical demand (for energy balance)
        Inter_dhw : list of intermediate annual domestic hot water demand (for energy balance)
        Inter_sph : list of intermediate annual space heating  demand (for energy balance)
        liste_shp_curve : list of intermediate electrical curve demand (for energy balance)
        liste_el_curve : list of intermediate space heating demand curve(for energy balance)
        liste_dhw_curve : list of intermediate domestic hot water demand curve(for energy balance)
        liste_max_sph : list of intermediate maximum space heating  demand (for energy balance)
        liste_max_el : list of intermediate maximum electrical demand (for energy balance)
        liste_max_dhw : list of intermediate maximum domestic hot water demand (for energy balance)

        Nboiler_rescale : number of City with  rescaled boiler(space heating demand to high)
    """

    if type(values) != np.ndarray:
        raise TypeError("The argument `values` must be a numpy ndarray")

    Y = np.zeros([values.shape[0]])  # array of annual gas demand
    Z = np.zeros([values.shape[0]])  # array of annual electrical demand after energy balance
    A = np.zeros([values.shape[0]])  # array of annuity
    H = np.zeros([values.shape[0]])  # array of ghg emission kg/year
    F = np.zeros([values.shape[0]])  # array of specific ghg emission kg/kwhyear
    Inter_el = np.zeros([values.shape[0]])  # array of annual electrical demand for energy balance
    Inter_dhw = np.zeros([values.shape[0]])  # array of annual dhw demand
    Inter_sph = np.zeros([values.shape[0]])  # array of annual SPH demand
    liste_shp_curve = []
    liste_el_curve = []
    liste_dhw_curve = []
    liste_max_sph = np.zeros([values.shape[0]])
    liste_max_el = np.zeros([values.shape[0]])
    liste_max_dhw = np.zeros([values.shape[0]])

    Nboiler_rescaled = 0 # number of boiler rescaled (thermal demand to high)


    # Save the City and building numbers

    City_ref = copy.deepcopy(City)
    list_building = City_ref.get_list_build_entity_node_ids()

    #  Generate environment
    #  ######################################################

    year = 2010
    timestep = City.environment.timer.timeDiscretization  # Timestep in seconds


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

        ############################################

        # ## Generate new buildings

        ############################################

        print ('\nStart loop over buildings')
        for n in list_building:
            print ('\nBuilding n°: {}'.format(n))
            print ('-----------------')
            if City.node[n]['entity']._kind == 'building':

                # function to recalculate building electrical_curve DHW and Space Heating Curve

                City.node[n]['entity'] = buildmod.new_evaluation_building(City.node[n]['entity'], parameters=row[4: 15])

        print ('End of loop over buildings')
        print('###################################')

        ############################################

        # ## Generate new space heating curve

        ############################################

        # ## Rescaling Space Heating generation

        vent_factor = row[15]
        Tset_heat = row[16]
        Tset_night = row[17]
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

        City = esysmod.new_evaluation_esys(City, parameters=row[18: 43])

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

        print()
        print('Annual electricity demand : ', annual_el_dem, 'kWh/year')
        print('Annual thermal demand : ', annual_sph_dem, 'kWh/year')
        print('Annual domestic hot water : ', annual_dhw_dem, 'kWh/year')
        print()

        # return intermediate energy demand
        Inter_el [loop] = annual_el_dem
        Inter_sph [loop] = annual_sph_dem
        Inter_dhw [loop] = annual_dhw_dem
        liste_shp_curve.append(sph_curve)
        liste_dhw_curve.append(dhw_curve)
        liste_el_curve.append(el_curve)
        liste_max_sph [loop] = max_sph
        liste_max_el [loop] = max_el
        liste_max_dhw [loop] = max_dhw

        ############################################

        # ## Energy balance

        ############################################


        # Energy balance calculations
        print("Energy balance calculations")
        Calculator = EBB.calculator(City)
        dict_bes_data = Calculator.assembler()

        invalidind = EBB.invalidind
        rescale_boiler = False
        invalidind2 = EB.invalidind2
        rescale_EH = False



        # Loop over energy systems
        try:
            for i in range(len(dict_bes_data)):
                City, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)
        except invalidind:
            # Get list of building and rescale boiler
            list_of_building = City.get_list_build_entity_node_ids()
            for build in list_of_building:
                # Het max demand building
                demand_building = dimfunc.get_max_power_of_building(City.node[build]['entity'], with_dhw=True)
                # Rescale Boiler
                if City.node[build]['entity'].bes.hasBoiler == True:
                    City.node[build]['entity'].bes.boiler.qNominal = dimfunc.round_esys_size(
                        demand_building/City.node[build]['entity'].bes.boiler.eta,round_up=True)

                    rescale_boiler = True

                    print()
                    print('Rescale boiler 0')
                    print('new boiler capacity kW: ', City.node[build]['entity'].bes.boiler.qNominal / 1000)
                    print()

                if City.node[build]['entity'].bes.hasElectricalHeater == True:
                    City.node[build]['entity'].bes.electricalHeater.qNominal = dimfunc.round_esys_size(
                        demand_building/City.node[build]['entity'].bes.electricalHeater.eta, round_up=True)

                    rescale_EH = True

                    print()
                    print('Rescale EH')
                    print('new EH capacity kW: ', City.node[build]['entity'].bes.electricalHeater.qNominal / 1000)
                    print()

            # Do another time EBB
            for i in range(len(dict_bes_data)):
                City, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)

        except invalidind2:
        # Get list of building and rescale boiler
            list_of_building = City.get_list_build_entity_node_ids()
            for build in list_of_building:
                demand_building = dimfunc.get_max_power_of_building(City.node[build]['entity'], with_dhw=True)
                if City.node[build]['entity'].bes.hasBoiler == True:
                    City.node[build]['entity'].bes.boiler.qNominal = dimfunc.round_esys_size(demand_building,
                                                                                                 round_up=True)
                    rescale_boiler = True

                    print()
                    print('Rescale boiler')
                    print('new boiler capacity kW: ', City.node[build]['entity'].bes.boiler.qNominal / 1000)
                    print()

                if City.node[build]['entity'].bes.hasElectricalHeater == True:
                    City.node[build]['entity'].bes.electricalHeater.qNominal = dimfunc.round_esys_size(
                        demand_building, round_up=True)
                    rescale_EH = True

                    print()
                    print('Rescale EH')
                    print('new EH capacity kW: ', City.node[build]['entity'].bes.electricalHeater.qNominal / 1000)
                    print()

            # Do another time EBB
            for i in range(len(dict_bes_data)):
                City, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)

        #Gas and electrical demand
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
                            gas_dem += sum(City.node[n]['fuel demand']) *\
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
        interest = row[53]  # Interest rate
        print ('\n New interest: {}'.format(interest))

        price_ch_cap = row[43]
        price_ch_dem_gas = row[44]
        price_ch_dem_el = row[45]
        price_ch_op = row[46]
        price_ch_EEG_Umlage_tax_chp = row[47]
        price_ch_EEG_Umlage_tax_pv = row[48]
        price_EEX_baseload_price = row[49]
        specific_cost = row[50]
        life_factor = row[51]
        maintenance_factor = row[52]

        print("Annuity calculation")
        Market_instance = Mark.GermanMarket()

        #  Generate economic calculator object
        print("Economic object generation")
        eco_inst = eco_calc.EconomicCalculation(time=time, germanmarket=Market_instance,  interest=interest, price_ch_cap=price_ch_cap,
                                                price_ch_dem_gas=price_ch_dem_gas, price_ch_dem_el=price_ch_dem_el,
                                                price_ch_op=price_ch_op,
                                                price_ch_eeg_chp=price_ch_EEG_Umlage_tax_chp,
                                                price_ch_eeg_pv=price_ch_EEG_Umlage_tax_pv,
                                                price_ch_eex=price_EEX_baseload_price)

        # Modification lifetime and maintenance
        for key1 in eco_inst.dict_lifetimes.keys():
            tempp = eco_inst.dict_lifetimes[key1] * life_factor
            eco_inst.dict_lifetimes[key1] = tempp

        for key2 in eco_inst.dict_maintenance.keys():
            tempp = eco_inst.dict_maintenance[key2] * maintenance_factor
            eco_inst.dict_maintenance[key2] = tempp

        ## Annuity Calculation


        # Annuity
        dem_rel_annuity = eco_inst.calc_dem_rel_annuity_city(City)
        total_proc_annuity = eco_inst.calc_proc_annuity_multi_comp_city(City)
        cap_rel_ann, op_rel_ann = eco_inst.calc_cap_and_op_rel_annuity_city(City)

        total_annuity = eco_inst.calc_total_annuity(ann_capital=cap_rel_ann*specific_cost,
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
        H[loop] = GHG_Emission
        F[loop] = GHG_Emission/(annual_sph_dem+annual_dhw_dem+annual_el_dem)

    return(Y, Z, H, A, F, liste_max_dhw, liste_max_el, liste_max_sph, liste_shp_curve, liste_el_curve, liste_dhw_curve)
