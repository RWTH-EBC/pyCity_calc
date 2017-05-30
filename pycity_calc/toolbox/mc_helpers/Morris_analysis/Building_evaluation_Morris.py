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

    # Modification pv roof area

    if ref_building.roof_usabl_pv_area is not None:
        building.roof_usabl_pv_area = building.roof_usabl_pv_area*(1-parameters[2])

    # year of construction and year of modernisation

    if ref_building.mod_year is None:
        building.build_year = parameters[3]

    else:
        building.mod_year = parameters[3]

        if building.mod_year < building.build_year:

            building.build_year = building.mod_year
    print('new modification year {}'.format(building.build_year))

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

        curr_occupants = int(parameters[4])
        print('curr nb occupants', curr_occupants)
        print('ref nb occupants', ref_appart_occupants)
        print()

        temp = ref_el_demand_curve * curr_occupants / ref_appart_occupants
        print('ref annual el dem', ref_annual_el_demand)
        print('annual el dem', ref_annual_el_demand*(1-parameters[5]))

        # parameter 5: user annual electrical consumption
        building.apartments[appart].power_el.loadcurve = temp * (1-parameters[5])
        print('building el curve', building.apartments[appart].power_el.loadcurve)
        print('ref el curve', ref_el_demand_curve)

        # ## Rescaling domestic hot water
        tFlow = parameters[6]
        Tsupply = parameters[7]

        building.apartments[appart].demandDomesticHotWater = \
            DomHotWat.DomesticHotWater(building.environment, tFlow=tFlow, method=2, supplyTemperature=Tsupply,
                                      occupancy=building.apartments[appart].occupancy.occupancy)

        print('DHW', building.apartments[appart].demandDomesticHotWater)

        return building
