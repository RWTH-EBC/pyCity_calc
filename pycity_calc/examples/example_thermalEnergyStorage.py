#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 10 14:37:31 2015
"""
from __future__ import division
from __future__ import division
import numpy as np
import matplotlib.pyplot as plt

import pycity_calc.energysystems.thermalEnergyStorage as TES

import pycity_base.classes.Weather as Weather
import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.environment as env
import pycity_calc.environments.market as mark
import pycity_calc.environments.timer as time


def run_test():
    # Create environment
    year = 2010
    timestep = 900  # Timestep in seconds
    location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop

    timer = time.TimerExtended(timestep=timestep, year=year)
    weather = Weather.Weather(timer, useTRY=True)
    market = mark.Market()
    co2em = co2.Emissions(year=year)
    environment = env.EnvironmentExtended(timer, weather, prices=market,
                                          location=location, co2em=co2em)

    # Create Heating Device
    t_init = 50  # °C
    capacity = 100000  # kg
    t_max = 80  # °C
    t_min = 20  # °C
    cp = 4186  # J/kgK
    t_surroundings = 20  # °C
    k_losses = 0.7  # W/(Km²)
    rho = 1000  # kg / m³
    tes = TES.thermalEnergyStorageExtended(environment=environment,
                                           t_init=t_init,
                                           c_p=cp,
                                           capacity=capacity,
                                           t_max=t_max,
                                           t_min=t_min,
                                           t_surroundings=t_surroundings,
                                           k_loss=k_losses,
                                           rho=rho)

    # extended functions
    volume = tes.calc_storage_volume()
    diameter = tes.calc_storage_diameter()
    height = tes.calc_storage_height()
    outside_area = tes.calc_storage_outside_area()
    stored_energy = tes.calc_storage_curr_amount_of_energy()

    print()
    print(("Storage volume: " + str(volume)))
    print(("Storage diameter: " + str(diameter)))
    print(("Storage height: " + str(height)))
    print(("Storage outside area: " + str(outside_area)))
    print(("currently stored energy: " + str(stored_energy) + " kWh"))

    tes.use_outside_temp = True
    t_current = tes.t_current
    q_in = 0  # W
    q_out = 12000000  # W
    t_ambient = 10  # °C

    # calculate the maximal possible thermal input and output
    q_out_max = tes.calc_storage_q_out_max(t_ambient=t_ambient, q_in=0)
    q_in_max = tes.calc_storage_q_in_max(t_ambient=t_ambient, q_out=0)

    # check if thermal input and output is possible
    q_out_possible = tes.storage_q_out_possible(
        control_signal=q_out_max + 100000, t_ambient=t_ambient)
    q_in_possible = tes.storage_q_in_possible(control_signal=q_in_max + 100000,
                                              t_ambient=t_ambient)

    # calculate the new storage temperature
    t_new_out = tes.calc_storage_temp_for_next_timestep(q_in=0, q_out=q_out,
                                                        t_prior=t_current,
                                                        t_ambient=t_ambient,
                                                        set_new_temperature=False)
    t_new_in = tes.calc_storage_temp_for_next_timestep(q_in=q_out, q_out=0,
                                                       t_prior=t_current,
                                                       t_ambient=t_ambient,
                                                       set_new_temperature=True)

    # calculate the corresponding storage energy
    q_new = tes.calc_storage_curr_amount_of_energy()

    print()
    print(("Prior Temperature: " + str(t_current) + " °C"))
    print(("currently stored energy: " + str(stored_energy) + " kWW"))
    print()
    print("Maximal thermal Output: " + str(q_out_max) + " W")
    print("Maximal thermal Input: " + str(q_in_max) + " W")
    print()
    print("Thermal input of " + str(q_in_max + 100000) + " W possible? " + str(
        q_in_possible))
    print(
        "Thermal output of " + str(q_out_max + 10000) + " W possible? " + str(
            q_out_possible))
    print()
    print(("Q_in: " + str(q_in) + " W. Q_out: " + str(q_out) + " W @ " + str(
        t_ambient) + " °C"))
    print(("new temperature after charging: " + str(t_new_in) + " °C"))
    print(("new temperature after discharging: " + str(t_new_out) + " °C"))
    print(("new stored energy: " + str(q_new) + " kWh"))


def run_example_tes(print_results=False):
    # Create environment
    year = 2010
    timestep = 900  # Timestep in seconds
    location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop

    timer = time.TimerExtended(timestep=timestep, year=year)
    weather = Weather.Weather(timer, useTRY=True)
    market = mark.Market()
    co2em = co2.Emissions(year=year)
    environment = env.EnvironmentExtended(timer, weather, prices=market,
                                          location=location, co2em=co2em)

    #  Generate tes object
    my_tes = TES.thermalEnergyStorageExtended(environment, t_init=80,
                                              capacity=200)

    #  Calc storage diameter
    d_tes = my_tes.calc_storage_diameter()
    print('Storage diameter is', round(d_tes, 2), 'm')

    #  Calc storage height
    h_tes = my_tes.calc_storage_height()
    print('Storage height is', round(h_tes, 2), 'm')

    #  Calc storage volume
    volume_tes = my_tes.calc_storage_volume()
    print('Storage volume is', round(volume_tes, 2), 'm^3')

    environment = my_tes.environment

    #  Generate time array from environment
    timestep = environment.timer.timeDiscretization
    timesteps_total = environment.timer.timestepsTotal
    time_array = np.arange(0, timestep * timesteps_total, timestep)
    temp_storage_array = np.zeros(len(time_array))
    # Dummy array for storage temperature results

    #  Calculate cooldown of storage for constant surrounding temperature
    #  and no demand or generation
    for i in range(len(time_array)):
        temp_current = my_tes.t_current

        temp_new = my_tes.calc_storage_temp_for_next_timestep(q_in=0, q_out=0,
                                                              t_prior=temp_current,
                                                              set_new_temperature=True,
                                                              save_res=True,
                                                              time_index=i)

        temp_storage_array[i] = temp_new

    print('Storage temperature over time in degree Celsius:',
          temp_storage_array)

    if print_results:
        plt.plot(time_array / (3600 * 24), temp_storage_array)
        plt.xlim([0, 50])  # 50 days max
        plt.annotate('T_env = 20 deg C (const.)', xy=(15, 30), xytext=(15, 30))
        plt.xlabel('Time in days')
        plt.ylabel('Storage temp. in degree C')
        plt.show()


def run_example_tes2(print_results=False):
    #  Generate environment
    year = 2010
    timestep = 900  # Timestep in seconds
    location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop

    timer = time.TimerExtended(timestep=timestep, year=year)
    weather = Weather.Weather(timer, useTRY=True)
    market = mark.Market()
    co2em = co2.Emissions(year=year)
    environment = env.EnvironmentExtended(timer, weather, prices=market,
                                          location=location, co2em=co2em)

    #  Generate tes object
    my_tes = TES.thermalEnergyStorageExtended(environment, t_init=20,
                                              capacity=500)

    #  Generate time array from environment
    timestep = environment.timer.timeDiscretization
    timesteps_total = environment.timer.timestepsTotal
    time_array = np.arange(0, timestep * timesteps_total, timestep)
    temp_storage_array = np.zeros(len(time_array))
    # Dummy array for storage temperature results

    #  Calculate heating up of storage for constant surrounding temperature and constant power input
    for i in range(len(time_array)):
        temp_current = my_tes.t_current

        temp_new = my_tes.calc_storage_temp_for_next_timestep(q_in=50, q_out=0,
                                                              t_prior=temp_current,
                                                              set_new_temperature=True,
                                                              save_res=True,
                                                              time_index=i)
        temp_storage_array[i] = temp_new

    print('Storage temperature over time in degree Celsius:',
          temp_storage_array)

    if print_results:
        plt.plot(time_array / (3600 * 24), temp_storage_array)
        plt.annotate('Q_dot_input = 50 W', xy=(0, 20), xytext=(5, 23),
                     arrowprops=dict(facecolor='black',
                                     shrink=0.05))
        plt.annotate('T_env = 20 deg C (const.)', xy=(15, 30), xytext=(15, 30))
        plt.xlim([0, 50])  # 50 days max
        plt.xlabel('Time in days')
        plt.ylabel('Storage temp. in degree C')
        plt.show()


def run_example_tes3(print_results=False):
    #  Generate environment
    year = 2010
    timestep = 900  # Timestep in seconds
    location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop

    timer = time.TimerExtended(timestep=timestep, year=year)
    weather = Weather.Weather(timer, useTRY=True)
    market = mark.Market()
    co2em = co2.Emissions(year=year)
    environment = env.EnvironmentExtended(timer, weather, prices=market,
                                          location=location, co2em=co2em)

    #  Generate tes object
    my_tes = TES.thermalEnergyStorageExtended(environment, t_init=80,
                                              capacity=500)

    #  Generate time array from environment
    timestep = environment.timer.timeDiscretization
    timesteps_total = environment.timer.timestepsTotal
    time_array = np.arange(0, timestep * timesteps_total, timestep)
    temp_storage_array = np.zeros(len(time_array))
    # Dummy array for storage temperature results

    #  Initial values for q_in and q_out
    q_in = 0
    q_out = 0

    #  Calculate heating up of storage for constant surrounding temperature and constant power input
    for i in range(len(time_array)):

        temp_current = my_tes.t_current

        #  Event of starting charging at timearray position 3
        if i == 3000:
            q_in = 50

        # Event of starting discharging at timearray position 6
        if i == 6000:
            q_out = 40

        temp_new = my_tes.calc_storage_temp_for_next_timestep(q_in=q_in,
                                                              q_out=q_out,
                                                              t_prior=temp_current,
                                                              set_new_temperature=True,
                                                              save_res=True,
                                                              time_index=i)
        temp_storage_array[i] = temp_new

    print('Storage temperature over time in degree Celsius:',
          temp_storage_array)

    if print_results:
        plt.plot(time_array / (3600 * 24), temp_storage_array)
        plt.annotate('Q_dot_input = 3 kW', xy=(30, 20), xytext=(45, 35),
                     arrowprops=dict(facecolor='black',
                                     shrink=0.05))
        plt.annotate('Q_dot_output = 6 kW', xy=(62, 52), xytext=(77, 67),
                     arrowprops=dict(facecolor='black',
                                     shrink=0.05))
        plt.xlim([0, 365])  # 50 days max
        plt.xlabel('Time in days')
        plt.ylabel('Storage temp. in degree C')
        plt.show()


def run_example_tes4(print_results=False):
    #  Generate environment
    year = 2010
    timestep = 900  # Timestep in seconds
    location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop

    timer = time.TimerExtended(timestep=timestep, year=year)
    weather = Weather.Weather(timer, useTRY=True)
    market = mark.Market()
    co2em = co2.Emissions(year=year)
    environment = env.EnvironmentExtended(timer, weather, prices=market,
                                          location=location, co2em=co2em)

    #  Generate tes object (use outdoor temperature for loss calculation)
    my_tes = TES.thermalEnergyStorageExtended(environment, t_init=60,
                                              capacity=2000,
                                              use_outside_temp=True)

    #  Generate time array from environment
    timestep = environment.timer.timeDiscretization
    timesteps_total = environment.timer.timestepsTotal
    time_array = np.arange(0, timestep * timesteps_total, timestep)
    temp_storage_array = np.zeros(len(time_array))
    # Dummy array for storage temperature results

    #  Calculate heating up of storage for constant surrounding temperature
    #  and constant power input
    for i in range(len(time_array)):
        #  Outdoor temperature
        t_outside = environment.weather.tAmbient[i]

        #  Temperature of storage
        temp_current = my_tes.t_current

        temp_new = my_tes.calc_storage_temp_for_next_timestep(q_in=150, q_out=0,
                                                              t_prior=temp_current,
                                                              t_ambient=t_outside,
                                                              set_new_temperature=True,
                                                              save_res=True,
                                                              time_index=i)
        temp_storage_array[i] = temp_new

    print('Storage temperature over time in degree Celsius:',
          temp_storage_array)

    if print_results:
        plt.plot(time_array / (3600 * 24), temp_storage_array)
        plt.annotate('Q_dot_input = 150 Watt', xy=(1, 60), xytext=(11, 55),
                     arrowprops=dict(facecolor='black',
                                     shrink=0.05))
        plt.annotate('Position outdoor (losses active)', xy=(2, 32),
                     xytext=(2, 32))
        plt.xlim([0, 365])  # 50 days max
        plt.xlabel('Time in days')
        plt.ylabel('Storage temp. in degree C')
        plt.show()


if __name__ == '__main__':
    #  Run program
    run_test()

    #  Run other examples with plotting
    run_example_tes(print_results=True)
    run_example_tes2(print_results=True)
    run_example_tes3(print_results=True)
    run_example_tes4(print_results=True)
