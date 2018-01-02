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


class TestCityAnnuityCalc():
    def test_city_annuity_chp_calc1(self):
        """
        Compares annuity calculation of CHP for single building district with
        reference value (CHP el. energy is only consumed within ref. building)
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
        t_init = 70  # °C
        capacity = 100  # kg
        t_max = 80  # °C
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

        #  ##################################################################
        #  Perform economic calculations
        #  ##################################################################

        #  Calculate capital and operation related annuity
        (cap_rel_ann, op_rel_ann) = \
            city_eco_calc.calc_cap_and_op_rel_annuity_city()

        #  Calculate demand related annuity
        dem_rel_annuity = city_eco_calc.calc_dem_rel_annuity_city()

        print('dem_rel_annuity: ', dem_rel_annuity)

        #  Calculate proceedings
        proc_rel_annuity = city_eco_calc.calc_proceeds_annuity_city()

        #  Calculate total annuity
        annuity = city_eco_calc.annuity_obj. \
            calc_total_annuity(ann_capital=cap_rel_ann,
                               ann_demand=dem_rel_annuity,
                               ann_op=op_rel_ann,
                               ann_proc=proc_rel_annuity)

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
        el_energy_self = chp_energy_el
        assert el_energy_self >= 0

        #  Estimate amount of bought electricity from the grid
        el_energy_import = el_energy - el_energy_self
        assert el_energy_import >= 0

        print('el_energy_self: ', el_energy_self)
        print('el_energy_import:', el_energy_import)

        #  Payment gas (with gas price (WITHOUT tax exception --> Within
        #  proceedings))

        # Calculate specific cost values for energy demands
        spec_cost_gas = \
            city_eco_calc.energy_balance.city.environment.prices. \
                get_spec_gas_cost(type='res',
                                  year=year,
                                  annual_demand=chp_energy_gas)

        print('spec_cost_gas: ', spec_cost_gas)

        payment_gas = spec_cost_gas * chp_energy_gas

        #  Payment el. grid (el. price)
        spec_cost_el = city_eco_calc.energy_balance.city.environment.prices. \
            get_spec_el_cost(type='res',
                             year=year,
                             annual_demand=el_energy_import)

        payment_electr = spec_cost_el * el_energy_import

        #  EEG payment on self produced and consumed CHP el. energy
        eeg_chp = \
            city_eco_calc.energy_balance.city.environment. \
                prices.get_eeg_payment(type='chp')

        eeg_payment = eeg_chp * el_energy_self

        #  Assert demand related annuity
        assert abs(dem_rel_annuity -
                   (payment_gas + payment_electr + eeg_payment)) \
               <= 0.01 * dem_rel_annuity

        #  Income/proceedings
        #  Tax return/exception for CHP
        #  Subsidies for chp_self_consumption

        # Get specific price (tax return)
        tax_exep_chp = city_eco_calc.energy_balance.city.environment. \
            prices.chp_tax_return

        tax_exception = tax_exep_chp * chp_energy_gas

        # Get specific price
        sub_chp_self = city_eco_calc.energy_balance.city.environment. \
            prices.get_sub_chp_self(
            p_nom=chp_el_pow)

        #  Estimate max. CHP payments per year
        chp_runtime_used_per_year = (el_energy_self) \
                                    * 1000 / chp_el_pow
        print('chp_runtime_used_per_year: ', chp_runtime_used_per_year)

        if chp_runtime_used_per_year <= 6000:
            chp_subsidy = sub_chp_self * el_energy_self
        else:  # Limited to 6000 h for each year (10 years reference)
            chp_subsidy = sub_chp_self * 6000 * chp_el_pow / 1000

        print('chp_subsidy: ', chp_subsidy)

        #  Assert proceedings
        assert abs(proc_rel_annuity - (tax_exception + chp_subsidy)) <= \
               0.01 * proc_rel_annuity

        print('Annuity factor: ', annuity_obj.ann_factor)

    def test_city_annuity_chp_calc2(self):
        """
        Compares annuity calculation of CHP for single building district with
        reference value (CHP also feeds into grid)
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
        t_init = 70  # °C
        capacity = 100  # kg
        t_max = 80  # °C
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

        #  ##################################################################
        #  Perform economic calculations
        #  ##################################################################

        #  Calculate capital and operation related annuity
        (cap_rel_ann, op_rel_ann) = \
            city_eco_calc.calc_cap_and_op_rel_annuity_city()

        #  Calculate demand related annuity
        dem_rel_annuity = city_eco_calc.calc_dem_rel_annuity_city()

        #  Calculate proceedings
        proc_rel_annuity = city_eco_calc.calc_proceeds_annuity_city()

        #  Calculate total annuity
        annuity = city_eco_calc.annuity_obj. \
            calc_total_annuity(ann_capital=cap_rel_ann,
                               ann_demand=dem_rel_annuity,
                               ann_op=op_rel_ann,
                               ann_proc=proc_rel_annuity)

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

        #  Payment gas (with gas price (WITHOUT tax exception --> Within
        #  proceedings))

        # Calculate specific cost values for energy demands
        spec_cost_gas = \
            city_eco_calc.energy_balance.city.environment.prices. \
                get_spec_gas_cost(type='res',
                                  year=year,
                                  annual_demand=chp_energy_gas)

        payment_gas = spec_cost_gas * chp_energy_gas

        #  EEG payment on self produced and consumed CHP el. energy
        eeg_chp = \
            city_eco_calc.energy_balance.city.environment. \
                prices.get_eeg_payment(type='chp')

        eeg_payment = eeg_chp * el_energy_self

        # #  Assert demand related annuity
        assert abs(dem_rel_annuity - (payment_gas + eeg_payment)) \
               <= 0.01 * dem_rel_annuity

        #  Income/proceedings
        #  Tax return/exception for CHP
        #  Subsidies for chp_self_consumption

        # Get specific price (tax return)
        tax_exep_chp = city_eco_calc.energy_balance.city.environment. \
            prices.chp_tax_return

        tax_exception = tax_exep_chp * chp_energy_gas

        print('Tax exception in Euro: ', tax_exception)

        # Get specific price
        sub_chp_self = city_eco_calc.energy_balance.city.environment. \
            prices.get_sub_chp_self(
            p_nom=chp_el_pow)

        #  Estimate max. CHP payments per year
        chp_runtime_used_per_year = 8760
        print('chp_runtime_used_per_year: ', chp_runtime_used_per_year)

        if chp_runtime_used_per_year <= 6000:
            chp_subsidy_self = sub_chp_self * el_energy_self
        else:  # Limited to 6000 h for each year (10 years reference)
            chp_subsidy_self = sub_chp_self * 6000 * p_nom / 1000

        print('chp_subsidy_self: ', chp_subsidy_self)

        #  Calculate specific subsidy payment in Euro/kWh
        spec_chp_sub = city_eco_calc.energy_balance.city.environment. \
            prices.get_sub_chp(p_nom=chp_el_pow)

        if chp_runtime_used_per_year <= 6000:
            chp_subsidy_sold = spec_chp_sub * el_energy_export
        else:  # Limited to 6000 h for each year (10 years reference)
            chp_subsidy_sold = spec_chp_sub * 6000 * (chp_el_pow - p_nom) \
                               / 1000

        print('chp_subsidy_sold: ', chp_subsidy_sold)

        #  Calculate EEX payments and avoided grid usage fee
        sub_eex = sum(
            city_eco_calc.energy_balance.city.
                environment.prices.eex_baseload) / len(
            city_eco_calc.energy_balance.city.
                environment.prices.eex_baseload)

        #  Get grid usage avoidance fee
        sub_avoid_grid_use = city_eco_calc.energy_balance.city.environment. \
            prices.grid_av_fee

        eex_payment = sub_eex * el_energy_export
        grid_av_pay = sub_avoid_grid_use * el_energy_export

        print('EEX payment: ', eex_payment)
        print('Avoided grid usage fee: ', grid_av_pay)

        # print('Delta abs: ')
        # delta_abs = abs(proc_rel_annuity - (tax_exception + chp_subsidy_self +
        #                                chp_subsidy_sold + eex_payment
        #                                + grid_av_pay))
        # print(delta_abs)
        # delta_rel = delta_abs / proc_rel_annuity
        # print('Delta rel: ', delta_rel)

        #  Assert proceedings
        assert abs(proc_rel_annuity - (tax_exception + chp_subsidy_self +
                                       chp_subsidy_sold + eex_payment
                                       + grid_av_pay)) <= \
               0.01 * proc_rel_annuity
