# coding=utf-8
"""
Example script for Market class
"""

import pycity_calc.environments.market as mark


def run_example():

    market = mark.Market()

    year = 2010

    res_demand = 15000
    ind_demand = 600000

    spec_cost_gas = market.get_spec_gas_cost(type='res', year=year,
                                             annual_demand=res_demand)
    print('Specific cost of gas for residential building with demand ' +
          str(res_demand) + ' kWh for year ' + str(year) + ' in Euro/kWh:')
    print(spec_cost_gas)

    spec_cost_el = market.get_spec_el_cost(type='ind', year=year,
                                           annual_demand=ind_demand)
    print('Specific cost of electricity for industrial building with demand ' +
          str(ind_demand) + ' kWh for year ' + str(year) + ' in Euro/kWh:')
    print(spec_cost_el)


if __name__ == '__main__':
    run_example()
