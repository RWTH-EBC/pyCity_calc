#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to run all example files
"""
from __future__ import division
import pycity_calc.examples.example_battery as example_battery
import pycity_calc.examples.example_boiler as example_boiler
import pycity_calc.examples.example_building as example_building
import pycity_calc.examples.example_chp as example_chp
import pycity_calc.examples.example_city as example_city
import pycity_calc.examples.example_city_street as example_city_street
import pycity_calc.examples.example_co2emissions as example_co2emissions
import pycity_calc.examples.example_complex_city_generator \
    as example_complex_city_generator
import pycity_calc.examples.example_electricalHeater as \
    example_electricalHeater
import pycity_calc.examples.example_environment as example_environment
import pycity_calc.examples.example_estimate_retrofit_state \
    as example_estimate_retrofit_state
import pycity_calc.examples.example_extern_el_grid as example_extern_el_grid
import pycity_calc.examples.example_heatPump as example_heatPump
import pycity_calc.examples.example_market as example_market
import pycity_calc.examples.example_teaser as example_teaser
import pycity_calc.examples.example_thermalEnergyStorage \
    as example_thermalEnergyStorage
import pycity_calc.examples.example_timer as example_timer
import pycity_calc.examples.example_vdi_6007 as example_vdi_6007
import pycity_calc.examples.example_vdi_6007_city as example_vdi_6007_city
import pycity_calc.examples.example_osm as example_osm
import pycity_calc.examples.example_city_annuity_calculation as city_ann


class Test_RunExamples():
    def test_example_battery(self):
        example_battery.run_example()

    def test_example_boiler(self):
        example_boiler.run_test()

    def test_example_building(self):
        example_building.run_example()

    def test_example_chp(self):
        example_chp.run_test()

    def test_example_city(self):
        example_city.run_example()

    def test_example_city_street(self):
        example_city_street.run_example()

    def test_example_co2emissions(self):
        example_co2emissions.run_example()

    def test_example_complex_city_generator(self):
        example_complex_city_generator.run_example()

    #  Fixme: Requires new input (city generation instead of pickle file!)
    # def test_example_economic_annuity_city(self):
    #     example_economic_annuity_city.run_example()

    def test_example_electricalHeater(self):
        example_electricalHeater.run_test()

    def test_example_environment(self):
        example_environment.run_example()

    def test_example_estimate_retrofit_state(self):
        example_estimate_retrofit_state.run_example_retro_estimate()

    def test_example_extern_el_grid(self):
        example_extern_el_grid.run_example_1()

    def test_example_heatPump(self):
        example_heatPump.run_test()
        example_heatPump.run_hp_example(False)

    def test_example_market(self):
        example_market.run_example()

    def test_example_teaser(self):
        example_teaser.run_example_exbuild()
        example_teaser.run_example_city()

    def test_example_thermalEnergyStorage(self):
        example_thermalEnergyStorage.run_test()
        example_thermalEnergyStorage.run_example_tes()
        example_thermalEnergyStorage.run_example_tes2()
        example_thermalEnergyStorage.run_example_tes3()
        example_thermalEnergyStorage.run_example_tes4()

    def test_example_timer(self):
        example_timer.run_example()

    def test_example_vdi_6007(self):
        example_vdi_6007.run_example_vdi_6007()

    #  Fixme: Requires new input (city generation instead of pickle file!)
    # def test_example_vdi_6007_city(self):
    #     example_vdi_6007_city.run_example_vdi_city()

    def test_example_osm(self):
        example_osm.run_osm_example()

    # def test_city_eb_and_annuity_calc(self):
    #     city_ann.run_example_city_energy_balance_and_annuity_calc()
