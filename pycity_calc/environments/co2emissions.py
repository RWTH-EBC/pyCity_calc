# coding=utf-8
"""
Script with emission class holding CO2 and primary energy (PE) factors
"""
from __future__ import division
import os
import numpy as np
import warnings


class Emissions(object):
    """
    Emissions class of pycity_calculator, holding CO2 and primary energy (PE)
    factors
    """

    def __init__(self, year=None, load_gemis_file=False, co2_factor_oil=0.31,
                 co2_factor_gas=0.241, co2_factor_liquid_gas=0.258,
                 co2_factor_hard_coal=0.419, co2_factor_soft_coal=0.417,
                 co2_factor_woodchip=0.012, co2_factors_wood=0.012,
                 co2_factor_pellets=0.012, co2_factor_el_mix=0.527,
                 co2_factor_pv_multi=0.062, co2_factor_el_feed_in=0.714,
                 co2_factor_pv_fed_in=0.651,
                 pe_oil=1.1, pe_gas=1.1, pe_liquid_gas=1.1, pe_hard_coal=1.2,
                 pe_soft_coal=1.2, pe_total_biogas=1.5, pe_non_ren_biogas=0.5,
                 pe_total_wood=1.2, pe_non_ren_wood=0.2, pe_total_el_mix=2.8,
                 pe_non_ren_el_mix=2.4, pe_total_feed_in_el=2.8,
                 pe_non_ren_feed_in_el=2.8, pe_total_env_energy=1,
                 pe_non_ren_env_energy=0, load_dyn_co2=True):
        """
        Constructor of emissions object in pycity_calc. Holds emission factors
        for Germany.

        If year is set, code tries to import emission values from input data
        file. If this is successful, default values/input values are
        overwritten. If data import fails, default values/input values are
        going to be used.

        Parameters
        ----------
        year : int, optional
            Year (default: None). If year is set to None, default CO2
            values are going to be used, respectively user inputs.
            Is year is defined and load_gemis_file is True,
            code tries to import co2 emission factors
            from input path 'data', 'BaseData', 'CO2', 'co2_gemis_factors.txt'
        load_gemis_file : bool, optional
            Defines, if gemis file should be loaded (defalt: False).
            If True, requires year to be set!
        co2_factor_oil : float, optional
            CO2 emission factor for oil in kg/kWh (ref: lower heating value)
            (default: 0.313).
            Based on [1]
        co2_factor_gas : float, optional
            CO2 emission factor for gas in kg/kWh (ref: lower heating value)
            (default: 0.241).
            Based on [1]
        co2_factor_liquid_gas : float, optional
            CO2 emission factor for liquid gas in kg/kWh
            (ref: lower heating value)
            (default: 0.261).
            Based on [1]
        co2_factor_hard_coal : float, optional
            CO2 emission factor for hard coal in kg/kWh
            (ref: lower heating value)
            (default: 0.427).
            Based on [1]
        co2_factor_soft_coal : float, optional
            CO2 emission factor for soft coal in kg/kWh
            (ref: lower heating value)
            (default: 0.449).
            Based on [1]
        co2_factor_woodchip : float, optional
            CO2 emission factor for woodchips in kg/kWh
            (ref: lower heating value)
            (default: 0.014).
            Based on [1]
        co2_factors_wood : float, optional
            CO2 emission factor for wood in kg/kWh (ref: lower heating value)
            (default: 0.011).
            Based on [1]
        co2_factor_pellets : float, optional
            CO2 emission factor for wood pellets in kg/kWh
            (ref: lower heating value)
            (default: 0.018).
            Based on [1]
        co2_factor_el_mix : float, optional
            CO2 emission factor for electricity mix in kg/kWh
            (default: 0.617).
            Based on [2]
        co2_factor_pv_multi : float, optional
            CO2 emission factor for PV (multi) in kg/kWh (default: 0.062)
            Based on [1]
        co2_factor_el_feed_in : float, optional
            CO2 factor feed in (Verdrängungsstrommix) in kg/kWh
            (default: 0.714).
            Based on [3]
        co2_factor_pv_fed_in : float, optional
            CO2 factor of PV feed in electricity in kg/kWh
            (default: 0.651).
            Based on [3]
        pe_oil : float, optional
            Primary energy factor for oil (default: 1.1)
        pe_gas : float, optional
            Primary energy factor for gas (default: 1.1)
        pe_liquid_gas : float, optional
            Primary energy factor for liquid gas (default: 1.1)
        pe_hard_coal : float, optional
            Primary energy factor for hard coal (default: 1.1)
        pe_soft_coal : float, optional
            Primary energy factor for soft coal (default: 1.2)
        pe_total_biogas : float, optional
            Primary energy factor (total) for biogas (default: 1.5)
        pe_non_ren_biogas : float, optional
            Primary energy factor (non-renewable) for biogas (default: 0.5)
        pe_total_wood : float, optional
            Primary energy factor (total) for wood (default: 1.2)
        pe_non_ren_wood : float, optional
            Primary energy factor (non_renewable) for wood (default: 0.2)
        pe_total_el_mix : float, optional
            Primary energy factor (total) for electricity mix (default: 2.8)
        pe_non_ren_el_mix : float, optional
            Primary energy factor (non-renewable) for electricity mix
            (default: 2.4)
        pe_total_feed_in_el : float, optional
            Primary energy factor (total) for feed in electricity
             (Verdraengungstrom)(default: 2.8)
        pe_non_ren_feed_in_el : float, optional
            Primary energy factor (non-ren) for feed in electricity
             (Verdraengungstrom)(default: 2.8)
        pe_total_env_energy : float, optional
            Primary energy factor (total) for environmental energy, such as
            solarenergy, geothermal energy or environmental heat
            (default: 1)
        pe_non_ren_env_energy : float, optional
            Primary energy factor (non-renewable) for environmental energy,
            such as solarenergy, geothermal energy or environmental heat
            (default: 0)
        load_dyn_co2 : bool, optional
            Defines, if dynamic CO2 signals should be loaded (default: True)

        References
        ----------
        [1] - Institut für Wohnen und Umwelt - IWU (2014):
        Kumulierter Energieverbrauch verschiedener Energieträger und
        Energieversorgungen. Online verfügbar unter
        http://www.iwu.de/fileadmin/user_upload/dateien/energie/werkzeuge/kea.pdf,
        zuletzt geprüft am 04.05.2018.
        [2] - Icha, Petra; Kuhs, Gunter (2017):
        Entwicklung der spezifischen Kohlendioxid-Emissionen des deutschen
        Strommix in den Jahren 1990 - 2016. Hg. v. Umweltbundesamt.
        Dessau-Roßlau. Online verfügbar unter
        https://www.umweltbundesamt.de/sites/default/files/medien/1410/publikationen/2017-05-22_climate-change_15-2017_strommix.pdf,
        zuletzt geprüft am 04.05.2018.
        [3] - Klobasa, Marian; Sensfuß, Frank (2016):
        CO2-Minderung im Stromsektor durch den Einsatz erneuerbarer Energien
        in den Jahren 2012 und 2013. Hg. v. Umweltbundesamt. Dessau-Roßlau.
        """

        self.year = year

        #  List with years, which have gemis co2 emission factors
        #  within input file
        gemis_year_list = [2010, 2014, 2017]

        #  Path were this file is executed
        script_dir = os.path.dirname(__file__)

        #  Get src path
        src_path = os.path.dirname(script_dir)

        #  CO2 factors
        if year is not None and load_gemis_file:
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
                    elif year == 2017:
                        use_column = 3

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
        self.co2_factor_pv_fed_in = co2_factor_pv_fed_in
        self.pe_oil = pe_oil
        self.pe_gas = pe_gas
        self.pe_liquid_gas = pe_liquid_gas
        self.pe_hard_coal = pe_hard_coal
        self.pe_soft_coal = pe_soft_coal
        self.pe_total_biogas = pe_total_biogas
        self.pe_non_ren_biogas = pe_non_ren_biogas
        self.pe_total_wood = pe_total_wood
        self.pe_non_ren_wood = pe_non_ren_wood
        self.pe_total_el_mix = pe_total_el_mix
        self.pe_non_ren_el_mix = pe_non_ren_el_mix
        self.pe_total_feed_in_el = pe_total_feed_in_el
        self.pe_non_ren_feed_in_el = pe_non_ren_feed_in_el
        self.pe_total_env_energy = pe_total_env_energy
        self.pe_non_ren_env_energy = pe_non_ren_env_energy

        #  Arrays with dynamic CO2 signals for electricity mix in Germany
        #  for different shares of renewables (60%, 80%, 100%)
        self.array_co2_el_mix_60_ren = None
        self.array_co2_el_mix_80_ren = None
        self.array_co2_el_mix_100_ren = None

        #  Arrays with dynamic CO2 signals for conventional electricity
        #  in Germany for different shares of renewables (60%, 80%, 100%)
        self.array_co2_el_sup_60_ren = None
        self.array_co2_el_sup_80_ren = None
        self.array_co2_el_sup_100_ren = None

        if load_dyn_co2:
            #  Load dynamic CO2 signals
            self.load_dyn_co2_signals()

    def load_dyn_co2_signals(self, path_mix=None, path_sup=None):
        """
        Load dynamic co2 signals from given pathes. If path is None, uses
        default path.

        Parameters
        ----------
        path_mix : str, optional
            Path to dynamic CO2 signals for electricity
            mix (default: None). If None, uses data set within
            ..\pyCity_calc\pycity_calc\data\El_grid\CO2factors_mix.txt
        path_sup : str, optional
            Path to dynamic CO2 signals for conventional electricity supply
            (default: None). If None, uses data set within
            ..\pyCity_calc\pycity_calc\data\El_grid\CO2factors_supp.txt
        """

        path_this = os.path.dirname(os.path.abspath(__file__))
        path_src = os.path.dirname(path_this)
        path_data_folder = os.path.join(path_src, 'data', 'El_grid')

        if path_mix is None:
            name_mix = 'CO2factors_mix.txt'
            path_mix = os.path.join(path_data_folder, name_mix)

        if path_sup is None:
            name_sup = 'CO2factors_supp.txt'
            path_sup = os.path.join(path_data_folder, name_sup)

        matrix_co2_mix = np.loadtxt(path_mix, usecols=(0, 1, 2))
        matrix_co2_sup = np.loadtxt(path_sup, usecols=(0, 1, 2))

        #  Arrays with dynamic CO2 signals for electricity mix in Germany
        #  for different shares of renewables (60%, 80%, 100%)
        self.array_co2_el_mix_60_ren = matrix_co2_mix[:, 0]
        self.array_co2_el_mix_80_ren = matrix_co2_mix[:, 1]
        self.array_co2_el_mix_100_ren = matrix_co2_mix[:, 2]

        #  Arrays with dynamic CO2 signals for conventional electricity
        #  in Germany for different shares of renewables (60%, 80%, 100%)
        self.array_co2_el_sup_60_ren = matrix_co2_sup[:, 0]
        self.array_co2_el_sup_80_ren = matrix_co2_sup[:, 1]
        self.array_co2_el_sup_100_ren = matrix_co2_sup[:, 2]

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

    def get_primary_energy_factor(self, non_ren, type):
        """
        Returns primary energy factor depending on chosen type and kind
        of primary energy factor (total or non-renewable)

        Parameters
        ----------
        non_ren : bool
            Defines, if non-renewable part should be returned
            Options:
            - True : Returns non-renewable part of PE
            - False : Returns total PE
        type : str
            Type of energy / combustible.
            Options:
            - 'oil'
            - 'gas'
            - 'liquid_gas'
            - 'hard_coal'
            - 'soft_coal'
            - 'biogas'
            - 'wood'
            - 'el_mix' (Electricity mix)
            - 'el_feed_in' (Feed in electricity / Verdraengungsstrom)
            - 'env_en' (environmental energy, such as solar energy, waste heat)

        Returns
        -------
        pe_factor : float
            Primary energy factor
        """
        if non_ren:
            #  Return non-renewable part of PE
            pe_dict = {'oil': self.pe_oil,
                       'gas': self.pe_gas,
                       'liquid_gas': self.pe_liquid_gas,
                       'hard_coal': self.pe_hard_coal,
                       'soft_coal': self.pe_soft_coal,
                       'biogas': self.pe_non_ren_biogas,
                       'wood': self.pe_non_ren_wood,
                       'el_mix': self.pe_non_ren_el_mix,
                       'el_feed_in': self.pe_non_ren_feed_in_el,
                       'env_en': self.pe_non_ren_env_energy}

        else:
            #  Return total PE factors
            pe_dict = {'oil': self.pe_oil,
                       'gas': self.pe_gas,
                       'liquid_gas': self.pe_liquid_gas,
                       'hard_coal': self.pe_hard_coal,
                       'soft_coal': self.pe_soft_coal,
                       'biogas': self.pe_total_biogas,
                       'wood': self.pe_total_wood,
                       'el_mix': self.pe_total_el_mix,
                       'el_feed_in': self.pe_total_feed_in_el,
                       'env_en': self.pe_total_env_energy}

        return pe_dict[type]


if __name__ == '__main__':
    emission = Emissions(load_dyn_co2=True)

    #  Get CO2 factor for natural gas
    co2_gas = emission.get_co2_emission_factors(type='gas')

    print('CO2 factor for natural gas in kg/kWh: ')
    print(co2_gas)

    #  Get primary energy factor for electricity mix (total)
    pe_total_el_mix = emission.get_primary_energy_factor(non_ren=False,
                                                         type='el_mix')

    print('Total primary energy factor of electricity mix: ')
    print(pe_total_el_mix)
