#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
from __future__ import division

import os
import pickle
import warnings

import pycity_calc.simulation.energy_balance.check_eb_requ as check_eb


def calc_build_therm_eb(build, soc_init=0.5, boiler_full_pl=True,
                        eh_full_pl=True):
    """
    Calculate building thermal energy balance. Requires extended building
    object with loads and thermal energy supply system.

    Parameters
    ----------
    build : object
        Extended building object of pyCity_calc
    soc_init : float, optional
        Factor of relative state of charge of thermal storage (if thermal
        storage is existent)
    boiler_full_pl
    eh_full_pl
    """

    #  Check if building fulfills necessary requirements for energy balance
    #  calculation
    check_eb.check_eb_build_requ(build=build)

    #  Check existent energy systems
    has_boiler = False
    has_chp = False
    has_hp = False
    has_eh = False
    has_tes = False

    if build.bes.hasBoiler is True:
        has_boiler = True

        #  Set pl of boiler (+ warning)



    if build.bes.hasChp is True:
        has_chp = True

    if build.bes.hasHeatpump is True:
        has_hp = True

    if build.bes.hasElectricalHeater is True:
        has_eh = True

        #  Set pl of eh (+ warning)

        

    if build.bes.hasTes is True:
        has_tes = True

        # Set initial soc to soc_init * soc_max

    #  Get building thermal load curves
    sh_power = build.get_space_heating_power_curve()
    dhw_power = build.get_dhw_power_curve()

    if has_tes:

        pass

    else:  # Has no TES
        #  Run thermal simulation, if no TES is existent (only relevant for
        #  Boiler and EH
        pass

        #  Loop over power values

            #  Try covering power with boiler




if __name__ == '__main__':

    this_path = os.path.dirname(os.path.abspath(__file__))