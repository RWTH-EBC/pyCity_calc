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


def calc_cap_rel_annuity_city(city, eco_calc):
    """
    Calculate sum of all capital related annuities of city

    Parameters
    ----------
    city : object
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
    for n in city.nodes():
        if 'node_type' in city.node[n]:
            #  If node_type is building
            if city.node[n]['node_type'] == 'building':
                #  If entity is kind building
                if city.node[n]['entity']._kind == 'building':
                    build = city.node[n]['entity']
                    if build.hasBes:
                        #  BES pointer
                        bes = build.bes

                        if bes.hasBattery:
                            cap_kWh = bes.battery.capacity / (3600 * 1000)
                            #  In kWh
                            bat_invest = \
                                bat_cost.calc_invest_cost_bat(cap=cap_kWh)
                            cap_rel_ann += \
                                eco_calc.calc_capital_rel_annuity_with_type(
                                    invest=bat_invest, type='BAT')
                            #  Add to lists
                            list_invest.append(bat_invest)
                            list_type.append('BAT')

                        if bes.hasBoiler:
                            q_nom = bes.boiler.qNominal / 1000  # in kW
                            boil_invest = \
                                boiler_cost.calc_abs_boiler_cost(q_nom=q_nom)
                            cap_rel_ann += \
                                eco_calc.calc_capital_rel_annuity_with_type(
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
                                eco_calc.calc_capital_rel_annuity_with_type(
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
                                eco_calc.calc_capital_rel_annuity_with_type(
                                    invest=eh_invest, type='EH')
                            #  Add to lists
                            list_invest.append(eh_invest)
                            list_type.append('EH')

                        if bes.hasHeatpump:
                            q_hp = bes.heatpump.qNominal / 1000  # in kW
                            hp_invest = \
                                hp_cost.calc_invest_cost_hp(q_nom=q_hp)
                            cap_rel_ann += \
                                eco_calc.calc_capital_rel_annuity_with_type(
                                    invest=hp_invest, type='HP')
                            #  Add to lists
                            list_invest.append(hp_invest)
                            list_type.append('HP')

                        if bes.hasPv:
                            pv_area = bes.pv.area
                            pv_invest = pv_cost.calc_pv_invest(area=pv_area)
                            cap_rel_ann += \
                                eco_calc.calc_capital_rel_annuity_with_type(
                                    invest=pv_invest, type='PV')
                            #  Add to lists
                            list_invest.append(pv_invest)
                            list_type.append('PV')

                        if bes.hasTes:
                            tes_vol = bes.tes.capacity / 1000  # in m3
                            tes_invest = \
                                tes_cost.calc_invest_cost_tes(volume=tes_vol)
                            cap_rel_ann += \
                                eco_calc.calc_capital_rel_annuity_with_type(
                                    invest=tes_invest, type='TES')
                            #  Add to lists
                            list_invest.append(tes_invest)
                            list_type.append('TES')

    # Get capital-related annuities per LHN network
    #  ######################################################################
    list_lhn_con = \
        netop.get_list_with_energy_net_con_node_ids(city=city,
                                                    network_type='heating')

    #  Add weights to edges
    netop.add_weights_to_edges(city)

    #  If LHN networks exist
    if len(list_lhn_con) > 0:

        invest_lhn_pipe = 0
        invest_lhn_trans = 0

        #  Loop over each connected lhn network
        for sublist in list_lhn_con:

            list_th_pow = []

            #  Get max. power values of all buildings connected to lhn
            for n in city.nodes():
                if 'node_type' in city.node[n]:
                    #  If node_type is building
                    if city.node[n]['node_type'] == 'building':
                        #  If entity is kind building
                        if city.node[n]['entity']._kind == 'building':
                            build = city.node[n]['entity']
                            th_pow = \
                                dimfunc.get_max_power_of_building(build,
                                                                  with_dhw=False)
                            list_th_pow.append(
                                th_pow / 1000)  # Convert W to kW

            # Calculate investment cost for lhn transmission stations
            invest_lhn_trans += \
                lhn_cost.calc_invest_cost_lhn_stations(list_powers=list_th_pow)

            #  Add to lists
            list_invest.append(invest_lhn_trans)
            list_type.append('LHN_station')

            #  Loop over every heating pipe and calculate cost
            for u in sublist:
                for v in sublist:
                    if city.has_edge(u, v):
                        if 'network_type' in city.edge[u][v]:
                            if (city.edge[u][v]['network_type'] == 'heating' or
                                city.edge[u][v]['network_type'] == 'heating_and_deg'):
                                #  Pointer to pipe (edge)
                                pipe = city.edge[u][v]
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
            eco_calc.calc_capital_rel_annuity_with_type(
                invest=invest_lhn_trans,
                type='LHN_station')

        #  Capital-related annuity for LHN pipelines
        cap_rel_ann += \
            eco_calc.calc_capital_rel_annuity_with_type(
                invest=invest_lhn_pipe,
                type='LHN_plastic_pipe')

    #  Get capital-related annuities per DEG network
    #  ######################################################################
    list_deg_con = \
        netop.get_list_with_energy_net_con_node_ids(city=city,
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
            for n in city.nodes():
                if 'node_type' in city.node[n]:
                    #  If node_type is building
                    if city.node[n]['node_type'] == 'building':
                        #  If entity is kind building
                        if city.node[n]['entity']._kind == 'building':
                            nb_build += 1

            deg_len = 0
            deg_len_w_lhn = 0

            #  Loop over every deg pipe and calculate cost
            for u in sublist:
                for v in sublist:
                    if city.has_edge(u, v):
                        if 'network_type' in city.edge[u][v]:
                            if city.edge[u][v]['network_type'] == 'electricity':
                                deg_len += city.edge[u][v]['weight']
                            elif city.edge[u][v]['network_type'] == 'heating_and_deg':
                                deg_len_w_lhn += city.edge[u][v]['weight']


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
                eco_calc.calc_capital_rel_annuity_with_type(
                    invest=deg_invest,
                    type='DEG')

    return (cap_rel_ann, list_invest, list_type)


def calc_cap_and_op_rel_annuity_city(city, eco_calc):
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
        calc_cap_rel_annuity_city(city=city, eco_calc=eco_calc)

    #  Calculate operation-related annuity
    op_rel_ann = \
        eco_calc.calc_op_rel_annuity_multi_comp(list_invest=list_invest,
                                                list_types=list_type)

    return (cap_rel_ann, op_rel_ann)
