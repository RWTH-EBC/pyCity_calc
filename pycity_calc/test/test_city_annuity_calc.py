#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
from __future__ import division

import os
import copy
import numpy as np
import shapely.geometry.point as point

import pycity_base.classes.demand.SpaceHeating as spaceheat
import pycity_base.classes.demand.ElectricalDemand as elecdemand
import pycity_base.classes.supply.BES as BES
import pycity_base.classes.supply.PV as PV
import pycity_base.classes.demand.Apartment as apart

import pycity_calc.cities.city as cit
import pycity_calc.buildings.building as build
import pycity_calc.simulation.energy_balance.building_eb_calc as buildeb
import pycity_calc.simulation.energy_balance.city_eb_calc as cityeb
import pycity_calc.energysystems.chp as chpsys
import pycity_calc.energysystems.battery as bat
import pycity_calc.energysystems.boiler as boil
import pycity_calc.energysystems.electricalHeater as ehsys
import pycity_calc.energysystems.heatPumpSimple as hpsys
import pycity_calc.energysystems.thermalEnergyStorage as sto
import pycity_calc.energysystems.Input.chp_asue_2015 as asue
import pycity_calc.cities.scripts.city_generator.city_generator as citygen
import pycity_calc.cities.scripts.overall_gen_and_dimensioning as overall
import pycity_calc.toolbox.dimensioning.dim_networks as dimnet

from pycity_calc.test.pycity_calc_fixtures import fixture_building, \
    fixture_environment, fixture_city, fixture_apartment, fixture_th_demand, \
    fixture_el_demand


class TestCityAnnuityCalc():
    def test_city_annuity_chp_calc1(self, fixture_environment):
        """
        Compares annuity calculation of CHP for single building district with
        reference value
        """

        #  City
        city = cit.City(environment=fixture_environment)

        #  One building
        building = build.BuildingExtended(environment=fixture_environment)

        #  One apartment
        apartment = apart.Apartment(environment=fixture_environment)

        #  Initialize constant space heating and electrical load
        q_nom = 1000  # in W

        array_sh = np.ones(fixture_environment.timer.timestepsTotal) * q_nom
        heat_demand = spaceheat.SpaceHeating(environment=fixture_environment,
                                             method=0, loadcurve=array_sh)

        p_nom = 300  # in W

        array_el = np.ones(fixture_environment.timer.timestepsTotal) * p_nom
        el_demand = elecdemand.ElectricalDemand(
            environment=fixture_environment,
            method=0,
            loadcurve=array_el)

        #  Add energy demands to apartment
        apartment.addMultipleEntities([heat_demand, el_demand])

        #  Add apartment to extended building
        building.addEntity(entity=apartment)

        #  Add building to city
        pos = point.Point(0, 0)
        city.add_extended_building(extended_building=building, position=pos)

        #  BES
        bes = BES.BES(environment=fixture_environment)

        #  CHP
        chp = chpsys.ChpExtended(environment=fixture_environment,
                                 q_nominal=q_nom,
                                 p_nominal=0.0001,  # Dummmy value
                                 eta_total=1)

        #  ASUE calc --> el. power
        

        #  Run eb
