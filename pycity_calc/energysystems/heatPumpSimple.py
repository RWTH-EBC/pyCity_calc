# coding=utf-8
"""
Simple heat Pump class, based on heating device of pycity
(not on heat pump class of pycity!)

"""
from __future__ import division

import numpy as np
import warnings
import pycity_base.classes.supply.HeatingDevice as heat
import pycity_calc.toolbox.unit_conversion as unitcon


class heatPumpSimple(heat.HeatingDevice):
    """
    Implementation of simple heat pump. COP is estimated via quality grade
    (Guetegrad) and Carnot COP.
    """

    def __init__(self, environment, q_nominal, t_max=55.0,
                 lower_activation_limit=0.5, hp_type='aw',
                 t_sink=45.0):
        """
        Parameters
        ----------
        environment : Extended environment object
            Common to all other objects. Includes time and weather instances
        q_nominal : float
            Nominal heat output in Watt
        t_max : float, optional
            Maximum provided temperature in °C
            (default : 85 °C)
        lower_activation_limit : float, optional
            Define the lower activation limit (Default: 1). For example, heat
            pumps are
            typically able to operate between 50 % part load and rated load.
            In this case, lower_activation_limit would be 0.5
            Two special cases:
            Linear behavior: lower_activation_limit = 0
            Two-point controlled: lower_activation_limit = 1
            Range:(0 <= lower_activation_limit <= 1)
            (Default : 0.5)
        hp_type : str, optional
            Type of heat pump
            Options:
            'aw': Air/water (air temperature is taken from function call)
            'ww': Water/water (water temperature is taken from
            environment.temp_ground)
            (default : 'aw')
        t_sink : float, optional
            Temperature of heat sink in °C
            (default : 45 °C)


        Attributes
        ----------
        quality_grade : float
            Estimation for quality grad of different hp Types
            Options:
            0.36: for air water hp
            0.5. for water water hp

        Annotations
        -----------
        COP is estimated with quality grade (Guetegrad) and max. possible COP.

        COP is limited to value of 5.

        Heat sink temperature is defined as input parameter.
        If building object with variable indoor temperature is
        given, heat pump should be modified to get indoor temperature per
        function call.
        """

        # super Class
        super(heatPumpSimple, self).__init__(environment=environment,
                                             qNominal=q_nominal,
                                             tMax=t_max,
                                             lowerActivationLimit=
                                             lower_activation_limit)
        # further attributes
        self._kind = "heatpump"
        self.hp_type = hp_type

        assert t_sink <= t_max, ('Temperature of heat sink cannot be ' +
                                 ' higher than max. output temperature.')
        self.t_sink = t_sink

        #  TODO: Add reference for quality grades (Guetegrade)
        if hp_type == 'aw':
            self.quality_grade = 0.36  # Estimation of quality grade (Guetegrad)
        elif hp_type == 'ww':
            self.quality_grade = 0.5  # Estimation of quality grade (Guetegrad)
        else:
            warnings.warn(
                'Unkown type of heat pump. Cannot define quality grade.')
            self.quality_grade = None

        timesteps_total = environment.timer.timestepsTotal
        self.array_el_power_in = np.zeros(timesteps_total)

    def calc_hp_carnot_cop(self, temp_source):
        """
        Returns maximal possible COP based on carnot efficiency

        Parameters
        ----------
        temp_source : float
            Temperature of heatsource in °C

        Returns
        ------
        cop_max : float
            (Theoretical,) maximal possible COP of heat pump (without unit)
        """

        assert unitcon.con_celsius_to_kelvin(temp_source) > 0
        assert temp_source < self.t_sink, ('the temperature of the heat ' +
                                          'source must be below the ' +
                                          'temperature of the heat sink. ' +
                                          'Check your System')

        cop_max = unitcon.con_celsius_to_kelvin(self.t_sink) / (
        self.t_sink - temp_source)

        return cop_max

    def calc_hp_cop_with_quality_grade(self, temp_source):
        """
        Returns estimation of COP based on heatpump type (quality grade)
        and max. possible COP.
        Maximal allowed COP values is 5.

        Parameters
        ----------
        temp_source : float
            Temperature of heatsource in °C

        Returns
        ------
        cop : float
            Heatpump coefficient of performance (no unit)
            max 5
        """

        assert unitcon.con_celsius_to_kelvin(temp_source) > 0

        if temp_source >= self.t_sink:
            return 5

        # Get maximal possible COP
        cop_max = self.calc_hp_carnot_cop(temp_source=temp_source)

        #  Estimate COP with quality grade (Guetegrad)
        cop = self.quality_grade * cop_max

        #  If COP is larger than 5, COP is set to 5
        if cop > 5:
            cop = 5

        return cop

    def calc_hp_th_power_output(self, control_signal):
        """
        Returns heatpump thermal power output in Watt

        Parameters
        ----------
        control_signal : float
            Input signal that defines desired thermal output in W

        Returns
        ------
        q_power_output : float
            Thermal power output in W
        """
        if control_signal < 0:
            warnings.warn(
                'Control signal for heatpump' + str(
                self) + 'is negative. Therefore, output is defined as zero.')
            control_signal = 0
        elif (control_signal < self.lowerActivationLimit * self.qNominal
              and control_signal !=0):
            warnings.warn('Control signal for heatpump' + str(
                self) + 'is below minimum part load performance. '
                        'Therefore, output is defined as zero.')
            control_signal = 0

        #  If desired output power is smaller or equal to nominal power,
        #  desired power can be provided
        if control_signal <= self.qNominal:
            q_power_output = control_signal
        else:  # Output is limited to nominal thermal power
            q_power_output = self.qNominal

        return q_power_output

    def calc_hp_el_power_input(self, control_signal, t_source):
        """
        Returns electric power input of heat pump, depending on the required
        thermal output and given temperature. If Heat Pump type is air-water
        the cop is calculated with the given temperature as t_Ambient,
        otherwise environment.temp_ground is used

        Parameters
        ----------
        control_signal : float
            Input signal that defines desired thermal output in W
        t_source : float
            Temperature of heatsource in °C
            t_source is used for the calculation of the air-water hp,
            for water-water hp environment.temp_ground is used
        Returns
        ------
        p_el_in : float
            Electrical power input in W
        """
        # estimate thermal_output
        q_power_output = self.calc_hp_th_power_output(control_signal)

        if q_power_output > 0:

            #  Estimate COP with quality grade
            cop = self.calc_hp_cop_with_quality_grade(t_source)

            # Calculate electrical power
            p_el_in = q_power_output / cop

        else:
            p_el_in = 0.0

        return p_el_in

    def calc_hp_all_results(self, control_signal, t_source, time_index,
                            save_res=True):
        """
        Calculate and save all results of heat pump
        (thermal power output, electrical power input)

        Parameters
        ----------
        control_signal : float
            Desired thermal power output in W
        t_source : float
            Source temperature in °C
        time_index : int
            Number of timestep (relevant for saving results)
        save_res : bool, optional
            Defines, if results should be saved on hp object instance
            (default: True)

        Returns
        -------
        results_tuple : tuple
            Tuple with results (thermal power output, electrical power input)
        """

        #  Calculate thermal power output
        th_power_out = self.calc_hp_th_power_output(control_signal)

        #  Calculate electrical power input
        el_power_in = self.calc_hp_el_power_input(th_power_out, t_source)

        if save_res:
            #  Save results
            self.totalQOutput[time_index] = th_power_out
            self.array_el_power_in[time_index] = el_power_in

        return (th_power_out, el_power_in)
