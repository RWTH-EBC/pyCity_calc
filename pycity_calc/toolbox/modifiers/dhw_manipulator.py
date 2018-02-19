# coding=utf-8
"""
Script to modify domestic hot water (DWH) power curves.
Script limits maximum peak size, but keeps the energy balance.
"""

__author__ = 'tsh-dor'

import copy
import numpy as np
import matplotlib.pyplot as plt

import pycity_base.classes.Weather as Weather
import pycity_base.classes.demand.Occupancy as occup
import pycity_base.classes.demand.DomesticHotWater as DomesticHotWater

import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.environment as env
import pycity_calc.environments.market as mark
import pycity_calc.environments.timer as time


def gen_dhw_obj(year=2010, timestep=60, nb_persons=1, temp_in=60, temp_out=25):
    """
    Generates domestic hot water (dhw) object

    Parameters
    ----------
    year : int, optional
        Year of environment (default: 2010)
    timestep : int, optional
        Timestep in seconds (default: 60)
    nb_persons : int, optional
        Number of persons (default: 1)
    temp_in : float, optional
        Inlet temperature in degree Celsius (default: 60)
    temp_out : float, optional
        Return flow temperature in degree Celsius (default: 25)

    Returns
    -------
    dhw_object : object
        Domestic hot water object
    """

    #  Create extended environment of pycity_calc
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

    occupancy_object = occup.Occupancy(environment,
                                       number_occupants=nb_persons)
    occupancy_profile = occupancy_object.occupancy

    dhw_object = DomesticHotWater.DomesticHotWater(environment,
                                                   tFlow=temp_in,
                                                   thermal=True,
                                                   method=2,
                                                   supplyTemperature=temp_out,
                                                   occupancy=occupancy_profile)

    return dhw_object


def dhw_manipulator(dhw_curve, new_max_value=3000):
    """
    dhw_manipulator eliminates the peaks in the dhw_power_curves;
    otherwise intelligent dimensioning would not be possible and Bes
    would be oversized

    Parameters
    ----------
    dhw_curve : array-like
        DHW power curve with power value in Watt per timestep
    new_max_value : float, optional
        Defines maximal allowed peak power value in Watt

    Returns
    -------
    dhw_curve : array-like
        Peak-shaved DHW power curve with power value in Watt per timestep
    """

    dhw_curve_c = copy.deepcopy(dhw_curve)

    bigger_total = []

    for i in range(len(dhw_curve_c)):
        # max value is cutted of
        if dhw_curve_c[i] >= new_max_value:
            bigger_total.append(dhw_curve_c[i] - new_max_value)
            dhw_curve_c[i] = new_max_value

    for i in range(len(dhw_curve_c)):
        if dhw_curve_c[i] < new_max_value:
            # each timestep is enhanced with a share of peak power
            dhw_curve_c[i] += sum(bigger_total) / len(dhw_curve_c)

    return dhw_curve_c


def dhw_manipulation_city(city):
    """
    Limit all dhw profiles within city district to specific power limit.
    Keep energy demand constant.

    Parameters
    ----------
    city : object
        City object of pycity_calc
    """

    #  Loop over all buildings
    for n in city:
        #  If node holds attribute 'node_type'
        if 'node_type' in city.nodes[n]:
            #  If node_type is building
            if city.nodes[n]['node_type'] == 'building':
                #  If entity is kind building
                if city.nodes[n]['entity']._kind == 'building':
                    cur_b = city.nodes[n]['entity']

                    #  Loop over apartments
                    for a in cur_b.apartments:
                        #  Get dhw curve
                        dhw_curve = a.demandDomesticHotWater.loadcurve

                        #  Manipulate
                        new_dhw = \
                            dhw_manipulator(dhw_curve=dhw_curve,
                                            new_max_value=3000)

                        #  Set new dhw curve to apartment
                        a.demandDomesticHotWater.loadcurve = new_dhw


if __name__ == '__main__':

    timestep = 900  # in seconds
    max_power_value = 3500  # in Watt

    dhw_obj = gen_dhw_obj(timestep=timestep)
    dhw_curve_original = dhw_obj.get_power(currentValues=False,
                                           returnTemperature=False)

    print('Generated dhw object')
    print('Old profile:')
    print(dhw_curve_original)

    print('Max power value of old dhw curve in Watt:')
    print(np.max(dhw_curve_original))
    print()

    print('Use dhw manipulator')
    dhw_curve_new = dhw_manipulator(dhw_curve_original, max_power_value)

    print('New profile:')
    print(dhw_curve_new)

    energy_old = np.sum(dhw_curve_original) * timestep
    energy_new = np.sum(dhw_curve_new) * timestep

    assert (energy_old - energy_new) / energy_old <= 0.001

    print('Max power value of new dhw curve in Watt:')
    print(np.max(dhw_curve_new))

    assert np.max(dhw_curve_new) <= max_power_value * 1.001

    fig = plt.figure()
    ax1 = fig.add_subplot(2, 1, 1)
    plt.ylabel('Power / W')
    plt.xlabel('Time')
    ax1.plot(dhw_curve_original, '#DD402D',
            linewidth=0.6, label='Dhw old')
    plt.legend()

    ax2 = fig.add_subplot(2, 1, 2)
    plt.ylabel('Power / W')
    plt.xlabel('Time')
    ax2.plot(dhw_curve_new, 'k', linewidth=0.6, label='Dhw new')
    plt.legend()
    plt.show()
