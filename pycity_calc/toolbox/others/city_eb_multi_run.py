#!/usr/bin/env python
# coding=utf-8
"""

"""
from __future__ import division

import os
import pickle

import pycity_calc.simulation.energy_balance.city_eb_calc as citeb

def main():
    this_path = os.path.dirname(os.path.abspath(__file__))

    path_folder_cities = os.path.join(this_path, 'input', 'city_eb_multi2')

    list_city_files = []
    for file in os.listdir(path_folder_cities):
        if file.endswith('.pkl'):
            list_city_files.append(file)

    print(list_city_files)

    for file in list_city_files:

        print('File: ')
        print(file)
        print('#########################################################')

        path_load = os.path.join(path_folder_cities, file)
        city = pickle.load(open(path_load, mode='rb'))

        folder_name = str(file[:-4])
        path_save_folder = str(os.path.join(this_path,
                                            'output',
                                            'city_eb_multi',
                                            folder_name))

        if not os.path.isdir(path_save_folder):
            os.makedirs(path_save_folder)

        # Construct energy balance
        energy_balance = citeb.CityEBCalculator(city=city)

        #  Calc. city energy balance
        energy_balance.calc_city_energy_balance()

        #  Perform final energy anaylsis
        dict_fe_city = energy_balance.calc_final_energy_balance_city()

        #  Perform emissions calculation
        co2 = energy_balance.calc_co2_emissions(el_mix_for_chp=True)

        #  Calculate amounts of generated and consumed energy to calculate
        #  coverage
        dict_energy = energy_balance.get_gen_and_con_energy()

        fuel_boiler = dict_fe_city['fuel_boiler']
        fuel_chp = dict_fe_city['fuel_chp']
        grid_import_dem = dict_fe_city['grid_import_dem']
        grid_import_hp = dict_fe_city['grid_import_hp']
        grid_import_eh = dict_fe_city['grid_import_eh']
        chp_feed = dict_fe_city['chp_feed']
        pv_feed = dict_fe_city['pv_feed']
        pump_energy = dict_fe_city['pump_energy']

        print('Amounts of generated and consumed energy')
        print('#############################################')
        for key in dict_energy.keys():
            print('Dict. key: ')
            print(key)
            print('Values')
            print(dict_energy[key])
            print()
        print('#############################################')
        print()

        print('Boiler fuel demand in kWh/a: ')
        print(round(fuel_boiler, 0))

        print('CHP fuel demand in kWh/a: ')
        print(round(fuel_chp, 0))
        print()

        print('Imported electricity in kWh/a: ')
        print(round(grid_import_dem + grid_import_eh + grid_import_hp, 0))

        print('Exported CHP electricity in kWh/a: ')
        print(round(chp_feed, 0))

        print('Exported PV electricity in kWh/a: ')
        print(round(pv_feed, 0))
        print()

        print('LHN electric pump energy in kWh/a:')
        print(round(pump_energy, 0))
        print()

        print('#############################################')
        print()

        print('Total emissions of city district in t/a:')
        print(round(co2 / 1000, 0))

        print()
        print('File')
        print(file)
        print('#############')
        print()

        #  Plot coverage figures
        energy_balance.plot_coverage(
            path_save_folder=path_save_folder,
            save_tikz=False
        )

        print()


if __name__ == '__main__':
    main()
