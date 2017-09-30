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
            Columns:    0: eta_battery_charge
                        1: eta_battery_discharge
                        2: self_discharge_battery
                        3: eta_boiler
                        4: LAL_boiler
                        5: T_max_boiler
                        6: eta_CHP
                        7: T_max_CHP
                        8: LAL_CHP
                        9: eta_EH
                        10: T_max_EH
                        11: LAL_HP
                        12: T_max_HP
                        13: T_sink_HP
                        14: Qualitätsgrad_HP
                        15: eta_PV
                        16: Tnom_PV
                        18: beta_PV
                        19: gamma_PV

        Return :  City : City modified with the new energy systems parameter
        -------

        """
    print('----------------------------- ')
    print('New energy systems generation ')

    #  Save copy

    Cityref = copy.deepcopy(City)
    list_build = Cityref.get_list_build_entity_node_ids()

    # Rescale energy systems traits

    for build in list_build:

        if Cityref.node[build]['entity'].bes.hasBattery == True:

            City.node[build]['entity'].bes.battery.etaCharge = parameters[0]
            City.node[build]['entity'].bes.battery.etaDischarge = parameters[1]
            City.node[build]['entity'].bes.battery.selfDischarge = parameters[2]

        #if Cityref.node[build]['entity'].bes.hasTes == True:
            #print ('new t_max', parameters[3])
            #print ('new tmin', parameters[4])
            #print ('new tinit: ', parameters[7] )
            #print ('new t surrounding', parameters[5])
            #print ('new klosses', parameters[6])
            #City.node[build]['entity'].bes.tes.t_max = parameters[3]
            #City.node[build]['entity'].bes.tes.t_min = parameters[4]
            #City.node[build]['entity'].bes.tes.t_surroundings = parameters[5]
            #City.node[build]['entity'].bes.tes.k_loss = parameters[6]
            #City.node[build]['entity'].bes.tes.t_init = parameters[7]
            #City.node[build]['entity'].bes.tes.capacity = 999999999999999

        if Cityref.node[build]['entity'].bes.hasBoiler == True:
            City.node[build]['entity'].bes.boiler.eta = parameters [3]
            City.node[build]['entity'].bes.boiler.lower_activation_limit = parameters[4]
            City.node[build]['entity'].bes.boiler.t_max = parameters[5]

        if Cityref.node[build]['entity'].bes.hasChp == True:
            City.node[build]['entity'].bes.chp.omega = parameters[6]
            City.node[build]['entity'].bes.chp.t_max = parameters[7]
            City.node[build]['entity'].bes.chp.lower_activation_limit = parameters[8]

        if Cityref.node[build]['entity'].bes.hasElectricalHeater == True:
            City.node[build]['entity'].bes.electricalHeater.eta = parameters [9]
            City.node[build]['entity'].bes.electricalHeater.t_max = parameters[10]

        if Cityref.node[build]['entity'].bes.hasHeatpump == True:
            City.node[build]['entity'].bes.heatpump.lower_activation_limit = parameters[11]
            City.node[build]['entity'].bes.heatpump.t_max = parameters [12]
            City.node[build]['entity'].bes.heatpump.t_sink = parameters [13]
            City.node[build]['entity'].bes.heatpump.quality_grade = parameters [14]

        if Cityref.node[build]['entity'].bes.hasPv == True:
            City.node[build]['entity'].bes.pv.eta = parameters[15]
            City.node[build]['entity'].bes.pv.temperature_nominal = parameters[16]
            #City.node[build]['entity'].bes.pv.alpha = parameters[17]
            City.node[build]['entity'].bes.pv.beta = parameters[17]
            City.node[build]['entity'].bes.pv.gamma = parameters[18]
            #City.node[build]['entity'].bes.pv.tau_alpha = parameters[20]

    print ('End of energy systems reevaluation')
    print('----------------------------- ')


    return City