# coding=utf-8
"""
Example script for usage of city class.
"""
from __future__ import division

import shapely.geometry.point as point

import pycity_base.classes.Weather as Weather
import pycity_base.classes.demand.SpaceHeating as SpaceHeating
import pycity_base.classes.demand.ElectricalDemand as ElectricalDemand
import pycity_base.classes.demand.Apartment as Apartment

import pycity_calc.buildings.building as build_ex
import pycity_calc.cities.city as city
import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.environment as env
import pycity_calc.environments.market as mark
import pycity_calc.environments.timer as time
# import pycity_calc.toolbox.dimensioning.dim_functions as dimfunc


def run_example():
    """
    Run example to create city object of pycity with 3 buildings
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

    #  Generate city object
    city_object = city.City(environment=environment)

    #  Iterate 3 times to generate 3 building objects
    for i in range(3):
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

        extended_building = build_ex.BuildingExtended(environment,
                                                      build_year=1962,
                                                      mod_year=2003,
                                                      build_type=0,
                                                      roof_usabl_pv_area=30,
                                                      net_floor_area=150,
                                                      height_of_floors=3,
                                                      nb_of_floors=2,
                                                      neighbour_buildings=0,
                                                      residential_layout=0,
                                                      attic=0, cellar=1,
                                                      construction_type='heavy',
                                                      dormer=0)

        #  Add apartment to extended building
        extended_building.addEntity(entity=apartment)

        position = point.Point(i * 10, 0)

        city_object.add_extended_building(extended_building=extended_building,
                                          position=position)

    print('Get demands of all buildings')
    print('Get number of buildings:')
    print(city_object.get_nb_of_building_entities())

    print('\nGet list of node ids with building objects:')
    print(city_object.get_list_build_entity_node_ids())

    print('\nGet annual space heating demand of all buildings')
    print(city_object.get_annual_space_heating_demand())

    # print('\nGet thermal annual load duration curve')
    # print(dimfunc.get_ann_load_dur_curve(city_object))

    print('\nNode ids of original city district')
    print(city_object.nodes(data=False))
    print('With data:')
    print(city_object.nodes(data=True))

    # print('\nGet max. th. power of city district (space heating + dhw) in W:')
    # print(dimfunc.get_max_p_of_city(city_object, get_thermal=True,
    #                                 with_dhw=True))

    # (id, th_p) = dimfunc.get_id_max_th_power(city=city_object, with_dhw=True,
    #                                          find_max=False, return_value=True)
    # print('\nGet id of building with smallest max. th. power value:')
    # print(id)
    # print('Smallest max. th. power value in W:')
    # print(th_p)

    return city_object


if __name__ == '__main__':
    #  Execute example
    city_object = run_example()
