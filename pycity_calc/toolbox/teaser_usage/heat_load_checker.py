#!/usr/bin/env python
# coding=utf-8
"""

"""
from __future__ import division

from teaser.project import Project


def main():
    project = Project(load_data=True)

    type_bldg = \
        project.add_residential(
            method='iwu',
            usage='single_family_dwelling',
            name='test_building',
            year_of_construction=1960,
            number_of_floors=2,
            height_of_floors=3,
            net_leased_area=600,
            with_ahu=False,
            residential_layout=0,
            neighbour_buildings=0,
            attic=1,
            cellar=1,
            dormer=0,
            construction_type='heavy')

    heat_load_before_retro = type_bldg.sum_heat_load
    print('Before: ', heat_load_before_retro)

    project.retrofit_all_buildings(year_of_retrofit=1985)

    heat_load_after_retro = type_bldg.sum_heat_load
    print('After: ', heat_load_after_retro)


if __name__ == '__main__':
    main()
