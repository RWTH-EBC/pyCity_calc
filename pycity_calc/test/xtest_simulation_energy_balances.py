"""
Pytestfile for Energy_balance_thermal script
"""
from __future__ import division
import shapely.geometry.point as point

import pycity_base.classes.Weather as Weather
import pycity_base.classes.demand.SpaceHeating as SpaceHeating
import pycity_base.classes.demand.ElectricalDemand as ElectricalDemand
import pycity_base.classes.demand.Apartment as Apartment

import pycity_calc.buildings.building as build_ex
import pycity_calc.cities.city as city
import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.environment as env
import pycity_calc.environments.market as mark
import pycity_calc.environments.timer as time
import pycity_calc.toolbox.dimensioning.dim_networks as dimnet

import pycity_base.classes.supply.BES as BES
import pycity_calc.energysystems.boiler as Boiler
import pycity_calc.energysystems.electricalHeater as EH
import pycity_calc.energysystems.heatPumpSimple as HP
import pycity_calc.energysystems.thermalEnergyStorage as TES
import pycity_calc.energysystems.chp as CHP
import pycity_calc.energysystems.battery as Battery
import pycity_base.classes.supply.PV as PV

import pycity_calc.simulation.energy_balance_optimization.energy_balance_building as EBB

#  Currently named xTest to prevent execution on Travis CI (workaround for #87)
class xTest_simulation_EnergyBalances():

    def test_single_house_boiler(self):
        """
        Test case for single building with only one boiler. Qnom=3000W

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

        list_types=['B']
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
        tes_capacity=[700]
        tes_k_loss=[0]
        tes_t_max=[95]
        eh_q_nominal=[3000]
        hp_q_nominal=[3000]
        hp_lal=[0.5]
        chp_p_nominal=[2000]
        chp_q_nominal=[6000]
        chp_eta_total=[0.9]
        chp_lal=[0.5]


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

            node=node+1

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

        city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve=[2999.999]*100+[2000]*100+[1000]*100+[0]*8460

        Calculator=EBB.calculator(city_object)
        dict_bes_data=Calculator.assembler()
        print('Dict city data', dict_bes_data)
        for i in range(len(dict_bes_data)):
            city_object, dict_Qlhn, dict_supply =Calculator.eb_balances(dict_bes_data,i)

        assert abs(city_object.node[1001]['entity'].bes.boiler.array_fuel_power[10]-3333) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[10]-3000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.array_fuel_power[110]-2222) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[110]-2000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.array_fuel_power[210]-1666.6) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[210]-1500) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.array_fuel_power[310]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[310]-0) <= 1

        assert set(city_object.node[1001]['fuel demand']) == set(city_object.node[1001]['entity'].bes.boiler.array_fuel_power)

    def test_single_house_boiler_tes(self):
        """
        Test case for single building with one boiler + tes. Qnom = 3000W, m_tes = 1000kg


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

        list_types=['BTES']
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

            node=node+1

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

        city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve=[2999.999]*100+[2000]*100+[4000]*10+[2000]*100+[1000]*10+[0]*8440

        Calculator=EBB.calculator(city_object)
        dict_bes_data=Calculator.assembler()
        print('Dict city data', dict_bes_data)
        for i in range(len(dict_bes_data)):
            city_object, dict_Qlhn, dict_supply =Calculator.eb_balances(dict_bes_data,i)

        assert abs(city_object.node[1001]['entity'].bes.boiler.array_fuel_power[10]-3333) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[10]-3000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[10]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[10]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.array_fuel_power[105]-3333) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[105]-3000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[105]-1000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[105]) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.array_fuel_power[150]-2222) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[150]-2000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[150]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[150]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.array_fuel_power[205]-3333) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[205]-3000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[205]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[205]-1000) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.array_fuel_power[215]-3333) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[215]-2999) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[215]-1000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[215]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.array_fuel_power[315]-1666) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[315]-1500) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[315]-500) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[315]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.array_fuel_power[330]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[330]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[330]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[330]-0) <= 1

        assert set(city_object.node[1001]['fuel demand']) == set(city_object.node[1001]['entity'].bes.boiler.array_fuel_power)

    def test_single_house_chp_boiler_tes(self):
        """
        Test case for single building with chp + boiler + tes. Qnom_chp = 3000W, Pnom_CHP = 1000W, Qnom_boiler = 3000W, m_tes = 1000kg


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
        chp_p_nominal=[1000]
        chp_q_nominal=[3000]
        chp_eta_total=[0.9]
        chp_lal=[0.5]


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

            node=node+1

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

        city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve=[0]*10+[1000]*50+[2000]*100+[4000]*100+[2000]*100+[5000]*50+[7000]*10+[0]*8340

        Calculator=EBB.calculator(city_object)
        dict_bes_data=Calculator.assembler()
        print('Dict city data', dict_bes_data)
        for i in range(len(dict_bes_data)):
            city_object, dict_Qlhn, dict_supply =Calculator.eb_balances(dict_bes_data,i)

        assert abs(city_object.node[1001]['entity'].bes.chp.array_fuel_power[2]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[2]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.array_fuel_power[2]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[2]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[2]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[2]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.chp.array_fuel_power[35]-2142) <= 1
        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[35]-1500) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.array_fuel_power[35]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[35]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[35]-500) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[35]-0) <= 1

        assert abs(max(city_object.node[1001]['entity'].bes.chp.array_fuel_power[47:59])-2142) <= 1
        assert abs(max(city_object.node[1001]['entity'].bes.chp.totalQOutput[47:59]) - 1500) <= 1
        assert abs(max(city_object.node[1001]['entity'].bes.tes.array_q_charge[47:59]) - 500) <= 1
        assert abs(max(city_object.node[1001]['entity'].bes.tes.array_q_discharge[47:59]) - 1000) <= 1
        assert abs(min(city_object.node[1001]['entity'].bes.tes.array_q_charge[47:59]) - 0) <= 1
        assert abs(min(city_object.node[1001]['entity'].bes.tes.array_q_discharge[47:59]) - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.chp.array_fuel_power[100]-4400) <= 1
        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[100]-3000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.array_fuel_power[100]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[100]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[100]-1000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[100]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.chp.array_fuel_power[150]-2886) <= 1
        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[150]-2000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.array_fuel_power[150]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[150]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[150]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[150]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.chp.array_fuel_power[200]-4400) <= 1
        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[200]-3000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.array_fuel_power[200]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[200]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[200]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[200]-1000) <= 1

        assert abs(city_object.node[1001]['entity'].bes.chp.array_fuel_power[245]-4400) <= 1
        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[245]-3000) <= 1
        assert abs(max(city_object.node[1001]['entity'].bes.boiler.totalQOutput[240:250])-1500) <= 1 and abs(max(city_object.node[1001]['entity'].bes.tes.array_q_charge[240:250])-500) <= 1
        assert abs(max(city_object.node[1001]['entity'].bes.tes.array_q_discharge[240:250])-1000) <= 1

        assert abs(city_object.node[1001]['entity'].bes.chp.array_fuel_power[380]-4400) <= 1
        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[380]-3000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.array_fuel_power[380]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[380]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[380]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[380]-2000) <= 1

        assert abs(city_object.node[1001]['entity'].bes.chp.array_fuel_power[400]-4400) <= 1
        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[400]-3000) <= 1
        assert abs(max(city_object.node[1001]['entity'].bes.boiler.totalQOutput[395:405])-3000) <= 1 and abs(max(city_object.node[1001]['entity'].bes.tes.array_q_charge[395:405])-1000) <= 1
        assert abs(max(city_object.node[1001]['entity'].bes.tes.array_q_discharge[395:405])-2000) <= 1

        assert abs(city_object.node[1001]['entity'].bes.chp.array_fuel_power[415]-4400) <= 1
        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[415]-3000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.array_fuel_power[415]-3333.3) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[415]-3000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[415]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[415]-1000) <= 1

        assert set(city_object.node[1001]['fuel demand']) == set(city_object.node[1001]['entity'].bes.boiler.array_fuel_power+ city_object.node[1001]['entity'].bes.chp.array_fuel_power)

    def test_two_house_boiler(self):
        """
        Test case for two buildings with boiler and LHN conncection. Qnom_boiler = 3000W

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
        ###############
        # Building 1
        ##############
        list_types=['BLHN','BLHN']
        year = 2010
        timestep = 3600
        livingArea=[120,120]
        b_Space_heat_demand=True
        specificDemandSH=[100,100]
        annualDemandel=[5100,3100]
        profileType=['H0','H0']
        methodel=[1,1]
        b_domestic_hot_water=False
        b_el_demand=True
        roof_usabl_pv_area=[30,30]
        boiler_q_nominal=[5000,3000]
        boiler_eta=[0.9,0.9]
        boiler_lal=[0.5,0.5]
        tes_capacity=[1000,1000]
        tes_k_loss=[0,0]
        tes_t_max=[95,95]
        eh_q_nominal=[3000,3000]
        hp_q_nominal=[3000,3000]
        hp_lal=[0.5,0.5]
        chp_p_nominal=[1000,1000]
        chp_q_nominal=[3000,3000]
        chp_eta_total=[0.9,0.9]
        chp_lal=[0.5,0.5]


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

            node=node+1

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

        city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve=[0]*50+[1000]*50+[2000]*50+[2999.99]*50+[4000]*50+[0]*8510
        city_object.node[1002]['entity'].apartments[0].demandSpaceheating.loadcurve=([0]*10+[1000]*10+[2000]*10+[2999.99]*10+[3800]*10)*5+[0]*8510

        Calculator=EBB.calculator(city_object)
        dict_bes_data=Calculator.assembler()
        print('Dict city data', dict_bes_data)
        for i in range(len(dict_bes_data)):
            city_object, dict_Qlhn, dict_supply =Calculator.eb_balances(dict_bes_data,i)


        print('aaaaaaaaaaaaaaaaaa:', sum(city_object.node[1001]['entity'].bes.boiler.totalQOutput))
        print(sum(city_object.node[1002]['entity'].bes.boiler.totalQOutput))

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[5]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[5]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[15]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[15]-1500) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[25]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[25]-2000) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[35]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[35]-3000) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[45]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[45]-3000) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[55]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[55]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[65]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[65]-1500) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[75]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[75]-2000) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[85]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[85]-3000) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[95]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[95]-3000) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[105]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[105]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[115]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[115]-1500) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[125]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[125]-2000) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[135]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[135]-3000) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[145]-2911) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[145]-3000) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[155]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[155]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[165]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[165]-1500) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[175]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[175]-2000) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[185]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[185]-3000) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[195]-3911) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[195]-3000) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[205]-4000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[205]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[215]-4000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[215]-1500) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[225]-4000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[225]-2000) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[235]-4000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[235]-3000) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[245]-4911) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[245]-3000) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[255]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[255]-0) <= 1

        assert set(city_object.node[1001]['fuel demand']) == set(city_object.node[1001]['entity'].bes.boiler.array_fuel_power)
        assert set(city_object.node[1002]['fuel demand']) == set(city_object.node[1002]['entity'].bes.boiler.array_fuel_power)

    def test_two_house_boiler_tes(self):
        """
        Test case for two buildings with boiler+tes and LHN conncection. Qnom_boiler = 3000W

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
        ###############
        # Building 1
        ##############
        list_types=['BTESLHN','BTESLHN']
        year = 2010
        timestep = 3600
        livingArea=[120,120]
        b_Space_heat_demand=True
        specificDemandSH=[100,100]
        annualDemandel=[3000,3000]
        profileType=['H0','H0']
        methodel=[1,1]
        b_domestic_hot_water=False
        b_el_demand=True
        roof_usabl_pv_area=[30,30]
        boiler_q_nominal=[7001,2500]
        boiler_eta=[0.9,0.9]
        boiler_lal=[0.5,0.5]
        tes_capacity=[500,50]
        tes_k_loss=[0.01,0.01]
        tes_t_max=[95,95]
        eh_q_nominal=[3000,3000]
        hp_q_nominal=[3000,3000]
        hp_lal=[0.5,0.5]
        chp_p_nominal=[1000,1000]
        chp_q_nominal=[3000,3000]
        chp_eta_total=[0.9,0.9]
        chp_lal=[0.5,0.5]


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

            node=node+1

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
                tes = TES.thermalEnergyStorageExtended(environment, t_init=20.01, capacity=tes_capacity[i], t_max=tes_t_max[i], t_surroundings=20,
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

        city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve=[0]*50+[1000]*50+[2000]*50+[2999.99]*50+[4000]*50+[5000]*50+[0]*8460
        city_object.node[1002]['entity'].apartments[0].demandSpaceheating.loadcurve=([0]*10+[1000]*10+[2000]*10+[2999.99]*10+[3800]*10)*6+[0]*8460


        Calculator=EBB.calculator(city_object)
        dict_bes_data=Calculator.assembler()
        print('Dict city data', dict_bes_data)
        for i in range(len(dict_bes_data)):
            city_object, dict_Qlhn, dict_supply =Calculator.eb_balances(dict_bes_data,i)


        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[5]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[5]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[5]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[5]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[5]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[5]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[15]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[15]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[15]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[15]-1250) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[15]-250) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[15]-0) <= 1

        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[20]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[20]-500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[20]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[25]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[25]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[25]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[25]-2000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[25]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[25]-0) <= 1

        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[30]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[30]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[30]-500) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[35]-3500) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[35]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[35]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[35]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[35]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[35]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[45]-3500) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[45]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[45]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[45]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[45]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[45]-0) <= 1

        assert abs(max(city_object.node[1001]['entity'].bes.boiler.totalQOutput[55:83])-3500) <=1
        assert abs(max(city_object.node[1001]['entity'].bes.tes.array_q_charge[55:83]) - 2500) <= 1
        assert abs(max(city_object.node[1001]['entity'].bes.tes.array_q_discharge[55:83]) - 1000) <= 1
        assert abs(min(city_object.node[1001]['entity'].bes.boiler.totalQOutput[55:83])-0) <=1
        assert abs(min(city_object.node[1001]['entity'].bes.tes.array_q_charge[55:83]) - 0) <= 1
        assert abs(min(city_object.node[1001]['entity'].bes.tes.array_q_discharge[55:83]) - 0) <= 1

        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[55]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[55]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[55]-0) <= 1

        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[65]-1250) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[65]-250) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[65]-0) <= 1

        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[75]-2000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[75]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[75]-0) <= 1

        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[80]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[80]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[80]-500) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[85]-3500) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[85]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[85]-1000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[85]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[85]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[85]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[95]-3500) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[95]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[95]-1000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[95]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[95]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[95]-0) <= 1

        assert abs(max(city_object.node[1001]['entity'].bes.boiler.totalQOutput[100:132])-3500) <=1
        assert abs(max(city_object.node[1001]['entity'].bes.tes.array_q_charge[100:132]) - 1500) <= 1
        assert abs(max(city_object.node[1001]['entity'].bes.tes.array_q_discharge[100:132]) - 2000) <= 1
        assert abs(min(city_object.node[1001]['entity'].bes.boiler.totalQOutput[100:132])-0) <=1
        assert abs(min(city_object.node[1001]['entity'].bes.tes.array_q_charge[100:132]) - 0) <= 1
        assert abs(min(city_object.node[1001]['entity'].bes.tes.array_q_discharge[100:132]) - 0) <= 1

        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[105]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[105]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[105]-0) <= 1


        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[115]-1250) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[115]-250) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[115]-0) <= 1

        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[125]-2000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[125]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[125]-0) <= 1

        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[130]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[130]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[130]-500) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[135]-4111) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[135]-1500) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[135]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[135]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[135]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[135]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[145]-4911) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[145]-1500) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[145]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[145]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[145]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[145]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[155]-3500) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[155]-500) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[155]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[155]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[155]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[155]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[165]-3500) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[165]-500) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[165]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[165]-1250) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[165]-250) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[165]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[175]-3500) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[175]-500) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[175]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[175]-2000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[175]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[175]-0) <= 1

        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[180]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[180]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[180]-500) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[185]-4111) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[185]-500) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[185]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[185]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[185]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[185]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[195]-4911) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[195]-500) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[195]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[195]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[195]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[195]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[205]-4000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[205]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[205]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[205]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[205]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[205]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[215]-4000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[215]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[215]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[215]-1250) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[215]-250) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[215]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[225]-4000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[225]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[225]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[225]-2000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[225]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[225]-0) <= 1


        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[235]-4611) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[235]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[235]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[235]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[235]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[235]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[245]-5411) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[245]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[245]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[245]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[245]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[245]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[255]-5000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[255]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[255]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[255]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[255]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[255]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[265]-5000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[265]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[265]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[265]-1250) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[265]-250) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[265]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[275]-5000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[275]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[275]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[275]-2000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[275]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[275]-0) <= 1

        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[280]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[280]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[280]-500) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[285]-5611) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[285]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[285]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[285]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[285]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[285]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[295]-6411) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[295]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[295]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[295]-2500) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[295]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[295]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[305]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[305]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[305]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[305]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[305]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[305]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[400]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[400]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[400]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[400]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[400]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[400]-0) <= 1

        assert set(city_object.node[1001]['fuel demand']) == set(city_object.node[1001]['entity'].bes.boiler.array_fuel_power)
        assert set(city_object.node[1002]['fuel demand']) == set(city_object.node[1002]['entity'].bes.boiler.array_fuel_power)

    def test_two_house_chp_boiler_tes(self):
        """
        Test case for two buildings with chp+boiler+tes and LHN conncection. Qnom_boiler = 3000W

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
        ###############
        # Building 1
        ##############
        list_types=['CHPLHN','CHPLHN']
        year = 2010
        timestep = 3600
        livingArea=[120,120]
        b_Space_heat_demand=True
        specificDemandSH=[100,100]
        annualDemandel=[3000,3000]
        profileType=['H0','H0']
        methodel=[1,1]
        b_domestic_hot_water=False
        b_el_demand=True
        roof_usabl_pv_area=[30,30]
        boiler_q_nominal=[3000,3000]
        boiler_eta=[0.9,0.9]
        boiler_lal=[0.5,0.5]
        tes_capacity=[100,10]
        tes_k_loss=[0.01,0.01]
        tes_t_max=[95,95]
        eh_q_nominal=[3000,3000]
        hp_q_nominal=[3000,3000]
        hp_lal=[0.5,0.5]
        chp_p_nominal=[1000,1000]
        chp_q_nominal=[3000,3000]
        chp_eta_total=[0.9,0.9]
        chp_lal=[0.5,0.5]


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

            node=node+1

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
                tes = TES.thermalEnergyStorageExtended(environment, t_init=94.9, capacity=tes_capacity[i], t_max=tes_t_max[i], t_surroundings=20,
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

        city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve=[0]*30+[1000]*30+[2000]*30+[4000]*30+[4600]*30+[0]*8610
        city_object.node[1002]['entity'].apartments[0].demandSpaceheating.loadcurve=[6000]*150+[0]*8610
        city_object.node[1002]['entity'].apartments[0].demandSpaceheating.loadcurve[5]=7400
        city_object.node[1002]['entity'].apartments[0].demandSpaceheating.loadcurve[6]=7600
        city_object.node[1002]['entity'].apartments[0].demandSpaceheating.loadcurve[7]=9100
        city_object.node[1002]['entity'].apartments[0].demandSpaceheating.loadcurve[8]=10600

        city_object.node[1002]['entity'].apartments[0].demandSpaceheating.loadcurve[30]=7400
        city_object.node[1002]['entity'].apartments[0].demandSpaceheating.loadcurve[31]=7600
        city_object.node[1002]['entity'].apartments[0].demandSpaceheating.loadcurve[32]=9100
        city_object.node[1002]['entity'].apartments[0].demandSpaceheating.loadcurve[33]=10600

        city_object.node[1002]['entity'].apartments[0].demandSpaceheating.loadcurve[60]=7400
        city_object.node[1002]['entity'].apartments[0].demandSpaceheating.loadcurve[61]=7600

        city_object.node[1002]['entity'].apartments[0].demandSpaceheating.loadcurve[70]=6900
        city_object.node[1002]['entity'].apartments[0].demandSpaceheating.loadcurve[71]=7100
        city_object.node[1002]['entity'].apartments[0].demandSpaceheating.loadcurve[72]=8600
        city_object.node[1002]['entity'].apartments[0].demandSpaceheating.loadcurve[73]=9900 - 12
        city_object.node[1002]['entity'].apartments[0].demandSpaceheating.loadcurve[74]=6100

        city_object.node[1002]['entity'].apartments[0].demandSpaceheating.loadcurve[90]=7400
        city_object.node[1002]['entity'].apartments[0].demandSpaceheating.loadcurve[91]=7600

        city_object.node[1002]['entity'].apartments[0].demandSpaceheating.loadcurve[99]=7400 -12

        city_object.node[1002]['entity'].apartments[0].demandSpaceheating.loadcurve[126]=7400 -111
        #city_object.node[1002]['entity'].apartments[0].demandSpaceheating.loadcurve[127]=7600


        Calculator=EBB.calculator(city_object)
        dict_bes_data=Calculator.assembler()
        print('Dict city data', dict_bes_data)
        for i in range(len(dict_bes_data)):
            city_object, dict_Qlhn, dict_supply =Calculator.eb_balances(dict_bes_data,i)

        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[4]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[4]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[4]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[4]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.chp.totalQOutput[4]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[4]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[4]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[4]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[5]-1511) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[5]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[5]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[5]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.chp.totalQOutput[5]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[5]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[5]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[5]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[6]-1711) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[6]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[6]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[6]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.chp.totalQOutput[6]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[6]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[6]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[6]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[7]-3000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[7]-1500) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[7]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[7]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.chp.totalQOutput[7]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[7]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[7]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[7]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[8]-3000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[8]-1711) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[8]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[5]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.chp.totalQOutput[8]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[8]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[8]- 0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[8]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[9]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[9]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[9]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[9]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.chp.totalQOutput[9]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[9]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[9]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[9]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[29]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[29]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[29]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[29]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.chp.totalQOutput[29]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[29]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[29]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[29]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[30]-1511) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[30]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[30]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[30]-1000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.chp.totalQOutput[30]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[30]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[30]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[30]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[31]-1711) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[31]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[31]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[31]-1000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.chp.totalQOutput[31]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[31]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[31]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[31]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[32]-3000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[32]-1500) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[32]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[32]-1000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.chp.totalQOutput[32]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[32]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[32]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[32]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[33]-3000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[33]-1711) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[33]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[33]-1000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.chp.totalQOutput[33]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[33]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[33]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[33]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[60]-3000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[60]-1511) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[60]-1000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[60]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.chp.totalQOutput[60]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[60]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[60]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[60]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[61]-3000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[61]-1711) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[61]-1000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[61]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.chp.totalQOutput[61]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[61]-3000) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[61]-0) <= 1
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[61]-0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[70]-3000) <= 2
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[70]-1500) <= 2
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[70]-0) <= 2
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[70]-0) <= 2
        assert abs(city_object.node[1002]['entity'].bes.chp.totalQOutput[70]-3000) <= 2
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[70]-3000) <= 2
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[70]-0) <= 2
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[70]-0) <= 2

        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[71]-3000) <= 2
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[71]-1500) <= 2
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[71]-0) <= 2
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[71]-0) <= 2
        assert abs(city_object.node[1002]['entity'].bes.chp.totalQOutput[71]-3000) <= 2
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[71]-3000) <= 2
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[71]-0) <= 2
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[71]-0) <= 2

        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[72]-3000) <= 2
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[72]-1714) <= 2
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[72]-3) <= 2
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[72]-0) <= 2
        assert abs(city_object.node[1002]['entity'].bes.chp.totalQOutput[72]-3000) <= 2
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[72]-3000) <= 2
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[72]-0) <= 2
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[72]-0) <= 2

        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[73]-3000) <= 2
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[73]-3000) <= 2
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[73]-0) <= 2
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[73]-0) <= 2
        assert abs(city_object.node[1002]['entity'].bes.chp.totalQOutput[73]-3000) <= 2
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[73]-3000) <= 2
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[73]-0) <= 2
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[73]-0) <= 2

        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[74]-2000) <= 2
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[74]-0) <= 2
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[74]-0) <= 2
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[74]-0) <= 2
        assert abs(city_object.node[1002]['entity'].bes.chp.totalQOutput[74]-3000) <= 2
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[74]-3000) <= 2
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[74]-0) <= 2
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[74]-100) <= 2

        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[90]-3000) <= 2
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[90]-1511) <= 2
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[90]-0) <= 2
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[90]-1000) <= 2
        assert abs(city_object.node[1002]['entity'].bes.chp.totalQOutput[90]-3000) <= 2
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[90]-3000) <= 2
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[90]-0) <= 2
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[90]-0) <= 2

        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[91]-3000) <= 2
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[91]-1711) <= 2
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[91]-0) <= 2
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[91]-1000) <= 2
        assert abs(city_object.node[1002]['entity'].bes.chp.totalQOutput[91]-3000) <= 2
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[91]-3000) <= 2
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[91]-0) <= 2
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[91]-0) <= 2

        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[99]-3000) <= 2
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[99]-3000) <= 2
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[99]-500) <= 2
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[99]-0) <= 2
        assert abs(city_object.node[1002]['entity'].bes.chp.totalQOutput[99]-3000) <= 2
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[99]-3000) <= 2
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[99]-0) <= 2
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[99]-0) <= 2

        assert abs(city_object.node[1001]['entity'].bes.chp.totalQOutput[126]-3000) <= 2
        assert abs(city_object.node[1001]['entity'].bes.boiler.totalQOutput[126]-1500) <= 2
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[126]-0) <= 2
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[126]-1600) <= 2
        assert abs(city_object.node[1002]['entity'].bes.chp.totalQOutput[126]-3000) <= 2
        assert abs(city_object.node[1002]['entity'].bes.boiler.totalQOutput[126]-3000) <= 2
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_charge[126]-0) <= 2
        assert abs(city_object.node[1002]['entity'].bes.tes.array_q_discharge[126]-0) <= 2

        assert set(city_object.node[1001]['fuel demand']) == set(city_object.node[1001]['entity'].bes.boiler.array_fuel_power+city_object.node[1001]['entity'].bes.chp.array_fuel_power)
        assert set(city_object.node[1002]['fuel demand'] )== set(city_object.node[1002]['entity'].bes.boiler.array_fuel_power+city_object.node[1002]['entity'].bes.chp.array_fuel_power)

    def test_single_house_hp_eh_tes(self):
        """
        Test case for single building with one boiler + tes. Qnom = 3000W, m_tes = 1000kg


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

            node=node+1

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
        city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve=[999.999]*100+[2000]*100+[2999.999]*100+[3900]*100+[2000]*100+[4100]*100+[2000]*100+[4600]*100+[6100]*10+[0]*7950

        # check 2
        # city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve=[2999.999]*100+[2000]*100+[4000]*10+[2000]*100+[1000]*10+[0]*8440

        # check 3
        # city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve=[2500]*100+[4000]*200+[1499]*300+[5000]*400+[0]*7760


        Calculator=EBB.calculator(city_object)
        dict_bes_data=Calculator.assembler()
        print('Dict city data', dict_bes_data)
        for i in range(len(dict_bes_data)):
            city_object, dict_Qlhn, dict_supply =Calculator.eb_balances(dict_bes_data,i)

        #check 1

        #timestep: 5
        assert abs(city_object.node[1001]['entity'].bes.heatpump.totalQOutput[5]-2500) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalQOutput[5]-500) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[5]-2000)<=1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[5]-0)<=1


        #timestep: 150
        assert abs(city_object.node[1001]['entity'].bes.heatpump.totalQOutput[150]-2750) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalQOutput[150]-250) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[150]-1000)<=1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[150]-0)<=1

        #timestep: 190
        assert abs(city_object.node[1001]['entity'].bes.heatpump.totalQOutput[190]-2000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalQOutput[190]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[190]-0)<=1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[190]-0)<=1


        #timestep: 250
        assert abs(city_object.node[1001]['entity'].bes.heatpump.totalQOutput[250]-3000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalQOutput[250]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[250]-0)<=1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[250]-0)<=1


        #timestep: 320
        assert abs(city_object.node[1001]['entity'].bes.heatpump.totalQOutput[320]-3000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalQOutput[320]-0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[320]-0)<=1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[320]-900)<=1


        #timestep: 380
        assert abs(city_object.node[1001]['entity'].bes.heatpump.totalQOutput[380]-3000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalQOutput[380]-900) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[380]-0)<=1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[380]-0)<=1

        #timestep: 450
        assert abs(city_object.node[1001]['entity'].bes.heatpump.totalQOutput[450]-2750) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalQOutput[450]-250) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[450]-1000)<=1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[450]-0)<=1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.totalQOutput[480] - 2000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalQOutput[480] - 0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[480] - 0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[480] - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.totalQOutput[510] - 3000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalQOutput[510] - 0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[510] - 0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[510] - 1100) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.totalQOutput[580] - 3000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalQOutput[580] - 1100) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[580] - 0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[580] - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.totalQOutput[610] - 2750) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalQOutput[610] - 250) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[610] - 1000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[610] - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.totalQOutput[680] - 2000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalQOutput[680] - 0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[680] - 0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[680] - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.totalQOutput[710] - 3000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalQOutput[710] - 0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[710] - 0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[710] - 1600) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.totalQOutput[750] - 3000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalQOutput[750] - 1600) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[750] - 0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[750] - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.totalQOutput[802] - 3000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalQOutput[802] - 3000) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[802] - 0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[802] - 100) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.totalQOutput[820] - 0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalQOutput[820] - 0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_charge[820] - 0) <= 1
        assert abs(city_object.node[1001]['entity'].bes.tes.array_q_discharge[820] - 0) <= 1

        #assert set(city_object.node[1001]['electrical demand']) == set(city_object.node[1001]['entity'].get_electric_power_curve()+city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption+city_object.node[1001]['entity'].bes.heatpump.array_el_power_in)
        #for iiii in range(len(city_object.node[1001]['electrical demand'])):
        #    if abs(city_object.node[1001]['electrical demand'][iiii] - city_object.node[1001]['entity'].get_electric_power_curve()[iiii]+city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[iiii]+city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[iiii])<2:
        #        print('stop')

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
        city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve=[999.999]*100+[2000]*100+[2999.999]*100+[3900]*100+[2000]*100+[4100]*100+[2000]*100+[4600]*100+[6100]*10+[0]*7950
        city_object.node[1001]['entity'].apartments[0].power_el.loadcurve=[1000]*8760
        city_object.environment.weather.tAmbient=[10]*8760 # for constant HP electrical demand


        Calculator=EBB.calculator(city_object)
        dict_bes_data=Calculator.assembler()
        print('Dict city data', dict_bes_data)
        for i in range(len(dict_bes_data)):
            city_object, dict_Qlhn, dict_supply =Calculator.eb_balances(dict_bes_data,i)

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[5] - 764) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[5] - 500) <= 1

        assert abs(max(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[20:40]) - 764) <= 1
        assert abs(max(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[20:40]) - 500) <= 1
        assert abs(min(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[20:40]) - 0) <= 1
        assert abs(min(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[20:40]) - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[120] - 840) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[120] - 250) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[180] - 611) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[180] - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[220] - 917) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[220] - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[320] - 917) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[320] - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[380] - 917) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[380] - 900) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[420] - 840) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[420] - 250) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[480] - 611) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[480] - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[520] - 917) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[520] - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[570] - 917) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[570] - 1100) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[620] - 840) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[620] - 250) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[680] - 611) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[680] - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[710] - 917) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[710] - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[750] - 917) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[750] - 1600) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[805] - 917) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[805] - 3000) <= 1

        assert set(city_object.node[1001]['electrical demand']) == set(city_object.node[1001]['entity'].get_electric_power_curve()+city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption+city_object.node[1001]['entity'].bes.heatpump.array_el_power_in)

    def test_single_house_electricity_hp_pv(self):

        """
        Test case for single building with heatpump and PV


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
        bat_capacity = [0]
        list_etaCharge = [0.96]
        list_etaDischarge = [0.95]

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
                selfDischarge = 0.02
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
        city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve = [999.999]*144+[2000]*144+[3900]*144+[2000]*144+[4100]*144+[2000]*144+[4600]*144+[6100]*10+[0]*7742
        #city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve = ([0]*10+[500] * 100 + [1000] * 100 + [2000] * 100 + [3200] * 100 + [4000]* 100 + [5000] *100 + [7000]*10)*3 +[0] * 6900
        city_object.node[1001]['entity'].apartments[0].power_el.loadcurve = [1000] * 8760
        city_object.environment.weather.tAmbient = [10] * 8760  # for constant HP electrical demand
        #city_object.environment.weather.qDiffuse[0:8760] =  [400] * 30 + [100] * 30 + [0] * 26 + [400] * 4 + [100] * 4 + [0] * 3 + [400] * 11+ [100] * 10 + [0] * 9 + [400] * 3+ [100] * 4 + [0] * 8626
        #city_object.environment.weather.qDirect[0:8760] =   [400] * 30 + [100] * 30 + [0] * 26 + [400] * 4 + [100] * 4 + [0] * 3 + [400] * 11+ [100] * 10 + [0] * 9 + [400] * 3+ [100] * 4 + [0] * 8626

        city_object.environment.weather.qDiffuse[0:8760] = ([400]*24 + [200] * 24 + [0] * 24) * 14 + [0]*7752
        city_object.environment.weather.qDirect[0:8760] = ([400]*24 + [200] * 24 + [0] * 24) * 14 + [0]*7752

        Calculator = EBB.calculator(city_object)
        dict_bes_data = Calculator.assembler()
        print('Dict city data', dict_bes_data)
        for i in range(len(dict_bes_data)):
            city_object, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[5] - 764) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[5] - 500) <= 1

        assert abs(max(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[20:140]) - 764) <= 1
        assert abs(max(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[20:140]) - 500) <= 1
        assert abs(min(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[20:140]) - 0) <= 1
        assert abs(min(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[20:140]) - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[150] - 840) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[150] - 250) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[250] - 611) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[250] - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[300] - 917) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[300] - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[400] - 917) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[400] - 900) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[450] - 840) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[450] - 250) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[550] - 611) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[550] - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[600] - 917) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[600] - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[650] - 917) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[650] - 1100) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[750] - 840) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[750] - 250) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[800] - 611) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[800] - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[900] - 917) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[900] - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[950] - 917) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[950] - 1600) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[1010] - 917) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[1010] - 3000) <= 1


        assert abs(city_object.node[1001]['pv_used_self'][5] - 2264) <= 1
        assert abs(city_object.node[1001]['pv_sold'][5] - 1336) <= 1

        assert abs(max(city_object.node[1001]['pv_used_self'][10:16]) - 2264) <= 1
        assert abs(max(city_object.node[1001]['pv_sold'][10:16]) - 6200) <= 1
        assert abs(min(city_object.node[1001]['pv_used_self'][10:16]) - 1000) <= 1
        assert abs(min(city_object.node[1001]['pv_sold'][10:16]) - 4936) <= 1

        assert abs(max(city_object.node[1001]['pv_used_self'][17:22]) - 2264) <= 1
        assert abs(max(city_object.node[1001]['pv_sold'][17:22]) - 2600) <= 1
        assert abs(min(city_object.node[1001]['pv_used_self'][17:22]) - 1000) <= 1
        assert abs(min(city_object.node[1001]['pv_sold'][17:22]) - 1336) <= 1

        assert abs(max(city_object.node[1001]['pv_used_self'][25:32]) - 1800) <= 1
        assert abs(max(city_object.node[1001]['pv_sold'][25:32]) - 800) <= 1
        assert abs(min(city_object.node[1001]['pv_used_self'][25:32]) - 1000) <= 1
        assert abs(min(city_object.node[1001]['pv_sold'][25:32]) - 0) <= 1

        assert abs(max(city_object.node[1001]['pv_used_self'][34:40]) - 2264) <= 1
        assert abs(max(city_object.node[1001]['pv_sold'][34:40]) - 2600) <= 1
        assert abs(min(city_object.node[1001]['pv_used_self'][34:40]) - 1000) <= 1
        assert abs(min(city_object.node[1001]['pv_sold'][34:40]) - 1336) <= 1

        assert abs(max(city_object.node[1001]['pv_used_self'][41:47]) - 1800) <= 1
        assert abs(max(city_object.node[1001]['pv_sold'][41:47]) - 800) <= 1
        assert abs(min(city_object.node[1001]['pv_used_self'][41:47]) - 1000) <= 1
        assert abs(min(city_object.node[1001]['pv_sold'][41:47]) - 0) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][50] - 0) <= 1
        assert abs(city_object.node[1001]['pv_sold'][50] - 0) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][150] - 2090) <= 1
        assert abs(city_object.node[1001]['pv_sold'][150] - 1510) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][156] - 2090) <= 1
        assert abs(city_object.node[1001]['pv_sold'][156] - 5110) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][165] - 2090) <= 1
        assert abs(city_object.node[1001]['pv_sold'][165] - 1510) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][170] - 1800) <= 1
        assert abs(city_object.node[1001]['pv_sold'][170] - 0) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][180] - 2090) <= 1
        assert abs(city_object.node[1001]['pv_sold'][180] - 1510) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][190] - 1800) <= 1
        assert abs(city_object.node[1001]['pv_sold'][190] - 0) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][200] - 0) <= 1
        assert abs(city_object.node[1001]['pv_sold'][200] - 0) <= 1


        assert abs(city_object.node[1001]['pv_used_self'][220] - 1611) <= 1
        assert abs(city_object.node[1001]['pv_sold'][220] - 1989) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][230] - 1611) <= 1
        assert abs(city_object.node[1001]['pv_sold'][230] - 5589) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][237] - 1611) <= 1
        assert abs(city_object.node[1001]['pv_sold'][237] - 1989) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][245] - 1611) <= 1
        assert abs(city_object.node[1001]['pv_sold'][245] - 189) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][253] - 1611) <= 1
        assert abs(city_object.node[1001]['pv_sold'][253] - 1989) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][260] - 1611) <= 1
        assert abs(city_object.node[1001]['pv_sold'][260] - 189) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][270] - 0) <= 1
        assert abs(city_object.node[1001]['pv_sold'][270] - 0) <= 1



        assert abs(city_object.node[1001]['pv_used_self'][290] - 1917) <= 1
        assert abs(city_object.node[1001]['pv_sold'][290] - 1683) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][300] - 1917) <= 1
        assert abs(city_object.node[1001]['pv_sold'][300] - 5283) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][310] - 1917) <= 1
        assert abs(city_object.node[1001]['pv_sold'][310] - 1683) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][315] - 1800) <= 1
        assert abs(city_object.node[1001]['pv_sold'][315] - 0) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][325] - 1917) <= 1
        assert abs(city_object.node[1001]['pv_sold'][325] - 1683) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][332] - 1800) <= 1
        assert abs(city_object.node[1001]['pv_sold'][332] - 0) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][340] - 0) <= 1
        assert abs(city_object.node[1001]['pv_sold'][340] - 0) <= 1



        assert abs(city_object.node[1001]['pv_used_self'][368] - 2817) <= 1
        assert abs(city_object.node[1001]['pv_sold'][368] - 783) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][375] - 2817) <= 1
        assert abs(city_object.node[1001]['pv_sold'][375] - 4383) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][380] - 2817) <= 1
        assert abs(city_object.node[1001]['pv_sold'][380] - 783) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][390] - 1800) <= 1
        assert abs(city_object.node[1001]['pv_sold'][390] - 0) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][395] - 2817) <= 1
        assert abs(city_object.node[1001]['pv_sold'][395] - 783) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][405] - 1800) <= 1
        assert abs(city_object.node[1001]['pv_sold'][405] - 0) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][410] - 0) <= 1
        assert abs(city_object.node[1001]['pv_sold'][410] - 0) <= 1


        assert abs(city_object.node[1001]['pv_used_self'][435] - 2090) <= 1
        assert abs(city_object.node[1001]['pv_sold'][435] - 1510) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][445] - 2090) <= 1
        assert abs(city_object.node[1001]['pv_sold'][445] - 5110) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][455] - 2090) <= 1
        assert abs(city_object.node[1001]['pv_sold'][455] - 1510) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][460] - 1800) <= 1
        assert abs(city_object.node[1001]['pv_sold'][460] - 0) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][470] - 2090) <= 1
        assert abs(city_object.node[1001]['pv_sold'][470] - 1510) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][475] - 1800) <= 1
        assert abs(city_object.node[1001]['pv_sold'][475] - 0) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][481] - 0) <= 1
        assert abs(city_object.node[1001]['pv_sold'][481] - 0) <= 1




        assert abs(city_object.node[1001]['pv_used_self'][580] - 1917) <= 1
        assert abs(city_object.node[1001]['pv_sold'][580] - 1683) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][590] - 1917) <= 1
        assert abs(city_object.node[1001]['pv_sold'][590] - 5283) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][598] - 1917) <= 1
        assert abs(city_object.node[1001]['pv_sold'][598] - 1683) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][605] - 1800) <= 1
        assert abs(city_object.node[1001]['pv_sold'][605] - 0) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][615] - 1917) <= 1
        assert abs(city_object.node[1001]['pv_sold'][615] - 1683) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][620] - 1800) <= 1
        assert abs(city_object.node[1001]['pv_sold'][620] - 0) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][630] - 0) <= 1
        assert abs(city_object.node[1001]['pv_sold'][630] - 0) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][650] - 3017) <= 1
        assert abs(city_object.node[1001]['pv_sold'][650] - 583) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][660] - 3017) <= 1
        assert abs(city_object.node[1001]['pv_sold'][660] - 4183) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][670] - 3017) <= 1
        assert abs(city_object.node[1001]['pv_sold'][670] - 583) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][675] - 1800) <= 1
        assert abs(city_object.node[1001]['pv_sold'][675] - 0) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][685] - 3017) <= 1
        assert abs(city_object.node[1001]['pv_sold'][685] - 583) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][695] - 1800) <= 1
        assert abs(city_object.node[1001]['pv_sold'][695] - 0) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][700] - 0) <= 1
        assert abs(city_object.node[1001]['pv_sold'][700] - 0) <= 1



        assert abs(city_object.node[1001]['pv_used_self'][940] - 3517) <= 1
        assert abs(city_object.node[1001]['pv_sold'][940] - 83) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][950] - 3517) <= 1
        assert abs(city_object.node[1001]['pv_sold'][950] - 3683) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][955] - 3517) <= 1
        assert abs(city_object.node[1001]['pv_sold'][955] - 83) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][965] - 1800) <= 1
        assert abs(city_object.node[1001]['pv_sold'][965] - 0) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][975] - 3517) <= 1
        assert abs(city_object.node[1001]['pv_sold'][975] - 83) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][980] - 1800) <= 1
        assert abs(city_object.node[1001]['pv_sold'][980] - 0) <= 1

        assert abs(city_object.node[1001]['pv_used_self'][990] - 0) <= 1
        assert abs(city_object.node[1001]['pv_sold'][990] - 0) <= 1

        totalPV = sum(city_object.node[1001]['pv_sold']) / 1000 + sum(city_object.node[1001]['pv_used_self']) / 1000
        PV_supply = sum(city_object.node[1001]['entity'].bes.pv.getPower()) / 1000
        assert abs(totalPV - PV_supply) <= 10


        total_el_demand = sum(city_object.node[1001]['entity'].get_electric_power_curve()) / 1000
        if city_object.node[1001]['entity'].bes.hasHeatpump:
            total_el_demand += sum(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in) / 1000
            total_el_demand += sum(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption) / 1000
        el_buy = sum(city_object.node[1001]['electrical demand']) / 1000

        aaa = sum(city_object.node[1001]['electricity_heatpump']) / 1000
        # assert total electricity energy amount
        chp_sold = sum(city_object.node[1001]['chp_sold']) / 1000
        pv_sold = sum(city_object.node[1001]['pv_sold']) / 1000

        assert abs(el_buy + PV_supply - total_el_demand - chp_sold - pv_sold) < 10

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
        city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve = [999.999] * 144 + [2000] * 144 + [3900] * 144 + [2000] * 144 + [4100] * 144 + [2000] * 144 + [4600] * 144 + [6100] * 10 + [0] * 7742
        # city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve = ([0]*10+[500] * 100 + [1000] * 100 + [2000] * 100 + [3200] * 100 + [4000]* 100 + [5000] *100 + [7000]*10)*3 +[0] * 6900
        city_object.node[1001]['entity'].apartments[0].power_el.loadcurve = [1000] * 8760
        city_object.environment.weather.tAmbient = [10] * 8760  # for constant HP electrical demand
        # city_object.environment.weather.qDiffuse[0:8760] =  [400] * 30 + [100] * 30 + [0] * 26 + [400] * 4 + [100] * 4 + [0] * 3 + [400] * 11+ [100] * 10 + [0] * 9 + [400] * 3+ [100] * 4 + [0] * 8626
        # city_object.environment.weather.qDirect[0:8760] =   [400] * 30 + [100] * 30 + [0] * 26 + [400] * 4 + [100] * 4 + [0] * 3 + [400] * 11+ [100] * 10 + [0] * 9 + [400] * 3+ [100] * 4 + [0] * 8626

        city_object.environment.weather.qDiffuse[0:8760] = ([400] * 24 + [200] * 24 + [0] * 24) * 14 + [0] * 7752
        city_object.environment.weather.qDirect[0:8760] = ([400] * 24 + [200] * 24 + [0] * 24) * 14 + [0] * 7752

        Calculator = EBB.calculator(city_object)
        dict_bes_data = Calculator.assembler()
        print('Dict city data', dict_bes_data)
        for i in range(len(dict_bes_data)):
            city_object, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[5] - 764) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[5] - 500) <= 1

        assert abs(max(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[20:140]) - 764) <= 1
        assert abs(max(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[20:140]) - 500) <= 1
        assert abs(min(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[20:140]) - 0) <= 1
        assert abs(min(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[20:140]) - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[150] - 840) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[150] - 250) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[250] - 611) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[250] - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[300] - 917) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[300] - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[400] - 917) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[400] - 900) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[450] - 840) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[450] - 250) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[550] - 611) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[550] - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[600] - 917) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[600] - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[650] - 917) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[650] - 1100) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[750] - 840) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[750] - 250) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[800] - 611) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[800] - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[900] - 917) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[900] - 0) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[950] - 917) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[950] - 1600) <= 1

        assert abs(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in[1010] - 917) <= 1
        assert abs(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption[1010] - 3000) <= 1

        # assert abs(city_object.node[1001]['pv_used_self'][5] - 2264) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][5] - 1336) <= 1
        #
        # assert abs(max(city_object.node[1001]['pv_used_self'][10:16]) - 2264) <= 1
        # assert abs(max(city_object.node[1001]['pv_sold'][10:16]) - 6200) <= 1
        # assert abs(min(city_object.node[1001]['pv_used_self'][10:16]) - 1000) <= 1
        # assert abs(min(city_object.node[1001]['pv_sold'][10:16]) - 4936) <= 1
        #
        # assert abs(max(city_object.node[1001]['pv_used_self'][17:22]) - 2264) <= 1
        # assert abs(max(city_object.node[1001]['pv_sold'][17:22]) - 2600) <= 1
        # assert abs(min(city_object.node[1001]['pv_used_self'][17:22]) - 1000) <= 1
        # assert abs(min(city_object.node[1001]['pv_sold'][17:22]) - 1336) <= 1
        #
        # assert abs(max(city_object.node[1001]['pv_used_self'][25:32]) - 1800) <= 1
        # assert abs(max(city_object.node[1001]['pv_sold'][25:32]) - 800) <= 1
        # assert abs(min(city_object.node[1001]['pv_used_self'][25:32]) - 1000) <= 1
        # assert abs(min(city_object.node[1001]['pv_sold'][25:32]) - 0) <= 1
        #
        # assert abs(max(city_object.node[1001]['pv_used_self'][34:40]) - 2264) <= 1
        # assert abs(max(city_object.node[1001]['pv_sold'][34:40]) - 2600) <= 1
        # assert abs(min(city_object.node[1001]['pv_used_self'][34:40]) - 1000) <= 1
        # assert abs(min(city_object.node[1001]['pv_sold'][34:40]) - 1336) <= 1
        #
        # assert abs(max(city_object.node[1001]['pv_used_self'][41:47]) - 1800) <= 1
        # assert abs(max(city_object.node[1001]['pv_sold'][41:47]) - 800) <= 1
        # assert abs(min(city_object.node[1001]['pv_used_self'][41:47]) - 1000) <= 1
        # assert abs(min(city_object.node[1001]['pv_sold'][41:47]) - 0) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][50] - 0) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][50] - 0) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][150] - 2090) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][150] - 1510) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][156] - 2090) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][156] - 5110) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][165] - 2090) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][165] - 1510) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][170] - 1800) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][170] - 0) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][180] - 2090) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][180] - 1510) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][190] - 1800) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][190] - 0) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][200] - 0) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][200] - 0) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][220] - 1611) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][220] - 1989) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][230] - 1611) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][230] - 5589) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][237] - 1611) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][237] - 1989) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][245] - 1611) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][245] - 189) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][253] - 1611) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][253] - 1989) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][260] - 1611) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][260] - 189) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][270] - 0) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][270] - 0) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][290] - 1917) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][290] - 1683) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][300] - 1917) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][300] - 5283) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][310] - 1917) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][310] - 1683) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][315] - 1800) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][315] - 0) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][325] - 1917) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][325] - 1683) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][332] - 1800) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][332] - 0) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][340] - 0) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][340] - 0) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][368] - 2817) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][368] - 783) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][375] - 2817) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][375] - 4383) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][380] - 2817) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][380] - 783) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][390] - 1800) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][390] - 0) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][395] - 2817) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][395] - 783) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][405] - 1800) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][405] - 0) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][410] - 0) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][410] - 0) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][435] - 2090) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][435] - 1510) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][445] - 2090) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][445] - 5110) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][455] - 2090) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][455] - 1510) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][460] - 1800) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][460] - 0) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][470] - 2090) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][470] - 1510) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][475] - 1800) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][475] - 0) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][481] - 0) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][481] - 0) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][580] - 1917) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][580] - 1683) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][590] - 1917) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][590] - 5283) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][598] - 1917) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][598] - 1683) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][605] - 1800) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][605] - 0) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][615] - 1917) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][615] - 1683) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][620] - 1800) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][620] - 0) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][630] - 0) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][630] - 0) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][650] - 3017) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][650] - 583) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][660] - 3017) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][660] - 4183) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][670] - 3017) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][670] - 583) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][675] - 1800) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][675] - 0) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][685] - 3017) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][685] - 583) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][695] - 1800) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][695] - 0) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][700] - 0) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][700] - 0) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][940] - 3517) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][940] - 83) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][950] - 3517) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][950] - 3683) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][955] - 3517) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][955] - 83) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][965] - 1800) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][965] - 0) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][975] - 3517) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][975] - 83) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][980] - 1800) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][980] - 0) <= 1
        #
        # assert abs(city_object.node[1001]['pv_used_self'][990] - 0) <= 1
        # assert abs(city_object.node[1001]['pv_sold'][990] - 0) <= 1

        ########################################
        # compare total demand and supplied values
        ########################################
        # calculate total produced heat
        totalQ_produced = sum(city_object.node[1001]['entity'].bes.heatpump.totalQOutput) / 1000 + sum(
            city_object.node[1001]['entity'].bes.electricalHeater.totalQOutput) / 1000

        # Compare the initial tes Energy with the tes Energy at the end
        deltaT = city_object.node[1001]['entity'].bes.tes.array_temp_storage[8759] - \
                 city_object.node[1001]['entity'].bes.tes.array_temp_storage[0]
        deltaQstorage = city_object.node[1001][
                            'entity'].bes.tes.capacity * deltaT * 4182 / 1000 / 3600  # delta Q storage in kWh

        # Calculate total heat demand
        sph_demand_building = city_object.node[1001]['entity'].get_space_heating_power_curve()
        dhw_demand_building = city_object.node[1001]['entity'].get_dhw_power_curve()
        totalQ_demand = sum(sph_demand_building + dhw_demand_building) / 1000

        assert abs(totalQ_produced - totalQ_demand - deltaQstorage) <= 10

        totalPV = sum(city_object.node[1001]['pv_sold']) / 1000 + sum(city_object.node[1001]['pv_used_self']) / 1000
        PV_supply = sum(city_object.node[1001]['entity'].bes.pv.getPower()) / 1000
        assert abs(totalPV - PV_supply) <= 10

        eta_load = city_object.node[1001]['entity'].bes.battery.etaCharge
        eta_unload = city_object.node[1001]['entity'].bes.battery.etaDischarge
        eta_selfdischarge = city_object.node[1001]['entity'].bes.battery.selfDischarge
        deltabat2 = city_object.node[1001]['entity'].bes.battery.socInit
        for timestep in range(city_object.environment.timer.timestepsTotal):
            deltabat2 = deltabat2 * (1 - eta_selfdischarge)
            deltabat2 += (city_object.node[1001]['entity'].bes.battery.totalPCharge[timestep] * eta_load -
                          city_object.node[1001]['entity'].bes.battery.totalPDischarge[
                              timestep] / eta_unload) * city_object.environment.timer.timeDiscretization

            assert (deltabat2 - city_object.node[1001]['entity'].bes.battery.totalSoc[timestep]) < 2

        deltabat3 = (sum(city_object.node[1001]['batt_load']) - sum(city_object.node[1001]['batt_unload'])) / 1000
        deltabat4 = (sum(city_object.node[1001]['entity'].bes.battery.totalPCharge) - sum(
            city_object.node[1001]['entity'].bes.battery.totalPDischarge)) / 1000

        # assert delta electricity battery. Assert if different save methods produce equal results

        assert abs(deltabat3 - deltabat4) < 1

        total_el_demand = sum(city_object.node[1001]['entity'].get_electric_power_curve()) / 1000
        if city_object.node[1001]['entity'].bes.hasHeatpump:
            total_el_demand += sum(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in) / 1000
            total_el_demand += sum(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption) / 1000
        el_buy = sum(city_object.node[1001]['electrical demand']) / 1000

        # assert total electricity energy amount
        chp_sold = sum(city_object.node[1001]['chp_sold']) / 1000
        pv_sold = sum(city_object.node[1001]['pv_sold']) / 1000

        assert abs(el_buy + PV_supply - total_el_demand - chp_sold - pv_sold - deltabat3) < 10

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
        #city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve=[2000]*100+[4000]*100+[7000]*10+[0]*8550
        city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve=[2000]*100+[5000]*100+[7000]*100+[8000]*100+[10000]*10+[0]*8350
        city_object.node[1001]['entity'].apartments[0].power_el.loadcurve=[1000]*8760
        city_object.environment.weather.tAmbient=[10]*8760 # for constant HP electrical demand


        Calculator=EBB.calculator(city_object)
        dict_bes_data=Calculator.assembler()
        print('Dict city data', dict_bes_data)
        for i in range(len(dict_bes_data)):
            city_object, dict_Qlhn, dict_supply =Calculator.eb_balances(dict_bes_data,i)

        assert abs(city_object.node[1001]['power_el_chp'][5] - 959) <= 1
        assert abs(city_object.node[1001]['chp_sold'][5] - 0) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][5] - 959) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][50] - 0) <= 1
        assert abs(city_object.node[1001]['chp_sold'][50] - 0) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][50] - 0) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][101] - 2160) <= 1
        assert abs(city_object.node[1001]['chp_sold'][101] - 1160) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][101] - 1000) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][180] - 1744) <= 1
        assert abs(city_object.node[1001]['chp_sold'][180] - 744) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][180] - 1000) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][203] - 2160) <= 1
        assert abs(city_object.node[1001]['chp_sold'][203] - 1160) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][203] - 1000) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][450] - 0) <= 1
        assert abs(city_object.node[1001]['chp_sold'][450] - 0) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][450] - 0) <= 1

        ########################################
        # compare total demand and supplied values
        ########################################
        # calculate total produced heat
        totalQ_produced = sum(city_object.node[1001]['entity'].bes.chp.totalQOutput) / 1000 + sum(
            city_object.node[1001]['entity'].bes.boiler.totalQOutput) / 1000

        # Compare the initial tes Energy with the tes Energy at the end
        deltaT = city_object.node[1001]['entity'].bes.tes.array_temp_storage[8759] - \
                 city_object.node[1001]['entity'].bes.tes.array_temp_storage[0]
        deltaQstorage = city_object.node[1001][
                            'entity'].bes.tes.capacity * deltaT * 4182 / 1000 / 3600  # delta Q storage in kWh

        # Calculate total heat demand
        sph_demand_building = city_object.node[1001]['entity'].get_space_heating_power_curve()
        dhw_demand_building = city_object.node[1001]['entity'].get_dhw_power_curve()
        totalQ_demand = sum(sph_demand_building + dhw_demand_building) / 1000

        assert abs(totalQ_produced - totalQ_demand - deltaQstorage) <= 10

        totalCHP = sum(city_object.node[1001]['chp_sold']) / 1000 + sum(city_object.node[1001]['chp_used_self']) / 1000
        CHP_supply = sum(city_object.node[1001]['entity'].bes.chp.totalPOutput) / 1000
        assert abs(totalCHP - CHP_supply) <= 10



        total_el_demand = sum(city_object.node[1001]['entity'].get_electric_power_curve()) / 1000
        if city_object.node[1001]['entity'].bes.hasHeatpump:
            total_el_demand += sum(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in) / 1000
            total_el_demand += sum(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption) / 1000
        el_buy = sum(city_object.node[1001]['electrical demand']) / 1000

        # assert total electricity energy amount
        chp_sold = sum(city_object.node[1001]['chp_sold']) / 1000
        pv_sold = sum(city_object.node[1001]['pv_sold']) / 1000

        assert abs(el_buy + CHP_supply - total_el_demand - chp_sold - pv_sold) < 10

    def test_single_house_electricity_chp_pv(self):

        """
        Test case for single building with CHP and PV


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
        bat_capacity = [0]
        list_etaCharge = [0.96]
        list_etaDischarge = [0.95]

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
                selfDischarge = 0.02
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

        # check 2
        # city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve = [2000] * 72 + [4000] * 72 + [6050] * 72 + [0] * 8544
        # city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve = ([0]*10+[500] * 100 + [1000] * 100 + [2000] * 100 + [3200] * 100 + [4000]* 100 + [5000] *100 + [7000]*10)*3 +[0] * 6900

        city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve = [1000] * 100 + [2000] * 100 + [4000] * 100 + [5000] * 100 + [0] * 8360

        city_object.node[1001]['entity'].apartments[0].power_el.loadcurve = [1000] * 8760
        city_object.environment.weather.tAmbient = [10] * 8760  # for constant HP electrical demand
        # city_object.environment.weather.qDiffuse[0:8760] =  [400] * 30 + [100] * 30 + [0] * 26 + [400] * 4 + [100] * 4 + [0] * 3 + [400] * 11+ [100] * 10 + [0] * 9 + [400] * 3+ [100] * 4 + [0] * 8626
        # city_object.environment.weather.qDirect[0:8760] =   [400] * 30 + [100] * 30 + [0] * 26 + [400] * 4 + [100] * 4 + [0] * 3 + [400] * 11+ [100] * 10 + [0] * 9 + [400] * 3+ [100] * 4 + [0] * 8626

        # city_object.environment.weather.qDiffuse[0:8760] = ([400]*24 + [200] * 24 + [0] * 24) * 3 + [0]*8544
        # city_object.environment.weather.qDirect[0:8760] = ([400]*24 + [200] * 24 + [0] * 24) * 3 + [0]*8544

        city_object.environment.weather.qDiffuse[0:8760] = ([400] * 20 + [300] * 20 + [200] * 20 + [0] * 20) * 5 + [0] * 8360
        city_object.environment.weather.qDirect[0:8760] = ([400] * 20 + [300] * 20 + [200] * 20 + [0] * 20) * 5 + [0] * 8360



        Calculator = EBB.calculator(city_object)
        dict_bes_data = Calculator.assembler()
        print('Dict city data', dict_bes_data)
        for i in range(len(dict_bes_data)):
            city_object, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)

        assert abs(city_object.node[1001]['power_el_chp'][5] - 428) <= 1
        assert abs(city_object.node[1001]['pv_sold'][5] - 2600) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][5] - 1000) <= 1
        assert abs(city_object.node[1001]['chp_sold'][5] - 428) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][5] - 0) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][15] - 428) <= 1
        assert abs(city_object.node[1001]['pv_sold'][15] - 6200) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][15] - 1000) <= 1
        assert abs(city_object.node[1001]['chp_sold'][15] - 428) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][15] - 0) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][25] - 428) <= 1
        assert abs(city_object.node[1001]['pv_sold'][25] - 1700) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][25] - 1000) <= 1
        assert abs(city_object.node[1001]['chp_sold'][25] - 428) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][25] - 0) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][39] - 428) <= 1
        assert abs(city_object.node[1001]['pv_sold'][39] - 4400) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][39] - 1000) <= 1
        assert abs(city_object.node[1001]['chp_sold'][39] - 428) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][39] - 0) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][46] - 0) <= 1
        assert abs(city_object.node[1001]['pv_sold'][46] - 800) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][46] - 1000) <= 1
        assert abs(city_object.node[1001]['chp_sold'][46] - 0) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][46] - 0) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][72] - 428) <= 1
        assert abs(city_object.node[1001]['pv_sold'][72] - 0) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][72] - 0) <= 1
        assert abs(city_object.node[1001]['chp_sold'][72] - 0) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][72] - 428) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][85] - 0) <= 1
        assert abs(city_object.node[1001]['pv_sold'][85] - 6200) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][85] - 1000) <= 1
        assert abs(city_object.node[1001]['chp_sold'][85] - 0) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][85] - 0) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][95] - 428) <= 1
        assert abs(city_object.node[1001]['pv_sold'][95] - 2600) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][95] - 1000) <= 1
        assert abs(city_object.node[1001]['chp_sold'][95] - 428) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][95] - 0) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][103] - 959) <= 1
        assert abs(city_object.node[1001]['pv_sold'][103] - 1700) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][103] - 1000) <= 1
        assert abs(city_object.node[1001]['chp_sold'][103] - 959) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][103] - 0) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][150] - 959) <= 1
        assert abs(city_object.node[1001]['pv_sold'][150] - 0) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][150] - 0) <= 1
        assert abs(city_object.node[1001]['chp_sold'][150] - 0) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][150] - 959) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][170] - 598) <= 1
        assert abs(city_object.node[1001]['pv_sold'][170] - 2600) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][170] - 1000) <= 1
        assert abs(city_object.node[1001]['chp_sold'][170] - 598) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][170] - 0) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][230] - 959) <= 1
        assert abs(city_object.node[1001]['pv_sold'][230] - 0) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][230] - 0) <= 1
        assert abs(city_object.node[1001]['chp_sold'][230] - 0) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][230] - 959) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][290] - 959) <= 1
        assert abs(city_object.node[1001]['pv_sold'][290] - 800) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][290] - 1000) <= 1
        assert abs(city_object.node[1001]['chp_sold'][290] - 959) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][290] - 0) <= 1

        ########################################
        # compare total demand and supplied values
        ########################################
        # calculate total produced heat
        totalQ_produced = sum(city_object.node[1001]['entity'].bes.chp.totalQOutput) / 1000 + sum(
            city_object.node[1001]['entity'].bes.boiler.totalQOutput) / 1000

        # Compare the initial tes Energy with the tes Energy at the end
        deltaT = city_object.node[1001]['entity'].bes.tes.array_temp_storage[8759] - \
                 city_object.node[1001]['entity'].bes.tes.array_temp_storage[0]
        deltaQstorage = city_object.node[1001][
                            'entity'].bes.tes.capacity * deltaT * 4182 / 1000 / 3600  # delta Q storage in kWh

        # Calculate total heat demand
        sph_demand_building = city_object.node[1001]['entity'].get_space_heating_power_curve()
        dhw_demand_building = city_object.node[1001]['entity'].get_dhw_power_curve()
        totalQ_demand = sum(sph_demand_building + dhw_demand_building) / 1000

        # assert total heat energy amount
        assert abs(totalQ_produced - totalQ_demand - deltaQstorage) <= 10

        totalPV = sum(city_object.node[1001]['pv_sold']) / 1000 + sum(city_object.node[1001]['pv_used_self']) / 1000
        PV_supply = sum(city_object.node[1001]['entity'].bes.pv.getPower()) / 1000

        # assert PV electricity amounts
        assert abs(totalPV - PV_supply) <= 10

        totalCHP = sum(city_object.node[1001]['chp_sold']) / 1000 + sum(city_object.node[1001]['chp_used_self']) / 1000
        CHP_supply = sum(city_object.node[1001]['entity'].bes.chp.totalPOutput) / 1000

        # assert CHP electricity amounts
        assert abs(totalCHP - CHP_supply) <= 10



        total_el_demand = sum(city_object.node[1001]['entity'].get_electric_power_curve()) / 1000
        if city_object.node[1001]['entity'].bes.hasHeatpump:
            total_el_demand += sum(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in) / 1000
            total_el_demand += sum(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption) / 1000
        el_buy = sum(city_object.node[1001]['electrical demand']) / 1000

        # assert total electricity energy amount
        chp_sold = sum(city_object.node[1001]['chp_sold']) / 1000
        pv_sold = sum(city_object.node[1001]['pv_sold']) / 1000

        assert abs(el_buy + PV_supply + CHP_supply - total_el_demand - chp_sold - pv_sold) < 10

    def test_single_house_electricity_chp_pv_batt(self):

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
        bat_capacity = [500] #4kWh
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
                pv_simple = PV.PV(environment=environment, area=list_PV[i], eta=0.9, beta=0)
                bes.addDevice(pv_simple)
                # TODO: eta and beta must be set properly
            if bat_capacity[i] > 0:
                # Create Battery
                capacity = bat_capacity[i]  # 4 * 3600 * 1000  # 4 kWh = 4 * 3600*1000 J
                socInit = 0.5
                selfDischarge = 0
                etaCharge = list_etaCharge[i]  # 0.96
                etaDischarge = list_etaDischarge[i]  # 0.95
                battery = Battery.BatteryExtended(environment=environment, soc_init_ratio=socInit, capacity_kwh=capacity,
                                                  self_discharge=selfDischarge, eta_charge=etaCharge, eta_discharge=etaDischarge)
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

        # check 2
        # city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve = [2000] * 72 + [4000] * 72 + [6050] * 72 + [0] * 8544
        # city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve = ([0]*10+[500] * 100 + [1000] * 100 + [2000] * 100 + [3200] * 100 + [4000]* 100 + [5000] *100 + [7000]*10)*3 +[0] * 6900

        city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve = [1000] * 100 + [2000] * 100 + [4000] * 100 + [5000] * 100 + [0] * 8360

        city_object.node[1001]['entity'].apartments[0].power_el.loadcurve = [1000] * 8760
        city_object.environment.weather.tAmbient = [10] * 8760  # for constant HP electrical demand
        # city_object.environment.weather.qDiffuse[0:8760] =  [400] * 30 + [100] * 30 + [0] * 26 + [400] * 4 + [100] * 4 + [0] * 3 + [400] * 11+ [100] * 10 + [0] * 9 + [400] * 3+ [100] * 4 + [0] * 8626
        # city_object.environment.weather.qDirect[0:8760] =   [400] * 30 + [100] * 30 + [0] * 26 + [400] * 4 + [100] * 4 + [0] * 3 + [400] * 11+ [100] * 10 + [0] * 9 + [400] * 3+ [100] * 4 + [0] * 8626

        # city_object.environment.weather.qDiffuse[0:8760] = ([400]*24 + [200] * 24 + [0] * 24) * 3 + [0]*8544
        # city_object.environment.weather.qDirect[0:8760] = ([400]*24 + [200] * 24 + [0] * 24) * 3 + [0]*8544

        city_object.environment.weather.qDiffuse[0:8760] = ([400] * 20 + [300] * 20 + [200] * 20 + [0] * 20) * 5 + [0] * 8360
        city_object.environment.weather.qDirect[0:8760] = ([400] * 20 + [300] * 20 + [200] * 20 + [0] * 20) * 5 + [0] * 8360



        Calculator = EBB.calculator(city_object)
        dict_bes_data = Calculator.assembler()
        print('Dict city data', dict_bes_data)
        for i in range(len(dict_bes_data)):
            city_object, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)

        assert abs(city_object.node[1001]['power_el_chp'][5] - 428) <= 1
        assert abs(city_object.node[1001]['pv_sold'][5] - 0) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][5] - 3600) <= 1
        assert abs(city_object.node[1001]['batt_load'][5] - 3028) <= 1
        assert abs(city_object.node[1001]['batt_unload'][5] - 0) <= 1
        assert abs(city_object.node[1001]['chp_sold'][5] - 0) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][5] - 428) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][15] - 428) <= 1
        assert abs(city_object.node[1001]['pv_sold'][15] - 0) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][15] - 7200) <= 1
        assert abs(city_object.node[1001]['batt_load'][15] - 6628) <= 1
        assert abs(city_object.node[1001]['batt_unload'][15] - 0) <= 1
        assert abs(city_object.node[1001]['chp_sold'][15] - 0) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][15] - 428) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][38] - 428) <= 1
        assert abs(city_object.node[1001]['pv_sold'][38] - 0) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][38] - 5400) <= 1
        assert abs(city_object.node[1001]['batt_load'][38] - 4828) <= 1
        assert abs(city_object.node[1001]['batt_unload'][38] - 0) <= 1
        assert abs(city_object.node[1001]['chp_sold'][38] - 0) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][38] - 428) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][58] - 0) <= 1
        assert abs(city_object.node[1001]['pv_sold'][58] - 0) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][58] - 3600) <= 1
        assert abs(city_object.node[1001]['batt_load'][58] - 2600) <= 1
        assert abs(city_object.node[1001]['batt_unload'][58] - 0) <= 1
        assert abs(city_object.node[1001]['chp_sold'][58] - 0) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][58] - 0) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][68] - 428) <= 1
        assert abs(city_object.node[1001]['pv_sold'][68] - 0) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][68] - 0) <= 1
        assert abs(city_object.node[1001]['batt_load'][68] - 0) <= 1
        assert abs(city_object.node[1001]['batt_unload'][68] - 572) <= 1
        assert abs(city_object.node[1001]['chp_sold'][68] - 0) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][68] - 428) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][70] - 0) <= 1
        assert abs(city_object.node[1001]['pv_sold'][70] - 0) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][70] - 0) <= 1
        assert abs(city_object.node[1001]['batt_load'][70] - 0) <= 1
        assert abs(city_object.node[1001]['batt_unload'][70] - 1000) <= 1
        assert abs(city_object.node[1001]['chp_sold'][70] - 0) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][70] - 0) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][85] - 0) <= 1
        assert abs(city_object.node[1001]['pv_sold'][85] - 0) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][85] - 7200) <= 1
        assert abs(city_object.node[1001]['batt_load'][85] - 6200) <= 1
        assert abs(city_object.node[1001]['batt_unload'][85] - 0) <= 1
        assert abs(city_object.node[1001]['chp_sold'][85] - 0) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][85] - 0) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][108] - 959) <= 1
        assert abs(city_object.node[1001]['pv_sold'][108] - 4400) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][108] - 1000) <= 1
        assert abs(city_object.node[1001]['batt_load'][108] - 0) <= 1
        assert abs(city_object.node[1001]['batt_unload'][108] - 0) <= 1
        assert abs(city_object.node[1001]['chp_sold'][108] - 959) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][108] - 0) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][145] - 959) <= 1
        assert abs(city_object.node[1001]['pv_sold'][145] - 0) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][145] - 0) <= 1
        assert abs(city_object.node[1001]['batt_load'][145] - 0) <= 1
        assert abs(city_object.node[1001]['batt_unload'][145] - 41) <= 1
        assert abs(city_object.node[1001]['chp_sold'][145] - 0) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][145] - 959) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][163] - 959) <= 1
        assert abs(city_object.node[1001]['pv_sold'][163] - 2600) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][163] - 1000) <= 1
        assert abs(city_object.node[1001]['batt_load'][163] - 0) <= 1
        assert abs(city_object.node[1001]['batt_unload'][163] - 0) <= 1
        assert abs(city_object.node[1001]['chp_sold'][163] - 959) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][163] - 0) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][180] - 598) <= 1
        assert abs(city_object.node[1001]['pv_sold'][180] - 4400) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][180] - 1000) <= 1
        assert abs(city_object.node[1001]['batt_load'][180] - 0) <= 1
        assert abs(city_object.node[1001]['batt_unload'][180] - 0) <= 1
        assert abs(city_object.node[1001]['chp_sold'][180] - 598) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][180] - 0) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][205] - 959) <= 1
        assert abs(city_object.node[1001]['pv_sold'][205] - 2600) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][205] - 1000) <= 1
        assert abs(city_object.node[1001]['batt_load'][205] - 0) <= 1
        assert abs(city_object.node[1001]['batt_unload'][205] - 0) <= 1
        assert abs(city_object.node[1001]['chp_sold'][205] - 959) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][205] - 0) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][230] - 959) <= 1
        assert abs(city_object.node[1001]['pv_sold'][230] - 0) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][230] - 0) <= 1
        assert abs(city_object.node[1001]['batt_load'][230] - 0) <= 1
        assert abs(city_object.node[1001]['batt_unload'][230] - 41) <= 1
        assert abs(city_object.node[1001]['chp_sold'][230] - 0) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][230] - 959) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][240] - 959) <= 1
        assert abs(city_object.node[1001]['pv_sold'][240] - 2600) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][240] - 1000) <= 1
        assert abs(city_object.node[1001]['batt_load'][240] - 959) <= 1
        assert abs(city_object.node[1001]['batt_unload'][240] - 0) <= 1
        assert abs(city_object.node[1001]['chp_sold'][240] - 0) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][240] - 959) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][255] - 959) <= 1
        assert abs(city_object.node[1001]['pv_sold'][255] - 6200) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][255] - 1000) <= 1
        assert abs(city_object.node[1001]['batt_load'][255] - 0) <= 1
        assert abs(city_object.node[1001]['batt_unload'][255] - 0) <= 1
        assert abs(city_object.node[1001]['chp_sold'][255] - 959) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][255] - 0) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][280] - 959) <= 1
        assert abs(city_object.node[1001]['pv_sold'][280] - 2600) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][280] - 1000) <= 1
        assert abs(city_object.node[1001]['batt_load'][280] - 0) <= 1
        assert abs(city_object.node[1001]['batt_unload'][280] - 0) <= 1
        assert abs(city_object.node[1001]['chp_sold'][280] - 959) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][280] - 0) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][390] - 959) <= 1
        assert abs(city_object.node[1001]['pv_sold'][390] - 0) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][390] - 0) <= 1
        assert abs(city_object.node[1001]['batt_load'][390] - 0) <= 1
        assert abs(city_object.node[1001]['batt_unload'][390] - 41) <= 1
        assert abs(city_object.node[1001]['chp_sold'][390] - 0) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][390] - 959) <= 1

        assert abs(city_object.node[1001]['power_el_chp'][402] - 0) <= 1
        assert abs(city_object.node[1001]['pv_sold'][402] - 0) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][402] - 0) <= 1
        assert abs(city_object.node[1001]['batt_load'][402] - 0) <= 1
        assert abs(city_object.node[1001]['batt_unload'][402] - 1000) <= 1
        assert abs(city_object.node[1001]['chp_sold'][402] - 0) <= 1
        assert abs(city_object.node[1001]['chp_used_self'][402] - 0) <= 1



        # TODO: check these 2 following assertions

        # assert city_object.node[1001]['entity'].bes.battery.totalSoc[50] <= 73984723.7035
        # assert city_object.node[1001]['entity'].bes.battery.totalSoc[180] <= 197318304.695

        ########################################
        # compare total demand and supplied values
        ########################################
        # calculate total produced heat
        totalQ_produced = sum(city_object.node[1001]['entity'].bes.chp.totalQOutput) / 1000 + sum(
            city_object.node[1001]['entity'].bes.boiler.totalQOutput) / 1000

        # Compare the initial tes Energy with the tes Energy at the end
        deltaT = city_object.node[1001]['entity'].bes.tes.array_temp_storage[8759] - \
                 city_object.node[1001]['entity'].bes.tes.array_temp_storage[0]
        deltaQstorage = city_object.node[1001][
                            'entity'].bes.tes.capacity * deltaT * 4182 / 1000 / 3600  # delta Q storage in kWh

        # Calculate total heat demand
        sph_demand_building = city_object.node[1001]['entity'].get_space_heating_power_curve()
        dhw_demand_building = city_object.node[1001]['entity'].get_dhw_power_curve()
        totalQ_demand = sum(sph_demand_building + dhw_demand_building) / 1000

        # assert total heat energy amount
        assert abs(totalQ_produced - totalQ_demand - deltaQstorage) <= 10

        totalPV = sum(city_object.node[1001]['pv_sold']) / 1000 + sum(city_object.node[1001]['pv_used_self']) / 1000
        PV_supply = sum(city_object.node[1001]['entity'].bes.pv.getPower()) / 1000

        # assert pv electricity energy amount
        assert abs(totalPV - PV_supply) <= 10

        totalCHP = sum(city_object.node[1001]['chp_sold']) / 1000 + sum(city_object.node[1001]['chp_used_self']) / 1000
        CHP_supply = sum(city_object.node[1001]['entity'].bes.chp.totalPOutput) / 1000

        # assert chp electricity energy amount
        assert abs(totalCHP - CHP_supply) <= 10

        eta_load = city_object.node[1001]['entity'].bes.battery.etaCharge
        eta_unload = city_object.node[1001]['entity'].bes.battery.etaDischarge
        eta_selfdischarge = city_object.node[1001]['entity'].bes.battery.selfDischarge
        deltabat2 = city_object.node[1001]['entity'].bes.battery.socInit
        for timestep in range(city_object.environment.timer.timestepsTotal):
            deltabat2 = deltabat2 * (1 - eta_selfdischarge)
            deltabat2 += (city_object.node[1001]['entity'].bes.battery.totalPCharge[timestep] * eta_load -
                          city_object.node[1001]['entity'].bes.battery.totalPDischarge[
                              timestep] / eta_unload) * city_object.environment.timer.timeDiscretization

            assert (deltabat2 - city_object.node[1001]['entity'].bes.battery.totalSoc[timestep]) < 2

        deltabat3 = (sum(city_object.node[1001]['batt_load']) - sum(city_object.node[1001]['batt_unload'])) / 1000
        deltabat4 = (sum(city_object.node[1001]['entity'].bes.battery.totalPCharge) - sum(
            city_object.node[1001]['entity'].bes.battery.totalPDischarge)) / 1000

        # assert delta electricity battery. Assert if different save methods produce equal results
        assert abs(deltabat3 - deltabat4) < 1

        total_el_demand = sum(city_object.node[1001]['entity'].get_electric_power_curve()) / 1000
        if city_object.node[1001]['entity'].bes.hasHeatpump:
            total_el_demand += sum(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in) / 1000
            total_el_demand += sum(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption) / 1000
        el_buy = sum(city_object.node[1001]['electrical demand']) / 1000

        aaa = sum(city_object.node[1001]['electricity_heatpump']) / 1000
        # assert total electricity energy amount
        chp_sold = sum(city_object.node[1001]['chp_sold']) / 1000
        pv_sold = sum(city_object.node[1001]['pv_sold']) / 1000

        assert abs(el_buy + PV_supply + CHP_supply - total_el_demand - chp_sold - pv_sold - deltabat3) < 10

    def test_single_house_electricity_boiler_pv_batt(self):

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

        list_types = ['B']
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
        boiler_q_nominal = [5000]
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
        bat_capacity = [50]
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
                pv_simple = PV.PV(environment=environment, area=list_PV[i], eta=0.9, beta=0)
                bes.addDevice(pv_simple)
                # TODO: eta and beta must be set properly
            if bat_capacity[i] > 0:
                # Create Battery
                capacity = bat_capacity[i]  # 4 * 3600 * 1000  # 4 kWh = 4 * 3600*1000 J
                socInit = 0.5
                selfDischarge = 0
                etaCharge = list_etaCharge[i]  # 0.96
                etaDischarge = list_etaDischarge[i]  # 0.95
                battery = Battery.BatteryExtended(environment=environment, soc_init_ratio=socInit, capacity_kwh=capacity,
                                                  self_discharge=selfDischarge, eta_charge=etaCharge, eta_discharge=etaDischarge)
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

        # check 2
        # city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve = [2000] * 72 + [4000] * 72 + [6050] * 72 + [0] * 8544
        # city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve = ([0]*10+[500] * 100 + [1000] * 100 + [2000] * 100 + [3200] * 100 + [4000]* 100 + [5000] *100 + [7000]*10)*3 +[0] * 6900

        #city_object.node[1001]['entity'].apartments[0].demandSpaceheating.loadcurve = [1000] * 100 + [2000] * 100 + [4000] * 100 + [5000] * 100 + [0] * 8360

        city_object.node[1001]['entity'].apartments[0].power_el.loadcurve = [1000] * 8760
        city_object.environment.weather.tAmbient = [10] * 8760  # for constant HP electrical demand
        # city_object.environment.weather.qDiffuse[0:8760] =  [400] * 30 + [100] * 30 + [0] * 26 + [400] * 4 + [100] * 4 + [0] * 3 + [400] * 11+ [100] * 10 + [0] * 9 + [400] * 3+ [100] * 4 + [0] * 8626
        # city_object.environment.weather.qDirect[0:8760] =   [400] * 30 + [100] * 30 + [0] * 26 + [400] * 4 + [100] * 4 + [0] * 3 + [400] * 11+ [100] * 10 + [0] * 9 + [400] * 3+ [100] * 4 + [0] * 8626

        # city_object.environment.weather.qDiffuse[0:8760] = ([400]*24 + [200] * 24 + [0] * 24) * 3 + [0]*8544
        # city_object.environment.weather.qDirect[0:8760] = ([400]*24 + [200] * 24 + [0] * 24) * 3 + [0]*8544

        city_object.environment.weather.qDiffuse[0:8760] = ([400] * 20 + [300] * 20 + [200] * 20 + [0] * 20) * 5 + [0] * 8360
        city_object.environment.weather.qDirect[0:8760] = ([400] * 20 + [300] * 20 + [200] * 20 + [0] * 20) * 5 + [0] * 8360



        Calculator = EBB.calculator(city_object)
        dict_bes_data = Calculator.assembler()
        print('Dict city data', dict_bes_data)
        for i in range(len(dict_bes_data)):
            city_object, dict_Qlhn, dict_supply = Calculator.eb_balances(dict_bes_data, i)

        assert abs(city_object.node[1001]['pv_sold'][5] - 0) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][5] - 3600) <= 1
        assert abs(city_object.node[1001]['batt_load'][5] - 2600) <= 1
        assert abs(city_object.node[1001]['batt_unload'][5] - 0) <= 1

        assert abs(city_object.node[1001]['pv_sold'][12] - 6200) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][12] - 1000) <= 1
        assert abs(city_object.node[1001]['batt_load'][12] - 0) <= 1
        assert abs(city_object.node[1001]['batt_unload'][12] - 0) <= 1

        assert abs(city_object.node[1001]['pv_sold'][50] - 800) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][50] - 1000) <= 1
        assert abs(city_object.node[1001]['batt_load'][50] - 0) <= 1
        assert abs(city_object.node[1001]['batt_unload'][50] - 0) <= 1

        assert abs(city_object.node[1001]['pv_sold'][70] - 0) <= 1
        assert abs(city_object.node[1001]['pv_used_self'][70] - 0) <= 1
        assert abs(city_object.node[1001]['batt_load'][70] - 0) <= 1
        assert abs(city_object.node[1001]['batt_unload'][70] - 1000) <= 1




        ########################################
        # compare total demand and supplied values
        ########################################


        # Calculate total heat demand
        sph_demand_building = city_object.node[1001]['entity'].get_space_heating_power_curve()
        dhw_demand_building = city_object.node[1001]['entity'].get_dhw_power_curve()
        #totalQ_demand = sum(sph_demand_building + dhw_demand_building) / 1000

        demand = sph_demand_building + dhw_demand_building
        for i in range(len(sph_demand_building)):
            if demand[i] <2500:
                demand[i]=2500
        totalQ_demand = sum(demand) / 1000

        # calculate total produced heat
        totalQ_produced = sum(city_object.node[1001]['entity'].bes.boiler.totalQOutput) / 1000


        # assert total heat energy amount
        assert abs(totalQ_produced - totalQ_demand) <= 10

        totalPV = sum(city_object.node[1001]['pv_sold']) / 1000 + sum(city_object.node[1001]['pv_used_self']) / 1000
        PV_supply = sum(city_object.node[1001]['entity'].bes.pv.getPower()) / 1000

        # assert pv electricity energy amount
        assert abs(totalPV - PV_supply) <= 10

        eta_load = city_object.node[1001]['entity'].bes.battery.etaCharge
        eta_unload = city_object.node[1001]['entity'].bes.battery.etaDischarge
        eta_selfdischarge = city_object.node[1001]['entity'].bes.battery.selfDischarge
        deltabat2 = city_object.node[1001]['entity'].bes.battery.socInit
        for timestep in range(city_object.environment.timer.timestepsTotal):
            deltabat2 = deltabat2 * (1 - eta_selfdischarge)
            deltabat2 += (city_object.node[1001]['entity'].bes.battery.totalPCharge[timestep] * eta_load -
                          city_object.node[1001]['entity'].bes.battery.totalPDischarge[
                              timestep] / eta_unload) * city_object.environment.timer.timeDiscretization

            assert (deltabat2 - city_object.node[1001]['entity'].bes.battery.totalSoc[timestep]) < 2

        deltabat3 = (sum(city_object.node[1001]['batt_load']) - sum(city_object.node[1001]['batt_unload'])) / 1000
        deltabat4 = (sum(city_object.node[1001]['entity'].bes.battery.totalPCharge) - sum(
            city_object.node[1001]['entity'].bes.battery.totalPDischarge)) / 1000

        # assert delta electricity battery. Assert if different save methods produce equal results
        assert abs(deltabat3 - deltabat4) < 1

        total_el_demand = sum(city_object.node[1001]['entity'].get_electric_power_curve()) / 1000
        if city_object.node[1001]['entity'].bes.hasHeatpump:
            total_el_demand += sum(city_object.node[1001]['entity'].bes.heatpump.array_el_power_in) / 1000
            total_el_demand += sum(city_object.node[1001]['entity'].bes.electricalHeater.totalPConsumption) / 1000
        el_buy = sum(city_object.node[1001]['electrical demand']) / 1000

        aaa = sum(city_object.node[1001]['electricity_heatpump']) / 1000
        # assert total electricity energy amount
        pv_sold = sum(city_object.node[1001]['pv_sold']) / 1000

        assert abs(el_buy + PV_supply - total_el_demand - pv_sold - deltabat3) < 10
