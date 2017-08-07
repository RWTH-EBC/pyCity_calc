'''
function to calculate total CO2 emission of city_object. Sums up alle Co2 emission by gas and electricity consumtion.
Sold energy of CHP and PV are credited by replacing conventional electricity  production.

parameters
----------
city_object: city_object from pycity_calc
emission_object: emission_object from pycity_calc
CO2_zero_lowerbound: 'bool', define if total CO2 amount can be smaller than zero.
        True - total CO2 amount can be smaller than zero (due to elctrity replacement by chp or pv)
        False- total CO2 amount minimum is 0. No negative emissions allowed
eco_calc_instance: 'object', if CO2_ref_ch is not None
    instance from pycity_calc.economic.annuity_calculation class
CO2_ref_ch: 'float', optional,
    take change of el_mix CO_2 emission factor into acount: Average change of el_mix CO_2 emission factor per year


returns:
-------
CO2_total: 'float', total amount of CO2 emission in kg/year
'''
from __future__ import division

def CO2_emission_calc(city_object, emission_object, CO2_zero_lowerbound = False, eco_calc_instance=None):


    #  Generate emission object
    CO2_total=0

    el_co2_em = emission_object.get_co2_emission_factors(type='el_mix')
    gas_co2_em = emission_object.get_co2_emission_factors(type='gas')
    co2_factor_el_feed_in = emission_object.get_co2_emission_factors(type='el_feed_in')


    for node in city_object.nodes():

        if 'node_type' in city_object.node[node]:

            #  If node_type is building
            if city_object.node[node]['node_type'] == 'building':

                #  If entity is kind building
                if city_object.node[node]['entity']._kind == 'building':
                    #calculate CO2 emission: sum(powerin)*timestep*emissionfactor

                    if 'electrical demand' in city_object.node[node]:
                        if type(city_object.node[node]['electrical demand']) != int:

                            el_dem = sum(city_object.node[node]['electrical demand']) * city_object.environment.timer.timeDiscretization / 1000 / 3600

                            CO2_total += el_dem * el_co2_em


                    if 'fuel demand' in city_object.node[node]:
                        if type(city_object.node[node]['fuel demand']) != int:

                            gas_dem = sum(city_object.node[node]['fuel demand']) * city_object.environment.timer.timeDiscretization / 1000 / 3600

                            CO2_total += gas_dem * gas_co2_em

                    if 'chp_sold' in city_object.node[node]:

                            CHP_sold = sum(city_object.node[node]['chp_sold']) * city_object.environment.timer.timeDiscretization / 1000 / 3600

                            CO2_total -= CHP_sold * co2_factor_el_feed_in

                    if 'pv_sold' in city_object.node[node]:

                            PV_sold = sum(city_object.node[node]['pv_sold']) * city_object.environment.timer.timeDiscretization / 1000 / 3600

                            CO2_total -= PV_sold * el_co2_em

                    if CO2_zero_lowerbound == True and CO2_total < 0:
                        CO2_total = 0


    return CO2_total



