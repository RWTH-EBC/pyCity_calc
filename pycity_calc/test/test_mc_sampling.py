#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
from __future__ import division

import copy
import shapely.geometry.point as point

import pycity_calc.cities.city as city
import pycity_calc.toolbox.mc_helpers.building.build_unc_set_gen as mcbuild
import pycity_calc.toolbox.mc_helpers.user.user_unc_sampling as mcuse
import pycity_calc.toolbox.mc_helpers.weather.gen_weather_set as mcweat
import pycity_calc.toolbox.mc_helpers.demand_unc_single_build as mc_build
import pycity_calc.toolbox.mc_helpers.demand_unc_city as mc_city

from pycity_calc.test.pycity_calc_fixtures import fixture_building, \
    fixture_environment, fixture_city, fixture_apartment, fixture_th_demand, \
    fixture_el_demand, fixture_detailed_building



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

    def test_calc_set_temp_samples(self):
        nb_samples = 100

        list_set_temp = \
            mcuse.calc_set_temp_samples(nb_samples, mean=20, sdev=2.5)

        assert len(list_set_temp) == nb_samples

        assert min(list_set_temp) >= 0
        assert max(list_set_temp) <= 50

    def test_calc_user_air_ex_rates(self):
        nb_samples = 100

        list_usr_inf = \
            mcuse.calc_user_air_ex_rates(nb_samples, min_value=0,
                                         max_value=1.2,
                                         pdf='nakagami')

        assert len(list_usr_inf) == nb_samples

        assert min(list_usr_inf) >= 0
        assert max(list_usr_inf) <= 10

        list_usr_inf = \
            mcuse.calc_user_air_ex_rates(nb_samples, min_value=0,
                                         max_value=1.2,
                                         pdf='triangle')

        assert len(list_usr_inf) == nb_samples

        assert min(list_usr_inf) >= 0
        assert max(list_usr_inf) <= 1.2

        list_usr_inf = \
            mcuse.calc_user_air_ex_rates(nb_samples, min_value=0,
                                         max_value=1.2,
                                         pdf='equal')

        assert len(list_usr_inf) == nb_samples

        assert min(list_usr_inf) >= 0
        assert max(list_usr_inf) <= 1.2

    def test_calc_sampling_occ_per_app(self):
        nb_samples = 100

        list_nb_occ = mcuse.calc_sampling_occ_per_app(nb_samples,
                                                      method='destatis',
                                                      min_occ=1, max_occ=5)

        assert len(list_nb_occ) == nb_samples
        assert min(list_nb_occ) >= 1
        assert max(list_nb_occ) <= 5

        list_nb_occ = mcuse.calc_sampling_occ_per_app(nb_samples,
                                                      method='equal',
                                                      min_occ=2, max_occ=3)

        assert len(list_nb_occ) == nb_samples
        assert min(list_nb_occ) >= 2
        assert max(list_nb_occ) <= 3

    def test_calc_sampling_el_demand_per_apartment(self):
        nb_samples = 100

        list_el_demands = \
            mcuse.calc_sampling_el_demand_per_apartment(nb_samples,
                                                        nb_persons=1,
                                                        type='sfh',
                                                        method='stromspiegel2017')

        assert len(list_el_demands) == nb_samples
        assert min(list_el_demands) >= 1300
        assert max(list_el_demands) <= 4000

        list_el_demands = \
            mcuse.calc_sampling_el_demand_per_apartment(nb_samples,
                                                        nb_persons=5,
                                                        type='sfh',
                                                        method='stromspiegel2017')

        assert len(list_el_demands) == nb_samples
        assert min(list_el_demands) >= 3500
        assert max(list_el_demands) <= 7500

        list_el_demands = \
            mcuse.calc_sampling_el_demand_per_apartment(nb_samples,
                                                        nb_persons=1,
                                                        type='mfh',
                                                        method='stromspiegel2017')

        assert len(list_el_demands) == nb_samples
        assert min(list_el_demands) >= 800
        assert max(list_el_demands) <= 2200

        list_el_demands = \
            mcuse.calc_sampling_el_demand_per_apartment(nb_samples,
                                                        nb_persons=5,
                                                        type='mfh',
                                                        method='stromspiegel2017')

        assert len(list_el_demands) == nb_samples
        assert min(list_el_demands) >= 2200
        assert max(list_el_demands) <= 5700

    def test_calc_sampling_dhw_per_person(self):
        nb_samples = 100

        list_dhw_vol = \
            mcuse.calc_sampling_dhw_per_person(nb_samples, pdf='equal',
                                               equal_diff=34,
                                               mean=64, std=10)
        assert len(list_dhw_vol) == nb_samples
        assert min(list_dhw_vol) >= 30
        assert max(list_dhw_vol) <= 98

        list_dhw_vol = \
            mcuse.calc_sampling_dhw_per_person(nb_samples, pdf='gaussian',
                                               equal_diff=34,
                                               mean=64, std=10)

        assert len(list_dhw_vol) == nb_samples
        assert min(list_dhw_vol) >= 0
        assert max(list_dhw_vol) <= 150

    def test_calc_dhw_ref_volume_for_multiple_occ(self):

        dhw_ref = mcuse.calc_dhw_ref_volume_for_multiple_occ(nb_occ=1,
                                                             ref_one_occ=64)

        assert dhw_ref == 64

        dhw_ref = mcuse.calc_dhw_ref_volume_for_multiple_occ(nb_occ=2,
                                                             ref_one_occ=64)

        assert dhw_ref < 64

    def test_calc_sampling_dhw_per_apartment(self):
        nb_samples = 100
        nb_persons = 3

        list_dhw_vol = \
            mcuse.calc_sampling_dhw_per_apartment(nb_samples,
                                                  nb_persons,
                                                  method='stromspiegel_2017',
                                                  pdf='equal',
                                                  equal_diff=34, mean=64,
                                                  std=10,
                                                  b_type='sfh', delta_t=35,
                                                  c_p_water=4182,
                                                  rho_water=995)

        assert len(list_dhw_vol) == nb_samples
        assert min(list_dhw_vol) >= 3 * 9
        assert max(list_dhw_vol) <= 3 * 50

        list_dhw_vol = \
            mcuse.calc_sampling_dhw_per_apartment(nb_samples,
                                                  nb_persons,
                                                  method='stromspiegel_2017',
                                                  pdf='equal',
                                                  equal_diff=34, mean=64,
                                                  std=10,
                                                  b_type='mfh', delta_t=35,
                                                  c_p_water=4182,
                                                  rho_water=995)

        assert len(list_dhw_vol) == nb_samples
        assert min(list_dhw_vol) >= 3 * 20
        assert max(list_dhw_vol) <= 3 * 40

        nb_persons = 1

        list_dhw_vol = \
            mcuse.calc_sampling_dhw_per_apartment(nb_samples,
                                                  nb_persons,
                                                  method='nb_occ_dep',
                                                  pdf='gaussian',
                                                  equal_diff=34, mean=64,
                                                  std=10,
                                                  b_type='mfh', delta_t=35,
                                                  c_p_water=4182,
                                                  rho_water=995)

        assert len(list_dhw_vol) == nb_samples
        assert min(list_dhw_vol) >= 0
        assert max(list_dhw_vol) <= 150

        list_dhw_vol = \
            mcuse.calc_sampling_dhw_per_apartment(nb_samples,
                                                  nb_persons,
                                                  method='indep',
                                                  pdf='equal',
                                                  equal_diff=34, mean=64,
                                                  std=10,
                                                  b_type='mfh', delta_t=35,
                                                  c_p_water=4182,
                                                  rho_water=995)

        assert len(list_dhw_vol) == nb_samples
        assert min(list_dhw_vol) >= 0
        assert max(list_dhw_vol) <= 150

    def test_gen_set_of_weathers(self):
        timestep = 3600
        region_nb = 5  # Region number for TRY usage
        #  (currently, 5 and 12 are available. More TRY datasets can be found
        #   on DWD website for download)
        year = 2010  # Year of TRY (2010 for current TRY or 2035 for future TRY)
        nb_weather = 5
        random_method = 'uniform'  # 'normal' or 'uniform'

        list_wea = mcweat.gen_set_of_weathers(nb_weath=nb_weather,
                                              year=year,
                                              timestep=timestep,
                                              region_nb=region_nb,
                                              random_method=random_method)

        assert len(list_wea) == nb_weather
        assert min(list_wea[0].tAmbient) >= -25
        assert max(list_wea[0].tAmbient) <= 50

    def test_run_mc_sh_uncertain_single_building(self,
                                                 fixture_detailed_building):

        building = copy.deepcopy(fixture_detailed_building)
        nb_samples = 2

        mc_build.run_mc_sh_uncertain_single_building(building, nb_samples,
                                                     time_sp_force_retro=40,
                                                     max_retro_year=2014,
                                                     weather_region=5,
                                                     weather_year=2010,
                                                     nb_occ_unc=True,
                                                     MC_analysis=False,
                                                     build_physic_unc=True)

    def test_mc_city(self, fixture_environment, fixture_detailed_building):
        nb_samples = 2

        city_obj = city.City(environment=fixture_environment)

        building1 = copy.deepcopy(fixture_detailed_building)
        building2 = copy.deepcopy(fixture_detailed_building)

        city_obj.add_building(building1, point.Point(0, 0))
        city_obj.add_building(building2, point.Point(10, 10))

        mc_city.run_mc_sh_uncertain_city(city=city_obj,
                                         nb_samples=nb_samples,
                                         time_sp_force_retro=40,
                                         max_retro_year=2014,
                                         weather_region=5,
                                         weather_year=2010,
                                         nb_occ_unc=True)