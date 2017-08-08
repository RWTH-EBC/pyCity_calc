#!/usr/bin/env python
# coding=utf-8
"""
Extended electric chp class (based on CHP object of pycity)
"""
from __future__ import division
import warnings

import numpy as np

import pycity_base.classes.supply.CHP as chp
import pycity_calc.energysystems.Input.chp_asue_2015 as asue


class ChpExtended(chp.CHP):
    """
    ChpExtended class (inheritance from pycity CHP class)

    self.totalQOutput
    self.totalPOutput
    self.array_fuel_power
    """

    def __init__(self, environment,
                 q_nominal,
                 p_nominal,
                 t_max=90,
                 lower_activation_limit=0.6,
                 eta_total=0.9,
                 chp_type='ASUE_2015',
                 thermal_operation_mode=True):
        """
        Parameters
        ---------
        environment : Extended environment object
            Common to all other objects. Includes time and weather instances
        p_nominal : float
            nominal electricity output in Watt
        q_nominal : float
            nominal heat output in Watt
        t_max : integer, optional
            maximum provided temperature in °C
            (default : 90 °C)
        lower_activation_limit : float
            Define the lower activation limit . For example, heat pumps are
            typically able to operate between 50 % part load and rated load.
            In this case, lower_activation_limit would be 0.5
            Two special cases:
            Linear behavior: lower_activation_limit = 0
            Two-point controlled: lower_activation_limit = 1
            Range: (0 <= lower_activation_limit <= 1)
            (default : 0.6)
        eta_total : float
            total efficiency of the CHP unit (without unit)
            (default : 0.9)
        chp_type : str, optional
            Defines chp type (with efficiency and specific cost curves)
            (default : 'ASUE_2015')
            chp_type='ASUE_2015' (for datasets of Arbeitsgemeinschaft für
            sparsamen und umweltfreundlichen
            Energieverbrauch e.V., BHKW-Kenndaten 2014/15, Essen, 2015.)
            Options:
            - 'ASUE_2015'
        thermal_operation_mode : boolean, optional
            Defines if the chp modul is in thermal or electrical operation mode
            this determines the corresponding nominal thermal or electrical
            power of the chp module
            (default : True) -->
            True = thermal operation mode
            False = electrical operation mode

        Attributes
        ----------
        chp_type : str
            Defines chp type (with efficiency and specific cost curves)
            (default: 'ASUE_2015')
        thermal_operation_mode : boolean
            Defines if the chp modul is in thermal or electrical operation mode
            True = thermal operation mode
            False = electrical operation mode
        qNominal_thOpM : float
            the nominal thermal power if used in thermal operation mode
        pNominal_elOpM : float
            the nominal electrical power if used in electrical operatoin mode
        """

        #  Assert functions
        assert q_nominal >= 0, 'Thermal Power cannot be below zero.'
        assert p_nominal >= 0, 'Electrical Power cannot be below zero.'
        assert eta_total > 0, ('CHP total efficiency should not be equal to ' +
                               ' or below zero. Check your inputs.')
        assert eta_total <= 1, ('CHP total efficiency should not go above 1.' +
                                'Check your inputs.')

        assert lower_activation_limit <= 1, 'Part Load can not be above 100 %.'
        assert lower_activation_limit >= 0, 'Part Load can not be below 0.'

        assert eta_total >= 0, ('The total efficiency of the CHP Unit ' +
                                'cannot be negativ.')
        assert eta_total <= 1, (
            'The total efficiency of the CHP Unit cannot be larger'
            'than one.')

        if thermal_operation_mode:  # thermal operation mode

            th_power = q_nominal
            el_power = asue.calc_el_power_with_th_power(q_nominal, eta_total)

            try:
                assert el_power < p_nominal * 1.2
            except AssertionError:
                warnings.warn(
                    "Electrical nominal power is too large for thermal"
                    "operation mode. Electrical power should be between " +
                    str(round(el_power / 1.2, 2)) + " and " +
                    str(round(el_power * 1.2, 2)) + " W."
                    " Check your System!")
            try:
                assert el_power > p_nominal / 1.2
            except AssertionError:
                warnings.warn(
                    "Electrical nominal power is too large for thermal"
                    "operation mode. Electrical power should be between " +
                    str(round(el_power / 1.2, 2)) + " and " +
                    str(round(el_power * 1.2, 2)) + " W."
                    " Check your System!")

        else:  # electrical operation mode
            el_power = p_nominal
            th_power = asue.calc_th_output_with_p_el(el_power, eta_total)

            try:
                assert th_power < q_nominal * 1.2
            except AssertionError:
                warnings.warn(
                    "Thermal nominal power is too little for electrical"
                    "operation mode. Thermal power should be between " +
                    str(round(th_power / 1.2, 2)) + " and " +
                    str(round(th_power * 1.2, 2)) + " W."
                    " Check your system!")
            try:
                assert th_power > q_nominal / 1.2
            except AssertionError:
                warnings.warn(
                    "Thermal nominal power is too little for electrical"
                    "operation mode. Thermal power should be between " +
                    str(round(th_power / 1.2, 2)) + " and " +
                    str(round(th_power * 1.2, 2)) + " W."
                    " Check your system!")

        super(ChpExtended, self).__init__(environment,
                                          qNominal=th_power,
                                          tMax=t_max,
                                          lowerActivationLimit=
                                          lower_activation_limit,
                                          pNominal=el_power,
                                          omega=eta_total)

        timesteps_total = environment.timer.timestepsTotal

        # further attributes
        self.chp_type = chp_type
        self.array_fuel_power = np.zeros(timesteps_total)
        self.thermal_operation_mode = thermal_operation_mode
        self.qNominal_thOpM = q_nominal
        self.pNominal_elOpM = p_nominal

    def change_operation_mode(self):
        """
        Changes the predefined operation mode of the chp module.
        If the operation mode was thermal is will further be electrical and
        vice versa.

        The now changed thermal or electrical power is set to the nominal
        initialized power.
        """

        if self.thermal_operation_mode:  # thermal operation mode --> change the electrical operation mode
            self.thermal_operation_mode = False
            el_power = self.pNominal_elOpM
            th_power = asue.calc_th_output_with_p_el(el_power, self.omega)

            assert th_power < self.qNominal_thOpM * 1.2, "Thermal nominal power is too large for electrical operation mode." \
                                                         " Thermal power should be between " + str(
                round(th_power / 1.2, 2)) + " and " + str(
                round(th_power * 1.2, 2)) + " W." \
                                            " Check your system!"
            assert th_power > self.qNominal_thOpM / 1.2, "Thermal nominal power is too large for electrical operation mode." \
                                                         " Thermal power should be between " + str(
                round(th_power / 1.2, 2)) + " and " + str(
                round(th_power * 1.2, 2)) + " W." \
                                            " Check your system!"
            self.pNominal = el_power
            self.qNominal = th_power

        else:  # electrical operation mode --> change to thermal operation mode
            self.thermal_operation_mode = True
            th_power = self.qNominal_thOpM
            el_power = asue.calc_el_power_with_th_power(th_power, self.omega)

            assert el_power < self.pNominal_elOpM * 1.2, "Electrical nominal power is too little for thermal operation mode. " \
                                                         " Electrical power should be between " + str(
                round(el_power / 1.2, 2)) + " W and " + str(
                round(el_power * 1.2, 2)) + " W." \
                                            " Check your system!"
            assert el_power > self.pNominal_elOpM / 1.2, "Electrical nominal power is too little for thermal operation mode. " \
                                                         " Electrical power should be between " + str(
                round(el_power / 1.2, 2)) + " W and " + str(
                round(el_power * 1.2, 2)) + " W." \
                                            " Check your system!"
            self.pNominal = el_power
            self.qNominal = th_power

    def thOperation_calc_chp_th_power_output(self, control_signal):
        """
        Returns the thermal power output in W in thermal operation mode.
        Maximal thermal output is limited by q_nominal of CHP.
        Calculation are based on the ASUE_2015 Data.

        Parameters
        ----------
        control_signal : float
            Desired thermal power output in W

        Returns
        ------
        th_power : float
            Thermal power output of CHP in W
        """

        #  If control signal is negative, define output as zero
        if control_signal < 0:
            warnings.warn('Thermal control signal for CHP' + str(self) +
                          'is negative. Therefore, output is defined as zero.')
            control_signal = 0

        # If control signal is below minimal part load performance,
        #  output is defined as zero
        elif control_signal < self.lowerActivationLimit * self.qNominal:
            warnings.warn('Thermal control signal for CHP' + str(self) +
                          'is below minimum part load performance. '
                          'Therefore, output is defined as zero.')
            control_signal = 0

        # If desired output power is smaller or equal to nominal power,
        #  desired power can be provided
        if control_signal <= self.qNominal:
            th_power = control_signal
        else:  # Otherwise, output power is limited to nominal thermal power
            th_power = self.qNominal

        return th_power

    def thOperation_calc_chp_el_power_output(self, control_signal):
        """
        Returns the electric power output of the CHP module in W in thermal
        operation mode.
        The electrical output is limited by omega of the CHP module.
        Calculation are based on the ASUE_2015 Data.

        Parameters
        ----------
        control_signal : float
            Desired thermal power output in W

        Returns
        ------
        el_power :  float
            Electrical power output in W
        """
        # calculate thermal power
        th_power = self.thOperation_calc_chp_th_power_output(control_signal)

        if self.chp_type == 'ASUE_2015':
            el_power = asue.calc_el_power_with_th_power(th_power, self.omega)
        else:
            raise AssertionError('Unknown chp_type. Check input.')

        return el_power

    def thOperation_calc_chp_el_power_output_w_th(self, th_power_out):
        """
        Returns the electric power output of the CHP module in W in thermal
        operation mode.
        The electrical output is limited by omega of the CHP module.
        Calculation are based on the ASUE_2015 Data.

        Parameters
        ----------
        th_power_out : float
            Thermal power output of chp in W

        Returns
        ------
        el_power :  float
            Electrical power output in W
        """

        assert th_power_out >= 0

        if self.chp_type == 'ASUE_2015':
            if th_power_out > 0:
                el_power = asue.calc_el_power_with_th_power(th_power_out,
                                                            self.omega)
            elif th_power_out == 0:
                el_power = 0
        else:
            raise AssertionError('Unknown chp_type. Check input.')

        return el_power

    def thOperation_calc_chp_fuel_power_input(self, control_signal):
        """
        Calculates fuel power input of the CHP module in W in thermal
        operation mode.
        Calculation are based on the ASUE_2015 Data.

        Parameters
        ----------
        control_signal : float
            Desired thermal power output in W

        Returns
        ------
        fuel_power : float
            Fuel power input in W
        """
        # calculate thermal power
        th_power = self.thOperation_calc_chp_th_power_output(control_signal)

        if self.chp_type == 'ASUE_2015':
            th_eff = asue.calc_th_eff_with_th_power(th_power, self.omega)
            fuel_power = th_power / th_eff
            assert fuel_power >= 0, 'Required fuel power cannot be below zero.'
        else:
            raise AssertionError('Unknown chp_type. Check input.')

        return fuel_power

    def thOperation_calc_chp_fuel_power_input_w_th(self, th_power_out):
        """
        Calculates fuel power input of the CHP module in W in thermal
        operation mode.
        Calculation are based on the ASUE_2015 Data.

        Parameters
        ----------
        th_power_out : float
            Thermal power output of chp in W

        Returns
        ------
        fuel_power : float
            Fuel power input in W
        """

        assert th_power_out >= 0

        if self.chp_type == 'ASUE_2015':
            if th_power_out > 0:
                th_eff = asue.calc_th_eff_with_th_power(th_power_out,
                                                        self.omega)
                fuel_power = th_power_out / th_eff
                assert fuel_power >= 0, 'Fuel power cannot be negative.'
            elif th_power_out == 0:
                fuel_power = 0
        else:
            raise AssertionError('Unknown chp_type. Check input.')

        return fuel_power

    def thOperation_calc_chp_th_efficiency(self, control_signal):
        """
        Calculates thermal efficiency of CHP module in thermal operation mode.
        Calculation are based on the ASUE_2015 Data.

        Parameters
        ----------
        control_signal : float
            Desired thermal power output in W

        Returns
        ------
        th_eff : float
            Thermal efficiency (no unit)
        """

        # calculate thermal power
        th_power = self.thOperation_calc_chp_th_power_output(control_signal)

        if th_power == 0:
            th_eff = 0
        else:
            if self.chp_type == 'ASUE_2015':
                th_eff = asue.calc_th_eff_with_th_power(th_power, self.omega)
                assert th_eff >= 0, 'Thermal efficiency cannot be below zero.'
                assert th_eff <= 1, ('Thermal efficiency cannot be larger' +
                                     ' than one.')
            else:
                raise AssertionError('Unknown chp_type. Check inputs.')

        return th_eff

    def thOperation_calc_chp_th_efficiency_w_th(self, th_power_out):
        """
        Calculates thermal efficiency of CHP module in thermal operation mode.
        Calculation are based on the ASUE_2015 Data.

        Parameters
        ----------
        th_power_out : float
            Thermal power output of chp in W

        Returns
        ------
        th_eff : float
            Thermal efficiency (no unit)
        """

        assert th_power_out >= 0

        if th_power_out == 0:
            th_eff = 0
        else:
            if self.chp_type == 'ASUE_2015':
                th_eff = asue.calc_th_eff_with_th_power(th_power_out,
                                                        self.omega)
                assert th_eff >= 0, 'Thermal efficiency cannot be below zero.'
                assert th_eff <= 1, ('Thermal efficiency cannot be larger' +
                                     ' than one.')
            else:
                raise AssertionError('Unknown chp_type. Check inputs.')

        return th_eff

    def thOperation_calc_chp_el_efficiency(self, control_signal):
        """
        Calculates electric efficiency of CHP module in thermal operation mode.
        Calculation are based on the ASUE_2015 Data.

        Parameters
        ----------
        control_signal : float
            Desired thermal power output in W

        Returns
        ------
        el_eff : float
            Electric efficiency (no unit)
        """
        # calculate thermal power
        th_power = self.thOperation_calc_chp_th_power_output(control_signal)

        if th_power == 0:
            el_eff = 0
        else:
            if self.chp_type == 'ASUE_2015':
                el_eff = asue.calc_el_eff_with_th_power(th_power)
                assert el_eff >= 0, 'Electrical efficiency cannot be below zero.'
                assert el_eff <= 1, 'Electrical efficiency cannot be larger than one.'
            else:
                raise AssertionError('Unknown chp_type. Check inputs.')

        return el_eff

    def thOperation_calc_chp_el_efficiency_w_th(self, th_power_out):
        """
        Calculates electric efficiency of CHP module in thermal operation mode.
        Calculation are based on the ASUE_2015 Data.

        Parameters
        ----------
        th_power_out : float
            Thermal power output of chp in W

        Returns
        ------
        el_eff : float
            Electric efficiency (no unit)
        """

        assert th_power_out >= 0

        if th_power_out == 0:
            el_eff = 0
        else:
            if self.chp_type == 'ASUE_2015':
                el_eff = asue.calc_el_eff_with_th_power(th_power_out)
                assert el_eff >= 0, 'Electrical efficiency cannot be below zero.'
                assert el_eff <= 1, 'Electrical efficiency cannot be larger than one.'
            else:
                raise AssertionError('Unknown chp_type. Check inputs.')

        return el_eff

    def th_op_calc_all_results(self, control_signal, time_index,
                               save_res=True):
        """
        Calculate and save results (thermal and el. output, fuel input)
        for thermal operation mode.

        Parameters
        ----------
        control_signal : float
            Control signal for desired thermal power in W
        time_index : int
            Number of timestep (relevant for saving results)
        save_res : bool, optional
            Defines, if results should be saved on boiler object instance
            (default: True)

        Returns
        -------
        results_tuple : tuple
            Tuple with results (thermal power, el. power, fuel power)
        """

        #  Calculate thermal power output of chp in W
        th_power = self.thOperation_calc_chp_th_power_output(control_signal)

        #  Calculate el. power output of chp in W
        el_power = self.thOperation_calc_chp_el_power_output_w_th(th_power)

        #  Calculate fuel power input of chp in W
        fuel_power_in = \
            self.thOperation_calc_chp_fuel_power_input_w_th(th_power)

        if save_res:
            #  Save results
            self.totalQOutput[time_index] = th_power
            self.totalPOutput[time_index] = el_power
            self.array_fuel_power[time_index] = fuel_power_in

        return (th_power, el_power, fuel_power_in)


    ##########################################################################
    ########################## electrical operation ##########################
    ##########################################################################

    def elOperation_calc_chp_el_power_output(self, control_signal):
        """
        Returns the electrical power output in W in electrical operation mode
        Maximal thermal output is limited by p_nominal of CHP.
        Calculation are based on the ASUE_2015 Data.

        Parameters
        ----------
        control_signal : float
            Desired electrical power output in W

        Returns
        ------
        el_power : float
            Electrical power output of CHP in W
        """

        #  If control signal is negative, define output as zero
        if control_signal < 0:
            warnings.warn('Electrical control signal for CHP' + str(self) +
                          'is negative. Therefore, output is defined as zero.')
            control_signal = 0

        # If control signal is below minimal part load performance,
        #  output is defined as zero
        elif control_signal < self.lowerActivationLimit * self.pNominal:
            warnings.warn('Electrical control signal for CHP' + str(self) +
                          'is below minimum part load performance. '
                          'Therefore, output is defined as zero.')
            control_signal = 0

        # If desired output power is smaller or equal to nominal power,
        #  desired power can be provided
        if control_signal <= self.pNominal:
            el_power = control_signal
        else:  # Otherwise, output power is limited to nominal thermal power
            el_power = self.pNominal

        return el_power

    def elOperation_calc_chp_th_power_output(self, control_signal):
        """
        Returns the thermal power output of the CHP module in W in electrical
        operation mode.
        The th output is limited by omega of the CHP module.
        Calculation are based on the ASUE_2015 Data.

        Parameters
        ----------
        control_signal : float
            Desired electrical power output in W

        Returns
        ------
        el_power :  float
            Thermal power output in W
        """

        # calculate electrical power
        el_power = self.elOperation_calc_chp_el_power_output(control_signal)

        if el_power == 0:
            th_power = 0
        else:
            if self.chp_type == 'ASUE_2015':
                th_power = asue.calc_th_output_with_p_el(el_power, self.omega)
            else:
                raise AssertionError('Unknown chp_type. Check inputs.')

        return th_power

    def elOperation_calc_chp_th_power_output_w_el(self, el_power):
        """
        Returns the thermal power output of the CHP module in W in electrical
        operation mode.
        The th output is limited by omega of the CHP module.
        Calculation are based on the ASUE_2015 Data.

        Parameters
        ----------
        el_power : float
            Electrical power output in W

        Returns
        ------
        el_power :  float
            Thermal power output in W
        """

        assert el_power >= 0

        if el_power == 0:
            th_power = 0
        else:
            if self.chp_type == 'ASUE_2015':
                th_power = asue.calc_th_output_with_p_el(el_power, self.omega)
                assert th_power >= 0
            else:
                raise AssertionError('Unknown chp_type. Check inputs.')

        return th_power

    def elOperation_calc_chp_fuel_power_input(self, control_signal):
        """
        Calculates fuel power input of the CHP module in W in electrical
        operation mode.
        Calculation are based on the ASUE_2015 Data.

        Parameters
        ----------
        control_signal : float
            Desired electrical power output in W

        Returns
        ------
        fuel_power : float
            Fuel power input in W
        """
        # calculate electrical power
        el_power = self.elOperation_calc_chp_el_power_output(control_signal)

        if el_power == 0:
            fuel_power = 0
        else:
            if self.chp_type == 'ASUE_2015':
                el_eff = asue.calc_el_eff_with_p_el(el_power)
                fuel_power = el_power / el_eff
                assert fuel_power >= 0, 'Required fuel power cannot be below zero.'
            else:
                raise AssertionError('Unknown chp_type. Check inputs.')

        return fuel_power

    def elOperation_calc_chp_fuel_power_input_w_el(self, el_power):
        """
        Calculates fuel power input of the CHP module in W in electrical
        operation mode.
        Calculation are based on the ASUE_2015 Data.

        Parameters
        ----------
        el_power : float
            Electrical power output in W

        Returns
        ------
        fuel_power : float
            Fuel power input in W
        """

        assert el_power >= 0

        if el_power == 0:
            fuel_power = 0
        else:
            if self.chp_type == 'ASUE_2015':
                el_eff = asue.calc_el_eff_with_p_el(el_power)
                fuel_power = el_power / el_eff
                assert fuel_power >= 0, 'Fuel power cannot be below zero.'
            else:
                raise AssertionError('Unknown chp_type. Check inputs.')

        return fuel_power

    def elOperation_calc_chp_th_efficiency(self, control_signal):
        """
        Calculates thermal efficiency of CHP module in electrical operation
        mode.
        Calculation are based on the ASUE_2015 Data.

        Parameters
        ----------
        control_signal : float
            Desired electrical power output in W

        Returns
        ------
        th_eff : float
            Thermal efficiency (no unit)
        """
        # calculate electrical power
        el_power = self.elOperation_calc_chp_el_power_output(control_signal)

        if el_power == 0:
            th_eff = 0
        else:
            if self.chp_type == 'ASUE_2015':
                th_eff = asue.calc_th_eff_with_p_el(el_power, self.omega)
                assert th_eff >= 0, 'Thermal efficiency cannot be below zero.'
                assert th_eff <= 1, 'Thermal efficiency cannot be larger than one.'
            else:
                raise AssertionError('Unknown chp_type. Check inputs.')

        return th_eff

    def elOperation_calc_chp_th_efficiency_w_el(self, el_power):
        """
        Calculates thermal efficiency of CHP module in electrical operation
        mode.
        Calculation are based on the ASUE_2015 Data.

        Parameters
        ----------
        el_power : float
            Electrical power output in W

        Returns
        ------
        th_eff : float
            Thermal efficiency (no unit)
        """

        assert el_power >= 0

        if el_power == 0:
            th_eff = 0
        else:
            if self.chp_type == 'ASUE_2015':
                th_eff = asue.calc_th_eff_with_p_el(el_power, self.omega)
                assert th_eff >= 0, 'Thermal efficiency cannot be below zero.'
                assert th_eff <= 1, 'Thermal efficiency cannot be larger than one.'
            else:
                raise AssertionError('Unknown chp_type. Check inputs.')

        return th_eff

    def elOperation_calc_chp_el_efficiency(self, control_signal):
        """
        Calculates electric efficiency of CHP module in electrical operation
        mode.
        Calculation are based on the ASUE_2015 Data.

        Parameters
        ----------
        control_signal : float
            Desired electrical power output in W

        Returns
        ------
        el_eff : float
            Electric efficiency (no unit)
        """

        # calculate electrical power
        el_power = self.elOperation_calc_chp_el_power_output(control_signal)

        if el_power == 0:
            el_eff = 0
        else:
            if self.chp_type == 'ASUE_2015':
                el_eff = asue.calc_el_eff_with_p_el(el_power)
                assert el_eff >= 0, 'Electrical efficiency cannot be below zero.'
                assert el_eff <= 1, 'Electrical efficiency cannot be larger than one.'
            else:
                raise AssertionError('Unknown chp_type. Check inputs.')

        return el_eff

    def elOperation_calc_chp_el_efficiency_w_el(self, el_power):
        """
        Calculates electric efficiency of CHP module in electrical operation
        mode.
        Calculation are based on the ASUE_2015 Data.

        Parameters
        ----------
        el_power : float
            Electrical power output in W

        Returns
        ------
        el_eff : float
            Electric efficiency (no unit)
        """

        assert el_power >= 0

        if el_power == 0:
            el_eff = 0
        else:
            if self.chp_type == 'ASUE_2015':
                el_eff = asue.calc_el_eff_with_p_el(el_power)
                assert el_eff >= 0, 'Electrical efficiency cannot be below zero.'
                assert el_eff <= 1, 'Electrical efficiency cannot be larger than one.'
            else:
                raise AssertionError('Unknown chp_type. Check inputs.')

        return el_eff

    def el_op_calc_all_results(self, control_signal, time_index,
                               save_res=True):
        """
        Calculate and save results (thermal and el. output, fuel input)
        for electrical operation mode.

        Parameters
        ----------
        control_signal : float
            Control signal for desired electrical power in W
        time_index : int
            Number of timestep (relevant for saving results)
        save_res : bool, optional
            Defines, if results should be saved on CHP object instance
            (default: True)

        Returns
        -------
        results_tuple : tuple
            Tuple with results (thermal power, el. power, fuel power)
        """

        #  Calculate el. power output of chp in W
        el_power = self.elOperation_calc_chp_el_power_output(control_signal)

        #  Calculate thermal power output of chp in W
        th_power = self.elOperation_calc_chp_th_power_output_w_el(el_power)

        #  Calculate fuel power input of chp in W
        fuel_power_in = \
            self.elOperation_calc_chp_fuel_power_input_w_el(el_power)

        if save_res:
            #  Save results
            self.totalQOutput[time_index] = th_power
            self.totalPOutput[time_index] = el_power
            self.array_fuel_power[time_index] = fuel_power_in

        return (th_power, el_power, fuel_power_in)
