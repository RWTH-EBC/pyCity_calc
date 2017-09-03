#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
from __future__ import division

import os
import pickle
import warnings

import pycity_calc.simulation.energy_balance.check_eb_requ as check_eb

class EnergyBalanceException(Exception):
    def __init__(self, message):
        """
        Constructor of own Energy Balance Exception

        Parameters
        ----------
        message : str
            Error message
        """

        super().__init__(message)


def calc_build_therm_eb(build, soc_init=0.5, boiler_full_pl=True,
                        eh_full_pl=True, id=None):
    """
    Calculate building thermal energy balance. Requires extended building
    object with loads and thermal energy supply system.

    Parameters
    ----------
    build : object
        Extended building object of pyCity_calc
    soc_init : float, optional
        Factor of relative state of charge of thermal storage (if thermal
        storage is existent)
    boiler_full_pl : bool, optional
        Defines, if boiler should be set to full part load ability
        (default: True)
    eh_full_pl : bool, optional
        Defines, if electrical heater should be set to full part load ability
        (default: True)
    id : int, optional
        Building id (default: None)
    """

    #  Check if building fulfills necessary requirements for energy balance
    #  calculation
    #  #################################################################
    check_eb.check_eb_build_requ(build=build)

    #  Check existent energy systems
    #  #################################################################
    has_boiler = False
    has_chp = False
    has_hp = False
    has_eh = False
    has_tes = False

    if build.bes.hasBoiler is True:
        has_boiler = True

        #  Set pl of boiler (+ warning)
        curr_lal = build.bes.boiler.lowerActivationLimit

        if boiler_full_pl:
            if curr_lal != 0:
                msg = 'Boiler lower activation limit is currently higher ' \
                      'than 0.' \
                      ' Thus, new lower activation limit is set to zero 0.'
                warnings.warn(msg)
                build.bes.boiler.lowerActivationLimit = 0

    if build.bes.hasChp is True:
        has_chp = True

    if build.bes.hasHeatpump is True:
        has_hp = True

    if build.bes.hasElectricalHeater is True:
        has_eh = True

        if eh_full_pl:
            if curr_lal != 0:
                msg = 'EH lower activation limit is currently higher than 0.' \
                      ' Thus, new lower activation limit is set to zero 0.'
                warnings.warn(msg)
                build.bes.electricalHeater.lowerActivationLimit = 0

    if build.bes.hasTes is True:
        has_tes = True

        # Set initial soc to soc_init * soc_max

    #  Get building thermal load curves
    #  #################################################################
    sh_p_array = build.get_space_heating_power_curve()
    dhw_p_array = build.get_dhw_power_curve()

    #  Perform energy balance calculation for different states
    #  #################################################################
    if has_tes:
        #  Energy balance calculation with thermal storage
        #  #################################################################

        pass

    else:  # Has no TES
        #  Run thermal simulation, if no TES is existent (only relevant for
        #  Boiler and EH
        #  #################################################################

        #  Loop over power values
        for i in range(len(sh_p_array)):

            sh_power = sh_p_array[i]
            dhw_power = dhw_p_array[i]
            th_power = sh_power + dhw_power

            #  Remaining th_ power
            th_pow_remain = th_power + 0.0

            #  Try covering power with boiler
            if has_boiler:

                #  Boiler pointer
                boiler = build.bes.boiler

                #  Get nominal boiler power
                q_nom_boi = boiler.qNominal

                if q_nom_boi < th_pow_remain:
                    #  Only cover partial power demand with boiler power
                    boiler.calc_boiler_all_results(control_signal=q_nom_boi,
                                                   time_index=i)
                    th_pow_remain -= q_nom_boi

                else:  #  Cover total thermal power demand with boiler

                    boiler.calc_boiler_all_results(control_signal=th_power,
                                                   time_index=i)
                    th_pow_remain = 0

            #  If not enough, use EH, if existent
            if has_eh:

                #  EH pointer
                eh = build.bes.electricalHeater

                #  Get nominal eh power
                q_nom_eh = eh.qNominal

                if q_nom_eh < th_pow_remain:
                    #  Only cover partial power demand with eh power
                    eh.calc_el_h_all_results(control_signal=q_nom_eh,
                                             time_index=i)
                    th_pow_remain -= q_nom_eh

                else:  #  Cover total thermal power demand with eh

                    eh.calc_el_h_all_results(control_signal=th_pow_remain,
                                             time_index=i)
                    th_pow_remain = 0

            if th_pow_remain > 0:
                msg = 'Could not cover thermal energy power at timestep ' \
                      '' + str(i) + ' at building ' + str(id)
                EnergyBalanceException(msg)

if __name__ == '__main__':

    this_path = os.path.dirname(os.path.abspath(__file__))

    city_name = 'city_clust_simple_with_esys.pkl'

    city_path = os.path.join(this_path, 'input', city_name)

    city = pickle.load(open(city_path, mode='rb'))

    #  Get buiding 1007
    exbuild = city.node[1007]['entity']

    import pycity_calc.energysystems.electricalHeater as elheat

    eh = elheat.ElectricalHeaterExtended(environment=exbuild.environment,
                                         q_nominal=10000)

    exbuild.bes.addDevice(eh)

    calc_build_therm_eb(build=exbuild)

    q_out = exbuild.bes.boiler.totalQOutput
    fuel_in = exbuild.bes.boiler.array_fuel_power
    sh_p_array = exbuild.get_space_heating_power_curve()
    dhw_p_array = exbuild.get_dhw_power_curve()

    import matplotlib.pyplot as plt

    plt.plot(q_out, label='q_out')
    plt.plot(fuel_in, label='fuel in')
    plt.plot(sh_p_array, label='sh power')
    plt.plot(dhw_p_array, label='dhw power')
    plt.legend()
    plt.show()
    plt.close()

