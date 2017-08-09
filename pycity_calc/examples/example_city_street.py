# coding=utf-8
"""
Example script for usage of city class with street network
"""
from __future__ import division
import shapely.geometry.point as point

import pycity_base.classes.Weather as Weather
import pycity_base.classes.demand.SpaceHeating as SpaceHeating
import pycity_base.classes.demand.ElectricalDemand as ElectricalDemand
import pycity_base.classes.demand.Apartment as Apartment

import pycity_calc.buildings.building as build_ex
import pycity_calc.cities.city as cit
import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.environment as env
import pycity_calc.environments.market as mark
import pycity_calc.environments.timer as time
import pycity_calc.toolbox.networks.network_ops as netop


def run_example():
    """
    Run example to create city object of pycity with 3 buildings and
    street network
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
    city_object = cit.City(environment=environment)

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

        position = point.Point(i*10, 0)

        #  Add 3 extended buildings to city object
        city_object.add_extended_building(extended_building=extended_building,
                                          position=position)

    #  Add street network
    #  Add str nodes
    node_1 = city_object.add_street_node(position=point.Point(0, -1))
    node_2 = city_object.add_street_node(position=point.Point(10, -1))
    node_3 = city_object.add_street_node(position=point.Point(20, -1))

    #  Add edges
    city_object.add_edge(node_1, node_2, network_type='street')
    city_object.add_edge(node_2, node_3, network_type='street')

    street = netop.get_street_subgraph(city_object)

    assert street.nodes() == [node_1, node_2, node_3]
    assert street.edges() == [(node_1, node_2), (node_2, node_3)]

    print('Street nodes ', street.nodes())
    print('Street edges ', street.edges())
    print('Street nodes with data ', street.nodes(data=True))

    subcity = netop.get_build_str_subgraph(city=city_object, nodelist=[1001])

    print('Subcity nodes ', subcity.nodes())
    print('Subcity nodes with data: ', subcity.nodes(data=True))
    print('Subcity edges ', subcity.edges())

    assert subcity.nodes() == [1001, node_1, node_2, node_3]
    assert subcity.edges() == [(node_1, node_2), (node_2, node_3)]

    print('Nodelist street:')
    print(subcity.nodelist_street)
    print('Nodelist buildings:')
    print(subcity.nodelist_building)

if __name__ == '__main__':
    #  Execute example
    run_example()
