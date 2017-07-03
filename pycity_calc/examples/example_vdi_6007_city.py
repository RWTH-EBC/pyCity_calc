#!/usr/bin/env python
# coding=utf-8
"""
Example script how to calculate thermal space heating load with TEASER and
VDI 6007 calculation core for whole city district

Steps:
- Generate environment
- Generate occuancy object
- Generate el. load object
- Generate apartment and add profile objects
- Generate building and add apartment
- Run VDI simulation with building
"""

import os
import pickle
import matplotlib.pylab as plt

import pycity_calc.toolbox.teaser_usage.teaser_use as tus

try:
    from teaser.project import Project
    import teaser.logic.simulation.VDI_6007.low_order_VDI as low_order_vdi
    import teaser.logic.simulation.VDI_6007.weather as vdiweather
except:
    raise ImportError('Could not import TEASER package. Please check your '
                      'installation. TEASER can be found at: '
                      'https://github.com/RWTH-EBC/TEASER. '
                      'Installation is possible via pip.')

def run_example_vdi_city(plot_res=False):

    requ_profiles = True
    # requ_profiles : bool, optional
    #     Defines, if function demands occupancy and electrical load profiles
    #     for VDI usage (default: True).
    #     If set to True: Requires profile on every building
    #     If set to False: Set user profile and el. load profiles to zero

    t_set_heat = 20  # Heating set temperature in degree Celsius
    t_set_night = 16  # Night set back temperature in degree Celsius
    t_set_cool = 70  # Cooling set temperature in degree Celsius

    air_vent_mode = 1
    #  int; Define mode for air ventilation rate generation
    #  0 : Use constant value (vent_factor in 1/h)
    #  1 : Use deterministic, temperature-dependent profile
    #  2 : Use stochastic, user-dependent profile
    #  False: Use static ventilation rate value

    vent_factor = 0.5  # Constant. ventilation rate
    #  (only used, if air_vent_mode == 0)

    heat_lim_val = None  # Heater limit in Watt

    this_path = os.path.dirname(os.path.abspath(__file__))
    filename = 'city_vdi_6007_input.p'
    file_path = os.path.join(this_path, 'inputs', filename)

    #  Load city pickle file
    city = pickle.load(open(file_path, 'rb'))

    #  Perform VDI 6007 simulation for every building in city and add
    #  space heating demand object to each building
    tus.calc_and_add_vdi_6007_loads_to_city(city=city,
                                            requ_profiles=requ_profiles,
                                            air_vent_mode=air_vent_mode,
                                            vent_factor=vent_factor,
                                            t_set_heat=t_set_heat,
                                            t_set_cool=t_set_cool,
                                            t_night=t_set_night,
                                            alpha_rad=None,
                                            project_name='project',
                                            heat_lim_val=heat_lim_val)

    city_th_load = city.get_aggr_space_h_power_curve()

    print()
    print('Total net thermal space heating energy demand in kWh/a:')
    print(city.get_annual_space_heating_demand())

    if plot_res:
        plt.plot(city_th_load)
        plt.xlabel('Time in hours')
        plt.ylabel('City district space heating load in W')
        plt.show()

        build_1 = city.node[1001]['entity']

        sp_heat_load = build_1.get_space_heating_power_curve()

        plt.plot(sp_heat_load)
        plt.xlabel('Time in hours')
        plt.ylabel('Space heating load of building 1001')
        plt.show()

if __name__ == '__main__':

    run_example_vdi_city(True)