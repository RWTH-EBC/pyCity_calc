# coding=utf-8
"""
This script gives a brief example of how to include the TEASER package in
pyCity you can see how to usw teaser to create a typeBuilding from either
an ExtendedBuilding or City Object from pyCity
You can either use a pickled files for testing or create an object from
example_city.py or example_building.py respectively
"""
from __future__ import division
import pycity_calc.examples.example_building as ex_building
import pycity_calc.examples.example_city as ex_city
import pycity_calc.toolbox.teaser_usage.teaser_use as teaser_usage


def run_example_exbuild():
    """
    create a typeBuilding from a pyCity Extended Building
    """

    #  Generate example building
    BuildingExtended = ex_building.run_example()

    #  Create the teaser project
    project = teaser_usage.create_teaser_project(name='example_building')

    #  Create the typeBuilding
    teaser_usage.create_teaser_typebld(project, BuildingExtended,
                                 generate_Output=False, name='building_1')


def run_example_city():
    """
    Create TypeBuildings form a pycity City Object

    Returns
    -------
    city_object : Pycity city object
        return the edited city object
    """

    city_object = ex_city.run_example()

    # create the teaser project
    project = teaser_usage.create_teaser_project(name='example_city')

    # create the typeBuilding
    teaser_usage.create_teaser_typecity(project, city_object,
                                  generate_Output=False)

    return city_object


if __name__ == '__main__':
    # Execute Example extended Building
    run_example_exbuild()

    #  Execute Example City and return the edited pyCity Object
    run_example_city()
