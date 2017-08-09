#!/usr/bin/env python
# coding=utf-8

'''
Script to rescale building electrical curve and domestic hot water for Morris analysis

'''

import copy
import numpy as np
import pycity_base.classes.Weather as Weather
import pycity_calc.environments.environment as env
import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.market as mark
import pycity_calc.environments.timer as time
import pycity_calc.buildings.building as build_ex
import pycity_base.classes.demand.Apartment as Apartment
import pycity_base.classes.demand.ElectricalDemand as ElectricalDemand
import pycity_base.classes.demand.DomesticHotWater as dhwater
import pycity_base.classes.demand.Occupancy as occ


def new_evaluation_building(building, parameters):
    """
         Rescale Buildings of a city with new parameters

         Parameters
         ----------
         Building : object
             Building object of pycity_calc
         Parameters: list
             new parameters for buildings
             Structure: 0: net_floor_area - percent of modification
                        1: average_height_of_floors - meters
                        2: year_of_modernization - new year of modernisation
                        3: dormer - float [0-2]
                        4: attic - float [0-4]
                        5: cellar - float [0-4]
                        6: construction type - float [-1-1]
                        7: total_number_occupants - float [0-5]
                        8: Annual_el_e_dem - percent of modification
                        9: dhw_Tflow - float - new flow temperature
                        10: dhw_Tsupply - float - new supply temperature

         Return :   Building: object
                    Building Extended object from pycity_calc
         -------

         """

    print('New building generation ')

    #  Save copy

    ref_building = copy.deepcopy(building)

    timestep = ref_building.environment.timer.timeDiscretization

    #  ##################################################################
    #  Rewrite the building parameters
    #  ##################################################################

    # Modification net surface area
    building.net_floor_area = building.net_floor_area * (1 - parameters[0])

    # Average height of floors
    building.height_of_floors = parameters[1]

    # year of construction and year of modernisation

    if ref_building.mod_year is None:
        building.build_year = parameters[2]

    else:
        building.mod_year = parameters[2]

        if building.mod_year < building.build_year:

            building.build_year = building.mod_year
    print('new modification year {}'.format(building.build_year))

    # Dormer
    if parameters[3]>1:
        building.dormer = 1
        print ('building has a dormer')
    else:
        building.dormer = 0
        print ('building has no dormer')

    # Attic
    if parameters[4]<1:
        building.attic = 0
        print ('building has flat roof')
    elif parameters[4]<2:
        building.attic = 1
        print ('building has non heated attic')
    elif parameters[4]<3:
        building.attic = 2
        print ('buildings has partly heated attic')
    else:
        building.attic = 3
        print ('building has heated attic')

    # Cellar
    if parameters[5]<1:
        building.cellar = 0
        print ('building has no cellar')
    elif parameters[5]<2:
        building.cellar = 1
        print('building has non heated cellar')
    elif parameters[5]<3:
        building.cellar = 2
        print('building has partly heated cellar')
    else:
        building.cellar = 3
        print('building has heated cellar')

    # Construction type
    if parameters[6]>0:
        building.construction_type = 'heavy'
        print ('construction type: heavy')
    else:
        building.construction_type = 'light'
        print ('construction type: light')




    # ##################################################################
    # ## Loop over apartment
    #  ##################################################################

    for appart in range(len(building.apartments)):

        print('\napartment n°:  ', appart, '\n')
        # ##  reference values
        ref_appart_occupants = ref_building.apartments[appart].occupancy.number_occupants
        ref_annual_el_demand = np.zeros(timestep)
        ref_el_demand_curve = ref_building.apartments[appart].get_el_power_curve()

        # annual electrical demand for this apartment in kWh
        ref_annual_el_demand = np.sum(ref_el_demand_curve * ref_building.environment.timer.timeDiscretization)/(100*3600)

        # ## Rescale electrical curve (to do: analysis of appliances, light, season_mod)

        curr_occupants = int(parameters[7])
        print('curr nb occupants', curr_occupants)
        print('ref nb occupants', ref_appart_occupants)
        #print()

        temp = ref_el_demand_curve * curr_occupants / ref_appart_occupants
        print('ref annual el dem', ref_annual_el_demand)
        print('annual el dem', ref_annual_el_demand*(1-parameters[8]))

        # parameter 8: user annual electrical consumption
        building.apartments[appart].power_el.loadcurve = temp * (1-parameters[8])
        #print('building el curve', building.apartments[appart].power_el.loadcurve)
        #print('ref el curve', ref_el_demand_curve)

        # ## Rescaling domestic hot water

        tFlow = parameters[9]
        Tsupply = parameters[10]
        t_diff_ref = ref_building.apartments[appart].demandDomesticHotWater.tFlow - 25

        # stochastic generation of domestic hot water: rescale with new water temperature difference
        # otherwise impact on the sensitivity analysis
        ref_dhw = ref_building.apartments[appart].demandDomesticHotWater.get_power(currentValues=False,
                                                                                   returnTemperature=False)

        building.apartments[appart].demandDomesticHotWater.loadcurve = ref_dhw*(tFlow-Tsupply)/t_diff_ref
        #print ('\nNew dhw curve generation')
        #print('DHW', building.apartments[appart].demandDomesticHotWater)

    return building


if __name__ == '__main__':

    # ## Building generation
    # ######################

    #  Define simulation settings
    build_year = 1962  # Year of construction
    mod_year = None  # Year of retrofit
    net_floor_area = 200  # m2
    height_of_floors = 2.8  # m
    nb_of_floors = 2  # m
    num_occ = 3  # Set fix to prevent long run time for multiple new occupancy
    #  and electrical load profiles

    #  #  Create PyCity_Calc environment
    #  ###############################################################

    #  Create extended environment of pycity_calc
    year = 2010
    timestep = 3600  # Timestep in seconds
    location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop
    altitude = 55  # Altitude of Bottrop

    #  ###############################################################

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

    #  #  Create occupancy profile
    #  #####################################################################

    print('Calculate occupancy.\n')
    #  Generate occupancy profile
    occupancy_obj = occ.Occupancy(environment, number_occupants=num_occ)

    print('Finished occupancy calculation.\n')

    # #  Create electrical load
    #  #####################################################################

    print('Calculate el. load.\n')

    el_dem_stochastic = ElectricalDemand.ElectricalDemand(environment,
                               method=2,
                               annualDemand=3000,  # Dummy value
                               do_normalization=True,
                               total_nb_occupants=num_occ,
                               randomizeAppliances=True,
                               lightConfiguration=10,
                               occupancy=occupancy_obj.occupancy[:])

    print('Finished el. load calculation.\n')

    #  # Create dhw load
    #  #####################################################################
    dhw_stochastical = dhwater.DomesticHotWater(environment,
                                 tFlow=60,
                                 thermal=True,
                                 method=2,
                                 supplyTemperature=20,
                                 occupancy=occupancy_obj.occupancy)

    #  #  Create apartment and building object
    #  #####################################################################

    #  Create apartment
    apartment = Apartment.Apartment(environment)

    #  Add demands to apartment
    apartment.addMultipleEntities([el_dem_stochastic, occupancy_obj,
                                   dhw_stochastical])

    #  Create extended building object
    extended_building = build_ex.BuildingExtended(environment,
                                  build_year=build_year,
                                  mod_year=mod_year,
                                  build_type=0,
                                  roof_usabl_pv_area=30,
                                  net_floor_area=net_floor_area,
                                  height_of_floors=height_of_floors,
                                  nb_of_floors=nb_of_floors,
                                  neighbour_buildings=0,
                                  residential_layout=0,
                                  attic=1, cellar=1,
                                  construction_type='heavy',
                                  dormer=1)

    #  Add apartment to extended building
    extended_building.addEntity(entity=apartment)

    # ## New parameters
    # #################
    list_pam = []

    net_floor_area = 0.10
    list_pam.append(net_floor_area)
    average_height_of_floors = 2.7
    list_pam.append(average_height_of_floors)
    year_of_modernization = 1993
    list_pam.append(year_of_modernization)
    dormer = 0
    list_pam.append(dormer)
    attic = 4
    list_pam.append(attic)
    cellar = 4
    list_pam.append(cellar)
    construction_type = 0.4
    list_pam.append(construction_type)
    total_number_occupants = 4
    list_pam.append(total_number_occupants)
    Annual_el_e_dem = 0.3
    list_pam.append(Annual_el_e_dem)
    dhw_Tflow = 60
    list_pam.append(dhw_Tflow)
    dhw_Tsupply = 25
    list_pam.append(dhw_Tsupply)

    print ('new parameters : ', list_pam)



    extended_building = new_evaluation_building(extended_building, list_pam)

    print ('End')
