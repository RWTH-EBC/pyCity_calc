#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""

import pycity.classes.supply.PV as pvmodule
import pycity.classes.Weather as Weather
import pycity.classes.demand.ElectricalDemand as elecdem
import pycity.classes.demand.Occupancy as occu
import pycity.functions.changeResolution as chres

import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.environment as env
import pycity_calc.environments.market as mark
import pycity_calc.environments.timer as time


def init_pv(environment, area=50, eta=0.15, alpha=0, temperature_nominal=45,
            beta=30, gamma=0, tau_alpha=0.9):
    """

    Parameters
    ----------
    environment : Environment object
            Common to all other objects. Includes time and weather instances
        area : integer, optional
            installation area in m2 (default: 50)
        eta : float, optional
            Electrical efficiency at NOCT conditions (without unit)
            (default: 0.15)
        temperature_nominal : float, optional
            Nominal cell temperature at NOCT conditions (in degree Celsius)
            (default: 45)
        alpha : float, optional
            Temperature coefficient at NOCT conditions (default: 0)
        beta : float, optional
            Slope, the angle (in degree) between the plane of the surface in
            question and the horizontal. 0 <= beta <= 180. If beta > 90, the
            surface faces downwards. (default: 30)
        gamma : float, optional
            Surface azimuth angle. The deviation of the projection on a
            horizontal plane of the normal to the surface from the local
            meridian, with zero due south, east negative, and west positive.
            -180 <= gamma <= 180 (default: 0)
        tau_alpha : float, optional
            Optical properties of the PV unit. Product of absorption and
            transmission coeffients.
            According to Duffie, Beckman - Solar Engineering of Thermal
            Processes (4th ed.), page 758, this value is typically close to 0.9
            (default: 0.9)

    Returns
    -------
    pv : object
        PV object instance of pycity
    """

    pv = pvmodule.PV(environment=environment, area=area, eta=eta,
                     temperature_nominal=temperature_nominal,
                     alpha=alpha, beta=beta, gamma=gamma,
                     tau_alpha=tau_alpha)

    return pv


if __name__ == '__main__':

    #  Create extended environment of pycity_calc
    year = 2010
    timestep = 60  # Timestep in seconds
    location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop
    altitude = 55  # Altitude of Bottrop

    nb_occ = 3  # Nb. of occupants

    pv_area = 30  # m2

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

    #  Initialize pv module
    pv = init_pv(environment=environment, area=pv_area)

    #  Get pv power
    pv_power = pv.getPower()

    occupancy = occu.Occupancy(environment, number_occupants=nb_occ)

    el_dem_stochastic = elecdem.ElectricalDemand(environment,
                                                 method=2,
                                                 total_nb_occupants=nb_occ,
                                                 randomizeAppliances=True,
                                                 lightConfiguration=10,
                                                 occupancy=occupancy.occupancy,
                                                 prev_heat_dev=True)

    el_power = el_dem_stochastic.loadcurve

    own_consumption = 0
    pv_energy = 0
    el_demand = 0

    for i in range(len(pv_power)):
        curr_pv_pow = pv_power[i]
        curr_el_pow = el_power[i]

        if curr_pv_pow <= curr_el_pow:
            own_consumption += curr_pv_pow * timestep / (1000 * 3600)
        else:
            own_consumption += curr_el_pow * timestep / (1000 * 3600)

        pv_energy += curr_pv_pow * timestep / (1000 * 3600)
        el_demand += curr_el_pow * timestep / (1000 * 3600)

    print('Analysis with timestep of ' + str(timestep) + ' seconds.')
    print('########################################################')

    print('Total energy generated by PV in kWh/a: ')
    print(pv_energy)
    print()

    print('Total electric energy demand in kWh/a: ')
    print(el_demand)
    print()

    print('Self-consumed PV energy in kWh/a: ')
    print(own_consumption)
    print()

    share_self = (own_consumption / pv_energy) * 100
    share_feed_in = (pv_energy - own_consumption) / pv_energy * 100

    print('Share of self consumption in %: ', share_self)
    print('Share of feed in PV el. energy in %: ', share_feed_in)

    print('########################################################')
    print()

    #  Analysis with timestep of 3600 seconds

    #  Change timesteps
    pv_power_3600 = chres.changeResolution(values=pv_power[:],
                                           oldResolution=timestep,
                                           newResolution=3600)
    el_power_3600 = chres.changeResolution(values=el_power[:],
                                           oldResolution=timestep,
                                           newResolution=3600)

    own_consumption_3600 = 0
    pv_energy_3600 = 0
    el_demand_3600 = 0

    for i in range(len(pv_power_3600)):
        curr_pv_pow_3600 = pv_power_3600[i]
        curr_el_pow_3600 = el_power_3600[i]

        if curr_pv_pow_3600 <= curr_el_pow_3600:
            own_consumption_3600 += curr_pv_pow_3600 * 3600 / (1000 * 3600)
        else:
            own_consumption_3600 += curr_el_pow_3600 * 3600 / (1000 * 3600)

        pv_energy_3600 += curr_pv_pow_3600 * 3600 / (1000 * 3600)
        el_demand_3600 += curr_el_pow_3600 * 3600 / (1000 * 3600)

    print('Analysis with timestep of 3600 seconds.')
    print('########################################################')

    print('Total energy generated by PV in kWh/a: ')
    print(pv_energy_3600)
    print()

    print('Total electric energy demand in kWh/a: ')
    print(el_demand_3600)
    print()

    print('Self-consumed PV energy in kWh/a: ')
    print(own_consumption_3600)
    print()

    share_self_3600 = (own_consumption_3600 / pv_energy_3600) * 100
    share_feed_in_3600 = (pv_energy_3600 - own_consumption_3600) / \
                         pv_energy_3600 * 100

    print('Share of self consumption in %: ', share_self_3600)
    print('Share of feed in PV el. energy in %: ', share_feed_in_3600)

    print('########################################################')
    print()

    print('Delta in own consumption in kWh/a: ')
    print(own_consumption - own_consumption_3600)
    print('In percent: ')
    print((own_consumption - own_consumption_3600) * 100 / own_consumption)

    import matplotlib.pyplot as plt

    idx_start = 0
    idx_stop = int(72 * 3600 / timestep)

    plt.plot(pv_power[idx_start:idx_stop])
    plt.plot(el_power[idx_start:idx_stop])
    plt.show()
    plt.close()

    delta_t = int(180 * 24 * 3600 / timestep)
    idx_start += delta_t
    idx_stop += delta_t

    plt.plot(pv_power[idx_start:idx_stop])
    plt.plot(el_power[idx_start:idx_stop])
    plt.show()
    plt.close()

    idx_start = 0
    idx_stop = 72

    plt.plot(pv_power_3600[idx_start:idx_stop])
    plt.plot(el_power_3600[idx_start:idx_stop])
    plt.show()
    plt.close()

    delta_t = 180 * 24
    idx_start += delta_t
    idx_stop += delta_t

    plt.plot(pv_power_3600[idx_start:idx_stop])
    plt.plot(el_power_3600[idx_start:idx_stop])
    plt.show()
    plt.close()
