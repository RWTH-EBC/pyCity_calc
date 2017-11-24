# coding=utf-8
"""
Script for energy balance calculation. Holds calculator class.
"""

__author__ = 'tsh-dor'

import os
import sys
import pickle
import copy
import time as ti
import itertools
import numpy as np
import matplotlib.pyplot as plt
import pycity_calc.toolbox.networks.network_ops as netop
import pycity_calc.environments.timer as time
import pycity_calc.visualization.city_visual as citvis
import pycity_calc.toolbox.dimensioning.dim_networks as dimnet
import pycity_calc.toolbox.dimensioning.dhw_manipulator as dhwman


class calculator(object):
    def __init__(self, city_object):
        """
        Constructor of calculation class. Adds pointer to city_object.

        Parameters
        ----------
        city_object : object
            City object of pycity_calc
        """

        self.city_object = city_object

    def grids(self):
        """
        Method extracts information about energy network interconnected
        buildings and single buildings within city.

        Returns
        -------
        grids : list (of lists)
            List, holding lists of grid interconnected buildings (lhn or deg)
            and single building lists (not connected to energy networks)
        lhn_con : list (of lists)
            List, holding lists of lhn connected buildings
        deg_con : list (of lists)
            List, holding lists of deg connected buildings
        """

        #  Get list of lists of lhn connected building node ids
        lhn_con = \
            netop.get_list_with_energy_net_con_node_ids(self.city_object,
                                                        network_type='heating')

        #  Get list of lists of deg connected building node ids
        deg_con = \
            netop.get_list_with_energy_net_con_node_ids(self.city_object,
                                                        network_type='electricity')

        #  Get list of all nodes of building entities
        all_building_nodes = self.city_object.get_list_build_entity_node_ids()

        #  Total grid connected list (might still hold double entries
        #  for heating_and_deg connections)
        grids_cumulated = lhn_con + deg_con

        #  Eliminate double entries. Add list of grid interconnected buildings,
        #  only.
        #  TODO: Does not work for different network interconnections
        grids_cumulated.sort()
        grids = list(grids_cumulated for grids_cumulated, _ in
                     itertools.groupby(grids_cumulated))

        nodes_with_grid = []
        nodes_without_grid_list = []
        for subcity in range(len(grids)):
            for node in range(len(grids[subcity])):
                nodes_with_grid.append(grids[subcity][node])

        for x in all_building_nodes:
            if (x in nodes_with_grid) == False:
                nodes_without_grid = []
                nodes_without_grid.append(x)
                nodes_without_grid_list.append(nodes_without_grid)

        # Generate grids lists, holding list of lhn and deg interconnected
        #  buildings as well as single buildings
        grids_cumulated = lhn_con + deg_con + nodes_without_grid_list
        grids_cumulated.sort()
        grids = list(grids_cumulated for grids_cumulated, _ in
                     itertools.groupby(grids_cumulated))

        #  Calculate network lenght
        # netop.add_weights_to_edges(self.city_object)
        # lengths_of_networks = netop.calc_length_of_grids(self.city_object,
        #                                                  grids)

        #  List of all lhn and/or deg interconnected buidings and single
        return (grids, lhn_con, deg_con)

    def assembler(self):
        """
        assembler method is collecting all relevant data in the city_object
        such as building energy systems for instance;
        loop over all subcities in city -> checks each node attributes

        Returns
        -------
        dict_bes_data : dict
            Dictionary, holding integer number as key (starting from 0) and
            bes dictionary as values. bes dictionary is holding attributes:
            'Buildings with bes' (list of building node ids with bes)
            'hasDEG' (boolean. Definse, if deg exists)
            'Building in subcity' (list of building node ids, which are
            interconnected
            'hasLHN' (boolean. Defines, if lhn exists)
        """

        #  Call grids method
        (grids, lhn_con, deg_con) = self.grids()

        print('Grids in assembler:', grids)
        print('LHN con in assembler: ', lhn_con)
        print('DEG con in assembler:', deg_con)

        dict_bes_data = {}

        for subcity in range(len(grids)):

            if grids[subcity] in lhn_con:
                hasLHN = True
            else:
                hasLHN = False

            if grids[subcity] in deg_con:
                hasDEG = True
            else:
                hasDEG = False

            building_with_bes = []
            for node in range(len(grids[subcity])):
                Node = self.city_object.nodes[grids[subcity][node]]
                if ('entity' in Node) == True:
                    if Node['entity']._kind == 'building':
                        if (Node['entity'].hasBes):
                            id_building_with_bes = grids[subcity][node]
                            building_with_bes.append(id_building_with_bes)

            city_dict = {"Buildings in subcity": grids[subcity],
                         "Buildings with bes": building_with_bes,
                         "hasLHN": hasLHN, "hasDEG": hasDEG}
            dict_bes_data[subcity] = city_dict

        return dict_bes_data

    def eb_balances(self, dict_city_data, index):
        """
        eb_balances is divided into two main and two subsections:
        Main: Thermal and electrical calculations
        Sub: With Grids and without grids
        Another difference are storages;
        If there are some calculations are different

        Parameters
        ----------
        dict_city_data : dict
            dictionary which is created by assembler
        index : int
            number of the subcity
        """

        tes_temp = []
        tes_load = []
        tes_unload = []
        #  TODO: Erase lists, when tes info is loaded from tes object itself

        #  You can add the boiler_temp to every boiler object and later
        #  save the city as results_object
        # time vector needed to initialise the length of arrays
        time_vector = time.TimerExtended(
            timestep=self.city_object.environment.timer.timeDiscretization)

        #  ############################################
        #  If subcity does not hold lhn connection
        if (dict_city_data[index]['hasLHN']) == False:

            #  Loop over building list in subcity
            for i in range(len(dict_city_data[index]['Buildings with bes'])):

                #  Pointer to current node
                Node = self.city_object.nodes[
                    dict_city_data[index]['Buildings in subcity'][i]]

                #  Check if single building holds bes
                if Node['entity'].hasBes == False:
                    raise AssertionError("Since there is no lhn, building",
                                         dict_city_data[index][
                                             'Buildings in subcity'][
                                             i],
                                         "needs a thermal supply system!")

                # Check if bes holds thermal energy system
                has_th_e_sys = False  # Init value
                if (Node['entity'].bes.hasBoiler or
                        Node['entity'].bes.hasChp or
                        Node['entity'].bes.hasElectricalHeater or
                        Node['entity'].bes.hasHeatpump):
                    has_th_e_sys = True

                if has_th_e_sys == False:
                    raise AssertionError(
                        'Node ' + str(Node) + ' is not holding'
                                              'thermal energy system, but this is '
                                              'required for single building!')

                # Since no lhn is available the balances has to be done for
                # each building!
                power_boiler_total = []

                #  Current bes
                Bes = Node['entity'].bes

                Node['electricity_heatpump'] = np.zeros(
                    len(time_vector.time_vector()))
                Node['fuel_demand'] = np.zeros(len(time_vector.time_vector()))
                #  TODO: Save to energy systems, instead

                #  #---------------------------------------------------------
                if (Node['entity'].bes.hasHeatpump) == True:
                    #  Script for Building with HP, Eh and Tes

                    power_hp_total = []
                    power_eh_total = []
                    #  TODO: Why saving results on node instead of energy system?

                    #  Get heat pump nominals
                    hp_qNominal = Node['entity'].bes.heatpump.qNominal
                    hp_lal = Node['entity'].bes.heatpump.lowerActivationLimit
                    eh_qNominal = Node['entity'].bes.electricalHeater.qNominal

                    #  Get space heating demand of building
                    sph_demand_building = Node[
                        'entity'].get_space_heating_power_curve()

                    #  TODO: Allow user to define, if dhw should be used, too

                    #  Get building hot water demand
                    dhw_demand_building = Node['entity'].get_dhw_power_curve()

                    #  Aggregate demand curves
                    thermal_demand_building = sph_demand_building + \
                                              dhw_demand_building
                    array_temp = self.city_object.environment.weather.tAmbient

                    #  #-----------------------------------------------------
                    if (Node['entity'].bes.hasTes) == True:

                        #  Start temperature of the storage is set as t
                        #  surrounding + buffer!
                        t_tes = Bes.tes.t_surroundings + 0.01
                        #  TODO: Do we net buffer factor?

                        #  Loop over thermal demand of building
                        for ii in range(len(thermal_demand_building)):

                            #  Define max. possible input/output power of tes
                            q_out_max_tes = Bes.tes.calc_storage_q_out_max(
                                t_ambient=20, q_in=0)
                            q_in_max_tes = Bes.tes.calc_storage_q_in_max(
                                t_ambient=20, q_out=0)

                            #  Calculate max load power (max. supply mimus
                            #  current demand)
                            load_power_max = hp_qNominal + eh_qNominal - \
                                             thermal_demand_building[ii]
                            #  Calculate max hp load power (max. hp power minus
                            #  current demand)
                            load_power = hp_qNominal - thermal_demand_building[
                                ii]

                            #  #---------------------------------------------
                            if load_power_max < 0:
                                #  Thermal building demand is larger than
                                #  nominal hp and eh power!
                                #  In case of peak load eh has to run under
                                #  full load conditions!!!
                                assert q_out_max_tes > -load_power, (
                                    "TES is now empty and can't be unloaded")

                                #  Calc. temperature of next timestep
                                t_tes = \
                                    Bes.tes.calc_storage_temp_for_next_timestep(
                                        q_in=0 - 0.01, q_out=-load_power_max,
                                        t_prior=t_tes, t_ambient=20,
                                        set_new_temperature=True,
                                        save_res=True,
                                        time_index=ii)

                                #  Calculate power of heat pump (max.)
                                power_hp = \
                                    Bes.heatpump.calc_hp_all_results(
                                        hp_qNominal, array_temp[ii], ii)[1]

                                #  Calculate power of el. heater (max.)
                                power_eh = \
                                    Bes.electricalHeater.calc_el_h_all_results(
                                        eh_qNominal, ii)[1]

                                #  Charging power (zero)
                                tes_load_power = 0
                                #  Uncharging power
                                tes_unload_power = -load_power_max

                            # #---------------------------------------------
                            #  Thermal demand of building is larger than
                            #  possible part load power of hp, but smaller than
                            #  nominal hp power --> HP can supply full power
                            #  and charge storage
                            elif thermal_demand_building[
                                ii] > hp_lal * hp_qNominal and load_power > 0:

                                if q_in_max_tes > 0 and load_power > q_in_max_tes:
                                    #  Boiler supplies house and loads storage
                                    #  with full load

                                    t_tes = Bes.tes.calc_storage_temp_for_next_timestep(
                                        q_in=q_in_max_tes - 0.01, q_out=0,
                                        t_prior=t_tes, t_ambient=20,
                                        set_new_temperature=True,
                                        save_res=True,
                                        time_index=ii)

                                    power_hp = \
                                        Bes.heatpump.calc_hp_all_results(
                                            sph_demand_building[ii] + 3 / 4 *
                                            dhw_demand_building[
                                                ii] + 3 / 4 * q_in_max_tes,
                                            array_temp[ii], ii)[1]

                                    power_eh = \
                                        Bes.electricalHeater.calc_el_h_all_results(
                                            1 / 4 * dhw_demand_building[
                                                ii] + 1 / 4 * q_in_max_tes,
                                            ii)[1]

                                    tes_load_power = q_in_max_tes
                                    tes_unload_power = 0

                                elif q_in_max_tes > 0 and load_power < \
                                        q_in_max_tes:
                                    # Boiler supplies house and loads storage
                                    # with part load
                                    assert load_power > 0, ("negative load "
                                                            "impossible --> check size tes and"
                                                            " demand dhw!")

                                    t_tes = Bes.tes.calc_storage_temp_for_next_timestep(
                                        q_in=load_power - 0.01, q_out=0,
                                        t_prior=t_tes, t_ambient=20,
                                        set_new_temperature=True,
                                        save_res=True,
                                        time_index=ii)

                                    power_hp = \
                                        Bes.heatpump.calc_hp_all_results(
                                            sph_demand_building[ii] + 3 / 4 *
                                            dhw_demand_building[
                                                ii] + 3 / 4 * load_power,
                                            array_temp[ii], ii)[1]

                                    #  TODO: How do we know that el_heater can supply 1/4 of dhw demand?
                                    power_eh = \
                                        Bes.electricalHeater.calc_el_h_all_results(
                                            1 / 4 * dhw_demand_building[
                                                ii] + 1 / 4 * load_power, ii)[
                                            1]

                                    tes_load_power = load_power
                                    tes_unload_power = 0

                            # #---------------------------------------------
                            #  Thermal demand power of building is smaller than
                            #  part load behavior of heat pump
                            if thermal_demand_building[
                                ii] < hp_lal * hp_qNominal:

                                if q_out_max_tes > 0 and q_out_max_tes > \
                                        thermal_demand_building[ii]:
                                    # tes has enough energy to unload

                                    t_tes = Bes.tes.calc_storage_temp_for_next_timestep(
                                        q_in=0,
                                        q_out=thermal_demand_building[ii],
                                        t_prior=t_tes, t_ambient=20,
                                        set_new_temperature=True,
                                        save_res=True,
                                        time_index=ii)

                                    power_hp = 0
                                    power_eh = 0
                                    tes_load_power = 0
                                    tes_unload_power = thermal_demand_building[
                                        ii]

                                elif q_out_max_tes > 0 and q_out_max_tes < \
                                        thermal_demand_building[ii]:
                                    #  Storage doesn't have enough energy to
                                    #  unload

                                    hp_max_load_power = hp_qNominal - \
                                                        thermal_demand_building[
                                                            ii]
                                    # for loading the eh should not be used
                                    # due to its bad efficiency
                                    if hp_max_load_power > q_in_max_tes:
                                        #  Use heat pump only

                                        #  Charge storage with heat pump
                                        t_tes = Bes.tes.calc_storage_temp_for_next_timestep(
                                            q_in=q_in_max_tes - 0.01, q_out=0,
                                            t_prior=t_tes, t_ambient=20,
                                            set_new_temperature=True,
                                            save_res=True,
                                            time_index=ii)

                                        #  Use heat pump to cover space heating
                                        #  and charge storage
                                        power_hp = \
                                            Bes.heatpump.calc_hp_all_results(
                                                sph_demand_building[
                                                    ii] + 3 / 4 *
                                                dhw_demand_building[
                                                    ii] + 3 / 4 * q_in_max_tes,
                                                array_temp[ii], ii)[1]

                                        power_eh = \
                                            Bes.heater.calc_el_h_all_results(
                                                1 / 4 * dhw_demand_building[
                                                    ii] + 1 / 4 * q_in_max_tes,
                                                ii)[1]

                                        tes_load_power = q_in_max_tes
                                        tes_unload_power = 0

                                    elif hp_max_load_power < q_in_max_tes:
                                        #  Heat pump can cover building
                                        #  thermal power demand, but cannot
                                        #  charge storage with full power

                                        t_tes = Bes.tes.calc_storage_temp_for_next_timestep(
                                            q_in=hp_max_load_power - 0.01,
                                            q_out=0, t_prior=t_tes,
                                            t_ambient=20,
                                            set_new_temperature=True,
                                            save_res=True,
                                            time_index=ii)

                                        power_hp = \
                                            Bes.heatpump.calc_hp_all_results(
                                                sph_demand_building[
                                                    ii] + 3 / 4 *
                                                dhw_demand_building[
                                                    ii] + 3 / 4 * hp_max_load_power,
                                                array_temp[ii], ii)[1]

                                        power_eh = \
                                            Bes.electricalHeater.calc_el_h_all_results(
                                                1 / 4 * dhw_demand_building[
                                                    ii] + 1 / 4 * hp_max_load_power,
                                                ii)[1]

                                        tes_load_power = hp_max_load_power
                                        tes_unload_power = 0

                                elif q_out_max_tes == 0:
                                    #  Storage is empty

                                    hp_max_load_power = \
                                        hp_qNominal - \
                                        thermal_demand_building[ii]

                                    t_tes = Bes.tes.calc_storage_temp_for_next_timestep(
                                        q_in=hp_max_load_power - 0.01, q_out=0,
                                        t_prior=t_tes, t_ambient=20,
                                        set_new_temperature=True,
                                        save_res=True,
                                        time_index=ii)

                                    power_hp = \
                                        Bes.heatpump.calc_hp_all_results(
                                            sph_demand_building[ii] + 3 / 4 *
                                            dhw_demand_building[
                                                ii] + 3 / 4 * hp_max_load_power,
                                            array_temp[ii], ii)[1]

                                    power_eh = \
                                        Bes.electricalHeater.calc_el_h_all_results(
                                            1 / 4 * dhw_demand_building[
                                                ii] + 1 / 4 * hp_max_load_power,
                                            ii)[1]

                                    tes_load_power = hp_max_load_power
                                    tes_unload_power = 0

                            power_hp_total.append(power_hp)
                            power_eh_total.append(power_eh)

                            tes_temp.append(t_tes)
                            tes_load.append(tes_load_power)
                            tes_unload.append(tes_unload_power)

                    Node['fuel_demand'] = 0
                    Node['electricity_heatpump'] = (
                        np.array(power_hp_total) + np.array(power_eh_total))

                #  #------------------------------------------------------
                #  E. balance for chp usage
                if (Node['entity'].bes.hasChp) == True:
                    # Script for Building with CHP, Boiler and Tes

                    tes_object = Bes.tes

                    #  Get chp and boiler nominals
                    chp_qNominal = Node['entity'].bes.chp.qNominal
                    # chp_pNominal = Node['entity'].bes.chp.pNominal
                    chp_lal = Node['entity'].bes.chp.lowerActivationLimit
                    boiler_qNominal = Node['entity'].bes.boiler.qNominal
                    boiler_lal = Node['entity'].bes.boiler.lowerActivationLimit

                    sph_demand_building = Node[
                        'entity'].get_space_heating_power_curve()

                    dhw_demand_building = Node['entity'].get_dhw_power_curve()
                    thermal_demand_building = sph_demand_building + \
                                              dhw_demand_building
                    # Start temperature of the storage is set as t surrounding!
                    t_tes = tes_object.t_surroundings

                    power_th_chp_list = []
                    power_el_chp_list = []
                    power_boiler_total = []
                    tes_load = []
                    tes_unload = []
                    tes_temp = []

                    #  Loop over every timestep
                    #  #-----------------------------------------------------
                    for ii in range(len(thermal_demand_building)):

                        q_out_max_tes = Bes.tes.calc_storage_q_out_max(
                            t_ambient=20, q_in=0)
                        q_in_max_tes = Bes.tes.calc_storage_q_in_max(
                            t_ambient=20, q_out=0)

                        load_power = chp_qNominal - \
                                     thermal_demand_building[ii]

                        #  #-------------------------------------------------
                        if thermal_demand_building[ii] > chp_qNominal:
                            #  Thermal demand power  of building is larger than
                            #  nominal thermal chp power

                            if thermal_demand_building[ii] > (
                                        boiler_qNominal + chp_qNominal):
                                #  Thermal demand power of building is larger
                                #  than boiler and chp nominals. Requires
                                #  thermal storage usage

                                #  Power differenz
                                diff = thermal_demand_building[
                                           ii] - boiler_qNominal - chp_qNominal

                                #  Check if tes can provide enough power
                                assert q_out_max_tes > diff, ("TES is now "
                                                              "empty and can't"
                                                              " be unloaded")

                                #  Calculate chp behavior with full power
                                (power_thermal_chp, power_electrical_chp, fuel_power_in_chp) = \
                                    Bes.chp.th_op_calc_all_results(
                                        chp_qNominal,
                                        ii)

                                #  Discharge diff power from tes
                                t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                    q_in=0, q_out=diff, t_prior=t_tes,
                                    t_ambient=20, set_new_temperature=True,
                                    save_res=True, time_index=ii)

                                #  Boiler with full power
                                power_boiler = \
                                    Bes.boiler.calc_boiler_all_results(
                                        boiler_qNominal, ii)[1]

                                tes_load_power = 0
                                tes_unload_power = diff

                            if thermal_demand_building[ii] < (
                                        boiler_qNominal + chp_qNominal):
                                #  chp and boiler are running;
                                #  Tes is needed when boiler can't run due
                                #  to lower activation limit!

                                #  Calculate power difference, which can
                                #  be covered by boiler
                                boiler_diff = \
                                    thermal_demand_building[ii]\
                                    - chp_qNominal + q_in_max_tes

                                #  TODO: How do we know that chp is not below min. part load?

                                if boiler_lal * boiler_qNominal > boiler_diff:
                                    # Boiler can't run due to LAL!!!

                                    t_tes = \
                                        tes_object.calc_storage_temp_for_next_timestep(
                                        q_in=0,
                                        q_out=thermal_demand_building[ii] - chp_qNominal,
                                        t_prior=t_tes, t_ambient=20,
                                        set_new_temperature=True,
                                        save_res=True, time_index=ii)

                                    (power_thermal_chp, power_electrical_chp, fuel_power_in_chp) = \
                                        Bes.chp.th_op_calc_all_results(
                                            chp_qNominal, ii)

                                    power_boiler = 0
                                    tes_load_power = 0

                                    tes_unload_power = \
                                        thermal_demand_building[ ii] - \
                                        chp_qNominal

                                elif boiler_lal * boiler_qNominal < boiler_diff:
                                    #  boiler can be used

                                    #  Calc. boiler power
                                    boiler_max_load_power = boiler_qNominal - (
                                        thermal_demand_building[
                                            ii] - chp_qNominal)

                                    #  If conditions check the power with
                                    #  which the tes can be loaded!
                                    if boiler_max_load_power > q_in_max_tes:
                                        #  tes can be fully charged with boiler

                                        t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                            q_in=q_in_max_tes - 0.01, q_out=0,
                                            t_prior=t_tes, t_ambient=20,
                                            set_new_temperature=True,
                                            save_res=True, time_index=ii)

                                        #  Calculate chp behavior
                                        (power_thermal_chp, power_electrical_chp, fuel_power_in_chp) = \
                                            Bes.chp.th_op_calc_all_results(
                                                chp_qNominal, ii)

                                        power_boiler = \
                                            Bes.boiler.calc_boiler_all_results(
                                                (thermal_demand_building[ii] -
                                                 chp_qNominal) + q_in_max_tes,
                                                ii)[1]

                                        tes_load_power = q_in_max_tes
                                        tes_unload_power = 0

                                    if boiler_max_load_power < q_in_max_tes:
                                        #  tes can only be charged with
                                        #  boiler part load

                                        t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                            q_in=boiler_max_load_power - 0.01,
                                            q_out=0, t_prior=t_tes,
                                            t_ambient=20,
                                            set_new_temperature=True,
                                            save_res=True, time_index=ii)

                                        (power_thermal_chp, power_electrical_chp, fuel_power_in_chp) = \
                                            Bes.chp.th_op_calc_all_results(
                                                chp_qNominal, ii)

                                        power_boiler = \
                                            Bes.boiler.calc_boiler_all_results(
                                                (thermal_demand_building[ii]
                                                 - chp_qNominal) +
                                                boiler_max_load_power, ii)[1]

                                        tes_load_power = boiler_max_load_power
                                        tes_unload_power = 0

                        elif thermal_demand_building[
                            ii] > chp_lal * chp_qNominal and \
                                        thermal_demand_building[
                                            ii] < chp_qNominal:
                            # chp is running and loads the tes if possible;
                            # TES off

                            if q_in_max_tes > 0 and load_power > q_in_max_tes:

                                t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                    q_in=q_in_max_tes - 0.1, q_out=0,
                                    t_prior=t_tes, t_ambient=20,
                                    set_new_temperature=True,
                                    save_res=True, time_index=ii)

                                (power_thermal_chp, power_electrical_chp, fuel_power_in_chp) = \
                                    Bes.chp.th_op_calc_all_results(
                                        thermal_demand_building[
                                            ii] + q_in_max_tes, ii)

                                power_boiler = 0
                                tes_load_power = q_in_max_tes
                                tes_unload_power = 0

                            elif q_in_max_tes > 0 and load_power < q_in_max_tes:
                                #  chp available power can be used ot charge
                                #  tes, but will not be able to fully load it

                                assert load_power > 0, ("negative load "
                                                        "impossible --> check"
                                                        " size tes and demand"
                                                        " dhw!")

                                #  Load tes with load_power (chp - build power)
                                t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                    q_in=load_power, q_out=0, t_prior=t_tes,
                                    t_ambient=20, set_new_temperature=True,
                                    save_res=True, time_index=ii)

                                (power_thermal_chp, power_electrical_chp, fuel_power_in_chp) = \
                                    Bes.chp.th_op_calc_all_results(
                                        thermal_demand_building[
                                            ii] + load_power, ii)

                                power_boiler = 0
                                tes_load_power = load_power
                                tes_unload_power = 0

                        if thermal_demand_building[
                            ii] < chp_lal * chp_qNominal:
                            #  CHP cannot be operated
                            #  tes is running
                            #  if tes is empty, boiler starts to run

                            if q_out_max_tes > 0 and q_out_max_tes > \
                                    thermal_demand_building[ii]:
                                # tes has enough energy to unload

                                t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                    q_in=0, q_out=thermal_demand_building[ii],
                                    t_prior=t_tes, set_new_temperature=True,
                                    save_res=True, time_index=ii)

                                power_thermal_chp = 0
                                power_electrical_chp = 0
                                power_boiler = 0
                                tes_load_power = 0
                                tes_unload_power = thermal_demand_building[ii]

                            elif q_out_max_tes > 0 and q_out_max_tes < \
                                    thermal_demand_building[ii]:
                                # tes does not have enough energy to unload

                                #  Calculate max. available boiler power
                                boiler_max_load_power \
                                    = boiler_qNominal - \
                                      thermal_demand_building[ii]

                                if boiler_max_load_power > q_in_max_tes:
                                    #  TES can be fully charged

                                    t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                        q_in=q_in_max_tes - 0.01, q_out=0,
                                        t_prior=t_tes,
                                        set_new_temperature=True,
                                        save_res=True, time_index=ii)

                                    power_thermal_chp = 0
                                    power_electrical_chp = 0
                                    power_boiler = \
                                        Bes.boiler.calc_boiler_all_results(
                                            thermal_demand_building[
                                                ii] + q_in_max_tes, ii)[1]
                                    tes_load_power = q_in_max_tes
                                    tes_unload_power = 0

                                if boiler_max_load_power < q_in_max_tes:
                                    #  tes can only be shared with boiler
                                    #  part load

                                    t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                        q_in=boiler_max_load_power - 0.01,
                                        q_out=0, t_prior=t_tes,
                                        set_new_temperature=True,
                                        save_res=True, time_index=ii)

                                    power_thermal_chp = 0
                                    power_electrical_chp = 0
                                    power_boiler = \
                                        Bes.boiler.calc_boiler_all_results(
                                            thermal_demand_building[
                                                ii] + boiler_max_load_power,
                                            ii)[1]

                                    tes_load_power = boiler_max_load_power
                                    tes_unload_power = 0

                        power_th_chp_list.append(power_thermal_chp)
                        power_el_chp_list.append(power_electrical_chp)
                        power_boiler_total.append(power_boiler)
                        tes_load.append(tes_load_power)
                        tes_unload.append(tes_unload_power)
                        tes_temp.append(t_tes)

                    Node['power_el_chp'] = (np.array(power_el_chp_list))
                    Node['fuel_demand'] = (
                        np.array(power_boiler_total) + np.array(
                            power_th_chp_list))

                #  #---------------------------------------------------------
                if (Node['entity'].bes.hasBoiler) == True and (
                            Node['entity'].bes.hasChp == False):
                    # Script for Building with Boiler and Tes only

                    boiler_qNominal = Node['entity'].bes.boiler.qNominal
                    boiler_lal = Node['entity'].bes.boiler.lowerActivationLimit

                    sph_demand_building = Node[
                        'entity'].get_space_heating_power_curve()

                    dhw_demand_building = Node['entity'].get_dhw_power_curve()
                    thermal_demand_building = sph_demand_building + \
                                              dhw_demand_building

                    if (Node['entity'].bes.hasTes) == True:
                        #  If tes exists

                        tes_object = Node['entity'].bes.tes

                        # Start temperature of the storage is set as
                        # t surrounding!
                        t_tes = tes_object.t_surroundings

                        for ii in range(len(thermal_demand_building)):

                            q_out_max_tes = Bes.tes.calc_storage_q_out_max(
                                t_ambient=20, q_in=0)
                            q_in_max_tes = Bes.tes.calc_storage_q_in_max(
                                t_ambient=20, q_out=0)

                            load_power = boiler_qNominal - \
                                         thermal_demand_building[ii]

                            if load_power < 0:
                                assert q_out_max_tes > -load_power, ("TES is "
                                            "now empty and can't be unloaded")

                                t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                    q_in=0 - 0.01, q_out=-load_power,
                                    t_prior=t_tes, t_ambient=20,
                                    set_new_temperature=True,
                                    save_res=True, time_index=ii)

                                power_boiler = \
                                    Bes.boiler.calc_boiler_all_results(
                                        boiler_qNominal, ii)[1]

                                tes_load_power = 0
                                tes_unload_power = -load_power

                            elif thermal_demand_building[
                                ii] > boiler_lal * boiler_qNominal and load_power > 0:
                                #  boiler can cover demand in part load
                                #  without usage of storage

                                if q_in_max_tes > 0 and load_power > q_in_max_tes:
                                    #  Boiler supplies house and loads storage
                                    #  with full load

                                    t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                        q_in=q_in_max_tes - 0.01, q_out=0,
                                        t_prior=t_tes, t_ambient=20,
                                        set_new_temperature=True,
                                        save_res=True, time_index=ii)

                                    power_boiler = \
                                        Bes.boiler.calc_boiler_all_results(
                                            thermal_demand_building[
                                                ii] + q_in_max_tes, ii)[1]

                                    tes_load_power = q_in_max_tes
                                    tes_unload_power = 0

                                elif q_in_max_tes > 0 and load_power < q_in_max_tes:
                                    #  Boiler supplies house and loads storage
                                    #  with part load

                                    assert load_power > 0, ("negative load "
                                                            "impossible --> "
                                                            "check size tes "
                                                            "and demand dhw!")

                                    #  Load storage with boiler part load
                                    t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                        q_in=load_power - 0.01, q_out=0,
                                        t_prior=t_tes, t_ambient=20,
                                        set_new_temperature=True,
                                        save_res=True, time_index=ii)

                                    power_boiler = \
                                        Bes.boiler.calc_boiler_all_results(
                                            thermal_demand_building[
                                                ii] + load_power, ii)[1]

                                    tes_load_power = load_power
                                    tes_unload_power = 0

                            elif thermal_demand_building[
                                ii] < boiler_lal * boiler_qNominal:
                                #  Thermal demand is below boiler part load

                                if q_out_max_tes > 0 and q_out_max_tes > \
                                        thermal_demand_building[ii]:
                                    # tes has enough energy to unload

                                    t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                        q_in=0,
                                        q_out=thermal_demand_building[ii] - 0.01,
                                        t_prior=t_tes, t_ambient=20,
                                        set_new_temperature=True,
                                        save_res=True, time_index=ii)

                                    power_boiler = 0
                                    tes_load_power = 0
                                    tes_unload_power = \
                                        thermal_demand_building[ii]

                                elif q_out_max_tes > 0 and q_out_max_tes < \
                                        thermal_demand_building[ii]:
                                    #  Boiler has to be used to cover part
                                    #  of thermal power demand of building

                                    boiler_max_load_power = boiler_qNominal - \
                                                            thermal_demand_building[
                                                                ii]

                                    if boiler_max_load_power > q_in_max_tes:
                                        #  Fully load storage

                                        t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                            q_in=q_in_max_tes - 0.01, q_out=0,
                                            t_prior=t_tes, t_ambient=20,
                                            set_new_temperature=True,
                                            save_res=True, time_index=ii)

                                        power_boiler = \
                                            Bes.boiler.calc_boiler_all_results(
                                                thermal_demand_building[
                                                    ii] + q_in_max_tes, ii)[1]

                                        tes_load_power = q_in_max_tes
                                        tes_unload_power = 0

                                    elif boiler_max_load_power < q_in_max_tes:
                                        #  Partly load storage

                                        t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                            q_in=boiler_max_load_power - 0.01,
                                            q_out=0, t_prior=t_tes,
                                            t_ambient=20,
                                            set_new_temperature=True,
                                            save_res=True, time_index=ii)

                                        power_boiler = \
                                            Bes.boiler.calc_boiler_all_results(
                                                thermal_demand_building[
                                                    ii] + boiler_max_load_power,
                                                ii)[1]
                                        tes_load_power = boiler_max_load_power
                                        tes_unload_power = 0

                            power_boiler_total.append(power_boiler)
                            tes_temp.append(t_tes)

                            tes_load.append(tes_load_power)
                            tes_unload.append(tes_unload_power)

                        Node['fuel_demand'] = np.array(power_boiler_total)

                    if (Node['entity'].bes.hasTes) == False:

                        #  TODO: Check boiler for full part load behavior
                        # Boiler operates with full part load behaviour
                        Bes = \
                            self.city_object.nodes[
                                dict_city_data[index]["Buildings with bes"][
                                    i]][
                                'entity'].bes
                        assert boiler_qNominal >= max(
                            thermal_demand_building), ('Thermal demand is ' +
                                                       'higher than Boiler_qNominal')

                        for ii in range(len(thermal_demand_building)):

                            power_boiler = Bes.boiler.calc_boiler_all_results(
                                thermal_demand_building[ii], ii)[1]

                            power_boiler_total.append(power_boiler)

                        Node['fuel_demand'] = np.array(power_boiler_total)

        #  #---------------------------------------------------------------
        if (dict_city_data[index]['hasLHN']) == True:

            chp_list = []

            for i in range(len(dict_city_data[index]['Buildings with bes'])):
                Node = self.city_object.nodes[
                    dict_city_data[index]['Buildings with bes'][i]]

                # Thermal demands can be aggregated now because there is an lhn
                aggregated_thermal_demand = np.zeros(
                    len(time_vector.time_vector()))

                for ii in range(
                        len(dict_city_data[index]["Buildings in subcity"])):
                    building_demand_th = \
                        self.city_object.nodes[
                            dict_city_data[index]["Buildings in subcity"] \
                                [ii]]['entity'].get_space_heating_power_curve()

                    dhw_demand_building = self.city_object.nodes[
                        dict_city_data[index]["Buildings in subcity"][ii]][
                        'entity'].get_dhw_power_curve()
                    aggregated_thermal_demand = aggregated_thermal_demand + \
                                                building_demand_th + \
                                                dhw_demand_building

                Bes = \
                    self.city_object.nodes[
                        dict_city_data[index]["Buildings with bes"][i]][
                        'entity'].bes
                tes_object = Bes.tes

                max_th_power = max(aggregated_thermal_demand)

                #  Get list of lhn connected buildings
                list_lhn = dict_city_data[index]['Buildings in subcity']

                #  Get subgraph copy
                # graph_copy = copy.deepcopy(self.city_object.subgraph(list_lhn))
                graph_copy = self.city_object.subgraph(list_lhn).copy()

                #  Add weights to edges
                netop.add_weights_to_edges(graph_copy)

                #  Get lhn network length
                curr_length = netop.sum_up_weights_of_edges(graph_copy,
                                                            network_type='heating')

                #  Extract lhn edge attributes
                for u, v in graph_copy.edges():
                    if graph_copy.has_edge(u, v):
                        if 'network_type' in graph_copy.edges[u, v]:
                            if (graph_copy.edges[u, v]['network_type'] ==
                                    'heating' or
                                        graph_copy.edges[u, v][
                                            'network_type'] ==
                                        'heating_and_deg'):
                                temp_vl = graph_copy.edges[u, v]['temp_vl']
                                temp_rl = graph_copy.edges[u, v]['temp_rl']
                                d_i = graph_copy.edges[u, v]['d_i']
                                break

                # Calculate u_value of pipe
                u_value = dimnet.estimate_u_value(d_i=d_i)

                #  Get ground temperature
                temp_ground = self.city_object.environment.temp_ground

                q_dot_loss = \
                    dimnet.calc_pipe_power_loss(length=curr_length,
                                                u_pipe=u_value,
                                                temp_vl=temp_vl,
                                                temp_rl=temp_rl,
                                                temp_environment=temp_ground)

                aggregated_thermal_demand += q_dot_loss

                del graph_copy
                ###########################################


                if (Node['entity'].bes.hasHeatpump) == True:
                    #  TODO: Raise assertionError
                    print("Heatpump is not available if there is an LHN!")
                    sys.exit()

                if (Node['entity'].bes.hasChp) == True:
                    chp_list.append(1)
                    assert len(
                        chp_list) < 2, "If there is an lhn, it is only allowed that one node supplies the grid"

                    # the following codes assumes that thermal energy is only supplied at one node
                    chp_qNominal = Node['entity'].bes.chp.qNominal
                    boiler_qNominal = Node['entity'].bes.boiler.qNominal
                    chp_lal = Node['entity'].bes.chp.lowerActivationLimit
                    boiler_lal = Node['entity'].bes.boiler.lowerActivationLimit

                    # Start temperature of the storage is set as t surrounding!
                    t_tes = tes_object.t_surroundings
                    power_el_chp_list = []
                    power_th_chp_list = []
                    power_boiler_total = []
                    tes_load = []
                    tes_unload = []
                    tes_temp = []

                    for ii in range(len(
                            dict_city_data[index]["Buildings in subcity"])):
                        # first all buildings are initialised with a demand of zero;
                        # Value is later overwritten for the building, where the thermal bes is located!
                        self.city_object.nodes[
                            dict_city_data[index]["Buildings in subcity"][ii]][
                            'fuel_demand'] = np.zeros(
                            len(time_vector.time_vector()))
                        self.city_object.nodes[
                            dict_city_data[index]["Buildings in subcity"][ii]][
                            'electricity_heatpump'] = np.zeros(
                            len(time_vector.time_vector()))

                    for ii in range(len(aggregated_thermal_demand)):

                        q_out_max_tes = Bes.tes.calc_storage_q_out_max(
                            t_ambient=20, q_in=0)
                        q_in_max_tes = Bes.tes.calc_storage_q_in_max(
                            t_ambient=20, q_out=0)
                        load_power = chp_qNominal - aggregated_thermal_demand[
                            ii]

                        if aggregated_thermal_demand[ii] > chp_qNominal:

                            if aggregated_thermal_demand[ii] > (
                                        boiler_qNominal + chp_qNominal):
                                diff = aggregated_thermal_demand[
                                           ii] - boiler_qNominal - chp_qNominal
                                assert q_out_max_tes > diff, "TES is now empty and can't be unloaded"
                                power_thermal_chp = \
                                    Bes.chp.th_op_calc_all_results(
                                        chp_qNominal,
                                        ii)[2]
                                power_electrical_chp = \
                                    Bes.chp.th_op_calc_all_results(
                                        chp_qNominal,
                                        ii)[1]
                                t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                    q_in=0, q_out=diff, t_prior=t_tes,
                                    t_ambient=20, set_new_temperature=True)
                                power_boiler = \
                                    Bes.boiler.calc_boiler_all_results(
                                        boiler_qNominal, ii)[1]
                                tes_load_power = 0
                                tes_unload_power = diff

                            if aggregated_thermal_demand[ii] < (
                                        boiler_qNominal + chp_qNominal):
                                # chp and boiler are running; Tes is needed when boiler can't run due to lower activation limit!
                                boiler_diff = aggregated_thermal_demand[
                                                  ii] - chp_qNominal + q_in_max_tes

                                if boiler_lal * boiler_qNominal > boiler_diff:
                                    # Boiler can't run due to LAL!!!
                                    t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                        q_in=0,
                                        q_out=aggregated_thermal_demand[
                                                  ii] - chp_qNominal,
                                        t_prior=t_tes, t_ambient=20,
                                        set_new_temperature=True)
                                    power_thermal_chp = \
                                        Bes.chp.th_op_calc_all_results(
                                            chp_qNominal, ii)[2]
                                    power_electrical_chp = \
                                        Bes.chp.th_op_calc_all_results(
                                            chp_qNominal, ii)[1]
                                    power_boiler = 0
                                    tes_load_power = 0
                                    tes_unload_power = \
                                        aggregated_thermal_demand[
                                            ii] - chp_qNominal

                                if boiler_lal * boiler_qNominal < boiler_diff:
                                    # Tes is now almost empty so that the boiler can again start to run
                                    boiler_max_load_power = boiler_qNominal - (
                                        aggregated_thermal_demand[
                                            ii] - chp_qNominal)
                                    # If conditions check the power with which the tes can be loaded!
                                    if boiler_max_load_power > q_in_max_tes:
                                        t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                            q_in=q_in_max_tes - 0.1, q_out=0,
                                            t_prior=t_tes, t_ambient=20,
                                            set_new_temperature=True)
                                        power_thermal_chp = \
                                            Bes.chp.th_op_calc_all_results(
                                                chp_qNominal, ii)[2]
                                        power_electrical_chp = \
                                            Bes.chp.th_op_calc_all_results(
                                                chp_qNominal, ii)[1]
                                        power_boiler = \
                                            Bes.boiler.calc_boiler_all_results(
                                                aggregated_thermal_demand[
                                                    ii] - chp_qNominal + q_in_max_tes,
                                                ii)[1]
                                        tes_load_power = q_in_max_tes
                                        tes_unload_power = 0

                                    if boiler_max_load_power < q_in_max_tes:
                                        t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                            q_in=boiler_max_load_power - 0.1,
                                            q_out=0, t_prior=t_tes,
                                            t_ambient=20,
                                            set_new_temperature=True)
                                        power_thermal_chp = \
                                            Bes.chp.th_op_calc_all_results(
                                                chp_qNominal, ii)[2]
                                        power_electrical_chp = \
                                            Bes.chp.th_op_calc_all_results(
                                                chp_qNominal, ii)[1]
                                        power_boiler = \
                                            Bes.boiler.calc_boiler_all_results(
                                                aggregated_thermal_demand[
                                                    ii] - chp_qNominal + boiler_max_load_power,
                                                ii)[1]
                                        tes_load_power = q_in_max_tes
                                        tes_unload_power = 0

                        if aggregated_thermal_demand[
                            ii] > chp_lal * chp_qNominal and \
                                        aggregated_thermal_demand[
                                            ii] < chp_qNominal:
                            # chp is running and loads the tes if possible
                            if q_in_max_tes > 0 and load_power > q_in_max_tes:
                                t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                    q_in=q_in_max_tes - 0.1, q_out=0,
                                    t_prior=t_tes, t_ambient=20,
                                    set_new_temperature=True)
                                power_thermal_chp = \
                                    Bes.chp.th_op_calc_all_results(
                                        aggregated_thermal_demand[
                                            ii] + q_in_max_tes, ii)[2]
                                power_electrical_chp = \
                                    Bes.chp.th_op_calc_all_results(
                                        aggregated_thermal_demand[
                                            ii] + q_in_max_tes, ii)[1]
                                power_boiler = 0
                                tes_load_power = q_in_max_tes
                                tes_unload_power = 0

                            if q_in_max_tes > 0 and load_power < q_in_max_tes:
                                assert load_power > 0, "negative load impossible --> check size tes and demand dhw!"

                                t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                    q_in=load_power - 0.1, q_out=0,
                                    t_prior=t_tes, t_ambient=20,
                                    set_new_temperature=True)
                                power_thermal_chp = \
                                    Bes.chp.th_op_calc_all_results(
                                        aggregated_thermal_demand[
                                            ii] + load_power,
                                        ii)[2]
                                power_electrical_chp = \
                                    Bes.chp.th_op_calc_all_results(
                                        aggregated_thermal_demand[
                                            ii] + q_in_max_tes, ii)[1]
                                power_boiler = 0
                                tes_load_power = load_power
                                tes_unload_power = 0

                        if aggregated_thermal_demand[
                            ii] < chp_lal * chp_qNominal:
                            # tes is running and if empty boiler starts to run

                            if q_out_max_tes > 0 and q_out_max_tes > \
                                    aggregated_thermal_demand[ii]:
                                # tes has enough energy to unload
                                t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                    q_in=0,
                                    q_out=aggregated_thermal_demand[ii],
                                    t_prior=t_tes, set_new_temperature=True)
                                power_thermal_chp = 0
                                power_electrical_chp = 0
                                power_boiler = 0
                                tes_load_power = 0
                                tes_unload_power = aggregated_thermal_demand[
                                    ii]

                            if q_out_max_tes > 0 and q_out_max_tes < \
                                    aggregated_thermal_demand[ii]:
                                # tes does not have enough energy to unload

                                boiler_max_load_power = boiler_qNominal - \
                                                        aggregated_thermal_demand[
                                                            ii]

                                if boiler_max_load_power > q_in_max_tes:
                                    t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                        q_in=q_in_max_tes - 0.1, q_out=0,
                                        t_prior=t_tes,
                                        set_new_temperature=True)
                                    power_thermal_chp = 0
                                    power_electrical_chp = 0
                                    power_boiler = \
                                        Bes.boiler.calc_boiler_all_results(
                                            aggregated_thermal_demand[
                                                ii] + q_in_max_tes, ii)[1]
                                    tes_load_power = q_in_max_tes
                                    tes_unload_power = 0

                                if boiler_max_load_power < q_in_max_tes:
                                    t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                        q_in=boiler_max_load_power - 0.1,
                                        q_out=0, t_prior=t_tes,
                                        set_new_temperature=True)
                                    power_thermal_chp = 0
                                    power_electrical_chp = 0
                                    power_boiler = \
                                        Bes.boiler.calc_boiler_all_results(
                                            aggregated_thermal_demand[
                                                ii] + boiler_max_load_power,
                                            ii)[1]
                                    tes_load_power = q_in_max_tes
                                    tes_unload_power = 0

                        power_th_chp_list.append(power_thermal_chp)
                        power_el_chp_list.append(power_electrical_chp)
                        power_boiler_total.append(power_boiler)
                        tes_load.append(tes_load_power)
                        tes_unload.append(tes_unload_power)
                        tes_temp.append(t_tes)

                    Node['power_el_chp'] = (np.array(power_el_chp_list))
                    total_thermal_demand = np.array(
                        power_th_chp_list) + np.array(power_boiler_total)
                    self.city_object.nodes[
                        dict_city_data[index]["Buildings with bes"][i]][
                        'fuel_demand'] = total_thermal_demand




                    # fig = plt.figure()
                    # plt.title('')
                    # ax = fig.add_subplot(3,1,1)
                    # plt.ylabel('Leistung [W]')
                    # plt.xlabel('Laufzeit [h/a]')
                    # ax.plot(time_vector.time_vector(),power_boiler_total,'#DD402D',linewidth=0.6,label='Kessel Brennstoff Leistung')
                    # ax.plot(time_vector.time_vector(),power_th_chp_list,'k',linewidth=0.5,label='CHP Brennstoff Leisung')
                    # ax.plot(time_vector.time_vector(),power_el_chp_list,'g',linewidth=0.6,label='CHP el Leistung')
                    # ax.plot(time_vector.time_vector(),aggregated_thermal_demand,'b',linewidth=1,label='Bedarf Leisung')
                    # plt.legend()
                    # plt.grid()
                    # ax = fig.add_subplot(3,1,2)
                    # plt.ylabel('Leistung [W]')
                    # plt.xlabel('Laufzeit [h/a]')
                    # ax.plot(time_vector.time_vector(),tes_unload,'#DD402D',linewidth=0.6,label='Tes entladen')
                    # ax.plot(time_vector.time_vector(),tes_load,'k',linewidth=0.5,label='Tes laden')
                    # #ax.plot(time_vector.time_vector(),aggregated_thermal_demand,'b',linewidth=1,label='Bedarf Leisung')
                    # plt.legend()
                    # plt.grid()
                    # ax = fig.add_subplot(3,1,3)
                    # plt.ylabel('Temp')
                    # plt.xlabel('Laufzeit [h/a]')
                    # ax.plot(time_vector.time_vector(),tes_temp,'#DD402D',linewidth=0.6,label='Tes temp')
                    # plt.legend()
                    # plt.grid()
                    # #plt.show()

                if (Node['entity'].bes.hasBoiler) == True and (
                            Node['entity'].bes.hasChp == False):
                    # Script for Building with Boiler and Tes only
                    # todo:  this code is unchecked yet because energy_sys_generator still cant handle boiler + tes + lhn !!!
                    boiler_qNominal = Node['entity'].bes.boiler.qNominal
                    boiler_lal = Node['entity'].bes.boiler.lowerActivationLimit

                    for z in range(len(
                            dict_city_data[index]["Buildings in subcity"])):
                        # first all buildings are initialised with a demand of zero;
                        # Value is later overwritten for the building, where the thermal bes is located!
                        self.city_object.nodes[
                            dict_city_data[index]["Buildings in subcity"][z]][
                            'fuel_demand'] = 0
                        self.city_object.nodes[
                            dict_city_data[index]["Buildings in subcity"][z]][
                            'electricity_heatpump'] = 0

                    if (Node['entity'].bes.hasTes) == True:

                        # Start temperature of the storage is set as t surrounding!
                        t_tes = tes_object.t_surroundings
                        for ii in range(len(aggregated_thermal_demand)):
                            q_out_max_tes = Bes.tes.calc_storage_q_out_max(
                                t_ambient=20, q_in=0)
                            q_in_max_tes = Bes.tes.calc_storage_q_in_max(
                                t_ambient=20, q_out=0)
                            load_power = boiler_qNominal - \
                                         aggregated_thermal_demand[ii]

                            if load_power < 0:
                                assert q_out_max_tes > -load_power, "TES is now empty and can't be unloaded"
                                t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                    q_in=0 - 0.1, q_out=-load_power,
                                    t_prior=t_tes, t_ambient=20,
                                    set_new_temperature=True)
                                power_boiler = \
                                    Bes.boiler.calc_boiler_all_results(
                                        boiler_qNominal, ii)[1]
                                tes_load_power = 0
                                tes_unload_power = -load_power

                            if aggregated_thermal_demand[
                                ii] > boiler_lal * boiler_qNominal and load_power > 0:

                                if q_in_max_tes > 0 and load_power > q_in_max_tes:
                                    # Boiler supplies house and loads kessel with full load

                                    t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                        q_in=q_in_max_tes - 0.1, q_out=0,
                                        t_prior=t_tes, t_ambient=20,
                                        set_new_temperature=True)
                                    power_boiler = \
                                        Bes.boiler.calc_boiler_all_results(
                                            aggregated_thermal_demand[
                                                ii] + q_in_max_tes, ii)[1]
                                    tes_load_power = q_in_max_tes
                                    tes_unload_power = 0

                                if q_in_max_tes > 0 and load_power < q_in_max_tes:
                                    # Boiler supplies house and loads kessel with part load
                                    assert load_power > 0, "negative load impossible --> check size tes and demand dhw!"

                                    t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                        q_in=load_power - 0.1, q_out=0,
                                        t_prior=t_tes, t_ambient=20,
                                        set_new_temperature=True)
                                    power_boiler = \
                                        Bes.boiler.calc_boiler_all_results(
                                            aggregated_thermal_demand[
                                                ii] + load_power, ii)[1]

                                    tes_load_power = load_power
                                    tes_unload_power = 0

                            if aggregated_thermal_demand[
                                ii] < boiler_lal * boiler_qNominal:

                                if q_out_max_tes > 0 and q_out_max_tes > \
                                        aggregated_thermal_demand[ii]:
                                    # tes has enough energy to unload
                                    t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                        q_in=0,
                                        q_out=aggregated_thermal_demand[
                                                  ii] - 0.1,
                                        t_prior=t_tes, t_ambient=20,
                                        set_new_temperature=True)
                                    power_boiler = 0
                                    tes_load_power = 0
                                    tes_unload_power = \
                                        aggregated_thermal_demand[ii]

                                if q_out_max_tes > 0 and q_out_max_tes < \
                                        aggregated_thermal_demand[ii]:
                                    # tes does not have enough energy to unload
                                    t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                        q_in=q_in_max_tes - 0.1, q_out=0,
                                        t_prior=t_tes, t_ambient=20,
                                        set_new_temperature=True)
                                    power_boiler = \
                                        Bes.boiler.calc_boiler_all_results(
                                            aggregated_thermal_demand[
                                                ii] + q_in_max_tes, ii)[1]
                                    tes_load_power = q_in_max_tes
                                    tes_unload_power = 0

                                    boiler_max_load_power = boiler_qNominal - \
                                                            aggregated_thermal_demand[
                                                                ii]

                                    if boiler_max_load_power > q_in_max_tes:
                                        t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                            q_in=q_in_max_tes - 0.1, q_out=0,
                                            t_prior=t_tes, t_ambient=20,
                                            set_new_temperature=True)
                                        power_boiler = \
                                            Bes.boiler.calc_boiler_all_results(
                                                aggregated_thermal_demand[
                                                    ii] + q_in_max_tes, ii)[1]
                                        tes_load_power = q_in_max_tes
                                        tes_unload_power = 0

                                    if boiler_max_load_power < q_in_max_tes:
                                        t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                            q_in=boiler_max_load_power - 0.1,
                                            q_out=0, t_prior=t_tes,
                                            t_ambient=20,
                                            set_new_temperature=True)
                                        power_boiler = \
                                            Bes.boiler.calc_boiler_all_results(
                                                aggregated_thermal_demand[
                                                    ii] + boiler_max_load_power,
                                                ii)[1]
                                        tes_load_power = boiler_max_load_power
                                        tes_unload_power = 0

                            power_boiler_total.append(power_boiler)
                            tes_temp.append(t_tes)

                            tes_load.append(tes_load_power)
                            tes_unload.append(tes_unload_power)

                        Node['fuel_demand'] = np.array(power_boiler_total)
                        ######################################################################################################################################
                        ###########################################                     ######################################################################
                        ########################################### electrical balances ######################################################################
                        ###########################################                     ######################################################################
                        ######################################################################################################################################
                        #####################################################
        if (dict_city_data[index]['hasDEG']) == False:  #########
            #####################################################

            for i in range(len(dict_city_data[index]['Buildings in subcity'])):
                Node = self.city_object.nodes[
                    dict_city_data[index]['Buildings in subcity'][i]]
                demand_heatpump = Node['electricity_heatpump']

                if (Node['entity'].hasBes) == False:
                    # if no deg and no bes each building has to buy the full electrical demand
                    Node['electrical demand'] = (
                        Node['entity'].get_electric_power_curve())
                    Node['electrical demand_with_deg'] = (
                        Node['entity'].get_electric_power_curve())
                    Node['pv_used_self'] = 0
                    Node['pv_used_with_batt'] = 0
                    Node['pv_not_used'] = 0
                    Node['chp_used_self'] = 0
                    Node['chp_used_with_batt'] = 0
                    Node['chp_not_used'] = 0

                if (Node['entity'].hasBes) == True:
                    # if conditions checks if initial electrical demand is changed by bes
                    # these are overwritten if necessary
                    Node['electrical demand'] = (Node[
                                                     'entity'].get_electric_power_curve()) + (
                                                    demand_heatpump)
                    Node['electrical demand_with_deg'] = (Node[
                                                              'entity'].get_electric_power_curve()) + (
                                                             demand_heatpump)
                    Node['pv_used_self'] = 0
                    Node['pv_used_with_batt'] = 0
                    Node['pv_not_used'] = 0
                    Node['chp_used_self'] = 0
                    Node['chp_used_with_batt'] = 0
                    Node['chp_not_used'] = 0
                    general_demand = Node['entity'].get_electric_power_curve()

                    if (Node['entity'].bes.hasBattery) == True:

                        if (Node['entity'].bes.hasHeatpump):
                            general_demand += demand_heatpump

                        if (Node['entity'].bes.hasPv):
                            print(Node['entity'].bes.hasPv)
                            # pv electricity is very expensive and therefore more important to use than chp!
                            supply_pv = self.city_object.nodes[
                                dict_city_data[index]['Buildings in subcity'][
                                    i]][
                                'entity'].bes.pv.getPower()
                            pv_used = []
                            pv_sold = []
                            demand_after_pv = []
                            load = []
                            unload = []
                            for v in range(len(general_demand)):

                                p_batt_max_out = Bes.battery.calc_battery_max_p_el_out(
                                    p_el_in=0)
                                p_batt_max_in = Bes.battery.calc_battery_max_p_el_in(
                                    p_el_out=0)

                                if general_demand[v] < supply_pv[v]:
                                    load_power = supply_pv[v] - general_demand[
                                        v]

                                    if load_power < p_batt_max_in:
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=load_power, p_el_out=0)
                                        pv_used.append(general_demand[v])
                                        pv_sold.append(0)
                                        demand_after_pv.append(0)
                                        load.append(load_power)
                                        unload.append(0)

                                    if load_power > p_batt_max_in:
                                        pv_sold.append(load_power)
                                        pv_used.append(general_demand[v])
                                        demand_after_pv.append(0)
                                        load.append(0)
                                        unload.append(0)

                                if general_demand[v] > supply_pv[v]:
                                    lack_of_power = general_demand[v] - \
                                                    supply_pv[v]

                                    if lack_of_power < p_batt_max_out:
                                        pv_used.append(supply_pv[v])
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=0, p_el_out=lack_of_power)
                                        pv_sold.append(0)
                                        demand_after_pv.append(0)
                                        load.append(0)
                                        unload.append(lack_of_power)

                                    if lack_of_power > p_batt_max_out:
                                        pv_used.append(supply_pv[v])
                                        pv_sold.append(0)
                                        demand_after_pv.append(lack_of_power)
                                        load.append(0)
                                        unload.append(0)

                            Node['electrical demand'] = np.array(
                                demand_after_pv)
                            # To make it complete and comparable to the entities of the other nodes
                            Node['electrical demand_with_deg'] = np.array(
                                demand_after_pv)  # useless here but consequent!
                            Node['pv_used_self'] = sum(pv_used)
                            Node['pv_not_used'] = sum(pv_sold)
                            Node['pv_used_with_batt'] = sum(pv_used) + sum(
                                unload)


                            # fig = plt.figure()
                            # plt.title('')
                            # ax = fig.add_subplot(2,1,1)
                            # plt.ylabel('Leistung [W]')
                            # plt.xlabel('Laufzeit [h/a]')
                            # ax.plot(general_demand,'b',linewidth=0.6,label='general_demand')
                            # ax.plot(supply_pv,'y',linewidth=0.6,label='supply pv')
                            # ax.plot(pv_sold,'k',linewidth=0.5,label='pv_sold')
                            # ax.plot(pv_used,'g',linewidth=0.6,label='pv_used_building')
                            # ax.plot(demand_after_pv,'r',linewidth=1,label='demand_after_pv')
                            # plt.legend()
                            # plt.grid()
                            # ax = fig.add_subplot(2,1,2)
                            # plt.ylabel('Leistung [W]')
                            # plt.xlabel('Laufzeit [h/a]')
                            # ax.plot(unload,'b',linewidth=0.6,label='unload')
                            # ax.plot(load,'k',linewidth=0.5,label='load')
                            # plt.legend()
                            # plt.grid()
                            # #plt.show()

                        if (Node['entity'].bes.hasChp):
                            if (Node['entity'].bes.hasPv) == False:
                                demand_after_pv = general_demand

                            supply_chp = np.array(power_el_chp_list)
                            demand_after_chp = []
                            chp_used = []
                            chp_sold = []
                            load = []
                            unload = []
                            for z in range(len(demand_after_pv)):

                                p_batt_max_out = Bes.battery.calc_battery_max_p_el_out(
                                    p_el_in=0)
                                p_batt_max_in = Bes.battery.calc_battery_max_p_el_in(
                                    p_el_out=0)

                                if demand_after_pv[z] < supply_chp[z]:
                                    load_power = supply_chp[z] - \
                                                 demand_after_pv[z]

                                    if load_power < p_batt_max_in:
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=load_power, p_el_out=0)
                                        chp_used.append(demand_after_pv[z])
                                        chp_sold.append(0)
                                        demand_after_chp.append(0)
                                        load.append(load_power)
                                        unload.append(0)

                                    if load_power > p_batt_max_in:
                                        chp_sold.append(load_power)
                                        chp_used.append(demand_after_pv[z])
                                        demand_after_chp.append(0)
                                        load.append(0)
                                        unload.append(0)

                                if demand_after_pv[z] > supply_chp[z]:
                                    lack_of_power = demand_after_pv[z] - \
                                                    supply_chp[z]

                                    if lack_of_power < p_batt_max_out:
                                        chp_used.append(supply_chp[z])
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=0, p_el_out=lack_of_power)
                                        chp_sold.append(0)
                                        demand_after_chp.append(0)
                                        load.append(0)
                                        unload.append(lack_of_power)

                                    if lack_of_power > p_batt_max_out:
                                        chp_used.append(supply_chp[z])
                                        chp_sold.append(0)
                                        demand_after_chp.append(lack_of_power)
                                        load.append(0)
                                        unload.append(0)
                            # print ("")
                            # fig = plt.figure()
                            # plt.title('')
                            # ax = fig.add_subplot(2,1,1)
                            # plt.ylabel('Leistung [W]')
                            # plt.xlabel('Laufzeit [h/a]')
                            # ax.plot(demand_after_pv,'b',linewidth=0.6,label='demand_after_pv')
                            # ax.plot(supply_chp,'y',linewidth=0.6,label='supply chp')
                            # ax.plot(chp_sold,'k',linewidth=0.5,label='chp_sold')
                            # ax.plot(chp_used,'g',linewidth=0.6,label='chp_used_building')
                            # ax.plot(demand_after_chp,'r',linewidth=1,label='demand_after_chp')
                            # plt.legend()
                            # plt.grid()
                            # ax = fig.add_subplot(2,1,2)
                            # plt.ylabel('Leistung [W]')
                            # plt.xlabel('Laufzeit [h/a]')
                            # ax.plot(unload,'b',linewidth=0.6,label='unload')
                            # ax.plot(load,'k',linewidth=0.5,label='load')
                            # plt.legend()
                            # plt.grid()
                            # #plt.show()

                            Node['electrical demand'] = np.array(
                                demand_after_chp)
                            # To make it complete and comparable to the entities of the other nodes
                            Node['electrical demand_with_deg'] = np.array(
                                demand_after_chp)  # useless here but consequent!
                            Node['chp_used_self'] = sum(chp_used)
                            Node['chp_not_used'] = sum(chp_sold)
                            Node['chp_used_with_batt'] = sum(chp_used) + sum(
                                unload)

                        if (Node['entity'].bes.hasPv) == False and (
                                Node['entity'].bes.hasChp) == False:
                            # In case there is a battery without local producer of electrical energy!
                            assert (Node[
                                        'entity'].bes.hasBattery) == False, "Battery System without PV or CHP is useless! Remember that battery only serves local and not interacting with the DEG"

                    if (Node['entity'].bes.hasBattery) == False:

                        if (Node['entity'].bes.hasHeatpump):
                            # todo!
                            general_demand += demand_heatpump

                        if (Node['entity'].bes.hasPv):
                            # pv electricity is very expensive and therefore more important to use than chp!
                            supply_pv = self.city_object.nodes[
                                dict_city_data[index]['Buildings in subcity'][
                                    i]][
                                'entity'].bes.pv.getPower()
                            diff1_demand = general_demand - supply_pv
                            pv_sold = [x for x in diff1_demand if x < 0]
                            pv_used = sum(supply_pv) + sum(pv_sold)
                            general_demand = []
                            for y in range(len(diff1_demand)):
                                if diff1_demand[y] < 0:
                                    general_demand.append(0)
                                if diff1_demand[y] > 0:
                                    general_demand.append(diff1_demand[y])

                            Node['pv_used_self'] = pv_used
                            Node['pv_not_used'] = -1 * sum(pv_sold)
                            final_electrical_demand = np.array(general_demand)
                            Node[
                                'electrical demand_with_deg'] = final_electrical_demand  # useless because there is no DEG here but consequent!
                            Node['electrical demand'] = final_electrical_demand

                        if (Node['entity'].bes.hasChp):

                            supply_chp = np.array(power_el_chp_list)
                            diff2_demand = general_demand - supply_chp
                            chp_sold = [x for x in diff2_demand if x < 0]
                            chp_used = sum(supply_chp) + sum(chp_sold)

                            general_demand = []
                            for y in range(len(diff2_demand)):
                                if diff2_demand[y] < 0:
                                    general_demand.append(0)
                                if diff2_demand[y] > 0:
                                    general_demand.append(diff2_demand[y])

                            Node['chp_used_self'] = chp_used
                            Node['chp_not_used'] = -1 * sum(chp_sold)
                            general_demand = [x for x in general_demand if
                                              x > 0]
                            final_electrical_demand = np.array(general_demand)
                            # To make it complete and comparable to the entities of the other nodes
                            Node[
                                'electrical demand_with_deg'] = final_electrical_demand  # useless because there is no DEG here but consequent!
                            Node['electrical demand'] = final_electrical_demand



                            ######################################################
        if (dict_city_data[index]['hasDEG']) == True:  ###########
            ######################################################
            cumulated_surplus = np.zeros(len(time_vector.time_vector()))

            for i in range(len(dict_city_data[index]['Buildings in subcity'])):
                Node = self.city_object.nodes[
                    dict_city_data[index]['Buildings in subcity'][i]]
                demand_heatpump = Node['electricity_heatpump']

                # if (Node['entity'].hasBes)==False:
                # if no deg and no bes each building has to buy the full electrical demand
                Node['electrical demand'] = (
                    Node['entity'].get_electric_power_curve())
                Node['electrical demand_with_deg'] = (
                    Node['entity'].get_electric_power_curve())
                Node['pv_used_self'] = 0
                Node['pv_used_with_batt'] = 0
                Node['pv_not_used'] = 0
                Node['chp_used_self'] = 0
                Node['chp_used_with_batt'] = 0
                Node['chp_not_used'] = 0
                Node[
                    'cumulated_surplus'] = cumulated_surplus  # Overload from single building for DEG
                Node['electrical demand_without_deg'] = (
                    Node['entity'].get_electric_power_curve())

            print()
            for i in range(len(dict_city_data[index]['Buildings with bes'])):

                Node = self.city_object.nodes[
                    dict_city_data[index]['Buildings with bes'][i]]
                demand_heatpump = Node['electricity_heatpump']

                if (Node['entity'].hasBes) == True:

                    # print(dict_city_data[index]["Buildings with bes"][i])
                    Bes = self.city_object.nodes[
                        dict_city_data[index]["Buildings with bes"][i]][
                        'entity'].bes
                    # if conditions checks if initial electrical demand is changed by bes
                    general_demand = Node['entity'].get_electric_power_curve()
                    # these are overwritten if necessary
                    Node['electrical demand'] = (Node[
                                                     'entity'].get_electric_power_curve()) + (
                                                    demand_heatpump)
                    Node['electrical demand_with_deg'] = (Node[
                                                              'entity'].get_electric_power_curve()) + (
                                                             demand_heatpump)
                    Node['electrical demand_without_deg'] = (Node[
                                                                 'entity'].get_electric_power_curve()) + (
                                                                demand_heatpump)
                    Node['pv_used_self'] = 0
                    Node['pv_used_with_batt'] = 0
                    Node['pv_not_used'] = 0
                    Node['chp_used_self'] = 0
                    Node['chp_used_with_batt'] = 0
                    Node['chp_not_used'] = 0

                    # The following code calculates the demands if batteries are used!
                    # The Battery is only used local and a surplus within the DEG cannnot be stored in them!!
                    if (Node['entity'].bes.hasBattery) == True:

                        # cumulated_surplus saves the inputs of pv and chp
                        cumulated_surplus = np.zeros(
                            len(time_vector.time_vector()))
                        # Initially set to an array of zeros but overwritten if needed!
                        Node['cumulated_surplus'] = cumulated_surplus

                        if (Node['entity'].bes.hasHeatpump):
                            general_demand += demand_heatpump

                        if (Node['entity'].bes.hasPv):

                            # pv electricity is very expensive and therefore more important to use than chp!
                            supply_pv = Node['entity'].bes.pv.getPower()
                            pv_used = []
                            pv_sold = []
                            demand_after_pv = []
                            load = []
                            unload = []
                            for v in range(len(general_demand)):

                                p_batt_max_out = Bes.battery.calc_battery_max_p_el_out(
                                    p_el_in=0)
                                p_batt_max_in = Bes.battery.calc_battery_max_p_el_in(
                                    p_el_out=0)

                                if general_demand[v] < supply_pv[v]:
                                    load_power = supply_pv[v] - general_demand[
                                        v]

                                    if load_power < p_batt_max_in:
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=load_power, p_el_out=0)
                                        pv_used.append(general_demand[v])
                                        pv_sold.append(0)
                                        demand_after_pv.append(0)
                                        load.append(load_power)
                                        unload.append(0)

                                    if load_power > p_batt_max_in:
                                        pv_sold.append(load_power)
                                        pv_used.append(general_demand[v])
                                        demand_after_pv.append(0)
                                        load.append(0)
                                        unload.append(0)

                                if general_demand[v] > supply_pv[v]:
                                    lack_of_power = general_demand[v] - \
                                                    supply_pv[v]

                                    if lack_of_power < p_batt_max_out:
                                        pv_used.append(supply_pv[v])
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=0, p_el_out=lack_of_power)
                                        pv_sold.append(0)
                                        demand_after_pv.append(0)
                                        load.append(0)
                                        unload.append(lack_of_power)

                                    if lack_of_power > p_batt_max_out:
                                        pv_used.append(supply_pv[v])
                                        pv_sold.append(0)
                                        demand_after_pv.append(lack_of_power)
                                        load.append(0)
                                        unload.append(0)

                            cumulated_surplus -= np.array(pv_sold)

                            Node['electrical demand'] = (demand_after_pv)
                            Node['pv_used_self'] = sum(pv_used)
                            Node['pv_not_used'] = sum(pv_sold)
                            Node['pv_used_with_batt'] = sum(pv_used) + sum(
                                unload)
                            Node[
                                'electrical demand_without_deg'] = demand_after_pv
                            Node['cumulated_surplus'] = cumulated_surplus

                        if (Node['entity'].bes.hasChp):
                            if (Node['entity'].bes.hasPv) == False:
                                demand_after_pv = general_demand

                            supply_chp = np.array(power_el_chp_list)
                            demand_after_chp = []
                            chp_used = []
                            chp_sold = []
                            load = []
                            unload = []

                            for z in range(len(demand_after_pv)):

                                p_batt_max_out = Bes.battery.calc_battery_max_p_el_out(
                                    p_el_in=0)
                                p_batt_max_in = Bes.battery.calc_battery_max_p_el_in(
                                    p_el_out=0)

                                if demand_after_pv[z] < supply_chp[z]:
                                    load_power = supply_chp[z] - \
                                                 demand_after_pv[z]

                                    if load_power < p_batt_max_in:
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=load_power, p_el_out=0)
                                        chp_used.append(demand_after_pv[z])
                                        chp_sold.append(0)
                                        demand_after_chp.append(0)
                                        load.append(load_power)
                                        unload.append(0)

                                    if load_power > p_batt_max_in:
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=0, p_el_out=0)
                                        chp_sold.append(load_power)
                                        chp_used.append(demand_after_pv[z])
                                        demand_after_chp.append(0)
                                        load.append(0)
                                        unload.append(0)

                                if demand_after_pv[z] > supply_chp[z]:
                                    lack_of_power = demand_after_pv[z] - \
                                                    supply_chp[z]

                                    if lack_of_power < p_batt_max_out:
                                        chp_used.append(supply_chp[z])
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=0, p_el_out=lack_of_power)
                                        chp_sold.append(0)
                                        demand_after_chp.append(0)
                                        load.append(0)
                                        unload.append(lack_of_power)

                                    if lack_of_power > p_batt_max_out:
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=0, p_el_out=0)
                                        chp_used.append(supply_chp[z])
                                        chp_sold.append(0)
                                        demand_after_chp.append(lack_of_power)
                                        load.append(0)
                                        unload.append(0)

                                if demand_after_pv[z] == supply_chp[z]:
                                    Bes.battery.calc_battery_soc_next_timestep(
                                        p_el_in=0, p_el_out=0)
                                    chp_used.append(supply_chp[z])
                                    chp_sold.append(0)
                                    demand_after_chp.append(0)
                                    load.append(0)
                                    unload.append(0)

                            cumulated_surplus -= np.array(chp_sold)

                            Node['electrical demand'] = np.array(
                                demand_after_chp)
                            Node['chp_used_self'] = sum(chp_used)
                            Node['chp_not_used'] = sum(chp_sold)
                            Node['chp_used_with_batt'] = sum(chp_used) + sum(
                                unload)
                            Node[
                                'electrical demand_without_deg'] = demand_after_chp
                            Node['cumulated_surplus'] = cumulated_surplus

                    if (Node['entity'].bes.hasBattery) == False:
                        # cumulated_surplus saves the inputs of pv and chp
                        cumulated_surplus = np.zeros(
                            len(time_vector.time_vector()))
                        # Initially set to an array of zeros but overwritten if needed!
                        Node['cumulated_surplus'] = cumulated_surplus
                        print()

                        if (Node['entity'].bes.hasHeatpump):
                            general_demand += demand_heatpump

                        if (Node['entity'].bes.hasPv):
                            # pv electricity is very expensive and therefore more important to use than chp!
                            pv_sold = []
                            supply_pv = Node['entity'].bes.pv.getPower()
                            diff1_demand = general_demand - supply_pv
                            for i in range(len(diff1_demand)):
                                if diff1_demand[i] < 0:
                                    pv_sold.append(diff1_demand[i])
                                if diff1_demand[i] > 0:
                                    pv_sold.append(0)
                            pv_used = sum(supply_pv) + sum(pv_sold)
                            general_demand = []
                            for y in range(len(diff1_demand)):
                                if diff1_demand[y] < 0:
                                    general_demand.append(0)
                                if diff1_demand[y] > 0:
                                    general_demand.append(diff1_demand[y])
                            cumulated_surplus += np.array(pv_sold)

                            Node['pv_used_self'] = pv_used
                            Node['pv_not_used'] = -1 * sum(pv_sold)
                            final_electrical_demand = (general_demand)
                            Node['electrical demand'] = np.array(
                                general_demand)
                            Node[
                                'electrical demand_without_deg'] = final_electrical_demand
                            Node['cumulated_surplus'] = cumulated_surplus

                        if (Node['entity'].bes.hasChp):
                            chp_sold = []
                            # print ("2power_electrical_chp",sum(power_el_chp_list))
                            supply_chp = Node['power_el_chp']
                            # supply_chp=np.array(power_el_chp_list)
                            diff2_demand = general_demand - supply_chp
                            for i in range(len(diff2_demand)):
                                if diff2_demand[i] < 0:
                                    chp_sold.append(diff2_demand[i])
                                if diff2_demand[i] > 0:
                                    chp_sold.append(0)
                            chp_used = sum(supply_chp) + sum(chp_sold)
                            general_demand = []
                            for y in range(len(diff2_demand)):
                                if diff2_demand[y] < 0:
                                    general_demand.append(0)
                                if diff2_demand[y] > 0:
                                    general_demand.append(diff2_demand[y])
                            cumulated_surplus += np.array(chp_sold)

                            Node['chp_used_self'] = chp_used
                            Node['chp_not_used'] = -1 * sum(chp_sold)
                            Node['electrical demand'] = np.array(
                                general_demand)
                            final_electrical_demand = (general_demand)
                            Node[
                                'electrical demand_without_deg'] = final_electrical_demand
                            Node['cumulated_surplus'] = cumulated_surplus


                        else:
                            # In case there is a battery without local producer of electrical energy!
                            assert (Node[
                                        'entity'].bes.hasBattery) == False, "Battery System without PV or CHP is useless! Remember that battery only serves local and not interacting with the DEG"

                else:
                    pass

            # This part of the code is now looking for surpluses and lacks of energy within the grid
            # and tries to decrease the amount of self produced energy which has to be sold !
            cumulated_demand = np.zeros(len(time_vector.time_vector()))
            cumulated_surplus = np.zeros(len(time_vector.time_vector()))
            for ii in range(len(dict_city_data[index]['Buildings with bes'])):
                # The surplus which every house BES's creates is added

                cumulated_demand += \
                    self.city_object.nodes[
                        dict_city_data[index]['Buildings with bes'][ii]][
                        'entity'].get_electric_power_curve()
                cumulated_surplus += \
                    self.city_object.nodes[
                        dict_city_data[index]['Buildings with bes'][ii]][
                        'cumulated_surplus']

            not_used = np.zeros(len(time_vector.time_vector()))
            for ii in range(
                    len(dict_city_data[index]['Buildings in subcity'])):
                # the amount of power is determined by the initial demand of power
                # if the cutsomer needs a lot of power he will receive more power from the deg
                # the amount is linear weighed!
                Node = self.city_object.nodes[
                    dict_city_data[index]['Buildings in subcity'][ii]]
                final_electrical_demand_afer_deg = []
                # Ratio is a percent value which says how much of the energy is for a specific customer
                ratio = (sum(self.city_object.nodes[
                                 dict_city_data[index]['Buildings in subcity'][
                                     ii]][
                                 'entity'].get_electric_power_curve()) / sum(
                    cumulated_demand))

                weighted_individual_surplus = np.array(
                    [-1 * ratio * x for x in cumulated_surplus]) + not_used
                demand_deg = \
                    self.city_object.nodes[
                        dict_city_data[index]['Buildings in subcity'][ii]][
                        'electrical demand_without_deg']
                not_used = []

                for z in range(len(demand_deg)):
                    # Energy which is not_used stays in the DEG and might be used at a different node
                    # If not, it is finally sold!

                    if weighted_individual_surplus[z] > demand_deg[z]:
                        not_used.append(
                            weighted_individual_surplus[z] - demand_deg[z])
                        final_electrical_demand_afer_deg.append(0)

                    if weighted_individual_surplus[z] <= demand_deg[z]:
                        not_used.append(0)
                        final_electrical_demand_afer_deg.append(
                            demand_deg[z] - weighted_individual_surplus[z])

                Node['electrical demand_with_deg'] = np.array(
                    final_electrical_demand_afer_deg)
                not_used = np.array(not_used)

            # this energy cant be used within the DEG and has to be sold!
            print("el_energy_not_used:", sum(not_used))


if __name__ == '__main__':

    #  Path definitions
    script_dir = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.dirname(os.path.dirname(script_dir))

    #  City pickle filename
    #  City should hold buildings with energy supply (at least one thermal
    #  energy network connection or a thermal energy systems within each
    #  building)
    city_filename = 'city_clust_simple_with_esys.p'

    #  City object file path
    city_path = os.path.join(src_path, 'cities', 'scripts',
                             'output_overall', city_filename)
    #  Load city pickle file
    #  Load city pickle file
    city_object = pickle.load(open(city_path, 'rb'))

    #  Limit hot water profile to specific max. power value and rescale profile
    do_dhw_man = True
    #  True - Limit and rescale profile
    #  False - Do nothing

    if do_dhw_man:
        #  Do dhw limiting for whole city
        dhwman.dhw_manipulation_city(city_object)

    # Plot city
    citvis.plot_city_district(city=city_object, plot_lhn=True, plot_deg=True,
                              plot_esys=True)

    #  Initialize calculator class with city object
    test = calculator(city_object)

    #  Call assemlber method
    dict_city_data = test.assembler()

    print('Dict city data', dict_city_data)
    # for key in dict_city_data:
    #     print('key', key)
    #     print('value', dict_city_data[key])

    for i in range(len(dict_city_data)):
        test.eb_balances(dict_city_data, i)

    # Pickle and save city file
    save_path = os.path.join(script_dir, 'city_clust_after_energy.p')
    pickle.dump(city_object, open(save_path, mode='wb'))

    print("")
    print("1001")
    print("pv_used_self", city_object.nodes[1001]['pv_used_self'])
    print("pv_used_with_batt", city_object.nodes[1001]['pv_used_with_batt'])
    print("pv_not_used", city_object.nodes[1001]['pv_not_used'])
    print('chp_used_self', city_object.nodes[1001]['chp_used_self'])
    print('chp_used_with_batt', city_object.nodes[1001]['chp_used_with_batt'])
    print('chp_not_used', city_object.nodes[1001]['chp_not_used'])
    print('fuel_demand', (city_object.nodes[1001]['fuel_demand']))
    print('electrical demand',
          sum(city_object.nodes[1001]['electrical demand']))
    print('electrical demand_with_deg',
          sum(city_object.nodes[1001]['electrical demand_with_deg']))
    print()
    print("1002")
    print("pv_used_self", city_object.nodes[1002]['pv_used_self'])
    print("pv_used_with_batt", city_object.nodes[1002]['pv_used_with_batt'])
    print("pv_not_used", city_object.nodes[1002]['pv_not_used'])
    print('chp_used_self', city_object.nodes[1002]['chp_used_self'])
    print('chp_used_with_batt', city_object.nodes[1002]['chp_used_with_batt'])
    print('chp_not_used', city_object.nodes[1002]['chp_not_used'])
    print('fuel_demand', sum(city_object.nodes[1002]['fuel_demand']))
    print('electrical demand',
          sum(city_object.nodes[1002]['electrical demand']))
    print('electrical demand_with_deg',
          sum(city_object.nodes[1002]['electrical demand_with_deg']))
    print()
    print("1003")
    print("pv_used_self", city_object.nodes[1003]['pv_used_self'])
    print("pv_used_with_batt", city_object.nodes[1003]['pv_used_with_batt'])
    print("pv_not_used", city_object.nodes[1003]['pv_not_used'])
    print('chp_used_self', city_object.nodes[1003]['chp_used_self'])
    print('chp_used_with_batt', city_object.nodes[1003]['chp_used_with_batt'])
    print('chp_not_used', city_object.nodes[1003]['chp_not_used'])
    print('fuel_demand', (city_object.nodes[1003]['fuel_demand']))
    print('electrical demand',
          sum(city_object.nodes[1003]['electrical demand']))
    print('electrical demand_with_deg',
          sum(city_object.nodes[1003]['electrical demand_with_deg']))
    print()
    print("1004")
    print("pv_used_self", city_object.nodes[1004]['pv_used_self'])
    print("pv_used_with_batt", city_object.nodes[1004]['pv_used_with_batt'])
    print("pv_not_used", city_object.nodes[1004]['pv_not_used'])
    print('chp_used_self', city_object.nodes[1004]['chp_used_self'])
    print('chp_used_with_batt', city_object.nodes[1004]['chp_used_with_batt'])
    print('chp_not_used', city_object.nodes[1004]['chp_not_used'])
    print('fuel_demand', sum(city_object.nodes[1004]['fuel_demand']))
    print('electrical demand',
          sum(city_object.nodes[1004]['electrical demand']))
    print('electrical demand_with_deg',
          sum(city_object.nodes[1004]['electrical demand_with_deg']))
    print()

    print("1005")
    print("pv_used_self", city_object.nodes[1005]['pv_used_self'])
    print("pv_used_with_batt", city_object.nodes[1005]['pv_used_with_batt'])
    print("pv_not_used", city_object.nodes[1005]['pv_not_used'])
    print('chp_used_self', city_object.nodes[1005]['chp_used_self'])
    print('chp_used_with_batt', city_object.nodes[1005]['chp_used_with_batt'])
    print('chp_not_used', city_object.nodes[1005]['chp_not_used'])
    print('fuel_demand', sum(city_object.nodes[1005]['fuel_demand']))
    print('electrical demand',
          sum(city_object.nodes[1005]['electrical demand']))
    print('electrical demand_with_deg',
          sum(city_object.nodes[1005]['electrical demand_with_deg']))

    print()
    print("1006")
    print("pv_used_self", city_object.nodes[1006]['pv_used_self'])
    print("pv_used_with_batt", city_object.nodes[1006]['pv_used_with_batt'])
    print("pv_not_used", city_object.nodes[1006]['pv_not_used'])
    print('chp_used_self', city_object.nodes[1006]['chp_used_self'])
    print('chp_used_with_batt', city_object.nodes[1006]['chp_used_with_batt'])
    print('chp_not_used', city_object.nodes[1006]['chp_not_used'])
    print('fuel_demand', sum(city_object.nodes[1006]['fuel_demand']))
    print('electrical demand',
          sum(city_object.nodes[1006]['electrical demand']))
    print('electrical demand_with_deg',
          sum(city_object.nodes[1006]['electrical demand_with_deg']))
    print()
    print("1007")
    print("pv_used_self", city_object.nodes[1007]['pv_used_self'])
    print("pv_used_with_batt", city_object.nodes[1007]['pv_used_with_batt'])
    print("pv_not_used", city_object.nodes[1007]['pv_not_used'])
    print('chp_used_self', city_object.nodes[1007]['chp_used_self'])
    print('chp_used_with_batt', city_object.nodes[1007]['chp_used_with_batt'])
    print('chp_not_used', city_object.nodes[1007]['chp_not_used'])
    print('fuel_demand', sum(city_object.nodes[1007]['fuel_demand']))
    print('electrical demand',
          sum(city_object.nodes[1007]['electrical demand']))
    print('electrical demand_with_deg',
          sum(city_object.nodes[1007]['electrical demand_with_deg']))

    print()
    print("1008")
    print("pv_used_self", city_object.nodes[1008]['pv_used_self'])
    print("pv_used_with_batt", city_object.nodes[1008]['pv_used_with_batt'])
    print("pv_not_used", city_object.nodes[1008]['pv_not_used'])
    print('chp_used_self', city_object.nodes[1008]['chp_used_self'])
    print('chp_used_with_batt', city_object.nodes[1008]['chp_used_with_batt'])
    print('chp_not_used', city_object.nodes[1008]['chp_not_used'])
    print('electricity heatpump',
          sum(city_object.nodes[1008]['electricity_heatpump']))
    print('fuel_demand', (city_object.nodes[1008]['fuel_demand']))
    print('electrical demand',
          sum(city_object.nodes[1008]['electrical demand']))
    print('electrical demand_with_deg',
          sum(city_object.nodes[1008]['electrical demand_with_deg']))
    print('Total thermal output:',
          sum(city_object.nodes[1008]['entity'].bes.heatpump.totalQOutput))

    print()
    print("1009")
    print("pv_used_self", city_object.nodes[1009]['pv_used_self'])
    print("pv_used_with_batt", city_object.nodes[1009]['pv_used_with_batt'])
    print("pv_not_used", city_object.nodes[1009]['pv_not_used'])
    print('chp_used_self', city_object.nodes[1009]['chp_used_self'])
    print('chp_used_with_batt', city_object.nodes[1009]['chp_used_with_batt'])
    print('chp_not_used', city_object.nodes[1009]['chp_not_used'])
    print('electricity heatpump',
          sum(city_object.nodes[1009]['electricity_heatpump']))
    print('fuel_demand', (city_object.nodes[1009]['fuel_demand']))
    print('electrical demand',
          sum(city_object.nodes[1009]['electrical demand']))
    print('electrical demand_with_deg',
          sum(city_object.nodes[1009]['electrical demand_with_deg']))

    print()
    print("1010")
    print("pv_used_self", city_object.nodes[1010]['pv_used_self'])
    print("pv_used_with_batt", city_object.nodes[1010]['pv_used_with_batt'])
    print("pv_not_used", city_object.nodes[1010]['pv_not_used'])
    print('chp_used_self', city_object.nodes[1010]['chp_used_self'])
    print('chp_used_with_batt', city_object.nodes[1010]['chp_used_with_batt'])
    print('chp_not_used', city_object.nodes[1010]['chp_not_used'])
    print('fuel_demand', sum(city_object.nodes[1010]['fuel_demand']))
    print('electrical demand',
          sum(city_object.nodes[1010]['electrical demand']))
    print('electrical demand_with_deg',
          sum(city_object.nodes[1010]['electrical demand_with_deg']))
    print()
    print("1011")
    print("pv_used_self", city_object.nodes[1011]['pv_used_self'])
    print("pv_used_with_batt", city_object.nodes[1011]['pv_used_with_batt'])
    print("pv_not_used", city_object.nodes[1011]['pv_not_used'])
    print('chp_used_self', city_object.nodes[1011]['chp_used_self'])
    print('chp_used_with_batt', city_object.nodes[1011]['chp_used_with_batt'])
    print('chp_not_used', city_object.nodes[1011]['chp_not_used'])
    print('fuel_demand', sum(city_object.nodes[1011]['fuel_demand']))
    print('electrical demand',
          sum(city_object.nodes[1011]['electrical demand']))
    print('electrical demand_with_deg',
          sum(city_object.nodes[1011]['electrical demand_with_deg']))
    print()
    print("1012")
    print("pv_used_self", city_object.nodes[1012]['pv_used_self'])
    print("pv_used_with_batt", city_object.nodes[1012]['pv_used_with_batt'])
    print("pv_not_used", city_object.nodes[1012]['pv_not_used'])
    print('chp_used_self', city_object.nodes[1012]['chp_used_self'])
    print('chp_used_with_batt', city_object.nodes[1012]['chp_used_with_batt'])
    print('chp_not_used', city_object.nodes[1012]['chp_not_used'])
    print('fuel_demand', sum(city_object.nodes[1012]['fuel_demand']))
    print('electrical demand',
          sum(city_object.nodes[1012]['electrical demand']))
    print('electrical demand_with_deg',
          sum(city_object.nodes[1012]['electrical demand_with_deg']))
    # print ()
    # print ("1013")
    # print ("pv_used_self",city_object.nodes[1013]['pv_used_self'])
    # print ("pv_used_with_batt",city_object.nodes[1013]['pv_used_with_batt'])
    # print ("pv_not_used",city_object.nodes[1013]['pv_not_used'])
    # print ('chp_used_self',city_object.nodes[1013]['chp_used_self'])
    # print ('chp_used_with_batt',city_object.nodes[1013]['chp_used_with_batt'])
    # print ('chp_not_used',city_object.nodes[1013]['chp_not_used'])
    # print ('fuel_demand',sum(city_object.nodes[1013]['fuel_demand']))
    # print ('electrical demand',sum(city_object.nodes[1013]['electrical demand']))
    # print ('electrical demand_with_deg',sum(city_object.nodes[1013]['electrical demand_with_deg']))
    # print ()
    # print ("1014")
    # print ("pv_used_self",city_object.nodes[1014]['pv_used_self'])
    # print ("pv_used_with_batt",city_object.nodes[1014]['pv_used_with_batt'])
    # print ("pv_not_used",city_object.nodes[1014]['pv_not_used'])
    # print ('chp_used_self',city_object.nodes[1014]['chp_used_self'])
    # print ('chp_used_with_batt',city_object.nodes[1014]['chp_used_with_batt'])
    # print ('chp_not_used',city_object.nodes[1014]['chp_not_used'])
    # print ('fuel_demand',sum(city_object.nodes[1014]['fuel_demand']))
    # print ('electrical demand',sum(city_object.nodes[1014]['electrical demand']))
    # print ('electrical demand_with_deg',sum(city_object.nodes[1014]['electrical demand_with_deg']))
    # print ()
    # print ("1015")
    # print ("pv_used_self",city_object.nodes[1015]['pv_used_self'])
    # print ("pv_used_with_batt",city_object.nodes[1015]['pv_used_with_batt'])
    # print ("pv_not_used",city_object.nodes[1015]['pv_not_used'])
    # print ('chp_used_self',city_object.nodes[1015]['chp_used_self'])
    # print ('chp_used_with_batt',city_object.nodes[1015]['chp_used_with_batt'])
    # print ('chp_not_used',city_object.nodes[1015]['chp_not_used'])
    # print ('fuel_demand',sum(city_object.nodes[1015]['fuel_demand']))
    # print ('electrical demand',sum(city_object.nodes[1015]['electrical demand']))
    # print ('electrical demand_with_deg',sum(city_object.nodes[1015]['electrical demand_with_deg']))
    # print ()
    # print ("1016")
    # print ("pv_used_self",city_object.nodes[1016]['pv_used_self'])
    # print ("pv_used_with_batt",city_object.nodes[1016]['pv_used_with_batt'])
    # print ("pv_not_used",city_object.nodes[1016]['pv_not_used'])
    # print ('chp_used_self',city_object.nodes[1016]['chp_used_self'])
    # print ('chp_used_with_batt',city_object.nodes[1016]['chp_used_with_batt'])
    # print ('chp_not_used',city_object.nodes[1016]['chp_not_used'])
    # print ('fuel_demand',sum(city_object.nodes[1016]['fuel_demand']))
    # print ('electrical demand',sum(city_object.nodes[1016]['electrical demand']))
    # print ('electrical demand_with_deg',sum(city_object.nodes[1016]['electrical demand_with_deg']))
    # print ()
    # print ("1017")
    # print ("pv_used_self",city_object.nodes[1017]['pv_used_self'])
    # print ("pv_used_with_batt",city_object.nodes[1017]['pv_used_with_batt'])
    # print ("pv_not_used",city_object.nodes[1017]['pv_not_used'])
    # print ('chp_used_self',city_object.nodes[1017]['chp_used_self'])
    # print ('chp_used_with_batt',city_object.nodes[1017]['chp_used_with_batt'])
    # print ('chp_not_used',city_object.nodes[1017]['chp_not_used'])
    # print ('fuel_demand',sum(city_object.nodes[1017]['fuel_demand']))
    # print ('electrical demand',sum(city_object.nodes[1017]['electrical demand']))
    # print ('electrical demand_with_deg',sum(city_object.nodes[1017]['electrical demand_with_deg']))
    # print ()
    # print ("1018")
    # print ("pv_used_self",city_object.nodes[1018]['pv_used_self'])
    # print ("pv_used_with_batt",city_object.nodes[1018]['pv_used_with_batt'])
    # print ("pv_not_used",city_object.nodes[1018]['pv_not_used'])
    # print ('chp_used_self',city_object.nodes[1018]['chp_used_self'])
    # print ('chp_used_with_batt',city_object.nodes[1018]['chp_used_with_batt'])
    # print ('chp_not_used',city_object.nodes[1018]['chp_not_used'])
    # print ('fuel_demand',sum(city_object.nodes[1018]['fuel_demand']))
    # print ('electrical demand',sum(city_object.nodes[1018]['electrical demand']))
    # print ('electrical demand_with_deg',sum(city_object.nodes[1018]['electrical demand_with_deg']))
    # print ()
    # print ("1019")
    # print ("pv_used_self",city_object.nodes[1019]['pv_used_self'])
    # print ("pv_used_with_batt",city_object.nodes[1019]['pv_used_with_batt'])
    # print ("pv_not_used",city_object.nodes[1019]['pv_not_used'])
    # print ('chp_used_self',city_object.nodes[1019]['chp_used_self'])
    # print ('chp_used_with_batt',city_object.nodes[1019]['chp_used_with_batt'])
    # print ('chp_not_used',city_object.nodes[1019]['chp_not_used'])
    # print ('fuel_demand',sum(city_object.nodes[1019]['fuel_demand']))
    # print ('electrical demand',sum(city_object.nodes[1019]['electrical demand']))
    # print ('electrical demand_with_deg',sum(city_object.nodes[1019]['electrical demand_with_deg']))
    # print ()
