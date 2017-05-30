#!/usr/bin/env python
# coding=utf-8
"""

"""

import shapely.geometry.point as point

import pycity.classes.Timer as time
import pycity.classes.Weather as weath
import pycity.classes.Prices as price
import pycity.classes.Environment as env
import pycity.classes.demand.SpaceHeating as SpaceHeating
import pycity.classes.demand.ElectricalDemand as ElectricalDemand
import pycity.classes.demand.Apartment as Apartment

import pycity_calc.buildings.building as build_ex
import pycity_calc.toolbox.clustering.clustering as clust
import pycity_calc.cities.city as cit


def get_street_subgraph():

    cluster = clust.StreetCluster()
    #  Fixme: Broken reference at StreetCluster() (Missing inputs)

    #  Create environment
    timer = time.Timer()
    weather = weath.Weather(timer)
    prices = price.Prices()
    environment = env.Environment(timer, weather, prices)

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
                                                 mod_year=2003, build_type=0)

    #  Init street graph
    city = cit.City(environment=environment)

    cluster = clust.StreetCluster()

    #  Add str nodes
    node_1 = city.add_street_node(position=point.Point(0, 0))
    node_2 = city.add_street_node(position=point.Point(0, 5))
    node_3 = city.add_street_node(position=point.Point(0, 10))

     #  Add edges
    city.add_edge(node_1, node_2, networktype='street')
    city.add_edge(node_2, node_3, networktype='street')

     #  Add building entities
    city.addEntity(entity=extended_building, position=point.Point(-1, 0))
    city.addEntity(entity=extended_building, position=point.Point(1, 1))
    city.addEntity(entity=extended_building, position=point.Point(1, 2))

    cluster.city = city

    cluster.street  = cluster.get_street_subgraph()

    str_node_dict, str_edge_dict = cluster.gen_str_dicts()

    print(str_node_dict)
    print(str_edge_dict)


if __name__ == '__main__':
    get_street_subgraph()