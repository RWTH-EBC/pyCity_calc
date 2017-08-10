#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""

import pycity_calc.economic.energy_sys_cost.bat_cost as bat_cost
import pycity_calc.economic.energy_sys_cost.boiler_cost as boiler_cost
import pycity_calc.economic.energy_sys_cost.chp_cost as chp_cost
import pycity_calc.economic.energy_sys_cost.deg_cost as deg_cost
import pycity_calc.economic.energy_sys_cost.eh_cost as eh_cost
import pycity_calc.economic.energy_sys_cost.hp_cost as hp_cost
import pycity_calc.economic.energy_sys_cost.lhn_cost as lhn_cost
import pycity_calc.economic.energy_sys_cost.pv_cost as pv_cost
import pycity_calc.economic.energy_sys_cost.tes_cost as tes_cost


class Test_EnersysCost():
    def test_bat_cost(self):

        bat_cap = 5  # kWh
        list_methods = ['sma', 'carmen']

        for method in list_methods:
            #  Calculate specific cost for battery
            spec_cost = bat_cost.calc_spec_cost_bat(cap=bat_cap, method=method)
            print('Specific cost for battery in Euro/kWh (method ' +
                  str(method) + '):')
            print(round(spec_cost, 2))
            print()

        print('##################################')
        for method in list_methods:
            #  Calculate investment cost for battery
            inv_cost = bat_cost.calc_invest_cost_bat(cap=bat_cap,
                                                     method=method)
            print('Investment cost for battery in Euro (method '
                  + str(method) + '):')
            print(round(inv_cost, 2))
            print()

    def test_boiler_cost(self):

        boiler_size = 40000  # in Watt

        boiler_kW = boiler_size / 1000

        #  Specific cost according to dbi
        dbi_spec_cost = boiler_cost.calc_spec_cost_boiler(q_nom=boiler_kW,
                                                          method='dbi')
        dbi_abs = boiler_cost.calc_abs_boiler_cost(q_nom=boiler_kW,
                                                   method='dbi')
        print('DBI specific boiler cost in Euro/kW:')
        print(round(dbi_spec_cost, 2))
        print('DBI absolut boiler cost in Euro:')
        print(round(dbi_abs, 2))
        print()

        #  Specific cost according to Viessmann 2013
        viess_spec_cost = \
            boiler_cost.calc_spec_cost_boiler(q_nom=boiler_kW,
                                              method='viess2013')
        viess_abs = boiler_cost.calc_abs_boiler_cost(q_nom=boiler_kW,
                                                     method='viess2013')
        print('Viessmann specific boiler cost in Euro/kW:')
        print(round(viess_spec_cost, 2))
        print('Viessmann absolut boiler cost in Euro:')
        print(round(viess_abs, 2))
        print()

        #  Specific cost according to Spieker et al.
        spiek_spec_cost = \
            boiler_cost.calc_spec_cost_boiler(q_nom=boiler_kW,
                                              method='spieker')
        spiek_abs = boiler_cost.calc_abs_boiler_cost(q_nom=boiler_kW,
                                                     method='spieker')
        print('Spieker et al. specific boiler cost in Euro/kW:')
        print(round(spiek_spec_cost, 2))
        print('Spieker et al.  absolut boiler cost in Euro:')
        print(round(spiek_abs, 2))
        print()

    def test_chp_cost(self):

        chp_nom_el_power = 30000  # in Watt
        method = 'asue2015'
        with_inst = True  # With cost for transport and installation

        chp_el_kW = chp_nom_el_power / 1000

        #  Calculate specific cost of CHP
        spec_cost = chp_cost.calc_spec_cost_chp(p_el_nom=chp_el_kW,
                                                method=method,
                                                with_inst=with_inst)
        print('Specific CHP cost in Euro/kW:')
        print(round(spec_cost, 2))
        print()

        #  Calculate total investment cost for CHP
        total_cost = chp_cost.calc_invest_cost_chp(p_el_nom=chp_el_kW,
                                                   method=method,
                                                   with_inst=with_inst)
        print('Total investment cost for CHP in Euro:')
        print(round(total_cost, 2))

    def test_deg_cost(self):

        deg_len = 300  # in m
        nb_con = 10  # 10 Buildings
        nb_sub = 1  # 1 (sub-)deg
        share_lhn = 0.75

        deg_invest = \
            deg_cost.calc_invest_cost_deg(length=deg_len, nb_con=nb_con,
                                          nb_sub=nb_sub,
                                          share_lhn=share_lhn)

        print('Investment cost into DEG in Euro:')
        print(round(deg_invest, 2))

    def test_eh_cost(self):

        eh_size = 30000  # in Watt

        eh_kw = eh_size / 1000  # in kW

        #  Specific cost
        eh_spec_cost = eh_cost.calc_spec_cost_eh(q_nom=eh_kw)
        print('Specific EH cost in Euro/kW:')
        print(round(eh_spec_cost, 2))
        print()

        #  Investment cost
        inv_cost = eh_cost.calc_abs_cost_eh(q_nom=eh_kw)
        print('Investment cost of EH in Euro:')
        print(round(inv_cost, 2))
        print()

    def test_hp_cost(self):

        hp_th_pow = 10000  # Heat pump thermal power in Watt
        method = 'stinner'
        hp_type = 'aw'  # Brine/water
        with_source_cost = False  # With/Without cost for heat source preparation

        hp_kw = hp_th_pow / 1000  # in kW

        #  Calculate specific heat pump cost
        spec_cost = hp_cost.calc_spec_cost_hp(q_nom=hp_kw, method=method,
                                              hp_type=hp_type)
        print('Specific heat pump cost in Euro/kW:')
        print(round(spec_cost, 2))
        print()

        #  Calculate heat pump investment cost
        invest_hp = hp_cost.calc_invest_cost_hp(q_nom=hp_kw, method=method,
                                                hp_type=hp_type,
                                                with_source_cost=with_source_cost,
                                                with_inst=True)
        print('Investment cost for heat pump in Euro:')
        print(round(invest_hp, 2))

    def test_lhn_cost(self):

        d = 0.05  # Diameter in m
        lhn_len = 100  # Length of LHN system in m

        list_q_nom = [10, 20, 15, 25]
        # List nominal th. powers in kW (per building)

        #  Calculate specific cost of LHN pipings
        spec_lhn_cost = lhn_cost.calc_spec_cost_lhn(d=d)
        print('Specific LHN cost in Euro/m: ')
        print(round(spec_lhn_cost, 2))
        print()

        #  Calculate investment cost of LHN pipes
        invest_lhn_pip = lhn_cost.calc_invest_cost_lhn_pipes(d=d,
                                                             length=lhn_len)
        print('Investment cost of LHN pipes in Euro:')
        print(round(invest_lhn_pip, 2))
        print()

        #  Calculate LHN invest cost for transmission stations
        invest_trans = lhn_cost.calc_invest_cost_lhn_stations(
            list_powers=list_q_nom)
        print('Investment cost of LHN transmision stations in Euro:')
        print(round(invest_trans, 2))
        print()

        #  Calculate total invest
        total_invest = \
            lhn_cost.calc_total_lhn_invest_cost(d=d, length=lhn_len,
                                                list_powers=list_q_nom)
        print('Total investment cost for LHN:')
        print(round(total_invest, 2))

    def test_pv_cost(self):

        area = 10

        #  Calculate PV investment cost
        pv_invest = pv_cost.calc_pv_invest(area=area)

        print('PV investment cost in Euro:')
        print(round(pv_invest, 2))

    def test_tes_cost(self):

        volume = 300  # in literes
        method_1 = 'spieker'
        #  method_2 = 'schmidt'  # Only valid for large scale storage systems

        volume_m3 = volume / 1000

        #  Calculate specific cost for tes
        spec_cost_1 = tes_cost.calc_spec_cost_tes(volume=volume_m3,
                                                  method=method_1)

        print('Specific cost (Spieker et al.) for tes in Euro/m3: ')
        print(round(spec_cost_1, 2))
        print()

        #  Calculate investment cost for tes
        invest_cost_1 = tes_cost.calc_invest_cost_tes(volume=volume_m3,
                                                      method=method_1)

        print('Investment cost (Spieker et al.) for tes in Euro: ')
        print(round(invest_cost_1, 2))
