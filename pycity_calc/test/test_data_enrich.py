#!/usr/bin/env python
# coding=utf-8
"""

"""
from __future__ import division
import pycity_calc.toolbox.data_enrichment.occupants.enrich_input_file as en_in_file


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
        assert (len(list_5) / nb_loops - prob_dist[4]) < 0.01 * prob_dist[4]
