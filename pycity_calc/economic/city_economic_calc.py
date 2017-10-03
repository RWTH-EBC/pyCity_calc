#!/usr/bin/env python
# coding=utf-8
"""
Script to calculate annuities of city district
"""
from __future__ import division
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


class CityAnnuityCalc():
    def __init__(self, annuity_obj, city_eb_obj):
        """
        Constructor of CityAnnuityCalc object instance

        Parameters
        ----------
        annuity_obj : object
            Annuity object of pyCity_calc
        city_eb_obj : object
            City energy balance object of pyCity_calc
        """

        self.annuity_obj = annuity_obj
        self.city_eb_obj = city_eb_obj

    def calc_cap_rel_annuity_city(self):
        """
        Calculate sum of all capital related annuities of city
    
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

        cap_rel_ann = 0  # Dummy value for capital-related annuity
        list_invest = []  # Dummy list to store investment cost
        list_type = []  # Dummy list to store type of component

        #  Get capital-related annuities per energy system unit
        #  ###################################################################
        for n in self.city_eb_obj.city.nodes():
            if 'node_type' in self.city_eb_obj.city.node[n]:
                #  If node_type is building
                if self.city_eb_obj.city.node[n]['node_type'] == 'building':
                    #  If entity is kind building
                    if self.city_eb_obj.city.node[n][
                        'entity']._kind == 'building':
                        build = self.city_eb_obj.city.node[n]['entity']
                        if build.hasBes:
                            #  BES pointer
                            bes = build.bes

                            if bes.hasBattery:
                                cap_kWh = bes.battery.capacity / (3600 * 1000)
                                #  In kWh
                                bat_invest = \
                                    bat_cost.calc_invest_cost_bat(cap=cap_kWh)
                                cap_rel_ann += \
                                    self.annuity_obj.calc_capital_rel_annuity_with_type(
                                        invest=bat_invest, type='BAT')
                                #  Add to lists
                                list_invest.append(bat_invest)
                                list_type.append('BAT')

                            if bes.hasBoiler:
                                q_nom = bes.boiler.qNominal / 1000  # in kW
                                boil_invest = \
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
                                chp_invest = \
                                    chp_cost.calc_invest_cost_chp(p_el_nom=
                                                                  p_el_nom)
                                cap_rel_ann += \
                                    self.annuity_obj.calc_capital_rel_annuity_with_type(
                                        invest=chp_invest, type='CHP')
                                #  Add to lists
                                list_invest.append(chp_invest)
                                list_type.append('CHP')

                            if bes.hasElectricalHeater:
                                q_eh = \
                                    bes.electricalHeater.qNominal / 1000  # in kW
                                eh_invest = \
                                    eh_cost.calc_abs_cost_eh(q_nom=q_eh)
                                cap_rel_ann += \
                                    self.annuity_obj.calc_capital_rel_annuity_with_type(
                                        invest=eh_invest, type='EH')
                                #  Add to lists
                                list_invest.append(eh_invest)
                                list_type.append('EH')

                            if bes.hasHeatpump:
                                q_hp = bes.heatpump.qNominal / 1000  # in kW
                                hp_invest = \
                                    hp_cost.calc_invest_cost_hp(q_nom=q_hp)
                                cap_rel_ann += \
                                    self.annuity_obj.calc_capital_rel_annuity_with_type(
                                        invest=hp_invest, type='HP')
                                #  Add to lists
                                list_invest.append(hp_invest)
                                list_type.append('HP')

                            if bes.hasPv:
                                pv_area = bes.pv.area
                                pv_invest = pv_cost.calc_pv_invest(
                                    area=pv_area)
                                cap_rel_ann += \
                                    self.annuity_obj.calc_capital_rel_annuity_with_type(
                                        invest=pv_invest, type='PV')
                                #  Add to lists
                                list_invest.append(pv_invest)
                                list_type.append('PV')

                            if bes.hasTes:
                                tes_vol = bes.tes.capacity / 1000  # in m3
                                tes_invest = \
                                    tes_cost.calc_invest_cost_tes(
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
                city=self.city_eb_obj.city,
                network_type='heating')

        #  Add weights to edges
        netop.add_weights_to_edges(self.city_eb_obj.city)

        #  If LHN networks exist
        if len(list_lhn_con) > 0:

            invest_lhn_pipe = 0
            invest_lhn_trans = 0

            #  Loop over each connected lhn network
            for sublist in list_lhn_con:

                #  Todo: Probably need to define thermal demand independent
                #  Todo: way to calculate cost of transmission station, as
                #  Todo: thermal power might change in monte carlo run

                list_th_pow = []

                #  Get max. power values of all buildings connected to lhn
                for n in self.city_eb_obj.city.nodes():
                    if 'node_type' in self.city_eb_obj.city.node[n]:
                        #  If node_type is building
                        if self.city_eb_obj.city.node[n][
                            'node_type'] == 'building':
                            #  If entity is kind building
                            if self.city_eb_obj.city.node[n][
                                'entity']._kind == 'building':
                                build = self.city_eb_obj.city.node[n]['entity']
                                th_pow = \
                                    dimfunc.get_max_power_of_building(build,
                                                                      with_dhw=False)
                                list_th_pow.append(
                                    th_pow / 1000)  # Convert W to kW

                # Calculate investment cost for lhn transmission stations
                invest_lhn_trans += \
                    lhn_cost.calc_invest_cost_lhn_stations(
                        list_powers=list_th_pow)

                #  Add to lists
                list_invest.append(invest_lhn_trans)
                list_type.append('LHN_station')

                #  Loop over every heating pipe and calculate cost
                for u in sublist:
                    for v in sublist:
                        if self.city_eb_obj.city.has_edge(u, v):
                            if 'network_type' in self.city_eb_obj.city.edge[u][
                                v]:
                                if (self.city_eb_obj.city.edge[u][v][
                                        'network_type'] == 'heating' or
                                            self.city_eb_obj.city.edge[u][v][
                                                'network_type'] == 'heating_and_deg'):
                                    #  Pointer to pipe (edge)
                                    pipe = self.city_eb_obj.city.edge[u][v]
                                    d_i = pipe['d_i']
                                    length = pipe['weight']
                                    invest_lhn_pipe += \
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
                city=self.city_eb_obj.city,
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
                for n in self.city_eb_obj.city.nodes():
                    if 'node_type' in self.city_eb_obj.city.node[n]:
                        #  If node_type is building
                        if self.city_eb_obj.city.node[n][
                            'node_type'] == 'building':
                            #  If entity is kind building
                            if self.city_eb_obj.city.node[n][
                                'entity']._kind == 'building':
                                nb_build += 1

                deg_len = 0
                deg_len_w_lhn = 0

                #  Loop over every deg pipe and calculate cost
                for u in sublist:
                    for v in sublist:
                        if self.city_eb_obj.city.has_edge(u, v):
                            if 'network_type' in self.city_eb_obj.city.edge[u][
                                v]:
                                if self.city_eb_obj.city.edge[u][v][
                                    'network_type'] == 'electricity':
                                    deg_len += \
                                    self.city_eb_obj.city.edge[u][v]['weight']
                                elif self.city_eb_obj.city.edge[u][v][
                                    'network_type'] == 'heating_and_deg':
                                    deg_len_w_lhn += \
                                    self.city_eb_obj.city.edge[u][v]['weight']

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

    def calc_cap_and_op_rel_annuity_city(self):
        """
        Calculate capital- and operation-related annuities of city
    
        Parameters
        ----------
        city : object
            City object
        eco_calc : object
            EconomicCalculation object of pycity_calc
    
        Returns
        -------
        tup_ann : tuple (of floats)
            Tuple with capital- and operation-related annuities (floats) in Euro
            (cap_rel_ann, op_rel_ann)
        """

        #  Calculate capital-related annuities
        (cap_rel_ann, list_invest, list_type) = \
            self.calc_cap_rel_annuity_city()

        #  Calculate operation-related annuity
        op_rel_ann = \
            self.annuity_obj.calc_op_rel_annuity_multi_comp(
                list_invest=list_invest,
                list_types=list_type)

        return (cap_rel_ann, op_rel_ann)

    # def calc_dem_rel_annuity_city (self):
    #     """
    #     In the city object the energy parameters are calculated in [W] and
    #     the time is calculated in [s], so it is
    #     necessary divided by (3600*1000) in order to get the [kWh] as unit.
    #
    #     Attention to the el/gas price, in fact there are 2 different values
    #     depending on the building type
    #     (residential or industrial).
    #
    #     Distinction between electricity for heating pump and electricity for
    #     daily life: different tariff
    #
    #     Returns
    #     -------
    #     dem_rel_annuity : float
    #         Demand related annuity in Euro/a
    #     """
    #     gas_dem = 0
    #     dem_rel_annuity = 0
    #     el_price = 0
    #     gas_price = 0
    #     curr_el_dem_normal = np.zeros(len(city_object.environment.timer.time_vector()))
    #     curr_el_dem_hp = np.zeros(len(city_object.environment.timer.time_vector()))
    #
    #
    #     for n in city_object.nodes():
    #         if 'node_type' in city_object.node[n]:
    #             #  If node_type is building
    #             if city_object.node[n]['node_type'] == 'building':
    #                 #  If entity is kind building
    #                 if city_object.node[n]['entity']._kind == 'building':
    #
    #                     if 'electrical demand normal usage' in city_object.node[n]:
    #                         el_dem_normal = city_object.node[n]['electrical demand normal usage']
    #                         # Sum power curve to obtain total energy demand in kWh
    #                         curr_el_dem_normal = sum(el_dem_normal)\
    #                                              * city_object.environment.timer.timeDiscretization / 1000 / 3600
    #
    #                     if 'fuel demand' in city_object.node[n]:
    #                         gas_dem = sum(city_object.node[n]['fuel demand'])\
    #                                   *city_object.environment.timer.timeDiscretization /1000 /3600
    #
    #                     if 'electrical demand hp' in city_object.node[n]:
    #                         el_dem_hp = city_object.node[n]['electrical demand hp']
    #                         curr_el_dem_hp = sum(el_dem_hp) * city_object.environment.timer.timeDiscretization / 1000 / 3600
    #
    #                     # residential building
    #                     if city_object.node[n]['entity'].build_type == 0:
    #                         el_price = self.germanmarket.get_spec_el_cost('res', city_object.environment.timer.year,
    #                                                                       curr_el_dem_normal)
    #                         gas_price = self.germanmarket.get_spec_gas_cost('res', city_object.environment.timer.year,
    #                                                                         gas_dem)
    #
    #                     # industrial building
    #                     elif city_object.node[n]['entity'].build_type != 0:
    #                         el_price = self.germanmarket.get_spec_el_cost('ind', city_object.environment.timer.year,
    #                                                                     curr_el_dem_normal)
    #                         gas_price =self.germanmarket.get_spec_gas_cost('ind', city_object.environment.timer.year,
    #                                                                       gas_dem)
    #                     # special price for el. hp
    #                     price_el_hp = self.germanmarket.hp_day_tarif
    #                     # TODO: hp_price night and hp_price_day difference
    #
    #                     # Add to final demand counter
    #                     #dem_rel_annuity += price_el_hp*curr_el_dem_hp
    #
    #                     dem_rel_annuity += self.calc_dem_rel_annuity(sum_el_e=curr_el_dem_normal, sum_gas_e=gas_dem,
    #                                                                 price_el=el_price, price_gas=gas_price,
    #                                                                 price_el_hp=price_el_hp, sum_el_hp_e=curr_el_dem_hp)
    #
    #     return dem_rel_annuity

    def calc_eeg_self_con(self, en_chp_self=0, en_pv_self=0):
        """
        Calculate EEG payment on self-produced and consumed electric energy of
        PV and CHP systems

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
        b_eeg_chp = self.price_dyn_eeg_chp
        b_eeg_pv = self.price_dyn_eeg_pv

        eeg_chp = \
            self.city_eb_obj.city.environment.prices.get_eeg_payment(type='chp')
        eeg_pv = \
            self.city_eb_obj.city.environment.prices.get_eeg_payment(type='pv')

        # Calculate EEG payment
        eeg_payment = b_eeg_chp * en_chp_self * eeg_chp \
                      + b_eeg_pv * en_pv_self * eeg_pv

        return eeg_payment * self.ann_factor

    def calc_sub_chp_sold(self, en_chp_sold=None, pnominal=None):
        """
        Calculate specific incomes : EEX baseload price, avoided grid-usage
        fee, chp subsidies by the state
        related to the amount of electricity sold for CHP

        Parameters
        ----------
        en_chp_sold : float
            Amount of sold el. energy of CHP in kWh/a
        pnominal : int
            Nominal electrical CHP power in W

        Returns
        -------
        sub_payment_chp_sold : float
            Annualized specific incomes for chp refered to sold electric
            energy in Euro/a
        """

        #  TODO: Add function to check if prices object is GermanMarket

        #  Pointers to price dynamic factors
        b_chp_sub = self.price_dyn_chp_sub
        b_avoid_grid_usage = self.price_dyn_grid_use
        b_eex_base = self.price_dyn_eex

        # Get specific prices
        sub_chp_sold = self.city_eb_obj.city.environment.prices.get_sub_chp(p_nom=pnominal)
        #  Todo: Consider adding one EEX price?
        sub_eex = sum(self.city_eb_obj.city.environment.prices.eex_baseload) / len(
            self.city_eb_obj.city.environment.prices.eex_baseload)
        sub_avoid_grid_use = self.city_eb_obj.city.environment.prices.grid_av_fee

        # Calculate specific incomes [EUro/kWh]
        sub_payment_chp_sold = (b_chp_sub * sub_chp_sold
                                + b_avoid_grid_usage * sub_avoid_grid_use
                                + b_eex_base * sub_eex) * en_chp_sold

        return sub_payment_chp_sold * self.ann_factor

    def calc_sub_chp_el_used(self, en_chp_used=None, pnominal=None):
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
        b_chp_sub_used = self.price_dyn_chp_self

        # Get specific price
        sub_chp_sold = self.city_eb_obj.city.environment.prices.get_sub_chp_self(p_nom=pnominal)

        # Calculate specific income [Euro/kWh]
        sub_payment_chp_used = b_chp_sub_used*sub_chp_sold*en_chp_used

        return sub_payment_chp_used * self.ann_factor

    def calc_sub_chp_gas_used(self, en_chp_used=None):
        """
        Calculate a tax exception on gas for the CHP related to the amount
        of gas used

        Parameters
        ----------
        en_chp_used : float
            Amount of used gas energy of CHP in kWh/a

        Returns
        -------
        tax_exep_chp_used : float
            Annualized specific incomes for chp refered to used gas energy
            in Euro/a
        """

        #  TODO: Add function to check if prices object is GermanMarket

        #  Pointers to price dynamic factors
        b_chp_sub_used = self.price_dyn_chp_tax_return

        # Get specific price
        tax_exep_chp = self.city_eb_obj.city.environment.prices.chp_tax_return

        # Calculate specific income [Euro/kWh]
        tax_exep_chp_used = b_chp_sub_used*tax_exep_chp*en_chp_used

        return tax_exep_chp_used * self.ann_factor

    def calc_sub_pv_sold(self, en_pv_sold=None, pv_peak_load=None, is_res=True):
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
        b_pv_sub_sold = self.price_dyn_pv_sub

        # Get specific price
        pv_sub_sold = self.city_eb_obj.city.environment.prices.get_sub_pv(pv_peak_load=pv_peak_load, is_res=is_res)

        # Calculate specific income [Euro/kWh]
        sub_pv_sold = b_pv_sub_sold*pv_sub_sold*en_pv_sold

        return sub_pv_sold * self.ann_factor

    # def calc_proc_annuity_multi_comp_city(self, city_object):
    #
    #     """
    #
    #         Parameters
    #         ----------
    #         city_object: object from pycity_calc
    #         City object from pycity_calc holding list of sold and used energy
    #
    #     Returns
    #         -------
    #         proc_annuity : float
    #             Annuity of proceedings for multi components in Euro
    #
    #
    #     Comment:
    #
    #         The proceedings realities annuity has to be calculated for the PV and CHP taking in account all the several
    #         specific incomes existing for each one of them.
    #
    #
    #         For the CHP proceedings there are 4 different specific_income and each one of them is related to a type
    #         of energy:
    #
    #             - Tax referred to the EEG-Umlage (fee for specific share), which is related to the amount of own electricity
    #               consumed: proc_rel_annuity_chp1;
    #
    #             - Specific incomes (EEX baseload price + avoided grid-usage fee + chp subsidy by the state(CHP law 2016))
    #               referred to State subsidies, which are related to the amount of electricity sold: proc_rel_annuity_chp2;
    #
    #             - Specific income referred to a subsidy payment for CHP el. energy, which is related to the amount of
    #               electricity used to cover the own demand: proc_rel_annuity_chp3;
    #
    #             - Specific income referred to a tax exception on gas for the CHP, which is related to the amount of
    #               gas energy used by the CHP: proc_rel_annuity_chp4;
    #
    #
    #         For the PV proceedings there are 2 different specific_income:
    #
    #             - Tax referred to the EEG-Umlage (fee for specific share), which is related to the amount of own electricity
    #               consumed: proc_rel_annuity_pv1;
    #
    #             - Specific income referred to State subsidies, which are related to the amount of electricity sold:
    #               proc_rel_annuity_pv2.
    #
    #     """
    #
    #     # initialisation
    #     total_proc_annuity = 0
    #
    #     for n in city_object.nodes():
    #         if 'node_type' in city_object.node[n]:
    #             #  If node_type is building
    #             if city_object.node[n]['node_type'] == 'building':
    #                 #  If entity is kind building
    #                 if city_object.node[n]['entity']._kind == 'building':
    #                     build = city_object.node[n]['entity']
    #                     if build.hasBes:
    #                         #  BES pointer
    #                         bes = build.bes
    #
    #                         if bes.hasChp:
    #
    #                             # ## Tax referred to the EEG-Umlage
    #                             # electricity self consumed [kWh]
    #                             en_chp_self = sum(city_object.node[n]['chp_used_self']) * city_object.environment.\
    #                                 timer.timeDiscretization / 1000 / 3600
    #
    #                             # Specific income[€/kWh]el
    #                             proc_rel_annuity_chp1 = self.calc_eeg_self_con(en_chp_self=en_chp_self)
    #
    #                             # ## Specific incomes : EEX baseload price + avoided grid-usage fee # + chp subsidy
    #                             # CHP law 2016
    #                             # electricity sold [kWh]
    #                             en_chp_sold= sum(city_object.node[n]['chp_sold'])* city_object.environment.\
    #                                 timer.timeDiscretization / 1000 / 3600
    #                             # Specific income[€/kWh]el
    #                             proc_rel_annuity_chp2 = self.calc_sub_chp_sold(en_chp_sold=en_chp_sold,
    #                                                                            pnominal=bes.chp.pNominal)
    #
    #                             # ## Specific income referred to a subsidy payment for CHP el. energy used to cover
    #                             #  the own demand
    #
    #                             # electricity consumed [kWh]
    #                             en_chp_used = sum(city_object.node[n]['chp_used_self']) * city_object.environment.\
    #                                 timer.timeDiscretization / 1000 / 3600
    #                             # Specific income[€/kWh]el
    #                             proc_rel_annuity_chp3 = self.calc_sub_chp_el_used(en_chp_used=en_chp_used,
    #                                                                               pnominal=bes.chp.pNominal)
    #
    #                             # ## Specific income tax exception on gas for the CHP [€/kWh]th
    #                             # gas consumed [kWh]
    #                             en_gas_used=sum(city_object.node[n]['entity'].bes.chp.array_fuel_power) *\
    #                                         city_object.environment.timer.timeDiscretization / 1000 / 3600
    #                             # Specific income[€/kWh]th
    #                             proc_rel_annuity_chp4 = self.calc_sub_chp_gas_used(en_chp_used=en_gas_used)
    #
    #                             # Sum of all proc_annuity for this building
    #                             proc_rel_annuity = - proc_rel_annuity_chp1 + proc_rel_annuity_chp2 +\
    #                                                proc_rel_annuity_chp3 + proc_rel_annuity_chp4
    #
    #                             # Add building proc annuity to total proc_annuity for the city
    #                             total_proc_annuity += proc_rel_annuity
    #
    #                         if bes.hasPv:
    #
    #                             # ## Tax referred to the EEG-Umlage
    #                             # Total peak power
    #                             peak_power_pv = bes.pv.area * 1000
    #
    #                             if peak_power_pv >= 10000:
    #                                 # electricity self consumed [kWh]
    #                                 en_pv_con = sum( city_object.node[n]['pv_used_self']) * city_object.environment.\
    #                                     timer.timeDiscretization / 1000 / 3600
    #                                 # Specific income[€/kWh]el
    #                                 proc_rel_annuity_pv1 = self.calc_eeg_self_con(en_pv_self=en_pv_con)
    #                             else:
    #                                 proc_rel_annuity_pv1 = 0
    #
    #                             # Specific income [€/kWh]el
    #                             # subsidy payments depend on installed peak power. According to EEG 2017
    #                             peak_power_pv = bes.pv.area * 1000
    #                             # electricity sold [kWh]
    #                             pv_sold = sum(city_object.node[n]['pv_sold']) * city_object.environment.\
    #                                 timer.timeDiscretization / 1000 / 3600
    #
    #                             # Define building type
    #                             if build.build_type == 0:
    #                                 is_res = True
    #                             else:
    #                                 is_res = False
    #
    #                             # Specific income [€/kWh]el
    #                             proc_rel_annuity_pv2 = self.calc_sub_pv_sold(en_pv_sold=pv_sold,
    #                                                                          pv_peak_load=peak_power_pv, is_res=is_res)
    #
    #                             # Sum of all proc_annuity for this building
    #                             proc_rel_annuity = - proc_rel_annuity_pv1 + proc_rel_annuity_pv2
    #
    #                             # Add building proc annuity to total proc_annuity for the city
    #                             total_proc_annuity += proc_rel_annuity
    #
    #     return total_proc_annuity
