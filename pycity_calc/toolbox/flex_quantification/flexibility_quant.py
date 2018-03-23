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
import time
import numpy as np
import warnings
import matplotlib.pyplot as plt

import pycity_base.functions.changeResolution as chres

import pycity_calc.energysystems.boiler as boisys
import pycity_calc.energysystems.thermalEnergyStorage as tessys
import pycity_calc.cities.scripts.energy_sys_generator as esysgen
import pycity_calc.simulation.energy_balance.building_eb_calc as buildeb
import pycity_calc.cities.scripts.energy_network_generator as enetgen
import pycity_calc.toolbox.networks.network_ops as netop
import pycity_calc.simulation.energy_balance.city_eb_calc as citeb


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

    #  Create initial array
    array_t_forced = np.zeros(int(365 * 24 * 3600 / timestep))

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

    #  Append array_th to prevent out of index errors for t_forced, which
    #  "passes" 365 day mark
    array_th = np.append(array_th, array_th)

    #  Loop over each timestep
    #  ###########################################################
    for i in range(len(array_t_forced)):
        #  Copy storage and set initial / current temperature to t_min (empty)
        tes_copy = copy.deepcopy(tes)
        tes_copy.t_current = tes_copy.t_min
        tes_copy.tInit = tes_copy.t_min

        #  Initial timestep
        for t in range(len(array_t_forced)):

            #  Current thermal power demand
            th_pow_cur = array_th[t + i]

            #  Calculate possible charging power
            if q_ehg_nom > th_pow_cur:
                p_charge = q_ehg_nom - th_pow_cur
            else:
                #  break loop, as system cannot over "real" flexibility,
                #  as it has to be driven anyway
                #  Reduce by one increment of t, if t > 0
                if t > 0:
                    t -= 1
                #  End seconds for loop
                break

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


def calc_t_delayed_build(q_ehg_nom, array_sh, array_dhw, timestep, tes,
                         plot_soc=False, use_boi=False, q_boi_nom=None):
    """
    Calculate t delayed array for building. Precalculates SOC based on
    EHG thermal output power and thermal power of building (demand)

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
    plot_soc : bool, optional
        Plots SOC of storage over year for pre-charging (Default: False)
    use_boi : bool, optional
        Defines, if boiler should be used to pre-charge tes (default: False)
    q_boi_nom : float, optional
        Boiler nominal thermal power in Watt (default: None). Only relevant,
        if use_boi is True

    Returns
    -------
    array_t_delayed : np.array
        Array holding t delayed for each timestep.
        t_delayed is given in seconds
    """

    #  Create initial array
    array_t_delayed = np.zeros(int(365 * 24 * 3600 / timestep))

    #  ###########################################################
    if q_ehg_nom == 0:
        msg = 'Building ' \
              + str(id) + ' has no thermo-electric energy systems. ' \
                          'Thus, therm. flexibility is zero.'
        warnings.warn(msg)
        #  Flexibility is zero, return array with zeros
        return array_t_delayed

    #  Extract thermal power curve of building
    array_th = array_sh + array_dhw

    #  Append array_th to prevent out of index errors for t_forced, which
    #  "passes" 365 day mark
    array_th = np.append(array_th, array_th)

    #  Precalculate, if it is possible to fully charge tes in prior timestep
    #  ###########################################################
    array_tes_en = np.zeros(len(array_th))
    array_tes_soc = np.zeros(len(array_th))

    #  Calculate maximal amount of storable energy in kWh
    q_sto_max = tes.calc_storage_max_amount_of_energy()

    #  Assuming empty storage at beginning
    q_sto_cur = 0

    #  If use_boi is True, boiler can also be used for pre-charging of TES
    if use_boi:
        q_ref_nom = q_ehg_nom + q_boi_nom
    else:
        q_ref_nom = q_ehg_nom + 0.0

    for i in range(len(array_th) - 1):

        if q_ref_nom > array_th[i]:
            #  Charging possible
            delta_q = (q_ref_nom - array_th[i]) * timestep / (3600 * 1000)
            if q_sto_cur + delta_q < q_sto_max:
                q_sto_cur += delta_q
            else:
                q_sto_cur = q_sto_max + 0.0
        else:
            #  Discharging event
            delta_q = (-q_ref_nom + array_th[i]) * timestep / (3600 * 1000)
            if q_sto_cur - delta_q > 0:
                q_sto_cur -= delta_q
            else:
                q_sto_cur = 0

        #  Save current state of charge (with delay of one timestep, as
        #  availability is given at next timestep
        array_tes_en[i + 1] = q_sto_cur

    #  Calculate soc value for each timestep
    for i in range(len(array_th)):
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
        tes_copy = copy.deepcopy(tes)
        tes_copy.t_current = tes_copy.tMax * array_tes_soc[i]
        tes_copy.tInit = tes_copy.tMax * array_tes_soc[i]

        #  Initial timestep
        for t in range(len(array_t_delayed)):

            #  Current thermal power demand
            th_pow_cur = array_th[t + i]

            if th_pow_cur > q_ref_nom:
                #  If thermal power is larger than ehg (resp. ref. power),
                #  end flexibility timespan (cannot be switched of reasonably)
                #  Reduce by one increment of t, if t > 0
                if t > 0:
                    t -= 1
                #  End seconds for loop
                break


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


def calc_pow_ref_sublhn(city, tes_cap=0.001, mod_boi=True,
                        boi_size=50000, eta_boi=0.95,
                        use_eh=False):
    """
    Calculate reference electric heat generator load curve by solving thermal
    and electric energy balance with reduced tes size (for sublhn)
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
    array_p_el_ref : np.array
        Array holding electric power values in Watt (used/produced by
        electric heat generator (EHG)) ( - produced electric energy (CHP))
    """

    #  Copy city object
    city_copy = copy.deepcopy(city)

    list_builds_ids = city_copy.get_list_build_entity_node_ids()

    #  Loop over buildings in city_copy
    for n in list_builds_ids:
        curr_build = city_copy.nodes[n]['entity']

        if curr_build.hasBes:
            #  Reduce TES size (TES still required to prevent assertion error in
            #  energy balance, when CHP is used!)
            if curr_build.bes.hasTes:
                curr_build.bes.tes.capacity = tes_cap

            #  Remove PV, if existent
            if curr_build.bes.hasPv:
                curr_build.bes.pv = None
                curr_build.bes.hasPv = False

            #  Remove Bat, if existent
            if curr_build.bes.hasBattery:
                curr_build.bes.battery = None
                curr_build.bes.hasBattery = False

            if use_eh is False and curr_build.bes.hasElectricalHeater:
                #  Remove electric heater
                curr_build.bes.electricalHeater = None
                curr_build.bes.hasElectricalHeater = False

            if mod_boi and boi_size > 0:
                if curr_build.bes.hasBoiler:
                    curr_build.bes.boiler.qNominal = boi_size
                elif curr_build.bes.hasBoiler is False:
                    #  Generate boiler object (also for HP/EH combi to prevent
                    #  assertion error, if TES capacity is reduced)
                    print('boi_size ', boi_size)
                    boi = boisys.BoilerExtended(environment=
                                                curr_build.environment,
                                                q_nominal=boi_size,
                                                eta=eta_boi)
                    curr_build.bes.addDevice(boi)

    #  Generate city energy balance calculator object instance
    cit_eb_calc = citeb.CityEBCalculator(city=city_copy)

    #  Calc. city energy balance
    cit_eb_calc.calc_city_energy_balance()

    timestep = city_copy.environment.timer.timeDiscretization

    array_p_el_ref = np.zeros(int(365 * 24 * 3600 / timestep))

    for n in list_builds_ids:
        curr_build = city_copy.nodes[n]['entity']
        if curr_build.hasBes:
            if curr_build.bes.hasChp:
                array_p_el_ref -= curr_build.bes.chp.totalPOutput

    return array_p_el_ref


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


def calc_power_ref_curve_sublhn(city, mod_boi=True, boi_size=0, use_eh=False):
    """
    Calculate EHG electric power reference curve for sub-LHN city district

    Parameters
    ----------
    city : object
        City object of pyCity_calc
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
    array_p_el_ref : np.array
        Array holding electric power values in Watt (used/produced by
        electric heat generator (EHG)) ( - produced electric energy (CHP))
    """

    do_ref_curve = True

    boi_size_use = boi_size + 0.0

    counter = 0

    while do_ref_curve:
        try:
            array_p_el_ref = \
                calc_pow_ref_sublhn(city=city,
                                    boi_size=boi_size_use,
                                    mod_boi=mod_boi,
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

    return array_p_el_ref


def calc_pow_flex_forced(timestep, p_ehg_nom, array_t_forced, array_p_el_ref):
    """
    Calculate forced power flexibility for every timestep in given
    forced period

    Parameters
    ----------
    timestep : int
        Timestep in seconds
    p_ehg_nom : float
        Nominal el. power of EHG(s) in Watt
    array_t_force : np.array
        Array holding t forced for each timestep. t_forced is given in seconds
    array_p_el_ref : np.array
        Array holding electric power values in Watt (used/produced by
        electric heat generator (EHG)) (+ used energy (HP/EH) / - produced
        electric energy (CHP))

    Returns
    -------
    list_lists_pow_forced : list (of lists)
        List of lists, holding power flexibility values for forced flexibility.
        Each lists represents a timespan, beginning at timestep t, with
        corresponding el. power values for forced flexibility in Watt.
    """

    #  Append array to prevent out of index error when flexible time span
    #  passes 365 days mark
    array_p_el_ref_extended = np.append(array_p_el_ref, array_p_el_ref)

    list_lists_pow_forced = []

    #  Loop over t_forced array
    for i in range(len(array_t_forced)):

        list_pow_forced = []

        t_forced = array_t_forced[i]  # in seconds
        t_forced_steps = int(t_forced / timestep)

        #  Loop over number of timesteps
        for t in range(t_forced_steps):
            #  Max - Ref
            pow_flex = p_ehg_nom - abs(array_p_el_ref_extended[i + t])
            list_pow_forced.append(pow_flex)

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


def calc_dimless_el_power_flex(timestep, array_sh, array_dhw, array_el_flex):
    """
    Calculate dimensionless electric power flexibility alpha_el

    Parameters
    ----------
    timestep : int
        Timestep in seconds
    array_sh : array (of floats)
        Array holding space heating power values in Watt
    array_dhw : array (of floats)
        Array holding hot water power values in Watt
    array_el_flex : np.array
        Array holding el. flexibility power values (for forced or delayed
        operation)

    Returns
    -------
    array_alpha_el : np.array (of floats)
        Array holding dimensionless electric power flexibility
    """

    array_alpha_el = np.zeros(len(array_el_flex))

    array_th = array_sh + array_dhw

    # If timestep is different from 3600 seconds, convert th_power array
    th_power_new = chres.changeResolution(array_th,
                                          oldResolution=timestep,
                                          newResolution=3600)

    for i in range(len(array_alpha_el)):
        array_alpha_el[i] = array_el_flex[i] / max(th_power_new)

    return array_alpha_el


def calc_dimless_tes_el_flex(array_flex_energy, sh_dem,
                             dhw_dem):
    """
    Calculate dimensionless electric storage flexibility beta_el

    Parameters
    ----------
    building : object
        Building object of pyCity_calc
    array_flex_energy : np.array (of floats)
        Array holding energy flexibilities in Joule
    sh_dem : float
        Space heating demand in kWh
    dhw_dem : float
        Hot water demand in kWh

    Returns
    -------
    array_beta_el : np.array (of floats)
        Array holding dimensionless electric storage flexibility
    """

    #  Convert array_flex_energy from Joule to kWh
    array_flex_energy_kwh = array_flex_energy / (3600 * 1000)

    #  Calculate beta_el
    array_beta_el = array_flex_energy_kwh / ((sh_dem + dhw_dem) / 365)

    return array_beta_el


def perform_flex_analysis_single_build(build, use_eh=False, mod_boi=False,
                                       id=None, plot_res=False):
    """
    Perform flexibility analysis for stand alone building (no LHN connection)

    Parameters
    ----------
    build : object
        Building object of pyCity_calc
    use_eh : bool, optional
        Defines, if electric heater is also used to define t_forced_build
        (default: False).
    mod_boi : bool, optional
        Defines, if boiler size should be modified (CHP/BOI) /
        added (for HP/EH system) (default: True)
    id : int, optional
        Id of building (default: None)
    plot_res : bool, optional
        Defines, if results should be plotted (default: False)

    Returns
    -------
    dict_flex : dict
        Dict holding results of flexibility analysis
            dict_flex['alpha_th'] = alpha_th
            dict_flex['beta_th'] = beta_th
            dict_flex['array_t_forced'] = array_t_forced
            dict_flex['array_t_delayed'] = array_t_delayed
            dict_flex['array_p_el_ref'] = array_p_el_ref
            dict_flex['array_av_flex_forced'] = array_av_flex_forced
            dict_flex['array_cycle_flex_forced'] = array_cycle_flex_forced
            dict_flex['array_energy_flex_forced'] = array_energy_flex_forced
            dict_flex['energy_flex_forced'] = energy_flex_forced
            dict_flex['array_alpha_el_forced'] = array_alpha_el_forced
            dict_flex['array_beta_th_forced'] = array_beta_th_forced
            dict_flex['array_av_flex_delayed'] = array_av_flex_delayed
            dict_flex['array_cycle_flex_delayed'] = array_cycle_flex_delayed
            dict_flex['energy_flex_delayed'] = energy_flex_delayed
            dict_flex['array_alpha_el_delayed'] = array_alpha_el_delayed
            dict_flex['array_beta_th_delayed'] = array_beta_th_delayed
    """

    dict_flex = {}

    print('Process building ' + str(id))
    print('#############################################################')

    timestep = build.environment.timer.timeDiscretization

    #  Get maximal thermal output power of electric heat generators
    #  (CHP, EH, HP)
    q_ehg_nom = 0  # in Watt
    p_ehg_nom = 0  # in Watt
    if build.bes.hasChp:
        q_ehg_nom += build.bes.chp.qNominal
        p_ehg_nom += build.bes.chp.pNominal

        has_chp = True  # Use to define algebraic-sign of forced/delayed flex.

    elif build.bes.hasHeatpump:
        q_ehg_nom += build.bes.heatpump.qNominal
        #  Estimate p_ehg of HP with COP of 3
        p_ehg_nom += build.bes.heatpump.qNominal / 3

        has_chp = False  # Use to define algebraic-sign of forced/delayed flex.

        if build.bes.hasElectricalHeater and use_eh:
            q_ehg_nom += build.bes.electricalHeater.qNominal
            p_ehg_nom += build.bes.electricalHeater.qNominal

    if q_ehg_nom == 0:
        msg = 'Building ' \
              + str(id) + 'does not have an electric heat generator (EHG). ' \
                          'Thus, it cannot provide flexibility. Return None.'
        warnings.warn(msg)
        return None

    #  Calculate average building thermal power
    #  Extract thermal power curve of building
    array_sh = build.get_space_heating_power_curve()
    array_dhw = build.get_dhw_power_curve()

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

    dict_flex['alpha_th'] = alpha_th

    #  Copy building to perform energy balance calculation (necessary to
    #  estimate stored amount of energy in TES per timestep)
    build_copy = copy.deepcopy(build)
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

    dict_flex['beta_th'] = beta_th

    #  Calculate t_forced
    #  ###################################################################

    #  Pointer to tes
    tes = build.bes.tes

    #  Calculate t_force array
    array_t_forced = calc_t_forced_build(q_ehg_nom=q_ehg_nom,
                                         array_sh=array_sh,
                                         array_dhw=array_dhw,
                                         timestep=timestep,
                                         tes=tes)

    if plot_res:
        plt.plot(array_t_forced / 3600)
        plt.title('T_forced for building ' + str(id))
        plt.xlabel('Time in hours')
        plt.ylabel('T_forced in hours')
        plt.show()
        plt.close()

    dict_flex['array_t_forced'] = array_t_forced

    #  Calculate t_delayed
    #  ###################################################################

    #  Calculate t_delayed array
    array_t_delayed = calc_t_delayed_build(q_ehg_nom=q_ehg_nom,
                                           array_sh=array_sh,
                                           array_dhw=array_dhw,
                                           timestep=timestep,
                                           tes=tes,
                                           plot_soc=False,
                                           use_boi=False,
                                           q_boi_nom=None)

    if plot_res:
        plt.plot(array_t_delayed / 3600)
        plt.title('T_delayed for building ' + str(id))
        plt.xlabel('Time in hours')
        plt.ylabel('T_delayed in hours')
        plt.show()
        plt.close()

    dict_flex['array_t_delayed'] = array_t_delayed

    #  Calculate reference EHG el. load curve
    #  ##################################################################
    (array_p_el_ref, array_el_power_hp_in) = \
        calc_power_ref_curve(building=build, mod_boi=mod_boi,
                             use_eh=use_eh)

    if plot_res:
        plt.plot(array_p_el_ref / 1000)
        plt.title('Ref. EHG power for building ' + str(id))
        plt.xlabel('Time in hours')
        plt.ylabel('Reference EHG el. power in kW')
        plt.show()
        plt.close()

    dict_flex['array_p_el_ref'] = array_p_el_ref

    #  Calculate pow_force_flex for each timespan
    #  ##################################################################
    list_lists_pow_forced = calc_pow_flex_forced(timestep=timestep,
                                                 p_ehg_nom=p_ehg_nom,
                                                 array_t_forced=array_t_forced,
                                                 array_p_el_ref=array_p_el_ref)

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

    if has_chp is False:
        #  Convert algebraic sign to minus (for HP/EH systems)
        array_av_flex_forced *= -1
        array_cycle_flex_forced *= -1

    if plot_res:
        plt.plot(array_av_flex_forced / 1000, label='Average')
        plt.plot(array_cycle_flex_forced / 1000, label='Cycle')
        plt.title('Forced power flex. for building ' + str(id))
        plt.xlabel('Time in hours')
        plt.ylabel('Forced el. power flexibility in kW')
        plt.legend()
        plt.tight_layout()
        plt.show()
        plt.close()

    dict_flex['array_av_flex_forced'] = array_av_flex_forced
    dict_flex['array_cycle_flex_forced'] = array_cycle_flex_forced

    #  Calculate force energy flexibility
    array_energy_flex_forced = \
        calc_cycle_energy_forced_year(timestep=timestep,
                                      array_cycle_flex_forced=
                                      array_cycle_flex_forced)

    energy_flex_forced = sum(array_energy_flex_forced) / (3600 * 1000)

    print('Energy flexibility in kWh for forced operation:')
    print(energy_flex_forced)

    dict_flex['array_energy_flex_forced'] = array_energy_flex_forced
    dict_flex['energy_flex_forced'] = energy_flex_forced

    #  Calculate dimensionless electric power flexibility for forced operation
    array_alpha_el_forced = \
        calc_dimless_el_power_flex(timestep=timestep,
                                   array_sh=array_sh,
                                   array_dhw=array_dhw,
                                   array_el_flex=
                                   array_cycle_flex_forced)

    if plot_res:
        plt.plot(array_alpha_el_forced)
        plt.title('alpha_el (forced) for building ' + str(id))
        plt.xlabel('Time in hours')
        plt.ylabel('Dimensionless el. power flexibility alpha_el (forced)')
        plt.show()
        plt.close()

    dict_flex['array_alpha_el_forced'] = array_alpha_el_forced

    #  Calculate energy flexibility for forced operation
    array_beta_th_forced = \
        calc_dimless_tes_el_flex(array_flex_energy=array_energy_flex_forced,
                                 sh_dem=sh_dem,
                                 dhw_dem=dhw_dem)

    print('Dimensionless el. energy flexibility for force operation:')
    print(sum(array_beta_th_forced))
    print()

    if plot_res:
        plt.plot(array_beta_th_forced)
        plt.title('beta_el (forced) for building ' + str(id))
        plt.xlabel('Time in hours')
        plt.ylabel('Dimensionless el. energy flexibility beta_el (forced)')
        plt.show()
        plt.close()

    dict_flex['array_beta_th_forced'] = array_beta_th_forced

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

    if has_chp is True:
        #  Convert algebraic sign to minus (for CHP systems)
        array_av_flex_delayed *= -1
        array_cycle_flex_delayed *= -1

    if plot_res:
        plt.plot(array_av_flex_delayed / 1000, label='Average')
        plt.plot(array_cycle_flex_delayed / 1000, label='Cycle')
        plt.title('Delayed el. power flex. for building ' + str(id))
        plt.xlabel('Time in hours')
        plt.ylabel('Delayed el. power flexibility in kW')
        plt.legend()
        plt.show()
        plt.close()

    dict_flex['array_av_flex_delayed'] = array_av_flex_delayed
    dict_flex['array_cycle_flex_delayed'] = array_cycle_flex_delayed

    array_energy_flex_delayed = \
        calc_cycle_energy_delayed_year(timestep=timestep,
                                       array_cycle_flex_delayed=
                                       array_cycle_flex_delayed)

    energy_flex_delayed = sum(array_energy_flex_delayed) / (3600 * 1000)

    print('Energy flexibility in kWh for delayed operation:')
    print(energy_flex_delayed)

    dict_flex['energy_flex_delayed'] = energy_flex_delayed

    #  Calculate dimensionless electric power flexibility for forced operation
    array_alpha_el_delayed = \
        calc_dimless_el_power_flex(timestep=timestep,
                                   array_sh=array_sh,
                                   array_dhw=array_dhw,
                                   array_el_flex=
                                   array_cycle_flex_delayed)

    if plot_res:
        plt.plot(array_alpha_el_delayed)
        plt.title('alpha_el (delayed) for building ' + str(id))
        plt.xlabel('Time in hours')
        plt.ylabel('Dimensionless el. power flexibility alpha_el (delayed)')
        plt.show()
        plt.close()

    dict_flex['array_alpha_el_delayed'] = array_alpha_el_delayed

    #  Calculate energy flexibility for delayed operation
    array_beta_th_delayed = \
        calc_dimless_tes_el_flex(array_flex_energy=array_energy_flex_delayed,
                                 sh_dem=sh_dem,
                                 dhw_dem=dhw_dem)

    print('Dimensionless el. energy flexibility for delayed operation:')
    print(sum(array_beta_th_delayed))

    if plot_res:
        plt.plot(array_beta_th_delayed)
        plt.title('beta_el (delayed) for building ' + str(id))
        plt.xlabel('Time in hours')
        plt.ylabel('Dimensionless el. energy flexibility beta_el (delayed)')
        plt.show()
        plt.close()

    dict_flex['array_beta_th_delayed'] = array_beta_th_delayed

    print('#############################################################')
    print()

    return dict_flex


def perform_flex_analysis_sublhn(city, list_lhn, use_eh=False, mod_boi=False,
                                 plot_res=False):
    """
    Perform flexibility analysis for city district with (single) LHN

    Parameters
    ----------
    city : object
        City object of pyCity_calc
    list_lhn : list
        List holding LHN connected building node ids for given LHN
    use_eh : bool, optional
        Defines, if electric heater is also used to define t_forced_build
        (default: False).
    mod_boi : bool, optional
        Defines, if boiler size should be modified (CHP/BOI) /
        added (for HP/EH system) (default: True)
    plot_res : bool, optional
        Defines, if results should be plotted (default: False)

    Returns
    -------
    dict_flex : dict
        Dict holding results of flexibility analysis
            dict_flex['alpha_th'] = alpha_th
            dict_flex['beta_th'] = beta_th
            dict_flex['array_t_forced'] = array_t_forced
            dict_flex['array_t_delayed'] = array_t_delayed
            dict_flex['array_p_el_ref'] = array_p_el_ref
            dict_flex['array_av_flex_forced'] = array_av_flex_forced
            dict_flex['array_cycle_flex_forced'] = array_cycle_flex_forced
            dict_flex['array_energy_flex_forced'] = array_energy_flex_forced
            dict_flex['energy_flex_forced'] = energy_flex_forced
            dict_flex['array_alpha_el_forced'] = array_alpha_el_forced
            dict_flex['array_beta_th_forced'] = array_beta_th_forced
            dict_flex['array_av_flex_delayed'] = array_av_flex_delayed
            dict_flex['array_cycle_flex_delayed'] = array_cycle_flex_delayed
            dict_flex['energy_flex_delayed'] = energy_flex_delayed
            dict_flex['array_alpha_el_delayed'] = array_alpha_el_delayed
            dict_flex['array_beta_th_delayed'] = array_beta_th_delayed
    """

    dict_flex = {}

    #  Generate deepcopy of city object instance
    city_copy = copy.deepcopy(city)

    list_build_ids = city_copy.get_list_build_entity_node_ids()

    #  Delete all building nodes, which are not in list_lhn
    for n in list_build_ids:
        if n not in list_lhn:
            city_copy.remove_building(node_number=n)

    print('Process LHN connected buildings ' + str(list_lhn))
    print('#############################################################')

    timestep = city_copy.environment.timer.timeDiscretization

    #  Get maximal thermal output power of electric heat generators
    #  (CHPs)
    q_ehg_nom = 0  # in Watt
    p_ehg_nom = 0  # in Watt
    for n in list_lhn:
        curr_build = city_copy.nodes[n]['entity']
        if curr_build.hasBes:
            if curr_build.bes.hasChp:
                q_ehg_nom += curr_build.bes.chp.qNominal
                p_ehg_nom += curr_build.bes.chp.pNominal

    #  Calculate average building thermal power
    #  Extract thermal power curve of building
    array_sh = city_copy.get_aggr_space_h_power_curve()
    array_dhw = city_copy.get_aggr_dhw_power_curve()

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

    dict_flex['alpha_th'] = alpha_th

    #  Copy city to perform energy balance calculation (necessary to estimate
    #  stored amount of energy in each TES (if multipel TES exist in LHN))
    city_copy2 = copy.deepcopy(city)

    #  Generate city energy balance calculator object instance
    cit_eb_calc = citeb.CityEBCalculator(city=city_copy2)

    #  Calc. city energy balance
    cit_eb_calc.calc_city_energy_balance()

    #  Calculate average stored amount of energy in TES per timestep (for a
    #  whole year)

    #  Loop over buildings in sublhn
    en_av_tes = 0
    for n in list_lhn:
        curr_b = city_copy2.nodes[n]['entity']
        en_av_tes += calc_av_energy_tes_year(building=curr_b)

    #  Calculate dimensionless thermal storage energy flexibility
    beta_th = calc_dimless_tes_th_flex(sh_dem=sh_dem, dhw_dem=dhw_dem,
                                       en_av_tes=en_av_tes)

    print('Dimensionless thermal storage energy flexibility (beta_th): ')
    print(beta_th)
    print()

    dict_flex['beta_th'] = beta_th

    #  Calculate t_forced
    #  ###################################################################

    #  Generate virtual storage as sum of all existing storages
    mass_tes_v = 0
    for n in list_lhn:
        curr_b = city_copy.nodes[n]['entity']
        if curr_b.hasBes:
            if curr_b.bes.hasTes:
                mass_tes_v += curr_b.bes.tes.capacity
                t_max = curr_b.bes.tes.tMax + 0.0
                t_min = curr_b.bes.tes.t_min + 0.0
                c_p = curr_b.bes.tes.c_p + 0.0
                rho = curr_b.bes.tes.rho + 0.0
                k_loss = curr_b.bes.tes.k_loss + 0.0
                h_d_ratio = curr_b.bes.tes.h_d_ratio + 0.0

    tes_forced = \
        tessys.thermalEnergyStorageExtended(environment=city_copy.environment,
                                            t_init=0.8 * t_max,
                                            capacity=mass_tes_v, c_p=c_p,
                                            rho=rho,
                                            t_max=t_max,
                                            t_min=t_min,
                                            k_loss=k_loss,
                                            h_d_ratio=h_d_ratio)

    #  Calculate t_force array (with virtual TES)
    array_t_forced = calc_t_forced_build(q_ehg_nom=q_ehg_nom,
                                         array_sh=array_sh,
                                         array_dhw=array_dhw,
                                         timestep=timestep,
                                         tes=tes_forced)

    if plot_res:
        plt.plot(array_t_forced / 3600)
        plt.title('T_forced for sublhn ' + str(list_lhn))
        plt.xlabel('Time in hours')
        plt.ylabel('T_forced in hours')
        plt.show()
        plt.close()

    dict_flex['array_t_forced'] = array_t_forced

    #  Calculate t_delayed
    #  ###################################################################

    #  Calculate t_delayed array
    array_t_delayed = calc_t_delayed_build(q_ehg_nom=q_ehg_nom,
                                           array_sh=array_sh,
                                           array_dhw=array_dhw,
                                           timestep=timestep,
                                           tes=tes_forced,
                                           plot_soc=False,
                                           use_boi=False,
                                           q_boi_nom=None)

    if plot_res:
        plt.plot(array_t_delayed / 3600)
        plt.title('T_delayed for sublhn ' + str(list_lhn))
        plt.xlabel('Time in hours')
        plt.ylabel('T_delayed in hours')
        plt.show()
        plt.close()

    dict_flex['array_t_delayed'] = array_t_delayed

    #  Calculate reference EHG el. load curve
    #  ##################################################################
    array_p_el_ref = \
        calc_power_ref_curve_sublhn(city=city_copy, mod_boi=mod_boi,
                                    use_eh=use_eh)

    if plot_res:
        plt.plot(array_p_el_ref / 1000)
        plt.title('Ref. EHG power for sublhn ' + str(list_lhn))
        plt.xlabel('Time in hours')
        plt.ylabel('Reference EHG el. power in kW')
        plt.show()
        plt.close()

    dict_flex['array_p_el_ref'] = array_p_el_ref

    #  Calculate pow_force_flex for each timespan
    #  ##################################################################
    list_lists_pow_forced = calc_pow_flex_forced(timestep=timestep,
                                                 p_ehg_nom=p_ehg_nom,
                                                 array_t_forced=array_t_forced,
                                                 array_p_el_ref=array_p_el_ref)

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

    if plot_res:
        plt.plot(array_av_flex_forced / 1000, label='Average')
        plt.plot(array_cycle_flex_forced / 1000, label='Cycle')
        plt.title('Forced power flex. for sublhn ' + str(list_lhn))
        plt.xlabel('Time in hours')
        plt.ylabel('Forced el. power flexibility in kW')
        plt.legend()
        plt.tight_layout()
        plt.show()
        plt.close()

    dict_flex['array_av_flex_forced'] = array_av_flex_forced
    dict_flex['array_cycle_flex_forced'] = array_cycle_flex_forced

    #  Calculate force energy flexibility
    array_energy_flex_forced = \
        calc_cycle_energy_forced_year(timestep=timestep,
                                      array_cycle_flex_forced=
                                      array_cycle_flex_forced)

    energy_flex_forced = sum(array_energy_flex_forced) / (3600 * 1000)

    print('Energy flexibility in kWh for forced operation:')
    print(energy_flex_forced)

    dict_flex['array_energy_flex_forced'] = array_energy_flex_forced
    dict_flex['energy_flex_forced'] = energy_flex_forced

    #  Calculate dimensionless electric power flexibility for forced operation
    array_alpha_el_forced = \
        calc_dimless_el_power_flex(timestep=timestep,
                                   array_sh=array_sh,
                                   array_dhw=array_dhw,
                                   array_el_flex=
                                   array_cycle_flex_forced)

    if plot_res:
        plt.plot(array_alpha_el_forced)
        plt.title('alpha_el (forced) for sublhn ' + str(list_lhn))
        plt.xlabel('Time in hours')
        plt.ylabel('Dimensionless el. power flexibility alpha_el (forced)')
        plt.show()
        plt.close()

    dict_flex['array_alpha_el_forced'] = array_alpha_el_forced

    #  Calculate energy flexibility for forced operation
    array_beta_th_forced = \
        calc_dimless_tes_el_flex(array_flex_energy=array_energy_flex_forced,
                                 sh_dem=sh_dem,
                                 dhw_dem=dhw_dem)

    print('Dimensionless el. energy flexibility for force operation:')
    print(sum(array_beta_th_forced))
    print()

    if plot_res:
        plt.plot(array_beta_th_forced)
        plt.title('beta_el (forced) for sublhn ' + str(list_lhn))
        plt.xlabel('Time in hours')
        plt.ylabel('Dimensionless el. energy flexibility beta_el (forced)')
        plt.show()
        plt.close()

    dict_flex['array_beta_th_forced'] = array_beta_th_forced

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

    #  Convert pre-sign to minus, as CHP systems are used in LHN)
    array_av_flex_delayed *= -1
    array_cycle_flex_delayed *= -1

    if plot_res:
        plt.plot(array_av_flex_delayed / 1000, label='Average')
        plt.plot(array_cycle_flex_delayed / 1000, label='Cycle')
        plt.title('Delayed el. power flex. for sublhn ' + str(list_lhn))
        plt.xlabel('Time in hours')
        plt.ylabel('Delayed el. power flexibility in kW')
        plt.legend()
        plt.show()
        plt.close()

    dict_flex['array_av_flex_delayed'] = array_av_flex_delayed
    dict_flex['array_cycle_flex_delayed'] = array_cycle_flex_delayed

    array_energy_flex_delayed = \
        calc_cycle_energy_delayed_year(timestep=timestep,
                                       array_cycle_flex_delayed=
                                       array_cycle_flex_delayed)

    energy_flex_delayed = sum(array_energy_flex_delayed) / (3600 * 1000)

    print('Energy flexibility in kWh for delayed operation:')
    print(energy_flex_delayed)

    dict_flex['energy_flex_delayed'] = energy_flex_delayed

    #  Calculate dimensionless electric power flexibility for forced operation
    array_alpha_el_delayed = \
        calc_dimless_el_power_flex(timestep=timestep,
                                   array_sh=array_sh,
                                   array_dhw=array_dhw,
                                   array_el_flex=
                                   array_cycle_flex_delayed)
    if plot_res:
        plt.plot(array_alpha_el_delayed)
        plt.title('alpha_el (delayed) for sublhn ' + str(list_lhn))
        plt.xlabel('Time in hours')
        plt.ylabel('Dimensionless el. power flexibility alpha_el (delayed)')
        plt.show()
        plt.close()

    dict_flex['array_alpha_el_delayed'] = array_alpha_el_delayed

    #  Calculate energy flexibility for delayed operation
    array_beta_th_delayed = \
        calc_dimless_tes_el_flex(array_flex_energy=array_energy_flex_delayed,
                                 sh_dem=sh_dem, dhw_dem=dhw_dem)

    print('Dimensionless el. energy flexibility for delayed operation:')
    print(sum(array_beta_th_delayed))

    if plot_res:
        plt.plot(array_beta_th_delayed)
        plt.title('beta_el (delayed) for sublhn ' + str(list_lhn))
        plt.xlabel('Time in hours')
        plt.ylabel('Dimensionless el. energy flexibility beta_el (delayed)')
        plt.show()
        plt.close()

    dict_flex['array_beta_th_delayed'] = array_beta_th_delayed

    print('#############################################################')
    print()

    return dict_flex


def perform_flex_analysis_city(city, use_eh=False, mod_boi=False,
                               plot_res=False):
    """
    Perform flexibility analysis for city object instance

    Parameters
    ----------
    city : object
        City object of pyCity_calc
    use_eh : bool, optional
        Defines, if electric heater is also used to define t_forced_build
        (default: False).
    mod_boi : bool, optional
        Defines, if boiler size should be modified (CHP/BOI) /
        added (for HP/EH system) (default: True)
    plot_res : bool, optional
        Defines, if results should be plotted (default: False)

    Returns
    -------
    dict_flex_city : dict
        Dict holding flexibility results for whole city
            dict_flex_city['list_alpha_el_forced'] = list_alpha_el_forced
            dict_flex_city['list_alpha_el_delayed'] = list_alpha_el_delayed
            dict_flex_city['array_cycle_flex_forced_plus'] = \
                array_cycle_flex_forced_plus
            dict_flex_city['array_cycle_flex_forced_minus'] = \
                array_cycle_flex_forced_minus
            dict_flex_city['array_cycle_flex_delayed_plus'] = \
                array_cycle_flex_delayed_plus
            dict_flex_city['array_cycle_flex_delayed_minus'] = \
                array_cycle_flex_delayed_minus
            dict_flex_city['energy_flex_forced_pos']
            dict_flex_city['energy_flex_forced_neg']
            dict_flex_city['energy_flex_delayed_pos']
            dict_flex_city['energy_flex_delayed_neg']
    """

    timestep = city.environment.timer.timeDiscretization

    dict_flex_city = {}

    list_alpha_el_forced = []
    list_alpha_el_delayed = []
    array_cycle_flex_forced_plus = np.zeros(int(3600 * 24 * 365 / timestep))
    array_cycle_flex_forced_minus = np.zeros(int(3600 * 24 * 365 / timestep))
    array_cycle_flex_delayed_plus = np.zeros(int(3600 * 24 * 365 / timestep))
    array_cycle_flex_delayed_minus = np.zeros(int(3600 * 24 * 365 / timestep))
    dict_flex_city['energy_flex_forced_pos'] = 0
    dict_flex_city['energy_flex_forced_neg'] = 0
    dict_flex_city['energy_flex_delayed_pos'] = 0
    dict_flex_city['energy_flex_delayed_neg'] = 0

    dict_flex_city['list_alpha_el_forced'] = list_alpha_el_forced
    dict_flex_city['list_alpha_el_delayed'] = list_alpha_el_delayed
    dict_flex_city['array_cycle_flex_forced_plus'] = \
        array_cycle_flex_forced_plus
    dict_flex_city['array_cycle_flex_forced_minus'] = \
        array_cycle_flex_forced_minus
    dict_flex_city['array_cycle_flex_delayed_plus'] = \
        array_cycle_flex_delayed_plus
    dict_flex_city['array_cycle_flex_delayed_minus'] = \
        array_cycle_flex_delayed_minus

    #  Get list of buildings (with and without LHN connections
    #  ######################################################################
    #  Get list building ids
    list_build_ids = city.get_list_build_entity_node_ids()

    #  Find LHN connected buildings (--> Process as single flexibility entity)
    #  List of lists of building interconnected nodes (heating)
    list_lists_lhn_ids_build = \
        netop.get_list_with_energy_net_con_node_ids(city=city,
                                                    network_type='heating',
                                                    build_node_only=True)

    #  Make flat list with lhn conn. buildings
    list_lhn_build = []

    for sublhn in list_lists_lhn_ids_build:
        for id in sublhn:
            list_lhn_build.append(id)

    #  Find stand alone buildings
    list_stand_alone_build = list(set(list_build_ids) - set(list_lhn_build))
    #  ######################################################################

    #  Process LHN connected buildings
    #  ######################################################################
    for sublhn in list_lists_lhn_ids_build:
        dict_flex = perform_flex_analysis_sublhn(city=city,
                                                 list_lhn=sublhn,
                                                 use_eh=use_eh,
                                                 mod_boi=mod_boi,
                                                 plot_res=plot_res)

        dict_flex_city['list_alpha_el_forced']. \
            append(dict_flex['array_alpha_el_forced'])
        dict_flex_city['list_alpha_el_delayed']. \
            append(dict_flex['array_alpha_el_delayed'])

        if max(dict_flex['array_cycle_flex_forced']) >= 0:
            dict_flex_city['array_cycle_flex_forced_plus'] += \
                dict_flex['array_cycle_flex_forced']
        else:
            dict_flex_city['array_cycle_flex_forced_minus'] += \
                dict_flex['array_cycle_flex_forced']
        if max(dict_flex['array_cycle_flex_delayed']) >= 0:
            dict_flex_city['array_cycle_flex_delayed_plus'] += \
                dict_flex['array_cycle_flex_delayed']
        else:
            dict_flex_city['array_cycle_flex_delayed_minus'] += \
                dict_flex['array_cycle_flex_delayed']

        if dict_flex['energy_flex_forced'] >= 0:
            dict_flex_city['energy_flex_forced_pos'] += \
                abs(dict_flex['energy_flex_forced'])
        else:
            dict_flex_city['energy_flex_forced_neg'] += \
                abs(dict_flex['energy_flex_forced'])

        if dict_flex['energy_flex_delayed'] >= 0:
            dict_flex_city['energy_flex_delayed_pos'] += \
                abs(dict_flex['energy_flex_delayed'])
        else:
            dict_flex_city['energy_flex_delayed_neg'] += \
                abs(dict_flex['energy_flex_delayed'])

    #  Process stand alone buildings
    #  ######################################################################
    for n in list_stand_alone_build:
        curr_build = city.nodes[n]['entity']

        dict_flex = perform_flex_analysis_single_build(build=curr_build,
                                                       use_eh=use_eh,
                                                       mod_boi=mod_boi,
                                                       id=n, plot_res=plot_res)

        dict_flex_city['list_alpha_el_forced']. \
            append(dict_flex['array_alpha_el_forced'])
        dict_flex_city['list_alpha_el_delayed']. \
            append(dict_flex['array_alpha_el_delayed'])
        if sum(dict_flex['array_cycle_flex_forced']) >= 0:
            dict_flex_city['array_cycle_flex_forced_plus'] += \
                dict_flex['array_cycle_flex_forced']
        else:
            dict_flex_city['array_cycle_flex_forced_minus'] += \
                dict_flex['array_cycle_flex_forced']
        if sum(dict_flex['array_cycle_flex_delayed']) >= 0:
            dict_flex_city['array_cycle_flex_delayed_plus'] += \
                dict_flex['array_cycle_flex_delayed']
        else:
            dict_flex_city['array_cycle_flex_delayed_minus'] += \
                dict_flex['array_cycle_flex_delayed']

        if dict_flex['energy_flex_forced'] >= 0:
            dict_flex_city['energy_flex_forced_pos'] += \
                abs(dict_flex['energy_flex_forced'])
        else:
            dict_flex_city['energy_flex_forced_neg'] += \
                abs(dict_flex['energy_flex_forced'])

        if dict_flex['energy_flex_delayed'] >= 0:
            dict_flex_city['energy_flex_delayed_pos'] += \
                abs(dict_flex['energy_flex_delayed'])
        else:
            dict_flex_city['energy_flex_delayed_neg'] += \
                abs(dict_flex['energy_flex_delayed'])

    return dict_flex_city


# def calc_sum_city_flexibilities(timestep, dict_flex_city):
#     """
#     Calculate sum of flexibilities within city
#
#     Parameters
#     ----------
#     timestep : int
#         Timestep in seconds
#     dict_flex_city : dict
#         Dict holding flexibility results for whole city
#             dict_flex_city['list_alpha_el_forced'] = list_alpha_el_forced
#             dict_flex_city['list_alpha_el_delayed'] = list_alpha_el_delayed
#             dict_flex_city['array_cycle_flex_forced_plus'] = \
#                 array_cycle_flex_forced_plus
#             dict_flex_city['array_cycle_flex_forced_minus'] = \
#                 array_cycle_flex_forced_minus
#             dict_flex_city['array_cycle_flex_delayed_plus'] = \
#                 array_cycle_flex_delayed_plus
#             dict_flex_city['array_cycle_flex_delayed_minus'] = \
#                 array_cycle_flex_delayed_minus
#
#     Returns
#     -------
#     tup_res : tuple (of floats)
#         Tuple with summed of positive and negative energy flexibilities in kWh
#         en_flex_forced_pos, en_flex_forced_neg, en_flex_delayed_pos,
#             en_flex_delayed_neg)
#     """
#
#     en_flex_forced_pos = 0  # Generation (forced) (CHP)
#     en_flex_forced_neg = 0  # Consumption (forced) (HP)
#     en_flex_delayed_pos = 0  # Reference consumption blocked (delayed) (HP)
#     en_flex_delayed_neg = 0  # Reference generation blocked (delayed) (CHP)
#
#     en_flex_forced_pos += \
#         sum(dict_flex_city['array_cycle_flex_forced_plus']) \
#                           * timestep / (3600 * 1000)
#     en_flex_forced_neg += \
#         sum(dict_flex_city['array_cycle_flex_forced_minus']) \
#                           * timestep / (3600 * 1000)
#
#     en_flex_delayed_pos += \
#         sum(dict_flex_city['array_cycle_flex_delayed_plus']) \
#         * timestep / (3600 * 1000)
#     en_flex_delayed_neg += \
#         sum(dict_flex_city['array_cycle_flex_delayed_minus']) \
#                            * timestep / (3600 * 1000)
#
#     return (en_flex_forced_pos, en_flex_forced_neg, en_flex_delayed_pos,
#             en_flex_delayed_neg)

def main():
    #  Perform flexibility calculation for whole city district

    time_start = time.time()

    #  Add energy system, if no energy system exists on city.pkl file
    #  Necessary to perform flexibility calculation
    add_esys = True

    mod_boi = True  # Add boiler, if necessary to solve energy balance to
    #  calculate reference ehg electric load

    use_eh = False  # If True, also accounts for electric heater power to
    #  quantify flexiblity

    plot_res = False

    city_name = 'aachen_kronenberg_6.pkl'
    path_here = os.path.dirname(os.path.abspath(__file__))
    path_city = os.path.join(path_here, 'input', city_name)

    city = pickle.load(open(path_city, mode='rb'))

    if add_esys:
        dict_data_entry = {'type': 'heating', 'method': 1,
                           'nodelist': [1001, 1002]}

        dict_data = {1: dict_data_entry}

        #  Add LHN network to all buildings
        enetgen.add_energy_networks_to_city(city=city,
                                            dict_data=dict_data)

        #  Add energy system
        #  Generate one feeder with CHP, boiler and TES
        list_esys = [(1001, 1, 4),  # CHP, Boiler, TES, with LHN to 1002
                     # (1002, 1, 4),
                     (1003, 1, 4),
                     (1004, 2, 2),  # HP (ww), EH, TES
                     (1005, 2, 2),
                     (1006, 2, 2)]

        esysgen.gen_esys_for_city(city=city,
                                  list_data=list_esys,
                                  dhw_scale=True)

    dict_flex_city = perform_flex_analysis_city(city=city,
                                                use_eh=use_eh,
                                                mod_boi=mod_boi,
                                                plot_res=plot_res)

    en_flex_forced_pos = dict_flex_city['energy_flex_forced_pos']
    en_flex_forced_neg = dict_flex_city['energy_flex_forced_neg']
    en_flex_delayed_pos = dict_flex_city['energy_flex_delayed_pos']
    en_flex_delayed_neg = dict_flex_city['energy_flex_delayed_neg']

    print('Positive energy flexibility (forced) in kWh (CHP):')
    print(en_flex_forced_pos)
    print()
    print('Negative energy flexibility (forced) in kWh (HP):')
    print(en_flex_forced_neg)
    print()

    print('Positive energy flexibility (delayed) in kWh (HP):')
    print(en_flex_delayed_pos)
    print()
    print('Negative energy flexibility (delayed) in kWh (CHP):')
    print(en_flex_delayed_neg)
    print()

    time_stop = time.time()

    delta_t = time_stop - time_start

    print('Required runtime for execution in seconds: ')
    print(round(delta_t, 0))

    nb_build = city.get_nb_of_building_entities()

    print('Average runtime per building in seconds: ')
    print(int(delta_t / nb_build))


def main2():
    #  Perform flexibility analysis for single building

    #  Add energy system, if no energy system exists on city.pkl file
    #  Necessary to perform flexibility calculation
    add_esys = True

    build_id = 1001

    mod_boi = True  # Add boiler, if necessary to solve energy balance to
    #  calculate reference ehg electric load

    use_eh = False  # If True, also accounts for electric heater power to
    #  quantify flexiblity

    plot_res = True

    city_name = 'aachen_kronenberg_6.pkl'
    path_here = os.path.dirname(os.path.abspath(__file__))
    path_city = os.path.join(path_here, 'input', city_name)

    city = pickle.load(open(path_city, mode='rb'))

    if add_esys:
        # dict_data_entry = {'type': 'heating', 'method': 1,
        #                    'nodelist': [1001, 1002]}
        #
        # dict_data = {1: dict_data_entry}
        #
        # #  Add LHN network to all buildings
        # enetgen.add_energy_networks_to_city(city=city,
        #                                     dict_data=dict_data)

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

    perform_flex_analysis_single_build(build=curr_build,
                                       use_eh=use_eh,
                                       mod_boi=mod_boi,
                                       id=build_id,
                                       plot_res=plot_res)


if __name__ == '__main__':
    # main()
    main2()
