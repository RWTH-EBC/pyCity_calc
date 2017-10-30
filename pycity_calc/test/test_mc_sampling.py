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
import pycity_calc.toolbox.mc_helpers.city.city_sampling as citsamp
import pycity_calc.toolbox.mc_helpers.esys.esyssampling as esyssamp
import pycity_calc.toolbox.mc_helpers.demand_unc_single_build as mc_build
import pycity_calc.toolbox.mc_helpers.demand_unc_city as mc_city

from pycity_calc.test.pycity_calc_fixtures import fixture_building, \
    fixture_environment, fixture_city, fixture_apartment, fixture_th_demand, \
    fixture_el_demand, fixture_detailed_building


class Test_MC_Sampling():
    def test_calc_array_mod_years_single_build(self):

        nb_samples = 100
        year_of_constr = 1970
        max_year = 2014
        time_sp_force_retro = None

        list_mod_years = \
            mcbuild.calc_array_mod_years_single_build(nb_samples=nb_samples,
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
            mcbuild.calc_array_mod_years_single_build(nb_samples=nb_samples,
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
            mcbuild.calc_array_mod_years_single_build(nb_samples=nb_samples,
                                                      year_of_constr=year_of_constr,
                                                      max_year=max_year,
                                                      time_sp_force_retro=time_sp_force_retro)

        assert min(list_mod_years) >= 1970
        assert max(list_mod_years) <= 2000

    def test_calc_list_mod_years_single_build_min_year(self):
        nb_samples = 2
        year_of_constr = 1990
        max_year = 2009
        time_sp_force_retro = 30

        array_years = \
            mcbuild.calc_array_mod_years_single_build(nb_samples=nb_samples,
                                                      year_of_constr=
                                                      year_of_constr,
                                                      max_year=max_year,
                                                      time_sp_force_retro=
                                                      time_sp_force_retro)

        assert len(array_years) == nb_samples

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

    def test_calc_sh_samples_build(self):
        nb_samples = 5
        sh_ref = 10000

        array_sh = mcbuild.calc_sh_demand_samples(nb_samples=nb_samples,
                                                   sh_ref=sh_ref)

        assert len(array_sh) == nb_samples
        for i in range(len(array_sh)):
            array_sh[i] >= 0
            array_sh[i] <= sh_ref * 1000

    def test_calc_sh_on_off_samples(self):
        nb_samples = 5

        array_sh = mcbuild.calc_sh_summer_on_off_samples(nb_samples)

        assert len(array_sh) == nb_samples
        for i in range(len(array_sh)):
            array_sh[i] == 0 or array_sh[i] == 1

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

    def test_mc_non_res(self, fixture_building):

        building = copy.deepcopy(fixture_building)

        building.build_type = 2

        nb_samples = 2

        (list_sh, list_el) = mc_build.non_res_build_unc_sampling(
            exbuilding=building, nb_samples=nb_samples, sh_unc=True,
            el_unc=True, th_factor=0.5, el_factor=0.5)

        assert len(list_sh) == 2
        assert len(list_el) == 2

        sh_dem = building.get_annual_space_heat_demand()
        el_dem = building.get_annual_el_demand()

        for i in range(len(list_sh)):
            sh_sample = list_sh[i]
            el_sample = list_el[i]

            assert abs(sh_sample - sh_dem) <= 0.5001 * sh_dem
            assert abs(el_sample - el_dem) <= 0.5001 * el_dem

    def test_city_sampling(self):

        nb_samples = 2

        minv = 0.95
        maxv = 1.18

        array_int = \
            citsamp.sample_interest(nb_samples, minval=minv, maxval=maxv)

        assert len(array_int) == 2
        for i in range(len(array_int)):
            assert array_int[i] >= minv
            assert array_int[i] <= maxv

        array_int = \
            citsamp.sample_price_ch_cap(nb_samples, minval=minv, maxval=maxv)

        assert len(array_int) == 2
        for i in range(len(array_int)):
            assert array_int[i] >= minv
            assert array_int[i] <= maxv

        array_int = \
            citsamp.sample_price_ch_dem_gas(nb_samples, minval=minv,
                                            maxval=maxv)

        assert len(array_int) == 2
        for i in range(len(array_int)):
            assert array_int[i] >= minv
            assert array_int[i] <= maxv

        array_int = \
            citsamp.sample_price_ch_dem_el(nb_samples, minval=minv,
                                           maxval=maxv)

        assert len(array_int) == 2
        for i in range(len(array_int)):
            assert array_int[i] >= minv
            assert array_int[i] <= maxv

        array_int = \
            citsamp.sample_price_ch_op(nb_samples, minval=minv,
                                       maxval=maxv)

        assert len(array_int) == 2
        for i in range(len(array_int)):
            assert array_int[i] >= minv
            assert array_int[i] <= maxv

        array_int = \
            citsamp.sample_price_ch_op(nb_samples, minval=minv,
                                       maxval=maxv)

        assert len(array_int) == 2
        for i in range(len(array_int)):
            assert array_int[i] >= minv
            assert array_int[i] <= maxv

        array_int = \
            citsamp.sample_price_ch_eeg_chp(nb_samples, minval=minv,
                                            maxval=maxv)

        assert len(array_int) == 2
        for i in range(len(array_int)):
            assert array_int[i] >= minv
            assert array_int[i] <= maxv

        array_int = \
            citsamp.sample_price_ch_eeg_pv(nb_samples, minval=minv,
                                           maxval=maxv)

        assert len(array_int) == 2
        for i in range(len(array_int)):
            assert array_int[i] >= minv
            assert array_int[i] <= maxv

        array_int = \
            citsamp.sample_price_ch_eex(nb_samples, minval=minv,
                                        maxval=maxv)

        assert len(array_int) == 2
        for i in range(len(array_int)):
            assert array_int[i] >= minv
            assert array_int[i] <= maxv

        array_int = \
            citsamp.sample_price_ch_grid_use(nb_samples, minval=minv,
                                             maxval=maxv)

        assert len(array_int) == 2
        for i in range(len(array_int)):
            assert array_int[i] >= minv
            assert array_int[i] <= maxv

        array_int = \
            citsamp.sample_grid_av_fee(nb_samples, minval=minv,
                                       maxval=maxv)

        assert len(array_int) == 2
        for i in range(len(array_int)):
            assert array_int[i] >= minv
            assert array_int[i] <= maxv

        minv = 8
        maxv = 12

        array_int = \
            citsamp.sample_temp_ground(nb_samples, minval=minv,
                                       maxval=maxv)

        assert len(array_int) == 2
        for i in range(len(array_int)):
            assert array_int[i] >= minv
            assert array_int[i] <= maxv

        array_int = \
            citsamp.sample_quota_summer_heat_on(nb_samples, minval=0,
                                                maxval=100)

        assert len(array_int) == 2
        for i in range(len(array_int)):
            assert array_int[i] >= 0
            assert array_int[i] <= 100

    def test_esys_sampling(self):

        nb_samples = 2

        minv = 0.1
        maxv = 0.9

        array_int = \
            esyssamp.sample_bat_self_disch(nb_samples, minv=minv,
                                           maxv=maxv)

        assert len(array_int) == 2
        for i in range(len(array_int)):
            assert array_int[i] >= minv
            assert array_int[i] <= maxv

        array_int = \
            esyssamp.sample_bat_eta_charge(nb_samples)

        assert len(array_int) == 2
        for i in range(len(array_int)):
            assert array_int[i] >= 0
            assert array_int[i] <= 1

        array_int = \
            esyssamp.sample_bat_eta_discharge(nb_samples)

        assert len(array_int) == 2
        for i in range(len(array_int)):
            assert array_int[i] >= 0
            assert array_int[i] <= 1

        array_int = \
            esyssamp.sample_boi_eff(nb_samples)

        assert len(array_int) == 2
        for i in range(len(array_int)):
            assert array_int[i] >= 0
            assert array_int[i] <= 1

        array_int = \
            esyssamp.sample_quality_grade_hp_bw(nb_samples, minv=minv,
                                           maxv=maxv)

        assert len(array_int) == 2
        for i in range(len(array_int)):
            assert array_int[i] >= minv
            assert array_int[i] <= maxv

        array_int = \
            esyssamp.sample_quality_grade_hp_aw(nb_samples, minv=minv,
                                                maxv=maxv)

        assert len(array_int) == 2
        for i in range(len(array_int)):
            assert array_int[i] >= minv
            assert array_int[i] <= maxv

        array_int = \
            esyssamp.sample_pv_eta(nb_samples)

        assert len(array_int) == 2
        for i in range(len(array_int)):
            assert array_int[i] >= 0
            assert array_int[i] <= 1

        array_int = \
            esyssamp.sample_pv_beta(nb_samples, minv=0, maxv=70)

        assert len(array_int) == 2
        for i in range(len(array_int)):
            assert array_int[i] >= 0
            assert array_int[i] <= 70

        array_int = \
            esyssamp.sample_pv_gamma(nb_samples, minv=-180, maxv=180)

        assert len(array_int) == 2
        for i in range(len(array_int)):
            assert array_int[i] >= -180
            assert array_int[i] <= 180
