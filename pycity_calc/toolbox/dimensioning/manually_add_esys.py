#!/usr/bin/env python
# coding=utf-8
"""
#401 Script to enable manually dimensioning of energy systems for a city
object
"""
from __future__ import division

import os
import pickle
import copy

import pycity_base.classes.supply.BES as BES
import pycity_base.classes.supply.PV as PV
import pycity_calc.energysystems.boiler as boil
import pycity_calc.energysystems.chp as chpsys
import pycity_calc.energysystems.thermalEnergyStorage as tessys
import pycity_calc.energysystems.heatPumpSimple as hpsys
import pycity_calc.energysystems.electricalHeater as ehsys
import pycity_calc.energysystems.battery as batt


def add_esys_to_city(city, dict_dicts_esys):
    """

    Parameters
    ----------
    city
    dict_dicts_esys

    Returns
    -------
    city_w_esys
    """

    #  Generate copy of city object to prevent modification of original
    #  city object instance
    city_w_esys = copy.deepcopy(city)

    #  Loop over building ids
    for key in dict_dicts_esys.keys():
        build = city_w_esys.nodes[key]['entity']

        #  Generate and add bes
        bes = BES.BES(environment=city_w_esys.environment)
        build.addEntity(bes)

        #  Loop over energy systems
        for esys in dict_dicts_esys[key]:
            if esys == 'bat':
                list_data = dict_dicts_esys[key][esys]
                bat = batt.BatteryExtended(environment=city.environment,
                                           soc_init_ratio=list_data[1],
                                           capacity_kwh=list_data[0])
                #  Add battery
                bes.addDevice(bat)
            if esys == 'boi':
                list_data = dict_dicts_esys[key][esys]
                boi = boil.BoilerExtended(environment=city.environment,
                                          q_nominal=list_data[0] * 1000,
                                          eta=list_data[1])
                #  Add boiler
                bes.addDevice(boi)
            if esys == 'chp':
                list_data = dict_dicts_esys[key][esys]
                chp = chpsys.ChpExtended(environment=city.environment,
                                         q_nominal=list_data[0] * 1000,
                                         eta_total=list_data[1])
                #  Add CHP
                bes.addDevice(chp)
            if esys == 'eh':
                list_data = dict_dicts_esys[key][esys]
                eheater = ehsys.ElectricalHeaterExtended(
                    environment=city.environment,
                    q_nominal=list_data[0] * 1000)
                #  Add eh
                bes.addDevice(eheater)
            if esys == 'hp':
                list_data = dict_dicts_esys[key][esys]
                hp = hpsys.heatPumpSimple(environment=city.environment,
                                          q_nominal=list_data[0] * 1000,
                                          hp_type=list_data[1])
                #  Add HP
                bes.addDevice(hp)
            if esys == 'tes':
                list_data = dict_dicts_esys[key][esys]
                tes = tessys.thermalEnergyStorageExtended(
                    environment=city.environment,
                    capacity=list_data[0],
                    t_init=list_data[1],
                    t_max=list_data[2])
                #  Add TES
                bes.addDevice(tes)
            if esys == 'pv':
                list_data = dict_dicts_esys[key][esys]
                pv = PV.PV(environment=city.environment,
                           area=list_data[0],
                           eta=list_data[1])
                #  Add PV
                bes.addDevice(pv)

    return city_w_esys


def main():
    this_path = os.path.dirname(os.path.abspath(__file__))

    city_name = 'aachen_kronenberg_6.pkl'

    path_city = os.path.join(this_path, 'input', city_name)

    city_save = city_name[:-4] + '_milp_min_cost.pkl'
    path_save = os.path.join(this_path, 'output', city_save)

    city = pickle.load(open(path_city, mode='rb'))

    #  Add initial dict of dicts for energy system params
    dict_dicts_esys = {}

    #  Add energy system to building 1001
    #  #################################################################
    dict_esys = {
        #  boiler [q_nom_kW, eta]
        'boi': [79, 0.95],
        #  PV [area_m2, eta]
        'pv': [43.2, 0.12]
    }

    #  Add dict_esys to dict_dicts_esys
    dict_dicts_esys[1001] = dict_esys
    #  #################################################################

    #  Add energy system to building 1001
    #  #################################################################
    dict_esys = {
        #  boiler [q_nom_kW, eta]
        'boi': [86.8, 0.95],
        #  PV [area_m2, eta]
        'pv': [73.6, 0.12]
    }

    #  Add dict_esys to dict_dicts_esys
    dict_dicts_esys[1002] = dict_esys
    #  #################################################################

    #  Add energy system to building 1001
    #  #################################################################
    dict_esys = {
        #  boiler [q_nom_kW, eta]
        'boi': [109.3, 0.95],
        #  PV [area_m2, eta]
        'pv': [74.4, 0.12]
    }

    #  Add dict_esys to dict_dicts_esys
    dict_dicts_esys[1003] = dict_esys
    #  #################################################################

    #  Add energy system to building 1001
    #  #################################################################
    dict_esys = {
        #  boiler [q_nom_kW, eta]
        'boi': [79.5, 0.95],
        #  PV [area_m2, eta]
        'pv': [66.4, 0.12]
    }

    #  Add dict_esys to dict_dicts_esys
    dict_dicts_esys[1004] = dict_esys
    #  #################################################################

    #  Add energy system to building 1001
    #  #################################################################
    dict_esys = {
        #  boiler [q_nom_kW, eta]
        'boi': [82.2, 0.95],
        #  PV [area_m2, eta]
        'pv': [62.4, 0.12]
    }

    #  Add dict_esys to dict_dicts_esys
    dict_dicts_esys[1005] = dict_esys
    #  #################################################################

    #  Add energy system to building 1001
    #  #################################################################
    dict_esys = {
        #  boiler [q_nom_kW, eta]
        'boi': [111.2, 0.95],
        #  PV [area_m2, eta]
        'pv': [42.4, 0.12]
    }

    #  Add dict_esys to dict_dicts_esys
    dict_dicts_esys[1006] = dict_esys
    #  #################################################################

    #  #################################################################
    #  Add further buildings
    #  .....
    #  .....
    #  #################################################################

    city_w_esys = add_esys_to_city(city=city, dict_dicts_esys=dict_dicts_esys)

    print()

    pickle.dump(city_w_esys, open(path_save, mode='wb'))


if __name__ == '__main__':
    main()
