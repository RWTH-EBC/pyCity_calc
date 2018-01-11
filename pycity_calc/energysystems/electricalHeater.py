#!/usr/bin/env python
# coding=utf-8
"""
Extended electricalHeater class (based on electricalHeater object of pycity)
"""
from __future__ import division

import pycity_base.classes.supply.ElectricalHeater as EHeat
import warnings


class ElectricalHeaterExtended(EHeat.ElectricalHeater):
    """
    electricalHeaterExtended class (inheritance from electricalHeater Boiler
    class)

    self.totalPConsumption
    self.totalQOutput
    """

    def __init__(self,
                 environment,
                 q_nominal,
                 eta=1,
                 t_max=85,
                 lower_activation_limit=0):
        """
        Parameters
        ----------
        environment : Extended environment object
            Common to all other objects. Includes time and weather instances
        q_nominal : float
            nominal heat production in W
        eta : float, optional
            nominal efficiency (without unit) (default: 1)
        t_max : float
            maximum provided temperature in °C
            (default : 85 °C)
        lower_activation_limit : float, optional
            Define the lower activation limit. For example, heat pumps are
            typically able to operate between 50 % part load and rated load.
            In this case, lower_activation_limit would be 0.5
            Two special cases:
            Linear behavior: lower_activation_limit = 0
            Two-point controlled: lower_activation_limit = 1
            Range:(0 <= lower_activation_limit <= 1)
            (Default : 0)

        Attributes
        ----------
        p_nominal : float
            nominal electrical power input in W
        """

        assert eta > 0, ('Efficiency of electrical heater should not be ' +
                         'equal to or below zero. Check your inputs.')
        assert eta <= 1, ('Efficiency of electrical heater should not' +
                          ' exceed 1. Check your inputs.')

        super(ElectricalHeaterExtended, self).__init__(environment=environment,
                                                       qNominal=q_nominal,
                                                       tMax=t_max,
                                                       lowerActivationLimit=
                                                       lower_activation_limit,
                                                       eta=eta)

    def calc_el_heater_thermal_power_output(self, control_signal):
        """
        Returns thermal power output of electric heater (limited by q_nominal)

        Parameters
        ----------
        control_signal : float
            input signal that defines desired thermal output in W

        Returns
        -------
        q_power_output : float
            Thermal power output in W of extended electric heating system
        """

        if control_signal < 0:
            warnings.warn('Control signal for electrical heater' + str(self) +
                          'is negative. Output is defined as zero.')
            control_signal = 0
        elif (control_signal < self.lowerActivationLimit * self.qNominal
              and control_signal !=0):
            warnings.warn('Control signal for electrical heater' + str(self) +
                          'is below minimum part load performance. '
                          'Therefore, output is defined as zero.')
            control_signal = 0

        #  If desired output power is smaller or equal to nominal power,
        #  desired power can be provided
        if control_signal <= self.qNominal:
            q_power_output = control_signal
        else:  # Output is limited to nominal thermal power
            q_power_output = self.qNominal

        assert q_power_output >= 0, 'thermal output cannot be negative'

        return q_power_output

    def calc_el_heater_electric_power_input(self, th_power_out):
        """
        Returns electrical power input of extended electric heating system

        Parameters
        ----------
        th_power_out : float
            Thermal power output in W

        Returns
        ------
        el_power_input : float
            Electrical power input in W
        """

        assert th_power_out >= 0

        if th_power_out == 0:
            el_power_input = 0
        else:
            el_power_input = th_power_out / self.eta

        assert el_power_input >= 0, 'electrical Output cannot be negative'

        return el_power_input

    def calc_el_h_all_results(self, control_signal, time_index, save_res=True):
        """
        Calculate and save all results of electrical heater (thermal power,
        electrical power input)

        Parameters
        ----------
        control_signal : float
            Desired thermal power output in W
        time_index : int
            Number of timestep (necessary to save results)
        save_res : bool, optional
            Defines, if results should be saved on EH object instance
            (default: True)

        Returns
        -------
        result_tuple : tuple
            Tuple with results (thermal_power, el_power_in)
        """

        th_power = self.calc_el_heater_thermal_power_output(control_signal)

        el_power_in = self.calc_el_heater_electric_power_input(th_power)

        if save_res:
            #  Save results
            self.totalPConsumption[time_index] = el_power_in
            self.totalQOutput[time_index] = th_power

        return (th_power, el_power_in)