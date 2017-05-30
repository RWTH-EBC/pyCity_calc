####################### TEST ##############################
'''
Pytestfile for economic_ann and calc_CO2_emission scripts
'''

import pycity_calc.simulation.energy_balance_optimization.energy_balance_building as EBB
import pycity_calc.simulation.energy_balance_optimization.Energy_balance_lhn as EBT

import shapely.geometry.point as point


import pycity.classes.Weather as Weather
import pycity.classes.demand.SpaceHeating as SpaceHeating
import pycity.classes.demand.ElectricalDemand as ElectricalDemand
import pycity.classes.demand.Apartment as Apartment

import pycity_calc.buildings.building as build_ex
import pycity_calc.cities.city as city
import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.environment as env
import pycity_calc.environments.market as mark
import pycity_calc.environments.timer as time
import pycity_calc.toolbox.dimensioning.dim_networks as dimnet

import pycity.classes.supply.BES as BES
import pycity_calc.energysystems.boiler as Boiler
import pycity_calc.energysystems.electricalHeater as EH
import pycity_calc.energysystems.heatPumpSimple as HP
import pycity_calc.energysystems.thermalEnergyStorage as TES
import pycity_calc.energysystems.chp as CHP
import pycity_calc.energysystems.battery as Battery
import pycity.classes.supply.PV as PV

##########
import pickle
import pycity_calc.economic.annuity_calculation as eco_calc
import pycity_calc.economic.economic_ann as economic_ann

# CO2 emission
import pycity_calc.economic.calc_CO2_emission as CO2_em
import pycity_calc.environments.co2emissions as CO2_emissions


class test_simulation_economic_ann():

    # test_single_house_electricity_chp_pv_batt(self, plot_res)
    def test_single_house_electricity_chp_pv_batt(self):
        list_types = ['CHP']
        year = 2010
        timestep = 3600
        livingArea = [120]
        b_Space_heat_demand = True
        specificDemandSH = [100]
        annualDemandel = [3000]
        profileType = ['H0']
        methodel = [1]
        b_domestic_hot_water = False
        b_el_demand = True
        roof_usabl_pv_area = [30]
        boiler_q_nominal = [3000]
        boiler_eta = [0.9]
        boiler_lal = [0.5]
        tes_capacity = [1000]
        tes_k_loss = [0]
        tes_t_max = [95]
        eh_q_nominal = [3000]
        hp_q_nominal = [3000]
        hp_lal = [0.5]
        chp_p_nominal = [1000]
        chp_q_nominal = [3000]
        chp_eta_total = [0.9]
        chp_lal = [0.5]
        list_PV = [10]
        bat_capacity = [55] #4kWh
        list_etaCharge = [1]
        list_etaDischarge = [1]

        #  Create extended environment of pycity_calc


        location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop
        altitude = 55  # Altitude of Bottrop

        #  Generate timer object
        timer = time.TimerExtended(timestep=timestep, year=year)

        #  Generate weather object
        weather = Weather.Weather(timer, useTRY=True, location=location,
                                  altitude=altitude)

        #  Generate market object
        market = mark.Market()

        #  Generate co2 emissions object
        co2em = co2.Emissions(year=year)

        #  Generate environment
        environment = env.EnvironmentExtended(timer, weather, prices=market,
                                              location=location, co2em=co2em)

        #  Generate city object
        city_object = city.City(environment=environment)

        #  Iterate 3 times to generate 3 building objects (with boiler)
        node = 1001  # initialization
        LHN_nodes = []  # initialization
        for i in range(len(list_types)):

            types = list_types[i]

            # TODO: Not sure if the node method will run stable under other conditions!!
            if types == 'BTESLHN' or types == 'BLHN' or types == "HPLHN" or types == 'CHPLHN':
                LHN_nodes.append(node)

            # Create apartment
            apartment = Apartment.Apartment(environment)

            #  Create demands
            if b_Space_heat_demand == True:
                heat_demand = SpaceHeating.SpaceHeating(environment,
                                                        method=1,
                                                        profile_type='HEF',
                                                        livingArea=livingArea[i],
                                                        specificDemand=specificDemandSH[i])
                apartment.addEntity(heat_demand)

            if b_domestic_hot_water == True:
                assert b_domestic_hot_water == False, ('domestic hot water not implemented yet')
                #
                # apartment.addEntity(heat_demand)

            if b_el_demand == True:
                el_demand = ElectricalDemand.ElectricalDemand(environment, method=methodel[i],
                                                              annualDemand=annualDemandel[i],
                                                              profileType=profileType[i])
                apartment.addEntity(el_demand)

            extended_building = build_ex.BuildingExtended(environment,
                                                          build_year=1962,
                                                          mod_year=2003,
                                                          build_type=0,
                                                          roof_usabl_pv_area=roof_usabl_pv_area[i],
                                                          net_floor_area=livingArea[i],
                                                          height_of_floors=3,
                                                          nb_of_floors=2,
                                                          neighbour_buildings=0,
                                                          residential_layout=0,
                                                          attic=0, cellar=1,
                                                          construction_type='heavy',
                                                          dormer=0)

            #  Add apartment to extended building
            extended_building.addEntity(entity=apartment)

            position = point.Point(i * 10, 0)

            ######
            # create bes
            bes = BES.BES(environment)

            # boiler
            if types == 'B' or types == 'BLHN' or types == 'BTES' or types == 'BTESLHN' or types == 'CHP' or types == 'CHPLHN':
                # TODO: check if all types are covered
                # Create boiler
                boiler = Boiler.BoilerExtended(environment, q_nominal=boiler_q_nominal[i], eta=boiler_eta[i], t_max=90,
                                               lower_activation_limit=boiler_lal[i])
                bes.addDevice(boiler)

            # tes
            if types == 'BTES' or types == 'BTESLHN' or types == 'HP' or types == "HPLHN" or types == 'CHP' or types == 'CHPLHN':
                # Create thermal storage
                tes = TES.thermalEnergyStorageExtended(environment, t_init=20, capacity=tes_capacity[i],
                                                       t_max=tes_t_max[i], t_surroundings=20,
                                                       k_loss=tes_k_loss[i], h_d_ratio=3.5, use_outside_temp=False)
                bes.addDevice(tes)

            # heatpump
            if types == 'HP' or types == "HPLHN":
                # Create electrical heater
                eh = EH.ElectricalHeaterExtended(environment, q_nominal=eh_q_nominal[i], eta=1,
                                                 t_max=85, lower_activation_limit=0)
                bes.addDevice(eh)

                # Create HP
                heater = HP.heatPumpSimple(environment, q_nominal=hp_q_nominal[i], t_max=55.0,
                                           lower_activation_limit=hp_lal[i], hp_type='aw', t_sink=45.0)
                bes.addDevice(heater)

            # chp
            if types == 'CHP' or types == 'CHPLHN':
                # Create chp
                heater = CHP.ChpExtended(environment, p_nominal=chp_p_nominal[i], q_nominal=chp_q_nominal[i],
                                         eta_total=chp_eta_total[i], t_max=90,
                                         lower_activation_limit=chp_lal[i])
                bes.addDevice(heater)

            extended_building.addEntity(bes)

            city_object.add_extended_building(extended_building=extended_building,
                                              position=position)

            if list_PV[i] > 0:
                # Create PV
                if city_object.node[node]['entity'].roof_usabl_pv_area < list_PV[i]:
                    # Check if there is enough roof area for PV, if not set PV area to maximum roof area
                    list_PV[i] = city_object.node[node]['entity'].roof_usabl_pv_area
                pv_simple = PV.PV(environment, list_PV[i], eta=0.9, beta=0)
                bes.addDevice(pv_simple)
                # TODO: eta and beta must be set properly
            if bat_capacity[i] > 0:
                # Create Battery
                capacity = bat_capacity[i]  # 4 * 3600 * 1000  # 4 kWh = 4 * 3600*1000 J
                socInit = 0.5
                selfDischarge = 0
                etaCharge = list_etaCharge[i]  # 0.96
                etaDischarge = list_etaDischarge[i]  # 0.95
                battery = Battery.BatteryExtended(environment, socInit, capacity,
                                                  selfDischarge, etaCharge, etaDischarge)
                bes.addDevice(battery)

            node = node + 1

            # TODO: Only Bat when PV??

        # Add a local heating network to the city
        # LHN_nodes= city_object.get_list_build_entity_node_ids() # List of buildingnodes
        if len(LHN_nodes) >= 2:
            print('Buildnode with LHN:', LHN_nodes)
            dimnet.add_lhn_to_city(city_object, LHN_nodes, temp_vl=90,
                                   temp_rl=50, c_p=4186, rho=1000,
                                   use_street_network=False, network_type='heating',
                                   plot_stepwise=False)

        print('\nGet list of node ids with building objects:')
        print(city_object.get_list_build_entity_node_ids())


        city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve = [6000] * 8760

        city_object.node[1001]['entity'].apartments[0].power_el.loadcurve = [1000] * 8760
        city_object.environment.weather.tAmbient = [10] * 8760  # for constant HP electrical demand


        city_object.environment.weather.qDiffuse[0:8760] = [100] * 8760
        city_object.environment.weather.qDirect[0:8760] = [100] * 8760


        eco_calc_instance = eco_calc.EconomicCalculation()
        Calculator = EBB.calculator(city_object)
        dict_bes_data = Calculator.assembler()
        print('Dict city data', dict_bes_data)
        for i in range(len(dict_bes_data)):
            city_object, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)

        dem_rel_annuity = economic_ann.calc_dem_rel_annuity_city(city_object, eco_calc_instance)
        total_proc_annuity = economic_ann.calc_proc_annuity_multi_comp_city(city_object, eco_calc_instance)

        cap_rel_ann, op_rel_ann = economic_ann.calc_cap_and_op_rel_annuity_city(city_object, eco_calc_instance)

        # TOTAL ANNUITY
        total_annuity = eco_calc_instance.calc_total_annuity(ann_capital=cap_rel_ann,
                                                      ann_demand=dem_rel_annuity,
                                                      ann_op=op_rel_ann,
                                                      ann_proc=total_proc_annuity)
        # CO2 emission
        co2_instance = CO2_emissions.Emissions(year=2010)
        CO2_em_tot = CO2_em.CO2_emission_calc(city_object, co2_instance)



        print()
        print()
        print('dem_rel_annuity:', round(dem_rel_annuity, 2))
        print()
        print('proc_rel_annuity:', round(total_proc_annuity, 2))
        print()
        print('cap_rel_ann:', round(cap_rel_ann, 2))
        print()
        print('op_rel_ann:', round(op_rel_ann, 2))
        print()
        print('total_annuity:', round(total_annuity, 2))

        print()
        print('CO2_emissions:', round(CO2_em_tot, 2))


    # test_single_house_electricity_hp_pv_batt(plot_res=False):
    def test_single_house_electricity_hp_pv_batt(self):

        """
        Test case for single building with heatpump and PV and battery


        Run example to create city object of pycity with 3 buildings
        Variables:
        list_types: 'list of types', list defines which enerysystems will be used, len(list_types)=numHouses
            types: CHP (CHP+B+TES);CHPLHN (CHP+B+TES+LHN); HP(HP+EH+TES);HPLHN(HP+EH+TES+LHN);BTES (B+TES),BTESLHN (B+TES+LHN), B(B),BLHN(B+LHN)
        timestep: 'int', Timestep in seconds
        year: 'int', the year
        livingArea: 'list', living area of each house, len(livingArea)=numHouses
        b_Space_heat_demand: 'bool', set if spaceheating demand or not
        specificDemandSH:  'list', specific demand of each house, len(specificDemandSH)=numHouses
        annualDemandel: 'list', anual electric demand of each house, len(annualDemandel)=numHouses
        profileType: 'list of profileTypes', required for SLP, see pyCity/pycity/classes/demand/ElectricalDemand.py, len(profileType)=numHouses
        methodel: 'list of method's', method to determine the electrical profile for each building, see pyCity/pycity/classes/demand/ElectricalDemand.py, len(methodel)=numHouses
        b_domestic_hot_water: 'bool', set if domestic hot water demand or not
        b_el_demand: 'bool', set if electric demand or not
        roof_usabl_pv_area: 'list', list of PV roof areas for each building, len(roof_usabl_pv_area)=numHouses
        boiler_q_nominal: 'list', in Watt, len(boiler_q_nominal)=numHouses
        boiler_eta: 'list', len(boiler_eta)=numHouses
        boiler_lal: 'list', len(boiler_lal)=numHouses
        tes_capacity: 'list', in kg len(tes_capacity)=numHouses
        tes_k_loss: 'list', in W, len(tes_k_loss)=numHouses
        tes_t_max: 'list', in Celsius, len(tes_t_max)=numHouses
        eh_q_nominal: 'list', in W, len(eh_q_nominal)=numHouses
        hp_q_nominal: 'list', in W, len(hp_q_nominal)=numHouses
        hp_lal: 'list', len(hp_lal)=numHouses
        chp_p_nominal: 'list', len(chp_p_nominal)=numHouses
        chp_q_nominal: 'list', len(chp_q_nominal)=numHouses
        chp_eta_total: 'list', len(chp_eta_total)=numHouses
        chp_lal: 'list', len(chp_lal)=numHouses

        #######IMPORTANT##########
        all lists must be of same length. Example:
        list_types=['BTES','CHP','HP'] -> 3 buildings
        chp_q_nominal=[0,1000,0]
        """

        # TODO: check the whole script, in particular all if cases, if bes is set correctly

        list_types = ['HP']
        year = 2010
        timestep = 3600
        livingArea = [120]
        b_Space_heat_demand = True
        specificDemandSH = [100]
        annualDemandel = [3000]
        profileType = ['H0']
        methodel = [1]
        b_domestic_hot_water = False
        b_el_demand = True
        roof_usabl_pv_area = [30]
        boiler_q_nominal = [3000]
        boiler_eta = [0.9]
        boiler_lal = [0.5]
        tes_capacity = [1000]
        tes_k_loss = [0]
        tes_t_max = [95]
        eh_q_nominal = [3000]
        hp_q_nominal = [3000]
        hp_lal = [0.5]
        chp_p_nominal = [1000]
        chp_q_nominal = [3000]
        chp_eta_total = [0.9]
        chp_lal = [0.5]
        list_PV = [10]
        bat_capacity = [55] #4kWh
        list_etaCharge = [1]
        list_etaDischarge = [1]

        #  Create extended environment of pycity_calc


        location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop
        altitude = 55  # Altitude of Bottrop

        #  Generate timer object
        timer = time.TimerExtended(timestep=timestep, year=year)

        #  Generate weather object
        weather = Weather.Weather(timer, useTRY=True, location=location,
                                  altitude=altitude)

        #  Generate market object
        market = mark.Market()

        #  Generate co2 emissions object
        co2em = co2.Emissions(year=year)

        #  Generate environment
        environment = env.EnvironmentExtended(timer, weather, prices=market,
                                              location=location, co2em=co2em)

        #  Generate city object
        city_object = city.City(environment=environment)

        #  Iterate 3 times to generate 3 building objects (with boiler)
        node = 1001  # initialization
        LHN_nodes = []  # initialization
        for i in range(len(list_types)):

            types = list_types[i]

            # TODO: Not sure if the node method will run stable under other conditions!!
            if types == 'BTESLHN' or types == 'BLHN' or types == "HPLHN" or types == 'CHPLHN':
                LHN_nodes.append(node)

            # Create apartment
            apartment = Apartment.Apartment(environment)

            #  Create demands
            if b_Space_heat_demand == True:
                heat_demand = SpaceHeating.SpaceHeating(environment,
                                                        method=1,
                                                        profile_type='HEF',
                                                        livingArea=livingArea[i],
                                                        specificDemand=specificDemandSH[i])
                apartment.addEntity(heat_demand)

            if b_domestic_hot_water == True:
                assert b_domestic_hot_water == False, ('domestic hot water not implemented yet')
                #
                # apartment.addEntity(heat_demand)

            if b_el_demand == True:
                el_demand = ElectricalDemand.ElectricalDemand(environment, method=methodel[i],
                                                              annualDemand=annualDemandel[i],
                                                              profileType=profileType[i])
                apartment.addEntity(el_demand)

            extended_building = build_ex.BuildingExtended(environment,
                                                          build_year=1962,
                                                          mod_year=2003,
                                                          build_type=0,
                                                          roof_usabl_pv_area=roof_usabl_pv_area[i],
                                                          net_floor_area=livingArea[i],
                                                          height_of_floors=3,
                                                          nb_of_floors=2,
                                                          neighbour_buildings=0,
                                                          residential_layout=0,
                                                          attic=0, cellar=1,
                                                          construction_type='heavy',
                                                          dormer=0)

            #  Add apartment to extended building
            extended_building.addEntity(entity=apartment)

            position = point.Point(i * 10, 0)

            ######
            # create bes
            bes = BES.BES(environment)

            # boiler
            if types == 'B' or types == 'BLHN' or types == 'BTES' or types == 'BTESLHN' or types == 'CHP' or types == 'CHPLHN':
                # TODO: check if all types are covered
                # Create boiler
                boiler = Boiler.BoilerExtended(environment, q_nominal=boiler_q_nominal[i], eta=boiler_eta[i], t_max=90,
                                               lower_activation_limit=boiler_lal[i])
                bes.addDevice(boiler)

            # tes
            if types == 'BTES' or types == 'BTESLHN' or types == 'HP' or types == "HPLHN" or types == 'CHP' or types == 'CHPLHN':
                # Create thermal storage
                tes = TES.thermalEnergyStorageExtended(environment, t_init=20, capacity=tes_capacity[i],
                                                       t_max=tes_t_max[i], t_surroundings=20,
                                                       k_loss=tes_k_loss[i], h_d_ratio=3.5, use_outside_temp=False)
                bes.addDevice(tes)

            # heatpump
            if types == 'HP' or types == "HPLHN":
                # Create electrical heater
                eh = EH.ElectricalHeaterExtended(environment, q_nominal=eh_q_nominal[i], eta=1,
                                                 t_max=85, lower_activation_limit=0)
                bes.addDevice(eh)

                # Create HP
                heater = HP.heatPumpSimple(environment, q_nominal=hp_q_nominal[i], t_max=55.0,
                                           lower_activation_limit=hp_lal[i], hp_type='aw', t_sink=45.0)
                bes.addDevice(heater)

            # chp
            if types == 'CHP' or types == 'CHPLHN':
                # Create chp
                heater = CHP.ChpExtended(environment, p_nominal=chp_p_nominal[i], q_nominal=chp_q_nominal[i],
                                         eta_total=chp_eta_total[i], t_max=90,
                                         lower_activation_limit=chp_lal[i])
                bes.addDevice(heater)

            extended_building.addEntity(bes)

            city_object.add_extended_building(extended_building=extended_building,
                                              position=position)

            if list_PV[i] > 0:
                # Create PV
                if city_object.node[node]['entity'].roof_usabl_pv_area < list_PV[i]:
                    # Check if there is enough roof area for PV, if not set PV area to maximum roof area
                    list_PV[i] = city_object.node[node]['entity'].roof_usabl_pv_area
                pv_simple = PV.PV(environment, list_PV[i], eta=0.9, beta=0)
                bes.addDevice(pv_simple)
                # TODO: eta and beta must be set properly
            if bat_capacity[i] > 0:
                # Create Battery
                capacity = bat_capacity[i]  # 4 * 3600 * 1000  # 4 kWh = 4 * 3600*1000 J
                socInit = 0.5
                selfDischarge = 0
                etaCharge = list_etaCharge[i]  # 0.96
                etaDischarge = list_etaDischarge[i]  # 0.95
                battery = Battery.BatteryExtended(environment, socInit, capacity,
                                                  selfDischarge, etaCharge, etaDischarge)
                bes.addDevice(battery)

            node = node + 1

            # TODO: Only Bat when PV??

        # Add a local heating network to the city
        # LHN_nodes= city_object.get_list_build_entity_node_ids() # List of buildingnodes
        if len(LHN_nodes) >= 2:
            print('Buildnode with LHN:', LHN_nodes)
            dimnet.add_lhn_to_city(city_object, LHN_nodes, temp_vl=90,
                                   temp_rl=50, c_p=4186, rho=1000,
                                   use_street_network=False, network_type='heating',
                                   plot_stepwise=False)

        print('\nGet list of node ids with building objects:')
        print(city_object.get_list_build_entity_node_ids())

        # check 1
        city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve = [6000] * 8760
        city_object.node[1001]['entity'].apartments[0].power_el.loadcurve = [1000] * 8760
        city_object.environment.weather.tAmbient = [10] * 8760  # for constant HP electrical demand

        city_object.environment.weather.qDiffuse[0:8760] = [600] * 8760
        city_object.environment.weather.qDirect[0:8760] = [600] * 8760


        eco_calc_instance = eco_calc.EconomicCalculation()
        Calculator = EBB.calculator(city_object)
        dict_bes_data = Calculator.assembler()
        print('Dict city data', dict_bes_data)
        for i in range(len(dict_bes_data)):
            city_object, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)

        dem_rel_annuity = economic_ann.calc_dem_rel_annuity_city(city_object, eco_calc_instance)
        total_proc_annuity = economic_ann.calc_proc_annuity_multi_comp_city(city_object, eco_calc_instance)

        cap_rel_ann, op_rel_ann = economic_ann.calc_cap_and_op_rel_annuity_city(city_object, eco_calc_instance)

        # TOTAL ANNUITY
        total_annuity = eco_calc_instance.calc_total_annuity(ann_capital=cap_rel_ann,
                                                      ann_demand=dem_rel_annuity,
                                                      ann_op=op_rel_ann,
                                                      ann_proc=total_proc_annuity)



        # CO2 emission
        co2_instance = CO2_emissions.Emissions(year=2010)
        CO2_em_tot = CO2_em.CO2_emission_calc(city_object, co2_instance)



        print()
        print()
        print('dem_rel_annuity:', round(dem_rel_annuity, 2))
        print()
        print('proc_rel_annuity:', round(total_proc_annuity, 2))
        print()
        print('cap_rel_ann:', round(cap_rel_ann, 2))
        print()
        print('op_rel_ann:', round(op_rel_ann, 2))
        print()
        print('total_annuity:', round(total_annuity, 2))

        print()
        print('CO2_emissions:', round(CO2_em_tot, 2))

    # test_single_house_electricity_hp
    def test_single_house_electricity_hp(self):

        """
        Test case for single building with heatpump, testing electrip hp demand


        Run example to create city object of pycity with 3 buildings
        Variables:
        list_types: 'list of types', list defines which enerysystems will be used, len(list_types)=numHouses
            types: CHP (CHP+B+TES);CHPLHN (CHP+B+TES+LHN); HP(HP+EH+TES);HPLHN(HP+EH+TES+LHN);BTES (B+TES),BTESLHN (B+TES+LHN), B(B),BLHN(B+LHN)
        timestep: 'int', Timestep in seconds
        year: 'int', the year
        livingArea: 'list', living area of each house, len(livingArea)=numHouses
        b_Space_heat_demand: 'bool', set if spaceheating demand or not
        specificDemandSH:  'list', specific demand of each house, len(specificDemandSH)=numHouses
        annualDemandel: 'list', anual electric demand of each house, len(annualDemandel)=numHouses
        profileType: 'list of profileTypes', required for SLP, see pyCity/pycity/classes/demand/ElectricalDemand.py, len(profileType)=numHouses
        methodel: 'list of method's', method to determine the electrical profile for each building, see pyCity/pycity/classes/demand/ElectricalDemand.py, len(methodel)=numHouses
        b_domestic_hot_water: 'bool', set if domestic hot water demand or not
        b_el_demand: 'bool', set if electric demand or not
        roof_usabl_pv_area: 'list', list of PV roof areas for each building, len(roof_usabl_pv_area)=numHouses
        boiler_q_nominal: 'list', in Watt, len(boiler_q_nominal)=numHouses
        boiler_eta: 'list', len(boiler_eta)=numHouses
        boiler_lal: 'list', len(boiler_lal)=numHouses
        tes_capacity: 'list', in kg len(tes_capacity)=numHouses
        tes_k_loss: 'list', in W, len(tes_k_loss)=numHouses
        tes_t_max: 'list', in Celsius, len(tes_t_max)=numHouses
        eh_q_nominal: 'list', in W, len(eh_q_nominal)=numHouses
        hp_q_nominal: 'list', in W, len(hp_q_nominal)=numHouses
        hp_lal: 'list', len(hp_lal)=numHouses
        chp_p_nominal: 'list', len(chp_p_nominal)=numHouses
        chp_q_nominal: 'list', len(chp_q_nominal)=numHouses
        chp_eta_total: 'list', len(chp_eta_total)=numHouses
        chp_lal: 'list', len(chp_lal)=numHouses

        #######IMPORTANT##########
        all lists must be of same length. Example:
        list_types=['BTES','CHP','HP'] -> 3 buildings
        chp_q_nominal=[0,1000,0]
        """



        # TODO: check the whole script, in particular all if cases, if bes is set correctly

        list_types=['HP']
        year = 2010
        timestep = 3600
        livingArea=[120]
        b_Space_heat_demand=True
        specificDemandSH=[100]
        annualDemandel=[3000]
        profileType=['H0']
        methodel=[1]
        b_domestic_hot_water=False
        b_el_demand=True
        roof_usabl_pv_area=[30]
        boiler_q_nominal=[3000]
        boiler_eta=[0.9]
        boiler_lal=[0.5]
        tes_capacity=[1000]
        tes_k_loss=[0]
        tes_t_max=[95]
        eh_q_nominal=[3000]
        hp_q_nominal=[3000]
        hp_lal=[0.5]
        chp_p_nominal=[2000]
        chp_q_nominal=[6000]
        chp_eta_total=[0.9]
        chp_lal=[0.5]
        list_PV=[0]
        bat_capacity=[0]
        list_etaCharge=[0.96]
        list_etaDischarge=[0.95]


        #  Create extended environment of pycity_calc


        location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop
        altitude = 55  # Altitude of Bottrop

        #  Generate timer object
        timer = time.TimerExtended(timestep=timestep, year=year)

        #  Generate weather object
        weather = Weather.Weather(timer, useTRY=True, location=location,
                                  altitude=altitude)

        #  Generate market object
        market = mark.Market()

        #  Generate co2 emissions object
        co2em = co2.Emissions(year=year)

        #  Generate environment
        environment = env.EnvironmentExtended(timer, weather, prices=market,
                                              location=location, co2em=co2em)

        #  Generate city object
        city_object = city.City(environment=environment)

        #  Iterate 3 times to generate 3 building objects (with boiler)
        node=1001 # initialization
        LHN_nodes=[] # initialization
        for i in range(len(list_types)):

            types=list_types[i]


            # TODO: Not sure if the node method will run stable under other conditions!!
            if types=='BTESLHN' or types=='BLHN' or types=="HPLHN" or types=='CHPLHN':
                LHN_nodes.append(node)



            #  Create apartment
            apartment = Apartment.Apartment(environment)

            #  Create demands
            if b_Space_heat_demand == True:
                heat_demand = SpaceHeating.SpaceHeating(environment,
                                                        method=1,
                                                        profile_type='HEF',
                                                        livingArea=livingArea[i],
                                                        specificDemand=specificDemandSH[i])
                apartment.addEntity(heat_demand)

            if b_domestic_hot_water == True:
                assert b_domestic_hot_water == False, ('domestic hot water not implemented yet')
                #
                #apartment.addEntity(heat_demand)

            if b_el_demand == True:
                el_demand = ElectricalDemand.ElectricalDemand(environment, method=methodel[i],
                                                              annualDemand=annualDemandel[i],
                                                              profileType=profileType[i])
                apartment.addEntity(el_demand)

            extended_building = build_ex.BuildingExtended(environment,
                                                          build_year=1962,
                                                          mod_year=2003,
                                                          build_type=0,
                                                          roof_usabl_pv_area=roof_usabl_pv_area[i],
                                                          net_floor_area=livingArea[i],
                                                          height_of_floors=3,
                                                          nb_of_floors=2,
                                                          neighbour_buildings=0,
                                                          residential_layout=0,
                                                          attic=0, cellar=1,
                                                          construction_type='heavy',
                                                          dormer=0)

            #  Add apartment to extended building
            extended_building.addEntity(entity=apartment)

            position = point.Point(i * 10, 0)


            ######
            # create bes
            bes = BES.BES(environment)

            # boiler
            if types == 'B' or types == 'BLHN' or types == 'BTES' or types == 'BTESLHN' or types == 'CHP' or types == 'CHPLHN':
                #TODO: check if all types are covered
                # Create boiler
                boiler = Boiler.BoilerExtended(environment, q_nominal=boiler_q_nominal[i], eta=boiler_eta[i], t_max=90,
                                               lower_activation_limit=boiler_lal[i])
                bes.addDevice(boiler)

            # tes
            if types=='BTES' or types == 'BTESLHN' or types == 'HP' or types == "HPLHN" or types == 'CHP' or types == 'CHPLHN':
                # Create thermal storage
                tes = TES.thermalEnergyStorageExtended(environment, t_init=20, capacity=tes_capacity[i], t_max=tes_t_max[i], t_surroundings=20,
                                                   k_loss=tes_k_loss[i], h_d_ratio=3.5, use_outside_temp=False)
                bes.addDevice(tes)

            # heatpump
            if types == 'HP' or types == "HPLHN":
                # Create electrical heater
                eh = EH.ElectricalHeaterExtended(environment, q_nominal=eh_q_nominal[i], eta=1,
                                                       t_max=85, lower_activation_limit=0)
                bes.addDevice(eh)

                # Create HP
                heater = HP.heatPumpSimple(environment, q_nominal=hp_q_nominal[i], t_max=55.0,
                         lower_activation_limit=hp_lal[i], hp_type='aw', t_sink=45.0)
                bes.addDevice(heater)

            # chp
            if types == 'CHP' or types == 'CHPLHN':
                # Create chp
                heater = CHP.ChpExtended(environment, p_nominal=chp_p_nominal[i], q_nominal=chp_q_nominal[i], eta_total=chp_eta_total[i], t_max=90,
                                     lower_activation_limit=chp_lal[i])
                bes.addDevice(heater)

            extended_building.addEntity(bes)

            city_object.add_extended_building(extended_building=extended_building,
                                              position=position)

            if list_PV[i] > 0:
                # Create PV
                if city_object.node[node]['entity'].roof_usabl_pv_area < list_PV[i]:
                # Check if there is enough roof area for PV, if not set PV area to maximum roof area
                    list_PV[i] = city_object.node[node]['entity'].roof_usabl_pv_area
                pv_simple = PV.PV(environment, list_PV[i], eta=0.9, beta=0)
                bes.addDevice(pv_simple)
                # TODO: eta and beta must be set properly
            if bat_capacity[i] > 0:
                # Create Battery
                capacity = bat_capacity[i]   #4 * 3600 * 1000  # 4 kWh = 4 * 3600*1000 J
                socInit = 0.5
                selfDischarge = 0.02
                etaCharge = list_etaCharge[i] #0.96
                etaDischarge = list_etaDischarge[i] # 0.95
                battery = Battery.BatteryExtended(environment, socInit, capacity,
                                      selfDischarge, etaCharge, etaDischarge)
                bes.addDevice(battery)

            node=node+1

            # TODO: Only Bat when PV??

        # Add a local heating network to the city
        #LHN_nodes= city_object.get_list_build_entity_node_ids() # List of buildingnodes
        if len(LHN_nodes)>=2:
            print('Buildnode with LHN:',LHN_nodes)
            dimnet.add_lhn_to_city(city_object, LHN_nodes, temp_vl=90,
                            temp_rl=50, c_p=4186, rho=1000,
                            use_street_network=False, network_type='heating',
                            plot_stepwise=False)

        print('\nGet list of node ids with building objects:')
        print(city_object.get_list_build_entity_node_ids())

        # check 1
        city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve=[6000]*8760
        city_object.node[1001]['entity'].apartments[0].power_el.loadcurve=[1000]*8760
        city_object.environment.weather.tAmbient=[10]*8760 # for constant HP electrical demand


        eco_calc_instance = eco_calc.EconomicCalculation()
        Calculator = EBB.calculator(city_object)
        dict_bes_data = Calculator.assembler()
        print('Dict city data', dict_bes_data)
        for i in range(len(dict_bes_data)):
            city_object, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)

        dem_rel_annuity = economic_ann.calc_dem_rel_annuity_city(city_object, eco_calc_instance)
        total_proc_annuity = economic_ann.calc_proc_annuity_multi_comp_city(city_object, eco_calc_instance)

        cap_rel_ann, op_rel_ann = economic_ann.calc_cap_and_op_rel_annuity_city(city_object, eco_calc_instance)

        # TOTAL ANNUITY
        total_annuity = eco_calc_instance.calc_total_annuity(ann_capital=cap_rel_ann,
                                                      ann_demand=dem_rel_annuity,
                                                      ann_op=op_rel_ann,
                                                      ann_proc=total_proc_annuity)



        # CO2 emission
        co2_instance = CO2_emissions.Emissions(year=2010)
        CO2_em_tot = CO2_em.CO2_emission_calc(city_object, co2_instance)



        print()
        print()
        print('dem_rel_annuity:', round(dem_rel_annuity, 2))
        print()
        print('proc_rel_annuity:', round(total_proc_annuity, 2))
        print()
        print('cap_rel_ann:', round(cap_rel_ann, 2))
        print()
        print('op_rel_ann:', round(op_rel_ann, 2))
        print()
        print('total_annuity:', round(total_annuity, 2))

        print()
        print('CO2_emissions:', round(CO2_em_tot, 2))


    # test_single_house_electricity_chp
    def test_single_house_electricity_chp(self):

        """
        Test case for single building with CHP, testing electrip chp demand


        Run example to create city object of pycity with 3 buildings
        Variables:
        list_types: 'list of types', list defines which enerysystems will be used, len(list_types)=numHouses
            types: CHP (CHP+B+TES);CHPLHN (CHP+B+TES+LHN); HP(HP+EH+TES);HPLHN(HP+EH+TES+LHN);BTES (B+TES),BTESLHN (B+TES+LHN), B(B),BLHN(B+LHN)
        timestep: 'int', Timestep in seconds
        year: 'int', the year
        livingArea: 'list', living area of each house, len(livingArea)=numHouses
        b_Space_heat_demand: 'bool', set if spaceheating demand or not
        specificDemandSH:  'list', specific demand of each house, len(specificDemandSH)=numHouses
        annualDemandel: 'list', anual electric demand of each house, len(annualDemandel)=numHouses
        profileType: 'list of profileTypes', required for SLP, see pyCity/pycity/classes/demand/ElectricalDemand.py, len(profileType)=numHouses
        methodel: 'list of method's', method to determine the electrical profile for each building, see pyCity/pycity/classes/demand/ElectricalDemand.py, len(methodel)=numHouses
        b_domestic_hot_water: 'bool', set if domestic hot water demand or not
        b_el_demand: 'bool', set if electric demand or not
        roof_usabl_pv_area: 'list', list of PV roof areas for each building, len(roof_usabl_pv_area)=numHouses
        boiler_q_nominal: 'list', in Watt, len(boiler_q_nominal)=numHouses
        boiler_eta: 'list', len(boiler_eta)=numHouses
        boiler_lal: 'list', len(boiler_lal)=numHouses
        tes_capacity: 'list', in kg len(tes_capacity)=numHouses
        tes_k_loss: 'list', in W, len(tes_k_loss)=numHouses
        tes_t_max: 'list', in Celsius, len(tes_t_max)=numHouses
        eh_q_nominal: 'list', in W, len(eh_q_nominal)=numHouses
        hp_q_nominal: 'list', in W, len(hp_q_nominal)=numHouses
        hp_lal: 'list', len(hp_lal)=numHouses
        chp_p_nominal: 'list', len(chp_p_nominal)=numHouses
        chp_q_nominal: 'list', len(chp_q_nominal)=numHouses
        chp_eta_total: 'list', len(chp_eta_total)=numHouses
        chp_lal: 'list', len(chp_lal)=numHouses

        #######IMPORTANT##########
        all lists must be of same length. Example:
        list_types=['BTES','CHP','HP'] -> 3 buildings
        chp_q_nominal=[0,1000,0]
        """



        # TODO: check the whole script, in particular all if cases, if bes is set correctly

        list_types=['CHP']
        year = 2010
        timestep = 3600
        livingArea=[120]
        b_Space_heat_demand=True
        specificDemandSH=[100]
        annualDemandel=[3000]
        profileType=['H0']
        methodel=[1]
        b_domestic_hot_water=False
        b_el_demand=True
        roof_usabl_pv_area=[30]
        boiler_q_nominal=[3000]
        boiler_eta=[0.9]
        boiler_lal=[0.5]
        tes_capacity=[1000]
        tes_k_loss=[0]
        tes_t_max=[95]
        eh_q_nominal=[3000]
        hp_q_nominal=[3000]
        hp_lal=[0.5]
        chp_p_nominal=[2000]
        chp_q_nominal=[6000]
        chp_eta_total=[0.9]
        chp_lal=[0.5]
        list_PV=[0]
        bat_capacity=[0]
        list_etaCharge=[0.96]
        list_etaDischarge=[0.95]


        #  Create extended environment of pycity_calc


        location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop
        altitude = 55  # Altitude of Bottrop

        #  Generate timer object
        timer = time.TimerExtended(timestep=timestep, year=year)

        #  Generate weather object
        weather = Weather.Weather(timer, useTRY=True, location=location,
                                  altitude=altitude)

        #  Generate market object
        market = mark.Market()

        #  Generate co2 emissions object
        co2em = co2.Emissions(year=year)

        #  Generate environment
        environment = env.EnvironmentExtended(timer, weather, prices=market,
                                              location=location, co2em=co2em)

        #  Generate city object
        city_object = city.City(environment=environment)

        #  Iterate 3 times to generate 3 building objects (with boiler)
        node=1001 # initialization
        LHN_nodes=[] # initialization
        for i in range(len(list_types)):

            types=list_types[i]


            # TODO: Not sure if the node method will run stable under other conditions!!
            if types=='BTESLHN' or types=='BLHN' or types=="HPLHN" or types=='CHPLHN':
                LHN_nodes.append(node)



            #  Create apartment
            apartment = Apartment.Apartment(environment)

            #  Create demands
            if b_Space_heat_demand == True:
                heat_demand = SpaceHeating.SpaceHeating(environment,
                                                        method=1,
                                                        profile_type='HEF',
                                                        livingArea=livingArea[i],
                                                        specificDemand=specificDemandSH[i])
                apartment.addEntity(heat_demand)

            if b_domestic_hot_water == True:
                assert b_domestic_hot_water == False, ('domestic hot water not implemented yet')
                #
                #apartment.addEntity(heat_demand)

            if b_el_demand == True:
                el_demand = ElectricalDemand.ElectricalDemand(environment, method=methodel[i],
                                                              annualDemand=annualDemandel[i],
                                                              profileType=profileType[i])
                apartment.addEntity(el_demand)

            extended_building = build_ex.BuildingExtended(environment,
                                                          build_year=1962,
                                                          mod_year=2003,
                                                          build_type=0,
                                                          roof_usabl_pv_area=roof_usabl_pv_area[i],
                                                          net_floor_area=livingArea[i],
                                                          height_of_floors=3,
                                                          nb_of_floors=2,
                                                          neighbour_buildings=0,
                                                          residential_layout=0,
                                                          attic=0, cellar=1,
                                                          construction_type='heavy',
                                                          dormer=0)

            #  Add apartment to extended building
            extended_building.addEntity(entity=apartment)

            position = point.Point(i * 10, 0)


            ######
            # create bes
            bes = BES.BES(environment)

            # boiler
            if types == 'B' or types == 'BLHN' or types == 'BTES' or types == 'BTESLHN' or types == 'CHP' or types == 'CHPLHN':
                #TODO: check if all types are covered
                # Create boiler
                boiler = Boiler.BoilerExtended(environment, q_nominal=boiler_q_nominal[i], eta=boiler_eta[i], t_max=90,
                                               lower_activation_limit=boiler_lal[i])
                bes.addDevice(boiler)

            # tes
            if types=='BTES' or types == 'BTESLHN' or types == 'HP' or types == "HPLHN" or types == 'CHP' or types == 'CHPLHN':
                # Create thermal storage
                tes = TES.thermalEnergyStorageExtended(environment, t_init=20, capacity=tes_capacity[i], t_max=tes_t_max[i], t_surroundings=20,
                                                   k_loss=tes_k_loss[i], h_d_ratio=3.5, use_outside_temp=False)
                bes.addDevice(tes)

            # heatpump
            if types == 'HP' or types == "HPLHN":
                # Create electrical heater
                eh = EH.ElectricalHeaterExtended(environment, q_nominal=eh_q_nominal[i], eta=1,
                                                       t_max=85, lower_activation_limit=0)
                bes.addDevice(eh)

                # Create HP
                heater = HP.heatPumpSimple(environment, q_nominal=hp_q_nominal[i], t_max=55.0,
                         lower_activation_limit=hp_lal[i], hp_type='aw', t_sink=45.0)
                bes.addDevice(heater)

            # chp
            if types == 'CHP' or types == 'CHPLHN':
                # Create chp
                heater = CHP.ChpExtended(environment, p_nominal=chp_p_nominal[i], q_nominal=chp_q_nominal[i], eta_total=chp_eta_total[i], t_max=90,
                                     lower_activation_limit=chp_lal[i])
                bes.addDevice(heater)

            extended_building.addEntity(bes)

            city_object.add_extended_building(extended_building=extended_building,
                                              position=position)

            if list_PV[i] > 0:
                # Create PV
                if city_object.node[node]['entity'].roof_usabl_pv_area < list_PV[i]:
                # Check if there is enough roof area for PV, if not set PV area to maximum roof area
                    list_PV[i] = city_object.node[node]['entity'].roof_usabl_pv_area
                pv_simple = PV.PV(environment, list_PV[i], eta=0.9, beta=0)
                bes.addDevice(pv_simple)
                # TODO: eta and beta must be set properly
            if bat_capacity[i] > 0:
                # Create Battery
                capacity = bat_capacity[i]   #4 * 3600 * 1000  # 4 kWh = 4 * 3600*1000 J
                socInit = 0.5
                selfDischarge = 0.02
                etaCharge = list_etaCharge[i] #0.96
                etaDischarge = list_etaDischarge[i] # 0.95
                battery = Battery.BatteryExtended(environment, socInit, capacity,
                                      selfDischarge, etaCharge, etaDischarge)
                bes.addDevice(battery)

            node=node+1

            # TODO: Only Bat when PV??

        # Add a local heating network to the city
        #LHN_nodes= city_object.get_list_build_entity_node_ids() # List of buildingnodes
        if len(LHN_nodes)>=2:
            print('Buildnode with LHN:',LHN_nodes)
            dimnet.add_lhn_to_city(city_object, LHN_nodes, temp_vl=90,
                            temp_rl=50, c_p=4186, rho=1000,
                            use_street_network=False, network_type='heating',
                            plot_stepwise=False)

        print('\nGet list of node ids with building objects:')
        print(city_object.get_list_build_entity_node_ids())

        # check 1
        city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve = [9000] * 8760
        city_object.node[1001]['entity'].apartments[0].power_el.loadcurve = [1000] * 8760

        city_object.environment.weather.tAmbient=[10]*8760 # for constant HP electrical demand

        eco_calc_instance = eco_calc.EconomicCalculation()
        Calculator = EBB.calculator(city_object)
        dict_bes_data = Calculator.assembler()
        print('Dict city data', dict_bes_data)
        for i in range(len(dict_bes_data)):
            city_object, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)

        dem_rel_annuity = economic_ann.calc_dem_rel_annuity_city(city_object, eco_calc_instance)
        total_proc_annuity = economic_ann.calc_proc_annuity_multi_comp_city(city_object, eco_calc_instance)

        cap_rel_ann, op_rel_ann = economic_ann.calc_cap_and_op_rel_annuity_city(city_object, eco_calc_instance)

        # TOTAL ANNUITY
        total_annuity = eco_calc_instance.calc_total_annuity(ann_capital=cap_rel_ann,
                                                      ann_demand=dem_rel_annuity,
                                                      ann_op=op_rel_ann,
                                                      ann_proc=total_proc_annuity)

        # CO2 emission
        co2_instance = CO2_emissions.Emissions(year=2010)
        CO2_em_tot = CO2_em.CO2_emission_calc(city_object, co2_instance)



        print()
        print()
        print('dem_rel_annuity:', round(dem_rel_annuity, 2))
        print()
        print('proc_rel_annuity:', round(total_proc_annuity, 2))
        print()
        print('cap_rel_ann:', round(cap_rel_ann, 2))
        print()
        print('op_rel_ann:', round(op_rel_ann, 2))
        print()
        print('total_annuity:', round(total_annuity, 2))

        print()
        print('CO2_emissions:', round(CO2_em_tot, 2))





if __name__ == '__main__':

    simulator = test_simulation_economic_ann()

    simulator.test_single_house_electricity_chp_pv_batt()
    simulator.test_single_house_electricity_hp_pv_batt()
    simulator.test_single_house_electricity_hp()
    simulator.test_single_house_electricity_chp()




