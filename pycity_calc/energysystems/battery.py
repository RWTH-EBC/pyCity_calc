#!/usr/bin/env python
# coding=utf-8
"""
Extended electric battery class (based on battery object of pycity)
"""
from __future__ import division
import warnings

import pycity_base.classes.supply.Battery as Batt
import pycity_calc.toolbox.unit_conversion as unitcon


class BatteryExtended(Batt.Battery):
    """
    BatteryExtended class (inheritance from pycity Battery class)
    """

    def __init__(self, environment, soc_init_ratio, capacity_kwh,
                 self_discharge=0.01, eta_charge=0.95, eta_discharge=0.9):
        """
        Parameters
        ----------
        environment : Extended environment object
            Common to all other objects. Includes time and weather instances
        soc_init_ratio : float
            Initial state of charge (relative to capacity) (no unit)
            (0 <= soc_init_ratio <= 1)
        capacity_kwh : float
            Battery's capacity in kWh
        self_discharge : float
            Rate of self discharge per time step (without unit)
            (default: 0.01)
            (0 <= self_discharge <= 1)
        eta_charge : float
            Charging efficiency (without unit)
            (default: 0.95)
            (0 <= eta_charge <= 1)
        eta_discharge : float
            Discharging efficiency (without unit)
            (default: 0.9)
            (0 <= eta_discharge <= 1)

        Attributes
        ----------
        soc_ratio_current : float
            Current state of charge (relative to capacity) (no unit)
            (0 <= soc_init_ratio <= 1)

        Annotations
        -----------
        Be aware, that the choice of timestep has a major impact on the
        battery losses (when the charging and discharging efficiencies are
        kept constant for different timesteps)! If necessary, recalculate
        self_discharge, eta_charge and eta_discharge.

        Furthermore, attribute self.capacity is saved with Joule as unit!
        Input capacity in kWh is automatically recalculated!
        """

        #  Assert functions
        assert soc_init_ratio >= 0, ('Initial state of charge of battery' +
                                     ' cannot be negative!')
        assert soc_init_ratio <= 1, ('Initial state of charge of battery' +
                                     'cannot be higher than nominal capacity!')
        assert capacity_kwh > 0, ('Capacity of battery cannot be equal or' +
                                  ' below zero!')
        assert self_discharge >= 0, ('Self discharge rate of battery cannot' +
                                     ' be negative!')
        assert self_discharge <= 1, ('Self discharge rate of battery cannot' +
                                     ' be larger than one!')
        assert eta_charge >= 0, ('Charging efficiency of battery cannot be' +
                                 ' negative!')
        assert eta_charge <= 1, ('Charging efficiency of battery cannot be ' +
                                 'larger than one!')
        assert eta_discharge >= 0, ('Discharging efficiency of battery ' +
                                    'cannot be negative!')
        assert eta_discharge <= 1, ('Discharging efficiency of battery ' +
                                    'cannot be larger than one!')

        #  Convert soc_init_ratio to socInit in Joule
        soc_init = unitcon.con_kwh_to_joule(soc_init_ratio * capacity_kwh)

        #  Convert capacity from kWh to Joule
        cap = unitcon.con_kwh_to_joule(capacity_kwh)

        # Initialize superclass
        super(BatteryExtended, self).__init__(environment, socInit=soc_init,
                                              capacity=cap,
                                              selfDischarge=self_discharge,
                                              etaCharge=eta_charge,
                                              etaDischarge=eta_discharge)

        #  Further attribute
        self.soc_ratio_current = soc_init_ratio  # Current SOC ratio

    def get_battery_capacity_in_kwh(self):
        """
        Returns maximum battery capacity in kwh.

        Returns
        -------
        capacity_kwh : float
            capacity of the extended battery in kWh
        """
        #  Convert self.capacity value (in Joule) to kWh value
        capacity_kwh = unitcon.con_joule_to_kwh(self.capacity)
        return capacity_kwh

    def calc_battery_soc_next_timestep(self, p_el_in, p_el_out,
                                       soc_ratio_current=None,
                                       set_new_soc=True, save_res=False,
                                       time_index=None):
        """
        Returns battery state of charge for next timestep

        Parameters
        ----------
        p_el_in : float
            Electric charging power in W
        p_el_out : float
            Electric discharging power in W
        soc_ratio_current : float, optional
            Current SOC share (relative to capacity) (no unit)
            (0 <= soc_init_ratio <= 1)
            (default : None) the current soc_ratio_current ratio from the
            ExtendedBattery is used
        set_new_soc : bool
            Boolean to define, if new state of charge should be saved
            within battery (default: True)
            True: Save new state of charge as soc_current
            False: Do NOT save new state of charge in battery object,
            only hand out value
        save_res : bool, optional
            Defines, if results should be saved (default: False)
        time_index : int, optional
            Number of timestep, which should be used to save results

        Returns
        ------
        soc_ratio_next : float
            State of charge ratio at next timestep (without unit)
            (0 <= eta_charge <= 1)
        """
        assert p_el_in >= 0
        assert p_el_out >= 0

        #  if soc_ratio_current is None soc_ratio_current is used from
        #  Extended Battery object
        if soc_ratio_current is None:
            soc_ratio_current = self.soc_ratio_current


        #  Energy balance with P_in * timestep - P_out * timestep (in Ws)
        #  org state of charge (in Joule) minus discharging
        soc_next_joule = (self.etaCharge * p_el_in - p_el_out /
                          self.etaDischarge) * \
                         self.environment.timer.timeDiscretization \
                         + soc_ratio_current * self.capacity \
                           * (1 - self.selfDischarge)

        #  Normalize
        soc_ratio_next = soc_next_joule / self.capacity

        #  Check if new state of charge is below zero
        assert soc_ratio_next >= 0, ('New state of charge cannot be below'
                                     ' zero. Check your control system.')
        assert soc_ratio_next <= 1, ('New state of charge cannot'
                                     ' be above maximal capacity.')

        #  If new state of charge should be saved within battery
        if set_new_soc:
            #  Set current soc share to next soc share
            self.soc_ratio_current = soc_ratio_next

        if save_res:
            if time_index is not None:
                #  Save results (use attributes of pycity battery object)
                self.totalSoc[time_index] = self.capacity * soc_ratio_next
                self.totalPCharge[time_index] = p_el_in
                self.totalPDischarge[time_index] = p_el_out
            else:
                warnings.warn('time_index is None. Thus, cannot save ' +
                              'battery results')

        return soc_ratio_next

    def calc_battery_max_p_el_out(self, soc_ratio_current=None, p_el_in=0,
                                  eps=0.1):
        """
        Function calculates maximal discharging power possible (over timestep)
        without reaching negative state of charge.

        Parameters
        ----------
         soc_ratio_current : float, optional
            Current SOC share (relative to capacity) (no unit)
            (0 <= soc_init_ratio <= 1)
            (default : None) the current soc_ratio_current ratio from the
            ExtendedBattery is used
         p_el_in : float, optional
            input power at same timestep in W (default: 0)
        eps : float, optional
            Tolerance value in Watt (default: 0.1). Tolerance is subtracted
            from q_in_max. In case of negative values, q_in_max is re-set
            to 0.

        Returns
        ------
        p_el_out_max : float
            Maximum possible discharging power over next timestep in W
        """
        #  if soc_ratio_current is None soc_ratio_current is used from
        #  Extended Battery object
        assert p_el_in >= 0, "No negative charging possible!"
        if soc_ratio_current is None:
            soc_ratio_current = self.soc_ratio_current
        else:
            pass

        p_el_out_max = \
            self.etaDischarge * (self.etaCharge * p_el_in +
                                (
                                1 - self.selfDischarge) * soc_ratio_current *
                                self.capacity / self.environment.timer.timeDiscretization)

        p_el_out_max -= eps

        if p_el_out_max < 0:
            p_el_out_max = 0

        assert p_el_out_max >= 0
        return p_el_out_max

    def battery_discharge_possible(self, p_el_out, soc_ratio_current=None,
                                   p_el_in=0):
        """
        Returns boolean to define, if desired electrical power output
        (over timestep) is possible.

        Parameters
        ----------
        p_el_out : float
            Desired electrical dischargin power in W
        soc_ratio_current : float, optional
            Current SOC share (relative to capacity) (no unit)
            (0 <= soc_init_ratio <= 1)
            (default : None) the current soc_ratio_current ratio from the
            ExtendedBattery is used
         p_el_in : float, optional
            input power at same timestep in W (default: 0)

        Returns
        ------
        discharge_possible : bool
            Boolean to define, if discharging with desired output power
            is possible
            True: Discharging possible (enough energy left)
            False: Discharging not possible (would go below zero capacity)
        """
        assert p_el_out >= 0
        assert p_el_in >= 0

        # if soc_ratio_current is None soc_ratio_current is used from
        #  Extended Battery object
        if soc_ratio_current is None:
            soc_ratio_current = self.soc_ratio_current
        else:
            pass

        p_el_out_max = self.calc_battery_max_p_el_out(soc_ratio_current=
                                                      soc_ratio_current,
                                                      p_el_in=p_el_in)
        if p_el_out_max >= p_el_out:
            discharge_possible = True
        else:
            discharge_possible = False
        return discharge_possible

    def calc_battery_max_p_el_in(self, soc_ratio_current=None, p_el_out=0,
                                 eps=0.1):
        """
        Function calculates maximal charging power possible (over timestep)
        without going above nominal capacity of battery.

        Parameters
        ----------
        soc_ratio_current : float, optional
            Current SOC share (relative to capacity) (no unit)
            (0 <= soc_init_ratio <= 1)
            (default : None) the current soc_ratio_current ratio from the
            ExtendedBattery is used
        p_el_out : float, optional
            Output power at same timestep in W (default: 0)
        eps : float, optional
            Tolerance value in Watt (default: 0.1). Tolerance is subtracted
            from q_in_max. In case of negative values, q_in_max is re-set
            to 0.

        Returns
        ------
        p_el_in_max : float
            Maximum possible discharging power over next timestep in W
        """
        assert p_el_out >= 0

        # if soc_ratio_current is None soc_ratio_current is used from
        # Extended Battery object
        if soc_ratio_current is None:
            soc_ratio_current = self.soc_ratio_current
        else:
            pass

        p_el_in_max = 1 / self.etaCharge * (self.capacity /
                                            self.environment.timer.timeDiscretization +
                                            p_el_out / self.etaDischarge -
                                            (1 - self.selfDischarge) *
                                            soc_ratio_current * self.capacity /
                                            self.environment.timer.timeDiscretization)

        p_el_in_max -= eps

        if p_el_in_max < 0:
            p_el_in_max = 0

        assert p_el_in_max >= 0
        return p_el_in_max

    def battery_charge_possible(self, p_el_in, soc_ratio_current=None,
                                p_el_out=0):
        """
        Returns boolean to define, if desired electrical power input
        (over timestep) is possible.

        Parameters
        ----------
        p_el_in : float
            Desired electrical charging power in W
         soc_ratio_current : float, optional
            Current SOC share (relative to capacity) (no unit)
            (0 <= soc_init_ratio <= 1)
            (default : None) the current soc_ratio_current ratio from the
            ExtendedBattery is used
        p_el_out : float
            Electrical dischargin power in W (default: 0)

        Returns
        ------
        charge_possible : bool
            Boolean to define, if charging with desired input power is possible
            True: Charging possible (enough capacity left)
            False: Charging not possible (would go above maximal capacity)
        """
        assert p_el_out >= 0
        assert p_el_in >= 0

        # if soc_ratio_current is None soc_ratio_current is used from
        # Extended Battery object
        if soc_ratio_current is None:
            soc_ratio_current = self.soc_ratio_current
        else:
            pass

        p_el_in_max = self.calc_battery_max_p_el_in(soc_ratio_current=
                                                    soc_ratio_current,
                                                    p_el_out=p_el_out)
        if p_el_in_max >= p_el_in:
            charge_possible = True
        else:
            charge_possible = False
        return charge_possible
