#!/usr/bin/env python
# coding=utf-8
"""
Extended boiler class (based on Boiler object of pycity)
"""
from __future__ import division
import numpy as np
import warnings

import pycity_base.classes.supply.Boiler as Boil


class BoilerExtended(Boil.Boiler):
    """
    BoilerExtended class (inheritance from pycity Boiler class)

    Derives from boiler (HeatingDevice) of pycity.

    self.totalQOutput
    self.array_fuel_power
    """

    def __init__(self, environment,
                 q_nominal,
                 eta,
                 t_max=85,
                 lower_activation_limit=0.2):
        """
        Parameters
        ----------
        environment : Extended environment object
            Common to all other objects. Includes time and weather instances
        q_nominal : float
            nominal heat output in W
        eta : float
            efficiency (without unit)
        t_max : Integer, optional
            maximum provided temperature in °C
            (default : 85 °C)
        lower_activation_limit : float , optional
            (0 <= lowerActivationLimit <= 1)
            Define the lower activation limit. For example, heat pumps are
            typically able to operate between 50 % part load and rated load.
            In this case, lowerActivationLimit would be 0.5
            Two special cases:
            Linear behavior: lowerActivationLimit = 0
            Two-point controlled: lowerActivationLimit = 1
            (default : 0.2)
        """

        assert 0 < eta, ('Efficiency of boiler should be greater 0.' +
                         ' Check your input for eta.')
        assert eta <= 1, ('Efficiency of boiler should smaller or equal to 1.' +
                          ' Check your input for eta.')

        # Initialize superclass
        super(BoilerExtended, self).__init__(environment=environment,
                                             qNominal=q_nominal,
                                             tMax=t_max,
                                             lowerActivationLimit=
                                             lower_activation_limit,
                                             eta=eta)

        timesteps_total = environment.timer.timestepsTotal

        self.array_fuel_power = np.zeros(timesteps_total)

    def calc_boiler_thermal_power_output(self, control_signal):
        """
        Returns thermal power output of boiler (limited by q_nominal)

        Parameters
        ----------
        control_signal : float
            input signal that defines desired thermal output in W

        Returns
        -------
        q_power_output : float
            Thermal power output in W
        """

        if control_signal < 0:
            warnings.warn('Control signal for boiler' + str(self) +
                          'is negative. Therefore, output is defined as zero.')
            control_signal = 0

        elif control_signal < self.lowerActivationLimit * self.qNominal:
            warnings.warn('Control signal for boiler' + str(self) +
                          'is below minimum part load performance. '
                          'Therefore, output is defined as zero.')
            control_signal = 0

        #  If desired output power is smaller or equal to nominal power,
        #  desired power can be provided
        if control_signal <= self.qNominal:
            q_power_output = control_signal
        else:  # Output is limited to nominal thermal power
            q_power_output = (self.qNominal)

        assert q_power_output >= 0, 'thermal power cannot be negative'

        return q_power_output

    def calc_boiler_fuel_power_input(self, control_signal):
        """
        Returns boiler fuel power input.

        Parameters
        ----------
        control_signal : float
            input signal that defines desired thermal output in W

        Returns
        -------
        fuel_power_input : float
            fuel power input in W
        """
        th_power = self.calc_boiler_thermal_power_output(control_signal)

        assert th_power >= 0, 'thermal power cannot be negative'

        fuel_power_input = (th_power / self.eta)

        return fuel_power_input

    def calc_b_fuel_power_in_w_th(self, thermal_power):
        """
        Returns boiler fuel power input.

        Parameters
        ----------
        thermal_power : float
            Thermal output power of boiler in W

        Returns
        -------
        fuel_power_input : float
            fuel power input in W
        """

        assert thermal_power >= 0, 'thermal power cannot be negative'
        assert thermal_power <= self.qNominal

        fuel_power_input = (thermal_power / self.eta)

        return fuel_power_input

    def calc_boiler_all_results(self, control_signal, time_index,
                                save_res=True):
        """
        Calculate and save results of boiler for next timestep
        (thermal power output and fuel power input)

        Parameters
        ----------
        control_signal : float
            input signal that defines desired thermal output in W
        time_index : int
            Number of timestep, which should be used for calculation and
            results saving (starting with 0 for first entry)
        save_res : bool, optional
            Defines, if results should be saved on boiler object instance
            (default: True)

        Returns
        -------
        results_tuple : tuple
            Tuple holding results (thermal power, fuel power)
        """

        #  Calculate thermal power output in W
        th_power = self.calc_boiler_thermal_power_output(control_signal)

        #  Calculate fuel power input in W
        fuel_power_in = self.calc_b_fuel_power_in_w_th(thermal_power=th_power)

        if save_res:
            #  Save results
            self.totalQOutput[time_index] = th_power
            self.array_fuel_power[time_index] = fuel_power_in

        return (th_power, fuel_power_in)
