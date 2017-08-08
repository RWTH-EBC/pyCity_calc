#!/usr/bin/env python
# coding=utf-8
"""
Examples script for BatteryExtended class
"""
from __future__ import division
import pycity_calc.energysystems.battery as batt

import pycity_base.classes.Weather as Weather
import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.environment as env
import pycity_calc.environments.market as mark
import pycity_calc.environments.timer as time


def run_example():
    # create environment
    year = 2010
    timestep = 900  # Timestep in seconds
    location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop

    timer = time.TimerExtended(timestep=timestep, year=year)
    weather = Weather.Weather(timer, useTRY=True)
    market = mark.Market()
    co2em = co2.Emissions(year=year)
    environment = env.EnvironmentExtended(timer, weather, prices=market,
                                          location=location, co2em=co2em)

    # create the battery
    soc_init_ratio = 0.5
    capacity_kwh = 40  # kWh
    battery = batt.BatteryExtended(environment, soc_init_ratio, capacity_kwh)

    nominals = battery.getNominalValues()

    print()
    print(("Kind: " + str(battery._kind)))
    print("Capacity: " + str(nominals[0]) + " J")
    print("Rate of self discharge: " + str(nominals[1]))
    print("Charging efficiency: " + str(nominals[2]))
    print("Discharging efficiency: " + str(nominals[3]))

    capacity = battery.get_battery_capacity_in_kwh()
    max_p_el_in = battery.calc_battery_max_p_el_in()
    max_p_el_out = battery.calc_battery_max_p_el_out()

    current_energy = capacity * battery.soc_ratio_current

    print()
    print("Capacity: " + str(capacity) + " kWh")
    print("Currently stored energy: " + str(
        round(current_energy, 2)) + " kWh; " + str(
        round(battery.soc_ratio_current, 2)) + " %")
    print("Max charging power: " + str(round(max_p_el_in, 2)) + " W")
    print("Max discharging power: " + str(round(max_p_el_out, 2)) + " W")

    charging_power = 400000  # W
    charging_possible = battery.battery_charge_possible(charging_power)
    if charging_possible:
        charging_soc = battery.calc_battery_soc_next_timestep(
            p_el_in=charging_power,
            p_el_out=0, set_new_soc=True)
    else:
        charging_soc = battery.soc_ratio_current

    energy_charging = capacity * charging_soc

    print()
    print(
        "Charging of " + str(round(charging_power, 2)) + " W possibel? " + str(
            charging_possible))
    print()
    print("Currently stored energy: " + str(
        round(energy_charging, 2)) + " kWh; " + str(
        round(charging_soc, 2)) + " %")

    discharging_power = 40000  # W
    discharging_possible = battery.battery_discharge_possible(
        discharging_power)
    if discharging_possible:
        discharging_soc = battery.calc_battery_soc_next_timestep(p_el_in=0,
                                                                 p_el_out=discharging_power,
                                                                 set_new_soc=True)
    else:
        discharging_soc = battery.soc_ratio_current

    energy_discharging = capacity * discharging_soc

    print()
    print("Discharging of " + str(
        round(discharging_power, 2)) + " W possibel? " + str(
        discharging_possible))
    print()
    print("Currently stored energy: " + str(
        round(energy_discharging, 2)) + " kWh; " + str(
        round(discharging_soc, 2)) + " %")


if __name__ == '__main__':
    #  Run program
    run_example()
