# -*- coding: utf-8 -*-
"""
Script with CHP efficiency curves and calculations based on:

Arbeitsgemeinschaft für sparsamen und umweltfreundlichen
Energieverbrauch e.V., BHKW-Kenndaten 2014/15, Essen, 2015.
(following functions  are only valid for gas-CHP systems!)
"""

#  #------------------------------------------------------------------------------------------------------------------
#  From th. power --> el. efficiency th. efficiency --> --> el. power

def calc_el_eff_with_th_power(th_power):
    """
    Returns electrical efficiency of CHP (input: thermal power in W)

    Parameters
    ----------
    th_power : float
        Thermal output power in W

    Returns
    ------
    el_eff : float
        Thermal efficiency (without unit)
    """

    assert th_power >= 0

    #  TODO: Add eta_total as parameter (necessary, because it influences functions)
    #  Asue classes of electric nominal power
    if th_power <= 21130:  #  in Watt
        el_eff = 0.0787*(th_power)**0.1273
    elif th_power <= 139762:
        el_eff = 0.0847*(th_power)**0.1227
    elif th_power <= 1064487:
        el_eff = 0.1304*(th_power)**0.0845
    else:  # Larger than 1000 kW el. power
        el_eff = 0.1926*(th_power)**0.0557
    assert el_eff >= 0
    assert el_eff <= 1
    return el_eff

def calc_th_eff_with_el_eff(el_eff, eta_total):
    """
    Returns thermal efficiency of CHP

    Parameters
    ----------
    el_eff : float
        Electric efficiency (no unit)
    eta_total : float
        Total efficiency of CHP (no unit)

    Returns
    -------
    th_eff : float
        Thermal efficiency (no unit)
    """
    assert eta_total > 0
    assert el_eff >= 0

    th_eff = eta_total - el_eff
    assert th_eff >= 0
    assert th_eff <= 1
    return th_eff

def calc_th_eff_with_th_power(th_power, eta_total):
    """
    Returns thermal efficiency of CHP

    Parameters
    ----------
    th_power : float
        Thermal power
    eta_total : float
        Total efficiency of CHP (no unit)

    Returns
    -------
    th_eff : float
        Thermal efficiency (no unit)
    """
    el_eff = calc_el_eff_with_th_power(th_power)
    th_eff = calc_th_eff_with_el_eff(el_eff, eta_total)
    assert th_eff >= 0
    assert th_eff <= 1
    return th_eff

def calc_el_power_with_th_power(th_power, eta_total):
    """
    Returns thermal power of CHP in Watt

    Parameters
    ----------
    th_power : float
        Thermal power output of CHP in W
    eta_total : float
        total efficiency of CHP (no unit)

    Returns
    ------
    el_power : float
        Electrical power output of CHP in W
    """
    assert th_power >= 0
    #  Calculate el. efficiency
    el_eff = calc_el_eff_with_th_power(th_power)
    #  Calculate thermal efficiency
    th_eff = calc_th_eff_with_el_eff(el_eff, eta_total)
    #  Calculate electric power output
    el_power = th_power * el_eff / th_eff
    return el_power

#  #------------------------------------------------------------------------------------------------------------------
#  From electric power --> El. efficiency --> Th. efficiency --> Thermal power

def calc_el_eff_with_p_el(el_power):
    """
    Returns electric efficiency of CHP (input: electric power in W)

    Parameters
    ----------
    el_power : float
        Electric output power in W

    Returns
    ------
    el_eff : float
        Electric efficiency (without unit)
    """

    assert el_power >= 0

    #  Asue classes of electric nominal power
    if el_power <= 10*1000:  # Factor 1000 to convert kW into W
        el_eff = 0.21794*(el_power/1000)**0.108
    elif el_power <= 100*1000:
        el_eff = 0.2256*(el_power/1000)**0.1032
    elif el_power <= 1000*1000:
        el_eff = 0.25416*(el_power/1000)**0.0732
    else:  # Larger than 1000 kW el. power
        el_eff = 0.29627*(el_power/1000)**0.0498
    assert el_eff >= 0
    assert el_eff <= 1
    return el_eff

def calc_th_eff_with_p_el(el_power, eta_total):
    """
    Returns thermal efficiency of CHP

    Parameter
    ---------
    el_power : float
        Electric output power in W
    eta_total : float
        Total efficiency of chp

    Returns
    ------
    th_eff : float
        Thermal efficiency (without unit)
    """

    assert el_power >= 0
    assert eta_total > 0

    #  Calculate electric efficiency
    el_eff = calc_el_eff_with_p_el(el_power)

    #  Calculate thermal efficiency
    th_eff = eta_total - el_eff
    assert th_eff > 0
    assert th_eff <= 1
    return th_eff

def calc_th_output_with_p_el(el_power, eta_total):
    """
    Returns thermal power output of CHP in Watt

    Parameters
    ----------
    el_power : float
        Electric output power in W
    eta_total : float
        Total efficiency of chp

    Returns
    ------
    th_power_output : float
        Thermal power output in W
    """

    assert el_power >= 0
    assert eta_total > 0

    #  Calculate electric efficiency
    el_eff = calc_el_eff_with_p_el(el_power)

    #  Calculate thermal efficiency
    th_eff = eta_total - el_eff
    assert th_eff > 0

    #  Calculate thermal power output
    th_power_output = el_power * th_eff / el_eff
    return th_power_output

def calc_asue_el_th_ratio(th_power):
    """
    Estimate Stromkennzahl according to ASUE 2015 data sets

    Parameters
    ----------
    th_power : float
        Thermal power in Watt

    Returns
    -------
    el_th_ratio : float
        Current el. to th. power ratio (Stromkennzahl)
    """

    el_th_ratio = 0.0799 * th_power ** 0.1783

    return el_th_ratio
