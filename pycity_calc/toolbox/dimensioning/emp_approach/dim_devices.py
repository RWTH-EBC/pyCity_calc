#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt

import pycity_base.classes.supply.BES as BES
import pycity_base.classes.supply.Boiler as Boiler

import pycity_base.classes.supply.CHP as CHP
import pycity_calc.economic.energy_sys_cost.chp_cost as chp_cost
import pycity_calc.economic.energy_sys_cost.tes_cost as tes_cost
import pycity_calc.economic.energy_sys_cost.boiler_cost as boiler_cost

import pycity_calc.energysystems.heatPumpSimple as HP


def dim_decentral_hp(environment, sh_curve, t_biv=-2, hp_type='aw', lowerActivationLimit=0.5, tSink=35, temp_norm=-12, t_blocked=4):
    """
    Dimensioning of air/water and brine/water heat pump.

    Parameters
    ----------
    environment : Environment class of city-object
    sh_curve : Space heating curve of building
    t_biv : bivalence temperature
    hp_type : type of hp, 'aw'/'ww'
    lowerActivationLimit : lower activation limit of heat pump
    tSink : minimal flow temperature
    temp_norm : -12°C for Aachen

    Returns
    -------
    q_hp_biv : float
        Power of heat pump in bivalence point (-> Q_nom)
    tMax : int
        max. flow temperature
    lowerActivationLimit : float
        lower activation limit of heat pump
    tSink : int
        return flow temperature
    t_dem_ldc : list
        space heating demand sorted by outside temperature
    biv_ind : int
        index of bivalence point in t_dem_ldc
    """

    if hp_type == 'aw':
        # monoenergetic operation mode

        # get ldc with sh-demand and tAmbient
        t_dem_ldc = get_t_demand_list(temp_curve=environment.weather.tAmbient,
                                      th_curve=sh_curve)

        # plot temp-sorted demand curve
        # plt.plot(sorted(environment.weather.tAmbient), t_dem_ldc)

        # Find bivalence point and necessary thermal power of heat pump
        for i in range(len(t_dem_ldc)):

            # iterate through temp from min to max until temp is bigger than t_biv
            if sorted(environment.weather.tAmbient)[i] > t_biv:

                # get index of bivalence point in sorted temp curve
                biv_ind = i - 1

                # th. power in bivalence point (straight line between max(sh-demand) at temp_norm and 0 kW at 20°C)
                q_hp_biv = max(sh_curve) / (temp_norm - 20) * (t_biv - 20)

                # calculate produced heat by peak supply
                q2 = 0
                for q in sh_curve:
                    if q > q_hp_biv:
                        q2 += q - q_hp_biv

                # If curves are generated with method 1 (SLP by Hellwig), ratio is always 0.91% - maybe bc curves are only scaled up?
                print('peak supply produces ' + str(np.round(q2*100/np.sum(sh_curve),2)) + '% of annual heat demand.')

                ee_ratio = 1 - q2 / np.sum(sh_curve)

                break
        else:
            raise Exception('Error in demand calculation at bivalence point')

        # Choose heat pump from catalogue
        q_nom, cop_list, tMax, tSink = choose_hp(q_ideal=q_hp_biv,
                                                 t_biv=t_biv)

        return q_nom, cop_list, tMax, lowerActivationLimit, tSink, t_dem_ldc, biv_ind, ee_ratio

    elif hp_type == 'ww':
        # monovalent operation mode

        # two compressors
        lowerActivationLimit = 0.5

        # factor for blocked time (energy supply companies)
        f = round(24/(24-t_blocked), 1)

        # calculate necessary th. power
        q_hp = max(sh_curve) * f

        # choose heat pump from catalogue
        q_nom, cop_list, tMax, tSink = choose_hp(q_ideal=q_hp,
                                                 method=0,
                                                 hp_type='ww',
                                                 t_ground=environment.temp_ground)

        return q_nom, cop_list, tMax, lowerActivationLimit, tSink

    else:
        raise Warning('wrong heatpump type defined.')


def choose_hp(q_ideal, t_biv=-2, method=0, hp_type='aw', t_ground=10):
    """
    Choose heat pump depending on desired thermal power and bivalence point
    Method 0: Return best possible Heat Pump with average COPs
    Method 1: Choose heat pump from catalogue of existing devices (source: Dimplex)

    Parameters
    ----------
    q_ideal
    t_biv
    method
    hp_type
    t_ground

    Returns
    -------

    """

    # choose heat pump with ideal th.power and average cop
    if method == 0:

        # Air/Water heatpump
        if hp_type == 'aw':
            best_q = q_ideal

            # COPs for [A-7/W35, A2/W35, A7/W35]
            best_cop_list = [2.9, 3.7, 4.4]

            # 55/35 normal temp spread (Vor-/Ruecklauf)
            tMax = 43   #55
            tSink = 43  #35

        # Brine/Water heatpump
        elif hp_type == 'ww':
            best_q = q_ideal

            # COPs depending on constant t_ground (depending on depth of collector)
            if t_ground == 0:
                best_cop_list = [4.8]
            elif t_ground == 10:
                best_cop_list = [6]
            else:
                raise Warning('ground temperature not supported: ' + str(t_ground))

            tMax = 62
            tSink = 35

        else:
            raise Warning('heat pump type unknown: ' + hp_type)

        return best_q, best_cop_list, tMax, tSink

    # choose heatpump from catalogue
    elif method == 1:

        # Air/Water heatpump
        if hp_type == 'aw':

            # [heating power],[COP] (at A-7/W35, A2/W35, A7/W35), [tMax, tMin] (source: Dimplex)
            hp_list = {'LA6TU':([4000,5100,6400],[2.9,3.8,4.6],[60,18]),'LA9TU':([5200,7500,9200],[2.8,3.6,4.2],[58,18]),
                       'LA12TU':([7600,9400,11600],[2.9,3.7,4.3],[58,18]),'LA17TU':([10300,14600,19600],[2.9,3.7,4.4],[58,18]),
                       'LA25TU':([16700,19600,26100],[3.0,3.7,4.4],[58,18]),'LA40TU':([23800,30000,35700], [3.0,3.8,4.4],[58,18])}

            # get data for smallest heatpump in catalogue
            best_hp = 'LA6TU'
            best_q_biv = (hp_list['LA6TU'][0][2] - hp_list['LA6TU'][0][0]) / (7 + 7) * (t_biv + 7) + hp_list['LA6TU'][0][0]
            best_cop_list = hp_list['LA6TU'][1]

            # iterate through catalogue and choose most suitable heatpump
            for hp in hp_list:

                # get th.power list of current hp
                q_nom = hp_list[hp][0]

                # get th.power at t_biv for current hp (interpolation)
                q_biv = (q_nom[2] - q_nom[0])/(7 + 7) * (t_biv + 7) + q_nom[0]

                # update best_hp if current hp is more suitable
                if abs(q_biv - q_ideal) <= abs(best_q_biv - q_ideal):
                    best_hp = hp
                    best_q_biv = q_biv
                    best_cop_list = hp_list[hp][1]

            print('Best A/W-HP: ' + best_hp)

            # temperature constraints
            tMax = hp_list[best_hp][2][0]
            tSink = 35

            return best_q_biv, best_cop_list, tMax, tSink

        elif hp_type == 'ww':
            # [heating power],[COP] (at B0/W35, B10/W35),[tMax] (source: Dimplex)
            hp_list = {'SI8TU':([8100,11000],[4.8,6.2],[62]),'SI11TU':([10900,14100],[4.9,6.2],[62]),'SI14TU':([13900,18000],[5,6.2],[62]),
                       'SI18TU':([17500,22000],[4.7,5.6],[62]),'SI22TU':([22900,28000],[4.4,5.2],[58])}

            if t_ground == 10:
                t_ind = 0
            elif t_ground == 10:
                t_ind = 1
            else:
                raise Warning('hp for specific ground temperature not available: ' + str(t_ground) + '°C')

            # iterate through catalogue and choose most suitable heatpump
            for hp in hp_list:
                q_nom = hp_list[hp][0][t_ind]

                # choose first hp with th.power higher than needed
                if q_nom >= q_ideal:
                    best_hp = hp
                    best_q = q_nom
                    best_cop_list = hp_list[hp][1]
                    break
            else:
                raise Warning('Heat pumps in catalogue too small. Needed ' + str(round(q_ideal/1000,2))+'kW'+'; Found: '
                              + str(round(hp_list['SI22TU'][0][t_ind]/1000,2)) + ' kW.')

            print('Best S/W-HP: ' + best_hp)

            # temperature constraints
            tMax = hp_list[best_hp][2][0]
            tSink = 35

            return best_q, best_cop_list, tMax, tSink

        else:
            raise Warning('heat pump type unknown: ' + hp_type)

    else:
        raise Warning('method unknown: ' + str(method))


def dim_decentral_chp(th_LDC, q_total, method=0):
    """
    Dimensioning of CHP in decentralized supply system.

    Parameters
    ----------
    th_LDC : list : thermal load demand curve
    q_total : float : total heat demand per year in Wh
    method : int
        0 : method according to krimmling 2011
        1 : method to comply with EEWaermeG

    Returns
    -------
    eta_el : el. efficiency
    eta_th : th. efficiency
    p_nom : el. nominal power
    q_nom : th. nominal power
    t_x : full load hours
    t_ann_op : annual operation hours
    """

    # ---------------- Method 0: Krimmling and interviews ----------------
    if method == 0:

        # Set minimum th. power for chp
        q_chp = 0.1 * max(th_LDC)

        # Choose CHP from catalogue with minimum th. power and get estimated op.time (annual op. hours, full load hours)
        [eta_el, eta_th, p_nom, q_nom] = choose_chp(q_chp)
        (t_ann_op_max, t_x_max) = get_chp_ann_op_time(q_nom, th_LDC)

        # Set minimum full load hours
        chp_flh = 5000

        # get th. power with minimal full load hours (max th. power for chp)
        q_chp = th_LDC[chp_flh]

        # Choose CHP from catalogue with minimum th. power and get estimated op.time
        [eta_el, eta_th, p_nom, q_nom] = choose_chp(q_chp)
        (t_ann_op_min, t_x_min) = get_chp_ann_op_time(q_nom, th_LDC)

        # search best solution between chp with min and max full load hours
        if t_x_min <= t_x_max:

            # dummy values
            best_costs = 1000000000
            best_sol_costs = 0, 0, 0, 0, 0, 0

            array_q_nom = []
            array_t_x = []
            array_t_ann_op = []
            array_deckung = []
            array_costs = []

            # search for most economical chp - each iteration increases flh by 20h
            for t in range(t_x_min, t_x_max+1, 20):  # t_x_max+1 to have at least 1 value in range if t_max = t_min
                cost_cap = []
                cost_dem = []
                rev = []

                # choose best chp at timestep t
                q_chp = th_LDC[t]
                [eta_el, eta_th, p_nom, q_nom] = choose_chp(q_chp)

                # get estimated operational hours
                (t_ann_op, t_x) = get_chp_ann_op_time(q_nom, th_LDC)
                chp_ratio = q_nom * t_ann_op / q_total

                # Calculate estimated costs for chp
                q_chp_nom = q_nom / 1000  # in kW
                p_chp_nom = p_nom / 1000  # in kW

                a_chp = 0.08 * (1 + 0.08) ** 15 / ((1 + 0.08) ** 15 - 1)  # annuity factor
                chp_invest = chp_cost.calc_invest_cost_chp(p_el_nom=p_chp_nom,
                                                           method='asue2015',
                                                           with_inst=True,
                                                           use_el_input=True,
                                                           q_th_nom=None)
                cost_cap.append(chp_invest * a_chp)
                cost_dem.append((q_chp_nom) / eta_th * t_ann_op * 0.0661)
                rev.append(p_chp_nom * t_ann_op * get_el_feedin_tariff_chp(q_chp_nom))

                # Calculate estimated costs for thermal energy storage
                v_tes = q_chp_nom * 60  # in liter

                a_tes = 0.08 * (1 + 0.08) ** 20 / ((1 + 0.08) ** 20 - 1)
                tes_invest = tes_cost.calc_invest_cost_tes(v_tes / 1000, method='spieker')

                cost_cap.append(tes_invest * a_tes)
                rev.append(get_subs_tes_chp(chp_ratio, v_tes, tes_invest, p_chp_nom))
                rev.append(get_subs_minichp(p_chp_nom, q_chp_nom, v_tes))

                # Calculate costs for Boiler
                q_boiler_nom = max(max(th_LDC) - q_nom, 0) / 1000

                a_boiler = 0.08 * (1 + 0.08) ** 18 / ((1 + 0.08) ** 18 - 1)
                boiler_invest = boiler_cost.calc_abs_boiler_cost(q_boiler_nom, method='viess2013')

                cost_cap.append(boiler_invest * a_boiler)
                cost_dem.append((q_total / 1000 - q_chp_nom * t_ann_op) / 0.8 * 0.0661)

                costs_total = sum(cost_cap) + sum(cost_dem) - sum(rev)

                array_q_nom.append(q_nom)
                array_t_x.append(t_x)
                array_t_ann_op.append(t_ann_op)
                array_deckung.append((t_ann_op * q_nom) / q_total)
                array_costs.append(costs_total)

                # Choose current option if best option so far
                if costs_total < best_costs:
                    best_sol_costs = (eta_el, eta_th, p_nom, q_nom, t_x, t_ann_op)
                    best_costs = costs_total

            (eta_el, eta_th, p_nom, q_nom, t_x, t_ann_op) = best_sol_costs

        else:
            return None

    # ---------------- Method 1: EEWaermeG ----------------

    elif method == 1:

        eewg = False
        count = 0

        # Requirement are at least 50% heat per year from chp
        # Calculate sufficient th.power for CHP for average operation
        q_chp = 0.5 * q_total / 8760

        # Choose appropriate device and calculate estimated operation time
        [eta_el, eta_th, p_nom, q_nom] = choose_chp(q_chp)
        (t_ann_op, t_x) = get_chp_ann_op_time(q_nom, th_LDC)

        while not eewg:
            # Calculate ratio of chp heat usage (min. 50% necessary)
            ee_ratio = q_nom * t_ann_op / q_total

            if ee_ratio > 0.5:

                # calculate primary energy for separate production
                refeta_th = 0.85  # th. reference efficiency rate for devices older than 2016 (natural gas)
                refeta_el = 0.525  # el. reference efficiency rate for devices built between 2012 and 2015 (natural gas)

                # Primary energy savings in % calculated according to EU directive 2012/27/EU
                pee = (1 - 1 / ((eta_th / refeta_th) + (eta_el / refeta_el))) * 100

                # PE savings for CHP with el.power >= 1 MW have to be at least 10%
                if p_nom >= 1000000:
                    if pee >= 10:
                        eewg = True
                        break

                # PE savings for CHP with el. power < 1 MW have to be existent
                else:
                    if pee > 0:
                        eewg = True
                        break

                if ee_ratio >= 1:
                    raise Warning('EEWaermeG not satisfied: unrealistic values! (Q_chp >= Q_total)')

            # Raise th.power with 5% per iteration if conditions for EEWaermeG were not met
            q_chp = 0.5 * q_total / 8760 + count * q_total / (8760 * 100)
            [eta_el, eta_th, p_nom, q_nom] = choose_chp(q_chp)
            (t_ann_op, t_x) = get_chp_ann_op_time(q_nom, th_LDC)
            count += 5
    else:
        raise Exception('Invalid input for method!')

    return eta_el, eta_th, p_nom, q_nom, t_x, t_ann_op


def dim_central_chp(th_LDC, q_total, method=0):
    """
    Dimensioning of CHP in centralized supply system.

    Parameters
    ----------
    method : int
        0 : Standard approach (Krimmling 2011):
                - Q_th > 10% (< 20%) of max. thermal demand
                - Full-Load-hours preferably > 6000 h/a (minimum 5000 h/a)
        1 : Approach to satisfy EEWaermeG without any other constraints
        2 : Choose device where BAFA-Support for heating networks is available (Q_chp >= 75% of total annual heat
            demand) as described in KWKG without any other constraints

    Returns
    -------
    chp : ChpExtended
    """

    # ---------------- Method 0: Krimmling and interviews ----------------
    if method == 0:

        # Set minimum th. power for chp
        q_chp = 0.1*max(th_LDC)

        # Choose CHP from catalogue with minimum th. power and get estimated op.time (annual op. hours, full load hours)
        [eta_el, eta_th, p_nom, q_nom] = choose_chp(q_chp)
        (t_ann_op_max, t_x_max) = get_chp_ann_op_time(q_nom, th_LDC)

        # Set minimum full load hours
        chp_flh = 5000

        # get th. power with minimal full load hours (max th. power for chp)
        q_chp = th_LDC[chp_flh]

        # Choose CHP from catalogue with minimum th. power and get estimated op.time
        [eta_el, eta_th, p_nom, q_nom] = choose_chp(q_chp)
        (t_ann_op_min, t_x_min) = get_chp_ann_op_time(q_nom, th_LDC)

        # search best solution between chp with min and max full load hours
        if t_x_min < t_x_max:

            # dummy values
            best_costs = 1000000000
            best_sol_costs = 0,0,0,0,0,0

            array_q_nom = []
            array_t_x = []
            array_t_ann_op = []
            array_deckung = []
            array_costs = []

            # search for most economical chp - each iteration increases flh by 20h
            for t in range(t_x_min, t_x_max+1, 20):  # t_x_max+1 to have at least 1 value in range if t_max = t_min
                cost_cap = []
                cost_dem = []
                rev = []

                # choose best chp at timestep t
                q_chp = th_LDC[t]
                [eta_el, eta_th, p_nom, q_nom] = choose_chp(q_chp)

                # get estimated operational hours
                (t_ann_op, t_x) = get_chp_ann_op_time(q_nom, th_LDC)
                chp_ratio = q_nom * t_ann_op / q_total

                # Calculate estimated costs for chp
                q_chp_nom = q_nom/1000  # in kW
                p_chp_nom = p_nom/1000  # in kW

                a_chp = 0.08 * (1 + 0.08) ** 15 / ((1 + 0.08) ** 15 - 1)    # annuity factor
                chp_invest = chp_cost.calc_invest_cost_chp(p_el_nom=p_chp_nom,
                                                           method='asue2015',
                                                           with_inst=True,
                                                           use_el_input=True,
                                                           q_th_nom=None)
                cost_cap.append(chp_invest * a_chp)
                cost_dem.append((q_chp_nom)/eta_th * t_ann_op * 0.0661)
                rev.append(p_chp_nom * t_ann_op * get_el_feedin_tariff_chp(q_chp_nom))

                # Calculate estimated costs for thermal energy storage
                v_tes = q_chp_nom * 60  # in liter

                a_tes = 0.08 * (1 + 0.08) ** 20 / ((1 + 0.08) ** 20 - 1)    # annuity factor
                tes_invest = tes_cost.calc_invest_cost_tes(v_tes/1000, method='spieker')

                cost_cap.append(tes_invest * a_tes)
                rev.append(get_subs_tes_chp(chp_ratio, v_tes, tes_invest, p_chp_nom))
                rev.append(get_subs_minichp(p_chp_nom, q_chp_nom, v_tes))

                # Calculate costs for Boiler
                q_boiler_nom = max(max(th_LDC) - q_nom, 0)/1000

                a_boiler = 0.08 * (1 + 0.08) ** 18 / ((1 + 0.08) ** 18 - 1)    # annuity factor
                boiler_invest = boiler_cost.calc_abs_boiler_cost(q_boiler_nom, method='viess2013')

                cost_cap.append(boiler_invest * a_boiler)
                cost_dem.append((q_total/1000 - q_chp_nom * t_ann_op)/0.8*0.0661)  # operational costs for boiler

                costs_total = sum(cost_cap) + sum(cost_dem) - sum(rev)

                array_q_nom.append(q_nom)
                array_t_x.append(t_x)
                array_t_ann_op.append(t_ann_op)
                array_deckung.append((t_ann_op * q_nom) / q_total)
                array_costs.append(costs_total)

                # Choose current option if best option so far
                if costs_total < best_costs:
                    best_sol_costs = (eta_el, eta_th, p_nom, q_nom, t_x, t_ann_op)
                    best_costs = costs_total

            (eta_el, eta_th, p_nom, q_nom, t_x, t_ann_op) = best_sol_costs

        else:
            return None

    # ---------------- Method 1: EEWaermeG ----------------

    elif method == 1:

        eewg = False
        count = 0

        # Requirement are at least 50% heat per year from chp
        # Calculate sufficient th.power for CHP for average operation
        q_chp = 0.5 * q_total / 8760

        # Choose appropriate device and calculate estimated operation time
        [eta_el, eta_th, p_nom, q_nom] = choose_chp(q_chp)
        (t_ann_op, t_x) = get_chp_ann_op_time(q_nom, th_LDC)

        while not eewg:
            # Calculate ratio of chp heat usage (min. 50% necessary)
            ee_ratio = q_nom * t_ann_op / q_total

            if ee_ratio > 0.5:

                # calculate primary energy for separate production
                refeta_th = 0.85  # th. reference efficiency rate for devices older than 2016 (natural gas)
                refeta_el = 0.525  # el. reference efficiency rate for devices built between 2012 and 2015 (natural gas)

                # Primary energy savings in % calculated according to EU directive 2012/27/EU
                pee = (1 - 1 / ((eta_th / refeta_th) + (eta_el / refeta_el))) * 100

                # PE savings for CHP with el.power >= 1 MW have to be at least 10%
                if p_nom >= 1000000:
                    if pee >= 10:
                        eewg = True
                        break

                # PE savings for CHP with el. power < 1 MW have to be existent
                else:
                    if pee > 0:
                        eewg = True
                        break

                if ee_ratio >= 1:
                    print('EEWaermeG not satisfied: unrealistic values! (Q_chp >= Q_total)')
                    break

            # Raise th.power with 5% per iteration if conditions for EEWaermeG were not met
            q_chp = 0.5 * q_total / 8760 + count * q_total / (8760 * 100)
            [eta_el, eta_th, p_nom, q_nom] = choose_chp(q_chp)
            (t_ann_op, t_x) = get_chp_ann_op_time(q_nom, th_LDC)
            count += 5

    # ---------------- Method 2: BAFA support ----------------

    elif method == 2:

        # best possible full-load-hours (top border)
        chp_flh = 7000

        # Calculate CHP th.power for max full load hours
        q_chp = th_LDC[chp_flh]

        # Choose appropriate device and calculate estimated operation time
        [eta_el, eta_th, p_nom, q_nom] = choose_chp(q_chp)
        (t_ann_op, t_x) = get_chp_ann_op_time(q_nom, th_LDC)

        while True:
            # BAFA subsidy applicable if 75% of annual heat demand are supplied by CHP
            if (q_nom * t_ann_op / q_total) >= 0.75:

                print('CHP: BAFA funding for LHN possible! Coverage: ' + str(
                    round(q_nom * t_ann_op * 100 / q_total, 2)) + '%')
                print('Full load hours:', t_x, 'h/a; Annual operation time:', t_ann_op, 'h/a')
                break

            # if annual CHP heat supply ratio is smaller than 75%, lower flh (raises CHP th.power)
            else:
                chp_flh -= 75

                if chp_flh > 1000:
                    q_chp = th_LDC[chp_flh]
                    [eta_el, eta_th, p_nom, q_nom] = choose_chp(q_chp)
                    (t_ann_op, t_x) = get_chp_ann_op_time(q_nom, th_LDC)
                    print(round(q_nom * t_ann_op * 100 / q_total,2),'%')

                # break if full load hours are below 1000 h/yr
                else:
                    print('CHP: BAFA funding for LHN not possible!')
                    return None

    # unknown method
    else:
        raise Exception('Invalid input for method!')

    return eta_el, eta_th, p_nom, q_nom, t_x, t_ann_op


def get_LDC(curve):
    """
    Calculates load duration curve (Jahresdauerlinie)

    Parameters
    ----------
    curve : thermal or electrical curve

    Returns
    -------
    sorted curve : sorted load duration curve
    """
    return sorted(curve, reverse=True)


def get_t_demand_list(temp_curve, th_curve):
    """
    Sorts thermal energy demand based on values of ambient temperatures.

    Parameters
    ----------
    temp_curve : list of ambient temperatures for one year
    th_curve : list of thermal energy demand for one year

    Returns
    -------
    t_demand_curve : thermal energy curve sorted based on ambient temperature values
    """
    return [th_demand for _, th_demand in sorted(zip(temp_curve, th_curve))]


def get_chp_ann_op_time(q_nom, th_LDC):
    """
    Calculates annual operation time and full load hours of chp

    Parameters
    ----------
    q_nom   : Nominal thermal power of chp
    th_LDC  : thermal Load duration curve

    Returns
    -------
    t_ann_operation : total annual operation time of chp
    t_x             : Full load hours of chp
    """

    # calculate annual operation time according to Krimmling 2011
    for q_m in th_LDC:

        # find crossing point on LDC (indicates full load hours)
        if q_m <= q_nom:
            t_x = th_LDC.index(q_m)
            break
    else:
        print('Warning! No crossing point between CHP th.power and LDC found. Check parameters or add devices!')
        return 0, 0

    # Find point in time, when area between t:t_x and t_x:8760 are the same size (see Krimmling p.131, Abb.4-15)

    # difference between areas
    delta_a = 8760 * th_LDC[0]

    # make ldc numpy array
    ldc = np.array(th_LDC)

    # iterate through timesteps between full load hours of chp and end of year
    for t in range(t_x, 8760):

        # area 1
        a1 = q_m * (t - t_x) - np.sum(ldc[t_x:t])
        # area 2
        a2 = np.sum(ldc[t:8760])

        # if difference between areas is bigger than last iteration
        if delta_a <= abs(a2 - a1):

            # t-1 indicates index where a1 is (almost) a2 -> estimated annual hours of operation
            t_ann_operation = t - 1
            return t_ann_operation, t_x

        else:
            delta_a = a2 - a1


def choose_chp(q_ideal, method=0):
    """
    Choose CHP device
    Method 0: Return device with desired thermal power and average effiency
    Method 1: Out of catalogue of available devices

    Parameters
    ----------
    q_ideal : exact thermal power needed of chp

    Returns
    -------
    specs : list with specifications of chp device [eta_el, eta_th, p_nom, q_nom]
    """

    if method == 0:
        q_nom = q_ideal
        #eta_el = 0.27  # average for real devices
        #eta_th = 0.65  # average for real devices
        eta_el = 0.45   # default in pyCity_calc
        eta_th = 0.45   # default in pyCity_calc

        # Calculate el.power based on efficiency and ideal th.power
        p_nom = round(q_nom/eta_th * eta_el/10)*10

        return eta_el, eta_th, p_nom, q_nom

    else:
        # TODO: Import data from excel
        # [eta_el, eta_th, p_nom, q_nom] - (Source: BHKW-Kenndaten 2014, S.26)
        chp_list = {'vai1': [0.263, 0.658, 1000, 2500], 'intelli': [0.245, 0.613, 2600, 6500],
                    'vai2': [0.25, 0.667, 3000, 8000], 'kirsch': [0.19, 0.76, 1900, 9000],
                    'vai3': [0.247, 0.658, 4700, 12500], 'ecp': [0.286, 0.644, 6000, 13500],
                    'vie': [0.27, 0.671, 6000, 14900], 'hoef': [0.27, 0.664, 7000, 17200],
                    'rmb7.2': [0.263, 0.657, 7200, 18000],'oet8': [0.268, 0.633, 8000, 19000],
                    'xrgi9': [0.289, 0.641, 9000, 20000], 'kwe': [0.268, 0.818, 7500, 22900],
                    'rmb11.0': [0.289, 0.632, 11000, 24000], 'oet12': [0.279, 0.605, 12000, 26000],
                    'motat': [0.279, 0.651, 12000, 28000],'xrgi15': [0.307, 0.613, 15000, 30000],
                    'ews': [0.711, 0.311, 14000, 32000], 'asv1534': [0.306, 0.694, 15000, 34000],
                    'sb16': [0.314, 0.72, 16000, 36700], 'enrtc': [0.323, 0.629, 20000, 39000],
                    'xrgi20': [0.32, 0.64, 20000, 40000]}

        # define starting specs
        if q_ideal < 2500:
            specs = chp_list['vai1']
        else:
            specs = [0, 0, 0, 0]

        # choose most suitable chp regarding th.power
        for dev in chp_list.values():
            q_nom = dev[3]
            if abs(q_nom-q_ideal) < abs(specs[3]-q_ideal):
                specs = dev[:]

        return specs


def get_el_feedin_tariff_chp(q_nom, el_feedin_epex=0.02978, vnn=0.01):
    """
    Calculates feed-in tariff for CHP-produced electricity.

    Parameters
    ----------
    q_nom : nominal thermal power of chp in kW
    el_feedin_epex : epex price for electricity in Euro/kWh
    vnn : avoided grid charges ("vermiedenes Netznutzungsentgelt") in Euro/kWh

    Returns
    -------
    feed-in tariff in EUR/kWh
    """

    # KWKG 2016 revenues for el. feed-in + feedin price from epex + avoided grid charges
    if q_nom < 50:
        return 0.08+el_feedin_epex+vnn  # Euro/kWh, only paid for 60.000 flh
    elif 50 <= q_nom < 100:
        return 0.06+el_feedin_epex+vnn  # Euro/kWh, only paid for 30.000 flh
    elif 100 <= q_nom < 250:
        return 0.05+el_feedin_epex+vnn  # Euro/kWh, only paid for 30.000 flh
    elif 250 <= q_nom < 2000:
        return 0.044+el_feedin_epex+vnn  # Euro/kWh, only paid for 30.000 flh
    else:  # q_nom > 2000:
        return 0.031+el_feedin_epex+vnn  # Euro/kWh, only paid for 30.000 flh


def get_subs_minichp(p_nom, q_nom, v_tes):
    """
    Calculate BAFA subsidy for mini chp devices.

    Parameters
    ----------
    p_nom : chp el. power in kW
    q_nom : chp th. power in kW
    v_tes : volume of thermal energy storage in liter

    Returns
    -------
    bafa_subs_chp : subsidy for mini-chp
    """

    # BAFA subsidy for Mini-CHP (CHP device must be listed on BAFA-list)
    bafa_subs_chp = 0

    if v_tes > 0:

        # el.power smaller than 20 kW and TES-volume at least 60 l/kW_th
        if p_nom < 20 and v_tes/q_nom >= 60:

            if p_nom < 1:
                bafa_subs_chp = 1900

            elif p_nom < 4:
                bafa_subs_chp = 1900 + (p_nom / 1000 - 1) * 300

            elif p_nom < 10:
                bafa_subs_chp = 1900 + 3 * 300 + (p_nom / 1000 - 4) * 100

            else:  # bes.chp.pNominal < 20:
                bafa_subs_chp = 1900 + 3 * 300 + 6 * 100 + (p_nom / 1000 - 10) * 10

    return bafa_subs_chp


def get_subs_tes_chp(chp_ratio, v_tes, tes_invest, p_nom):
    """
    Calculate KWKG subsidy for TES in combination with CHP

    Parameters
    ----------
    chp_ratio : chp_heat/total_heat per year
    v_tes : tes volume in liter
    tes_invest
    p_nom : el. power in kW

    Returns
    -------
    kwkg_subs_tes : amount of subsidy
    """

    kwkg_subs_tes = 0

    # TES volume in m3
    v_m3 = v_tes/1000

    # subsidy applies only for systems with ratio of chp heat per year higher than 50%
    if chp_ratio >= 0.5:

        if 1.0 <= v_m3 <= 50.0:
            kwkg_subs_tes = 250 * v_m3

        elif v_m3 > 50:
            kwkg_subs_tes = 0.3 * tes_invest

        else:
            if v_m3 >= 0.3 * p_nom:
                kwkg_subs_tes = 250 * v_m3

    return kwkg_subs_tes


def get_bafa_subs_hp(q_nom, spf):
    """
    BAFA subsidy for a/w heat pumps with nominal power <= 100 kW and spf >= 3.5

    heat pump must be used for:
        - combined space heating and dhw
        - only space heating if dhw is generated with renewable energy
        - generating heat for lhn

    Values only for retrofit; subsidy for new buildings is lower (not implemented)

    Parameters
    ----------
    q_nom : thermal nominal power of heat pump in kW
    spf : seasonal performance factor ("Jahresarbeitszahl")

    Returns
    -------
    subs : amount of subsidy
    """
    subs = 0

    # innovation subsidy
    if q_nom <= 100 and spf >= 4.5:
        if q_nom < 32.5:
            subs = 1950
        else:
            subs = 60*q_nom

    # base subsidy
    if q_nom <= 100 and spf >= 3.5:
        if q_nom < 32.5:
            subs = 1300
        else:
            subs = 40*q_nom

    return subs


def get_kfw_subs_430(invest_cost):
    '''
    KfW subsidy for single measures regarding program 430. Currently only applicable for first connection to lhn.
    For further constraints see KfW website.

    Parameters
    ----------
    invest_cost : invest cost of single measure

    Returns
    -------
    kfw_subs_430 : possible subsidy from KfW
    '''

    kfw_subs_430 = invest_cost * 0.1

    return kfw_subs_430