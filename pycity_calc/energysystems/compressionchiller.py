#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example of chiller calculation class
"""

from __future__ import division

import numpy as np
import warnings
import pycity_base.classes.supply.compressionchiller as chill


class CompressionChiller(chill.CompressionChiller):
    """
    Implementation of simple Chiller. Values are based on regeressions for
    chillers based on fixme.
    As a first reference i'll use the bachelor thesis of Hardy Lottermann
    """

    def __init__(self,
                 environment,
                 q_nominal,
                 t_min=4,
                 lower_activation_limit=0.2):
        """

        Constructor of the chiller calculation class

        Parameters
        ----------
        environment : Extended environment object
        Common to all other objects. Includes time and weather instances

        q_nominal: float [W]
        max cooling load of chiller

        lower_activation_limit : float , optional
        (0 <= lowerActivationLimit <= 1)
        Define the lower activation limit. For example, centrifugal chillers
        are
        typically able to operate between 20 % part load and rated load.
        In this case, lowerActivationLimit would be 0.2

        Attributes:
        -----------
        cooling_load : float [W]
        hourly value of measured cooling load

        plr : float
        value of calculated part load ratio

        Returns:
        ----------
        q_th_output : float [W]
        thermal output power of KKM

        cop : float
        calculated cop value for KKM

        elec_power_input: float [W]
        electric load for current cooling load

        results_tuple : tuple
        tuple holding results (thermal power, elec power)
        """
        self._kind = "kkm"

        self.q_nominal = q_nominal
        self.t_min = t_min
        self.lower_activation_limit = lower_activation_limit

        timesteps_total = environment.timer.timestepsTotal

        self.total_q_output = np.zeros(environment.timer.timestepsTotal)
        self.current_q_output = np.zeros(
            environment.timer.timestepsUsedHorizon)
        self.array_elec_power = np.zeros(timesteps_total)
        self.array_th_heat_power = np.zeros(timesteps_total)

    def calc_q_th_power_output(self, cooling_load):
        """
        Returns thermal power output of KKM (limited by q_nominal)

        Parameters
        ----------
        cooling_load : float [W]
        Desired thermal output

        Returns
        -------
        q_th_output : float [W]
        Thermal output power of KKM
        """

        if cooling_load < 0:
            warnings.warn('Cooling load for KKM' + str(self) +
                          'is negative. Therefore, output is defined as zero.')
            cooling_load = 0

        elif cooling_load < self.lower_activation_limit * self.q_nominal:
            warnings.warn('Cooling load for KKM' + str(self) +
                          'is below minimum part load performance. '
                          'Therefore, output is defined as zero.')
            cooling_load = 0

        #  If desired output power is smaller or equal to nominal power,
        #  desired power can be provided
        if cooling_load <= self.q_nominal:
            q_th_output = cooling_load
        # Output is limited to nominal thermal power
        else:
            q_th_output = (self.q_nominal)

        assert q_th_output >= 0, 'thermal power cannot be negative'

        return q_th_output

    def kkm_cop(self, cooling_load):
        '''
        Calculation of the temporary COP-Load with the current part load
        ratio (plr)
        and the max cooling power of the KKM

        Parameters
        ----------
        cooling_load : float [W]
        desired thermal output


        Attributes
        ----------
        plr: float
        value of calculated part load ratio

        Returns
        -------
        cop : float
        calculated cop value for KKM
        '''
        if cooling_load > 0:

            plr = cooling_load / self.q_nominal

            assert 0 <= plr <= 1, 'part load ratio has to be between 0 and 1'

            if plr >= self.lower_activation_limit:

                if self.q_nominal <= 1750000:
                    cop = ((-4.4917) * plr ** 2) + (8.1083 * plr) + 2.01

                elif self.q_nominal > 1750000:
                    cop = (-7.66 * plr ** 2) + (11.169 * plr) + 1.8454

            elif plr <= self.lower_activation_limit:
                cop = 0
        else:
            cop = 0

        return cop

    def calc_elec_power_input(self, cooling_load):
        '''
        Calculates the elcetric power input of KKM.

        Parameters
        ----------
        cooling_load : float [W]
        desired thermal output

        Returns
        -------
        elec_power_input: float [W]
        electric load for current cooling load
        '''
        q_th = self.calc_q_th_power_output(cooling_load)

        cop = self.kkm_cop(cooling_load)

        assert q_th >= 0, 'thermal cooling power cannot be negative'

        assert q_th <= self.q_nominal, 'thermal power cannot be bigger ' +\
            'than q_nominal'

        assert 0 <= cop <= 7, 'cop of fixed speed centrifugal chiller ' +\
            'is below 7'

        if q_th > 0:
            elec_power_input = q_th / cop

        else:
            elec_power_input = 0

        return elec_power_input

    def calc_kkm_all_results(self, cooling_load, time_index,
                             save_res=True):
        """
        Calculate and save results of kkm for next timestep
        (thermal cooling power output and elec power input)

        Parameters
        ----------
        cooling_load : float [W]
        desired thermal output

        time_index : int
        number of timestep, which should be used for calculation and
        results saving (starting with 0 for first entry)

        save_res : bool, optional
        defines, if results should be saved on kkm object instance
        (default: True)

        Returns
        -------
        results_tuple : tuple
            Tuple holding results (thermal power, elec power)
        """

        #  Calculate thermal power output in W
        th_power = self.calc_q_th_power_output(cooling_load)

        #  Calculate elec power input in W
        elec_power_in = self.calc_elec_power_input(cooling_load=th_power)

        if save_res:
            #  Save results
            self.total_q_output[time_index] = th_power
            self.array_elec_power[time_index] = elec_power_in

        return (th_power, elec_power_in)
