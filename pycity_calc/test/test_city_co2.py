#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
from __future__ import division

import numpy as np
import shapely.geometry.point as point

import pycity_base.classes.Weather as Weather
import pycity_base.classes.demand.SpaceHeating as spaceheat
import pycity_base.classes.demand.ElectricalDemand as elecdemand
import pycity_base.classes.supply.BES as BES
import pycity_base.classes.supply.PV as PV
import pycity_base.classes.demand.Apartment as apart

import pycity_calc.cities.city as cit
import pycity_calc.buildings.building as build
import pycity_calc.environments.co2emissions as co2em
import pycity_calc.environments.environment as env
import pycity_calc.environments.timer as time
import pycity_calc.environments.germanmarket as germanmarket
import pycity_calc.simulation.energy_balance.city_eb_calc as cityeb
import pycity_calc.energysystems.chp as chpsys
import pycity_calc.energysystems.battery as bat
import pycity_calc.energysystems.boiler as boil
import pycity_calc.energysystems.electricalHeater as ehsys
import pycity_calc.energysystems.heatPumpSimple as hpsys
import pycity_calc.energysystems.thermalEnergyStorage as sto
import pycity_calc.economic.annuity_calculation as annu
import pycity_calc.economic.city_economic_calc as citecon


class TestCityCO2():
    def test_city_co2_with_pv_only(self):
        """
        Compares CO2 values for city with single building, PV and electrical
        demand, only.
        """

        #  Create extended environment of pycity_calc
        year = 2017
        timestep = 900  # Timestep in seconds
        location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop
        altitude = 55  # Altitude of Bottrop

        #  Generate environment
        #  Generate timer object
        timer = time.TimerExtended(timestep=timestep, year=year)

        nb_timesteps = timer.timestepsTotal

        #  Generate weather object
        weather = Weather.Weather(timer, useTRY=True, location=location,
                                  altitude=altitude)

        #  Generate market object
        gmarket = germanmarket.GermanMarket()

        #  Generate co2 emissions object
        co2emissions = co2em.Emissions(year=year)

        #  Generate environment
        environment = env.EnvironmentExtended(timer, weather,
                                              prices=gmarket,
                                              location=location,
                                              co2em=co2emissions)

        #  City
        city = cit.City(environment=environment)

        #  One building
        building = build.BuildingExtended(environment=environment,
                                          build_type=0)

        #  One apartment
        apartment = apart.Apartment(environment=environment)

        p_nom = 500  # in W

        array_el = np.ones(environment.timer.timestepsTotal) * p_nom
        el_demand = elecdemand.ElectricalDemand(
            environment=environment,
            method=0,
            loadcurve=array_el)

        #  Add energy demands to apartment
        apartment.addEntity(el_demand)

        #  Add apartment to extended building
        building.addEntity(entity=apartment)

        #  Add building to city
        pos = point.Point(0, 0)
        city.add_extended_building(extended_building=building, position=pos)

        #  BES
        bes = BES.BES(environment=environment)

        #  PV
        pv_simple = PV.PV(environment=environment, area=10, eta=0.15)

        boiler = boil.BoilerExtended(environment=environment,
                                     q_nominal=1, # Dummy value
                                     eta=1)

        #  Add devices to BES
        bes.addMultipleDevices([pv_simple, boiler])

        #  Add BES to building
        building.addEntity(bes)

        #  Generate energy balance object
        energy_balance = cityeb.CityEBCalculator(city=city)

        #  Generate annuity object instance
        annuity_obj = annu.EconomicCalculation(interest=0.000000001,
                                               #  Zero interest undefined,
                                               #  thus, using small value
                                               price_ch_cap=1,
                                               price_ch_dem_gas=1,
                                               price_ch_dem_el=1,
                                               price_ch_dem_cool=1,
                                               price_ch_op=1,
                                               price_ch_proc_chp=1.0,
                                               price_ch_proc_pv=1.0,
                                               price_ch_eeg_chp=1.0,
                                               price_ch_eeg_pv=1,
                                               price_ch_eex=1,
                                               price_ch_grid_use=1,
                                               price_ch_chp_sub=1,
                                               price_ch_chp_self=1,
                                               price_ch_chp_tax_return=1,
                                               price_ch_pv_sub=1,
                                               price_ch_dem_el_hp=1)

        #  Generate city economic calculator
        city_eco_calc = citecon.CityAnnuityCalc(annuity_obj=annuity_obj,
                                                energy_balance=energy_balance)

        #  ##################################################################
        #  Run energy balance
        #  ##################################################################

        #  Calc. city energy balance
        city_eco_calc.energy_balance.calc_city_energy_balance()

        #  Perform final energy anaylsis
        city_eco_calc.energy_balance.calc_final_energy_balance_city()

        #  Perform emissions calculation
        co2 = city_eco_calc.energy_balance.calc_co2_emissions(
            el_mix_for_chp=True)

        #  Total el. demand
        el_energy = building.get_annual_el_demand()

        #  Get reference co2 emission factor for electricity
        co2_factor_el_mix = city.environment.co2emissions.co2_factor_el_mix

        #  Get el. power array of PV
        pv_power_array = pv_simple.getPower()

        #  El. energy PV
        pv_el_energy = sum(pv_power_array) * timestep / (1000 * 3600)

        co2_ref = (el_energy - pv_el_energy) * co2_factor_el_mix

        assert abs(co2 - co2_ref) <= 0.001 * co2

    def test_city_co2_with_pv_only_no_el_demand(self):
        """
        Compares CO2 values for city with single building, PV (no electr.
        demand)
        """

        #  Create extended environment of pycity_calc
        year = 2017
        timestep = 900  # Timestep in seconds
        location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop
        altitude = 55  # Altitude of Bottrop

        #  Generate environment
        #  Generate timer object
        timer = time.TimerExtended(timestep=timestep, year=year)

        #  Generate weather object
        weather = Weather.Weather(timer, useTRY=True, location=location,
                                  altitude=altitude)

        #  Generate market object
        gmarket = germanmarket.GermanMarket()

        #  Generate co2 emissions object
        co2emissions = co2em.Emissions(year=year)

        #  Generate environment
        environment = env.EnvironmentExtended(timer, weather,
                                              prices=gmarket,
                                              location=location,
                                              co2em=co2emissions)

        #  City
        city = cit.City(environment=environment)

        #  One building
        building = build.BuildingExtended(environment=environment,
                                          build_type=0)

        #  One apartment
        apartment = apart.Apartment(environment=environment)

        p_nom = 0  # in W

        array_el = np.ones(environment.timer.timestepsTotal) * p_nom
        el_demand = elecdemand.ElectricalDemand(
            environment=environment,
            method=0,
            loadcurve=array_el)

        #  Add energy demands to apartment
        apartment.addEntity(el_demand)

        #  Add apartment to extended building
        building.addEntity(entity=apartment)

        #  Add building to city
        pos = point.Point(0, 0)
        city.add_extended_building(extended_building=building, position=pos)

        #  BES
        bes = BES.BES(environment=environment)

        #  PV
        pv_simple = PV.PV(environment=environment, area=10, eta=0.15)

        boiler = boil.BoilerExtended(environment=environment,
                                     q_nominal=1, # Dummy value
                                     eta=1)

        #  Add devices to BES
        bes.addMultipleDevices([pv_simple, boiler])

        #  Add BES to building
        building.addEntity(bes)

        #  Generate energy balance object
        energy_balance = cityeb.CityEBCalculator(city=city)

        #  Generate annuity object instance
        annuity_obj = annu.EconomicCalculation(interest=0.000000001,
                                               #  Zero interest undefined,
                                               #  thus, using small value
                                               price_ch_cap=1,
                                               price_ch_dem_gas=1,
                                               price_ch_dem_el=1,
                                               price_ch_dem_cool=1,
                                               price_ch_op=1,
                                               price_ch_proc_chp=1.0,
                                               price_ch_proc_pv=1.0,
                                               price_ch_eeg_chp=1.0,
                                               price_ch_eeg_pv=1,
                                               price_ch_eex=1,
                                               price_ch_grid_use=1,
                                               price_ch_chp_sub=1,
                                               price_ch_chp_self=1,
                                               price_ch_chp_tax_return=1,
                                               price_ch_pv_sub=1,
                                               price_ch_dem_el_hp=1)

        #  Generate city economic calculator
        city_eco_calc = citecon.CityAnnuityCalc(annuity_obj=annuity_obj,
                                                energy_balance=energy_balance)

        #  ##################################################################
        #  Run energy balance
        #  ##################################################################

        #  Calc. city energy balance
        city_eco_calc.energy_balance.calc_city_energy_balance()

        #  Perform final energy anaylsis
        city_eco_calc.energy_balance.calc_final_energy_balance_city()

        #  Perform emissions calculation
        co2 = city_eco_calc.energy_balance.calc_co2_emissions(
            el_mix_for_chp=True)

        assert co2 < 0

        #  Get reference co2 emission factor for electricity
        co2_factor_el_mix = city.environment.co2emissions.co2_factor_el_mix

        #  Get el. power array of PV
        pv_power_array = pv_simple.getPower()

        #  El. energy PV
        pv_el_energy = sum(pv_power_array) * timestep / (1000 * 3600)

        co2_ref = (- pv_el_energy) * co2_factor_el_mix

        assert abs(co2 - co2_ref) <= 0.001 * abs(co2)

    def test_city_co2_chp_calc1(self):
        """

        """

        #  Create extended environment of pycity_calc
        year = 2017
        timestep = 900  # Timestep in seconds
        location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop
        altitude = 55  # Altitude of Bottrop

        #  Generate environment
        #  Generate timer object
        timer = time.TimerExtended(timestep=timestep, year=year)

        nb_timesteps = timer.timestepsTotal

        #  Generate weather object
        weather = Weather.Weather(timer, useTRY=True, location=location,
                                  altitude=altitude)

        #  Generate market object
        gmarket = germanmarket.GermanMarket()

        #  Generate co2 emissions object
        co2emissions = co2em.Emissions(year=year)

        #  Generate environment
        environment = env.EnvironmentExtended(timer, weather,
                                              prices=gmarket,
                                              location=location,
                                              co2em=co2emissions)

        #  City
        city = cit.City(environment=environment)

        #  One building
        building = build.BuildingExtended(environment=environment,
                                          build_type=0)

        #  One apartment
        apartment = apart.Apartment(environment=environment)

        #  Initialize constant space heating and electrical load
        q_nom = 1000  # in W

        array_sh = np.ones(environment.timer.timestepsTotal) * q_nom
        heat_demand = spaceheat.SpaceHeating(environment=environment,
                                             method=0, loadcurve=array_sh)

        p_nom = 300  # in W

        array_el = np.ones(environment.timer.timestepsTotal) * p_nom
        el_demand = elecdemand.ElectricalDemand(
            environment=environment,
            method=0,
            loadcurve=array_el)

        #  Add energy demands to apartment
        apartment.addMultipleEntities([heat_demand, el_demand])

        #  Add apartment to extended building
        building.addEntity(entity=apartment)

        #  Add building to city
        pos = point.Point(0, 0)
        city.add_extended_building(extended_building=building, position=pos)

        #  BES
        bes = BES.BES(environment=environment)

        #  CHP
        chp = chpsys.ChpExtended(environment=environment,
                                 q_nominal=q_nom,
                                 p_nominal=0.001,  # Dummmy value
                                 eta_total=1)

        #  ASUE calc --> el. power --> Get el. power
        chp_el_pow = chp.pNominal
        print('CHP el. power in Watt: ', chp_el_pow)

        #  Add CHP to BES
        bes.addDevice(chp)

        #  Create thermal storage
        # Create Heating Device
        t_init = 55  # °C
        capacity = 100  # kg
        t_max = 60  # °C
        t_min = 20  # °C
        cp = 4186  # J/kgK
        t_surroundings = 20  # °C
        k_losses = 0  # W/(Km²)  #  Losses set to zero
        rho = 1000  # kg / m³
        tes = sto.thermalEnergyStorageExtended(environment=environment,
                                               t_init=t_init,
                                               c_p=cp,
                                               capacity=capacity,
                                               t_max=t_max,
                                               t_min=t_min,
                                               t_surroundings=t_surroundings,
                                               k_loss=k_losses,
                                               rho=rho)

        #  Add TES to BES
        bes.addDevice(tes)

        #  Add BES to building
        building.addEntity(bes)

        #  Generate energy balance object
        energy_balance = cityeb.CityEBCalculator(city=city)

        #  Generate annuity object instance
        annuity_obj = annu.EconomicCalculation(interest=0.000000001,
                                               #  Zero interest undefined,
                                               #  thus, using small value
                                               price_ch_cap=1,
                                               price_ch_dem_gas=1,
                                               price_ch_dem_el=1,
                                               price_ch_dem_cool=1,
                                               price_ch_op=1,
                                               price_ch_proc_chp=1.0,
                                               price_ch_proc_pv=1.0,
                                               price_ch_eeg_chp=1.0,
                                               price_ch_eeg_pv=1,
                                               price_ch_eex=1,
                                               price_ch_grid_use=1,
                                               price_ch_chp_sub=1,
                                               price_ch_chp_self=1,
                                               price_ch_chp_tax_return=1,
                                               price_ch_pv_sub=1,
                                               price_ch_dem_el_hp=1)

        #  Generate city economic calculator
        city_eco_calc = citecon.CityAnnuityCalc(annuity_obj=annuity_obj,
                                                energy_balance=energy_balance)

        #  ##################################################################
        #  Run energy balance
        #  ##################################################################

        #  Calc. city energy balance
        city_eco_calc.energy_balance.calc_city_energy_balance()

        #  Perform final energy anaylsis
        city_eco_calc.energy_balance.calc_final_energy_balance_city()

        #  Perform emissions calculation
        co2 = city_eco_calc.energy_balance.calc_co2_emissions(
            el_mix_for_chp=True)

        #  Perform simplified reference annuity calculation
        #  ################################################################

        #  Total space heating energy
        sh_energy = building.get_annual_space_heat_demand()

        #  Total el. demand
        el_energy = building.get_annual_el_demand()

        print('Total space heating demand in kWh: ', sh_energy)
        print('Total electrical demand in kWh: ', el_energy)

        #  Get amount of CHP-generated el. energy
        chp_energy_el = sum(chp.totalPOutput) * timestep / (1000 * 3600)

        #  Get CHP gas demand
        chp_energy_gas = sum(chp.array_fuel_power) * timestep / (1000 * 3600)

        print('chp_energy_el: ', chp_energy_el)
        print('chp_energy_gas:', chp_energy_gas)

        #  Estimate amount of self-used electric energy
        el_energy_self = chp_energy_el
        assert el_energy_self >= 0

        #  Estimate amount of bought electricity from the grid
        el_energy_import = el_energy - el_energy_self
        assert el_energy_import >= 0

        print('el_energy_self: ', el_energy_self)
        print('el_energy_import:', el_energy_import)

        co2_gas = city.environment.co2emissions.co2_factor_gas
        co2_el = city.environment.co2emissions.co2_factor_el_mix

        co2_ref = co2_gas * chp_energy_gas + co2_el * el_energy_import

        assert abs(co2_ref - co2) <= 0.001 * co2

        gas_ref = sh_energy * (chp_el_pow + q_nom) / q_nom

        assert abs(chp_energy_gas - gas_ref) <= 0.001 * gas_ref

        chp_el_gen_ref = gas_ref * chp_el_pow / (chp_el_pow + q_nom)

        assert abs(chp_el_gen_ref - chp_energy_el) <= 0.001 * chp_energy_el

        el_energy_import_b = el_energy - chp_el_gen_ref

        co2_ref_b = co2_gas * gas_ref + co2_el * el_energy_import_b

        assert abs(co2_ref_b - co2) <= 0.001 * co2

    def test_city_co2_chp_calc2(self):
        """

        """

        #  Create extended environment of pycity_calc
        year = 2010
        timestep = 900  # Timestep in seconds
        location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop
        altitude = 55  # Altitude of Bottrop

        #  Generate environment
        #  Generate timer object
        timer = time.TimerExtended(timestep=timestep, year=year)

        nb_timesteps = timer.timestepsTotal

        #  Generate weather object
        weather = Weather.Weather(timer, useTRY=True, location=location,
                                  altitude=altitude)

        #  Generate market object
        gmarket = germanmarket.GermanMarket()

        #  Generate co2 emissions object
        co2emissions = co2em.Emissions(year=year)

        #  Generate environment
        environment = env.EnvironmentExtended(timer, weather,
                                              prices=gmarket,
                                              location=location,
                                              co2em=co2emissions)

        #  City
        city = cit.City(environment=environment)

        #  One building
        building = build.BuildingExtended(environment=environment,
                                          build_type=0)

        #  One apartment
        apartment = apart.Apartment(environment=environment)

        #  Initialize constant space heating and electrical load
        q_nom = 1000  # in W

        array_sh = np.ones(environment.timer.timestepsTotal) * q_nom
        heat_demand = spaceheat.SpaceHeating(environment=environment,
                                             method=0, loadcurve=array_sh)

        p_nom = 100  # in W

        array_el = np.ones(environment.timer.timestepsTotal) * p_nom
        el_demand = elecdemand.ElectricalDemand(
            environment=environment,
            method=0,
            loadcurve=array_el)

        #  Add energy demands to apartment
        apartment.addMultipleEntities([heat_demand, el_demand])

        #  Add apartment to extended building
        building.addEntity(entity=apartment)

        #  Add building to city
        pos = point.Point(0, 0)
        city.add_extended_building(extended_building=building, position=pos)

        #  BES
        bes = BES.BES(environment=environment)

        #  CHP
        chp = chpsys.ChpExtended(environment=environment,
                                 q_nominal=q_nom,
                                 p_nominal=0.001,  # Dummmy value
                                 eta_total=1)

        #  ASUE calc --> el. power --> Get el. power
        chp_el_pow = chp.pNominal
        print('CHP el. power in Watt: ', chp_el_pow)

        #  Add CHP to BES
        bes.addDevice(chp)

        #  Create thermal storage
        # Create Heating Device
        t_init = 55  # °C
        capacity = 100  # kg
        t_max = 60  # °C
        t_min = 20  # °C
        cp = 4186  # J/kgK
        t_surroundings = 20  # °C
        k_losses = 0  # W/(Km²)  #  Losses set to zero
        rho = 1000  # kg / m³
        tes = sto.thermalEnergyStorageExtended(environment=environment,
                                               t_init=t_init,
                                               c_p=cp,
                                               capacity=capacity,
                                               t_max=t_max,
                                               t_min=t_min,
                                               t_surroundings=t_surroundings,
                                               k_loss=k_losses,
                                               rho=rho)

        #  Add TES to BES
        bes.addDevice(tes)

        #  Add BES to building
        building.addEntity(bes)

        #  Generate energy balance object
        energy_balance = cityeb.CityEBCalculator(city=city)

        #  Generate annuity object instance
        annuity_obj = annu.EconomicCalculation(interest=0.0000001,
                                               #  Zero interest undefined,
                                               #  thus, using small value
                                               price_ch_cap=1,
                                               price_ch_dem_gas=1,
                                               price_ch_dem_el=1,
                                               price_ch_dem_cool=1,
                                               price_ch_op=1,
                                               price_ch_proc_chp=1.0,
                                               price_ch_proc_pv=1.0,
                                               price_ch_eeg_chp=1.0,
                                               price_ch_eeg_pv=1,
                                               price_ch_eex=1,
                                               price_ch_grid_use=1,
                                               price_ch_chp_sub=1,
                                               price_ch_chp_self=1,
                                               price_ch_chp_tax_return=1,
                                               price_ch_pv_sub=1,
                                               price_ch_dem_el_hp=1)

        #  Generate city economic calculator
        city_eco_calc = citecon.CityAnnuityCalc(annuity_obj=annuity_obj,
                                                energy_balance=energy_balance)

        #  ##################################################################
        #  Run energy balance
        #  ##################################################################

        #  Calc. city energy balance
        city_eco_calc.energy_balance.calc_city_energy_balance()

        #  Perform final energy anaylsis
        city_eco_calc.energy_balance.calc_final_energy_balance_city()

        #  Perform emissions calculation
        co2 = city_eco_calc.energy_balance.calc_co2_emissions(
            el_mix_for_chp=True)

        #  Perform simplified reference annuity calculation
        #  ################################################################
        #  Estimate amount of gas used by CHP

        #  Total space heating energy
        sh_energy = building.get_annual_space_heat_demand()

        #  Total el. demand
        el_energy = building.get_annual_el_demand()

        print('Total space heating demand in kWh: ', sh_energy)
        print('Total electrical demand in kWh: ', el_energy)

        #  Get amount of CHP-generated el. energy
        chp_energy_el = sum(chp.totalPOutput) * timestep / (1000 * 3600)

        #  Get CHP gas demand
        chp_energy_gas = sum(chp.array_fuel_power) * timestep / (1000 * 3600)

        print('chp_energy_el: ', chp_energy_el)
        print('chp_energy_gas:', chp_energy_gas)

        #  Estimate amount of self-used electric energy
        el_energy_self = el_energy
        assert el_energy_self >= 0

        #  Estimate amount of exported electricity to the grid
        el_energy_export = chp_energy_el - el_energy
        assert el_energy_export >= 0

        co2_gas = city.environment.co2emissions.co2_factor_gas
        co2_el = city.environment.co2emissions.co2_factor_el_mix

        co2_ref = co2_gas / 1.11 * chp_energy_gas - co2_el * el_energy_export

        assert abs(co2_ref - co2) <= 0.001 * co2

        gas_ref = sh_energy * (chp_el_pow + q_nom) / q_nom

        assert abs(chp_energy_gas - gas_ref) <= 0.001 * gas_ref

        chp_el_gen_ref = gas_ref * chp_el_pow / (chp_el_pow + q_nom)

        assert abs(chp_el_gen_ref - chp_energy_el) <= 0.001 * chp_energy_el

        el_energy_export_b = chp_el_gen_ref - el_energy

        co2_ref_b = co2_gas * gas_ref / 1.11 - co2_el * el_energy_export_b

        assert abs(co2_ref_b - co2) <= 0.001 * co2
