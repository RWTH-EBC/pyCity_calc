# coding=utf-8
"""
Example script to use extended environment class
"""
from __future__ import division
import numpy as np

import pycity_base.classes.Weather as Weather

import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.environment as env
import pycity_calc.environments.market as mark
import pycity_calc.environments.timer as time


def run_example():

    #  Create extended environment of pycity_calc
    year = 2010
    timestep = 3600  # Timestep in seconds
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

    print('Chosen timestep:', environment.timer.timeDiscretization)

    temp_amb, q_dir, q_diff = weather.getWeatherForecast(getTAmbient=True,
                                                         getQDirect=True,
                                                         getQDiffuse=True,
                                                         getVWind=False,
                                                         getPhiAmbient=False,
                                                         getPAmbient=False)

    print('Get weather data:')
    print('Ambient Temperature in degree Celsius:')
    print(temp_amb)
    print('Direct radiation in W/m2:')
    print(q_dir)
    print('Diffuse radiation in W/m2:')
    print(q_diff)

    print('CO2 emission factor of electricity mix in kg/kWh:')
    print(environment.co2emissions.co2_factor_el_mix)


if __name__ == '__main__':
    run_example()
