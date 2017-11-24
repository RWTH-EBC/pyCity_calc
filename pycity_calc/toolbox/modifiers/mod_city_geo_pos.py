#!/usr/bin/env python
# coding=utf-8
"""
Holding functions to manipulate city object
"""

# import sympy.geometry.point as point
import shapely.geometry.point as point

import pycity_calc.cities.scripts.city_generator.city_generator as citgen

import pycity_base.classes.demand.SpaceHeating as SpaceHeating
import pycity_base.classes.demand.ElectricalDemand as ElectricalDemand
import pycity_base.classes.demand.Apartment as Apartment
import pycity_calc.buildings.building as build_ex
import pycity_calc.cities.city as cit

import pycity_calc.visualization.city_visual as citvis


def gen_test_city(timestep=3600, year=2017, try_path=None,
                  location=(51.529086, 6.944689), altitude=55):
    """
    Generate test city district

    Parameters
    ----------
    timestep : int
        Timestep in seconds
    year : int, optional
        Chosen year of analysis (default: 2010)
        (influences initial day for profile generation, market prices
        and co2 factors)
        If year is set to None, user has to define day_init!
    try_path : str, optional
        Path to TRY weather file (default: None)
        If set to None, uses default weather TRY file (2010, region 5)
    location : Tuple, optional
        (latitude , longitude) of the simulated system's position,
        (default: (51.529086, 6.944689) for Bottrop, Germany.
    altitude : float, optional
        Altitute of location in m (default: 55 - City of Bottrop)

    Returns
    -------
    city : object
        City object of pycity_calc
    """

    #  Generate environment
    environment = citgen.generate_environment(timestep=timestep,
                                              year_timer=year,
                                              year_co2=year,
                                              try_path=try_path,
                                              location=location,
                                              altitude=altitude)

    #  Generate city object
    city = cit.City(environment=environment)

    list_x_coord = [15, 25, 40]
    list_y_coord = [25, 10, 45]

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
                                                      build_year=1970,
                                                      mod_year=2003,
                                                      build_type=0)

        #  Add apartment to extended building
        extended_building.addEntity(entity=apartment)

        position = point.Point(list_x_coord[i], list_y_coord[i])

        #  Add 3 extended buildings to city object
        city.add_extended_building(extended_building=extended_building,
                                   position=position)

    # Add street network
    #  Add str nodes
    node_1 = city.add_street_node(position=point.Point(10, 20))
    node_2 = city.add_street_node(position=point.Point(30, 20))
    node_3 = city.add_street_node(position=point.Point(50, 20))

    #  Add edges
    city.add_edge(node_1, node_2, network_type='street')
    city.add_edge(node_2, node_3, network_type='street')

    return city


def get_min_x_y_coord(city):
    """
    Returns min x- and y-coordinates as tuple, found within city object.

    Requires position parameter (shapely point) on every node!

    Parameters
    ----------
    city : object
        City object of pycity_calc

    Returns
    -------
    tuple_min : tuple (of floats)
        Tuple holding minimal x-/y-coordinates (x_min, y_min)
    """

    x_min = None
    y_min = None

    #  Find min x and y coordinate
    for n in city.nodes():
        x_curr = city.nodes[n]['position'].x
        y_curr = city.nodes[n]['position'].y

        if x_min is None or x_min > x_curr:
            x_min = x_curr

        if y_min is None or y_min > y_curr:
            y_min = y_curr

    tuple_min = (x_min, y_min)

    return tuple_min

def set_zero_coordinate(city, buffer=10):
    """
    Function manipulates position attributes of all nodes within city.
    Finds zero point with info of smallest x- and y-coordinates (plus buffer)

    Requires, that all nodes in city hold attribute 'position'!

    Parameters
    ----------
    city : object
        City object of pycity
    buffer : float, optional
        Buffer that should be used between found min x- and y-coordinates
        and newly defined zero point (default: 10).
        E.g. if buffer == 0, zero point is defined with (x_min/y_min)
    """

    for n in city.nodes():
        if 'position' not in city.nodes[n]:
            msg = str('Error: No position attribute on node ' + str(n))
            raise AssertionError(msg)

    x_min = None
    y_min = None

    #  Find min x and y coordinate
    (x_min, y_min) = get_min_x_y_coord(city)

    if buffer != 0:
        x_min -= buffer
        y_min -= buffer

    # Convert every point position
    for n in city.nodes():
        x_new = city.nodes[n]['position'].x - x_min
        y_new = city.nodes[n]['position'].y - y_min

        #  Generate new point
        point_new = point.Point(x_new, y_new)

        #  Overwrite point
        city.nodes[n]['position'] = point_new


if __name__ == '__main__':

    buffer = 5

    #  Generate test city object
    city = gen_test_city()

    #  Plot city
    citvis.plot_city_district(city, plt_title='Before zero point conversion')

    #  Convert points
    set_zero_coordinate(city, buffer=buffer)

    #  Plot city
    citvis.plot_city_district(city, plt_title='After zero point conversion')
