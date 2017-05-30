"""
Script to extend pycity market object
"""

import os
import numpy as np
import warnings

import pycity.classes.Market as Market


class Germanmarket(Market.Market):
    """
    Germanmarket class of pycity_calculator. Extends market object of pycity.
    Contains different taxes and subsidy payments from German law for CHP and
    PV usage

    Attributes:
    -----------
    EEG_Umlage_tax
        #  TODO
    EEX_baseload_price
        #  TODO
    avoid_grid_usage: 'float', payment for avoided grid usage for sold chp electricity according to KWKG2016.
        in €/kWh
    sub_chp: 'list', subsidiy payments for sold chp electricity according to KWKG2016.
        sub_chp[0] - pNom < 50kW in €/kWh
        sub_chp[1] - 50kW < pNom < 100kW  in €/kWh
    self_demand_usage_chp: 'list', subsidiy payments for self used chp electricity according to KWKG2016.
        sub_chp[0] - pNom < 50kW  in €/kWh
        sub_chp[1] - 50kW < pNom < 100kW  in €/kWh
    gas_disc_chp: 'float', discount on used gas with highly efficient Energysystems according to german Energy tax law.
    sub_pv: 'list', subsidiy payments for sold pv electricity according to EEG2017.
        sub_pv[0] - kWpeak < 10kW  in €/kWh
        sub_pv[1] - 10kW < kWpeak < 40kW  in €/kWh
        sub_pv[2] - 40kW < kWpeak < 100kW  in €/kWh
    """

    def __init__(self, reset_pycity_default_values=True):
        """
        Constructor of germanmarket object instance

        Parameters
        ----------
        reset_pycity_default_values : bool, optional
            #  TODO
        """

        super(Germanmarket, self).__init__(reset_pycity_default_values=
                                           reset_pycity_default_values)

        #TODO: get the values from somewere
        self.EEG_Umlage_tax=[0.05,0.04]
        self.EEX_baseload_price=1
        self.avoid_grid_usage=0.07
        self.sub_chp=[0.08,0.06,0.05,0.044,0.031]
        self.self_demand_usage_chp=[0.04,0.03,0]
        self.gas_disc_chp=0.0055
        self.sub_pv=[0.123,0.1196,0.1069]

    def get_EEG_Umlage_tax(self, year):
        return self.EEG_Umlage_tax
    def get_EEX_baseload_price(self, year):
        return self.EEX_baseload_price
    def get_avoid_grid_usage(self, year):
        return self.avoid_grid_usage

    def get_sub_chp(self, year, pNom):
        '''
        return the subsidy payment for sold chp electritiy

        -----------
        Parameters:
        year: 'int', reference year
        pNom: 'float', nominal electrical CHP power
        --------
        Returns:
        sub_chp: 'float', subsidiy payments for sold chp electricity according to KWKG2016.
        '''

        if pNom <= 50000:
            sub_chp = self.sub_chp[0]
        elif pNom > 50000 and pNom <= 100000:
            sub_chp = self.sub_chp[1]
        elif pNom > 100000 and pNom <= 250000:
            sub_chp = self.sub_chp[2]
        elif pNom > 250000 and pNom <= 2000000:
            sub_chp = self.sub_chp[3]
        else:
            sub_chp = self.sub_chp[4]

        return sub_chp

    def get_self_demand_usage_chp(self, year,pNom):
        '''
        return the subsidy payment for self used chp electritiy

        -----------
        Parameters:
        year: 'int', reference year
        pNom: 'float', nominal electrical CHP power
        --------
        Returns:
        self_demand_usage_chp: 'float', subsidiy payments for sold chp electricity according to KWKG2016.
        '''
        if pNom <= 50000:
            self_demand_usage_chp = self.self_demand_usage_chp[0]
        elif pNom > 50000 and pNom <= 100000:
            self_demand_usage_chp = self.self_demand_usage_chp[1]
        else:
            self_demand_usage_chp = self.self_demand_usage_chp[2]
        return self_demand_usage_chp
    def get_gas_disc_chp(self, year):
        return self.gas_disc_chp
    def get_sub_pv(self, year, peakload):
        '''
        return the subsidy payment for sold pv electritiy

        -----------
        Parameters:
        year: 'int', reference year
        peakload: 'float', installed PV Peakload in W
        --------
        Returns:
        sub_pv: 'float', subsidiy payments for sold pv electricity according to EEG2017.
        '''
        if peakload <= 10000:
            # max 10kWp
            sub_pv = self.sub_pv[0]
        elif 10000 < peakload and peakload <= 40000:
            # from 10 to 40kWp
            sub_pv = self.sub_pv[1]
        elif peakload <= 100000:
            # maximum 100kWp
            sub_pv = self.sub_pv[2]
        else:
            # TODO: there are some exception from the 100kWp maximum in the EEG
            # TODO: implement a case for more than 100kWp
            warnings.warn('PV System hast more than 100kWp. The implemented EEG subsidy payments \n'
                          'method is not valid for this case. sub_pv set to 0.1109')
            sub_pv = self.sub_pv[2]
        return sub_pv

    def load_pricing_data(self):
        #TODO: get the values from somewere
        #TODO: think about structure of the input data. On which values do the prices depent? Year? Demand?
        print('nothing here yet')