
import numpy as np
import matplotlib.pyplot as plt

import pycity_base.classes.supply.BES as BES
import pycity_base.classes.supply.Boiler as Boiler

import pycity_base.classes.supply.CHP as CHP
import pycity_calc.economic.energy_sys_cost.chp_cost as chp_cost
import pycity_calc.economic.energy_sys_cost.tes_cost as tes_cost
import pycity_calc.economic.energy_sys_cost.boiler_cost as boiler_cost

import pycity_calc.energysystems.heatPumpSimple as HP

def dim_decentral_hp(environment, sh_curve, t_biv=-5, tMax=55, lowerActivationLimit=0.5, tSink=45):

    # monoenergetic operation
    t_dem_ldc = get_t_demand_list(environment.weather.tAmbient, sh_curve)  # ldc with sh-demand and tAmbient
    # plt.plot(sorted(city.environment.weather.tAmbient), t_dem_ldc)

    for i in range(len(t_dem_ldc)):
        if sorted(environment.weather.tAmbient)[i] > t_biv:
            biv_ind = i - 1
            q_hp_biv = max(t_dem_ldc[biv_ind:-1])  # highest demand before bivalence point should be met
            # q_hp_biv = t_dem_ldc[biv_ind]
            break
    else:
        raise Exception('Error in calculation of demand in bivalence point')

    # choose_device('hp',q_hp_biv)
    #plt.plot([min(environment.weather.tAmbient), max(environment.weather.tAmbient)], [q_hp_biv, q_hp_biv],'r')
    #plt.show()

    return q_hp_biv, tMax, lowerActivationLimit, tSink, t_dem_ldc, biv_ind

def dim_decentral_chp(th_LDC, q_total, method=0):

    # ---------------- Method 0: Krimmling and interviews ----------------
    if method == 0:
        print('Method 0')
        # Set minimum for q_chp
        q_chp = 0.1 * max(th_LDC)
        [eta_el, eta_th, p_nom, q_nom] = choose_chp(q_chp)
        (t_ann_op_max, t_x_max) = get_chp_ann_op_time(q_nom, th_LDC)  # (annual operation time, full load hours)

        # Set minimum for flh
        chp_flh = 4000
        q_chp = th_LDC[chp_flh]
        [eta_el, eta_th, p_nom, q_nom] = choose_chp(q_chp)
        (t_ann_op_min, t_x_min) = get_chp_ann_op_time(q_nom, th_LDC)

        if t_x_min < t_x_max:
            best_costs = 1000000000
            best_sol_costs = 0, 0, 0, 0, 0

            array_q_nom = []
            array_t_x = []
            array_t_ann_op = []
            array_deckung = []
            array_costs = []

            for t in range(t_x_min, t_x_max, 20):
                cost_cap = []
                cost_op = []
                rev = []

                q_chp = th_LDC[t]
                [eta_el, eta_th, p_nom, q_nom] = choose_chp(q_chp)
                (t_ann_op, t_x) = get_chp_ann_op_time(q_nom, th_LDC)

                # Calculate costs for chp
                a_chp = 0.08 * (1 + 0.08) ** 15 / ((1 + 0.08) ** 15 - 1)  # annuity factor
                chp_invest = chp_cost.calc_invest_cost_chp(p_nom / 1000, method='asue2015', with_inst=True,
                                                           use_el_input=True, q_th_nom=None)
                cost_cap.append(chp_invest * a_chp)
                cost_op.append((q_nom / 1000) / eta_th * t_ann_op * 0.0661)
                rev.append(p_nom / 1000 * t_ann_op * get_el_feedin_tariff_chp(q_nom))

                # TODO: weitere Förderungen eintragen

                # Calculate costs for thermal energy storage
                v_tes = (q_nom / 1000) * 60 / 1000  # (in m3) Förderung von Speichern für Mini-BHKW durch BAFA bei Speichergrößen über 60 l/kW_th
                a_tes = 0.08 * (1 + 0.08) ** 20 / ((1 + 0.08) ** 20 - 1)  # annuity factor
                cost_cap.append(tes_cost.calc_invest_cost_tes(v_tes, method='spieker') * a_tes)
                rev.append(get_subs_minichp(p_nom, v_tes))

                # Calculate costs for Boiler
                q_boiler = max(th_LDC) - q_nom
                a_boiler = 0.08 * (1 + 0.08) ** 18 / ((1 + 0.08) ** 18 - 1)  # annuity factor
                cost_cap.append(boiler_cost.calc_abs_boiler_cost(q_boiler / 1000, method='viess2013') * a_boiler)
                cost_op.append(((q_total - q_nom * t_ann_op) / 1000) / 0.8 * 0.0661)

                costs_total = sum(cost_cap) + sum(cost_op) - sum(rev)

                array_q_nom.append(q_nom)
                array_t_x.append(t_x)
                array_t_ann_op.append(t_ann_op)
                array_deckung.append((t_ann_op * q_nom) / q_total)
                array_costs.append(costs_total)

                if costs_total < best_costs:
                    best_sol_costs = (eta_el, eta_th, p_nom, q_nom, t_x, t_ann_op)
                    best_costs = costs_total

            plt.figure(1)
            plt.plot(array_costs)

            #plt.figure(2)

            (eta_el, eta_th, p_nom, q_nom, t_x, t_ann_op) = best_sol_costs

        else:
            return None

    # ---------------- Method 1: EEWaermeG ----------------
    # TODO: Nochmal checken ob Bedingungen für zentral/dezentral gleich sind
    elif method == 1:
        print('Method 1')
        eewg = False
        count = 0

        # Mindestwert 50% Deckung
        q_chp = 0.5 * q_total / 8760
        [eta_el, eta_th, p_nom, q_nom] = choose_chp(q_chp)
        (t_ann_op, t_x) = get_chp_ann_op_time(q_nom, th_LDC)
        # TODO: Evtl. weitere Einschränkungen miteinbauen (Möglichkeit mit der längsten Laufzeit aussuchen)
        while not eewg:
            ee_ratio = q_nom * t_ann_op / q_total
            if ee_ratio > 0.5:
                # calculate primary energy
                refeta_th = 0.85  # th. reference efficiency rate for devices older than 2016 (natural gas)
                refeta_el = 0.525  # el. reference efficiency rate for devices built between 2012 and 2015 (natural gas)

                # Primary energy savings in % calculated according to EU directive 2012/27/EU
                pee = (1 - 1 / ((eta_th / refeta_th) + (eta_el / refeta_el))) * 100
                if p_nom >= 1000000:
                    if pee >= 10:
                        eewg = True
                        break
                else:
                    if pee > 0:
                        eewg = True
                        break
                if ee_ratio >= 1:
                    print('EEWärmeG not satisfied: unrealistic values! (Q_chp >= Q_total)')
                    break

            q_chp = 0.5 * q_total / 8760 + count * q_total / (
                8760 * 100)  # Mindestwert 50% Deckung + 5% der Gesamtleistung je Durchlauf
            [eta_el, eta_th, p_nom, q_nom] = choose_chp(q_chp)
            (t_ann_op, t_x) = get_chp_ann_op_time(q_nom, th_LDC)  # (Jahreslaufzeit, Volllaststunden)
            count += 5
    else:
        raise Exception('Invalid input for method!')

    return eta_el, eta_th, p_nom, q_nom, t_x, t_ann_op


def dim_central_chp(th_LDC, q_total, district_type, method=0):
    """

    Parameters
    ----------
    city            : city_object
    district_type   : string
    method          : integer
        = 0:  Standard approach (Krimmling 2011):
                - Q_th > 10% (< 20%) of max. thermal demand
                - Full-Load-hours preferably > 6000 h/a (minimum 5000 h/a)
        = 1:  Approach to satisfy EEWaermeG without any other constraints
        = 2:  Choose device where BAFA-Support for heating networks is available (Q_chp >= 75% of total annual heat
              demand) as described in KWKG without any other constraints

    Returns         : chp
    -------

    """

    # ---------------- Method 0: Krimmling and interviews ----------------
    if method == 0:
        print('Method 0')
        # Set minimum for q_chp
        q_chp = 0.1*max(th_LDC)
        [eta_el, eta_th, p_nom, q_nom] = choose_chp(q_chp)
        (t_ann_op_max, t_x_max) = get_chp_ann_op_time(q_nom, th_LDC)  # (annual operation time, full load hours)

        # Set minimum for flh
        chp_flh = 4500
        q_chp = th_LDC[chp_flh]
        [eta_el, eta_th, p_nom, q_nom] = choose_chp(q_chp)
        (t_ann_op_min, t_x_min) = get_chp_ann_op_time(q_nom, th_LDC)

        if t_x_min < t_x_max:
            best_costs = 1000000000
            best_sol_costs = 0,0,0,0,0

            array_q_nom = []
            array_t_x = []
            array_t_ann_op = []
            array_deckung = []
            array_costs = []

            for t in range(t_x_min, t_x_max, 20):
                cost_cap = []
                cost_op = []
                rev = []

                q_chp = th_LDC[t]
                [eta_el, eta_th, p_nom, q_nom] = choose_chp(q_chp)
                (t_ann_op, t_x) = get_chp_ann_op_time(q_nom, th_LDC)

                # Calculate costs for chp
                a_chp = 0.08 * (1 + 0.08) ** 15 / ((1 + 0.08) ** 15 - 1)    # annuity factor
                chp_invest = chp_cost.calc_invest_cost_chp(p_nom / 1000, method='asue2015', with_inst=True,
                                                           use_el_input=True, q_th_nom=None)
                cost_cap.append(chp_invest*a_chp)
                cost_op.append((q_nom/1000)/eta_th * t_ann_op * 0.0661)
                rev.append(p_nom/1000 * t_ann_op * get_el_feedin_tariff_chp(q_nom))

                # TODO: weitere Förderungen eintragen

                # Calculate costs for thermal energy storage
                v_tes = (q_nom / 1000) * 60/1000  # (in m3) Förderung von Speichern für Mini-BHKW durch BAFA bei Speichergrößen über 60 l/kW_th
                # TODO: Wie sieht die Dimensionierung für KWK-Anlagen über 30 kW aus? Sind die 20% realistisch?
                a_tes = 0.08 * (1 + 0.08) ** 20 / ((1 + 0.08) ** 20 - 1)    # annuity factor
                cost_cap.append(tes_cost.calc_invest_cost_tes(v_tes, method='spieker')*a_tes)
                rev.append(get_subs_minichp(p_nom, v_tes))

                # Calculate costs for Boiler
                q_boiler = max(th_LDC) - q_nom
                a_boiler = 0.08 * (1 + 0.08) ** 18 / ((1 + 0.08) ** 18 - 1)    # annuity factor
                cost_cap.append(boiler_cost.calc_abs_boiler_cost(q_boiler / 1000, method='viess2013')*a_boiler)
                cost_op.append(((q_total - q_nom * t_ann_op)/1000)/0.8*0.0661)

                costs_total = sum(cost_cap) + sum(cost_op) - sum(rev)

                array_q_nom.append(q_nom)
                array_t_x.append(t_x)
                array_t_ann_op.append(t_ann_op)
                array_deckung.append((t_ann_op * q_nom) / q_total)
                array_costs.append(costs_total)

                if costs_total < best_costs:
                    best_sol_costs = (eta_el, eta_th, p_nom, q_nom, t_x, t_ann_op)
                    best_costs = costs_total

            (eta_el, eta_th, p_nom, q_nom, t_x, t_ann_op) = best_sol_costs

        else:
            return None

    # ---------------- Method 1: EEWaermeG ----------------
    elif method == 1:
        print('Method 1')
        eewg = False
        count = 0

        # Mindestwert 50% Deckung
        q_chp = 0.5 * q_total / 8760
        [eta_el, eta_th, p_nom, q_nom] = choose_chp(q_chp)
        (t_ann_op, t_x) = get_chp_ann_op_time(q_nom, th_LDC)
        # TODO: Evtl. weitere Einschränkungen miteinbauen (Möglichkeit mit der längsten Laufzeit aussuchen)
        while not eewg:
            ee_ratio = q_nom * t_ann_op / q_total
            if ee_ratio > 0.5:
                # calculate primary energy
                refeta_th = 0.85  # th. reference efficiency rate for devices older than 2016 (natural gas)
                refeta_el = 0.525  # el. reference efficiency rate for devices built between 2012 and 2015 (natural gas)

                # Primary energy savings in % calculated according to EU directive 2012/27/EU
                pee = (1 - 1 / ((eta_th / refeta_th) + (eta_el / refeta_el))) * 100
                if p_nom >= 1000000:
                    if pee >= 10:
                        eewg = True
                        break
                else:
                    if pee > 0:
                        eewg = True
                        break
                if ee_ratio >= 1:
                    print('EEWärmeG not satisfied: unrealistic values! (Q_chp >= Q_total)')
                    break

            q_chp = 0.5 * q_total / 8760 + count * q_total / (
            8760 * 100)  # Mindestwert 50% Deckung + 5% der Gesamtleistung je Durchlauf
            [eta_el, eta_th, p_nom, q_nom] = choose_chp(q_chp)
            (t_ann_op, t_x) = get_chp_ann_op_time(q_nom, th_LDC)  # (Jahreslaufzeit, Volllaststunden)
            count += 5

    # ---------------- Method 2: BAFA support ----------------
    elif method == 2:
        print('Method 2')
        chp_flh = 7000  # best possible full-load-hours (not actual flh - just for dimensioning)
        q_chp = th_LDC[chp_flh]
        [eta_el, eta_th, p_nom, q_nom] = choose_chp(q_chp)
        (t_ann_op, t_x) = get_chp_ann_op_time(q_nom, th_LDC)  # (annual operation time, full load hours)

        while True:
            # Auslegung auf BAFA Förderung für Wärmenetze (75% Deckungsanteil aus KWK)
            if (q_nom * t_ann_op / q_total) >= 0.75:
                print('CHP: BAFA funding for LHN possible! Coverage: ' + str(
                    round(q_nom * t_ann_op * 100 / q_total, 2)) + '%')
                print('Full load hours:', t_x, 'h/a; Annual operation time:', t_ann_op, 'h/a')
                break
            else:
                chp_flh -= 75
                if chp_flh > 1000:
                    q_chp = th_LDC[chp_flh]
                    [eta_el, eta_th, p_nom, q_nom] = choose_chp(q_chp)
                    (t_ann_op, t_x) = get_chp_ann_op_time(q_nom, th_LDC)
                    print(round(q_nom * t_ann_op * 100 / q_total,2),'%')
                else:
                    print('CHP: BAFA funding for LHN not possible!')
                    return None
    # ------------------------------------------------------

    else:
        raise Exception('Invalid input for method!')

    # chp = CHP.CHP(city.environment, p_nom, q_nom, eta_el + eta_th)
    # if check_eewaermeg(city, chp, t_ann_op, q_total):
    #     print('CHP: Q_nom = ' + str(q_nom / 1000) + ' kW (' + str(
    #         round(q_nom * 100 / max(th_curve), 2)) + '% of Q_max) ->', t_x, 'full-load hours.')
    # else:
    #     print('EEWaermeG was not fulfilled by calculated CHP (method=' + str(method) + ')')
    #     return None

    return eta_el, eta_th, p_nom, q_nom, t_x, t_ann_op

def dim_central_tes(city):
    """

    Parameters
    ----------
    city    : city_object with BES and heat supply

    Returns : city_object with implemented TES (if necessary)
    -------

    """
    # TODO: (Reicht auch Boolean im return??)


def dim_central_boiler(city):
    """
    If other devices are already implemented in BES, boiler is used as peak supply.
    Else boiler supplies whole demand of city.

    Parameters
    ----------
    city    : city_object with BES

    Returns : city_object with implemented boiler in BES
    -------

    """
    # TODO: (Reicht auch Boolean im return??)

    print('boiler')


def get_LDC(curve):
    '''
    returns Load duration curve (Jahresdauerlinie)
    :param curve: thermal or electrical curve
    :return: load duration curve
    '''
    return sorted(curve, reverse=True)

def get_t_demand_list(temp_curve, th_curve):
    '''
    Sorts thermal energy demand based on values of ambient temperatures.

    :param temp_curve: curve of ambient temperatures
    :param th_curve: curve of thermal energy demand
    :return: thermal energy curve sorted based on ambient temperature values
    '''
    return [th_demand for _, th_demand in sorted(zip(temp_curve, th_curve))]


def get_chp_ann_op_time(q_nom, th_LDC):
    """
    Calculates annual operation time and full load hours of chp

    Parameters
    ----------
    q_nom   : Nominal thermal power of chp
    th_LDC  : thermal Load duration curve

    Returns : t_ann_operation : total annual operation time of chp
              t_x             : Full load hours of chp
    -------

    """

    # CHP-Jahreslaufzeitberechnung (annual operation time) nach Krimmling(2011)
    for q_m in th_LDC:
        if q_m <= q_nom:
            t_x = th_LDC.index(q_m)  # find crossing point on LDC (indicates full load hours)
            break
    else:
        raise Exception('No crossing point between CHP th.power and LDC found. Check parameters!')

    # Find point in time, when area between t:t_x and t_x:8760 are the same size (see Krimmling p.131, Abb.4-15)
    delta_a = 8760 * th_LDC[0]
    for t in range(t_x, 8760):
        a1 = q_m * (t - t_x) - sum(th_LDC[t_x:t])
        a2 = sum(th_LDC[t:8760])
        if delta_a <= abs(a2 - a1):
            t_ann_operation = t - 1
            return t_ann_operation, t_x
        else:
            delta_a = a2 - a1

def choose_chp(q_ideal):
    """
    Choose CHP device out of catalogue of available devices

    improvement -> add costs and more devices

    Parameters
    ----------
    q_ideal : exact thermal power needed of chp

    Returns : specs: list with specifications of chp device [eta_el, eta_th, p_nom, q_nom]
    -------

    """
    # TODO: beim letzten gefundenen Ergebnis starten um Prozess zu beschleunigen

    # Source: BHKW-Kenndaten 2014, S.26 - [eta_el, eta_th, p_nom, q_nom]
    chp_list = {'vai1':[0.263, 0.658, 1000, 2500], 'vai2':[0.25, 0.667, 3000, 8000], 'vai3':[0.247,0.658,4700,12500],
                'vie':[0.27, 0.671, 6000, 14900], 'rmb7.2':[0.263, 0.657, 7200, 18000],'oet8':[0.268,0.633,8000,19000],
                'xrgi9':[0.289,0.641,9000,20000],'rmb11.0':[0.289,0.632,11000,24000],'xrgi15':[0.307,0.613,15000,30000],
                'asv1534':[0.306,0.694,15000,34000],'sb16':[0.314,0.72,16000,36700],'xrgi20':[0.32,0.64,20000,40000]}

    specs = [0, 0, 0, 0]
    for dev in chp_list.values():
        eta_th = dev[1]
        q_nom = dev[3]
        if abs(q_nom-q_ideal) < abs(specs[3]-q_ideal):
            specs = dev[:]
    return specs

def get_el_feedin_tariff_chp(q_nom, el_feedin_epex=0.02978):
    # KWKG 2016 revenues for el. feed-in + feedin price from epex
    if q_nom < 50000:
        return 0.08+el_feedin_epex  # Euro/kWh, only paid for 60.000 flh
    elif q_nom > 50000 and q_nom < 100000:
        return 0.06+el_feedin_epex  # Euro/kWh, only paid for 30.000 flh
    elif q_nom > 100000 and q_nom < 250000:
        return 0.05+el_feedin_epex  # Euro/kWh, only paid for 30.000 flh
    elif q_nom > 250000 and q_nom < 2000000:
        return 0.044+el_feedin_epex  # Euro/kWh, only paid for 30.000 flh
    else:  # q_nom > 2000000:
        return 0.031+el_feedin_epex  # Euro/kWh, only paid for 30.000 flh

def get_subs_minichp(p_nom, v_tes):
    # BAFA subsidy for Mini-CHP (CHP device must be listed on BAFA-list)
    bafa_subs_chp = 0
    if v_tes > 0:
        if p_nom < 20000 and v_tes >= 0.06:
            if p_nom < 1000:
                bafa_subs_chp = 1900
            elif p_nom < 4000:
                bafa_subs_chp = 1900 + (p_nom / 1000 - 1) * 300
            elif p_nom < 10000:
                bafa_subs_chp = 1900 + 3 * 300 + (p_nom / 1000 - 4) * 100
            else:  # bes.chp.pNominal < 20000:
                bafa_subs_chp = 1900 + 3 * 300 + 6 * 100 + (p_nom / 1000 - 10) * 10
    return bafa_subs_chp

