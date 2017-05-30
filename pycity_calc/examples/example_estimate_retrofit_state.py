#!/usr/bin/env python
# coding=utf-8
"""
Script to estimate state of retrofit for single building instance
"""

import pycity.classes.Weather as Weather
import pycity.classes.demand.Occupancy as occ
import pycity.classes.demand.ElectricalDemand as eldem
import pycity.classes.demand.Apartment as Apartment

import pycity_calc.buildings.building as build_ex
import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.environment as env
import pycity_calc.environments.market as mark
import pycity_calc.environments.timer as time

import pycity_calc.toolbox.data_enrichment.retrofit_state.estimate_retrofit \
    as retrostate


def run_example_retro_estimate():
    """
    Run example to estimate state of retrofit of building for given
    net space heating demand input
    """

    #  Define simulation settings
    build_year = 1962  # Year of construction
    mod_year = None  # Year of retrofit

    el_demand = 3000  # Annual, el. demand in kWh

    sh_ref = 10000  # Reference net space heating demand in kWh

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

    # #  Create electrical load
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
                                                  net_floor_area=100,
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

    retrostate.estimate_build_retrofit(building=extended_building,
                                       sh_ann_demand=sh_ref,
                                       print_output=True)

    print('Last year of retrofit chosen for reference model: ',
          extended_building.mod_year)


if __name__ == '__main__':
    run_example_retro_estimate()
