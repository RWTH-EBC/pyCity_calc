# coding=utf-8
"""
Example script for usage of BuildingExtended class.
(inheritance of building object of pycity)
"""
from __future__ import division
import pycity_base.classes.Weather as Weather
import pycity_base.classes.demand.SpaceHeating as SpaceHeating
import pycity_base.classes.demand.ElectricalDemand as ElectricalDemand
import pycity_base.classes.demand.Apartment as Apartment

import pycity_calc.buildings.building as build_ex
import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.environment as env
import pycity_calc.environments.market as mark
import pycity_calc.environments.timer as time
import pycity_calc.toolbox.dimensioning.dim_functions as dimfunc


def run_example():
    """
    Run example to generate BuildingExtended object of pycity_calc
    (inheritance of building object of pycity)
    """

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

    #  Create demands (with standardized load profiles (method=1))
    heat_demand = SpaceHeating.SpaceHeating(environment,
                                            method=1,
                                            profile_type='HEF',
                                            livingArea=100,
                                            specificDemand=130)

    el_demand = ElectricalDemand.ElectricalDemand(environment, method=1,
                                                  annualDemand=3000,
                                                  profileType="H0")

    #  Create apartment
    apartment = Apartment.Apartment(environment)

    #  Add demands to apartment
    apartment.addMultipleEntities([heat_demand, el_demand])

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

    print('Get building space heating power curve:')
    print(extended_building.get_space_heating_power_curve())

    print('Length of space heating power curve array:')
    print(len(extended_building.get_space_heating_power_curve()))

    print('\nGet building electrical power curve:')
    print(extended_building.get_electric_power_curve())

    print('Length of electrical power curve array:')
    print(len(extended_building.get_electric_power_curve()))

    print('\nGet building hot water power curve:')
    print(extended_building.get_dhw_power_curve())

    print('Length of hot water power curve array:')
    print(len(extended_building.get_dhw_power_curve()))

    print('\nGet annual load duration curve (space heating):')
    print(dimfunc.get_load_dur_curve_building(extended_building))

    print('\nGet max. thermal power of building:')
    p_max = dimfunc.get_max_power_of_building(extended_building,
                                              get_therm=True, with_dhw=False)
    print('Max. thermal power in kW: ', p_max/1000)

    print('\nCalculate nominal th. power for CHP with ' +
          'max. rectangular method.')
    chp_nom_power = \
        dimfunc.calc_chp_nom_th_power_building(building=extended_building,
                                               method=1, min_runtime=None,
                                               force_min_runtime=False,
                                               with_dhw=False)
    print('Nominal thermal CHP power in kW:', chp_nom_power/1000)

    return extended_building

if __name__ == '__main__':

    #  Execute example
    building_object = run_example()
