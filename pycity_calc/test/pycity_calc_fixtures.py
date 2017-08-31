#!/usr/bin/env python
# coding=utf-8
"""
Pytest fixtures of pycity_calc
"""

from __future__ import division
import pytest

import pycity_calc.environments.market as mark
import pycity_calc.environments.timer as time
import pycity_calc.environments.co2emissions as co2
import pycity_calc.environments.environment as env

import pycity_base.classes.Weather as weat
import pycity_base.classes.demand.SpaceHeating as SpaceHeating
import pycity_base.classes.demand.ElectricalDemand as ElDemand
import pycity_base.classes.demand.Apartment as Apartment
import pycity_calc.buildings.building as build_ex
import pycity_calc.cities.city as city
import pycity_base.classes.demand.Occupancy as occu
import pycity_base.classes.demand.DomesticHotWater as DomesticHotWater

import pycity_calc.energysystems.battery as batt
import pycity_calc.energysystems.chp as chp
import pycity_calc.energysystems.boiler as boiler
import pycity_calc.energysystems.electricalHeater as eHeater
import pycity_calc.energysystems.heatPumpSimple as hp
import pycity_calc.energysystems.thermalEnergyStorage as tES

import pycity_calc.extern_el_grid.PowerGrid as grid


@pytest.fixture(scope='module')
def fixture_environment(year=2010, timestep=900,
                        location=(51.529086, 6.944689)):
    """
    Fixture to create environment object for PyCity (scope='module')

    Parameters
    ----------
    year : int, optional
        Reference year (default: 2010)
    timestep : int, optional
        Integer timestep in seconds (default: 900)
    location : tuple (of floats)
        2d tuple with latitude adn longitude of location
        (default: (51.529086, 6.944689) for Bottrop, Germany)

    Returns
    -------
    fixture_environment : environment object
        Extended environment object of Pycity_calc
    """
    #  Generate extended timer of pycity_calc
    timer = time.TimerExtended(timestep, year=year, annual_profiles=True,
                               timespan_non_annual=None, day_init=None)

    #  Generate pycity weather object
    weather = weat.Weather(timer, useTRY=True)

    #  Generate market object of pycity_calc (extends prices of pycity)
    market = mark.Market()

    #  Generate emission object of pycity_calc
    emission = co2.Emissions(year=year)

    fixture_environment = env.EnvironmentExtended(timer=timer, weather=weather,
                                                  prices=market,
                                                  location=location,
                                                  co2em=emission)
    return fixture_environment


@pytest.fixture
def fixture_market():
    """
    Fixture to create market object of pycity_calc

    Returns
    -------
    fixture_market : object
        Market object of pycity_calc
    """
    #  Generate market object
    fixture_market = mark.Market()
    return fixture_market


@pytest.fixture
def fixture_th_demand(fixture_environment, annual_th_demand=13000):
    """
    Fixture for generation of thermal load profile (SLP).

    Parameters
    ----------
    fixture_environment : object
        Fixture environment object
    annual_th_demand : float, optional
        Annual thermal energy demand in kWh/a (default: 13000)

    Returns
    -------
    fixture_th_demand : object
        Thermal demand object
    """
    living_area = 100
    specific_demand = annual_th_demand / living_area

    fixture_th_demand = SpaceHeating.SpaceHeating(fixture_environment,
                                                  method=1,
                                                  profile_type='HEF',
                                                  livingArea=living_area,
                                                  specificDemand=specific_demand)
    return fixture_th_demand


@pytest.fixture
def fixture_el_demand(fixture_environment, annual_el_demand=3000):
    """
    Fixture for generation of el. load profile (SLP).

    Parameters
    ----------
    fixture_environment : object
        Fixture environment object
    annual_el_demand : float, optional
        Annual electrfical energy demand in kWh/a (default: 3000)

    Returns
    -------
    fixture_el_demand : object
        Electrical demand object
    """

    fixture_el_demand = ElDemand.ElectricalDemand(fixture_environment,
                                                  method=1,
                                                  annualDemand=annual_el_demand,
                                                  profileType="H0")
    return fixture_el_demand


@pytest.fixture
def fixture_apartment(fixture_environment, fixture_th_demand,
                      fixture_el_demand):
    """
    Fixture for generation of apartment object with loads

    Parameters
    ----------
    fixture_environment : object
        Fixture environment object
    fixture_th_demand : object
        Thermal demand object
    fixture_el_demand : object
        Electrical demand object

    Returns
    -------
    fixture_apartment : object
        Fixture apartment object
    """

    #  Create apartment
    fixture_apartment = Apartment.Apartment(fixture_environment)

    #  Loads
    load_list = [fixture_th_demand, fixture_el_demand]

    #  Add loads
    fixture_apartment.addMultipleEntities(load_list)

    return fixture_apartment


@pytest.fixture
def fixture_building(fixture_environment, fixture_apartment):
    """
    Fixture for generation of extended building object with
    single apartment with loads

    Parameters
    ----------
    fixture_environment : object
        Fixture environment object
    fixture_apartment : object
        Fixture apartment object

    Returns
    -------
    fixture_building : object
        Fixture building object
    """
    fixture_building = build_ex.BuildingExtended(fixture_environment)

    #  Add apartment
    fixture_building.addEntity(entity=fixture_apartment)

    return fixture_building


@pytest.fixture
def fixture_detailed_building(fixture_environment):
    #  Create demands (with standardized load profiles (method=1))
    heat_demand = SpaceHeating.SpaceHeating(fixture_environment,
                                            method=1,
                                            profile_type='HEF',
                                            livingArea=100,
                                            specificDemand=130)

    el_demand = ElDemand.ElectricalDemand(fixture_environment,
                                          method=1,
                                          annualDemand=3000,
                                          profileType="H0")

    dhw_annex42 = DomesticHotWater.DomesticHotWater(fixture_environment,
                                                    tFlow=60,
                                                    thermal=True,
                                                    method=1,  # Annex 42
                                                    dailyConsumption=100,
                                                    supplyTemperature=25)

    #  Create occupancy
    occupancy_object = occu.Occupancy(fixture_environment, number_occupants=3)

    #  Create apartment
    apartment = Apartment.Apartment(fixture_environment)

    #  Add demands to apartment
    apartment.addMultipleEntities([heat_demand, el_demand, dhw_annex42,
                                   occupancy_object])

    #  Create extended building object
    fixture_detailed_building = \
        build_ex.BuildingExtended(fixture_environment,
                                  build_year=1962,
                                  mod_year=2003,
                                  build_type=0,
                                  roof_usabl_pv_area=30,
                                  net_floor_area=150,
                                  height_of_floors=3,
                                  nb_of_floors=2,
                                  neighbour_buildings=0,
                                  residential_layout=0,
                                  attic=0, cellar=1,
                                  construction_type='heavy',
                                  dormer=0)
    #  BuildingExtended holds further, optional input parameters,
    #  such as ground_area, nb_of_floors etc.

    #  Add apartment to extended building
    fixture_detailed_building.addEntity(entity=apartment)

    return fixture_detailed_building


@pytest.fixture
def fixture_city(fixture_environment):
    """
    Fixture for generation of city object of pycity_calc (without apartments,
    BES and Flow-temp.-curves)

    Parameters
    ----------
    fixture_environment : object
        Fixture environment object
    """
    #  Generate city object
    fixture_city = city.City(environment=fixture_environment)

    return fixture_city


@pytest.fixture
def fixture_battery(fixture_environment, soc_init_ratio=1, capacity_kwh=100):
    """
    Fixture for battery class

    Parameters
    ----------
    fixture_environment : object
        Fixture environment object
    soc_init_ratio : float, optional
        Initial state of charge (relative to capacity) (no unit)
        (default: 1 --> Fully loaded)
        (0 <= soc_init_ratio <= 1)
    capacity_kwh : float, optional
        Battery's capacity in kWh (default: 100)

    Returns
    -------
    fixture_battery : object
        Fixture battery object
    """
    fixture_battery = batt.BatteryExtended(environment=fixture_environment,
                                           soc_init_ratio=soc_init_ratio,
                                           capacity_kwh=capacity_kwh)
    return fixture_battery


@pytest.fixture
def fixture_chp_th(fixture_environment, q_nominal=10000, p_nominal=4500,
                   lower_activation_limit=0.6, omega=0.87,
                   thermal_operation_mode=True):
    """
    Fixture for battery class

    Parameters
    ----------
    fixture_environment : object
        Fixture environment object
    p_nominal : float
            nominal electricity output in Watt
            default: 10,000
    q_nominal : float
            nominal heat output in Watt
            default: 6,000
    lower_activation_limit : float
            Define the lower activation limit (default: 0.6). For example, heat pumps are
            typically able to operate between 50 % part load and rated load.
            In this case, lower_activation_limit would be 0.5
            Two special cases:
            Linear behavior: lower_activation_limit = 0
            Two-point controlled: lower_activation_limit = 1
            Range: (0 <= lower_activation_limit <= 1)
    omega : float
            total efficiency of the CHP unit (without unit)
            (default: 0.87)


    Returns
    -------
    fixture_chp : object
        Fixture chp object
    """
    fixture_chp_th = chp.ChpExtended(environment=fixture_environment,
                                     q_nominal=q_nominal,
                                     p_nominal=p_nominal,
                                     lower_activation_limit=lower_activation_limit,
                                     eta_total=omega,
                                     thermal_operation_mode=thermal_operation_mode)

    return fixture_chp_th


@pytest.fixture
def fixture_chp_el(fixture_environment, q_nominal=10000, p_nominal=4500,
                   lower_activation_limit=0.6, omega=0.87,
                   thermal_operation_mode=False):
    """
    Fixture for battery class

    Parameters
    ----------
    fixture_environment : object
        Fixture environment object
    p_nominal : float
            nominal electricity output in Watt
            default: 10,000
    q_nominal : float
            nominal heat output in Watt
            default: 6,000
    lower_activation_limit : float
            Define the lower activation limit (default: 0.6). For example, heat pumps are
            typically able to operate between 50 % part load and rated load.
            In this case, lower_activation_limit would be 0.5
            Two special cases:
            Linear behavior: lower_activation_limit = 0
            Two-point controlled: lower_activation_limit = 1
            Range: (0 <= lower_activation_limit <= 1)
    omega : float
            total efficiency of the CHP unit (without unit)
            (default: 0.87)
    thermal_operation_mode : boolean
            determines the operation mode of the chp module
            True : thermal operation mode
            False : electrical operation mode


    Returns
    -------
    fixture_chp : object
        Fixture chp object
    """
    fixture_chp_el = chp.ChpExtended(environment=fixture_environment,
                                     q_nominal=q_nominal,
                                     p_nominal=p_nominal,
                                     lower_activation_limit=lower_activation_limit,
                                     eta_total=omega,
                                     thermal_operation_mode=thermal_operation_mode)

    return fixture_chp_el


@pytest.fixture
def fixture_boiler(fixture_environment, q_nominal=10000, eta=0.9, t_max=85,
                   lower_activation_limit=0):
    """

    Parameters
    ----------
    fixture_environment : Environment object
        Common to all other objects. Includes time and weather instances
    q_nominal : float
        nominal heat output in Watt
        default: 10000
    eta : float
        efficiency (without unit)
        default: 0.9
    t_max : Integer, optional
        maximum provided temperature in °C
        default: 85
    lower_activation_limit : float (0 <= lowerActivationLimit <= 1)
        Define the lower activation limit. For example, heat pumps are
        typically able to operate between 50 % part load and rated load.
        In this case, lowerActivationLimit would be 0.5
        Two special cases:
        Linear behavior: lowerActivationLimit = 0 (default)
        Two-point controlled: lowerActivationLimit = 1

    Returns
    -------
    fixture_boiler: object
        Fixture boiler object
    """
    fixture_boiler = boiler.BoilerExtended(environment=fixture_environment,
                                           q_nominal=q_nominal,
                                           eta=eta,
                                           t_max=t_max,
                                           lower_activation_limit=lower_activation_limit)

    return fixture_boiler


@pytest.fixture
def fixture_electricalHeater(fixture_environment, q_nominal=10000, eta=0.9,
                             t_max=85, lower_activation_limit=0):
    """

    Parameters
    ----------
    fixture_environment : Environment object
        Common to all other objects. Includes time and weather instances
    q_nominal : float
        nominal heat output in Watt
        default: 10000
    eta : float
        efficiency (without unit)
        default: 0.9
    t_max : Integer, optional
        maximum provided temperature in °C
        default: 85
    lower_activation_limit : float (0 <= lowerActivationLimit <= 1)
        Define the lower activation limit. For example, heat pumps are
        typically able to operate between 50 % part load and rated load.
        In this case, lowerActivationLimit would be 0.5
        Two special cases:
        Linear behavior: lowerActivationLimit = 0 (default)
        Two-point controlled: lowerActivationLimit = 1

    Returns
    -------
    fixture_electricalHeater: object
        Fixture electricalHeater object
    """
    fixture_electricalHeater = eHeater.ElectricalHeaterExtended(
        environment=fixture_environment,
        q_nominal=q_nominal,
        eta=eta,
        t_max=t_max,
        lower_activation_limit=lower_activation_limit)

    return fixture_electricalHeater


@pytest.fixture
def fixture_heatPumpSimple(fixture_environment, q_nominal=10000, t_max=85.0,
                           lower_activation_limit=0.5, hp_type='aw',
                           t_sink=45.0):
    """
    Constructor of heat pump.

    Parameters
    ----------
    environment : Environment object
        Common to all other objects. Includes time and weather instances
    q_nominal : float
        Nominal heat output in Watt
    t_max : float, optional
        Maximum provided temperature in °C (default: 85 °C)
    lower_activation_limit : float, optional
        Define the lower activation limit (Default: 1). For example, heat pumps are
        typically able to operate between 50 % part load and rated load.
        In this case, lower_activation_limit would be 0.5
        Two special cases:
        Linear behavior: lower_activation_limit = 0
        Two-point controlled: lower_activation_limit = 1
        Range:(0 <= lower_activation_limit <= 1)
    hp_type : str, optional
        Type of heat pump (default: 'aw')
        Options:
        'aw': Air/water (air temperature is taken from environment._outdoor_temp_curve)
        'ww': Water/water (water temperature is taken from environment.temp_ground)
    temp_sink : float, optional
        Temperature of heat sink in °C (default: 45 °C)

    Annotations
    -----------
    COP is estimated with quality grade (Guetegrad) and max. possible COP.

    COP is limited to value of 5.

    Heat sink temperature is defined as input parameter. If building object with variable indoor temperature is
    given, heat pump should be modified to get indoor temperature per function call.

    Returns
    -------
    fixture_heatPumpSimple: object
        Fixture heatPumpSimple object
    """
    fixture_heatPumpSimple = hp.heatPumpSimple(environment=fixture_environment,
                                               q_nominal=q_nominal,
                                               t_max=t_max,
                                               lower_activation_limit=lower_activation_limit,
                                               hp_type=hp_type,
                                               t_sink=t_sink)

    return fixture_heatPumpSimple


@pytest.fixture
def fixture_thermalEnergyStorage(fixture_environment, t_init=50,
                                 capacity=100000,
                                 c_p=4186, rho=1000, t_max=80.0, t_min=0.0,
                                 t_surroundings=20.0, k_loss=0.7,
                                 h_d_ratio=3.5, use_outside_temp=False):
    """
    Construcotr of extended thermal storage system

    Parameters
    ----------
    environment : Environment object
        Common to all other objects. Includes time and weather instances
    t_init : float
        initialization temperature in °C
    capacity : float
        storage mass in kg
    c_p : float, optional
        Specific heat capacity of storage medium in J/(kg*K) (default: 4186 - water)
    rho : float, optional
        Density of storage medium in kg/m^3 (default: 1000 - water)
    t_max : float, optional
        Maximum storage temperature in °C (default: 80 °C)
        Related to physical properties of water
    t_min : float, optional
        Minimal storage temperature in °C (default: 0 °C)
        Related to physical properties of water
    t_surroundings : float, optional
        temperature of the storage's surroundings in °C (default: 20 °C)
    k_loss : float, optional
        Loss factor of storage in W/m^2*K (default: 0.7)
    h_d_ratio : float, optional
        Ratio between storage height and diameter (assumes cylindrical storage form)
        (Default: 3.5)
    use_outside_temp : bool, optional
        Boolean to define, if outside temperature of environment should be used to calculate
        heat losses (default: False)
        False: Use t_surroundings (input parameter of Thermalenergystorage)
        True: Use t_outside of environment object

    Annotation
    ----------
    Thermal storage system does not have internal control system.
    If temperature limits are exceeded, an assertionError is raised.

    Default value for k_loss has been estimated with datascheet of buderus Logalux SMS 290/5E
    https://productsde.buderus.com/buderus/productsat.buderus.com/broschuren-buderus.at/broschuren-alt/speicher/speicher-prospekt-logalux.pdf
    h=1,835 m; V=290 L; delta T = 65 - 20 K; Q_dot_loss = 2,07 kWh / 24 h

    h/d - ratio is also estimated with buderus datascheet
    """

    fixture_thermalEnergyStorage = tES.thermalEnergyStorageExtended(
        environment=fixture_environment,
        t_max=t_max,
        t_min=t_min,
        c_p=c_p, rho=rho,
        t_surroundings=t_surroundings,
        t_init=t_init,
        k_loss=k_loss,
        capacity=capacity,
        h_d_ratio=h_d_ratio,
        use_outside_temp=use_outside_temp)

    return fixture_thermalEnergyStorage
