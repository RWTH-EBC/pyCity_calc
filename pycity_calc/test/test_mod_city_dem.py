#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

"""
from __future__ import division

import numpy as np

import pycity_calc.toolbox.modifiers.mod_city_sh_dem as modsh

class TestModCity(object):

    def test_sh_curve_summer_off(self):

        sh_array = np.ones(365 * 24) * 10000

        sh_dem_before = sum(sh_array) * 3600 / (1000 * 3600)

        sh_array_after = modsh.sh_curve_summer_off(sh_array=sh_array, resc=1)
        sh_dem_after = sum(sh_array_after) * 3600 / (1000 * 3600)

        assert abs(sh_dem_after - sh_dem_before) <= 0.001

        sh_array_after = modsh.sh_curve_summer_off(sh_array=sh_array, resc=0.5)
        sh_dem_after = sum(sh_array_after) * 3600 / (1000 * 3600)

        assert sh_dem_before > sh_dem_after
