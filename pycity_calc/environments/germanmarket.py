#!/usr/bin/env python
# coding=utf-8
"""
Script to extend pycity market object
"""
from __future__ import division
import warnings

import pycity_calc.environments.market as market


class GermanMarket(market.Market):
    """
    GermanMarket class of pycity_calculator.
    Extends pycity_calc market class with specific regulations for German
    market, such as CHP subsidies (German CHP law / KWK Gesetz) and renewable
    energy regulations (Renewable energy law / EEG), EEX baseload prices,
    grid avoidance fee.
    """

    def __init__(self, reset_pycity_default_values=True,
                 chp_tax_return=0.0055, eeg_pay=0.0688,
                 eex_baseload=[0.03309, 0.03309, 0.03309, 0.03309],
                 grid_av_fee=0.0055, hp_day_tarif=0.22, hp_night_tarif=0.2):
        """
        Constructor of GermanMarket object instance

        Parameters
        ----------
        reset_pycity_default_values : bool, optional
            Boolean to define, if pycity default values should be set to None.
            (default: True)
            True - Set all default values to None
            False - Keep pycity default market values
        chp_tax_return : float, optional
            CHP tax return on gas usage in Euro/kWh (default: 0.0055)
        eeg_pay : float, optional
            EEG payment in Euro/kWh (default: 0.0688)
        eex_baseload : list (of floats), optional
            List with quarterly EEX baseload prices in Euro/kWh
            (default: [0.03272, 0.03272, 0.03272, 0.03272])
        grid_av_fee : float, optional
            Grid usage avoidance fee in Euro/kWh
            (default: 0.0055)
        hp_day_tarif : float, optional
            Heat pump day tarif in Euro/kWh
            (default: 0.22)
        hp_night_tarif : float, optional
            Heat pump night tarif in Euro/kWh
            (default: 0.2)
        """

        super(GermanMarket, self).__init__(reset_pycity_default_values=
                                           reset_pycity_default_values)

        #  List of CHP subsidies for fed-in electric energy
        self._sub_chp = [0.08, 0.06, 0.05, 0.044, 0.031]

        #  List of CHP subsidies for self-consumed electric energy
        self._sub_chp_self = [0.04, 0.03, 0]

        #  List of PV subsidies
        self._sub_pv = [0.123, 0.1196, 0.1069, 0.0851]

        #  CHP tax return on gas
        self.chp_tax_return = chp_tax_return

        #  HP tarifs
        self.hp_day_tarif = hp_day_tarif
        self.hp_night_tarif = hp_night_tarif

        #  EEX baseload prices
        self.eex_baseload = eex_baseload

        #  Grid usage avoidance fee
        self.grid_av_fee = grid_av_fee

        #  EEG payment
        self.eeg_pay = eeg_pay

        #  Dict with EEG payment on self consumed energy (status quo: 2017)
        self._dict_eeg_self = {'pv': 0.4 * eeg_pay, 'chp': 0.4 * eeg_pay}

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

    def get_max_total_runtime_chp_sub(self, p_el_nom):
        """
        Returns maximal full-load hours runtime of CHP for getting
        payments of German CHP law (KWKG)

        Parameters
        ----------
        p_el_nom : float
            Nominal electric power of CHP in Watt

        Returns
        -------
        sub_chp_runtime : int
            Maximum CHP runtime, which is used to get subsidy payments, in
            hours

        Annotations
        -----------
        http://www.bhkw-jetzt.de/foerderung/nach-kwk-g/
        """

        assert p_el_nom >= 0

        if p_el_nom <= 50 * 1000:
            return 60000
        else:  # Larger than 50 kW el.
            return 30000


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

    def get_eeg_payment(self, type):
        """
        Returns EEG payment on self-produced and consumed el. energy of CHP
        or PV system.

        Parameters
        ----------
        type : str
            Defines system type. Options:
            - 'chp' : CHP system
            - 'pv' : PV system

        Returns
        -------
        eeg_pay : float
            Specific EEG payment in Euro/kWh
        """

        assert type in ['chp', 'pv'], 'Type is invalid (must be PV or CHP)'

        if type == 'chp':
            eeg_pay = self._dict_eeg_self['chp']
        elif type == 'pv':
            eeg_pay = self._dict_eeg_self['pv']

        return eeg_pay

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

    #  Get EEG payment on self-produced and consumed CHP el. energy
    #  ###################################################################
    eeg_pay = germanmarket.get_eeg_payment(type='chp')

    print('EEG payment on self-consumed CHP el. energy in Euro/kWh:')
    print(eeg_pay)
