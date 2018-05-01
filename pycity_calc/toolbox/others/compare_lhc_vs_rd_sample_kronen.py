#!/usr/bin/env python
# coding=utf-8
"""
Compare latin hypercube sampling with randomized sampling
(compare QMC and MC economic and ecologic results)
"""
from __future__ import division

import os
import warnings
import pickle
import time

import matplotlib.pyplot as plt

import pycity_base.classes.supply.BES as BES
import pycity_base.classes.supply.PV as PV

import pycity_calc.energysystems.boiler as boi
import pycity_calc.economic.city_economic_calc as citecon
import pycity_calc.environments.germanmarket as gmarket
import pycity_calc.simulation.energy_balance.city_eb_calc as citeb
import pycity_calc.economic.annuity_calculation as annu
import pycity_calc.toolbox.mc_helpers.mc_runner as mcrun


def main():

    sampling_method = 'lhc'
    #  Options: 'lhc' (latin hypercube) or 'random'

    nb_runs = 100  # Number of MC runs
    do_sampling = True  # Perform initial sampling or use existing samples

    #  ##################################################################

    #  City pickle filename
    city_file = 'aachen_kronenberg_6.pkl'

    #  Path to load file
    this_path = os.path.dirname(os.path.abspath(__file__))
    path_city_file = os.path.join(this_path, 'input', city_file)

    #  Load kronenberg
    city = pickle.load(open(path_city_file, mode='rb'))

    #  Workaround: Add additional emissions data, if necessary
    try:
        print(city.environment.co2emissions.co2_factor_pv_fed_in)
    except:
        msg = 'co2em object does not have attribute co2_factor_pv_fed_in. ' \
              'Going to manually add it.'
        warnings.warn(msg)
        city.environment.co2emissions.co2_factor_pv_fed_in = 0.651

    #  Extract single building / delete all unnecessary buildings
    list_remove = [1002, 1003, 1004, 1005, 1006]
    b_id = 1001

    for n in list_remove:
        city.remove_building(node_number=n)

    #  Add boiler + pv
    area = 50
    eta = 0.125
    beta = 35
    pv_simple = PV.PV(environment=city.environment,
                      area=area, eta=eta, beta=beta)

    q_boiler = 120000
    eta_boi = 0.95
    lal_boi = 0
    boiler = boi.BoilerExtended(environment=city.environment,
                                q_nominal=q_boiler,
                                eta=eta_boi,
                                lower_activation_limit=lal_boi)

    #  Add energy systems to bes
    bes = BES.BES(environment=city.environment)
    bes.addMultipleDevices([pv_simple, boiler])

    #  Add bes to building
    city.nodes[b_id]['entity'].addEntity(entity=bes)

    #  #####################################################################
    #  Generate object instances
    #  #####################################################################

    start_time = time.time()

    #  Generate german market instance (if not already included in environment)
    ger_market = gmarket.GermanMarket()

    #  Add GermanMarket object instance to city
    city.environment.prices = ger_market

    #  Generate annuity object instance
    annuity_obj = annu.EconomicCalculation()

    #  Generate energy balance object for city
    energy_balance = citeb.CityEBCalculator(city=city)

    city_eco_calc = citecon.CityAnnuityCalc(annuity_obj=annuity_obj,
                                            energy_balance=energy_balance)

    #  Hand over initial city object to mc_runner
    mc_run = mcrun.McRunner(city_eco_calc=city_eco_calc)

    # Perform MC run
    #  Perform Monte-Carlo uncertainty analysis
    #  #####################################################################
    (dict_samples_const, dict_samples_esys, dict_res, dict_mc_setup,
     dict_profiles_lhc, dict_mc_cov) = \
        mc_run.run_mc_analysis(nb_runs=nb_runs,
                               failure_tolerance=0,
                               do_sampling=do_sampling,
                               prevent_printing=False,
                               heating_off=True,
                               sampling_method=sampling_method,
                               load_sh_mc_res=False,
                               path_mc_res_folder=None,
                               use_profile_pool=False,
                               gen_use_prof_method=0,
                               path_profile_dict=None,
                               random_profile=False,
                               load_city_n_build_samples=
                               False,
                               path_city_sample_dict=None,
                               path_build_sample_dict=None,
                               eeg_pv_limit=True,
                               use_kwkg_lhn_sub=False,
                               calc_th_el_cov=False,
                               dem_unc=True,
                               el_mix_for_chp=False,
                               el_mix_for_pv=False
                               )

    #  Evaluation
    #  #####################################################################
    path_save_res = os.path.join(this_path, 'output', 'lhc_vs_rd')

    if not os.path.isdir(path_save_res):
        os.makedirs(path_save_res)

    if sampling_method == 'lhc':
        path_res = os.path.join(path_save_res, 'lhc_dict_res.pkl')
        path_sample_const = os.path.join(path_save_res, 'lhc_dict_city.pkl')
        path_sample_esys = os.path.join(path_save_res, 'lhc_dict_build.pkl')
        path_setup = os.path.join(path_save_res, 'lhc_dict_setup.pkl')

    else:
        path_res = os.path.join(path_save_res, 'rd_dict_res.pkl')
        path_sample_const = os.path.join(path_save_res, 'rd_dict_city.pkl')
        path_sample_esys = os.path.join(path_save_res, 'rd_dict_build.pkl')
        path_setup = os.path.join(path_save_res, 'rd_dict_setup.pkl')

    pickle.dump(dict_res, open(path_res, mode='wb'))
    print('Saved results dict to: ', path_res)
    print()

    pickle.dump(dict_samples_const, open(path_sample_const, mode='wb'))
    print('Saved sample dict to: ', path_sample_const)
    print()

    pickle.dump(dict_samples_esys, open(path_sample_esys, mode='wb'))
    print('Saved sample dict to: ', path_sample_esys)
    print()

    pickle.dump(dict_mc_setup, open(path_setup, mode='wb'))
    print('Saved mc settings dict to: ', path_setup)
    print()

    # if dict_profiles_lhc is not None:
    #     pickle.dump(dict_profiles_lhc, open(path_profiles, mode='wb'))
    #     print('Saved profiles dict to: ', path_profiles)
    #     print()
    #
    # if calc_th_el_cov and dict_mc_cov is not None:
    #     pickle.dump(dict_mc_cov, open(path_mc_cov, mode='wb'))
    #     print('Saved dict_mc_cov to: ', path_mc_cov)
    #     print()

    print('Nb. failed runs: ', str(len(dict_mc_setup['idx_failed_runs'])))
    print()

    print('Indexes of failed runs: ', str(dict_mc_setup['idx_failed_runs']))
    print()

    stop_time = time.time()
    time_delta = round(stop_time - start_time)

    print('Execution time for MC-Analysis (without city generation) in'
          ' seconds: ', time_delta)

    array_annuity = dict_res['annuity']
    array_co2 = dict_res['co2']
    array_sh = dict_res['sh_dem']

    plt.hist(array_annuity, bins='auto')
    plt.xlabel('Annuity in Euro/a')
    plt.ylabel('Number')
    plt.show()
    plt.close()

    plt.hist(array_co2, bins='auto')
    plt.xlabel('Emissions in kg/a')
    plt.ylabel('Number')
    plt.show()
    plt.close()

    plt.hist(array_sh, bins='auto')
    plt.xlabel('Space heating demand in kWh/a')
    plt.ylabel('Number')
    plt.show()
    plt.close()

if __name__ == '__main__':
    main()
