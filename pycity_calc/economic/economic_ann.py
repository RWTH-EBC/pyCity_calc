#!/usr/bin/env python
# coding=utf-8
"""
Script to calculate annuities of city district

Comment:
    In this Script are implemented 4 methods able to calculate the total annuity of a city district.
    The attributes city_object and eco_calc are passed to each methods and permit to get the POWER ENERGY
    parameters [kWh/y] and the ECONOMIC parameters [€/kWh]; combining these two is possible to get the variables
    necessary to calculate the total annuity [€/y].
"""
from __future__ import division
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

import pycity_calc.environments.market as mark


import pycity_calc.toolbox.dimensioning.dim_functions as dimfunc
import warnings

def calc_dem_rel_annuity_city(city_object, eco_calc_instance, market_instance):

    """
    Input:
        el_dem : float, optional
            Sum of electrical energy demand, which has to be payed (in kWh)
        gas_dem : float, optional
            Sum of thermal energy demand, which has to be payed (in kWh)

        el_price : float, optional
            Specific price of electricity (in Euro/kWh)
        gas_price : float, optional
            Specific price of thermal energy (in Euro/kWh)

    Return:
        demand related cost of city (in Euro)


    Comment:

        In the city object the energy parameters are calculated in [W] and the time is calculated in [s], so it is
        necessary divided by (3600*1000) in order to get the [kWh] as unit.

        Attention to the el/gas price, in fact there are 2 different values depending on the building type (residential
        or industrial).

    """
    el_dem = 0
    gas_dem = 0
    dem_rel_annuity = 0
    el_price = 0
    gas_price = 0



    for n in city_object.nodes():
        if 'node_type' in city_object.node[n]:
            #  If node_type is building
            if city_object.node[n]['node_type'] == 'building':
                #  If entity is kind building
                if city_object.node[n]['entity']._kind == 'building':

                    if 'electrical demand' in city_object.node[n]:
                        if type(city_object.node[n]['electrical demand']) != int:
                            el_dem = sum(city_object.node[n]['electrical demand']) * city_object.environment.timer.timeDiscretization / 1000 / 3600


                    if 'fuel demand' in city_object.node[n]:
                        if type(city_object.node[n]['fuel demand']) != int:
                            gas_dem = sum(city_object.node[n]['fuel demand']) * city_object.environment.timer.timeDiscretization / 1000 / 3600



                    # residential building
                    if city_object.node[n]['entity'].build_type == 0:
                        el_price = market_instance.get_spec_el_cost('res', city_object.environment.timer.year, el_dem)
                        gas_price = market_instance.get_spec_gas_cost('res', city_object.environment.timer.year, gas_dem)


                    # industrial building
                    elif city_object.node[n]['entity'].build_type != 0:
                        el_price = market_instance.get_spec_el_cost('ind', city_object.environment.timer.year, el_dem)
                        gas_price = market_instance.get_spec_gas_cost('ind', city_object.environment.timer.year, gas_dem)



                    dem_rel_annuity += \
                        eco_calc_instance.calc_dem_rel_annuity(sum_el_e=el_dem, sum_gas_e=gas_dem,
                                                      price_el=el_price, price_gas=gas_price)

    return dem_rel_annuity



def calc_proc_annuity_multi_comp_city(city_object, eco_calc_instance):

    """
    Input list need to be in corresponding order

        Parameters
        ----------
        list_spec_income : list (of floats)
            List holding specific prices per sold unit of energy (in Euro/kWh)

        list_sold_energy : list (of floats)
            List holding amount of sold energy (in kWh)

        list_types : list (of str)
            List holding types of energy system
                Options:
                - 'CHP'
                - 'PV'

    Returns
        -------
        proc_annuity : float
            Annuity of proceedings for multi components in Euro


    Comment:

        The proceedings realities annuity has to be calculated for the PV and CHP taking in account all the several
        specific incomes existing for each one of them.


        For the CHP proceedings there are 4 different specific_income and each one of them is related to a type
        of energy:

            - Tax referred to the EEG-Umlage (fee for specific share), which is related to the amount of own electricity
              consumed: proc_rel_annuity_chp1;

            - Specific incomes (EEX baseload price + avoided grid-usage fee + chp subsidy by the state(CHP law 2016))
              referred to State subsidies, which are related to the amount of electricity sold: proc_rel_annuity_chp2;

            - Specific income referred to a subsidy payment for CHP el. energy, which is related to the amount of
              electricity used to cover the own demand: proc_rel_annuity_chp3;

            - Specific income referred to a tax exception on gas for the CHP, which is related to the amount of
              gas energy used by the CHP.


        For the PV proceedings there are 2 different specific_income:

            - Tax referred to the EEG-Umlage (fee for specific share), which is related to the amount of own electricity
              consumed: proc_rel_annuity_pv1;

            - Specific income referred to State subsidies, which are related to the amount of electricity sold:
              proc_rel_annuity_pv2.

    """


    total_proc_annuity = 0

    for n in city_object.nodes():
        if 'node_type' in city_object.node[n]:
            #  If node_type is building
            if city_object.node[n]['node_type'] == 'building':
                #  If entity is kind building
                if city_object.node[n]['entity']._kind == 'building':
                    build = city_object.node[n]['entity']
                    if build.hasBes:
                        #  BES pointer
                        bes = build.bes

                        if bes.hasChp:

                            # Specific income [€/kWh]el
                            EEG_Umlage_tax_chp = 0.0688  * 0.4

                            proc_rel_annuity_chp1 = \
                                eco_calc_instance.calc_proc_annuity_single_comp(spec_income=EEG_Umlage_tax_chp,
                                                                      sold_energy=sum(city_object.node[n]['chp_used_self']) * city_object.environment.timer.timeDiscretization / 1000 / 3600,
                                                                      type='CHP', spec_income_type='EEG_Umlage_tax')


                            # Specific incomes [€/kWh]el
                            EEX_baseload_price = 0.029
                            proc_rel_annuity_chp2 = \
                                eco_calc_instance.calc_proc_annuity_single_comp(spec_income=EEX_baseload_price,
                                    sold_energy=sum(city_object.node[n]['chp_sold']) * city_object.environment.timer.timeDiscretization / 1000 / 3600,
                                    type='CHP', spec_income_type='EEX_baseload_price')

                            avoid_grid_usage = 0.007
                            proc_rel_annuity_chp3 = \
                                eco_calc_instance.calc_proc_annuity_single_comp(
                                    spec_income=(avoid_grid_usage),
                                    sold_energy=sum(city_object.node[n]['chp_sold']) * city_object.environment.timer.timeDiscretization / 1000 / 3600,
                                    type='CHP', spec_income_type='avoid_grid_usage')

                            # Specific incomes for sold chp electrical energy [€/kWh]el
                            # subsidy payments depend on pNominal. According to KWKG 2016
                            if bes.chp.pNominal <= 50000:
                                sub_chp = 0.08
                            elif bes.chp.pNominal > 50000 and bes.chp.pNominal <= 100000:
                                sub_chp = 0.06
                            elif bes.chp.pNominal > 100000 and bes.chp.pNominal <= 250000:
                                sub_chp = 0.05
                            elif bes.chp.pNominal > 250000 and bes.chp.pNominal <= 2000000:
                                sub_chp = 0.044
                            else:
                                #TODO implement other case to handle pNom >100000
                                sub_chp = 0.031
                                warnings.warn(
                                    'CHP System hast more than 100kWel. The implemented KWKG subsidy payments \n'
                                    'method is not valid for this case. self_demand_usage_chp set to 0.03')
                            proc_rel_annuity_chp4 = \
                                eco_calc_instance.calc_proc_annuity_single_comp(spec_income=(sub_chp),
                                                                      sold_energy=sum(city_object.node[n]['chp_sold']) * city_object.environment.timer.timeDiscretization / 1000 / 3600,
                                                                      type='CHP', spec_income_type='sub_chp')

                            # Specific incomes for chp electrical self usage [€/kWh]el
                            # subsidy payments depends on pNominal. According to KWKG 2016
                            if bes.chp.pNominal <= 50000:
                                self_demand_usage_chp = 0.04
                            elif bes.chp.pNominal > 50000 and bes.chp.pNominal <= 100000:
                                self_demand_usage_chp = 0.03
                            else:
                                # TODO implement other case to handle pNom >100000
                                self_demand_usage_chp = 0
                                warnings.warn('CHP System hast more than 100kWel. The implemented KWKG subsidy payments \n'
                                              'method is not valid for this case. self_demand_usage_chp set to 0.03')

                            proc_rel_annuity_chp5 = \
                                eco_calc_instance.calc_proc_annuity_single_comp(spec_income=self_demand_usage_chp,
                                                                      sold_energy=sum(city_object.node[n]['chp_used_self']) * city_object.environment.timer.timeDiscretization / 1000 / 3600,
                                                                      type='CHP', spec_income_type='self_usage_chp')


                            #Specific income on chp_gas used [€/kWh]th
                            gas_disc_chp = 0.0055
                            proc_rel_annuity_chp6 = \
                                eco_calc_instance.calc_proc_annuity_single_comp(spec_income=gas_disc_chp,
                                                                      sold_energy=sum(city_object.node[n]['entity'].bes.chp.array_fuel_power) * city_object.environment.timer.timeDiscretization / 1000 / 3600,
                                                                      type='CHP', spec_income_type='gas_disc_chp')


                            proc_rel_annuity = - proc_rel_annuity_chp1 + proc_rel_annuity_chp2 + proc_rel_annuity_chp3 + proc_rel_annuity_chp4 + proc_rel_annuity_chp5 + proc_rel_annuity_chp6

                            total_proc_annuity += proc_rel_annuity


                        if bes.hasPv:

                            # Specific income [€/kWh]el
                            EEG_Umlage_tax_pv = 0.0688 * 0.4

                            if bes.pv.area * 1000 >= 10000:
                                proc_rel_annuity_pv1 = \
                                    eco_calc_instance.calc_proc_annuity_single_comp(spec_income=EEG_Umlage_tax_pv,
                                                                          sold_energy=sum(city_object.node[n]['pv_used_self']) * city_object.environment.timer.timeDiscretization / 1000 / 3600,
                                                                          type='PV', spec_income_type='EEG_Umlage_tax')
                            else:
                                proc_rel_annuity_pv1 = 0


                            # Specific income [€/kWh]el
                            # subsidy payments depend on installed peak power. According to EEG 2017
                            if bes.pv.area*1000 <= 10000:
                                #max 10kWp
                                sub_pv = 0.123
                            elif 10000 < bes.pv.area*1000 and bes.pv.area*1000 <= 40000:
                                # from 10 to 40kWp
                                sub_pv = 0.1196
                            elif bes.pv.area*1000 <= 100000:
                                # maximum 100kWp
                                sub_pv = 0.1069
                            else:
                                # TODO: there are some exception from the 100kWp maximum in the EEG
                                # TODO: implement a case for more than 100kWp
                                warnings.warn('PV System hast more than 100kWp. The implemented EEG subsidy payments \n'
                                              'method is not valid for this case. sub_pv set to 0.1109')
                                sub_pv = 0.1069
                            proc_rel_annuity_pv2 = \
                                eco_calc_instance.calc_proc_annuity_single_comp(spec_income=sub_pv,
                                                                      sold_energy=sum(city_object.node[n]['pv_sold']) * city_object.environment.timer.timeDiscretization / 1000 / 3600,
                                                                      type='PV', spec_income_type='sub_pv')

                            proc_rel_annuity = - proc_rel_annuity_pv1 + proc_rel_annuity_pv2
                            total_proc_annuity += proc_rel_annuity



    return total_proc_annuity


'''
I took the 2 methods (calc_cap_rel_annuity_city(city_object, eco_calc),
calc_cap_and_op_rel_annuity_city(city_object, eco_calc)) from 'city_economic_calc' and
I adapted these 2 methods in order to get the total annuity in one script ('economic_ann')
'''

def calc_cap_rel_annuity_city(city_object, eco_calc_instance):
    """
    Calculate sum of all capital related annuities of city

    Parameters
    ----------
    city_object : object
        City object
    eco_calc : object
        EconomicCalculation object of pycity_calc

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
    #  ######################################################################
    for n in city_object.nodes():
        if 'node_type' in city_object.node[n]:
            #  If node_type is building
            if city_object.node[n]['node_type'] == 'building':
                #  If entity is kind building
                if city_object.node[n]['entity']._kind == 'building':
                    build = city_object.node[n]['entity']
                    if build.hasBes:
                        #  BES pointer
                        bes = build.bes

                        if bes.hasBattery:
                            cap_kWh = bes.battery.capacity / (3600 * 1000)
                            #  In kWh
                            bat_invest = \
                                bat_cost.calc_invest_cost_bat(cap=cap_kWh, method='carmen')
                            cap_rel_ann += \
                                eco_calc_instance.calc_capital_rel_annuity_with_type(
                                    invest=bat_invest, type='BAT')
                            #  Add to lists
                            list_invest.append(bat_invest)
                            list_type.append('BAT')

                        if bes.hasBoiler:
                            q_nom = bes.boiler.qNominal / 1000  # in kW
                            boil_invest = \
                                boiler_cost.calc_abs_boiler_cost(q_nom=q_nom, method = 'spieker')
                            cap_rel_ann += \
                                eco_calc_instance.calc_capital_rel_annuity_with_type(
                                    invest=boil_invest, type='B')
                            #  Add to lists
                            list_invest.append(boil_invest)
                            list_type.append('B')

                        if bes.hasChp:
                            p_el_nom = bes.chp.pNominal / 1000  # in kW
                            chp_invest = \
                                chp_cost.calc_invest_cost_chp(p_el_nom= p_el_nom, method = 'spieker')
                            cap_rel_ann += \
                                eco_calc_instance.calc_capital_rel_annuity_with_type(
                                    invest=chp_invest, type='CHP')
                            #  Add to lists
                            list_invest.append(chp_invest)
                            list_type.append('CHP')

                        if bes.hasElectricalHeater:
                            q_eh = \
                                bes.electricalHeater.qNominal / 1000  # in kW
                            eh_invest = \
                                eh_cost.calc_abs_cost_eh(q_nom=q_eh, method = 'spieker')
                            cap_rel_ann += \
                                eco_calc_instance.calc_capital_rel_annuity_with_type(
                                    invest=eh_invest, type='EH')
                            #  Add to lists
                            list_invest.append(eh_invest)
                            list_type.append('EH')

                        if bes.hasHeatpump:
                            q_hp = bes.heatpump.qNominal / 1000  # in kW
                            hp_invest = \
                                hp_cost.calc_invest_cost_hp(q_nom=q_hp, method='wolf')
                            cap_rel_ann += \
                                eco_calc_instance.calc_capital_rel_annuity_with_type(
                                    invest=hp_invest, type='HP')
                            #  Add to lists
                            list_invest.append(hp_invest)
                            list_type.append('HP')

                        if bes.hasPv:
                            pv_area = bes.pv.area
                            pv_invest = pv_cost.calc_pv_invest(area=pv_area, method = 'EuPD')
                            cap_rel_ann += \
                                eco_calc_instance.calc_capital_rel_annuity_with_type(
                                    invest=pv_invest, type='PV')
                            #  Add to lists
                            list_invest.append(pv_invest)
                            list_type.append('PV')

                        if bes.hasTes:
                            tes_vol = bes.tes.capacity / 1000  # in m3
                            tes_invest = \
                                tes_cost.calc_invest_cost_tes(volume=tes_vol, method='spieker')
                            cap_rel_ann += \
                                eco_calc_instance.calc_capital_rel_annuity_with_type(
                                    invest=tes_invest, type='TES')
                            #  Add to lists
                            list_invest.append(tes_invest)
                            list_type.append('TES')

    # Get capital-related annuities per LHN network
    #  ######################################################################
    list_lhn_con = \
        netop.get_list_with_energy_net_con_node_ids(city=city_object,
                                                    network_type='heating')

    #  Add weights to edges
    netop.add_weights_to_edges(city_object)

    #  If LHN networks exist
    if len(list_lhn_con) > 0:

        invest_lhn_pipe = 0
        invest_lhn_trans = 0

        #  Loop over each connected lhn network
        for sublist in list_lhn_con:

            list_th_pow = []

            #  Get max. power values of all buildings connected to lhn
            for n in city_object.nodes():
                if 'node_type' in city_object.node[n]:
                    #  If node_type is building
                    if city_object.node[n]['node_type'] == 'building':
                        #  If entity is kind building
                        if city_object.node[n]['entity']._kind == 'building':
                            build = city_object.node[n]['entity']
                            th_pow = \
                                dimfunc.get_max_power_of_building(build,
                                                                  with_dhw=False)
                            list_th_pow.append(
                                th_pow / 1000)  # Convert W to kW

            # Calculate investment cost for lhn transmission statinos
            invest_lhn_trans += \
                lhn_cost.calc_invest_cost_lhn_stations(list_powers=list_th_pow)

            #  Add to lists
            list_invest.append(invest_lhn_trans)
            list_type.append('LHN_station')

            #  Loop over every heating pipe and calculate cost
            for u in sublist:
                for v in sublist:
                    if city_object.has_edge(u, v):
                        if 'network_type' in city_object.edge[u][v]:
                            if (city_object.edge[u][v]['network_type'] == 'heating' or
                                city_object.edge[u][v]['network_type'] == 'heating_and_deg'):
                                #  Pointer to pipe (edge)
                                pipe = city_object.edge[u][v]
                                d_i = pipe['d_i']
                                length = pipe['weight']
                                invest_lhn_pipe += \
                                    lhn_cost.calc_invest_cost_lhn_pipes(d=d_i,
                                                                        length=length)

            # Add to lists
            list_invest.append(invest_lhn_pipe)
            list_type.append('LHN_plastic_pipe')

        # Calculate capital-related annuity of LHN network

        #  Capital-related annuity for LHN transmission stations
        cap_rel_ann += \
            eco_calc_instance.calc_capital_rel_annuity_with_type(
                invest=invest_lhn_trans,
                type='LHN_station')

        #  Capital-related annuity for LHN pipelines
        cap_rel_ann += \
            eco_calc_instance.calc_capital_rel_annuity_with_type(
                invest=invest_lhn_pipe,
                type='LHN_plastic_pipe')

    #  Get capital-related annuities per DEG network
    #  ######################################################################
    list_deg_con = \
        netop.get_list_with_energy_net_con_node_ids(city=city_object,
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
            for n in city_object.nodes():
                if 'node_type' in city_object.node[n]:
                    #  If node_type is building
                    if city_object.node[n]['node_type'] == 'building':
                        #  If entity is kind building
                        if city_object.node[n]['entity']._kind == 'building':
                            nb_build += 1

            deg_len = 0
            deg_len_w_lhn = 0

            #  Loop over every deg pipe and calculate cost
            for u in sublist:
                for v in sublist:
                    if city_object.has_edge(u, v):
                        if 'network_type' in city_object.edge[u][v]:
                            if city_object.edge[u][v]['network_type'] == 'electricity':
                                deg_len += city_object.edge[u][v]['weight']
                            elif city_object.edge[u][v]['network_type'] == 'heating_and_deg':
                                deg_len_w_lhn += city_object.edge[u][v]['weight']


            #  Calculate deg investment cost for (sub-)deg
            deg_invest += \
                deg_cost.calc_invest_cost_deg(length=deg_len+deg_len_w_lhn,
                              nb_con=nb_build,
                              nb_sub=1,
                              share_lhn=(deg_len_w_lhn/(deg_len+deg_len_w_lhn)))

            # Add to lists
            list_invest.append(deg_invest)
            list_type.append('DEG')

            #  Capital-related annuity for LHN transmission stations
            cap_rel_ann += \
                eco_calc_instance.calc_capital_rel_annuity_with_type(
                    invest=deg_invest,
                    type='DEG')


    return (cap_rel_ann, list_invest, list_type)


def calc_cap_and_op_rel_annuity_city(city_object, eco_calc_instance):
    """
    Calculate capital- and operation-related annuities of city

    Parameters
    ----------
    city_object : object
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
        calc_cap_rel_annuity_city(city_object=city_object, eco_calc_instance=eco_calc_instance)

    #  Calculate operation-related annuity
    op_rel_ann = \
        eco_calc_instance.calc_op_rel_annuity_multi_comp(list_invest=list_invest, list_types=list_type)

    return (cap_rel_ann, op_rel_ann)