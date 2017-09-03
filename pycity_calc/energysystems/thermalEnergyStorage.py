#!/usr/bin/env python
# coding=utf-8
"""
Extended thermal energy storage class (based on battery object of pycity)
"""
from __future__ import division

import math
import numpy as np

import pycity_base.classes.supply.ThermalEnergyStorage as TES
import pycity_calc.toolbox.unit_conversion as unitcon


class thermalEnergyStorageExtended(TES.ThermalEnergyStorage):
    """
    thermalEnergyStorageExtended (inheritance from pycity ThermalEnergyStorage
    Class)
    """

    def __init__(self, environment, t_init, capacity, c_p=4186, rho=1000,
                 t_max=80.0, t_min=20.0,
                 t_surroundings=20.0, k_loss=0.3, h_d_ratio=3.5,
                 use_outside_temp=False):
        """
        Construcotr of extended thermal storage system

        Parameters
        ----------
        environment : Extended environment object
            Common to all other objects. Includes time and weather instances
        t_init : float
            initialization temperature in °C
        capacity : float
            storage mass in kg
        c_p : float, optional
            Specific heat capacity of storage medium in J/(kg*K)
             (default: 4186 J/(kg*K) <-> water)
        rho : float, optional
            Density of storage medium in kg/m^3
            (default: 1000 kg/m^3 <-> water)
        t_max : float, optional
            Maximum storage temperature in °C
            (default: 80 °C)
        t_min : float, optional
            Minimal storage temperature in °C
            (default: 20 °C)
        t_surroundings : float, optional
            temperature of the storage's surroundings in °C
            (default: 20 °C)
        k_loss : float, optional
            Loss factor of storage in W/(m^2*K)
             (default: 0.3 W/(m^2*K))
             Reference:
        h_d_ratio : float, optional
            Ratio between storage height and diameter (assumes cylindrical
            storage form)
            (Default: 3.5)
        use_outside_temp : bool, optional
            Boolean to define, if outside temperature of environment should be
            used to calculate
            heat losses
            False: Use t_surroundings (input parameter of Thermalenergystorage)
            True: Use t_outside of environment object
            (default: False)

        Annotation
        ----------
        Thermal storage system does not have internal control system.
        If temperature limits are exceeded, an assertionError is raised.

        Default value for k_loss has been estimated with datascheet of buderus
        Logalux SMS 290/5E
        https://productsde.buderus.com/buderus/productsat.buderus.com/broschuren-buderus.at/broschuren-alt/speicher/speicher-prospekt-logalux.pdf
        h=1,835 m; V=290 L; delta T = 65 - 20 K; Q_dot_loss = 2,07 kWh / 24 h

        h/d - ratio is also estimated with buderus datascheet

        Attributes
        ----------
        t_current : float
            the current temperature of the extended thermal energy storage unit
            initialized with t_init
        """

        assert t_init <= t_max, ('Initial temperature should not exceed ' +
                                 'maximum temperature')
        assert t_init >= t_min, ('Initial temperature should not go below ' +
                                 'minimum temperature')

        assert capacity > 0, 'Capacity must be larger than zero'
        assert c_p > 0, 'heat capacity must be larger than zero'
        assert rho > 0, 'Density must be larger than zero'
        assert t_surroundings > -273.15, 'Surrounding temp is too low!'
        assert t_max > -273.15, 'Max. temperature is too low!'
        assert k_loss >= 0, 'loss factor cannot be below zero'
        assert h_d_ratio > 0, ('Ratio between storage height and diameter ' +
                               'must be larger than zero')
        assert t_init > -273.15, 'Init. temperature is too low!'

        # initialize super class
        super(thermalEnergyStorageExtended, self).__init__(
            environment=environment,
            tInit=t_init,
            capacity=capacity,
            tMax=t_max,
            tSurroundings=t_surroundings,
            kLosses=k_loss)

        self.c_p = c_p
        self.rho = rho
        self.t_min = t_min
        self.k_loss = k_loss
        self.h_d_ratio = h_d_ratio
        self.use_outside_temp = use_outside_temp

        #  t_current can be changed when method calc_storage_temp_for_next_
        #  timestep is used
        self.t_current = t_init  # initialized with t_init

        #  If outside temperature should not be used, use t_surroundings
        if not use_outside_temp:
            self.t_surroundings = t_surroundings
        # Otherwise: use outside temperature of environment
        else:
            self.t_surroundings = None

        timesteps_total = environment.timer.timestepsTotal

        self.array_temp_storage = np.zeros(timesteps_total)
        self.array_q_charge = np.zeros(timesteps_total)
        self.array_q_discharge = np.zeros(timesteps_total)

    def calc_storage_volume(self):
        """
        Returns storage volume.

        Returns
        ------
        v_storage : float
            Storage volume in m^3
        """
        v_storage = self.capacity / self.rho
        return v_storage

    def calc_storage_diameter(self):
        """
        Returns (cylindrical) storage diameter

        Returns
        ------
        d_storage : float
            Diameter of (cylindrical) storage in m

        Notes
        -----
        The diameter is calculated with the following formula:
        .. math::
            d_{storage} = \sqrt[3]{\frac{4 \cdot V}{\pi \cdot hdRatio}}
        """
        volume = self.calc_storage_volume()
        d_storage = (4 * volume / (math.pi * self.h_d_ratio)) ** (1 / 3)
        return d_storage

    def calc_storage_height(self):
        """
        Returns storage height

        Returns
        ------
        h_storage : float
            Height of (cylindrical) storage in m
        """
        d = self.calc_storage_diameter()
        h_storage = d * self.h_d_ratio
        return h_storage

    def calc_storage_outside_area(self):
        """
        Returns outside storage area

        Returns
        ------
        area_storage : float
            Surface area of storage in m^2
        """
        d = self.calc_storage_diameter()
        h = self.calc_storage_height()
        area_storage = 2 * math.pi * (d / 2) ** 2 + 2 * math.pi * (d / 2) * h
        return area_storage

    def calc_storage_temp_for_next_timestep(self, q_in, q_out, t_prior,
                                            t_ambient=None,
                                            set_new_temperature=True,
                                            save_res=False, time_index=None):
        """
        Calculates new storage temperature with given outside temperature of
        environment. Function is also necessary if user wants to charge or
        discharge storage system.

        Parameters
        ----------
        q_in : float
            Thermal power input in Watt (Charging of storage)
        q_out : float
            Thermal power output in Watt (Discharging of storage)
        t_prior : float
            Prior temperature in °C
        t_ambient : float, optional
            Outside temperature in °C
            (default: None). If no surrounding temperature is given, User
            has to define t_ambient
        set_new_temperature : bool, optional
            Boolean to define, if new calculated temperature value should be
            set as new internal temperature value.
            True: Set t_next as t_current
            False: Only return t_next, do NOT change t_current
            (default: True)
        save_res : bool, optional
            Defines if results should be saved (default: False)
        time_index : int, optional
            Number of timestep (default: None). Necessary if results should
            be saved

        Returns
        ------
        t_next : float
            Next storage temperature in °C

        Raises
        ------
        assertionError
            If temperature limits are exceeded (below minimum temperature or
             maximum temperature

        Notes
        -----
        The next temperature within the storage is calculated with the
        following formula:
        .. math::
            T_{next} = T_{prior} + \Delta T
                     = T_{prior} + (\dot{Q}_{in} - \dot{Q}_{out} - k \cdot A \cdot (T - T_{U})) \cdot t
        """

        # check if charging or discharging is possible
        assert q_out <= self.calc_storage_q_out_max(t_ambient=t_ambient,
                                                    q_in=q_in), 'Discharging is not possible'
        assert q_in <= self.calc_storage_q_in_max(t_ambient=t_ambient,
                                                  q_out=q_out), 'Charging is not possible'

        #  If environment outside temp should be used
        if self.use_outside_temp:
            assert t_ambient > -273.15  # °C
            t_u = t_ambient
        else:  # Use given temperature t_surroundings in Kelvin
            t_u = self.tSurroundings  # in °C

        area = self.calc_storage_outside_area()

        #  Calculate change of temperature with simplified energy balance
        delta_t = (1 / (self.capacity * self.c_p)) * (
            q_in - q_out - self.k_loss * area * (t_prior - t_u)) \
                  * self.environment.timer.timeDiscretization

        #  Calculate next temperature with temperature difference
        t_next = t_prior + delta_t  # in °C

        #  Check if t_next is within temperature limits
        assert t_next >= self.t_min, ('Temperature should not go below ' +
                                      'minimum temperature. Check your ' +
                                      'control system.')
        assert t_next <= self.tMax, ('Temperature should not go above ' +
                                     'maximal temperature. Check your ' +
                                     'control system.')

        #  Save t_next as new internal temperature value
        if set_new_temperature:
            self.t_current = t_next  # in °C

        if save_res:
            #  Save results
            self.array_temp_storage[time_index] = t_next
            self.array_q_charge[time_index] = q_in
            self.array_q_discharge[time_index] = q_out

        return t_next

    def calc_storage_curr_amount_of_energy(self):
        """
        Calculates current amount of stored energy within thermal storage.

        Returns
        ------
        tes_energy : float
            Amount of stored energy within thermal storage in kWh
        """
        #  tes_energy = self.capacity * self.c_p * (temp - self.t_min)
        tes_energy_joule = self.capacity * self.c_p * (
            self.t_current - self.t_min)  # Energy in Joule
        tes_energy = unitcon.con_joule_to_kwh(
            tes_energy_joule)  # Convert J (Ws) to kWh

        return tes_energy

    def calc_storage_max_amount_of_energy(self):
        """
        Returns maximum amount of storable energy within thermal storage.

        Returns
        -------
        max_energy : float
            Maximum amount of stored energy within thermal storage in kWh
        """

        max_energy_joule = self.capacity * self.c_p * (
            self.tMax - self.t_min)  # Energy in Joule
        max_energy = unitcon.con_joule_to_kwh(
            max_energy_joule)  # Convert J (Ws) to kWh

        return max_energy

    def calc_curr_state_of_charge(self):
        """
        Returns relative state of charge (factor of current stored amount of
        energy related to maximum possible amount of energy, e.g. 0.6 means
        60 % state of charge)

        Returns
        -------
        soc : float
            Current state of charge
        """
        curr_energy = self.calc_storage_curr_amount_of_energy()
        max_energy = self.calc_storage_max_amount_of_energy()

        return curr_energy / max_energy

    def calc_storage_q_out_max(self, t_ambient=None, q_in=0, eps=0.1):
        """
        Returns maximum thermal discharging power over next timestep
        (without going below reference temperature)

        Parameters
        ----------
        t_ambient : float, optional
            Outside temperature in °C (default: None)
            if self.use_outside_temp is False, tSurroundings is taken
            and no value for t_ambient is required
        q_in : float, optional
            Thermal input power in W
            (default: 0 W)
        eps : float, optional
            Tolerance value in Watt (default: 0.1). Tolerance is subtracted
            from q_out_max. In case of negative values, q_out_max is re-set
            to 0.

        Returns
        ------
        q_out_max : float
            Maximal thermal discharging power in W
        """
        #  Calculate storage surface area
        area = self.calc_storage_outside_area()

        #  Get surrounding temperature (for loss calculation)
        if self.use_outside_temp:
            assert t_ambient is not None
            assert t_ambient > -273.15  # °C
            t_u = t_ambient  # Get outside temperature from funtion call, in °C
        else:  # Use given temperature t_surroundings in Kelvin
            t_u = self.tSurroundings  # in °C

        # Calculate currently stored amount of energy (in kWh)
        tes_energy = self.calc_storage_curr_amount_of_energy()

        q_out_max = q_in - self.k_loss * area * (
            self.t_current - t_u) + unitcon.con_kwh_to_joule(tes_energy) \
                                    / self.environment.timer.timeDiscretization

        q_out_max -= eps

        if q_out_max < 0:
            q_out_max = 0

        return q_out_max

    def calc_storage_q_in_max(self, t_ambient=None, q_out=0, eps=0.1):
        """
        Returns maximum thermal charging power over next time step
        (without going above maximal temperature)

        Parameters
        ----------
        t_ambient : float, optional
            Outside temperature in °C (default: None)
            if self.use_outside_temp is False, tSurroundings is taken
            and no value for t_ambient is required
        q_out : float, optional
            Thermal input power in W
            (default: 0 W)
        eps : float, optional
            Tolerance value in Watt (default: 0.1). Tolerance is subtracted
            from q_in_max. In case of negative values, q_in_max is re-set
            to 0.

        Returns
        ------
        q_in_max : float
            Maximal thermal charging power in W
        """

        #  Calculate storage surface area
        area = self.calc_storage_outside_area()

        #  Get surrounding temperature (for loss calculation)
        if self.use_outside_temp:
            assert t_ambient is not None
            assert t_ambient > -273.15  # °C
            t_u = t_ambient  # Get outside temperature from funtion call, in °C
        else:  # Use given temperature t_surroundings in Kelvin
            t_u = self.tSurroundings

        # Calculate currently stored amount of energy (in kWh)
        tes_energy = self.calc_storage_curr_amount_of_energy()

        q_in_max = q_out + self.k_loss * area * (self.t_current - t_u) + \
                   (self.capacity * self.c_p * (
                       self.tMax - self.t_min) - unitcon.con_kwh_to_joule(
                       tes_energy)) \
                   / self.environment.timer.timeDiscretization

        q_in_max -= eps

        if q_in_max < 0:
            q_in_max = 0

        return q_in_max

    def storage_q_out_possible(self, control_signal, t_ambient, q_in=0):
        """
        Returns boolean to define, if desired discharging power over next
        time step is possible

        Parameters
        ----------
        control_signal : float
            Desired thermal discharging power in W
        t_ambient : float
            Outside temperature in °C
        q_in : float, optional
            Thermal input power in W
            (default: 0 W)

        Returns
        ------
        q_out_possible : bool
            Boolean to define, if desired discharging power output is possible
            True: Discharging is possible (enough energy left)
            False: Discharging NOT possible (would go below minimum temperature)
        """

        q_out_max = self.calc_storage_q_out_max(q_in=q_in, t_ambient=t_ambient)

        if control_signal <= q_out_max:
            q_out_possible = True
        else:
            q_out_possible = False

        return q_out_possible

    def storage_q_in_possible(self, control_signal, t_ambient, q_out=0):
        """
        Returns boolean to define, if desired charging power over next time
        step is possible

        Parameters
        ----------
        t_ambient : float
            Outside temperature in °C
        control_signal : float
            Desired thermal charging power in W
        q_out : float, optional
            Thermal output power in W
             (default: 0 W)

        Returns
        ------
        q_in_possible : bool
            Boolean to define, if desired discharging power output is possible
            True: Discharging is possible (enough energy left)
            False: Discharging NOT possible (would go below minimum temperature)
        """
        q_in_max = self.calc_storage_q_in_max(q_out=q_out, t_ambient=t_ambient)

        if control_signal <= q_in_max:
            q_in_possible = True
        else:
            q_in_possible = False

        return q_in_possible
