#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
from __future__ import division

import numpy as np

import pycity_base.classes.supply.PV as PV
import pycity_base.classes.Weather as Weather

import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.environment as env
import pycity_calc.environments.market as mark
import pycity_calc.environments.timer as time

#  Create extended environment of pycity_calc
year = 2010
timestep = 900  # Timestep in seconds
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

pv = PV.PV(environment=environment, area=20, eta=0.15, temperature_nominal=45,
           alpha=0, beta=0, gamma=0, tau_alpha=0.9)

pv_power = pv.getPower(currentValues=False, updatePower=True)

print(max(pv_power))

import matplotlib.pyplot as plt

plt.plot(pv_power)
plt.show()
plt.close()