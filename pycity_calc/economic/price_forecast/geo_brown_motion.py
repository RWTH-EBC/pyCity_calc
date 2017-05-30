#!/usr/bin/env python
# coding=utf-8
"""
Script to forecast pricing with geometric brownian motion
"""

import random
import numpy as np
import matplotlib.pyplot as plt


def calc_price_geo_brown_motion(price_init, timespan, timestep, mu, sigma):
    """
    Forecast pricing with geometric brownian motion

    Parameters
    ----------
    price_init : float
        Initial price
    timespan : int
        Total timespan (e.g. in years)
    timestep : int
        Time discretization (e.g. in years)
    mu : float
        Drift / mean of price change per timestep
    sigma : float
        Shock / standard deviation of price change per timestep

    Returns
    -------
    brown_motion : array-like
        Array with new pricing data values
    """

    steps = round(timespan / timestep)
    time_arranged = np.linspace(0, timespan, steps)
    w = np.random.standard_normal(size=steps)
    w = np.cumsum(w) * np.sqrt(timestep)
    x = (mu - 0.5 * sigma ** 2) * time_arranged + sigma * w
    brown_motion = price_init * np.exp(x)

    return brown_motion

if __name__ == '__main__':

    timespan = 20

    mu_min = -0.05
    mu_max = 0.05

    sigma = 0.05
    price_init = 0.26
    timestep = 1

    nb_runs = 50

    for i in range(nb_runs):

        mu = random.uniform(mu_min, mu_max)

        prices = calc_price_geo_brown_motion(timestep=timestep,
                                             timespan=timespan,
                                             mu=mu, sigma=sigma,
                                             price_init=price_init)

        plt.plot(prices)

    plt.title('Brownian motion price change for ' + str(nb_runs) + ' runs')
    plt.xlabel('Time in years')
    plt.ylabel('Price in Euro')
    plt.show()