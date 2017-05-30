# coding=utf-8
"""
Example script for emissions class
"""

import pycity_calc.environments.co2emissions as co2


def run_example():

    year = 2010

    #  Generate emission object
    emission = co2.Emissions(year=year)

    print('CO2 emission factor for electricity in kg/kWh for ' + str(year))
    print(emission.get_co2_emission_factors(type='el_mix'))

    print('CO2 emission factor for gas in kg/kWh for ' + str(year))
    print(emission.get_co2_emission_factors(type='gas'))

if __name__ == '__main__':
    run_example()
