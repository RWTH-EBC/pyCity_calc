#!/usr/bin/env python
# coding=utf-8
"""

"""
from __future__ import division

import os
import pickle
import matplotlib.pyplot as plt

import pycity_calc.toolbox.modifiers.mod_resc_peak_load_day as modpeak


def main():

    resc_factor = 2

    this_path = os.path.dirname(os.path.abspath(__file__))
    filename = 'aachen_kronenberg_6.pkl'
    path_input_file = os.path.join(this_path, 'input', filename)

    file_out = filename[:-4] + '_peak_resc_' + str(resc_factor) + '.pkl'
    path_out = os.path.join(this_path, 'output', file_out)

    #  Load city object
    city = pickle.load(open(path_input_file, mode='rb'))

    #  Get sh peak load power
    power_curve_old = city.get_aggr_space_h_power_curve()
    sh_max_old = max(power_curve_old)

    #  Modify city
    list_build_ids = city.get_list_build_entity_node_ids()

    #  Loop over all buildings
    for n in list_build_ids:
        #  Current building
        build = city.nodes[n]['entity']

        modpeak.resc_sh_peak_load_build(building=build,
                                        resc_factor=resc_factor)

    #  Get sh peak load power
    power_curve_new = city.get_aggr_space_h_power_curve()
    sh_max_new = max(power_curve_new)

    print('Old sh max:  ', sh_max_old)
    print('New sh max:  ', sh_max_new)

    assert sh_max_new > sh_max_old
    assert abs(sh_max_new >- sh_max_old * resc_factor) <= 0.01 * sh_max_new

    #  Save modified city district
    pickle.dump(city, open(path_out, mode='wb'))

    plt.plot(power_curve_old, label='old')
    plt.plot(power_curve_new, label='new')
    plt.legend()
    plt.show()
    plt.close()

if __name__ == '__main__':
    main()
