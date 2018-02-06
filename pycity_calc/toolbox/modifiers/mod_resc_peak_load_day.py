#!/usr/bin/env python
# coding=utf-8
"""
Script for rescaling space heating peak load day (related to robust rescaling
in pyCity_opt
"""
from __future__ import division

import copy
import numpy as np
import matplotlib.pyplot as plt


def resc_sh_peak_load(loadcurve, timestep, resc_factor, span=1):
    """
    Rescales space heating peak load day with given rescaling factor.
    Assuming that loadcurve represents one year.

    Parameters
    ----------
    loadcurve : array
        Space heating load curve in Watt
    timestep : int
        Timestep in seconds
    resc_factor : float
        Rescaling factor for peak load day (e.g. 2 means, that every space
        heating power at peak load day are going to rescaled with factor 2)
    span : int, optional
        Timespan in hours, defining peak load period (default: 1).

    Returns
    -------
    mod_loadcurve : array
        Rescaled loadcurve
    """
    assert resc_factor > 0
    assert isinstance(span, int)
    assert span > 0

    #  Get original space heating demand value
    sp_dem_org = sum(loadcurve) * timestep / (3600 * 1000)

    #  Identify peak load timestep
    idx_max = np.argmax(loadcurve)

    #  Identify list of peak load period indexes
    hour = 0
    while hour * 3600 < idx_max * timestep:
        hour += 24

    start = hour - span * 24  # Start index; while hour is stop index
    list_idx = list(range(start, hour))

    #  Copy loadcurve
    mod_loadcurve = copy.copy(loadcurve)

    #  Rescale each value
    for idx in list_idx:
        mod_loadcurve[idx] *= resc_factor

    #  Calculate new energy demand
    sp_dem_mod = sum(mod_loadcurve) * timestep / (3600 * 1000)

    #  Generate list of all indexes
    list_all_idx = list(range(0, len(loadcurve)))

    #  Get differences in indexes
    list_remain_idx = list(set(list_all_idx) - set(list_idx))

    #  Normalize overall array
    norm_factor = sp_dem_org / sp_dem_mod
    for idx in list_remain_idx:
        mod_loadcurve[idx] *= norm_factor

    return mod_loadcurve


def resc_sh_peak_load_build(building, resc_factor, span=1):
    """
    Rescales space heating peak load day with given rescaling factor within
    building object

    Parameters
    ----------
    building : object
        Building object of pyCity_calc
    resc_factor : float
        Rescaling factor for peak load day (e.g. 2 means, that every space
        heating power at peak load day are going to rescaled with factor 2)
    span : int, optional
        Timespan in days, defining peak load period (default: 1).
    """

    assert resc_factor > 0
    assert isinstance(span, int)
    assert span > 0
    assert len(building.apartments) > 0, 'Building does not hold apartment'

    timestep = building.environment.timer.timeDiscretization

    #  Loop over apartments in building
    for app in building.apartments:
        #  Pointer to space heating load
        sh_load = app.demandSpaceheating.loadcurve

        #  Rescale space heating load
        mod_sh = resc_sh_peak_load(loadcurve=sh_load,
                                   timestep=timestep,
                                   resc_factor=resc_factor,
                                   span=span)

        #  Overwrite original value
        app.demandSpaceheating.loadcurve = mod_sh


if __name__ == '__main__':
    import pycity_base.classes.demand.SpaceHeating as spaceheat
    import pycity_base.classes.Weather as Weather
    import pycity_base.classes.demand.Apartment as apart

    import pycity_calc.buildings.building as build_ex
    import pycity_calc.environments.co2emissions as co2
    import pycity_calc.environments.environment as env
    import pycity_calc.environments.market as mark
    import pycity_calc.environments.timer as time

    #  Rescaling factor
    resc_factor = 3

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
    #  You can also use GermanMarket to have specific German tariffs and
    #  subsidies

    #  Generate co2 emissions object
    co2em = co2.Emissions(year=year)

    #  Generate environment
    environment = env.EnvironmentExtended(timer, weather, prices=market,
                                          location=location, co2em=co2em)

    #  Generate space heating load (SLP)
    hd_slp = spaceheat.SpaceHeating(environment=environment,
                                    method=1,  # Standard load profile
                                    livingArea=150,
                                    specificDemand=100)

    #  Pointer to loadcurve
    loadcurve = hd_slp.loadcurve

    #  Copy loadcurve
    load_org = copy.copy(loadcurve)

    #  Create apartment
    apartment = apart.Apartment(environment)

    #  Add demands to apartment
    apartment.addEntity(hd_slp)

    #  Create extended building object
    extended_building = build_ex.BuildingExtended(environment, build_year=1962,
                                                  mod_year=2003, build_type=0,
                                                  roof_usabl_pv_area=30,
                                                  net_floor_area=150,
                                                  height_of_floors=3,
                                                  nb_of_floors=2,
                                                  neighbour_buildings=0,
                                                  residential_layout=0,
                                                  attic=0, cellar=1,
                                                  construction_type='heavy',
                                                  dormer=0)
    #  BuildingExtended holds further, optional input parameters,
    #  such as ground_area, nb_of_floors etc.

    #  Add apartment to extended building
    extended_building.addEntity(entity=apartment)

    #  Rescale sh peak load day of building
    resc_sh_peak_load_build(building=extended_building,
                            resc_factor=resc_factor)

    #  New load
    load_new = extended_building.get_space_heating_power_curve()

    plt.plot(load_org)
    plt.plot(load_new)
    plt.show()
    plt.close()

    assert (sum(load_org) * timestep / (3600 * 1000)
            - sum(load_new) * timestep / (3600 * 1000)) <= 0.001
