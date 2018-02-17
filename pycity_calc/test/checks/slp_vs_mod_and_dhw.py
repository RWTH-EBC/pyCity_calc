#!/usr/bin/env python
# coding=utf-8
"""
Script to compare thermal SLP with Modelica thermal power curve for
space heating plus domestic hot water curve
"""

import numpy as np
import matplotlib.pyplot as plt

import pycity_base.classes.Timer
import pycity_base.classes.Weather
import pycity_base.classes.Environment
import pycity_base.classes.Prices
import pycity_base.classes.demand.SpaceHeating as SpaceHeating
import pycity_base.classes.demand.DomesticHotWater as DomesticHotWater
import pycity_base.classes.demand.Occupancy as occup
import pycity_base.functions.changeResolution as chres
import pycity_calc.toolbox.modifiers.slp_th_manipulator as slpman


def compare_slp_mod_dhw(timestep=3600, nb_occ=3):
    """
    Compare thermal SLP with Modelica space heating power curve and domestic
    hot water profile.

    Parameters
    ----------
    timestep : int
        Timestep of environment
    nb_occ : int
        Number of occupants
    """

    #  Space heating net energy demand in kWh
    sh_net_energy = 12000
    area = 120  # Area of apartment

    #  Hot water parameters
    t_in = 60
    t_sup = 20

    #  Generate pycity environment
    timer = pycity_base.classes.Timer.Timer(timeDiscretization=timestep)
    weather = pycity_base.classes.Weather.Weather(timer, useTRY=True)
    prices = pycity_base.classes.Prices.Prices()

    environment = pycity_base.classes.Environment.Environment(timer, weather,
                                                         prices)

    #  Generate occupancy object
    occupancy_object = \
        pycity_base.classes.demand.Occupancy.Occupancy(environment,
                                                  number_occupants=nb_occ)
    occupancy_profile = occupancy_object.occupancy

    #  Calculate spec. th. energy demand in kWh/m2a
    spec_dem_for_sim = sh_net_energy / area

    #  Modelica space heating profile
    sim_th_load = SpaceHeating.SpaceHeating(environment, method=3,
                                            # Sim profile
                                            livingArea=area,
                                            specificDemand=spec_dem_for_sim)

    #  Stochastic hot water profile
    dhw_object = DomesticHotWater.DomesticHotWater(environment,
                                                   tFlow=t_in,
                                                   thermal=True,
                                                   method=2,
                                                   supplyTemperature=t_sup,
                                                   occupancy=occupancy_profile)

    #  Get modelica space heating curve and hot water power curve
    sim_curve = sim_th_load.loadcurve
    dhw_curve = dhw_object.get_power(currentValues=False,
                                     returnTemperature=False)

    dhw_res_old = 365 * 24 * 3600 / len(dhw_curve)

    #  Change resolution of hot water curve
    dhw_curve = chres.changeResolution(dhw_curve, oldResolution=dhw_res_old,
                                       newResolution=timestep)

    sim_energy = sum(sim_curve) * timestep / (1000 * 3600)
    dhw_energy = sum(dhw_curve) * timestep / (1000 * 3600)

    print('Sim energy in kWh:', sim_energy)
    print('DHW energy in kWh:', dhw_energy)

    #  Calculate spec. th. energy demand for SLP in kWh/m2a
    #  Requires space heating and hot water energy
    spec_dem_for_slp = (sh_net_energy + dhw_energy) / area

    #  Generate thermal SLP object of pycity
    hd_slp = SpaceHeating.SpaceHeating(environment,
                                       method=1,  # Standard load profile
                                       livingArea=area,
                                       specificDemand=spec_dem_for_slp)

    temp_array = environment.weather.tAmbient
    #  Generate modified SLP curve (cut of energy demands on days with
    #  average temperature equal to or larger than 12 °C.
    mod_slp_curve = \
        slpman.slp_th_manipulator(timestep, th_slp_curve=hd_slp.loadcurve,
                                  temp_array=temp_array, temp_av_cut=12)

    #  Reconvert mod_slp_curve to sim_energy demand
    con_mod_factor = sim_energy / (sum(mod_slp_curve) * timestep / (3600 * 1000))
    mod_slp_curve *= con_mod_factor

    slp_curve = hd_slp.loadcurve
    slp_energy = sum(slp_curve) * timestep / (1000 * 3600)
    print('SLP energy in kWh (space heat+dhw):', slp_energy)

    mod_slp_energy = sum(mod_slp_curve) * timestep / (1000 * 3600)
    print('SLP mod. energy in kWh (space heat.):', mod_slp_energy)

    assert slp_energy - (sim_energy + dhw_energy) <= 0.01

    time_array = np.arange(0, 365 * 24 * 3600 / timestep, timestep / 3600)

    plt.plot(time_array, sim_curve, label='Modelica SH')
    plt.plot(time_array, slp_curve, label='SLP')
    plt.plot(time_array, dhw_curve, label='Hot water')
    plt.legend()
    plt.xlabel('Time in hours')
    plt.ylabel('Power in W')
    plt.show()

    aggr_profile = sim_curve + dhw_curve

    plt.plot(time_array, aggr_profile, label='Modelica + DHW')
    plt.plot(time_array, slp_curve, label='SLP')
    plt.legend()
    plt.xlabel('Time in hours')
    plt.ylabel('Power in W')
    plt.show()

    plt.plot(time_array, sim_curve, label='Modelica')
    plt.plot(time_array, mod_slp_curve, label='Mod. SLP')
    plt.legend()
    plt.xlabel('Time in hours')
    plt.ylabel('Power in W')
    plt.show()


def compare_modified_slp_curve():
    """
    Create and compare thermal SLP curves with modified ones based upon the output of function slp_th_manipulator
    for different timestep values.

    """
    timestep_range = [900, 1800, 2700, 3600]

    # Check result for each timestep value:
    for timestep in timestep_range:
        # Generate pycity environment
        timer = pycity_base.classes.Timer.Timer(timeDiscretization=timestep,
                                                timestepsHorizon=int(3600 * 24 * 365 / timestep),
                                                timestepsUsedHorizon=int(24 * 3600 / timestep),
                                                timestepsTotal=int(3600 * 24 * 365 / timestep))
        weather = pycity_base.classes.Weather.Weather(timer, useTRY=True)
        prices = pycity_base.classes.Prices.Prices()

        environment = pycity_base.classes.Environment.Environment(timer, weather, prices)

        pycity_base.classes.demand.SpaceHeating.SpaceHeating.loaded_slp = False

        #  Generate slp object
        slp_object = slpman.gen_th_slp(environment)

        #  Pointer to temperature curve
        temp_curve = environment.weather.tAmbient

        #  Pointer to slp curve
        slp_curve = slp_object.loadcurve

        # Energy before manipulation:
        energy_before = sum(slp_curve[t] for t in range(len(slp_curve)))

        #  Manipulate slp profile
        slp_mod_curve = slpman.slp_th_manipulator(timestep, th_slp_curve=slp_curve, temp_array=temp_curve)

        # Energy after manipulation:
        energy_after = sum(slp_mod_curve[t] for t in range(len(slp_mod_curve)))

        assert energy_before - energy_after <= 0.0001

        plt.plot(slp_curve, label='Org. SLP')
        plt.plot(slp_mod_curve, label='Mod. SLP')
        plt.xlabel('Time in {} hours'.format(float(timestep/3600.0)))
        plt.ylabel('Thermal power in W')
        plt.legend()
        plt.show()
    return


if __name__ == '__main__':
    compare_slp_mod_dhw()
    compare_modified_slp_curve()
