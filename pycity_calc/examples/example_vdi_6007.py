#!/usr/bin/env python
# coding=utf-8
"""
Example script how to calculate thermal space heating load with TEASER and
VDI 6007 calculation core.

Steps:
- Generate environment
- Generate occuancy object
- Generate el. load object
- Generate apartment and add profile objects
- Generate building and add apartment
- Run VDI simulation with building
"""

import numpy as np

import pycity.classes.Weather as Weather
import pycity.classes.demand.Occupancy as occ
import pycity.classes.demand.ElectricalDemand as eldem
import pycity.classes.demand.Apartment as Apartment

import pycity_calc.buildings.building as build_ex
import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.environment as env
import pycity_calc.environments.market as mark
import pycity_calc.environments.timer as time

import pycity_calc.toolbox.teaser_usage.teaser_use as tus
import pycity_calc.toolbox.user.user_air_exchange as usair

try:
    from teaser.project import Project
    import teaser.logic.simulation.VDI_6007.low_order_VDI as low_order_vdi
    import teaser.logic.simulation.VDI_6007.weather as vdiweather
except:
    raise ImportError('Could not import TEASER package. Please check your '
                      'installation. TEASER can be found at: '
                      'https://github.com/RWTH-EBC/TEASER. '
                      'Installation is possible via pip. '
                      'Alternatively, you might have run into trouble with '
                      'XML bindings in TEASER. This can happen '
                      'if you try to re-import TEASER within an active '
                      'Python console. Please close the active Python '
                      'console and open another one. Then try again.')


def run_example_vdi_6007(plot_res=False):
    #  Define simulation settings
    build_year = 1962  # Year of construction
    mod_year = 2014  # Year of retrofit

    el_demand = 3000  # Annual, el. demand in kWh

    t_set_heat = 20  # Heating set temperature in degree Celsius
    t_set_night = 16  # Night set back temperature in degree Celsius
    t_set_cool = 70  # Cooling set temperature in degree Celsius

    air_vent_mode = 2
    #  int; Define mode for air ventilation rate generation
    #  0 : Use constant value (vent_factor in 1/h)
    #  1 : Use deterministic, temperature-dependent profile
    #  2 : Use stochastic, user-dependent profile
    #  False: Use static ventilation rate value

    vent_factor = 0.5  # Constant. ventilation rate
    #  (only used, if air_vent_mode == 0)

    heat_lim_val = None  # Heater limit in Watt

    #  #  Create PyCity_Calc environment
    #  #####################################################################

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

    #  #  Create occupancy profile
    #  #####################################################################

    num_occ = 3

    print('Calculate occupancy.\n')
    #  Generate occupancy profile
    occupancy_obj = occ.Occupancy(environment, number_occupants=num_occ)

    print('Finished occupancy calculation.\n')

    #  #  Generate ventilation rate (window opening etc.)
    #  #####################################################################

    #  Get infiltration rate
    if mod_year is None:
        year = build_year
    else:
        year = mod_year
    inf_rate = usair.get_inf_rate(year)

    if air_vent_mode == 0:  # Use constant value
        array_vent = None  # If array_vent is None, use default values

    elif air_vent_mode == 1:  # Use deterministic, temp-dependent profile
        array_vent = \
            usair.gen_det_air_ex_rate_temp_dependend(occ_profile=
                                                     occupancy_obj.occupancy,
                                                     temp_profile=
                                                     environment.weather.tAmbient,
                                                     inf_rate=inf_rate)


    elif air_vent_mode == 2:
        #  Get ventilation rate (in 1/h, related to building air volume)
        array_vent = \
            usair.gen_user_air_ex_rate(occ_profile=occupancy_obj.occupancy,
                                       temp_profile=environment.weather.tAmbient,
                                       b_type='res',
                                       inf_rate=inf_rate)

    #  #  Create electrical load
    #  #####################################################################

    print('Calculate el. load.\n')

    # el_dem_stochastic = \
    #     eldem.ElectricalDemand(environment,
    #                            method=2,
    #                            annualDemand=el_demand,
    #                            do_normalization=True,
    #                            total_nb_occupants=num_occ,
    #                            randomizeAppliances=True,
    #                            lightConfiguration=10,
    #                            occupancy=occupancy_obj.occupancy[:])

    # #  Instead of stochastic profile, use SLP to be faster with calculation
    el_dem_stochastic = eldem.ElectricalDemand(environment,
                                               method=1,
                                               # Standard load profile
                                               profileType="H0",
                                               annualDemand=el_demand)

    print('Finished el. load calculation.\n')

    #  #  Create apartment and building object
    #  #####################################################################

    #  Create apartment
    apartment = Apartment.Apartment(environment)

    #  Add demands to apartment
    apartment.addMultipleEntities([el_dem_stochastic, occupancy_obj])

    #  Create extended building object
    extended_building = build_ex.BuildingExtended(environment,
                                                  build_year=build_year,
                                                  mod_year=mod_year,
                                                  build_type=0,
                                                  roof_usabl_pv_area=30,
                                                  net_floor_area=200,
                                                  height_of_floors=2.8,
                                                  nb_of_floors=2,
                                                  neighbour_buildings=0,
                                                  residential_layout=0,
                                                  attic=1, cellar=1,
                                                  construction_type='heavy',
                                                  dormer=1)
    #  BuildingExtended holds further, optional input parameters,
    #  such as ground_area, nb_of_floors etc.

    #  Add apartment to extended building
    extended_building.addEntity(entity=apartment)

    #  Calculate thermal space heating load and add instance to building
    #  #####################################################################
    (temp_in, q_heat_cool, q_in_wall, q_out_wall) = \
        tus.calc_th_load_build_vdi6007_ex_build(exbuild=extended_building,
                                                add_th_load=True,
                                                vent_factor=vent_factor,
                                                array_vent_rate=array_vent,
                                                t_set_heat=t_set_heat,
                                                t_set_cool=t_set_cool,
                                                t_night=t_set_night,
                                                heat_lim_val=heat_lim_val)

    #  Results
    #  #####################################################################
    q_heat = np.zeros(len(q_heat_cool))
    q_cool = np.zeros(len(q_heat_cool))
    for i in range(len(q_heat_cool)):
        if q_heat_cool[i] > 0:
            q_heat[i] = q_heat_cool[i]
        elif q_heat_cool[i] < 0:
            q_cool[i] = q_heat_cool[i]

    sh_energy = sum(q_heat) * (timestep / 3600) / 1000

    print('Sum of net space heating heating energy in kWh:')
    print(sh_energy)

    print('Specific net space heating energy demand in kWh/m2:')
    print(sh_energy / extended_building.net_floor_area)

    if sum(q_cool) < 0:
        print('Sum of cooling energy in kWh:')
        print(-sum(q_cool) * (timestep / 3600)  / 1000)

    if plot_res:
        import matplotlib.pyplot as plt

        fig = plt.figure()
        if air_vent_mode != 2:
            fig.add_subplot(311)
            plt.plot(environment.weather.tAmbient)
            plt.ylabel('Outdoor air\ntemperature in\ndegree Celsius')
            fig.add_subplot(312)
            plt.plot(temp_in)
            plt.ylabel('Indoor air\ntemperature in\ndegree Celsius')
            fig.add_subplot(313)
            plt.plot(q_heat_cool / 1000)
            plt.ylabel('Heating/cooling\npower (+/-)\nin kW')
            plt.xlabel('Time in hours')
        else:
            fig.add_subplot(411)
            plt.plot(environment.weather.tAmbient)
            plt.ylabel('Outdoor air\ntemperature in\ndegree Celsius')
            fig.add_subplot(412)
            plt.plot(temp_in)
            plt.ylabel('Indoor air\ntemperature in\ndegree Celsius')
            fig.add_subplot(413)
            plt.plot(q_heat_cool / 1000)
            plt.ylabel('Heating/cooling\npower (+/-)\nin kW')
            fig.add_subplot(414)
            plt.plot(array_vent)
            plt.ylabel('Air\nexchange\nrate in 1/h')
            plt.xlabel('Time in hours')
        plt.tight_layout()
        plt.show()
        plt.close()

if __name__ == '__main__':
    run_example_vdi_6007(True)
