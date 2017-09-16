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
                        id=None):
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

        if has_eh is False and build.get_annual_dhw_demand() > 0:
            msg = 'Building ' + str() + ' does only have HP without EH.' \
                                        ' Thus, it cannot cover hot water' \
                                        ' energy demand, which is larger ' \
                                        'than zero!'
            raise AssertionError(msg)

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

    #  TODO: Differentiate between building with and without HP

    #  Perform energy balance calculation for different states
    #  #################################################################
    if has_tes and has_hp is False:
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

                    if (sh_pow_remain + dhw_pow_remain) >= q_nom_chp:
                        #  Cover part of power with full CHP load
                        chp.th_op_calc_all_results(control_signal=q_nom_chp,
                                                   time_index=i)

                        #  Calculate remaining thermal power
                        if sh_pow_remain - q_nom_chp > 0:
                            sh_pow_remain -= q_nom_chp
                        elif sh_pow_remain == q_nom_chp:
                            sh_pow_remain = 0
                        elif sh_pow_remain - q_nom_chp < 0:
                            dhw_pow_remain -= (q_nom_chp - sh_pow_remain)
                            sh_pow_remain = 0

                    elif (sh_pow_remain + dhw_pow_remain) < q_nom_chp:
                        #  Try to use CHP, depending on part load

                        chp_lal = chp.lowerActivationLimit

                        if (
                            sh_pow_remain + dhw_pow_remain) < chp_lal * q_nom_chp:
                            #  Required power is below part load performance,
                            #  thus, chp cannot be used
                            chp.th_op_calc_all_results(control_signal=0,
                                                       time_index=i)
                        else:
                            #  CHP can operate in part load
                            chp.th_op_calc_all_results(
                                control_signal=sh_pow_remain + dhw_pow_remain,
                                time_index=i)

                            sh_pow_remain = 0
                            dhw_pow_remain = 0

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

                if (sh_pow_remain + dhw_pow_remain) >= q_out_max:
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
                        dhw_pow_remain -= (q_out_max - sh_pow_remain)
                        sh_pow_remain = 0

                else:
                    #  Cover remaining demand with storage load

                    tes.calc_storage_temp_for_next_timestep(q_in=0,
                                                            q_out=sh_pow_remain + dhw_pow_remain,
                                                            t_prior=t_prior,
                                                            t_ambient=None,
                                                            set_new_temperature=True,
                                                            save_res=True,
                                                            time_index=i)

                    sh_pow_remain = 0
                    dhw_pow_remain = 0

                if has_boiler:

                    #  boiler pointer
                    boiler = build.bes.boiler

                    #  Get nominal power
                    q_nom_boi = boiler.qNominal

                    #  if sh_pow_remain > 0 or dhw_pow_remain > 0, use boiler
                    if (sh_pow_remain + dhw_pow_remain) >= q_nom_boi:
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
                            dhw_pow_remain -= (q_nom_boi - sh_pow_remain)
                            sh_pow_remain = 0

                    elif (sh_pow_remain + dhw_pow_remain) < q_nom_boi:
                        #  Use boiler in part load

                        boiler.calc_boiler_all_results(
                            control_signal=(sh_pow_remain + dhw_pow_remain),
                            time_index=i)

                        sh_pow_remain = 0
                        dhw_pow_remain = 0

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
                            control_signal=(sh_pow_remain + dhw_pow_remain),
                            time_index=i)

                        sh_pow_remain = 0
                        dhw_pow_remain = 0

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

                    if (sh_pow_remain + dhw_pow_remain + q_tes_in_max) \
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

                                q_tes_in = q_nom_chp - sh_pow_remain - \
                                           dhw_pow_remain

                                dhw_pow_remain = 0
                            sh_pow_remain = 0

                    elif (sh_pow_remain + dhw_pow_remain + q_tes_in_max) < \
                            q_nom_chp:
                        #  Try to use CHP, depending on part load

                        chp_lal = chp.lowerActivationLimit

                        if ((sh_pow_remain + dhw_pow_remain + q_tes_in_max)
                                < chp_lal * q_nom_chp):
                            #  Required power is below part load performance,
                            #  thus, chp cannot be used
                            chp.th_op_calc_all_results(control_signal=0,
                                                       time_index=i)
                            q_tes_in = 0

                        else:
                            #  CHP can operate in part load
                            chp.th_op_calc_all_results(
                                control_signal=sh_pow_remain + dhw_pow_remain + q_tes_in_max,
                                time_index=i)

                            q_tes_in = q_tes_in_max + 0.0

                            sh_pow_remain = 0
                            dhw_pow_remain = 0

                if has_boiler:

                    #  boiler pointer
                    boiler = build.bes.boiler

                    #  Get nominal power
                    q_nom_boi = boiler.qNominal

                    #  if sh_pow_remain > 0 or dhw_pow_remain > 0, use boiler
                    if (sh_pow_remain + dhw_pow_remain) >= q_nom_boi:
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
                            dhw_pow_remain -= (q_nom_boi - sh_pow_remain)
                            sh_pow_remain = 0

                    elif (sh_pow_remain + dhw_pow_remain) < q_nom_boi:
                        #  Use boiler in part load

                        boiler.calc_boiler_all_results(
                            control_signal=(sh_pow_remain + dhw_pow_remain),
                            time_index=i)

                        sh_pow_remain = 0
                        dhw_pow_remain = 0

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
                            control_signal=(sh_pow_remain + dhw_pow_remain),
                            time_index=i)

                        sh_pow_remain = 0
                        dhw_pow_remain = 0

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

                    if (sh_pow_remain + dhw_pow_remain + q_tes_in_max) \
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

                                q_tes_in = q_nom_chp - sh_pow_remain - \
                                           dhw_pow_remain

                                q_tes_in_remain -= q_tes_in
                                dhw_pow_remain = 0

                            sh_pow_remain = 0

                    elif (sh_pow_remain + dhw_pow_remain + q_tes_in_max) < \
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
                                control_signal=sh_pow_remain + dhw_pow_remain + q_tes_in_max,
                                time_index=i)

                            q_tes_in = q_tes_in_max + 0.0

                            sh_pow_remain = 0
                            dhw_pow_remain = 0
                            q_tes_in_remain = 0

                if has_boiler:

                    #  boiler pointer
                    boiler = build.bes.boiler

                    #  Get nominal power
                    q_nom_boi = boiler.qNominal

                    #  if sh_pow_remain > 0 or dhw_pow_remain > 0, use boiler
                    if (sh_pow_remain + dhw_pow_remain + q_tes_in_remain) \
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

                                # Add boiler power to CHP power to load
                                #  storage
                                q_tes_in += q_nom_boi - sh_pow_remain - \
                                            dhw_pow_remain

                                q_tes_in_remain -= q_nom_boi - \
                                                   sh_pow_remain - \
                                                   dhw_pow_remain
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

                                # Add eh power to CHP and boiler power to load
                                #  storage
                                q_tes_in += q_nom_eh - sh_pow_remain - \
                                            dhw_pow_remain

                                q_tes_in_remain -= q_nom_eh - \
                                                   sh_pow_remain - \
                                                   dhw_pow_remain
                                #  Logic-check
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

                #  Calc. storage energy balance for this timestep
                tes.calc_storage_temp_for_next_timestep(q_in=q_tes_in,
                                                        q_out=q_out_requ,
                                                        t_prior=temp_prior,
                                                        set_new_temperature=True,
                                                        save_res=True,
                                                        time_index=i)

            if sh_pow_remain > 0 or dhw_pow_remain > 0:
                msg = 'Could not solve thermal energy balance in ' \
                      'building' + str(id) + ' at timestep ' + str(i) + '.'
                raise EnergyBalanceException(msg)

    elif has_tes and has_hp:
        #  Use heat pump with thermal storage to cover space heating demand

        #  Loop over power values
        for i in range(len(sh_p_array)):

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

            #  TES mode 1

                #  Use HP for SH
                #  Use EH for DHW
                #  Use TES for SH, if necessary
                #  Use EH for SH, if necessary

            #  TES mode 2

                #  Use HP for SH and TES
                #  Use EH for DHW
                #  Use EH for SH, if necessary
                #  Use TES for SH, if necessary

            #  TES mode 3

                #  Use HP for SH and TES
                #  Use EH for DHW
                #  Use EH for SH and TES

            # if sh_pow_remain >= q_nom_hp:
            #     #  Cover part of sh power with full HP load
            #     hp.calc_hp_all_results(
            #         control_signal=q_nom_hp,
            #         t_source=temp_source,
            #         time_index=i)
            #
            #     sh_pow_remain -= q_nom_hp
            #
            # else:
            #     #  sh_pow_remain < q_nom_hp
            #     #  Try using hp in part load
            #
            #     hp_lal = hp.lowerActivationLimit
            #
            #     if sh_pow_remain < hp_lal * q_nom_hp:
            #         #  Required power is below part load performance,
            #         #  thus, hp cannot be used
            #         hp.calc_hp_all_results(
            #             control_signal=0,
            #             t_source=temp_source,
            #             time_index=i)
            #     else:
            #         #  HP can operate in part load
            #         hp.th_op_calc_all_results(
            #             control_signal=sh_pow_remain,
            #             time_index=i)
            #
            #         sh_pow_remain = 0



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
    # citvis.plot_city_district(city=city, plot_esys=True, plot_lhn=True,
    #                           plot_deg=True)

    #  ####################################################################
    # #  Get buiding 1007 (boiler, only)
    # #  Add EH to test energy balance for boiler and eh without tes
    # exbuild = city.node[1007]['entity']
    #
    # eh = elheat.ElectricalHeaterExtended(environment=exbuild.environment,
    #                                      q_nominal=10000)
    #
    # exbuild.bes.addDevice(eh)
    #
    # calc_build_therm_eb(build=exbuild)
    #
    # q_out = exbuild.bes.boiler.totalQOutput
    # fuel_in = exbuild.bes.boiler.array_fuel_power
    # sh_p_array = exbuild.get_space_heating_power_curve()
    # dhw_p_array = exbuild.get_dhw_power_curve()
    #
    # plt.plot(q_out, label='q_out')
    # plt.plot(fuel_in, label='fuel in')
    # plt.plot(sh_p_array, label='sh power')
    # plt.plot(dhw_p_array, label='dhw power')
    # plt.legend()
    # plt.show()
    # plt.close()
    #  ####################################################################

    #  ####################################################################
    #  Get buiding 1001 (CHP, boiler, tes)
    #  Add EH to test energy balance for CHP, boiler, EH with TES
    exbuild = city.node[1001]['entity']

    # eh = elheat.ElectricalHeaterExtended(environment=exbuild.environment,
    #                                      q_nominal=10000)
    #
    # exbuild.bes.addDevice(eh)

    #  Calculate energy balance
    calc_build_therm_eb(build=exbuild)

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

    #  Checks
    sh_net_energy = sum(sh_p_array) * 3600 / (1000 * 3600) # in kWh
    dhw_net_energy = sum(dhw_p_array) * 3600 / (1000 * 3600) # in kWh
    boil_th_energy = sum(q_out) * 3600 / (1000 * 3600) # in kWh
    chp_th_energy = sum(q_chp_out) * 3600 / (1000 * 3600) # in kWh
    fuel_boiler_energy = sum(fuel_in) * 3600 / (1000 * 3600) # in kWh
    fuel_chp_energy = sum(fuel_chp_in) * 3600 / (1000 * 3600)  # in kWh
    chp_el_energy = sum(p_el_chp_out) * 3600 / (1000 * 3600)  # in kWh

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

    plt.subplot(4, 1, 1)
    plt.plot(sh_p_array, label='Space heat. in Watt')
    plt.plot(dhw_p_array, label='Hot water power in Watt')
    plt.legend()

    plt.subplot(4, 1, 2)
    plt.plot(q_out, label='Boiler th. power in Watt')
    plt.plot(fuel_in, label='Boiler fuel power in Watt')
    plt.legend()

    plt.subplot(4, 1, 3)
    plt.plot(q_chp_out, label='CHP th. power in Watt')
    plt.plot(fuel_chp_in, label='CHP fuel power in Watt')
    plt.legend()

    plt.subplot(4, 1, 4)
    plt.plot(p_el_chp_out, label='CHP el. power in Watt')
    plt.legend()

    plt.ylabel('Time in hours')

    plt.show()
    plt.close()
    #  ####################################################################