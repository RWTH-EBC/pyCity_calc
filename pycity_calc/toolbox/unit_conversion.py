#!/usr/bin/env python
# coding=utf-8
"""
Unit conversion functions
"""

def con_joule_to_kwh(energy_joule):
    """
    Converts energy value from Joule to kWh

    Parameters
    ----------
    energy_joule : float
        Energy demand value in Joule

    Returns
    -------
    energy_kwh : float
        Energy demand value in kWh
    """
    energy_kwh = energy_joule / (1000 * 3600)
    return energy_kwh

def con_kwh_to_joule(energy_kwh):
    """
    Converts energy value from kWh to Joule

    Parameters
    ----------
    energy_kwh : float
        Energy demand value in kWh

    Returns
    -------
    energy_joule : float
        Energy demand value in Joule
    """
    energy_joule = energy_kwh * 1000 * 3600
    return energy_joule

def con_celsius_to_kelvin(degree_celsius):
    """

    Parameters
    ----------
    degree_celsius : float
        temperature in Celsius

    Returns
    -------
    degree_kelvin : float
        temperature in Kelvin

    """
    degree_kelvin = degree_celsius + 273.15

    return degree_kelvin

def con_kelvin_to_celsius(degree_kelvin):
    """

    Parameters
    ----------
    degree_kelvin : float
        temperature in Celsius

    Returns
    -------
    degree_celsius : float
        temperature in Kelvin

    """
    degree_celsius = degree_kelvin - 273.15

    return degree_celsius

