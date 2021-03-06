#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script holds class to calculate energy balance of whole city district
"""
from __future__ import division

import os
import copy
import pickle
import warnings
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

try:
    from matplotlib2tikz import save as tikz_save
except:
    msg = 'Could not import matplotlib2tikz'
    warnings.warn(msg)

import pycity_calc.simulation.energy_balance.check_eb_requ as check_eb
import pycity_calc.toolbox.networks.network_ops as netop
import pycity_calc.simulation.energy_balance.building_eb_calc as beb
import pycity_calc.toolbox.dimensioning.dim_networks as dimnet


def get_list_lhn_build_without_th_esys(city, list_buildings=None):
    """
    Return list of ids of building nodes, which do not have any internal
    thermal supply, except LHN connection.

    Parameters
    ----------
    city : object
        City object of pyCity_calc
    list_buildings list (of ints), optional
        List of buildings (default: None). If None, searches for
        all buildings

    Returns
    -------
    list_no_th_esys : list (of li ints)
        List of buildings without own thermal energy supply unit
    """

    if list_buildings is None:
        list_buildings = city.get_list_build_entity_node_ids()

    list_no_th_esys = []

    for n in list_buildings:

        build = city.nodes[n]['entity']

        has_th_supply = False

        if build.hasBes:

            if build.bes.hasBoiler:
                assert build.bes.boiler._kind == 'boiler'
                has_th_supply = True

            if build.bes.hasChp:
                assert build.bes.chp._kind == 'chp'
                has_th_supply = True

            if build.bes.hasElectricalHeater:
                assert build.bes.electricalHeater._kind == 'electricalheater'
                has_th_supply = True

            if build.bes.hasHeatpump:
                assert build.bes.heatpump._kind == 'heatpump'
                has_th_supply = True

        if has_th_supply is False:
            print('Found building without own thermal energy supply:')
            print('ID: ', n)
            list_no_th_esys.append(n)

    return list_no_th_esys


class CityEBCalculator(object):
    """
    City Energy Balance Calculator class. Used to perform energy balance
    calculations for whole city district.
    """

    def __init__(self, city, copy_city=False, check_city=True, loss_buff=1.1,
                 press_loss=100, eta_pump=0.6):
        """
        Constructor of city energy balance
        Parameters
        ----------
        city : object
            City object of pyCity_calc
        copy_city : bool, optional
            Defines, if original city should be used for energy balance run
            or if city should be copied (default: False). If True, copies
            city. Chosen city object is going to be modified by energy
            balance
        check_city : bool, optional
            Check, if city object fulfills requirements for energy balance
            calculation (default: True)
        loss_buff : float, optional
            Defines factor, which is used to rescale loss power of thermal
            network (default: 1.1). This factor should account for additional
            losses during off-time (cooling down etc.), which are not taken
            into account by regular energy balance, when building demand
            is zero.
        press_loss : float, optional
            Pressure loss factor of pipe in Pa/m (default: 100). Based on:
            [1] Fraunhofer UMSICHT - Leitfaden Nahwärme (page 46)
            https://www.umsicht.fraunhofer.de/content/dam/umsicht/de/dokumente/energie/leitfaden-nahwaerme.pdf
        eta_pump : float, optional
            Pumping efficiency (default: 0.6)
        """

        if loss_buff < 1:
            msg = 'loss_buff factor should always be larger or equal to 1!'
            raise AssertionError(msg)
        if eta_pump > 1:
            msg = 'Pumping efficiency factor cannot be larger than 1!'
            raise AssertionError(msg)
        if press_loss < 0:
            msg = 'Pressure loss cannot be negative!'
            raise AssertionError(msg)

        if check_city:
            check_eb.check_eb_requirements(city=city)

        if copy_city:
            self.city = copy.deepcopy(city)
        else:
            self.city = city

        self.loss_buff = loss_buff
        self.press_loss = press_loss
        self.eta_pump = eta_pump
        self.list_pump_energy = None  # List with pump energy per LHN
        self.dict_fe_city_balance = None  # Final energy results dict
        self.co2 = None  # CO2 emissions of city district in kg/a

        self.list_th_done = None
        self.list_el_done = None

        self._list_lists_lhn_ids = None
        self._list_lists_lhn_ids_build = None
        self._list_lists_deg_ids = None
        self._list_lists_deg_ids_build = None
        self._list_single_build = None
        self._list_no_th_esys = None

        self._dict_energy = None  # Dictionary with amounts of generated and
        #  consumed energy (call get_gen_and_con_energy after energy_balance
        #  has been un to calculate this dict (save_res=True))

        #  Get list of sub-cities
        self.set_subcity_lists()

    def reinit(self, check_city=True):
        """
        Reinitialize CityEBCCalculator object (set result lists to None and
        extract new infos about energy systems and networks), e.g.
        when being used with modified city object in GA.

        Parameters
        ----------
        check_city : bool, optional
            Check, if city object fulfills requirements for energy balance
            calculation (default: True)
        """
        self.list_pump_energy = None  # List with pump energy per LHN
        self.dict_fe_city_balance = None  # Final energy results dict
        self.co2 = None  # CO2 emissions of city district in kg/a

        self.list_th_done = None
        self.list_el_done = None

        self._list_lists_lhn_ids = None
        self._list_lists_lhn_ids_build = None
        self._list_lists_deg_ids = None
        self._list_lists_deg_ids_build = None
        self._list_single_build = None
        self._list_no_th_esys = None

        if check_city:
            check_eb.check_eb_requirements(city=self.city)

        #  Get list of sub-cities
        self.set_subcity_lists()

    def set_subcity_lists(self):
        """
        Calculate values subcity lists:
        _list_lists_lhn_ids
        _list_lists_lhn_ids_build
        _list_lists_deg_ids
        _list_lists_deg_ids_build
        _list_single_build
        _list_lists_lhn_no_th_supply
        """

        #  List of lists of local heating network connected nodes
        self._list_lists_lhn_ids = \
            netop.get_list_with_energy_net_con_node_ids(city=self.city,
                                                        network_type='heating')

        #  List of lists of building interconnected nodes (heating)
        self._list_lists_lhn_ids_build = \
            netop.get_list_with_energy_net_con_node_ids(city=self.city,
                                                        network_type='heating',
                                                        build_node_only=True)

        #  List of lists of electricity network connected nodes
        self._list_lists_deg_ids = \
            netop.get_list_with_energy_net_con_node_ids(city=self.city,
                                                        network_type='electricity')

        #  List of lists of building interconnected nodes (electricity)
        self._list_lists_deg_ids_build = \
            netop.get_list_with_energy_net_con_node_ids(city=self.city,
                                                        network_type='electricity',
                                                        build_node_only=True)

        #  Get list of single building ids (not connected to energy networks)
        self._list_single_build = \
            netop.get_list_build_without_energy_network(city=self.city)

        #  Get list of all buildings, which do not have own internal
        #  thermal energy supply
        self._list_no_th_esys = \
            get_list_lhn_build_without_th_esys(city=self.city)

    def calc_lhn_energy_balance(self, run_mc=False, dict_samples_const=None,
                                run_idx=None, sampling_method=None,
                                dict_city_sample_lhc=None):
        """
        Calculate thermal energy balance for LHN connected buildings

        Parameters
        ----------
        run_mc : bool, optional
            Defines, if Monte-Carlo analysis should be run (default: False).
            If True, puts uncertainty factors of dict_samples on investment
            cost, lifetime and maintenance factors. If False, only performs
            single annuity calculation run with default values.
        dict_samples_const : dict (of dicts)
            Dictionary holding dictionaries with constant
            sample data for MC run (default: None)
            dict_samples_const['city'] = dict_city_samples
            dict_samples_const['<building_id>'] = dict_build_dem
            (of building with id <building_id>)
        run_idx : int, optional
            Index / number of run for Monte-Carlo analysis (default: None)
        sampling_method : str, optional
            Defines method used for sampling (default: None). Only
            relevant if mc_run is True.
            Options:
            - 'lhc': latin hypercube sampling
            - 'random': randomized sampling
        dict_city_sample_lhc : dict, optional
            Dict holding city parameter names as keys and numpy arrays with
            samples as dict values (default: None). Only
            relevant if mc_run is True and sampling_method == 'lhc'

        Returns
        -------
        list_pump_energy : list (of floats)
            List with pump energy in kWh/a for each LHN
        """

        if run_mc and sampling_method is 'random':
            if dict_samples_const is None:
                msg = 'Sample dictionary dict_samples cannnot be None, if' \
                      ' you want to perform Monte-Carlo analysis.'
                raise AssertionError(msg)
            if run_idx is None:
                msg = 'Index value run_idx cannnot be None, if' \
                      ' you want to perform Monte-Carlo analysis.'
                raise AssertionError(msg)

        if run_mc and sampling_method is 'lhc':
            if dict_city_sample_lhc is None is None:
                msg = 'Sample dicts. cannnot be None, if' \
                      ' you want to perform Monte-Carlo analysis.'
                raise AssertionError(msg)
            if run_idx is None:
                msg = 'Index value run_idx cannnot be None, if' \
                      ' you want to perform Monte-Carlo analysis.'
                raise AssertionError(msg)

        if run_mc and sampling_method is None:
            msg = 'sampling_method cannot be None, if run_mc is True!'
            raise AssertionError(msg)

        if self.loss_buff < 1:
            msg = 'loss_buff factor should always be larger or equal to 1!'
            raise AssertionError(msg)
        if self.eta_pump > 1:
            msg = 'Pumping efficiency factor cannot be larger than 1!'
            raise AssertionError(msg)
        if self.press_loss < 0:
            msg = 'Pressure loss cannot be negative!'
            raise AssertionError(msg)

        if run_mc and sampling_method == 'random':
            #  Get sampling uncertainty value for u-value (Monte-Carlo run)
            u_val_unc = dict_samples_const['city']['lhn_loss'][run_idx]
        elif run_mc and sampling_method == 'lhc':
            #  Get sampling uncertainty value for u-value (Monte-Carlo run)
            u_val_unc = dict_city_sample_lhc['lhn_loss'][run_idx]
        else:
            u_val_unc = 1

        # Add weights to edges
        netop.add_weights_to_edges(graph=self.city)

        list_pump_energy = []

        #  Loop over subcities
        for list_lhn_build_ids in self._list_lists_lhn_ids_build:

            print()
            print('########################################################')
            print('Process LHN network with buildings: ')
            print(list_lhn_build_ids)
            print()

            #  Start with buildings without own thermal energy supply units
            #  Identify all buildings in list_lhn_build_ids, which do
            #  not have own thermal energy supply
            list_no_th_esys = []
            list_th_esys = []
            for n in list_lhn_build_ids:
                if n in self._list_no_th_esys:
                    list_no_th_esys.append(n)
                else:
                    list_th_esys.append(n)

            print('Buildings within LHN network without thermal energy '
                  'supply:')
            print(list_no_th_esys)

            print('Buildings within LHN network with feeder supply:')
            print(list_th_esys)
            print()

            timestep = self.city.environment.timer.timeDiscretization

            #  Sum up thermal energy demand of all buildings without own th.
            #  supply system
            th_lhn_power = np.zeros(int(365 * 24 * 3600 / timestep))

            for n in list_no_th_esys:
                build = self.city.nodes[n]['entity']

                th_lhn_power += build.get_space_heating_power_curve()
                th_lhn_power += build.get_dhw_power_curve()

                self.list_th_done.append(n)

            # Get maximum thermal power of buildings (without esys
            q_dot_max_buildings = max(th_lhn_power)

            # Estimate energy network losses
            #  ###########################################################
            #  Get lhn network temperatures, env. temperature and diameter

            #  TODO: Implement better way to extract LHN pipe data instead of
            #  TODO: Choosing from first node

            #  Get first id of buildings without thermal energy systems
            if len(list_no_th_esys) > 0:
                ref_id = list_no_th_esys[0]
            else:
                ref_id = list_th_esys[0]

            # Identify neighbors of first building
            list_neighb = nx.neighbors(G=self.city, n=ref_id)

            temp_vl = None

            #  Extract data
            for n in list_neighb:

                if 'network_type' in self.city.edges[ref_id, n]:

                    if (self.city.edges[ref_id, n]['network_type'] == 'heating'
                            or self.city.edges[ref_id, n][
                                'network_type'] == 'heating_and_deg'):
                        #  Extract lhn data
                        temp_vl = self.city.edges[ref_id, n]['temp_vl']
                        temp_rl = self.city.edges[ref_id, n]['temp_rl']
                        d_i = self.city.edges[ref_id, n]['d_i']
                        rho = self.city.edges[ref_id, n]['rho']
                        c_p = self.city.edges[ref_id, n]['c_p']

                        #  Estimate u-value of pipe in W/mK
                        u_value = dimnet.estimate_u_value(d_i)
                        break

            if temp_vl is None:
                msg = 'Could not find network of type heating or network' \
                      ' does not have temp_vl as attribute!'
                raise AssertionError(msg)

            # Get LHN network length
            list_lhn_weights = \
                list(self.city.edges(nbunch=list_lhn_build_ids, data='weight'))

            #  Sum up weights to get total network lenght
            lhn_len = 0
            for tup_lhn in list_lhn_weights:
                lhn_len += tup_lhn[2]

            print('Total LHN network length in m: ')
            print(round(lhn_len, 0))
            print()

            #  Estimate heat pipe losses per timestep, where LHN is used
            #  ###########################################################

            #  Get ground temperature as LHN losses reference temperature
            temp_env = self.city.environment.temp_ground

            q_lhn_loss_if = u_val_unc * u_value * lhn_len * \
                            (temp_vl - temp_env)
            q_lhn_loss_rf = u_val_unc * u_value * lhn_len * \
                            (temp_rl - temp_env)

            #  Sum up loss powers and use rescaling factor
            q_lhn_loss = self.loss_buff * (q_lhn_loss_if + q_lhn_loss_rf)

            q_dot_max = q_dot_max_buildings + q_lhn_loss

            print('Total heating power loss of LHN in kW:')
            print(round(q_lhn_loss / 1000, 2))
            print()

            #  Add LHN losses to total thermal power demand
            #  (when LHN is active)
            for i in range(len(th_lhn_power)):
                if th_lhn_power[i] > 0:
                    th_lhn_power[i] += q_lhn_loss

            # Add LHN electric power demand for pumps
            #  ##########################################################
            #  Estimate total pressure loss
            delta_p_total = self.press_loss * lhn_len  # in Pa

            #  Estimate mass flow rate in kg/s
            m_dot = q_dot_max / (c_p * (temp_vl - temp_rl))

            #  Estimate pump power
            p_pump = delta_p_total * m_dot / (rho * self.eta_pump)

            pump_energy = 0
            #  Estimate pump energy
            for i in range(len(th_lhn_power)):
                if th_lhn_power[i] > 0:
                    pump_energy += p_pump * timestep

            # Convert pump energy from Joule to kWh
            pump_energy /= (1000 * 3600)

            print('Estimated pump energy in kWh/a:')
            print(round(pump_energy, ndigits=2))

            #  Append pump energy list
            list_pump_energy.append(pump_energy)

            #  Hand over network energy demand to feeder node buildings
            #  and solve thermal energy balance
            #  ##########################################################

            th_lhn_power_remain = copy.deepcopy(th_lhn_power)

            #  Sort list_th_esys (CHP systems first)
            list_th_esys_copy = []
            for n in list_th_esys:
                build = self.city.nodes[n]['entity']

                if build.bes.hasChp:
                    list_th_esys_copy.insert(0, n)
                else:
                    list_th_esys_copy.append(n)

            list_th_esys = list_th_esys_copy

            for n in list_th_esys:
                build = self.city.nodes[n]['entity']

                #  Solve thermal energy balance for single building with
                #  remaining LHN power demand
                beb.calc_build_therm_eb(build=build,
                                        id=n,
                                        th_lhn_pow_rem=th_lhn_power_remain)

                self.list_th_done.append(n)

            for i in range(len(th_lhn_power_remain)):
                if abs(th_lhn_power_remain[i]) > 0.001:
                    msg = 'Could not cover LHN thermal energy demand of' \
                          ' ' + str(int(th_lhn_power_remain[i])) + ' Watt' \
                                                                   ' for timestep ' + str(
                        i) + '.'
                    raise beb.EnergyBalanceException(msg)

        # Save list pump energy on energy balance object
        self.list_pump_energy = list_pump_energy

        return list_pump_energy

    def calc_city_energy_balance(self, run_mc=False,
                                 dict_samples_const=None,
                                 run_idx=None, eeg_pv_limit=False,
                                 sampling_method=None,
                                 dict_city_sample_lhc=None
                                 ):
        """
        Calculate energy balance of whole city. Save results on city object

        Parameters
        ----------
        run_mc : bool, optional
            Defines, if Monte-Carlo analysis should be run (default: False).
            If True, puts uncertainty factors of dict_samples on investment
            cost, lifetime and maintenance factors. If False, only performs
            single annuity calculation run with default values.
        dict_samples_const : dict (of dicts)
            Dictionary holding dictionaries with constant
            sample data for MC run (default: None)
            dict_samples_const['city'] = dict_city_samples
            dict_samples_const['<building_id>'] = dict_build_dem
            (of building with id <building_id>
        run_idx : int, optional
            Index / number of run for Monte-Carlo analysis (default: None)
        eeg_pv_limit : bool, optional
            Defines, if EEG PV feed-in limitation of 70 % of peak load is
            active (default: False). If limitation is active, maximal 70 %
            of PV peak load are fed into the grid.
            However, self-consumption is used, first.
        sampling_method : str, optional
            Defines method used for sampling (default: None). Only
            relevant if mc_run is True.
            Options:
            - 'lhc': latin hypercube sampling
            - 'random': randomized sampling
        dict_city_sample_lhc : dict, optional
            Dict holding city parameter names as keys and numpy arrays with
            samples as dict values (default: None). Only
            relevant if mc_run is True and sampling_method == 'lhc'
        """

        if run_mc and sampling_method is 'random':
            if dict_samples_const is None:
                msg = 'Sample dicts. cannnot be None, if' \
                      ' you want to perform Monte-Carlo analysis.'
                raise AssertionError(msg)
            if run_idx is None:
                msg = 'Index value run_idx cannnot be None, if' \
                      ' you want to perform Monte-Carlo analysis.'
                raise AssertionError(msg)

        if run_mc and sampling_method is 'lhc':
            if dict_city_sample_lhc is None is None:
                msg = 'Sample dicts. cannnot be None, if' \
                      ' you want to perform Monte-Carlo analysis.'
                raise AssertionError(msg)
            if run_idx is None:
                msg = 'Index value run_idx cannnot be None, if' \
                      ' you want to perform Monte-Carlo analysis.'
                raise AssertionError(msg)

        if run_mc and sampling_method is None:
            msg = 'sampling_method cannot be None, if run_mc is True!'
            raise AssertionError(msg)

        # Dummy list for processed buildings
        self.list_th_done = []
        self.list_el_done = []

        #  Loop over buildings, which are not connected to energy networks
        for n in self._list_single_build:
            print()
            print('########################################################')
            print('Process stand-alone building with id: ', n)

            building = self.city.nodes[n]['entity']

            #  Calculate single building thermal energy balance
            beb.calc_build_therm_eb(build=building, id=n)

            self.list_th_done.append(n)

            #  Calculate single building electrical energy balance
            beb.calc_build_el_eb(build=building, eeg_pv_limit=eeg_pv_limit)

            self.list_el_done.append(n)

        # LHN energy balance
        #  ################################################################

        self.calc_lhn_energy_balance(run_mc=run_mc,
                                     dict_samples_const=dict_samples_const,
                                     run_idx=run_idx,
                                     sampling_method=sampling_method,
                                     dict_city_sample_lhc=dict_city_sample_lhc)

        #  Make flat lists with all buildings in LHN and DEG networks
        list_lhn_all_b = []
        list_deg_all_b = []

        for list_lhn in self._list_lists_lhn_ids_build:
            for id in list_lhn:
                list_lhn_all_b.append(id)

        for list_deg in self._list_lists_deg_ids_build:
            for id in list_deg:
                list_deg_all_b.append(id)

        # Solve electric energy balance for buildings with LHN connection
        #  which are not connected to DEG
        for n in list_lhn_all_b:
            if n not in list_deg_all_b:
                build = self.city.nodes[n]['entity']

                beb.calc_build_el_eb(build=build, eeg_pv_limit=eeg_pv_limit)

                self.list_el_done.append(n)

                #  Electrical energy balance of subcity (deg subcities)
                #  TODO: Implement DEG energy balance

                #  Share with deg

        # Control check, if all buildings have been processed
        list_buildings = copy.deepcopy(
            self.city.get_list_build_entity_node_ids())

        if sorted(list_buildings) != sorted(self.list_th_done):
            diff = list(set(list_buildings) - set(self.list_th_done))
            msg = 'The following buildings have not been processed with' \
                  ' thermal energy balance:' + str(diff)
            raise AssertionError(msg)

        if sorted(list_buildings) != sorted(self.list_el_done):
            diff = list(set(list_buildings) - set(self.list_el_done))
            msg = 'The following buildings have not been processed with' \
                  ' electric energy balance:' + str(diff)
            raise AssertionError(msg)

        # Reset lists
        self.list_th_done = None
        self.list_el_done = None

    def calc_final_energy_balance_building(self, id, save_fe_dict=True):
        """
        Calculate final energy balance of building with id

        Parameters
        ----------
        id : int
            Building node id
        save_fe_dict : bool, optional
            Defines, if final energy results dictionary should be saved as
            dict_fe_balance attribute on building object (default: True)

        Returns
        -------
        dict_fe_balance : dict (of floats)
            Final energy balance results dictionary. Holding the following
            parameters:
            - fuel_boiler: Boiler fuel energy in kWh/a
            - fuel_chp: CHP fuel energy in kWh/a
            - grid_import_dem: Imported electric energy (for demand) in kWh/a
            - grid_import_hp: Imported electric energy for HP in kWh/a
            - grid_import_eh: Imported electric energy for EH in kWh/a
            - chp_feed: Exported CHP electric energy in kWh/a
            - pv_feed: Exported PV electric energy in kWh/a
        """

        #  Dictionary with final energy demand results
        dict_fe_balance = {}

        build = self.city.nodes[id]['entity']

        if not hasattr(build, 'dict_el_eb_res'):
            msg = 'Building ' + str(id) + ' does not have dict_el_eb_res.'
            raise AssertionError(msg)

        timestep = build.environment.timer.timeDiscretization

        if build.hasBes:
            if build.bes.hasBoiler:
                #  Boiler gas final energy demand in kWh/a
                fuel_b_power = build.bes.boiler.array_fuel_power
                fuel_boiler = sum(fuel_b_power) * timestep \
                              / (1000 * 3600)  # in kWh
                dict_fe_balance['fuel_boiler'] = fuel_boiler
            else:
                dict_fe_balance['fuel_boiler'] = 0
        else:
            dict_fe_balance['fuel_boiler'] = 0

        # CHP gas final energy demand in kWh/a
        if build.hasBes:
            if build.bes.hasChp:
                fuel_chp_power = build.bes.chp.array_fuel_power
                fuel_chp = sum(fuel_chp_power) * timestep \
                           / (1000 * 3600)  # in kWh
                dict_fe_balance['fuel_chp'] = fuel_chp
            else:
                dict_fe_balance['fuel_chp'] = 0
        else:
            dict_fe_balance['fuel_chp'] = 0

        # General electric energy import (without HP and EH) in kWh/a
        grid_import_dem_p = build.dict_el_eb_res['grid_import_dem']
        grid_import_dem = sum(grid_import_dem_p) * timestep \
                          / (1000 * 3600)  # in kWh
        dict_fe_balance['grid_import_dem'] = grid_import_dem

        #  Electric energy import for HP in kWh/a
        grid_import_hp_p = build.dict_el_eb_res['grid_import_hp']
        grid_import_hp = sum(grid_import_hp_p) * timestep \
                         / (1000 * 3600)  # in kWh
        dict_fe_balance['grid_import_hp'] = grid_import_hp

        #  Electric energy import for EH in kWh/a
        grid_import_eh_p = build.dict_el_eb_res['grid_import_eh']
        grid_import_eh = sum(grid_import_eh_p) * timestep \
                         / (1000 * 3600)  # in kWh
        dict_fe_balance['grid_import_eh'] = grid_import_eh

        #  CHP electric energy export in kWh/a
        chp_feed_p = build.dict_el_eb_res['chp_feed']
        chp_feed = sum(chp_feed_p) * timestep \
                   / (1000 * 3600)  # in kWh
        dict_fe_balance['chp_feed'] = chp_feed

        #  PV electric energy export in kWh/a
        pv_feed_p = build.dict_el_eb_res['pv_feed']
        pv_feed = sum(pv_feed_p) * timestep \
                  / (1000 * 3600)  # in kWh
        dict_fe_balance['pv_feed'] = pv_feed

        if save_fe_dict:
            #  Save results dict
            build.dict_fe_balance = dict_fe_balance

        return dict_fe_balance

    def calc_final_energy_balance_city(self):
        """
        Calculate final energy balance of whole city district.
        Requires, that thermal and electric energy balance have been calculated
        for city district!

        Returns
        -------
        dict_fe_city_balance : dict
            Results dict for final energy balance, holding the following
            parameters:
            - fuel_boiler: Boiler fuel energy in kWh/a
            - fuel_chp: CHP fuel energy in kWh/a
            - grid_import_dem: Imported electric energy (for demand) in kWh/a
            - grid_import_hp: Imported electric energy for HP in kWh/a
            - grid_import_eh: Imported electric energy for EH in kWh/a
            - chp_feed: Exported CHP electric energy in kWh/a
            - pv_feed: Exported PV electric energy in kWh/a
        """

        dict_fe_city_balance = {}
        dict_fe_city_balance['fuel_boiler'] = 0
        dict_fe_city_balance['fuel_chp'] = 0
        dict_fe_city_balance['grid_import_dem'] = 0
        dict_fe_city_balance['grid_import_hp'] = 0
        dict_fe_city_balance['grid_import_eh'] = 0
        dict_fe_city_balance['chp_feed'] = 0
        dict_fe_city_balance['pv_feed'] = 0

        #  If system has LHN and pump energy losses
        pump_energy = 0
        if self.list_pump_energy is not None:
            for p_energy in self.list_pump_energy:
                pump_energy += p_energy

        dict_fe_city_balance['pump_energy'] = pump_energy

        list_buildings = self.city.get_list_build_entity_node_ids()

        for n in list_buildings:
            dict_fe_build = self.calc_final_energy_balance_building(id=n)

            dict_fe_city_balance['fuel_boiler'] += dict_fe_build['fuel_boiler']
            dict_fe_city_balance['fuel_chp'] += dict_fe_build['fuel_chp']
            dict_fe_city_balance['grid_import_dem'] \
                += dict_fe_build['grid_import_dem']
            dict_fe_city_balance['grid_import_hp'] \
                += dict_fe_build['grid_import_hp']
            dict_fe_city_balance['grid_import_eh'] \
                += dict_fe_build['grid_import_eh']
            dict_fe_city_balance['chp_feed'] += dict_fe_build['chp_feed']
            dict_fe_city_balance['pv_feed'] += dict_fe_build['pv_feed']

        self.dict_fe_city_balance = dict_fe_city_balance

        return dict_fe_city_balance

    def calc_co2_emissions(self, el_mix_for_chp=True, el_mix_for_pv=True,
                           gcv_to_ncv=True, gcv_to_ncv_factor=1.11):
        """
        Calculate overall CO2 emissions of city district for building energy
        supply.

        Parameters
        ----------
        el_mix_for_chp : bool, optional
            Defines, if el. mix should be used for CHP fed-in electricity
            (default: True). If False, uses specific fed-in CHP factor,
            defined in co2emissions object (co2_factor_el_feed_in)
        el_mix_for_pv : bool, optional
            Defines, if el. mix should be used for PV fed-in electricity
            (default: True). If False, uses specific fed-in PV factor,
            defined in co2emissions object (co2_factor_pv_fed_in)
        gcv_to_ncv : bool, optional
            Perform gross calorific to net calorific conversion
            for gas emissions calculation (default: True)
        gcv_to_ncv_factor : float, optional
            Conversion factor for gross calorific to net calorific conversion
            for gas emissions calculation (default: 1.11)

        Returns
        -------
        co2 : float
            CO2 equivalent in kg/a
        """

        if self.city.environment.co2emissions is None:
            msg = 'Environment does not hold co2emissions object, which is' \
                  ' necessary to calculate emissions. You have to add it, ' \
                  'first. Look within pyCity_calc environments/co2emissions.' \
                  ' You can add it to the existing environment as attribute ' \
                  'co2emissions.'
            raise AssertionError(msg)

        if self.dict_fe_city_balance is None:
            print('Final energy balance has not been calculated, yet. Thus,'
                  ' going to call calc_final_energy_balance_city().')
            self.calc_final_energy_balance_city()

        # Initial co2 emission value
        co2 = 0

        #  Pointer to emission object instance
        co2em = self.city.environment.co2emissions

        if el_mix_for_chp:
            f_chp = co2em.co2_factor_el_mix
        else:
            f_chp = co2em.co2_factor_el_feed_in

        if el_mix_for_pv:
            f_pv = co2em.co2_factor_el_mix
        else:
            f_pv = co2em.co2_factor_pv_fed_in

        # Add emission depending on energy system and fuel
        if gcv_to_ncv:
            co2 += self.dict_fe_city_balance[
                       'fuel_boiler'] * co2em.co2_factor_gas \
                   / gcv_to_ncv_factor
            co2 += self.dict_fe_city_balance['fuel_chp'] * \
                   co2em.co2_factor_gas / gcv_to_ncv_factor
        else:
            co2 += self.dict_fe_city_balance[
                       'fuel_boiler'] * co2em.co2_factor_gas
            co2 += self.dict_fe_city_balance['fuel_chp'] * co2em.co2_factor_gas
        co2 += self.dict_fe_city_balance['grid_import_dem'] \
               * co2em.co2_factor_el_mix
        co2 += self.dict_fe_city_balance['grid_import_hp'] \
               * co2em.co2_factor_el_mix
        co2 += self.dict_fe_city_balance['grid_import_eh'] \
               * co2em.co2_factor_el_mix
        co2 += self.dict_fe_city_balance['pump_energy'] \
               * co2em.co2_factor_el_mix

        #  Subtract feed in amount
        co2 -= self.dict_fe_city_balance['chp_feed'] * f_chp
        co2 -= self.dict_fe_city_balance['pv_feed'] * f_pv

        self.co2 = co2

        return co2

    def calc_co2_em_with_dyn_signal(self, share_ren=0.6, gcv_to_ncv=True,
                                    gcv_to_ncv_factor=1.11):
        """
        Calculates co2 emission with dynamic co2 signal

        Parameters
        ----------
        share_ren : float, optional
            Share of renewables on total el. consumption (default: 0.6).
            E.g. 0.6 means 60% renewables related to total annual el. energy
            consumption. Options: [0.6, 0.8, 1]
        gcv_to_ncv : bool, optional
            Perform gross calorific to net calorific conversion
            for gas emissions calculation (default: True)
        gcv_to_ncv_factor : float, optional
            Conversion factor for gross calorific to net calorific conversion
            for gas emissions calculation (default: 1.11)

        Returns
        -------
        array_co2_dyn : float
            Array with dynamic CO2 emissions in kg (for each timestep)
        """

        assert share_ren in [0.6, 0.8, 1]

        timestep = self.city.environment.timer.timeDiscretization

        array_co2_dyn = np.zeros(len(self.city.environment.weather.tAmbient))

        #  Static factors
        co2_fac_gas = self.city.environment.co2emissions.co2_factor_gas + 0.0
        co2_fac_el = self.city.environment.co2emissions.co2_factor_el_mix + 0.0

        if share_ren == 0.6:
            array_co2_mix = self.city.environment. \
                co2emissions.array_co2_el_mix_60_ren
            array_co2_sup = self.city.environment. \
                co2emissions.array_co2_el_sup_60_ren
        elif share_ren == 0.8:
            array_co2_mix = self.city.environment. \
                co2emissions.array_co2_el_mix_80_ren
            array_co2_sup = self.city.environment. \
                co2emissions.array_co2_el_sup_80_ren
        elif share_ren == 1:
            array_co2_mix = self.city.environment. \
                co2emissions.array_co2_el_mix_100_ren
            array_co2_sup = self.city.environment. \
                co2emissions.array_co2_el_sup_100_ren

        #  Extract co2 emissions caused by pump usage in LHN
        pump_energy = 0
        if self.list_pump_energy is not None:
            for p_energy in self.list_pump_energy:
                pump_energy += p_energy

        co2_pump = pump_energy * co2_fac_el
        co2_pump_per_timestep = co2_pump / len(array_co2_dyn)

        #  Equally distribute co2 emission of pump usage over one year
        for i in range(len(array_co2_dyn)):
            array_co2_dyn[i] += co2_pump_per_timestep

        #  Extract dynamic co2 emission per building
        list_buildings = self.city.get_list_build_entity_node_ids()

        for n in list_buildings:

            build = self.city.nodes[n]['entity']

            if build.hasBes:
                if gcv_to_ncv:
                    #  Boiler
                    if build.bes.hasBoiler:
                        for i in range(len(array_co2_dyn)):
                            array_co2_dyn[i] += \
                                co2_fac_gas * \
                                build.bes.boiler.array_fuel_power[i] * \
                                timestep / (1000 * 3600 * gcv_to_ncv_factor)

                    # CHP
                    if build.bes.hasChp:
                        for i in range(len(array_co2_dyn)):
                            array_co2_dyn[i] += \
                                co2_fac_gas * \
                                build.bes.chp.array_fuel_power[i] * \
                                timestep / (1000 * 3600 * gcv_to_ncv_factor)

                else:
                    #  Boiler
                    if build.bes.hasBoiler:
                        for i in range(len(array_co2_dyn)):
                            array_co2_dyn[i] += \
                                co2_fac_gas * \
                                build.bes.boiler.array_fuel_power[i] * \
                                timestep / (1000 * 3600)

                    # CHP
                    if build.bes.hasChp:
                        for i in range(len(array_co2_dyn)):
                            array_co2_dyn[i] += \
                                co2_fac_gas * \
                                build.bes.chp.array_fuel_power[i] * \
                                timestep / (1000 * 3600)

            # General electric energy import (without HP and EH) in kWh
            array_grid_import_dem = build.dict_el_eb_res['grid_import_dem'] \
                                    * timestep / (1000 * 3600)  # in kWh

            #  Electric energy import for HP in kWh
            array_grid_import_hp = build.dict_el_eb_res['grid_import_hp'] \
                                   * timestep / (1000 * 3600)  # in kWh

            #  Electric energy import for EH in kWh
            array_grid_import_eh = build.dict_el_eb_res['grid_import_eh'] \
                                   * timestep / (1000 * 3600)  # in kWh

            #  CHP electric energy export in kWh
            array_chp_feed = build.dict_el_eb_res['chp_feed'] \
                             * timestep / (1000 * 3600)  # in kWh

            #  PV electric energy export in kWh/a
            array_pv_feed = build.dict_el_eb_res['pv_feed'] \
                            * timestep / (1000 * 3600)  # in kWh

            for i in range(len(array_co2_dyn)):
                array_co2_dyn[i] += array_co2_mix[i] * array_grid_import_dem[i]
                array_co2_dyn[i] += array_co2_mix[i] * array_grid_import_hp[i]
                array_co2_dyn[i] += array_co2_mix[i] * array_grid_import_eh[i]

                array_co2_dyn[i] -= array_co2_sup[i] * array_chp_feed[i]
                array_co2_dyn[i] -= array_co2_sup[i] * array_pv_feed[i]

        return array_co2_dyn

    def get_gen_and_con_energy(self, save_res=True):
        """
        Calculate thermal and electric coverage of city. Returning dict with
        amounts of generated and consumed thermal and eletric energy
        (plus grid import/export).

        Requires thermal and electric energy balance to have been run!

        Parameters
        ----------
        save_res : bool, optional
            Defines, if results should be stored on CityEBCalculator
            (default: True)

        Returns
        -------
        dict_energy : dict (of dicts)
            Dict holdings dicts with amounts of energy
                dict_energy['el_con'] = dict_el_con
                dict_energy['th_gen'] = dict_th_en
                dict_energy['el_gen'] = dict_el_gen
                dict_energy['el_exp'] = dict_el_exp
                dict_energy['el_imp'] = dict_el_imp

                dict_th_en = {'boi': 0, 'chp': 0, 'hp_aw': 0, 'hp_ww': 0,
                'eh': 0}
                dict_el_gen = {'chp': 0, 'pv': 0}
                dict_el_con = {'dem': 0, 'hp_aw': 0, 'hp_ww': 0, 'eh': 0,
                'pump': 0}
                dict_el_exp = {'pv': 0, 'chp': 0}
                dict_el_imp = {'dem': 0, 'hp': 0, 'eh': 0}
        """

        dict_energy = {}

        #  Dummy dicts storing amounts of energy in kWh
        dict_th_en = {'boi': 0, 'chp': 0, 'hp_aw': 0, 'hp_ww': 0, 'eh': 0}
        dict_el_gen = {'chp': 0, 'pv': 0}
        dict_el_con = {'dem': 0, 'hp_aw': 0, 'hp_ww': 0, 'eh': 0, 'pump': 0}
        dict_el_exp = {'pv': 0, 'chp': 0}
        dict_el_imp = {'dem': 0, 'hp': 0, 'eh': 0}

        #  Timestep pointer
        timestep = self.city.environment.timer.timeDiscretization

        #  Get list of building ids
        list_build_ids = self.city.get_list_build_entity_node_ids()

        #  Loop over buildings
        for n in list_build_ids:
            build = self.city.nodes[n]['entity']

            #  Sum up el. demands in kWh
            dict_el_con['dem'] += build.get_annual_el_demand()

            if build.hasBes:

                #  Extract produced amount of thermal energy in kWh
                if build.bes.hasBoiler:
                    dict_th_en['boi'] += \
                        sum(build.bes.boiler.totalQOutput) * timestep / \
                        (3600 * 1000)
                if build.bes.hasChp:
                    dict_th_en['chp'] += \
                        sum(build.bes.chp.totalQOutput) * timestep / \
                        (3600 * 1000)
                if build.bes.hasHeatpump:
                    if build.bes.heatpump.hp_type == 'aw':
                        dict_th_en['hp_aw'] += \
                            sum(build.bes.heatpump.totalQOutput) * timestep / \
                            (3600 * 1000)
                    if build.bes.heatpump.hp_type == 'ww':
                        dict_th_en['hp_ww'] += \
                            sum(build.bes.heatpump.totalQOutput) * timestep / \
                            (3600 * 1000)
                if build.bes.hasElectricalHeater:
                    dict_th_en['eh'] += \
                        sum(build.bes.electricalHeater.totalQOutput) \
                        * timestep / (3600 * 1000)

                #  Extract produced amount of electric energy in kWh
                if build.bes.hasPv:
                    dict_el_gen['pv'] += \
                        sum(build.bes.pv.totalPower) * timestep / \
                        (3600 * 1000)
                if build.bes.hasChp:
                    dict_el_gen['chp'] += \
                        sum(build.bes.chp.totalPOutput) * timestep / \
                        (3600 * 1000)

                #  Extract electric consumption in kWh (for HPs)
                if build.bes.hasHeatpump:
                    if build.bes.heatpump.hp_type == 'aw':
                        dict_el_con['hp_aw'] += \
                            sum(build.bes.heatpump.array_el_power_in) \
                            * timestep / (3600 * 1000)
                    if build.bes.heatpump.hp_type == 'ww':
                        dict_el_con['hp_ww'] += \
                            sum(build.bes.hp.array_el_power_in) * timestep / \
                            (3600 * 1000)
                if build.bes.hasElectricalHeater:
                    dict_el_con['eh'] += \
                        sum(build.bes.electricalHeater.totalPConsumption) \
                        * timestep / (3600 * 1000)

        #  Get pump energy in kWh
        dict_el_con['pump'] = self.dict_fe_city_balance['pump_energy'] + 0.0

        dict_el_exp['pv'] = self.dict_fe_city_balance['pv_feed'] + 0.0
        dict_el_exp['chp'] = self.dict_fe_city_balance['chp_feed'] + 0.0

        dict_el_imp['dem'] = self.dict_fe_city_balance['grid_import_dem'] + 0.0
        dict_el_imp['hp'] = self.dict_fe_city_balance['grid_import_hp'] + 0.0
        dict_el_imp['eh'] = self.dict_fe_city_balance['grid_import_eh'] + 0.0

        #  Save results to dict energy
        dict_energy['el_con'] = dict_el_con
        dict_energy['th_gen'] = dict_th_en
        dict_energy['el_gen'] = dict_el_gen
        dict_energy['el_exp'] = dict_el_exp
        dict_energy['el_imp'] = dict_el_imp

        if save_res:
            self._dict_energy = dict_energy

        return dict_energy

    def plot_coverage(self, path_save_folder=None, save_plots=True,
                      output_filename='energy_coverage',
                      save_tikz=True, dpi=100, print_cov=True):
        """
        Plot thermal and electric coverage plots. Requires
        get_gen_and_con_energy to be run before (to generate
        self._dict_energy)

        Parameters
        ----------
        path_save_folder : str, optional
            Path to folder, where plots should be saved (default: None).
            If None, uses ..\output as savings path folder.
        save_plots : bool, optional
            Save plots (default: True)
        output_filename : str, optional (if None, plot is not saved)
            Defines name of saving file (without file ending)
            (default: 'energy_coverage')
        save_tikz : bool, optional
            Save figure as tikz (default: True). If true, saves figure in
            tikz format for latex implementation
        dpi : int, optional
            DPI size of figures (default: 100). 1000 recommended for Elsevier
            EPS.
        print_cov : bool, optiona
            Defines, if coverage factors should be printed (default: True)
        """

        #  Extract data for stacked bar no. 1
        list_th_energy = []

        boi_th_en = self._dict_energy['th_gen']['boi']
        chp_th_en = self._dict_energy['th_gen']['chp']
        hp_aw_th_en = self._dict_energy['th_gen']['hp_aw']
        hp_ww_th_en = self._dict_energy['th_gen']['hp_ww']
        eh_th_en = self._dict_energy['th_gen']['eh']

        list_th_energy.append(boi_th_en)
        list_th_energy.append(chp_th_en)
        list_th_energy.append(hp_aw_th_en)
        list_th_energy.append(hp_ww_th_en)
        list_th_energy.append(eh_th_en)

        sum_th_energy = sum(list_th_energy)
        array_th_en_cov = np.array(list_th_energy) / sum_th_energy

        #  Extract data for stacked bar no. 2
        list_th_dem = []

        th_dem_city_sh = self.city.get_annual_space_heating_demand()
        th_dem_city_dhw = self.city.get_annual_dhw_demand()

        th_losses = sum(list_th_energy) - th_dem_city_dhw - th_dem_city_sh

        list_th_dem.append(th_dem_city_sh)
        list_th_dem.append(th_dem_city_dhw)
        list_th_dem.append(th_losses)
        list_th_dem.append(0)
        list_th_dem.append(0)

        sum_th_dem = sum(list_th_dem)
        array_th_dem_cov = np.array(list_th_dem) / sum_th_dem

        #  Extract data for stacked bar no. 3
        list_el_energy = []

        chp_gen = self._dict_energy['el_gen']['chp']
        pv_gen = self._dict_energy['el_gen']['pv']

        chp_exp = self._dict_energy['el_exp']['chp']
        pv_exp = self._dict_energy['el_exp']['pv']

        if print_cov:
            print('CHP fed-in energy in kWh:')
            print(chp_exp)
            print('PV fed-in energy in kWh:')
            print(pv_exp)
            print()

        chp_self = chp_gen - chp_exp
        pv_self = pv_gen - pv_exp

        grid_import_dem = self._dict_energy['el_imp']['dem']
        grid_import_hp = self._dict_energy['el_imp']['hp']
        grid_import_eh = self._dict_energy['el_imp']['eh']

        if print_cov:
            print()
            print('CHP self consumed el. energy in kWh: ')
            print(chp_self)
            print('PV self consumed el. energy in kWh: ')
            print(pv_self)
            print()

        list_el_energy.append(chp_self)
        list_el_energy.append(pv_self)
        list_el_energy.append(grid_import_dem)
        list_el_energy.append(grid_import_hp)
        list_el_energy.append(grid_import_eh)

        sum_el_en = sum(list_el_energy)

        #  Extract data for stacked bar no. 4 (negative (feed-in) values)
        list_fed_in_chp = []

        list_fed_in_chp.append(0)
        list_fed_in_chp.append(0)
        list_fed_in_chp.append(-chp_exp)
        list_fed_in_chp.append(0)

        list_fed_in_pv = []
        list_fed_in_pv.append(0)
        list_fed_in_pv.append(0)
        list_fed_in_pv.append(-pv_exp)
        list_fed_in_pv.append(0)

        sum_exp = abs(sum(list_fed_in_chp)) + abs(sum(list_fed_in_pv))

        array_el_en_cov = np.array(list_el_energy) / (sum_el_en + sum_exp)

        array_el_exp_chp_cov = np.array(list_fed_in_chp) / (
                sum_el_en + sum_exp)

        array_el_exp_pv_cov = np.array(list_fed_in_pv) / (sum_el_en + sum_exp)

        #  Extract data for stacked bar no. 5 (electric demands)
        list_el_dem = []

        el_dem = self._dict_energy['el_con']['dem']
        hp_aw_dem = self._dict_energy['el_con']['hp_aw']
        hp_ww_dem = self._dict_energy['el_con']['hp_ww']
        eh_dem = self._dict_energy['el_con']['eh']
        pump_dem = self._dict_energy['el_con']['pump']

        own_cov = (chp_self + pv_self) / \
                  (el_dem + hp_aw_dem + hp_ww_dem + eh_dem)
        pv_cov = (pv_self) / \
                 (el_dem + hp_aw_dem + hp_ww_dem + eh_dem)
        chp_cov = (chp_self) / \
                  (el_dem + hp_aw_dem + hp_ww_dem + eh_dem)

        if print_cov:
            print('Coverage of building, HP and EH el. energy demand'
                  ' by own CHP and PV generation: ')
            print(own_cov)
            print()

            print('Share of CHP (th.):')
            chp_th_cov = chp_th_en / sum_th_dem
            print(chp_th_cov)
            print()

            print('Share of CHP (el.):')
            print(chp_cov)
            print()

            print('Share of PV:')
            print(pv_cov)
            print()

        list_el_dem.append(el_dem)
        list_el_dem.append(hp_aw_dem)
        list_el_dem.append(hp_ww_dem)
        list_el_dem.append(eh_dem)
        list_el_dem.append(pump_dem)

        sum_el_dem = sum(list_el_dem)
        array_el_dem = np.array(list_el_dem) / sum_el_dem

        #  Stack arrays together
        array_res = np.vstack((array_th_en_cov, array_th_dem_cov))
        array_res = np.vstack((array_res, array_el_en_cov))
        array_res = np.vstack((array_res, array_el_dem))

        # array_th_en_cov
        # array_th_dem_cov
        # array_el_en_cov
        # array_el_exp(x)
        # array_el_dem

        array_res = np.transpose(array_res)

        #  Stack negative values to rs
        array_res = np.vstack((array_res, array_el_exp_chp_cov))
        array_res = np.vstack((array_res, array_el_exp_pv_cov))

        #  Start plotting
        #  ###############################################################
        list_col_1 = ['#e6194b', '#911eb4', '#008080', '#aaffc3']
        list_col_2 = ['#3cb44b', '#46f0f0', '#e6beff', '#808000']
        list_col_3 = ['#ffe119', '#f032e6', '#aa6e28', '#ffd8b1']
        list_col_4 = ['#0082c8', '#d2f53c', '#fffac8', '#000080']
        list_col_5 = ['#f58231', '#fabebe', '#800000', '#000000']

        list_col_6 = ['#C0C0C0', '#C0C0C0', '#C0C0C0', '#C0C0C0']
        list_col_7 = ['#646464', '#646464', '#646464', '#646464']

        fig = plt.figure(figsize=(8, 6))

        N = 4

        ind = np.arange(N)

        width = 0.6

        colors = ['#624ea7', 'g', 'yellow', 'k', 'maroon']

        p1 = plt.bar(ind, array_res[0], width=width, color=list_col_1)
        p2 = plt.bar(ind, array_res[1], bottom=array_res[0], width=width,
                     color=list_col_2)
        p3 = plt.bar(ind, array_res[2], bottom=array_res[0] + array_res[1],
                     width=width,
                     color=list_col_3)
        p4 = plt.bar(ind, array_res[3],
                     bottom=array_res[0] + array_res[1] + array_res[2],
                     width=width,
                     color=list_col_4)
        p5 = plt.bar(ind, array_res[4],
                     bottom=array_res[0] + array_res[1] + array_res[2] +
                            array_res[3], width=width,
                     color=list_col_5)

        #  Negative plots
        p6 = plt.bar(ind, array_res[5], width=width,
                     color=list_col_6)
        p7 = plt.bar(ind, array_res[6], bottom=array_res[5], width=width,
                     color=list_col_7)

        plt.xticks(ind, ('Thermal sources',
                         'Thermal sinks',
                         'Electric sources',
                         'Electric sinks'
                         ))

        # #  Add hatches
        # patterns = ('//', '//', 'x', 'x')
        # for bar, pattern in zip(p1, patterns):
        #     bar.set_hatch(pattern)
        # for bar, pattern in zip(p2, patterns):
        #     bar.set_hatch(pattern)
        # for bar, pattern in zip(p3, patterns):
        #     bar.set_hatch(pattern)
        # for bar, pattern in zip(p4, patterns):
        #     bar.set_hatch(pattern)
        # for bar, pattern in zip(p5, patterns):
        #     bar.set_hatch(pattern)
        # for bar, pattern in zip(p6, patterns):
        #     bar.set_hatch(patterns)
        # for bar, pattern in zip(p7, patterns):
        #     bar.set_hatch(patterns)

        dict_th_en = {'boi': 0, 'chp': 0, 'hp_aw': 0, 'hp_ww': 0, 'eh': 0}

        #  Add legend
        patch_1_a = mpatches.Patch(facecolor='#e6194b',
                                   # hatch=r'//',
                                   label='BOI')
        patch_1_b = mpatches.Patch(facecolor='#3cb44b',
                                   # hatch=r'//',
                                   label='CHP')
        patch_1_c = mpatches.Patch(facecolor='#ffe119',
                                   # hatch=r'//',
                                   label='HP (aw)')
        patch_1_d = mpatches.Patch(facecolor='#0082c8',
                                   # hatch=r'//',
                                   label='HP (ww)')
        patch_1_e = mpatches.Patch(facecolor='#f58231',
                                   # hatch=r'//',
                                   label='EH')

        patch_2_a = mpatches.Patch(facecolor='#911eb4',
                                   # hatch=r'//',
                                   label='Space heat')
        patch_2_b = mpatches.Patch(facecolor='#46f0f0',
                                   # hatch=r'//',
                                   label='Hot water')
        patch_2_c = mpatches.Patch(facecolor='#f032e6',
                                   # hatch=r'//',
                                   label='Losses')

        patch_3_a = mpatches.Patch(facecolor='#008080',
                                   # hatch=r'x',
                                   label='CHP (self)')
        patch_3_b = mpatches.Patch(facecolor='#e6beff',
                                   # hatch=r'x',
                                   label='PV (self)')
        patch_3_c = mpatches.Patch(facecolor='#aa6e28',
                                   # hatch=r'x',
                                   label='Grid (House dem)')
        patch_3_d = mpatches.Patch(facecolor='#fffac8',
                                   # hatch=r'x',
                                   label='Grid (HP)')
        patch_3_e = mpatches.Patch(facecolor='#800000',
                                   # hatch=r'x',
                                   label='Grid (EH)')

        patch_4_a = mpatches.Patch(facecolor='#aaffc3',
                                   # hatch=r'x',
                                   label='House (dem)')
        patch_4_b = mpatches.Patch(facecolor='#808000',
                                   # hatch=r'x',
                                   label='HP (aw) (dem)')
        patch_4_c = mpatches.Patch(facecolor='#ffd8b1',
                                   # hatch=r'x',
                                   label='HP (ww) (dem)')
        patch_4_d = mpatches.Patch(facecolor='#000080',
                                   # hatch=r'x',
                                   label='EH (dem)')
        patch_4_e = mpatches.Patch(facecolor='#000000',
                                   # hatch=r'x',
                                   label='Pumps (dem)')

        patch_5_a = mpatches.Patch(facecolor='#C0C0C0',
                                   # hatch=r'xx',
                                   label='CHP (exp)')
        patch_5_b = mpatches.Patch(facecolor='#646464',
                                   # hatch=r'xx',
                                   label='PV (exp)')

        ax = fig.gca()
        # Shrink current axis's height by 10% on the bottom
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.2,
                         box.width, box.height * 0.8])

        plt.legend(handles=[patch_1_a, patch_1_b, patch_1_c, patch_1_d,
                            patch_1_e,
                            patch_2_a, patch_2_b, patch_2_c,
                            patch_3_a, patch_3_b, patch_3_c, patch_3_d,
                            patch_3_e,
                            patch_5_a, patch_5_b,
                            patch_4_a, patch_4_b, patch_4_c, patch_4_d,
                            patch_4_e
                            ],
                   # loc='best', ncol=2)
                   loc='upper center', bbox_to_anchor=(0.5, -0.1),
                   fancybox=True, shadow=False, ncol=4)

        plt.ylabel('Share of energy')
        # plt.tight_layout()
        plt.show()

        if path_save_folder is None:
            this_path = os.path.dirname(os.path.abspath(__file__))
            path_save_folder = os.path.join(this_path, 'output')

        # Save plot
        if save_plots:
            #  Generate path if not existent

            #  Generate file names for different formats
            file_pdf = output_filename + '.pdf'
            file_eps = output_filename + '.eps'
            file_png = output_filename + '.png'
            file_tiff = output_filename + '.tiff'
            file_tikz = output_filename + '.tikz'
            file_svg = output_filename + '.svg'

            #  Generate saving pathes
            path_pdf = os.path.join(path_save_folder, file_pdf)
            path_eps = os.path.join(path_save_folder, file_eps)
            path_png = os.path.join(path_save_folder, file_png)
            path_tiff = os.path.join(path_save_folder, file_tiff)
            path_tikz = os.path.join(path_save_folder, file_tikz)
            path_svg = os.path.join(path_save_folder, file_svg)

            #  Save figure in different formats
            plt.savefig(path_pdf, format='pdf', dpi=dpi)
            plt.savefig(path_eps, format='eps', dpi=dpi)
            plt.savefig(path_png, format='png', dpi=dpi)
            # plt.savefig(path_tiff, format='tiff', dpi=dpi)
            plt.savefig(path_svg, format='svg', dpi=dpi)

            if save_tikz:
                tikz_save(path_tikz, figureheight='\\figureheight',
                          figurewidth='\\figurewidth')

        plt.close()


def main():
    import pycity_calc.cities.scripts.city_generator.city_generator as citygen
    import pycity_calc.cities.scripts.overall_gen_and_dimensioning as overall
    import matplotlib.pyplot as plt

    this_path = os.path.dirname(os.path.abspath(__file__))

    el_mix_for_chp = True  # Use el. mix for CHP fed-in electricity
    el_mix_for_pv = True  # Use el. mix for PV fed-in electricity

    try:
        #  Try loading city pickle file
        filename = 'city_clust_simple_with_esys.pkl'
        file_path = os.path.join(this_path, 'input', filename)
        city_object = pickle.load(open(file_path, mode='rb'))

    except:
        print('Could not load city pickle file. Going to generate a new one.')
        #  # Userinputs
        #  #----------------------------------------------------------------------

        #  Generate environment
        #  ######################################################
        year_timer = 2017
        year_co2 = 2017
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
        th_gen_method = 3
        #  For non-residential buildings, SLPs are generated automatically.

        #  Manipulate thermal slp to fit to space heating demand?
        slp_manipulate = True
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
        el_gen_method = 2
        #  If user defindes method_3_nb or method_4_nb within input file
        #  (only valid for non-residential buildings), SLP will not be used.
        #  Instead, corresponding profile will be loaded (based on measurement
        #  data, see ElectricalDemand.py within pycity)

        #  Do normalization of el. load profile
        #  (only relevant for el_gen_method=2).
        #  Rescales el. load profile to expected annual el. demand value in kWh
        do_normalization = True

        #  Randomize electrical demand value (residential buildings, only)
        el_random = False

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
        use_dhw = True  # Only relevant for residential buildings

        #  DHW generation method? (1 - Annex 42; 2 - Stochastic profiles)
        #  Choice of Annex 42 profiles NOT recommended for multiple buildings,
        #  as profile stays the same and only changes scaling.
        #  Stochastic profiles require defined nb of occupants per residential
        #  building
        dhw_method = 2  # Only relevant for residential buildings

        #  Define dhw volume per person and day (use_dhw=True)
        dhw_volumen = None  # Only relevant for residential buildings

        #  Randomize choosen dhw_volume reference value by selecting new value
        #  from gaussian distribution with 20 % standard deviation
        dhw_random = False

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
        air_vent_mode = 2
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
                                                      year_timer=year_timer,
                                                      year_co2=year_co2,
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

        city_object.nodes[1006]['entity'].bes.boiler.qNominal *= 5
        city_object.nodes[1006]['entity'].bes.tes.capacity *= 5

        # Save new pickle file
        filename = 'city_clust_simple_with_esys.pkl'
        file_path = os.path.join(this_path, 'input', filename)
        pickle.dump(city_object, open(file_path, mode='wb'))

    # Construct energy balance
    energy_balance = CityEBCalculator(city=city_object)

    #  Calc. city energy balance
    energy_balance.calc_city_energy_balance()

    #  Perform final energy anaylsis
    dict_fe_city = energy_balance.calc_final_energy_balance_city()

    #  Perform emissions calculation
    co2 = energy_balance.calc_co2_emissions(el_mix_for_chp=el_mix_for_chp,
                                            el_mix_for_pv=el_mix_for_pv)

    #  Calculate amounts of generated and consumed energy to calculate
    #  coverage
    dict_energy = energy_balance.get_gen_and_con_energy()

    fuel_boiler = dict_fe_city['fuel_boiler']
    fuel_chp = dict_fe_city['fuel_chp']
    grid_import_dem = dict_fe_city['grid_import_dem']
    grid_import_hp = dict_fe_city['grid_import_hp']
    grid_import_eh = dict_fe_city['grid_import_eh']
    chp_feed = dict_fe_city['chp_feed']
    pv_feed = dict_fe_city['pv_feed']
    pump_energy = dict_fe_city['pump_energy']

    print('Amounts of generated and consumed energy')
    print('#############################################')
    for key in dict_energy.keys():
        print('Dict. key: ')
        print(key)
        print('Values')
        print(dict_energy[key])
        print()
    print('#############################################')
    print()

    print('Boiler fuel demand in kWh/a: ')
    print(round(fuel_boiler, 0))

    print('CHP fuel demand in kWh/a: ')
    print(round(fuel_chp, 0))
    print()

    print('Imported electricity in kWh/a: ')
    print(round(grid_import_dem + grid_import_eh + grid_import_hp, 0))

    print('Exported CHP electricity in kWh/a: ')
    print(round(chp_feed, 0))

    print('Exported PV electricity in kWh/a: ')
    print(round(pv_feed, 0))
    print()

    print('LHN electric pump energy in kWh/a:')
    print(round(pump_energy, 0))
    print()

    print('#############################################')
    print()

    print('Total emissions of city district in t/a:')
    print(round(co2 / 1000, 0))

    #  Plot coverage figures
    energy_balance.plot_coverage()

    print('#############################################')
    print()

    #  Calculate dynamic CO2 signal
    array_co2_dyn = energy_balance.calc_co2_em_with_dyn_signal(share_ren=0.6)

    print('Sum of dynamic CO2 emissions in t/a: ')
    print(round(sum(array_co2_dyn) / 1000, 0))

    # plt.plot(array_co2_dyn)
    # plt.ylabel('CO2 emission in kg')
    # plt.title('Dynamic CO2 emissions')
    # plt.show()
    # plt.close()


if __name__ == '__main__':
    main()