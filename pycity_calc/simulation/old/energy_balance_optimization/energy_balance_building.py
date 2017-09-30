# coding=utf-8
"""
Script for energy balance calculation. Holds calculator class.
"""
from __future__ import division

__author__ = 'tsh-dor'

import os
import pickle
import itertools
import numpy as np
import pycity_calc.toolbox.networks.network_ops as netop
import pycity_calc.environments.timer as time
import pycity_calc.visualization.city_visual as citvis

# define invalid Individual Error.
class invalidind(Exception):
    pass

class calculator(object):
    def __init__(self, city_object,buffer_hyst=1.5, buffer = 0.2):
        """
        Constructor of calculation class. Adds pointer to city_object.

        Parameters
        ----------
        city_object : object
            City object of pycity_calc
        buffer_hyst: float
            Hysteresis factor, defines how much over the buffer is
        buffer : float
            Buffer factor  (default: 0.2)
        """

        self.city_object = city_object
        self.buffer_hyst = buffer_hyst
        self.buffer = buffer



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
        lhn_con_nodes = \
            netop.get_list_with_energy_net_con_node_ids(self.city_object,
                                                        network_type='heating')

        #  Get list of lists of deg connected building node ids
        deg_con_nodes = \
            netop.get_list_with_energy_net_con_node_ids(self.city_object,
                                                        network_type='electricity')

        #  Get list of all nodes of building entities
        all_building_nodes = self.city_object.get_list_build_entity_node_ids()

        #delete non buildingnodes from lhn_con
        lhn_con = []
        for i in range(len(lhn_con_nodes)):
            # loop over all subcities
            lhn_con.append([buildingnode for buildingnode in lhn_con_nodes[i] if buildingnode in all_building_nodes])

        # delete non buildingnodes from deg_con
        deg_con = []
        for i in range(len(deg_con_nodes)):
            # loop over all subcities
            deg_con.append([buildingnode for buildingnode in deg_con_nodes[i] if buildingnode in all_building_nodes])

        # delete non buildingnodes from deg_con

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

        ####print('Grids in assembler:', grids)
        ####print('LHN con in assembler: ', lhn_con)
        ####print('DEG con in assembler:', deg_con)

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
                Node = self.city_object.node[grids[subcity][node]]
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

        # Save all "print(...)" to a txt file, good for debugging
        #import sys
        #filename = open("resultstest.txt", 'w')
        #sys.stdout = filename

        #  You can add the boiler_temp to every boiler object and later
        #  save the city as results_object
        # time vector needed to initialise the length of arrays
        time_vector = time.TimerExtended(
            timestep=self.city_object.environment.timer.timeDiscretization)


        tes_temp = np.zeros(len(time_vector.time_vector()))
        tes_load = np.zeros(len(time_vector.time_vector()))
        tes_unload = np.zeros(len(time_vector.time_vector()))


        dict_Qlhn = {}

        #  Loop over building list in subcity
        for i in range(len(dict_city_data[index]['Buildings in subcity'])):#TODO:'Buildings in subcity'

            # Initialize result lists
            Qth_sum=np.zeros(time_vector.timestepsTotal)
            Qchp_nom=np.zeros(time_vector.timestepsTotal)
            Qchp_min=np.zeros(time_vector.timestepsTotal)
            Qboiler_nom=np.zeros(time_vector.timestepsTotal)
            Qboiler_min=np.zeros(time_vector.timestepsTotal)
            Qeh_nom=np.zeros(time_vector.timestepsTotal)




            #  Pointer to current node
            Node = self.city_object.node[
                dict_city_data[index]['Buildings in subcity'][i]]#TODO:'Buildings in subcity'


            #  Check if single building holds bes
            if Node['entity'].hasBes == False:
                raise AssertionError("Since there is no lhn, building",
                                     dict_city_data[index][
                                         'Buildings in subcity'][
                                         i],
                                     "needs a thermal supply system!")#TODO:'Buildings in subcity'

            # Check if bes holds thermal energy system
            # has_th_e_sys = False  # Init value
            # if Node['entity'].bes.hasBoiler or Node['entity'].bes.hasChp or Node['entity'].bes.hasElectricalHeater or Node['entity'].bes.hasHeatpump:
            #     has_th_e_sys = True
            #
            # if has_th_e_sys == False:
            #     raise AssertionError(
            #         'Node ' + str(Node) + ' is not holding'
            #                               'thermal energy system, but this is '
            #                               'required for single building!')

            # Since no lhn is available the balances has to be done for
            # each building!
            power_boiler_in_total = np.zeros(len(time_vector.time_vector()))

            #  Current bes
            Bes = Node['entity'].bes


            Node['electricity_heatpump'] = np.zeros(len(time_vector.time_vector()))
            Node['power_el_chp'] = np.zeros(len(time_vector.time_vector()))
            Node['fuel demand'] = np.zeros(len(time_vector.time_vector()))
            Node['heat_demand_for_boiler'] = np.zeros(len(time_vector.time_vector()))
            Node['heat_demand_for_chp'] = np.zeros(len(time_vector.time_vector()))

            #  #---------------------------------------------------------
            if (Node['entity'].bes.hasHeatpump) == True:
                #  Script for Building with HP, Eh and Tes

                power_hp_total = np.zeros(len(time_vector.time_vector()))
                power_eh_total = np.zeros(len(time_vector.time_vector()))

                #  Get heat pump nominals
                hp_qNominal = Node['entity'].bes.heatpump.qNominal
                hp_lal = Node['entity'].bes.heatpump.lowerActivationLimit
                eh_qNominal = Node['entity'].bes.electricalHeater.qNominal

                #  Get space heating demand of building
                sph_demand_building = Node[
                    'entity'].get_space_heating_power_curve()

                #  Get building hot water demand
                dhw_demand_building = Node['entity'].get_dhw_power_curve()

                #  Aggregate demand curves
                thermal_demand_building = sph_demand_building + \
                                          dhw_demand_building
                array_temp = self.city_object.environment.weather.tAmbient

                #  #-----------------------------------------------------
                if (Node['entity'].bes.hasTes) == True:

                    tes_object = Bes.tes

                    # Start temperature of the storage is set as tInit
                    t_tes = Bes.tes.tInit

                    #  Loop over thermal demand of building
                    for ii in range(len(thermal_demand_building)):
                        #print('#######node: ', str(dict_city_data[index]['Buildings in subcity'][i]), '\n','#######timestep: ', ii)

                        ####print('case0')

                        #  Define max. possible input/output power of tes
                        q_out_max_tes = Bes.tes.calc_storage_q_out_max(
                            t_ambient=20, q_in=0, eps=0.11)
                        q_in_max_tes = Bes.tes.calc_storage_q_in_max(
                            t_ambient=20, q_out=0, eps=0.11)

                        # for numerical reasons
                        if Bes.tes.tMax - Bes.tes.t_current < 0.01:
                            q_in_max_tes = 0

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
                            ####print('case1')
                            #  Thermal building demand is larger than
                            #  nominal hp and eh power!
                            #  In case of peak load eh has to run under
                            #  full load conditions!!!

                            if q_out_max_tes < -load_power_max:
                                if (dict_city_data[index]['hasLHN']) == False:

                                    print('Invalid Individual: TES is now emtpy and can not be unloaded')
                                    raise invalidind # raise the invalid Individual Error

                                # else:
                                #     #tes is empty, can't be unloaded. Energy from LHN is needed
                                #     load_power_max=0

                            #  Calc. temperature of next timestep
                            t_tes = \
                                Bes.tes.calc_storage_temp_for_next_timestep(
                                    q_in=0 - 0.01, q_out=-load_power_max,
                                    t_prior=t_tes, t_ambient=20,
                                    set_new_temperature=True,
                                    save_res=True,
                                    time_index=ii)
                            print ('timestep' , ii,'-----',t_tes)
                            #  Calculate power of heat pump (max.)
                            power_hp, power_hp_in = \
                                Bes.heatpump.calc_hp_all_results(
                                    hp_qNominal, array_temp[ii], ii)

                            #  Calculate power of el. heater (max.)
                            power_eh, power_eh_in = \
                                Bes.electricalHeater.calc_el_h_all_results(
                                    eh_qNominal, ii)

                            #  Charging power (zero)
                            tes_load_power = 0
                            #  Uncharging power
                            tes_unload_power = -load_power_max

                        # #---------------------------------------------
                        #  Thermal demand of building is larger than
                        #  possible nominal hp power, but smaller than
                        #  (nominal hp power + nominal eh power) --> HP and EH or TES can supply the demand


                        elif load_power < 0 and load_power_max >= 0:
                            ####print('case4')

                            #TODO: added a if case to check if hp is below partload
                            # sph_demand_building[ii] + 3 / 4 *dhw_demand_building[ii] needs to be supplied by HP
                            # check if hp is below partload
                            # if so then run at partload
                            if hp_lal*hp_qNominal <= sph_demand_building[ii] + 3 / 4 *dhw_demand_building[ii]:
                                hp_therm_out= sph_demand_building[ii] + 3 / 4 *dhw_demand_building[ii]
                            elif hp_lal*hp_qNominal > sph_demand_building[ii] + 3 / 4 *dhw_demand_building[ii]:
                                hp_therm_out=hp_lal*hp_qNominal

                            # hp will probably run at full load
                            power_hp, power_hp_in = \
                                Bes.heatpump.calc_hp_all_results(hp_therm_out, array_temp[ii], ii)


                            tes_load_power = 0
                            q_unc = thermal_demand_building[ii] - power_hp
                            #DEFINE Enom(nominal energy of TES)
                            Enom = tes_object.capacity*tes_object.c_p*(tes_object.tMax - tes_object.t_min)
                            # DEFINE Et(current in time energy of TES)
                            Et = tes_object.calc_storage_curr_amount_of_energy() * 3.6 * 10**6
                            # DEFINE Et_new(current in time energy of TES after 1 loop)
                            Et_new = Et - (q_unc * self.city_object.environment.timer.timeDiscretization)
                            # check the tes conditions to see if tes can be used
                            if q_unc > 0 and Enom* self.buffer < Et_new:
                                # Spaceheating demand greater HPnom, tes is over buffer and can be used
                                ####print('case4.1')

                                #check if unconvered demand can completely be covered by tes
                                if q_unc <= q_out_max_tes:
                                    ####print('case4.1.1')
                                    # Tes max out is enough to cover uncovered demand completely
                                    ####print('case4.1.1')

                                    tes_unload_power = q_unc
                                    tes_load_power = 0
                                    power_eh = 0
                                    power_eh_in = 0

                                    t_tes = Bes.tes.calc_storage_temp_for_next_timestep(
                                    q_in=0, q_out=q_unc,
                                    t_prior=t_tes, t_ambient=20,
                                    set_new_temperature=True,
                                    save_res=True,
                                    time_index=ii)


                                #TODO: migth need futher testing. This case is very rare
                                elif q_unc > q_out_max_tes:
                                    ####print('case4.1.2')
                                    # Tes max out is not enough to cover uncovered demand, switch on EH to support tes
                                    power_eh, power_eh_in = \
                                    Bes.electricalHeater.calc_el_h_all_results(q_unc-q_out_max_tes, ii)
                                    # check if eh can supply the requested energy
                                    if q_unc-q_out_max_tes > eh_qNominal:
                                        print('eh has not enough power')
                                        raise invalidind
                                    tes_unload_power = q_out_max_tes
                                    tes_load_power = 0

                                    t_tes = Bes.tes.calc_storage_temp_for_next_timestep(
                                    q_in=0, q_out=q_out_max_tes,
                                    t_prior=t_tes, t_ambient=20,
                                    set_new_temperature=True,
                                    save_res=True,
                                    time_index=ii)



                            elif q_unc > 0 and Enom* self.buffer >= Et_new:
                                # Spaceheating demand greater HPnom, tes empty, use EH
                                ####print('case4.2')
                                power_eh, power_eh_in = \
                                Bes.electricalHeater.calc_el_h_all_results(q_unc, ii)
                                # check if eh can supply the requested energy
                                if q_unc > eh_qNominal:
                                    print('eh has not enough power')
                                    raise invalidind

                                tes_unload_power = 0
                                t_tes = Bes.tes.calc_storage_temp_for_next_timestep(
                                q_in=0, q_out=0,
                                t_prior=t_tes, t_ambient=20,
                                set_new_temperature=True,
                                save_res=True,
                                time_index=ii)

                            else:
                                power_eh, power_eh_in = \
                                    Bes.electricalHeater.calc_el_h_all_results(1 / 4 *dhw_demand_building[ii], ii)
                                # check if eh can supply the requested energy
                                if 1 / 4 *dhw_demand_building[ii] > eh_qNominal:
                                    print('eh has not enough power')
                                    raise invalidind

                                tes_unload_power = 0
                                t_tes = Bes.tes.calc_storage_temp_for_next_timestep(
                                    q_in=0, q_out=0,
                                    t_prior=t_tes, t_ambient=20,
                                    set_new_temperature=True,
                                    save_res=True,
                                    time_index=ii)

                        # #---------------------------------------------
                        #  Thermal demand of building is larger than
                        #  possible part load power of hp, but smaller than
                        #  nominal hp power --> HP can supply full power
                        #  and charge storage
                        elif thermal_demand_building[
                            ii] > hp_lal * hp_qNominal and load_power >= 0:
                            ####print('case2')

                            if q_in_max_tes >= 0 and load_power >= q_in_max_tes:
                                #  Heatpump supplies house and loads storage q_in_max_tes
                                ####print('case2.1')

                                t_tes = Bes.tes.calc_storage_temp_for_next_timestep(
                                    q_in=q_in_max_tes - 0.01, q_out=0,
                                    t_prior=t_tes, t_ambient=20,
                                    set_new_temperature=True,
                                    save_res=True,
                                    time_index=ii)

                                #TODO: added a if case to check if hp is below partload
                                # sph_demand_building[ii] + 3 / 4 *dhw_demand_building[ii]+ 3 / 4 * q_in_max_tes needs to be supplied by HP
                                # check if hp is below partload
                                # if so then run at partload
                                if hp_lal*hp_qNominal <= sph_demand_building[ii] + 3 / 4 *dhw_demand_building[ii] + 3 / 4 * q_in_max_tes:
                                    hp_therm_out= sph_demand_building[ii] + 3 / 4 *dhw_demand_building[ii] + 3 / 4 * q_in_max_tes
                                elif hp_lal*hp_qNominal > sph_demand_building[ii] + 3 / 4 *dhw_demand_building[ii] + 3 / 4 * q_in_max_tes:
                                    hp_therm_out=hp_lal*hp_qNominal

                                power_hp, power_hp_in = \
                                    Bes.heatpump.calc_hp_all_results(hp_therm_out,array_temp[ii], ii)

                                power_eh, power_eh_in = \
                                    Bes.electricalHeater.calc_el_h_all_results(
                                        1 / 4 * dhw_demand_building[
                                            ii] + 1 / 4 * q_in_max_tes,
                                        ii)

                                # check if eh can supply the requested energy
                                if 1 / 4 * dhw_demand_building[ii] + 1 / 4 * q_in_max_tes > eh_qNominal:
                                    print('eh has not enough power')
                                    raise invalidind

                                tes_load_power = q_in_max_tes
                                tes_unload_power = 0

                            elif q_in_max_tes >= 0 and load_power < \
                                    q_in_max_tes:
                                # Boiler supplies house and loads storage with part load
                                ####print('case2.2')
                                #assert load_power > 0, ("negative load "
                                #                        "impossible --> check size tes and"
                                #                        " demand dhw!. Timestep:", ii)
                                if load_power < 0:
                                    print('Invalid Individual: Negative loadpower of TES')
                                    raise invalidind  # raise the invalid Individual Error

                                t_tes = Bes.tes.calc_storage_temp_for_next_timestep(
                                    q_in=load_power - 0.01, q_out=0,
                                    t_prior=t_tes, t_ambient=20,
                                    set_new_temperature=True,
                                    save_res=True,
                                    time_index=ii)

                                #TODO: added a if case to check if hp is below partload
                                # sph_demand_building[ii] + 3 / 4 *dhw_demand_building[ii]+ 3 / 4 * load_power needs to be supplied by HP
                                # check if hp is below partload
                                # if so then run at partload
                                if hp_lal*hp_qNominal <= sph_demand_building[ii] + 3 / 4 *dhw_demand_building[ii] + 3 / 4 * load_power:
                                    hp_therm_out= sph_demand_building[ii] + 3 / 4 *dhw_demand_building[ii] + 3 / 4 * load_power
                                elif hp_lal*hp_qNominal > sph_demand_building[ii] + 3 / 4 *dhw_demand_building[ii] + 3 / 4 * load_power:
                                    hp_therm_out=hp_lal*hp_qNominal

                                power_hp, power_hp_in = \
                                    Bes.heatpump.calc_hp_all_results(hp_therm_out,array_temp[ii], ii)


                                power_eh, power_eh_in = \
                                    Bes.electricalHeater.calc_el_h_all_results(
                                        1 / 4 * dhw_demand_building[
                                            ii] + 1 / 4 * load_power, ii)
                                # check if eh can supply the requested energy
                                if 1 / 4 * dhw_demand_building[ii] + 1 / 4 * load_power > eh_qNominal:
                                    print('eh has not enough power')
                                    raise invalidind

                                tes_load_power = load_power
                                tes_unload_power = 0


                        # #---------------------------------------------
                        #  Thermal demand power of building is smaller than
                        #  part load behavior of heat pump
                        elif thermal_demand_building[
                            ii] <= hp_lal * hp_qNominal:
                            ####print('case3')

                            # unvered demand
                            q_unc = thermal_demand_building[ii]

                            #DEFINE Enom(nominal energy of TES)
                            Enom = tes_object.capacity*tes_object.c_p*(tes_object.tMax - tes_object.t_min)

                            # DEFINE Et(current in time energy of TES)
                            Et = tes_object.calc_storage_curr_amount_of_energy() * 3.6 * 10**6

                            # DEFINE Et_new(current in time energy of TES after 1 loop)
                            Et_new = Et - (q_unc * self.city_object.environment.timer.timeDiscretization)


                            if q_out_max_tes > 0 and q_out_max_tes >= \
                                    thermal_demand_building[ii] and Enom*self.buffer <= Et_new:
                                # tes has enough energy to unload and is above the buffer
                                ####print('case3.1')

                                t_tes = Bes.tes.calc_storage_temp_for_next_timestep(
                                    q_in=0,
                                    q_out=thermal_demand_building[ii],
                                    t_prior=t_tes, t_ambient=20,
                                    set_new_temperature=True,
                                    save_res=True,
                                    time_index=ii)

                                power_hp = 0
                                power_hp_in = 0
                                power_eh = 0
                                power_eh_in = 0
                                tes_load_power = 0
                                tes_unload_power = thermal_demand_building[
                                    ii]

                            elif q_out_max_tes > 0 and q_out_max_tes < \
                                    thermal_demand_building[ii] or Enom*self.buffer >= Et_new:
                                #  Storage doesn't have enough energy to
                                #  unload
                                ####print('case3.2')

                                hp_max_load_power = hp_qNominal - sph_demand_building[ii] - 3 / 4 *dhw_demand_building[ii]

                                if hp_max_load_power > q_in_max_tes:
                                    # load tes with q_in_max_tes,
                                    ####print('case3.2.1')

                                    #  Charge storage with heat pump
                                    t_tes = Bes.tes.calc_storage_temp_for_next_timestep(
                                        q_in=q_in_max_tes - 0.01, q_out=0,
                                        t_prior=t_tes, t_ambient=20,
                                        set_new_temperature=True,
                                        save_res=True,
                                        time_index=ii)

                                    #TODO: added a if case to check if hp is below partload
                                    # sph_demand_building[ii] + 3 / 4 *dhw_demand_building[ii] + 3 / 4 * q_in_max_tes needs to be supplied by HP
                                    # check if hp is below partload
                                    # if so then run at partload
                                    if hp_lal*hp_qNominal <= sph_demand_building[ii] + 3 / 4 *dhw_demand_building[ii] + 3 / 4 * q_in_max_tes:
                                        hp_therm_out=sph_demand_building[ii] + 3 / 4 *dhw_demand_building[ii] + 3 / 4 * q_in_max_tes
                                    elif hp_lal*hp_qNominal > sph_demand_building[ii] + 3 / 4 *dhw_demand_building[ii] + 3 / 4 * q_in_max_tes:
                                        hp_therm_out=hp_lal*hp_qNominal

                                    #  Use heat pump to cover space heating
                                    #  and charge storage
                                    power_hp, power_hp_in = \
                                        Bes.heatpump.calc_hp_all_results(hp_therm_out,array_temp[ii], ii)

                                    power_eh, power_eh_in = \
                                        Bes.electricalHeater.calc_el_h_all_results(
                                            1 / 4 * dhw_demand_building[
                                                ii] + 1 / 4 * q_in_max_tes,ii)

                                    # check if eh can supply the requested energy
                                    if 1 / 4 * dhw_demand_building[ii] + 1 / 4 * q_in_max_tes > eh_qNominal:
                                        print('eh has not enough power')
                                        raise invalidind

                                    tes_load_power = q_in_max_tes
                                    tes_unload_power = 0

                                elif hp_max_load_power <= q_in_max_tes:
                                    #  Heat pump can cover building
                                    #  thermal power demand, but cannot
                                    #  charge storage with full power
                                    ####print('case3.2.2')

                                    t_tes = Bes.tes.calc_storage_temp_for_next_timestep(
                                        q_in=hp_max_load_power - 0.01,
                                        q_out=0, t_prior=t_tes,
                                        t_ambient=20,
                                        set_new_temperature=True,
                                        save_res=True,
                                        time_index=ii)

                                    #TODO: added a if case to check if hp is below partload
                                    # sph_demand_building[ii] + 3 / 4 *dhw_demand_building[ii] + 3 / 4 * hp_max_load_power needs to be supplied by HP
                                    # check if hp is below partload
                                    # if so then run at partload
                                    if hp_lal*hp_qNominal <= sph_demand_building[ii] + 3 / 4 *dhw_demand_building[ii] + 3 / 4 * hp_max_load_power:
                                        hp_therm_out=sph_demand_building[ii] + 3 / 4 *dhw_demand_building[ii] + 3 / 4 * hp_max_load_power
                                    elif hp_lal*hp_qNominal > sph_demand_building[ii] + 3 / 4 *dhw_demand_building[ii] + 3 / 4 * hp_max_load_power:
                                        hp_therm_out=hp_lal*hp_qNominal

                                    power_hp, power_hp_in = \
                                        Bes.heatpump.calc_hp_all_results(hp_therm_out,array_temp[ii], ii)

                                    power_eh, power_eh_in = \
                                        Bes.electricalHeater.calc_el_h_all_results(
                                            1 / 4 * dhw_demand_building[
                                                ii] + 1 / 4 * hp_max_load_power,ii)

                                    # check if eh can supply the requested energy
                                    if 1 / 4 * dhw_demand_building[ii] + 1 / 4 * hp_max_load_power > eh_qNominal:
                                        print('eh has not enough power')
                                        raise invalidind

                                    tes_load_power = hp_max_load_power
                                    tes_unload_power = 0

                            elif q_out_max_tes <= 0:
                                #  Storage is empty
                                ####print('case3.3')

                                hp_max_load_power = \
                                    hp_qNominal - \
                                    thermal_demand_building[ii]

                                t_tes = Bes.tes.calc_storage_temp_for_next_timestep(
                                    q_in=hp_max_load_power - 0.01, q_out=0,
                                    t_prior=t_tes, t_ambient=20,
                                    set_new_temperature=True,
                                    save_res=True,
                                    time_index=ii)

                                #TODO: added a if case to check if hp is below partload
                                # sph_demand_building[ii] + 3 / 4 *dhw_demand_building[ii] + 3 / 4 * hp_max_load_power needs to be supplied by HP
                                # check if hp is below partload
                                # if so then run at partload
                                if hp_lal*hp_qNominal <= sph_demand_building[ii] + 3 / 4 *dhw_demand_building[ii] + 3 / 4 * hp_max_load_power:
                                    hp_therm_out=sph_demand_building[ii] + 3 / 4 *dhw_demand_building[ii] + 3 / 4 * hp_max_load_power
                                elif hp_lal*hp_qNominal > sph_demand_building[ii] + 3 / 4 *dhw_demand_building[ii] + 3 / 4 * hp_max_load_power:
                                    hp_therm_out=hp_lal*hp_qNominal

                                power_hp, power_hp_in = \
                                    Bes.heatpump.calc_hp_all_results(hp_therm_out,array_temp[ii], ii)

                                power_eh, power_eh_in = \
                                    Bes.electricalHeater.calc_el_h_all_results(
                                        1 / 4 * dhw_demand_building[
                                            ii] + 1 / 4 * hp_max_load_power,
                                        ii)

                                tes_load_power = hp_max_load_power
                                tes_unload_power = 0

                        #elif thermal_demand_building[ii] == 0:
                        #    power_hp = 0
                        #    power_hp_in = 0
                        #    power_eh = 0
                        #    power_eh_in = 0
                        #    tes_load_power = 0
                        #    tes_unload_power = 0

                        power_hp_total[ii] = power_hp_in
                        power_eh_total[ii] = power_eh_in

                        tes_temp[ii] = t_tes
                        tes_load[ii] = tes_load_power
                        tes_unload[ii] = tes_unload_power

                        # FILL UP THE NEW LIST
                        # Qeh_nom[ii] = eh_qNominal - power_eh
                        # if thermal_demand_building[ii] >= power_eh + power_hp + tes_unload_power:
                        #     Qth_sum[ii] = -thermal_demand_building[ii] + power_eh + power_hp + tes_unload_power
                        #     # Only one case, because HP/EH is not supposed to supply energy to LHN


                            ####print('demand: ', thermal_demand_building[ii], '\n',
                              ####'Qhp: ', power_hp, '\n',
                              ####'power_eh_therm: ',power_eh, '\n',
                              ####'Qeh: ', power_eh, '\n',
                              ####'tes_content: ', tes_object.calc_storage_curr_amount_of_energy() * 3.6 * 10**6, '\n'
                              ####'Qtesunload: ', tes_unload_power, '\n',
                              ####'Qtesload: ', tes_load_power, '\n',
                              ####'Qth_sum: ', Qth_sum[ii], '\n')

                    # FILL UP DICT
                    if (dict_city_data[index]['hasLHN']) == True:
                        dict_Qlhn.update({str(dict_city_data[index]['Buildings in subcity'][i]): {"Qsum": Qth_sum, "Qchp_nom": Qchp_nom, "Qchp_min": Qchp_min,
                                             "Qboiler_nom": Qboiler_nom, "Qboiler_min": Qboiler_min,
                                             "Qeh_nom": Qeh_nom}})


                Node['electricity_heatpump'] = (power_hp_total + power_eh_total)

            # #------------------------------------------------------
            #  E. balance for chp usage
            if (Node['entity'].bes.hasChp) == True:
                ####print('################################### hasCHP')
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
                # Start temperature of the storage is set as tInit
                t_tes = Bes.tes.tInit

                power_chp_in_total = np.zeros(len(time_vector.time_vector()))
                power_el_chp_total = np.zeros(len(time_vector.time_vector()))
                power_boiler_in_total = np.zeros(len(time_vector.time_vector()))
                tes_load = np.zeros(len(time_vector.time_vector()))
                tes_unload = np.zeros(len(time_vector.time_vector()))
                tes_temp = np.zeros(len(time_vector.time_vector()))
                total_heat_demand_for_boiler = np.zeros(len(time_vector.time_vector())) # demand which has to be covered by boiler, the actual supplied energy might be higher when LAL condition
                total_heat_demand_for_chp = np.zeros(len(time_vector.time_vector())) # demand which has to be covered by chp, the actual supplied energy might be higher when LAL condition

                #  Loop over every timestep
                #  #-----------------------------------------------------
                for ii in range(len(thermal_demand_building)):
                    print('timestep', ii)
                    #print('#######node: ', str(dict_city_data[index]['Buildings in subcity'][i]), '\n',
                    #          '#######timestep: ', ii)

                    q_out_max_tes = Bes.tes.calc_storage_q_out_max(
                        t_ambient=20, q_in=0, eps=0.11)
                    q_in_max_tes = Bes.tes.calc_storage_q_in_max(
                        t_ambient=20, q_out=0, eps=0.11)

                    # for numerical reasons
                    if Bes.tes.tMax - Bes.tes.t_current < 0.01:
                        q_in_max_tes = 0

                    load_power = chp_qNominal - \
                                 thermal_demand_building[ii]

                    #  #-------------------------------------------------
                    if thermal_demand_building[ii] > chp_qNominal:
                        ####print('case1')
                        #  Thermal demand power  of building is larger than
                        #  nominal thermal chp power

                        if thermal_demand_building[ii] > (
                                    boiler_qNominal + chp_qNominal):
                            ####print('case1.1')
                            #  Thermal demand power of building is larger
                            #  than boiler and chp nominals. Requires
                            #  thermal storage usage

                            #  Power differenz
                            diff = thermal_demand_building[
                                       ii] - boiler_qNominal - chp_qNominal

                            #  Check if tes can provide enough power
                            #assert q_out_max_tes > diff, ("TES is now "
                            #                              "empty and can't"
                            #                              " be unloaded")

                            # Check if boiler has enough energy. If not, don't use it
                            if q_out_max_tes < diff:
                                if (dict_city_data[index]['hasLHN']) == False:
                                    #tes is empty, can't be unloaded. No LHn connection

                                    print('Invalid Individual: TES is now emtpy and can not be unloaded')
                                    raise invalidind  # raise the invalid Individual Error
                                else:
                                    #tes is empty, can't be unloaded. Energy from LHN is needed
                                    diff=0


                            #  Calculate chp behavior with full power
                            (power_thermal_chp, power_electrical_chp, fuel_power_in_chp) = \
                                Bes.chp.th_op_calc_all_results(chp_qNominal,ii)

                            #  Discharge diff power from tes
                            t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                q_in=0, q_out=diff, t_prior=t_tes,
                                t_ambient=20, set_new_temperature=True,
                                save_res=True, time_index=ii)

                            #  Boiler with full power
                            power_boiler, power_boiler_in = \
                                Bes.boiler.calc_boiler_all_results(boiler_qNominal, ii)

                            tes_load_power = 0
                            tes_unload_power = diff
                            total_heat_demand_for_boiler[ii]=boiler_qNominal # demand which has to be covered by boiler, the actual supplied energy might be higher when LAL condition
                            total_heat_demand_for_chp[ii]=chp_qNominal # demand which has to be covered by chp, the actual supplied energy might be higher when LAL condition

                        if thermal_demand_building[ii] <= (
                                    boiler_qNominal + chp_qNominal):
                            #  chp and boiler are running;
                            #  Tes is needed when boiler can't run due
                            #  to lower activation limit!
                            ####print('case1.2')


                            ### Calo ####

                            # WORKING METHOD is to look up on the TES and figure out how much energy we have.
                            # In the first case we have enough energy and we can cover the demand using TES.
                            # In the second case we are in the "below buffer condition" so we need to switch on
                            # the boiler in order to satisfy the demand. Here we get 2 other condition:
                            # when demand is greater than powerboiler_min we just use the boiler to satisfy the demand.
                            # when demand is lower than power_boiler_min we use the boiler at minimum power and
                            # firstly we satisfy the demand and with the "surplus_energy" we fill up the TES

                            # DEFINE Enom(nominal energy of TES)

                            Enom = tes_object.capacity*tes_object.c_p*(tes_object.tMax - tes_object.t_min)

                            # DEFINE Et(current in time energy of TES)
                            Et = tes_object.calc_storage_curr_amount_of_energy() * 3.6 * 10**6

                            #DEFINE q_unc(part of energy demand not covered by CHP)
                            q_unc = thermal_demand_building[ii] - chp_qNominal

                            # DEFINE Et_new(current in time energy of TES after 1 loop)
                            Et_new = Et - (q_unc * self.city_object.environment.timer.timeDiscretization)

                            #  TODO: How do we know that chp is not below min. part load?

                            #CASE 1
                            if Et_new > self.buffer * Enom:
                                ####print('case1.2.1')

                                t_tes = \
                                    tes_object.calc_storage_temp_for_next_timestep(
                                        q_in=0,
                                        q_out=q_unc,
                                        t_prior=t_tes, t_ambient=20,
                                        set_new_temperature=True,
                                        save_res=True, time_index=ii)

                                (power_thermal_chp, power_electrical_chp, fuel_power_in_chp) = \
                                    Bes.chp.th_op_calc_all_results(chp_qNominal, ii)

                                power_boiler = 0
                                power_boiler_in = 0
                                tes_load_power = 0
                                tes_unload_power = q_unc
                                total_heat_demand_for_boiler[ii]=0 # demand which has to be covered by boiler, the actual supplied energy might be higher when LAL condition
                                total_heat_demand_for_chp[ii]=chp_qNominal # demand which has to be covered by chp, the actual supplied energy might be higher when LAL condition

                            #CASE 2
                            elif Et_new < self.buffer * Enom:
                                ####print('case1.2.2')

                                delta = (Enom * self.buffer - Et_new) / self.city_object.environment.timer.timeDiscretization

                                if delta *self.buffer_hyst> q_in_max_tes:
                                    #check if delta*self.buffer_hyst is greater than tes max in
                                    # if so delta must be reduced
                                    delta = q_in_max_tes / self.buffer_hyst * 0.99999

                                if delta *self.buffer_hyst> boiler_qNominal + chp_qNominal - thermal_demand_building[ii]:
                                    # check if necessary load power is greater than boiler q_nom,
                                    # if so set to load power(delta) to maximum possible boiler power
                                    delta = (boiler_qNominal + chp_qNominal - thermal_demand_building[ii]) *0.99999 / self.buffer_hyst

                                if q_unc > boiler_lal * boiler_qNominal:
                                    # BOILER: supply the q_unc
                                    ########print('case1.2.2.1')

                                    #TODO: added a if case to check if energy can be stored
                                    # check if delta * self.buffer_hyst can be stored in tes
                                    # if not, then only store q_in_max_tes
                                    if q_in_max_tes > delta * self.buffer_hyst:
                                        q_in_tes=delta * self.buffer_hyst
                                    elif q_in_max_tes <= delta * self.buffer_hyst:
                                        q_in_tes=q_in_max_tes * 0.9999

                                    t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                        q_in=q_in_tes, q_out=0,
                                        t_prior=t_tes, t_ambient=20,
                                        set_new_temperature=True,
                                        save_res=True, time_index=ii)

                                    #  Calculate chp behavior
                                    (power_thermal_chp, power_electrical_chp, fuel_power_in_chp) = \
                                        Bes.chp.th_op_calc_all_results(chp_qNominal, ii)

                                    #TODO: added a if case to check if boiler is working below partload
                                    # q_unc + delta * self.buffer_hyst need to be covered by th boiler
                                    # check if boiler is working below partload
                                    # if so run at partload
                                    if q_unc + delta * self.buffer_hyst > boiler_qNominal*boiler_lal:
                                        boiler_therm_out = q_unc + delta * self.buffer_hyst
                                    elif q_unc + delta * self.buffer_hyst <= boiler_qNominal*boiler_lal:
                                        boiler_therm_out = boiler_qNominal*boiler_lal

                                    power_boiler, power_boiler_in = \
                                        Bes.boiler.calc_boiler_all_results(boiler_therm_out,ii)

                                    tes_load_power = delta * self.buffer_hyst
                                    tes_unload_power = 0
                                    total_heat_demand_for_boiler[ii]=q_unc + delta * self.buffer_hyst # demand which has to be covered by boiler, the actual supplied energy might be higher when LAL condition
                                    total_heat_demand_for_chp[ii]=chp_qNominal # demand which has to be covered by chp, the actual supplied energy might be higher when LAL condition


                                else:
                                    # BOILER supply q_unc and fill up the TES
                                    ####print('case1.2.2.2')
                                    #TODO: added a if case to check if energy can be stored
                                    # check if (boiler_qNominal * boiler_lal) - q_unc can be stored in tes
                                    # if not, then only store q_in_max_tes
                                    if q_in_max_tes > (boiler_qNominal * boiler_lal) - q_unc:
                                        q_in_tes=(boiler_qNominal * boiler_lal) - q_unc
                                    elif q_in_max_tes <= (boiler_qNominal * boiler_lal) - q_unc:
                                        q_in_tes=q_in_max_tes * 0.9999

                                    t_tes = \
                                        tes_object.calc_storage_temp_for_next_timestep(
                                            q_in=q_in_tes,
                                            q_out=0,
                                            t_prior=t_tes, t_ambient=20,
                                            set_new_temperature=True,
                                            save_res=True, time_index=ii)

                                    (power_thermal_chp, power_electrical_chp, fuel_power_in_chp) = \
                                        Bes.chp.th_op_calc_all_results(chp_qNominal, ii)

                                    power_boiler, power_boiler_in = Bes.boiler.calc_boiler_all_results(
                                                     boiler_qNominal * boiler_lal, ii)
                                    tes_load_power = (boiler_qNominal * boiler_lal) - q_unc

                                    tes_unload_power = 0
                                    total_heat_demand_for_boiler[ii]=boiler_qNominal * boiler_lal # demand which has to be covered by boiler, the actual supplied energy might be higher when LAL condition
                                    total_heat_demand_for_chp[ii]=chp_qNominal # demand which has to be covered by chp, the actual supplied energy might be higher when LAL condition


                    elif thermal_demand_building[
                        ii] > chp_lal * chp_qNominal and \
                                    thermal_demand_building[
                                        ii] <= chp_qNominal:
                        # chp is running and loads the tes if possible;
                        # TES off
                        # In this case the TES is filled up using the load_power(energy from CHP, so is covenient
                        # fill up the TES with this type of energy
                        ########print('case2')
                        if q_in_max_tes > 0 and load_power > q_in_max_tes:
                            ####print('case2.1')

                            t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                q_in=q_in_max_tes *0.9999, q_out=0,
                                t_prior=t_tes, t_ambient=20,
                                set_new_temperature=True,
                                save_res=True, time_index=ii)

                            (power_thermal_chp, power_electrical_chp, fuel_power_in_chp) = \
                                Bes.chp.th_op_calc_all_results(
                                    thermal_demand_building[ii] + q_in_max_tes, ii)


                            power_boiler = 0
                            power_boiler_in = 0
                            tes_load_power = q_in_max_tes
                            tes_unload_power = 0
                            total_heat_demand_for_boiler[ii]=0 # demand which has to be covered by boiler, the actual supplied energy might be higher when LAL condition
                            total_heat_demand_for_chp[ii]=thermal_demand_building[ii] + q_in_max_tes # demand which has to be covered by chp, the actual supplied energy might be higher when LAL condition

                        elif q_in_max_tes > 0 and load_power <= q_in_max_tes:
                            #  chp available power can be used ot charge
                            #  tes, but will not be able to fully load it
                            ####print('case2.2')

                            #assert load_power > 0, ("negative load "
                            #                        "impossible --> check"
                            #                        " size tes and demand"
                            #                        " dhw! Timestep: ", ii)
                            if load_power < 0:
                                print('Invalid Individual: negative load power of TES')
                                raise invalidind  # raise the invalid Individual Error

                            #  Load tes with load_power (chp - build power)
                            t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                q_in=load_power, q_out=0, t_prior=t_tes,
                                t_ambient=20, set_new_temperature=True,
                                save_res=True, time_index=ii)

                            (power_thermal_chp, power_electrical_chp, fuel_power_in_chp) = \
                                Bes.chp.th_op_calc_all_results(
                                    thermal_demand_building[ii] + load_power, ii)

                            power_boiler = 0
                            power_boiler_in = 0
                            tes_load_power = load_power
                            tes_unload_power = 0
                            total_heat_demand_for_boiler[ii] = 0 # demand which has to be covered by boiler, the actual supplied energy might be higher when LAL condition
                            total_heat_demand_for_chp[ii] = thermal_demand_building[ii]+ load_power # demand which has to be covered by chp, the actual supplied energy might be higher when LAL condition
                        #TODO: added this case because there was no case for a fully loaded tes!
                        elif q_in_max_tes <= 0:
                            # the tes is full.
                            t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                q_in=0, q_out=0,
                                t_prior=t_tes, t_ambient=20,
                                set_new_temperature=True,
                                save_res=True, time_index=ii)

                            (power_thermal_chp, power_electrical_chp, fuel_power_in_chp) = \
                                Bes.chp.th_op_calc_all_results(
                                    thermal_demand_building[ii], ii)


                            power_boiler = 0
                            power_boiler_in = 0
                            tes_load_power = 0
                            tes_unload_power = 0
                            total_heat_demand_for_boiler[ii]=0 # demand which has to be covered by boiler, the actual supplied energy might be higher when LAL condition
                            total_heat_demand_for_chp[ii]=thermal_demand_building[ii] # demand which has to be covered by chp, the actual supplied energy might be higher when LAL condition


                    elif thermal_demand_building[
                        ii] <= chp_lal * chp_qNominal and thermal_demand_building[ii] != 0:
                        # under chp minimum condition. Use tes or run chp_lal an charge tes
                        ####print('case3')

                        # DEFINE Enom(nominal energy of TES)
                        Enom = tes_object.capacity*tes_object.c_p*(tes_object.tMax - tes_object.t_min)

                        # DEFINE Et(current in time energy of TES)
                        Et = tes_object.calc_storage_curr_amount_of_energy() * 3.6 * 10**6

                        #DEFINE q_unc, amount which needs to be supllied by tes
                        q_unc = thermal_demand_building[ii]

                        # DEFINE Et_new(current in time energy of TES after 1 loop)
                        Et_new = Et - (q_unc * self.city_object.environment.timer.timeDiscretization)


                        '''
                        if q_out_max_tes > 0 and q_out_max_tes > \
                                thermal_demand_building[ii]:
                            # tes has enough energy to unload
                            ####print('case3.1')
                        '''

                        if Enom * self.buffer <= Et_new and q_out_max_tes >= thermal_demand_building[ii]:
                            #tes has enough energy and is over buffer, tes can supply the demand
                            ####print('case3.1')
                            t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                q_in=0, q_out=thermal_demand_building[ii],
                                t_prior=t_tes, set_new_temperature=True,
                                save_res=True, time_index=ii)

                            power_thermal_chp = 0
                            power_electrical_chp = 0
                            fuel_power_in_chp = 0
                            power_boiler = 0
                            power_boiler_in = 0
                            tes_load_power = 0
                            tes_unload_power = thermal_demand_building[ii]
                            total_heat_demand_for_boiler[ii] = 0 # demand which has to be covered by boiler, the actual supplied energy might be higher when LAL condition
                            total_heat_demand_for_chp[ii] = 0 # demand which has to be covered by chp, the actual supplied energy might be higher when LAL condition

                        elif Enom * self.buffer > Et_new or q_out_max_tes < thermal_demand_building[ii]:
                            #tes is below buffer. tes needs to be loaded. Demand and loadpower is covered by chp
                            ####print('case3.2')

                            #TODO: added a if case to check if energy can be stored
                            # check if chp_qNominal * chp_lal - thermal_demand_building[ii] can be stored in tes
                            # if not, then only store q_in_max_tes
                            if q_in_max_tes > chp_qNominal * chp_lal - thermal_demand_building[ii]:
                                q_in_tes=chp_qNominal * chp_lal - thermal_demand_building[ii]
                            elif q_in_max_tes <= chp_qNominal * chp_lal - thermal_demand_building[ii]:
                                q_in_tes=q_in_max_tes*0.99999

                            t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                q_in=q_in_tes, q_out=0,
                                t_prior=t_tes,
                                set_new_temperature=True,
                                save_res=True, time_index=ii)
                            (power_thermal_chp, power_electrical_chp, fuel_power_in_chp) = \
                                Bes.chp.th_op_calc_all_results(chp_qNominal* chp_lal, ii)
                            power_boiler = 0
                            power_boiler_in = 0
                            tes_load_power = q_in_tes
                            tes_unload_power = 0
                            total_heat_demand_for_boiler[ii]=0 # demand which has to be covered by boiler, the actual supplied energy might be higher when LAL condition
                            total_heat_demand_for_chp[ii]=thermal_demand_building[ii] + q_in_tes# demand which has to be covered by chp, the actual supplied energy might be higher when LAL condition


                    elif thermal_demand_building[ii] == 0:
                        ####print('case4')
                        t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                q_in=0, q_out=0,
                                t_prior=t_tes,
                                set_new_temperature=True,
                                save_res=True, time_index=ii)

                        Bes.chp.totalQOutput[ii] = 0
                        Bes.chp.totalPOutput[ii] = 0
                        Bes.chp.array_fuel_power[ii] = 0


                        power_thermal_chp = 0
                        power_electrical_chp = 0
                        fuel_power_in_chp = 0
                        power_boiler = 0
                        power_boiler_in = 0
                        tes_load_power = 0
                        tes_unload_power = 0
                        total_heat_demand_for_boiler[ii]=0 # demand which has to be covered by boiler, the actual supplied energy might be higher when LAL condition
                        total_heat_demand_for_chp[ii]=0 # demand which has to be covered by chp, the actual supplied energy might be higher when LAL condition

                    power_chp_in_total[ii] = fuel_power_in_chp
                    power_el_chp_total[ii] = power_electrical_chp
                    power_boiler_in_total[ii]=power_boiler_in
                    tes_load[ii] = tes_load_power
                    tes_unload[ii] = tes_unload_power
                    tes_temp[ii] = t_tes

                    # FILL UP THE NEW LIST

                    Qchp_nom[ii] = chp_qNominal - total_heat_demand_for_chp[ii]
                    if chp_qNominal * chp_lal - total_heat_demand_for_chp[ii] >= 0:
                        Qchp_min[ii] = chp_qNominal * chp_lal - total_heat_demand_for_chp[ii]
                    Qboiler_nom[ii] = boiler_qNominal - total_heat_demand_for_boiler[ii]
                    if boiler_qNominal * boiler_lal - total_heat_demand_for_boiler[ii] >= 0:
                        Qboiler_min[ii] = boiler_qNominal * boiler_lal - total_heat_demand_for_boiler[ii]
                    Qth_sum[ii] = -thermal_demand_building[ii] + chp_qNominal + boiler_qNominal \
                                  + tes_unload_power - tes_load_power


                    ####print('demand: ', thermal_demand_building[ii], '\n',
                    ####'Qchp: ', power_thermal_chp, '\n',
                    ####'Qboiler: ', power_boiler, '\n',
                    ####'tes_content: ', tes_object.calc_storage_curr_amount_of_energy() * 3.6 * 10**6, '\n',
                    ####'Qtesunload: ', tes_unload_power, '\n',
                    ####'Qtesload: ', tes_load_power, '\n',
                    ####'Qth_sum: ', Qth_sum[ii], '\n',
                    ####'supply/demand for/from lhn: ', '\n',
                    ####'Qchp_nom: ', Qchp_nom[ii], '\n',
                    ####'Qchp_min: ', Qchp_min[ii], '\n',
                    ####'Qbpoiler_nom: ', Qboiler_nom[ii], '\n',
                    ####'Qboiler_min: ', Qboiler_min[ii], '\n',)

                # FILL UP DICT
                if (dict_city_data[index]['hasLHN']) == True:
                    dict_Qlhn.update({str(dict_city_data[index]['Buildings in subcity'][i]): {"Qsum": Qth_sum, "Qchp_nom": Qchp_nom, "Qchp_min": Qchp_min,
                                            "Qboiler_nom": Qboiler_nom, "Qboiler_min": Qboiler_min,
                                            "Qeh_nom": Qeh_nom}})

                Node['power_el_chp'] = power_el_chp_total
                Node['fuel demand'] = (power_boiler_in_total + power_chp_in_total)
                Node['heat_demand_for_boiler'] = total_heat_demand_for_boiler # demand which has to be covered by boiler, the actual supplied energy might be higher when LAL condition
                Node['heat_demand_for_chp'] = total_heat_demand_for_chp # demand which has to be covered by chp, the actual supplied energy might be higher when LAL condition

            # #---------------------------------------------------------
            if (Node['entity'].bes.hasBoiler) == True and (
                        Node['entity'].bes.hasChp == False):
                ####print('################################### hasBoiler only')
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

                    # Start temperature of the storage is set as tInit
                    t_tes = Bes.tes.tInit

                    total_heat_demand_for_boiler = np.zeros(len(time_vector.time_vector()))


                    for ii in range(len(thermal_demand_building)):
                        print('timestep', ii)
                        ####print('#######node: ', str(dict_city_data[index]['Buildings in subcity'][i]), '\n',
                              ####'#######timestep: ', ii)

                        q_out_max_tes = Bes.tes.calc_storage_q_out_max(
                            t_ambient=20, q_in=0, eps=0.11)
                        q_in_max_tes = Bes.tes.calc_storage_q_in_max(
                            t_ambient=20, q_out=0, eps=0.11)
                        # for numerical reasons
                        if Bes.tes.tMax - Bes.tes.t_current < 0.01:
                            q_in_max_tes = 0

                        # when t_tes almost equal to t_tes_max tes_object.calc_storage_temp_for_next_timestep was unstable
                        #if q_in_max_tes <= 0.1:
                        #            q_in_max_tes = 0
                        area = tes_object.calc_storage_outside_area()
                        load_power = boiler_qNominal - \
                                     thermal_demand_building[ii]

                        ###############################
                        ###############################
                        ###############################

                        Enom = tes_object.capacity*tes_object.c_p*(tes_object.tMax - tes_object.t_min)

                        # DEFINE Et(current in time energy of TES)
                        Et = tes_object.calc_storage_curr_amount_of_energy() * 3.6 * 10**6

                        #DEFINE q_unc(part of energy demand not covered by CHP)
                        q_unc = thermal_demand_building[ii]


                        # DEFINE Et_new(current in time energy of TES after 1 loop)
                        Et_new = Et - (q_unc * self.city_object.environment.timer.timeDiscretization)

                        ##################################
                        ##################################
                        ##################################

                        if load_power < 0:
                            # demand greater than boiler nominal. Tes needs to be unloaded

                            ####print('case1')
                            # assert q_out_max_tes > -load_power, ("TES is "
                            #                                     "now empty and can't be unloaded")

                            if q_out_max_tes < -load_power:
                                ####print('case1.1')
                                if (dict_city_data[index]['hasLHN']) == False:
                                    #tes is empty, can't be unloaded. No LHn connection
                                    #assert q_out_max_tes > -load_power, ("TES is "
                                    #                             "now empty and can't be unloaded. Timestep: ", ii
                                    if q_out_max_tes < -load_power:
                                        print('Invalid Individual: TES is now emtpy and can not be unloaded')
                                        raise invalidind  # raise the invalid Individual Error
                                else:
                                    #tes is empty, can't be unloaded. Energy from LHN is needed
                                    load_power=0

                            t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                q_in=0, q_out=-load_power,
                                t_prior=t_tes, t_ambient=20,
                                set_new_temperature=True,
                                save_res=True, time_index=ii)

                            power_boiler, power_boiler_in = Bes.boiler.calc_boiler_all_results(boiler_qNominal, ii)

                            tes_load_power = 0
                            tes_unload_power = -load_power

                            total_heat_demand_for_boiler[ii]=boiler_qNominal # demand which has to be covered by boiler, the actual supplied energy might be higher when LAL condition


                         ########### Calo ###########
                        # In the first case demand > q_boiler_min switch on the boiler in order to cover the demand
                        # In the second case demand < q_boiler_min switch on the boiler (until to the min_power)
                        # to cover demand and charge tes(if there is enough space, otherwise charge
                        # as much as possible using q_in_curr)


                        # CASE 1
                        elif thermal_demand_building[ii] > (boiler_lal * boiler_qNominal) and load_power >= 0:
                            # demand between boiler_nom and boiler_lal. Boiler in partload
                            ####print('case2')

                            if Enom * self.buffer < Et_new:
                                # Demand is covered by boiler. Tes is not loaded, because it's above buffer value
                                ####print('case2.1')
                                t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                     q_in=0, q_out=0,
                                     t_prior=t_tes, t_ambient=20,
                                     set_new_temperature=True,
                                     save_res=True, time_index=ii)

                                power_boiler, power_boiler_in = Bes.boiler.calc_boiler_all_results(thermal_demand_building[ii], ii)
                                tes_load_power = 0
                                tes_unload_power = 0
                                total_heat_demand_for_boiler[ii]=thermal_demand_building[ii] # demand which has to be covered by boiler, the actual supplied energy might be higher when LAL condition

                            else:
                                # Demand is covered by boiler. Tes is below buffer. Tes loads with boilerLaL-demand delta*self.buffer_hyst
                                # buffer_hyst is a hysteresis factor to load above the buffer value
                                ####print('case2.2')

                                delta = (Enom * self.buffer - Et_new) / self.city_object.environment.timer.timeDiscretization

                                if delta *self.buffer_hyst> q_in_max_tes:
                                    #check if delta*self.buffer_hyst is greater than tes max in
                                    # if so delta must be reduced
                                    delta = q_in_max_tes * 0.99999 / self.buffer_hyst

                                if delta *self.buffer_hyst> boiler_qNominal - thermal_demand_building[ii]:
                                    # check if necessary load power is greater than boiler q_nom,
                                    # if so set to load power(delta) to maximum possible boiler power
                                    delta = (boiler_qNominal - thermal_demand_building[ii]) * 0.99999 / self.buffer_hyst

                                #TODO: added a if case to check if energy can be stored
                                # check if delta*self.buffer_hyst can be stored in tes
                                # if not, then only store q_in_max_tes
                                if q_in_max_tes > delta*self.buffer_hyst:
                                    q_in_tes=delta*self.buffer_hyst
                                elif q_in_max_tes <= delta*self.buffer_hyst:
                                    q_in_tes=q_in_max_tes*0.99999

                                t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                    q_in=q_in_tes, q_out=0,
                                    t_prior=t_tes,
                                    set_new_temperature=True,
                                    save_res=True, time_index=ii)

                                power_boiler, power_boiler_in = Bes.boiler.calc_boiler_all_results(
                                                  thermal_demand_building[ii] + delta * self.buffer_hyst, ii)
                                tes_load_power = delta*self.buffer_hyst
                                tes_unload_power = 0
                                total_heat_demand_for_boiler[ii]=thermal_demand_building[ii] + delta * self.buffer_hyst # demand which has to be covered by boiler, the actual supplied energy might be higher when LAL condition


                        # CASE 2
                        elif thermal_demand_building[ii] <= (boiler_lal * boiler_qNominal) and thermal_demand_building[ii]!= 0:
                            # Demand is smaller than boiler_lal. Demand is covered by boiler if tes is below buffer. If tes has enough energy demand is covered by tes
                            ####print('case3')
                            if Enom * self.buffer < Et_new:
                                # demand is covered by tes
                                t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                            q_in=0 , q_out=thermal_demand_building[ii],
                                            t_prior=t_tes,
                                            set_new_temperature=True,
                                            save_res=True, time_index=ii)

                                power_boiler = 0
                                power_boiler_in = 0
                                tes_load_power = 0
                                tes_unload_power = thermal_demand_building[ii]
                                total_heat_demand_for_boiler[ii]= 0
                            else:
                                # demand cannot be covered by tes because it is below buffer
                                if q_in_max_tes>(boiler_qNominal * boiler_lal - thermal_demand_building[ii]):
                                    # tes is loaded with remaining boiler power (boiler_lal-demand)
                                    ####print('case3.1')
                                    t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                            q_in=boiler_qNominal * boiler_lal - thermal_demand_building[ii], q_out=0,
                                            t_prior=t_tes,
                                            set_new_temperature=True,
                                            save_res=True, time_index=ii)

                                    power_boiler, power_boiler_in = Bes.boiler.calc_boiler_all_results(
                                                      boiler_qNominal * boiler_lal, ii)
                                    tes_load_power = boiler_qNominal * boiler_lal - thermal_demand_building[ii]
                                    tes_unload_power = 0
                                    total_heat_demand_for_boiler[ii]=boiler_qNominal * boiler_lal # demand which has to be covered by boiler, the actual supplied energy might be higher when LAL condition

                                elif q_in_max_tes<=(boiler_qNominal * boiler_lal - thermal_demand_building[ii]):
                                    #tes is almost fully loaded. It is charged to 100%, the rest of boiler energy will be wasted

                                    t_tes = tes_object.calc_storage_temp_for_next_timestep(
                                       q_in=q_in_max_tes*0.999, q_out=0,
                                       t_prior=t_tes,
                                       set_new_temperature=True,
                                       save_res=True, time_index=ii)  # 0.999 factor is necessary because otherwise t_tes<t_tes_max might be violated
                                    power_boiler, power_boiler_in = Bes.boiler.calc_boiler_all_results(
                                                    boiler_qNominal * boiler_lal, ii)
                                    tes_load_power = q_in_max_tes
                                    tes_unload_power = 0
                                    total_heat_demand_for_boiler[ii]=thermal_demand_building[ii]+q_in_max_tes # demand which has to be covered by boiler, the actual supplied energy might be higher when LAL condition


                                    tes_unload_power = 0

                        if thermal_demand_building[ii]== 0:
                            # if demand is zero
                            ####print('case3.2.1')
                            t_tes = tes_object.calc_storage_temp_for_next_timestep(
                               q_in=0, q_out=0,
                               t_prior=t_tes,
                               set_new_temperature=True,
                               save_res=True, time_index=ii)
                            power_boiler = 0
                            power_boiler_in = 0
                            tes_load_power = 0
                            tes_unload_power = 0
                            total_heat_demand_for_boiler[ii]=0 # demand which has to be covered by boiler, the actual supplied energy might be higher when LAL condition

                        # FILL UP THE NEW LIST
                        if boiler_qNominal > thermal_demand_building[ii]:
                            Qboiler_nom[ii]=boiler_qNominal - thermal_demand_building[ii] -tes_load_power
                        if boiler_qNominal * boiler_lal - total_heat_demand_for_boiler[ii] >= 0:
                            Qboiler_min[ii]=boiler_qNominal * boiler_lal - total_heat_demand_for_boiler[ii]
                        Qth_sum[ii] = boiler_qNominal + tes_unload_power - tes_load_power - thermal_demand_building[ii]



                        power_boiler_in_total[ii]=power_boiler_in

                        ####print('demand: ', thermal_demand_building[ii], '\n',
                        ####'Qboiler: ', power_boiler, '\n',
                        ####'tes_content: ', tes_object.calc_storage_curr_amount_of_energy() * 3.6 * 10**6, '\n',
                        ####'Qtesunload: ', tes_unload_power, '\n',
                        ####'Qtesload: ', tes_load_power, '\n',
                        ####'Qth_sum: ', Qth_sum[ii], '\n',
                        ####'supply/demand for/from lhn: ', '\n',
                        ####'Qbpoiler_nom: ', Qboiler_nom[ii], '\n',
                        ####'Qboiler_min: ', Qboiler_min[ii], '\n',)

                    # FILL UP DICT
                    if (dict_city_data[index]['hasLHN']) == True:
                        dict_Qlhn.update({str(dict_city_data[index]['Buildings in subcity'][i]): {"Qsum": Qth_sum, "Qchp_nom": Qchp_nom, "Qchp_min": Qchp_min,
                                             "Qboiler_nom": Qboiler_nom, "Qboiler_min": Qboiler_min,
                                             "Qeh_nom": Qeh_nom}})

                    Node['heat_demand_for_boiler'] = total_heat_demand_for_boiler
                    Node['fuel demand'] = power_boiler_in_total

                if (Node['entity'].bes.hasTes) == False:

                    total_heat_demand_for_boiler = np.zeros(len(time_vector.time_vector()))

                    Bes = self.city_object.node[dict_city_data[index]["Buildings with bes"][i]]['entity'].bes
                    if boiler_qNominal <= max(thermal_demand_building):
                        # if boilernom is smaller than demand check if LHN connected to cover missing demand
                        if (dict_city_data[index]['hasLHN']) == False:
                            #assert boiler_qNominal >= max(
                            #    thermal_demand_building), ('Thermal demand is ' +
                            #                            'higher than Boiler_qNominal.')
                            if boiler_qNominal < max(thermal_demand_building):
                                print('Invalid Individual: Thermal demand is higher than Boiler_qNominal')
                                raise invalidind  # raise the invalid Individual Error

                    for ii in range(len(thermal_demand_building)):

                        ####print('#######node: ', str(dict_city_data[index]['Buildings in subcity'][i]), '\n',
                              ####'#######timestep: ', ii)
                        if thermal_demand_building[ii]>= boiler_qNominal*boiler_lal:
                            power_boiler, power_boiler_in = Bes.boiler.calc_boiler_all_results(
                                thermal_demand_building[ii], ii)
                            power_boiler_in_total[ii]=power_boiler_in
                            total_heat_demand_for_boiler[ii]=thermal_demand_building[ii]
                        elif thermal_demand_building[ii]< boiler_qNominal*boiler_lal and thermal_demand_building[ii]>0:
                            power_boiler, power_boiler_in = Bes.boiler.calc_boiler_all_results(
                                boiler_qNominal*boiler_lal, ii)
                            power_boiler_in_total[ii]=power_boiler_in
                            total_heat_demand_for_boiler[ii]=boiler_qNominal*boiler_lal
                        elif thermal_demand_building[ii] == 0:
                            power_boiler = 0
                            power_boiler_in = 0
                            power_boiler_in_total[ii]=0
                            total_heat_demand_for_boiler[ii]= 0



                        # FILL UP THE NEW LIST
                        if boiler_qNominal > thermal_demand_building[ii]:
                            Qboiler_nom[ii]=boiler_qNominal - thermal_demand_building[ii]
                        if boiler_qNominal * boiler_lal > thermal_demand_building[ii]:
                            Qboiler_min[ii]=boiler_qNominal * boiler_lal - total_heat_demand_for_boiler[ii]
                        Qth_sum[ii] = boiler_qNominal - total_heat_demand_for_boiler[ii]


                        ####print('demand: ', thermal_demand_building[ii], '\n',
                        ####'Qboiler: ', power_boiler, '\n',
                        ####'Qth_sum: ', Qth_sum[ii], '\n',
                        ####'supply/demand for/from lhn: ', '\n',
                        ####'Qbpoiler_nom: ', Qboiler_nom[ii], '\n',
                        ####'Qboiler_min: ', Qboiler_min[ii], '\n',)

                    # FILL UP THE DICT
                    if (dict_city_data[index]['hasLHN']) == True:
                        dict_Qlhn.update({str(dict_city_data[index]['Buildings in subcity'][i]): {"Qsum": Qth_sum, "Qchp_nom": Qchp_nom, "Qchp_min": Qchp_min,
                                             "Qboiler_nom": Qboiler_nom, "Qboiler_min": Qboiler_min,
                                             "Qeh_nom": Qeh_nom}})


                    Node['fuel demand'] = power_boiler_in_total
                    Node['heat_demand_for_boiler'] = thermal_demand_building

            if (Node['entity'].bes.hasBoiler) == False and (Node['entity'].bes.hasChp) == False and (Node['entity'].bes.hasHeatpump) == False:
                # Building has no own heat supply.
                if (dict_city_data[index]['hasLHN']) == True:
                    sph_demand_building = Node[
                        'entity'].get_space_heating_power_curve()

                    dhw_demand_building = Node['entity'].get_dhw_power_curve()
                    thermal_demand_building = sph_demand_building + \
                                              dhw_demand_building
                    dict_Qlhn.update({str(dict_city_data[index]['Buildings in subcity'][i]): {"Qsum": -thermal_demand_building, "Qchp_nom": np.zeros(len(thermal_demand_building)), "Qchp_min": np.zeros(len(thermal_demand_building)),
                                         "Qboiler_nom": np.zeros(len(thermal_demand_building)), "Qboiler_min": np.zeros(len(thermal_demand_building)),
                                         "Qeh_nom": np.zeros(len(thermal_demand_building))}})
                    Node['fuel demand'] = np.zeros(len(thermal_demand_building))
                    Node['heat_demand_for_boiler'] = np.zeros(len(thermal_demand_building))
                elif (dict_city_data[index]['hasLHN']) == False:
                    print('Building has no own heat supply and is not connected to LHN')
                    raise invalidind # raise the invalid Individual Error
        ######################################################################################################################################
        ###########################################                     ######################################################################
        ###########################################      LHN SUPPLY     ######################################################################
        ###########################################                     ######################################################################
        ######################################################################################################################################
        if dict_city_data[index]['hasLHN'] == True:
            import pycity_calc.simulation.energy_balance_optimization.Energy_balance_lhn as EB
            self.city_object, dict_supply = EB.city_energy_balance(self.city_object, dict_Qlhn, subcity_building_nodes=dict_city_data[index]['Buildings in subcity'])
        else:
            dict_supply = {}

        ######################################################################################################################################
        ###########################################                     ######################################################################
        ########################################### electrical balances ######################################################################
        ###########################################                     ######################################################################
        ######################################################################################################################################


        ####print('########################################### electrical balances ##############################################')

        if (dict_city_data[index]['hasDEG']) == False:

            #for i in range(len(dict_city_data[index]['Buildings in subcity'])):
            for i in range(len(dict_city_data[index]['Buildings in subcity'])):#TODO:'Buildings in subcity'
                Node = self.city_object.node[dict_city_data[index]['Buildings in subcity'][i]]#TODO:'Buildings in subcity'

                if (Node['entity'].hasBes) == False:
                    # if no deg and no bes each building has to buy the full electrical demand
                    Node['electrical demand'] = (Node['entity'].get_electric_power_curve())
                    Node['electrical demand_with_deg'] = (Node['entity'].get_electric_power_curve())
                    Node['pv_used_self'] = np.zeros(len(time_vector.time_vector()))
                    Node['pv_sold'] = np.zeros(len(time_vector.time_vector()))
                    Node['chp_used_self'] = np.zeros(len(time_vector.time_vector()))
                    Node['chp_sold'] = np.zeros(len(time_vector.time_vector()))
                    Node['batt_unload'] = np.zeros(len(time_vector.time_vector()))
                    Node['batt_load'] = np.zeros(len(time_vector.time_vector()))
                    Node['electrical demand normal usage'] = np.zeros(len(time_vector.time_vector()))
                    Node['electrical demand hp'] = np.zeros(len(time_vector.time_vector()))

                    #Node['pv_used_with_batt'] = 0
                    #Node['pv_not_used'] = 0
                    #Node['chp_used_with_batt'] = 0
                    #Node['chp_not_used'] = 0


                else:
                    assert (Node['entity'].hasBes) == True
                    # if conditions checks if initial electrical demand is changed by bes
                    # these are overwritten if necessary

                    # Pointer to current energy system
                    Bes = Node['entity'].bes

                    # Calculation of heat pump electricity demand
                    if Bes.hasHeatpump:
                        demand_heatpump = Node['electricity_heatpump']
                        #Node['electrical_dem_heatpump'] = demand_heatpump
                    else:
                        demand_heatpump = np.zeros(len(time_vector.time_vector()))
                        #Node['electrical_dem_heatpump'] = demand_heatpump

                    # Initialisation
                    Node['electrical demand'] = (Node['entity'].get_electric_power_curve()) + (demand_heatpump)
                    Node['electrical demand_with_deg'] = (Node['entity'].get_electric_power_curve()) + (demand_heatpump)
                    Node['pv_used_self'] = np.zeros(len(time_vector.time_vector()))
                    Node['pv_sold'] = np.zeros(len(time_vector.time_vector()))
                    Node['chp_used_self'] = np.zeros(len(time_vector.time_vector()))
                    Node['chp_sold'] = np.zeros(len(time_vector.time_vector()))
                    Node['batt_unload'] = np.zeros(len(time_vector.time_vector()))
                    Node['batt_load'] = np.zeros(len(time_vector.time_vector()))
                    general_demand = Node['entity'].get_electric_power_curve() + demand_heatpump
                    Node['electrical demand normal usage'] = np.zeros(len(time_vector.time_vector()))
                    Node['electrical demand hp'] = np.zeros(len(time_vector.time_vector()))

                    # Building has a battery
                    if (Node['entity'].bes.hasBattery):

                        #reset Battery status
                        Bes.battery.totalSoc = np.zeros(len(time_vector.time_vector()))
                        Bes.battery.currentSoc = Bes.battery.socInit
                        Bes.battery.soc_ratio_current = Bes.battery.socInit/Bes.battery.capacity

                        # Building with battery, pv but without Chp
                        if Node['entity'].bes.hasPv == True and Node['entity'].bes.hasChp == False:

                            # pv electricity is very expensive and therefore more important to use than chp!
                            # Initialisation pv arrays
                            supply_pv = self.city_object.node[dict_city_data[index]['Buildings in subcity'][i]]['entity'].bes.pv.getPower(currentValues=False, updatePower=False)#TODO:'Buildings in subcity'
                            pv_used = np.zeros(len(time_vector.time_vector()))
                            pv_sold = np.zeros(len(time_vector.time_vector()))
                            demand_after_pv = np.zeros(len(time_vector.time_vector()))
                            load = np.zeros(len(time_vector.time_vector()))
                            unload = np.zeros(len(time_vector.time_vector()))

                            # Loop over timestep
                            for v in range(len(general_demand)):
                                # maximal discharging battery power
                                p_batt_max_out = Bes.battery.calc_battery_max_p_el_out(p_el_in=0)
                                # maximal charging battery power
                                p_batt_max_in = Bes.battery.calc_battery_max_p_el_in(p_el_out=0)

                                # pv can supply all electricity demand
                                if general_demand[v] <= supply_pv[v]:
                                    # calculate pv el. surplus
                                    load_power = supply_pv[v] - general_demand[v]
                                    # pv el. surplus can charge the battery without reaching maximal battery capacity
                                    if load_power < p_batt_max_in:
                                        # Calculates new state of charge for the battery
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=load_power, p_el_out=0, save_res=True, time_index=v)
                                        pv_used[v] = supply_pv[v]
                                        pv_sold[v] = 0
                                        demand_after_pv[v] = 0
                                        load[v] = load_power
                                        unload[v] = 0
                                    # reach maximal battery capacity: no charge is possible
                                    elif load_power >= p_batt_max_in:
                                        # Calculates new state of charge for the battery
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=0, p_el_out=0, save_res=True, time_index=v)
                                        pv_sold[v] = load_power
                                        pv_used[v] = general_demand[v]
                                        demand_after_pv[v] = 0
                                        load[v] = 0
                                        unload[v] = 0

                                # pv are not sufficient to cover demand
                                elif general_demand[v] > supply_pv[v]:

                                    lack_of_power = general_demand[v] - supply_pv[v]

                                    # Battery can cover electricity shortage
                                    if lack_of_power < p_batt_max_out:
                                        # Calculate new state of charge for the battery
                                        pv_used[v] = supply_pv[v]
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=0, p_el_out=lack_of_power, save_res=True, time_index=v)
                                        pv_sold[v] = 0
                                        demand_after_pv[v] = 0
                                        load[v] = 0
                                        unload[v] = lack_of_power

                                    # lack of power can't be cover with battery
                                    elif lack_of_power >= p_batt_max_out:
                                        # Calculate new state of charge for the battery
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=0, p_el_out=0, save_res=True, time_index=v)
                                        pv_used[v] = supply_pv[v]
                                        pv_sold[v] = 0
                                        demand_after_pv[v] = lack_of_power
                                        load[v] = 0
                                        unload[v] = 0

                            Node['electrical demand'] = demand_after_pv
                            # To make it complete and comparable to the entities of the other nodes
                            Node['electrical demand_with_deg'] = demand_after_pv  # useless here but consequent!
                            Node['pv_used_self'] = pv_used
                            Node['pv_sold'] = pv_sold
                            Node['batt_unload'] = unload
                            Node['batt_load'] = load

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

                        # Building with Chp but without pv
                        elif Node['entity'].bes.hasPv == False and Node['entity'].bes.hasChp == True:

                            supply_chp = Bes.chp.totalPOutput
                            demand_after_chp = np.zeros(len(time_vector.time_vector()))
                            chp_used = np.zeros(len(time_vector.time_vector()))
                            chp_sold = np.zeros(len(time_vector.time_vector()))
                            load = np.zeros(len(time_vector.time_vector()))
                            unload = np.zeros(len(time_vector.time_vector()))

                            # Loop over timestep
                            for z in range(len(general_demand)):
                                # maximal discharging battery power
                                p_batt_max_out = Bes.battery.calc_battery_max_p_el_out( p_el_in=0)
                                # maximal charging battery power
                                p_batt_max_in = Bes.battery.calc_battery_max_p_el_in(p_el_out=0)

                                # Chp can cover general demand
                                if general_demand[z] <= supply_chp[z]:
                                    # chp el. surplus
                                    load_power = supply_chp[z] - general_demand[z]

                                    # chp el. surplus can charge the battery without reaching maximal battery capacity
                                    if load_power < p_batt_max_in:

                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=load_power, p_el_out=0, save_res=True, time_index=z)
                                        chp_used[z] = supply_chp[z]
                                        chp_sold[z] = 0
                                        demand_after_chp[z] = 0
                                        load[z] = load_power
                                        unload[z] = 0

                                    #  reach maximal battery capacity: no charge is possible
                                    elif load_power >= p_batt_max_in:

                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=0, p_el_out=0, save_res=True, time_index=z)
                                        chp_sold[z] = load_power
                                        chp_used[z] = general_demand[z]
                                        demand_after_chp[z] = 0
                                        load[z] = 0
                                        unload[z] = 0

                                # Chp are not sufficient to cover demand
                                elif general_demand[z] > supply_chp[z]:

                                    lack_of_power = general_demand[z] - supply_chp[z]

                                    # Battery can cover electricity shortage
                                    if lack_of_power < p_batt_max_out:

                                        chp_used[z] = supply_chp[z]
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=0, p_el_out=lack_of_power, save_res=True, time_index=z)
                                        chp_sold[z] = 0
                                        demand_after_chp[z] = 0
                                        load[z] = 0
                                        unload[z] = lack_of_power

                                    # lack of power can't be cover with battery
                                    elif lack_of_power >= p_batt_max_out:

                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=0, p_el_out=0, save_res=True, time_index=z)
                                        chp_used[z] = supply_chp[z]
                                        chp_sold[z] = 0
                                        demand_after_chp[z] = lack_of_power
                                        load[z] = 0
                                        unload[z] = 0

                            # print ("")
                            # fig = plt.figure()
                            # plt.title('')
                            # ax = fig.add_subplot(2,1,1)
                            # plt.ylabel('Leistung [W]')
                            # plt.xlabel('Laufzeit [h/a]')
                            # ax.plot(general_demand,'b',linewidth=0.6,label='general_demand')
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

                            Node['electrical demand'] = demand_after_chp
                            # To make it complete and comparable to the entities of the other nodes
                            Node['electrical demand_with_deg'] = demand_after_chp  # useless here but consequent!
                            Node['chp_used_self'] = chp_used
                            Node['chp_sold'] = chp_sold
                            Node['batt_unload'] = unload
                            Node['batt_load'] = load


                        # Building with battery, pv and Chp
                        elif Node['entity'].bes.hasPv == True and Node['entity'].bes.hasChp == True:

                            # THIS CASE WAS IMPLEMENTED BECAUSE OF A MAJOR PROBLEM WITH BATTERY SOC:
                            # If the soc for the complete simulation time is calculated for pv at first and
                            # afterwards for chp it causes problems if battery has reached 100% soc. Technically this
                            # means, that one can predict the battery soc after pv for the whole year to always
                            # have enough free battery space to store pv. If the battery is will be full at any time by PV
                            # power that means it cannot store any CHP power because then it would reach the point of full
                            # load earlier than calculated in the PV balance. From that point on the PV balance calculated
                            # before will be meaningless
                            # SHORT: Battery SOC depends and PV and CHP! Thus you cannot calc SOC for PV first and then add
                            # SOC for CHP.
                            # THEREFORE it was necessary to implement a case for PV AND CHP!

                            # Initialisation pv arrays
                            supply_pv = self.city_object.node[dict_city_data[index]['Buildings in subcity'][i]][
                                'entity'].bes.pv.getPower(currentValues=False, updatePower=False)#TODO:'Buildings in subcity'
                            pv_used = np.zeros(len(time_vector.time_vector()))
                            pv_sold = np.zeros(len(time_vector.time_vector()))
                            demand_after_pv = np.zeros(len(time_vector.time_vector()))
                            load = np.zeros(len(time_vector.time_vector()))
                            unload = np.zeros(len(time_vector.time_vector()))

                            # for chp energybalance
                            supply_chp = Bes.chp.totalPOutput
                            demand_after_chp = np.zeros(len(time_vector.time_vector()))
                            chp_used = np.zeros(len(time_vector.time_vector()))
                            chp_sold = np.zeros(len(time_vector.time_vector()))

                            #save selfdischarge value
                            selfDischarge=Bes.battery.selfDischarge
                            eta_load = Bes.battery.etaCharge
                            eta_unload = Bes.battery.etaDischarge
                            totalSoc = Bes.battery.socInit

                            # Loop over timestep
                            for v in range(len(general_demand)):
                                #set selfdischarge to zero to avoid that it is apllied twice in one timerstep
                                Bes.battery.selfDischarge = 0

                                # maximal discharging battery power
                                p_batt_max_out = Bes.battery.calc_battery_max_p_el_out(p_el_in=0)
                                # maximal charging battery power
                                p_batt_max_in = Bes.battery.calc_battery_max_p_el_in(p_el_out=0)

                                #  pv can supply all electricity demand
                                if general_demand[v] <= supply_pv[v]:
                                    # calculate pv el. surplus
                                    load_power = supply_pv[v] - general_demand[v]

                                    # pv el. surplus can charge the battery without reaching maximal battery capacity
                                    if load_power < p_batt_max_in:
                                        # Calculate new state of charge for the battery
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=load_power, p_el_out=0, save_res=True, time_index=v)
                                        pv_used[v] = supply_pv[v]
                                        pv_sold[v] = 0
                                        demand_after_pv[v] = 0
                                        load[v] = load_power
                                        unload[v] = 0

                                    # Reach maximal battery capacity: no charge is possible
                                    elif load_power >= p_batt_max_in:

                                        # Calculate new state of charge for the battery
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=0, p_el_out=0, save_res=True, time_index=v)
                                        pv_sold[v] = load_power
                                        pv_used[v] = general_demand[v]
                                        demand_after_pv[v] = 0
                                        load[v] = 0
                                        unload[v] = 0

                                # pv can not supply all electricity demand
                                elif general_demand[v] > supply_pv[v]:

                                    # el. shortage
                                    lack_of_power = general_demand[v] - supply_pv[v]

                                    # this case doesn't have a subcase (lack_of_power < or > p_bat_max). It might be
                                    # possible that chp has enough power to supply lack of power. Only if chp and pv
                                    # can not supply the demand the battery is unloaded!!
                                    pv_used[v] = supply_pv[v]
                                    Bes.battery.calc_battery_soc_next_timestep(
                                        p_el_in=0, p_el_out=0, save_res=True, time_index=v)
                                    pv_sold[v] = 0
                                    demand_after_pv[v] = lack_of_power
                                    load[v] = 0
                                    unload[v] = 0

                                # Set selfdischarge back to the normal value
                                Bes.battery.selfDischarge=selfDischarge
                                # maximal discharging battery power
                                p_batt_max_out = Bes.battery.calc_battery_max_p_el_out(
                                    p_el_in=0)
                                # maximal charging battery power
                                p_batt_max_in = Bes.battery.calc_battery_max_p_el_in(
                                    p_el_out=0)

                                # chp can cover lack of power
                                if demand_after_pv[v] <= supply_chp[v]:

                                    load_power = supply_chp[v] - demand_after_pv[v]

                                    # pv el. surplus can charge the battery without reaching maximal battery capacity
                                    if load_power < p_batt_max_in:

                                        # Calculate new state of charge for the battery
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=load_power, p_el_out=0, save_res=True, time_index=v)
                                        chp_used[v] = supply_chp[v]
                                        chp_sold[v] = 0
                                        demand_after_chp[v] = 0
                                        load[v] += load_power
                                        unload[v] += 0

                                    # Reach maximal battery capacity: no charge is possible
                                    elif load_power >= p_batt_max_in:
                                        # Calculate new state of charge for the battery
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=0, p_el_out=0, save_res=True, time_index=v)
                                        chp_sold[v] = load_power
                                        chp_used[v] = demand_after_pv[v]
                                        demand_after_chp[v] = 0
                                        load[v] += 0
                                        unload[v] += 0

                                # Chp not sufficient to cover the rest of electricity demand
                                elif demand_after_pv[v] > supply_chp[v]:

                                    lack_of_power = demand_after_pv[v] - supply_chp[v]

                                    # Battery can cover the rest of electricity
                                    if lack_of_power < p_batt_max_out:
                                        # Calculate new state of charge for the battery
                                        chp_used[v] = supply_chp[v]
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=0, p_el_out=lack_of_power, save_res=True, time_index=v)
                                        chp_sold[v] = 0
                                        demand_after_chp[v] = 0
                                        load[v] += 0
                                        unload[v] += lack_of_power

                                    # Battery can not cover the rest of el. demand
                                    elif lack_of_power >= p_batt_max_out:
                                        # Calculate new state of charge for the battery
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=0, p_el_out=0, save_res=True, time_index=v)
                                        chp_used[v] = supply_chp[v]
                                        chp_sold[v] = 0
                                        demand_after_chp[v] = lack_of_power
                                        load[v] += 0
                                        unload[v] += 0

                                # Since Battery is loaded twice in one timestep it is mandatory to recalculate the total
                                # SOC. The Soc is calculated in a way that pvload/unload and chpload/unload happen at the same time
                                # and not in a sequence as above.

                                totalSoc = totalSoc * (1 - selfDischarge)
                                totalSoc += (load[v] * eta_load - unload[v] / eta_unload) * self.city_object.environment.timer.timeDiscretization
                                Bes.battery.totalSoc[v]=totalSoc


                            Node['electrical demand'] = demand_after_chp
                            # To make it complete and comparable to the entities of the other nodes
                            Node['electrical demand_with_deg'] =demand_after_chp  # useless here but consequent!
                            Node['pv_used_self'] = pv_used
                            Node['pv_sold'] = pv_sold
                            Node['chp_used_self'] = chp_used
                            Node['chp_sold'] = chp_sold
                            Node['batt_unload'] = unload
                            Node['batt_load'] = load
                            # overwrite Charge and Discharge arrays of battery because they are invalid
                            # because they were overwritten in the chp part of the energybalance
                            Node['entity'].bes.battery.totalPCharge = load
                            Node['entity'].bes.battery.totalPDischarge = unload


                        elif (Node['entity'].bes.hasPv) == False and (Node['entity'].bes.hasChp) == False:
                            # In case there is a battery without local producer of electrical energy!
                            assert (Node['entity'].bes.hasBattery) == False, \
                                "Battery System without PV or CHP is useless! Remember that battery " \
                                "only serves local and not interacting with the DEG"

                    # Building has no Battery
                    else:
                        assert (Node['entity'].bes.hasBattery) == False

                        # Building with pv
                        if (Node['entity'].bes.hasPv):

                            # pv electricity is very expensive and therefore more important to use than chp!
                            supply_pv = self.city_object.node[dict_city_data[index]['Buildings in subcity'][
                                    i]]['entity'].bes.pv.getPower(currentValues=False, updatePower=False)#TODO:'Buildings in subcity'

                            # Initialisation
                            pv_sold = np.zeros(len(time_vector.time_vector()))
                            final_electrical_demand = np.zeros(len(time_vector.time_vector()))

                            # Calculate intermediate variable
                            diff1_demand = general_demand - supply_pv

                            # Loop over timestep
                            for iii in range(len(pv_sold)):
                                # pv el. can supply all el. demand
                                if diff1_demand[iii] < 0:

                                    pv_sold[iii] = diff1_demand[iii]

                                # pv can not supply all el. demand
                                else: # diff1_demand[iii] >= 0
                                    final_electrical_demand[iii] = diff1_demand[iii]

                            Node['pv_used_self'] = supply_pv + pv_sold
                            Node['pv_sold'] = -1 * (pv_sold)

                            Node['electrical demand_with_deg'] = final_electrical_demand
                            # useless because there is no DEG here but consequent!
                            Node['electrical demand'] = final_electrical_demand

                        # Building with Chp
                        if (Node['entity'].bes.hasChp):

                            # Initialisation
                            chp_sold = np.zeros(len(time_vector.time_vector()))
                            supply_chp = Bes.chp.totalPOutput
                            final_electrical_demand= np.zeros(len(time_vector.time_vector()))

                            # Calculate intermediate variable
                            diff2_demand = general_demand - supply_chp

                            # Loop over timestep
                            for y in range(len(diff2_demand)):

                                if diff2_demand[y] < 0:
                                    chp_sold[y] = diff2_demand[y]

                                # Chp can not supply all el. demand
                                else: # diff2_demand[y] >= 0

                                    final_electrical_demand[y] = diff2_demand[y]

                            Node['chp_used_self'] = supply_chp + chp_sold
                            Node['chp_sold'] = -1 * (chp_sold)

                            # To make it complete and comparable to the entities of the other nodes
                            Node['electrical demand_with_deg'] = final_electrical_demand  # useless because there is no DEG here but consequent!
                            Node['electrical demand'] = final_electrical_demand

            # ## Difference beetween electrical demand for daily use or for HP/EH
            # Assume that pv/chp cover preferentially normal daily electrical needs
            # Initialisation
            Node['electrical demand normal usage'] = np.zeros(len(time_vector.time_vector()))
            Node['electrical demand hp'] = np.zeros(len(time_vector.time_vector()))
            # electrical demand for daily use
            el_dem_normal = np.zeros(len(time_vector.time_vector()))
            # electrical demand for heatpump
            el_dem_hp = np.zeros(len(time_vector.time_vector()))

            # Loop over timestep
            for tps in range(len(demand_heatpump)):
                # Total electrical demand after electrical balance:
                el_dem = Node['electrical demand']

                # total electrical demand higher than heat_pump demand:
                if el_dem[tps] > demand_heatpump[tps]:
                    # electrical demand with normal tariff
                    el_dem_normal[tps] = el_dem[tps]-demand_heatpump[tps]
                    # electrical demand with heat_pump tariff
                    el_dem_hp[tps] = demand_heatpump[tps]
                    # total electrical demand lower than heat_pump demand:
                else:
                    # electrical demand with normal tariff
                    el_dem_normal[tps] = 0
                    # electrical demand with heat_pump tariff
                    el_dem_hp[tps] = demand_heatpump [tps]
            # electrical demand for daily use
            Node ['electrical demand normal usage'] = el_dem_normal
            # electrical demand for heatpump
            Node ['electrical demand hp'] = el_dem_hp


                            ######################################################
        """
        elif (dict_city_data[index]['hasDEG']) == True:  ###########
            warnings.warn('the DEG energybalance has not been checked yet!!')
            ######################################################
            cumulated_surplus = np.zeros(len(time_vector.time_vector()))

            # Loop over Buildings
            for i in range(len(dict_city_data[index]['Buildings in subcity'])):
                #  Pointer to current building
                Node = self.city_object.node[dict_city_data[index]['Buildings in subcity'][i]]
                demand_heatpump = Node['electricity_heatpump']

                # if (Node['entity'].hasBes)==False:
                # if no deg and no bes each building has to buy the full electrical demand
                Node['electrical demand'] = (Node['entity'].get_electric_power_curve())
                Node['electrical demand_with_deg'] = (Node['entity'].get_electric_power_curve())
                Node['pv_used_self'] = 0
                Node['chp_sold'] = 0
                Node['chp_sold'] = 0
                Node['batt_unload'] = 0
                Node['batt_load'] = 0
                #Node['pv_used_with_batt'] = 0
                #Node['pv_not_used'] = 0
                Node['chp_used_self'] = 0
                #Node['chp_used_with_batt'] = 0
                #Node['chp_not_used'] = 0
                Node['cumulated_surplus'] = cumulated_surplus  # Overload from single building for DEG
                Node['electrical demand_without_deg'] = (
                    Node['entity'].get_electric_power_curve())


            for i in range(len(dict_city_data[index]['Buildings with bes'])):

                Node = self.city_object.node[
                    dict_city_data[index]['Buildings with bes'][i]]
                demand_heatpump = Node['electricity_heatpump']

                if (Node['entity'].hasBes) == True:

                    # print(dict_city_data[index]["Buildings with bes"][i])
                    Bes = self.city_object.node[
                        dict_city_data[index]["Buildings with bes"][i]][
                        'entity'].bes
                    # if conditions checks if initial electrical demand is changed by bes
                    general_demand = Node['entity'].get_electric_power_curve()
                    # these are overwritten if necessary
                    Node['electrical demand'] = (Node['entity'].get_electric_power_curve()) + (demand_heatpump)
                    Node['electrical demand_with_deg'] = (Node['entity'].get_electric_power_curve()) + (demand_heatpump)
                    Node['electrical demand_without_deg'] = (Node['entity'].get_electric_power_curve()) + (demand_heatpump)
                    Node['pv_used_self'] = 0
                    Node['chp_sold'] = 0
                    Node['chp_sold'] = 0
                    Node['batt_unload'] = 0
                    Node['batt_load'] = 0
                    #Node['pv_used_with_batt'] = 0
                    #Node['pv_not_used'] = 0
                    Node['chp_used_self'] = 0
                    #Node['chp_used_with_batt'] = 0
                    #Node['chp_not_used'] = 0

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
                            pv_used = np.zeros(len(time_vector.time_vector()))
                            pv_sold = np.zeros(len(time_vector.time_vector()))
                            demand_after_pv = np.zeros(len(time_vector.time_vector()))
                            load = np.zeros(len(time_vector.time_vector()))
                            unload = np.zeros(len(time_vector.time_vector()))
                            for v in range(len(general_demand)):

                                p_batt_max_out = Bes.battery.calc_battery_max_p_el_out(
                                    p_el_in=0)
                                p_batt_max_in = Bes.battery.calc_battery_max_p_el_in(
                                    p_el_out=0)

                                if general_demand[v] <= supply_pv[v]:
                                    load_power = supply_pv[v] - general_demand[
                                        v]

                                    if load_power <= p_batt_max_in:
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=load_power, p_el_out=0, save_res=True, time_index=v)
                                        pv_used[v] = general_demand[v]
                                        pv_sold[v] = 0
                                        demand_after_pv[v] = 0
                                        load[v] = load_power
                                        unload[v] = 0

                                    elif load_power > p_batt_max_in:
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=0, p_el_out=0, save_res=True, time_index=v)
                                        pv_sold[v] = load_power
                                        pv_used[v] = general_demand[v]
                                        demand_after_pv[v] = 0
                                        load[v] = 0
                                        unload[v] = 0

                                elif general_demand[v] > supply_pv[v]:
                                    lack_of_power = general_demand[v] - \
                                                    supply_pv[v]

                                    if lack_of_power <= p_batt_max_out:
                                        pv_used[v] = supply_pv[v]
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=0, p_el_out=lack_of_power, save_res=True, time_index=v)
                                        pv_sold[v] = 0
                                        demand_after_pv[v] = 0
                                        load[v] = 0
                                        unload[v] = lack_of_power

                                    elif lack_of_power > p_batt_max_out:
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=0, p_el_out=0, save_res=True, time_index=v)
                                        pv_used[v] = supply_pv[v]
                                        pv_sold[v] = 0
                                        demand_after_pv[v] = lack_of_power
                                        load[v] = 0
                                        unload[v] = 0

                            cumulated_surplus -= pv_sold

                            Node['electrical demand'] = (demand_after_pv)
                            Node['pv_used_self'] = pv_used
                            Node['pv_sold'] = pv_sold
                            Node['batt_unload'] = unload
                            Node['batt_load'] = load
                            Node['electrical demand_without_deg'] = demand_after_pv
                            Node['cumulated_surplus'] = cumulated_surplus
                            Node['batt_load'] = load
                            '''
                            Node['electrical demand'] = (demand_after_pv)
                            Node['pv_used_self'] = sum(pv_used)
                            Node['pv_not_used'] = sum(pv_sold)
                            Node['pv_used_with_batt'] = sum(pv_used) + sum(
                                unload)
                            Node[
                                'electrical demand_without_deg'] = demand_after_pv
                            Node['cumulated_surplus'] = cumulated_surplus
                            '''
                        if (Node['entity'].bes.hasChp):
                            if (Node['entity'].bes.hasPv) == False:
                                demand_after_pv = general_demand

                            supply_chp = power_el_chp_total
                            demand_after_chp = np.zeros(len(time_vector.time_vector()))
                            chp_used = np.zeros(len(time_vector.time_vector()))
                            chp_sold = np.zeros(len(time_vector.time_vector()))
                            load = np.zeros(len(time_vector.time_vector()))
                            unload = np.zeros(len(time_vector.time_vector()))


                            for z in range(len(demand_after_pv)):

                                p_batt_max_out = Bes.battery.calc_battery_max_p_el_out(
                                    p_el_in=0)
                                p_batt_max_in = Bes.battery.calc_battery_max_p_el_in(
                                    p_el_out=0)

                                if demand_after_pv[z] < supply_chp[z]:
                                    load_power = supply_chp[z] - \
                                                 demand_after_pv[z]

                                    if load_power <= p_batt_max_in:
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=load_power, p_el_out=0, save_res=True, time_index=z)
                                        chp_used[z] = demand_after_pv[z]
                                        chp_sold[z] = 0
                                        demand_after_chp[z] = 0
                                        load[z] = load_power
                                        unload[z] = 0

                                    elif load_power > p_batt_max_in:
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=0, p_el_out=0, save_res=True, time_index=z)
                                        chp_sold[z] = load_power
                                        chp_used[z] = demand_after_pv[z]
                                        demand_after_chp[z] = 0
                                        load[z] = 0
                                        unload[z] = 0

                                elif demand_after_pv[z] > supply_chp[z]:
                                    lack_of_power = demand_after_pv[z] - \
                                                    supply_chp[z]

                                    if lack_of_power <= p_batt_max_out:
                                        chp_used[z] = supply_chp[z]
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=0, p_el_out=lack_of_power, save_res=True, time_index=z)
                                        chp_sold[z] = 0
                                        demand_after_chp[z] = 0
                                        load[z] = 0
                                        unload[z] = lack_of_power

                                    elif lack_of_power > p_batt_max_out:
                                        Bes.battery.calc_battery_soc_next_timestep(
                                            p_el_in=0, p_el_out=0, save_res=True, time_index=z)
                                        chp_used[z] = supply_chp[z]
                                        chp_sold[z] = 0
                                        demand_after_chp[z] = lack_of_power
                                        load[z] = 0
                                        unload[z] = 0

                                elif demand_after_pv[z] == supply_chp[z]:
                                    Bes.battery.calc_battery_soc_next_timestep(
                                        p_el_in=0, p_el_out=0, save_res=True, time_index=z)
                                    chp_used[z] = supply_chp[z]
                                    chp_sold[z] = 0
                                    demand_after_chp[z] = 0
                                    load[z] = 0
                                    unload[z] = 0

                            cumulated_surplus -= chp_sold

                            Node['electrical demand'] = demand_after_chp
                            Node['chp_used_self'] = chp_used
                            Node['chp_sold'] = chp_sold
                            Node['batt_unload'] = unload
                            Node['batt_load'] = load
                            Node['electrical demand_without_deg'] = demand_after_chp
                            Node['cumulated_surplus'] = cumulated_surplus
                            '''
                            Node['electrical demand'] = demand_after_chp
                            Node['chp_used_self'] = sum(chp_used)
                            Node['chp_not_used'] = sum(chp_sold)
                            Node['chp_used_with_batt'] = sum(chp_used) + sum(
                                unload)
                            Node[
                                'electrical demand_without_deg'] = demand_after_chp
                            Node['cumulated_surplus'] = cumulated_surplus
                            '''

                    if (Node['entity'].bes.hasBattery) == False:
                        # cumulated_surplus saves the inputs of pv and chp
                        cumulated_surplus = np.zeros(
                            len(time_vector.time_vector()))
                        # Initially set to an array of zeros but overwritten if needed!
                        Node['cumulated_surplus'] = cumulated_surplus


                        if (Node['entity'].bes.hasHeatpump):
                            general_demand += demand_heatpump

                        if (Node['entity'].bes.hasPv):
                            # pv electricity is very expensive and therefore more important to use than chp!
                            pv_sold = np.zeros(len(time_vector.time_vector()))
                            supply_pv = Node['entity'].bes.pv.getPower()
                            diff1_demand = general_demand - supply_pv
                            for i in range(len(diff1_demand)):
                                if diff1_demand[i] < 0:
                                    pv_sold[i] = diff1_demand[i]
                            pv_used = sum(supply_pv) + sum(pv_sold)
                            general_demand = []
                            for y in range(len(diff1_demand)):
                                if diff1_demand[y] > 0:
                                    general_demand[y] = diff1_demand[y]
                            cumulated_surplus += pv_sold

                            Node['pv_used_self'] = supply_pv + pv_sold
                            Node['pv_sold'] = -1 * (pv_sold)
                            final_electrical_demand = general_demand
                            Node['electrical demand'] = general_demand
                            Node['electrical demand_without_deg'] = final_electrical_demand
                            Node['cumulated_surplus'] = cumulated_surplus
                            '''
                            Node['pv_used_self'] = pv_used
                            Node['pv_not_used'] = -1 * sum(pv_sold)
                            final_electrical_demand = (general_demand)
                            Node['electrical demand'] = np.array(
                                general_demand)
                            Node[
                                'electrical demand_without_deg'] = final_electrical_demand
                            Node['cumulated_surplus'] = cumulated_surplus
                            '''
                        if (Node['entity'].bes.hasChp):
                            chp_sold = np.zeros(len(time_vector.time_vector()))
                            # print ("2power_electrical_chp",sum(power_el_chp_total))
                            supply_chp = Node['power_el_chp']
                            # supply_chp=np.array(power_el_chp_total)
                            diff2_demand = general_demand - supply_chp
                            for i in range(len(diff2_demand)):
                                if diff2_demand[i] < 0:
                                    chp_sold[i] = diff2_demand[i]
                            chp_used = sum(supply_chp) + sum(chp_sold)
                            general_demand = np.zeros(len(time_vector.time_vector()))
                            for y in range(len(diff2_demand)):
                                if diff2_demand[y] > 0:
                                    general_demand[y] = diff2_demand[y]
                            cumulated_surplus += chp_sold

                            Node['chp_used_self'] = supply_chp + chp_sold
                            Node['chp_sold'] = -1 * chp_sold
                            Node['electrical demand'] = general_demand
                            final_electrical_demand = general_demand
                            Node['electrical demand_without_deg'] = final_electrical_demand
                            Node['cumulated_surplus'] = cumulated_surplus
                            '''
                            Node['chp_used_self'] = chp_used
                            Node['chp_not_used'] = -1 * sum(chp_sold)
                            Node['electrical demand'] = general_demand
                            final_electrical_demand = general_demand
                            Node[
                                'electrical demand_without_deg'] = final_electrical_demand
                            Node['cumulated_surplus'] = cumulated_surplus
                            '''


                        else:
                            # In case there is a battery without local producer of electrical energy!
                            assert (Node['entity'].bes.hasBattery) == False, "Battery System without PV or CHP is useless! Remember that battery only serves local and not interacting with the DEG"

                else:
                    pass

            # This part of the code is now looking for surpluses and lacks of energy within the grid
            # and tries to decrease the amount of self produced energy which has to be sold !
            cumulated_demand = np.zeros(len(time_vector.time_vector()))
            cumulated_surplus = np.zeros(len(time_vector.time_vector()))
            for ii in range(len(dict_city_data[index]['Buildings with bes'])):
                # The surplus which every house BES's creates is added

                cumulated_demand += \
                    self.city_object.node[
                        dict_city_data[index]['Buildings with bes'][ii]][
                        'entity'].get_electric_power_curve()
                cumulated_surplus += \
                    self.city_object.node[
                        dict_city_data[index]['Buildings with bes'][ii]][
                        'cumulated_surplus']

            not_used = np.zeros(len(time_vector.time_vector()))
            for ii in range(
                    len(dict_city_data[index]['Buildings in subcity'])):
                # the amount of power is determined by the initial demand of power
                # if the cutsomer needs a lot of power he will receive more power from the deg
                # the amount is linear weighed!
                Node = self.city_object.node[
                    dict_city_data[index]['Buildings in subcity'][ii]]
                final_electrical_demand_afer_deg = []
                # Ratio is a percent value which says how much of the energy is for a specific customer
                ratio = (sum(self.city_object.node[
                                 dict_city_data[index]['Buildings in subcity'][
                                     ii]][
                                 'entity'].get_electric_power_curve()) / sum(
                    cumulated_demand))

                weighted_individual_surplus = np.array(
                    [-1 * ratio * x for x in cumulated_surplus]) + not_used
                demand_deg = \
                    self.city_object.node[
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
            ####print("el_energy_not_used:", sum(not_used))
        """

        return self.city_object, dict_Qlhn, dict_supply

        # if import sys at the beginning of this funciton is used then file must be closed
        #filename.close()

if __name__ == '__main__':

    import pycity_calc.cities.scripts.city_generator.city_generator as citygen
    import pycity_calc.cities.scripts.overall_gen_and_dimensioning as overall
    import pycity_calc.simulation.energy_balance_optimization.Plot as Plot

    import pycity_base.classes.supply.BES as BES

    this_path = os.path.dirname(os.path.abspath(__file__))

    try:
        filename = 'city_clust_simple_with_esys.pkl'
        file_path = os.path.join(this_path, 'input', filename)
        city_object = pickle.load(open(file_path, mode='rb'))
    except:
        print('Could not load city pickle file. Going to generate a new one.')
        #  # Userinputs
        #  #----------------------------------------------------------------------

        #  Generate environment
        #  ######################################################
        year = 2010
        timestep = 3600  # Timestep in seconds
        # location = (51.529086, 6.944689)  # (latitude, longitude) of Bottrop
        location = (50.775346, 6.083887)  # (latitude, longitude) of Aachen
        altitude = 266  # Altitude of location in m (Aachen)

        #  Weather path
        try_path = None
        #  If None, used default TRY (region 5, 2010)

        new_try = False
        #  new_try has to be set to True, if you want to use TRY data of 2017
        #  or newer! Else: new_try = False

        #  Space heating load generation
        #  ######################################################
        #  Thermal generation method
        #  1 - SLP (standardized load profile)
        #  2 - Load and rescale Modelica simulation profile
        #  (generated with TRY region 12, 2010)
        #  3 - VDI 6007 calculation (requires el_gen_method = 2)
        th_gen_method = 1
        #  For non-residential buildings, SLPs are generated automatically.

        #  Manipulate thermal slp to fit to space heating demand?
        slp_manipulate = False
        #  True - Do manipulation
        #  False - Use original profile
        #  Only relevant, if th_gen_method == 1
        #  Sets thermal power to zero in time spaces, where average daily outdoor
        #  temperature is equal to or larger than 12 °C. Rescales profile to
        #  original demand value.

        #  Manipulate vdi space heating load to be normalized to given annual net
        #  space heating demand in kWh
        vdi_sh_manipulate = False

        #  Electrical load generation
        #  ######################################################
        #  Choose electric load profile generation method (1 - SLP; 2 - Stochastic)
        #  Stochastic profile is only generated for residential buildings,
        #  which have a defined number of occupants (otherwise, SLP is used)
        el_gen_method = 1
        #  If user defindes method_3_nb or method_4_nb within input file
        #  (only valid for non-residential buildings), SLP will not be used.
        #  Instead, corresponding profile will be loaded (based on measurement
        #  data, see ElectricalDemand.py within pycity)

        #  Do normalization of el. load profile
        #  (only relevant for el_gen_method=2).
        #  Rescales el. load profile to expected annual el. demand value in kWh
        do_normalization = True

        #  Randomize electrical demand value (residential buildings, only)
        el_random = True

        #  Prevent usage of electrical heating and hot water devices in
        #  electrical load generation
        prev_heat_dev = True
        #  True: Prevent electrical heating device usage for profile generation
        #  False: Include electrical heating devices in electrical load generation

        #  Use cosine function to increase winter lighting usage and reduce
        #  summer lighting usage in richadson el. load profiles
        #  season_mod is factor, which is used to rescale cosine wave with
        #  lighting power reference (max. lighting power)
        season_mod = 0.3
        #  If None, do not use cosine wave to estimate seasonal influence
        #  Else: Define float
        #  (only relevant if el_gen_method == 2)

        #  Hot water profile generation
        #  ######################################################
        #  Generate DHW profiles? (True/False)
        use_dhw = False  # Only relevant for residential buildings

        #  DHW generation method? (1 - Annex 42; 2 - Stochastic profiles)
        #  Choice of Anex 42 profiles NOT recommended for multiple builings,
        #  as profile stays the same and only changes scaling.
        #  Stochastic profiles require defined nb of occupants per residential
        #  building
        dhw_method = 1  # Only relevant for residential buildings

        #  Define dhw volume per person and day (use_dhw=True)
        dhw_volumen = None  # Only relevant for residential buildings

        #  Randomize choosen dhw_volume reference value by selecting new value
        #  from gaussian distribution with 20 % standard deviation
        dhw_random = True

        #  Use dhw profiles for esys dimensioning
        dhw_dim_esys = True

        #  Plot city district with pycity_calc visualisation
        plot_pycity_calc = False

        #  Efficiency factor of thermal energy systems
        #  Used to convert input values (final energy demand) to net energy demand
        eff_factor = 1

        #  Define city district input data filename
        filename = 'city_clust_simple.txt'

        txt_path = os.path.join(this_path, 'input', filename)

        #  Define city district output file
        save_filename = None
        # save_path = os.path.join(this_path, 'output_overall', save_filename)
        save_path = None

        #  #####################################
        t_set_heat = 20  # Heating set temperature in degree Celsius
        t_set_night = 16  # Night set back temperature in degree Celsius
        t_set_cool = 70  # Cooling set temperature in degree Celsius

        #  Air exchange rate (required for th_gen_method = 3 (VDI 6007 sim.))
        air_vent_mode = 1
        #  int; Define mode for air ventilation rate generation
        #  0 : Use constant value (vent_factor in 1/h)
        #  1 : Use deterministic, temperature-dependent profile
        #  2 : Use stochastic, user-dependent profile
        #  False: Use static ventilation rate value

        vent_factor = 0.5  # Constant. ventilation rate
        #  (only used, if air_vent_mode = 0)
        #  #####################################

        #  Use TEASER to generate typebuildings?
        call_teaser = False
        teaser_proj_name = filename[:-4]

        merge_windows = False
        # merge_windows : bool, optional
        # Defines TEASER project setting for merge_windows_calc
        # (default: False). If set to False, merge_windows_calc is set to False.
        # If True, Windows are merged into wall resistances.

        #  Log file for city_generator
        do_log = False  # True, generate log file
        log_path = os.path.join(this_path, 'input',
                                'city_gen_overall_log.txt')

        #  Generate street networks
        gen_str = True  # True - Generate street network

        #  Street node and edges input filenames
        str_node_filename = 'street_nodes_cluster_simple.csv'
        str_edge_filename = 'street_edges_cluster_simple.csv'

        #  Load street data from csv
        str_node_path = os.path.join(this_path, 'input',
                                     str_node_filename)
        str_edge_path = os.path.join(this_path, 'input',
                                     str_edge_filename)

        #  Add energy networks to city
        gen_e_net = True  # True - Generate energy networks

        #  Path to energy network input file (csv/txt; tab separated)
        network_filename = 'city_clust_simple_networks.txt'
        network_path = os.path.join(this_path, 'input',
                                    network_filename)

        #  Add energy systems to city
        gen_esys = True  # True - Generate energy networks

        #  Path to energy system input file (csv/txt; tab separated)
        esys_filename = 'city_clust_simple_enersys.txt'
        esys_path = os.path.join(this_path, 'input',
                                 esys_filename)

        #  #----------------------------------------------------------------------

        #  Load district_data file
        district_data = citygen.get_district_data_from_txt(txt_path)

        city_object = overall.run_overall_gen_and_dim(timestep=timestep,
                                                      year=year,
                                                      location=location,
                                                      try_path=try_path,
                                                      th_gen_method=th_gen_method,
                                                      el_gen_method=el_gen_method,
                                                      use_dhw=use_dhw,
                                                      dhw_method=dhw_method,
                                                      district_data=district_data,
                                                      gen_str=gen_str,
                                                      str_node_path=str_node_path,
                                                      str_edge_path=str_edge_path,
                                                      generation_mode=0,
                                                      eff_factor=eff_factor,
                                                      save_path=save_path,
                                                      altitude=altitude,
                                                      do_normalization=do_normalization,
                                                      dhw_volumen=dhw_volumen,
                                                      gen_e_net=gen_e_net,
                                                      network_path=network_path,
                                                      gen_esys=gen_esys,
                                                      esys_path=esys_path,
                                                      dhw_dim_esys=dhw_dim_esys,
                                                      plot_pycity_calc=plot_pycity_calc,
                                                      slp_manipulate=slp_manipulate,
                                                      call_teaser=call_teaser,
                                                      teaser_proj_name=teaser_proj_name,
                                                      do_log=do_log,
                                                      log_path=log_path,
                                                      air_vent_mode=air_vent_mode,
                                                      vent_factor=vent_factor,
                                                      t_set_heat=t_set_heat,
                                                      t_set_cool=t_set_cool,
                                                      t_night=t_set_night,
                                                      vdi_sh_manipulate=vdi_sh_manipulate,
                                                      el_random=el_random,
                                                      dhw_random=dhw_random,
                                                      prev_heat_dev=prev_heat_dev,
                                                      season_mod=season_mod,
                                                      merge_windows=merge_windows,
                                                      new_try=new_try)

        for n in city_object.nodes():
            #  Workaround: To prevent AssertionError with non-existent BES,
            #  BES are added to all buildings
            if 'entity' in city_object.node[n]:
                build = city_object.node[n]['entity']

                if build.hasBes == False:
                    bes = BES.BES(environment=city_object.environment)
                    build.addEntity(bes)

        #  Save new pickle file
        filename = 'city_clust_simple_with_esys.pkl'
        file_path = os.path.join(this_path, 'input', filename)
        pickle.dump(city_object, open(file_path, mode='wb'))

    citvis.plot_city_district(city=city_object, plot_lhn=True, plot_deg=True,
                              plot_esys=True)

    Calculator = calculator(city_object)
    dict_bes_data = Calculator.assembler()
    print('Dict city data', dict_bes_data)
    for i in range(len(dict_bes_data)):
        city_object, dict_Qlhn, dict_supply = Calculator.eb_balances(
            dict_bes_data, i)

    # Plot.plot_all_results(city_object, dict_supply, t_start=0, t_stop=8759)
