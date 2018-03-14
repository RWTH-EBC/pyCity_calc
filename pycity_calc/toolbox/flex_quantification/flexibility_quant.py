#!/usr/bin/env python
# coding=utf-8
"""
Script to estimate thermal and electrical flexibility of building energy
systems based on approach of Sebastian Stinner:
https://www.sciencedirect.com/science/article/pii/S0306261916311424
https://doi.org/10.1016/j.apenergy.2016.08.055
"""
from __future__ import division

import os
import pickle
import copy
import numpy as np
import warnings
import matplotlib.pyplot as plt

import pycity_base.functions.changeResolution as chres

import pycity_calc.energysystems.boiler as boisys
import pycity_calc.cities.scripts.energy_sys_generator as esysgen
import pycity_calc.simulation.energy_balance.building_eb_calc as buildeb


def calc_t_forced_build(q_ehg_nom, array_sh, array_dhw, timestep, tes):
    """
    Calculate t forced array for building

    Parameters
    ----------
    q_ehg_nom : float
        Nominal thermal power of electric heat generator(s) in Watt
    array_sh : array (of floats)
        Array holding space heating power values in Watt
    array_dhw : array (of floats)
        Array holding hot water power values in Watt
    timestep : int
        Timestep in seconds
    tes : object
        TES object of pyCity_calc

    Returns
    -------
    array_t_force : np.array
        Array holding t forced for each timestep. t_forced is given in seconds
    """

    # timestep = building.environment.timer.timeDiscretization

    #  Create initial array
    array_t_forced = np.zeros(int(365 * 24 * 3600 / timestep))

    # #  Check if building has energy system
    # #  ###########################################################
    # if building.hasBes is False:
    #     msg = 'Building ' + str(id) + ' has no building energy system! ' \
    #                                   'Thus, cannot calculate t_forced array.'
    #     warnings.warn(msg)
    #     return array_t_forced
    #
    # #  ###########################################################
    # if building.bes.hasTes is False:
    #     msg = 'Building ' + str(id) + ' has no thermal storage. ' \
    #                                   'Thus, therm. flexibility is zero.'
    #     warnings.warn(msg)
    #     #  Flexibility is zero, return array with zeros
    #     return array_t_forced

    # #  Get maximal thermal output power of electric heat generators
    # #  (CHP, EH, HP)
    # q_ehg_nom = 0  # in Watt
    # if building.bes.hasChp:
    #     q_ehg_nom += building.bes.chp.qNominal
    # if building.bes.hasHeatpump:
    #     q_ehg_nom += building.bes.heatpump.qNominal
    #
    # if building.bes.hasElectricalHeater and use_eh:
    #     q_ehg_nom += building.bes.electricalHeater.qNominal

    #  ###########################################################
    if q_ehg_nom == 0:
        msg = 'Building ' \
              + str(id) + ' has no thermo-electric energy systems. ' \
                          'Thus, therm. flexibility is zero.'
        warnings.warn(msg)
        #  Flexibility is zero, return array with zeros
        return array_t_forced

    # #  Extract thermal power curve of building
    # sh_power = building.get_space_heating_power_curve()
    # dhw_power = building.get_dhw_power_curve()
    array_th = array_sh + array_dhw

    #  Loop over each timestep
    #  ###########################################################
    for i in range(len(array_t_forced)):
        #  Copy storage and set initial / current temperature to t_min (empty)
        tes_copy = copy.deepcopy(tes)
        tes_copy.t_current = tes_copy.t_min
        tes_copy.tInit = tes_copy.t_min

        #  Initial timestep
        for t in range(len(array_t_forced) - i):

            #  Current thermal power demand
            th_pow_cur = array_th[t + i]

            #  Calculate possible charging power
            if q_ehg_nom > th_pow_cur:
                p_charge = q_ehg_nom - th_pow_cur
            else:
                p_charge = 0
                #  TODO: Add discharging?

            #  if calc_storage_q_in_max > q_ehg_nom
            if tes_copy.calc_storage_q_in_max() > p_charge:
                t_prior = tes_copy.t_current

                #  perform calc_storage_temp_for_next_timestep
                tes_copy.calc_storage_temp_for_next_timestep(q_in=p_charge,
                                                             q_out=0,
                                                             t_prior=t_prior,
                                                             save_res=True,
                                                             time_index=t)

            else:
                #  Reduce by one increment of t, if t > 0
                if t > 0:
                    t -= 1
                #  End seconds for loop
                break

        #  Save to array_t_forced
        array_t_forced[i] = t * timestep  # in seconds

    return array_t_forced


def calc_t_delayed_build(building, id=None, use_boi=False, plot_soc=False):
    """
    Calculate t delayed array for building. Precalculates SOC based on
    EHG thermal output power and thermal power of building (demand)

    Parameters
    ----------
    building : object
        Building object of pyCity_calc
    id : int, optional
        Building id (default: None)
    use_boi : bool, optional
        Defines, if boiler can be used to charge thermal storage in prior
        timesteps (default: False). This can be of interest, if the EHG
        nominal thermal power is below the thermal power of the building
        (e.g. for CHPs) and the TES is not fully charged (reducing the delayed
        time)
    plot_soc : bool, optional
        Plots SOC of storage over year for pre-charging (Default: False)

    Returns
    -------
    array_t_delayed : np.array
        Array holding t delayed for each timestep.
        t_delayed is given in seconds
    """

    #  Check if building has energy system
    #  ###########################################################
    if building.hasBes is False:
        msg = 'Building ' + str(id) + ' has no building energy system! ' \
                                      'Thus, cannot calculate t_forece array.'
        raise AssertionError(msg)

    timestep = building.environment.timer.timeDiscretization

    #  Create initial array
    array_t_delayed = np.zeros(int(365 * 24 * 3600 / timestep))

    #  ###########################################################
    if building.bes.hasTes is False:
        msg = 'Building ' + str(id) + ' has no thermal storage. ' \
                                      'Thus, therm. flexibility is zero.'
        warnings.warn(msg)
        #  Flexibility is zero, return array with zeros
        return array_t_delayed

    #  Get maximal thermal output power of electric heat generators
    #  (CHP, EH, HP)
    q_ehg_nom = 0  # in Watt
    if building.bes.hasChp:
        q_ehg_nom += building.bes.chp.qNominal
    if building.bes.hasHeatpump:
        q_ehg_nom += building.bes.heatpump.qNominal
    if building.bes.hasElectricalHeater:
        q_ehg_nom += building.bes.electricalHeater.qNominal
    if building.bes.hasBoiler:
        q_boi_nom = building.bes.boiler.qNominal

    #  ###########################################################
    if q_ehg_nom == 0:
        msg = 'Building ' \
              + str(id) + ' has no thermo-electric energy systems. ' \
                          'Thus, therm. flexibility is zero.'
        warnings.warn(msg)
        #  Flexibility is zero, return array with zeros
        return array_t_delayed

    #  Extract thermal power curve of building
    sh_power = building.get_space_heating_power_curve()
    dhw_power = building.get_dhw_power_curve()
    th_power = sh_power + dhw_power

    #  Precalculate, if it is possible to fully charge tes in prior timestep
    #  ###########################################################
    array_tes_en = np.zeros(len(array_t_delayed))
    array_tes_soc = np.zeros(len(array_t_delayed))

    #  Calculate maximal amount of storable energy in kWh
    q_sto_max = building.bes.tes.calc_storage_max_amount_of_energy()

    #  Assuming empty storage at beginning
    q_sto_cur = 0

    #  If use_boi is True, boiler can also be used for pre-charging of TES
    if use_boi:
        q_ref_nom = q_ehg_nom + q_boi_nom
    else:
        q_ref_nom = q_ehg_nom + 0.0

    for i in range(len(th_power) - 1):

        if q_ref_nom > th_power[i]:
            #  Charging possible
            delta_q = (q_ref_nom - th_power[i]) * timestep / (3600 * 1000)
            if q_sto_cur + delta_q < q_sto_max:
                q_sto_cur += delta_q
            else:
                q_sto_cur = q_sto_max + 0.0
        else:
            #  Discharging event
            delta_q = (-q_ref_nom + th_power[i]) * timestep / (3600 * 1000)
            if q_sto_cur - delta_q > 0:
                q_sto_cur -= delta_q
            else:
                q_sto_cur = 0

        #  Save current state of charge (with delay of one timestep, as
        #  availability is given at next timestep
        array_tes_en[i + 1] = q_sto_cur

    #  Calculate soc value for each timestep
    for i in range(len(th_power)):
        array_tes_soc[i] = array_tes_en[i] / q_sto_max

    if plot_soc:
        #  Plot tes soc array
        plt.plot(array_tes_soc)
        plt.xlabel('Time in hours')
        plt.ylabel('TES SOC')
        plt.show()
        plt.close()

    #  Loop over each timestep
    #  ###########################################################
    for i in range(len(array_t_delayed)):
        #  Copy storage and set initial / current temperature
        #  to t_max * soc (definingn state of charge for TES)
        tes_copy = copy.deepcopy(building.bes.tes)
        tes_copy.t_current = tes_copy.tMax * array_tes_soc[i]
        tes_copy.tInit = tes_copy.tMax * array_tes_soc[i]

        #  Initial timestep
        for t in range(len(array_t_delayed) - i):

            #  Current thermal power demand
            th_pow_cur = th_power[t + i]

            #  if calc_storage_q_in_max > q_ehg_nom
            if tes_copy.calc_storage_q_out_max() > th_pow_cur:
                t_prior = tes_copy.t_current

                #  perform calc_storage_temp_for_next_timestep
                tes_copy.calc_storage_temp_for_next_timestep(q_in=0,
                                                             q_out=th_pow_cur,
                                                             t_prior=t_prior,
                                                             save_res=True,
                                                             time_index=t)

            else:
                #  Reduce by one increment of t, if t > 0
                if t > 0:
                    t -= 1
                #  End seconds for loop
                break

        #  Save to array_t_forced
        array_t_delayed[i] = t * timestep  # in seconds

    return array_t_delayed


def calc_pow_ref(building, tes_cap=0.001, mod_boi=True,
                 boi_size=50000, eta_boi=0.95,
                 use_eh=False):
    """
    Calculate reference electric heat generator load curve by solving thermal
    and electric energy balance with reduced tes size.
    (+ used energy (HP/EH) / - produced electric energy (CHP))
    Deactivate PV and el. battery, if existent.

    Parameters
    ----------
    building : object
        Building object
    tes_cap : float, optional
        Storage capacity (mass in kg) of TES (default: 0.001). Default value
        is low to minimize tes flexibility influence on reference curve.
    mod_boi : bool, optional
        Defines, if boiler size should be modified (CHP/BOI) /
        added (for HP/EH system) (default: True)
    boi_size : float, optional
        Boiler nominal thermal power in Watt (default: 50000). Used to add
        boiler, if no boiler exists and run fails (e.g. HP/EH usage).
        Increasing boiler size for CHP/BOI system
    eta_boi : float, optional
        Initial boiler efficiency (default: 0.95)
    use_eh : bool, optional
        Defines, if electric heater is also used to define t_forced_build
        (default: False).

    Returns
    -------
    res_tuple : tuple
        Tuple holding (array_p_el_ref, array_el_power_hp_in)
        array_p_el_ref : np.array
            Array holding electric power values in Watt (used/produced by
            electric heat generator (EHG)) (+ used energy (HP/EH) / - produced
            electric energy (CHP))
        array_el_power_hp_in : np.array
            Array holding input electrical power for heat pump in Watt
    """

    if building.hasBes is False:
        msg = 'Buiding has no BES. Thus, cannot calculate reference EHG ' \
              'power curves. Going to return (None, None).'
        warnings.warn(msg)
        return (None, None)

    #  Copy building object
    build_copy = copy.deepcopy(building)

    #  Reduce TES size (TES still required to prevent assertion error in
    #  energy balance, when CHP is used!)
    build_copy.bes.tes.capacity = tes_cap

    #  Remove PV, if existent
    if build_copy.bes.hasPv:
        build_copy.bes.pv = None
        build_copy.bes.hasPv = False

    #  Remove Bat, if existent
    if build_copy.bes.hasBattery:
        build_copy.bes.battery = None
        build_copy.bes.hasBattery = False

    if use_eh is False and build_copy.bes.hasElectricalHeater:
        #  Remove electric heater
        build_copy.bes.electricalHeater = None
        build_copy.bes.hasElectricalHeater = False

    if mod_boi and boi_size > 0:
        if build_copy.bes.hasBoiler:
            build_copy.bes.boiler.qNominal = boi_size
        elif build_copy.bes.hasBoiler is False:
            #  Generate boiler object (also for HP/EH combi to prevent assertion
            #  error, if TES capacity is reduced)
            print('boi_size ', boi_size)
            boi = boisys.BoilerExtended(environment=build_copy.environment,
                                        q_nominal=boi_size,
                                        eta=eta_boi)
            build_copy.bes.addDevice(boi)

    #  Calculate thermal energy balance with reduced TES
    buildeb.calc_build_therm_eb(build=build_copy)

    #  Calculate electric energy balance with reduced TES
    dict_el_eb_res = buildeb.calc_build_el_eb(build=build_copy)

    timestep = build_copy.environment.timer.timeDiscretization

    array_p_el_ref = np.zeros(int(365 * 24 * 3600 / timestep))

    #  Only use grid import/export values (also account for internal el.
    #  demand of building
    # #  Minus CHP power production
    # array_p_el_ref -= dict_el_eb_res['chp_feed']
    # #  Plus HP grid usage
    # array_p_el_ref += dict_el_eb_res['grid_import_hp']
    # #  Plus EH grid usage
    # array_p_el_ref += dict_el_eb_res['grid_import_eh']

    if build_copy.bes.hasChp:
        array_p_el_ref -= build_copy.bes.chp.totalPOutput
    else:
        #  Only account for EH, if CHP is not present
        if build_copy.bes.hasHeatpump:
            array_p_el_ref += build_copy.bes.heatpump.array_el_power_in
        if build_copy.bes.hasElectricalHeater:
            array_p_el_ref += build_copy.bes.electricalHeater.totalPConsumption

    if build_copy.bes.hasHeatpump:
        array_el_power_hp_in = copy. \
            copy(build_copy.bes.heatpump.array_el_power_in)
    else:
        array_el_power_hp_in = None

    return (array_p_el_ref, array_el_power_hp_in)


def calc_power_ref_curve(building, mod_boi=True, boi_size=0, use_eh=False):
    """
    Calculate reference electric heat generator load curve by solving thermal
    and electric energy balance with reduced tes size.
    (+ used energy (HP/EH) / - produced electric energy (CHP))
    Deactivate PV and el. battery, if existent.

    Important: calc_power_ref_curve uses try/except block to prevent failure
    (in comparison to calc_pow_ref())

    Parameters
    ----------
    building : object
        Building object
    mod_boi : bool, optional
        Defines, if boiler size should be modified (CHP/BOI) /
        added (for HP/EH system) (default: True)
    boi_size : float, optional
        Boiler nominal thermal power in Watt (default: 0). Used to add
        boiler, if no boiler exists and run fails (e.g. HP/EH usage).
        Increasing boiler size for CHP/BOI system. If 0, does not perform
        modification.
    use_eh : bool, optional
        Defines, if electric heater is also used to define t_forced_build
        (default: False).

    Returns
    -------
    res_tuple : tuple
        Tuple holding (array_p_el_ref, array_el_power_hp_in)
        array_p_el_ref : np.array
            Array holding electric power values in Watt (used/produced by
            electric heat generator (EHG)) (+ used energy (HP/EH) / - produced
            electric energy (CHP))
        array_el_power_hp_in : np.array
            Array holding input electrical power for heat pump in Watt
    """

    if building.hasBes is False:
        msg = 'Buiding has no BES. Thus, cannot calculate reference EHG ' \
              'power curves. Going to return (None, None).'
        warnings.warn(msg)
        return (None, None)

    do_ref_curve = True

    boi_size_use = boi_size + 0.0

    counter = 0

    while do_ref_curve:
        try:
            (array_p_el_ref, array_el_power_hp_in) = \
                calc_pow_ref(building, boi_size=boi_size_use, mod_boi=mod_boi,
                             use_eh=use_eh)
            do_ref_curve = False
        except:
            msg = 'El. ref. curve calc. failed. Thus, going to increase ' \
                  'boiler thermal power (and add boiler, if not existent)' \
                  '. New boiler size: ' + str(boi_size_use / 1000) + ' kW.'
            warnings.warn(msg)
            boi_size_use += 50000
            counter += 1
            if counter == 20:
                msg = 'Failed to calculate electric reference curve for' \
                      ' flexibility quantification'
                raise AssertionError(msg)

    return (array_p_el_ref, array_el_power_hp_in)


def calc_pow_flex_forced(building, array_t_forced, array_p_el_ref,
                         use_eh=False):
    """
    Calculate forced power flexibility for every timestep in given
    forced period

    Parameters
    ----------
    building : object
        Building object of pyCity_calc
    array_t_force : np.array
        Array holding t forced for each timestep. t_forced is given in seconds
    array_p_el_ref : np.array
        Array holding electric power values in Watt (used/produced by
        electric heat generator (EHG)) (+ used energy (HP/EH) / - produced
        electric energy (CHP))
    use_eh : bool, optional
        Defines, if electric heater is also used to define t_forced_build
        (default: False).

    Returns
    -------
    list_lists_pow_forced : list (of lists)
        List of lists, holding power flexibility values for forced flexibility.
        Each lists represents a timespan, beginning at timestep t, with
        corresponding el. power values for forced flexibility in Watt.
    """

    timestep = building.environment.timer.timeDiscretization

    list_lists_pow_forced = []

    #  Get maximal thermal output power of electric heat generators
    #  (CHP, EH, HP)
    p_ehg_nom = 0  # in Watt

    if building.bes.hasChp:
        p_ehg_nom += building.bes.chp.pNominal
    elif building.bes.hasHeatpump:
        # p_ehg_nom += max(building.bes.heatpump.array_el_power_in)
        #  TODO: Add option to estimate
        p_ehg_nom += building.bes.heatpump.qNominal / 3

        if building.bes.hasElectricalHeater and use_eh:
            p_ehg_nom += building.bes.electricalHeater.qNominal

    #  Loop over t_forced array
    for i in range(len(array_t_forced)):

        list_pow_forced = []

        t_forced = array_t_forced[i]  # in seconds
        t_forced_steps = int(t_forced / timestep)

        #  Loop over number of timesteps
        for t in range(t_forced_steps):
            #  Prevent out of index error
            if i + t <= len(array_t_forced) - 1:
                #  Max - Ref
                pow_flex = p_ehg_nom - abs(array_p_el_ref[i + t])
                list_pow_forced.append(pow_flex)
            #  TODO: Move idx to front, if too large

        list_lists_pow_forced.append(list_pow_forced)

    return list_lists_pow_forced


def calc_av_pow_flex_forced(list_lists_pow_forced, timestep):
    """
    Calculate average power flexibility for forced operation

    Parameters
    ----------
    list_lists_pow_forced : list (of lists)
        List of lists, holding power flexibility values for forced flexibility.
        Each lists represents a timespan, beginning at timestep t, with
        corresponding el. power values for forced flexibility in Watt.
    timestep : int
        timestep in seconds

    Returns
    -------
    array_av_flex_forced : np.array
        Array holding average flexibility power values in Watt for each
        timestep (forced operation)
    """

    array_av_flex_forced = np.zeros(len(list_lists_pow_forced))

    for i in range(len(array_av_flex_forced)):
        list_pow_forced = list_lists_pow_forced[i]

        av_energy_forced = sum(list_pow_forced) * timestep

        timespan = len(list_pow_forced) * timestep

        if timespan > 0:
            av_pow_forced = av_energy_forced / timespan
        else:
            av_pow_forced = 0

        array_av_flex_forced[i] = av_pow_forced

    return array_av_flex_forced


def calc_cycle_pow_flex_forced(list_lists_pow_forced, array_t_delayed,
                               timestep):
    """
    Calculate cycle power flexibility for forced operation

    Parameters
    ----------
    list_lists_pow_forced : list (of lists)
        List of lists, holding power flexibility values for forced flexibility.
        Each lists represents a timespan, beginning at timestep t, with
        corresponding el. power values for forced flexibility in Watt.
    array_t_delayed : np.array
        Array holding t delayed for each timestep.
        t_delayed is given in seconds
    timestep : int
        timestep in seconds

    Returns
    -------
    array_cycle_flex_forced : np.array
        Array holding cycle flexibility power values in Watt for each
        timestep (forced operation)
    """

    array_cycle_flex_forced = np.zeros(len(list_lists_pow_forced))

    for i in range(len(array_cycle_flex_forced)):
        list_pow_forced = list_lists_pow_forced[i]

        av_energy_forced = sum(list_pow_forced) * timestep

        timespan_forced = len(list_pow_forced) * timestep

        idx = i + len(list_pow_forced)
        if idx > len(array_t_delayed) - 1:
            #  Move index to start of array_t_delayed
            idx -= len(array_t_delayed) - 1

        timespan_delayed = array_t_delayed[idx]

        sum_timespans = timespan_forced + timespan_delayed

        if sum_timespans > 0:
            cycle_pow_forced = av_energy_forced / sum_timespans
        else:
            cycle_pow_forced = 0

        array_cycle_flex_forced[i] = cycle_pow_forced

    return array_cycle_flex_forced


def calc_cycle_energy_forced_year(timestep, array_cycle_flex_forced):
    """
    Calculate cycle energy flexibility for whole year (with forced operation)

    Parameters
    ----------
    timestep : int
        Timestep in seconds
    array_cycle_flex_forced : np.array
        Array holding cycle flexibility power values in Watt for each
        timestep (forced operation)

    Returns
    -------
    array_energy_flex_forced : np.array (of floats)
        Array holding energy flexibilities (in J) for forced operation
    """

    return array_cycle_flex_forced * timestep


def calc_pow_flex_delayed(timestep, array_t_delayed, array_p_el_ref):
    """
    Calculate delayed power flexibility for every timestep in given
    delayed period

    Parameters
    ----------
    timestep : int
        timestep in seconds
    array_t_delayed : np.array
        Array holding t delayed for each timestep.
        t_delayed is given in seconds
    array_p_el_ref : np.array
        Array holding electric power values in Watt (used/produced by
        electric heat generator (EHG)) (+ used energy (HP/EH) / - produced
        electric energy (CHP))

    Returns
    -------
    list_lists_pow_delayed : list (of lists)
        List of lists, holding power flexibility values for delayed
        flexibility.
        Each lists represents a timespan, beginning at timestep t, with
        corresponding el. power values for delayed flexibility in Watt.
    """

    list_lists_pow_delayed = []

    #  Loop over array_t_delayed
    for i in range(len(array_t_delayed)):

        list_pow_delayed = []

        t_delayed = array_t_delayed[i]  # in seconds
        t_delayed_steps = int(t_delayed / timestep)

        #  Loop over number of timesteps
        for t in range(t_delayed_steps):
            #  Prevent out of index error
            if i + t <= len(array_t_delayed) - 1:
                #  Ref - min (min == 0)
                pow_flex = abs(array_p_el_ref[i + t])
                list_pow_delayed.append(pow_flex)

        list_lists_pow_delayed.append(list_pow_delayed)

    return list_lists_pow_delayed


def calc_av_pow_flex_delayed(list_lists_pow_delayed, timestep):
    """

    Parameters
    ----------
    list_lists_pow_delayed
    timestep : int
        timestep in seconds

    Returns
    -------
    array_av_flex_delayed : np.array
    """

    array_av_flex_delayed = np.zeros(len(list_lists_pow_delayed))

    for i in range(len(array_av_flex_delayed)):
        list_pow_delayed = list_lists_pow_delayed[i]

        av_energy_delayed = sum(list_pow_delayed) * timestep

        timespan = len(list_pow_delayed) * timestep

        if timespan > 0:
            av_pow_delayed = av_energy_delayed / timespan
        else:
            av_pow_delayed = 0

        array_av_flex_delayed[i] = av_pow_delayed

    return array_av_flex_delayed


def calc_cycle_pow_flex_delayed(list_lists_pow_delayed, array_t_forced,
                                timestep):
    """
    Calculate cycle power flexibility for forced operation

    Parameters
    ----------
    list_lists_pow_delayed : list (of lists)
        List of lists, holding power flexibility values for forced flexibility.
        Each lists represents a timespan, beginning at timestep t, with
        corresponding el. power values for forced flexibility in Watt.
    array_t_forced : np.array
        Array holding t delayed for each timestep.
        t_delayed is given in seconds
    timestep : int
        timestep in seconds

    Returns
    -------
    array_cycle_flex_delayed : np.array
        Array holding cycle flexibility power values in Watt for each
        timestep (forced operation)
    """

    array_cycle_flex_delayed = np.zeros(len(list_lists_pow_delayed))

    for i in range(len(array_cycle_flex_delayed)):
        list_pow_delayed = list_lists_pow_delayed[i]

        av_energy_delayed = sum(list_pow_delayed) * timestep

        timespan_delayed = len(list_pow_delayed) * timestep

        idx = i + len(list_pow_delayed)
        if idx > len(array_t_forced) - 1:
            #  Move index to start of array_t_delayed
            idx -= len(array_t_forced) - 1

        timespan_forced = array_t_forced[idx]

        sum_timespans = timespan_delayed + timespan_forced

        if sum_timespans > 0:
            cycle_pow_delayed = av_energy_delayed / sum_timespans
        else:
            cycle_pow_delayed = 0

        array_cycle_flex_delayed[i] = cycle_pow_delayed

    return array_cycle_flex_delayed


def calc_cycle_energy_delayed_year(timestep, array_cycle_flex_delayed):
    """
    Calculate cycle energy flexibility for whole year (with delayed operation)

    Parameters
    ----------
    timestep : int
        Timestep in seconds
    array_cycle_flex_delayed : np.array
        Array holding cycle flexibility power values in Watt for each
        timestep (delayed operation)

    Returns
    -------
    array_energy_flex_delayed : np.array (of floats)
        Array holding energy flexibilities (in J) for delayed operation
    """

    return array_cycle_flex_delayed * timestep


def calc_storage_av_energy_year(building):
    """
    Returns array holding stored usable amount of thermal energy within TES
    per timestep (in kWh). Building has to be processed with thermal energy
    balance before calling calc_storage_av_energy_year()!

    Parameters
    ----------
    building : object
        Building object of pyCity (requires bes with thermal supplier and
        TES). Needs to be processed with thermal energy balance calculation!

    Returns
    -------
    array_tes_en : array (of float)
        Array holding stored usable amount of thermal energy within TES
        per timestep (in kWh)
    """

    timestep = building.environment.timer.timeDiscretization

    #  Calculate array with stored energy within tes
    array_tes_en = np.zeros(int(3600 * 24 * 365 / timestep))

    if building.hasBes is False:
        msg = 'Building has no BES. Thus, cannot calculate array with TES' \
              ' energy. Return zero array!'
        warnings.warn(msg)
        return array_tes_en
    else:
        #  Check if TES exists
        if building.bes.hasTes is False:
            msg = 'Building has no TES. Thus, cannot calculate array ' \
                  'with TES energy. Return zero array!'
            warnings.warn(msg)
            return array_tes_en

    #  Extract tes data
    #  Pointer to tes temperature array
    array_temp_storage = building.bes.tes.array_temp_storage
    #  Pointer to minimum storage temperature, c_p and capacity
    t_min = building.bes.tes.t_min
    c_p = building.bes.tes.c_p
    mass = building.bes.tes.capacity

    for i in range(len(array_tes_en)):  # in kWh
        array_tes_en[i] = mass * c_p * \
                          (array_temp_storage[i] * t_min) / (3600 * 1000)

    return array_tes_en


def calc_av_energy_tes_year(building):
    """
    Calculates average stored amount of energy within TES for a whole year.
    Building has to be processed with thermal energy
    balance before calling calc_av_energy_tes_year()!

    Parameters
    ----------
    building : object
        Building object of pyCity (requires bes with thermal supplier and
        TES). Needs to be processed with thermal energy balance calculation!

    Returns
    -------
    en_av_tes : float
        Average stored usable amount of thermal energy within TES for a
        whole year in kWh
    """

    array_tes_en = calc_storage_av_energy_year(building=building)

    #  Calculate average amount of energy within tes
    en_av_tes = sum(array_tes_en) / len(array_tes_en)

    return en_av_tes


def calc_dimless_th_power_flex(q_ehg_nom, array_sh, array_dhw, timestep):
    """
    Calculates dimensionless thermal power flexibility alpha_th

    Parameters
    ----------
    q_ehg_nom : float
        Nominal thermal power of electric heat generator(s) in Watt
    array_sh : array (of floats)
        Array holding space heating power values in Watt
    array_dhw : array (of floats)
        Array holding hot water power values in Watt
    timestep : int
        Timestep in seconds

    Returns
    -------
    alpha_th : float
        Dimensionless thermal power flexibility of BES
    """

    #  ###########################################################
    if q_ehg_nom == 0:
        msg = 'Building ' \
              + str(id) + ' has no thermo-electric energy systems. ' \
                          'Thus, therm. flexibility is zero.'
        warnings.warn(msg)
        #  Flexibility is zero
        return 0

    array_thermal = array_sh + array_dhw

    # If timestep is different from 3600 seconds, convert th_power array
    th_power_new = chres.changeResolution(array_thermal,
                                          oldResolution=timestep,
                                          newResolution=3600)

    if max(th_power_new) > 0:
        alpha_th = q_ehg_nom / max(th_power_new)
    else:
        msg = 'Thermal power is zero! Thus, alpha_th cannot be calculated' \
              ' Return None'
        warnings.warn(msg)
        alpha_th = None

    return alpha_th


def calc_dimless_tes_th_flex(sh_dem, dhw_dem, en_av_tes):
    """
    Calculate dimensionless thermal storage flexibility beta_th

    Parameters
    ----------
    sh_dem : float
        Annual space heating demand in kWh
    dhw_dem : float
        Annual hot water demand in kWh
    en_av_tes : float
        Average stored usable amount of thermal energy within TES for a
        whole year in kWh

    Returns
    -------
    beta_th : float
        Dimensionless thermal storage flexibility
    """
    assert sh_dem >= 0
    assert dhw_dem >= 0
    assert en_av_tes >= 0

    if sh_dem + dhw_dem == 0:
        msg = 'Cannot calculate beta_th, as thermal demands are zero!' \
              ' Going to return None.'
        warnings.warn(msg)
        beta_th = None
    else:
        #  Calculate beta_th
        beta_th = en_av_tes / ((sh_dem + dhw_dem) / 365)

    return beta_th


def calc_dimless_el_power_flex(building, array_el_flex):
    """
    Calculate dimensionless electric power flexibility alpha_el

    Parameters
    ----------
    building : object
        Building object of pyCity_calc
    array_el_flex : np.array
        Array holding el. flexibility power values (for forced or delayed
        operation)
    use_eh : bool, optional
        Defines, if electric heater is also used to define t_forced_build
        (default: False)

    Returns
    -------
    array_alpha_el : np.array (of floats)
        Array holding dimensionless electric power flexibility
    """

    array_alpha_el = np.zeros(len(array_el_flex))

    #  Calculate average building thermal power
    #  ###########################################################
    #  Extract thermal power curve of building
    sh_power = building.get_space_heating_power_curve()
    dhw_power = building.get_dhw_power_curve()
    th_power = sh_power + dhw_power

    timestep = int(3600 * 24 * 365 / len(th_power))  # in seconds
    # If timestep is different from 3600 seconds, convert th_power array
    th_power_new = chres.changeResolution(th_power,
                                          oldResolution=timestep,
                                          newResolution=3600)

    for i in range(len(array_alpha_el)):
        array_alpha_el[i] = array_el_flex[i] / max(th_power_new)

    return array_alpha_el


def calc_dimless_tes_el_flex(building, array_flex_energy, id=None,
                             use_eh=False):
    """
    Calculate dimensionless electric storage flexibility beta_el

    Parameters
    ----------
    building : object
        Building object of pyCity_calc
    array_flex_energy : np.array (of floats)
        Array holding energy flexibilities in Joule
    id : int, optional
        Building id (default: None)
    use_eh : bool, optional
        Defines, if electric heater is also used to define t_forced_build
        (default: False).

    Returns
    -------
    array_beta_el : np.array (of floats)
        Array holding dimensionless electric storage flexibility
    """

    #  Check if building has energy system
    #  ###########################################################
    if building.hasBes is False:
        msg = 'Building ' + str(id) + ' has no building energy system! ' \
                                      'Thus, cannot calculate el. flexibility.'
        raise AssertionError(msg)

    #  Get maximal thermal output power of electric heat generators
    #  (CHP, EH, HP)
    q_ehg_nom = 0  # in Watt
    if building.bes.hasChp:
        q_ehg_nom += building.bes.chp.qNominal
    elif building.bes.hasHeatpump:
        q_ehg_nom += building.bes.heatpump.qNominal

        if building.bes.hasElectricalHeater and use_eh:
            q_ehg_nom += building.bes.electricalHeater.qNominal

    #  ###########################################################
    if q_ehg_nom == 0:
        msg = 'Building ' \
              + str(id) + ' has no thermo-electric energy systems. ' \
                          'Thus, el. flexibility is zero.'
        warnings.warn(msg)
        #  Flexibility is zero
        return 0

    #  Copy building object
    build_copy = copy.deepcopy(building)

    #  Get thermal energy demands
    #  ###########################################################
    sh_dem = build_copy.get_annual_space_heat_demand()
    dhw_dem = build_copy.get_annual_dhw_demand()

    #  Run thermal energy balance
    buildeb.calc_build_therm_eb(build=build_copy)

    #  Convert array_flex_energy from Joule to kWh
    array_flex_energy_kwh = array_flex_energy / (3600 * 1000)

    #  Calculate beta_el
    array_beta_el = array_flex_energy_kwh / ((sh_dem + dhw_dem) / 365)

    return array_beta_el


def main():
    #  Add energy system, if no energy system exists on city.pkl file
    #  Necessary to perform flexibility calculation
    add_esys = True

    build_id = 1001

    mod_boi = True  # Add boiler, if necessary to solve energy balance to
    #  calculate reference ehg electric load

    use_eh = False  # If True, also accounts for electric heater power to
    #  quantify flexiblity

    city_name = 'aachen_kronenberg_6.pkl'
    path_here = os.path.dirname(os.path.abspath(__file__))
    path_city = os.path.join(path_here, 'input', city_name)

    city = pickle.load(open(path_city, mode='rb'))

    timestep = city.environment.timer.timeDiscretization

    if add_esys:
        #  Add energy system
        #  Generate one feeder with CHP, boiler and TES
        list_esys = [(1001, 1, 4),  # CHP, Boiler, TES
                     (1002, 1, 4),
                     (1003, 1, 4),
                     (1004, 2, 2),  # HP (ww), EH, TES
                     (1005, 2, 2),
                     (1006, 2, 2)]

        esysgen.gen_esys_for_city(city=city,
                                  list_data=list_esys,
                                  dhw_scale=True)

    #  Pointer to current building object
    curr_build = city.nodes[build_id]['entity']

    #  Get maximal thermal output power of electric heat generators
    #  (CHP, EH, HP)
    q_ehg_nom = 0  # in Watt
    if curr_build.bes.hasChp:
        q_ehg_nom += curr_build.bes.chp.qNominal
    elif curr_build.bes.hasHeatpump:
        q_ehg_nom += curr_build.bes.heatpump.qNominal

        if curr_build.bes.hasElectricalHeater and use_eh:
            q_ehg_nom += curr_build.bes.electricalHeater.qNominal

    #  Calculate average building thermal power
    #  Extract thermal power curve of building
    array_sh = curr_build.get_space_heating_power_curve()
    array_dhw = curr_build.get_dhw_power_curve()

    sh_dem = sum(array_sh) * timestep / (3600 * 1000)
    dhw_dem = sum(array_dhw) * timestep / (3600 * 1000)

    #  Begin calculations
    #  #####################################################################

    #  Calculate dimensionless thermal power flexibility
    alpha_th = calc_dimless_th_power_flex(q_ehg_nom=q_ehg_nom,
                                          array_sh=array_sh,
                                          array_dhw=array_dhw,
                                          timestep=timestep)

    print('Dimensionless thermal power flexibility (alpha_th): ')
    print(alpha_th)
    print()

    #  Copy building to perform energy balance calculation (necessary to
    #  estimate stored amount of energy in TES per timestep)
    build_copy = copy.deepcopy(curr_build)
    #  Run thermal energy balance
    buildeb.calc_build_therm_eb(build=build_copy)
    #  Calculate average stored amount of energy in TES per timestep (for a
    #  whole year)
    en_av_tes = calc_av_energy_tes_year(building=build_copy)

    #  Calculate dimensionless thermal storage energy flexibility
    beta_th = calc_dimless_tes_th_flex(sh_dem=sh_dem, dhw_dem=dhw_dem,
                                       en_av_tes=en_av_tes)

    print('Dimensionless thermal storage energy flexibility (beta_th): ')
    print(beta_th)
    print()

    #  Calculate t_forced
    #  ###################################################################

    #  Pointer to tes
    tes = curr_build.bes.tes

    #  Calculate t_force array
    array_t_forced = calc_t_forced_build(q_ehg_nom=q_ehg_nom,
                                         array_sh=array_sh,
                                         array_dhw=array_dhw,
                                         timestep=timestep,
                                         tes=tes)

    plt.plot(array_t_forced / 3600)
    plt.xlabel('Time in hours')
    plt.ylabel('T_forced in hours')
    plt.show()
    plt.close()

    #  Calculate t_forced
    #  ###################################################################

    #  Calculate t_force array
    array_t_delayed = calc_t_delayed_build(building=curr_build, id=build_id)

    plt.plot(array_t_delayed / 3600)
    plt.xlabel('Time in hours')
    plt.ylabel('T_delayed in hours')
    plt.show()
    plt.close()

    #  Calculate reference EHG el. load curve
    #  ##################################################################
    (array_p_el_ref, array_el_power_hp_in) = \
        calc_power_ref_curve(building=curr_build, mod_boi=mod_boi,
                             use_eh=use_eh)

    plt.plot(array_p_el_ref / 1000)
    plt.xlabel('Time in hours')
    plt.ylabel('Reference EHG el. power in kW')
    plt.show()
    plt.close()

    #  Calculate pow_force_flex for each timespan
    #  ##################################################################
    list_lists_pow_forced = calc_pow_flex_forced(building=curr_build,
                                                 array_t_forced=array_t_forced,
                                                 array_p_el_ref=array_p_el_ref,
                                                 use_eh=use_eh)

    # for sublist in list_lists_pow_forced:
    #     print(sublist)

    #  Calculate average forced flex power for each timestep
    array_av_flex_forced = \
        calc_av_pow_flex_forced(list_lists_pow_forced=list_lists_pow_forced,
                                timestep=timestep)

    #  Calculate cycle forced flex. power for each timestep
    array_cycle_flex_forced = \
        calc_cycle_pow_flex_forced(list_lists_pow_forced=list_lists_pow_forced,
                                   array_t_delayed=array_t_delayed,
                                   timestep=timestep)

    plt.plot(array_av_flex_forced / 1000, label='Average')
    plt.plot(array_cycle_flex_forced / 1000, label='Cycle')
    plt.xlabel('Time in hours')
    plt.ylabel('Forced el. power flexibility in kW')
    plt.legend()
    plt.tight_layout()
    plt.show()
    plt.close()

    #  Calculate force energy flexibility
    array_energy_flex_forced = \
        calc_cycle_energy_forced_year(timestep=timestep,
                                      array_cycle_flex_forced=
                                      array_cycle_flex_forced)

    print('Energy flexibility in kWh for forced operation:')
    print(sum(array_energy_flex_forced) / (3600 * 1000))

    #  Calculate dimensionless electric power flexibility for forced operation
    array_alpha_el_forced = \
        calc_dimless_el_power_flex(building=curr_build,
                                   array_el_flex=
                                   array_cycle_flex_forced)

    plt.plot(array_alpha_el_forced)
    plt.xlabel('Time in hours')
    plt.ylabel('Dimensionless el. power flexibility alpha_el (forced)')
    plt.show()
    plt.close()

    #  Calculate energy flexibility for forced operation
    array_beta_th_forced = \
        calc_dimless_tes_el_flex(building=curr_build,
                                 array_flex_energy=array_energy_flex_forced,
                                 id=build_id, use_eh=use_eh)

    print('Dimensionless el. energy flexibility for force operation:')
    print(sum(array_beta_th_forced))
    print()

    plt.plot(array_beta_th_forced)
    plt.xlabel('Time in hours')
    plt.ylabel('Dimensionless el. energy flexibility beta_el (forced)')
    plt.show()
    plt.close()

    #  Calculate pow_delayed_flex for each timespan
    #  ##################################################################
    list_lists_pow_delayed = \
        calc_pow_flex_delayed(timestep=timestep,
                              array_t_delayed=array_t_delayed,
                              array_p_el_ref=array_p_el_ref)

    # for sublist in list_lists_pow_delayed:
    #     print(sublist)

    array_av_flex_delayed = \
        calc_av_pow_flex_delayed(list_lists_pow_delayed=list_lists_pow_delayed,
                                 timestep=timestep)

    array_cycle_flex_delayed = \
        calc_cycle_pow_flex_delayed(
            list_lists_pow_delayed=list_lists_pow_delayed,
            array_t_forced=array_t_forced,
            timestep=timestep)

    plt.plot(array_av_flex_delayed / 1000, label='Average')
    plt.plot(array_cycle_flex_delayed / 1000, label='Cycle')
    plt.xlabel('Time in hours')
    plt.ylabel('Delayed el. power flexibility in kW')
    plt.legend()
    plt.show()
    plt.close()

    array_energy_flex_delayed = \
        calc_cycle_energy_delayed_year(timestep=timestep,
                                       array_cycle_flex_delayed=
                                       array_cycle_flex_delayed)

    print('Energy flexibility in kWh for delayed operation:')
    print(sum(array_energy_flex_delayed) / (3600 * 1000))

    #  Calculate dimensionless electric power flexibility for forced operation
    array_alpha_el_delayed = \
        calc_dimless_el_power_flex(building=curr_build,
                                   array_el_flex=
                                   array_cycle_flex_delayed)

    plt.plot(array_alpha_el_delayed)
    plt.xlabel('Time in hours')
    plt.ylabel('Dimensionless el. power flexibility alpha_el (delayed)')
    plt.show()
    plt.close()

    #  Calculate energy flexibility for delayed operation
    array_beta_th_delayed = \
        calc_dimless_tes_el_flex(building=curr_build,
                                 array_flex_energy=array_energy_flex_delayed,
                                 id=build_id, use_eh=use_eh)

    print('Dimensionless el. energy flexibility for delayed operation:')
    print(sum(array_beta_th_delayed))

    plt.plot(array_beta_th_delayed)
    plt.xlabel('Time in hours')
    plt.ylabel('Dimensionless el. energy flexibility beta_el (delayed)')
    plt.show()
    plt.close()


if __name__ == '__main__':
    main()
