#!/usr/bin/env python
# coding=utf-8
"""
Script to calculate annuities of city district
"""
from __future__ import division

import os
import pickle
import warnings

import pycity_calc.environments.germanmarket as gmarket
import pycity_calc.simulation.energy_balance.city_eb_calc as citeb
import pycity_calc.economic.annuity_calculation as annu
import pycity_calc.toolbox.dimensioning.dim_functions as dimfunc
import pycity_calc.toolbox.networks.network_ops as netop

import pycity_calc.economic.energy_sys_cost.bat_cost as bat_cost
import pycity_calc.economic.energy_sys_cost.boiler_cost as boiler_cost
import pycity_calc.economic.energy_sys_cost.chp_cost as chp_cost
import pycity_calc.economic.energy_sys_cost.deg_cost as deg_cost
import pycity_calc.economic.energy_sys_cost.eh_cost as eh_cost
import pycity_calc.economic.energy_sys_cost.hp_cost as hp_cost
import pycity_calc.economic.energy_sys_cost.lhn_cost as lhn_cost
import pycity_calc.economic.energy_sys_cost.pv_cost as pv_cost
import pycity_calc.economic.energy_sys_cost.tes_cost as tes_cost


class CityAnnuityCalc(object):
    """
    Annuity calculation class for city

    Attributes
    ----------
    annuity_obj : object
        Annuity object of pyCity_calc
    energy_balance : object
        City energy balance object of pyCity_calc
    _list_buildings : list (of ints)
        List of building entity ids in city (calculated within __init__)
    """

    def __init__(self, annuity_obj, energy_balance):
        """
        Constructor of CityAnnuityCalc object instance

        Parameters
        ----------
        annuity_obj : object
            Annuity object of pyCity_calc
        energy_balance : object
            City energy balance object of pyCity_calc
        """

        self.annuity_obj = annuity_obj
        self.energy_balance = energy_balance

        self._list_buildings = \
            self.energy_balance.city.get_list_build_entity_node_ids()

    def calc_cap_rel_annuity_city(self, run_mc=False, dict_samples_const=None,
                                  dict_samples_esys=None,
                                  run_idx=None, sampling_method=None,
                                  dict_city_sample_lhc=None,
                                  dict_build_samples_lhc=None):
        """
        Calculate sum of all capital related annuities of city

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
        dict_samples_esys : dict (of dicts)
            Dictionary holding dictionaries with energy system sampling
            data for MC run (default: None)
            dict_samples_esys['<building_id>'] = dict_esys
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
        dict_build_samples_lhc : dict, optional
            Dict. holding building ids as keys and dict of samples as
            values (default: None).
            These dicts hold paramter names as keys and numpy arrays with
            samples as dict values.  Only
            relevant if mc_run is True and sampling_method == 'lhc'

        Returns
        -------
        tup_res : tuple
            Results tuple with 3 entries (cap_rel_ann, list_invest, list_type)
            cap_rel_ann : float
                Capital-related annuity in Euro
            list_invest : list (of floats)
                List holding investment cost per component in Euro
            list_type : list (of str)
                List holding tags of system type (str), such as 'B' for boiler
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
            if dict_city_sample_lhc is None or dict_build_samples_lhc is None:
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

        cap_rel_ann = 0  # Dummy value for capital-related annuity
        list_invest = []  # Dummy list to store investment cost
        list_type = []  # Dummy list to store type of component

        #  Get capital-related annuities per energy system unit
        #  ###################################################################
        for n in self._list_buildings:
            build = self.energy_balance.city.nodes[n]['entity']
            if build.hasBes:

                #  BES pointer
                bes = build.bes

                if run_mc and sampling_method == 'random':
                    #  Get pointer to energy system sample dict
                    dict_esys = dict_samples_esys[str(n)]

                if bes.hasBattery:
                    cap_kWh = bes.battery.capacity / (3600 * 1000)

                    if run_mc and sampling_method == 'random':
                        inv_unc = dict_esys['bat']['bat_inv'][run_idx]
                    elif run_mc and sampling_method == 'lhc':
                        #  Get pointer to energy system sample dict
                        inv_unc = \
                            dict_build_samples_lhc[n]['bat_inv'][run_idx]
                    else:
                        inv_unc = 1

                    # In kWh
                    bat_invest = inv_unc * \
                                 bat_cost.calc_invest_cost_bat(cap=cap_kWh)

                    cap_rel_ann += \
                        self.annuity_obj.calc_capital_rel_annuity_with_type(
                            invest=bat_invest, type='BAT')

                    #  Add to lists
                    list_invest.append(bat_invest)
                    list_type.append('BAT')

                if bes.hasBoiler:
                    q_nom = bes.boiler.qNominal / 1000  # in kW

                    if run_mc and sampling_method == 'random':
                        inv_unc = dict_esys['boi']['boi_inv'][run_idx]
                    elif run_mc and sampling_method == 'lhc':
                        #  Get pointer to energy system sample dict
                        inv_unc = \
                            dict_build_samples_lhc[n]['boi_inv'][run_idx]
                    else:
                        inv_unc = 1

                    boil_invest = inv_unc * \
                                  boiler_cost.calc_abs_boiler_cost(
                                      q_nom=q_nom)

                    cap_rel_ann += \
                        self.annuity_obj.calc_capital_rel_annuity_with_type(
                            invest=boil_invest, type='B')
                    #  Add to lists
                    list_invest.append(boil_invest)
                    list_type.append('B')

                if bes.hasChp:
                    p_el_nom = bes.chp.pNominal / 1000  # in kW

                    if run_mc and sampling_method == 'random':
                        inv_unc = dict_esys['chp']['chp_inv'][run_idx]
                    elif run_mc and sampling_method == 'lhc':
                        #  Get pointer to energy system sample dict
                        inv_unc = \
                            dict_build_samples_lhc[n]['chp_inv'][run_idx]
                    else:
                        inv_unc = 1

                    chp_invest = inv_unc * chp_cost.calc_invest_cost_chp(
                        p_el_nom=p_el_nom)

                    cap_rel_ann += \
                        self.annuity_obj.calc_capital_rel_annuity_with_type(
                            invest=chp_invest, type='CHP')
                    #  Add to lists
                    list_invest.append(chp_invest)
                    list_type.append('CHP')

                if bes.hasElectricalHeater:
                    q_eh = \
                        bes.electricalHeater.qNominal / 1000  # in kW

                    if run_mc and sampling_method == 'random':
                        inv_unc = dict_esys['eh']['eh_inv'][run_idx]
                    elif run_mc and sampling_method == 'lhc':
                        #  Get pointer to energy system sample dict
                        inv_unc = \
                            dict_build_samples_lhc[n]['eh_inv'][run_idx]
                    else:
                        inv_unc = 1

                    eh_invest = inv_unc * eh_cost.calc_abs_cost_eh(q_nom=q_eh)

                    cap_rel_ann += \
                        self.annuity_obj.calc_capital_rel_annuity_with_type(
                            invest=eh_invest, type='EH')
                    #  Add to lists
                    list_invest.append(eh_invest)
                    list_type.append('EH')

                if bes.hasHeatpump:
                    q_hp = bes.heatpump.qNominal / 1000  # in kW

                    if run_mc and sampling_method == 'random':
                        inv_unc = dict_esys['hp']['hp_inv'][run_idx]
                    elif run_mc and sampling_method == 'lhc':
                        #  Get pointer to energy system sample dict
                        inv_unc = \
                            dict_build_samples_lhc[n]['hp_inv'][run_idx]
                    else:
                        inv_unc = 1

                    hp_invest = inv_unc * \
                                hp_cost.calc_invest_cost_hp(q_nom=q_hp)

                    cap_rel_ann += \
                        self.annuity_obj.calc_capital_rel_annuity_with_type(
                            invest=hp_invest, type='HP')
                    #  Add to lists
                    list_invest.append(hp_invest)
                    list_type.append('HP')

                if bes.hasPv:
                    pv_area = bes.pv.area

                    if run_mc and sampling_method == 'random':
                        inv_unc = dict_esys['PV']['pv_inv'][run_idx]
                    elif run_mc and sampling_method == 'lhc':
                        #  Get pointer to energy system sample dict
                        inv_unc = \
                            dict_build_samples_lhc[n]['pv_inv'][run_idx]
                    else:
                        inv_unc = 1

                    pv_invest = inv_unc * pv_cost.calc_pv_invest(
                        area=pv_area)

                    cap_rel_ann += \
                        self.annuity_obj.calc_capital_rel_annuity_with_type(
                            invest=pv_invest, type='PV')
                    #  Add to lists
                    list_invest.append(pv_invest)
                    list_type.append('PV')

                if bes.hasTes:
                    tes_vol = bes.tes.capacity / 1000  # in m3

                    if run_mc and sampling_method == 'random':
                        inv_unc = dict_esys['tes']['tes_inv'][run_idx]
                    elif run_mc and sampling_method == 'lhc':
                        #  Get pointer to energy system sample dict
                        inv_unc = \
                            dict_build_samples_lhc[n]['tes_inv'][run_idx]
                    else:
                        inv_unc = 1

                    tes_invest = inv_unc * tes_cost.calc_invest_cost_tes(
                        volume=tes_vol)

                    cap_rel_ann += \
                        self.annuity_obj.calc_capital_rel_annuity_with_type(
                            invest=tes_invest, type='TES')
                    #  Add to lists
                    list_invest.append(tes_invest)
                    list_type.append('TES')

        # Get capital-related annuities per LHN network
        #  ###################################################################
        list_lhn_con = \
            netop.get_list_with_energy_net_con_node_ids(
                city=self.energy_balance.city,
                network_type='heating')

        #  Add weights to edges
        netop.add_weights_to_edges(self.energy_balance.city)

        #  If LHN networks exist
        if len(list_lhn_con) > 0:

            invest_lhn_pipe = 0
            invest_lhn_trans = 0

            if run_mc and sampling_method == 'random':
                inv_unc = dict_samples_const['city']['lhn_inv'][run_idx]
            elif run_mc and sampling_method == 'lhc':
                inv_unc = dict_city_sample_lhc['lhn_inv'][run_idx]
            else:
                inv_unc = 1

            # Loop over each connected lhn network
            for sublist in list_lhn_con:

                list_th_pow = []

                if run_mc:
                    #  Simplified estimation, as precise calculation can cause
                    #  assertion errors (if Monte-Carlo run th. demand is
                    #  zero for lhn connected buliding #258)
                    invest_lhn_trans += inv_unc * 5000
                else:
                    for n in self.energy_balance.city.nodes():
                        if 'node_type' in self.energy_balance.city.nodes[n]:
                            #  If node_type is building
                            if self.energy_balance.city.nodes[n][
                                'node_type'] == 'building':
                                #  If entity is kind building
                                if self.energy_balance.city.nodes[n][
                                    'entity']._kind == 'building':
                                    build = self.energy_balance.city.nodes[n][
                                        'entity']
                                    th_pow = \
                                        dimfunc.get_max_power_of_building(
                                            build,
                                            with_dhw=False)
                                    list_th_pow.append(
                                        th_pow / 1000)  # Convert W to kW

                    invest_lhn_trans += \
                        lhn_cost.calc_invest_cost_lhn_stations(
                            list_powers=list_th_pow)

                # Add to lists
                list_invest.append(invest_lhn_trans)
                list_type.append('LHN_station')

                #  Loop over every heating pipe and calculate cost
                for u in sublist:
                    for v in sublist:
                        if self.energy_balance.city.has_edge(u, v):
                            if 'network_type' in \
                                    self.energy_balance.city.edges[u, v]:
                                if (self.energy_balance.city.edges[u, v][
                                        'network_type'] == 'heating' or
                                            self.energy_balance.city.edges[u,
                                                                           v][
                                                'network_type'] == 'heating_and_deg'):
                                    #  Pointer to pipe (edge)
                                    pipe = self.energy_balance.city.edges[u, v]
                                    d_i = pipe['d_i']
                                    length = pipe['weight']

                                    invest_lhn_pipe += inv_unc * \
                                                       lhn_cost.calc_invest_cost_lhn_pipes(
                                                           d=d_i,
                                                           length=length)

                # Add to lists
                list_invest.append(invest_lhn_pipe)
                list_type.append('LHN_plastic_pipe')

            # Calculate capital-related annuity of LHN network

            #  Capital-related annuity for LHN transmission stations
            cap_rel_ann += \
                self.annuity_obj.calc_capital_rel_annuity_with_type(
                    invest=invest_lhn_trans,
                    type='LHN_station')

            #  Capital-related annuity for LHN pipelines
            cap_rel_ann += \
                self.annuity_obj.calc_capital_rel_annuity_with_type(
                    invest=invest_lhn_pipe,
                    type='LHN_plastic_pipe')

        # Get capital-related annuities per DEG network
        #  ###################################################################
        list_deg_con = \
            netop.get_list_with_energy_net_con_node_ids(
                city=self.energy_balance.city,
                network_type='electricity')

        #  If DEG networks exist
        if len(list_deg_con) > 0:

            deg_invest = 0

            #  Loop over (sub-)deg networks
            for sublist in list_deg_con:

                print('Current sublist')
                print(sublist)

                nb_build = 0

                #  Get number of buildings within district
                #  Defines the number of meters
                for n in self.energy_balance.city.nodes():
                    if 'node_type' in self.energy_balance.city.nodes[n]:
                        #  If node_type is building
                        if self.energy_balance.city.nodes[n][
                            'node_type'] == 'building':
                            #  If entity is kind building
                            if self.energy_balance.city.nodes[n][
                                'entity']._kind == 'building':
                                nb_build += 1

                deg_len = 0
                deg_len_w_lhn = 0

                #  Loop over every deg pipe and calculate cost
                for u in sublist:
                    for v in sublist:
                        if self.energy_balance.city.has_edge(u, v):
                            if 'network_type' in \
                                    self.energy_balance.city.edges[u,
                                                                   v]:
                                if self.energy_balance.city.edges[u, v][
                                    'network_type'] == 'electricity':
                                    deg_len += \
                                        self.energy_balance.city.edges[u, v][
                                            'weight']
                                elif self.energy_balance.city.edges[u, v][
                                    'network_type'] == 'heating_and_deg':
                                    deg_len_w_lhn += \
                                        self.energy_balance.city.edges[u, v][
                                            'weight']

                # Calculate deg investment cost for (sub-)deg
                deg_invest += \
                    deg_cost.calc_invest_cost_deg(
                        length=deg_len + deg_len_w_lhn,
                        nb_con=nb_build,
                        nb_sub=1,
                        share_lhn=(deg_len_w_lhn / (deg_len + deg_len_w_lhn)))

                # Add to lists
                list_invest.append(deg_invest)
                list_type.append('DEG')

                #  Capital-related annuity for LHN transmission stations
                cap_rel_ann += \
                    self.annuity_obj.calc_capital_rel_annuity_with_type(
                        invest=deg_invest,
                        type='DEG')

        return (cap_rel_ann, list_invest, list_type)

    def calc_cap_and_op_rel_annuity_city(self, run_mc=False,
                                         dict_samples_const=None,
                                         dict_samples_esys=None,
                                         run_idx=None,
                                         sampling_method=None,
                                         dict_city_sample_lhc=None,
                                         dict_build_samples_lhc=None
                                         ):
        """
        Calculate capital- and operation-related annuities of city
    
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
        dict_samples_esys : dict (of dicts)
            Dictionary holding dictionaries with energy system sampling
            data for MC run (default: None)
            dict_samples_esys['<building_id>'] = dict_esys
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
        dict_build_samples_lhc : dict, optional
            Dict. holding building ids as keys and dict of samples as
            values (default: None).
            These dicts hold paramter names as keys and numpy arrays with
            samples as dict values.  Only
            relevant if mc_run is True and sampling_method == 'lhc'

        Returns
        -------
        tup_ann : tuple (of floats)
            Tuple with capital- and operation-related annuities (floats) in Euro
            (cap_rel_ann, op_rel_ann)
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
            if dict_city_sample_lhc is None or dict_build_samples_lhc is None:
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

        # Calculate capital-related annuities
        (cap_rel_ann, list_invest, list_type) = \
            self.calc_cap_rel_annuity_city(run_mc=run_mc,
                                           dict_samples_const=
                                           dict_samples_const,
                                           dict_samples_esys=dict_samples_esys,
                                           run_idx=run_idx,
                                           sampling_method=
                                           sampling_method,
                                           dict_city_sample_lhc=
                                           dict_city_sample_lhc,
                                           dict_build_samples_lhc=
                                           dict_build_samples_lhc
                                           )

        #  Calculate operation-related annuity
        op_rel_ann = \
            self.annuity_obj.calc_op_rel_annuity_multi_comp(
                list_invest=list_invest,
                list_types=list_type)

        return (cap_rel_ann, op_rel_ann)

    def calc_dem_rel_annuity_building(self, id, save_dem_rel_res=True):
        """
        Returns demand related annuity for single building of city

        Parameters
        ----------
        id : int
            Building node id
        save_dem_rel_res : bool, optional
            Defines, if dem_rel_build should be saved on buildinb object
            (default: True)

        Returns
        -------
        dem_rel_build : float
            Demand related annuity of single buiding in Euro/a
        """

        #  Building pointer
        build = self.energy_balance.city.nodes[id]['entity']

        timestep = build.environment.timer.timeDiscretization

        #  Get final energy results dict of building
        dict_fe = build.dict_fe_balance

        #  Final energy in kWh
        fuel_boiler = dict_fe['fuel_boiler']
        fuel_chp = dict_fe['fuel_chp']
        grid_import_dem = dict_fe['grid_import_dem']
        grid_import_hp = dict_fe['grid_import_hp']
        grid_import_eh = dict_fe['grid_import_eh']

        #  Get net electric energy demand results
        dict_el_eb = build.dict_el_eb_res

        #  Self produced and consumed electric energy in kWh
        pv_self = sum(dict_el_eb['pv_self']) * timestep / (1000 * 3600)
        chp_self = sum(dict_el_eb['chp_self']) * timestep / (1000 * 3600)

        #  Use same year as co2 emission factors
        #  TODO: Extract year for annuity calculation
        year = self.energy_balance.city.environment.timer.year

        if build.build_type is None:
            msg = 'build.build_type is None. Assume, that this building is' \
                  ' residential building to estimate specific energy cost.'
            warnings.warn(msg)
            type = 'res'
        elif build.build_type == 0:
            type = 'res'
        elif build.build_type > 0:
            type = 'ind'
        else:
            msg = 'Wrong input for build.build_type!'
            raise AssertionError(msg)

        # Calculate specific cost values for energy demands
        spec_cost_gas = \
            self.energy_balance.city.environment.prices. \
                get_spec_gas_cost(type=type,
                                  year=year,
                                  annual_demand=fuel_boiler + fuel_chp)

        spec_cost_el = self.energy_balance.city.environment.prices. \
            get_spec_el_cost(type=type,
                             year=year,
                             annual_demand=grid_import_dem)

        #  Heat pump tariffs
        if build.hasBes:
            if type == 'res' and build.bes.hasHeatpump:
                hp_tariff = self.energy_balance.city. \
                                environment.prices.hp_day_tarif + 0.0
            else:
                #  Use regular prices
                hp_tariff = spec_cost_el + 0.0
        else:
            #  Use regular prices
            hp_tariff = spec_cost_el + 0.0

        # #  Electric heater tariff
        # if build.bes.hasHeatpump:
        #     #  Use hp_tariff
        #     eh_tariff = hp_tariff + 0.0
        # else:
        #     #  Use regular prices
        #     eh_tariff = spec_cost_el + 0.0

        #  Calculate demand related annuity for gas and electricity purchases
        #  (without EEG)
        dem_rel_annuity = self.annuity_obj. \
            calc_dem_rel_annuity(sum_el_e=grid_import_dem,
                                 price_el=spec_cost_el,
                                 sum_gas_e=fuel_boiler + fuel_chp,
                                 price_gas=spec_cost_gas,
                                 sum_el_hp_e=grid_import_hp + grid_import_eh,
                                 price_el_hp=hp_tariff)

        #  Calculate EEG payments on self consumed and produced electricity
        dem_rel_eeg_annuity = self.calc_eeg_self_con(en_chp_self=chp_self,
                                                     en_pv_self=pv_self)

        dem_rel_build = dem_rel_annuity + dem_rel_eeg_annuity

        if save_dem_rel_res:
            build.dem_rel_build = dem_rel_build

        return dem_rel_build

    def calc_lhn_pump_dem_rel_annuity(self):
        """
        Calculate demand related annuity of LHN pump electric consumption

        Returns
        -------
        dem_rel_annuity_pump : float
            Demand related annuity of LHN pump in Euro/a
        """

        #  Get pump_energy from dict_fe_city
        pump_energy = self.energy_balance.dict_fe_city_balance['pump_energy']

        year = self.energy_balance.city.environment.timer.year

        #  Get specific el. cost
        spec_cost_el = self.energy_balance.city.environment.prices. \
            get_spec_el_cost(type='ind',
                             year=year,
                             annual_demand=pump_energy)

        #  Calculate demand related annuity for gas and electricity purchases
        #  (without EEG)
        dem_rel_annuity_pump = self.annuity_obj. \
            calc_dem_rel_annuity(sum_el_e=pump_energy,
                                 price_el=spec_cost_el)

        return dem_rel_annuity_pump

    def calc_dem_rel_annuity_city(self):
        """
        Returns demand related annuity of whole city district

        Returns
        -------
        dem_rel_annuity : float
            Demand related annuity in Euro/a
        """

        dem_rel_annuity = 0

        #  Calculate demand related annuity per building
        for n in self._list_buildings:
            dem_rel_build = self.calc_dem_rel_annuity_building(id=n)

            dem_rel_annuity += dem_rel_build

        # Add demand related annuity of LHN pump
        dem_rel_annuity += self.calc_lhn_pump_dem_rel_annuity()

        return dem_rel_annuity

    def calc_proceeds_annuity_building(self, id, pv_peak_per_area=125):
        """
        Returns annualized proceedings of single building

        Parameters
        ----------
        id : int
            Building id
        pv_peak_per_area : float, optional
            PV peak load per area in W/m2 (default: 125)

        Returns
        -------
        proc_ann_build : float
            Annualized proceedings of single building in Euro/a
        """

        #  Building pointer
        build = self.energy_balance.city.nodes[id]['entity']

        timestep = build.environment.timer.timeDiscretization

        #  Get final energy results dict of building
        dict_fe = build.dict_fe_balance

        #  Final energy in kWh
        fuel_chp = dict_fe['fuel_chp']

        #  Get net electric energy demand results
        dict_el_eb = build.dict_el_eb_res

        #  PV energy
        pv_feed = sum(dict_el_eb['pv_feed']) * timestep / (1000 * 3600)

        #  CHP electric energy
        chp_self = sum(dict_el_eb['chp_self']) * timestep / (1000 * 3600)
        chp_feed = sum(dict_el_eb['chp_feed']) * timestep / (1000 * 3600)

        assert chp_self >= 0, 'chp_self: ' + str(chp_self)
        assert chp_feed >= 0, 'chp_feed: ' + str(chp_feed)

        #  Calculate PV fed-in proceedings
        if build.build_type is None:
            msg = 'build.build_type is None. Assume, that this building is' \
                  ' residential building to estimate specific energy cost.'
            warnings.warn(msg)
            is_res = 'res'
        elif build.build_type == 0:  # Residential
            is_res = True
        else:
            is_res = False

        # Dummy value
        annuity_pv = 0

        if build.hasBes:
            if build.bes.hasPv:
                #  Estimate PV peak load
                pv_peak_load = pv_peak_per_area * build.bes.pv.area

                annuity_pv = self.calc_sub_pv_sold(en_pv_sold=pv_feed,
                                                   pv_peak_load=pv_peak_load,
                                                   is_res=is_res)

        # Dummy values
        annuity_chp_eex_sold = 0
        annuity_chp_sub_sold = 0
        annuity_chp_sub_self = 0
        annuity_chp_tax_return = 0

        #  Check full-load runtime of CHP
        if build.hasBes:
            if build.bes.hasChp:

                p_el_nom = build.bes.chp.pNominal

                assert p_el_nom >= 0

                #  Get maximum subsidies CHP total runtime
                #  (e.g. 30000 or 60000 hours)
                chp_runtime = self.energy_balance.city.environment. \
                    prices.get_max_total_runtime_chp_sub(p_el_nom=p_el_nom)

                #  Calculate average subsidies runtime per year
                chp_runtime_per_year = chp_runtime / self.annuity_obj.time

                #  TODO: Part load?
                chp_runtime_used_per_year = (chp_self + chp_feed) \
                                            * 1000 / p_el_nom

                assert chp_runtime_used_per_year >= 0

                #  If runtime exceeds maximum subsidies runtime, use maximum
                #  subsidies runtime
                if chp_runtime_per_year >= chp_runtime_used_per_year:
                    chp_runtime_sub = chp_runtime_used_per_year + 0.0
                else:
                    chp_runtime_sub = chp_runtime_per_year + 0.0

                assert chp_runtime_sub >= 0
                assert chp_runtime_sub <= 60000 / self.annuity_obj.time

                #  Split runtime to shares of chp sold and chp self energy
                if chp_self != 0 or chp_feed != 0:
                    share_self = chp_self / (chp_self + chp_feed)
                    share_feed = 1 - share_self
                elif chp_self == 0 and chp_feed == 0:
                    share_self = 0
                    share_feed = 0

                assert share_self >= 0
                assert share_feed >= 0

                #  Runtime for sold and self consumed energy
                r_time_self = chp_runtime_sub * share_self
                r_time_feed = chp_runtime_sub * share_feed

                #  Subsidies amount of electric energy in kWh
                chp_en_self = r_time_self * p_el_nom / 1000
                chp_en_feed = r_time_feed * p_el_nom / 1000

                assert chp_en_self >= 0
                assert chp_en_feed >= 0

                #  Calc. EEX and grid avoidance payment for chp fed-in
                annuity_chp_eex_sold = self.calc_chp_sold(en_chp_sold=chp_feed)

                assert annuity_chp_eex_sold >= 0

                #  Calculate CHP sold subsidies, depending on size and
                #  maximum runtime
                annuity_chp_sub_sold = self. \
                    calc_sub_chp_el_sold(en_chp_sold=chp_en_feed,
                                         pnominal=p_el_nom)

                assert annuity_chp_sub_sold >= 0

                #  Calculate CHP self subsidies, depending on size and
                #  maximum runtime
                annuity_chp_sub_self = self. \
                    calc_sub_chp_el_used(en_chp_used=chp_en_self,
                                         pnominal=p_el_nom)

                assert annuity_chp_sub_self >= 0

                #  Calc CHP tax return
                annuity_chp_tax_return = self. \
                    calc_sub_chp_gas_used(gas_chp_used=fuel_chp)

                assert annuity_chp_tax_return >= 0

        # Sum up proceeding related annuities
        annuity_proceeds = annuity_pv + annuity_chp_eex_sold \
                           + annuity_chp_sub_sold + annuity_chp_sub_self \
                           + annuity_chp_tax_return

        return annuity_proceeds

    def calc_proceeds_annuity_city(self):
        """
        Returns annualized proceedings of city

        Returns
        -------
        proc_ann : float
            Annualized proceedings of city in Euro/a
        """

        proc_ann = 0

        for n in self._list_buildings:
            proc_ann_build = self.calc_proceeds_annuity_building(id=n)

            proc_ann += proc_ann_build

        return proc_ann

    def calc_eeg_self_con(self, en_chp_self, en_pv_self):
        """
        Calculate annuity EEG payment on self-produced and consumed electric
        energy of PV and CHP systems

        Parameters
        ----------
        en_chp_self : float
            Amount of self-produced and consumed el. energy of CHP in kWh/a
        en_pv_self : float
            Amount of self-produced and consumed el. energy of PV in kWh/a

        Returns
        -------
        eeg_payment : float
            Annualized EEG payment in Euro/a
        """

        #  TODO: Add function to check if prices object is GermanMarket

        #  Pointers to price dynamic factors
        b_eeg_chp = self.annuity_obj.price_dyn_eeg_chp
        b_eeg_pv = self.annuity_obj.price_dyn_eeg_pv

        eeg_chp = \
            self.energy_balance.city.environment. \
                prices.get_eeg_payment(type='chp')
        eeg_pv = \
            self.energy_balance.city.environment. \
                prices.get_eeg_payment(type='pv')

        # Calculate EEG payment
        eeg_payment = b_eeg_chp * en_chp_self * eeg_chp \
                      + b_eeg_pv * en_pv_self * eeg_pv

        return eeg_payment * self.annuity_obj.ann_factor

    def calc_chp_sold(self, en_chp_sold):
        """
        Calculate specific incomes : EEX baseload price and avoided grid-usage
        fee (without CHP subsidies)

        Parameters
        ----------
        en_chp_sold : float
            Amount of sold el. energy of CHP in kWh/a

        Returns
        -------
        sub_payment_chp_sold : float
            Annualized specific incomes for chp related to sold electric
            energy in Euro/a
        """

        #  TODO: Add function to check if prices object is GermanMarket

        #  Pointers to price dynamic factors
        b_avoid_grid_usage = self.annuity_obj.price_dyn_grid_use
        b_eex_base = self.annuity_obj.price_dyn_eex

        #  Calc. average EEX baseload
        sub_eex = sum(
            self.energy_balance.city.environment.prices.eex_baseload) / len(
            self.energy_balance.city.environment.prices.eex_baseload)
        #  Get grid usage avoidance fee
        sub_avoid_grid_use = self.energy_balance.city.environment. \
            prices.grid_av_fee

        # Calculate specific incomes [EUro/kWh]
        payment_chp_sold = (b_avoid_grid_usage * sub_avoid_grid_use
                            + b_eex_base * sub_eex) * en_chp_sold

        return payment_chp_sold * self.annuity_obj.ann_factor

    def calc_sub_chp_el_sold(self, en_chp_sold, pnominal):
        """
        Calculate proceeding related annuity for subsidies on sold
        CHP electric energy

        Parameters
        ----------
        en_chp_sold : float
            Produced and sold electric energy of CHP in kWh
        pnominal : float
            Nominal electric power of CHP system in Watt

        Returns
        -------
        annuity_chp_sub : float
            Annualized proceedings of subsidies for sold electric energy of
            CHP in Euro/a
        """

        assert en_chp_sold >= 0
        assert pnominal > 0

        #  Pointers to price dynamic factors
        b_chp_sub = self.annuity_obj.price_dyn_chp_sub

        #  Calculate specific subsidy payment in Euro/kWh
        spec_chp_sub = self.energy_balance.city.environment. \
            prices.get_sub_chp(p_nom=pnominal)

        annuity_chp_sub = b_chp_sub * spec_chp_sub * en_chp_sold * \
                          self.annuity_obj.ann_factor

        return annuity_chp_sub

    def calc_sub_chp_el_used(self, en_chp_used, pnominal):
        """
        Calculate specific incomes for CHP related to the amount of
        electricity used to cover the own demand

        Parameters
        ----------
        en_chp_used : float
            Amount of used el. energy of CHP to cover the own demand in kWh/a
        pnominal : int
            Nominal electrical CHP power in W

        Returns
        -------
        sub_payment_chp_used : float
            Annualized specific incomes for chp refered to used electric
            energy in Euro/a
        """

        #  TODO: Add function to check if prices object is GermanMarket

        #  Pointers to price dynamic factors
        b_chp_sub_used = self.annuity_obj.price_dyn_chp_self

        # Get specific price
        sub_chp_self = self.energy_balance.city.environment. \
            prices.get_sub_chp_self(
            p_nom=pnominal)

        # Calculate specific income [Euro/kWh]
        sub_payment_chp_used = b_chp_sub_used * sub_chp_self * en_chp_used

        return sub_payment_chp_used * self.annuity_obj.ann_factor

    def calc_sub_chp_gas_used(self, gas_chp_used):
        """
        Calculate a tax exception on gas for the CHP related to the amount
        of gas used

        Parameters
        ----------
        gas_chp_used : float
            Amount of used gas energy of CHP in kWh/a

        Returns
        -------
        tax_exep_chp_used : float
            Annualized specific incomes for chp refered to used gas energy
            in Euro/a
        """

        #  TODO: Add function to check if prices object is GermanMarket

        #  Pointers to price dynamic factors
        b_chp_sub_used = self.annuity_obj.price_dyn_chp_tax_return

        # Get specific price
        tax_exep_chp = self.energy_balance.city.environment. \
            prices.chp_tax_return

        # Calculate specific income [Euro/kWh]
        tax_exep_chp_used = b_chp_sub_used * tax_exep_chp * gas_chp_used

        return tax_exep_chp_used * self.annuity_obj.ann_factor

    def calc_sub_pv_sold(self, en_pv_sold=None, pv_peak_load=None,
                         is_res=True):
        """
        Specific income referred to State subsidies, which are related to the
        amount of electricity sold

        Parameters
        ----------
        en_pv_sold : float
            Amount of sold el. energy of PV  in kWh/a
        pv_peak_load : float
            PV peak load in Watt
        is_res : bool, optional
            Defines, if PV is installed on residential building (default: True)
            If True, PV is installed on residential building.
            If False, PV is installed on non-residential building with
            lower subsidies.

        Returns
        -------
        sub_pv_sold : float
            Annualized specific incomes for pv refered to sold electric
            energy in Euro/a
        """

        #  TODO: Add function to check if prices object is GermanMarket

        #  Pointers to price dynamic factors
        b_pv_sub_sold = self.annuity_obj.price_dyn_pv_sub

        # Get specific price
        pv_sub_sold = self.energy_balance.city.environment.prices.get_sub_pv(
            pv_peak_load=pv_peak_load, is_res=is_res)

        # Calculate specific income [Euro/kWh]
        sub_pv_sold = b_pv_sub_sold * pv_sub_sold * en_pv_sold

        return sub_pv_sold * self.annuity_obj.ann_factor

    def perform_overall_energy_balance_and_economic_calc(self, run_mc=False,
                                                         dict_samples_const=None,
                                                         dict_samples_esys=None,
                                                         run_idx=None,
                                                         eeg_pv_limit=False,
                                                         sampling_method=None,
                                                         dict_city_sample_lhc=None,
                                                         dict_build_samples_lhc=None
                                                         ):
        """
        Script runs energy balance and annuity calculation for city in
        energy_balance object

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
        dict_samples_esys : dict (of dicts)
            Dictionary holding dictionaries with energy system sampling
            data for MC run (default: None)
            dict_samples_esys['<building_id>'] = dict_esys
            (of building with id <building_id>)
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
        dict_build_samples_lhc : dict, optional
            Dict. holding building ids as keys and dict of samples as
            values (default: None).
            These dicts hold paramter names as keys and numpy arrays with
            samples as dict values.  Only
            relevant if mc_run is True and sampling_method == 'lhc'

        Returns
        -------
        res_tuple : tuple (of floats)
            Results tuple (annuity, co2) with
            annuity : float
                Annuity in Euro/a
            co2 : float
                Emissions in kg/a
        """

        if run_mc and sampling_method is 'random':
            if dict_samples_const is None or dict_samples_esys is None:
                msg = 'Sample dicts. cannnot be None, if' \
                      ' you want to perform Monte-Carlo analysis.'
                raise AssertionError(msg)
            if run_idx is None:
                msg = 'Index value run_idx cannnot be None, if' \
                      ' you want to perform Monte-Carlo analysis.'
                raise AssertionError(msg)

        if run_mc and sampling_method is 'lhc':
            if dict_city_sample_lhc is None or dict_build_samples_lhc is None:
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

        # ##################################################################
        #  Run energy balance
        #  ##################################################################

        #  Calc. city energy balance
        self.energy_balance. \
            calc_city_energy_balance(run_mc=run_mc,
                                     dict_samples_const=
                                     dict_samples_const,
                                     run_idx=run_idx,
                                     eeg_pv_limit=eeg_pv_limit,
                                     sampling_method=sampling_method,
                                     dict_city_sample_lhc=dict_city_sample_lhc)

        #  Perform final energy anaylsis
        self.energy_balance.calc_final_energy_balance_city()

        #  Perform emissions calculation
        co2 = self.energy_balance.calc_co2_emissions(
            el_mix_for_chp=True)

        #  ##################################################################
        #  Perform economic calculations
        #  ##################################################################

        #  Calculate capital and operation related annuity
        (cap_rel_ann, op_rel_ann) = \
            self.calc_cap_and_op_rel_annuity_city(run_mc=run_mc,
                                                  dict_samples_const=
                                                  dict_samples_const,
                                                  dict_samples_esys=
                                                  dict_samples_esys,
                                                  run_idx=run_idx,
                                                  sampling_method=
                                                  sampling_method,
                                                  dict_city_sample_lhc=
                                                  dict_city_sample_lhc,
                                                  dict_build_samples_lhc=
                                                  dict_build_samples_lhc
                                                  )

        #  Calculate demand related annuity
        dem_rel_annuity = self.calc_dem_rel_annuity_city()

        #  Calculate proceedings
        proc_rel_annuity = self.calc_proceeds_annuity_city()

        #  Calculate total annuity
        annuity = self.annuity_obj. \
            calc_total_annuity(ann_capital=cap_rel_ann,
                               ann_demand=dem_rel_annuity,
                               ann_op=op_rel_ann,
                               ann_proc=proc_rel_annuity)

        return (annuity, co2)


if __name__ == '__main__':

    import pycity_calc.cities.scripts.city_generator.city_generator as citygen
    import pycity_calc.cities.scripts.overall_gen_and_dimensioning as overall

    this_path = os.path.dirname(os.path.abspath(__file__))

    #  Check requirements for pycity_deap
    pycity_deap = False

    eeg_pv_limit = False

    try:
        #  Try loading city pickle file
        filename = 'city_clust_simple_with_esys.pkl'
        file_path = os.path.join(this_path, 'inputs', filename)
        city = pickle.load(open(file_path, mode='rb'))

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
        #  Choice of Anex 42 profiles NOT recommended for multiple builings,
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

        txt_path = os.path.join(this_path, 'inputs', filename)

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
        log_path = os.path.join(this_path, 'inputs',
                                'city_gen_overall_log.txt')

        #  Generate street networks
        gen_str = True  # True - Generate street network

        #  Street node and edges input filenames
        str_node_filename = 'street_nodes_cluster_simple.csv'
        str_edge_filename = 'street_edges_cluster_simple.csv'

        #  Load street data from csv
        str_node_path = os.path.join(this_path, 'inputs',
                                     str_node_filename)
        str_edge_path = os.path.join(this_path, 'inputs',
                                     str_edge_filename)

        #  Add energy networks to city
        gen_e_net = True  # True - Generate energy networks

        #  Path to energy network input file (csv/txt; tab separated)
        network_filename = 'city_clust_simple_networks.txt'
        network_path = os.path.join(this_path, 'inputs',
                                    network_filename)

        #  Add energy systems to city
        gen_esys = True  # True - Generate energy networks

        #  Path to energy system input file (csv/txt; tab separated)
        esys_filename = 'city_clust_simple_enersys.txt'
        esys_path = os.path.join(this_path, 'inputs',
                                 esys_filename)

        #  #----------------------------------------------------------------------

        #  Load district_data file
        district_data = citygen.get_district_data_from_txt(txt_path)

        city = overall.run_overall_gen_and_dim(timestep=timestep,
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

        # Save new pickle file
        filename = 'city_clust_simple_with_esys.pkl'
        file_path = os.path.join(this_path, 'input', filename)
        pickle.dump(city, open(file_path, mode='wb'))

    # #####################################################################
    #  Generate object instances
    #  #####################################################################

    #  Generate german market instance
    ger_market = gmarket.GermanMarket()

    #  Add GermanMarket object instance to city
    city.environment.prices = ger_market

    #  Generate annuity object instance
    annuity_obj = annu.EconomicCalculation()

    #  Generate energy balance object for city
    energy_balance = citeb.CityEBCalculator(city=city)

    city_eco_calc = CityAnnuityCalc(annuity_obj=annuity_obj,
                                    energy_balance=energy_balance)

    #  #####################################################################
    #  Run energy balance
    #  #####################################################################

    #  Calc. city energy balance
    city_eco_calc.energy_balance. \
        calc_city_energy_balance(eeg_pv_limit=eeg_pv_limit)

    #  Perform final energy anaylsis
    dict_fe_city = \
        city_eco_calc.energy_balance.calc_final_energy_balance_city()

    #  Perform emissions calculation
    co2 = city_eco_calc.energy_balance.calc_co2_emissions(el_mix_for_chp=True)

    #  #####################################################################
    #  Perform economic calculations
    #  #####################################################################

    #  Calculate capital and operation related annuity
    (cap_rel_ann, op_rel_ann) = \
        city_eco_calc.calc_cap_and_op_rel_annuity_city()

    #  Calculate demand related annuity
    dem_rel_annuity = city_eco_calc.calc_dem_rel_annuity_city()

    #  Calculate proceedings
    proc_rel_annuity = city_eco_calc.calc_proceeds_annuity_city()

    #  Calculate total annuity
    total_annuity = city_eco_calc.annuity_obj. \
        calc_total_annuity(ann_capital=cap_rel_ann,
                           ann_demand=dem_rel_annuity,
                           ann_op=op_rel_ann,
                           ann_proc=proc_rel_annuity)

    print('Capital related annuity in Euro/a:')
    print(round(cap_rel_ann, 0))
    print()

    print('Demand related annuity in Euro/a:')
    print(round(dem_rel_annuity, 0))
    print()

    print('Operations related annuity in Euro/a:')
    print(round(op_rel_ann, 0))
    print()

    print('Proceedings related annuity in Euro/a:')
    print(round(proc_rel_annuity, 0))
    print()

    print('##########################################')
    print()

    print('CO2 emissions in kg/a:')
    print(round(co2, 0))
    print()

    print('Total annuity in Euro/a:')
    print(round(total_annuity, 0))
    print()
