# coding=utf-8
"""
Script to extend pycity environment class
"""
from __future__ import division
import pycity_base.classes.Environment as Env


class EnvironmentExtended(Env.Environment):
    """
    Extended Environment class (inheritance from pycity environment class)
    """
    def __init__(self, timer, weather, prices, location, co2em,
                 temp_ground=10):
        """
        Constructor of EnvironmentExtended class. pycity environment class

        Parameters
        ----------
        timer : Timer object
            Handles current timestep, time discretization and horizon lengths.
        weather : Weather object
            Includes ambient temperature, solar radiation (diffuse, direct),
            relative humidity, air pressure and wind velocity
        prices : Prices object
            Definition of electricity price, remuneration ...
        location : Tuple
            (latitude, longitude) of the simulated system's position, e.g.
            (50.76, 6.07) represent Aachen, Germany.
        co2em : object
            Emission object of pycity_calc, holding co2 emission values for
            different combustibles and electricity mix.
        temp_ground : float, optional
            Ground temperature in degree Celsius (assumed to be constant).
            (default: 10)
        """

        #  Initialize subclass environment (of pycity)
        super(EnvironmentExtended, self).__init__(timer, weather, prices,
                                                  location)

        #  Add co2 emissions object
        self.co2emissions = co2em

        #  Further attributes
        self.temp_ground = temp_ground
