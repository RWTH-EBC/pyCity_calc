#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example of chiller calculation class
"""

from __future__ import division

import numpy as np
import warnings
import pycity_base.classes.supply.absorptionchiller as achill


class AbsorptionChiller(achill.AbsorptionChiller):
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

        thermal_power_input: float [W]
        thermal load for current cooling load

        results_tuple : tuple
        tuple holding results (thermal power, thernal power)
        """
        self._kind = "kkm"

        self.q_nominal = q_nominal
        self.t_min = t_min
        self.lower_activation_limit = lower_activation_limit

        timesteps_total = environment.timer.timestepsTotal

        self.total_q_output = np.zeros(environment.timer.timestepsTotal)
        self.current_q_output = np.zeros(
            environment.timer.timestepsUsedHorizon)
        self.array_thermal_power = np.zeros(timesteps_total)
        self.array_th_heat_power = np.zeros(timesteps_total)

    def calc_q_thermal_power_output(self, cooling_load):
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

    def akm_cop(self, cooling_load):
        '''
        Calculation of the temporary COP-Load with the current part load
        ratio (plr)
        and the max cooling power of the AKM

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
        calculated cop value for AKM
        '''
        if cooling_load > 0:

            plr = cooling_load / self.q_nominal

            assert 0 <= plr <= 1, 'part load ratio has to be between 0 and 1'

            if plr >= self.lower_activation_limit:

                cop = (0.6709 * plr ** 3) - (1.5419 * plr ** 2) +\
                    (1.1928 * plr) + 0.4528

            elif plr <= self.lower_activation_limit:
                cop = 0
        else:
            cop = 0

        return cop

    def calc_th_heat_power_input(self, cooling_load):
        '''
        Calculates the thermal heat power input of AKM.

        Parameters
        ----------
        cooling_load : float [W]
        desired thermal output

        Returns
        -------
        th_heat_power_input: float [W]
        necessary thermal heat load for current cooling load
        '''
        q_th = self.calc_q_thermal_power_output(cooling_load)

        cop = self.akm_cop(cooling_load)

        assert q_th >= 0, 'thermal cooling power cannot be negative'

        assert q_th <= self.q_nominal, 'thermal cooling power cannot be ' +\
            'bigger than q_nominal'

        assert 0 <= cop <= 1, 'cop of single effect absorption chiller is ' +\
            'below 1'

        if q_th > 0:
            th_heat_power_input = q_th / cop

        else:
            th_heat_power_input = 0

        return th_heat_power_input

    def calc_akm_all_results(self, cooling_load, time_index,
                             save_res=True):
        """
        Calculate and save results of akm for next timestep
        (thermal cooling power output and thermal heat power input)

        Parameters
        ----------
        cooling_load : float [W]
        desired thermal output

        time_index : int
        number of timestep, which should be used for calculation and
        results saving (starting with 0 for first entry)

        save_res : bool, optional
        defines, if results should be saved on boiler object instance
        (default: True)

        Returns
        -------
        results_tuple : tuple
            Tuple holding results (thermal cooling power out, thermal heat
            power in)
        """

        #  Calculate thermal power output in W
        th_power = self.calc_q_thermal_power_output(cooling_load)

        #  Calculate elec power input in W
        th_heat_power_in = self.calc_th_heat_power_input(
            cooling_load=th_power,
            q_nominal=self.q_nominal)

        if save_res:
            #  Save results
            self.total_q_output[time_index] = th_power
            self.array_th_heat_power[time_index] = th_heat_power_in

        return (th_power, th_heat_power_in)
