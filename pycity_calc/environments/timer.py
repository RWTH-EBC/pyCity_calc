# coding=utf-8
"""
Script extends timer class of pycity
"""
from __future__ import division
import datetime
import numpy as np
import pycity_base.classes.Timer as Timer


class TimerExtended(Timer.Timer):
    """
    Extended Timer class (inheritance from pycity Timer class)
    """

    def __init__(self, timestep, year=2010, annual_profiles=True,
                 timespan_non_annual=None, day_init=None,
                 time_steps_horizon=None,
                 t_used_horizon=None):
        """
        Constructor of extended timer object (inheritance from pycity Timer
        object)

        Parameters
        ----------
        timestep : int
            Timestep in seconds
        year : int, optional
            Chosen year of analysis (default: 2010)
            (influences initial day for profile generation, market prices
            and co2 factors)
            If year is set to None, user has to define day_init!
        annual_profiles : bool, optional
            Boolean to define, if annual profiles should be generated.
            (default: True)
            True - Generate annual profiles
            False - Define own timespan of analysis (requires valid input
            value for timespan_non_annual)
        timespan_non_annual : int, optional
            Timespan in seconds for non-annual analysis (default: None).
            Only relevant, if annual_profiles is set to False.
        day_init : int, optional
            Integer for initial weekday (default: None)
            1 - Monday ... 7 - Sunday (corresponding to pyCity nomenclature)
            Only relevant, if year is set to None
        time_steps_horizon : int, optional
            Number of timesteps for forecast horizon (default: None)
            If timestep=3600, time_steps_horizon=10 would require
            forecasts for the next 10 hours. If set to None, time_steps_horizon
            is set to total number of timesteps (for one year)
        t_used_horizon : int, optional
            How many timesteps are shifted/accepted in each horizon?
            1 <= timestepsUsedHorizon <= timestepsHorizon
            (default: None). If set to None t_used_horizon
            is set to total number of timesteps (for one year)
        """
        if annual_profiles:
            #  Currently, leap year is not supported!
            days = 365

            # Calculate nb_timesteps with timestep and number of days
            #  nb_timesteps defines number of timesteps
            nb_timesteps = int(days * 24 * 60 * 60 / timestep)

        else:  # Own time span (as number of timesteps)
            nb_timesteps = int(timespan_non_annual / timestep)

        # Calculate weekday / day_init for given year
        if year is not None:
            #  Python weekday definition (0 - Monday; ...; 6 - Sunday)
            day_init = datetime.date(year=year, month=1, day=1).weekday()
            #  Increase by 1 to match to corresponding pyCity nomenclature
            day_init += 1
            if day_init not in [1, 2, 3, 4, 5, 6, 7]:
                msg = 'Initial day (day_init) is not within range 1 to 7, ' \
                      'according to pyCity nomenclature (Mo - 1; Su - 7).'
                raise AssertionError(msg)

        if time_steps_horizon is None:
            time_steps_horizon = nb_timesteps
        if t_used_horizon is None:
            t_used_horizon = nb_timesteps

        super(TimerExtended, self).__init__(timeDiscretization=timestep,
                                            timestepsTotal=nb_timesteps,
                                            initialDay=day_init,
                                            timestepsHorizon=time_steps_horizon,
                                            timestepsUsedHorizon=t_used_horizon)

        #  Further attributes
        self.timestep = timestep
        self.year = year

    #  Uncommented, as time_vector is currently not in use. Has only been
    #  Used by old energy balance script
    # def time_vector(self):
    #     """
    #     Generates time array (with hourly values!)
    #
    #     Returns
    #     -------
    #     time_vector : np.array
    #         Numpy array with
    #     """
    #
    #     initial_annual_steps = 8760
    #     time_vector_list = []
    #     for i in range(int(initial_annual_steps * 3600 / self.timestep)):
    #         time_vector_list.append(i)
    #
    #     #  Convert to numpy array
    #     time_vector = np.array(time_vector_list)
    #
    #     return time_vector


if __name__ == '__main__':

    timestep = 900  # timestep in seconds
    timer = TimerExtended(timestep=timestep)

    time_array = timer.time_vector()

    print(time_array)
    print(len(time_array))
