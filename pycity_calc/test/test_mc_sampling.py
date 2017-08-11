#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
from __future__ import division

import pycity_calc.toolbox.mc_helpers.building.build_unc_set_gen as mcbuild



class Test_MC_Sampling():

    def test_calc_list_mod_years_single_build(self):

        nb_samples = 100
        year_of_constr = 1970
        max_year = 2014
        time_sp_force_retro = None

        list_mod_years = \
            mcbuild.calc_list_mod_years_single_build(nb_samples=nb_samples,
                                                     year_of_constr=year_of_constr,
                                                     max_year=max_year,
                                                     time_sp_force_retro=time_sp_force_retro)

        assert len(list_mod_years) == 100
        assert min(list_mod_years) >= 1970
        assert max(list_mod_years) <= 2014

        year_of_constr = 1985
        max_year = 1986
        time_sp_force_retro = None

        list_mod_years = \
            mcbuild.calc_list_mod_years_single_build(nb_samples=nb_samples,
                                                     year_of_constr=year_of_constr,
                                                     max_year=max_year,
                                                     time_sp_force_retro=time_sp_force_retro)

        assert len(list_mod_years) == 100
        assert min(list_mod_years) >= 1985
        assert max(list_mod_years) <= 1986

        nb_samples = 100
        year_of_constr = 1960
        max_year = 2000
        time_sp_force_retro = 30

        list_mod_years = \
            mcbuild.calc_list_mod_years_single_build(nb_samples=nb_samples,
                                                     year_of_constr=year_of_constr,
                                                     max_year=max_year,
                                                     time_sp_force_retro=time_sp_force_retro)

        assert min(list_mod_years) >= 1970
        assert max(list_mod_years) <= 2000

    def test_calc_inf_samples(self):
        nb_samples = 100

        list_inf = mcbuild.calc_inf_samples(nb_samples, mean=0, sdev=1,
                                            max_val=3)

        assert len(list_inf) == nb_samples
        assert min(list_inf) >= 0
        assert max(list_inf) <= 10

    def test_calc_list_net_floor_area_sampling(self):

        mcbuild.calc_list_net_floor_area_sampling(mean=500, sigma=10,
                                                  nb_of_samples=2)

    def test_calc_list_dormer_samples(self):
        nb_samples = 100

        list_dormer, list_attic, list_cellar, list_const = \
            mcbuild.calc_list_dormer_samples(nb_samples=nb_samples)

        assert len(list_dormer) == nb_samples
        assert len(list_attic) == nb_samples
        assert len(list_cellar) == nb_samples
        assert len(list_const) == nb_samples

        assert min(list_dormer) >= 0
        assert max(list_dormer) <= 1

        assert min(list_attic) >= 0
        assert max(list_attic) <= 3

        assert min(list_cellar) >= 0
        assert max(list_cellar) <= 3

        assert min(list_const) >= 0
        assert max(list_const) <= 1






