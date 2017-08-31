#!/usr/bin/env python
# coding=utf-8
"""

"""
from __future__ import division

import os

import pycity_calc.toolbox.data_enrichment.occupants.enrich_input_file as en_in_file
import pycity_calc.cities.scripts.city_generator.city_generator as citgen
import pycity_calc.toolbox.data_enrichment.enrich_app_occ_and_retrofit as eaor

class Test_DataEnrich():

    def test_estimate_occ_per_ap(self):

        prob_dist = [0.405, 0.345, 0.125, 0.092, 0.033]

        list_1 = []
        list_2 = []
        list_3 = []
        list_4 = []
        list_5 = []

        nb_loops = 1000000

        for i in range(nb_loops):

            occ = en_in_file.estimate_occ_per_ap(prob_dist)

            if occ == 1:
                list_1.append(occ)
            elif occ == 2:
                list_2.append(occ)
            elif occ == 3:
                list_3.append(occ)
            elif occ == 4:
                list_4.append(occ)
            elif occ == 5:
                list_5.append(occ)

        # Occ. probabilities should be close to original probability dist.
        assert (len(list_1) / nb_loops - prob_dist[0]) < 0.01 * prob_dist[0]
        assert (len(list_2) / nb_loops - prob_dist[1]) < 0.01 * prob_dist[1]
        assert (len(list_3) / nb_loops - prob_dist[2]) < 0.01 * prob_dist[2]
        assert (len(list_4) / nb_loops - prob_dist[3]) < 0.01 * prob_dist[3]
        # assert (len(list_5) / nb_loops - prob_dist[4]) < 0.01 * prob_dist[4]

    def test_est_nb_apartments(self):

        nfa = 74
        nb_app = en_in_file.est_nb_apartments(net_floor_area=nfa)
        assert nb_app == 1

        nfa = 10
        nb_app = en_in_file.est_nb_apartments(net_floor_area=nfa)
        assert nb_app == 1

        nfa = 80
        nb_app = en_in_file.est_nb_apartments(net_floor_area=nfa)
        assert nb_app == 1

        nfa = 74 * 2
        nb_app = en_in_file.est_nb_apartments(net_floor_area=nfa)
        assert nb_app == 2

        nfa = 70 * 2
        nb_app = en_in_file.est_nb_apartments(net_floor_area=nfa)
        assert nb_app == 2

        nfa = 74 * 3 - 74/2 + 1
        nb_app = en_in_file.est_nb_apartments(net_floor_area=nfa)
        assert nb_app == 3

    def test_enrich_app_occ_and_retrofit(self):

        this_path = os.path.dirname(os.path.abspath(__file__))

        #  User input
        #  ####################################################################

        #  Input and output filename
        filename = 'city_5_enrich.txt'

        #  Input and output filepath
        file_path = os.path.join(this_path, 'input_generator', filename)

        #  Check input data consistency?
        check_input = True
        #  If True, runs input data checker
        #  If False, skips input data checker

        #  Enrich buildings with number of apartments, if no number of apartments
        #  is given
        enrich_apps = True

        #  Enrich buildings with number of occupants, if no number of occupants
        #  is given
        enrich_occ = True

        #  Estimate last year of modernization, based on given thermal net space
        #  heating demand
        est_m_year = True

        #  End of user input
        #  ####################################################################

        #  Load basic city input txt file
        #  Load city district data set
        district_data = citgen.get_district_data_from_txt(path=file_path)

        if check_input:
            #  Run district data input checker
            eaor.check_district_data_set(district_data=district_data)

        if enrich_apps:
            #  Run apartment enrichment
            eaor.enrich_apartments(district_data=district_data)

        if enrich_occ:
            #  Run occupancy enrichment
            en_in_file.add_occ_to_given_app(district_data=district_data)

        if est_m_year:
            #  Estimate mod. year, based on given net space heating thermal
            #  energy demand (if no year of mod. is given)

            #  Generate dummy environment
            environment = citgen.generate_environment()

            eaor.est_mod_year(district_data=district_data,
                              environment=environment)
