# coding=utf-8
"""
Script to extend pycity prices object
"""
from __future__ import division
import os
import numpy as np
import warnings

import pycity.classes.Prices as Price


class Market(Price.Prices):
    """
    Market class of pycity_calculator. Extends prices object of pycity.
    Holds specific price data for gas and electricity for different reference
    years and residential as well as non-residential buildings
    """

    def __init__(self, reset_pycity_default_values=True):
        """
        Constructor of Market object of pycity_calculator.
        Extends prices object of pycity.

        When object is initialized, price data is automatically imported from
        ...\pycity_calc\data\Economic\Energy_Prices\

        Parameters
        ----------
        reset_pycity_default_values : bool, optional
            Boolean to define, if pycity default values should be set to None.
            (default: True)
            True - Set all default values to None
            False - Keep pycity default market values
        """

        super(Market, self).__init__()

        if reset_pycity_default_values:
            #  Set all pycity default values to None
            self.revChp = None
            self.costsEl = None
            self.revEl = None
            self.costsGas = None

        # Load price data for Germany
        el_price_data_res, el_price_data_ind, gas_price_data_res, \
        gas_price_data_ind = self.load_pricing_data()

        #  Further attributes
        #  #-----------------------------------------------------------------

        #  Prices per demand
        #  1. Residential (el)
        self.el_price_data_res = el_price_data_res

        #  2. Non-residential (el)
        self.el_price_data_ind = el_price_data_ind

        #  3. Residential (gas)
        self.gas_price_data_res = gas_price_data_res

        #  4. Non-residential (gas)
        self.gas_price_data_ind = gas_price_data_ind

    def load_pricing_data(self):
        """
        Method returns np.arrays with pricing data for gas and electricity
        for residential and non-residential buildings in Germany.
        Prices are related to annual demand and reference year.

        The output format is:
        1. column: Demand in kWh from
        2. column: Demand in kWh to
        3. column: 2010 price data in Euro/kWh
        4. column: 2011 price data in Euro/kWh
        ...
        9. column: 2016 price data in Euro/kWh

        Returns
        -------
        el_price_data_res : np.array
            Electric price data for residential buildings in Euro/kWh
        el_price_data_ind : np.array
            Electric price data for industrial buildings in Euro/kWh
        gas_price_data_res : np.array
            Gas price data for residential buildings in Euro/kWh
        gas_price_data_ind : np.array
            Gas price data for industrial buildings in Euro/kWh

        Reference
        ---------
        [1] Eurostat energy database
        http://ec.europa.eu/eurostat/web/energy/data/database
        """

        el_price_data_res = None
        el_price_data_ind = None
        gas_price_data_res = None
        gas_price_data_ind = None

        file_path = os.path.abspath(__file__)
        src_path = os.path.dirname(os.path.dirname(file_path))
        data_path = os.path.join(src_path, 'data', 'Economic', 'Energy_Prices')

        #  Electricity prices (residential)
        #  #------------------------------------------------------------------
        el_res_filename = 'el_prices_germany.txt'
        el_res_filepath = os.path.join(data_path, 'Electricity', 'Private',
                                       el_res_filename)
        try:
            el_price_data_res = np.genfromtxt(el_res_filepath, delimiter='\t',
                                              skip_header=2)
        except:
            warnings.warn('Could not load res. el. price data. ' +
                          'Going to return None.')

        # Electricity prices (industrial)
        #  #------------------------------------------------------------------
        el_ind_filename = 'el_prices_germany.txt'
        el_ind_filepath = os.path.join(data_path, 'Electricity', 'Industry',
                                       el_ind_filename)
        try:
            el_price_data_ind = np.genfromtxt(el_ind_filepath, delimiter='\t',
                                              skip_header=2)
        except:
            warnings.warn('Could not load res. el. price data. ' +
                          'Going to return None.')

        # Gas prices (residential)
        #  #------------------------------------------------------------------
        gas_res_filename = 'gas_prices_germany.txt'
        gas_res_filepath = os.path.join(data_path, 'Gas', 'Private',
                                        gas_res_filename)
        try:
            gas_price_data_res = np.genfromtxt(gas_res_filepath,
                                               delimiter='\t', skip_header=2)
        except:
            warnings.warn('Could not load res. el. price data. ' +
                          'Going to return None.')

        # Gas prices (industrial)
        #  #------------------------------------------------------------------
        gas_ind_filename = 'gas_prices_germany.txt'
        gas_ind_filepath = os.path.join(data_path, 'Gas', 'Industry',
                                        gas_ind_filename)
        try:
            gas_price_data_ind = np.genfromtxt(gas_ind_filepath,
                                               delimiter='\t', skip_header=2)
        except:
            warnings.warn('Could not load res. el. price data. ' +
                          'Going to return None.')

        return el_price_data_res, el_price_data_ind, gas_price_data_res, \
               gas_price_data_ind

    def get_spec_gas_cost(self, type, year, annual_demand):
        """
        Returns specific gas cost in Euro/kWh, depending on building type,
        reference year and annual gas demand in kWh.

        Parameters
        ----------
        type : str
            Building type. Options:
            - 'res' - Residential
            - 'ind' - Industrial / Non-residential
        year : int
            Reference year. Options:
            (2010, 2011, 2012, 2013, 2014, 2015, 2016)
        annual_demand : float
            Annual gas energy demand in kWh/a

        Returns
        -------
        spec_cost_gas : float
            Specific cost of gas in Euro/kWh
        """
        list_of_years = [2010, 2011, 2012, 2013, 2014, 2015, 2016]
        assert year in list_of_years, 'Year must be in list_of_years!'

        #  Find column index according to year
        year_index = list_of_years.index(year)  # Find year index in list
        column = year_index + 2  # Skip two columns with demand data

        if type == 'res' or type == 'ind':
            if type == 'res':  # Residential
                gas_price_data = self.gas_price_data_res
            elif type == 'ind':  # Industrial
                gas_price_data = self.gas_price_data_ind
            # Find row index according to demand
            max_demand_column = gas_price_data[:, [1]]
            for i in range(len(max_demand_column)):
                #  If annual_demand is smaller than max demand value in data
                if annual_demand < max_demand_column[i]:
                    row = i  # Return row index
                    break
                else:  # index of last row
                    row = len(max_demand_column) - 1

            spec_cost_gas = gas_price_data[row][column]
        else:
            raise ValueError('Chosen type for method get_spec_gas_cost is ' +
                             'unknown. Select "res" or "ind".')

        return spec_cost_gas

    def get_spec_el_cost(self, type, year, annual_demand):
        """
        Returns specific electricity cost in Euro/kWh, depending on building
        type, reference year and annual electricity demand in kWh.

        Parameters
        ----------
        type : str
            Building type. Options:
            - 'res' - Residential
            - 'ind' - Industrial / Non-residential
        year : int
            Reference year. Options:
            (2010, 2011, 2012, 2013, 2014, 2015, 2016)
        annual_demand : float
            Annual electricity energy demand in kWh/a

        Returns
        -------
        spec_cost_el : float
            Specific cost of gas in Euro/kWh
        """
        list_of_years = [2010, 2011, 2012, 2013, 2014, 2015, 2016]
        assert year in list_of_years, 'Year must be in list_of_years!'

        #  Find column index according to year
        year_index = list_of_years.index(year)  # Find year index in list
        column = year_index + 2  # Skip two columns with demand data

        if type == 'res' or type == 'ind':
            if type == 'res':  # Residential
                el_price_data = self.el_price_data_res
            elif type == 'ind':  # Industrial
                el_price_data = self.el_price_data_ind
            # Find row index according to demand
            max_demand_column = el_price_data[:, [1]]
            for i in range(len(max_demand_column)):
                #  If annual_demand is smaller than max demand value in data
                if annual_demand < max_demand_column[i]:
                    row = i  # Return row index
                    break
                else:  # index of last row
                    row = len(max_demand_column) - 1

            spec_cost_gas = el_price_data[row][column]
        else:
            raise ValueError('Chosen type for method get_spec_el_cost is ' +
                             'unknown. Select "res" or "ind".')

        return spec_cost_gas


if __name__ == '__main__':
    market = Market()

    print('Gas price data residential buildings for 2010 (by demands):')
    print(market.gas_price_data_res[:, [2]])

    spec_cost_gas = market.get_spec_gas_cost(type='res', year=2015,
                                             annual_demand=15000)
    print('Specific cost of gas for chosen type, year and demand in Euro/kWh:')
    print(spec_cost_gas)

    spec_cost_el = market.get_spec_el_cost(type='ind', year=2012,
                                           annual_demand=600 * 1000)
    print('Specific cost of electricity for chosen type, year and demand in ' +
          'Euro/kWh:')
    print(spec_cost_el)
