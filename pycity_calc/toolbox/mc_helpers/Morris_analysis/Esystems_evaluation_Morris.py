#!/usr/bin/env python
# coding=utf-8

'''
Script to rescale energy systems for city district modified in order to do the Morris analysis
'''

import copy
import pycity_calc.toolbox.dimensioning.dim_functions as dimfunc


def new_evaluation_esys(City, parameters):
    """
        Rescale energy systems of a city

        Parameters
        ----------
        City : object
            City object of pycity_calc
        parameters: np array
            new parameters for energy systems

        Return : City
        -------

        """

    print('New energy systems generation ')

    #  Save copy

    Cityref = copy.deepcopy(City)
    list_build = Cityref.get_list_build_entity_node_ids()

    # Rescale energy systems traits

    for build in list_build:

        if Cityref.node[build]['entity'].bes.hasBattery == True:
            City.node[build]['entity'].bes.battery.eta_charge = parameters[0]
            City.node[build]['entity'].bes.battery.eta_discharge = parameters[1]
            City.node[build]['entity'].bes.battery.self_discharge = parameters[2]

        if Cityref.node[build]['entity'].bes.hasTes == True:
            City.node[build]['entity'].bes.tes.t_max = parameters[3]
            City.node[build]['entity'].bes.tes.t_min = parameters[4]
            City.node[build]['entity'].bes.tes.t_surroundings = parameters[5]
            City.node[build]['entity'].bes.tes.k_loss = parameters[6]
            City.node[build]['entity'].bes.tes.t_init = parameters[7]

        if Cityref.node[build]['entity'].bes.hasBoiler == True:
            City.node[build]['entity'].bes.boiler.eta = parameters [8]
            City.node[build]['entity'].bes.boiler.lower_activation_limit = parameters[9]
            City.node[build]['entity'].bes.boiler.t_max = parameters[10]

        if Cityref.node[build]['entity'].bes.hasChp == True:
            City.node[build]['entity'].bes.chp.eta = parameters[11]
            City.node[build]['entity'].bes.chp.t_max = parameters[12]
            City.node[build]['entity'].bes.chp.lower_activation_limit = parameters[13]

        if Cityref.node[build]['entity'].bes.hasElectricalHeater == True:
            City.node[build]['entity'].bes.electricalHeater.eta = parameters [14]
            City.node[build]['entity'].bes.electricalHeater.t_max = parameters[15]

        if City.node[build]['entity'].bes.hasHeatpump == True:
            City.node[build]['entity'].bes.heatpump.lower_activation_limit = parameters[16]
            City.node[build]['entity'].bes.heatpump.t_max = parameters [17]
            City.node[build]['entity'].bes.heatpump.t_sink = parameters [18]

        if City.node[build]['entity'].bes.hasPv == True:
            City.node[build]['entity'].bes.pv.eta = parameters[19]
            City.node[build]['entity'].bes.pv.temperature_nominal = parameters[20]
            City.node[build]['entity'].bes.pv.alpha = parameters[21]
            City.node[build]['entity'].bes.pv.beta = parameters[22]
            City.node[build]['entity'].bes.pv.gamma = parameters[23]
            City.node[build]['entity'].bes.pv.tau_alpha = parameters[24]

        #Rescale boiler qNominal to cover all the thermal demand

        boiler_qNominal = City.node[build]['entity'].bes.boiler.qNominal

        demand_building = dimfunc.get_max_power_of_building(City.node[build]['entity'], with_dhw=True)

        if Cityref.node[build]['entity'].bes.hasBoiler == True:

            if demand_building > boiler_qNominal:
                City.node[build]['entity'].bes.boiler.qNominal = \
                    dimfunc.round_esys_size(demand_building, round_up=True)

                print('new boiler capacity kW: ', City.node[build]['entity'].bes.boiler.qNominal/1000)
                print()

    return City