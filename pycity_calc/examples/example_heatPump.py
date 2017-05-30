#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu May 21 13:44:16 2015

@author: Thomas
"""

from __future__ import division

import numpy as np
import matplotlib.pyplot as plt

import pycity_calc.energysystems.heatPumpSimple as HP

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

    # Create HP
    qNominal = 100000  # W
    tMax = 50  # °C
    lowerActivationLimit = 0.5
    hpType = 'aw'  # air water hp
    tSink = 45  # °C

    heatPump = HP.heatPumpSimple(environment,
                                 q_nominal=qNominal,
                                 t_max=tMax,
                                 lower_activation_limit=lowerActivationLimit,
                                 hp_type=hpType,
                                 t_sink=tSink)

    # Print results
    print()
    print(("Type: " + heatPump._kind))
    print()
    print(("Maximum flow temperature: " + str(heatPump.tMax)))
    print(("Q_Nominal: " + str(qNominal) + " W"))
    print(("Lower activation limit: " + str(heatPump.lowerActivationLimit)))
    print(("Heat Pumpt type: " + str(heatPump.hp_type)))
    print(("Ground Temperature: " + str(
        heatPump.environment.temp_ground) + " °C"))

    # set outside temperature
    temp_source = -2  # °C

    carnot_cop = heatPump.calc_hp_carnot_cop(temp_source=temp_source)
    cop_quality_grade = heatPump.calc_hp_cop_with_quality_grade(
        temp_source=temp_source)

    thermal_demand = 80000  # W

    th_output = heatPump.calc_hp_th_power_output(thermal_demand)
    el_input = heatPump.calc_hp_el_power_input(thermal_demand, temp_source)

    print('Carnot COP: ', carnot_cop)
    print('COP (via Guetegrad): ', cop_quality_grade)
    print()
    print('Thermal power output in W: ', th_output)
    print('El. output in W: ', el_input)
    print()

    thermal_demand = 70000  # W

    #  Calculate and save all important results of hp
    (th_power_out, el_power_in) = \
        heatPump.calc_hp_all_results(control_signal=thermal_demand,
                                     t_source=temp_source, time_index=0)

    print('Thermal power output in W: ', th_power_out)
    print('El. output in W: ', el_power_in)


def run_hp_example(print_results=False):
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

    # Create HP
    qNominal = 100000  # W
    tMax = 50  # °C
    lowerActivationLimit = 0
    hpType = 'aw'  # air water hp
    tSink = 45  # °C

    heatpump = HP.heatPumpSimple(environment,
                                 q_nominal=qNominal,
                                 t_max=tMax,
                                 lower_activation_limit=lowerActivationLimit,
                                 hp_type=hpType,
                                 t_sink=tSink)

    timestep = environment.timer.timeDiscretization
    timesteps_total = environment.timer.timestepsTotal
    #  Generate time array
    time_array = np.arange(0, timesteps_total * timestep, timestep)

    cop_array = np.zeros(len(time_array))
    el_in_array = np.zeros(len(time_array))

    q_power_output = 10000

    #  Get temperature array (source: outdoor air)
    array_temp = environment.weather.tAmbient

    #  Run loop over timearray
    for i in range(len(time_array)):
        current_time = time_array[i]
        curr_temp = array_temp[i]
        cop_array[i] = \
            heatpump.calc_hp_cop_with_quality_grade(temp_source=curr_temp)
        el_in_array[i] = \
            heatpump.calc_hp_el_power_input(control_signal=q_power_output,
                                            t_source=curr_temp)

    print('COP over time:')
    print(cop_array)

    print('\nAverage COP:')
    print(np.mean((cop_array)))

    print('\nElectrical power input in Watt:')
    print(el_in_array)

    days_a_year = 365

    print('\nCalculation of annual operating factor (Jahresarbeitszahl):')
    hp_op_fac = q_power_output * days_a_year * 24 / (
        np.sum(el_in_array * timestep / 3600))
    print(hp_op_fac)

    if print_results:
        fig1 = plt.figure()
        fig1.add_subplot(311)
        plt.xlim([0, days_a_year])
        plt.ylim([0, 6])
        plt.plot(time_array / (3600 * 24), cop_array)
        plt.ylabel('COP')
        fig1.add_subplot(312)
        plt.xlim([0, days_a_year])
        plt.ylim([0, 5])
        plt.plot(time_array / (3600 * 24), el_in_array / 1000)
        plt.ylabel('El. power in kW')
        fig1.add_subplot(313)
        plt.xlim([0, days_a_year])
        plt.plot(time_array / (3600 * 24), array_temp)
        plt.ylabel('Outdoor temp. in deg C')
        plt.xlabel('Time in days')
        plt.show()


if __name__ == '__main__':
    #  Run program
    run_test()

    #  Run citypy example
    run_hp_example(print_results=True)
