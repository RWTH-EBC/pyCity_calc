#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
from __future__ import division

import os
import copy
import numpy as np

import pycity_base.classes.supply.BES as BES
import pycity_base.classes.supply.PV as PV

import pycity_calc.simulation.energy_balance.building_eb_calc as buildeb
import pycity_calc.energysystems.chp as chpsys
import pycity_calc.energysystems.battery as bat
import pycity_calc.energysystems.boiler as boil
import pycity_calc.energysystems.electricalHeater as ehsys
import pycity_calc.energysystems.heatPumpSimple as hpsys
import pycity_calc.energysystems.thermalEnergyStorage as sto
import pycity_calc.energysystems.Input.chp_asue_2015 as asue

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
        assert abs(boil_th_energy - (sh_net_energy + dhw_net_energy)) <= 0.001

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

        assert abs(sh_en + dhw_en - (q_hp_out_en + q_eh_out_en)) < 0.001
        assert abs(dhw_en - q_eh_out_en) < 0.001
        assert abs(q_eh_out_en - el_eh_in_en) < 0.001
        assert el_hp_in_en <= q_hp_out_en

        # #  #################################################################

    def test_building_eb_2(self, fixture_building):
        """
        Test, if share of CHP self-consumed and fed-in electric energy is
        correct
        """

        build = copy.deepcopy(fixture_building)

        timestep = build.environment.timer.timeDiscretization
        nb_timesteps = int(365 * 24 * 3600 / timestep)

        q_nom = 1000
        eta_total = 0.9

        p_nom = asue.calc_el_power_with_th_power(th_power=q_nom,
                                                 eta_total=eta_total)

        sh_power = np.ones(nb_timesteps) * q_nom  # 1000 W

        el_power = np.ones(nb_timesteps) * p_nom / 4  # 1/4 p_nom in W

        build.apartments[0].demandSpaceheating.loadcurve = sh_power
        build.apartments[0].power_el.loadcurve = el_power

        chp = chpsys.ChpExtended(environment=build.environment,
                                 q_nominal=q_nom,
                                 p_nominal=p_nom, eta_total=eta_total)

        tes = sto.thermalEnergyStorageExtended\
            (environment=build.environment, t_init=75, capacity=100)

        bes = BES.BES(environment=build.environment)

        bes.addDevice(chp)
        bes.addDevice(tes)

        build.addEntity(bes)

        #  Calculate energy balances
        buildeb.calc_build_therm_eb(build=build)

        buildeb.calc_build_el_eb(build=build)

        #  Check results
        chp_self = build.dict_el_eb_res['chp_self']
        chp_feed = build.dict_el_eb_res['chp_feed']

        sum_chp_self = sum(chp_self) * timestep / (100 * 3600)
        sum_chp_feed = sum(chp_feed) * timestep / (100 * 3600)

        assert abs(sum_chp_self / (sum_chp_self + sum_chp_feed) - 1/4) < 0.001
