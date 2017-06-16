#!/usr/bin/env python
# coding=utf-8
"""
Script to extend pycity market object
"""

import warnings

import pycity_calc.environments.market as market


class GermanMarket(market.Market):
    """
    GermanMarket class of pycity_calculator.
    Extends pycity_calc market class with specific regulations for German
    market, such as CHP subsidies (German CHP law / KWK Gesetz) and renewable
    energy regulations (Renewable energy law / EEG)

    Attributes:
    -----------
    EEG_Umlage_tax
        #  TODO
    EEX_baseload_price
        #  TODO
    avoid_grid_usage: 'float', payment for avoided grid usage for sold chp
    electricity according to KWKG2016.
        in €/kWh
    sub_chp: 'list', subsidiy payments for sold chp electricity according to
    KWKG2016.
        sub_chp[0] - pNom < 50kW in €/kWh
        sub_chp[1] - 50kW < pNom < 100kW  in €/kWh
    self_demand_usage_chp: 'list', subsidiy payments for self used chp
    electricity according to KWKG2016.
        sub_chp[0] - pNom < 50kW  in €/kWh
        sub_chp[1] - 50kW < pNom < 100kW  in €/kWh
    gas_disc_chp: 'float', discount on used gas with highly efficient
    Energysystems according to german Energy tax law.
    sub_pv: 'list', subsidiy payments for sold pv electricity according to
    EEG2017.
        sub_pv[0] - kWpeak < 10kW  in €/kWh
        sub_pv[1] - 10kW < kWpeak < 40kW  in €/kWh
        sub_pv[2] - 40kW < kWpeak < 100kW  in €/kWh
    """

    def __init__(self, reset_pycity_default_values=True):
        """
        Constructor of GermanMarket object instance

        Parameters
        ----------
        reset_pycity_default_values : bool, optional
            Boolean to define, if pycity default values should be set to None.
            (default: True)
            True - Set all default values to None
            False - Keep pycity default market values
        """
        #  TODO: Add gas tax return for CHP

        super(GermanMarket, self).__init__(reset_pycity_default_values=
                                           reset_pycity_default_values)

        #  List of CHP subsidies for fed-in electric energy
        self._sub_chp = [0.08, 0.06, 0.05, 0.044, 0.031]

        #  List of CHP subsidies for self-consumed electric energy
        self._sub_chp_self = [0.04, 0.03, 0]

        #  List of PV subsidies
        self._sub_pv = [0.123, 0.1196, 0.1069, 0.0851]

        # self.EEG_Umlage_tax=[0.05,0.04]
        # self.EEX_baseload_price=1
        # self.avoid_grid_usage=0.07
        # self.gas_disc_chp=0.0055

    def get_sub_chp(self, p_nom):
        """
        Returns CHP subsidy payment per kWh feed in el. energy, depending
        on nominal el. CHP power

        Parameters
        ----------
        p_nom : float
            Nominal electrical CHP power in W

        Returns
        -------
        sub_chp : float
            CHP subsidies payment in Euro/kWh for fed-in electric energy
        """

        for i in range(len(self._sub_chp) - 1):
            if self._sub_chp[i + 1] > self._sub_chp[i]:
                msg = 'self._sub_chp list seems to hold higher subsidies for' \
                      'larger CHP units. Check if this has been done ' \
                      'intentionally. According to German CHP law, subsidies' \
                      ' are higher for smaller CHP sizes.'
                warnings.warn(msg)

        if p_nom <= 50000:
            sub_chp = self._sub_chp[0]
        elif p_nom <= 100000:
            sub_chp = self._sub_chp[1]
        elif p_nom <= 250000:
            sub_chp = self._sub_chp[2]
        elif p_nom <= 2000000:
            sub_chp = self._sub_chp[3]
        else:
            sub_chp = self._sub_chp[4]

        return sub_chp

    def get_sub_chp_self(self, p_nom):
        """
        Returns CHP subsidy payment for self consumed electric energy in
        Euro/kWh.

        Parameters
        ----------
        p_nom : float
            Nominal electrical CHP power in W

        Returns
        -------
        sub_chp : float
            CHP subsidies payment in Euro/kWh for self-consumed electric energy
        """
        for i in range(len(self._sub_chp_self) - 1):
            if self._sub_chp_self[i + 1] > self._sub_chp_self[i]:
                msg = 'self._sub_chp_self list seems to hold higher subsidies ' \
                      'for larger CHP units. Check if this has been done ' \
                      'intentionally. According to German CHP law, subsidies' \
                      ' are higher for smaller CHP sizes.'
                warnings.warn(msg)

        if p_nom <= 50000:
            sub_chp = self._sub_chp_self[0]
        elif p_nom <= 100000:
            sub_chp = self._sub_chp_self[1]
        else:
            sub_chp = self._sub_chp_self[2]

        return sub_chp

    def get_sub_pv(self, pv_peak_load, is_res=True):
        """
        Returns the subsidy payment for sold pv electricity

        Parameters
        ----------
        pv_peak_load : float
            PV peak load in Watt
        is_res : bool, optional
            Defines, if PV is installed on residential building (default: True)
            If True, PV is installed on residential building.
            If False, PV is installed on non-residential building with
            lower subsidies.

        Returns
        -------
        sub_pv : float
            Subsidy payment for sold PV el. energy in Euro/kWh
        """

        if is_res:

            if pv_peak_load <= 10000:
                # max 10kWp
                sub_pv = self._sub_pv[0]
            elif pv_peak_load <= 40000:
                # from 10 to 40kWp
                sub_pv = self._sub_pv[1]
            elif pv_peak_load <= 100000:
                # maximum 100kWp
                sub_pv = self._sub_pv[2]
            else:
                msg = 'PV System hast more than 100kWp.\nThe implemented EEG' \
                      ' subsidy payments method is not valid for this case.\n' \
                      ' sub_pv set to ' + str(self._sub_pv[3] * 0.7) + '.\n ' \
                      'Consider adding own PV subsidy value!'
                warnings.warn(msg)
                sub_pv = self._sub_pv[2] * 0.7

        else:
            if pv_peak_load <= 100000:
                sub_pv = self._sub_pv[3]
            else:
                msg = 'PV System hast more than 100kWp.\nThe implemented EEG' \
                      ' subsidy payments method is not valid for this case.\n' \
                      ' sub_pv set to ' + str(self._sub_pv[3] * 0.7) + '.\n ' \
                      'Consider adding own PV subsidy value!'
                warnings.warn(msg)
                sub_pv = self._sub_pv[3] * 0.7

        return sub_pv


if __name__ == '__main__':

    #  Initialize GermanMarket object instance
    germanmarket = GermanMarket()

    chp_nom_el_p = 30000  # El. CHP power in Watt
    chp_nom_el_p_2 = 100000  # El. CHP power in Watt

    #  Get CHP subsidies of CHP fed-in el. energy
    chp_sub = germanmarket.get_sub_chp(p_nom=chp_nom_el_p)

    #  Get CHP subsidies of CHP for self consumed el. energy
    chp_sub_self = germanmarket.get_sub_chp_self(p_nom=chp_nom_el_p)

    print('Get CHP subsidies for CHP of size ' + str(chp_nom_el_p / 1000) +
          ' kW:')
    print('CHP subsidy for fed-in el. energy in Euro/kWh:')
    print(chp_sub)
    print('CHP subsidy for self consumed el. energy in Euro/kWh:')
    print(chp_sub_self)
    print()

    #  Get CHP subsidies of CHP fed-in el. energy
    chp_sub2 = germanmarket.get_sub_chp(p_nom=chp_nom_el_p_2)

    #  Get CHP subsidies of CHP for self consumed el. energy
    chp_sub_self2 = germanmarket.get_sub_chp_self(p_nom=chp_nom_el_p_2)

    print('Get CHP subsidies for CHP of size ' + str(chp_nom_el_p_2 / 1000) +
          ' kW:')
    print('CHP subsidy for fed-in el. energy in Euro/kWh:')
    print(chp_sub2)
    print('CHP subsidy for self consumed el. energy in Euro/kWh:')
    print(chp_sub_self2)
    print()

    #  PV subsidies
    #  ###################################################################
    pv_peak_power = 30000  # in Watt

    pv_sub_res = germanmarket.get_sub_pv(pv_peak_load=pv_peak_power,
                                         is_res=True)

    pv_sub_nonres = germanmarket.get_sub_pv(pv_peak_load=pv_peak_power,
                                            is_res=False)

    print('PV subsidy payment in Euro/kWh for PV module with peak load '
          + str(pv_peak_power / 1000) + ' kW on residential building:')
    print(pv_sub_res)

    print('PV subsidy payment in Euro/kWh for PV module with peak load '
          + str(pv_peak_power / 1000) + ' kW on non-residential building:')
    print(pv_sub_nonres)
