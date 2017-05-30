#!/usr/bin/env python
# coding=utf-8
"""

"""

import shapely.geometry.point as point

import pycity.classes.Weather as Weather
import pycity.classes.demand.SpaceHeating as SpaceHeating
import pycity.classes.demand.ElectricalDemand as ElectricalDemand
import pycity.classes.demand.Apartment as Apartment

import pycity_calc.buildings.building as build_ex
import pycity_calc.cities.city as cit
import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.environment as env
import pycity_calc.environments.market as mark
import pycity_calc.environments.timer as time
import pycity_calc.toolbox.networks.network_ops as netop


def r_process_neighbours():
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
    city_object = cit.City(environment=environment)

    position_1 = point.Point(0, 0)
    position_2 = point.Point(0, 10)
    position_3 = point.Point(10, 0)
    dict_pos = {0: position_1, 1: position_2, 2: position_3}

    for i in range(0, 3):
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
        extended_building = build_ex.BuildingExtended(environment,
                                                      build_year=1962,
                                                      mod_year=2003,
                                                      build_type=0)

        #  Add apartment to extended building
        extended_building.addEntity(entity=apartment)

        #  Add 3 extended buildings to city object
        city_object.add_extended_building(extended_building=extended_building,
                                          position=dict_pos[i])

    #  Add heating network
    heat_point = point.Point(0, 5)
    heat_1 = city_object.add_network_node(network_type='heating',
                                          position=heat_point)

    #  Add heating network edges
    city_object.add_edge(1001, heat_1, network_type='heating')
    city_object.add_edge(heat_1, 1002, network_type='heating')
    city_object.add_edge(1001, 1003, network_type='heating')

    list_lhn = \
        netop.get_list_with_energy_net_con_node_ids(city=city_object,
                                                    network_type='heating')

    list_deg = \
        netop.get_list_with_energy_net_con_node_ids(city=city_object,
                                                    network_type='electricity')

    assert list_lhn == [[1001, 1003, 1004, 1002]]
    assert list_deg == []

    #  Add heating network edges
    city_object.add_edge(1001, heat_1, network_type='electricity')
    city_object.add_edge(heat_1, 1002, network_type='electricity')
    city_object.add_edge(1001, 1003, network_type='electricity')

    list_deg = \
        netop.get_list_with_energy_net_con_node_ids(city=city_object,
                                                    network_type='electricity')

    assert list_lhn == [[1001, 1003, 1004, 1002]]


if __name__ == '__main__':

    r_process_neighbours()