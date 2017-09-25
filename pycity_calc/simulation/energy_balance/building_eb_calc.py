#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
from __future__ import division

import os
import pickle
import warnings
import numpy as np

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


def get_tes_status(tes, buffer_low, buffer_high):
    """
    Returns tes status:
    1 - No further power input allowed
    2 - Only thermal input of efficient devices (e.g. CHP, HP) allowed
    3 - All devices can provide energy

    Parameters
    ----------
    tes : object
        Thermal energy storage object of pyCity_calc
    buffer_low : float
        Defines factor of relative storage buffer (relative to max state of
        charge), when only CHP and HP are allowed to save energy to tes.
        Below buffer_low * soc_max also boiler and el. heater can be used.
        E.g. 0.1 means 10 % of soc_max.
    buffer_high : float
        Defines factor of relative storage buffer (relative to max state of
        charge), when no further thermal power input into tes is allowed.
        Below buffer_low * soc_max usage of CHP and/or HP is allowed.
        E.g. 0.98 means 98 % of soc_max.

    Returns
    -------
    tes_status : int
        TES status as integer number:
        1 - No further power input allowed
        2 - Only thermal input of efficient devices (e.g. CHP, HP) allowed
        3 - All devices can provide energy
    """

    #  Get current state of charge (soc)
    curr_soc = tes.calc_curr_state_of_charge()

    if curr_soc < buffer_low:
        return 3
    elif curr_soc < buffer_high:
        return 2
    else:
        return 1


def calc_build_therm_eb(build, soc_init=0.5, boiler_full_pl=True,
                        eh_full_pl=True, buffer_low=0.1, buffer_high=0.98,
                        id=None, th_lhn_pow_rem=None):
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
    buffer_low : float, optional
        Defines factor of relative storage buffer (relative to max state of
        charge), when only CHP and HP are allowed to save energy to tes.
        Below buffer_low * soc_max also boiler and el. heater can be used.
        (default: 0.1). E.g. 0.1 means 10 % of soc_max.
    buffer_high : float, optional
        Defines factor of relative storage buffer (relative to max state of
        charge), when no further thermal power input into tes is allowed.
        Below buffer_low * soc_max usage of CHP and/or HP is allowed.
        (default: 0.98). E.g. 0.98 means 98 % of soc_max.
    id : int, optional
        Building id (default: None)
    th_lhn_pow_rem : np.array, optional
        Numpy array with remaining thermal power demand for connected LHN
        network in Watt (default: None). If None, no LHN coverage is required/
        LHN is not connected to building.
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

        if build.bes.hasElectricalHeater is False and \
                        build.get_annual_dhw_demand() > 0:
            msg = 'Building ' + str() + ' does only have HP without EH.' \
                                        ' Thus, it cannot cover hot water' \
                                        ' energy demand, which is larger ' \
                                        'than zero!'
            raise AssertionError(msg)

    if build.bes.hasElectricalHeater is True:
        has_eh = True

        curr_lal = build.bes.electricalHeater.lowerActivationLimit

        if eh_full_pl:
            if curr_lal != 0:
                msg = 'EH lower activation limit is currently higher than 0.' \
                      ' Thus, new lower activation limit is set to zero 0.'
                warnings.warn(msg)
                build.bes.electricalHeater.lowerActivationLimit = 0

    if build.bes.hasTes is True:
        has_tes = True

        # Set initial soc to soc_init * soc_max
        t_min = build.bes.tes.t_min
        t_max = build.bes.tes.tMax

        t_init_new = soc_init * (t_max - t_min) + t_min

        if build.bes.tes.tInit != t_init_new:
            msg = 'Current tes initial temperature is different from ' \
                  'chosen one (via soc_init). The old initial temperature is' \
                  ' ' + str(build.bes.tes.tInit) + ' degree Celsius. The new' \
                                                   ' one is ' \
                                                   '' + str(t_init_new) + '' \
                                                                          ' degree Celsius.'
            warnings.warn(msg)
            build.bes.tes.tInit = t_init_new

    # Get building thermal load curves
    #  #################################################################
    sh_p_array = build.get_space_heating_power_curve()
    dhw_p_array = build.get_dhw_power_curve()

    #  Get remaining LHN thermal power demand, if existent
    if th_lhn_pow_rem is None:
        timestep = build.environment.timer.timeDiscretization

        th_lhn_pow_rem = np.zeros(int(365 * 24 * 3600 / timestep))

    # Perform energy balance calculation for different states
    #  #################################################################
    if has_tes and has_chp and has_hp is False:
        #  Energy balance calculation with thermal storage
        #  Relevant for CHP, boiler and EH, only, as HP cannot cover
        #  complete hot water demand / cannot reach temperature levels
        #  required for hot water demand
        #  #################################################################

        #  Loop over power values
        for i in range(len(sh_p_array)):

            #  Calculate tes status
            #  ##############################################################
            tes_status = get_tes_status(tes=build.bes.tes,
                                        buffer_low=buffer_low,
                                        buffer_high=buffer_high)
            #  TES status as integer number:
            # 1 - No further power input allowed
            # 2 - Only thermal input of efficient devices (CHP, HP) allowed
            # 3 - All devices can provide energy

            #  The following merrit order is defined for thermal power supply
            #  1. CHP
            #  2. TES (tried to be supplied by CHP and HP)
            #  3. Boiler
            #  4. Electrical heater

            #  Get required thermal power values
            sh_power = sh_p_array[i]
            dhw_power = dhw_p_array[i]

            #  Remaining thermal power values
            sh_pow_remain = sh_power + 0.0
            dhw_pow_remain = dhw_power + 0.0

            if tes_status == 1:
                #  #########################################################
                #  Do not load tes any further. Use esys only to supply
                #  thermal power

                if has_chp:
                    #  #####################################################
                    #  Use CHP

                    #  chp pointer
                    chp = build.bes.chp

                    #  Get nominal chp power
                    q_nom_chp = chp.qNominal

                    if (sh_pow_remain + dhw_pow_remain + th_lhn_pow_rem[i]) \
                            >= q_nom_chp:
                        #  Cover part of power with full CHP load
                        chp.th_op_calc_all_results(control_signal=q_nom_chp,
                                                   time_index=i)

                        #  Calculate remaining thermal power
                        if sh_pow_remain - q_nom_chp > 0:
                            sh_pow_remain -= q_nom_chp
                        elif sh_pow_remain == q_nom_chp:
                            sh_pow_remain = 0
                        elif sh_pow_remain - q_nom_chp < 0:

                            if dhw_pow_remain > (q_nom_chp - sh_pow_remain):
                                dhw_pow_remain -= (q_nom_chp - sh_pow_remain)
                                sh_pow_remain = 0
                            elif dhw_pow_remain == q_nom_chp - sh_pow_remain:
                                dhw_pow_remain = 0
                                sh_pow_remain = 0
                            else:
                                th_lhn_pow_rem[i] -= q_nom_chp \
                                                     - sh_pow_remain \
                                                     - dhw_pow_remain
                                dhw_pow_remain = 0
                                sh_pow_remain = 0

                    elif (sh_pow_remain + dhw_pow_remain + th_lhn_pow_rem[i]) \
                            < q_nom_chp:
                        #  Try to use CHP, depending on part load

                        chp_lal = chp.lowerActivationLimit

                        if (sh_pow_remain + dhw_pow_remain
                                + th_lhn_pow_rem[i]) \
                                < chp_lal * q_nom_chp:
                            #  Required power is below part load performance,
                            #  thus, chp cannot be used
                            chp.th_op_calc_all_results(control_signal=0,
                                                       time_index=i)
                        else:
                            #  CHP can operate in part load
                            chp.th_op_calc_all_results(
                                control_signal=sh_pow_remain + dhw_pow_remain +
                                               th_lhn_pow_rem[i],
                                time_index=i)

                            sh_pow_remain = 0
                            dhw_pow_remain = 0
                            th_lhn_pow_rem[i] = 0

                # if has_hp:
                #     #  ##################################################
                #
                #     #  hp pointer
                #     hp = build.bes.heatpump
                #
                #     #  Get nominal hp power
                #     q_nom_hp = hp.qNominal
                #
                #     #  Get heat pump source temperature
                #     if hp.hp_type == 'aw':
                #         #  Use outdoor temperature
                #         temp_source = build.environment.weather.tAmbient[i]
                #     elif hp.hp_type == 'ww':
                #         temp_source = build.environment.temp_ground
                #
                #     if sh_pow_remain >= q_nom_hp:
                #         #  Cover part of power with full HP load
                #         hp.calc_hp_all_results(
                #             control_signal=q_nom_hp,
                #             t_source=temp_source,
                #             time_index=i)
                #
                #         sh_pow_remain -= q_nom_hp
                #
                #     else:
                #         #  sh_pow_remain < q_nom_hp
                #         #  Try using hp in part load
                #
                #         hp_lal = hp.lowerActivationLimit
                #
                #         if sh_pow_remain < hp_lal * q_nom_hp:
                #             #  Required power is below part load performance,
                #             #  thus, hp cannot be used
                #             hp.calc_hp_all_results(
                #                 control_signal=0,
                #                 t_source=temp_source,
                #                 time_index=i)
                #         else:
                #             #  HP can operate in part load
                #             hp.th_op_calc_all_results(
                #                 control_signal=sh_pow_remain,
                #                 time_index=i)
                #
                #             sh_pow_remain = 0


                #  Use TES
                #  #####################################################

                #  TES pointer
                tes = build.bes.tes

                #  Get info about max tes power output (include buffer)
                #  Todo: (1 - buffer_low) only estimation, not desired value
                q_out_max = (1 - buffer_low) * tes.calc_storage_q_out_max()

                t_prior = tes.t_current

                if (sh_pow_remain + dhw_pow_remain + th_lhn_pow_rem[i]) \
                        >= q_out_max:
                    #  Cover part of remaining th. demand with full storage
                    #  load (leave buffer)

                    tes.calc_storage_temp_for_next_timestep(q_in=0,
                                                            q_out=q_out_max,
                                                            t_prior=t_prior,
                                                            t_ambient=None,
                                                            set_new_temperature=True,
                                                            save_res=True,
                                                            time_index=i)

                    #  Calculate remaining thermal power
                    if sh_pow_remain - q_out_max > 0:
                        sh_pow_remain -= q_out_max
                    elif sh_pow_remain == q_out_max:
                        sh_pow_remain = 0
                    elif sh_pow_remain - q_out_max < 0:

                        if dhw_pow_remain > (q_out_max - sh_pow_remain):
                            dhw_pow_remain -= (q_out_max - sh_pow_remain)
                            sh_pow_remain = 0
                        elif dhw_pow_remain == q_out_max - sh_pow_remain:
                            dhw_pow_remain = 0
                            sh_pow_remain = 0
                        else:
                            th_lhn_pow_rem[i] -= q_out_max \
                                                 - sh_pow_remain \
                                                 - dhw_pow_remain
                            dhw_pow_remain = 0
                            sh_pow_remain = 0

                else:
                    #  Cover remaining demand with storage load

                    tes.calc_storage_temp_for_next_timestep(q_in=0,
                                                            q_out=sh_pow_remain +
                                                                  dhw_pow_remain +
                                                                  th_lhn_pow_rem[i],
                                                            t_prior=t_prior,
                                                            t_ambient=None,
                                                            set_new_temperature=True,
                                                            save_res=True,
                                                            time_index=i)

                    sh_pow_remain = 0
                    dhw_pow_remain = 0
                    th_lhn_pow_rem[i] = 0

                if has_boiler:

                    #  boiler pointer
                    boiler = build.bes.boiler

                    #  Get nominal power
                    q_nom_boi = boiler.qNominal

                    #  if sh_pow_remain > 0 or dhw_pow_remain > 0, use boiler
                    if (sh_pow_remain + dhw_pow_remain + th_lhn_pow_rem[i])\
                            >= q_nom_boi:
                        #  Cover part of power with full boiler load
                        boiler.calc_boiler_all_results(
                            control_signal=q_nom_boi,
                            time_index=i)

                        #  Calculate remaining thermal power
                        if sh_pow_remain - q_nom_boi > 0:
                            sh_pow_remain -= q_nom_boi
                        elif sh_pow_remain == q_nom_boi:
                            sh_pow_remain = 0
                        elif sh_pow_remain - q_nom_boi < 0:

                            if dhw_pow_remain > (q_nom_boi - sh_pow_remain):
                                dhw_pow_remain -= (q_nom_boi - sh_pow_remain)
                                sh_pow_remain = 0
                            elif dhw_pow_remain == q_nom_boi - sh_pow_remain:
                                dhw_pow_remain = 0
                                sh_pow_remain = 0
                            else:
                                th_lhn_pow_rem[i] -= q_nom_boi \
                                                     - sh_pow_remain \
                                                     - dhw_pow_remain
                                dhw_pow_remain = 0
                                sh_pow_remain = 0

                    elif (sh_pow_remain + dhw_pow_remain + th_lhn_pow_rem[i]) \
                            < q_nom_boi:
                        #  Use boiler in part load

                        boiler.calc_boiler_all_results(
                            control_signal=(sh_pow_remain
                                            + dhw_pow_remain
                                            + th_lhn_pow_rem[i]),
                            time_index=i)

                        sh_pow_remain = 0
                        dhw_pow_remain = 0
                        th_lhn_pow_rem[i] = 0

                if has_eh:

                    #  if sh_pow_remain > 0 or dhw_pow_remain > 0, use eh

                    #  eh pointer
                    eheater = build.bes.electricalHeater

                    #  Get nominal power
                    q_nom_eh = eheater.qNominal

                    #  if sh_pow_remain > 0 or dhw_pow_remain > 0, use eh
                    if (sh_pow_remain + dhw_pow_remain
                            + th_lhn_pow_rem[i]) >= q_nom_eh:
                        #  Cover part of power with full eh load
                        eheater.calc_el_h_all_results(
                            control_signal=q_nom_eh,
                            time_index=i)

                        #  Calculate remaining thermal power
                        if sh_pow_remain - q_nom_eh > 0:
                            sh_pow_remain -= q_nom_eh
                        elif sh_pow_remain == q_nom_eh:
                            sh_pow_remain = 0
                        elif sh_pow_remain - q_nom_eh < 0:

                            if dhw_pow_remain > (q_nom_eh - sh_pow_remain):
                                dhw_pow_remain -= (q_nom_eh - sh_pow_remain)
                                sh_pow_remain = 0
                            elif dhw_pow_remain == q_nom_eh - sh_pow_remain:
                                dhw_pow_remain = 0
                                sh_pow_remain = 0
                            else:
                                th_lhn_pow_rem[i] -= q_nom_eh \
                                                     - sh_pow_remain \
                                                     - dhw_pow_remain
                                dhw_pow_remain = 0
                                sh_pow_remain = 0

                    elif (sh_pow_remain + dhw_pow_remain
                              + th_lhn_pow_rem[i]) < q_nom_eh:
                        #  Use eh in part load

                        eheater.calc_el_h_all_results(
                            control_signal=(sh_pow_remain + dhw_pow_remain
                                            + th_lhn_pow_rem[i]),
                            time_index=i)

                        sh_pow_remain = 0
                        dhw_pow_remain = 0
                        th_lhn_pow_rem[i] = 0

            elif tes_status == 2:
                #  Tes should be charged with CHP
                #  #########################################################

                #  Dummy value
                q_tes_in = None

                if has_chp:
                    #  #####################################################
                    #  Use CHP

                    #  chp pointer
                    chp = build.bes.chp

                    #  tes pointer
                    tes = build.bes.tes

                    #  Get nominal chp power
                    q_nom_chp = chp.qNominal

                    #  Get maximum possible tes power input
                    q_tes_in_max = tes.calc_storage_q_in_max()

                    if (sh_pow_remain + dhw_pow_remain + q_tes_in_max
                            + th_lhn_pow_rem[i]) \
                            >= q_nom_chp:
                        #  Cover part of power with full CHP load
                        chp.th_op_calc_all_results(control_signal=q_nom_chp,
                                                   time_index=i)

                        #  Calculate remaining thermal power
                        if sh_pow_remain - q_nom_chp > 0:
                            sh_pow_remain -= q_nom_chp
                            q_tes_in = 0

                        elif sh_pow_remain == q_nom_chp:
                            sh_pow_remain = 0
                            q_tes_in = 0

                        elif sh_pow_remain - q_nom_chp < 0:

                            if dhw_pow_remain \
                                    - (q_nom_chp - sh_pow_remain) > 0:
                                dhw_pow_remain -= (q_nom_chp - sh_pow_remain)
                                q_tes_in = 0

                            elif dhw_pow_remain == (q_nom_chp - sh_pow_remain):
                                dhw_pow_remain = 0
                                q_tes_in = 0

                            elif dhw_pow_remain - (q_nom_chp - sh_pow_remain) < 0:

                                if (q_tes_in_max <= q_nom_chp
                                    - sh_pow_remain - dhw_pow_remain):

                                    q_tes_in = q_nom_chp - sh_pow_remain - \
                                               dhw_pow_remain
                                    q_tes_in_remain -= q_tes_in
                                else:
                                    q_tes_in = q_tes_in_max + 0.0
                                    th_lhn_pow_rem[i] -= (q_nom_chp
                                                         - sh_pow_remain
                                                         - dhw_pow_remain
                                                         - q_tes_in_max)
                                    q_tes_in_remain = 0

                                dhw_pow_remain = 0
                            sh_pow_remain = 0

                    elif (sh_pow_remain + dhw_pow_remain + q_tes_in_max
                              + th_lhn_pow_rem[i]) < \
                            q_nom_chp:
                        #  Try to use CHP, depending on part load

                        chp_lal = chp.lowerActivationLimit

                        if ((sh_pow_remain + dhw_pow_remain + q_tes_in_max
                                 + th_lhn_pow_rem[i])
                                < chp_lal * q_nom_chp):
                            #  Required power is below part load performance,
                            #  thus, chp cannot be used
                            chp.th_op_calc_all_results(control_signal=0,
                                                       time_index=i)
                            q_tes_in = 0

                        else:
                            #  CHP can operate in part load
                            chp.th_op_calc_all_results(
                                control_signal=sh_pow_remain
                                               + dhw_pow_remain
                                               + q_tes_in_max
                                               + th_lhn_pow_rem[i],
                                time_index=i)

                            q_tes_in = q_tes_in_max + 0.0
                            q_tes_in_remain = 0

                            sh_pow_remain = 0
                            dhw_pow_remain = 0
                            th_lhn_pow_rem[i] = 0

                if has_boiler:

                    #  boiler pointer
                    boiler = build.bes.boiler

                    #  Get nominal power
                    q_nom_boi = boiler.qNominal

                    #  if sh_pow_remain > 0 or dhw_pow_remain > 0, use boiler
                    if (sh_pow_remain + dhw_pow_remain
                            + th_lhn_pow_rem[i]) >= q_nom_boi:
                        #  Cover part of power with full boiler load
                        boiler.calc_boiler_all_results(
                            control_signal=q_nom_boi,
                            time_index=i)

                        #  Calculate remaining thermal power
                        if sh_pow_remain - q_nom_boi > 0:
                            sh_pow_remain -= q_nom_boi
                        elif sh_pow_remain == q_nom_boi:
                            sh_pow_remain = 0
                        elif sh_pow_remain - q_nom_boi < 0:

                            if dhw_pow_remain > (q_nom_boi - sh_pow_remain):
                                dhw_pow_remain -= (q_nom_boi - sh_pow_remain)
                                sh_pow_remain = 0
                            elif dhw_pow_remain == (q_nom_boi - sh_pow_remain):
                                dhw_pow_remain = 0
                                sh_pow_remain = 0
                            else:
                                th_lhn_pow_rem[i] -= (q_nom_boi
                                                      - sh_pow_remain
                                                      - dhw_pow_remain)
                                dhw_pow_remain = 0
                                sh_pow_remain = 0

                    elif (sh_pow_remain + dhw_pow_remain
                              + th_lhn_pow_rem[i]) < q_nom_boi:
                        #  Use boiler in part load

                        boiler.calc_boiler_all_results(
                            control_signal=(sh_pow_remain
                                            + dhw_pow_remain
                                            + th_lhn_pow_rem[i]),
                            time_index=i)

                        sh_pow_remain = 0
                        dhw_pow_remain = 0
                        th_lhn_pow_rem[i] = 0

                if has_eh:

                    #  if sh_pow_remain > 0 or dhw_pow_remain > 0, use eh

                    #  eh pointer
                    eheater = build.bes.electricalHeater

                    #  Get nominal power
                    q_nom_eh = eheater.qNominal

                    #  if sh_pow_remain > 0 or dhw_pow_remain > 0, use eh
                    if (sh_pow_remain + dhw_pow_remain
                            + th_lhn_pow_rem[i]) >= q_nom_eh:
                        #  Cover part of power with full eh load
                        eheater.calc_el_h_all_results(
                            control_signal=q_nom_eh,
                            time_index=i)

                        #  Calculate remaining thermal power
                        if sh_pow_remain - q_nom_eh > 0:
                            sh_pow_remain -= q_nom_eh
                        elif sh_pow_remain == q_nom_eh:
                            sh_pow_remain = 0
                        elif sh_pow_remain - q_nom_eh < 0:

                            if dhw_pow_remain > (q_nom_eh - sh_pow_remain):
                                dhw_pow_remain -= (q_nom_eh - sh_pow_remain)
                                sh_pow_remain = 0
                            elif dhw_pow_remain == (q_nom_eh - sh_pow_remain):
                                dhw_pow_remain = 0
                                sh_pow_remain = 0
                            else:
                                th_lhn_pow_rem[i] -= (q_nom_eh
                                                      - sh_pow_remain
                                                      - dhw_pow_remain)
                                dhw_pow_remain = 0
                                sh_pow_remain = 0

                    elif (sh_pow_remain + dhw_pow_remain
                              + th_lhn_pow_rem[i]) < q_nom_eh:
                        #  Use eh in part load

                        eheater.calc_el_h_all_results(
                            control_signal=(sh_pow_remain + dhw_pow_remain + th_lhn_pow_rem[i]),
                            time_index=i)

                        sh_pow_remain = 0
                        dhw_pow_remain = 0
                        th_lhn_pow_rem[i] = 0

                # Use tes
                #  ###########################################################
                #  Use/load storage, if possible

                if q_tes_in is None:
                    q_tes_in = 0

                # tes pointer
                tes = build.bes.tes

                #  Get maximum possible tes power output
                q_tes_out_max = tes.calc_storage_q_out_max(q_in=q_tes_in)

                #  Plausibility check
                #  Get maximum possible tes power input
                q_tes_in_max = tes.calc_storage_q_in_max()
                assert q_tes_in_max >= q_tes_in

                temp_prior = tes.t_current

                if sh_pow_remain + dhw_pow_remain > 0:
                    #  Use storage to cover remaining demands
                    q_tes_out = sh_pow_remain + dhw_pow_remain

                else:
                    q_tes_out = 0

                if q_tes_out_max < q_tes_out:
                    msg = 'TES stored energy cannot cover remaining ' \
                          'demand in ' \
                          'building' + str(id) + ' at timestep ' + str(i) + '.'
                    raise EnergyBalanceException(msg)

                # Load storage with q_tes_in
                tes.calc_storage_temp_for_next_timestep(q_in=q_tes_in,
                                                        q_out=q_tes_out,
                                                        t_prior=temp_prior,
                                                        set_new_temperature=True,
                                                        save_res=True,
                                                        time_index=i)

            elif tes_status == 3:
                #  #########################################################
                #  Load tes with every possible device

                #  Dummy value
                q_tes_in = None

                #  tes pointer
                tes = build.bes.tes

                #  Get maximum possible tes power input
                q_tes_in_max = tes.calc_storage_q_in_max()

                q_tes_in_remain = q_tes_in_max + 0.0

                if has_chp:
                    #  #####################################################
                    #  Use CHP

                    #  chp pointer
                    chp = build.bes.chp

                    #  Get nominal chp power
                    q_nom_chp = chp.qNominal

                    if (sh_pow_remain + dhw_pow_remain
                            + q_tes_in_max + th_lhn_pow_rem[i]) \
                            >= q_nom_chp:
                        #  Cover part of power with full CHP load
                        chp.th_op_calc_all_results(control_signal=q_nom_chp,
                                                   time_index=i)

                        #  Calculate remaining thermal power
                        if sh_pow_remain - q_nom_chp > 0:
                            sh_pow_remain -= q_nom_chp
                            q_tes_in = 0

                        elif sh_pow_remain == q_nom_chp:
                            sh_pow_remain = 0
                            q_tes_in = 0

                        elif sh_pow_remain - q_nom_chp < 0:
                            if dhw_pow_remain - (
                                        q_nom_chp - sh_pow_remain) > 0:
                                dhw_pow_remain -= (q_nom_chp - sh_pow_remain)
                                q_tes_in = 0

                            elif dhw_pow_remain == (q_nom_chp - sh_pow_remain):
                                dhw_pow_remain = 0
                                q_tes_in = 0

                            elif dhw_pow_remain - (
                                        q_nom_chp - sh_pow_remain) < 0:

                                if (q_tes_in_max <= q_nom_chp
                                    - sh_pow_remain - dhw_pow_remain):

                                    q_tes_in = q_nom_chp - sh_pow_remain - \
                                               dhw_pow_remain
                                    q_tes_in_remain -= q_tes_in
                                else:
                                    q_tes_in = q_tes_in_max + 0.0
                                    th_lhn_pow_rem[i] -= (q_nom_chp
                                                          - sh_pow_remain
                                                          - dhw_pow_remain
                                                          - q_tes_in_max)
                                    q_tes_in_remain = 0

                                dhw_pow_remain = 0
                            sh_pow_remain = 0

                    elif (sh_pow_remain + dhw_pow_remain
                              + q_tes_in_max + th_lhn_pow_rem[i]) < \
                            q_nom_chp:
                        #  Try to use CHP, depending on part load

                        chp_lal = chp.lowerActivationLimit

                        if ((sh_pow_remain + dhw_pow_remain + q_tes_in_max)
                                < chp_lal * q_nom_chp):
                            #  Required power is below part load performance,
                            #  thus, chp cannot be used
                            chp.th_op_calc_all_results(control_signal=0,
                                                       time_index=i)

                        else:
                            #  CHP can operate in part load
                            chp.th_op_calc_all_results(
                                control_signal=sh_pow_remain
                                               + dhw_pow_remain
                                               + q_tes_in_max
                                               + th_lhn_pow_rem[i],
                                time_index=i)

                            q_tes_in = q_tes_in_max + 0.0

                            sh_pow_remain = 0
                            dhw_pow_remain = 0
                            q_tes_in_remain = 0
                            th_lhn_pow_rem[i] = 0

                if has_boiler:

                    #  boiler pointer
                    boiler = build.bes.boiler

                    #  Get nominal power
                    q_nom_boi = boiler.qNominal

                    #  if sh_pow_remain > 0 or dhw_pow_remain > 0, use boiler
                    if (sh_pow_remain + dhw_pow_remain
                            + q_tes_in_remain + th_lhn_pow_rem[i]) \
                            >= q_nom_boi:
                        #  Cover part of power with full boiler load
                        boiler.calc_boiler_all_results(
                            control_signal=q_nom_boi,
                            time_index=i)

                        #  Calculate remaining thermal power
                        if sh_pow_remain - q_nom_boi > 0:
                            sh_pow_remain -= q_nom_boi

                        elif sh_pow_remain == q_nom_boi:
                            sh_pow_remain = 0

                        elif sh_pow_remain - q_nom_boi < 0:
                            if dhw_pow_remain - \
                                    (q_nom_boi - sh_pow_remain) > 0:
                                dhw_pow_remain -= (q_nom_boi - sh_pow_remain)

                            elif dhw_pow_remain == (q_nom_boi - sh_pow_remain):
                                dhw_pow_remain = 0

                            elif dhw_pow_remain - \
                                    (q_nom_boi - sh_pow_remain) < 0:

                                if q_tes_in is None:
                                    q_tes_in = 0

                                if q_tes_in_remain > (q_nom_boi
                                                          - sh_pow_remain
                                                          - dhw_pow_remain):

                                    # Add boiler power to CHP power to load
                                    #  storage
                                    q_tes_in += q_nom_boi - sh_pow_remain - \
                                                dhw_pow_remain

                                    q_tes_in_remain -= q_nom_boi - \
                                                       sh_pow_remain - \
                                                       dhw_pow_remain
                                elif q_tes_in_remain == (q_nom_boi
                                                          - sh_pow_remain
                                                          - dhw_pow_remain):
                                    q_tes_in += q_tes_in_remain
                                    q_tes_in_remain = 0
                                else:
                                    q_tes_in += q_tes_in_remain
                                    th_lhn_pow_rem[i] -= (q_nom_boi
                                                          - sh_pow_remain
                                                          - dhw_pow_remain
                                                          - q_tes_in_remain)
                                    q_tes_in_remain = 0

                                #  Logic-check
                                assert q_tes_in_remain >= 0

                                dhw_pow_remain = 0

                            sh_pow_remain = 0

                if has_eh:

                    #  if sh_pow_remain > 0 or dhw_pow_remain > 0, use eh

                    #  eh pointer
                    eheater = build.bes.electricalHeater

                    #  Get nominal power
                    q_nom_eh = eheater.qNominal

                    #  if sh_pow_remain > 0 or dhw_pow_remain > 0, use boiler
                    if (sh_pow_remain + dhw_pow_remain + q_tes_in_remain) \
                            >= q_nom_boi:
                        #  Cover part of power with full boiler load
                        eheater.calc_el_h_all_results(
                            control_signal=q_nom_eh,
                            time_index=i)

                        #  Calculate remaining thermal power
                        if sh_pow_remain - q_nom_eh > 0:
                            sh_pow_remain -= q_nom_eh

                        elif sh_pow_remain == q_nom_eh:
                            sh_pow_remain = 0

                        elif sh_pow_remain - q_nom_eh < 0:
                            if dhw_pow_remain - \
                                    (q_nom_eh - sh_pow_remain) > 0:
                                dhw_pow_remain -= (q_nom_eh - sh_pow_remain)

                            elif dhw_pow_remain == (q_nom_eh - sh_pow_remain):
                                dhw_pow_remain = 0

                            elif dhw_pow_remain - \
                                    (q_nom_eh - sh_pow_remain) < 0:

                                if q_tes_in is None:
                                    q_tes_in = 0

                                if q_tes_in_remain > (q_nom_eh
                                                          - sh_pow_remain
                                                          - dhw_pow_remain):

                                    # Add boiler power to CHP power to load
                                    #  storage
                                    q_tes_in += q_nom_eh - sh_pow_remain - \
                                                dhw_pow_remain

                                    q_tes_in_remain -= q_nom_eh - \
                                                       sh_pow_remain - \
                                                       dhw_pow_remain
                                elif q_tes_in_remain == (q_nom_eh
                                                             - sh_pow_remain
                                                             - dhw_pow_remain):
                                    q_tes_in += q_tes_in_remain
                                    q_tes_in_remain = 0
                                else:
                                    q_tes_in += q_tes_in_remain
                                    th_lhn_pow_rem[i] -= (q_nom_eh
                                                          - sh_pow_remain
                                                          - dhw_pow_remain
                                                          - q_tes_in_remain)
                                    q_tes_in_remain = 0

                                # Logic-check
                                assert q_tes_in_remain >= 0

                                dhw_pow_remain = 0

                            sh_pow_remain = 0

                # If uncovered demand, use TES
                if sh_pow_remain > 0 or dhw_pow_remain > 0:
                    #  Use tes to cover demands
                    q_out_requ = sh_pow_remain + dhw_pow_remain

                    q_out_max = tes.calc_storage_q_out_max()

                    if q_out_max < q_out_requ:
                        msg = 'TES stored energy cannot cover remaining ' \
                              'demand in ' \
                              'building' + str(id) + ' at timestep ' + str(
                            i) + '.'
                        raise EnergyBalanceException(msg)
                else:
                    q_out_requ = 0

                temp_prior = tes.t_current

                if q_tes_in is None:
                    q_tes_in = 0

                # Calc. storage energy balance for this timestep
                tes.calc_storage_temp_for_next_timestep(q_in=q_tes_in,
                                                        q_out=q_out_requ,
                                                        t_prior=temp_prior,
                                                        set_new_temperature=True,
                                                        save_res=True,
                                                        time_index=i)

                sh_pow_remain = 0
                dhw_pow_remain = 0

            if sh_pow_remain > 0 or dhw_pow_remain > 0:
                msg = 'Could not solve thermal energy balance in ' \
                      'building' + str(id) + ' at timestep ' + str(i) + '.'
                raise EnergyBalanceException(msg)

    elif has_tes and has_hp:
        #  Use heat pump with thermal storage to cover space heating demand

        #  Loop over power values
        for i in range(len(sh_p_array)):

            #  Calculate tes status
            #  ##############################################################
            tes_status = get_tes_status(tes=build.bes.tes,
                                        buffer_low=buffer_low,
                                        buffer_high=buffer_high)
            #  TES status as integer number:
            # 1 - No further power input allowed
            # 2 - Only thermal input of efficient devices (CHP, HP) allowed
            # 3 - All devices can provide energy

            #  Get required thermal power values
            sh_power = sh_p_array[i]
            dhw_power = dhw_p_array[i]

            #  Remaining thermal power values
            sh_pow_remain = sh_power + 0.0
            dhw_pow_remain = dhw_power + 0.0

            #  hp pointer
            hp = build.bes.heatpump

            #  Get nominal hp power
            q_nom_hp = hp.qNominal

            #  Get heat pump source temperature
            if hp.hp_type == 'aw':
                #  Use outdoor temperature
                temp_source = build.environment.weather.tAmbient[i]
            elif hp.hp_type == 'ww':
                temp_source = build.environment.temp_ground

            # TES pointer
            tes = build.bes.tes

            #  Get maximum possible tes power input
            q_tes_in_max = tes.calc_storage_q_in_max()

            #  Get info about max tes power output (include buffer)
            #  Todo: (1 - buffer_low) only estimation, not desired value
            q_out_max = (1 - buffer_low) * tes.calc_storage_q_out_max()

            #  TES mode 1
            if tes_status == 1:
                # #########################################################
                #  Do not load tes any further. Use esys only to supply
                #  thermal power

                #  Use HP for SH
                #  Use EH for DHW
                #  Use TES for SH, if necessary
                #  Use EH for SH, if necessary
                if sh_pow_remain >= q_nom_hp:
                    #  Cover part of sh power with full HP load
                    hp.calc_hp_all_results(
                        control_signal=q_nom_hp,
                        t_source=temp_source,
                        time_index=i)

                    sh_pow_remain -= q_nom_hp

                else:
                    #  sh_pow_remain < q_nom_hp
                    #  Try using hp in part load

                    hp_lal = hp.lowerActivationLimit

                    if sh_pow_remain < hp_lal * q_nom_hp:
                        #  Required power is below part load performance,
                        #  thus, hp cannot be used
                        hp.calc_hp_all_results(
                            control_signal=0,
                            t_source=temp_source,
                            time_index=i)
                    else:
                        #  HP can operate in part load
                        hp.calc_hp_all_results(
                            control_signal=sh_pow_remain,
                            t_source=temp_source,
                            time_index=i)

                        sh_pow_remain = 0

                # Use TES
                #  #####################################################

                t_prior = tes.t_current

                if sh_pow_remain >= q_out_max:
                    #  Cover part of remaining th. demand with full storage
                    #  load (leave buffer)

                    tes.calc_storage_temp_for_next_timestep(q_in=0,
                                                            q_out=q_out_max,
                                                            t_prior=t_prior,
                                                            t_ambient=None,
                                                            set_new_temperature=True,
                                                            save_res=True,
                                                            time_index=i)

                    #  Calculate remaining thermal power
                    if sh_pow_remain - q_out_max > 0:
                        sh_pow_remain -= q_out_max
                    elif sh_pow_remain == q_out_max:
                        sh_pow_remain = 0

                else:
                    #  Cover remaining demand with storage load

                    tes.calc_storage_temp_for_next_timestep(q_in=0,
                                                            q_out=sh_pow_remain,
                                                            t_prior=t_prior,
                                                            t_ambient=None,
                                                            set_new_temperature=True,
                                                            save_res=True,
                                                            time_index=i)
                    sh_pow_remain = 0

                if has_eh:

                    #  if sh_pow_remain > 0 or dhw_pow_remain > 0, use eh

                    #  eh pointer
                    eheater = build.bes.electricalHeater

                    #  Get nominal power
                    q_nom_eh = eheater.qNominal

                    #  if sh_pow_remain > 0 or dhw_pow_remain > 0, use eh
                    if (sh_pow_remain + dhw_pow_remain) >= q_nom_eh:
                        #  Cover part of power with full eh load
                        eheater.calc_el_h_all_results(
                            control_signal=q_nom_eh,
                            time_index=i)

                        #  Calculate remaining thermal power
                        if sh_pow_remain - q_nom_eh > 0:
                            sh_pow_remain -= q_nom_eh
                        elif sh_pow_remain == q_nom_eh:
                            sh_pow_remain = 0
                        elif sh_pow_remain - q_nom_eh < 0:
                            dhw_pow_remain -= (q_nom_eh - sh_pow_remain)
                            sh_pow_remain = 0

                    elif (sh_pow_remain + dhw_pow_remain) < q_nom_eh:
                        #  Use eh in part load

                        eheater.calc_el_h_all_results(
                            control_signal=(
                                sh_pow_remain + dhw_pow_remain),
                            time_index=i)

                        sh_pow_remain = 0
                        dhw_pow_remain = 0

            # TES mode 2
            elif tes_status == 2:
                #  Use HP for SH and TES
                #  Use EH for DHW
                #  Use EH for SH, if necessary
                #  Use TES for SH, if necessary

                #  Dummy value
                q_tes_in = None

                q_tes_in_remain = q_tes_in_max + 0.0

                #  Use HP
                if sh_pow_remain + q_tes_in_remain >= q_nom_hp:
                    #  Cover part of sh power with full HP load
                    hp.calc_hp_all_results(
                        control_signal=q_nom_hp,
                        t_source=temp_source,
                        time_index=i)

                    if sh_pow_remain > q_nom_hp:
                        sh_pow_remain -= q_nom_hp
                    elif sh_pow_remain == q_nom_hp:
                        sh_pow_remain = 0
                    elif sh_pow_remain < q_nom_hp:
                        q_tes_in = q_nom_hp - sh_pow_remain
                        q_tes_in_remain -= q_tes_in
                        sh_pow_remain = 0

                        assert q_tes_in <= q_tes_in_max

                else:
                    #  sh_pow_remain < q_nom_hp
                    #  Try using hp in part load

                    hp_lal = hp.lowerActivationLimit

                    if sh_pow_remain + q_tes_in_max < hp_lal * q_nom_hp:
                        #  Required power is below part load performance,
                        #  thus, hp cannot be used
                        hp.calc_hp_all_results(
                            control_signal=0,
                            t_source=temp_source,
                            time_index=i)
                    else:
                        #  HP can operate in part load
                        hp.calc_hp_all_results(
                            control_signal=sh_pow_remain + q_tes_in_remain,
                            t_source=temp_source,
                            time_index=i)

                        sh_pow_remain = 0
                        q_tes_in = q_tes_in_remain + 0.0
                        q_tes_in_remain = 0

                # Use tes
                #  ###########################################################
                #  Use/load storage, if possible

                if q_tes_in is None:
                    q_tes_in = 0

                # Get maximum possible tes power output
                q_tes_out_max = tes.calc_storage_q_out_max(q_in=q_tes_in)

                #  Plausibility check
                #  Get maximum possible tes power input
                q_tes_in_max = tes.calc_storage_q_in_max()
                assert q_tes_in_max >= q_tes_in

                temp_prior = tes.t_current

                if sh_pow_remain > 0:
                    #  Use storage to cover remaining demands
                    q_tes_out = sh_pow_remain
                else:
                    q_tes_out = 0

                if q_tes_out_max < q_tes_out:
                    msg = 'TES stored energy cannot cover remaining ' \
                          'demand in ' \
                          'building' + str(id) + ' at timestep ' + str(i) + '.'
                    raise EnergyBalanceException(msg)

                # Load storage with q_tes_in
                tes.calc_storage_temp_for_next_timestep(q_in=q_tes_in,
                                                        q_out=q_tes_out,
                                                        t_prior=temp_prior,
                                                        set_new_temperature=True,
                                                        save_res=True,
                                                        time_index=i)

                if has_eh:

                    #  if sh_pow_remain > 0 or dhw_pow_remain > 0, use eh

                    #  eh pointer
                    eheater = build.bes.electricalHeater

                    #  Get nominal power
                    q_nom_eh = eheater.qNominal

                    #  if sh_pow_remain > 0 or dhw_pow_remain > 0, use eh
                    if (sh_pow_remain + dhw_pow_remain) >= q_nom_eh:
                        #  Cover part of power with full eh load
                        eheater.calc_el_h_all_results(
                            control_signal=q_nom_eh,
                            time_index=i)

                        #  Calculate remaining thermal power
                        if sh_pow_remain - q_nom_eh > 0:
                            sh_pow_remain -= q_nom_eh
                        elif sh_pow_remain == q_nom_eh:
                            sh_pow_remain = 0
                        elif sh_pow_remain - q_nom_eh < 0:
                            dhw_pow_remain -= (q_nom_eh - sh_pow_remain)
                            sh_pow_remain = 0

                    elif (sh_pow_remain + dhw_pow_remain) < q_nom_eh:
                        #  Use eh in part load

                        eheater.calc_el_h_all_results(
                            control_signal=(
                                sh_pow_remain + dhw_pow_remain),
                            time_index=i)

                        sh_pow_remain = 0
                        dhw_pow_remain = 0

            # TES mode 3
            elif tes_status == 3:
                #  Load TES with every possible device
                #  Use HP for SH and TES
                #  Use EH for DHW
                #  Use EH for SH and TES

                #  Dummy value
                q_tes_in = None

                q_tes_in_remain = q_tes_in_max + 0.0

                #  Use HP
                if sh_pow_remain + q_tes_in_max >= q_nom_hp:
                    #  Cover part of sh power with full HP load
                    hp.calc_hp_all_results(
                        control_signal=q_nom_hp,
                        t_source=temp_source,
                        time_index=i)

                    if sh_pow_remain > q_nom_hp:
                        sh_pow_remain -= q_nom_hp
                    elif sh_pow_remain == q_nom_hp:
                        sh_pow_remain = 0
                    elif sh_pow_remain < q_nom_hp:
                        sh_pow_remain = 0
                        q_tes_in = q_nom_hp - sh_pow_remain
                        q_tes_in_remain -= q_tes_in

                else:
                    #  sh_pow_remain < q_nom_hp
                    #  Try using hp in part load

                    hp_lal = hp.lowerActivationLimit

                    if sh_pow_remain + q_tes_in_max < hp_lal * q_nom_hp:
                        #  Required power is below part load performance,
                        #  thus, hp cannot be used
                        hp.calc_hp_all_results(
                            control_signal=0,
                            t_source=temp_source,
                            time_index=i)
                    else:
                        #  HP can operate in part load
                        hp.calc_hp_all_results(
                            control_signal=sh_pow_remain + q_tes_in_max,
                            t_source=temp_source,
                            time_index=i)

                        sh_pow_remain = 0
                        q_tes_in = q_tes_in_max + 0.0
                        q_tes_in_remain -= q_tes_in

                # Use EH
                if has_eh:

                    #  if sh_pow_remain > 0 or dhw_pow_remain > 0, use eh

                    #  eh pointer
                    eheater = build.bes.electricalHeater

                    #  Get nominal power
                    q_nom_eh = eheater.qNominal

                    #  if sh_pow_remain > 0 or dhw_pow_remain > 0, use eh
                    if (sh_pow_remain + dhw_pow_remain + q_tes_in_remain) \
                            >= q_nom_eh:
                        #  Cover part of power with full eh load
                        eheater.calc_el_h_all_results(
                            control_signal=q_nom_eh,
                            time_index=i)

                        #  Calculate remaining thermal power
                        if sh_pow_remain - q_nom_eh > 0:
                            sh_pow_remain -= q_nom_eh
                        elif sh_pow_remain == q_nom_eh:
                            sh_pow_remain = 0
                        elif sh_pow_remain - q_nom_eh < 0:
                            if dhw_pow_remain > q_nom_eh - sh_pow_remain:
                                dhw_pow_remain -= (q_nom_eh - sh_pow_remain)
                                sh_pow_remain = 0
                            elif dhw_pow_remain == q_nom_eh - sh_pow_remain:
                                sh_pow_remain = 0
                                dhw_pow_remain = 0
                            elif dhw_pow_remain < q_nom_eh - sh_pow_remain:
                                q_tes_in_remain -= q_nom_eh - sh_pow_remain \
                                                   - dhw_pow_remain
                                q_tes_in += q_nom_eh - sh_pow_remain \
                                            - dhw_pow_remain

                    elif (sh_pow_remain + dhw_pow_remain + q_tes_in_remain) \
                            < q_nom_eh:
                        #  Use eh in part load

                        eheater.calc_el_h_all_results(
                            control_signal=(
                                sh_pow_remain + dhw_pow_remain + q_tes_in_remain),
                            time_index=i)

                        sh_pow_remain = 0
                        dhw_pow_remain = 0
                        q_tes_in_remain = 0
                        q_tes_in += q_tes_in_remain

                # Use TES
                # If uncovered demand, use TES
                if sh_pow_remain > 0:

                    q_out_max = tes.calc_storage_q_out_max(q_in=q_tes_in)

                    q_out_requ = sh_pow_remain + 0.0

                    if q_out_max < q_out_requ:
                        msg = 'TES stored energy cannot cover remaining ' \
                              'demand in ' \
                              'building' + str(
                            id) + ' at timestep ' + str(
                            i) + '.'
                        raise EnergyBalanceException(msg)
                else:
                    q_out_requ = 0

                temp_prior = tes.t_current

                #  Calc. storage energy balance for this timestep
                tes.calc_storage_temp_for_next_timestep(q_in=q_tes_in,
                                                        q_out=q_out_requ,
                                                        t_prior=temp_prior,
                                                        set_new_temperature=True,
                                                        save_res=True,
                                                        time_index=i)

                sh_pow_remain = 0

            if sh_pow_remain > 0 or dhw_pow_remain > 0:
                msg = 'Could not solve thermal energy balance in ' \
                      'building ' + str(id) + ' at timestep ' + str(i) + '.'
                raise EnergyBalanceException(msg)

    elif has_tes and has_boiler and has_chp is False and has_hp is False:
        #  #################################################################
        #  Run thermal simulation for combination of boiler, EH and TES

        #  Loop over power values
        for i in range(len(sh_p_array)):

            #  Calculate tes status
            #  ##############################################################
            tes_status = get_tes_status(tes=build.bes.tes,
                                        buffer_low=0.85,
                                        buffer_high=buffer_high)

            #  Get required thermal power values
            sh_power = sh_p_array[i]
            dhw_power = dhw_p_array[i]
            th_power = sh_power + dhw_power

            #  Remaining th_ power
            th_pow_remain = th_power + 0.0

            #  Pointer to TES
            tes = build.bes.tes

            q_out_max = tes.calc_storage_q_out_max()
            q_in_max = tes.calc_storage_q_in_max()

            q_tes_in = None

            if tes_status == 1 or tes_status == 2:
                #  Do not charge TES

                #  Try covering power with boiler
                if has_boiler:

                    #  Boiler pointer
                    boiler = build.bes.boiler

                    #  Get nominal boiler power
                    q_nom_boi = boiler.qNominal

                    if q_nom_boi < th_pow_remain + th_lhn_pow_rem[i]:
                        #  Only cover partial power demand with boiler power
                        boiler.calc_boiler_all_results(
                            control_signal=q_nom_boi,
                            time_index=i)

                        if th_pow_remain > q_nom_boi:
                            th_pow_remain -= q_nom_boi
                        elif th_pow_remain == q_nom_boi:
                            th_pow_remain = 0
                        else:
                            th_lhn_pow_rem[i] -= (q_nom_boi - th_pow_remain)
                            th_pow_remain = 0

                    else:  # Cover total thermal power demand with boiler

                        boiler.calc_boiler_all_results(control_signal=th_power+th_lhn_pow_rem[i],
                                                       time_index=i)
                        th_pow_remain = 0
                        th_lhn_pow_rem[i] = 0

                # If not enough, use EH, if existent
                if has_eh:

                    #  EH pointer
                    eh = build.bes.electricalHeater

                    #  Get nominal eh power
                    q_nom_eh = eh.qNominal

                    if q_nom_eh < th_pow_remain + th_lhn_pow_rem[i]:
                        #  Only cover partial power demand with eh power
                        eh.calc_el_h_all_results(control_signal=q_nom_eh,
                                                 time_index=i)
                        if th_pow_remain > q_nom_eh:
                            th_pow_remain -= q_nom_eh
                        elif th_pow_remain == q_nom_eh:
                            th_pow_remain == q_nom_eh
                        else:
                            th_lhn_pow_rem[i] -= (q_nom_eh - th_pow_remain)
                            th_pow_remain = 0

                    else:  # Cover total thermal power demand with eh

                        eh.calc_el_h_all_results(control_signal=th_pow_remain+th_lhn_pow_rem[i],
                                                 time_index=i)
                        th_pow_remain = 0
                        th_lhn_pow_rem[i] = 0

                if th_pow_remain > 0:
                    #  Use TES to cover remaining demand
                    #  Use tes to cover demands
                    q_out_requ = th_pow_remain + 0.0

                    if q_out_max < q_out_requ:
                        msg = 'TES stored energy cannot cover remaining ' \
                              'demand in ' \
                              'building' + str(id) + ' at timestep ' + str(
                            i) + '.'
                        raise EnergyBalanceException(msg)
                else:
                    q_out_requ = 0

                temp_prior = tes.t_current

                if q_tes_in is None:
                    q_tes_in = 0

                # Calc. storage energy balance for this timestep
                tes.calc_storage_temp_for_next_timestep(q_in=q_tes_in,
                                                        q_out=q_out_requ,
                                                        t_prior=temp_prior,
                                                        set_new_temperature=True,
                                                        save_res=True,
                                                        time_index=i)

                if th_pow_remain > 0:
                    msg = 'Could not cover thermal energy power at timestep ' \
                          '' + str(i) + ' at building ' + str(id)
                    EnergyBalanceException(msg)

            elif tes_status == 3:
                # Use boiler and/or EH to load TES

                q_tes_in_remain = q_in_max + 0.0
                q_tes_in = 0

                #  Try covering power with boiler
                if has_boiler:

                    #  Boiler pointer
                    boiler = build.bes.boiler

                    #  Get nominal boiler power
                    q_nom_boi = boiler.qNominal

                    if q_nom_boi < (th_pow_remain
                                        + q_tes_in_remain + th_lhn_pow_rem[i]):
                        #  Only cover partial power demand with boiler power
                        boiler.calc_boiler_all_results(
                            control_signal=q_nom_boi,
                            time_index=i)
                        if th_pow_remain > q_nom_boi:
                            th_pow_remain -= q_nom_boi
                        elif th_pow_remain == q_nom_boi:
                            th_pow_remain = 0
                        else:

                            if q_tes_in_remain > q_nom_boi - th_pow_remain:
                                q_tes_in_remain -= (q_nom_boi - th_pow_remain)
                                q_tes_in += (q_nom_boi - th_pow_remain)
                                th_pow_remain = 0
                            elif q_tes_in_remain == q_nom_boi - th_pow_remain:
                                q_tes_in += q_tes_in_remain
                                q_tes_in_remain = 0
                                th_pow_remain = 0
                            else:
                                th_lhn_pow_rem[i] -= (q_nom_boi - th_pow_remain - q_tes_in_remain)
                                q_tes_in += q_tes_in_remain
                                q_tes_in_remain = 0
                                th_pow_remain = 0

                    else:  # Cover total thermal power demand with boiler

                        boiler.calc_boiler_all_results(
                            control_signal=th_pow_remain
                                           + q_tes_in_remain
                                           + th_lhn_pow_rem[i],
                            time_index=i)
                        th_pow_remain = 0
                        q_tes_in += q_tes_in_remain
                        q_tes_in_remain = 0
                        th_lhn_pow_rem[i] = 0

                # If not enough, use EH, if existent
                if has_eh:

                    #  EH pointer
                    eh = build.bes.electricalHeater

                    #  Get nominal eh power
                    q_nom_eh = eh.qNominal

                    if q_nom_eh < (th_pow_remain
                                       + q_tes_in_remain + th_lhn_pow_rem[i]):
                        #  Only cover partial power demand with boiler power
                        eh.calc_el_h_all_results(
                            control_signal=q_nom_eh,
                            time_index=i)
                        if th_pow_remain > q_nom_eh:
                            th_pow_remain -= q_nom_eh
                        elif th_pow_remain == q_nom_eh:
                            th_pow_remain = 0
                        else:

                            if q_tes_in_remain > (q_nom_eh - th_pow_remain):
                                q_tes_in_remain -= (q_nom_eh - th_pow_remain)
                                q_tes_in += (q_nom_eh - th_pow_remain)
                                th_pow_remain = 0
                            elif q_tes_in_remain == (q_nom_eh - th_pow_remain):
                                q_tes_in += q_tes_in_remain
                                q_tes_in_remain = 0
                                th_pow_remain = 0
                            else:
                                th_lhn_pow_rem[i] -= (q_nom_eh
                                                      - th_pow_remain
                                                      - q_tes_in_remain)
                                q_tes_in += q_tes_in_remain
                                q_tes_in_remain = 0
                                th_pow_remain = 0

                    else:  # Cover total thermal power demand with boiler

                        eh.calc_el_h_all_results(
                            control_signal=th_pow_remain
                                           + q_tes_in_remain
                                           + th_lhn_pow_rem[i],
                            time_index=i)
                        th_pow_remain = 0
                        q_tes_in += q_tes_in_remain
                        q_tes_in_remain = 0
                        th_lhn_pow_rem[i] = 0

                tes = build.bes.tes

                if th_pow_remain > 0:
                    #  Use TES to cover remaining demand
                    #  Use tes to cover demands
                    q_out_requ = th_pow_remain + 0.0

                    q_out_max = tes.calc_storage_q_out_max(q_in=q_tes_in)

                    if q_out_max < q_out_requ:
                        msg = 'TES stored energy cannot cover remaining ' \
                              'demand in ' \
                              'building' + str(id) + ' at timestep ' + str(
                            i) + '.'
                        raise EnergyBalanceException(msg)
                else:
                    q_out_requ = 0

                temp_prior = tes.t_current

                if q_tes_in is None:
                    q_tes_in = 0

                # Calc. storage energy balance for this timestep
                tes.calc_storage_temp_for_next_timestep(q_in=q_tes_in,
                                                        q_out=q_out_requ,
                                                        t_prior=temp_prior,
                                                        set_new_temperature=True,
                                                        save_res=True,
                                                        time_index=i)

                if th_pow_remain > 0:
                    msg = 'Could not cover thermal energy power at timestep ' \
                          '' + str(i) + ' at building ' + str(id)
                    EnergyBalanceException(msg)


    elif has_tes is False and has_hp is False:  # Has no TES
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

                else:  # Cover total thermal power demand with boiler

                    boiler.calc_boiler_all_results(control_signal=th_power,
                                                   time_index=i)
                    th_pow_remain = 0

            # If not enough, use EH, if existent
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

                else:  # Cover total thermal power demand with eh

                    eh.calc_el_h_all_results(control_signal=th_pow_remain,
                                             time_index=i)
                    th_pow_remain = 0

            if th_pow_remain > 0:
                msg = 'Could not cover thermal energy power at timestep ' \
                      '' + str(i) + ' at building ' + str(id)
                EnergyBalanceException(msg)


def calc_build_el_eb(build, use_chp=True, use_pv=True, has_deg=False):
    """
    Calculate building electric energy balance.

    Parameters
    ----------
    build : object
        Extended building ob pyCity_calc
    use_chp : bool, optional
        Defines, if CHP power is self consumed (default: True). If False,
        has to feed all CHP el. power into the grid
    use_pv : bool, optional
        Defines
    has_deg : bool, optional
        Defines, if building is connected to deg (default: False)

    Returns
    -------
    dict_el_eb_res : dict
        Dictionary with results of electric energy balance
    """

    if use_chp is False:
        warnings.warn('use_chp==False has not been implemented, yet!')
    if use_pv is False:
        warnings.warn('use_pv==False has not been implemented, yet!')

    # Check building esys

    #  Pointer to bes
    bes = build.bes

    has_bat = False
    has_chp = False
    has_eh = False
    has_hp = False
    has_pv = False

    if bes.hasBattery:
        has_bat = True
    if bes.hasChp:
        has_chp = True
    if bes.hasElectricalHeater:
        has_eh = True
    if bes.hasHeatpump:
        has_hp = True
    if bes.hasPv:
        has_pv = True

        pv_gen_array = build.bes.pv.getPower(currentValues=False,
                                             updatePower=True)

    # Get electric power value
    el_pow_array = build.get_electric_power_curve()

    #  Initialize results_dict
    dict_el_eb_res = {}

    #  Initial result arrays
    pv_self = np.zeros(len(el_pow_array))
    pv_self_dem = np.zeros(len(el_pow_array))
    pv_self_hp = np.zeros(len(el_pow_array))
    pv_self_eh = np.zeros(len(el_pow_array))
    pv_self_bat = np.zeros(len(el_pow_array))
    pv_feed = np.zeros(len(el_pow_array))

    chp_self = np.zeros(len(el_pow_array))
    chp_self_dem = np.zeros(len(el_pow_array))
    chp_self_hp = np.zeros(len(el_pow_array))
    chp_self_eh = np.zeros(len(el_pow_array))
    chp_self_bat = np.zeros(len(el_pow_array))
    chp_feed = np.zeros(len(el_pow_array))

    bat_out_dem = np.zeros(len(el_pow_array))
    bat_out_hp = np.zeros(len(el_pow_array))
    bat_out_eh = np.zeros(len(el_pow_array))

    grid_import_dem = np.zeros(len(el_pow_array))
    grid_import_hp = np.zeros(len(el_pow_array))
    grid_import_eh = np.zeros(len(el_pow_array))

    #  Loop over power values
    for i in range(len(el_pow_array)):

        p_el = el_pow_array[i]
        p_el_remain = p_el + 0.0

        #  Dummy values
        p_el_eh_remain = 0
        p_el_hp_remain = 0
        p_el_chp_remain = 0
        p_pv_remain = 0

        #  Get remaining power, depending on system
        if has_pv:
            p_pv = pv_gen_array[i]
            p_pv_remain = p_pv + 0.0
        if has_hp:
            #  Get el. power demand of heat pump
            p_el_hp = build.bes.heatpump.array_el_power_in[i]
            p_el_hp_remain = p_el_hp + 0.0
        if has_eh:
            #  Get el. power demand of heat pump
            p_el_eh = build.bes.electricalHeater.totalPConsumption[i]
            p_el_eh_remain = p_el_eh + 0.0
        if has_chp:
            p_el_chp = build.bes.chp.totalPOutput[i]
            p_el_chp_remain = p_el_chp + 0.0

        # TODO: Erase later
        assert p_el_remain >= 0
        assert p_el_chp_remain >= 0

        #  1. Use PV electric energy
        if has_pv:

            #  El. demand
            if p_pv_remain >= p_el_remain:
                #  Cover complete el. demand with PV power
                p_pv_remain -= p_el_remain
                pv_self[i] += p_el_remain
                pv_self_dem[i] += p_el_remain
                p_el_remain = 0
            else:
                #  Cover part of el. power with PV power
                p_el_remain -= p_pv_remain
                pv_self[i] += p_pv_remain
                pv_self_dem[i] += p_pv_remain
                p_pv_remain = 0

            # HP
            if has_hp:

                if p_pv_remain >= p_el_hp_remain:
                    #  Cover complete HP demand with PV power
                    p_pv_remain -= p_el_hp_remain
                    pv_self[i] += p_el_hp_remain
                    pv_self_hp[i] += p_el_hp_remain
                    p_el_hp_remain = 0
                else:
                    #  Cover part of HP power with PV power
                    p_el_hp_remain -= p_pv_remain
                    pv_self[i] += p_pv_remain
                    pv_self_hp[i] += p_pv_remain
                    p_pv_remain = 0

            # EH
            if has_eh:

                if p_pv_remain >= p_el_eh_remain:
                    #  Cover complete EH demand with PV power
                    p_pv_remain -= p_el_eh_remain
                    pv_self[i] += p_el_eh_remain
                    pv_self_eh[i] += p_el_eh_remain
                    p_el_eh_remain = 0
                else:
                    #  Cover part of EH power with PV power
                    p_el_eh_remain -= p_pv_remain
                    pv_self[i] += p_pv_remain
                    pv_self_eh[i] += p_pv_remain
                    p_pv_remain = 0

        # TODO: Erase later
        assert p_el_remain >= 0
        assert p_el_chp_remain >= 0

        #  2. Use CHP electric energy
        if has_chp:

            #  El. demand
            if p_el_chp_remain >= p_el_remain:
                #  Cover complete el. demand with CHP power
                p_el_chp_remain -= p_el_remain
                chp_self[i] += p_el_remain
                chp_self_dem[i] += p_el_remain
                p_el_remain = 0
            else:
                #  Cover part of el. power with CHP power
                p_el_remain -= p_el_chp_remain
                chp_self[i] += p_el_chp_remain
                chp_self_dem[i] += p_el_chp_remain
                p_el_chp_remain = 0

            # HP
            if has_hp:

                if p_el_chp_remain >= p_el_hp_remain:
                    #  Cover complete HP demand with CHP power
                    p_el_chp_remain -= p_el_hp_remain
                    chp_self[i] += p_el_hp_remain
                    chp_self_hp[i] += p_el_hp_remain
                    p_el_hp_remain = 0
                else:
                    #  Cover part of HP power with CHP power
                    p_el_hp_remain -= p_el_chp_remain
                    chp_self[i] += p_el_chp_remain
                    chp_self_hp[i] += p_el_chp_remain
                    p_el_chp_remain = 0

            # EH
            if has_eh:

                if p_el_chp_remain >= p_el_eh_remain:
                    #  Cover complete EH demand with CHP power
                    p_el_chp_remain -= p_el_eh_remain
                    chp_self[i] += p_el_eh_remain
                    chp_self_eh[i] += p_el_eh_remain
                    p_el_eh_remain = 0
                else:
                    #  Cover part of EH power with CHP power
                    p_el_eh_remain -= p_el_chp_remain
                    chp_self[i] += p_el_chp_remain
                    chp_self_eh[i] += p_el_chp_remain
                    p_el_chp_remain = 0

        # TODO: Erase later
        assert p_el_remain >= 0
        assert p_el_chp_remain >= 0

        #  Bat
        if has_bat:

            #  Try to feed remaining el. power (PV and CHP) with battery

            #  Try to cover remaining el. power demand (building, HP, EH)
            #  with battery

            #  Battery pointer
            bat = build.bes.battery

            #  Initial values
            p_bat_charge = 0
            p_bat_discharge = 0

            #  Maximum charging power
            p_bat_charge_max = bat.calc_battery_max_p_el_in()
            p_bat_charge_remain = p_bat_charge_max + 0.0

            #  Maximum discharging power
            p_bat_disch_max = bat.calc_battery_max_p_el_out()
            p_bat_disch_remain = p_bat_disch_max + 0.0

            if has_pv:

                if p_pv_remain > 0:

                    if p_pv_remain >= p_bat_charge_remain:
                        #  Fully charge battery
                        p_pv_remain -= p_bat_charge_remain
                        pv_self[i] += p_bat_charge_remain
                        pv_self_bat[i] += p_bat_charge_remain
                        p_bat_charge += p_bat_charge_remain
                        p_bat_charge_remain = 0
                    else:
                        #  Partially charge battery
                        p_bat_charge_remain -= p_pv_remain
                        pv_self[i] += p_pv_remain
                        pv_self_bat[i] += p_pv_remain
                        p_bat_charge += p_pv_remain
                        p_pv_remain = 0

            if has_chp:

                if p_el_chp_remain > 0:

                    if p_el_chp_remain >= p_bat_charge_remain:
                        #  Fully charge battery
                        p_el_chp_remain -= p_bat_charge_remain
                        chp_self[i] += p_bat_charge_remain
                        chp_self_bat[i] += p_bat_charge_remain
                        p_bat_charge += p_bat_charge_remain
                        p_bat_charge_remain = 0
                    else:
                        #  Partially charge battery
                        p_bat_charge_remain -= p_el_chp_remain
                        chp_self[i] += p_el_chp_remain
                        chp_self_bat[i] += p_el_chp_remain
                        p_bat_charge += p_el_chp_remain
                        p_el_chp_remain = 0

                    assert p_el_chp_remain >= 0

            if p_el_remain > 0:

                if p_el_remain >= p_bat_disch_remain:
                    #  Fully uncharge battery
                    p_el_remain -= p_bat_disch_remain
                    p_bat_discharge += p_bat_disch_remain
                    bat_out_dem[i] += p_bat_disch_remain
                    p_bat_disch_remain = 0
                else:
                    #  Partially discharge battery
                    p_bat_disch_remain -= p_el_remain
                    p_bat_discharge += p_el_remain
                    bat_out_dem[i] += p_el_remain
                    p_el_remain = 0

            if has_hp:

                if p_el_hp_remain > 0:

                    if p_el_hp_remain >= p_bat_disch_remain:
                        #  Fully uncharge battery
                        p_el_hp_remain -= p_bat_disch_remain
                        p_bat_discharge += p_bat_disch_remain
                        bat_out_hp[i] += p_bat_disch_remain
                        p_bat_disch_remain = 0
                    else:
                        #  Partially discharge battery
                        p_bat_disch_remain -= p_el_hp_remain
                        p_bat_discharge += p_el_hp_remain
                        bat_out_hp[i] += p_el_hp_remain
                        p_el_hp_remain = 0

            if has_eh:

                if p_el_eh_remain > 0:

                    if p_el_eh_remain >= p_bat_disch_remain:
                        #  Fully uncharge battery
                        p_el_eh_remain -= p_bat_disch_remain
                        p_bat_discharge += p_bat_disch_remain
                        bat_out_eh[i] += p_bat_disch_remain
                        p_bat_disch_remain = 0
                    else:
                        #  Partially discharge battery
                        p_bat_disch_remain -= p_el_eh_remain
                        p_bat_discharge += p_el_eh_remain
                        bat_out_eh[i] += p_el_eh_remain
                        p_el_eh_remain = 0

            # Logic checks
            assert p_bat_charge <= p_bat_charge_max
            assert p_bat_discharge <= p_bat_disch_max

            #  Use battery
            bat.calc_battery_soc_next_timestep(p_el_in=p_bat_charge,
                                               p_el_out=p_bat_discharge,
                                               save_res=True,
                                               time_index=i)

        # TODO: Erase later
        assert p_el_remain >= 0
        assert p_el_chp_remain >= 0

        #  DEG
        if has_deg:
            warnings.warn('has_deg has not been implemented, yet!')
            pass

        # Grid
        #  Import remaining el. power from grid
        grid_import_dem[i] += p_el_remain
        p_el_remain = 0

        if has_hp:
            grid_import_hp[i] += p_el_hp_remain
            p_el_hp_remain = 0
        if has_eh:
            grid_import_eh[i] += p_el_eh_remain
            p_el_eh_remain = 0

        if has_pv:
            pv_feed[i] += p_pv_remain
            p_pv_remain = 0
        if has_chp:
            chp_feed[i] += p_el_chp_remain
            p_el_chp_remain = 0

    # Add to results dict
    dict_el_eb_res['pv_self'] = pv_self
    dict_el_eb_res['pv_feed'] = pv_feed

    dict_el_eb_res['pv_self_dem'] = pv_self_dem
    dict_el_eb_res['pv_self_hp'] = pv_self_hp
    dict_el_eb_res['pv_self_eh'] = pv_self_eh
    dict_el_eb_res['pv_self_bat'] = pv_self_bat

    dict_el_eb_res['chp_self'] = chp_self
    dict_el_eb_res['chp_feed'] = chp_feed

    dict_el_eb_res['chp_self_dem'] = chp_self_dem
    dict_el_eb_res['chp_self_hp'] = chp_self_hp
    dict_el_eb_res['chp_self_eh'] = chp_self_eh
    dict_el_eb_res['chp_self_bat'] = chp_self_bat

    dict_el_eb_res['grid_import_dem'] = grid_import_dem
    dict_el_eb_res['grid_import_hp'] = grid_import_hp
    dict_el_eb_res['grid_import_eh'] = grid_import_eh

    dict_el_eb_res['bat_out_dem'] = bat_out_dem
    dict_el_eb_res['bat_out_hp'] = bat_out_hp
    dict_el_eb_res['bat_out_eh'] = bat_out_eh

    #  Add dict to building
    build.dict_el_eb_res = dict_el_eb_res

    return dict_el_eb_res


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    import pycity_calc.visualization.city_visual as citvis
    import pycity_calc.energysystems.electricalHeater as elheat

    #  Load city
    #  ####################################################################
    this_path = os.path.dirname(os.path.abspath(__file__))

    city_name = 'city_clust_simple_with_esys.pkl'

    city_path = os.path.join(this_path, 'input', city_name)

    city = pickle.load(open(city_path, mode='rb'))
    #  ####################################################################

    #  Uncomment, if you would like to deactivate plotting)
    citvis.plot_city_district(city=city, plot_esys=True, plot_lhn=True,
                              plot_deg=True)

    timestep = city.environment.timer.timeDiscretization

    #  ####################################################################
    #  Get buiding 1007 (boiler, only)
    #  Add EH to test energy balance for boiler and eh without tes
    id = 1007
    exbuild = city.node[id]['entity']

    eh = elheat.ElectricalHeaterExtended(environment=exbuild.environment,
                                         q_nominal=10000)

    exbuild.bes.addDevice(eh)

    #  Calculate thermal energy balance
    calc_build_therm_eb(build=exbuild, id=id)

    #  Calculate electric energy balance
    calc_build_el_eb(build=exbuild)

    q_out = exbuild.bes.boiler.totalQOutput
    fuel_in = exbuild.bes.boiler.array_fuel_power
    sh_p_array = exbuild.get_space_heating_power_curve()
    dhw_p_array = exbuild.get_dhw_power_curve()

    plt.plot(q_out, label='q_out')
    plt.plot(fuel_in, label='fuel in')
    plt.plot(sh_p_array, label='sh power')
    plt.plot(dhw_p_array, label='dhw power')
    plt.legend()
    plt.show()
    plt.close()
    #  ####################################################################

    #  ####################################################################
    #  Get buiding 1001 (CHP, boiler, tes)
    #  Add EH to test energy balance for CHP, boiler, EH with TES
    id = 1001
    exbuild = city.node[id]['entity']

    # eh = elheat.ElectricalHeaterExtended(environment=exbuild.environment,
    #                                      q_nominal=10000)
    #
    # exbuild.bes.addDevice(eh)

    #  Calculate thermal energy balance
    calc_build_therm_eb(build=exbuild, id=id)

    #  Calculate electric energy balance
    calc_build_el_eb(build=exbuild)

    #  Get space heating results
    sh_p_array = exbuild.get_space_heating_power_curve()
    dhw_p_array = exbuild.get_dhw_power_curve()

    #  Get boiler results
    q_out = exbuild.bes.boiler.totalQOutput
    fuel_in = exbuild.bes.boiler.array_fuel_power

    #  Get CHP results
    q_chp_out = exbuild.bes.chp.totalQOutput
    p_el_chp_out = exbuild.bes.chp.totalPOutput
    fuel_chp_in = exbuild.bes.chp.array_fuel_power

    tes_temp = exbuild.bes.tes.array_temp_storage

    #  Checks
    sh_net_energy = sum(sh_p_array) * timestep / (1000 * 3600)  # in kWh
    dhw_net_energy = sum(dhw_p_array) * timestep / (1000 * 3600)  # in kWh
    boil_th_energy = sum(q_out) * timestep / (1000 * 3600)  # in kWh
    chp_th_energy = sum(q_chp_out) * timestep / (1000 * 3600)  # in kWh
    fuel_boiler_energy = sum(fuel_in) * timestep / (1000 * 3600)  # in kWh
    fuel_chp_energy = sum(fuel_chp_in) * timestep / (1000 * 3600)  # in kWh
    chp_el_energy = sum(p_el_chp_out) * timestep / (1000 * 3600)  # in kWh

    print('Space heating demand in kWh:')
    print(round(sh_net_energy, 0))
    print('DHW heating demand in kWh:')
    print(round(dhw_net_energy, 0))
    print()

    print('Boiler thermal energy output in kWh:')
    print(round(boil_th_energy, 0))
    print('CHP thermal energy output in kWh:')
    print(round(chp_th_energy, 0))
    print()

    print('Boiler fuel energy demand in kWh:')
    print(round(fuel_boiler_energy, 0))
    print('CHP fuel energy demand in kWh:')
    print(round(fuel_chp_energy, 0))
    print()

    print('CHP fuel energy demand in kWh:')
    print(round(chp_el_energy, 0))

    assert sh_net_energy + dhw_net_energy <= boil_th_energy + chp_th_energy

    fig = plt.figure()

    plt.subplot(5, 1, 1)
    plt.plot(sh_p_array, label='Space heat. in Watt')
    plt.plot(dhw_p_array, label='Hot water power in Watt')
    plt.legend()

    plt.subplot(5, 1, 2)
    plt.plot(q_out, label='Boiler th. power in Watt')
    plt.plot(fuel_in, label='Boiler fuel power in Watt')
    plt.legend()

    plt.subplot(5, 1, 3)
    plt.plot(q_chp_out, label='CHP th. power in Watt')
    plt.plot(fuel_chp_in, label='CHP fuel power in Watt')
    plt.legend()

    plt.subplot(5, 1, 4)
    plt.plot(p_el_chp_out, label='CHP el. power in Watt')
    plt.legend()

    plt.subplot(5, 1, 5)
    plt.plot(tes_temp, label='Storage temp. in degree C')
    plt.legend()

    plt.ylabel('Time in hours')

    plt.show()
    plt.close()
    #  ####################################################################

    # #  ####################################################################
    #  Extract building 1008 (HP, EH, PV and TES)
    id = 1008
    exbuild = city.node[id]['entity']

    #  Modify size of electrical heater
    exbuild.bes.electricalHeater.qNominal *= 1.5

    #  Modify tes
    exbuild.bes.tes.tMax = 45
    print('Capacity of TES in kg: ', exbuild.bes.tes.capacity)

    #  Calculate thermal energy balance
    calc_build_therm_eb(build=exbuild, id=id)

    #  Calculate electric energy balance
    calc_build_el_eb(build=exbuild)

    #  Get space heating results
    sh_p_array = exbuild.get_space_heating_power_curve()
    dhw_p_array = exbuild.get_dhw_power_curve()

    q_hp_out = exbuild.bes.heatpump.totalQOutput
    el_hp_in = exbuild.bes.heatpump.array_el_power_in

    q_eh_out = exbuild.bes.electricalHeater.totalQOutput
    el_eh_in = exbuild.bes.electricalHeater.totalPConsumption

    tes_temp = exbuild.bes.tes.array_temp_storage

    sh_en = sum(sh_p_array) * timestep / (1000 * 3600)
    dhw_en = sum(dhw_p_array) * timestep / (1000 * 3600)

    q_hp_out_en = sum(q_hp_out) * timestep / (1000 * 3600)
    q_eh_out_en = sum(q_eh_out) * timestep / (1000 * 3600)

    print('Space heating net energy demand in kWh:')
    print(sh_en)
    print('Domestic hot water net energy demand in kWh:')
    print(dhw_en)
    print()

    print('HP thermal energy output in kWh:')
    print(q_hp_out_en)
    print('EH thermal energy output in kWh:')
    print(q_eh_out_en)
    print()

    fig = plt.figure()

    plt.subplot(4, 1, 1)
    plt.plot(sh_p_array, label='Space heating power in W')
    plt.plot(dhw_p_array, label='DHW power in W')
    plt.legend()

    plt.subplot(4, 1, 2)
    plt.plot(q_hp_out, label='HP thermal output in W')
    plt.plot(el_hp_in, label='El. input HP in W')
    plt.legend()

    plt.subplot(4, 1, 3)
    plt.plot(q_eh_out, label='EH thermal output in W')
    plt.legend()

    plt.subplot(4, 1, 4)
    plt.plot(tes_temp, label='Storage temp. in degree C')
    plt.legend()

    plt.show()
    plt.close()
    # #  ####################################################################

    # #  ####################################################################
    #  Extract building 1008 (Boiler, TES, PV, Battery)
    id = 1006
    exbuild = city.node[id]['entity']

    print('Capacity of TES in kg: ', exbuild.bes.tes.capacity)

    #  Calculate thermal energy balance
    calc_build_therm_eb(build=exbuild, id=id)

    #  Calculate electric energy balance
    calc_build_el_eb(build=exbuild)

    #  Get space heating results
    sh_p_array = exbuild.get_space_heating_power_curve()
    dhw_p_array = exbuild.get_dhw_power_curve()

    tes_temp = exbuild.bes.tes.array_temp_storage

    sh_en = sum(sh_p_array) * timestep / (1000 * 3600)
    dhw_en = sum(dhw_p_array) * timestep / (1000 * 3600)

    q_boiler = exbuild.bes.boiler.array_fuel_power
    q_boil_th_en = sum(q_boiler) * timestep / (1000 * 3600)

    print('Space heating net energy demand in kWh:')
    print(sh_en)
    print('Domestic hot water net energy demand in kWh:')
    print(dhw_en)
    print()

    print('Boiler thermal energy output in kWh:')
    print(q_boil_th_en)
    print()

    fig = plt.figure()

    plt.subplot(3, 1, 1)
    plt.plot(sh_p_array, label='Space heating power in W')
    plt.plot(dhw_p_array, label='DHW power in W')
    plt.legend()

    plt.subplot(3, 1, 2)
    plt.plot(q_boiler, label='Boiler thermal output in W')
    plt.legend()

    plt.subplot(3, 1, 3)
    plt.plot(tes_temp, label='Storage temp. in degree C')
    plt.legend()

    plt.show()
    plt.close()
    # #  ####################################################################
