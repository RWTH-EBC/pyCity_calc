#!/usr/bin/env python
# coding=utf-8
"""
Script to sample new parameters and add them to existing city object.
"""

import os
import pickle
import copy
import numpy as np

import pycity_base.functions.changeResolution as chres

import pycity_calc.toolbox.mc_helpers.building.build_unc_set_gen as bunc
import pycity_calc.toolbox.mc_helpers.user.user_unc_sampling as usunc
import pycity_calc.toolbox.teaser_usage.teaser_use as tus
import pycity_calc.toolbox.user.user_air_exchange as usair


def randomize_city_params(city, mod_year=False, inf=False, temp_set=False,
                          el=False, dhw=False, max_retro_year=2014,
                          time_sp_force_retro=40, set_temp=20,
                          air_vent_mode=2):
    """
    Re-sample and overwrite specific parameters on city object and return
    new city object.

    Only working for residential buildings!

    Parameters
    ----------
    city : object
        City object of pycity_calc
    mod_year : bool, optional
        Defines, if mod_years should be re-sampled (default: False)
    inf : bool, optional
        Defines, if infiltration rates should be re-sampled (default: False)
    temp_set : bool, optional
        Defines, if set_temperatures should be re-sampled (default: False)
    el : bool, optional
        Defines, if electric energy demand should be re-sampled
        (default: False)
    dhw : bool, optional
        Defines, if hot water demands should be re-sampled (default: False)
    max_retro_year : int, optional
        Maximal / youngest possible retrofit year for sampling (default: 2014)
    time_sp_force_retro : int, optional
        Timespan, in which a retrofit action is forced to the system.
        (default: 40).
    set_temp : float, optional
        Default set temperature in degree Celsius (default: 20)
    air_vent_mode : int, optional
        Defines method to generation air exchange rate for VDI 6007 simulation
        (default: 2)
        Options:
        0 : Use constant value (vent_factor in 1/h)
        1 : Use deterministic, temperature-dependent profile
        2 : Use stochastic, user-dependent profile

    Returns
    -------
    city_new : object
        City object of pycity_calc with new sample data
    """

    city_new = copy.deepcopy(city)

    timestep = city_new.environment.timer.timeDiscretization

    #  Get list with building entity node ids
    list_b_ids = city_new.get_list_build_entity_node_ids()

    for n in list_b_ids:

        curr_b = city_new.nodes[n]['entity']

        if curr_b.build_type == 0:  # Residential buildings, only
            print('Process building: ', n)
            print('#########################################################')

            build_year = curr_b.build_year

            if mod_year:
                #  Resample mod. years
                sample_mod_year = \
                    bunc.calc_array_mod_years_single_build(nb_samples=1,
                                                          year_of_constr=build_year,
                                                          max_year=max_retro_year,
                                                          time_sp_force_retro=
                                                          time_sp_force_retro)[0]

                #  Overwrite mod year (or year of construction)
                #  If mod_year is smaller than 1982 (smallest retrofit option in teaser)
                #  add mod_year as new year of construction
                if sample_mod_year < 1982:
                    curr_b.build_year = sample_mod_year
                    curr_b.mod_year = None
                else:
                    #  Else, define new year of modernization
                    curr_b.mod_year = sample_mod_year

                print('Sampled mod. year: ', sample_mod_year)
                print('Set year of construction: ', curr_b.build_year)
                print('Set year of modernization: ', curr_b.mod_year)
            else:
                sample_mod_year = curr_b.mod_year

            if inf:
                #  Resample infiltration rate
                sample_inf = bunc.calc_inf_samples(nb_samples=1)[0]

                print('Sampled inf. rate in 1/h: ', sample_inf)
            else:
                if sample_mod_year is not None:
                    sample_inf = usair.get_inf_rate(mod_year=sample_mod_year)
                else:
                    sample_inf = usair.get_inf_rate(mod_year=build_year)

            if temp_set:

                list_set_temp_per_app = []

                for i in range(len(curr_b.apartments)):
                    #  Resample set temperature
                    sample_set_temp = usunc.calc_set_temp_samples(nb_samples=1)[0]
                    list_set_temp_per_app.append(sample_set_temp)

                # Calculate average set temperature over all apartments
                sample_set_temp = sum(list_set_temp_per_app) / \
                                  len(list_set_temp_per_app)

                print('Sampled set temperature in degree C: ', sample_set_temp)

            else:
                sample_set_temp = set_temp

            if el:
                #  Resample el. energy demands
                if len(curr_b.apartments) > 1:
                    btype = 'mfh'
                else:
                    btype = 'sfh'

                for app in curr_b.apartments:
                    nb_occ = app.get_max_nb_occupants()

                    #  Electrical demand per apartment, based on nb. of users
                    sample_el_dem = \
                        usunc.calc_sampling_el_demand_per_apartment(
                            nb_samples=1,
                            nb_persons=nb_occ,
                            type=btype)[0]

                    #  Rescale el. demand for apartment
                    #  Current electrical demand
                    curr_dem = \
                        sum(app.get_total_el_power(
                            currentValues=False) \
                            * timestep / (3600 * 1000))

                    #  Rescale el. load curve
                    app.power_el.loadcurve *= \
                        (sample_el_dem / curr_dem)

                    print('Sampled el. energy demand in kWh (per apartment): '
                          '', sample_el_dem)
                    print('Original el. en. demand in kWh (per apartment): '
                          '', curr_dem)

            if dhw:
                #  Resample dhw demand
                for app in curr_b.apartments:
                    #  Hot water volume per apartment
                    sample_dhw = \
                        usunc.calc_sampling_dhw_per_apartment(
                            nb_samples=1,
                            nb_persons=nb_occ)[0]

                    volume = sum(app.demandDomesticHotWater.water) * \
                             timestep / 3600

                    volume_per_day = volume / 365

                    conv_dhw = sample_dhw / volume_per_day

                    #  Convert water volume
                    app.demandDomesticHotWater.water *= conv_dhw

                    #  Convert dhw heat power
                    app.demandDomesticHotWater.loadcurve *= conv_dhw

                    print('Sampled volume in liters per day and apartment; ',
                          sample_dhw)

                    print('Original volume in liters per day and apartment; ',
                          volume_per_day)

            # Calculate new space heating load profile
            if mod_year or inf or temp_set:

                #  Define pointer to outdoor temperature
                temp_out = city.environment.weather.tAmbient

                if air_vent_mode == 0:
                    array_vent = None  # If array_vent is None, use constant

                elif air_vent_mode == 1:  # Use deterministic, temp-dependent profile

                    #  Generate dummy array
                    array_vent = np.zeros(len(temp_out))

                    #  Loop over all apartments
                    for ap in curr_b.apartments:

                        occ_profile = ap.get_occupancy_profile()[:]

                        if len(occ_profile) != 365 * 24 * 3600 / timestep:
                            #  Change resolution to timestep of environment
                            org_res = 365 * 24 * 3600 / len(occ_profile)

                            occ_profile = \
                                chres.changeResolution(occ_profile,
                                                       oldResolution=org_res,
                                                       newResolution=timestep)

                        # Sum up air exchange rates of all apartments
                        array_vent += \
                            usair.gen_det_air_ex_rate_temp_dependend(occ_profile=
                                                                     occ_profile,
                                                                     temp_profile=
                                                                     temp_out,
                                                                     inf_rate=0)

                    # Finally, add infiltration rate of building
                    array_vent += sample_inf

                    #  Divide by apartment number (because of normalizing
                    #  air exchange to total building volume)
                    array_vent /= len(curr_b.apartments)

                elif air_vent_mode == 2:

                    #  Generate dummy array
                    array_vent = np.zeros(len(temp_out))

                    #  Loop over all apartments
                    for ap in curr_b.apartments:

                        occ_profile = ap.get_occupancy_profile()[:]

                        if len(occ_profile) != 365 * 24 * 3600 / timestep:
                            #  Change resolution to timestep of environment
                            org_res = 365 * 24 * 3600 / len(occ_profile)

                            occ_profile = \
                                chres.changeResolution(occ_profile,
                                                       oldResolution=org_res,
                                                       newResolution=timestep)

                        # Sum up air exchange rate profiles
                        #  Get ventilation rate (in 1/h, related to building air volume)
                        array_vent += \
                            usair.gen_user_air_ex_rate(
                                occ_profile=occ_profile,
                                temp_profile=temp_out,
                                b_type='res',
                                inf_rate=0)

                    # Finally, add infiltration rate of building
                    array_vent += sample_inf

                    #  Divide by apartment number (because of normalizing
                    #  air exchange to total building volume)
                    array_vent /= len(curr_b.apartments)

                tus.calc_th_load_build_vdi6007_ex_build(exbuild=curr_b,
                                                        add_th_load=True,
                                                        array_vent_rate=array_vent,
                                                        vent_factor=sample_inf,
                                                        t_set_heat=sample_set_temp)
                print()

    ann_space_heat = round(city.get_annual_space_heating_demand(), 2)
    ann_el_dem = round(city.get_annual_el_demand(), 2)
    ann_dhw_dem = round(city.get_annual_dhw_demand(), 2)

    ann_space_heat_new = round(city_new.get_annual_space_heating_demand(), 2)
    ann_el_dem_new = round(city_new.get_annual_el_demand(), 2)
    ann_dhw_dem_new = round(city_new.get_annual_dhw_demand(), 2)

    print('Original annual net thermal space heating demand in kWh: ')
    print(ann_space_heat)
    print('New annual net thermal space heating demand in kWh: ')
    print(ann_space_heat_new)
    print('Difference')
    print(ann_space_heat_new - ann_space_heat)
    print('Percentage')
    print((ann_space_heat_new - ann_space_heat) * 100 / ann_space_heat)
    print('%')
    print()

    print('Original annual electrical demand in kWh: ')
    print(ann_el_dem)
    print('New annual electrical demand in kWh: ')
    print(ann_el_dem_new)
    print('Difference')
    print(ann_el_dem_new - ann_el_dem)
    print('Percentage')
    print((ann_el_dem_new - ann_el_dem) * 100 / ann_el_dem)
    print('%')
    print()

    print('Original annual hot water energy demand in kWh: ')
    print(ann_dhw_dem)
    print('New annual electrical demand in kWh: ')
    print(ann_dhw_dem_new)
    print('Difference')
    print(ann_dhw_dem_new - ann_dhw_dem)
    print('Percentage')
    print((ann_dhw_dem_new - ann_dhw_dem) * 100 / ann_dhw_dem)
    print('%')
    print()

    return city_new

if __name__ == '__main__':
    this_path = os.path.dirname(os.path.abspath(__file__))

    mod_year = False
    inf = False
    temp_set = True
    el = True
    dhw = True

    city_f_name = 'aachen_preusweg_5b.pkl'
    out_f_name = city_f_name[:-3] + '_resamples.pkl'

    city_path = os.path.join(this_path, 'input', city_f_name)
    out_path = os.path.join(this_path, 'output', out_f_name)

    city = pickle.load(open(city_path, mode='rb'))

    city_new = randomize_city_params(city=city, mod_year=mod_year, inf=inf,
                                     temp_set=temp_set, el=el, dhw=dhw)

    pickle.dump(city_new, open(out_path, mode='wb'))
