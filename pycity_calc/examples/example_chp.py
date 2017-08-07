#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 10 14:25:16 2015

@author: tsz
"""
from __future__ import division
from __future__ import division
import numpy as np
import pycity_calc.energysystems.chp as CHP
import pycity.classes.Weather as Weather
import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.environment as env
import pycity_calc.environments.market as mark
import pycity_calc.environments.timer as time


def run_test():
    # Create environment
    year = 2010
    timestep = 3600  # Timestep in seconds
    location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop

    timer = time.TimerExtended(timestep=timestep, year=year)
    weather = Weather.Weather(timer, useTRY=True)
    market = mark.Market()
    co2em = co2.Emissions(year=year)
    environment = env.EnvironmentExtended(timer, weather, prices=market,
                                          location=location, co2em=co2em)
    # Create CHP
    lower_activation_limit = 0.6
    q_nominal = 10000
    t_max = 86
    p_nominal = 4500
    eta_total = 0.87
    chp = CHP.ChpExtended(environment=environment,
                          p_nominal=p_nominal,
                          q_nominal=q_nominal,
                          eta_total=eta_total,
                          t_max=t_max,
                          lower_activation_limit=lower_activation_limit,
                          thermal_operation_mode=True)

    # Print results
    print()
    print(("Type: " + chp._kind))
    print()
    print(("Maximum electricity output: " + str(chp.pNominal)))
    print(("Total efficiency: " + str(chp.omega)))
    print(("Power to heat ratio: " + str(chp.sigma)))
    print(("Maximum heat output: " + str(chp.qNominal)))
    print(("Maximum flow temperature: " + str(chp.tMax)))
    print(("Lower activation limit: " + str(chp.lowerActivationLimit)))
    print(("Thermal operation mode? " + str(chp.thermal_operation_mode)))

    ##########################################################################
    ########################## thermal operation #############################
    ##########################################################################
    print()
    print(("Nominals: " + str(chp.getNominalValues())))

    thermal_p = 7500

    thermal_power_out = chp.thOperation_calc_chp_th_power_output(thermal_p)
    print('Thermal power output of chp in W: ', thermal_power_out)

    el_p_out = chp.thOperation_calc_chp_el_power_output(thermal_p)
    print('Electrial power output of chp in W: ', el_p_out)

    fuel_power_in = chp.thOperation_calc_chp_fuel_power_input(thermal_p)
    print('Fuel power input of chp in W: ', fuel_power_in)

    th_eff = chp.thOperation_calc_chp_th_efficiency(thermal_p)
    print('Thermal efficiency of chp: ', th_eff)

    el_eff = chp.thOperation_calc_chp_el_efficiency(thermal_p)
    print('El. efficiency of chp: ', el_eff)
    print()

    #  Calculate and save all important results of chp (thermal mode)
    (th_power, el_power, fuel_power_in) = chp.th_op_calc_all_results(
        control_signal=thermal_p, time_index=0)

    print('Thermal power output of chp in W: ', th_power)
    print('Electrial power output of chp in W: ', el_power)
    print('Fuel power input of chp in W: ', fuel_power_in)

    ##########################################################################
    ########################## electr. operation #############################
    ##########################################################################

    chp.change_operation_mode()

    print(("Thermal operation mode? " + str(chp.thermal_operation_mode)))
    print()
    print(("Nominals: " + str(chp.getNominalValues())))

    el_p = 4500

    thermal_power_out = chp.elOperation_calc_chp_th_power_output(el_p)
    print('Thermal power output of chp in W: ', thermal_power_out)

    el_p_out = chp.elOperation_calc_chp_el_power_output(el_p)
    print('Electrial power output of chp in W: ', el_p_out)

    fuel_power_in = chp.elOperation_calc_chp_fuel_power_input(el_p)
    print('Fuel power input of chp in W: ', fuel_power_in)

    th_eff = chp.elOperation_calc_chp_th_efficiency(el_p)
    print('Thermal efficiency of chp: ', th_eff)

    el_eff = chp.elOperation_calc_chp_el_efficiency(el_p)
    print('El. efficiency of chp: ', el_eff)
    print()

    #  Calculate and save all important results of chp (thermal mode)
    (th_power, el_power, fuel_power_in) = chp.el_op_calc_all_results(
        control_signal=el_p, time_index=0)

    print('Thermal power output of chp in W: ', th_power)
    print('Electrial power output of chp in W: ', el_power)
    print('Fuel power input of chp in W: ', fuel_power_in)

if __name__ == '__main__':
    #  Run program
    run_test()
