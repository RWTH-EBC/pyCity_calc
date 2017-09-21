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

        assert sh_en + dhw_en <= (q_hp_out_en + q_eh_out_en)
        assert dhw_en <= q_eh_out_en
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
        sh_energy = build.get_annual_space_heat_demand()

        chp_self = build.dict_el_eb_res['chp_self']
        chp_feed = build.dict_el_eb_res['chp_feed']

        sum_chp_self = sum(chp_self) * timestep / (1000 * 3600)
        sum_chp_feed = sum(chp_feed) * timestep / (1000 * 3600)

        chp_th_power = build.bes.chp.totalQOutput
        chp_el_power = build.bes.chp.totalPOutput

        chp_th_energy = sum(chp_th_power) * timestep / (1000 * 3600)
        chp_el_energy = sum(chp_el_power) * timestep / (1000 * 3600)

        assert abs(chp_el_energy - (sum_chp_self + sum_chp_feed)) <= 0.001
        assert abs(sum_chp_self / (sum_chp_self + sum_chp_feed) - 1/4) < 0.001
        assert chp_th_energy >= sh_energy

    def test_energy_balance_without_losses(self, fixture_building):
        """
        Check energy balance without losses
        """

        build = copy.deepcopy(fixture_building)

        timestep = build.environment.timer.timeDiscretization
        nb_timesteps = int(365 * 24 * 3600 / timestep)

        q_nom = 20000
        eta_total = 1

        p_nom = asue.calc_el_power_with_th_power(th_power=q_nom,
                                                 eta_total=eta_total)

        sh_power = np.ones(nb_timesteps) * 20000
        el_power = np.ones(nb_timesteps) * 12000

        build.apartments[0].demandSpaceheating.loadcurve = sh_power
        build.apartments[0].power_el.loadcurve = el_power

        chp = chpsys.ChpExtended(environment=build.environment,
                                 q_nominal=q_nom,
                                 p_nominal=p_nom, eta_total=eta_total)

        # eh = ehsys.ElectricalHeaterExtended(environment=build.environment,
        #                                     q_nominal=5000)

        tes = sto.thermalEnergyStorageExtended \
            (environment=build.environment, t_init=80, capacity=500, k_loss=0)

        pv = PV.PV(environment=build.environment, area=10, eta=1)

        pv.totalPower = np.ones(nb_timesteps) * 10000

        bes = BES.BES(environment=build.environment)

        bes.addDevice(chp)
        bes.addDevice(tes)
        bes.addDevice(pv)
        # bes.addDevice(eh)

        build.addEntity(bes)

        #  Calculate energy balances
        buildeb.calc_build_therm_eb(build=build)

        buildeb.calc_build_el_eb(build=build)

        #  Get results

        sh_energy = build.get_annual_space_heat_demand()
        dhw_energy = build.get_annual_dhw_demand()
        el_energy = build.get_annual_el_demand()

        chp_th_power = build.bes.chp.totalQOutput
        chp_el_power = build.bes.chp.totalPOutput

        chp_th_energy = sum(chp_th_power) * timestep / (100 * 3600)
        chp_el_energy = sum(chp_el_power) * timestep / (100 * 3600)

        chp_self = build.dict_el_eb_res['chp_self']
        chp_feed = build.dict_el_eb_res['chp_feed']
        pv_self = build.dict_el_eb_res['pv_self']
        pv_feed = build.dict_el_eb_res['pv_feed']

        sum_chp_self = sum(chp_self) * timestep / (100 * 3600)
        sum_chp_feed = sum(chp_feed) * timestep / (100 * 3600)
        sum_pv_self = sum(pv_self) * timestep / (100 * 3600)
        sum_pv_feed = sum(pv_feed) * timestep / (100 * 3600)

        grid_import_dem = build.dict_el_eb_res['grid_import_dem']
        sum_grid_import = sum(grid_import_dem) * timestep / (1000 * 3600)

        assert chp_el_energy - (sum_chp_self + sum_chp_feed) <= 0.001
        assert sh_energy + dhw_energy - chp_th_energy <= 0.001
        assert el_energy - (sum_chp_self + sum_pv_self + sum_grid_import) \
               <= 0.001

        assert abs(sum_pv_self / (sum_pv_feed + sum_pv_self) - 1) \
               <= 0.001
        assert abs(sum_chp_feed - (p_nom - 2000) * 900 / (3600 * 1000))

    def test_el_eb_pv(self, fixture_building):
        """
        Test el. energy balance with PV
        """

        build = copy.deepcopy(fixture_building)

        timestep = build.environment.timer.timeDiscretization
        nb_timesteps = int(365 * 24 * 3600 / timestep)

        build.apartments[0].power_el.loadcurve = np.ones(nb_timesteps) * 1000

        # battery = bat.BatteryExtended(environment=build.environment,
        #                               soc_init_ratio=1, capacity_kwh=10,
        #                               self_discharge=0, eta_charge=1,
        #                               eta_discharge=1)

        pv = PV.PV(environment=build.environment, area=20, eta=0.15,
                   temperature_nominal=45,
                   alpha=0, beta=0, gamma=0, tau_alpha=0.9)

        pv_power = pv.getPower(currentValues=False, updatePower=True)

        sum_pv_energy = sum(pv_power) * timestep / (3600 * 1000)

        bes = BES.BES(environment=build.environment)

        bes.addDevice(pv)
        # bes.addDevice(battery)

        build.addEntity(bes)

        buildeb.calc_build_el_eb(build=build)

        pv_self = build.dict_el_eb_res['pv_self']
        pv_feed = build.dict_el_eb_res['pv_feed']
        grid_import_dem = build.dict_el_eb_res['grid_import_dem']

        sum_pv_self = sum(pv_self) * timestep / (1000 * 3600)
        sum_pv_feed = sum(pv_feed) * timestep / (1000 * 3600)
        sum_grid_import = sum(grid_import_dem) * timestep / (1000 * 3600)

        el_demand = build.get_annual_el_demand()

        assert el_demand - (sum_pv_self + sum_grid_import) <= 0.001
        assert sum_pv_energy - (sum_pv_self + sum_pv_feed) <= 0.001

    def test_eb_pv_hp_eh(self, fixture_building):
        """

        """

        build = copy.deepcopy(fixture_building)

        timestep = build.environment.timer.timeDiscretization
        nb_timesteps = int(365 * 24 * 3600 / timestep)

        build.apartments[0].power_el.loadcurve = np.ones(nb_timesteps) * 1000
        build.apartments[0].demandSpaceheating.loadcurve = \
            np.ones(nb_timesteps) * 2000

        # battery = bat.BatteryExtended(environment=build.environment,
        #                               soc_init_ratio=1, capacity_kwh=10,
        #                               self_discharge=0, eta_charge=1,
        #                               eta_discharge=1)

        pv = PV.PV(environment=build.environment, area=20, eta=0.15,
                   temperature_nominal=45,
                   alpha=0, beta=0, gamma=0, tau_alpha=0.9)

        bes = BES.BES(environment=build.environment)

        hp = hpsys.heatPumpSimple(environment=build.environment,
                                  q_nominal=6000)

        eh = ehsys.ElectricalHeaterExtended(environment=build.environment,
                                            q_nominal=10000)

        tes = sto.thermalEnergyStorageExtended(environment=build.environment,
                                               t_init=45, t_max=45,
                                               capacity=100, k_loss=0)

        bes.addDevice(pv)
        # bes.addDevice(battery)
        bes.addDevice(hp)
        bes.addDevice(eh)
        bes.addDevice(tes)

        build.addEntity(bes)

        buildeb.calc_build_therm_eb(build=build)
        buildeb.calc_build_el_eb(build=build)

        sh_energy = build.get_annual_space_heat_demand()
        dhw_energy = build.get_annual_dhw_demand()
        el_energy = build.get_annual_el_demand()

        pv_power = pv.getPower(currentValues=False, updatePower=True)
        sum_pv_energy = sum(pv_power) * timestep / (3600 * 1000)

        hp_th_power = build.bes.heatpump.totalQOutput
        hp_el_power = build.bes.heatpump.array_el_power_in

        eh_th_power = build.bes.electricalHeater.totalQOutput
        eh_el_power = build.bes.electricalHeater.totalPConsumption

        sum_hp_th_energy = sum(hp_th_power) * timestep / (1000 * 3600)
        sum_hp_el_energy = sum(hp_el_power) * timestep / (1000 * 3600)
        sum_eh_th_energy = sum(eh_th_power) * timestep / (1000 * 3600)
        sum_eh_el_energy = sum(eh_el_power) * timestep / (1000 * 3600)

        pv_self = build.dict_el_eb_res['pv_self']
        pv_feed = build.dict_el_eb_res['pv_feed']
        grid_import_dem = build.dict_el_eb_res['grid_import_dem']
        grid_import_hp = build.dict_el_eb_res['grid_import_hp']
        grid_import_eh = build.dict_el_eb_res['grid_import_eh']

        sum_pv_self = sum(pv_self) * timestep / (1000 * 3600)
        sum_pv_feed = sum(pv_feed) * timestep / (1000 * 3600)
        sum_grid_import = sum(grid_import_dem) * timestep / (1000 * 3600)
        sum_grid_import_hp = sum(grid_import_hp) * timestep / (1000 * 3600)
        sum_grid_import_eh = sum(grid_import_eh) * timestep / (1000 * 3600)

        assert abs(el_energy + sum_hp_el_energy + sum_eh_el_energy\
               - (sum_pv_self + sum_grid_import + sum_grid_import_hp +
                  sum_grid_import_eh)) <= 0.001
        assert sum_hp_el_energy <= sum_grid_import_hp + sum_pv_self
        assert sum_eh_el_energy <= sum_grid_import_eh + sum_pv_self
        assert abs(sum_pv_energy - (sum_pv_self + sum_pv_feed)) <= 0.001

        assert abs(sh_energy + dhw_energy - (sum_hp_th_energy +
                                             sum_eh_th_energy)) <= 0.1