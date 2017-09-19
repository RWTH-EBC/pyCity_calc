#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
from __future__ import division

import os
import pickle

import pycity_calc.simulation.energy_balance.building_eb_calc as buildeb

from pycity_calc.test.pycity_calc_fixtures import fixture_building, \
    fixture_environment, fixture_city, fixture_apartment, fixture_th_demand, \
    fixture_el_demand, fixture_eb_city_district


class TestBuildingEnergyBalance():

    def test_building_eb_calc(self, fixture_eb_city_district):

        city = fixture_eb_city_district

        timestep = city.environment.timer.timeDiscretization

        #  ##################################################################
        #  Get buiding 1007 (boiler, only)
        #  Add EH to test energy balance for boiler and eh without tes
        id = 1007
        exbuild = city.node[id]['entity']

        #  Calculate thermal energy balance
        buildeb.calc_build_therm_eb(build=exbuild, id=id)

        #  Calculate electric energy balance
        buildeb.calc_build_el_eb(build=exbuild)

        q_out = exbuild.bes.boiler.totalQOutput
        fuel_in = exbuild.bes.boiler.array_fuel_power
        sh_p_array = exbuild.get_space_heating_power_curve()
        dhw_p_array = exbuild.get_dhw_power_curve()

        sh_net_energy = sum(sh_p_array) * timestep / (1000 * 3600)  # in kWh
        dhw_net_energy = sum(dhw_p_array) * timestep / (1000 * 3600)  # in kWh
        boil_th_energy = sum(q_out) * timestep / (1000 * 3600)  # in kWh
        fuel_boiler_energy = sum(fuel_in) * timestep / (1000 * 3600)  # in kWh

        assert fuel_boiler_energy >= boil_th_energy
        assert boil_th_energy - (sh_net_energy + dhw_net_energy) <= 0.001

        #  ##################################################################

        #  ##################################################################
        #  Get buiding 1001 (CHP, boiler, tes)
        #  Add EH to test energy balance for CHP, boiler, EH with TES
        id = 1001
        exbuild = city.node[id]['entity']

        # eh = elheat.ElectricalHeaterExtended(environment=exbuild.environment,
        #                                      q_nominal=10000)
        #
        # exbuild.bes.addDevice(eh)

        #  Calculate thermal energy balance
        buildeb.calc_build_therm_eb(build=exbuild, id=id)

        #  Calculate electric energy balance
        buildeb.calc_build_el_eb(build=exbuild)

        #  Get space heating results
        sh_p_array = exbuild.get_space_heating_power_curve()
        dhw_p_array = exbuild.get_dhw_power_curve()

        #  Get boiler results
        q_out = exbuild.bes.boiler.totalQOutput
        fuel_in = exbuild.bes.boiler.array_fuel_power

        #  Get CHP results
        q_chp_out = exbuild.bes.chp.totalQOutput
        p_el_chp_out = exbuild.bes.chp.totalPOutput
        fuel_chp_in = exbuild.bes.chp.array_fuel_power

        tes_temp = exbuild.bes.tes.array_temp_storage

        #  Checks
        sh_net_energy = sum(sh_p_array) * timestep / (1000 * 3600)  # in kWh
        dhw_net_energy = sum(dhw_p_array) * timestep / (1000 * 3600)  # in kWh
        boil_th_energy = sum(q_out) * timestep / (1000 * 3600)  # in kWh
        chp_th_energy = sum(q_chp_out) * timestep / (1000 * 3600)  # in kWh
        fuel_boiler_energy = sum(fuel_in) * timestep / (1000 * 3600)  # in kWh
        fuel_chp_energy = sum(fuel_chp_in) * timestep / (1000 * 3600)  # in kWh
        chp_el_energy = sum(p_el_chp_out) * timestep / (1000 * 3600)  # in kWh

        assert sh_net_energy + dhw_net_energy <= boil_th_energy + chp_th_energy
        assert fuel_chp_energy >= chp_th_energy + chp_el_energy
        assert boil_th_energy <= fuel_boiler_energy

        #  ##################################################################

        # #  ################################################################
        #  Extract building 1008 (HP, EH, PV and TES)
        id = 1008
        exbuild = city.node[id]['entity']

        #  Modify size of electrical heater
        exbuild.bes.electricalHeater.qNominal *= 1.5

        #  Modify tes
        exbuild.bes.tes.tMax = 45
        print('Capacity of TES in kg: ', exbuild.bes.tes.capacity)

        #  Calculate thermal energy balance
        buildeb.calc_build_therm_eb(build=exbuild, id=id)

        #  Calculate electric energy balance
        buildeb.calc_build_el_eb(build=exbuild)

        #  Get space heating results
        sh_p_array = exbuild.get_space_heating_power_curve()
        dhw_p_array = exbuild.get_dhw_power_curve()

        q_hp_out = exbuild.bes.heatpump.totalQOutput
        el_hp_in = exbuild.bes.heatpump.array_el_power_in

        q_eh_out = exbuild.bes.electricalHeater.totalQOutput
        el_eh_in = exbuild.bes.electricalHeater.totalPConsumption

        tes_temp = exbuild.bes.tes.array_temp_storage

        sh_en = sum(sh_p_array) * timestep / (1000 * 3600)
        dhw_en = sum(dhw_p_array) * timestep / (1000 * 3600)

        q_hp_out_en = sum(q_hp_out) * timestep / (1000 * 3600)
        q_eh_out_en = sum(q_eh_out) * timestep / (1000 * 3600)

        el_eh_in_en = sum(el_eh_in) * timestep / (1000 * 3600)
        el_hp_in_en = sum(el_hp_in) * timestep / (1000 * 3600)

        assert sh_en + dhw_en - (q_hp_out_en + q_eh_out_en) < 0.001
        assert dhw_en - q_eh_out_en < 0.001
        assert q_eh_out_en - el_eh_in_en < 0.001
        assert el_hp_in_en <= q_hp_out_en

        # #  #################################################################