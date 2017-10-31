#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
from __future__ import division

import random
import pycity_calc.economic.price_forecast.geo_brown_motion as bromo

class TestBrownMotion():
    def test_bro_mo(self):
        timespan = 20

        mu_min = -0.05
        mu_max = 0.05

        sigma = 0.05
        price_init = 0.26
        timestep = 1

        nb_runs = 10

        for i in range(nb_runs):
            mu = random.uniform(mu_min, mu_max)

            prices = bromo.calc_price_geo_brown_motion(timestep=timestep,
                                                       timespan=timespan,
                                                       mu=mu, sigma=sigma,
                                                       price_init=price_init)
