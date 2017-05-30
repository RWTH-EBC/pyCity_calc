#!/usr/bin/env python
# coding=utf-8
"""
Script to analyse domestic hot water profiles.

Based on Annex 42 Substask A --> Assumtion for Germany:
Around 64 Liters hot water per occupant and day (35 Kelvin temperatur split)
--> 2.6 kWh / person and day

Based on Canadian survey
http://www.sciencedirect.com/science/article/pii/S0378778812006238

Nb occupants - DHW volume per capita and day in liters
1 - 139
2 - 84
3 - 67
4 - 60
5 - 59
6 - 58
Mean - 65

No information on temperature split. However, 494 liters oil consumption
for dhw per year (on person apartment). --> Assuming lower caloric value
of 10 kWh/liter --> 13.5 kWh/day and person (for DHW)
--> Theoretically 84 Kelvin
Temperatur split (kind of high).

--> DHW volumes might be realistic for German citizens, however,
temperature-split should be reduced
"""

import numpy as np
import matplotlib.pyplot as plt

import pycity.classes.demand.DomesticHotWater as DomesticHotWater
import pycity.classes.demand.Occupancy as occ
import pycity.classes.Weather as Weather
import pycity.functions.changeResolution as chres

import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.environment as env
import pycity_calc.environments.market as mark
import pycity_calc.environments.timer as time
import pycity_calc.toolbox.dimensioning.dim_functions as dimfunc


def set_up_environment(timestep):
    """
    Generate environment object

    Parameters
    ----------
    timestep : int
        Timestep in seconds

    Returns
    -------
    environment : object
        Environment of pycity_calc
    """

    year = 2010
    location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop
    altitude = 55  # Altitude of Bottrop

    #  Generate timer object
    timer = time.TimerExtended(timestep=timestep, year=year)

    #  Generate weather object
    weather = Weather.Weather(timer, useTRY=True, location=location,
                              altitude=altitude)

    #  Generate market object
    market = mark.Market()

    #  Generate co2 emissions object
    co2em = co2.Emissions(year=year)

    #  Generate environment
    environment = env.EnvironmentExtended(timer, weather, prices=market,
                                          location=location, co2em=co2em)

    return environment


def run_dhw_analysis_annex42(environment):

    timestep = environment.timer.timeDiscretization
    temp_flow = 60
    return_flow = 25

    print('Analysis of profile with 1 person and 140 liters dhw per day.')
    print('Temperature split is 35 Kelvin')
    print('##############################################################')

    dhw_annex42 = DomesticHotWater.DomesticHotWater(environment,
                                                    tFlow=temp_flow,
                                                    thermal=True,
                                                    method=1,  # Annex 42
                                                    dailyConsumption=140,
                                                    supplyTemperature=
                                                    return_flow)

    results = dhw_annex42.get_power(currentValues=False)

    print('Results for Annex42 profile:')
    print()
    print("Thermal power in Watt: " + str(results[0]))
    print("Required flow temperature in degree Celsius: " + str(results[1]))
    print()

    #  Convert into energy values in kWh
    dhw_energy_curve = results[0] * timestep / (3600 * 1000)
    annual_energy_demand = np.sum(dhw_energy_curve)

    print('Annual dhw energy demand in kWh: ', annual_energy_demand)
    print()

    print('DHW energy demand in kWh / person and day: ',
          annual_energy_demand / 365)
    print()

    max_p = dimfunc.get_max_p_of_power_curve(results[0])
    print('Maximal thermal power in kW: ', max_p / 1000)

    av_p = annual_energy_demand / (365*24)  # in kW
    print('Average thermal power in kW: ', av_p)

    index_max = np.argmax(results[0])
    print('Index (minute) of maximal power: ', index_max)

    plt.plot(np.arange(365 * 24 * 3600 / timestep), dhw_annex42.loadcurve)
    plt.ylabel("Heat demand in Watt")
    plt.xlim((0, 8760))
    plt.show()

    print('##############################################################')

    print('Analysis of profile with 3 person and 67 * 3 liters dhw per day.')
    print('Temperature split is 35 Kelvin')
    print('##############################################################')

    nb_persons = 3
    dhw_total = 67 * nb_persons

    dhw_annex42 = DomesticHotWater.DomesticHotWater(environment,
                                                    tFlow=temp_flow,
                                                    thermal=True,
                                                    method=1,  # Annex 42
                                                    dailyConsumption=dhw_total,
                                                    supplyTemperature=
                                                    return_flow)

    results = dhw_annex42.get_power(currentValues=False)

    print('Results for Annex42 profile:')
    print()
    print("Thermal power in Watt: " + str(results[0]))
    print("Required flow temperature in degree Celsius: " + str(results[1]))
    print()

    #  Convert into energy values in kWh
    dhw_energy_curve = results[0] * timestep / (3600 * 1000)
    annual_energy_demand = np.sum(dhw_energy_curve)

    print('Annual dhw energy demand in kWh: ', annual_energy_demand)
    print()

    print('DHW energy demand in kWh / person and day: ',
          annual_energy_demand / (365 * nb_persons))
    print()

    max_p = dimfunc.get_max_p_of_power_curve(results[0])
    print('Maximal thermal power in kW: ', max_p / 1000)

    av_p = annual_energy_demand / (365*24)  # in kW
    print('Average thermal power in kW: ', av_p)

    index_max = np.argmax(results[0])
    print('Index (minute) of maximal power: ', index_max)

    plt.plot(np.arange(365 * 24 * 3600 / timestep), dhw_annex42.loadcurve)
    plt.ylabel("Heat demand in Watt")
    plt.xlim((0, 8760))
    plt.show()

    print('##############################################################')

    print('Analysis of profile with 5 person and 59 * 3 liters dhw per day.')
    print('Temperature split is 35 Kelvin')
    print('##############################################################')

    nb_persons = 5
    dhw_total = 59 * nb_persons

    dhw_annex42 = DomesticHotWater.DomesticHotWater(environment,
                                                    tFlow=temp_flow,
                                                    thermal=True,
                                                    method=1,  # Annex 42
                                                    dailyConsumption=dhw_total,
                                                    supplyTemperature=
                                                    return_flow)

    results = dhw_annex42.get_power(currentValues=False)

    print('Results for Annex42 profile:')
    print()
    print("Thermal power in Watt: " + str(results[0]))
    print("Required flow temperature in degree Celsius: " + str(results[1]))
    print()

    #  Convert into energy values in kWh
    dhw_energy_curve = results[0] * timestep / (3600 * 1000)
    annual_energy_demand = np.sum(dhw_energy_curve)

    print('Annual dhw energy demand in kWh: ', annual_energy_demand)
    print()
    print('DHW energy demand in kWh / person and day: ',
          annual_energy_demand / (365 * nb_persons))
    print()

    max_p = dimfunc.get_max_p_of_power_curve(results[0])
    print('Maximal thermal power in kW: ', max_p / 1000)

    av_p = annual_energy_demand / (365*24)  # in kW
    print('Average thermal power in kW: ', av_p)

    index_max = np.argmax(results[0])
    print('Index (minute) of maximal power: ', index_max)

    plt.plot(np.arange(365 * 24 * 3600 / timestep), dhw_annex42.loadcurve)
    plt.ylabel("Heat demand in Watt")
    plt.xlim((0, 8760))
    plt.show()

    print('##############################################################')


def run_analysis_dhw_stochastical(environment):

    timestep = environment.timer.timeDiscretization

    t_flow = 60
    t_back = 20

    #  Generate different occupancy profiles
    occupancy_object1 = occ.Occupancy(environment, number_occupants=1)
    occupancy_object3 = occ.Occupancy(environment, number_occupants=3)
    occupancy_object5 = occ.Occupancy(environment, number_occupants=5)

    #  Generate dhw profile for 1 person
    dhw_stochastical = DomesticHotWater.DomesticHotWater(environment,
                                                         tFlow=t_flow,
                                                         thermal=True,
                                                         method=2,
                                                         supplyTemperature=
                                                         t_back,
                                                         occupancy=
                                                         occupancy_object1.
                                                         occupancy)

    dhw_power_curve = dhw_stochastical.get_power(currentValues=False,
                                                 returnTemperature=False)
    #  Convert into energy values in kWh
    dhw_energy_curve = dhw_power_curve * timestep / (3600 * 1000)
    annual_energy_demand = np.sum(dhw_energy_curve)

    #  DHW volume flow curve in liters/hour
    volume_flow_curve = dhw_stochastical.water

    #  Recalc into water volume in liters
    water_volume_per_timestep = volume_flow_curve / 3600 * timestep

    # Average daily dhw consumption in liters
    av_daily_dhw_volume = np.sum(water_volume_per_timestep) / 365

    occ_profile = occupancy_object1.occupancy

    print('Results for stochastic DHW profile:\n')
    print('Max number of occupants:', max(occ_profile))
    print('Annual dhw energy demand in kWh: ', annual_energy_demand)
    print('Average daily domestic hot water volume in liters:',
          av_daily_dhw_volume)

    max_p = dimfunc.get_max_p_of_power_curve(dhw_power_curve)
    print('Maximal thermal power in kW: ', max_p / 1000)

    av_p = annual_energy_demand / (365*24)  # in kW
    print('Average thermal power in kW: ', av_p)

    ax1 = plt.subplot(2, 1, 1)
    plt.step(np.arange(365 * 24 * 3600 / timestep),
             dhw_stochastical.loadcurve, linewidth=2)
    plt.ylabel("Heat demand in Watt")
    plt.xlim((0, 8760))

    occ_profile_chres = chres.changeResolution(occ_profile, 600, timestep)

    plt.subplot(2, 1, 2, sharex=ax1)
    plt.step(np.arange(365 * 24 * 3600 / timestep), occ_profile_chres,
             linewidth=2)
    plt.ylabel("Active occupants")
    offset = 0.2
    plt.ylim((-offset, max(occ_profile) + offset))
    plt.yticks(list(range(int(max(occ_profile) + 1))))

    plt.show()

    print('############################################################')

    #  Generate dhw profile for 1 person
    dhw_stochastical = DomesticHotWater.DomesticHotWater(environment,
                                                         tFlow=t_flow,
                                                         thermal=True,
                                                         method=2,
                                                         supplyTemperature=
                                                         t_back,
                                                         occupancy=
                                                         occupancy_object3.
                                                         occupancy)

    dhw_power_curve = dhw_stochastical.get_power(currentValues=False,
                                                 returnTemperature=False)
    #  Convert into energy values in kWh
    dhw_energy_curve = dhw_power_curve * timestep / (3600 * 1000)
    annual_energy_demand = np.sum(dhw_energy_curve)

    #  DHW volume flow curve in liters/hour
    volume_flow_curve = dhw_stochastical.water

    #  Recalc into water volume in liters
    water_volume_per_timestep = volume_flow_curve / 3600 * timestep

    # Average daily dhw consumption in liters
    av_daily_dhw_volume = np.sum(water_volume_per_timestep) / 365

    occ_profile = occupancy_object3.occupancy

    print('Results for stochastic DHW profile:\n')
    print('Max number of occupants:', max(occ_profile))
    print('Annual dhw energy demand in kWh: ', annual_energy_demand)
    print('Average daily domestic hot water volume in liters:',
          av_daily_dhw_volume)

    max_p = dimfunc.get_max_p_of_power_curve(dhw_power_curve)
    print('Maximal thermal power in kW: ', max_p / 1000)

    av_p = annual_energy_demand / (365*24)  # in kW
    print('Average thermal power in kW: ', av_p)

    ax1 = plt.subplot(2, 1, 1)
    plt.step(np.arange(365 * 24 * 3600 / timestep),
             dhw_stochastical.loadcurve, linewidth=2)
    plt.ylabel("Heat demand in Watt")
    plt.xlim((0, 8760))

    occ_profile_chres = chres.changeResolution(occ_profile, 600, timestep)

    plt.subplot(2, 1, 2, sharex=ax1)
    plt.step(np.arange(365 * 24 * 3600 / timestep), occ_profile_chres,
             linewidth=2)
    plt.ylabel("Active occupants")
    offset = 0.2
    plt.ylim((-offset, max(occ_profile) + offset))
    plt.yticks(list(range(int(max(occ_profile) + 1))))

    plt.show()

    print('############################################################')

    #  Generate dhw profile for 1 person
    dhw_stochastical = DomesticHotWater.DomesticHotWater(environment,
                                                         tFlow=t_flow,
                                                         thermal=True,
                                                         method=2,
                                                         supplyTemperature=
                                                         t_back,
                                                         occupancy=
                                                         occupancy_object5.
                                                         occupancy)

    dhw_power_curve = dhw_stochastical.get_power(currentValues=False,
                                                 returnTemperature=False)
    #  Convert into energy values in kWh
    dhw_energy_curve = dhw_power_curve * timestep / (3600 * 1000)
    annual_energy_demand = np.sum(dhw_energy_curve)

    #  DHW volume flow curve in liters/hour
    volume_flow_curve = dhw_stochastical.water

    #  Recalc into water volume in liters
    water_volume_per_timestep = volume_flow_curve / 3600 * timestep

    # Average daily dhw consumption in liters
    av_daily_dhw_volume = np.sum(water_volume_per_timestep) / 365

    occ_profile = occupancy_object5.occupancy

    print('Results for stochastic DHW profile:\n')
    print('Max number of occupants:', max(occ_profile))
    print('Annual dhw energy demand in kWh: ', annual_energy_demand)
    print('Average daily domestic hot water volume in liters:',
          av_daily_dhw_volume)

    max_p = dimfunc.get_max_p_of_power_curve(dhw_power_curve)
    print('Maximal thermal power in kW: ', max_p / 1000)

    av_p = annual_energy_demand / (365*24)  # in kW
    print('Average thermal power in kW: ', av_p)

    ax1 = plt.subplot(2, 1, 1)
    plt.step(np.arange(365 * 24 * 3600 / timestep),
             dhw_stochastical.loadcurve, linewidth=2)
    plt.ylabel("Heat demand in Watt")
    plt.xlim((0, 8760))

    occ_profile_chres = chres.changeResolution(occ_profile, 600, timestep)

    plt.subplot(2, 1, 2, sharex=ax1)
    plt.step(np.arange(365 * 24 * 3600 / timestep), occ_profile_chres,
             linewidth=2)
    plt.ylabel("Active occupants")
    offset = 0.2
    plt.ylim((-offset, max(occ_profile) + offset))
    plt.yticks(list(range(int(max(occ_profile) + 1))))

    plt.show()

    print('############################################################')

if __name__ == '__main__':

    #  Generate environment
    environment = set_up_environment(timestep=900)

    #  Run program for Annex 42 profiles
    run_dhw_analysis_annex42(environment)

    #  Generate environment
    environment = set_up_environment(timestep=60)

    #  Run analysis for stochastical dhw profiles
    run_analysis_dhw_stochastical(environment)
