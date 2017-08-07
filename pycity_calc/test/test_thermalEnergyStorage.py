#!/usr/bin/env python
# coding=utf-8
"""
Test script for BoilerExtended class
"""

from __future__ import division
import pycity_calc.energysystems.thermalEnergyStorage as tES

from pycity_calc.test.pycity_calc_fixtures import fixture_environment, \
    fixture_thermalEnergyStorage
from decimal import *


class Test_thermalEnergyStorage():
    def test_thermalEnergyStorage_init(self, fixture_environment):
        boiler = tES.thermalEnergyStorageExtended(
            environment=fixture_environment,
            t_init=50,
            capacity=5000,
            t_surroundings=35,
            t_max=85,
            t_min=0,
            use_outside_temp=False)

        assert boiler._kind == 'tes'
        assert boiler.t_surroundings == 35

        boiler = tES.thermalEnergyStorageExtended(
            environment=fixture_environment,
            t_init=50,
            capacity=5000,
            t_surroundings=35,
            t_max=85,
            t_min=0,
            use_outside_temp=True)

        assert boiler._kind == 'tes'
        assert boiler.t_surroundings == None

    def test_calc_storage_volume(self, fixture_thermalEnergyStorage):
        # capacity is 100.000 kg
        # rho = 1000 kg /m³

        v_storage = fixture_thermalEnergyStorage.calc_storage_volume()
        assert round(v_storage, 2) == 100.00

    def test_calc_storage_diameter(self, fixture_thermalEnergyStorage):
        # capacity is 100.000 kg
        # rho = 1000 kg /m³

        d_storage = fixture_thermalEnergyStorage.calc_storage_diameter()
        assert round(d_storage, 2) == 3.31

    def test_calc_storage_height(self, fixture_thermalEnergyStorage):
        # capacity is 100.000 kg
        # rho = 1000 kg /m³

        h_storage = fixture_thermalEnergyStorage.calc_storage_height()
        assert round(h_storage, 2) == 11.60

    def test_calc_storage_outside_area(self, fixture_thermalEnergyStorage):
        # capacity is 100.000 kg
        # rho = 1000 kg /m³

        area_storage = fixture_thermalEnergyStorage.calc_storage_outside_area()
        assert round(area_storage, 2) == 137.97

    def test_calc_storage_temp_for_next_timestep(self,
                                                 fixture_thermalEnergyStorage):
        # capacity is 100.000 kg
        # rho = 1000 kg /m³

        # TODO
        fixture_thermalEnergyStorage.use_outside_temp = True
        t_ambient = 10  # °C
        t_current = fixture_thermalEnergyStorage.t_current

        q_out = 12000000
        t_new = fixture_thermalEnergyStorage.calc_storage_temp_for_next_timestep(
            q_in=0, q_out=q_out,
            t_prior=t_current, t_ambient=t_ambient,
            set_new_temperature=False)
        assert round(t_new, 2) == 24.19

        q_in = 12000000
        t_new = fixture_thermalEnergyStorage.calc_storage_temp_for_next_timestep(
            q_in=q_in, q_out=0,
            t_prior=t_current, t_ambient=t_ambient,
            set_new_temperature=True)

        assert round(t_new, 2) == 75.79
        assert round(fixture_thermalEnergyStorage.t_current, 2) == 75.79

    def test_calc_storage_curr_amount_of_energy(self,
                                                fixture_thermalEnergyStorage):
        # capacity is 100.000 kg
        # rho = 1000 kg /m³
        # cp = 4186 J/kg
        # t_init = 50, t_min = 0
        tes_energy = fixture_thermalEnergyStorage.calc_storage_curr_amount_of_energy()
        assert round(tes_energy, 2) == 5813.89

    def test_calc_storage_q_out_max(self, fixture_thermalEnergyStorage):
        # capacity is 100.000 kg
        # rho = 1000 kg /m³
        # cp = 4186 J/kg
        # t_init = 50, t_min = 0

        fixture_thermalEnergyStorage.use_outside_temp = True
        t_ambient = 10  # °C

        q_out_max = fixture_thermalEnergyStorage.calc_storage_q_out_max(
            t_ambient)
        assert round(q_out_max, 4) == 23251692.5149

    def test_calc_storage_q_in_max(self, fixture_thermalEnergyStorage):
        # capacity is 100.000 kg
        # rho = 1000 kg /m³
        # cp = 4186 J/kg
        # t_init = 50, t_min = 0

        t_ambient = 0  # °C

        #  Overwrite use_outside_temp
        fixture_thermalEnergyStorage.use_outside_temp = True

        q_in_max = fixture_thermalEnergyStorage.calc_storage_q_in_max(
            t_ambient)
        assert round(q_in_max, 2) == 13958162.13

    def test_storage_q_out_possible(self, fixture_thermalEnergyStorage):
        # capacity is 100.000 kg
        # rho = 1000 kg /m³
        # cp = 4186 J/kg
        # t_init = 50, t_min = 0
        # q_out_max = 580198869.7504

        fixture_thermalEnergyStorage.use_outside_temp = True
        t_ambient = 10  # °C

        q_out_possible = fixture_thermalEnergyStorage.storage_q_out_possible(
            30000000, t_ambient)

        assert q_out_possible == False

        q_out_possible = fixture_thermalEnergyStorage.storage_q_out_possible(
            20000000, t_ambient)

        assert q_out_possible == True

    def test_storage_q_in_possible(self, fixture_thermalEnergyStorage):
        # capacity is 100.000 kg
        # rho = 1000 kg /m³
        # cp = 4186 J/kg
        # t_init = 50, t_min = 0
        # q_in_max = 522143314.1949

        fixture_thermalEnergyStorage.use_outside_temp = True
        t_ambient = 10  # °C

        q_in_possible = fixture_thermalEnergyStorage.storage_q_in_possible(
            20000000, t_ambient)

        assert q_in_possible == False

        q_in_possible = fixture_thermalEnergyStorage.storage_q_in_possible(
            10000000, t_ambient)

        assert q_in_possible == True
