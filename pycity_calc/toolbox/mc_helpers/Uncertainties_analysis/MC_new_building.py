#!/usr/bin/env python
# coding=utf-8
"""
Script to reevaluate building for Monte carlo analysis
"""

import pycity_calc.toolbox.mc_helpers.demand_unc_single_build as dem_unc_b
import pycity_calc.toolbox.mc_helpers.weather.gen_weather_set as wea
import numpy as np
import pycity_calc.toolbox.teaser_usage.teaser_use as tus
import warnings
import pycity_calc.buildings.building as build_ex
import pycity.classes.demand.Apartment as Apartment
import pycity.classes.demand.ElectricalDemand as ElectricalDemand
import pycity.classes.demand.DomesticHotWater as dhwater
import pycity.classes.demand.Occupancy as occ
import pycity.classes.Weather as Weather
import pycity_calc.environments.environment as env
import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.market as mark
import pycity_calc.environments.timer as time
import matplotlib.pyplot as plt
import pycity.functions.changeResolution as chgr


def new_building_evaluation_mc(building, new_weather, max_retro_year=2014, time_sp_force_retro=40,
                               build_physic_unc=True, MC_analysis=True, nb_occ_unc=True):
    """
        Modifies building parameters for Monte Carlo Analysis

        Parameters
    ----------
    building : object
        Extended building object of pycity_calc (should hold occupancy profile)
    time_sp_force_retro : int, optional
        Timespan, in which a retrofit action is forced to the system.
        (default: 40).
    max_retro_year : int, optional
        Maximal / youngest possible retrofit year for sampling (default: 2014)
    nb_occ_unc : bool, optional
        Defines, if number of occupants per apartment is unknown
        (default: True).
        If set to True, number of occupants is unknown
        If set to False, uses number of occupants on occupancy objects
        as known values.
    MC_analysis: boolean, optional
            Defines extra modifications for monte carlo analysis
            (dormer,attic,cellar, construction_type, net_floor_area)
    buil_physic_unc: bool, optional
        Defines,if building physics unknown or not (default: True)
        True - Building physics is unknown
        False - Building physics is known (year of modernisation, dormer, cellar , construction type
                and attic are fixed, net floor area variation is smaller)

        Returns
        -------
        building : object
            Modified extended building object
        dict_problem : dict (of list)
            Dictionary of inputs with problems
            Keys:
            'year' : Holding modification year sample lists
            'infiltration' : Holding infiltration rate sample lists
            'dormer' : Holding dormer samples list
            'cellar' : Holding cellar samples list
            'attic' : Holding attic samples list
            'user_air' : Holding user air ventilation factor sampling
        el_demand : float
                    Electrical demand for this building per year (kWh)
        dhw_energy : float
                    Domestic hot water per year (kWh)
        sum_heat : float
                    Space heating demand per year (kWh)
        """

    # #################################################################
    # Initialisation:

    # Timestep definition
    timestep = building.environment.timer.timeDiscretization

    dict_problem = {}
    dict_problem['infiltration'] = []
    dict_problem['dormer'] = []
    dict_problem['attic'] = []
    dict_problem['cellar'] = []
    dict_problem['user_air'] = []
    dict_problem['year'] = []

    print('Start Modification building')
    print ()

    # ###############################################################
    # New building parameters

    #  Extract single sample dict for each parameter
    dict_samples = dem_unc_b.building_unc_sampling(exbuilding=building,
                                                   nb_samples=1,
                                                   max_retro_year=max_retro_year,
                                                   time_sp_force_retro=time_sp_force_retro,
                                                   nb_occ_unc=nb_occ_unc,buil_physic_unc=build_physic_unc)

    # new_physics parameters
    new_building = dem_unc_b.mod_single_build_w_samples(building,  dict_samples,
                                                        new_weather, i=0, MC_analysis=MC_analysis,
                                                        build_physic_unc=build_physic_unc)


    # New space heating
    # Get samples for parameters, which are not stored on building object
    inf_rate = dict_samples['inf']
    print('Inf. rate: ', inf_rate)
    usr_air_ex_rate = dict_samples['user_air']
    print('User air exchange rate: ', usr_air_ex_rate)

    vent_array = np.zeros(len(building.environment.weather.tAmbient))

    vent_array += inf_rate + usr_air_ex_rate
    #  Sum up user air exchange and infiltration

    tset_heat = dict_samples['set_temp'][0]
    print('Set temperature: ', tset_heat)

    #  Perform VDI 6007 simulation
    #  ##################################################################
    (temp_in, q_heat_cool, q_in_wall, q_out_wall) = tus.calc_th_load_build_vdi6007_ex_build(exbuild=new_building,
                                                                                            add_th_load=True,
                                                                                            vent_factor=None,
                                                                                            array_vent_rate=vent_array,
                                                                                            t_set_heat=tset_heat,
                                                                                            t_set_cool=100,
                                                                                            t_night=16,
                                                                                            heat_lim_val=1000000)


    #  Results
    #  #################################################################

    q_heat = np.zeros(len(q_heat_cool))
    for step_time in range(len(q_heat_cool)):
        if q_heat_cool[step_time] > 0:
            q_heat[step_time] = q_heat_cool[step_time]

    sum_heat = sum(q_heat) * timestep / (3600 * 1000)  # in kWh
    print('Sum net space heating energy in kWh: ', sum_heat)

    if sum_heat < 0:
        msg = 'Net space heating demand is smaller than zero!'
        raise AssertionError(msg)
    if sum_heat == 0:
        msg = 'Net space heating demand is equal to zero. Check if ' \
              'this is possible (e.g. high retrofit with low set temp ' \
              'and high internal loads.)'
        warnings.warn(msg)

        dict_problem['infiltration'].append(dict_samples['inf'][0])
        dict_problem['dormer'].append(dict_samples['dormer'][0])
        dict_problem['attic'].append(dict_samples['attic'][0])
        dict_problem['cellar'].append(dict_samples['cellar'][0])
        dict_problem['user_air'].append(dict_samples['user_air'][0])
        dict_problem ['year'].append(dict_samples['mod_year'][0])

    #  Get el. demand and dhw energy for a building
    el_demand = new_building.get_annual_el_demand()
    dhw_energy = new_building.get_annual_dhw_demand()

    print('El. energy demand in kWh for this building:')
    print(el_demand)
    print('Dhw energy demand in kWh for this building:')
    print(dhw_energy)
    print('Dhw volume per day in liters (per building):')
    print((dhw_energy * 3600 * 1000) / (4200 * 35 * 365))
    print('Total thermal demand in kWh for this building: ', (dhw_energy+sum_heat))
    print('Finished Monte-Carlo space heating simulation for building ')
    print()
    print('############################################################')
    print()

    #for j in range(len(new_building.apartments)):
        #elcurve = chgr.changeResolution(new_building.apartments[j].power_el.loadcurve,
                                        #oldResolution = len(new_building.apartments[j].power_el.loadcurve),
                                        #newResolution=8760 )

        #new_building.apartments[j].power_el.loadcurve = elcurve

        #print(len(new_building.apartments[j].power_el.loadcurve))

        #space_heating = chgr.changeResolution(values = new_building.apartments[j].demandSpaceheating.loadcurve,
                                                                 #oldResolution = len(new_building.apartments[j].demandSpaceheating.loadcurve),
                                                                 #newResolution=8760 )
        #new_building.apartments[j].demandSpaceheating.loadcurve = space_heating
        #dhwapp = chgr.changeResolution(values = new_building.apartments[j].demandDomesticHotWater.loadcurve,
                                                                 #oldResolution=len(new_building.apartments[j].demandDomesticHotWater.loadcurve),
                                                                 #newResolution=8760)

        #new_building.apartments[j].demandDomesticHotWater.loadcurve = dhwapp

    #print(len(new_building.get_electric_power_curve()))
    #print(len(new_building.get_space_heating_power_curve()))
    #print(len(new_building.get_dhw_power_curve()))

    return new_building,  dict_problem, el_demand, dhw_energy, sum_heat

if __name__ == '__main__':

    # ## Building generation
    # ######################

    #  Define simulation settings
    build_year = 1993  # Year of construction
    mod_year = 2000  # Year of retrofit
    net_floor_area = 200  # m2
    height_of_floors = 2.8  # m
    nb_of_floors = 2  # m
    num_occ = 3  # Set fix to prevent long run time for multiple new occupancy
    #  and electrical load profiles
    Nsamples = 1000

    #  #  Create PyCity_Calc environment
    #  ###############################################################

    #  Create extended environment of pycity_calc
    year = 2010
    timestep = 3600  # Timestep in seconds
    location = (51.529086, 6.944689)  # (latitude, longitute) of Bottrop
    altitude = 55  # Altitude of Bottrop

    #  ###############################################################

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

    print('Calculate occupancy.\n')
    #  Generate occupancy profile
    occupancy_obj = occ.Occupancy(environment, number_occupants=num_occ)

    print('Finished occupancy calculation.\n')

    # #  Create electrical load
    #  #####################################################################

    print('Calculate el. load.\n')

    el_dem_stochastic = ElectricalDemand.ElectricalDemand(environment,
                               method=2,
                               annualDemand=3000,  # Dummy value
                               do_normalization=True,
                               total_nb_occupants=num_occ,
                               randomizeAppliances=True,
                               lightConfiguration=10,
                               occupancy=occupancy_obj.occupancy[:])

    print('Finished el. load calculation.\n')

    #  # Create dhw load
    #  #####################################################################
    dhw_stochastical = dhwater.DomesticHotWater(environment,
                                 tFlow=60,
                                 thermal=True,
                                 method=2,
                                 supplyTemperature=20,
                                 occupancy=occupancy_obj.occupancy)

    #  #  Create apartment and building object
    #  #####################################################################

    #  Create apartment
    apartment = Apartment.Apartment(environment)

    #  Add demands to apartment
    apartment.addMultipleEntities([el_dem_stochastic, occupancy_obj,
                                   dhw_stochastical])

    #  Create extended building object
    extended_building = build_ex.BuildingExtended(environment,
                                  build_year=build_year,
                                  mod_year=mod_year,
                                  build_type=0,
                                  roof_usabl_pv_area=30,
                                  net_floor_area=net_floor_area,
                                  height_of_floors=height_of_floors,
                                  nb_of_floors=nb_of_floors,
                                  neighbour_buildings=0,
                                  residential_layout=0,
                                  attic=1, cellar=1,
                                  construction_type='heavy',
                                  dormer=1)

    #  Add apartment to extended building
    extended_building.addEntity(entity=apartment)

    # Get list of new weather

    list_weath = wea.gen_set_of_weathers(Nsamples,year=year)


    # ## function to do return for this building
    sh_demand_list = []
    el_demand_list = []
    dhw_demand_list = []
    dict_sp_zero = {}

    for i in range(Nsamples):
        # Get the weather
        new_weather = []
        new_weather.append(list_weath[i])
        building, dict_problem, el_demand, dhw_energy, sum_heat = new_building_evaluation_mc(extended_building,
                                                                                             new_weather=new_weather)

        # Add results to list of results
        sh_demand_list.append(sum_heat)
        el_demand_list.append(el_demand)
        dhw_demand_list.append(dhw_energy)
        if sum_heat==0:
            dict_sp_zero[str(i)] = dict_problem

    print('End simulations')

    fig = plt.figure()
    # the histogram of the data
    plt.hist(sh_demand_list, 100)
    plt.xlabel('Space heating net energy demand in kWh')
    plt.ylabel('Number of values')
    plt.show()
    plt.close()

    fig = plt.figure()
    # the histogram of the data
    plt.hist(el_demand_list, 100)
    plt.xlabel('Electric energy demand in kWh')
    plt.ylabel('Number of values')
    plt.show()
    plt.close()

    fig = plt.figure()
    # the histogram of the data
    plt.hist(dhw_demand_list, bins='auto')
    plt.xlabel('Hot water energy demand in kWh')
    plt.ylabel('Number of values')
    plt.show()
    plt.close()

    for keys in dict_problem:

        print(dict_problem[keys])
