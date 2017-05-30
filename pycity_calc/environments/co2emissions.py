# coding=utf-8
"""
Script with CO2 emission class
"""

import os
import numpy as np
import warnings


class Emissions(object):
    """
    Emissions class of pycity_calculator
    """

    def __init__(self, year=None, co2_factor_oil=0.313,
                 co2_factor_gas=0.241, co2_factor_liquid_gas=0.261,
                 co2_factor_hard_coal=0.427, co2_factor_soft_coal=0.449,
                 co2_factor_woodchip=0.014, co2_factors_wood=0.011,
                 co2_factor_pellets=0.018, co2_factor_el_mix=0.617,
                 co2_factor_pv_multi=0.062, co2_factor_el_feed_in=0.84):
        """
        Constructor of emissions object in pycity_calc. Holds emission factors
        for Germany, currently for the years:
        - 2010
        - 2014 (default)
        (based on IWU GEMIS calculations)

        If year is set, code tries to import emission values from input data
        file. If this is successful, default values/input values are
        overwritten. If data import fails, default values/input values are
        going to be used.

        Parameters
        ----------
        year : int, optional
            Year (default: None). If year is set to None, default CO2
            values are going to be used, respectively user inputs.
            Is year is defined, code tries to import co2 emission factors
            from input path 'data', 'BaseData', 'CO2', 'co2_gemis_factors.txt'
        co2_factor_oil : float, optional
            CO2 emission factor for oil in kg/kWh (ref: lower heating value)
            (default: 0.313).
        co2_factor_gas : float, optional
            CO2 emission factor for gas in kg/kWh (ref: lower heating value)
            (default: 0.241).
        co2_factor_liquid_gas : float, optional
            CO2 emission factor for liquid gas in kg/kWh
            (ref: lower heating value)
            (default: 0.261).
        co2_factor_hard_coal : float, optional
            CO2 emission factor for hard coal in kg/kWh
            (ref: lower heating value)
            (default: 0.427).
        co2_factor_soft_coal : float, optional
            CO2 emission factor for soft coal in kg/kWh
            (ref: lower heating value)
            (default: 0.449).
        co2_factor_woodchip : float, optional
            CO2 emission factor for woodchips in kg/kWh
            (ref: lower heating value)
            (default: 0.014).
        co2_factors_wood : float, optional
            CO2 emission factor for wood in kg/kWh (ref: lower heating value)
            (default: 0.011).
        co2_factor_pellets : float, optional
            CO2 emission factor for wood pellets in kg/kWh
            (ref: lower heating value)
            (default: 0.018).
        co2_factor_el_mix : float, optional
            CO2 emission factor for electricity mix in kg/kWh
            (default: 0.617).
        co2_factor_pv_multi : float, optional
            CO2 emission factor for PV (multi) in kg/kWh (default: 0.062)
        co2_factor_el_feed_in : float, optional
            CO2 factor feed in (Verdrängungsstrommix) in kg/kWh
            (default: 0.84); see [3]

        References
        ----------
        [1] Institut für Wohnen und Umwelt - IWU, Kumulierter Energieaufwand
        verschiedener Energieträgern und –versorgungen (2009).
        [2] Internationales Institut für Nachhaltigkeitsanalysen und
        -strategien, GEMIS - Globales Emissions-Modell integrierter Systeme,
         available at http://www.iinas.org/gemis-de.html (
         accessed on January 13, 2015).
        [3] IFEU:
        https://www.ifeu.de/energie/pdf/ifeu_Endbericht_Weiterentwicklung_PEF.pdf
        """

        #  List with years, which have gemis co2 emission factors
        #  within input file
        gemis_year_list = [2010, 2014]

        #  Path were this file is executed
        script_dir = os.path.dirname(__file__)

        #  Get src path
        src_path = os.path.dirname(script_dir)

        #  CO2 factors
        if year is not None:
            try:
                input_data_path = os.path.join(src_path, 'data', 'BaseData',
                                               'CO2', 'co2_gemis_factors.txt')
                co2_dataset = np.genfromtxt(input_data_path, delimiter='\t',
                                            skip_header=1)
                if year in gemis_year_list:
                    if year == 2014:
                        use_column = 2
                    elif year == 2010:  # Use default value for 2010
                        use_column = 1
                    else:
                        raise ValueError('Chosen year is not in GEMIS data.')
                    # CO2 factors in kg / kWh final energy (related to lower
                    #  heating value - Unterer Heizwert)
                    co2_factor_oil = co2_dataset[0][use_column] / 1000
                    co2_factor_gas = co2_dataset[1][use_column] / 1000
                    co2_factor_liquid_gas = co2_dataset[2][use_column] / 1000
                    co2_factor_hard_coal = co2_dataset[3][use_column] / 1000
                    co2_factor_soft_coal = co2_dataset[4][use_column] / 1000
                    co2_factor_woodchip = co2_dataset[5][use_column] / 1000
                    co2_factors_wood = co2_dataset[6][use_column] / 1000
                    co2_factor_pellets = co2_dataset[7][use_column] / 1000
                    co2_factor_el_mix = co2_dataset[8][use_column] / 1000
                    co2_factor_pv_multi = co2_dataset[9][use_column] / 1000
                    co2_factor_el_feed_in = co2_dataset[10][use_column] / 1000
                else:
                    warnings.warn('Chosen year ' + str(year) + 'does not ' +
                                  'exist in data file. Instead, default/' +
                                  'user CO2 factors are used.')
            except:
                warnings.warn('Cannot find CO2 data file: ' + input_data_path +
                              '. Instead, using default/input CO2 factors.')

        # Set attribute values
        self.co2_factor_oil = co2_factor_oil
        self.co2_factor_gas = co2_factor_gas
        self.co2_factor_liquid_gas = co2_factor_liquid_gas
        self.co2_factor_hard_coal = co2_factor_hard_coal
        self.co2_factor_soft_coal = co2_factor_soft_coal
        self.co2_factor_woodchip = co2_factor_woodchip
        self.co2_factors_wood = co2_factors_wood
        self.co2_factor_pellets = co2_factor_pellets
        self.co2_factor_el_mix = co2_factor_el_mix
        self.co2_factor_pv_multi = co2_factor_pv_multi
        self.co2_factor_el_feed_in = co2_factor_el_feed_in

    def get_co2_emission_factors(self, type):
        """
        Returns CO2 emission factor in kg/kWh, depending on chosen type
        (combustible, electricity).

        Parameters
        ----------
        type : str
            Type of CO2 emission.
            Options:
            - 'oil'
            - 'gas'
            - 'liquid_gas'
            - 'hard_coal'
            - 'soft_coal'
            - 'woodchip'
            - 'wood'
            - 'pellets'
            - 'el_mix' (Electricity mix)

        Returns
        -------
        co2_factor : float
            CO2 emission factor in kg/kWh
        """
        co2_dict = {'oil': self.co2_factor_oil,
                    'gas': self.co2_factor_gas,
                    'liquid_gas': self.co2_factor_liquid_gas,
                    'hard_coal': self.co2_factor_hard_coal,
                    'soft_coal': self.co2_factor_soft_coal,
                    'woodchip': self.co2_factor_woodchip,
                    'wood': self.co2_factor_woodchip,
                    'pellets': self.co2_factor_pellets,
                    'el_mix': self.co2_factor_el_mix,
                    'pv_multi': self.co2_factor_pv_multi,
                    'el_feed_in': self.co2_factor_el_feed_in}

        co2_factor = co2_dict[type]
        return co2_factor
