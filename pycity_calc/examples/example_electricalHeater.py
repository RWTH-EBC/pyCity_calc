#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 10 14:35:05 2015

@author: jsc-mth
"""
from __future__ import division
from __future__ import division
import numpy as np
from decimal import *

import pycity_calc.energysystems.electricalHeater as ElHeaterEx

import pycity_base.classes.Weather as Weather
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

    # Create Electrical Heater
    q_nominal = 10000
    t_max = 90
    eta = 0.98
    heater = ElHeaterEx.ElectricalHeaterExtended(environment, q_nominal, eta,
                                                 t_max)

    # Print results
    print()
    print(("Type: " + heater._kind))
    print()
    print(("Maximum electricity input: " + str(heater.pNominal)))
    print(("Maximum heat output: " + str(heater.qNominal)))
    print(("Efficiency: " + str(heater.eta)))
    print(("Maximum flow temperature: " + str(heater.tMax)))
    print(("Lower activation limit: " + str(heater.lowerActivationLimit)))

    print()
    print(("Nominals: " + str(heater.getNominalValues())))

    control_signal = 9000

    th_power_out = heater.calc_el_heater_thermal_power_output(control_signal)
    print('Thermal power output in W: ', th_power_out)

    el_power_in = heater.calc_el_heater_electric_power_input(th_power_out)
    print('El. power input in W: ', el_power_in)
    print()

    #  Calculate and save all important results of el. heater
    (th_power, el_power_in) = heater.calc_el_h_all_results(
        contro_signal=control_signal, time_index=0)

    print('Thermal power output in W: ', th_power)
    print('El. power input in W: ', el_power_in)


if __name__ == '__main__':
    #  Run program
    run_test()
