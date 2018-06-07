#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example of chiller calculation
"""
from __future__ import division
from __future__ import division

import numpy as np
import matplotlib.pyplot as plt

import pycity_calc.energysystems.absorptionchiller as achill

import pycity_base.classes.Weather as Weather
import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.environment as env
import pycity_calc.environments.market as mark
import pycity_calc.environments.timer as time

import pycity_base.classes.demand.SpaceHeating as SpaceHeating


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

    # Create chiller
    q_nominal = 100000  # W
    t_min = 4  # °C
    lower_activation_limit = 0.2

    chiller = achill.AbsorptionChiller(
        environment,
        q_nominal=q_nominal,
        t_min=t_min,
        lower_activation_limit=lower_activation_limit)

    # Print results
    print()
    print(("Type: " + chiller._kind))
    print()
    print(("Minimal flow temperature: " + str(chiller.t_min)))
    print(("Q_Nominal: " + str(q_nominal) + " W"))
    print(("Lower activation limit: " + str(chiller.lower_activation_limit)))

    thermal_demand = 80000  # W

    th_output = chiller.calc_q_th_power_output(thermal_demand)
    th_input = chiller.calc_th_heat_power_input(thermal_demand)

    print('Cooling power output in W: ', th_output)
    print('Thermal Input in W: ', th_input)
    print()

    thermal_demand = 70000  # W

    #  Calculate and save all important results of hp
    (th_power_out, th_power_in) = chiller.calc_akm_all_results(
        thermal_demand,
        time_index=0,
        save_res=True)

    print('Cooling power output in W: ', th_power_out)
    print('El. output in W: ', th_power_in)


def run_chiller_example(print_results=False):
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

    # Create chiller
    q_nominal = 10000  # W
    t_min = 4  # °C
    lower_activation_limit = 0.2

    chiller = achill.AbsorptionChiller(
        environment,
        q_nominal=q_nominal,
        t_min=t_min,
        lower_activation_limit=lower_activation_limit)

    timestep = environment.timer.timeDiscretization
    timesteps_total = environment.timer.timestepsTotal
    #  Generate time array
    time_array = np.arange(0, timesteps_total * timestep, timestep)

    cop_array = np.zeros(len(time_array))
    th_in_array = np.zeros(len(time_array))

    q_power_output = 10000

    #  Make cooliong load. Use space heating as a test
    array_temp = SpaceHeating.SpaceHeating(
        environment,
        method=1,   # Standard load profile
        livingArea=146,
        specificDemand=166).get_power()

    #  Run loop over timearray
    for i in range(len(time_array)):
        current_time = time_array[i]
        curr_load = array_temp[i]
        cop_array[i] = \
            chiller.akm_cop(curr_load)
        th_in_array[i] = \
            chiller.calc_th_heat_power_input(curr_load)

    print('COP over time:')
    print(cop_array)

    print('\nAverage COP:')
    print(np.mean((cop_array)))

    print('\nHeat power input in Watt:')
    print(th_in_array)

    days_a_year = 365

    print('\nCalculation of annual operating factor (Jahresarbeitszahl):')
    chiller_op_fac = 1 / (q_power_output * days_a_year * 24 / (
        np.sum(th_in_array * timestep / 3600)))
    print(chiller_op_fac)

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
        plt.plot(time_array / (3600 * 24), th_in_array / 1000)
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
    run_chiller_example(print_results=True)
