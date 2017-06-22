#!/usr/bin/env python
# coding=utf-8

'''
Script to rescale building electrical curve and domestic hot water for Morris analysis

'''

import copy
import numpy as np
import pycity.classes.demand.DomesticHotWater as DomHotWat



def new_evaluation_building(building, parameters):
    """
         Rescale Building of a city

         Parameters
         ----------
         Building : object
             Building object of pycity_calc
         parameters: np array
             new parameters for buildings

         Return : Building
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
    else:
        building.dormer = 0

    # Attic
    if parameters[4]<1:
        building.attic = 0
    elif parameters[4]<2:
        building.attic = 1
    elif parameters[4]<3:
        building.attic = 2
    else:
        building.attic = 3

    # Cellar
    if parameters[5]<1:
        building.cellar = 0
    elif parameters[5]<2:
        building.cellar = 1
    elif parameters[5]<3:
        building.cellar = 2
    else:
        building.cellar = 3

    # Construction type
    if parameters[6]>0:
        building.construction_type = 'heavy'
    else:
        building.construction_type = 'light'




    # ##################################################################
    # ## Loop over apartment
    #  ##################################################################

    for appart in range(len(building.apartments)):

        print('apartment n°:  ', appart)
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
        print()

        temp = ref_el_demand_curve * curr_occupants / ref_appart_occupants
        print('ref annual el dem', ref_annual_el_demand)
        print('annual el dem', ref_annual_el_demand*(1-parameters[8]))

        # parameter 5: user annual electrical consumption
        building.apartments[appart].power_el.loadcurve = temp * (1-parameters[8])
        print('building el curve', building.apartments[appart].power_el.loadcurve)
        print('ref el curve', ref_el_demand_curve)

        # ## Rescaling domestic hot water

        tFlow = parameters[9]
        Tsupply = parameters[10]
        t_diff_ref = ref_building.apartments[appart].demandDomesticHotWater.tFlow - 25

        # stochastic generation of domestic hot water: rescale with new water temperature difference
        # otherwise impact on the sensitivity analysis
        ref_dhw = ref_building.apartments[appart].demandDomesticHotWater.get_power(currentValues=False,
                                                                                   returnTemperature=False)

        building.apartments[appart].demandDomesticHotWater.loadcurve = ref_dhw*(tFlow-Tsupply)/t_diff_ref
        print ('\n new dhw curve generation')
        #print('DHW', building.apartments[appart].demandDomesticHotWater)

        return building
