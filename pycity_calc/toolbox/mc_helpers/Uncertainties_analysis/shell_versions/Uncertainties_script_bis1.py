#!/usr/bin/env python
# coding=utf-8

import pycity_calc.toolbox.mc_helpers.Uncertainties_analysis.Uncertainties_script as main_script

if __name__ == '__main__':

    main_script.do_uncertainty_analysis(Nsamples=10000, time=10, Is_k_esys_parameters=True, time_sp_force_retro=40,
                            max_retro_year=2014, Is_k_user_parameters=True, interest_fix=0.05,
                            MC_analyse_total=True, Confident_intervall_pourcentage=90, save_result=True,
                            save_path_mc='D:\jsc-les\\pyCity_calc_github\\pycity_calc\\toolbox\\mc_helpers\\Uncertainties_analysis\\output\\Sc_bis1',
                            results_name='mc_results.txt', results_excel_name='mesresultats',
                            Is_k_building_parameters=True, esys_filename='City_lolo_esys_bis1_Sc5.txt',
                            gen_e_net=True, network_filename='lolo_networks.txt',
                            city_pickle_name='aachen_kronenberg_3_mfh_ref_1.pkl')
