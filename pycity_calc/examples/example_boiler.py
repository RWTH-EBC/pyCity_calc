#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 10 14:32:46 2015

@author: jsc-mth
"""
from __future__ import division
from __future__ import division
import numpy as np
import pycity_calc.energysystems.boiler as Boiler

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

    # Create Boiler
    lower_activation_limit = 0.5
    q_nominal = 10000
    t_max = 90
    eta = 0.9
    heater = Boiler.BoilerExtended(environment, q_nominal, eta, t_max,
                                   lower_activation_limit)

    # Print results
    print()
    print(("Type: " + heater._kind))
    print(("Efficiency: " + str(heater.eta)))
    print(("Maximum heat output: " + str(heater.qNominal)))
    print(("Maximum flow temperature: " + str(heater.tMax)))
    print(("Lower activation limit: " + str(heater.lowerActivationLimit)))

    print()
    print(("Nominals: " + str(heater.getNominalValues())))

    # create example thermal demand
    thermal_demand = 8500

    thermal_output = heater.calc_boiler_thermal_power_output(thermal_demand)
    fuel_input = heater.calc_boiler_fuel_power_input(thermal_output)

    print('Thermal power output in Watt: ', thermal_output)
    print('Fuel power consumption in Watt: ', round(fuel_input, 0))
    print()

    thermal_power = 9000  # in W

    #  Calculate and save all important results of boiler
    (th_power, fuel_power_in) = heater.calc_boiler_all_results(
        control_signal=thermal_power, time_index=0)

    print('Thermal power output in Watt: ', th_power)
    print('Fuel power consumption in Watt: ', round(fuel_power_in, 0))


if __name__ == '__main__':
    #  Run program
    run_test()
